#!/usr/bin/env python3
"""Health Check Integration Demo - Phase 5 Implementation.

This example demonstrates the health check functionality implemented in Phase 5
of the Core Configuration System. It shows how to use the health check models
and endpoints to monitor application configuration status safely.

Usage:
    poetry run python examples/health_check_demo.py
"""

import asyncio
import json

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.config import (
    ApplicationSettings,
    ConfigurationStatusModel,
    get_configuration_health_summary,
    get_configuration_status,
    get_settings,
)

console = Console()


def demonstrate_configuration_status() -> None:
    """Demonstrate configuration status model generation."""
    console.print(
        Panel("[bold blue]Phase 5: Configuration Status Model Demo[/bold blue]"),
    )

    try:
        # Load current settings
        settings = get_settings(validate_on_startup=False)
        console.print(
            f"✅ Settings loaded for environment: [bold]{settings.environment}[/bold]",
        )

        # Generate configuration status
        status = get_configuration_status(settings)

        # Create a table to display status information
        table = Table(
            title="Configuration Status",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Description", style="dim")

        # Add configuration status rows
        table.add_row(
            "Environment",
            status.environment,
            "Current deployment environment",
        )
        table.add_row("Version", status.version, "Application version")
        table.add_row("Debug Mode", str(status.debug), "Whether debug mode is enabled")
        table.add_row(
            "Config Loaded",
            str(status.config_loaded),
            "Configuration loaded successfully",
        )
        table.add_row(
            "Encryption Available",
            str(status.encryption_enabled),
            "Encryption system status",
        )
        table.add_row(
            "Config Source",
            status.config_source,
            "Primary configuration source",
        )
        table.add_row(
            "Validation Status",
            status.validation_status,
            "Configuration validation result",
        )
        table.add_row(
            "Secrets Configured",
            str(status.secrets_configured),
            "Number of configured secrets",
        )
        table.add_row("API Host", status.api_host, "API server host address")
        table.add_row("API Port", str(status.api_port), "API server port")
        table.add_row(
            "Overall Healthy",
            str(status.config_healthy),
            "Computed health status",
        )

        console.print(table)

        # Show validation errors if any
        if status.validation_errors:
            console.print("\n[bold red]Validation Errors:[/bold red]")
            for error in status.validation_errors:
                console.print(f"  ❌ {error}")
        else:
            console.print("\n✅ [bold green]No validation errors[/bold green]")

        return status

    except Exception as e:
        console.print(
            f"❌ [bold red]Error generating configuration status:[/bold red] {e}",
        )
        return None


def demonstrate_health_summary() -> None:
    """Demonstrate simplified health summary."""
    console.print(Panel("[bold blue]Health Summary Demo[/bold blue]"))

    try:
        summary = get_configuration_health_summary()

        # Display summary in a nice format
        console.print("\n[bold]Health Summary:[/bold]")
        for key, value in summary.items():
            if key == "healthy":
                status_text = Text("✅ HEALTHY" if value else "❌ UNHEALTHY")
                status_text.stylize("bold green" if value else "bold red")
                console.print(f"  Status: {status_text}")
            elif key == "timestamp":
                console.print(f"  {key.title()}: [dim]{value}[/dim]")
            else:
                console.print(
                    f"  {key.title().replace('_', ' ')}: [cyan]{value}[/cyan]",
                )

    except Exception as e:
        console.print(f"❌ [bold red]Error getting health summary:[/bold red] {e}")


def demonstrate_json_serialization(status: ConfigurationStatusModel) -> None:
    """Demonstrate JSON serialization of configuration status."""
    console.print(Panel("[bold blue]JSON Serialization Demo[/bold blue]"))

    try:
        # Convert to JSON
        json_data = status.model_dump_json(indent=2)

        console.print("[bold]Configuration Status as JSON:[/bold]")
        console.print(f"[dim]{json_data}[/dim]")

        # Verify no sensitive data in JSON
        sensitive_keywords = [
            "password",
            "secret",
            "key",
            "token",
            "credential",
            "SecretStr",
            "super_secret",
            "api_key_value",
        ]

        has_sensitive = any(keyword in json_data.lower() for keyword in sensitive_keywords)

        if has_sensitive:
            console.print(
                "\n❌ [bold red]WARNING: JSON may contain sensitive data![/bold red]",
            )
        else:
            console.print(
                "\n✅ [bold green]JSON is safe - no sensitive data detected[/bold green]",
            )

    except Exception as e:
        console.print(f"❌ [bold red]Error serializing to JSON:[/bold red] {e}")


async def demonstrate_http_endpoints() -> None:
    """Demonstrate HTTP health check endpoints."""
    console.print(Panel("[bold blue]HTTP Health Check Endpoints Demo[/bold blue]"))

    # These would normally be tested against a running server
    # For demo purposes, we'll show what the endpoints would return

    base_url = "http://localhost:8000"

    console.print(f"[bold]Testing endpoints against:[/bold] [cyan]{base_url}[/cyan]")
    console.print(
        "[dim]Note: Start the server with 'poetry run python src/main.py' to test live endpoints[/dim]\n",
    )

    # Mock endpoint responses for demonstration
    endpoints = [
        ("/health", "Simple health check for load balancers"),
        ("/health/config", "Detailed configuration status"),
        ("/ping", "Simple ping endpoint"),
        ("/", "Root endpoint with app info"),
    ]

    for endpoint, description in endpoints:
        console.print(f"[bold cyan]{endpoint}[/bold cyan] - {description}")

    console.print("\n[bold]Example responses:[/bold]")

    # Show example health response
    example_health = {
        "status": "healthy",
        "service": "promptcraft-hybrid",
        "healthy": True,
        "environment": "dev",
        "version": "0.1.0",
        "config_loaded": True,
        "encryption_available": False,
        "timestamp": "2024-01-01T12:00:00Z",
    }

    console.print("[bold]GET /health:[/bold]")
    console.print(f"[dim]{json.dumps(example_health, indent=2)}[/dim]\n")

    # Try to connect to actual server if it's running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/ping", timeout=2.0)
            if response.status_code == 200:
                console.print(
                    "✅ [bold green]Live server detected! Testing real endpoints...[/bold green]",
                )

                # Test health endpoint
                health_response = await client.get(f"{base_url}/health")
                console.print(
                    f"[bold]Live /health response (status {health_response.status_code}):[/bold]",
                )
                console.print(
                    f"[dim]{json.dumps(health_response.json(), indent=2)}[/dim]\n",
                )

                # Test config health endpoint
                config_response = await client.get(f"{base_url}/health/config")
                console.print(
                    f"[bold]Live /health/config response (status {config_response.status_code}):[/bold]",
                )
                console.print(
                    f"[dim]{json.dumps(config_response.json(), indent=2)}[/dim]",
                )

    except (httpx.ConnectError, httpx.TimeoutException):
        console.print(
            "ℹ️  [dim]No live server detected. Start with 'poetry run python src/main.py' to test live endpoints.[/dim]",
        )


def demonstrate_security_features() -> None:
    """Demonstrate security features that prevent data leakage."""
    console.print(Panel("[bold blue]Security Features Demo[/bold blue]"))

    try:
        # Create settings with sensitive data
        from pydantic import SecretStr

        settings = ApplicationSettings(
            database_password=SecretStr("super_secret_db_password"),
            api_key=SecretStr("sk-1234567890abcdef"),
            secret_key=SecretStr("super_secret_app_key"),
            jwt_secret_key=SecretStr("jwt_signing_secret"),
        )

        console.print("✅ [bold]Created settings with sensitive data:[/bold]")
        console.print("  - Database password")
        console.print("  - API key")
        console.print("  - Secret key")
        console.print("  - JWT secret key")

        # Generate status
        status = get_configuration_status(settings)

        # Convert to JSON and verify no secrets
        json_output = status.model_dump_json()

        console.print(
            f"\n[bold]Secrets configured count:[/bold] [cyan]{status.secrets_configured}[/cyan]",
        )
        console.print("[bold]Security verification:[/bold]")

        # Check for secret values
        secret_values = [
            "super_secret_db_password",
            "sk-1234567890abcdef",
            "super_secret_app_key",
            "jwt_signing_secret",
        ]

        leaked_secrets = []
        for secret in secret_values:
            if secret in json_output:
                leaked_secrets.append(secret)

        if leaked_secrets:
            console.print(
                f"❌ [bold red]SECURITY BREACH: Found secrets in output:[/bold red] {leaked_secrets}",
            )
        else:
            console.print(
                "✅ [bold green]SECURE: No secret values found in health check output[/bold green]",
            )

        # Check for SecretStr representations
        if "SecretStr" in json_output:
            console.print(
                "❌ [bold red]WARNING: SecretStr representations found[/bold red]",
            )
        else:
            console.print(
                "✅ [bold green]SECURE: No SecretStr representations exposed[/bold green]",
            )

    except Exception as e:
        console.print(f"❌ [bold red]Error in security demo:[/bold red] {e}")


def main() -> None:
    """Run the health check integration demo."""
    console.print(
        "[bold green]PromptCraft-Hybrid: Health Check Integration Demo[/bold green]",
    )
    console.print("[dim]Phase 5 of the Core Configuration System[/dim]\n")

    # 1. Demonstrate configuration status model
    status = demonstrate_configuration_status()

    console.print("\n" + "=" * 60 + "\n")

    # 2. Demonstrate health summary
    demonstrate_health_summary()

    console.print("\n" + "=" * 60 + "\n")

    # 3. Demonstrate JSON serialization
    if status:
        demonstrate_json_serialization(status)

    console.print("\n" + "=" * 60 + "\n")

    # 4. Demonstrate HTTP endpoints
    asyncio.run(demonstrate_http_endpoints())

    console.print("\n" + "=" * 60 + "\n")

    # 5. Demonstrate security features
    demonstrate_security_features()

    console.print(
        "\n[bold green]✅ Health Check Integration Demo Complete![/bold green]",
    )
    console.print("\n[bold]Key Features Demonstrated:[/bold]")
    console.print("• Configuration status model with operational data")
    console.print("• Health check endpoints for monitoring")
    console.print("• Security: No sensitive data exposure")
    console.print("• JSON serialization for API responses")
    console.print("• Validation status reporting")
    console.print("• Encryption availability checking")

    console.print("\n[bold]Next Steps:[/bold]")
    console.print("• Start the server: [cyan]poetry run python src/main.py[/cyan]")
    console.print("• Test endpoints: [cyan]curl http://localhost:8000/health[/cyan]")
    console.print("• Monitor with tools: Use /health for load balancers")
    console.print("• Detailed monitoring: Use /health/config for ops dashboards")


if __name__ == "__main__":
    main()
