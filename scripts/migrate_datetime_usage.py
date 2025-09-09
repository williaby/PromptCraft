#!/usr/bin/env python3
"""
Automated migration script for datetime usage to fix DTZ005 errors.

This script analyzes Python files and automatically migrates datetime usage
from naive datetime.now() calls to timezone-aware alternatives using our
datetime_compat module.

Usage:
    python scripts/migrate_datetime_usage.py [--dry-run] [--src-only] [paths...]

Features:
- Context-aware replacements based on file type and usage patterns
- Safe backup creation before modifications
- Detailed reporting of changes made
- Support for dry-run mode to preview changes
- Handles both production and test code appropriately
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import sys


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class MigrationContext:
    """Context information for migration decisions."""
    file_path: Path
    is_test_file: bool
    is_src_file: bool
    has_database_imports: bool
    has_api_imports: bool
    has_caching_patterns: bool
    existing_datetime_compat: bool


@dataclass 
class ReplacementRule:
    """Rule for replacing datetime usage."""
    pattern: re.Pattern
    replacement: str
    import_needed: str
    context_filter: str | None = None


class DatetimeMigrationTool:
    """Tool for migrating datetime usage in Python files."""
    
    def __init__(self):
        self.replacements_made = 0
        self.files_modified = 0
        self.errors = []
        
        # Define replacement rules based on context
        self.replacement_rules = [
            # Direct datetime.now() calls
            ReplacementRule(
                pattern=re.compile(r"datetime\.now\(\)"),
                replacement="utc_now()",
                import_needed="utc_now",
                context_filter="general",
            ),
            
            # datetime.now() with timezone parameter (preserve existing)
            ReplacementRule(
                pattern=re.compile(r"datetime\.now\(([^)]+)\)"),
                replacement=r"datetime.now(\1)",  # Keep as-is, already has timezone
                import_needed="datetime",
                context_filter="already_has_tz",
            ),
            
            # Timestamp operations
            ReplacementRule(
                pattern=re.compile(r"datetime\.now\(\)\.timestamp\(\)"),
                replacement="timestamp_now()",
                import_needed="timestamp_now",
                context_filter="timestamp",
            ),
            
            # ISO format operations
            ReplacementRule(
                pattern=re.compile(r"datetime\.now\(\)\.isoformat\(\)"),
                replacement="to_iso(utc_now())",
                import_needed="utc_now, to_iso",
                context_filter="iso_format",
            ),
        ]
    
    def analyze_file_context(self, file_path: Path) -> MigrationContext:
        """Analyze file to determine migration context."""
        content = file_path.read_text(encoding="utf-8")
        
        context = MigrationContext(
            file_path=file_path,
            is_test_file="test" in str(file_path).lower(),
            is_src_file=str(file_path).startswith("src/"),
            has_database_imports=any(imp in content for imp in [
                "sqlalchemy", "database", "models", "db_session",
            ]),
            has_api_imports=any(imp in content for imp in [
                "fastapi", "flask", "django", "endpoint",
            ]),
            has_caching_patterns=any(pattern in content for pattern in [
                "cache", "ttl", "expire", "age_seconds",
            ]),
            existing_datetime_compat="datetime_compat" in content,
        )
        
        return context
    
    def determine_best_replacement(self, match: str, context: MigrationContext) -> tuple[str, str]:
        """Determine the best replacement for a datetime usage."""
        
        # Handle different patterns based on context
        if ".timestamp()" in match:
            return "timestamp_now()", "timestamp_now"
        
        if ".isoformat()" in match:
            return "to_iso(utc_now())", "utc_now, to_iso"
            
        if context.has_caching_patterns and "age" in match.lower():
            return "timestamp_now()", "timestamp_now"
            
        if context.is_test_file:
            # Test files should use utc_now for consistency
            return "utc_now()", "utc_now"
        
        if context.has_database_imports:
            # Database operations should use UTC
            return "utc_now()", "utc_now"
        
        if context.has_api_imports:
            # API responses might want local time, but UTC is safer
            return "utc_now()", "utc_now"
        
        # Default to UTC for safety
        return "utc_now()", "utc_now"
    
    def update_imports(self, content: str, imports_needed: set[str]) -> str:
        """Update imports in the file content."""
        lines = content.split("\n")
        
        # Check for existing datetime_compat imports
        has_datetime_compat_import = False
        datetime_compat_line_idx = None
        
        for i, line in enumerate(lines):
            if "from src.utils.datetime_compat import" in line:
                has_datetime_compat_import = True
                datetime_compat_line_idx = i
                break
        
        if has_datetime_compat_import:
            # Update existing import
            existing_line = lines[datetime_compat_line_idx]
            
            # Parse existing imports
            import_match = re.search(r"from src\.utils\.datetime_compat import (.+)", existing_line)
            if import_match:
                existing_imports = {imp.strip() for imp in import_match.group(1).split(",")}
                all_imports = existing_imports | imports_needed
                
                # Create new import line
                import_list = sorted(all_imports)
                if len(import_list) <= 3:
                    new_import = f"from src.utils.datetime_compat import {', '.join(import_list)}"
                else:
                    # Multi-line import for readability
                    new_import = "from src.utils.datetime_compat import (\n    " + \
                               ",\n    ".join(import_list) + ",\n)"
                
                lines[datetime_compat_line_idx] = new_import
        else:
            # Add new import after existing imports
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    insert_idx = i + 1
                elif line.strip() == "" and i > 0:
                    break
            
            # Create import line
            import_list = sorted(imports_needed)
            if len(import_list) <= 3:
                new_import = f"from src.utils.datetime_compat import {', '.join(import_list)}"
            else:
                new_import = "from src.utils.datetime_compat import (\n    " + \
                           ",\n    ".join(import_list) + ",\n)"
            
            lines.insert(insert_idx, new_import)
            lines.insert(insert_idx + 1, "")  # Add blank line
        
        return "\n".join(lines)
    
    def migrate_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Migrate a single file."""
        try:
            # Skip if file doesn't exist or isn't a Python file
            if not file_path.exists() or file_path.suffix != ".py":
                return False
            
            # Analyze file context
            context = self.analyze_file_context(file_path)
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            
            # Skip files that already use datetime_compat extensively
            if context.existing_datetime_compat:
                datetime_now_count = len(re.findall(r"datetime\.now\(\)", content))
                compat_usage_count = len(re.findall(r"utc_now\(\)", content))
                
                # If mostly migrated, skip
                if datetime_now_count < compat_usage_count:
                    print(f"⏭️  Skipping {file_path} (already mostly migrated)")
                    return False
            
            # Find datetime.now() usages
            datetime_now_pattern = re.compile(r"datetime\.now\(\)(?:\.(?:timestamp|isoformat)\(\))?")
            matches = list(datetime_now_pattern.finditer(content))
            
            if not matches:
                return False
                
            print(f"🔍 Processing {file_path} ({len(matches)} datetime.now() calls found)")
            
            # Track imports needed
            imports_needed = set()
            
            # Apply replacements
            offset = 0
            for match in matches:
                match_text = match.group(0)
                start_pos = match.start() + offset
                end_pos = match.end() + offset
                
                replacement, imports = self.determine_best_replacement(match_text, context)
                imports_needed.update(imp.strip() for imp in imports.split(","))
                
                # Apply replacement
                content = content[:start_pos] + replacement + content[end_pos:]
                offset += len(replacement) - len(match_text)
                self.replacements_made += 1
                
                print(f"  ✅ {match_text} → {replacement}")
            
            # Update imports if needed
            if imports_needed:
                content = self.update_imports(content, imports_needed)
            
            # Write changes (if not dry run)
            if not dry_run:
                # Create backup
                backup_path = file_path.with_suffix(file_path.suffix + ".backup")
                shutil.copy2(file_path, backup_path)
                
                # Write updated content
                file_path.write_text(content, encoding="utf-8")
                print(f"  💾 Updated {file_path} (backup: {backup_path})")
            else:
                print(f"  🔮 Would update {file_path} (dry run)")
            
            self.files_modified += 1
            return True
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def migrate_directory(self, directory: Path, dry_run: bool = False, patterns: list[str] = None) -> None:
        """Migrate all Python files in a directory."""
        patterns = patterns or ["**/*.py"]
        
        files_to_process = []
        for pattern in patterns:
            files_to_process.extend(directory.glob(pattern))
        
        # Sort files to process high-priority files first
        def priority_sort(path: Path) -> tuple[int, str]:
            path_str = str(path)
            
            # Priority levels (lower number = higher priority)
            if path_str.startswith("src/auth"):
                return (1, path_str)  # Authentication is critical
            if path_str.startswith("src/database"):
                return (2, path_str)  # Database operations
            if path_str.startswith("src/api"):
                return (3, path_str)  # API endpoints
            if path_str.startswith("src/core"):
                return (4, path_str)  # Core functionality
            if path_str.startswith("src/mcp_integration"):
                return (5, path_str)  # MCP integration
            if path_str.startswith("src/"):
                return (6, path_str)  # Other src files
            if "test" in path_str:
                return (10, path_str)  # Tests last
            return (20, path_str)  # Everything else
        
        files_to_process.sort(key=priority_sort)
        
        print(f"🚀 Starting migration of {len(files_to_process)} files")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
        print("=" * 60)
        
        for file_path in files_to_process:
            self.migrate_file(file_path, dry_run)
        
        print("=" * 60)
        print("📊 Migration Summary:")
        print(f"   Files modified: {self.files_modified}")
        print(f"   Replacements made: {self.replacements_made}")
        
        if self.errors:
            print(f"❌ Errors encountered: {len(self.errors)}")
            for error in self.errors:
                print(f"   {error}")
        
        if not dry_run and self.files_modified > 0:
            print("\n🔧 Next steps:")
            print("   1. Run tests: poetry run pytest")
            print("   2. Check linting: poetry run ruff check --select DTZ005")
            print("   3. Review changes: git diff")
            print("   4. Remove backups when satisfied: find . -name '*.py.backup' -delete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate datetime usage to fix DTZ005 errors")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them")
    parser.add_argument("--src-only", action="store_true", help="Only process src/ directory")
    parser.add_argument("paths", nargs="*", help="Specific paths to process (default: current directory)")
    
    args = parser.parse_args()
    
    # Determine paths to process
    if args.paths:
        paths = [Path(p) for p in args.paths]
    elif args.src_only:
        paths = [Path("src")]
    else:
        paths = [Path()]
    
    migration_tool = DatetimeMigrationTool()
    
    for path in paths:
        if path.is_file():
            migration_tool.migrate_file(path, args.dry_run)
        elif path.is_dir():
            migration_tool.migrate_directory(path, args.dry_run)
        else:
            print(f"❌ Path not found: {path}")
            sys.exit(1)


if __name__ == "__main__":
    main()