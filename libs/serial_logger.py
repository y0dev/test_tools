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
            
            else:
                # Default to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
        
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            raise


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
            "output_formats": ["json", "csv", "txt"],
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
