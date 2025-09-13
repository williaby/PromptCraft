"""User Tier Management Module for Admin Interface.

This module provides functionality for administrators to manage user tier assignments,
including adding/removing users from tiers, validating email addresses, and persisting
changes to the configuration.
"""

from datetime import datetime
import json
import logging
import re
from typing import Any

from src.auth_simple.config import ConfigLoader, ConfigManager, get_config_manager
from src.utils.datetime_compat import UTC


logger = logging.getLogger(__name__)


class UserTierManagerError(Exception):
    """Base exception for user tier management operations."""


class UserTierManager:
    """Manages user tier assignments and provides admin interface functionality."""

    def __init__(self, config_manager: ConfigManager | None = None) -> None:
        """Initialize the user tier manager.

        Args:
            config_manager: Optional config manager instance
        """
        self.config_manager = config_manager or get_config_manager()
        self.validator = self.config_manager.create_whitelist_validator()
        self.changes_log: list[dict[str, Any]] = []

    def _validate_email(self, email: str) -> bool:
        """Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid
        """
        if not email or not isinstance(email, str):
            return False

        # Handle domain patterns
        if email.startswith("@"):
            domain_pattern = (
                r"^@[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
            )
            return bool(re.match(domain_pattern, email))

        # Standard email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, email.strip()))

    def get_all_users(self) -> dict[str, list[dict[str, Any]]]:
        """Get all users organized by tier.

        Returns:
            Dictionary with tier names as keys and user lists as values
        """
        try:
            # Get all emails from whitelist
            whitelist_emails = set()
            for entry in self.config_manager.config.email_whitelist:
                whitelist_emails.add(entry.lower())

            users_by_tier: dict[str, list[dict[str, Any]]] = {"admin": [], "full": [], "limited": [], "unassigned": []}

            # Categorize tier users
            for email in self.config_manager.config.admin_emails:
                if email.lower() in whitelist_emails:
                    users_by_tier["admin"].append(
                        {"email": email, "can_access_premium": True, "is_admin": True, "assigned_at": "existing"},
                    )

            for email in self.config_manager.config.full_users:
                if email.lower() in whitelist_emails:
                    users_by_tier["full"].append(
                        {"email": email, "can_access_premium": True, "is_admin": False, "assigned_at": "existing"},
                    )

            for email in self.config_manager.config.limited_users:
                if email.lower() in whitelist_emails:
                    users_by_tier["limited"].append(
                        {"email": email, "can_access_premium": False, "is_admin": False, "assigned_at": "existing"},
                    )

            # Find unassigned whitelist users
            assigned_emails = set()
            for tier_users in [users_by_tier["admin"], users_by_tier["full"], users_by_tier["limited"]]:
                for user in tier_users:
                    assigned_emails.add(user["email"].lower())

            for email in whitelist_emails:
                if email not in assigned_emails and not email.startswith("@"):
                    users_by_tier["unassigned"].append(
                        {"email": email, "can_access_premium": False, "is_admin": False, "assigned_at": "unassigned"},
                    )

            return users_by_tier

        except Exception as e:
            logger.error("Error getting all users: %s", e)
            raise UserTierManagerError(f"Failed to retrieve users: {e}") from e

    def assign_user_tier(self, email: str, tier: str, admin_email: str) -> tuple[bool, str]:
        """Assign a user to a specific tier.

        Args:
            email: Email address to assign
            tier: Target tier (admin, full, limited)
            admin_email: Email of admin making the change

        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate inputs
            if not self._validate_email(email):
                return False, f"Invalid email format: {email}"

            if tier not in ["admin", "full", "limited"]:
                return False, f"Invalid tier: {tier}. Must be admin, full, or limited"

            # Check if user is in whitelist
            if not self.validator.is_authorized(email):
                return False, f"Email {email} is not in the whitelist. Add to Cloudflare Access first."

            # Remove from all tiers first
            success, msg = self._remove_from_all_tiers(email)
            if not success:
                return False, msg

            # Add to target tier
            if tier == "admin":
                self.config_manager.config.admin_emails.append(email)
            elif tier == "full":
                self.config_manager.config.full_users.append(email)
            elif tier == "limited":
                self.config_manager.config.limited_users.append(email)

            # Log the change
            self.changes_log.append(
                {
                    "action": "assign_tier",
                    "email": email,
                    "tier": tier,
                    "admin": admin_email,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

            logger.info("User %s assigned to %s tier by %s", email, tier, admin_email)
            return True, f"Successfully assigned {email} to {tier} tier"

        except Exception as e:
            logger.error("Error assigning user tier: %s", e)
            return False, f"Failed to assign tier: {e}"

    def remove_user_tier(self, email: str, admin_email: str) -> tuple[bool, str]:
        """Remove a user from all tiers.

        Args:
            email: Email address to remove
            admin_email: Email of admin making the change

        Returns:
            Tuple of (success, message)
        """
        try:
            success, msg = self._remove_from_all_tiers(email)
            if success:
                # Log the change
                self.changes_log.append(
                    {
                        "action": "remove_tier",
                        "email": email,
                        "admin": admin_email,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                )
                logger.info("User %s removed from all tiers by %s", email, admin_email)

            return success, msg

        except Exception as e:
            logger.error("Error removing user tier: %s", e)
            return False, f"Failed to remove tier: {e}"

    def _remove_from_all_tiers(self, email: str) -> tuple[bool, str]:
        """Remove user from all tier lists.

        Args:
            email: Email address to remove

        Returns:
            Tuple of (success, message)
        """
        removed_from = []

        if email in self.config_manager.config.admin_emails:
            self.config_manager.config.admin_emails.remove(email)
            removed_from.append("admin")

        if email in self.config_manager.config.full_users:
            self.config_manager.config.full_users.remove(email)
            removed_from.append("full")

        if email in self.config_manager.config.limited_users:
            self.config_manager.config.limited_users.remove(email)
            removed_from.append("limited")

        if removed_from:
            return True, f"Removed {email} from {', '.join(removed_from)} tier(s)"
        return True, f"{email} was not assigned to any tier"

    def get_user_tier_info(self, email: str) -> dict[str, Any] | None:
        """Get detailed tier information for a specific user.

        Args:
            email: Email address to check

        Returns:
            User tier information or None if not authorized
        """
        try:
            if not self.validator.is_authorized(email):
                return None

            tier = self.validator.get_user_tier(email)

            return {
                "email": email,
                "tier": tier.value,
                "can_access_premium": tier.can_access_premium_models,
                "is_admin": tier.has_admin_privileges,
                "is_authorized": True,
            }

        except Exception as e:
            logger.error("Error getting user tier info: %s", e)
            return None

    def validate_tier_configuration(self) -> list[str]:
        """Validate current tier configuration and return warnings.

        Returns:
            List of warning messages
        """
        try:
            result = self.validator.validate_whitelist_config()
            return result if isinstance(result, list) else [str(result)]
        except Exception as e:
            logger.error("Error validating configuration: %s", e)
            return [f"Configuration validation failed: {e}"]

    def get_tier_statistics(self) -> dict[str, Any]:
        """Get statistics about current tier assignments.

        Returns:
            Dictionary with tier statistics
        """
        try:
            stats = self.validator.get_whitelist_stats()

            # Add additional admin-specific stats
            stats.update(
                {
                    "total_authorized_users": (
                        stats["individual_emails"] + len([d for d in stats["domains"] if d.startswith("@")])
                    ),
                    "changes_made": len(self.changes_log),
                    "last_modified": datetime.now(UTC).isoformat(),
                },
            )

            return stats if isinstance(stats, dict) else {"error": "Invalid stats format"}

        except Exception as e:
            logger.error("Error getting tier statistics: %s", e)
            return {"error": f"Failed to get statistics: {e}"}

    def bulk_assign_tier(self, emails: list[str], tier: str, admin_email: str) -> dict[str, Any]:
        """Assign multiple users to a tier.

        Args:
            emails: List of email addresses
            tier: Target tier
            admin_email: Admin making the changes

        Returns:
            Dictionary with results
        """
        results: dict[str, Any] = {"successful": [], "failed": [], "total": len(emails)}

        for email in emails:
            success, msg = self.assign_user_tier(email.strip(), tier, admin_email)
            if success:
                results["successful"].append({"email": email, "message": msg})
            else:
                results["failed"].append({"email": email, "error": msg})

        return results

    def export_tier_configuration(self) -> str:
        """Export current tier configuration as JSON.

        Returns:
            JSON string with configuration
        """
        try:
            config_export = {
                "exported_at": datetime.now(UTC).isoformat(),
                "admin_emails": self.config_manager.config.admin_emails,
                "full_users": self.config_manager.config.full_users,
                "limited_users": self.config_manager.config.limited_users,
                "email_whitelist": self.config_manager.config.email_whitelist,
                "statistics": self.get_tier_statistics(),
                "changes_log": self.changes_log[-50:],  # Last 50 changes
            }

            return json.dumps(config_export, indent=2)

        except Exception as e:
            logger.error("Error exporting configuration: %s", e)
            return json.dumps({"error": f"Export failed: {e}"})

    def search_users(self, query: str) -> list[dict[str, Any]]:
        """Search users by email pattern.

        Args:
            query: Search query (email pattern)

        Returns:
            List of matching users
        """
        try:
            all_users = self.get_all_users()
            matching_users = []

            query_lower = query.lower()

            for tier, users in all_users.items():
                if isinstance(users, list):
                    for user in users:
                        if isinstance(user, dict) and "email" in user and query_lower in user["email"].lower():
                            user_info = user.copy()
                            user_info["current_tier"] = tier
                            matching_users.append(user_info)

            return matching_users

        except Exception as e:
            logger.error("Error searching users: %s", e)
            return []

    def get_changes_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent changes log.

        Args:
            limit: Maximum number of changes to return

        Returns:
            List of recent changes
        """
        return self.changes_log[-limit:] if self.changes_log else []

    def persist_changes(self) -> tuple[bool, str]:
        """Persist current tier configuration changes.

        This method updates the configuration manager and logs the changes.
        Note: Environment variable changes require application restart to take full effect.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Update the configuration manager's internal config
            # This will affect the current session immediately
            self.config_manager._validate_config()

            # Generate updated environment variables
            {
                "PROMPTCRAFT_ADMIN_EMAILS": ",".join(self.config_manager.config.admin_emails),
                "PROMPTCRAFT_FULL_USERS": ",".join(self.config_manager.config.full_users),
                "PROMPTCRAFT_LIMITED_USERS": ",".join(self.config_manager.config.limited_users),
            }

            # Log the configuration update
            logger.info("Persisting tier configuration changes")
            logger.info("Admin emails: %d", len(self.config_manager.config.admin_emails))
            logger.info("Full users: %d", len(self.config_manager.config.full_users))
            logger.info("Limited users: %d", len(self.config_manager.config.limited_users))

            # Add change to log
            self.changes_log.append(
                {
                    "action": "persist_config",
                    "admin": "system",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "changes_count": len(self.changes_log),
                },
            )

            return True, "Configuration changes applied to current session. Restart application for full effect."

        except Exception as e:
            logger.error("Error persisting changes: %s", e)
            return False, f"Failed to persist changes: {e}"

    def reload_configuration(self) -> tuple[bool, str]:
        """Reload configuration from environment/config files.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Recreate config manager to reload from environment
            # ConfigLoader imported at top level

            new_config = ConfigLoader.load_from_env()
            self.config_manager.config = new_config
            self.validator = self.config_manager.create_whitelist_validator()

            # Clear changes log since we've reloaded
            self.changes_log = []

            logger.info("Configuration reloaded from environment")
            return True, "Configuration successfully reloaded from environment"

        except Exception as e:
            logger.error("Error reloading configuration: %s", e)
            return False, f"Failed to reload configuration: {e}"

    def generate_env_file_updates(self) -> str:
        """Generate environment file updates that can be applied.

        Returns:
            String with environment variable updates
        """
        try:
            return f"""# User Tier Configuration - Updated {datetime.now(UTC).isoformat()}
# Generated by PromptCraft Admin Interface

# Admin Users (full access to all models and system features)
PROMPTCRAFT_ADMIN_EMAILS={','.join(self.config_manager.config.admin_emails)}

# Full Users (access to all models including premium)
PROMPTCRAFT_FULL_USERS={','.join(self.config_manager.config.full_users)}

# Limited Users (access to free models only)
PROMPTCRAFT_LIMITED_USERS={','.join(self.config_manager.config.limited_users)}

# Email whitelist (unchanged - managed via Cloudflare Access)
# PROMPTCRAFT_EMAIL_WHITELIST={','.join(self.config_manager.config.email_whitelist)}
"""

        except Exception as e:
            logger.error("Error generating env file updates: %s", e)
            return f"# Error generating environment updates: {e}"
