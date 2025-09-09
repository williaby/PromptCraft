#!/usr/bin/env python3
"""Service Token Management CLI for AUTH-2 implementation.

This script provides command-line interface for managing service tokens including:
- Token creation, rotation, and revocation
- Emergency revocation procedures
- Usage analytics and monitoring
- Token cleanup and maintenance

Usage:
    python scripts/service_token_management.py create --name "ci-cd-token" --permissions api_read,system_status
    python scripts/service_token_management.py rotate --identifier "ci-cd-token" --reason "scheduled_rotation"
    python scripts/service_token_management.py revoke --identifier "old-token" --reason "security_incident"
    python scripts/service_token_management.py emergency-revoke --reason "security_breach"
    python scripts/service_token_management.py analytics --token "ci-cd-token" --days 30
    python scripts/service_token_management.py cleanup --deactivate-only
"""

import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.auth.service_token_manager import ServiceTokenManager
from src.database.connection import database_health_check


async def create_token_command(args: argparse.Namespace) -> None:
    """Create a new service token."""
    manager = ServiceTokenManager()

    # Parse permissions from comma-separated string
    permissions = [p.strip() for p in args.permissions.split(",")] if args.permissions else []

    # Build metadata
    metadata = {
        "permissions": permissions,
        "created_by": args.created_by or "cli_admin",
        "purpose": args.purpose or "Manual token creation",
        "environment": args.environment or "production",
    }

    # Parse expiration
    expires_at = None
    if args.expires_days:
        expires_at = datetime.now(UTC) + timedelta(days=args.expires_days)
    elif args.expires_at:
        expires_at = datetime.fromisoformat(args.expires_at.replace("Z", "+00:00"))

    try:
        token_value, token_id = await manager.create_service_token(
            token_name=args.name,
            metadata=metadata,
            expires_at=expires_at,
            is_active=True,
        )

        print("✅ Service token created successfully!")
        print(f"Token ID: {token_id}")
        print(f"Token Name: {args.name}")
        print(f"Permissions: {', '.join(permissions)}")
        print(f"Expires: {expires_at.isoformat() if expires_at else 'Never'}")
        print()
        print("🔑 SERVICE TOKEN (save this securely - it won't be shown again):")
        print(f"{token_value}")
        print()
        print("💡 Usage examples:")
        print(f"curl -H 'Authorization: Bearer {token_value}' https://api.example.com/health")
        print(f"export PROMPTCRAFT_SERVICE_TOKEN='{token_value}'")

    except Exception as e:
        print(f"❌ Failed to create service token: {e}")
        sys.exit(1)


async def rotate_token_command(args: argparse.Namespace) -> None:
    """Rotate an existing service token."""
    manager = ServiceTokenManager()

    try:
        result = await manager.rotate_service_token(
            token_identifier=args.identifier,
            rotation_reason=args.reason or "manual_rotation",
        )

        if result:
            new_token_value, new_token_id = result
            print("✅ Service token rotated successfully!")
            print(f"New Token ID: {new_token_id}")
            print(f"Rotation Reason: {args.reason or 'manual_rotation'}")
            print()
            print("🔑 NEW SERVICE TOKEN (save this securely - it won't be shown again):")
            print(f"{new_token_value}")
            print()
            print("⚠️  IMPORTANT: Update all systems using the old token immediately!")
            print("   The old token has been deactivated and will no longer work.")
        else:
            print(f"❌ Failed to rotate token: Token '{args.identifier}' not found or inactive")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Failed to rotate service token: {e}")
        sys.exit(1)


async def revoke_token_command(args: argparse.Namespace) -> None:
    """Revoke a service token."""
    manager = ServiceTokenManager()

    try:
        success = await manager.revoke_service_token(
            token_identifier=args.identifier,
            revocation_reason=args.reason or "manual_revocation",
        )

        if success:
            print("✅ Service token revoked successfully!")
            print(f"Token: {args.identifier}")
            print(f"Reason: {args.reason or 'manual_revocation'}")
            print()
            print("⚠️  The token is now inactive and cannot be used for authentication.")
        else:
            print(f"❌ Token '{args.identifier}' not found")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Failed to revoke service token: {e}")
        sys.exit(1)


