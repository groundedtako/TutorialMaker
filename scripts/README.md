# Scripts Directory

This directory contains utility scripts for TutorialMaker development and maintenance.

## Files

### `check_permissions.py`
Utility script to check system permissions needed for screen recording and input monitoring.

**Usage:**
```bash
python scripts/check_permissions.py
```

**Purpose:**
- Verify screen recording permissions (macOS/Windows)
- Check input monitoring capabilities
- Diagnose permission-related issues
- Helpful for troubleshooting setup problems

### `export_tutorials.py`
Batch export script for converting existing tutorials to various formats.

**Usage:**
```bash
python scripts/export_tutorials.py [tutorial_id] [--format html,word,pdf]
```

**Purpose:**
- Export specific tutorials or all tutorials
- Batch conversion to multiple formats
- Useful for migration or bulk operations
- Can be automated in workflows

## Running Scripts

All scripts should be run from the project root directory:

```bash
# From project root
python scripts/script_name.py
```

Make sure you have activated the virtual environment and installed dependencies:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```