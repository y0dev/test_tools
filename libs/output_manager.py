#!/usr/bin/env python3
"""
Output Manager Module
Centralized management of output directories and file paths.

This module provides:
- Consistent output directory structure
- Automatic directory creation
- Timestamp-based file naming
- Output path resolution
- File organization utilities

Author: Automated Test Framework
Version: 1.0.0
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


class OutputManager:
    """
    Centralized output directory management system.
    
    This class handles all output file organization, directory creation,
    and path resolution for the test framework.
    """
    
    def __init__(self, base_output_dir: str = "./output"):
        """
        Initialize output manager.
        
        Args:
            base_output_dir: Base directory for all outputs
        """
        self.base_output_dir = Path(base_output_dir)
        self.logger = logging.getLogger(__name__)
        
        # Create base output directory
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define subdirectories
        self.subdirs = {
            'reports': 'reports',
            'serial_logs': 'serial_logs',
            'test_results': 'test_results',
            'jtag_logs': 'jtag_logs',
            'power_supply_logs': 'power_supply_logs',
            'automated_logs': 'automated_serial_logs',
            'parsed_data': 'parsed_data',
            'bitstreams': 'bitstreams',
            'boot_images': 'boot_images',
            'vivado_logs': 'vivado_logs'
        }
        
        # Create all subdirectories
        self._create_subdirectories()
    
    def _create_subdirectories(self):
        """Create all subdirectories."""
        for subdir_name, subdir_path in self.subdirs.items():
            subdir = self.base_output_dir / subdir_path
            subdir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created output subdirectory: {subdir}")
    
    def get_output_path(self, category: str, filename: str, 
                       use_date_hierarchy: bool = False,
                       date_format: str = "%Y/%m_%b/%m_%d") -> Path:
        """
        Get output path for a file.
        
        Args:
            category: Output category (reports, serial_logs, etc.)
            filename: Name of the file
            use_date_hierarchy: Whether to use date-based directory structure
            date_format: Date format for hierarchy
            
        Returns:
            Path: Full path to the output file
        """
        if category not in self.subdirs:
            self.logger.warning(f"Unknown output category: {category}. Using 'reports'.")
            category = 'reports'
        
        base_path = self.base_output_dir / self.subdirs[category]
        
        if use_date_hierarchy:
            date_path = datetime.now().strftime(date_format)
            base_path = base_path / date_path
        
        # Create directory if it doesn't exist
        base_path.mkdir(parents=True, exist_ok=True)
        
        return base_path / filename
    
    def get_timestamped_filename(self, prefix: str, extension: str, 
                                timestamp_format: str = "%Y%m%d_%H%M%S") -> str:
        """
        Generate a timestamped filename.
        
        Args:
            prefix: Filename prefix
            extension: File extension (with or without dot)
            timestamp_format: Timestamp format
            
        Returns:
            str: Timestamped filename
        """
        timestamp = datetime.now().strftime(timestamp_format)
        
        # Ensure extension starts with dot
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        return f"{prefix}_{timestamp}{extension}"
    
    def get_serial_log_path(self, use_date_hierarchy: bool = True) -> Path:
        """
        Get path for serial log file.
        
        Args:
            use_date_hierarchy: Whether to use date-based directory structure
            
        Returns:
            Path: Path to serial log file
        """
        filename = self.get_timestamped_filename("serial_log", "txt")
        return self.get_output_path('serial_logs', filename, use_date_hierarchy)
    
    def get_parsed_data_path(self, prefix: str = "parsed_data", 
                            extension: str = "json") -> Path:
        """
        Get path for parsed data file.
        
        Args:
            prefix: Filename prefix
            extension: File extension
            
        Returns:
            Path: Path to parsed data file
        """
        filename = self.get_timestamped_filename(prefix, extension)
        return self.get_output_path('parsed_data', filename)
    
    def get_report_path(self, report_type: str, extension: str = "html") -> Path:
        """
        Get path for report file.
        
        Args:
            report_type: Type of report (test_results, jtag_test, etc.)
            extension: File extension
            
        Returns:
            Path: Path to report file
        """
        filename = self.get_timestamped_filename(f"{report_type}_report", extension)
        return self.get_output_path('reports', filename)
    
    def get_test_results_path(self, test_name: str, extension: str = "json") -> Path:
        """
        Get path for test results file.
        
        Args:
            test_name: Name of the test
            extension: File extension
            
        Returns:
            Path: Path to test results file
        """
        filename = self.get_timestamped_filename(f"{test_name}_results", extension)
        return self.get_output_path('test_results', filename)
    
    def get_jtag_log_path(self, use_date_hierarchy: bool = True) -> Path:
        """
        Get path for JTAG log file.
        
        Args:
            use_date_hierarchy: Whether to use date-based directory structure
            
        Returns:
            Path: Path to JTAG log file
        """
        filename = self.get_timestamped_filename("jtag_log", "txt")
        return self.get_output_path('jtag_logs', filename, use_date_hierarchy)
    
    def get_power_supply_log_path(self, use_date_hierarchy: bool = True) -> Path:
        """
        Get path for power supply log file.
        
        Args:
            use_date_hierarchy: Whether to use date-based directory structure
            
        Returns:
            Path: Path to power supply log file
        """
        filename = self.get_timestamped_filename("power_supply_log", "txt")
        return self.get_output_path('power_supply_logs', filename, use_date_hierarchy)
    
    def get_bitstream_path(self, project_name: str) -> Path:
        """
        Get path for bitstream file.
        
        Args:
            project_name: Name of the Vivado project
            
        Returns:
            Path: Path to bitstream file
        """
        filename = f"{project_name}_bitstream.bit"
        return self.get_output_path('bitstreams', filename)
    
    def get_boot_image_path(self, image_name: str) -> Path:
        """
        Get path for boot image file.
        
        Args:
            image_name: Name of the boot image
            
        Returns:
            Path: Path to boot image file
        """
        filename = f"{image_name}_boot.bin"
        return self.get_output_path('boot_images', filename)
    
    def get_vivado_log_path(self, project_name: str) -> Path:
        """
        Get path for Vivado log file.
        
        Args:
            project_name: Name of the Vivado project
            
        Returns:
            Path: Path to Vivado log file
        """
        filename = self.get_timestamped_filename(f"{project_name}_vivado", "log")
        return self.get_output_path('vivado_logs', filename)
    
    def list_output_files(self, category: Optional[str] = None, 
                         pattern: Optional[str] = None) -> List[Path]:
        """
        List output files.
        
        Args:
            category: Specific category to list (optional)
            pattern: Pattern to match filenames (optional)
            
        Returns:
            List[Path]: List of output files
        """
        files = []
        
        if category:
            if category in self.subdirs:
                category_path = self.base_output_dir / self.subdirs[category]
                if category_path.exists():
                    files.extend(category_path.rglob('*'))
            else:
                self.logger.warning(f"Unknown category: {category}")
        else:
            # List all files in all subdirectories
            for subdir_path in self.subdirs.values():
                subdir = self.base_output_dir / subdir_path
                if subdir.exists():
                    files.extend(subdir.rglob('*'))
        
        # Filter by pattern if provided
        if pattern:
            import fnmatch
            files = [f for f in files if fnmatch.fnmatch(f.name, pattern)]
        
        # Filter out directories
        files = [f for f in files if f.is_file()]
        
        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def cleanup_old_files(self, category: str, days_old: int = 30):
        """
        Clean up old files in a category.
        
        Args:
            category: Category to clean up
            days_old: Age threshold in days
        """
        import time
        
        if category not in self.subdirs:
            self.logger.warning(f"Unknown category: {category}")
            return
        
        category_path = self.base_output_dir / self.subdirs[category]
        if not category_path.exists():
            return
        
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        removed_count = 0
        
        for file_path in category_path.rglob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    removed_count += 1
                    self.logger.debug(f"Removed old file: {file_path}")
                except Exception as e:
                    self.logger.error(f"Error removing file {file_path}: {e}")
        
        self.logger.info(f"Cleaned up {removed_count} old files from {category}")
    
    def get_output_summary(self) -> Dict[str, Any]:
        """
        Get summary of output directory structure.
        
        Returns:
            Dict[str, Any]: Summary information
        """
        summary = {
            'base_directory': str(self.base_output_dir),
            'categories': {},
            'total_files': 0,
            'total_size': 0
        }
        
        for category, subdir_path in self.subdirs.items():
            category_path = self.base_output_dir / subdir_path
            if category_path.exists():
                files = list(category_path.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                
                summary['categories'][category] = {
                    'path': str(category_path),
                    'file_count': file_count,
                    'total_size': total_size,
                    'size_mb': round(total_size / (1024 * 1024), 2)
                }
                
                summary['total_files'] += file_count
                summary['total_size'] += total_size
        
        summary['total_size_mb'] = round(summary['total_size'] / (1024 * 1024), 2)
        
        return summary


# Global output manager instance
_output_manager = None

def get_output_manager() -> OutputManager:
    """
    Get the global output manager instance.
    
    Returns:
        OutputManager: Global output manager instance
    """
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager()
    return _output_manager


def get_output_path(category: str, filename: str, **kwargs) -> Path:
    """
    Convenience function to get output path.
    
    Args:
        category: Output category
        filename: Filename
        **kwargs: Additional arguments for get_output_path
        
    Returns:
        Path: Output file path
    """
    return get_output_manager().get_output_path(category, filename, **kwargs)


def get_timestamped_filename(prefix: str, extension: str, **kwargs) -> str:
    """
    Convenience function to get timestamped filename.
    
    Args:
        prefix: Filename prefix
        extension: File extension
        **kwargs: Additional arguments for get_timestamped_filename
        
    Returns:
        str: Timestamped filename
    """
    return get_output_manager().get_timestamped_filename(prefix, extension, **kwargs)


if __name__ == "__main__":
    # Example usage
    manager = OutputManager()
    
    # Get various output paths
    print("Output Manager Example:")
    print(f"Serial log path: {manager.get_serial_log_path()}")
    print(f"Parsed data path: {manager.get_parsed_data_path()}")
    print(f"Report path: {manager.get_report_path('test_results')}")
    print(f"Test results path: {manager.get_test_results_path('power_cycle')}")
    
    # Get summary
    summary = manager.get_output_summary()
    print(f"\nOutput Summary:")
    print(f"Total files: {summary['total_files']}")
    print(f"Total size: {summary['total_size_mb']} MB")
    
    for category, info in summary['categories'].items():
        print(f"  {category}: {info['file_count']} files, {info['size_mb']} MB")
