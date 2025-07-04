#!/usr/bin/env python3
"""
Context7 Helper Script

This script provides utilities for working with Context7 package mappings,
eliminating the need to manually resolve library IDs.

Usage:
    python scripts/context7-helper.py get-id fastapi
    python scripts/context7-helper.py verify-package numpy
    python scripts/context7-helper.py list-verified
    python scripts/context7-helper.py list-pending
"""

import json
import sys
from pathlib import Path
from typing import Any


class Context7Helper:
    """Helper class for Context7 package ID management."""

    def __init__(self):
        """Initialize with the quick reference mappings."""
        self.reference_file = (
            Path(__file__).parent.parent / "docs" / "context7-quick-reference.json"
        )
        self.mappings = self._load_mappings()

    def _load_mappings(self) -> dict[str, Any]:
        """Load the Context7 package mappings from JSON file."""
        try:
            with open(self.reference_file) as f:
                data = json.load(f)
                return data.get("context7_package_mappings", {})
        except FileNotFoundError:
            print(f"Error: Reference file not found at {self.reference_file}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.reference_file}")
            return {}

    def get_context7_id(self, package_name: str) -> str | None:
        """
        Get the Context7 ID for a package.

        Args:
            package_name: The Python package name (e.g., 'fastapi')

        Returns:
            The Context7 ID (e.g., '/tiangolo/fastapi') or None if not found
        """
        verified = self.mappings.get("verified_packages", {})
        if package_name in verified:
            return verified[package_name]["context7_id"]
        return None

    def get_package_info(self, package_name: str) -> dict[str, Any] | None:
        """
        Get complete package information.

        Args:
            package_name: The Python package name

        Returns:
            Dictionary with package info or None if not found
        """
        verified = self.mappings.get("verified_packages", {})
        return verified.get(package_name)

    def is_verified(self, package_name: str) -> bool:
        """Check if a package is verified."""
        verified = self.mappings.get("verified_packages", {})
        return package_name in verified

    def needs_verification(self, package_name: str) -> bool:
        """Check if a package is in pending verification list."""
        pending = self.mappings.get("pending_verification", {})
        return package_name in pending

    def list_verified_packages(self) -> dict[str, str]:
        """Get all verified packages as dict of {package: context7_id}."""
        verified = self.mappings.get("verified_packages", {})
        return {pkg: info["context7_id"] for pkg, info in verified.items()}

    def list_pending_packages(self) -> dict[str, str]:
        """Get all pending packages as dict of {package: description}."""
        return self.mappings.get("pending_verification", {})

    def generate_context7_call(
        self, package_name: str, topic: str = None, tokens: int = 2000,
    ) -> str:
        """
        Generate a Context7 get-library-docs call.

        Args:
            package_name: The Python package name
            topic: Optional topic to focus on
            tokens: Number of tokens to retrieve

        Returns:
            Formatted Context7 call or error message
        """
        context7_id = self.get_context7_id(package_name)
        if not context7_id:
            return f"Error: Package '{package_name}' not found in verified mappings. Use resolve-library-id first."

        call = f"""mcp__context7-sse__get-library-docs
context7CompatibleLibraryID: "{context7_id}"
tokens: {tokens}"""

        if topic:
            call += f'\ntopic: "{topic}"'

        return call

    def update_mappings(
        self, package_name: str, context7_id: str, trust_score: float, notes: str = "",
    ):
        """
        Update the mappings file with a new verified package.

        Args:
            package_name: The Python package name
            context7_id: The Context7 ID
            trust_score: The trust score from Context7
            notes: Optional notes about the package
        """
        # Move from pending to verified
        pending = self.mappings.get("pending_verification", {})
        if package_name in pending:
            del pending[package_name]

        # Add to verified
        verified = self.mappings.setdefault("verified_packages", {})
        verified[package_name] = {
            "context7_id": context7_id,
            "trust_score": trust_score,
            "status": "verified",
            "notes": notes or f"Auto-verified {package_name}",
        }

        # Save back to file
        with open(self.reference_file, "w") as f:
            data = {"context7_package_mappings": self.mappings}
            json.dump(data, f, indent=2)

        print(f"Updated {package_name} -> {context7_id} (trust: {trust_score})")


def main():
    """Command-line interface for Context7 helper."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    helper = Context7Helper()
    command = sys.argv[1]

    if command == "get-id" and len(sys.argv) >= 3:
        package_name = sys.argv[2]
        context7_id = helper.get_context7_id(package_name)
        if context7_id:
            print(f"{package_name} -> {context7_id}")
        else:
            print(f"Package '{package_name}' not found in verified mappings")
            if helper.needs_verification(package_name):
                print("  -> Found in pending verification list")
            else:
                print("  -> Use resolve-library-id to find the correct Context7 ID")

    elif command == "verify-package" and len(sys.argv) >= 3:
        package_name = sys.argv[2]
        if helper.is_verified(package_name):
            info = helper.get_package_info(package_name)
            print(f"✅ {package_name} is verified:")
            print(f"   Context7 ID: {info['context7_id']}")
            print(f"   Trust Score: {info['trust_score']}")
            print(f"   Notes: {info['notes']}")
        elif helper.needs_verification(package_name):
            print(f"🔍 {package_name} needs verification")
        else:
            print(f"❓ {package_name} not found in mappings")

    elif command == "list-verified":
        verified = helper.list_verified_packages()
        print("✅ Verified packages:")
        for pkg, context7_id in sorted(verified.items()):
            print(f"  {pkg:<20} -> {context7_id}")

    elif command == "list-pending":
        pending = helper.list_pending_packages()
        print("🔍 Packages needing verification:")
        for pkg, desc in sorted(pending.items()):
            print(f"  {pkg:<20} - {desc}")

    elif command == "generate-call" and len(sys.argv) >= 3:
        package_name = sys.argv[2]
        topic = sys.argv[3] if len(sys.argv) >= 4 else None
        tokens = int(sys.argv[4]) if len(sys.argv) >= 5 else 2000

        call = helper.generate_context7_call(package_name, topic, tokens)
        print(call)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
