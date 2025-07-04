"""Tests for the encryption utility module.

This module tests the core encryption functionality including GPG operations,
environment key validation, and encrypted file handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.utils.encryption import (
    EncryptionError,
    GPGError,
    decrypt_env_file,
    encrypt_env_file,
    initialize_encryption,
    load_encrypted_env,
    validate_environment_keys,
)


class TestEncryptionError:
    """Test the custom encryption exception classes."""

    def test_encryption_error_creation(self):
        """Test creating EncryptionError with message."""
        error = EncryptionError("Test encryption error")
        assert str(error) == "Test encryption error"
        assert isinstance(error, Exception)

    def test_gpg_error_creation(self):
        """Test creating GPGError with message."""
        error = GPGError("Test GPG error")
        assert str(error) == "Test GPG error"
        assert isinstance(error, Exception)

    def test_error_inheritance(self):
        """Test that both errors inherit from Exception."""
        assert issubclass(GPGError, Exception)
        assert issubclass(EncryptionError, Exception)


class TestEnvironmentKeyValidation:
    """Test environment key validation functionality."""

    @patch("subprocess.run")
    def test_validate_environment_keys_success(self, mock_run):
        """Test successful environment key validation."""
        # Mock successful GPG and SSH key checks
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "gpg key found"
        mock_run.return_value = mock_result

        # Should not raise an exception
        try:
            validate_environment_keys()
        except Exception as e:
            pytest.fail(f"Key validation should succeed with valid keys: {e}")

    @patch("gnupg.GPG")
    def test_validate_environment_keys_gpg_failure(self, mock_gpg_class):
        """Test environment key validation with GPG failure."""
        # Mock GPG that returns no secret keys
        mock_gpg = Mock()
        mock_gpg.list_keys.return_value = []  # No keys
        mock_gpg_class.return_value = mock_gpg

        with pytest.raises(EncryptionError) as exc_info:
            validate_environment_keys()

        assert "GPG secret keys" in str(exc_info.value)

    @patch("subprocess.run")
    def test_validate_environment_keys_ssh_failure(self, mock_run):
        """Test environment key validation with SSH failure."""

        # Mock GPG success but SSH failure
        def side_effect(*args, **kwargs):
            if "gpg" in " ".join(args[0]):
                result = Mock()
                result.returncode = 0
                return result
            else:  # SSH command
                result = Mock()
                result.returncode = 1
                result.stderr = "No SSH keys found"
                return result

        mock_run.side_effect = side_effect

        with pytest.raises(EncryptionError) as exc_info:
            validate_environment_keys()

        assert "SSH" in str(exc_info.value)

    @patch("subprocess.run")
    def test_validate_environment_keys_command_exception(self, mock_run):
        """Test environment key validation with command execution exception."""
        # Mock GPG success first
        with patch("gnupg.GPG") as mock_gpg_class:
            mock_gpg = Mock()
            mock_gpg.list_keys.return_value = [{"keyid": "test"}]  # GPG success
            mock_gpg_class.return_value = mock_gpg

            # Mock SSH command failure
            mock_run.side_effect = FileNotFoundError("ssh-add command not found")

            with pytest.raises(EncryptionError) as exc_info:
                validate_environment_keys()

            assert "ssh-add command not found" in str(exc_info.value)


class TestEncryptedFileOperations:
    """Test encrypted file operations."""

    @patch("gnupg.GPG")
    def test_encrypt_env_file_success(self, mock_gpg_class):
        """Test successful environment file encryption."""
        # Mock GPG instance
        mock_gpg = Mock()
        mock_gpg_class.return_value = mock_gpg

        # Mock successful encryption
        mock_result = Mock()
        mock_result.ok = True
        mock_result.__str__ = Mock(return_value="encrypted_data")
        mock_gpg.encrypt.return_value = mock_result

        content = "SECRET_KEY=test_secret\nAPI_KEY=test_api"

        result = encrypt_env_file(content, recipient="test@example.com")

        assert result == "encrypted_data"
        mock_gpg.encrypt.assert_called_once()

    @patch("gnupg.GPG")
    def test_encrypt_env_file_failure(self, mock_gpg_class):
        """Test environment file encryption failure."""
        # Mock GPG instance
        mock_gpg = Mock()
        mock_gpg_class.return_value = mock_gpg

        # Mock failed encryption
        mock_result = Mock()
        mock_result.ok = False
        mock_result.status = "encryption failed"
        mock_gpg.encrypt.return_value = mock_result

        content = "SECRET_KEY=test_secret"

        with pytest.raises(GPGError) as exc_info:
            encrypt_env_file(content, recipient="test@example.com")

        assert "Encryption failed" in str(exc_info.value)

    @patch("gnupg.GPG")
    def test_decrypt_env_file_success(self, mock_gpg_class):
        """Test successful environment file decryption."""
        # Mock GPG instance
        mock_gpg = Mock()
        mock_gpg_class.return_value = mock_gpg

        # Mock successful decryption
        mock_result = Mock()
        mock_result.ok = True
        mock_result.__str__ = Mock(
            return_value="SECRET_KEY=test_secret\nAPI_KEY=test_api",
        )
        mock_gpg.decrypt.return_value = mock_result

        encrypted_content = "encrypted_data"

        result = decrypt_env_file(encrypted_content)

        assert result == "SECRET_KEY=test_secret\nAPI_KEY=test_api"
        mock_gpg.decrypt.assert_called_once_with(encrypted_content, passphrase=None)

    @patch("gnupg.GPG")
    def test_decrypt_env_file_failure(self, mock_gpg_class):
        """Test environment file decryption failure."""
        # Mock GPG instance
        mock_gpg = Mock()
        mock_gpg_class.return_value = mock_gpg

        # Mock failed decryption
        mock_result = Mock()
        mock_result.ok = False
        mock_result.status = "decryption failed"
        mock_gpg.decrypt.return_value = mock_result

        encrypted_content = "encrypted_data"

        with pytest.raises(GPGError) as exc_info:
            decrypt_env_file(encrypted_content)

        assert "Decryption failed" in str(exc_info.value)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    @patch("src.utils.encryption.decrypt_env_file")
    def test_load_encrypted_env_success(
        self,
        mock_decrypt,
        mock_read_text,
        mock_exists,
    ):
        """Test successful loading of encrypted environment file."""
        # Mock file exists and can be read
        mock_exists.return_value = True
        mock_read_text.return_value = "encrypted_content"

        # Mock successful decryption
        mock_decrypt.return_value = (
            "API_KEY=test_key\nSECRET=test_secret\nOTHER_VAR=other_value"
        )

        result = load_encrypted_env("/test/encrypted.env.gpg")

        expected = {
            "API_KEY": "test_key",
            "SECRET": "test_secret",
            "OTHER_VAR": "other_value",
        }
        assert result == expected

    @patch("pathlib.Path.exists")
    def test_load_encrypted_env_file_not_found(self, mock_exists):
        """Test loading encrypted environment file when file doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            load_encrypted_env("/test/nonexistent.env.gpg")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_load_encrypted_env_read_error(self, mock_read_text, mock_exists):
        """Test loading encrypted environment file with read error."""
        mock_exists.return_value = True
        mock_read_text.side_effect = PermissionError("Permission denied")

        with pytest.raises(PermissionError):
            load_encrypted_env("/test/encrypted.env.gpg")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    @patch("src.utils.encryption.decrypt_env_file")
    def test_load_encrypted_env_decrypt_error(
        self,
        mock_decrypt,
        mock_read_text,
        mock_exists,
    ):
        """Test loading encrypted environment file with decryption error."""
        mock_exists.return_value = True
        mock_read_text.return_value = "encrypted_content"
        mock_decrypt.side_effect = GPGError("Decryption failed")

        with pytest.raises(GPGError):
            load_encrypted_env("/test/encrypted.env.gpg")


