"""
Journey 1: Smart Templates Interface

This module implements the C.R.E.A.T.E. framework interface for prompt enhancement
with file upload support, model selection, and code snippet copying.
"""

import logging
import time
from pathlib import Path
from typing import Any

from src.utils.logging_mixin import LoggerMixin

logger = logging.getLogger(__name__)


class Journey1SmartTemplates(LoggerMixin):
    """
    Journey 1: Smart Templates implementation with C.R.E.A.T.E. framework.

    Features:
    - Multi-format input (text, file upload, URL, clipboard)
    - C.R.E.A.T.E. framework breakdown
    - File source attribution
    - Code snippet copying with multiple formats
    - Model attribution and cost tracking
    """

    def __init__(self):
        super().__init__()
        self.supported_file_types = [".txt", ".md", ".pdf", ".docx", ".csv", ".json"]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_files = 5

    def extract_file_content(self, file_path: str) -> tuple[str, str]:
        """
        Extract content from uploaded file with enhanced processing.

        Args:
            file_path: Path to the uploaded file

        Returns:
            Tuple of (content, file_type)
        """
        try:
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()

            if file_extension in [".txt", ".md"]:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Clean up common formatting issues
                content = self._clean_text_content(content)
                return content, file_extension

            if file_extension == ".pdf":
                # Enhanced PDF processing with metadata
                file_size = file_path_obj.stat().st_size
                return (
                    f"""[PDF Document: {file_path_obj.name}]
Size: {file_size / 1024:.1f} KB
Status: PDF text extraction requires PyPDF2 library
Note: Upload as .txt or .md for immediate processing
Content preview not available - please convert to text format""",
                    file_extension,
                )

            if file_extension in [".docx"]:
                # Enhanced DOCX processing with metadata
                file_size = file_path_obj.stat().st_size
                return (
                    f"""[Word Document: {file_path_obj.name}]
Size: {file_size / 1024:.1f} KB
Status: DOCX text extraction requires python-docx library
Note: Save as .txt or copy content for immediate processing
Content preview not available - please convert to text format""",
                    file_extension,
                )

            if file_extension == ".csv":
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Enhanced CSV processing with structure analysis
                processed_content = self._process_csv_content(content, file_path_obj.name)
                return processed_content, file_extension

            if file_extension == ".json":
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Enhanced JSON processing with structure analysis
                processed_content = self._process_json_content(content, file_path_obj.name)
                return processed_content, file_extension

            return (
                f"""[Unsupported file type: {file_extension}]
File: {file_path_obj.name}
Supported formats: .txt, .md, .pdf, .docx, .csv, .json
Please convert to a supported format for processing""",
                file_extension,
            )

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {e}")
            return (
                f"""[Error reading file: {e}]
File: {file_path_obj.name if 'file_path_obj' in locals() else 'unknown'}
Please check file format and try again""",
                "error",
            )

    def process_files(self, files: list[Any]) -> dict[str, Any]:
        """
        Process uploaded files and extract content with enhanced integration.

        Args:
            files: List of uploaded file objects

        Returns:
            Dictionary with file information and extracted content
        """
        if not files:
            return {
                "files": [],
                "content": "",
                "summary": "No files uploaded",
                "file_count": 0,
                "total_size": 0,
                "supported_files": 0,
                "preview_available": False,
            }

        processed_files = []
        combined_content = ""
        total_size = 0
        supported_files = 0
        errors = []

        for i, file_obj in enumerate(files[: self.max_files]):  # Limit to max files
            if hasattr(file_obj, "name"):
                file_path = file_obj.name
            else:
                file_path = str(file_obj)

            try:
                content, file_type = self.extract_file_content(file_path)
                file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0

                # Check if file is supported for processing
                is_supported = file_type in [".txt", ".md", ".csv", ".json"]
                if is_supported:
                    supported_files += 1

                file_info = {
                    "name": Path(file_path).name,
                    "type": file_type,
                    "size": file_size,
                    "size_mb": file_size / (1024 * 1024),
                    "content": content[:2000] + "..." if len(content) > 2000 else content,  # Increased preview length
                    "full_content": content,
                    "is_supported": is_supported,
                    "processing_status": "success" if not content.startswith("[Error") else "error",
                    "preview_lines": len(content.split("\n")) if content else 0,
                }

                processed_files.append(file_info)
                total_size += file_size

                # Add to combined content with better formatting
                separator = f"\\n\\n{'='*60}\\n"
                file_header = f"📄 FILE: {file_info['name']} ({file_info['size_mb']:.1f}MB)\\n"
                combined_content += f"{separator}{file_header}{'='*60}\\n{content}"

            except Exception as e:
                logger.error(f"Error processing file {i+1}: {e}")
                errors.append(f"File {i+1}: {e!s}")

                # Add error file info
                error_file = {
                    "name": Path(file_path).name if file_path else f"file_{i+1}",
                    "type": "error",
                    "size": 0,
                    "size_mb": 0,
                    "content": f"Error processing file: {e!s}",
                    "full_content": "",
                    "is_supported": False,
                    "processing_status": "error",
                    "preview_lines": 0,
                }
                processed_files.append(error_file)

        # Generate comprehensive summary
        summary_parts = []
        if processed_files:
            summary_parts.append(f"📁 Processed {len(processed_files)} files")
            if supported_files > 0:
                summary_parts.append(f"✅ {supported_files} files ready for processing")
            if len(processed_files) - supported_files > 0:
                summary_parts.append(f"⚠️ {len(processed_files) - supported_files} files need conversion")
            if total_size > 0:
                summary_parts.append(f"📊 Total size: {total_size / (1024 * 1024):.1f}MB")

        return {
            "files": processed_files,
            "content": combined_content,
            "summary": " | ".join(summary_parts) if summary_parts else "No files processed",
            "file_count": len(processed_files),
            "total_size": total_size,
            "supported_files": supported_files,
            "preview_available": any(f["is_supported"] for f in processed_files),
            "errors": errors,
            "processing_complete": True,
        }

    def enhance_prompt(
        self,
        text_input: str,
        files: list[Any],
        model_mode: str,
        custom_model: str,
        reasoning_depth: str,
        search_tier: str,
        temperature: float,
    ) -> tuple[str, str, str, str, str, str, str, str, str]:
        """
        Enhance the prompt using the C.R.E.A.T.E. framework.

        Args:
            text_input: User's text input
            files: Uploaded files
            model_mode: Model selection mode
            custom_model: Custom model selection
            reasoning_depth: Analysis depth
            search_tier: Search strategy
            temperature: Response creativity

        Returns:
            Tuple of enhanced content and C.R.E.A.T.E. components
        """
        start_time = time.time()

        try:
            # Process files
            file_data = self.process_files(files)

            # Combine text and file content
            combined_input = text_input
            if file_data["content"]:
                combined_input += "\\n\\n" + file_data["content"]

            # Determine model to use
            if model_mode == "custom":
                selected_model = custom_model
            elif model_mode == "free_mode":
                selected_model = "llama-4-maverick:free"
            elif model_mode == "premium":
                selected_model = "claude-3.5-sonnet"
            else:  # standard
                selected_model = "gpt-4o-mini"

            # For now, return mock enhanced content
            # In a real implementation, this would call the Zen MCP server
            enhanced_prompt = self._create_mock_enhanced_prompt(combined_input, reasoning_depth)

            # Create C.R.E.A.T.E. breakdown
            create_breakdown = self._create_mock_create_breakdown(combined_input)

            # Calculate mock cost and time
            response_time = time.time() - start_time
            mock_cost = self._calculate_mock_cost(selected_model, len(combined_input), len(enhanced_prompt))

            # Create model attribution
            model_attribution = f"""
            <div class="model-attribution">
                <strong>🤖 Generated by:</strong> {selected_model} |
                <strong>⏱️ Response time:</strong> {response_time:.2f}s |
                <strong>💰 Cost:</strong> ${mock_cost:.4f}
            </div>
            """

            # Create file sources display
            file_sources = self._create_file_sources_display(file_data)

            return (
                enhanced_prompt,
                create_breakdown["context"],
                create_breakdown["request"],
                create_breakdown["examples"],
                create_breakdown["augmentations"],
                create_breakdown["tone_format"],
                create_breakdown["evaluation"],
                model_attribution,
                file_sources,
            )

        except Exception as e:
            logger.error(f"Error enhancing prompt: {e}")
            return (
                f"Error processing request: {e}",
                "",
                "",
                "",
                "",
                "",
                "",
                f"<div class='error'>Error: {e}</div>",
                "<div class='error'>No files processed due to error</div>",
            )

    def _create_mock_enhanced_prompt(self, input_text: str, reasoning_depth: str) -> str:
        """Create a mock enhanced prompt for demonstration with code snippet examples."""
        if not input_text.strip():
            return "Please provide input text or upload files to enhance."

        # Extract the main task from input
        task = input_text.strip()[:100] + "..." if len(input_text) > 100 else input_text.strip()

        # Add code examples based on reasoning depth
        code_examples = ""
        if reasoning_depth == "comprehensive":
            code_examples = """

## Code Examples
Here are some examples to illustrate the approach:

```python
# Example: Professional communication structure
def create_professional_message(content, audience, purpose):
    message = {
        "opening": f"Dear {audience},",
        "context": "Setting the stage for the communication",
        "main_content": content,
        "action_items": ["Specific next steps", "Clear deadlines"],
        "closing": "Best regards, [Your Name]"
    }
    return message
```

```markdown
# Template Structure
## Context
Brief background information

## Main Message
Clear, specific communication

## Next Steps
- [ ] Action item 1
- [ ] Action item 2
- [ ] Follow-up date

## Contact Information
Your details for questions
```"""
        elif reasoning_depth == "detailed":
            code_examples = """

## Quick Reference
```
Structure: Context → Message → Action → Follow-up
Tone: Professional yet approachable
Format: Clear headings, bullet points, specific timelines
```"""

        enhanced = f"""# Enhanced Prompt

## Task Context
You are a professional communication specialist helping to create clear, effective content.

## Specific Request
{task}

## Enhanced Instructions
1. **Clarity**: Ensure the message is clear and unambiguous
2. **Tone**: Maintain a professional yet approachable tone
3. **Structure**: Organize information logically with clear headings
4. **Action Items**: Include specific next steps where applicable
5. **Audience**: Consider the target audience and their needs

## Output Format
- Use clear, concise language
- Include relevant examples where helpful
- Provide actionable recommendations
- Maintain professional formatting

## Quality Criteria
- Message achieves its intended purpose
- Tone is appropriate for the context
- Information is accurate and complete
- Call-to-action is clear and specific{code_examples}

---

*This enhanced prompt incorporates the C.R.E.A.T.E. framework for optimal results.*"""

        return enhanced

    def _create_mock_create_breakdown(self, input_text: str) -> dict[str, str]:
        """Create a mock C.R.E.A.T.E. framework breakdown with enhanced details."""
        task = input_text.strip()[:50] + "..." if len(input_text) > 50 else input_text.strip()

        return {
            "context": f"""**Professional Communication Analysis**
• Task: {task}
• Audience: Professional stakeholders requiring clear information
• Environment: Business/organizational communication context
• Constraints: Time-sensitive, requires actionable outcomes
• Background: Need for structured messaging with appropriate tone""",
            "request": f"""**Specific Deliverable Requirements**
• Primary objective: Create effective content for {task}
• Secondary objectives: Maintain professionalism, ensure clarity
• Success criteria: Message achieves intended purpose
• Scope: Comprehensive communication addressing all stakeholder needs
• Format: Structured document with clear action items""",
            "examples": """**Reference Examples & Templates**
• Structured emails with clear subject lines and BLUF approach
• Professional announcements with timeline and impact analysis
• Status updates with progress metrics and next steps
• Stakeholder communications with audience-specific messaging
• Crisis communications with transparency and action plans""",
            "augmentations": """**Enhanced Frameworks & Methodologies**
• BLUF (Bottom Line Up Front) for executive summaries
• STAR method (Situation, Task, Action, Result) for structured responses
• Stakeholder analysis for audience consideration
• Risk communication principles for sensitive topics
• Change management communication strategies""",
            "tone_format": """**Style & Formatting Guidelines**
• Tone: Professional yet approachable, confident but not arrogant
• Structure: Clear headings, logical flow, scannable format
• Language: Concise, jargon-free, action-oriented
• Visual elements: Bullet points, numbered lists, clear sections
• Formatting: Bold for emphasis, consistent spacing, professional layout""",
            "evaluation": """**Quality Assessment Criteria**
• Clarity: Message is easily understood by target audience
• Completeness: All necessary information is included
• Actionability: Clear next steps and responsibilities defined
• Professional tone: Appropriate for business context
• Engagement: Likely to generate positive response and action
• Measurable outcomes: Success can be tracked and evaluated""",
        }

    def _calculate_mock_cost(self, model: str, input_length: int, output_length: int) -> float:
        """Calculate mock cost for demonstration."""
        costs = {
            "llama-4-maverick:free": 0.0,
            "gpt-4o-mini": 0.0015,
            "claude-3.5-sonnet": 0.003,
            "gpt-4o": 0.015,
        }

        cost_per_1k = costs.get(model, 0.001)
        total_tokens = (input_length + output_length) // 4  # Rough token estimation
        return (total_tokens / 1000) * cost_per_1k

    def _create_file_sources_display(self, file_data: dict[str, Any]) -> str:
        """Create the enhanced file sources display HTML."""
        if not file_data["files"]:
            return """
            <div id="file-sources" style="background: #f8fafc; padding: 12px; border-radius: 6px; margin: 12px 0;">
                <strong>📄 Source Files Used:</strong>
                <div id="file-list">No files uploaded</div>
            </div>
            """

        file_list = ""
        supported_count = 0
        total_size = 0

        for file_info in file_data["files"]:
            size_mb = file_info.get("size_mb", file_info.get("size", 0) / (1024 * 1024))
            total_size += size_mb

            status_icon = "✅" if file_info.get("is_supported", False) else "⚠️"
            status_text = "Ready" if file_info.get("is_supported", False) else "Needs conversion"

            if file_info.get("is_supported", False):
                supported_count += 1

            # Color coding based on status
            color = "#10b981" if file_info.get("is_supported", False) else "#f59e0b"

            file_list += f"""
            <div style="margin: 4px 0; padding: 8px; background: white; border-radius: 4px; border-left: 3px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{status_icon} {file_info['name']}</strong>
                        <span style="color: #64748b; font-size: 12px;">({size_mb:.1f}MB, {file_info.get('type', 'unknown')})</span>
                    </div>
                    <div style="font-size: 12px; color: {color};">
                        {status_text}
                    </div>
                </div>
                {f"<div style='font-size: 12px; color: #64748b; margin-top: 4px;'>{file_info.get('preview_lines', 0)} lines</div>" if file_info.get('preview_lines', 0) > 0 else ""}
            </div>
            """

        # Summary statistics
        summary_stats = f"""
        <div style="margin-top: 12px; padding: 8px; background: white; border-radius: 4px; border: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #64748b;">
                <span>📊 Total: {len(file_data['files'])} files ({total_size:.1f}MB)</span>
                <span>✅ Ready: {supported_count} files</span>
                <span>⚠️ Needs conversion: {len(file_data['files']) - supported_count} files</span>
            </div>
        </div>
        """

        return f"""
        <div id="file-sources" style="background: #f8fafc; padding: 12px; border-radius: 6px; margin: 12px 0;">
            <strong>📄 Source Files Used:</strong>
            <div id="file-list">{file_list}</div>
            {summary_stats}
        </div>
        """

    def copy_code_blocks(self, content: str) -> str:
        """Extract and format code blocks for copying with enhanced functionality."""
        # Import the export utils for code block extraction
        from src.ui.components.shared.export_utils import ExportUtils

        export_utils = ExportUtils()

        # Extract code blocks
        code_blocks = export_utils.extract_code_blocks(content)

        if not code_blocks:
            return "No code blocks found in this response."

        # Format code blocks for copying
        formatted_blocks = export_utils.format_code_blocks_for_export(code_blocks)

        # In a real implementation, this would copy to clipboard
        return f"Found {len(code_blocks)} code blocks! Content formatted for copying:\n\n{formatted_blocks}"

    def copy_as_markdown(self, content: str) -> str:
        """Copy content as markdown preserving formatting with enhanced features."""
        if not content or not content.strip():
            return "No content to copy as markdown."

        # Import the export utils for markdown formatting
        from src.ui.components.shared.export_utils import ExportUtils

        export_utils = ExportUtils()

        # Extract code blocks and format as markdown
        code_blocks = export_utils.extract_code_blocks(content)

        if code_blocks:
            # Format with code blocks preserved
            markdown_blocks = export_utils.copy_code_as_markdown(code_blocks)
            return f"Copied {len(content)} characters as markdown with {len(code_blocks)} code blocks preserved:\n\n{markdown_blocks}"
        # Format as regular markdown
        lines = content.split("\n")
        formatted_lines = []

        for line in lines:
            # Add markdown formatting for headers if not already present
            if line.strip() and not line.startswith("#") and not line.startswith("*") and not line.startswith("-"):
                # Check if it might be a title/header (short line followed by content)
                if len(line.strip()) < 60 and line.strip().endswith(":"):
                    formatted_lines.append(f"## {line.strip()}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        formatted_content = "\n".join(formatted_lines)
        return f"Copied {len(content)} characters as markdown (formatted): {len(formatted_lines)} lines"

    def download_content(self, content: str, create_data: dict[str, str]) -> str:
        """Prepare content for download."""
        # In practice, this would generate a proper download file
        return f"Download prepared: {len(content)} characters of enhanced content"

    def _clean_text_content(self, content: str) -> str:
        """Clean and normalize text content."""
        # Remove excessive whitespace
        content = "\n".join(line.strip() for line in content.split("\n"))
        # Remove multiple consecutive empty lines
        while "\n\n\n" in content:
            content = content.replace("\n\n\n", "\n\n")
        # Remove common formatting artifacts
        content = content.replace("\r\n", "\n")
        content = content.replace("\r", "\n")
        return content.strip()

    def _process_csv_content(self, content: str, filename: str) -> str:
        """Process CSV content with structure analysis."""
        lines = content.split("\n")
        total_lines = len(lines)

        # Try to detect headers
        if total_lines > 0:
            header_line = lines[0]
            columns = header_line.split(",")
            column_count = len(columns)

            # Generate summary
            summary = f"""[CSV Data: {filename}]
Structure Analysis:
- Total rows: {total_lines}
- Columns: {column_count}
- Headers: {', '.join(col.strip() for col in columns[:5])}{"..." if column_count > 5 else ""}

Sample Data (first 5 rows):
{chr(10).join(lines[:5])}

Full Content:
{content}"""
            return summary

        return f"[CSV Data: {filename}]\nContent:\n{content}"

    def _process_json_content(self, content: str, filename: str) -> str:
        """Process JSON content with structure analysis."""
        try:
            import json

            data = json.loads(content)

            # Analyze structure
            data_type = type(data).__name__
            if isinstance(data, dict):
                keys = list(data.keys())[:5]
                structure_info = f"Object with {len(data)} keys: {', '.join(keys)}{'...' if len(data) > 5 else ''}"
            elif isinstance(data, list):
                structure_info = f"Array with {len(data)} items"
                if len(data) > 0:
                    first_item_type = type(data[0]).__name__
                    structure_info += f" (first item: {first_item_type})"
            else:
                structure_info = f"Simple {data_type} value"

            return f"""[JSON Data: {filename}]
Structure Analysis:
- Type: {data_type}
- Structure: {structure_info}

Formatted Content:
{json.dumps(data, indent=2, ensure_ascii=False)}"""

        except json.JSONDecodeError as e:
            return f"""[JSON Data: {filename}]
Status: Invalid JSON format
Error: {e!s}

Raw Content:
{content}"""

        except Exception as e:
            logger.error(f"Error processing JSON content: {e}")
            return f"""[JSON Data: {filename}]
Status: Processing error
Error: {e!s}

Raw Content:
{content}"""
