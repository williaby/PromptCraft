#!/usr/bin/env python3
"""
Claude Code Integration for Context7 Package Names

This script provides a simple interface for Claude Code to automatically
resolve Context7 package names from pyproject.toml dependencies.

Usage:
    python scripts/claude-context7-integration.py validate-package <package_name>
    python scripts/claude-context7-integration.py get-context7-call <package_name> [topic] [tokens]
    python scripts/claude-context7-integration.py check-all-deps
"""

import json
from pathlib import Path
import sys
from typing import Any


# Handle tomllib import for different Python versions
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: tomllib or tomli not available. Install with: pip install tomli")
        sys.exit(1)


class ClaudeContext7Integration:
    """Integration helper for Claude Code to use Context7 with proper package names."""

    def __init__(self):
        """Initialize with project configuration."""
        self.project_root = Path(__file__).parent.parent
        self.pyproject_file = self.project_root / "pyproject.toml"
        self.reference_file = self.project_root / "docs" / "context7-quick-reference.json"

        # Load configurations
        self.pyproject_deps = self._load_pyproject_dependencies()
        self.context7_mappings = self._load_context7_mappings()

    def _load_pyproject_dependencies(self) -> dict[str, str]:
        """Load dependencies from pyproject.toml."""
        try:
            with open(self.pyproject_file, "rb") as f:
                data = tomllib.load(f)
                deps = {}

                # Main dependencies
                main_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                for dep, version in main_deps.items():
                    if dep != "python":  # Skip Python version
                        deps[dep] = version

                # Dev dependencies
                dev_deps = (
                    data.get("tool", {}).get("poetry", {}).get("group", {}).get("dev", {}).get("dependencies", {})
                )
                for dep, version in dev_deps.items():
                    deps[f"{dep} (dev)"] = version

                return deps
        except Exception as e:
            print(f"Error loading pyproject.toml: {e}")
            return {}

    def _load_context7_mappings(self) -> dict[str, Any]:
        """Load Context7 package mappings."""
        try:
            with open(self.reference_file) as f:
                data = json.load(f)
                return data.get("context7_package_mappings", {})
        except Exception as e:
            print(f"Error loading Context7 mappings: {e}")
            return {}

    def get_package_base_name(self, package_spec: str) -> str:
        """Extract base package name from dependency specification."""
        # Handle extras like 'uvicorn[standard]' -> 'uvicorn'
        if "[" in package_spec:
            package_spec = package_spec.split("[")[0]

        # Handle dev marker
        if " (dev)" in package_spec:
            package_spec = package_spec.replace(" (dev)", "")

        return package_spec.strip()

    def validate_package(self, package_name: str) -> dict[str, Any]:
        """
        Validate a package and provide Context7 information.

        Returns:
            Dictionary with validation results and recommendations
        """
        base_name = self.get_package_base_name(package_name)
        result = {
            "package": base_name,
            "in_pyproject": base_name in [self.get_package_base_name(p) for p in self.pyproject_deps.keys()],
            "context7_status": "unknown",
            "context7_id": None,
            "trust_score": None,
            "recommendation": None,
        }

        verified = self.context7_mappings.get("verified_packages", {})
        pending = self.context7_mappings.get("pending_verification", {})

        if base_name in verified:
            pkg_info = verified[base_name]
            result.update(
                {
                    "context7_status": "verified",
                    "context7_id": pkg_info["context7_id"],
                    "trust_score": pkg_info["trust_score"],
                    "recommendation": f"Use Context7 ID: {pkg_info['context7_id']}",
                },
            )
        elif base_name in pending:
            result.update(
                {
                    "context7_status": "pending_verification",
                    "recommendation": f"Package needs verification. Use: mcp__context7-sse__resolve-library-id with libraryName: '{base_name}'",
                },
            )
        else:
            result.update(
                {
                    "context7_status": "not_mapped",
                    "recommendation": f"Package not in mappings. Search with: mcp__context7-sse__resolve-library-id with libraryName: '{base_name}'",
                },
            )

        return result

    def generate_context7_call(
        self,
        package_name: str,
        topic: str | None = None,
        tokens: int = 2000,
    ) -> str:
        """Generate a properly formatted Context7 call."""
        validation = self.validate_package(package_name)

        if validation["context7_status"] != "verified":
            return f"Error: {validation['recommendation']}"

        context7_id = validation["context7_id"]
        call_parts = [
            "mcp__context7-sse__get-library-docs",
            f'context7CompatibleLibraryID: "{context7_id}"',
            f"tokens: {tokens}",
        ]

        if topic:
            call_parts.append(f'topic: "{topic}"')

        return "\n".join(call_parts)

    def check_all_dependencies(self) -> dict[str, dict[str, Any]]:
        """Check all pyproject.toml dependencies against Context7 mappings."""
        results = {}

        for dep_spec in self.pyproject_deps.keys():
            base_name = self.get_package_base_name(dep_spec)
            results[base_name] = self.validate_package(base_name)

        return results

    def get_suggestions_for_claude(self, package_name: str) -> str:
        """Get Claude-friendly suggestions for using Context7 with a package."""
        validation = self.validate_package(package_name)
        base_name = validation["package"]

        if validation["context7_status"] == "verified":
            return f"""✅ Package '{base_name}' is verified for Context7.

Use this call:
```
{self.generate_context7_call(base_name)}
```

For specific topics, add: topic: "your_topic_here"
For more context, increase tokens (up to 10000)."""

        if validation["context7_status"] == "pending_verification":
            return f"""🔍 Package '{base_name}' needs verification.

First, resolve the Context7 ID:
```
mcp__context7-sse__resolve-library-id
libraryName: "{base_name}"
```

Then update the mappings in docs/context7-quick-reference.json"""

        return f"""❓ Package '{base_name}' not found in Context7 mappings.

Steps to add it:
1. Search for the package:
```
mcp__context7-sse__resolve-library-id
libraryName: "{base_name}"
```

2. Choose the option with highest trust score (9+ preferred)
3. Update docs/context7-quick-reference.json with the verified mapping"""