async def emergency_revoke_command(args: argparse.Namespace) -> None:
    """Emergency revocation of ALL service tokens."""
    manager = ServiceTokenManager()

    print(f"⚠️  EMERGENCY REVOCATION: {args.reason}")
    print("This will deactivate ALL active service tokens immediately.")

    if not args.confirm:
        confirm = input("Are you sure you want to proceed? Type 'EMERGENCY' to confirm: ")
        if confirm != "EMERGENCY":
            print("❌ Emergency revocation cancelled")
            return

    try:
        revoked_count = await manager.emergency_revoke_all_tokens(args.reason)

        print("🚨 EMERGENCY REVOCATION COMPLETED!")
        print(f"Tokens revoked: {revoked_count}")
        print(f"Reason: {args.reason}")
        print(f"Timestamp: {datetime.now(UTC).isoformat()}Z")
        print()
        print("💥 ALL SERVICE TOKENS HAVE BEEN DEACTIVATED!")
        print("   You must create new tokens before any automated systems can authenticate.")

    except Exception as e:
        print(f"❌ Emergency revocation failed: {e}")
        sys.exit(1)


async def analytics_command(args: argparse.Namespace) -> None:
    """Show usage analytics for service tokens."""
    manager = ServiceTokenManager()

    try:
        analytics = await manager.get_token_usage_analytics(token_identifier=args.token, days=args.days)

        if args.token:
            # Single token analytics
            if "error" in analytics:
                print(f"❌ {analytics['error']}")
                sys.exit(1)

            print(f"📊 Token Analytics: {analytics['token_name']}")
            print(f"Usage Count: {analytics['usage_count']}")
            print(f"Last Used: {analytics['last_used'] or 'Never'}")
            print(f"Created: {analytics['created_at']}")
            print(f"Status: {'Active' if analytics['is_active'] else 'Inactive'}")
            print(f"Expired: {'Yes' if analytics['is_expired'] else 'No'}")
            print(f"Recent Events: {analytics['events_count']} (last {args.days} days)")

            if analytics["recent_events"]:
                print("\n📋 Recent Authentication Events:")
                for event in analytics["recent_events"][:10]:  # Show last 10
                    status = "✅" if event["success"] else "❌"
                    print(f"   {status} {event['event_type']} - {event['timestamp']}")
        else:
            # All tokens summary
            summary = analytics["summary"]
            print("📊 Service Token Summary")
            print(f"Total Tokens: {summary['total_tokens']}")
            print(f"Active Tokens: {summary['active_tokens']}")
            print(f"Inactive Tokens: {summary['inactive_tokens']}")
            print(f"Expired Tokens: {summary['expired_tokens']}")
            print(f"Total Usage: {summary['total_usage']}")
            print(f"Avg Usage per Token: {summary['avg_usage_per_token']:.1f}")

            if analytics["top_tokens"]:
                print(f"\n🏆 Top {len(analytics['top_tokens'])} Most Used Tokens:")
                for i, token in enumerate(analytics["top_tokens"], 1):
                    print(f"   {i}. {token['token_name']} - {token['usage_count']} uses")

    except Exception as e:
        print(f"❌ Failed to get analytics: {e}")
        sys.exit(1)


async def cleanup_command(args: argparse.Namespace) -> None:
    """Clean up expired service tokens."""
    manager = ServiceTokenManager()

    try:
        result = await manager.cleanup_expired_tokens(deactivate_only=args.deactivate_only)

        action = result["action"]
        count = result["expired_tokens_processed"]

        if count > 0:
            print("✅ Token cleanup completed!")
            print(f"Action: {action.title()} {count} expired tokens")

            if "token_names" in result:
                print("Tokens processed:")
                for name in result["token_names"]:
                    print(f"   - {name}")
        else:
            print("✅ No expired tokens found - cleanup not needed")

    except Exception as e:
        print(f"❌ Token cleanup failed: {e}")
        sys.exit(1)


