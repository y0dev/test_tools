#!/usr/bin/env python3
"""
Serial Logger Module
Provides serial communication logging with configurable data parsing.

This module provides:
- Serial port communication and logging
- Real-time data parsing based on configurable patterns
- Multiple output formats (JSON, CSV, TXT)
- Data filtering and validation
- Log file management

Author: Automated Test Framework
Version: 1.0.0
"""

import serial
import json
import csv
import re
import time
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


class SerialLogger:
    """
    Serial logger with configurable data parsing capabilities.
    
    This class handles serial communication, data logging, and optional
    real-time data parsing based on configuration patterns.
    """
    
    def __init__(self, config: Dict[str, Any], parse_data: bool = False):
        """
        Initialize serial logger.
        
        Args:
            config: Configuration dictionary containing serial, logging, and parsing settings
            parse_data: Whether to enable real-time data parsing
        """
        self.config = config
        self.parse_data = parse_data
        self.serial_conn = None
        self.log_file = None
        self.log_file_path = None
        self.parsed_data = []
        self.running = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize data parser if enabled
        if parse_data:
            self.data_parser = SerialDataParser(config)
        else:
            self.data_parser = None
    
    def connect(self) -> bool:
        """
        Connect to serial port.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            serial_config = self.config['serial']
            
            self.serial_conn = serial.Serial(
                port=serial_config['port'],
                baudrate=serial_config['baud'],
                timeout=serial_config.get('timeout', 1.0),
                parity=serial_config.get('parity', 'N'),
                stopbits=serial_config.get('stopbits', 1),
                bytesize=serial_config.get('bytesize', 8)
            )
            
            self.logger.info(f"Connected to serial port {serial_config['port']} at {serial_config['baud']} baud")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to serial port: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.logger.info("Disconnected from serial port")
    
    def setup_log_file(self) -> bool:
        """
        Setup log file for data recording.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            logging_config = self.config['logging']
            base_log_dir = Path(logging_config['log_directory'])
            
            # Create date-based hierarchy if enabled
            if logging_config.get('use_date_hierarchy', False):
                date_format = logging_config.get('date_format', '%Y/%m_%b/%m_%d')
                date_path = datetime.now().strftime(date_format)
                log_dir = base_log_dir / date_path
            else:
                log_dir = base_log_dir
            
            # Create directory if needed
            if logging_config.get('auto_create_dirs', True):
                log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate log file name with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"serial_log_{timestamp}.txt"
            self.log_file_path = log_dir / log_filename
            
            # Open log file
            self.log_file = open(self.log_file_path, 'w', encoding='utf-8')
            
            self.logger.info(f"Log file created: {self.log_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup log file: {e}")
            return False
    
    def close_log_file(self):
        """Close log file."""
        if self.log_file:
            self.log_file.close()
            self.log_file = None
    
    def write_to_log(self, data: str, timestamp: Optional[datetime] = None):
        """
        Write data to log file.
        
        Args:
            data: Data to write
            timestamp: Optional timestamp (uses current time if None)
        """
        if not self.log_file:
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        timestamp_str = timestamp.strftime(self.config['logging']['timestamp_format'])
        log_entry = f"{timestamp_str},{data.strip()}\n"
        
        self.log_file.write(log_entry)
        self.log_file.flush()
    
    def filter_data(self, data: str) -> bool:
        """
        Check if data should be logged based on filters.
        
        Args:
            data: Data to check
            
        Returns:
            bool: True if data should be logged, False otherwise
        """
        filters = self.config.get('filters', {})
        
        # Check minimum/maximum length
        min_length = filters.get('min_data_length', 0)
        max_length = filters.get('max_data_length', float('inf'))
        
        if len(data) < min_length or len(data) > max_length:
            return False
        
        # Check exclude patterns
        exclude_patterns = filters.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if re.search(pattern, data):
                return False
        
        # Check include patterns (if any specified)
        include_patterns = filters.get('include_patterns', [])
        if include_patterns:
            for pattern in include_patterns:
                if re.search(pattern, data):
                    return True
            return False
        
        return True
    
    def start_logging(self):
        """Start serial data logging."""
        if not self.connect():
            raise Exception("Failed to connect to serial port")
        
        if not self.setup_log_file():
            raise Exception("Failed to setup log file")
        
        self.running = True
        self.logger.info("Starting serial data logging...")
        
        try:
            while self.running:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8', errors='ignore')
                    
                    if data and self.filter_data(data):
                        timestamp = datetime.now()
                        
                        # Write to log file
                        self.write_to_log(data, timestamp)
                        
                        # Parse data if enabled
                        if self.parse_data and self.data_parser:
                            parsed_result = self.data_parser.parse_line(data, timestamp)
                            if parsed_result:
                                self.parsed_data.append(parsed_result)
                                print(f"Parsed: {parsed_result}")
                        
                        # Display raw data
                        print(f"[{timestamp.strftime('%H:%M:%S')}] {data.strip()}")
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
        except KeyboardInterrupt:
            self.stop_logging()
        except Exception as e:
            self.logger.error(f"Error during logging: {e}")
            self.stop_logging()
            raise
    
    def stop_logging(self):
        """Stop serial data logging."""
        self.running = False
        self.disconnect()
        self.close_log_file()
        
        if self.parse_data and self.parsed_data:
            self.logger.info(f"Logging stopped. Parsed {len(self.parsed_data)} entries.")
        else:
            self.logger.info("Logging stopped.")
    
    def get_log_file(self) -> Optional[str]:
        """
        Get the path to the current log file.
        
        Returns:
            str: Path to log file, or None if no file is open
        """
        return str(self.log_file_path) if self.log_file_path else None
    
    def get_parsed_data(self) -> List[Dict[str, Any]]:
        """
        Get parsed data collected during logging.
        
        Returns:
            List[Dict[str, Any]]: List of parsed data entries
        """
        return self.parsed_data.copy()


