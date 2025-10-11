#!/usr/bin/env python3
"""
Export Module

This module provides comprehensive export functionality for the Automated Power Cycle 
and UART Validation Framework. It includes exporters for CSV, JSON, and HTML formats
with professional styling and interactive features.

Classes:
    CSVExporter: Handles CSV file generation with easy-to-read formatting
    JSONExporter: Handles JSON file generation with structured data organization
    HTMLExporter: Handles HTML file generation with embedded CSS and JavaScript

Usage:
    from lib.exports import CSVExporter, JSONExporter, HTMLExporter
    
    # Create exporters
    csv_exporter = CSVExporter()
    json_exporter = JSONExporter()
    html_exporter = HTMLExporter()
    
    # Export test results
    csv_file = csv_exporter.export_test_results(test_summary, cycle_data)
    json_file = json_exporter.export_test_results(test_summary, cycle_data)
    html_file = html_exporter.export_test_results(test_summary, cycle_data)
"""

from .csv_exporter import CSVExporter
from .json_exporter import JSONExporter
from .html_exporter import HTMLExporter

__all__ = ['CSVExporter', 'JSONExporter', 'HTMLExporter']

__version__ = '1.0.0'
__author__ = 'Automated Power Cycle and UART Validation Framework'
__description__ = 'Comprehensive export functionality for test results and data'
