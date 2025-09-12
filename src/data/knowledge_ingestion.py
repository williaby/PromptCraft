"""
Knowledge base ingestion pipeline for Qdrant vector database.

This module handles the conversion of markdown knowledge files into vector
embeddings and their insertion into Qdrant collections. It provides batch
processing, progress tracking, and error handling for large knowledge bases.
"""

import hashlib
import logging
from pathlib import Path
import time
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = type(None)
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from ..config.qdrant_settings import qdrant_settings
from ..core.vector_stores.collection_manager import QdrantCollectionManager


class KnowledgeIngestionPipeline:
    """Pipeline for ingesting knowledge base files into Qdrant."""

    def __init__(self, client: QdrantClient, embedding_model: SentenceTransformer | None = None) -> None:
        """Initialize knowledge ingestion pipeline."""
        self.client = client
        self.logger = logging.getLogger(__name__)

        # Check if sentence-transformers is available
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers is not installed. Install with: poetry install --with ml")

        # Initialize embedding model
        if embedding_model is None:
            self.logger.info("Loading embedding model: %s", qdrant_settings.embedding_model)
            self.embedding_model = SentenceTransformer(qdrant_settings.embedding_model)
        else:
            self.embedding_model = embedding_model

        # Initialize collection manager
        self.collection_manager = QdrantCollectionManager(client)

    async def ingest_create_agent_knowledge(self) -> dict[str, Any]:
        """Ingest CREATE framework knowledge from /knowledge/create_agent/ directory."""
        knowledge_path = Path("knowledge/create_agent")

        if not knowledge_path.exists():
            self.logger.error("CREATE agent knowledge directory not found: %s", knowledge_path)
            return {"success": False, "error": "Knowledge directory not found"}

        self.logger.info("Starting CREATE agent knowledge ingestion from %s", knowledge_path)

        # Ensure collection exists
        collection_name = qdrant_settings.create_agent_collection
        await self.collection_manager.create_collection(collection_name)

        # Process all markdown files
        markdown_files = list(knowledge_path.glob("**/*.md"))
        self.logger.info("Found %d markdown files to process", len(markdown_files))

        processed_documents = []
        errors = []

        for md_file in markdown_files:
            try:
                documents = await self._process_markdown_file(md_file, collection_name)
                processed_documents.extend(documents)
                self.logger.debug("Processed %s: %d chunks", md_file.name, len(documents))
            except Exception as e:
                error_msg = f"Failed to process {md_file}: {e!s}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        # Batch insert documents
        if processed_documents:
            insert_result = await self._batch_insert_documents(processed_documents, collection_name)

            return {
                "success": insert_result["success"],
                "files_processed": len(markdown_files) - len(errors),
                "total_files": len(markdown_files),
                "documents_created": len(processed_documents),
                "documents_inserted": insert_result.get("inserted_count", 0),
                "errors": errors,
                "processing_time": insert_result.get("processing_time", 0),
            }
        return {"success": False, "error": "No documents to insert", "errors": errors}

    async def _process_markdown_file(self, file_path: Path, collection_name: str) -> list[dict[str, Any]]:
        """Process a single markdown file into document chunks."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Split content into semantic chunks
            chunks = self._split_markdown_content(content)

            documents = []
            for i, chunk in enumerate(chunks):
                if chunk.strip():  # Skip empty chunks
                    # Generate embedding
                    embedding = self.embedding_model.encode(chunk)

                    # Create document ID
                    doc_id = self._generate_document_id(file_path, i)

                    # Extract metadata
                    metadata = self._extract_metadata(file_path, chunk, i)

                    documents.append(
                        {
                            "id": doc_id,
                            "content": chunk,
                            "embedding": embedding.tolist(),
                            "metadata": metadata,
                            "collection": collection_name,
                            "file_path": str(file_path),
                        },
                    )

            return documents

        except Exception as e:
            self.logger.error("Error processing file %s: %s", file_path, str(e))
            raise

    def _split_markdown_content(self, content: str, max_chunk_size: int = 1000) -> list[str]:
        """Split markdown content into semantic chunks."""
        # Simple chunking strategy - split by double newlines and headers
        chunks = []

        # Split by headers first
        sections = content.split("\n## ")

        for i, section in enumerate(sections):
            if i > 0:  # Add back the header marker for non-first sections
                section = "## " + section

            # If section is too long, split by paragraphs
            if len(section) > max_chunk_size:
                paragraphs = section.split("\n\n")
                current_chunk = ""

                for paragraph in paragraphs:
                    if len(current_chunk + paragraph) > max_chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = paragraph
                        else:
                            # Single paragraph too long, force split
                            chunks.append(paragraph[:max_chunk_size])
                            current_chunk = paragraph[max_chunk_size:]
                    else:
                        current_chunk += "\n\n" + paragraph if current_chunk else paragraph

                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            elif section.strip():
                chunks.append(section.strip())

        return [chunk for chunk in chunks if chunk.strip()]

    def _generate_document_id(self, file_path: Path, chunk_index: int) -> str:
        """Generate unique document ID from file path and chunk index."""
        # Create a hash from file path to ensure uniqueness
        file_hash = hashlib.sha256(str(file_path).encode()).hexdigest()[:8]
        return f"{file_path.stem}_{file_hash}_{chunk_index}"

    def _extract_metadata(self, file_path: Path, content: str, chunk_index: int) -> dict[str, Any]:
        """Extract metadata from file path and content."""
        metadata = {
            "source_file": str(file_path),
            "file_name": file_path.name,
            "chunk_index": chunk_index,
            "content_length": len(content),
            "timestamp": time.time(),
            "source_type": "knowledge_base",
        }

        # Extract category from file path
        if "create_agent" in str(file_path):
            metadata["category"] = "create_framework"

        # Extract additional metadata from content
        if "## " in content:
            # This chunk contains a header
            header_line = next(line for line in content.split("\n") if line.startswith("## "))
            metadata["section_title"] = header_line.replace("## ", "").strip()

        # Add difficulty level based on content complexity
        if any(term in content.lower() for term in ["advanced", "complex", "enterprise"]):
            metadata["difficulty"] = "advanced"
        elif any(term in content.lower() for term in ["intermediate", "moderate"]):
            metadata["difficulty"] = "intermediate"
        else:
            metadata["difficulty"] = "beginner"

        return metadata

    async def _batch_insert_documents(
        self,
        documents: list[dict[str, Any]],
        collection_name: str,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Insert documents into Qdrant in batches."""
        if batch_size is None:
            batch_size = qdrant_settings.batch_size

        start_time = time.time()
        inserted_count = 0
        errors = []

        try:
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]

                # Convert to Qdrant points
                points = []
                for doc in batch:
                    point = PointStruct(
                        id=doc["id"],
                        vector=doc["embedding"],
                        payload={
                            "content": doc["content"],
                            "metadata": doc["metadata"],
                            "file_path": doc["file_path"],
                            "collection": doc["collection"],
                        },
                    )
                    points.append(point)

                # Insert batch
                try:
                    self.client.upsert(collection_name=collection_name, points=points)
                    inserted_count += len(points)
                    self.logger.debug("Inserted batch %d-%d (%d documents)", i, i + len(batch), len(points))
                except Exception as e:
                    error_msg = f"Failed to insert batch {i}-{i + len(batch)}: {e!s}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            processing_time = time.time() - start_time

            self.logger.info(
                "Batch insertion completed: %d/%d documents inserted in %.2fs",
                inserted_count,
                len(documents),
                processing_time,
            )

            return {
                "success": len(errors) == 0,
                "inserted_count": inserted_count,
                "total_count": len(documents),
                "processing_time": processing_time,
                "errors": errors,
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error("Batch insertion failed: %s", str(e))
            return {
                "success": False,
                "inserted_count": inserted_count,
                "total_count": len(documents),
                "processing_time": processing_time,
                "error": str(e),
                "errors": errors,
            }

    async def validate_ingestion(self, collection_name: str) -> dict[str, Any]:
        """Validate the ingestion process by checking collection status."""
        try:
            collection_info = self.client.get_collection(collection_name)

            # Perform a test search
            test_query = "CREATE framework prompt engineering"
            test_embedding = self.embedding_model.encode(test_query)

            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=test_embedding.tolist(),
                limit=5,
            )

            return {
                "collection_name": collection_name,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status.value,
                "test_search_results": len(search_results),
                "sample_result": (
                    {
                        "score": search_results[0].score if search_results else None,
                        "content_preview": (
                            search_results[0].payload.get("content", "")[:100]
                            if search_results and search_results[0].payload
                            else None
                        ),
                    }
                    if search_results
                    else None
                ),
            }

        except Exception as e:
            self.logger.error("Ingestion validation failed: %s", str(e))
            return {"error": str(e)}

    async def get_ingestion_stats(self) -> dict[str, Any]:
        """Get statistics about the current ingestion status."""
        stats = await self.collection_manager.get_collection_stats()

        total_points = sum(
            collection.get("points_count", 0)
            for collection in stats.values()
            if isinstance(collection, dict) and "points_count" in collection
        )

        return {
            "total_documents": total_points,
            "collections": stats,
            "embedding_model": qdrant_settings.embedding_model,
            "vector_dimensions": qdrant_settings.vector_size,
        }
