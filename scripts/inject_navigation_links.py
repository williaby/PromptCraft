#!/usr/bin/env python3
"""
Inject navigation links into standard coverage.py HTML reports.

This script post-processes the htmlcov files to add navigation links
back to the enhanced coverage dashboard for easier navigation.
"""

from pathlib import Path


def inject_navigation_to_file(file_path: str, nav_html: str) -> bool:
    """
    Inject navigation HTML into a coverage file.

    Args:
        file_path: Path to the HTML file to modify
        nav_html: HTML content to inject

    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check if navigation is already present to avoid duplicate injection
        if "Enhanced Analysis:" in content:
            return False

        # Find the header content div and inject after the h1
        header_end = content.find("</h1>")
        if header_end == -1:
            print(f"Warning: Could not find </h1> tag in {file_path}")
            return False

        # Insert navigation after the h1 tag
        modified_content = content[: header_end + 5] + nav_html + content[header_end + 5 :]  # Include </h1>

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to inject navigation into all htmlcov files."""

    # Define navigation HTML
    nav_html = """
        <div style="background: #e8f4f8; border: 1px solid #007acc; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
            <strong style="color: #007acc;">Enhanced Analysis:</strong>
            <a href="file://wsl.localhost/Ubuntu/home/byron/dev/PromptCraft/reports/coverage/index.html"
               style="color: #007acc; text-decoration: none; margin: 0 8px;">Dashboard</a>
            <span style="color: #666;">•</span>
            <a href="file://wsl.localhost/Ubuntu/home/byron/dev/PromptCraft/reports/coverage/by-type/index.html"
               style="color: #007acc; text-decoration: none; margin: 0 8px;">By Test Type</a>
        </div>
    """

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

    modified_count = 0

    for html_file in html_files:
        if inject_navigation_to_file(str(html_file), nav_html):
            modified_count += 1
            print(f"✅ Enhanced: {html_file.name}")
        else:
            print(f"⚪ Skipped: {html_file.name}")

    print(f"\n📊 Summary: Enhanced {modified_count} files with navigation links")
    print("Users can now navigate back to the enhanced dashboard from standard coverage reports!")


if __name__ == "__main__":
    main()