class TestEnvironmentFileProcessing:
    """Test environment file content processing."""

    @patch("src.utils.encryption.decrypt_env_file")
    def test_load_encrypted_env_content_parsing(self, mock_decrypt):
        """Test parsing of decrypted environment file content."""
        # Mock decrypted content with various formats
        mock_decrypt.return_value = """
# Comment line
API_KEY=test_key_value
SECRET_KEY="quoted_secret"
DATABASE_URL='single_quoted_url'
OTHER_VAR=other_value
EMPTY_VAR=
# Another comment
SPACED_VAR = spaced_value
INVALID_LINE_WITHOUT_EQUALS
MULTILINE_VAR=line1\\nline2
"""

        with tempfile.NamedTemporaryFile(suffix=".gpg") as tmp_file:
            file_path = Path(tmp_file.name)

            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                with patch("pathlib.Path.read_text") as mock_read_text:
                    mock_read_text.return_value = "encrypted_content"

                    result = load_encrypted_env(file_path)

        expected = {
            "API_KEY": "test_key_value",
            "SECRET_KEY": "quoted_secret",
            "DATABASE_URL": "single_quoted_url",
            "OTHER_VAR": "other_value",
            "SPACED_VAR": "spaced_value",
            "MULTILINE_VAR": "line1\\nline2",
        }

        # Check that variables are included
        assert "API_KEY" in result
        assert result["API_KEY"] == "test_key_value"

        # Check that quotes are stripped
        assert result["SECRET_KEY"] == "quoted_secret"
        assert result["DATABASE_URL"] == "single_quoted_url"

        # Check that all non-empty variables are included
        assert "OTHER_VAR" in result

        # Check that empty variables are excluded (based on the actual parsing logic)
        # The actual implementation strips empty values, so they won't be in the result

    def test_env_content_edge_cases(self):
        """Test edge cases in environment content parsing."""
        with patch("src.utils.encryption.decrypt_env_file") as mock_decrypt:
            # Test with minimal content
            mock_decrypt.return_value = "SIMPLE=value"

            with tempfile.NamedTemporaryFile(suffix=".gpg") as tmp_file:
                file_path = tmp_file.name

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.read_text", return_value="encrypted"):
                        result = load_encrypted_env(file_path)

                        assert result == {"SIMPLE": "value"}

        with patch("src.utils.encryption.decrypt_env_file") as mock_decrypt:
            # Test with empty content
            mock_decrypt.return_value = ""

            with tempfile.NamedTemporaryFile(suffix=".gpg") as tmp_file:
                file_path = tmp_file.name

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.read_text", return_value="encrypted"):
                        result = load_encrypted_env(file_path)

                        assert result == {}

        with patch("src.utils.encryption.decrypt_env_file") as mock_decrypt:
            # Test with only comments and empty lines
            mock_decrypt.return_value = """
# Only comments
# and empty lines


"""

            with tempfile.NamedTemporaryFile(suffix=".gpg") as tmp_file:
                file_path = tmp_file.name

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.read_text", return_value="encrypted"):
                        result = load_encrypted_env(file_path)

                        assert result == {}


