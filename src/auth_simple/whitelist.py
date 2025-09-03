"""Email whitelist management for simplified authentication.

This module provides email whitelist validation with domain support,
enabling authorization of specific emails or entire domains (@company.com).
Supports both individual email addresses and admin privilege detection.
"""

import logging
from dataclasses import dataclass

from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


@dataclass
class WhitelistEntry:
    """Represents a whitelist entry with metadata."""

    value: str  # Email or @domain.com
    is_domain: bool
    added_at: str
    description: str | None = None


class EmailWhitelistConfig(BaseModel):
    """Configuration for email whitelist validation."""

    whitelist: list[str] = []
    admin_emails: list[str] = []
    case_sensitive: bool = False

    @validator("whitelist", "admin_emails", pre=True)
    def normalize_emails(cls, v: str | list[str]) -> list[str]:  # noqa: N805
        """Normalize email addresses to lowercase unless case_sensitive."""
        if isinstance(v, str):
            v = [email.strip() for email in v.split(",") if email.strip()]
        return [email.strip().lower() for email in v] if v else []


class EmailWhitelistValidator:
    """Email whitelist validator with domain support.

    Validates email addresses against a whitelist that can contain:
    - Individual email addresses: user@example.com
    - Domain patterns: @company.com (allows any email from that domain)
    - Admin privilege detection for specific admin emails
    """

    def __init__(
        self,
        whitelist: list[str],
        admin_emails: list[str] | None = None,
        case_sensitive: bool = False,
    ) -> None:
        """Initialize the email whitelist validator.

        Args:
            whitelist: List of allowed emails and domains (e.g., ['user@example.com', '@company.com'])
            admin_emails: List of emails with admin privileges
            case_sensitive: Whether email matching should be case-sensitive
        """
        self.case_sensitive = case_sensitive
        self.admin_emails = self._normalize_emails(admin_emails or [])

        # Separate individual emails from domain patterns
        self.individual_emails = set()
        self.domain_patterns = set()

        for entry in self._normalize_emails(whitelist):
            if entry.startswith("@"):
                self.domain_patterns.add(entry)
            else:
                self.individual_emails.add(entry)

        logger.info(
            "Initialized email whitelist: %s individual emails, %s domain patterns, %s admin emails",
            len(self.individual_emails),
            len(self.domain_patterns),
            len(self.admin_emails),
        )

    def _normalize_emails(self, emails: list[str]) -> list[str]:
        """Normalize email list based on case sensitivity setting."""
        if not emails:
            return []

        normalized = []
        for email_item in emails:
            email = email_item.strip()
            if email:
                normalized.append(email if self.case_sensitive else email.lower())

        return normalized

    def _normalize_email(self, email: str) -> str:
        """Normalize a single email address."""
        return email.strip() if self.case_sensitive else email.strip().lower()

    def is_authorized(self, email: str) -> bool:
        """Check if email is authorized via whitelist.

        Args:
            email: Email address to validate

        Returns:
            True if email is authorized, False otherwise
        """
        if not email:
            return False

        normalized_email = self._normalize_email(email)

        # Check individual email whitelist
        if normalized_email in self.individual_emails:
            logger.debug("Email %s authorized via individual whitelist", email)
            return True

        # Check domain patterns
        if "@" in normalized_email:
            domain = "@" + normalized_email.split("@")[1]
            if domain in self.domain_patterns:
                logger.debug("Email %s authorized via domain pattern %s", email, domain)
                return True

        logger.debug("Email %s not authorized", email)
        return False

    def is_admin(self, email: str) -> bool:
        """Check if email has admin privileges.

        Args:
            email: Email address to check for admin privileges

        Returns:
            True if email is an admin, False otherwise
        """
        if not email:
            return False

        normalized_email = self._normalize_email(email)
        is_admin_user = normalized_email in self.admin_emails

        if is_admin_user:
            logger.debug("Email %s has admin privileges", email)

        return is_admin_user

    def get_user_role(self, email: str) -> str:
        """Get user role based on email.

        Args:
            email: Email address to check

        Returns:
            'admin', 'user', or 'unauthorized'
        """
        if not self.is_authorized(email):
            return "unauthorized"

        return "admin" if self.is_admin(email) else "user"

    def get_whitelist_stats(self) -> dict:
        """Get statistics about the current whitelist configuration.

        Returns:
            Dictionary with whitelist statistics
        """
        return {
            "individual_emails": len(self.individual_emails),
            "domain_patterns": len(self.domain_patterns),
            "admin_emails": len(self.admin_emails),
            "total_entries": len(self.individual_emails) + len(self.domain_patterns),
            "case_sensitive": self.case_sensitive,
            "domains": list(self.domain_patterns),
        }

    def validate_whitelist_config(self) -> list[str]:
        """Validate the whitelist configuration and return any warnings.

        Returns:
            List of warning messages about the configuration
        """
        warnings = []

        # Check for empty whitelist
        if not self.individual_emails and not self.domain_patterns:
            warnings.append("Whitelist is empty - no users will be authorized")

        # Check for admin emails not in whitelist
        for admin_email in self.admin_emails:
            if not self.is_authorized(admin_email):
                warnings.append(f"Admin email {admin_email} is not in whitelist")

        # Check for potential security issues
        if "@gmail.com" in self.domain_patterns or "@outlook.com" in self.domain_patterns:
            warnings.append("Public email domains (@gmail.com, @outlook.com) in whitelist may be insecure")

        return warnings


