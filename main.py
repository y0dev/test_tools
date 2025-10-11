#!/usr/bin/env python3
"""
Automated Power Cycle and UART Validation Framework
Main entry point with CLI interface for hardware testing automation.

This framework provides:
- Automated power cycling via Keysight E3632A power supply
- UART data logging and pattern validation
- Comprehensive test reporting (CSV, JSON, HTML, text)
- Configurable test parameters via JSON
- Multi-DUT support and scaling capabilities

Author: Automated Test Framework
Version: 1.0.0
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

from lib.test_runner import PowerCycleTestRunner
from lib.report_generator import ReportGenerator


def setup_argument_parser():
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Automated Power Cycle and UART Validation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Run with default config.json
  python main.py -c my_config.json        # Run with custom config
  python main.py --interactive            # Interactive mode with prompts
  python main.py --validate-config        # Validate configuration file
  python main.py --list-patterns          # List available validation patterns
  python main.py --generate-config        # Generate sample configuration
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config/config.json',
        help='Configuration file path (default: config/config.json)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode with user prompts'
    )
    
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration file and exit'
    )
    
    parser.add_argument(
        '--list-patterns',
        action='store_true',
        help='List available validation patterns and exit'
    )
    
    parser.add_argument(
        '--generate-config',
        action='store_true',
        help='Generate sample configuration file and exit'
    )
    
    parser.add_argument(
        '--list-templates',
        action='store_true',
        help='List available test templates and exit'
    )
    
    parser.add_argument(
        '--generate-templates',
        action='store_true',
        help='Generate sample test templates file and exit'
    )
    
    parser.add_argument(
        '--parse-logs',
        action='store_true',
        help='Parse existing log files and generate reports'
    )
    
    parser.add_argument(
        '--log-dir',
        default='./output/logs',
        help='Directory containing log files (default: ./output/logs)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--cycles',
        type=int,
        help='Override number of test cycles from config'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run without actual hardware control'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Override output directory for logs and reports'
    )
    
    return parser


def validate_config(config_file: str) -> bool:
    """
    Validate configuration file.
    
    :param config_file: Path to configuration file
    :return: True if valid, False otherwise
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ['power_supply', 'uart_loggers', 'tests']
        missing_sections = [section for section in required_sections if section not in config]
        
        if missing_sections:
            print(f"❌ Missing required configuration sections: {missing_sections}")
            return False
        
        # Validate power_supply
        ps_config = config['power_supply']
        if 'resource' not in ps_config and 'port' not in ps_config:
            print("❌ power_supply must have either 'resource' (GPIB) or 'port' (RS232)")
            return False
        
        # Validate uart_loggers
        uart_loggers = config['uart_loggers']
        if not isinstance(uart_loggers, list) or len(uart_loggers) == 0:
            print("❌ uart_loggers must be a non-empty list")
            return False
        
        for i, logger in enumerate(uart_loggers):
            if 'port' not in logger or 'baud' not in logger:
                print(f"❌ UART logger {i} missing required fields: 'port' and 'baud'")
                return False
        
        # Validate tests
        tests = config['tests']
        if not isinstance(tests, list) or len(tests) == 0:
            print("❌ tests must be a non-empty list")
            return False
        
        for i, test in enumerate(tests):
            if 'name' not in test or 'cycles' not in test:
                print(f"❌ Test {i} missing required fields: 'name' and 'cycles'")
                return False
            
            # Validate uart_patterns if present
            patterns = test.get('uart_patterns', [])
            for j, pattern in enumerate(patterns):
                if 'regex' not in pattern:
                    print(f"❌ Test {i}, Pattern {j} missing required field: 'regex'")
                    return False
        
        print("✅ Configuration file is valid")
        return True
        
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False


def list_validation_patterns():
    """List available validation pattern types and examples."""
    print("Available Validation Pattern Types:")
    print("=" * 50)
    
    patterns = [
        {
            'type': 'contains',
            'description': 'Simple string containment check',
            'example': {'name': 'boot_ready', 'pattern': 'READY', 'pattern_type': 'contains'}
        },
        {
            'type': 'regex',
            'description': 'Regular expression pattern matching',
            'example': {'name': 'version_info', 'pattern': 'Version: \\d+\\.\\d+', 'pattern_type': 'regex'}
        },
        {
            'type': 'exact',
            'description': 'Exact string match',
            'example': {'name': 'status_ok', 'pattern': 'OK', 'pattern_type': 'exact'}
        },
        {
            'type': 'numeric_range',
            'description': 'Numeric value within range',
            'example': {'name': 'voltage_check', 'pattern': '3.0,3.6', 'pattern_type': 'numeric_range'}
        },
        {
            'type': 'json_key',
            'description': 'JSON key existence check',
            'example': {'name': 'json_status', 'pattern': 'status', 'pattern_type': 'json_key'}
        }
    ]
    
    for pattern in patterns:
        print(f"\n{pattern['type'].upper()}:")
        print(f"  Description: {pattern['description']}")
        print(f"  Example: {json.dumps(pattern['example'], indent=4)}")


