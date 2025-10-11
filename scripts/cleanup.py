#!/usr/bin/env python3
"""
Cleanup script for the Automated Power Cycle and UART Validation Framework.
This script helps clean up old log files and reports.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta


def cleanup_old_files(directory: str, days_old: int = 30):
    """Clean up old files in a directory."""
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Directory does not exist: {directory}")
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_date:
                try:
                    file_path.unlink()
                    print(f"Deleted: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
    
    return deleted_count


def cleanup_logs(days_old: int = 30):
    """Clean up old log files."""
    print(f"Cleaning up log files older than {days_old} days...")
    deleted_count = cleanup_old_files("output/logs", days_old)
    print(f"Deleted {deleted_count} log files")


def cleanup_reports(days_old: int = 30):
    """Clean up old report files."""
    print(f"Cleaning up report files older than {days_old} days...")
    deleted_count = cleanup_old_files("output/reports", days_old)
    print(f"Deleted {deleted_count} report files")


def cleanup_all(days_old: int = 30):
    """Clean up all old files."""
    print(f"Cleaning up all files older than {days_old} days...")
    
    total_deleted = 0
    total_deleted += cleanup_old_files("output/logs", days_old)
    total_deleted += cleanup_old_files("output/reports", days_old)
    
    print(f"Total files deleted: {total_deleted}")


def show_disk_usage():
    """Show disk usage of output directories."""
    print("\nDisk Usage:")
    print("-" * 40)
    
    for directory in ["output/logs", "output/reports"]:
        directory_path = Path(directory)
        if directory_path.exists():
            total_size = sum(f.stat().st_size for f in directory_path.rglob('*') if f.is_file())
            file_count = len(list(directory_path.rglob('*')))
            print(f"{directory}: {total_size / (1024*1024):.2f} MB ({file_count} files)")
        else:
            print(f"{directory}: Directory does not exist")


def main():
    """Main cleanup function."""
    print("=" * 60)
    print("CLEANUP SCRIPT")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        try:
            days_old = int(sys.argv[1])
        except ValueError:
            print("Invalid number of days. Using default: 30")
            days_old = 30
    else:
        days_old = 30
    
    print(f"Cleaning up files older than {days_old} days")
    
    # Show current disk usage
    show_disk_usage()
    
    # Clean up files
    cleanup_all(days_old)
    
    # Show disk usage after cleanup
    print("\nAfter cleanup:")
    show_disk_usage()
    
    print("\n✅ Cleanup completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)
