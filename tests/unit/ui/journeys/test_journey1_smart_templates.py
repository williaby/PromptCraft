"""
Unit tests for Journey1SmartTemplates class.

This module provides comprehensive test coverage for the Journey1SmartTemplates class,
testing file content extraction, C.R.E.A.T.E. framework functionality, and UI integration.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from src.ui.journeys.journey1_smart_templates import Journey1SmartTemplates


@pytest.mark.unit
class TestJourney1SmartTemplates:
    """Test cases for Journey1SmartTemplates class."""

    def test_init(self):
        """Test Journey1SmartTemplates initialization."""
        journey = Journey1SmartTemplates()
        
        assert journey.supported_file_types == [".txt", ".md", ".pdf", ".docx", ".csv", ".json"]
        assert journey.max_file_size == 10 * 1024 * 1024  # 10MB
        assert journey.max_files == 5

    def test_extract_file_content_txt(self):
        """Test extracting content from text files."""
        journey = Journey1SmartTemplates()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content\nWith multiple lines\n")
            temp_path = f.name
        
        try:
            content, file_type = journey.extract_file_content(temp_path)
            assert "This is test content" in content
            assert file_type == ".txt"
        finally:
            Path(temp_path).unlink()

    def test_extract_file_content_md(self):
        """Test extracting content from markdown files."""
        journey = Journey1SmartTemplates()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Markdown\n\nThis is **bold** text.")
            temp_path = f.name
        
        try:
            content, file_type = journey.extract_file_content(temp_path)
            assert "# Test Markdown" in content
            assert "**bold**" in content
            assert file_type == ".md"
        finally:
            Path(temp_path).unlink()

    def test_extract_file_content_pdf_placeholder(self):
        """Test PDF file handling (returns placeholder)."""
        journey = Journey1SmartTemplates()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"fake pdf content")
            temp_path = f.name
        
        try:
            content, file_type = journey.extract_file_content(temp_path)
            assert "[PDF Document:" in content
            assert "PDF text extraction requires PyPDF2" in content
            assert file_type == ".pdf"
        finally:
            Path(temp_path).unlink()

    def test_extract_file_content_docx_placeholder(self):
        """Test DOCX file handling (returns placeholder)."""
        journey = Journey1SmartTemplates()
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(b"fake docx content")
            temp_path = f.name
        
        try:
            content, file_type = journey.extract_file_content(temp_path)
            assert "[Word Document:" in content
            assert "DOCX text extraction requires python-docx" in content
            assert file_type == ".docx"
        finally:
            Path(temp_path).unlink()

    def test_extract_file_content_csv(self):
        """Test extracting content from CSV files."""
        journey = Journey1SmartTemplates()
        
        csv_content = "name,age,city\nJohn,25,New York\nJane,30,San Francisco"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        try:
            content, file_type = journey.extract_file_content(temp_path)
            assert "CSV Data Structure Analysis" in content
            assert "John,25,New York" in content
            assert file_type == ".csv"
        finally:
            Path(temp_path).unlink()

    def test_extract_file_content_json(self):
        """Test extracting content from JSON files."""
        journey = Journey1SmartTemplates()
        
        json_data = {"name": "test", "value": 123, "items": ["a", "b", "c"]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name
        
        try:
            content, file_type = journey.extract_file_content(temp_path)
            assert "JSON Data Structure Analysis" in content
            assert '"name": "test"' in content
            assert file_type == ".json"
        finally:
            Path(temp_path).unlink()

    def test_extract_file_content_unsupported(self):
        """Test handling unsupported file types."""
        journey = Journey1SmartTemplates()
        
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"unsupported content")
            temp_path = f.name
        
        try:
            content, file_type = journey.extract_file_content(temp_path)
            assert "[Unsupported file type: .xyz]" in content
            assert "Supported formats:" in content
            assert file_type == ".xyz"
        finally:
            Path(temp_path).unlink()

    def test_extract_file_content_file_not_found(self):
        """Test handling missing files."""
        journey = Journey1SmartTemplates()
        
        content, file_type = journey.extract_file_content("/nonexistent/file.txt")
        assert "[Error processing file]" in content
        assert "File not found or access denied" in content
        assert file_type == "error"

    def test_clean_text_content(self):
        """Test text content cleaning functionality."""
        journey = Journey1SmartTemplates()
        
        # Test with messy text content
        messy_text = "  Line 1  \n\n\n\n  Line 2  \n\t\tTabbed content\n   "
        cleaned = journey._clean_text_content(messy_text)
        
        assert cleaned == "Line 1\n\nLine 2\nTabbed content"
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")

    def test_clean_text_content_empty(self):
        """Test cleaning empty or whitespace-only content."""
        journey = Journey1SmartTemplates()
        
        assert journey._clean_text_content("") == ""
        assert journey._clean_text_content("   \n\t  ") == ""
        assert journey._clean_text_content("\n\n\n") == ""

    def test_process_csv_content(self):
        """Test CSV content processing."""
        journey = Journey1SmartTemplates()
        
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,SF"
        result = journey._process_csv_content(csv_content, "test.csv")
        
        assert "CSV Data Structure Analysis" in result
        assert "test.csv" in result
        assert "3 rows detected" in result
        assert "3 columns detected" in result
        assert csv_content in result

    def test_process_csv_content_malformed(self):
        """Test processing malformed CSV content."""
        journey = Journey1SmartTemplates()
        
        # Malformed CSV (inconsistent columns)
        malformed_csv = "name,age\nJohn,25,extra\nJane"
        result = journey._process_csv_content(malformed_csv, "bad.csv")
        
        assert "CSV Data Structure Analysis" in result
        assert "inconsistent column count" in result.lower()
        assert malformed_csv in result

    def test_process_json_content_valid(self):
        """Test processing valid JSON content."""
        journey = Journey1SmartTemplates()
        
        json_content = '{"name": "test", "items": [1, 2, 3], "nested": {"key": "value"}}'
        result = journey._process_json_content(json_content, "test.json")
        
        assert "JSON Data Structure Analysis" in result
        assert "test.json" in result
        assert "Valid JSON structure" in result
        assert "3 top-level keys" in result
        assert json_content in result

    def test_process_json_content_invalid(self):
        """Test processing invalid JSON content."""
        journey = Journey1SmartTemplates()
        
        invalid_json = '{"name": "test", "missing_quote: "value"}'
        result = journey._process_json_content(invalid_json, "bad.json")
        
        assert "JSON Data Structure Analysis" in result
        assert "Invalid JSON syntax" in result
        assert invalid_json in result

    def test_validate_file_size_valid(self):
        """Test file size validation for valid files."""
        journey = Journey1SmartTemplates()
        
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"small content")
            f.flush()
            
            is_valid, message = journey.validate_file_size(f.name)
            assert is_valid is True
            assert "File size is acceptable" in message

    def test_validate_file_size_too_large(self):
        """Test file size validation for oversized files."""
        journey = Journey1SmartTemplates()
        
        # Mock a large file
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 15 * 1024 * 1024  # 15MB
            
            is_valid, message = journey.validate_file_size("fake_large_file.txt")
            assert is_valid is False
            assert "File too large" in message
            assert "14.3 MB" in message

    def test_validate_file_size_not_found(self):
        """Test file size validation for missing files."""
        journey = Journey1SmartTemplates()
        
        is_valid, message = journey.validate_file_size("/nonexistent/file.txt")
        assert is_valid is False
        assert "File not found" in message

    def test_analyze_content_structure_code(self):
        """Test content structure analysis for code content."""
        journey = Journey1SmartTemplates()
        
        code_content = """