def main():
    """Command-line interface for Claude Code integration."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    integration = ClaudeContext7Integration()
    command = sys.argv[1]

    if command == "validate-package" and len(sys.argv) >= 3:
        package_name = sys.argv[2]
        result = integration.validate_package(package_name)

        print(f"Package: {result['package']}")
        print(f"In pyproject.toml: {result['in_pyproject']}")
        print(f"Context7 Status: {result['context7_status']}")
        if result["context7_id"]:
            print(f"Context7 ID: {result['context7_id']}")
            print(f"Trust Score: {result['trust_score']}")
        print(f"Recommendation: {result['recommendation']}")

    elif command == "get-context7-call" and len(sys.argv) >= 3:
        package_name = sys.argv[2]
        topic = sys.argv[3] if len(sys.argv) >= 4 else None
        tokens = int(sys.argv[4]) if len(sys.argv) >= 5 else 2000

        call = integration.generate_context7_call(package_name, topic, tokens)
        print(call)

    elif command == "check-all-deps":
        results = integration.check_all_dependencies()

        print("📦 Dependency Status Report:")
        print("=" * 50)

        verified = [(pkg, info) for pkg, info in results.items() if info["context7_status"] == "verified"]
        pending = [(pkg, info) for pkg, info in results.items() if info["context7_status"] == "pending_verification"]
        not_mapped = [(pkg, info) for pkg, info in results.items() if info["context7_status"] == "not_mapped"]

        if verified:
            print(f"\n✅ Verified ({len(verified)} packages):")
            for pkg, info in sorted(verified):
                print(
                    f"  {pkg:<20} -> {info['context7_id']} (trust: {info['trust_score']})",
                )

        if pending:
            print(f"\n🔍 Pending Verification ({len(pending)} packages):")
            for pkg, info in sorted(pending):
                print(f"  {pkg}")

        if not_mapped:
            print(f"\n❓ Not Mapped ({len(not_mapped)} packages):")
            for pkg, info in sorted(not_mapped):
                print(f"  {pkg}")

        print(
            f"\nSummary: {len(verified)} verified, {len(pending)} pending, {len(not_mapped)} unmapped",
        )

    elif command == "claude-help" and len(sys.argv) >= 3:
        package_name = sys.argv[2]
        suggestions = integration.get_suggestions_for_claude(package_name)
        print(suggestions)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
