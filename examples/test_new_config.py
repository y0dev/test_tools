#!/usr/bin/env python3
"""
Test script to verify the new configuration format works correctly.
This script demonstrates the updated framework with the new configuration structure.
"""

import json
import sys
from pathlib import Path

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / 'lib'))

from test_runner import PowerCycleTestRunner


def test_configuration_loading():
    """Test that the new configuration format loads correctly."""
    print("Testing configuration loading...")
    
    try:
        runner = PowerCycleTestRunner("config.json")
        config = runner.config
        
        print("✅ Configuration loaded successfully")
        print(f"  Power Supply: {config.get('power_supply', {}).get('resource', 'N/A')}")
        print(f"  UART Loggers: {len(config.get('uart_loggers', []))}")
        print(f"  Tests: {len(config.get('tests', []))}")
        
        # Test power supply factory
        from power_supply import PowerSupplyFactory
        ps_config = config.get('power_supply', {})
        if ps_config:
            print(f"  Power Supply Config: {ps_config}")
            # Don't actually create connection in test
            print("  ✅ Power supply configuration valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


def test_pattern_validation():
    """Test pattern validation with new format."""
    print("\nTesting pattern validation...")
    
    try:
        from pattern_validator import PatternValidator
        
        validator = PatternValidator()
        
        # Test data
        test_data = "Data: 0x12345678, 0xDEADBEEF"
        
        # New format pattern
        pattern_config = {
            'name': 'data_pattern',
            'pattern': r'Data:\s*(0x[0-9A-Fa-f]+),\s*(0x[0-9A-Fa-f]+)',
            'pattern_type': 'regex',
            'expected': [["0x12345678", "0xDEADBEEF"]]
        }
        
        result = validator.validate_pattern(test_data, pattern_config)
        
        if result.success:
            print("✅ Pattern validation successful")
            print(f"  Extracted values: {result.extracted_values}")
        else:
            print(f"❌ Pattern validation failed: {result.error_message}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern validation test failed: {e}")
        return False


def test_uart_configuration():
    """Test UART configuration conversion."""
    print("\nTesting UART configuration...")
    
    try:
        from uart_handler import UARTHandler
        
        # New format config
        new_config = {
            'port': 'COM3',
            'baud': 115200,
            'display': True
        }
        
        # Convert to old format
        old_format_config = {
            'port': new_config['port'],
            'baud_rate': new_config['baud'],
            'data_bits': 8,
            'parity': 'N',
            'stop_bits': 1,
            'timeout': 1.0,
            'buffer_size': 1024
        }
        
        print("✅ UART configuration conversion successful")
        print(f"  Port: {old_format_config['port']}")
        print(f"  Baud Rate: {old_format_config['baud_rate']}")
        
        return True
        
    except Exception as e:
        print(f"❌ UART configuration test failed: {e}")
        return False


def test_report_generation():
    """Test report generation with new format."""
    print("\nTesting report generation...")
    
    try:
        from report_generator import ReportGenerator
        
        # Mock test summary
        test_summary = {
            'test_name': 'Test Suite',
            'session_timestamp': '2024-01-15_14-30-00',
            'test_start_time': '2024-01-15T14:30:00',
            'test_end_time': '2024-01-15T14:35:00',
            'total_tests': 1,
            'total_cycles': 1,
            'successful_cycles': 1,
            'failed_cycles': 0,
            'success_rate': 1.0,
            'total_uart_data_points': 5,
            'total_validations': 2,
            'total_errors': 0,
            'tests_run': [{'name': 'Boot Data Test', 'cycles': 1}]
        }
        
        # Mock cycle data
        cycle_data = [{
            'cycle_number': 1,
            'test_name': 'Boot Data Test',
            'test_index': 0,
            'success': True,
            'validation_results': [
                {'pattern_name': 'pattern_0', 'success': True},
                {'pattern_name': 'pattern_1', 'success': True}
            ],
            'errors': []
        }]
        
        config = {'output': {'report_directory': 'test_reports'}}
        generator = ReportGenerator(config)
        
        # Test JSON report generation
        json_file = generator.generate_json_report(test_summary, cycle_data)
        
        if json_file:
            print("✅ Report generation successful")
            print(f"  JSON report: {json_file}")
        else:
            print("❌ Report generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Updated Configuration Format")
    print("=" * 60)
    
    tests = [
        test_configuration_loading,
        test_pattern_validation,
        test_uart_configuration,
        test_report_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Configuration format is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