def hello_world():
    print("Hello, World!")
    
class TestClass:
    def method(self):
        return True
"""
        
        analysis = journey.analyze_content_structure(code_content)
        
        assert analysis["content_type"] == "code"
        assert analysis["line_count"] > 0
        assert analysis["has_functions"] is True
        assert analysis["has_classes"] is True
        assert "python" in analysis["detected_language"].lower()

    def test_analyze_content_structure_documentation(self):
        """Test content structure analysis for documentation."""
        journey = Journey1SmartTemplates()
        
        doc_content = """
# Main Title

## Section 1
This is documentation content.

## Section 2
More documentation with [links](http://example.com).

- List item 1
- List item 2
"""
        
        analysis = journey.analyze_content_structure(doc_content)
        
        assert analysis["content_type"] == "documentation"
        assert analysis["line_count"] > 0
        assert analysis["has_headings"] is True
        assert analysis["has_links"] is True
        assert analysis["has_lists"] is True

    def test_analyze_content_structure_data(self):
        """Test content structure analysis for data content."""
        journey = Journey1SmartTemplates()
        
        data_content = """
name,age,city
John,25,NYC
Jane,30,SF
Bob,35,LA
"""
        
        analysis = journey.analyze_content_structure(data_content)
        
        assert analysis["content_type"] == "data"
        assert analysis["line_count"] > 0
        assert analysis["has_structure"] is True

    def test_analyze_content_structure_mixed(self):
        """Test content structure analysis for mixed content."""
        journey = Journey1SmartTemplates()
        
        mixed_content = """
# Documentation

Some text content here.

```python
def example():
    return "code"
```

Regular paragraph text continues.
"""
        
        analysis = journey.analyze_content_structure(mixed_content)
        
        assert analysis["content_type"] == "mixed"
        assert analysis["line_count"] > 0
        assert analysis["has_code_blocks"] is True
        assert analysis["has_headings"] is True

    def test_get_file_metadata(self):
        """Test getting file metadata."""
        journey = Journey1SmartTemplates()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            metadata = journey.get_file_metadata(temp_path)
            
            assert metadata["name"] == Path(temp_path).name
            assert metadata["extension"] == ".txt"
            assert metadata["size"] > 0
            assert "created" in metadata
            assert "modified" in metadata
        finally:
            Path(temp_path).unlink()

    def test_get_file_metadata_not_found(self):
        """Test getting metadata for non-existent file."""
        journey = Journey1SmartTemplates()
        
        metadata = journey.get_file_metadata("/nonexistent/file.txt")
        
        assert metadata["error"] == "File not found"
        assert metadata["name"] == "file.txt"
        assert metadata["extension"] == ".txt"

    def test_create_breakdown_comprehensive(self):
        """Test creating comprehensive C.R.E.A.T.E. breakdown."""
        journey = Journey1SmartTemplates()
        
        input_text = "Create a Python function that calculates fibonacci numbers efficiently."
        
        breakdown = journey.create_breakdown(input_text)
        
        # Verify all C.R.E.A.T.E. components are present
        assert "context" in breakdown
        assert "request" in breakdown
        assert "examples" in breakdown
        assert "augmentations" in breakdown
        assert "tone_format" in breakdown
        assert "evaluation" in breakdown
        
        # Verify content quality
        assert len(breakdown["context"]) > 10
        assert len(breakdown["request"]) > 10
        assert "fibonacci" in breakdown["request"].lower()

    def test_create_breakdown_empty_input(self):
        """Test creating breakdown with empty input."""
        journey = Journey1SmartTemplates()
        
        breakdown = journey.create_breakdown("")
        
        # Should still return all components, but with generic content
        assert all(key in breakdown for key in ["context", "request", "examples", "augmentations", "tone_format", "evaluation"])
        assert "provide more specific input" in breakdown["request"].lower()

    def test_create_breakdown_with_file_context(self):
        """Test creating breakdown with file context."""
        journey = Journey1SmartTemplates()
        
        input_text = "Optimize this code for performance"
        file_sources = [
            {"name": "slow_function.py", "type": "python", "size": 1024, "content_preview": "def slow_function():\n    time.sleep(1)"}
        ]
        
        breakdown = journey.create_breakdown(input_text, file_sources=file_sources)
        
        assert "slow_function.py" in breakdown["context"]
        assert "python" in breakdown["context"].lower()
        assert "performance" in breakdown["request"].lower()

    def test_enhance_prompt_basic(self):
        """Test basic prompt enhancement."""
        journey = Journey1SmartTemplates()
        
        original_prompt = "Write a sorting algorithm"
        breakdown = {
            "context": "Programming assistant role",
            "request": "Create efficient sorting algorithm",
            "examples": "Example: quicksort implementation",
            "augmentations": "Include time complexity analysis",
            "tone_format": "Technical and educational",
            "evaluation": "Verify correctness and efficiency"
        }
        
        enhanced = journey.enhance_prompt(original_prompt, breakdown)
        
        assert len(enhanced) > len(original_prompt)
        assert "sorting algorithm" in enhanced.lower()
        assert "context" in enhanced.lower() or "role" in enhanced.lower()

    def test_enhance_prompt_with_file_sources(self):
        """Test prompt enhancement with file sources."""
        journey = Journey1SmartTemplates()
        
        original_prompt = "Review this code"
        breakdown = {
            "context": "Code reviewer",
            "request": "Analyze code quality",
            "examples": "Point out issues",
            "augmentations": "Include suggestions",
            "tone_format": "Constructive feedback",
            "evaluation": "Check for best practices"
        }
        file_sources = [{"name": "code.py", "content": "def example(): pass"}]
        
        enhanced = journey.enhance_prompt(original_prompt, breakdown, file_sources)
        
        assert "code.py" in enhanced
        assert len(enhanced) > len(original_prompt)

    def test_copy_to_clipboard_simulation(self):
        """Test clipboard copying simulation."""
        journey = Journey1SmartTemplates()
        
        # Since we can't actually test clipboard in unit tests,
        # we'll test the method exists and returns expected format
        test_content = "Test content for clipboard"
        
        # This would normally copy to clipboard, but we can't test that
        # Instead, verify the method exists and handles the input
        try:
            result = journey.copy_to_clipboard(test_content)
            # Method should handle the operation gracefully
            assert result is None or isinstance(result, str)
        except Exception as e:
            # Expected in test environment without clipboard access
            assert "clipboard" in str(e).lower() or "not supported" in str(e).lower()

    def test_get_supported_formats(self):
        """Test getting supported file formats."""
        journey = Journey1SmartTemplates()
        
        formats = journey.get_supported_formats()
        
        assert isinstance(formats, list)
        assert ".txt" in formats
        assert ".md" in formats
        assert len(formats) == len(journey.supported_file_types)

    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        journey = Journey1SmartTemplates()
        
        # Small content
        small_content = "Short text"
        small_time = journey.estimate_processing_time(small_content)
        assert small_time > 0
        assert small_time < 10  # Should be quick
        
        # Large content
        large_content = "Large text content. " * 1000
        large_time = journey.estimate_processing_time(large_content)
        assert large_time > small_time  # Should take longer

    def test_validate_input_content(self):
        """Test input content validation."""
        journey = Journey1SmartTemplates()
        
        # Valid content
        valid_content = "This is valid input content for processing."
        is_valid, message = journey.validate_input_content(valid_content)
        assert is_valid is True
        assert "valid" in message.lower()
        
        # Empty content
        is_valid, message = journey.validate_input_content("")
        assert is_valid is False
        assert "empty" in message.lower()
        
        # Very long content
        long_content = "x" * 100000
        is_valid, message = journey.validate_input_content(long_content)
        assert is_valid is False
        assert "too long" in message.lower()

    def test_error_handling_robustness(self):
        """Test error handling across different scenarios."""
        journey = Journey1SmartTemplates()
        
        # Test with None inputs
        try:
            journey.analyze_content_structure(None)
        except (TypeError, AttributeError):
            pass  # Expected behavior
        
        # Test with invalid file paths
        content, file_type = journey.extract_file_content("")
        assert "Error processing file" in content
        assert file_type == "error"
        
        # Test breakdown with None
        breakdown = journey.create_breakdown(None)
        assert all(isinstance(v, str) for v in breakdown.values())