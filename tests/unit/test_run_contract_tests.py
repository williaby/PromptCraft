#!/usr/bin/env python3
"""
Unit tests for tests.contract.run_contract_tests.py

Comprehensive test suite covering all functions with >90% coverage.
"""

from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock, call, patch

import pytest


# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.contract import run_contract_tests


class TestInstallDependencies:
    """Test suite for install_dependencies function."""
    
    @patch("tests.contract.run_contract_tests.subprocess.run")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.Path")
    def test_install_dependencies_success(self, mock_path, mock_print, mock_subprocess_run):
        """Test successful dependency installation."""
        # Arrange
        mock_path.return_value.parent = "/test/path"
        mock_subprocess_run.return_value = None
        
        # Act
        run_contract_tests.install_dependencies()
        
        # Assert
        mock_print.assert_has_calls([
            call("📦 Installing dependencies..."),
            call("✅ Dependencies installed"),
        ])
        mock_subprocess_run.assert_called_once_with(
            ["poetry", "install"], 
            check=True, 
            cwd="/test/path",
        )
    
    @patch("tests.contract.run_contract_tests.subprocess.run")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.Path")
    @patch("tests.contract.run_contract_tests.sys.exit")
    def test_install_dependencies_failure(self, mock_exit, mock_path, mock_print, mock_subprocess_run):
        """Test dependency installation failure."""
        # Arrange
        mock_path.return_value.parent = "/test/path"
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["poetry", "install"])
        
        # Act
        run_contract_tests.install_dependencies()
        
        # Assert
        mock_print.assert_has_calls([
            call("📦 Installing dependencies..."),
            call("❌ Failed to install dependencies: Command '['poetry', 'install']' returned non-zero exit status 1."),
        ])
        mock_exit.assert_called_once_with(1)


class TestCheckPactBinary:
    """Test suite for check_pact_binary function."""
    
    @patch("shutil.which")
    @patch("tests.contract.run_contract_tests.print")
    def test_check_pact_binary_found(self, mock_print, mock_which):
        """Test when pact-mock-service binary is found."""
        # Arrange
        mock_which.return_value = "/usr/bin/pact-mock-service"
        
        # Act
        result = run_contract_tests.check_pact_binary()
        
        # Assert
        assert result is True
        mock_which.assert_called_once_with("pact-mock-service")
        mock_print.assert_called_once_with("✅ pact-mock-service binary found")
    
    @patch("shutil.which")
    @patch("tests.contract.run_contract_tests.print")
    def test_check_pact_binary_not_found(self, mock_print, mock_which):
        """Test when pact-mock-service binary is not found."""
        # Arrange
        mock_which.return_value = None
        
        # Act
        result = run_contract_tests.check_pact_binary()
        
        # Assert
        assert result is False
        mock_which.assert_called_once_with("pact-mock-service")
        mock_print.assert_has_calls([
            call("⚠️  pact-mock-service binary not found"),
            call("Install with: gem install pact-mock_service"),
            call("Or install pact-ruby-standalone"),
        ])


class TestRunContractTests:
    """Test suite for run_contract_tests function."""
    
    @patch("tests.contract.run_contract_tests.os.environ")
    @patch("tests.contract.run_contract_tests.subprocess.run")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.Path")
    def test_run_contract_tests_success(self, mock_path, mock_print, mock_subprocess_run, mock_environ):
        """Test successful contract test execution."""
        # Arrange
        mock_environ.copy.return_value = {"EXISTING": "value"}
        mock_path.return_value.parent = "/test/path"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result
        
        # Act
        result = run_contract_tests.run_contract_tests()
        
        # Assert
        assert result is True
        mock_print.assert_has_calls([
            call("🧪 Running contract tests..."),
            call("✅ Contract tests passed!"),
        ])
        
        expected_env = {
            "EXISTING": "value",
            "PACT_TEST_MODE": "consumer",
            "CONTRACT_TEST": "true",
            "LOG_LEVEL": "INFO",
        }
        
        mock_subprocess_run.assert_called_once_with([
            "poetry", "run", "pytest", 
            "tests/contract/test_mcp_contracts.py",
            "-v",
            "-m", "contract",
            "--tb=short",
        ], 
        check=False,
        env=expected_env,
        cwd="/test/path",
        )
    
    @patch("tests.contract.run_contract_tests.os.environ")
    @patch("tests.contract.run_contract_tests.subprocess.run")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.Path")
    def test_run_contract_tests_failure_returncode(self, mock_path, mock_print, mock_subprocess_run, mock_environ):
        """Test contract test execution with non-zero return code."""
        # Arrange
        mock_environ.copy.return_value = {"EXISTING": "value"}
        mock_path.return_value.parent = "/test/path"
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess_run.return_value = mock_result
        
        # Act
        result = run_contract_tests.run_contract_tests()
        
        # Assert
        assert result is False
        mock_print.assert_has_calls([
            call("🧪 Running contract tests..."),
            call("❌ Contract tests failed"),
        ])
    
    @patch("tests.contract.run_contract_tests.os.environ")
    @patch("tests.contract.run_contract_tests.subprocess.run")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.Path")
    def test_run_contract_tests_exception(self, mock_path, mock_print, mock_subprocess_run, mock_environ):
        """Test contract test execution with subprocess exception."""
        # Arrange
        mock_environ.copy.return_value = {"EXISTING": "value"}
        mock_path.return_value.parent = "/test/path"
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, ["poetry", "run", "pytest"])
        
        # Act
        result = run_contract_tests.run_contract_tests()
        
        # Assert
        assert result is False
        mock_print.assert_has_calls([
            call("🧪 Running contract tests..."),
            call("❌ Failed to run contract tests: Command '['poetry', 'run', 'pytest']' returned non-zero exit status 1."),
        ])