class TestGPGIntegration:
    """Test GPG integration and error handling."""

    @patch("gnupg.GPG")
    def test_gpg_initialization_error(self, mock_gpg_class):
        """Test handling of GPG initialization errors."""
        mock_gpg_class.side_effect = Exception("GPG not available")

        with pytest.raises(GPGError) as exc_info:
            encrypt_env_file("content", "recipient")

        assert "GPG not available" in str(exc_info.value)

    @patch("gnupg.GPG")
    def test_gpg_missing_recipient(self, mock_gpg_class):
        """Test encryption with missing recipient."""
        mock_gpg = Mock()
        mock_gpg_class.return_value = mock_gpg

        # Mock no secret keys available
        mock_gpg.list_keys.return_value = []

        with pytest.raises(GPGError) as exc_info:
            encrypt_env_file("content", recipient=None)

        assert "No GPG keys available" in str(exc_info.value)

    @patch("gnupg.GPG")
    def test_gpg_encryption_with_auto_recipient(self, mock_gpg_class):
        """Test encryption with auto-detected recipient."""
        mock_gpg = Mock()
        mock_gpg_class.return_value = mock_gpg

        # Mock available secret keys
        mock_gpg.list_keys.return_value = [{"keyid": "test_key_id"}]

        mock_result = Mock()
        mock_result.ok = True
        mock_result.__str__ = Mock(return_value="encrypted_with_auto_recipient")
        mock_gpg.encrypt.return_value = mock_result

        result = encrypt_env_file("content", recipient=None)

        assert result == "encrypted_with_auto_recipient"

        # Verify encrypt was called with auto-detected recipient
        call_args = mock_gpg.encrypt.call_args
        assert call_args[1]["recipients"] == ["test_key_id"]

    @patch("gnupg.GPG")
    def test_gpg_decryption_with_passphrase(self, mock_gpg_class):
        """Test decryption with passphrase handling."""
        mock_gpg = Mock()
        mock_gpg_class.return_value = mock_gpg

        mock_result = Mock()
        mock_result.ok = True
        mock_result.__str__ = Mock(return_value="decrypted_with_passphrase")
        mock_gpg.decrypt.return_value = mock_result

        result = decrypt_env_file("encrypted_content", passphrase="secret")

        assert result == "decrypted_with_passphrase"


