#!/usr/bin/env python3
"""
Cleanup script to organize coverage and test artifacts that are currently scattered at root level.
This script moves files to proper locations and creates an organized reports structure.
"""

import shutil
from pathlib import Path
import glob


def setup_reports_structure():
    """Create organized reports directory structure."""
    directories = [
        'reports',
        'reports/coverage',
        'reports/coverage/by-type', 
        'reports/junit',
        'reports/bandit',
        'reports/temp',
        'reports/archive'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created: {directory}/")
    
    return True


def organize_coverage_files():
    """Move coverage files to organized locations."""
    moved_files = []
    
    # Coverage XML files
    for file_path in glob.glob("coverage*.xml"):
        dest = Path("reports/coverage") / Path(file_path).name
        shutil.move(file_path, dest)
        moved_files.append(f"{file_path} → {dest}")
        print(f"📊 Moved coverage: {file_path} → {dest}")
    
    # JUnit XML files  
    for file_path in glob.glob("junit*.xml"):
        dest = Path("reports/junit") / Path(file_path).name
        shutil.move(file_path, dest)
        moved_files.append(f"{file_path} → {dest}")
        print(f"🧪 Moved junit: {file_path} → {dest}")
    
    return moved_files


def organize_security_files():
    """Move security scan files to organized locations."""
    moved_files = []
    
    # Bandit JSON files
    bandit_files = ["bandit-report.json", "bandit_report.json"]
    for file_name in bandit_files:
        if Path(file_name).exists():
            dest = Path("reports/bandit") / file_name
            shutil.move(file_name, dest)
            moved_files.append(f"{file_name} → {dest}")
            print(f"🔒 Moved bandit: {file_name} → {dest}")
    
    return moved_files


def organize_htmlcov_directories():
    """Move HTML coverage directories to organized structure."""
    moved_dirs = []
    
    # Standard htmlcov directory
    if Path("htmlcov").exists():
        dest = Path("reports/coverage/standard")
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move("htmlcov", dest)
        moved_dirs.append(f"htmlcov/ → {dest}/")
        print(f"📋 Moved htmlcov: htmlcov/ → {dest}/")
    
    # Type-specific htmlcov directory  
    if Path("htmlcov-by-type").exists():
        dest = Path("reports/coverage/by-type")
        # Move contents rather than the whole directory
        for item in Path("htmlcov-by-type").iterdir():
            item_dest = dest / item.name
            if item_dest.exists():
                if item_dest.is_dir():
                    shutil.rmtree(item_dest) 
                else:
                    item_dest.unlink()
            shutil.move(str(item), item_dest)
        
        # Remove empty source directory
        Path("htmlcov-by-type").rmdir()
        moved_dirs.append(f"htmlcov-by-type/ → {dest}/")
        print(f"📋 Moved htmlcov-by-type: htmlcov-by-type/ → {dest}/")
    
    return moved_dirs


def create_reports_index():
    """Create a master index for all reports."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PromptCraft Reports Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }
            .section { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .section h2 { color: #007acc; margin-top: 0; }
            .report-links { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
            .report-link { background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007acc; }
            .report-link a { text-decoration: none; color: #007acc; font-weight: bold; }
            .report-link a:hover { color: #005a9e; }
            .report-link p { margin: 5px 0 0 0; color: #666; font-size: 0.9em; }
            .file-structure { background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 PromptCraft Reports Dashboard</h1>
            
            <div class="file-structure">
                <h3>📁 Organized Reports Structure</h3>
                <p><strong>All test and coverage artifacts are now properly organized:</strong></p>
                <ul>
                    <li><code>reports/coverage/</code> - Coverage XML files and HTML reports</li>
                    <li><code>reports/coverage/by-type/</code> - Test-type specific coverage</li>
                    <li><code>reports/coverage/standard/</code> - Standard coverage report</li>
                    <li><code>reports/junit/</code> - JUnit XML test results</li>
                    <li><code>reports/bandit/</code> - Security scan results</li>
                    <li><code>reports/temp/</code> - Temporary files during generation</li>
                </ul>
            </div>

            <div class="section">
                <h2>📈 Coverage Reports</h2>
                <div class="report-links">
                    <div class="report-link">
                        <a href="coverage/standard/index.html">Standard Coverage Report</a>
                        <p>Complete project coverage analysis</p>
                    </div>
                    <div class="report-link">
                        <a href="coverage/by-type/index.html">Coverage by Test Type</a>
                        <p>Unit, integration, auth, performance breakdowns</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔒 Security Reports</h2>
                <div class="report-links">
                    <div class="report-link">
                        <a href="bandit/">Bandit Security Scans</a>
                        <p>Static security analysis results</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🧪 Test Results</h2>
                <div class="report-links">
                    <div class="report-link">
                        <a href="junit/">JUnit XML Reports</a>
                        <p>Detailed test execution results</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🧹 Cleanup Benefits</h2>
                <ul>
                    <li><strong>Root Directory:</strong> Clean of test artifacts</li>
                    <li><strong>Organization:</strong> Logical grouping by report type</li>
                    <li><strong>Easy Cleanup:</strong> <code>rm -rf reports/</code> removes everything</li>
                    <li><strong>CI/CD Friendly:</strong> Consistent paths for automation</li>
                    <li><strong>Version Control:</strong> Easy to ignore with <code>reports/</code> in .gitignore</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    index_file = Path("reports/index.html")
    index_file.write_text(html_content)
    print(f"📋 Created master index: {index_file}")


def update_gitignore():
    """Update .gitignore to include organized reports directory."""
    gitignore_path = Path(".gitignore")
    
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if "reports/" not in content:
            with gitignore_path.open("a") as f:
                f.write("\n# Generated reports (organized)\nreports/\n")
            print("📝 Updated .gitignore to ignore reports/ directory")
        else:
            print("📝 .gitignore already includes reports/ directory")
    else:
        gitignore_path.write_text("# Generated reports (organized)\nreports/\n")
        print("📝 Created .gitignore with reports/ directory")


def main():
    """Main cleanup function."""
    print("🧹 Organizing coverage and test artifacts")
    print("=" * 50)
    
    # Set up organized structure
    setup_reports_structure()
    print()
    
    # Move files to organized locations
    coverage_files = organize_coverage_files()
    security_files = organize_security_files()
    htmlcov_dirs = organize_htmlcov_directories()
    print()
    
    # Create master index
    create_reports_index()
    
    # Update .gitignore
    update_gitignore()
    
    # Summary
    total_moved = len(coverage_files) + len(security_files) + len(htmlcov_dirs)
    
    print(f"\n🎉 Cleanup completed successfully!")
    print(f"📁 Reports organized in: reports/")
    print(f"📊 Files moved: {total_moved}")
    print(f"🔗 Master index: reports/index.html")
    
    if total_moved > 0:
        print(f"\n📋 What was moved:")
        for item in coverage_files + security_files + htmlcov_dirs:
            print(f"  • {item}")
    
    print(f"\n💡 Next steps:")
    print(f"  • Use scripts/generate_test_type_coverage_clean.py for future reports")
    print(f"  • All new artifacts will be automatically organized")
    print(f"  • Root directory stays clean!")


if __name__ == "__main__":
    main()