"""
Minimal Heimdall MCP Server Stub

A lightweight stub implementation of Heimdall MCP Server endpoints
for contract testing. Provides deterministic responses for security
and code quality analysis endpoints.
"""

import asyncio
import logging
import os
import signal
import sys

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn


logger = logging.getLogger(__name__)


class HeimdallStubServer:
    """Stub implementation of Heimdall MCP Server for contract testing."""
    
    def __init__(self, port: int = 8081, host: str = "localhost"):
        self.port = port
        self.host = host
        self.app = FastAPI(title="Heimdall MCP Stub", version="1.0.0")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes matching Heimdall contract expectations."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "heimdall-stub"}
        
        @self.app.post("/api/v1/analyze/security")
        async def security_analysis(request_data: dict):
            """Security analysis endpoint - returns deterministic test data."""
            code = request_data.get("code", "")
            language = request_data.get("language", "python")
            
            # Return deterministic security findings for contract testing
            findings = []
            
            # Check for common security patterns
            if "os.system" in code:
                findings.append({
                    "type": "security_vulnerability",
                    "severity": "high", 
                    "message": "Potential command injection vulnerability",
                    "line": 1,
                    "suggestion": "Use subprocess.run() instead of os.system()",
                })
            
            if "eval(" in code:
                findings.append({
                    "type": "security_vulnerability",
                    "severity": "critical",
                    "message": "Use of eval() detected - potential code injection",
                    "line": 1,
                    "suggestion": "Avoid using eval() with user input",
                })
            
            if "password" in code.lower() and "=" in code:
                findings.append({
                    "type": "security_vulnerability", 
                    "severity": "medium",
                    "message": "Potential hardcoded password detected",
                    "line": 1,
                    "suggestion": "Use environment variables for sensitive data",
                })
            
            # Calculate security score (10 = secure, 0 = very insecure)
            score = max(0.0, 10.0 - (len(findings) * 2.5))
            
            return {
                "findings": findings,
                "score": score,
                "status": "completed",
            }
        
        @self.app.post("/api/v1/analyze/quality")
        async def quality_analysis(request_data: dict):
            """Code quality analysis endpoint - returns deterministic test data."""
            code = request_data.get("code", "")
            language = request_data.get("language", "python")
            
            # Calculate simple metrics based on code characteristics
            lines = code.split("\n")
            line_count = len(lines)
            complexity = min(10, max(1, line_count // 5))  # Simple complexity estimate
            
            # Maintainability score (higher is better)
            maintainability = max(1.0, 10.0 - (complexity * 0.5))
            
            # Readability score based on code structure
            readability = 8.0
            if any(line.strip() and not line.strip().startswith("#") for line in lines):
                if "def " in code:
                    readability += 1.0  # Has functions
                if "class " in code:
                    readability += 0.5  # Has classes
                if "#" in code:
                    readability += 0.5  # Has comments
            
            readability = min(10.0, readability)
            
            # Generate suggestions
            suggestions = []
            if complexity > 5:
                suggestions.append({
                    "type": "improvement",
                    "message": "Consider breaking down complex functions",
                    "priority": "medium",
                })
            
            if "def " not in code and line_count > 10:
                suggestions.append({
                    "type": "improvement", 
                    "message": "Consider organizing code into functions",
                    "priority": "low",
                })
            
            if "#" not in code:
                suggestions.append({
                    "type": "improvement",
                    "message": "Add comments to improve code documentation",
                    "priority": "low",
                })
            
            return {
                "metrics": {
                    "complexity": complexity,
                    "maintainability": maintainability,
                    "readability": readability,
                    "test_coverage": 0.0,  # Stub always returns 0
                },
                "suggestions": suggestions,
                "status": "completed",
            }
        
        @self.app.get("/api/v1/tools")
        async def list_tools():
            """List available tools - MCP protocol compliance."""
            return {
                "tools": [
                    {
                        "name": "security_analysis",
                        "description": "Analyze code for security vulnerabilities", 
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "language": {"type": "string"},
                            },
                            "required": ["code"],
                        },
                    },
                    {
                        "name": "quality_analysis",
                        "description": "Analyze code quality metrics",
                        "inputSchema": {
                            "type": "object", 
                            "properties": {
                                "code": {"type": "string"},
                                "language": {"type": "string"},
                            },
                            "required": ["code"],
                        },
                    },
                ],
            }
        
        @self.app.exception_handler(Exception)
        async def global_exception_handler(request, exc):
            """Global exception handler for consistent error responses."""
            logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": str(exc),
                    "status": "error",
                    "code": 500,
                },
            )
    
    def run(self):
        """Run the stub server."""
        logger.info(f"Starting Heimdall stub server on {self.host}:{self.port}")
        
        # Handle shutdown signals
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping server...")
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False,
        )


async def start_stub_server(port: int = 8081, host: str = "localhost") -> HeimdallStubServer:
    """Start Heimdall stub server asynchronously."""
    server = HeimdallStubServer(port=port, host=host)
    
    # Start server in background task
    config = uvicorn.Config(
        server.app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
    
    server_instance = uvicorn.Server(config)
    
    # Start server task
    task = asyncio.create_task(server_instance.serve())
    
    # Wait a moment for server to start
    await asyncio.sleep(1.0)
    
    return server, task


if __name__ == "__main__":
    # Allow running as standalone server for testing
    port = int(os.getenv("PORT", 8081))
    host = os.getenv("HOST", "localhost")
    
    server = HeimdallStubServer(port=port, host=host)
    server.run()