class SerialDataParser:
    """
    Serial data parser with configurable pattern matching.
    
    This class handles parsing of serial data based on regex patterns
    defined in the configuration file.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data parser.
        
        Args:
            config: Configuration dictionary containing parsing patterns
        """
        self.config = config
        self.parsing_config = config.get('data_parsing', {})
        self.patterns = self.parsing_config.get('patterns', [])
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = []
        for pattern in self.patterns:
            try:
                compiled = re.compile(pattern['regex'])
                self.compiled_patterns.append({
                    'name': pattern['name'],
                    'description': pattern.get('description', ''),
                    'type': pattern.get('type', 'string'),
                    'regex': compiled,
                    'extract_groups': pattern.get('extract_groups', []),
                    'labels': pattern.get('labels', [])
                })
            except re.error as e:
                logging.warning(f"Invalid regex pattern '{pattern['regex']}': {e}")
    
    def parse_line(self, data: str, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Parse a single line of serial data.
        
        Args:
            data: Raw data line to parse
            timestamp: Timestamp of the data
            
        Returns:
            Dict[str, Any]: Parsed data entry, or None if no pattern matches
        """
        for pattern in self.compiled_patterns:
            match = pattern['regex'].search(data)
            if match:
                result = {
                    'timestamp': timestamp.isoformat(),
                    'pattern_name': pattern['name'],
                    'pattern_type': pattern['type'],
                    'raw_data': data.strip(),
                    'parsed_data': {}
                }
                
                # Extract groups based on configuration
                extract_groups = pattern['extract_groups']
                labels = pattern['labels']
                
                for i, group_index in enumerate(extract_groups):
                    if group_index <= len(match.groups()):
                        value = match.group(group_index)
                        
                        # Convert value based on type
                        if pattern['type'] == 'float':
                            try:
                                value = float(value)
                            except ValueError:
                                pass
                        elif pattern['type'] == 'int':
                            try:
                                value = int(value)
                            except ValueError:
                                pass
                        
                        # Use label if available, otherwise use group index
                        key = labels[i] if i < len(labels) else f'group_{group_index}'
                        result['parsed_data'][key] = value
                
                return result
        
        return None
    
    def parse_log_file(self, log_file_path: str) -> List[Dict[str, Any]]:
        """
        Parse an entire log file.
        
        Args:
            log_file_path: Path to the log file to parse
            
        Returns:
            List[Dict[str, Any]]: List of parsed data entries
        """
        results = []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Parse timestamp and data from log line
                        if ',' in line:
                            timestamp_str, data = line.split(',', 1)
                            timestamp = datetime.fromisoformat(timestamp_str.strip())
                            
                            parsed_result = self.parse_line(data, timestamp)
                            if parsed_result:
                                parsed_result['line_number'] = line_num
                                results.append(parsed_result)
                    except Exception as e:
                        logging.warning(f"Error parsing line {line_num}: {e}")
                        continue
        
        except Exception as e:
            logging.error(f"Error reading log file: {e}")
            return []
        
        return results
    
    def display_summary(self, results: List[Dict[str, Any]]):
        """
        Display a summary of parsed results.
        
        Args:
            results: List of parsed data entries
        """
        if not results:
            print("No parsed data to display")
            return
        
        print(f"\nParsed Data Summary:")
        print("=" * 50)
        
        # Count by pattern type
        pattern_counts = {}
        for result in results:
            pattern_name = result['pattern_name']
            pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1
        
        print(f"Total entries: {len(results)}")
        print(f"Pattern breakdown:")
        for pattern_name, count in pattern_counts.items():
            print(f"  {pattern_name}: {count}")
        
        # Show sample entries
        print(f"\nSample entries:")
        for i, result in enumerate(results[:5]):  # Show first 5 entries
            print(f"  {i+1}. [{result['timestamp']}] {result['pattern_name']}: {result['parsed_data']}")
        
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more entries")
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """
        Save parsed results to file.
        
        Args:
            results: List of parsed data entries
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_formats = self.parsing_config.get('output_formats', ['json'])
        
        try:
            if 'json' in output_formats or output_path.suffix == '.json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
            
            elif 'csv' in output_formats or output_path.suffix == '.csv':
                if results:
                    # Get all unique keys from parsed data
                    all_keys = set()
                    for result in results:
                        all_keys.update(result['parsed_data'].keys())
                    
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        
                        # Write header
                        header = ['timestamp', 'pattern_name', 'pattern_type', 'raw_data'] + list(all_keys)
                        writer.writerow(header)
                        
                        # Write data rows
                        for result in results:
                            row = [
                                result['timestamp'],
                                result['pattern_name'],
                                result['pattern_type'],
                                result['raw_data']
                            ]
                            
                            # Add parsed data values
                            for key in all_keys:
                                row.append(result['parsed_data'].get(key, ''))
                            
                            writer.writerow(row)
            
            elif 'txt' in output_formats or output_path.suffix == '.txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for result in results:
                        f.write(f"[{result['timestamp']}] {result['pattern_name']}: {result['parsed_data']}\n")
                        f.write(f"Raw: {result['raw_data']}\n\n")
            
            elif 'html' in output_formats or output_path.suffix == '.html':
                self._generate_html_report(output_path, results)
            
            else:
                # Default to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
        
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            raise
    
    def _generate_html_report(self, output_path: Path, results: List[Dict[str, Any]]):
        """
        Generate an HTML report with pattern analysis and data visualization.
        
        Args:
            output_path: Path to save the HTML file
            results: List of parsed data entries
        """
        try:
            # Calculate statistics
            total_entries = len(results)
            pattern_counts = {}
            pattern_types = {}
            timestamp_range = None
            
            if results:
                # Count patterns
                for result in results:
                    pattern_name = result['pattern_name']
                    pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1
                    pattern_types[pattern_name] = result['pattern_type']
                
                # Get timestamp range
                timestamps = [result['timestamp'] for result in results]
                timestamp_range = f"{min(timestamps)} to {max(timestamps)}"
            
            # Generate HTML content
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Serial Data Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .patterns {{
            padding: 30px;
        }}
        .patterns h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .pattern-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .pattern-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .pattern-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .pattern-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .pattern-count {{
            font-size: 1.5em;
            color: #28a745;
            font-weight: bold;
        }}
        .pattern-type {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .data-table {{
            margin-top: 30px;
            overflow-x: auto;
        }}
        .data-table table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .data-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        .data-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        .data-table tr:hover {{
            background: #f8f9fa;
        }}
        .timestamp {{
            font-family: monospace;
            font-size: 0.9em;
            color: #666;
        }}
        .raw-data {{
            font-family: monospace;
            background: #f8f9fa;
            padding: 5px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .parsed-data {{
            font-family: monospace;
            color: #28a745;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Serial Data Analysis Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_entries}</div>
                <div class="stat-label">Total Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(pattern_counts)}</div>
                <div class="stat-label">Pattern Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(set(pattern_types.values()))}</div>
                <div class="stat-label">Data Types</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.patterns)}</div>
                <div class="stat-label">Configured Patterns</div>
            </div>
        </div>
        
        <div class="patterns">
            <h2>Pattern Analysis</h2>
            {self._generate_pattern_analysis_html(pattern_counts, pattern_types)}
        </div>
        
        <div class="data-table">
            <h2>Parsed Data</h2>
            {self._generate_data_table_html(results)}
        </div>
        
        <div class="footer">
            <p>Report generated by Serial Data Parser | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            logging.error(f"Error generating HTML report: {e}")
            raise
    
    def _generate_pattern_analysis_html(self, pattern_counts: Dict[str, int], pattern_types: Dict[str, str]) -> str:
        """Generate HTML for pattern analysis section."""
        if not pattern_counts:
            return '<div class="no-data">No pattern data available</div>'
        
        html = '<div class="pattern-grid">'
        for pattern_name, count in pattern_counts.items():
            pattern_type = pattern_types.get(pattern_name, 'unknown')
            percentage = (count / sum(pattern_counts.values())) * 100
            
            html += f'''
            <div class="pattern-card">
                <div class="pattern-name">{pattern_name}</div>
                <div class="pattern-count">{count}</div>
                <div class="pattern-type">Type: {pattern_type} | {percentage:.1f}%</div>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _generate_data_table_html(self, results: List[Dict[str, Any]]) -> str:
        """Generate HTML for data table section."""
        if not results:
            return '<div class="no-data">No data to display</div>'
        
        # Limit to first 100 entries for performance
        display_results = results[:100]
        
        html = '''
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Pattern</th>
                    <th>Type</th>
                    <th>Parsed Data</th>
                    <th>Raw Data</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for result in display_results:
            parsed_data_str = ', '.join([f"{k}: {v}" for k, v in result['parsed_data'].items()])
            html += f'''
            <tr>
                <td class="timestamp">{result['timestamp']}</td>
                <td>{result['pattern_name']}</td>
                <td>{result['pattern_type']}</td>
                <td class="parsed-data">{parsed_data_str}</td>
                <td class="raw-data" title="{result['raw_data']}">{result['raw_data'][:50]}{'...' if len(result['raw_data']) > 50 else ''}</td>
            </tr>
            '''
        
        html += '''
            </tbody>
        </table>
        '''
        
        if len(results) > 100:
            html += f'<p style="text-align: center; color: #666; margin-top: 20px;">Showing first 100 of {len(results)} entries</p>'
        
        return html


def create_sample_serial_logger_config() -> Dict[str, Any]:
    """
    Create a sample serial logger configuration.
    
    Returns:
        Dict[str, Any]: Sample configuration dictionary
    """
    return {
        "serial": {
            "port": "COM3",
            "baud": 115200,
            "timeout": 1.0,
            "parity": "N",
            "stopbits": 1,
            "bytesize": 8
        },
        "logging": {
            "log_directory": "./output/serial_logs",
            "log_format": "timestamp,data",
            "timestamp_format": "%Y-%m-%d %H:%M:%S.%f",
            "auto_create_dirs": True,
            "use_date_hierarchy": True,
            "date_format": "%Y/%m_%b/%m_%d"
        },
        "data_parsing": {
            "enabled": True,
            "patterns": [
                {
                    "name": "numeric_data",
                    "description": "Extract numeric values from serial data",
                    "regex": "^(\\d+(?:\\.\\d+)?)\\r?\\n$",
                    "type": "float",
                    "extract_groups": [1]
                },
                {
                    "name": "status_message",
                    "description": "Extract status messages",
                    "regex": "STATUS:\\s*(\\w+)",
                    "type": "string",
                    "extract_groups": [1]
                },
                {
                    "name": "sensor_data",
                    "description": "Extract sensor readings with labels",
                    "regex": "SENSOR\\s+(\\w+):\\s*(\\d+(?:\\.\\d+)?)",
                    "type": "sensor",
                    "extract_groups": [1, 2],
                    "labels": ["sensor_name", "value"]
                },
                {
                    "name": "error_codes",
                    "description": "Extract error codes",
                    "regex": "ERROR\\s+(\\d+):\\s*(.+)",
                    "type": "error",
                    "extract_groups": [1, 2],
                    "labels": ["error_code", "message"]
                }
            ],
            "output_formats": ["json", "csv", "txt", "html"],
            "save_raw_data": True
        },
        "filters": {
            "min_data_length": 1,
            "max_data_length": 1000,
            "exclude_patterns": ["^\\s*$", "^\\r?\\n$"],
            "include_patterns": []
        }
    }


if __name__ == "__main__":
    # Example usage
    config = create_sample_serial_logger_config()
    
    # Save sample config
    with open("config/serial_logger_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("Sample serial logger configuration created: config/serial_logger_config.json")
