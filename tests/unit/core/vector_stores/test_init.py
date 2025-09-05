"""Test vector_stores package initialization."""


class TestVectorStoresInit:
    """Test vector_stores package __init__.py module."""

    def test_import_vector_stores_package(self):
        """Test that the vector_stores package can be imported."""
        import src.core.vector_stores

        assert src.core.vector_stores is not None

    def test_qdrant_vector_store_import(self):
        """Test that QdrantVectorStore can be imported from the package."""
        from src.core.vector_stores import QdrantVectorStore

        assert QdrantVectorStore is not None

    def test_all_exports(self):
        """Test __all__ exports are correct."""
        import src.core.vector_stores as vs_module

        # Check that __all__ is defined
        assert hasattr(vs_module, "__all__")
        assert isinstance(vs_module.__all__, list)

        # Check expected exports
        expected_exports = ["QdrantVectorStore"]
        assert vs_module.__all__ == expected_exports

    def test_exported_classes_accessible(self):
        """Test that all exported classes are accessible."""
        import src.core.vector_stores as vs_module

        for export_name in vs_module.__all__:
            assert hasattr(vs_module, export_name)
            exported_class = getattr(vs_module, export_name)
            assert exported_class is not None

    def test_qdrant_vector_store_is_class(self):
        """Test that QdrantVectorStore is a class."""
        from src.core.vector_stores import QdrantVectorStore

        assert isinstance(QdrantVectorStore, type)

    def test_module_docstring_exists(self):
        """Test that the module has proper documentation."""
        import src.core.vector_stores as vs_module

        assert vs_module.__doc__ is not None
        assert len(vs_module.__doc__.strip()) > 0

        # Check for key documentation elements
        doc = vs_module.__doc__.lower()
        assert "vector" in doc
        assert "store" in doc or "implementation" in doc
