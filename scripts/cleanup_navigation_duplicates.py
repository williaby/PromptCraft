#!/usr/bin/env python3
"""
Clean up duplicate navigation blocks in htmlcov files.
"""

from pathlib import Path


def cleanup_duplicates_in_file(file_path: str) -> bool:
    """
    Remove duplicate navigation blocks from a file.

    Args:
        file_path: Path to the HTML file to clean

    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        nav_block = """        <div style="background: #e8f4f8; border: 1px solid #007acc; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
            <strong style="color: #007acc;">📊 Enhanced Analysis:</strong>
            <a href="file://wsl.localhost/Ubuntu/home/byron/dev/PromptCraft/reports/coverage/index.html"
               style="color: #007acc; text-decoration: none; margin: 0 8px;">Dashboard</a>
            <span style="color: #666;">•</span>
            <a href="file://wsl.localhost/Ubuntu/home/byron/dev/PromptCraft/reports/coverage/by-type/index.html"
               style="color: #007acc; text-decoration: none; margin: 0 8px;">By Test Type</a>
        </div>"""

        # Count occurrences
        count = content.count(nav_block)

        if count <= 1:
            return False  # No duplicates

        # Keep only the first occurrence
        first_occurrence = content.find(nav_block)
        before_first = content[: first_occurrence + len(nav_block)]
        after_first = content[first_occurrence + len(nav_block) :]

        # Remove all subsequent occurrences
        cleaned_after = after_first.replace(nav_block, "")

        cleaned_content = before_first + cleaned_after

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

        print(f"✅ Cleaned {count-1} duplicates from: {Path(file_path).name}")
        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to clean up duplicates in all htmlcov files."""

    # Get htmlcov directory
    htmlcov_dir = Path("htmlcov")
    if not htmlcov_dir.exists():
        print("Error: htmlcov directory not found")
        return

    # Find all HTML files in htmlcov
    html_files = list(htmlcov_dir.glob("*.html"))

    if not html_files:
        print("No HTML files found in htmlcov directory")
        return

    cleaned_count = 0

    for html_file in html_files:
        if cleanup_duplicates_in_file(str(html_file)):
            cleaned_count += 1

    if cleaned_count == 0:
        print("📊 No duplicate navigation blocks found")
    else:
        print(f"\n📊 Cleaned duplicates from {cleaned_count} files")


if __name__ == "__main__":
    main()