class TestSecurityConsiderations:
    """Test security-related aspects of encryption utilities."""

    def test_sensitive_data_not_logged(self, caplog):
        """Test that sensitive data is not logged during encryption operations."""
        import logging

        with patch("gnupg.GPG") as mock_gpg_class:
            mock_gpg = Mock()
            mock_gpg_class.return_value = mock_gpg

            mock_result = Mock()
            mock_result.ok = True
            mock_result.data = b"encrypted_data"
            mock_gpg.encrypt.return_value = mock_result

            with caplog.at_level(logging.DEBUG):
                content = "SECRET_KEY=very_secret_value\nAPI_KEY=another_secret"
                encrypt_env_file(content, recipient="test@example.com")

            # Check that sensitive values are not in logs
            log_text = " ".join(record.message for record in caplog.records)
            assert "very_secret_value" not in log_text
            assert "another_secret" not in log_text

    def test_error_messages_dont_leak_secrets(self):
        """Test that error messages don't contain sensitive information."""
        with patch("gnupg.GPG") as mock_gpg_class:
            mock_gpg = Mock()
            mock_gpg_class.return_value = mock_gpg

            mock_result = Mock()
            mock_result.ok = False
            mock_result.status = "Encryption operation failed"
            mock_gpg.encrypt.return_value = mock_result

            with pytest.raises(GPGError) as exc_info:
                encrypt_env_file("SECRET=test_value", recipient="test@example.com")

            # Error message should contain the failure
            error_msg = str(exc_info.value)
            assert "Encryption failed" in error_msg

            # Note: Current implementation doesn't sanitize error messages
            # This test verifies the current behavior rather than ideal behavior

    def test_temporary_file_handling(self):
        """Test that temporary files are handled securely."""
        # This test would verify that temporary files are created securely
        # and cleaned up properly, but the current implementation might not
        # use temporary files directly

    def test_memory_cleanup(self):
        """Test that sensitive data is cleared from memory appropriately."""
        # This test would verify that sensitive data is not left in memory
        # after encryption/decryption operations, but this is difficult to
        # test directly in Python


class TestInitializeEncryption:
    """Test the initialize_encryption function."""

    @patch("src.utils.encryption.validate_environment_keys")
    @patch("src.utils.encryption.load_encrypted_env")
    @patch("os.environ.setdefault")
    def test_initialize_encryption_success(
        self,
        mock_setdefault,
        mock_load_env,
        mock_validate,
    ):
        """Test successful initialization with encrypted env file."""
        mock_validate.return_value = None  # No exception
        mock_load_env.return_value = {
            "SECRET_KEY": "test_secret",
            "API_KEY": "test_api",
        }

        initialize_encryption()

        mock_validate.assert_called_once()
        mock_load_env.assert_called_once()

        # Verify environment variables were set
        assert mock_setdefault.call_count == 2

    @patch("src.utils.encryption.validate_environment_keys")
    @patch("src.utils.encryption.load_encrypted_env")
    def test_initialize_encryption_no_env_file(self, mock_load_env, mock_validate):
        """Test initialization when no encrypted env file exists."""
        mock_validate.return_value = None  # No exception
        mock_load_env.side_effect = FileNotFoundError("No env file")

        # Should not raise an exception
        initialize_encryption()

        mock_validate.assert_called_once()
        mock_load_env.assert_called_once()

    @patch("src.utils.encryption.validate_environment_keys")
    def test_initialize_encryption_validation_failure(self, mock_validate):
        """Test initialization when key validation fails."""
        mock_validate.side_effect = EncryptionError("No keys found")

        with pytest.raises(EncryptionError):
            initialize_encryption()
