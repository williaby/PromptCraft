"""
Hybrid Infrastructure API Endpoints

API endpoints for monitoring and managing the hybrid infrastructure
discovery systems for MCP servers and agents.
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from src.commands import CommandsManager
from src.scripts import ScriptsManager

# Import discovery systems
from src.standards import StandardsManager


logger = logging.getLogger(__name__)


def register_hybrid_infrastructure_routes(app: FastAPI) -> None:
    """Register hybrid infrastructure API routes with the FastAPI app."""

    @app.get("/api/discovery/agents")
    async def get_available_agents(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get list of available agents through discovery system."""
        try:
            if not hasattr(app.state, "agent_discovery"):
                raise HTTPException(status_code=503, detail="Agent discovery not initialized")

            available_agents = app.state.agent_discovery.get_available_agents()
            resource_usage = app.state.agent_resource_manager.get_resource_usage()

            return {
                "available_agents": available_agents,
                "total_count": len(available_agents),
                "resource_usage": resource_usage,
            }
        except HTTPException:
            # Let HTTPExceptions propagate as-is
            raise
        except Exception as e:
            logger.error("Failed to get available agents: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve agents") from e

    @app.get("/api/discovery/status")
    async def get_hybrid_infrastructure_status(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get overall hybrid infrastructure status."""
        try:
            status = {
                "mcp_manager_initialized": hasattr(app.state, "mcp_manager"),
                "agent_discovery_initialized": hasattr(app.state, "agent_discovery"),
                "agent_loader_initialized": hasattr(app.state, "agent_loader"),
            }

            if hasattr(app.state, "agent_resource_manager"):
                status["resource_usage"] = app.state.agent_resource_manager.get_resource_usage()

            if hasattr(app.state, "agent_discovery"):
                status["available_agents_count"] = len(app.state.agent_discovery.get_available_agents())  # type: ignore[assignment]

            status["overall_health"] = all(
                [
                    status["mcp_manager_initialized"],
                    status["agent_discovery_initialized"],
                    status["agent_loader_initialized"],
                ],
            )

            return status
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get hybrid infrastructure status: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve infrastructure status") from e

    @app.get("/api/discovery/mcp-servers")
    async def get_mcp_servers_status(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get MCP servers discovery and connection status."""
        try:
            if not hasattr(app.state, "mcp_manager"):
                raise HTTPException(status_code=503, detail="MCP manager not initialized")

            # Get enabled servers from configuration
            enabled_servers = []
            if app.state.mcp_manager.configuration:
                enabled_servers = list(app.state.mcp_manager.configuration.mcp_servers.keys())

            # Get active connections status
            connection_status = await app.state.mcp_manager.get_connection_status()

            # Discovery status
            return {
                "enabled_servers": enabled_servers,
                "discovery_enabled": app.state.mcp_manager.discovery is not None,
                "configuration_loaded": app.state.mcp_manager.configuration is not None,
                "connection_bridge_available": connection_status.get("connection_bridge_available", False),
                "active_connections": connection_status.get("total_connections", 0),
                "connections": connection_status.get("connections", {}),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get MCP servers status: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve MCP status") from e

    @app.post("/api/mcp-servers/{server_name}/connect")
    async def connect_mcp_server(server_name: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Connect to a specific MCP server using discovery and connection bridge."""
        try:
            if not hasattr(app.state, "mcp_manager"):
                raise HTTPException(status_code=503, detail="MCP manager not initialized")

            connection = await app.state.mcp_manager.connect_to_server(server_name)

            if connection:
                return {
                    "status": "connected",
                    "server_name": server_name,
                    "connection_type": connection.connection.type,
                    "url": connection.connection.url,
                    "connected_at": connection.connected_at.isoformat(),
                    "health_status": connection.health_status,
                }
            raise HTTPException(status_code=404, detail=f"Failed to connect to server '{server_name}'")

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error connecting to MCP server %s: %s", server_name, e)
            raise HTTPException(status_code=500, detail=f"Failed to connect: {e!s}") from e

    @app.delete("/api/mcp-servers/{server_name}/disconnect")
    async def disconnect_mcp_server(server_name: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Disconnect from a specific MCP server."""
        try:
            if not hasattr(app.state, "mcp_manager"):
                raise HTTPException(status_code=503, detail="MCP manager not initialized")

            success = await app.state.mcp_manager.disconnect_from_server(server_name)

            if success:
                return {
                    "status": "disconnected",
                    "server_name": server_name,
                }
            raise HTTPException(status_code=404, detail=f"No active connection to server '{server_name}'")

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error disconnecting from MCP server %s: %s", server_name, e)
            raise HTTPException(status_code=500, detail=f"Failed to disconnect: {e!s}") from e

    @app.get("/api/mcp-servers/connections")
    async def get_mcp_connections(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get status of all active MCP server connections."""
        try:
            if not hasattr(app.state, "mcp_manager"):
                raise HTTPException(status_code=503, detail="MCP manager not initialized")

            return await app.state.mcp_manager.get_connection_status()  # type: ignore[no-any-return]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get MCP connections: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve connections") from e

    @app.get("/api/mcp-servers/health")
    async def get_mcp_health(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get comprehensive health status of MCP system."""
        try:
            if not hasattr(app.state, "mcp_manager"):
                raise HTTPException(status_code=503, detail="MCP manager not initialized")

            return await app.state.mcp_manager.health_check()  # type: ignore[no-any-return]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get MCP health: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve health status") from e

    @app.post("/api/agents/{agent_id}/load")
    async def load_agent(agent_id: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Load a specific agent dynamically."""
        try:
            if not hasattr(app.state, "agent_loader"):
                raise HTTPException(status_code=503, detail="Agent loader not initialized")

            # Load agent with minimal config
            config = {"agent_id": agent_id}
            agent = app.state.agent_loader.load_agent(agent_id, config)

            return {
                "status": "loaded",
                "agent_id": agent_id,
                "capabilities": agent.get_capabilities() if hasattr(agent, "get_capabilities") else {},
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to load agent %s: %s", agent_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to load agent: {e!s}") from e

    @app.delete("/api/agents/{agent_id}/unload")
    async def unload_agent(agent_id: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Unload a specific agent and free resources."""
        try:
            if not hasattr(app.state, "agent_loader"):
                raise HTTPException(status_code=503, detail="Agent loader not initialized")

            app.state.agent_loader.unload_agent(agent_id)

            return {
                "status": "unloaded",
                "agent_id": agent_id,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to unload agent %s: %s", agent_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to unload agent: {e!s}") from e

    @app.get("/api/discovery/standards")
    async def get_available_standards(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get list of available development standards."""
        try:
            if not hasattr(app.state, "standards_manager"):
                # Initialize standards manager on demand
                app.state.standards_manager = StandardsManager()

            standards_system = app.state.standards_manager.discovery_system
            available_standards = standards_system.get_available_standards()
            status = standards_system.get_discovery_status()

            return {
                "available_standards": available_standards,
                "total_count": len(available_standards),
                "discovery_status": status,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get available standards: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve standards") from e

    @app.get("/api/discovery/standards/{standard_id}")
    async def get_standard_content(standard_id: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get content of a specific development standard."""
        try:
            if not hasattr(app.state, "standards_manager"):
                app.state.standards_manager = StandardsManager()

            standards_system = app.state.standards_manager.discovery_system
            standard = standards_system.get_standard(standard_id)

            if not standard:
                raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found")

            content = standards_system.get_standard_content(standard_id)

            return {
                "standard_id": standard.standard_id,
                "name": standard.name,
                "description": standard.description,
                "source_type": standard.source_type,
                "version": standard.version,
                "last_updated": standard.last_updated.isoformat() if standard.last_updated else None,
                "content": content,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get standard %s: %s", standard_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve standard: {e!s}") from e

    @app.post("/api/standards/validate")
    async def validate_project_standards(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Validate project compliance against development standards."""
        try:
            if not hasattr(app.state, "standards_manager"):
                app.state.standards_manager = StandardsManager()

            compliance_results = app.state.standards_manager.validate_project_compliance()

            return {
                "compliance_results": compliance_results,
                "overall_compliance": all(compliance_results.values()),
                "total_standards_checked": len(compliance_results),
                "compliant_standards": sum(compliance_results.values()),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to validate project standards: %s", e)
            raise HTTPException(status_code=500, detail="Failed to validate standards compliance") from e

    @app.get("/api/discovery/commands")
    async def get_available_commands(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get list of available Claude Code slash commands."""
        try:
            if not hasattr(app.state, "commands_manager"):
                app.state.commands_manager = CommandsManager()

            commands_system = app.state.commands_manager.discovery_system
            available_commands = commands_system.get_available_commands()
            status = commands_system.get_discovery_status()

            return {
                "available_commands": available_commands,
                "total_count": len(available_commands),
                "discovery_status": status,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get available commands: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve commands") from e

    @app.get("/api/discovery/commands/{command_id}")
    async def get_command_content(command_id: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get content of a specific Claude Code command."""
        try:
            if not hasattr(app.state, "commands_manager"):
                app.state.commands_manager = CommandsManager()

            commands_system = app.state.commands_manager.discovery_system
            command = commands_system.get_command(command_id)

            if not command:
                raise HTTPException(status_code=404, detail=f"Command '{command_id}' not found")

            content = commands_system.get_command_content(command_id)

            return {
                "command_id": command.command_id,
                "name": command.name,
                "description": command.description,
                "source_type": command.source_type,
                "category": command.category,
                "version": command.version,
                "parameters": command.parameters,
                "examples": command.examples,
                "last_updated": command.last_updated.isoformat() if command.last_updated else None,
                "content": content,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get command %s: %s", command_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve command: {e!s}") from e

    @app.get("/api/discovery/commands/category/{category}")
    async def get_commands_by_category(category: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get commands filtered by category."""
        try:
            if not hasattr(app.state, "commands_manager"):
                app.state.commands_manager = CommandsManager()

            commands_system = app.state.commands_manager.discovery_system
            category_commands = commands_system.get_commands_by_category(category)

            command_list = []
            for command in category_commands:
                command_list.append(
                    {
                        "command_id": command.command_id,
                        "name": command.name,
                        "description": command.description,
                        "source_type": command.source_type,
                    },
                )

            return {
                "category": category,
                "commands": command_list,
                "total_count": len(command_list),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get commands for category %s: %s", category, e)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve category commands: {e!s}") from e

    @app.get("/api/commands/search")
    async def search_commands(q: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Search commands by query string."""
        try:
            if not hasattr(app.state, "commands_manager"):
                app.state.commands_manager = CommandsManager()

            commands_system = app.state.commands_manager.discovery_system
            matching_commands = commands_system.search_commands(q)

            command_list = []
            for command in matching_commands:
                command_list.append(
                    {
                        "command_id": command.command_id,
                        "name": command.name,
                        "description": command.description,
                        "source_type": command.source_type,
                        "category": command.category,
                    },
                )

            return {
                "query": q,
                "commands": command_list,
                "total_count": len(command_list),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to search commands with query '%s': %s", q, e)
            raise HTTPException(status_code=500, detail=f"Failed to search commands: {e!s}") from e

    @app.get("/api/discovery/scripts")
    async def get_available_scripts(request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get list of available automation scripts."""
        try:
            if not hasattr(app.state, "scripts_manager"):
                app.state.scripts_manager = ScriptsManager()

            scripts_system = app.state.scripts_manager.discovery_system
            available_scripts = scripts_system.get_available_scripts()
            status = scripts_system.get_discovery_status()

            return {
                "available_scripts": available_scripts,
                "total_count": len(available_scripts),
                "discovery_status": status,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get available scripts: %s", e)
            raise HTTPException(status_code=500, detail="Failed to retrieve scripts") from e

    @app.get("/api/discovery/scripts/{script_id}")
    async def get_script_content(script_id: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get content of a specific automation script."""
        try:
            if not hasattr(app.state, "scripts_manager"):
                app.state.scripts_manager = ScriptsManager()

            scripts_system = app.state.scripts_manager.discovery_system
            script = scripts_system.get_script(script_id)

            if not script:
                raise HTTPException(status_code=404, detail=f"Script '{script_id}' not found")

            content = scripts_system.get_script_content(script_id)

            return {
                "script_id": script.script_id,
                "name": script.name,
                "description": script.description,
                "source_type": script.source_type,
                "script_type": script.script_type,
                "category": script.category,
                "version": script.version,
                "is_executable": script.is_executable,
                "dependencies": script.dependencies,
                "parameters": script.parameters,
                "last_updated": script.last_updated.isoformat() if script.last_updated else None,
                "content": content,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get script %s: %s", script_id, e)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve script: {e!s}") from e

    @app.get("/api/discovery/scripts/category/{category}")
    async def get_scripts_by_category(category: str, request: Request) -> dict[str, Any]:  # noqa: ARG001
        """Get scripts filtered by category."""
        try:
            if not hasattr(app.state, "scripts_manager"):
                app.state.scripts_manager = ScriptsManager()

            scripts_system = app.state.scripts_manager.discovery_system
            category_scripts = scripts_system.get_scripts_by_category(category)

            script_list = []
            for script in category_scripts:
                script_list.append(
                    {
                        "script_id": script.script_id,
                        "name": script.name,
                        "description": script.description,
                        "source_type": script.source_type,
                        "script_type": script.script_type,
                        "is_executable": script.is_executable,
                    },
                )

            return {
                "category": category,
                "scripts": script_list,
                "total_count": len(script_list),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get scripts for category %s: %s", category, e)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve category scripts: {e!s}") from e

    logger.info("Hybrid infrastructure API routes registered")