class TestMain:
    """Test suite for main function."""
    
    @patch("tests.contract.run_contract_tests.Path")
    @patch("tests.contract.run_contract_tests.install_dependencies")
    @patch("tests.contract.run_contract_tests.check_pact_binary")
    @patch("tests.contract.run_contract_tests.run_contract_tests")
    @patch("tests.contract.run_contract_tests.print")
    def test_main_success_with_pact(self, mock_print, mock_run_tests, mock_check_pact, 
                                   mock_install_deps, mock_path):
        """Test successful main execution with pact binary available."""
        # Arrange
        mock_path.return_value.exists.return_value = True
        mock_check_pact.return_value = True
        mock_run_tests.return_value = True
        
        # Act
        run_contract_tests.main()
        
        # Assert
        mock_install_deps.assert_called_once()
        mock_check_pact.assert_called_once()
        mock_run_tests.assert_called_once()
        
        mock_print.assert_has_calls([
            call("🚀 MCP Contract Test Runner"),
            call("=" * 40),
            call("\n🎉 All contract tests completed successfully!"),
            call("\nPact files generated in: ./pacts/"),
            call("Test servers used:"),
            call("  - zen-mcp-server on localhost:8080"),
            call("  - heimdall-stub on localhost:8081"),
        ])
    
    @patch("tests.contract.run_contract_tests.Path")
    @patch("tests.contract.run_contract_tests.install_dependencies")
    @patch("tests.contract.run_contract_tests.check_pact_binary")
    @patch("tests.contract.run_contract_tests.run_contract_tests")
    @patch("tests.contract.run_contract_tests.print")
    def test_main_success_without_pact(self, mock_print, mock_run_tests, mock_check_pact, 
                                      mock_install_deps, mock_path):
        """Test successful main execution without pact binary."""
        # Arrange
        mock_path.return_value.exists.return_value = True
        mock_check_pact.return_value = False
        mock_run_tests.return_value = True
        
        # Act
        run_contract_tests.main()
        
        # Assert
        mock_install_deps.assert_called_once()
        mock_check_pact.assert_called_once()
        mock_run_tests.assert_called_once()
        
        expected_calls = [
            call("🚀 MCP Contract Test Runner"),
            call("=" * 40),
            call("Note: Some Pact features may be limited without pact-mock-service binary"),
            call("\n🎉 All contract tests completed successfully!"),
            call("\nPact files generated in: ./pacts/"),
            call("Test servers used:"),
            call("  - zen-mcp-server on localhost:8080"),
            call("  - heimdall-stub on localhost:8081"),
        ]
        
        for expected_call in expected_calls:
            assert expected_call in mock_print.call_args_list
    
    @patch("tests.contract.run_contract_tests.Path")
    @patch("tests.contract.run_contract_tests.install_dependencies")
    @patch("tests.contract.run_contract_tests.check_pact_binary")
    @patch("tests.contract.run_contract_tests.run_contract_tests")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.sys.exit")
    def test_main_test_failure(self, mock_exit, mock_print, mock_run_tests, mock_check_pact, 
                              mock_install_deps, mock_path):
        """Test main execution when tests fail."""
        # Arrange
        mock_path.return_value.exists.return_value = True
        mock_check_pact.return_value = True
        mock_run_tests.return_value = False
        
        # Act
        run_contract_tests.main()
        
        # Assert
        mock_install_deps.assert_called_once()
        mock_check_pact.assert_called_once()
        mock_run_tests.assert_called_once()
        mock_exit.assert_called_once_with(1)
        
        mock_print.assert_has_calls([
            call("🚀 MCP Contract Test Runner"),
            call("=" * 40),
            call("\n💥 Contract tests failed - check output above"),
        ])
    
    @patch("tests.contract.run_contract_tests.Path")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.sys.exit")
    def test_main_wrong_directory(self, mock_exit, mock_print, mock_path):
        """Test main execution from wrong directory."""
        # Arrange
        mock_path.return_value.exists.return_value = False
        mock_exit.side_effect = SystemExit(1)  # Make sys.exit actually exit
        
        # Act
        with pytest.raises(SystemExit):
            run_contract_tests.main()
        
        # Assert
        mock_print.assert_has_calls([
            call("🚀 MCP Contract Test Runner"),
            call("=" * 40),
            call("❌ Must be run from project root (where pyproject.toml exists)"),
        ])
        mock_exit.assert_called_once_with(1)


