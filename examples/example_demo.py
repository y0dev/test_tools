#!/usr/bin/env python3
"""
Example script demonstrating the Automated Power Cycle and UART Validation Framework.
This script shows how to use the framework programmatically for custom test scenarios.
"""

import json
import time
from datetime import datetime
from libs.test_runner import PowerCycleTestRunner
from libs.pattern_validator import PatternValidator
from libs.uart_handler import UARTHandler


def create_example_config():
    """Create an example configuration for demonstration."""
    config = {
        "test_config": {
            "test_name": "Example Power Cycle Test",
            "test_description": "Demonstration of the framework capabilities",
            "total_cycles": 3,
            "cycle_delay": 1.0,
            "power_on_duration": 3.0,
            "power_off_duration": 2.0,
            "uart_timeout": 5.0
        },
        "power_supply": {
            "connection_type": "rs232",
            "port": "COM3",
            "baud_rate": 9600,
            "voltage": 5.0,
            "current_limit": 1.0,
            "timeout": 1.0
        },
        "uart": {
            "port": "COM4",
            "baud_rate": 115200,
            "data_bits": 8,
            "parity": "none",
            "stop_bits": 1,
            "timeout": 1.0,
            "buffer_size": 1024
        },
        "validation_patterns": [
            {
                "name": "boot_sequence",
                "pattern": "BOOT.*READY",
                "pattern_type": "regex",
                "timeout": 3.0,
                "required": True,
                "description": "Device boot sequence validation"
            },
            {
                "name": "version_info",
                "pattern": "Version: \\d+\\.\\d+",
                "pattern_type": "regex",
                "timeout": 2.0,
                "required": False,
                "description": "Firmware version information"
            },
            {
                "name": "status_ok",
                "pattern": "OK",
                "pattern_type": "contains",
                "timeout": 1.0,
                "required": True,
                "description": "Status OK check"
            }
        ],
        "output": {
            "log_directory": "logs",
            "report_directory": "reports",
            "csv_filename": "example_test_results.csv",
            "json_filename": "example_test_results.json",
            "text_filename": "example_test_summary.txt",
            "detailed_logs": True,
            "timestamp_format": "%Y-%m-%d_%H-%M-%S",
            "log_level": "INFO"
        },
        "duts": [
            {
                "id": "DUT_EXAMPLE",
                "name": "Example Device",
                "description": "Demonstration device",
                "enabled": True
            }
        ]
    }
    
    return config