async def list_tokens_command(args: argparse.Namespace) -> None:  # noqa: ARG001
    """List all service tokens with their status."""
    manager = ServiceTokenManager()

    try:
        # Get summary analytics to list all tokens
        analytics = await manager.get_token_usage_analytics(days=365)  # Full year

        if analytics["summary"]["total_tokens"] == 0:
            print("📋 No service tokens found")
            return

        print("📋 Service Token List")
        print("=" * 50)

        # Show top tokens (which includes all active ones)
        for token in analytics["top_tokens"]:
            print(f"Token: {token['token_name']}")
            print(f"  Usage: {token['usage_count']} times")
            print(f"  Last Used: {token['last_used'] or 'Never'}")
            print()

    except Exception as e:
        print(f"❌ Failed to list tokens: {e}")
        sys.exit(1)


async def validate_database_command(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Validate database connectivity and schema."""
    print("🔍 Validating database connectivity and schema...")

    try:
        # Test database connectivity
        health_status = await database_health_check()

        if health_status["status"] == "healthy":
            print("✅ Database connection: Healthy")
            print(f"   Connection time: {health_status['connection_time_ms']:.2f}ms")
        else:
            print("❌ Database connection: Failed")
            print(f"   Error: {health_status.get('error', 'Unknown error')}")
            sys.exit(1)

        # Test service token manager operations
        manager = ServiceTokenManager()

        # Try to get analytics (this tests table access)
        analytics = await manager.get_token_usage_analytics(days=1)
        print("✅ Database schema: Tables accessible")
        print(f"   Total tokens: {analytics['summary']['total_tokens']}")

        print("✅ Database validation completed successfully!")

    except Exception as e:
        print(f"❌ Database validation failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Service Token Management CLI for AUTH-2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create token command
    create_parser = subparsers.add_parser("create", help="Create a new service token")
    create_parser.add_argument("--name", required=True, help="Token name (must be unique)")
    create_parser.add_argument("--permissions", help="Comma-separated list of permissions")
    create_parser.add_argument("--expires-days", type=int, help="Token expires in N days")
    create_parser.add_argument("--expires-at", help="Token expires at specific ISO date")
    create_parser.add_argument("--created-by", help="Who created this token")
    create_parser.add_argument("--purpose", help="Purpose of this token")
    create_parser.add_argument("--environment", help="Environment (production, staging, dev)")

    # Rotate token command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate an existing service token")
    rotate_parser.add_argument("--identifier", required=True, help="Token name, ID, or hash")
    rotate_parser.add_argument("--reason", help="Reason for rotation")

    # Revoke token command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke a service token")
    revoke_parser.add_argument("--identifier", required=True, help="Token name, ID, or hash")
    revoke_parser.add_argument("--reason", help="Reason for revocation")

    # Emergency revoke command
    emergency_parser = subparsers.add_parser("emergency-revoke", help="Emergency revocation of ALL tokens")
    emergency_parser.add_argument("--reason", required=True, help="Emergency reason (required)")
    emergency_parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")

    # Analytics command
    analytics_parser = subparsers.add_parser("analytics", help="Show token usage analytics")
    analytics_parser.add_argument("--token", help="Specific token to analyze")
    analytics_parser.add_argument("--days", type=int, default=30, help="Days to analyze")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up expired tokens")
    cleanup_parser.add_argument(
        "--deactivate-only",
        action="store_true",
        default=True,
        help="Only deactivate expired tokens (don't delete)",
    )
    cleanup_parser.add_argument(
        "--delete",
        dest="deactivate_only",
        action="store_false",
        help="Delete expired tokens permanently",
    )

    # List tokens command
    _ = subparsers.add_parser("list", help="List all service tokens")

    # Validate database command
    _ = subparsers.add_parser("validate-db", help="Validate database connectivity and schema")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Set up asyncio event loop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Command routing
    command_handlers = {
        "create": create_token_command,
        "rotate": rotate_token_command,
        "revoke": revoke_token_command,
        "emergency-revoke": emergency_revoke_command,
        "analytics": analytics_command,
        "cleanup": cleanup_command,
        "list": list_tokens_command,
        "validate-db": validate_database_command,
    }

    handler = command_handlers.get(args.command)
    if handler:
        asyncio.run(handler(args))
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
