#!/usr/bin/env python3
"""
CSV Export Handler

Handles the generation of CSV files in an easy-to-read format for test results.
Provides comprehensive data export with proper formatting and organization.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class CSVExporter:
    """
    CSV export handler for test results and data.
    
    This class provides comprehensive CSV export functionality with:
    - Easy-to-read formatting
    - Multiple data sections
    - Proper column headers
    - Data type handling
    - Error handling and validation
    """
    
    def __init__(self, output_directory: str = "./output/reports"):
        """
        Initialize CSV exporter.
        
        Args:
            output_directory (str): Directory to save CSV files
        """
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def export_test_results(self, test_summary: Dict[str, Any], 
                          cycle_data: List[Dict[str, Any]] = None,
                          uart_data: List[Dict[str, Any]] = None,
                          validation_results: List[Dict[str, Any]] = None,
                          filename_prefix: str = "test_results") -> str:
        """
        Export comprehensive test results to CSV format.
        
        Args:
            test_summary (dict): Overall test summary data
            cycle_data (list): Individual cycle execution data
            uart_data (list): UART data collected during tests
            validation_results (list): Pattern validation results
            filename_prefix (str): Prefix for the generated filename
            
        Returns:
            str: Path to the generated CSV file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = self.output_directory / filename
        
        self.logger.info(f"Exporting test results to CSV: {filepath}")
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header information
                self._write_header_section(writer, test_summary)
                
                # Write test summary section
                self._write_summary_section(writer, test_summary)
                
                # Write cycle data section
                if cycle_data:
                    self._write_cycle_section(writer, cycle_data)
                
                # Write UART data section
                if uart_data:
                    self._write_uart_section(writer, uart_data)
                
                # Write validation results section
                if validation_results:
                    self._write_validation_section(writer, validation_results)
                
                # Write footer
                self._write_footer_section(writer)
            
            self.logger.info(f"CSV export completed successfully: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            raise
    
    def _write_header_section(self, writer: csv.writer, test_summary: Dict[str, Any]):
        """Write header section with metadata."""
        writer.writerow(['AUTOMATED POWER CYCLE AND UART VALIDATION FRAMEWORK'])
        writer.writerow(['Test Results Export'])
        writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Framework Version:', '1.0.0'])
        writer.writerow(['Export Format:', 'CSV'])
        writer.writerow([])  # Empty row for spacing
    
    def _write_summary_section(self, writer: csv.writer, test_summary: Dict[str, Any]):
        """Write test summary section."""
        writer.writerow(['TEST SUMMARY'])
        writer.writerow(['=' * 50])
        
        # Summary data
        summary_fields = [
            ('Test Name', test_summary.get('test_name', 'N/A')),
            ('Start Time', test_summary.get('start_time', 'N/A')),
            ('End Time', test_summary.get('end_time', 'N/A')),
            ('Duration (seconds)', test_summary.get('duration', 'N/A')),
            ('Total Cycles', test_summary.get('total_cycles', 0)),
            ('Successful Cycles', test_summary.get('successful_cycles', 0)),
            ('Failed Cycles', test_summary.get('failed_cycles', 0)),
            ('Success Rate (%)', f"{test_summary.get('success_rate', 0) * 100:.2f}"),
            ('Overall Status', test_summary.get('status', 'UNKNOWN'))
        ]
        
        for field, value in summary_fields:
            writer.writerow([field, value])
        
        writer.writerow([])  # Empty row for spacing
    
    def _write_cycle_section(self, writer: csv.writer, cycle_data: List[Dict[str, Any]]):
        """Write cycle data section."""
        writer.writerow(['CYCLE DATA'])
        writer.writerow(['=' * 50])
        
        if not cycle_data:
            writer.writerow(['No cycle data available'])
            writer.writerow([])
            return
        
        # Write headers
        headers = [
            'Cycle Number', 'Start Time', 'End Time', 'Duration (s)',
            'Status', 'Power On Time (s)', 'Power Off Time (s)',
            'Voltage Setting (V)', 'Current Setting (A)',
            'Voltage Measured (V)', 'Current Measured (A)', 'Error Message'
        ]
        writer.writerow(headers)
        
        # Write cycle data
        for cycle in cycle_data:
            row = [
                cycle.get('cycle_number', 'N/A'),
                cycle.get('start_time', 'N/A'),
                cycle.get('end_time', 'N/A'),
                f"{cycle.get('duration', 0):.2f}",
                cycle.get('status', 'UNKNOWN'),
                cycle.get('on_time', 'N/A'),
                cycle.get('off_time', 'N/A'),
                cycle.get('voltage_setting', 'N/A'),
                cycle.get('current_setting', 'N/A'),
                cycle.get('voltage_measured', 'N/A'),
                cycle.get('current_measured', 'N/A'),
                cycle.get('error_message', '')
            ]
            writer.writerow(row)
        
        writer.writerow([])  # Empty row for spacing
    
    def _write_uart_section(self, writer: csv.writer, uart_data: List[Dict[str, Any]]):
        """Write UART data section."""
        writer.writerow(['UART DATA'])
        writer.writerow(['=' * 50])
        
        if not uart_data:
            writer.writerow(['No UART data available'])
            writer.writerow([])
            return
        
        # Write headers
        headers = [
            'Timestamp', 'Port', 'Baud Rate', 'Data Length',
            'Data Preview', 'Full Data'
        ]
        writer.writerow(headers)
        
        # Write UART data (limit to first 1000 entries for readability)
        for i, data in enumerate(uart_data[:1000]):
            data_preview = str(data.get('data', ''))[:50] + '...' if len(str(data.get('data', ''))) > 50 else str(data.get('data', ''))
            
            row = [
                data.get('timestamp', 'N/A'),
                data.get('port', 'N/A'),
                data.get('baud_rate', 'N/A'),
                len(str(data.get('data', ''))),
                data_preview,
                str(data.get('data', ''))
            ]
            writer.writerow(row)
        
        if len(uart_data) > 1000:
            writer.writerow([f'... and {len(uart_data) - 1000} more entries'])
        
        writer.writerow([])  # Empty row for spacing
    
    def _write_validation_section(self, writer: csv.writer, validation_results: List[Dict[str, Any]]):
        """Write validation results section."""
        writer.writerow(['VALIDATION RESULTS'])
        writer.writerow(['=' * 50])
        
        if not validation_results:
            writer.writerow(['No validation results available'])
            writer.writerow([])
            return
        
        # Write headers
        headers = [
            'Pattern Name', 'Pattern Type', 'Success', 'Matched Data',
            'Expected Value', 'Message', 'Timestamp'
        ]
        writer.writerow(headers)
        
        # Write validation results
        for result in validation_results:
            row = [
                result.get('pattern_name', 'N/A'),
                result.get('pattern_type', 'N/A'),
                'PASS' if result.get('success', False) else 'FAIL',
                str(result.get('matched_data', '')),
                str(result.get('expected', '')),
                result.get('message', ''),
                result.get('timestamp', 'N/A')
            ]
            writer.writerow(row)
        
        writer.writerow([])  # Empty row for spacing
    
    def _write_footer_section(self, writer: csv.writer):
        """Write footer section."""
        writer.writerow(['END OF REPORT'])
        writer.writerow(['Generated by Automated Power Cycle and UART Validation Framework'])
        writer.writerow(['For more information, see the project documentation'])
    
    def export_simple_data(self, data: List[Dict[str, Any]], 
                          filename: str = "data_export.csv",
                          headers: List[str] = None) -> str:
        """
        Export simple data to CSV format.
        
        Args:
            data (list): List of dictionaries to export
            filename (str): Output filename
            headers (list): Custom headers (if None, uses data keys)
            
        Returns:
            str: Path to the generated CSV file
        """
        filepath = self.output_directory / filename
        
        self.logger.info(f"Exporting simple data to CSV: {filepath}")
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if not data:
                    writer = csv.writer(csvfile)
                    writer.writerow(['No data available'])
                    return str(filepath)
                
                # Determine headers
                if headers is None:
                    headers = list(data[0].keys())
                
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for row in data:
                    writer.writerow(row)
            
            self.logger.info(f"Simple CSV export completed: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to export simple CSV: {e}")
            raise
    
    def export_cycle_analysis(self, cycle_results: List[Dict[str, Any]], 
                            filename_prefix: str = "cycle_analysis") -> str:
        """
        Export detailed cycle analysis to CSV.
        
        Args:
            cycle_results (list): Detailed cycle analysis data
            filename_prefix (str): Prefix for filename
            
        Returns:
            str: Path to generated CSV file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = self.output_directory / filename
        
        self.logger.info(f"Exporting cycle analysis to CSV: {filepath}")
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write analysis headers
                writer.writerow(['CYCLE ANALYSIS REPORT'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                
                # Write detailed cycle data
                headers = [
                    'Cycle', 'Start Time', 'End Time', 'Duration (s)',
                    'Power On Time (s)', 'Power Off Time (s)', 'Status',
                    'Voltage Setting (V)', 'Voltage Measured (V)',
                    'Current Setting (A)', 'Current Measured (A)',
                    'Temperature (°C)', 'Error Message', 'Notes'
                ]
                writer.writerow(headers)
                
                for cycle in cycle_results:
                    row = [
                        cycle.get('cycle', 'N/A'),
                        cycle.get('start_time', 'N/A'),
                        cycle.get('end_time', 'N/A'),
                        f"{cycle.get('duration', 0):.2f}",
                        cycle.get('on_time', 'N/A'),
                        cycle.get('off_time', 'N/A'),
                        cycle.get('status', 'UNKNOWN'),
                        cycle.get('voltage_setting', 'N/A'),
                        cycle.get('voltage_measured', 'N/A'),
                        cycle.get('current_setting', 'N/A'),
                        cycle.get('current_measured', 'N/A'),
                        cycle.get('temperature', 'N/A'),
                        cycle.get('error_message', ''),
                        cycle.get('notes', '')
                    ]
                    writer.writerow(row)
            
            self.logger.info(f"Cycle analysis CSV export completed: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to export cycle analysis CSV: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create exporter
    exporter = CSVExporter()
    
    # Sample test data
    test_summary = {
        'test_name': 'Sample Test',
        'start_time': '2024-01-15 10:00:00',
        'end_time': '2024-01-15 10:05:00',
        'duration': 300,
        'total_cycles': 3,
        'successful_cycles': 2,
        'failed_cycles': 1,
        'success_rate': 0.67,
        'status': 'PARTIAL'
    }
    
    cycle_data = [
        {
            'cycle_number': 1,
            'start_time': '2024-01-15 10:00:00',
            'end_time': '2024-01-15 10:01:00',
            'duration': 60,
            'status': 'PASS',
            'on_time': 30,
            'off_time': 30,
            'voltage_setting': 5.0,
            'voltage_measured': 4.98
        },
        {
            'cycle_number': 2,
            'start_time': '2024-01-15 10:01:00',
            'end_time': '2024-01-15 10:02:00',
            'duration': 60,
            'status': 'PASS',
            'on_time': 30,
            'off_time': 30,
            'voltage_setting': 5.0,
            'voltage_measured': 5.01
        },
        {
            'cycle_number': 3,
            'start_time': '2024-01-15 10:02:00',
            'end_time': '2024-01-15 10:03:00',
            'duration': 60,
            'status': 'FAIL',
            'on_time': 30,
            'off_time': 30,
            'voltage_setting': 5.0,
            'voltage_measured': 0.0,
            'error_message': 'Power supply communication error'
        }
    ]
    
    # Export test results
    csv_file = exporter.export_test_results(test_summary, cycle_data)
    print(f"CSV export completed: {csv_file}")
    
    # Export cycle analysis
    analysis_file = exporter.export_cycle_analysis(cycle_data)
    print(f"Cycle analysis export completed: {analysis_file}")
