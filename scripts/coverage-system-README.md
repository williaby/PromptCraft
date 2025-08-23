# PromptCraft Coverage System - Core Components

## Overview

This directory contains the core coverage automation system that provides automatic coverage
report generation when running tests with coverage in VS Code.

## Core Components ✅

### 1. `vscode_coverage_hook.py` - Main Hook Script

- **Purpose**: Triggered automatically after VS Code runs "Run Tests with Coverage"
- **Function**: Calls both fast and simplified report generators
- **Integration**: Used by pytest plugin and VS Code tasks
- **Status**: CORE COMPONENT - DO NOT REMOVE

### 2. `generate_test_coverage_fast.py` - Fast Report Generator

- **Purpose**: Generates detailed coverage reports with test-type classification
- **Function**: Creates enhanced HTML reports with navigation
- **Called by**: `vscode_coverage_hook.py`
- **Status**: CORE COMPONENT - DO NOT REMOVE

### 3. `simplified_coverage_automation.py` - Simplified Report Generator

- **Purpose**: Generates the main `simplified_report.html` dashboard
- **Function**: Creates user-friendly overview with test type breakdown
- **Called by**: `vscode_coverage_hook.py`
- **Status**: CORE COMPONENT - DO NOT REMOVE

### 4. `coverage_data_loader.py` - Data Loading Support

- **Purpose**: Provides data loading utilities for coverage XML parsing
- **Function**: Shared by both report generators
- **Used by**: `generate_test_coverage_fast.py` and `simplified_coverage_automation.py`
- **Status**: SUPPORT COMPONENT - REQUIRED

## Supporting Files

### 5. `../pytest_plugins/coverage_hook_plugin.py` - Pytest Plugin

- **Purpose**: Auto-detects when VS Code runs tests with coverage
- **Function**: Automatically triggers `vscode_coverage_hook.py`
- **Integration**: Registered in `conftest.py`
- **Status**: CORE COMPONENT - DO NOT REMOVE

## How It Works

```text
VS Code "Run Tests with Coverage"
↓
pytest_plugins/coverage_hook_plugin.py (detects --cov flag)
↓
scripts/vscode_coverage_hook.py (main coordinator)
├── scripts/generate_test_coverage_fast.py (detailed reports)
└── scripts/simplified_coverage_automation.py (simplified_report.html)
↓
"✅ All coverage reports updated automatically"
```

## Usage

### Automatic (Recommended)

1. In VS Code, click "Run Tests with Coverage"
2. Reports automatically update in `reports/coverage/`
3. Open `reports/coverage/simplified_report.html` to view results

### Manual (Development/Debugging)

```bash
# Test the hook manually
python scripts/vscode_coverage_hook.py

# Run individual generators
python scripts/generate_test_coverage_fast.py
python scripts/simplified_coverage_automation.py
```

## Generated Reports

- **`reports/coverage/simplified_report.html`** - Main dashboard
- **`reports/coverage/index.html`** - Enhanced coverage overview
- **`reports/coverage/by-type/*.html`** - Test-type specific reports

## Recent Changes (August 2025)

### ✅ System Working Correctly

- **Automated Execution**: Reports update automatically with VS Code
- **Dual Report Generation**: Both fast and simplified reports generate together
- **Current Coverage**: Shows real-time coverage (15.2% actual vs 6% stale previously)
- **Zero Manual Steps**: Complete VS Code workflow integration

### 🗑️ Removed Obsolete Scripts (August 2025)

The following obsolete scripts were removed during cleanup:

- `auto_coverage_report.py`
- `coverage_file_watcher.py`
- `enhanced_coverage_loader.py`
- `fast_coverage_workflow.py`
- `path_based_coverage_analyzer.py`
- `vscode_coverage_analyzer.py`
- `vscode_coverage_integration.py`
- `vscode_coverage_integration_v2.py`
- `coverage_automation/` (entire directory)
- `test_type_slicer.py`
- `html_renderer.py`

Total removed: **10 obsolete scripts + 1 directory** → Simplified to **4 core components**

## Troubleshooting

### Reports Not Updating

1. Verify VS Code runs tests with `--cov` flag
2. Check that `pytest_plugins/coverage_hook_plugin.py` exists
3. Ensure `conftest.py` registers the plugin
4. Manually run `python scripts/vscode_coverage_hook.py` to test

### Missing Dependencies

```bash
# Install required packages
pip install coverage beautifulsoup4 tomli
```

### Error Messages

- Check the VS Code Python output panel for detailed error messages
- Verify all core component files exist and are executable

## System Status: ✅ FULLY OPERATIONAL

- **User Feedback**: "That is working properly"
- **Automation Goal**: ✅ Achieved
- **Current Coverage**: 15.2% (accurate, real-time)
- **Manual Steps**: ❌ None required

---

**Note**: This system replaces 26+ previous coverage scripts with 4 core components
that provide complete automation for VS Code coverage workflow.