def demonstrate_pattern_validation():
    """Demonstrate pattern validation capabilities."""
    print("=" * 60)
    print("PATTERN VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    validator = PatternValidator()
    
    # Test data samples
    test_data = [
        "System booting... BOOT sequence started",
        "Version: 1.2.3 - Build 2024",
        "Status: OK - All systems ready",
        "Error: Connection timeout",
        "Temperature: 25.5°C",
        "Voltage: 3.3V"
    ]
    
    # Pattern configurations
    patterns = [
        {
            "name": "boot_sequence",
            "pattern": "BOOT.*READY",
            "pattern_type": "regex"
        },
        {
            "name": "version_info",
            "pattern": "Version: \\d+\\.\\d+",
            "pattern_type": "regex"
        },
        {
            "name": "status_ok",
            "pattern": "OK",
            "pattern_type": "contains"
        },
        {
            "name": "error_check",
            "pattern": "ERROR|FAIL",
            "pattern_type": "regex"
        },
        {
            "name": "temperature",
            "pattern": "25.0,30.0",
            "pattern_type": "numeric_range"
        }
    ]
    
    print("Testing pattern validation with sample data:")
    print()
    
    for i, data in enumerate(test_data, 1):
        print(f"Test {i}: {data}")
        
        # Validate against all patterns
        results = validator.validate_multiple_patterns(data, patterns)
        
        for result in results:
            status = "✓ PASS" if result.success else "✗ FAIL"
            print(f"  {result.pattern_name}: {status}")
            
            if result.extracted_values:
                print(f"    Extracted: {result.extracted_values}")
        
        print()
    
    # Show validation summary
    summary = validator.get_validation_summary()
    print("Validation Summary:")
    print(f"  Total validations: {summary['total_validations']}")
    print(f"  Success rate: {summary['success_rate']:.1%}")
    print()


def demonstrate_uart_simulation():
    """Demonstrate UART handling with simulated data."""
    print("=" * 60)
    print("UART HANDLING DEMONSTRATION")
    print("=" * 60)
    
    # Create UART configuration (simulated)
    uart_config = {
        'port': 'COM4',
        'baud_rate': 115200,
        'data_bits': 8,
        'parity': 'N',
        'stop_bits': 1,
        'timeout': 1.0
    }
    
    print("UART Handler Configuration:")
    print(f"  Port: {uart_config['port']}")
    print(f"  Baud Rate: {uart_config['baud_rate']}")
    print(f"  Data Bits: {uart_config['data_bits']}")
    print(f"  Parity: {uart_config['parity']}")
    print(f"  Stop Bits: {uart_config['stop_bits']}")
    print()
    
    # Note: In a real scenario, you would connect to actual hardware
    print("Note: This is a simulation. In real usage, connect to actual UART hardware.")
    print("The UART handler would:")
    print("  1. Connect to the specified COM port")
    print("  2. Start continuous data logging")
    print("  3. Process incoming data in real-time")
    print("  4. Validate patterns as data arrives")
    print("  5. Generate comprehensive logs")
    print()


def demonstrate_test_runner():
    """Demonstrate the test runner capabilities."""
    print("=" * 60)
    print("TEST RUNNER DEMONSTRATION")
    print("=" * 60)
    
    # Create example configuration
    config = create_example_config()
    
    print("Test Configuration:")
    print(f"  Test Name: {config['test_config']['test_name']}")
    print(f"  Total Cycles: {config['test_config']['total_cycles']}")
    print(f"  Power On Duration: {config['test_config']['power_on_duration']}s")
    print(f"  Power Off Duration: {config['test_config']['power_off_duration']}s")
    print()
    
    print("Power Supply Configuration:")
    ps_config = config['power_supply']
    print(f"  Connection: {ps_config['connection_type']}")
    print(f"  Port: {ps_config['port']}")
    print(f"  Voltage: {ps_config['voltage']}V")
    print(f"  Current Limit: {ps_config['current_limit']}A")
    print()
    
    print("Validation Patterns:")
    for pattern in config['validation_patterns']:
        required = " (Required)" if pattern.get('required', False) else ""
        print(f"  - {pattern['name']}{required}")
        print(f"    Pattern: {pattern['pattern']}")
        print(f"    Type: {pattern['pattern_type']}")
        print(f"    Timeout: {pattern['timeout']}s")
    print()
    
    print("Output Configuration:")
    output_config = config['output']
    print(f"  Log Directory: {output_config['log_directory']}")
    print(f"  Report Directory: {output_config['report_directory']}")
    print(f"  Report Formats: CSV, JSON, HTML, Text")
    print()
    
    print("Note: This is a demonstration. In real usage:")
    print("  1. Connect to actual power supply hardware")
    print("  2. Connect to actual UART device")
    print("  3. Run automated power cycling")
    print("  4. Validate UART patterns in real-time")
    print("  5. Generate comprehensive test reports")
    print()


def demonstrate_report_generation():
    """Demonstrate report generation capabilities."""
    print("=" * 60)
    print("REPORT GENERATION DEMONSTRATION")
    print("=" * 60)
    
    # Simulate test results
    test_summary = {
        'test_name': 'Example Test',
        'session_timestamp': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
        'test_start_time': datetime.now().isoformat(),
        'test_end_time': datetime.now().isoformat(),
        'total_cycles': 3,
        'successful_cycles': 2,
        'failed_cycles': 1,
        'success_rate': 0.67,
        'total_uart_data_points': 15,
        'total_validations': 9,
        'total_errors': 2
    }
    
    cycle_data = [
        {
            'cycle_number': 1,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'success': True,
            'duration': datetime.now() - datetime.now(),
            'uart_data_count': 5,
            'validations': [
                {'pattern_name': 'boot_sequence', 'success': True, 'timestamp': datetime.now()},
                {'pattern_name': 'status_ok', 'success': True, 'timestamp': datetime.now()}
            ],
            'errors': []
        },
        {
            'cycle_number': 2,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'success': True,
            'duration': datetime.now() - datetime.now(),
            'uart_data_count': 5,
            'validations': [
                {'pattern_name': 'boot_sequence', 'success': True, 'timestamp': datetime.now()},
                {'pattern_name': 'status_ok', 'success': True, 'timestamp': datetime.now()}
            ],
            'errors': []
        },
        {
            'cycle_number': 3,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'success': False,
            'duration': datetime.now() - datetime.now(),
            'uart_data_count': 5,
            'validations': [
                {'pattern_name': 'boot_sequence', 'success': False, 'timestamp': datetime.now()},
                {'pattern_name': 'status_ok', 'success': False, 'timestamp': datetime.now()}
            ],
            'errors': [
                {'message': 'Boot sequence timeout', 'timestamp': datetime.now()}
            ]
        }
    ]
    
    print("Test Summary:")
    print(f"  Test Name: {test_summary['test_name']}")
    print(f"  Total Cycles: {test_summary['total_cycles']}")
    print(f"  Success Rate: {test_summary['success_rate']:.1%}")
    print(f"  Successful Cycles: {test_summary['successful_cycles']}")
    print(f"  Failed Cycles: {test_summary['failed_cycles']}")
    print()
    
    print("Cycle Details:")
    for cycle in cycle_data:
        status = "PASSED" if cycle['success'] else "FAILED"
        print(f"  Cycle {cycle['cycle_number']}: {status}")
        print(f"    UART Data Points: {cycle['uart_data_count']}")
        print(f"    Validations: {len(cycle['validations'])}")
        print(f"    Errors: {len(cycle['errors'])}")
    print()
    
    print("Report Generation:")
    print("  The framework generates reports in multiple formats:")
    print("  - CSV: Detailed test data for analysis")
    print("  - JSON: Structured data for programmatic processing")
    print("  - HTML: Visual reports with charts and tables")
    print("  - Text: Human-readable summary reports")
    print()
    
    print("Example report files would be created:")
    print("  - reports/example_test_results.csv")
    print("  - reports/example_test_results.json")
    print("  - reports/test_report_YYYY-MM-DD_HH-MM-SS.html")
    print("  - reports/example_test_summary.txt")
    print()


def main():
    """Main demonstration function."""
    print("Automated Power Cycle and UART Validation Framework")
    print("Demonstration Script")
    print("=" * 60)
    print()
    
    try:
        # Demonstrate each component
        demonstrate_pattern_validation()
        demonstrate_uart_simulation()
        demonstrate_test_runner()
        demonstrate_report_generation()
        
        print("=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print()
        print("To use this framework with real hardware:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Generate config: python main.py --generate-config")
        print("3. Edit config.json with your hardware settings")
        print("4. Run tests: python main.py --interactive")
        print()
        print("For more information, see README.md")
        
    except Exception as e:
        print(f"Demonstration error: {e}")


if __name__ == "__main__":
    main()
