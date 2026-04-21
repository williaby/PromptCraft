#!/usr/bin/env python3
"""
Test-specific datetime migration tool for fixing DTZ005 errors in test files.

This script migrates datetime.now() calls in test files to use timezone-aware alternatives,
with special handling for test patterns like MockDatetime contexts and deterministic testing.
"""

import argparse
import logging
from pathlib import Path
import re


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


class TestDatetimeMigrationTool:
    """Tool for migrating datetime usage in test files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Test-specific replacements
        self.test_replacements = [
            # Cache timestamp patterns
            (r"(\w+\._cache_timestamp\s*=\s*)datetime\.now\(\)", r"\1utc_now()"),
            # Authentication timestamps
            (r'("authenticated_at":\s*)datetime\.now\(\)', r"\1utc_now()"),
            # General variable assignments
            (r"(\w+\s*=\s*)datetime\.now\(\)", r"\1utc_now()"),
            # Direct datetime.now() calls
            (r"datetime\.now\(\)(?!\s*-|\s*\+)", r"utc_now()"),  # Not followed by arithmetic
            # Arithmetic with datetime.now() - keep for MockDatetime context
            (r"datetime\.now\(\)(\s*[-+]\s*timedelta\([^)]+\))", r"utc_now()\1"),
        ]

    def needs_datetime_compat_import(self, content: str) -> bool:
        """Check if file needs datetime_compat import."""
        return "utc_now" in content and "from src.utils.datetime_compat import" not in content

    def add_datetime_compat_import(self, content: str) -> str:
        """Add import for datetime_compat utilities."""
        lines = content.split("\n")

        # Skip docstring first
        in_docstring = False
        docstring_end_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                else:
                    docstring_end_idx = i + 1
                    break
            elif in_docstring and (line.strip().endswith('"""') or line.strip().endswith("'''")):
                docstring_end_idx = i + 1
                break

        # Find existing imports after docstring
        import_insert_idx = docstring_end_idx
        last_import_idx = docstring_end_idx

        # Look for existing imports and find where to insert our import
        for i in range(docstring_end_idx, len(lines)):
            line = lines[i].strip()
            if line.startswith(("from src.", "import src.")):
                # Insert before src imports
                if import_insert_idx == docstring_end_idx:
                    import_insert_idx = i
                break
            if line.startswith(("from ", "import ")):
                last_import_idx = i + 1
            elif line == "" or line.startswith("#"):
                continue
            else:
                # First non-import, non-blank, non-comment line
                if import_insert_idx == docstring_end_idx:
                    import_insert_idx = last_import_idx
                break

        if import_insert_idx == docstring_end_idx:
            import_insert_idx = last_import_idx

        # Insert the import
        import_line = "from src.utils.datetime_compat import utc_now"
        lines.insert(import_insert_idx, import_line)
        return "\n".join(lines)

    def migrate_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Migrate a single test file."""
        try:
            content = file_path.read_text()
            original_content = content

            # Apply replacements
            replacements_made = 0
            for pattern, replacement in self.test_replacements:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    replacements_made += count
                    self.logger.debug(f"Applied pattern '{pattern}' {count} times")

            if replacements_made == 0:
                return False

            # Add import if needed
            if self.needs_datetime_compat_import(content):
                content = self.add_datetime_compat_import(content)
                self.logger.debug("Added datetime_compat import")

            if dry_run:
                self.logger.info(f"Would migrate {file_path}: {replacements_made} replacements")
                return True

            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            backup_path.write_text(original_content)

            # Write migrated content
            file_path.write_text(content)
            self.logger.info(f"Migrated {file_path}: {replacements_made} replacements")
            return True

        except Exception as e:
            self.logger.error(f"Failed to migrate {file_path}: {e}")
            return False

    def find_test_files_with_datetime_now(self, base_path: Path) -> list[Path]:
        """Find test files containing datetime.now() calls."""
        test_files = []
        for file_path in base_path.rglob("test_*.py"):
            try:
                content = file_path.read_text()
                if "datetime.now()" in content:
                    test_files.append(file_path)
            except Exception as e:
                self.logger.warning(f"Could not read {file_path}: {e}")

        return sorted(test_files)

    def migrate_test_directory(self, test_dir: Path, dry_run: bool = False) -> dict[str, int]:
        """Migrate all test files in a directory."""
        results = {"migrated": 0, "skipped": 0, "failed": 0}

        test_files = self.find_test_files_with_datetime_now(test_dir)
        self.logger.info(f"Found {len(test_files)} test files with datetime.now() calls")

        for file_path in test_files:
            try:
                if self.migrate_file(file_path, dry_run):
                    results["migrated"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                results["failed"] += 1

        return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Migrate datetime.now() usage in test files to timezone-aware alternatives",
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path("tests"),
        help="Path to test directory or specific test file",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    tool = TestDatetimeMigrationTool()

    if args.path.is_file():
        # Migrate single file
        success = tool.migrate_file(args.path, args.dry_run)
        if success:
            print(f"✅ Successfully processed {args.path}")
        else:
            print(f"❌ No changes needed for {args.path}")
    else:
        # Migrate directory
        results = tool.migrate_test_directory(args.path, args.dry_run)
        print("\nMigration Results:")
        print(f"✅ Migrated: {results['migrated']} files")
        print(f"⏭️  Skipped: {results['skipped']} files")
        print(f"❌ Failed: {results['failed']} files")

        if args.dry_run:
            print("\n🔍 Dry run completed. Use --dry-run=false to apply changes.")


if __name__ == "__main__":
    main()