class WhitelistManager:
    """Manager for dynamic whitelist operations."""

    def __init__(self, validator: EmailWhitelistValidator) -> None:
        """Initialize whitelist manager with a validator."""
        self.validator = validator

    def add_email(self, email: str, is_admin: bool = False) -> bool:
        """Add email to whitelist (runtime operation).

        Note: This is for runtime operations. For persistent changes,
        update the configuration file directly.

        Args:
            email: Email to add
            is_admin: Whether email should have admin privileges

        Returns:
            True if email was added successfully
        """
        try:
            normalized_email = self.validator._normalize_email(email)

            if normalized_email.startswith("@"):
                self.validator.domain_patterns.add(normalized_email)
            else:
                self.validator.individual_emails.add(normalized_email)

            if is_admin:
                self.validator.admin_emails.append(normalized_email)

            logger.info("Added email %s to whitelist (admin: %s)", email, is_admin)
            return True

        except Exception as e:
            logger.error("Failed to add email %s to whitelist: %s", email, e)
            return False

    def remove_email(self, email: str) -> bool:
        """Remove email from whitelist (runtime operation).

        Args:
            email: Email to remove

        Returns:
            True if email was removed successfully
        """
        try:
            normalized_email = self.validator._normalize_email(email)

            # Remove from individual emails or domain patterns
            removed = False
            if normalized_email in self.validator.individual_emails:
                self.validator.individual_emails.remove(normalized_email)
                removed = True

            if normalized_email in self.validator.domain_patterns:
                self.validator.domain_patterns.remove(normalized_email)
                removed = True

            # Remove from admin emails if present
            if normalized_email in self.validator.admin_emails:
                self.validator.admin_emails.remove(normalized_email)

            if removed:
                logger.info("Removed email %s from whitelist", email)
            else:
                logger.warning("Email %s not found in whitelist", email)

            return removed

        except Exception as e:
            logger.error("Failed to remove email %s from whitelist: %s", email, e)
            return False

    def check_email(self, email: str) -> dict:
        """Check email status and provide detailed information.

        Args:
            email: Email to check

        Returns:
            Dictionary with email status information
        """
        return {
            "email": email,
            "is_authorized": self.validator.is_authorized(email),
            "is_admin": self.validator.is_admin(email),
            "role": self.validator.get_user_role(email),
            "normalized_email": self.validator._normalize_email(email),
        }


def create_validator_from_env(whitelist_str: str, admin_emails_str: str = "") -> EmailWhitelistValidator:
    """Create EmailWhitelistValidator from environment variable strings.

    Args:
        whitelist_str: Comma-separated string of emails/domains
        admin_emails_str: Comma-separated string of admin emails

    Returns:
        Configured EmailWhitelistValidator
    """
    whitelist = [email.strip() for email in whitelist_str.split(",") if email.strip()] if whitelist_str else []
    admin_emails = [email.strip() for email in admin_emails_str.split(",") if email.strip()] if admin_emails_str else []

    return EmailWhitelistValidator(whitelist=whitelist, admin_emails=admin_emails)
