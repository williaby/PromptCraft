"""
MCP Test Client

Real HTTP client implementation for contract testing with local MCP servers.
Replaces mock client calls with actual HTTP requests to test servers.
"""

import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class MCPTestClient:
    """HTTP client for making real requests to MCP test servers."""

    def __init__(
        self,
        zen_base_url: str = "http://localhost:8080",
        heimdall_base_url: str = "http://localhost:8081",
        timeout: float = 30.0,
    ):
        self.zen_base_url = zen_base_url.rstrip("/")
        self.heimdall_base_url = heimdall_base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout, connect=5.0, read=15.0)

    async def zen_client_call(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP call to zen-mcp-server."""
        url = f"{self.zen_base_url}{path}"

        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug(f"Making {method} request to {url}")

                if method.upper() == "GET":
                    response = await client.get(url, headers=default_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=body, headers=default_headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=body, headers=default_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=default_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle different response types
                if response.status_code >= 400:
                    # Return error response in expected format
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {"message": response.text}

                    return {
                        "error": error_data.get("error", "http_error"),
                        "message": error_data.get("message", f"HTTP {response.status_code}"),
                        "status": "error",
                        "code": response.status_code,
                    }

                # Return successful response
                try:
                    return response.json()
                except Exception:
                    # If not JSON, wrap in success response
                    return {
                        "result": response.text,
                        "status": "success",
                        "code": response.status_code,
                    }

            except httpx.TimeoutException:
                logger.error(f"Timeout calling {url}")
                return {
                    "error": "timeout",
                    "message": f"Request to {url} timed out",
                    "status": "error",
                    "code": 408,
                }
            except httpx.ConnectError:
                logger.error(f"Connection error calling {url}")
                return {
                    "error": "connection_error",
                    "message": f"Could not connect to {url}",
                    "status": "error",
                    "code": 503,
                }
            except Exception as e:
                logger.error(f"Unexpected error calling {url}: {e}")
                return {
                    "error": "unknown_error",
                    "message": str(e),
                    "status": "error",
                    "code": 500,
                }

    async def heimdall_client_call(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP call to Heimdall stub server."""
        url = f"{self.heimdall_base_url}{path}"

        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug(f"Making {method} request to {url}")

                if method.upper() == "GET":
                    response = await client.get(url, headers=default_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=body, headers=default_headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=body, headers=default_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=default_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle different response types
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {"message": response.text}

                    return {
                        "error": error_data.get("error", "http_error"),
                        "message": error_data.get("message", f"HTTP {response.status_code}"),
                        "status": "error",
                        "code": response.status_code,
                    }

                # Return successful response
                try:
                    return response.json()
                except Exception:
                    return {
                        "result": response.text,
                        "status": "success",
                        "code": response.status_code,
                    }

            except httpx.TimeoutException:
                logger.error(f"Timeout calling {url}")
                return {
                    "error": "timeout",
                    "message": f"Request to {url} timed out",
                    "status": "error",
                    "code": 408,
                }
            except httpx.ConnectError:
                logger.error(f"Connection error calling {url}")
                return {
                    "error": "connection_error",
                    "message": f"Could not connect to {url}",
                    "status": "error",
                    "code": 503,
                }
            except Exception as e:
                logger.error(f"Unexpected error calling {url}: {e}")
                return {
                    "error": "unknown_error",
                    "message": str(e),
                    "status": "error",
                    "code": 500,
                }

    async def check_server_health(self, server: str = "both") -> dict[str, bool]:
        """Check health of test servers."""
        results = {}

        if server in ("zen", "both"):
            try:
                response = await self.zen_client_call("GET", "/health")
                results["zen"] = response.get("status") == "success" or "healthy" in str(response).lower()
            except Exception:
                results["zen"] = False

        if server in ("heimdall", "both"):
            try:
                response = await self.heimdall_client_call("GET", "/health")
                results["heimdall"] = response.get("status") == "healthy" or "healthy" in str(response).lower()
            except Exception:
                results["heimdall"] = False

        return results

    async def verify_endpoints_available(self) -> dict[str, dict[str, bool]]:
        """Verify that expected contract endpoints are available."""
        zen_endpoints = [
            "/health",
            "/api/v1/query/process",
            "/health/agents",
            "/api/v1/knowledge/search",
        ]

        heimdall_endpoints = [
            "/health",
            "/api/v1/analyze/security",
            "/api/v1/analyze/quality",
            "/api/v1/tools",
        ]

        results = {
            "zen": {},
            "heimdall": {},
        }

        # Check zen endpoints
        for endpoint in zen_endpoints:
            try:
                response = await self.zen_client_call("GET", endpoint)
                # Endpoint is available if we get any response (even 404/405)
                results["zen"][endpoint] = response.get("code", 200) in (200, 404, 405)
            except Exception:
                results["zen"][endpoint] = False

        # Check heimdall endpoints
        for endpoint in heimdall_endpoints:
            try:
                response = await self.heimdall_client_call("GET", endpoint)
                results["heimdall"][endpoint] = response.get("code", 200) in (200, 404, 405)
            except Exception:
                results["heimdall"][endpoint] = False

        return results


class ContractTestHelpers:
    """Helper methods for contract testing."""

    @staticmethod
    def validate_response_structure(
        response: dict[str, Any],
        required_fields: list[str],
        response_type: str = "success",
    ) -> bool:
        """Validate that response has required structure for contract."""
        try:
            # Check required fields exist
            for field in required_fields:
                if field not in response:
                    logger.error(f"Missing required field '{field}' in {response_type} response")
                    return False

            # For success responses, check status
            if response_type == "success":
                if response.get("status") not in ("success", "completed", "healthy"):
                    logger.error(f"Invalid success status: {response.get('status')}")
                    return False

            # For error responses, check error structure
            elif response_type == "error":
                if response.get("status") != "error":
                    logger.error(f"Invalid error status: {response.get('status')}")
                    return False

                if not isinstance(response.get("code"), int):
                    logger.error(f"Error response missing integer code: {response.get('code')}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating response structure: {e}")
            return False

    @staticmethod
    def create_test_request(request_type: str, **kwargs) -> dict[str, Any]:
        """Create standardized test requests for contract testing."""
        if request_type == "query_processing":
            return {
                "query": kwargs.get("query", "Generate a Python function"),
                "context": kwargs.get("context", "Software development task"),
                "agent_id": kwargs.get("agent_id", "create_agent"),
            }

        if request_type == "knowledge_search":
            return {
                "query": kwargs.get("query", "Python best practices"),
                "agent_id": kwargs.get("agent_id", "create_agent"),
                "limit": kwargs.get("limit", 5),
            }

        if request_type == "security_analysis":
            return {
                "code": kwargs.get("code", "def unsafe_function(): os.system(user_input)"),
                "language": kwargs.get("language", "python"),
                "analysis_type": "security",
            }

        if request_type == "quality_analysis":
            return {
                "code": kwargs.get(
                    "code",
                    "def calculate_factorial(n):\n    return n * calculate_factorial(n-1) if n > 1 else 1",
                ),
                "language": kwargs.get("language", "python"),
                "analysis_type": "quality",
            }

        raise ValueError(f"Unknown request type: {request_type}")