def generate_sample_config():
    """Generate a sample configuration file."""
    sample_config = {
        "power_supply": {
            "resource": "GPIB0::5::INSTR",
            "voltage": 5.0,
            "current_limit": 0.5
        },
        "uart_loggers": [
            {
                "port": "COM3",
                "baud": 115200,
                "display": True
            }
        ],
        "tests": [
            {
                "name": "Boot Data Test",
                "description": "Verify correct boot data is printed",
                "cycles": 1,
                "on_time": 5,
                "off_time": 3,
                "output_format": "json",
                "uart_patterns": [
                    {
                        "regex": "Data:\\s*(0x[0-9A-Fa-f]+),\\s*(0x[0-9A-Fa-f]+)",
                        "expected": [["0x12345678", "0xDEADBEEF"]]
                    },
                    {
                        "regex": "Version:\\s*v(\\d\\.\\d)",
                        "expected": ["v1.2"]
                    }
                ]
            }
        ]
    }
    
    filename = "config/sample_config.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"✅ Sample configuration generated: {filename}")
    print("Edit this file with your specific hardware settings before running tests.")


def list_test_templates():
    """List available test templates."""
    try:
        from lib.test_template_loader import TestTemplateLoader
        
        loader = TestTemplateLoader()
        loader.list_templates()
        
    except ImportError:
        print("❌ Template loader not available")
    except Exception as e:
        print(f"❌ Error listing templates: {e}")


def generate_sample_templates():
    """Generate a sample test templates file."""
    sample_templates = {
        "test_templates": {
            "boot_data_test": {
                "description": "Verify correct boot data is printed",
                "uart_patterns": [
                    {
                        "regex": "Data:\\s*(0x[0-9A-Fa-f]+),\\s*(0x[0-9A-Fa-f]+)",
                        "expected": [["0x12345678", "0xDEADBEEF"]]
                    },
                    {
                        "regex": "Version:\\s*v(\\d\\.\\d)",
                        "expected": ["v1.2"]
                    }
                ],
                "output_format": "json"
            },
            "power_cycle_test": {
                "description": "Test multiple power cycles",
                "uart_patterns": [
                    {
                        "regex": "READY",
                        "expected": ["READY"]
                    }
                ],
                "output_format": "csv"
            },
            "simple_ready_test": {
                "description": "Simple ready signal test",
                "uart_patterns": [
                    {
                        "regex": "READY",
                        "expected": ["READY"]
                    }
                ],
                "output_format": "text"
            }
        },
        "defaults": {
            "cycles": 1,
            "on_time": 5,
            "off_time": 3,
            "output_format": "json"
        }
    }
    
    filename = "config/test_templates.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sample_templates, f, indent=2)
    
    print(f"✅ Sample test templates generated: {filename}")
    print("Edit this file to customize your test templates.")


def parse_existing_logs(log_directory: str):
    """Parse existing log files and generate reports."""
    try:
        from lib.log_parser import LogParser
        
        parser = LogParser(log_directory)
        
        print("Analyzing existing log files...")
        parser.print_summary()
        
        # Generate reports
        json_report = parser.generate_report_from_logs()
        csv_report = parser.export_to_csv()
        
        print(f"\nReports generated:")
        print(f"  JSON: {json_report}")
        print(f"  CSV: {csv_report}")
        
    except ImportError:
        print("❌ Log parser not available")
    except Exception as e:
        print(f"❌ Error parsing logs: {e}")


def modify_config_for_args(config: dict, args) -> dict:
    """
    Modify configuration based on command line arguments.
    
    :param config: Original configuration
    :param args: Parsed command line arguments
    :return: Modified configuration
    """
    modified_config = config.copy()
    
    # Override cycles if specified
    if args.cycles:
        modified_config['test_config']['total_cycles'] = args.cycles
    
    # Override output directory if specified
    if args.output_dir:
        modified_config['output']['log_directory'] = args.output_dir
        modified_config['output']['report_directory'] = args.output_dir
    
    # Set log level
    modified_config['output']['log_level'] = args.log_level
    
    return modified_config


def main():
    """Main entry point."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.validate_config:
        success = validate_config(args.config)
        sys.exit(0 if success else 1)
    
    if args.list_patterns:
        list_validation_patterns()
        sys.exit(0)
    
    if args.generate_config:
        generate_sample_config()
        sys.exit(0)
    
    if args.list_templates:
        list_test_templates()
        sys.exit(0)
    
    if args.generate_templates:
        generate_sample_templates()
        sys.exit(0)
    
    if args.parse_logs:
        parse_existing_logs(args.log_dir)
        sys.exit(0)
    
    # Check if config file exists
    if not Path(args.config).exists():
        print(f"❌ Configuration file not found: {args.config}")
        print("Use --generate-config to create a sample configuration file.")
        sys.exit(1)
    
    # Validate configuration
    if not validate_config(args.config):
        sys.exit(1)
    
    try:
        # Load and modify configuration
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config = modify_config_for_args(config, args)
        
        # Create test runner
        runner = PowerCycleTestRunner()
        runner.config = config  # Override config
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Run test
        if args.interactive:
            runner.run_interactive_test()
        else:
            print("Starting automated power cycle and UART validation test...")
            print(f"Configuration: {args.config}")
            print(f"Log Level: {args.log_level}")
            
            if not runner.initialize_components():
                print("❌ Failed to initialize components")
                sys.exit(1)
            
            try:
                results = runner.run_test()
                
                if 'error' in results:
                    print(f"❌ Test failed: {results['error']}")
                    sys.exit(1)
                else:
                    print(f"✅ Test completed successfully!")
                    print(f"Success Rate: {results['success_rate']:.2%}")
                    print(f"Successful Cycles: {results['successful_cycles']}/{results['total_cycles']}")
                    
                    if results.get('report_files'):
                        print(f"\nReports generated:")
                        for format_type, filepath in results['report_files'].items():
                            print(f"  {format_type.upper()}: {filepath}")
            
            finally:
                runner.cleanup_components()
    
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logging.exception("Unexpected error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
