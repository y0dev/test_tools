import re
import time
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """Enumeration for pattern matching types."""
    CONTAINS = "contains"
    REGEX = "regex"
    EXACT = "exact"
    NUMERIC_RANGE = "numeric_range"
    JSON_KEY = "json_key"


@dataclass
class ValidationResult:
    """Data class for validation results."""
    pattern_name: str
    success: bool
    matched_data: Optional[str] = None
    match_time: Optional[datetime] = None
    timeout_reached: bool = False
    error_message: Optional[str] = None
    extracted_values: Optional[Dict[str, Any]] = None


class PatternValidator:
    """
    Advanced pattern validation and parsing system for UART data.
    Supports multiple pattern types and data extraction.
    """
    
    def __init__(self):
        """Initialize the pattern validator."""
        self.logger = logging.getLogger(__name__)
        self.validation_history = []
        
    def validate_pattern(self, data: str, pattern_config: Dict, 
                        timeout: float = None) -> ValidationResult:
        """
        Validate data against a pattern configuration.
        
        :param data: Data string to validate
        :param pattern_config: Pattern configuration dictionary
        :param timeout: Optional timeout for validation
        :return: ValidationResult object
        """
        pattern_name = pattern_config.get('name', 'unknown')
        pattern = pattern_config.get('pattern', '')
        pattern_type = PatternType(pattern_config.get('pattern_type', 'contains'))
        
        try:
            result = ValidationResult(pattern_name=pattern_name, success=False)
            
            if pattern_type == PatternType.CONTAINS:
                result = self._validate_contains(data, pattern, result)
            elif pattern_type == PatternType.REGEX:
                result = self._validate_regex(data, pattern, result)
            elif pattern_type == PatternType.EXACT:
                result = self._validate_exact(data, pattern, result)
            elif pattern_type == PatternType.NUMERIC_RANGE:
                result = self._validate_numeric_range(data, pattern, result)
            elif pattern_type == PatternType.JSON_KEY:
                result = self._validate_json_key(data, pattern, result)
            else:
                result.error_message = f"Unknown pattern type: {pattern_type}"
            
            result.match_time = datetime.now()
            self.validation_history.append(result)
            
            return result
            
        except Exception as e:
            error_result = ValidationResult(
                pattern_name=pattern_name,
                success=False,
                error_message=str(e)
            )
            self.logger.error(f"Pattern validation error for {pattern_name}: {e}")
            return error_result
    
    def _validate_contains(self, data: str, pattern: str, result: ValidationResult) -> ValidationResult:
        """Validate contains pattern."""
        if pattern.lower() in data.lower():
            result.success = True
            result.matched_data = data
        return result
    
    def _validate_regex(self, data: str, pattern: str, result: ValidationResult) -> ValidationResult:
        """Validate regex pattern."""
        try:
            match = re.search(pattern, data)
            if match:
                result.success = True
                result.matched_data = data
                result.extracted_values = {
                    'full_match': match.group(0),
                    'groups': match.groups(),
                    'groupdict': match.groupdict()
                }
        except re.error as e:
            result.error_message = f"Invalid regex pattern: {e}"
        return result
    
    def _validate_exact(self, data: str, pattern: str, result: ValidationResult) -> ValidationResult:
        """Validate exact match pattern."""
        if data.strip() == pattern.strip():
            result.success = True
            result.matched_data = data
        return result
    
    def _validate_numeric_range(self, data: str, pattern: str, result: ValidationResult) -> ValidationResult:
        """Validate numeric range pattern (format: "min,max" or "value")."""
        try:
            # Extract numeric value from data
            numbers = re.findall(r'-?\d+\.?\d*', data)
            if not numbers:
                return result
            
            value = float(numbers[0])
            
            # Parse range pattern
            if ',' in pattern:
                min_val, max_val = map(float, pattern.split(','))
                if min_val <= value <= max_val:
                    result.success = True
                    result.matched_data = data
                    result.extracted_values = {'value': value, 'range': (min_val, max_val)}
            else:
                # Single value match
                target_value = float(pattern)
                if abs(value - target_value) < 0.001:  # Small tolerance for floating point
                    result.success = True
                    result.matched_data = data
                    result.extracted_values = {'value': value, 'target': target_value}
                    
        except (ValueError, IndexError) as e:
            result.error_message = f"Numeric validation error: {e}"
        return result
    
    def _validate_json_key(self, data: str, pattern: str, result: ValidationResult) -> ValidationResult:
        """Validate JSON key pattern."""
        try:
            import json
            json_data = json.loads(data)
            
            # Pattern format: "key1.key2.key3" for nested keys
            keys = pattern.split('.')
            current_data = json_data
            
            for key in keys:
                if isinstance(current_data, dict) and key in current_data:
                    current_data = current_data[key]
                else:
                    return result
            
            result.success = True
            result.matched_data = data
            result.extracted_values = {'json_value': current_data, 'path': pattern}
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            result.error_message = f"JSON validation error: {e}"
        return result
    
    def validate_multiple_patterns(self, data: str, pattern_configs: List[Dict]) -> List[ValidationResult]:
        """
        Validate data against multiple patterns.
        
        :param data: Data string to validate
        :param pattern_configs: List of pattern configuration dictionaries
        :return: List of ValidationResult objects
        """
        results = []
        for config in pattern_configs:
            result = self.validate_pattern(data, config)
            results.append(result)
        return results
    
    def wait_for_pattern_in_stream(self, uart_handler, pattern_config: Dict, 
                                 timeout: float = 10.0) -> Optional[ValidationResult]:
        """
        Wait for a pattern to appear in UART data stream.
        
        :param uart_handler: UARTHandler instance
        :param pattern_config: Pattern configuration dictionary
        :param timeout: Maximum time to wait
        :return: ValidationResult if pattern found, None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            data_entry = uart_handler.read_data(timeout=0.1)
            if data_entry:
                result = self.validate_pattern(data_entry['data'], pattern_config)
                if result.success:
                    return result
        
        # Timeout reached
        timeout_result = ValidationResult(
            pattern_name=pattern_config.get('name', 'unknown'),
            success=False,
            timeout_reached=True,
            error_message=f"Pattern not found within {timeout} seconds"
        )
        return timeout_result
    
    def get_validation_summary(self) -> Dict:
        """
        Get summary of validation history.
        
        :return: Dictionary with validation statistics
        """
        if not self.validation_history:
            return {'total_validations': 0, 'success_rate': 0}
        
        total = len(self.validation_history)
        successful = sum(1 for r in self.validation_history if r.success)
        
        pattern_stats = {}
        for result in self.validation_history:
            pattern_name = result.pattern_name
            if pattern_name not in pattern_stats:
                pattern_stats[pattern_name] = {'total': 0, 'successful': 0}
            
            pattern_stats[pattern_name]['total'] += 1
            if result.success:
                pattern_stats[pattern_name]['successful'] += 1
        
        return {
            'total_validations': total,
            'successful_validations': successful,
            'success_rate': successful / total if total > 0 else 0,
            'pattern_statistics': pattern_stats
        }
    
    def clear_history(self):
        """Clear validation history."""
        self.validation_history.clear()


class DataParser:
    """
    Advanced data parsing utilities for extracting structured information
    from UART data streams.
    """
    
    def __init__(self):
        """Initialize the data parser."""
        self.logger = logging.getLogger(__name__ + ".DataParser")
    
    def parse_temperature_data(self, data: str) -> Optional[Dict]:
        """
        Parse temperature data from various formats.
        
        :param data: Data string containing temperature information
        :return: Dictionary with temperature data or None
        """
        patterns = [
            r'Temperature:\s*([+-]?\d+\.?\d*)\s*°?C',
            r'TEMP:\s*([+-]?\d+\.?\d*)',
            r'Temp\s*=\s*([+-]?\d+\.?\d*)',
            r'([+-]?\d+\.?\d*)\s*°C'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                try:
                    temp = float(match.group(1))
                    return {
                        'temperature': temp,
                        'unit': 'C',
                        'raw_data': data,
                        'pattern_used': pattern
                    }
                except ValueError:
                    continue
        
        return None
    
    def parse_voltage_data(self, data: str) -> Optional[Dict]:
        """
        Parse voltage data from various formats.
        
        :param data: Data string containing voltage information
        :return: Dictionary with voltage data or None
        """
        patterns = [
            r'Voltage:\s*([+-]?\d+\.?\d*)\s*V',
            r'VOLT:\s*([+-]?\d+\.?\d*)',
            r'V\s*=\s*([+-]?\d+\.?\d*)',
            r'([+-]?\d+\.?\d*)\s*V'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                try:
                    voltage = float(match.group(1))
                    return {
                        'voltage': voltage,
                        'unit': 'V',
                        'raw_data': data,
                        'pattern_used': pattern
                    }
                except ValueError:
                    continue
        
        return None
    
    def parse_status_data(self, data: str) -> Optional[Dict]:
        """
        Parse status information from data.
        
        :param data: Data string containing status information
        :return: Dictionary with status data or None
        """
        status_keywords = ['OK', 'READY', 'ERROR', 'FAIL', 'PASS', 'RUNNING', 'IDLE', 'BUSY']
        
        for keyword in status_keywords:
            if keyword.lower() in data.lower():
                return {
                    'status': keyword,
                    'raw_data': data,
                    'timestamp': datetime.now()
                }
        
        return None
    
    def parse_json_data(self, data: str) -> Optional[Dict]:
        """
        Parse JSON data from string.
        
        :param data: Data string containing JSON
        :return: Parsed JSON data or None
        """
        try:
            import json
            return json.loads(data)
        except json.JSONDecodeError:
            return None
    
    def extract_numbers(self, data: str) -> List[float]:
        """
        Extract all numbers from data string.
        
        :param data: Data string
        :return: List of extracted numbers
        """
        numbers = re.findall(r'-?\d+\.?\d*', data)
        return [float(num) for num in numbers]
    
    def extract_key_value_pairs(self, data: str) -> Dict[str, str]:
        """
        Extract key-value pairs from data string.
        
        :param data: Data string
        :return: Dictionary of key-value pairs
        """
        # Pattern for "key: value" or "key=value" formats
        patterns = [
            r'(\w+)\s*[:=]\s*([^\s,]+)',
            r'"([^"]+)"\s*[:=]\s*"([^"]+)"'
        ]
        
        pairs = {}
        for pattern in patterns:
            matches = re.findall(pattern, data)
            for key, value in matches:
                pairs[key.strip()] = value.strip()
        
        return pairs


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create validator
    validator = PatternValidator()
    parser = DataParser()
    
    # Test data
    test_data = [
        "Temperature: 25.5°C",
        "Voltage: 3.3V",
        "Status: READY",
        "Boot sequence completed successfully",
        "Error: Connection timeout"
    ]
    
    # Test patterns
    patterns = [
        {
            'name': 'temperature',
            'pattern': r'Temperature:\s*([+-]?\d+\.?\d*)\s*°?C',
            'pattern_type': 'regex'
        },
        {
            'name': 'ready_status',
            'pattern': 'READY',
            'pattern_type': 'contains'
        },
        {
            'name': 'error_check',
            'pattern': 'ERROR|FAIL',
            'pattern_type': 'regex'
        }
    ]
    
    print("Testing pattern validation:")
    for data in test_data:
        print(f"\nData: {data}")
        
        # Validate patterns
        results = validator.validate_multiple_patterns(data, patterns)
        for result in results:
            print(f"  {result.pattern_name}: {'PASS' if result.success else 'FAIL'}")
            if result.extracted_values:
                print(f"    Extracted: {result.extracted_values}")
        
        # Parse data
        temp_data = parser.parse_temperature_data(data)
        if temp_data:
            print(f"  Temperature parsed: {temp_data}")
        
        voltage_data = parser.parse_voltage_data(data)
        if voltage_data:
            print(f"  Voltage parsed: {voltage_data}")
    
    # Print summary
    summary = validator.get_validation_summary()
    print(f"\nValidation Summary: {summary}")
