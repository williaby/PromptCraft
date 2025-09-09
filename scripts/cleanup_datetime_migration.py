#!/usr/bin/env python3
"""
Cleanup script for datetime migration backup files.

This script removes .backup files created during the datetime migration process.
"""

import argparse
from pathlib import Path
import logging

def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def find_backup_files(base_path: Path) -> list[Path]:
    """Find all .backup files in the project."""
    backup_files = []
    for pattern in ["**/*.backup", "**/*.py.backup"]:
        backup_files.extend(base_path.glob(pattern))
    return sorted(backup_files)

def cleanup_backup_files(base_path: Path, dry_run: bool = False) -> None:
    """Remove all backup files from the datetime migration."""
    logger = logging.getLogger(__name__)
    
    backup_files = find_backup_files(base_path)
    
    if not backup_files:
        logger.info("No backup files found.")
        return
    
    logger.info(f"Found {len(backup_files)} backup files.")
    
    for backup_file in backup_files:
        if dry_run:
            logger.info(f"Would remove: {backup_file}")
        else:
            try:
                backup_file.unlink()
                logger.info(f"Removed: {backup_file}")
            except Exception as e:
                logger.error(f"Failed to remove {backup_file}: {e}")
    
    if dry_run:
        logger.info(f"Dry run completed. {len(backup_files)} files would be removed.")
    else:
        logger.info(f"Cleanup completed. {len(backup_files)} backup files removed.")

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Cleanup backup files created during datetime migration"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Base path to search for backup files (default: current directory)"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    cleanup_backup_files(args.path, args.dry_run)

if __name__ == "__main__":
    main()