#!/usr/bin/env python3
"""
Clean emoji navigation blocks from htmlcov files.
"""

import re
from pathlib import Path


def clean_emoji_navigation(file_path: str) -> bool:
    """Remove navigation blocks containing emojis."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Remove navigation blocks that contain emojis
        pattern = r'<div style="background: #e8f4f8[^>]*>.*?📊 Enhanced Analysis:.*?</div>'
        if re.search(pattern, content, re.DOTALL):
            # Remove the navigation block
            new_content = re.sub(pattern, "", content, flags=re.DOTALL)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Clean all htmlcov files."""
    htmlcov_dir = Path("htmlcov")
    if not htmlcov_dir.exists():
        print("htmlcov directory not found")
        return

    html_files = list(htmlcov_dir.glob("*.html"))
    cleaned_count = 0

    for html_file in html_files:
        if clean_emoji_navigation(str(html_file)):
            cleaned_count += 1
            print(f"✅ Cleaned: {html_file.name}")
        else:
            print(f"⚪ Skipped: {html_file.name}")

    print(f"\n📊 Summary: Cleaned {cleaned_count} files")


if __name__ == "__main__":
    main()
