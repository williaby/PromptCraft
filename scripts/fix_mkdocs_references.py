#!/usr/bin/env python3
"""
Fix broken references in mkdocs.yml by checking file existence and suggesting alternatives.

This script validates all .md file references in mkdocs.yml and provides
fixes for broken links by finding the closest matching files.
"""

from difflib import get_close_matches
from pathlib import Path
import re


def extract_md_references(mkdocs_path: Path) -> list[str]:
    """Extract all .md file references from mkdocs.yml."""
    with open(mkdocs_path, encoding="utf-8") as f:
        content = f.read()

    # Extract .md files from the nav section and other references
    md_files = re.findall(r"([^:\s]+\.md)", content)
    return list(set(md_files))  # Remove duplicates


def find_existing_docs(docs_dir: Path) -> list[str]:
    """Find all existing .md files in the docs directory."""
    md_files = []
    for md_file in docs_dir.rglob("*.md"):
        # Get relative path from docs directory
        rel_path = md_file.relative_to(docs_dir)
        md_files.append(str(rel_path))
    return sorted(md_files)


def find_best_match(missing_file: str, existing_files: list[str]) -> list[str]:
    """Find the best matches for a missing file."""
    # Try exact filename match first
    filename = Path(missing_file).name
    exact_matches = [f for f in existing_files if Path(f).name == filename]

    if exact_matches:
        return exact_matches[:3]

    # Try close matches on full path
    close_matches = get_close_matches(missing_file, existing_files, n=3, cutoff=0.6)

    if not close_matches:
        # Try close matches on filename only
        close_matches = get_close_matches(filename, [Path(f).name for f in existing_files], n=3, cutoff=0.6)
        # Find the full paths
        if close_matches:
            full_path_matches = []
            for match in close_matches:
                full_paths = [f for f in existing_files if Path(f).name == match]
                full_path_matches.extend(full_paths)
            return full_path_matches[:3]

    return close_matches


def validate_mkdocs_references(mkdocs_path: Path, docs_dir: Path) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Validate all references in mkdocs.yml and return valid/invalid lists."""
    references = extract_md_references(mkdocs_path)
    existing_files = find_existing_docs(docs_dir)

    valid_files = []
    broken_files = []

    for ref in references:
        ref_path = docs_dir / ref
        if ref_path.exists():
            valid_files.append(ref)
        else:
            suggestions = find_best_match(ref, existing_files)
            broken_files.append((ref, suggestions))

    return valid_files, broken_files


def generate_fixed_mkdocs(mkdocs_path: Path, fixes: dict[str, str]) -> str:
    """Generate updated mkdocs.yml content with fixes applied."""
    with open(mkdocs_path, encoding="utf-8") as f:
        content = f.read()

    for broken, fixed in fixes.items():
        content = content.replace(broken, fixed)

    return content


def create_missing_stub_file(docs_dir: Path, file_path: str, title: str = None) -> None:
    """Create a stub file for missing documentation."""
    full_path = docs_dir / file_path

    # Ensure directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if title is None:
        title = Path(file_path).stem.replace("-", " ").replace("_", " ").title()

    content = f"""# {title}

> **Note:** This documentation file is currently under development.

## Overview

This section will contain information about {title.lower()}.

## Coming Soon

- Detailed documentation
- Examples and usage guides
- Best practices

---

*This file was auto-generated during documentation cleanup. Please update with actual content.*
"""

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Created stub file: {file_path}")


def main():
    """Main function to validate and fix mkdocs references."""
    project_root = Path(__file__).parent.parent
    mkdocs_path = project_root / "mkdocs.yml"
    docs_dir = project_root / "docs"

    print("🔍 Validating mkdocs.yml references...\n")

    if not mkdocs_path.exists():
        print(f"❌ mkdocs.yml not found at {mkdocs_path}")
        return 1

    if not docs_dir.exists():
        print(f"❌ docs directory not found at {docs_dir}")
        return 1

    valid_files, broken_files = validate_mkdocs_references(mkdocs_path, docs_dir)

    # Report findings
    print("📊 Validation Results:")
    print(f"   ✅ Valid references: {len(valid_files)}")
    print(f"   ❌ Broken references: {len(broken_files)}")
    print()

    if not broken_files:
        print("🎉 All mkdocs.yml references are valid!")
        return 0

    print("❌ Broken References Found:")
    print("=" * 50)

    fixes = {}
    create_stubs = []

    for broken_file, suggestions in broken_files:
        print(f"\n❌ Missing: {broken_file}")

        if suggestions:
            print("   📋 Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"      {i}. {suggestion}")

            # Auto-select best match if confidence is high
            best_match = suggestions[0]
            if broken_file.split("/")[-1] == best_match.split("/")[-1]:
                fixes[broken_file] = best_match
                print(f"   🔧 Auto-fix: {broken_file} → {best_match}")
            else:
                print(f"   💡 Suggested fix: {broken_file} → {best_match}")
                # Don't auto-apply if not confident
        else:
            print("   💭 No similar files found")
            # Consider creating a stub file
            create_stubs.append(broken_file)

    # Apply automatic fixes
    if fixes:
        print(f"\n🔧 Applying {len(fixes)} automatic fixes...")

        # Load and update mkdocs.yml
        with open(mkdocs_path, encoding="utf-8") as f:
            content = f.read()

        for broken, fixed in fixes.items():
            content = content.replace(broken, fixed)
            print(f"   ✅ {broken} → {fixed}")

        # Write back the fixed content
        with open(mkdocs_path, "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ Updated mkdocs.yml with fixes")

    # Offer to create stub files
    if create_stubs:
        print(f"\n📝 Creating stub files for {len(create_stubs)} missing documents...")

        for stub_file in create_stubs:
            create_missing_stub_file(docs_dir, stub_file)

    # Final validation
    print("\n🔍 Re-validating after fixes...")
    valid_files, broken_files = validate_mkdocs_references(mkdocs_path, docs_dir)

    if broken_files:
        print(f"⚠️  {len(broken_files)} references still broken after automatic fixes:")
        for broken_file, _ in broken_files:
            print(f"   ❌ {broken_file}")
        print("\n💡 Consider manually reviewing these references or creating the missing files.")
        return 1
    print("🎉 All mkdocs.yml references are now valid!")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