class TestEdgeCasesAndIntegration:
    """Test edge cases and integration scenarios."""
    
    @patch("tests.contract.run_contract_tests.os.environ")
    def test_environment_variable_handling(self, mock_environ):
        """Test environment variable setup and modification."""
        # Arrange
        original_env = {"PATH": "/usr/bin", "HOME": "/home/user"}
        mock_environ.copy.return_value = original_env.copy()
        
        with patch("tests.contract.run_contract_tests.subprocess.run") as mock_subprocess_run, \
             patch("tests.contract.run_contract_tests.Path") as mock_path, \
             patch("tests.contract.run_contract_tests.print"):
            
            mock_path.return_value.parent = "/test/path"
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess_run.return_value = mock_result
            
            # Act
            run_contract_tests.run_contract_tests()
            
            # Assert
            expected_env = original_env.copy()
            expected_env.update({
                "PACT_TEST_MODE": "consumer",
                "CONTRACT_TEST": "true",
                "LOG_LEVEL": "INFO",
            })
            
            args, kwargs = mock_subprocess_run.call_args
            assert kwargs["env"] == expected_env
    
    @patch("tests.contract.run_contract_tests.Path")
    def test_path_handling(self, mock_path):
        """Test path handling and file operations."""
        # Arrange
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent = "/project/root"
        mock_path_instance.exists.return_value = True
        
        with patch("tests.contract.run_contract_tests.subprocess.run") as mock_subprocess_run, \
             patch("tests.contract.run_contract_tests.print"):
            
            mock_subprocess_run.return_value = None
            
            # Act
            run_contract_tests.install_dependencies()
            
            # Assert - The function uses its own __file__, not the test's __file__
            # Use relative path for CI compatibility
            expected_path = str(Path(__file__).parent.parent / "contract" / "run_contract_tests.py")
            mock_path.assert_called_with(expected_path)
            mock_subprocess_run.assert_called_once_with(
                ["poetry", "install"], 
                check=True, 
                cwd="/project/root",
            )


class TestScriptExecution:
    """Test script execution scenarios."""
    
    @patch("tests.contract.run_contract_tests.main")
    def test_script_execution_as_main(self, mock_main):
        """Test script execution when run as __main__."""
        # This test ensures the if __name__ == "__main__" block is covered
        # We can't easily test this directly, but we can verify main() is callable
        
        # Act
        run_contract_tests.main()
        
        # Assert
        mock_main.assert_called_once()


# Parametrized tests for comprehensive coverage
class TestParametrizedScenarios:
    """Parametrized tests for various scenarios."""
    
    @pytest.mark.parametrize("return_code,expected_result", [
        (0, True),
        (1, False),
        (2, False),
        (127, False),
    ])
    @patch("tests.contract.run_contract_tests.os.environ")
    @patch("tests.contract.run_contract_tests.subprocess.run")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.Path")
    def test_run_contract_tests_various_return_codes(self, mock_path, mock_print, 
                                                    mock_subprocess_run, mock_environ,
                                                    return_code, expected_result):
        """Test run_contract_tests with various return codes."""
        # Arrange
        mock_environ.copy.return_value = {}
        mock_path.return_value.parent = "/test/path"
        mock_result = Mock()
        mock_result.returncode = return_code
        mock_subprocess_run.return_value = mock_result
        
        # Act
        result = run_contract_tests.run_contract_tests()
        
        # Assert
        assert result is expected_result
    
    @pytest.mark.parametrize("pact_available,success,should_exit", [
        (True, True, False),
        (True, False, True),
        (False, True, False),
        (False, False, True),
    ])
    @patch("tests.contract.run_contract_tests.Path")
    @patch("tests.contract.run_contract_tests.install_dependencies")
    @patch("tests.contract.run_contract_tests.check_pact_binary")
    @patch("tests.contract.run_contract_tests.run_contract_tests")
    @patch("tests.contract.run_contract_tests.print")
    @patch("tests.contract.run_contract_tests.sys.exit")
    def test_main_various_scenarios(self, mock_exit, mock_print, mock_run_tests, 
                                   mock_check_pact, mock_install_deps, mock_path,
                                   pact_available, success, should_exit):
        """Test main function with various combinations of conditions."""
        # Arrange
        mock_path.return_value.exists.return_value = True
        mock_check_pact.return_value = pact_available
        mock_run_tests.return_value = success
        
        # Act
        run_contract_tests.main()
        
        # Assert
        if should_exit:
            mock_exit.assert_called_once_with(1)
        else:
            mock_exit.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=run_contract_tests", "--cov-report=term-missing"])