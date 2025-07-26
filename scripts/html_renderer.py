#!/usr/bin/env python3
"""
HTML Renderer Module

Generates sophisticated HTML coverage reports with sortable tables, keyboard shortcuts,
and file-explorer compatibility. Restores the previous functionality while using
data from a single test run.

Implements the consensus approach of embedded static assets and relative linking
for file-explorer compatibility.
"""

import time
from pathlib import Path
from typing import Any


class HTMLRenderer:
    """Generates HTML coverage reports with sophisticated functionality."""

    # Embedded CSS for sortable tables (coverage.py style)
    EMBEDDED_CSS = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin: 20px; background: #f5f5f5; line-height: 1.6;
    }
    .container {
        max-width: 1200px; margin: 0 auto; background: white;
        padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    h1 {
        color: #333; border-bottom: 3px solid #007acc;
        padding-bottom: 10px; margin-bottom: 20px;
    }

    /* Navigation and controls */
    .nav-controls {
        background: #f8f9fa; padding: 15px; border-radius: 5px;
        margin: 20px 0; display: flex; justify-content: space-between;
        align-items: center; flex-wrap: wrap;
    }
    .filter-container {
        display: flex; align-items: center; gap: 15px;
    }
    .filter-container input[type="text"] {
        padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px;
        font-size: 14px; min-width: 200px;
    }
    .filter-container label {
        display: flex; align-items: center; gap: 5px;
        font-size: 14px; cursor: pointer;
    }

    /* Sortable table styles */
    .coverage-table {
        width: 100%; border-collapse: collapse; margin: 20px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .coverage-table th {
        background: #007acc; color: white; padding: 12px 15px;
        text-align: left; font-weight: 600; cursor: pointer;
        user-select: none; position: relative;
    }
    .coverage-table th:hover { background: #005a99; }
    .coverage-table th.sortable::after {
        content: ' ↕'; opacity: 0.5; font-size: 12px;
    }
    .coverage-table th.sorted-asc::after {
        content: ' ↑'; opacity: 1; color: #fff;
    }
    .coverage-table th.sorted-desc::after {
        content: ' ↓'; opacity: 1; color: #fff;
    }

    .coverage-table td {
        padding: 10px 15px; border-bottom: 1px solid #e9ecef;
        vertical-align: middle;
    }
    .coverage-table tr:hover { background: #f8f9fa; }
    .coverage-table tr.hidden { display: none; }

    /* Coverage percentage styling */
    .coverage-high { color: #28a745; font-weight: bold; }
    .coverage-medium { color: #ffc107; font-weight: bold; }
    .coverage-low { color: #dc3545; font-weight: bold; }

    /* File links */
    .file-link {
        color: #007acc; text-decoration: none;
        border-bottom: 1px dotted #007acc;
    }
    .file-link:hover {
        text-decoration: none; color: #005a99;
        border-bottom: 1px solid #005a99;
    }

    /* Summary cards */
    .summary-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px; margin: 20px 0;
    }
    .summary-card {
        background: #f8f9fa; border: 1px solid #e9ecef;
        border-radius: 8px; padding: 20px; text-align: center;
    }
    .summary-card h3 { margin: 0 0 10px 0; color: #007acc; }
    .summary-card .stat { font-size: 24px; font-weight: bold; margin: 10px 0; }

    /* Keyboard shortcuts help */
    .help-panel {
        background: #e8f4fd; border: 1px solid #b3d9ff;
        padding: 15px; border-radius: 5px; margin: 20px 0;
        display: none;
    }
    .help-panel.show { display: block; }
    .help-panel h4 { margin: 0 0 10px 0; color: #007acc; }
    .help-panel kbd {
        background: #f1f3f4; border: 1px solid #dadce0;
        border-radius: 3px; padding: 2px 6px; font-size: 12px;
        font-family: monospace; margin: 0 2px;
    }

    /* Back navigation */
    .back-link {
        display: inline-block; margin-bottom: 20px; padding: 8px 16px;
        background: #6c757d; color: white; text-decoration: none;
        border-radius: 4px; font-size: 14px;
    }
    .back-link:hover { background: #5a6268; color: white; }

    /* Footer */
    .footer {
        margin-top: 40px; padding-top: 20px; border-top: 1px solid #e9ecef;
        color: #666; font-size: 14px; text-align: center;
    }
    """

    # Embedded JavaScript for table sorting and filtering
    EMBEDDED_JS = """
    // Table sorting functionality
    function initializeSorting() {
        const table = document.querySelector('.coverage-table');
        if (!table) return;

        const headers = table.querySelectorAll('th.sortable');
        headers.forEach((header, index) => {
            header.addEventListener('click', () => sortTable(index));
        });
    }

    function sortTable(columnIndex) {
        const table = document.querySelector('.coverage-table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr:not(.hidden)'));
        const header = table.querySelectorAll('th')[columnIndex];

        // Determine sort direction
        const isAsc = !header.classList.contains('sorted-asc');

        // Clear all sort indicators
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sorted-asc', 'sorted-desc');
        });

        // Set current sort indicator
        header.classList.add(isAsc ? 'sorted-asc' : 'sorted-desc');

        // Sort rows
        rows.sort((a, b) => {
            const aText = a.cells[columnIndex].textContent.trim();
            const bText = b.cells[columnIndex].textContent.trim();

            // Handle percentage columns
            if (aText.includes('%') && bText.includes('%')) {
                const aVal = parseFloat(aText.replace('%', ''));
                const bVal = parseFloat(bText.replace('%', ''));
                return isAsc ? aVal - bVal : bVal - aVal;
            }

            // Handle numeric columns
            const aNum = parseFloat(aText.replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(bText.replace(/[^0-9.-]/g, ''));
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAsc ? aNum - bNum : bNum - aNum;
            }

            // String comparison
            return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
        });

        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    }

    // Table filtering functionality
    function initializeFiltering() {
        const filterInput = document.getElementById('filter');
        const hideFullyBtn = document.getElementById('hide-fully-covered');

        if (filterInput) {
            filterInput.addEventListener('input', applyFilters);
        }
        if (hideFullyBtn) {
            hideFullyBtn.addEventListener('change', applyFilters);
        }
    }

    function applyFilters() {
        const filterText = document.getElementById('filter')?.value.toLowerCase() || '';
        const hideFully = document.getElementById('hide-fully-covered')?.checked || false;
        const rows = document.querySelectorAll('.coverage-table tbody tr');

        rows.forEach(row => {
            const fileCell = row.cells[0]?.textContent.toLowerCase() || '';
            const coverageCell = row.cells[row.cells.length - 1]?.textContent || '';
            const coverage = parseFloat(coverageCell.replace('%', ''));

            const matchesFilter = fileCell.includes(filterText);
            const isFullyCovered = coverage >= 100;

            if (matchesFilter && (!hideFully || !isFullyCovered)) {
                row.classList.remove('hidden');
            } else {
                row.classList.add('hidden');
            }
        });

        updateFilterStatus();
    }

    function updateFilterStatus() {
        const totalRows = document.querySelectorAll('.coverage-table tbody tr').length;
        const visibleRows = document.querySelectorAll('.coverage-table tbody tr:not(.hidden)').length;
        const statusEl = document.getElementById('filter-status');

        if (statusEl) {
            statusEl.textContent = `Showing ${visibleRows} of ${totalRows} files`;
        }
    }

    // Keyboard shortcuts
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;

            switch(e.key.toLowerCase()) {
                case 'f':
                    e.preventDefault();
                    document.getElementById('filter')?.focus();
                    break;
                case 'h':
                    e.preventDefault();
                    toggleHelp();
                    break;
                case '?':
                    e.preventDefault();
                    toggleHelp();
                    break;
            }
        });
    }

    function toggleHelp() {
        const helpPanel = document.getElementById('help-panel');
        if (helpPanel) {
            helpPanel.classList.toggle('show');
        }
    }

    // Initialize all functionality when DOM is loaded
    document.addEventListener('DOMContentLoaded', () => {
        initializeSorting();
        initializeFiltering();
        initializeKeyboardShortcuts();
        updateFilterStatus();
    });
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "coverage"

    def get_coverage_class(self, percentage: float) -> str:
        """Get CSS class based on coverage percentage."""
        if percentage >= 80:
            return "coverage-high"
        if percentage >= 60:
            return "coverage-medium"
        return "coverage-low"

    def generate_main_index(
        self,
        coverage_data: dict[str, Any],
        test_distribution: dict[str, int],
        test_type_coverage: dict[str, dict[str, Any]],
    ) -> str:
        """Generate the main index.html page."""
        overall = coverage_data.get("overall", {})
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Generate test type cards
        test_type_cards = []
        test_icons = {
            "unit": "🧪",
            "integration": "🔗",
            "auth": "🔐",
            "performance": "🏃‍♂️",
            "stress": "💪",
            "security": "🛡️",
            "e2e": "🌐",
            "other": "📋",
        }

        for test_type, count in test_distribution.items():
            if count > 0:
                type_coverage = test_type_coverage.get(test_type, {}).get("overall", {})
                coverage_pct = type_coverage.get("percentage", 0)
                coverage_class = self.get_coverage_class(coverage_pct)
                icon = test_icons.get(test_type, "📋")

                test_type_cards.append(
                    f"""
                <div class="summary-card">
                    <h3>{icon} {test_type.title()} Tests</h3>
                    <div class="stat {coverage_class}">{coverage_pct:.1f}%</div>
                    <p>{count} tests executed</p>
                    <a href="by-type/{test_type}/index.html" class="file-link">View Details →</a>
                </div>""",
                )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptCraft Coverage Reports</title>
    <style>{self.EMBEDDED_CSS}</style>
</head>
<body>
    <div class="container">
        <h1>📊 PromptCraft Coverage Reports</h1>

        <div class="nav-controls">
            <div>
                <strong>Generated:</strong> {timestamp} •
                <strong>Source:</strong> VS Code "Run Tests with Coverage"
            </div>
            <button onclick="toggleHelp()" style="padding: 6px 12px; background: #007acc; color: white; border: none; border-radius: 4px; cursor: pointer;">
                Show Shortcuts (?)
            </button>
        </div>

        <div id="help-panel" class="help-panel">
            <h4>⌨️ Keyboard Shortcuts</h4>
            <p>
                <kbd>f</kbd> Focus filter box •
                <kbd>h</kbd> or <kbd>?</kbd> Toggle this help •
                Click column headers to sort
            </p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>📈 Overall Coverage</h3>
                <div class="stat {self.get_coverage_class(overall.get('percentage', 0))}">{overall.get('percentage', 0):.1f}%</div>
                <p>{overall.get('lines_covered', 0):,} / {overall.get('lines_valid', 0):,} lines</p>
                <a href="standard/index.html" class="file-link">View Standard Report →</a>
            </div>
            {''.join(test_type_cards)}
        </div>

        <div class="nav-controls">
            <h3>📋 Additional Reports</h3>
            <p>
                <a href="standard/index.html" class="file-link">Standard Coverage Report</a> •
                <a href="by-type/index.html" class="file-link">All Test Types</a> •
                <a href="enhanced-analysis.html" class="file-link">Enhanced Analysis</a>
            </p>
        </div>

        <div class="footer">
            <p>Generated automatically by VS Code integration • File-explorer compatible • No server required</p>
        </div>
    </div>

    <script>{self.EMBEDDED_JS}</script>
</body>
</html>"""

    def generate_by_type_index(
        self,
        test_distribution: dict[str, int],
        test_type_coverage: dict[str, dict[str, Any]],
    ) -> str:
        """Generate the by-type index page."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Generate cards for each test type
        type_cards = []
        test_icons = {
            "unit": "🧪",
            "integration": "🔗",
            "auth": "🔐",
            "performance": "🏃‍♂️",
            "stress": "💪",
            "security": "🛡️",
            "e2e": "🌐",
            "other": "📋",
        }

        for test_type, count in sorted(test_distribution.items()):
            if count > 0:
                type_coverage = test_type_coverage.get(test_type, {}).get("overall", {})
                coverage_pct = type_coverage.get("percentage", 0)
                coverage_class = self.get_coverage_class(coverage_pct)
                icon = test_icons.get(test_type, "📋")

                type_cards.append(
                    f"""
                <div class="summary-card">
                    <h3>{icon} {test_type.title()} Tests</h3>
                    <div class="stat {coverage_class}">{coverage_pct:.1f}%</div>
                    <p>{count} tests • {type_coverage.get('lines_covered', 0):,} / {type_coverage.get('lines_valid', 0):,} lines</p>
                    <a href="{test_type}/index.html" class="file-link">View Detailed Report →</a>
                </div>""",
                )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Reports by Test Type</title>
    <style>{self.EMBEDDED_CSS}</style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">← Back to Overview</a>

        <h1>📊 Coverage Reports by Test Type</h1>

        <div class="nav-controls">
            <div>
                <strong>Generated:</strong> {timestamp} •
                <strong>Auto-updated</strong> from VS Code test runs
            </div>
        </div>

        <div class="summary-grid">
            {''.join(type_cards)}
        </div>

        <div class="nav-controls">
            <h3>📋 How to Use These Reports</h3>
            <ul style="text-align: left; max-width: 600px; margin: 0 auto;">
                <li><strong>Coverage Percentages:</strong> Show lines covered by each test type</li>
                <li><strong>Detailed Reports:</strong> Click any card to see file-by-file breakdown</li>
                <li><strong>Sortable Tables:</strong> Click column headers to sort data</li>
                <li><strong>File-Explorer Links:</strong> All links work without a server</li>
            </ul>
        </div>

        <div class="footer">
            <p>Reports update automatically when you run "Tests with Coverage" in VS Code</p>
        </div>
    </div>

    <script>{self.EMBEDDED_JS}</script>
</body>
</html>"""

    def generate_test_type_detail(self, test_type: str, coverage_data: dict[str, Any], test_count: int) -> str:
        """Generate detailed report for a specific test type."""
        overall = coverage_data.get("overall", {})
        files_coverage = coverage_data.get("files", {})
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        test_icons = {
            "unit": "🧪",
            "integration": "🔗",
            "auth": "🔐",
            "performance": "🏃‍♂️",
            "stress": "💪",
            "security": "🛡️",
            "e2e": "🌐",
            "other": "📋",
        }
        icon = test_icons.get(test_type, "📋")

        # Generate file rows
        file_rows = []
        for filename, file_data in sorted(files_coverage.items(), key=lambda x: x[1]["percentage"]):
            coverage_class = self.get_coverage_class(file_data["percentage"])
            # Generate link to standard coverage HTML
            html_filename = self.get_coverage_html_filename(filename)

            file_rows.append(
                f"""
            <tr>
                <td><a href="../../standard/{html_filename}" class="file-link" title="{filename}">{filename}</a></td>
                <td class="{coverage_class}">{file_data['percentage']:.1f}%</td>
                <td>{file_data['lines_covered']}</td>
                <td>{file_data['lines_valid']}</td>
                <td>{file_data['lines_valid'] - file_data['lines_covered']}</td>
            </tr>""",
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{test_type.title()} Test Coverage Report</title>
    <style>{self.EMBEDDED_CSS}</style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">← Back to Test Types</a>

        <h1>{icon} {test_type.title()} Test Coverage Report</h1>

        <div class="nav-controls">
            <div class="filter-container">
                <input type="text" id="filter" placeholder="Filter files...">
                <label>
                    <input type="checkbox" id="hide-fully-covered">
                    Hide 100% covered files
                </label>
                <span id="filter-status"></span>
            </div>
            <button onclick="toggleHelp()">Show Shortcuts (?)</button>
        </div>

        <div id="help-panel" class="help-panel">
            <h4>⌨️ Keyboard Shortcuts</h4>
            <p>
                <kbd>f</kbd> Focus filter •
                <kbd>h</kbd> or <kbd>?</kbd> Toggle help •
                Click column headers to sort •
                Click file names for detailed line coverage
            </p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>📈 {test_type.title()} Coverage</h3>
                <div class="stat {self.get_coverage_class(overall.get('percentage', 0))}">{overall.get('percentage', 0):.1f}%</div>
                <p>{overall.get('lines_covered', 0):,} / {overall.get('lines_valid', 0):,} lines</p>
            </div>
            <div class="summary-card">
                <h3>🧪 Tests Executed</h3>
                <div class="stat">{test_count}</div>
                <p>{test_type} tests in this category</p>
            </div>
            <div class="summary-card">
                <h3>📁 Files Analyzed</h3>
                <div class="stat">{len(files_coverage)}</div>
                <p>source files with coverage data</p>
            </div>
        </div>

        <table class="coverage-table">
            <thead>
                <tr>
                    <th class="sortable">File</th>
                    <th class="sortable">Coverage</th>
                    <th class="sortable">Covered</th>
                    <th class="sortable">Total</th>
                    <th class="sortable">Missing</th>
                </tr>
            </thead>
            <tbody>
                {''.join(file_rows)}
            </tbody>
        </table>

        <div class="footer">
            <p>Generated: {timestamp} • Click file names for line-by-line coverage details</p>
        </div>
    </div>

    <script>{self.EMBEDDED_JS}</script>
</body>
</html>"""

    def get_coverage_html_filename(self, filepath: str) -> str:
        """Convert a source file path to its coverage HTML filename."""
        # Coverage.py generates HTML files with specific naming patterns
        filename = Path(filepath).stem

        # Look for existing HTML files in standard directory
        standard_dir = self.reports_dir / "standard"
        if standard_dir.exists():
            pattern = f"*{filename}*.html"
            matching_files = list(standard_dir.glob(pattern))
            if matching_files:
                return matching_files[0].name

        # Fallback: generate expected filename
        return f"{filename}_py.html"

    def save_html_file(self, content: str, filepath: Path) -> None:
        """Save HTML content to file, creating directories as needed."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        print(f"✅ Generated: {filepath}")


if __name__ == "__main__":
    # Test the renderer
    renderer = HTMLRenderer()

    # Test data
    test_coverage = {
        "overall": {"percentage": 75.5, "lines_covered": 1500, "lines_valid": 2000},
        "files": {
            "src/auth/models.py": {"percentage": 80.0, "lines_covered": 40, "lines_valid": 50},
            "src/core/vector_store.py": {"percentage": 45.0, "lines_covered": 90, "lines_valid": 200},
        },
    }

    test_distribution = {"unit": 100, "auth": 25, "integration": 15}
    test_type_coverage = {
        "unit": {"overall": {"percentage": 85.0, "lines_covered": 850, "lines_valid": 1000}},
        "auth": {"overall": {"percentage": 65.0, "lines_covered": 325, "lines_valid": 500}},
    }

    # Generate sample main index
    main_html = renderer.generate_main_index(test_coverage, test_distribution, test_type_coverage)
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tmp_file:
        tmp_file.write(main_html)
        sample_file = Path(tmp_file.name)
    print(f"✅ Test HTML generated: {sample_file}")
