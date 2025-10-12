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
- Interactive menu-based interface for user-friendly operation
- Command-line interface for automation and scripting

Key Features:
- Menu-driven interface when no arguments provided
- Template-based test configuration system
- Comprehensive logging with multiple output files
- Log parsing and historical data analysis
- Multiple output formats for reports
- Hardware abstraction for different power supply types

Author: Automated Test Framework
Version: 1.0.0
"""

import argparse
import sys
import json
import logging
import os
import time
from pathlib import Path
from datetime import datetime

from libs.test_runner import PowerCycleTestRunner
from libs.report_generator import ReportGenerator


def setup_argument_parser():
    """
    Setup command line argument parser with all available options.
    
    This function creates an ArgumentParser instance with comprehensive
    command-line options for the framework. It includes options for:
    - Configuration file management
    - Test execution modes
    - Logging and output control
    - Template and pattern management
    - Log analysis functionality
    
    Returns:
        argparse.ArgumentParser: Configured argument parser instance
    """
    parser = argparse.ArgumentParser(
        description="Automated Power Cycle and UART Validation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Show interactive menu
  python main.py -c my_config.json        # Run with custom config
  python main.py --interactive            # Interactive mode with prompts
  python main.py --validate-config        # Validate configuration file
  python main.py --list-patterns          # List available validation patterns
  python main.py --generate-config        # Generate sample configuration
  python main.py --parse-logs             # Analyze existing log files
        """
    )
    
    # Configuration file options
    parser.add_argument(
        '-c', '--config',
        default='config/config.json',
        help='Configuration file path (default: config/config.json)'
    )
    
    # Test execution modes
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode with user prompts'
    )
    
    # Configuration management options
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
    
    # Template management options
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
    
    # Log analysis options
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
    
    # Logging and output control
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
    Validate configuration file structure and content.
    
    This function performs comprehensive validation of the configuration file
    to ensure it contains all required sections and fields. It validates:
    - Required top-level sections (power_supply, uart_loggers, tests)
    - Power supply configuration (GPIB resource or RS232 port)
    - UART logger configuration (port, baud rate)
    - Test configuration (name, cycles, patterns)
    - Pattern validation (regex patterns)
    
    Args:
        config_file (str): Path to the configuration file to validate
        
    Returns:
        bool: True if configuration is valid, False otherwise
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        json.JSONDecodeError: If configuration file contains invalid JSON
        Exception: For other validation errors
    """
    try:
        # Load and parse the JSON configuration file
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate required top-level sections exist
        required_sections = ['power_supply', 'uart_loggers', 'tests']
        missing_sections = [section for section in required_sections if section not in config]
        
        if missing_sections:
            print(f"❌ Missing required configuration sections: {missing_sections}")
            return False
        
        # Validate power supply configuration
        # Must have either 'resource' (GPIB) or 'port' (RS232)
        ps_config = config['power_supply']
        if 'resource' not in ps_config and 'port' not in ps_config:
            print("❌ power_supply must have either 'resource' (GPIB) or 'port' (RS232)")
            return False
        
        # Validate UART loggers configuration
        # Must be a non-empty list with port and baud rate
        uart_loggers = config['uart_loggers']
        if not isinstance(uart_loggers, list) or len(uart_loggers) == 0:
            print("❌ uart_loggers must be a non-empty list")
            return False
        
        # Validate each UART logger has required fields
        for i, logger in enumerate(uart_loggers):
            if 'port' not in logger or 'baud' not in logger:
                print(f"❌ UART logger {i} missing required fields: 'port' and 'baud'")
                return False
        
        # Validate tests configuration
        # Must be a non-empty list with test definitions
        tests = config['tests']
        if not isinstance(tests, list) or len(tests) == 0:
            print("❌ tests must be a non-empty list")
            return False
        
        # Validate each test has required fields and patterns
        for i, test in enumerate(tests):
            if 'name' not in test or 'cycles' not in test:
                print(f"❌ Test {i} missing required fields: 'name' and 'cycles'")
                return False
            
            # Validate UART patterns if present
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
        from libs.test_template_loader import TestTemplateLoader
        
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
        from libs.log_parser import LogParser
        
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


def show_main_menu():
    """
    Display the main menu and handle user selections.
    
    This function provides the primary interface for users who run the
    application without command-line arguments. It displays a hierarchical
    menu system with the following main categories:
    - Run Tests: Execute interactive or automated tests
    - Configuration Management: Generate, validate, and manage configs
    - Log Analysis: Parse and analyze existing log files
    - Help & Documentation: Access help and project information
    - Exit: Clean exit from the application
    
    The menu runs in a loop until the user selects exit or interrupts
    with Ctrl+C. Each menu option leads to specialized sub-menus that
    provide focused functionality for specific tasks.
    
    Features:
    - Clear visual formatting with separators
    - Numbered options for easy selection
    - Error handling for invalid inputs
    - Keyboard interrupt support (Ctrl+C)
    - Graceful error handling and recovery
    """
    while True:
        print("\n" + "=" * 60)
        print("AUTOMATED POWER CYCLE AND UART VALIDATION FRAMEWORK")
        print("=" * 60)
        print()
        print("Main Menu:")
        print("1. Run Tests")
        print("2. Configuration Management")
        print("3. Log Analysis")
        print("4. JTAG Operations")
        print("5. STM32 Operations")
        print("6. Serial Logger")
        print("7. Automated Serial Setup")
        print("8. Help & Documentation")
        print("9. Exit")
        print()
        
        try:
            choice = input("Select an option (1-9): ").strip()
            
            if choice == '1':
                run_tests_menu()
            elif choice == '2':
                configuration_menu()
            elif choice == '3':
                log_analysis_menu()
            elif choice == '4':
                jtag_operations_menu()
            elif choice == '5':
                stm32_operations_menu()
            elif choice == '6':
                serial_logger_menu()
            elif choice == '7':
                automated_serial_setup_menu()
            elif choice == '8':
                help_menu()
            elif choice == '9':
                print("Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-9.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def run_tests_menu():
    """Menu for running tests."""
    while True:
        print("\n" + "-" * 40)
        print("RUN TESTS")
        print("-" * 40)
        print("1. Run Interactive Test")
        print("2. Run Automated Test")
        print("3. Validate Configuration")
        print("4. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-4): ").strip()
            
            if choice == '1':
                run_interactive_test()
            elif choice == '2':
                run_automated_test()
            elif choice == '3':
                validate_configuration()
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def configuration_menu():
    """Menu for configuration management."""
    while True:
        print("\n" + "-" * 40)
        print("CONFIGURATION MANAGEMENT")
        print("-" * 40)
        print("1. Generate Sample Configuration")
        print("2. Generate Sample Templates")
        print("3. List Available Templates")
        print("4. List Validation Patterns")
        print("5. Validate Configuration")
        print("6. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-6): ").strip()
            
            if choice == '1':
                generate_sample_config()
                input("\nPress Enter to continue...")
            elif choice == '2':
                generate_sample_templates()
                input("\nPress Enter to continue...")
            elif choice == '3':
                list_test_templates()
                input("\nPress Enter to continue...")
            elif choice == '4':
                list_validation_patterns()
                input("\nPress Enter to continue...")
            elif choice == '5':
                validate_configuration()
            elif choice == '6':
                break
            else:
                print("❌ Invalid choice. Please select 1-6.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def log_analysis_menu():
    """Menu for log analysis."""
    while True:
        print("\n" + "-" * 40)
        print("LOG ANALYSIS")
        print("-" * 40)
        print("1. Parse Existing Logs")
        print("2. Parse Logs from Custom Directory")
        print("3. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-3): ").strip()
            
            if choice == '1':
                parse_existing_logs('./output/logs')
                input("\nPress Enter to continue...")
            elif choice == '2':
                log_dir = input("Enter log directory path: ").strip()
                if log_dir:
                    parse_existing_logs(log_dir)
                else:
                    print("❌ No directory specified.")
                input("\nPress Enter to continue...")
            elif choice == '3':
                break
            else:
                print("❌ Invalid choice. Please select 1-3.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def jtag_operations_menu():
    """Menu for JTAG operations."""
    while True:
        print("\n" + "-" * 40)
        print("JTAG OPERATIONS")
        print("-" * 40)
        print("1. Run JTAG Test")
        print("2. JTAG Device Detection")
        print("3. Launch Tool in Separate Terminal")
        print("4. Monitor Terminal Processes")
        print("5. Send Command to Terminal")
        print("6. Kill Terminal Process")
        print("7. Generate Boot Image")
        print("8. Vivado Operations")
        print("9. Run Comprehensive Demo")
        print("10. Run JTAG Demo")
        print("11. Run Integration Demo")
        print("12. Generate JTAG Config")
        print("13. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-13): ").strip()
            
            if choice == '1':
                run_jtag_test()
            elif choice == '2':
                jtag_device_detection()
            elif choice == '3':
                launch_jtag_terminal()
            elif choice == '4':
                monitor_jtag_processes()
            elif choice == '5':
                send_jtag_command()
            elif choice == '6':
                kill_jtag_process()
            elif choice == '7':
                generate_boot_image()
            elif choice == '8':
                vivado_operations_menu()
            elif choice == '9':
                run_comprehensive_demo()
            elif choice == '10':
                run_jtag_demo()
            elif choice == '11':
                run_integration_demo()
            elif choice == '12':
                generate_jtag_config()
            elif choice == '13':
                break
            else:
                print("❌ Invalid choice. Please select 1-13.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def stm32_operations_menu():
    """Menu for STM32 operations."""
    while True:
        print("\n" + "-" * 40)
        print("STM32 OPERATIONS")
        print("-" * 40)
        print("1. Run STM32 Log Capture Test")
        print("2. Generate STM32 Config")
        print("3. List STM32 Templates")
        print("4. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-4): ").strip()
            
            if choice == '1':
                run_stm32_log_capture_test()
            elif choice == '2':
                generate_stm32_config()
            elif choice == '3':
                list_stm32_templates()
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def run_stm32_log_capture_test():
    """Run STM32 log capture test."""
    try:
        import subprocess
        import sys
        
        test_script = "stm32_log_capture_test.py"
        if not os.path.exists(test_script):
            print(f"❌ STM32 test script not found: {test_script}")
            return
        
        print("Running STM32 log capture test...")
        print("This will test STM32 UART logging and pattern validation")
        print()
        
        # Ask for configuration file
        config_file = input("Enter configuration file path (or press Enter for default): ").strip()
        if not config_file:
            config_file = "config/stm32_log_capture_config.json"
        
        # Build command
        cmd = [sys.executable, test_script]
        if config_file and os.path.exists(config_file):
            cmd.extend(["--config", config_file])
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            print("✅ STM32 log capture test completed successfully")
        else:
            print("❌ STM32 log capture test failed")
        
    except Exception as e:
        print(f"❌ Error running STM32 test: {e}")


def generate_stm32_config():
    """Generate STM32 configuration."""
    try:
        # Create sample STM32 configuration
        sample_config = {
            "power_supply": {
                "resource": "GPIB0::5::INSTR",
                "voltage": 3.3,
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
                    "name": "STM32 Log Capture Test",
                    "description": "Capture and validate STM32 UART output",
                    "cycles": 1,
                    "on_time": 10,
                    "off_time": 5,
                    "output_format": "json",
                    "uart_patterns": [
                        {
                            "regex": "^(\\d+)\\r\\n$",
                            "expected": ["5"],
                            "description": "Capture numeric output from DEV_SAMPLE_FUNCTION"
                        }
                    ]
                }
            ],
            "output": {
                "log_directory": "./output/logs",
                "report_directory": "./output/reports",
                "log_level": "INFO"
            }
        }
        
        filename = "config/stm32_log_capture_config.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"✅ STM32 configuration generated: {filename}")
        print("Edit this file with your specific STM32 settings.")
        
    except Exception as e:
        print(f"❌ Error generating STM32 configuration: {e}")


def list_stm32_templates():
    """List STM32 test templates."""
    try:
        config_file = "config/stm32_test_templates.json"
        if not os.path.exists(config_file):
            print(f"❌ STM32 templates file not found: {config_file}")
            return
        
        with open(config_file, 'r') as f:
            templates_data = json.load(f)
        
        templates = templates_data.get('test_templates', {})
        if not templates:
            print("No STM32 templates found")
            return
        
        print("Available STM32 Test Templates:")
        print("=" * 50)
        
        for template_name, template_data in templates.items():
            print(f"\n{template_name.upper()}:")
            print(f"  Description: {template_data.get('description', 'No description')}")
            print(f"  Output Format: {template_data.get('output_format', 'json')}")
            
            patterns = template_data.get('uart_patterns', [])
            if patterns:
                print(f"  Patterns: {len(patterns)} pattern(s)")
                for i, pattern in enumerate(patterns):
                    desc = pattern.get('description', 'No description')
                    print(f"    {i+1}. {desc}")
        
        print(f"\nTotal templates: {len(templates)}")
        
    except Exception as e:
        print(f"❌ Error listing STM32 templates: {e}")


def automated_serial_setup_menu():
    """Display automated serial setup menu."""
    while True:
        print("\n" + "="*50)
        print("Automated Serial Setup")
        print("="*50)
        print("1. Run Automated Setup")
        print("2. Create New Configuration")
        print("3. List Available Configurations")
        print("4. Test Configuration")
        print("5. Monitor Automation Status")
        print("6. Parse Automation Logs")
        print("7. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-7): ").strip()
            
            if choice == '1':
                run_automated_serial_setup()
            elif choice == '2':
                create_automated_serial_config()
            elif choice == '3':
                list_automated_serial_configs()
            elif choice == '4':
                test_automated_serial_config()
            elif choice == '5':
                monitor_automation_status()
            elif choice == '6':
                parse_automation_logs()
            elif choice == '7':
                break
            else:
                print("❌ Invalid choice. Please select 1-7.")
                
        except KeyboardInterrupt:
            print("\n\nReturning to main menu...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def run_automated_serial_setup():
    """Run automated serial setup."""
    try:
        print("\n=== Automated Serial Setup ===")
        
        # List available configurations
        config_files = get_automated_serial_configs()
        if not config_files:
            print("❌ No automated serial configurations found.")
            print("Use option 2 to create a new configuration.")
            return
        
        print("Available Automated Serial Configurations:")
        print("-" * 40)
        for i, config_file in enumerate(config_files):
            config_name = get_automated_config_display_name(config_file)
            print(f"  {i+1}. {config_name}")
        
        print(f"  {len(config_files)+1}. Enter custom path")
        print()
        
        # Get user selection
        choice = input(f"Select configuration (1-{len(config_files)+1}): ").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(config_files):
                config_file = config_files[choice_num - 1]
            elif choice_num == len(config_files) + 1:
                config_file = input("Enter configuration file path: ").strip()
                if not config_file:
                    print("❌ No configuration file specified")
                    return
            else:
                print("❌ Invalid selection")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Load configuration
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            return
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ Loaded configuration: {config['metadata']['name']}")
        print(f"   Description: {config['metadata']['description']}")
        print(f"   Steps: {len(config['steps'])}")
        print(f"   Serial Port: {config['serial']['port']} @ {config['serial']['baud']} baud")
        print()
        
        # Import and run automation
        from libs.automated_serial_setup import AutomatedSerialSetup
        
        automation = AutomatedSerialSetup(config)
        
        # Set up callbacks
        def on_step_complete(step_result):
            status = "✅ Success" if step_result['success'] else "❌ Failed"
            print(f"   Step {step_result['step_id']}: {step_result['step_name']} - {status}")
            if step_result['retry_count'] > 0:
                print(f"     (Retry #{step_result['retry_count']})")
        
        def on_completion(results):
            print()
            print("🎉 Automation completed successfully!")
            print(f"   Completed {len(results)} steps")
            print(f"   Log file: {automation.log_file_path}")
        
        def on_error(error_message):
            print()
            print(f"❌ Automation failed: {error_message}")
            print(f"   Log file: {automation.log_file_path}")
        
        automation.set_callbacks(on_step_complete, on_completion, on_error)
        
        # Confirm before running
        print("📋 Automation Steps:")
        for i, step in enumerate(config['steps'], 1):
            step_type = step.get('type', 'unknown')
            step_name = step.get('name', 'Unknown')
            print(f"   {i:2d}. {step['id']}: {step_name} ({step_type})")
        print()
        
        confirm = input("Run automation? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Automation cancelled.")
            return
        
        # Run automation
        print("\n🚀 Starting automation...")
        success = automation.run()
        
        if success:
            print("✅ Automation completed successfully!")
        else:
            print("❌ Automation failed!")
        
        automation.disconnect()
        
    except Exception as e:
        print(f"❌ Error running automated serial setup: {e}")

def get_automated_serial_configs():
    """Get list of automated serial configuration files."""
    config_dir = Path("config")
    if not config_dir.exists():
        return []
    
    # Look for automated serial config files
    patterns = [
        "automated_serial_setup_config*.json",
        "*_automated_serial*.json",
        "automated_*.json"
    ]
    
    config_files = []
    for pattern in patterns:
        config_files.extend(config_dir.glob(pattern))
    
    return sorted([str(f) for f in config_files])

def get_automated_config_display_name(config_file):
    """Get display name for automated serial config file."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Try metadata name first
        if 'metadata' in config and 'name' in config['metadata']:
            return config['metadata']['name']
        
        # Fallback to filename
        return Path(config_file).stem
        
    except Exception:
        return Path(config_file).stem

def create_automated_serial_config():
    """Create a new automated serial configuration."""
    try:
        print("\n=== Automated Serial Configuration Wizard ===")
        print("This wizard will help you create an automated serial setup configuration.")
        print()
        
        # Basic information
        config_name = input("Enter configuration name: ").strip()
        if not config_name:
            config_name = "Automated Serial Setup"
        
        description = input("Enter description (optional): ").strip()
        
        # Serial settings
        print("\n1. Serial Port Configuration")
        print("-" * 30)
        port = input("Enter serial port (e.g., COM3, COM1, /dev/ttyUSB0) [COM3]: ").strip()
        if not port:
            port = "COM3"
        
        baud = input("Enter baud rate [115200]: ").strip()
        if not baud:
            baud = 115200
        else:
            try:
                baud = int(baud)
            except ValueError:
                baud = 115200
        
        # Automation settings
        print("\n2. Automation Settings")
        print("-" * 30)
        max_retries = input("Maximum retries per step [3]: ").strip()
        if not max_retries:
            max_retries = 3
        else:
            try:
                max_retries = int(max_retries)
            except ValueError:
                max_retries = 3
        
        step_timeout = input("Step timeout in seconds [5.0]: ").strip()
        if not step_timeout:
            step_timeout = 5.0
        else:
            try:
                step_timeout = float(step_timeout)
            except ValueError:
                step_timeout = 5.0
        
        # Create basic steps
        print("\n3. Creating Basic Steps")
        print("-" * 30)
        
        steps = [
            {
                "id": "step_1",
                "name": "Initial Connection",
                "description": "Wait for device prompt",
                "type": "wait_for_prompt",
                "prompt_pattern": ">",
                "timeout": 10.0,
                "on_success": "step_2",
                "on_failure": "error_handler"
            },
            {
                "id": "step_2",
                "name": "Get Status",
                "description": "Get device status",
                "type": "send_command",
                "command": "status",
                "wait_for_response": True,
                "response_pattern": "Status:",
                "timeout": step_timeout,
                "on_success": "completion",
                "on_failure": "error_handler"
            },
            {
                "id": "completion",
                "name": "Setup Complete",
                "description": "Automation completed",
                "type": "completion",
                "message": "Automated serial setup completed successfully!"
            },
            {
                "id": "error_handler",
                "name": "Error Handler",
                "description": "Handle errors",
                "type": "error_handler",
                "retry_steps": ["step_1"],
                "max_retries": max_retries,
                "fallback_action": "stop"
            }
        ]
        
        # Build configuration
        config = {
            "metadata": {
                "name": config_name,
                "description": description,
                "created": datetime.now().isoformat(),
                "version": "1.0"
            },
            "serial": {
                "port": port,
                "baud": baud,
                "timeout": 1.0,
                "parity": "N",
                "stopbits": 1,
                "bytesize": 8
            },
            "automation": {
                "enabled": True,
                "max_retries": max_retries,
                "step_timeout": step_timeout,
                "wait_between_steps": 0.5,
                "log_all_interactions": True
            },
            "steps": steps,
            "logging": {
                "log_directory": "./output/automated_serial_logs",
                "log_format": "timestamp,step,action,data",
                "timestamp_format": "%Y-%m-%d %H:%M:%S.%f",
                "auto_create_dirs": True,
                "use_date_hierarchy": True,
                "date_format": "%Y/%m_%b/%m_%d"
            }
        }
        
        # Save configuration
        filename = f"config/automated_serial_{config_name.lower().replace(' ', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Automated serial configuration created successfully!")
        print(f"Configuration saved to: {filename}")
        print()
        print("Configuration Summary:")
        print(f"  Name: {config_name}")
        print(f"  Serial Port: {port} @ {baud} baud")
        print(f"  Steps: {len(steps)}")
        print(f"  Max Retries: {max_retries}")
        print(f"  Step Timeout: {step_timeout}s")
        
    except Exception as e:
        print(f"❌ Error creating automated serial configuration: {e}")

def list_automated_serial_configs():
    """List available automated serial configurations."""
    try:
        config_files = get_automated_serial_configs()
        
        if not config_files:
            print("❌ No automated serial configurations found.")
            print("Use option 2 to create a new configuration.")
            return
        
        print("Available Automated Serial Configurations:")
        print("=" * 50)
        
        for i, config_file in enumerate(config_files):
            config_name = get_automated_config_display_name(config_file)
            print(f"\n{i+1}. {config_name}")
            print(f"   File: {config_file}")
            
            # Load and display config details
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                if 'serial' in config:
                    port = config['serial'].get('port', 'Unknown')
                    baud = config['serial'].get('baud', 'Unknown')
                    print(f"   Serial: {port} @ {baud} baud")
                
                if 'steps' in config:
                    print(f"   Steps: {len(config['steps'])}")
                
                if 'automation' in config:
                    max_retries = config['automation'].get('max_retries', 'Unknown')
                    timeout = config['automation'].get('step_timeout', 'Unknown')
                    print(f"   Max Retries: {max_retries}, Timeout: {timeout}s")
                
            except Exception as e:
                print(f"   Error loading config: {e}")
        
    except Exception as e:
        print(f"❌ Error listing configurations: {e}")

def test_automated_serial_config():
    """Test automated serial configuration."""
    try:
        print("\n=== Test Automated Serial Configuration ===")
        
        # Run the test script
        import subprocess
        result = subprocess.run([sys.executable, "test_automated_serial_setup.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Configuration test passed!")
            print(result.stdout)
        else:
            print("❌ Configuration test failed!")
            print(result.stderr)
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")

def monitor_automation_status():
    """Monitor automation status (placeholder)."""
    print("\n=== Monitor Automation Status ===")
    print("This feature will be implemented in a future version.")
    print("For now, check the log files in ./output/automated_serial_logs/")

def parse_automation_logs():
    """Parse automation logs (placeholder)."""
    print("\n=== Parse Automation Logs ===")
    print("This feature will be implemented in a future version.")
    print("For now, check the log files in ./output/automated_serial_logs/")

def serial_logger_menu():
    """Menu for serial logger operations."""
    while True:
        print("\n" + "-" * 40)
        print("SERIAL LOGGER")
        print("-" * 40)
        print("1. Start Serial Logger")
        print("2. Parse Serial Data")
        print("3. Generate Serial Logger Config")
        print("4. List Serial Logger Configs")
        print("5. Select Default Config")
        print("6. List Data Parsing Patterns")
        print("7. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-7): ").strip()
            
            if choice == '1':
                start_serial_logger()
            elif choice == '2':
                parse_serial_data()
            elif choice == '3':
                generate_serial_logger_config()
            elif choice == '4':
                list_serial_logger_configs()
            elif choice == '5':
                select_default_config()
            elif choice == '6':
                list_data_parsing_patterns()
            elif choice == '7':
                break
            else:
                print("❌ Invalid choice. Please select 1-7.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def start_serial_logger():
    """Start serial logger with optional data parsing."""
    try:
        from libs.serial_logger import SerialLogger
        
        # Get available configurations
        config_files = get_serial_logger_configs()
        if not config_files:
            print("❌ No serial logger configurations found.")
            print("Use option 3 to generate a configuration file.")
            return
        
        # Show available configurations
        print("Available Serial Logger Configurations:")
        print("-" * 40)
        for i, config_file in enumerate(config_files):
            config_name = get_config_display_name(config_file)
            print(f"  {i+1}. {config_name}")
        
        print(f"  {len(config_files)+1}. Enter custom path")
        print()
        
        # Get user selection
        choice = input(f"Select configuration (1-{len(config_files)+1}): ").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(config_files):
                config_file = config_files[choice_num - 1]
            elif choice_num == len(config_files) + 1:
                config_file = input("Enter configuration file path: ").strip()
                if not config_file:
                    print("❌ No configuration file specified")
                    return
            else:
                print("❌ Invalid selection")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Check if config file exists
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            return
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Ask if user wants to parse data
        parse_data = input("Do you want to parse data in real-time? (y/n): ").strip().lower()
        parse_enabled = parse_data in ['y', 'yes']
        
        if parse_enabled:
            print("Real-time data parsing enabled")
        else:
            print("Raw data logging only")
        
        # Create and start serial logger
        logger = SerialLogger(config, parse_data=parse_enabled)
        
        print(f"Starting serial logger on {config['serial']['port']} at {config['serial']['baud']} baud...")
        print("Press Ctrl+C to stop logging")
        
        try:
            logger.start_logging()
        except KeyboardInterrupt:
            print("\n⚠️ Serial logging stopped by user")
            logger.stop_logging()
            
            # Ask if user wants to parse the logged data
            if not parse_enabled:
                parse_logged = input("Do you want to parse the logged data now? (y/n): ").strip().lower()
                if parse_logged in ['y', 'yes']:
                    parse_serial_data_from_file(logger.get_log_file())
        
    except ImportError:
        print("❌ Serial logger not available")
    except Exception as e:
        print(f"❌ Error starting serial logger: {e}")


def parse_serial_data():
    """Parse serial data from a log file."""
    try:
        from libs.serial_logger import SerialDataParser
        
        # Get log file path
        log_file = input("Enter log file path to parse: ").strip()
        if not log_file:
            print("❌ No log file specified")
            return
        
        if not os.path.exists(log_file):
            print(f"❌ Log file not found: {log_file}")
            return
        
        # Get available configurations
        config_files = get_serial_logger_configs()
        if not config_files:
            print("❌ No serial logger configurations found.")
            print("Use option 3 to generate a configuration file.")
            return
        
        # Show available configurations
        print("Select parsing configuration:")
        print("-" * 30)
        for i, config_file in enumerate(config_files):
            config_name = get_config_display_name(config_file)
            print(f"  {i+1}. {config_name}")
        
        print(f"  {len(config_files)+1}. Enter custom path")
        print()
        
        # Get user selection
        choice = input(f"Select configuration (1-{len(config_files)+1}): ").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(config_files):
                config_file = config_files[choice_num - 1]
            elif choice_num == len(config_files) + 1:
                config_file = input("Enter configuration file path: ").strip()
                if not config_file:
                    print("❌ No configuration file specified")
                    return
            else:
                print("❌ Invalid selection")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            return
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"Parsing data from: {log_file}")
        print(f"Using configuration: {get_config_display_name(config_file)}")
        print("Using parsing patterns from configuration...")
        
        # Create parser and parse data
        parser = SerialDataParser(config)
        results = parser.parse_log_file(log_file)
        
        if results:
            print(f"✅ Parsing completed successfully!")
            print(f"Found {len(results)} parsed entries")
            
            # Display summary
            parser.display_summary(results)
            
            # Ask if user wants to save results
            save_results = input("Do you want to save parsed results? (y/n): ").strip().lower()
            if save_results in ['y', 'yes']:
                output_file = input("Enter output file path (or press Enter for default): ").strip()
                if not output_file:
                    output_file = f"parsed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                parser.save_results(results, output_file)
                print(f"✅ Results saved to: {output_file}")
        else:
            print("❌ No data could be parsed from the log file")
        
    except ImportError:
        print("❌ Serial data parser not available")
    except Exception as e:
        print(f"❌ Error parsing serial data: {e}")


def parse_serial_data_from_file(log_file):
    """Parse serial data from a specific log file."""
    try:
        from libs.serial_logger import SerialDataParser
        
        # Use default config
        config_file = "config/serial_logger_config.json"
        
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            return
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"Parsing data from: {log_file}")
        
        # Create parser and parse data
        parser = SerialDataParser(config)
        results = parser.parse_log_file(log_file)
        
        if results:
            print(f"✅ Parsing completed successfully!")
            print(f"Found {len(results)} parsed entries")
            parser.display_summary(results)
        else:
            print("❌ No data could be parsed from the log file")
        
    except Exception as e:
        print(f"❌ Error parsing serial data: {e}")


def get_serial_logger_configs():
    """Get list of available serial logger configuration files."""
    config_dir = Path("config")
    config_files = []
    
    # Look for serial logger config files
    patterns = [
        "serial_logger_config*.json",
        "*_serial_logger.json",
        "serial_*.json"
    ]
    
    for pattern in patterns:
        config_files.extend(config_dir.glob(pattern))
    
    # Remove duplicates and sort
    config_files = sorted(list(set(config_files)))
    
    # Convert to strings
    return [str(f) for f in config_files]


def get_config_display_name(config_file):
    """Get a user-friendly display name for a configuration file."""
    try:
        # Try to load config and get name from metadata
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Check for custom name in config
        if 'metadata' in config and 'name' in config['metadata']:
            return config['metadata']['name']
        
        # Check for description
        if 'metadata' in config and 'description' in config['metadata']:
            return config['metadata']['description']
        
        # Use port and baud rate as identifier
        if 'serial' in config:
            port = config['serial'].get('port', 'Unknown')
            baud = config['serial'].get('baud', 'Unknown')
            return f"{port} @ {baud} baud"
        
    except Exception:
        pass
    
    # Fallback to filename
    return Path(config_file).stem


def list_serial_logger_configs():
    """List available serial logger configurations."""
    try:
        config_files = get_serial_logger_configs()
        
        if not config_files:
            print("No serial logger configurations found.")
            print("Use option 3 to generate a configuration file.")
            return
        
        print("Available Serial Logger Configurations:")
        print("=" * 50)
        
        for i, config_file in enumerate(config_files):
            config_name = get_config_display_name(config_file)
            print(f"\n{i+1}. {config_name}")
            print(f"   File: {config_file}")
            
            # Load and display config details
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                if 'serial' in config:
                    port = config['serial'].get('port', 'Unknown')
                    baud = config['serial'].get('baud', 'Unknown')
                    print(f"   Serial: {port} @ {baud} baud")
                
                if 'logging' in config:
                    log_dir = config['logging'].get('log_directory', 'Unknown')
                    hierarchy = config['logging'].get('use_date_hierarchy', False)
                    print(f"   Logging: {log_dir} (hierarchy: {'Yes' if hierarchy else 'No'})")
                
                if 'data_parsing' in config:
                    enabled = config['data_parsing'].get('enabled', False)
                    patterns = len(config['data_parsing'].get('patterns', []))
                    print(f"   Parsing: {'Enabled' if enabled else 'Disabled'} ({patterns} patterns)")
                
            except Exception as e:
                print(f"   Error reading config: {e}")
        
        print(f"\nTotal configurations: {len(config_files)}")
        
    except Exception as e:
        print(f"❌ Error listing configurations: {e}")


def select_default_config():
    """Set a default serial logger configuration."""
    try:
        config_files = get_serial_logger_configs()
        
        if not config_files:
            print("No serial logger configurations found.")
            print("Use option 3 to generate a configuration file.")
            return
        
        print("Select Default Serial Logger Configuration:")
        print("-" * 40)
        for i, config_file in enumerate(config_files):
            config_name = get_config_display_name(config_file)
            print(f"  {i+1}. {config_name}")
        
        choice = input(f"Select default configuration (1-{len(config_files)}): ").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(config_files):
                selected_config = config_files[choice_num - 1]
                
                # Create or update default config link
                default_config_path = "config/serial_logger_config.json"
                
                # If the selected config is not the default, copy it
                if selected_config != default_config_path:
                    import shutil
                    shutil.copy2(selected_config, default_config_path)
                    print(f"✅ Default configuration set to: {get_config_display_name(selected_config)}")
                else:
                    print("✅ This configuration is already the default")
                
            else:
                print("❌ Invalid selection")
                
        except ValueError:
            print("❌ Invalid input")
        
    except Exception as e:
        print(f"❌ Error setting default configuration: {e}")


def generate_serial_logger_config():
    """Generate serial logger configuration with interactive wizard."""
    try:
        print("Serial Logger Configuration Wizard")
        print("=" * 50)
        print("This wizard will help you create a customized serial logger configuration.")
        print()
        
        # Configuration metadata
        print("0. Configuration Metadata")
        print("-" * 30)
        config_name = input("Enter configuration name (e.g., 'Arduino Uno', 'ESP32 Dev Board'): ").strip()
        if not config_name:
            config_name = "Serial Logger Config"
        
        config_description = input("Enter description (optional): ").strip()
        
        # Ask for custom filename
        custom_filename = input("Enter custom filename (or press Enter for auto-generated): ").strip()
        if not custom_filename:
            # Generate filename from name
            safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            custom_filename = f"serial_logger_{safe_name}.json"
        
        if not custom_filename.endswith('.json'):
            custom_filename += '.json'
        
        print(f"Configuration will be saved as: config/{custom_filename}")
        print()
        
        # Serial port configuration
        print("1. Serial Port Configuration")
        print("-" * 30)
        port = input("Enter serial port (e.g., COM3, COM1, /dev/ttyUSB0) [COM3]: ").strip()
        if not port:
            port = "COM3"
        
        baud = input("Enter baud rate [115200]: ").strip()
        if not baud:
            baud = 115200
        else:
            try:
                baud = int(baud)
            except ValueError:
                baud = 115200
        
        timeout = input("Enter timeout in seconds [1.0]: ").strip()
        if not timeout:
            timeout = 1.0
        else:
            try:
                timeout = float(timeout)
            except ValueError:
                timeout = 1.0
        
        print(f"Serial settings: Port={port}, Baud={baud}, Timeout={timeout}")
        print()
        
        # Logging configuration
        print("2. Logging Configuration")
        print("-" * 30)
        log_dir = input("Enter log directory [./output/serial_logs]: ").strip()
        if not log_dir:
            log_dir = "./output/serial_logs"
        
        use_hierarchy = input("Use date-based directory hierarchy? (y/n) [y]: ").strip().lower()
        use_hierarchy = use_hierarchy in ['y', 'yes', ''] or use_hierarchy == ''
        
        if use_hierarchy:
            print("Date hierarchy format: YYYY/MM_MMM/MM_DD (e.g., 2025/10_Oct/10_12)")
            custom_format = input("Enter custom date format (or press Enter for default): ").strip()
            if not custom_format:
                custom_format = "%Y/%m_%b/%m_%d"
        else:
            custom_format = None
        
        print(f"Logging settings: Directory={log_dir}, Hierarchy={use_hierarchy}")
        print()
        
        # Data parsing configuration
        print("3. Data Parsing Configuration")
        print("-" * 30)
        enable_parsing = input("Enable data parsing? (y/n) [y]: ").strip().lower()
        enable_parsing = enable_parsing in ['y', 'yes', ''] or enable_parsing == ''
        
        patterns = []
        if enable_parsing:
            print("Configure parsing patterns:")
            print("Available pattern types:")
            print("  - numeric: Extract numbers (e.g., '123.45')")
            print("  - status: Extract status messages (e.g., 'STATUS: READY')")
            print("  - sensor: Extract sensor data (e.g., 'TEMP: 25.3')")
            print("  - error: Extract error codes (e.g., 'ERROR 101: Connection failed')")
            print("  - custom: Define your own pattern")
            print()
            
            while True:
                add_pattern = input("Add a parsing pattern? (y/n) [y]: ").strip().lower()
                if add_pattern not in ['y', 'yes', '']:
                    break
                
                print("\nPattern Configuration:")
                name = input("Pattern name: ").strip()
                if not name:
                    continue
                
                description = input("Description: ").strip()
                
                print("Pattern types:")
                print("1. Numeric data (extracts numbers)")
                print("2. Status message (extracts status text)")
                print("3. Sensor data (extracts sensor readings)")
                print("4. Error codes (extracts error info)")
                print("5. Custom pattern")
                
                pattern_type = input("Select pattern type (1-5) [1]: ").strip()
                
                if pattern_type == '1':
                    regex = "^(\\d+(?:\\.\\d+)?)\\r?\\n$"
                    data_type = "float"
                    extract_groups = [1]
                    labels = []
                elif pattern_type == '2':
                    regex = "STATUS:\\s*(\\w+)"
                    data_type = "string"
                    extract_groups = [1]
                    labels = []
                elif pattern_type == '3':
                    regex = "SENSOR\\s+(\\w+):\\s*(\\d+(?:\\.\\d+)?)"
                    data_type = "sensor"
                    extract_groups = [1, 2]
                    labels = ["sensor_name", "value"]
                elif pattern_type == '4':
                    regex = "ERROR\\s+(\\d+):\\s*(.+)"
                    data_type = "error"
                    extract_groups = [1, 2]
                    labels = ["error_code", "message"]
                else:
                    regex = input("Enter regex pattern: ").strip()
                    data_type = input("Data type (string/float/int) [string]: ").strip() or "string"
                    
                    groups_input = input("Enter group numbers to extract (comma-separated, e.g., 1,2): ").strip()
                    if groups_input:
                        try:
                            extract_groups = [int(x.strip()) for x in groups_input.split(',')]
                        except ValueError:
                            extract_groups = [1]
                    else:
                        extract_groups = [1]
                    
                    labels_input = input("Enter labels for groups (comma-separated, optional): ").strip()
                    labels = [x.strip() for x in labels_input.split(',')] if labels_input else []
                
                pattern = {
                    "name": name,
                    "description": description,
                    "regex": regex,
                    "type": data_type,
                    "extract_groups": extract_groups
                }
                
                if labels:
                    pattern["labels"] = labels
                
                patterns.append(pattern)
                print(f"Added pattern: {name}")
                print()
        
        print(f"Parsing settings: Enabled={enable_parsing}, Patterns={len(patterns)}")
        print()
        
        # Data filtering configuration
        print("4. Data Filtering Configuration")
        print("-" * 30)
        min_length = input("Minimum data length [1]: ").strip()
        if not min_length:
            min_length = 1
        else:
            try:
                min_length = int(min_length)
            except ValueError:
                min_length = 1
        
        max_length = input("Maximum data length [1000]: ").strip()
        if not max_length:
            max_length = 1000
        else:
            try:
                max_length = int(max_length)
            except ValueError:
                max_length = 1000
        
        print("Exclude patterns (regex patterns to skip):")
        exclude_patterns = []
        while True:
            exclude = input("Add exclude pattern (or press Enter to finish): ").strip()
            if not exclude:
                break
            exclude_patterns.append(exclude)
        
        print(f"Filtering settings: Min={min_length}, Max={max_length}, Exclude={len(exclude_patterns)}")
        print()
        
        # Build configuration
        config = {
            "metadata": {
                "name": config_name,
                "description": config_description,
                "created": datetime.now().isoformat(),
                "version": "1.0"
            },
            "serial": {
                "port": port,
                "baud": baud,
                "timeout": timeout,
                "parity": "N",
                "stopbits": 1,
                "bytesize": 8
            },
            "logging": {
                "log_directory": log_dir,
                "log_format": "timestamp,data",
                "timestamp_format": "%Y-%m-%d %H:%M:%S.%f",
                "auto_create_dirs": True,
                "use_date_hierarchy": use_hierarchy
            },
            "data_parsing": {
                "enabled": enable_parsing,
                "patterns": patterns,
                "output_formats": ["json", "csv", "txt"],
                "save_raw_data": True
            },
            "filters": {
                "min_data_length": min_length,
                "max_data_length": max_length,
                "exclude_patterns": exclude_patterns,
                "include_patterns": []
            }
        }
        
        if use_hierarchy and custom_format:
            config["logging"]["date_format"] = custom_format
        
        # Save configuration
        filename = f"config/{custom_filename}"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Serial logger configuration generated successfully!")
        print(f"Configuration saved to: {filename}")
        print()
        print("Configuration Summary:")
        print(f"  Serial Port: {port} @ {baud} baud")
        print(f"  Log Directory: {log_dir}")
        print(f"  Date Hierarchy: {'Yes' if use_hierarchy else 'No'}")
        print(f"  Data Parsing: {'Enabled' if enable_parsing else 'Disabled'}")
        print(f"  Parsing Patterns: {len(patterns)}")
        print(f"  Data Filters: {min_length}-{max_length} chars, {len(exclude_patterns)} exclusions")
        
    except Exception as e:
        print(f"❌ Error generating serial logger configuration: {e}")


def list_data_parsing_patterns():
    """List available data parsing patterns."""
    try:
        config_file = "config/serial_logger_config.json"
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            print("Use option 3 to generate a sample configuration file.")
            return
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        patterns = config.get('data_parsing', {}).get('patterns', [])
        if not patterns:
            print("No parsing patterns configured")
            return
        
        print("Available Data Parsing Patterns:")
        print("=" * 50)
        
        for i, pattern in enumerate(patterns):
            print(f"\n{i+1}. {pattern.get('name', 'Unnamed').upper()}:")
            print(f"   Description: {pattern.get('description', 'No description')}")
            print(f"   Type: {pattern.get('type', 'string')}")
            print(f"   Regex: {pattern.get('regex', 'Not specified')}")
            
            extract_groups = pattern.get('extract_groups', [])
            if extract_groups:
                print(f"   Extract Groups: {extract_groups}")
            
            labels = pattern.get('labels', [])
            if labels:
                print(f"   Labels: {labels}")
        
        print(f"\nTotal patterns: {len(patterns)}")
        
    except Exception as e:
        print(f"❌ Error listing parsing patterns: {e}")


def help_menu():
    """Menu for help and documentation."""
    while True:
        print("\n" + "-" * 40)
        print("HELP & DOCUMENTATION")
        print("-" * 40)
        print("1. Show Command Line Help")
        print("2. Show Project Structure")
        print("3. Show Quick Start Guide")
        print("4. Back to Main Menu")
        print()
        
        try:
            choice = input("Select an option (1-4): ").strip()
            
            if choice == '1':
                show_command_line_help()
            elif choice == '2':
                show_project_structure()
            elif choice == '3':
                show_quick_start_guide()
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def launch_jtag_terminal():
    """Launch JTAG tool in separate terminal."""
    try:
        from libs.xilinx_jtag import XilinxJTAGInterface, JTAGConfig, load_jtag_config
        
        # Load configuration
        config_file = get_config_file()
        if not config_file:
            return
        
        config = load_jtag_config(config_file)
        jtag = XilinxJTAGInterface(config)
        
        # Get tool selection
        print("Select JTAG Tool:")
        print("1. anxsct (AMD Xilinx System Control Tool)")
        print("2. xsdb (Xilinx Software Debugger)")
        
        tool_choice = input("Select tool (1-2): ").strip()
        
        if tool_choice == '1':
            tool_name = "anxsct_terminal"
            args = []
        elif tool_choice == '2':
            tool_name = "xsdb_terminal"
            args = []
        else:
            print("❌ Invalid tool selection")
            return
        
        # Launch in separate terminal
        print(f"Launching {tool_name} in separate terminal...")
        success = jtag.launch_in_separate_terminal(tool_name, args)
        
        if success:
            print(f"✅ {tool_name} launched successfully")
            print("The tool is now running in a separate terminal window.")
            print("Use 'Monitor Terminal Processes' to check its status.")
        else:
            print(f"❌ Failed to launch {tool_name}")
        
    except ImportError:
        print("❌ Xilinx JTAG interface not available")
    except Exception as e:
        print(f"❌ Error launching JTAG terminal: {e}")


def monitor_jtag_processes():
    """Monitor JTAG terminal processes."""
    try:
        from libs.xilinx_jtag import XilinxJTAGInterface, JTAGConfig, load_jtag_config
        
        # Load configuration
        config_file = get_config_file()
        if not config_file:
            return
        
        config = load_jtag_config(config_file)
        jtag = XilinxJTAGInterface(config)
        
        # Get list of processes
        processes = jtag.list_terminal_processes()
        
        if not processes:
            print("No JTAG terminal processes found.")
            print("Use 'Launch Tool in Separate Terminal' to start a process.")
            return
        
        print("JTAG Terminal Processes:")
        print("=" * 60)
        
        for i, process in enumerate(processes):
            if process:
                status_icon = "🟢" if process['is_running'] else "🔴"
                print(f"\n{i+1}. {status_icon} {process['name']}")
                print(f"   PID: {process['pid'] or 'N/A'}")
                print(f"   Status: {process['status']}")
                print(f"   Executable: {process['executable']}")
                print(f"   Title: {process['title']}")
                print(f"   Output Lines: {process['output_lines']}")
                print(f"   Error Lines: {process['error_lines']}")
                
                if process['start_time']:
                    runtime = time.time() - process['start_time']
                    print(f"   Runtime: {runtime:.1f} seconds")
        
        print(f"\nTotal processes: {len([p for p in processes if p])}")
        
        # Show recent output for running processes
        running_processes = [p for p in processes if p and p['is_running']]
        if running_processes:
            print("\nRecent Output:")
            print("-" * 40)
            
            for process in running_processes:
                tool_name = process['name']
                output = jtag.get_terminal_output(tool_name, 5)
                errors = jtag.get_terminal_errors(tool_name, 5)
                
                if output:
                    print(f"\n{tool_name} Output:")
                    for line in output:
                        print(f"  {line}")
                
                if errors:
                    print(f"\n{tool_name} Errors:")
                    for line in errors:
                        print(f"  ❌ {line}")
        
    except ImportError:
        print("❌ Xilinx JTAG interface not available")
    except Exception as e:
        print(f"❌ Error monitoring processes: {e}")


def send_jtag_command():
    """Send command to JTAG terminal process."""
    try:
        from libs.xilinx_jtag import XilinxJTAGInterface, JTAGConfig, load_jtag_config
        
        # Load configuration
        config_file = get_config_file()
        if not config_file:
            return
        
        config = load_jtag_config(config_file)
        jtag = XilinxJTAGInterface(config)
        
        # Get list of running processes
        processes = jtag.list_terminal_processes()
        running_processes = [p for p in processes if p and p['is_running']]
        
        if not running_processes:
            print("No running JTAG terminal processes found.")
            print("Use 'Launch Tool in Separate Terminal' to start a process.")
            return
        
        print("Running JTAG Terminal Processes:")
        for i, process in enumerate(running_processes):
            print(f"  {i+1}. {process['name']} (PID: {process['pid']})")
        
        # Get process selection
        choice = input(f"Select process (1-{len(running_processes)}): ").strip()
        try:
            process_index = int(choice) - 1
            if 0 <= process_index < len(running_processes):
                selected_process = running_processes[process_index]
                tool_name = selected_process['name']
            else:
                print("❌ Invalid process selection")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Get command
        command = input("Enter command to send: ").strip()
        if not command:
            print("❌ No command specified")
            return
        
        # Send command
        success = jtag.send_terminal_command(command, tool_name)
        
        if success:
            print(f"✅ Command sent to {tool_name}: {command}")
            print("Check the terminal window or use 'Monitor Terminal Processes' to see output.")
        else:
            print(f"❌ Failed to send command to {tool_name}")
        
    except ImportError:
        print("❌ Xilinx JTAG interface not available")
    except Exception as e:
        print(f"❌ Error sending command: {e}")


def kill_jtag_process():
    """Kill JTAG terminal process."""
    try:
        from libs.xilinx_jtag import XilinxJTAGInterface, JTAGConfig, load_jtag_config
        
        # Load configuration
        config_file = get_config_file()
        if not config_file:
            return
        
        config = load_jtag_config(config_file)
        jtag = XilinxJTAGInterface(config)
        
        # Get list of processes
        processes = jtag.list_terminal_processes()
        all_processes = [p for p in processes if p]
        
        if not all_processes:
            print("No JTAG terminal processes found.")
            return
        
        print("JTAG Terminal Processes:")
        for i, process in enumerate(all_processes):
            status_icon = "🟢" if process['is_running'] else "🔴"
            print(f"  {i+1}. {status_icon} {process['name']} - {process['status']}")
        
        # Get process selection
        choice = input(f"Select process to kill (1-{len(all_processes)}): ").strip()
        try:
            process_index = int(choice) - 1
            if 0 <= process_index < len(all_processes):
                selected_process = all_processes[process_index]
                tool_name = selected_process['name']
            else:
                print("❌ Invalid process selection")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Confirm kill
        confirm = input(f"Are you sure you want to kill {tool_name}? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled")
            return
        
        # Ask for force kill
        force = input("Force kill? (y/n): ").strip().lower()
        force_kill = force in ['y', 'yes']
        
        # Kill process
        success = jtag.kill_terminal_process(tool_name, force_kill)
        
        if success:
            print(f"✅ Process {tool_name} killed successfully")
        else:
            print(f"❌ Failed to kill process {tool_name}")
        
    except ImportError:
        print("❌ Xilinx JTAG interface not available")
    except Exception as e:
        print(f"❌ Error killing process: {e}")


def run_jtag_test():
    """Run JTAG-enabled test."""
    try:
        from libs.jtag_test_runner import JTAGTestRunner
        
        config_file = get_config_file()
        if not config_file:
            return
            
        print(f"Running JTAG test with config: {config_file}")
        
        # Create JTAG test runner
        runner = JTAGTestRunner(config_file)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize and run test
        if not runner.initialize_components():
            print("❌ Failed to initialize components")
            return
        
        try:
            # Run JTAG test
            results = runner.run_jtag_test()
            
            # Display test results
            if 'error' in results:
                print(f"❌ Test failed: {results['error']}")
            else:
                print(f"✅ JTAG test completed successfully!")
                print(f"Success Rate: {results['success_rate']:.2%}")
                print(f"Successful Cycles: {results['successful_cycles']}/{results['total_cycles']}")
                
                if results.get('report_files'):
                    print(f"\nReports generated:")
                    for format_type, filepath in results['report_files'].items():
                        print(f"  {format_type.upper()}: {filepath}")
        
        finally:
            runner.cleanup_components()
        
    except ImportError:
        print("❌ JTAG test runner not available")
    except Exception as e:
        print(f"❌ Error running JTAG test: {e}")


def jtag_device_detection():
    """Run JTAG device detection."""
    try:
        from libs.xilinx_jtag import XilinxJTAGInterface, JTAGConfig, JTAGInterface
        
        print("Scanning for JTAG devices...")
        
        # Create JTAG interface
        config = JTAGConfig(verbose_logging=True)
        with XilinxJTAGInterface(config) as jtag:
            devices = jtag.scan_devices()
            
            if not devices:
                print("❌ No JTAG devices found")
            else:
                print(f"✅ Found {len(devices)} JTAG device(s):")
                for device in devices:
                    print(f"  Device {device.index}: {device.name} (ID: {device.idcode})")
        
    except ImportError:
        print("❌ JTAG library not available")
    except Exception as e:
        print(f"❌ Error during device detection: {e}")


def run_jtag_demo():
    """Run JTAG demo."""
    try:
        import subprocess
        import sys
        
        demo_script = "examples/xilinx_jtag_demo.py"
        if not os.path.exists(demo_script):
            print(f"❌ Demo script not found: {demo_script}")
            return
        
        print("Running JTAG demo...")
        result = subprocess.run([sys.executable, demo_script], capture_output=False)
        
        if result.returncode == 0:
            print("✅ JTAG demo completed successfully")
        else:
            print("❌ JTAG demo failed")
        
    except Exception as e:
        print(f"❌ Error running JTAG demo: {e}")


def generate_boot_image():
    """Generate boot image using bootgen."""
    try:
        from libs.xilinx_tools_manager import XilinxToolsManager, load_xilinx_tools_config
        
        config_file = get_config_file()
        if not config_file:
            return
        
        print(f"Generating boot image with config: {config_file}")
        
        # Load configuration
        config = load_xilinx_tools_config(config_file)
        manager = XilinxToolsManager(config)
        
        # Resolve tool paths
        manager.resolve_tool_paths()
        
        # Initialize bootgen
        if not manager.initialize_bootgen():
            print("❌ Failed to initialize bootgen")
            return
        
        # Load bootgen configuration
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        bootgen_config = config_data.get('bootgen_config', {})
        if not bootgen_config:
            print("❌ No bootgen configuration found")
            return
        
        # Generate boot image
        success = manager.generate_boot_image(bootgen_config)
        
        if success:
            print(f"✅ Boot image generated: {bootgen_config.get('output_file', 'boot.bin')}")
        else:
            print("❌ Failed to generate boot image")
        
    except ImportError:
        print("❌ Xilinx tools manager not available")
    except Exception as e:
        print(f"❌ Error generating boot image: {e}")


def vivado_operations_menu():
    """Menu for Vivado operations."""
    while True:
        print("\n" + "-" * 40)
        print("VIVADO OPERATIONS")
        print("-" * 40)
        print("1. Generate Bitstream")
        print("2. Associate ELF File")
        print("3. Run TCL Script")
        print("4. Add Project")
        print("5. List Projects")
        print("6. Back to JTAG Menu")
        print()
        
        try:
            choice = input("Select an option (1-6): ").strip()
            
            if choice == '1':
                generate_vivado_bitstream()
            elif choice == '2':
                associate_elf_file()
            elif choice == '3':
                run_vivado_tcl_script()
            elif choice == '4':
                add_vivado_project()
            elif choice == '5':
                list_vivado_projects()
            elif choice == '6':
                break
            else:
                print("❌ Invalid choice. Please select 1-6.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def generate_vivado_bitstream():
    """Generate bitstream for Vivado project."""
    try:
        from libs.xilinx_tools_manager import XilinxToolsManager, load_xilinx_tools_config
        
        config_file = get_config_file()
        if not config_file:
            return
        
        # Load configuration
        config = load_xilinx_tools_config(config_file)
        manager = XilinxToolsManager(config)
        
        # Resolve tool paths
        manager.resolve_tool_paths()
        
        # Load project configuration
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        projects = config_data.get('vivado_projects', [])
        if not projects:
            print("❌ No Vivado projects configured")
            return
        
        # Show available projects
        print("Available projects:")
        for i, project in enumerate(projects):
            print(f"  {i+1}. {project['name']} - {project['project_path']}")
        
        choice = input("Select project (number): ").strip()
        try:
            project_index = int(choice) - 1
            if 0 <= project_index < len(projects):
                project = projects[project_index]
                project_name = project['name']
                
                # Add project to manager
                manager.add_vivado_project(
                    project_name,
                    project['project_path'],
                    project.get('target_cpu', 'ps7_cortexa9_0')
                )
                
        # Ask for custom TCL script
        custom_tcl = input("Enter custom TCL script path (or press Enter to use default/configured): ").strip()
        if not custom_tcl:
            custom_tcl = None
        
        # Ask for output directory
        output_dir = input("Enter output directory (or press Enter for default): ").strip()
        if not output_dir:
            output_dir = None
        
        # Generate bitstream
        print(f"Generating bitstream for project: {project_name}")
        bitstream_path = manager.generate_vivado_bitstream(project_name, output_dir, custom_tcl)
        
        if bitstream_path:
            print(f"✅ Bitstream generated: {bitstream_path}")
        else:
            print("❌ Failed to generate bitstream")
        
    except ImportError:
        print("❌ Xilinx tools manager not available")
    except Exception as e:
        print(f"❌ Error generating bitstream: {e}")


def run_vivado_tcl_script():
    """Run a TCL script for Vivado project."""
    try:
        from libs.xilinx_tools_manager import XilinxToolsManager, load_xilinx_tools_config
        
        # Load configuration
        config = load_xilinx_tools_config("config/xilinx_jtag_config.json")
        manager = XilinxToolsManager(config)
        
        # List available projects
        projects = manager.list_vivado_projects()
        if not projects:
            print("❌ No Vivado projects found")
            return
        
        print("Available Vivado Projects:")
        for i, project in enumerate(projects):
            print(f"  {i+1}. {project}")
        
        # Get project selection
        choice = input(f"Select project (1-{len(projects)}): ").strip()
        try:
            project_index = int(choice) - 1
            if 0 <= project_index < len(projects):
                project_name = projects[project_index]
            else:
                print("❌ Invalid project selection")
                return
        except ValueError:
            print("❌ Invalid input")
            return
        
        # Get TCL script options
        print("\nTCL Script Options:")
        print("1. Use configured script (bitstream_generation, programming, debug)")
        print("2. Specify custom TCL file path")
        print("3. Enter TCL commands directly")
        
        script_choice = input("Select option (1-3): ").strip()
        
        if script_choice == '1':
            # Use configured script
            print("Available script types:")
            print("1. bitstream_generation")
            print("2. programming") 
            print("3. debug")
            
            type_choice = input("Select script type (1-3): ").strip()
            script_types = ['bitstream_generation', 'programming', 'debug']
            
            try:
                type_index = int(type_choice) - 1
                if 0 <= type_index < len(script_types):
                    script_type = script_types[type_index]
                    tcl_path = f"configured_{script_type}"  # Placeholder for configured script
                else:
                    print("❌ Invalid script type")
                    return
            except ValueError:
                print("❌ Invalid input")
                return
                
        elif script_choice == '2':
            # Custom TCL file
            tcl_path = input("Enter TCL script file path: ").strip()
            if not tcl_path:
                print("❌ No TCL script path specified")
                return
            script_type = "custom"
            
        elif script_choice == '3':
            # Direct TCL commands
            print("Enter TCL commands (press Enter twice to finish):")
            tcl_commands = []
            while True:
                line = input()
                if line == "" and tcl_commands and tcl_commands[-1] == "":
                    break
                tcl_commands.append(line)
            
            # Remove empty lines
            tcl_commands = [cmd for cmd in tcl_commands if cmd.strip()]
            
            if not tcl_commands:
                print("❌ No TCL commands provided")
                return
            
            # Create temporary TCL file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False) as tcl_file:
                tcl_file.write('\n'.join(tcl_commands))
                tcl_path = tcl_file.name
            
            script_type = "custom"
            print(f"Created temporary TCL file: {tcl_path}")
            
        else:
            print("❌ Invalid choice")
            return
        
        # Get optional arguments
        args_input = input("Enter script arguments (space-separated, or press Enter for none): ").strip()
        args = args_input.split() if args_input else None
        
        # Run the TCL script
        print(f"Running TCL script for project: {project_name}")
        if script_choice == '1':
            success = manager.run_vivado_tcl_script(project_name, tcl_path, script_type, args)
        else:
            success = manager.run_vivado_tcl_script(project_name, tcl_path, "custom", args)
        
        if success:
            print("✅ TCL script executed successfully")
        else:
            print("❌ TCL script execution failed")
        
        # Cleanup temporary file if created
        if script_choice == '3' and 'tempfile' in locals():
            try:
                os.unlink(tcl_path)
            except:
                pass
        
    except ImportError:
        print("❌ Xilinx tools manager not available")
    except Exception as e:
        print(f"❌ Error running TCL script: {e}")


def associate_elf_file():
    """Associate ELF file with Vivado project."""
    try:
        from libs.xilinx_tools_manager import XilinxToolsManager, load_xilinx_tools_config
        
        config_file = get_config_file()
        if not config_file:
            return
        
        # Load configuration
        config = load_xilinx_tools_config(config_file)
        manager = XilinxToolsManager(config)
        
        # Resolve tool paths
        manager.resolve_tool_paths()
        
        # Load project configuration
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        projects = config_data.get('vivado_projects', [])
        if not projects:
            print("❌ No Vivado projects configured")
            return
        
        # Show available projects
        print("Available projects:")
        for i, project in enumerate(projects):
            print(f"  {i+1}. {project['name']} - {project['project_path']}")
        
        choice = input("Select project (number): ").strip()
        try:
            project_index = int(choice) - 1
            if 0 <= project_index < len(projects):
                project = projects[project_index]
                project_name = project['name']
                
                # Get ELF file path
                elf_path = input("Enter ELF file path: ").strip()
                if not elf_path:
                    print("❌ No ELF file path specified")
                    return
                
                # Add project to manager
                manager.add_vivado_project(
                    project_name,
                    project['project_path'],
                    project.get('target_cpu', 'ps7_cortexa9_0')
                )
                
                # Associate ELF file
                print(f"Associating ELF file with project: {project_name}")
                success = manager.associate_elf_with_project(project_name, elf_path)
                
                if success:
                    print("✅ ELF file associated successfully")
                else:
                    print("❌ Failed to associate ELF file")
            else:
                print("❌ Invalid project selection")
        except ValueError:
            print("❌ Invalid input")
        
    except ImportError:
        print("❌ Xilinx tools manager not available")
    except Exception as e:
        print(f"❌ Error associating ELF file: {e}")


def add_vivado_project():
    """Add a new Vivado project."""
    try:
        project_name = input("Enter project name: ").strip()
        if not project_name:
            print("❌ No project name specified")
            return
        
        project_path = input("Enter project path (.xpr file): ").strip()
        if not project_path:
            print("❌ No project path specified")
            return
        
        target_cpu = input("Enter target CPU (default: ps7_cortexa9_0): ").strip()
        if not target_cpu:
            target_cpu = "ps7_cortexa9_0"
        
        # Load existing configuration
        config_file = get_config_file()
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {}
        
        # Add project to configuration
        if 'vivado_projects' not in config_data:
            config_data['vivado_projects'] = []
        
        new_project = {
            'name': project_name,
            'project_path': project_path,
            'target_cpu': target_cpu
        }
        
        config_data['vivado_projects'].append(new_project)
        
        # Save configuration
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"✅ Project added: {project_name}")
        
    except Exception as e:
        print(f"❌ Error adding project: {e}")


def list_vivado_projects():
    """List configured Vivado projects."""
    try:
        config_file = get_config_file()
        if not config_file or not os.path.exists(config_file):
            print("❌ No configuration file found")
            return
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        projects = config_data.get('vivado_projects', [])
        if not projects:
            print("No Vivado projects configured")
            return
        
        print("Configured Vivado projects:")
        for i, project in enumerate(projects):
            print(f"  {i+1}. {project['name']}")
            print(f"     Path: {project['project_path']}")
            print(f"     Target CPU: {project.get('target_cpu', 'ps7_cortexa9_0')}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing projects: {e}")


def run_comprehensive_demo():
    """Run comprehensive Xilinx tools demo."""
    try:
        import subprocess
        import sys
        
        demo_script = "examples/xilinx_tools_comprehensive_demo.py"
        if not os.path.exists(demo_script):
            print(f"❌ Demo script not found: {demo_script}")
            return
        
        print("Comprehensive Xilinx Tools Demo")
        print("=" * 40)
        print("1. Run All Demos")
        print("2. Tool Path Resolution Demo")
        print("3. Bootgen Operations Demo")
        print("4. Vivado Operations Demo")
        print("5. JTAG Operations Demo")
        print("6. Configuration Management Demo")
        print("7. Back to JTAG Menu")
        print()
        
        choice = input("Select demo type (1-7): ").strip()
        
        if choice == '7':
            return
        
        # Ask for configuration file
        config_file = input("Enter configuration file path (or press Enter for default): ").strip()
        if not config_file:
            config_file = "config/xilinx_jtag_config.json"
        
        # Build command based on choice
        cmd = [sys.executable, demo_script]
        if config_file and os.path.exists(config_file):
            cmd.extend(["--config", config_file])
        
        demo_map = {
            '1': 'all',
            '2': 'paths',
            '3': 'bootgen',
            '4': 'vivado',
            '5': 'jtag',
            '6': 'config'
        }
        
        if choice in demo_map:
            if choice != '1':  # Not "all"
                cmd.extend(["--demo", demo_map[choice]])
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            print("✅ Demo completed successfully")
        else:
            print("❌ Demo failed")
        
    except Exception as e:
        print(f"❌ Error running comprehensive demo: {e}")


def run_integration_demo():
    """Run JTAG integration demo."""
    try:
        import subprocess
        import sys
        
        demo_script = "scripts/jtag_integration_demo.py"
        if not os.path.exists(demo_script):
            print(f"❌ Demo script not found: {demo_script}")
            return
        
        print("Running JTAG integration demo...")
        print("This will demonstrate JTAG integration with the test framework")
        print()
        
        # Ask for configuration file
        config_file = input("Enter configuration file path (or press Enter for default): ").strip()
        if not config_file:
            config_file = "config/xilinx_jtag_config.json"
        
        # Build command
        cmd = [sys.executable, demo_script]
        if config_file and os.path.exists(config_file):
            cmd.extend(["--config", config_file])
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            print("✅ Integration demo completed successfully")
        else:
            print("❌ Integration demo failed")
        
    except Exception as e:
        print(f"❌ Error running integration demo: {e}")


def generate_jtag_config():
    """Generate JTAG configuration."""
    try:
        from libs.xilinx_tools_manager import create_sample_xilinx_tools_config
        
        config = create_sample_xilinx_tools_config()
        filename = "config/xilinx_tools_config.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Xilinx tools configuration generated: {filename}")
        print("Edit this file with your specific tool paths and settings.")
        
    except ImportError:
        print("❌ Xilinx tools manager not available")
    except Exception as e:
        print(f"❌ Error generating configuration: {e}")


def run_interactive_test():
    """Run interactive test."""
    try:
        config_file = get_config_file()
        if not config_file:
            return
            
        print(f"Running interactive test with config: {config_file}")
        
        # Load configuration
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Create test runner
        runner = PowerCycleTestRunner()
        runner.config = config
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Run interactive test
        runner.run_interactive_test()
        
    except Exception as e:
        print(f"❌ Error running interactive test: {e}")


def run_automated_test():
    """Run automated test."""
    try:
        config_file = get_config_file()
        if not config_file:
            return
            
        print(f"Running automated test with config: {config_file}")
        
        # Load configuration
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Create test runner
        runner = PowerCycleTestRunner()
        runner.config = config
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize and run test
        if not runner.initialize_components():
            print("❌ Failed to initialize components")
            return
        
        try:
            # Attempt to run test
            results = runner.run_test()
            
            # Display test results
            if 'error' in results:
                print(f"❌ Test failed: {results['error']}")
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
        
    except Exception as e:
        print(f"❌ Error running automated test: {e}")


def validate_configuration():
    """Validate configuration file."""
    config_file = get_config_file()
    if config_file:
        success = validate_config(config_file)
        if success:
            print("✅ Configuration is valid!")
        else:
            print("❌ Configuration has errors.")
        input("\nPress Enter to continue...")


def get_config_file():
    """Get configuration file path from user."""
    default_config = "config/config.json"
    
    if Path(default_config).exists():
        use_default = input(f"Use default config ({default_config})? (y/n): ").strip().lower()
        if use_default in ['y', 'yes', '']:
            return default_config
    
    config_file = input("Enter configuration file path: ").strip()
    if not config_file:
        print("❌ No configuration file specified.")
        return None
    
    if not Path(config_file).exists():
        print(f"❌ Configuration file not found: {config_file}")
        return None
    
    return config_file


def show_command_line_help():
    """Show command line help."""
    print("\n" + "=" * 60)
    print("COMMAND LINE HELP")
    print("=" * 60)
    print()
    print("Usage: python main.py [options]")
    print()
    print("Options:")
    print("  -c, --config FILE        Configuration file path")
    print("  --interactive             Run in interactive mode")
    print("  --validate-config         Validate configuration file")
    print("  --list-patterns           List validation patterns")
    print("  --generate-config         Generate sample configuration")
    print("  --list-templates          List test templates")
    print("  --generate-templates      Generate sample templates")
    print("  --parse-logs              Parse existing log files")
    print("  --log-dir DIR             Log directory path")
    print("  --log-level LEVEL         Set logging level")
    print("  --cycles N                Override number of cycles")
    print("  --dry-run                 Perform dry run")
    print("  --output-dir DIR           Override output directory")
    print("  -h, --help                Show this help message")
    print()
    print("Examples:")
    print("  python main.py                           # Show menu")
    print("  python main.py --interactive            # Interactive mode")
    print("  python main.py -c config/my_config.json # Custom config")
    print("  python main.py --parse-logs             # Parse logs")
    print()
    input("Press Enter to continue...")


def show_project_structure():
    """Show project structure."""
    print("\n" + "=" * 60)
    print("PROJECT STRUCTURE")
    print("=" * 60)
    print()
    print("test_tool/")
    print("├── main.py                    # Main CLI entry point")
    print("├── requirements.txt           # Python dependencies")
    print("├── README.md                  # Project overview")
    print("├── stm32_log_capture_test.py   # STM32 test script")
    print("├── config/                    # Configuration files")
    print("│   ├── config.json           # Main configuration")
    print("│   ├── test_templates.json   # Test templates")
    print("│   ├── xilinx_jtag_config.json # Xilinx JTAG configuration")
    print("│   ├── bootgen_templates.json # Bootgen templates")
    print("│   ├── stm32_test_templates.json # STM32 templates")
    print("│   └── example_*.json        # Example configurations")
    print("├── libs/                     # Core framework modules")
    print("│   ├── test_runner.py       # Main test orchestrator")
    print("│   ├── power_supply.py      # Power supply control")
    print("│   ├── uart_handler.py      # UART communication")
    print("│   ├── pattern_validator.py # Pattern validation")
    print("│   ├── test_logger.py       # Test logging")
    print("│   ├── report_generator.py  # Report generation")
    print("│   ├── test_template_loader.py # Template system")
    print("│   ├── comprehensive_logger.py # Multi-file logging")
    print("│   ├── log_parser.py         # Log analysis")
    print("│   ├── serial_logger.py     # Serial logger with parsing")
    print("│   ├── xilinx_jtag.py       # Xilinx JTAG interface")
    print("│   ├── xilinx_bootgen.py    # Bootgen utility")
    print("│   ├── xilinx_tools_manager.py # Tools manager")
    print("│   └── jtag_test_runner.py  # JTAG test runner")
    print("├── examples/                 # Example scripts")
    print("│   ├── xilinx_jtag_demo.py  # JTAG functionality demos")
    print("│   └── xilinx_tools_comprehensive_demo.py # Comprehensive demo")
    print("├── docs/                     # Documentation")
    print("│   ├── xilinx_jtag_guide.md # JTAG guide")
    print("│   ├── xilinx_tools_comprehensive_guide.md # Comprehensive guide")
    print("│   └── stm32_log_capture_guide.md # STM32 guide")
    print("├── scripts/                  # Utility scripts")
    print("│   └── jtag_integration_demo.py # Integration demo")
    print("└── output/                   # Generated output")
    print("    ├── logs/                # Log files")
    print("    └── reports/             # Test reports")
    print()
    input("Press Enter to continue...")


def show_quick_start_guide():
    """Show quick start guide."""
    print("\n" + "=" * 60)
    print("QUICK START GUIDE")
    print("=" * 60)
    print()
    print("1. Generate Sample Files:")
    print("   python main.py --generate-config")
    print("   python main.py --generate-templates")
    print("   # Or use menu: 2. Configuration Management")
    print()
    print("2. Edit Configuration:")
    print("   - config/config.json - Hardware settings")
    print("   - config/test_templates.json - Test definitions")
    print("   - config/xilinx_jtag_config.json - Xilinx tools")
    print("   - config/stm32_test_templates.json - STM32 templates")
    print()
    print("3. Run Tests:")
    print("   python main.py --interactive")
    print("   # or just: python main.py")
    print()
    print("4. Xilinx Tools:")
    print("   - Menu: 4. JTAG Operations")
    print("   - Generate boot images, Vivado operations")
    print("   - JTAG device detection and programming")
    print()
    print("5. STM32 Operations:")
    print("   - Menu: 5. STM32 Operations")
    print("   - Run STM32 log capture tests")
    print("   - Generate STM32 configurations")
    print()
    print("6. Serial Logger:")
    print("   - Menu: 6. Serial Logger")
    print("   - Start serial data logging")
    print("   - Parse serial data with configurable patterns")
    print("   - Real-time or post-processing data analysis")
    print()
    print("7. Analyze Results:")
    print("   python main.py --parse-logs")
    print("   # or menu: 3. Log Analysis")
    print()
    print("8. View Examples:")
    print("   python examples/xilinx_tools_comprehensive_demo.py")
    print("   python examples/xilinx_jtag_demo.py")
    print("   python scripts/jtag_integration_demo.py")
    print()
    print("9. Read Documentation:")
    print("   - docs/xilinx_tools_comprehensive_guide.md")
    print("   - docs/xilinx_jtag_guide.md")
    print("   - docs/stm32_log_capture_guide.md")
    print()
    input("Press Enter to continue...")


def main():
    """
    Main entry point for the Automated Power Cycle and UART Validation Framework.
    
    This function serves as the primary entry point and handles both menu-based
    and command-line operation modes:
    
    Menu Mode (no arguments):
    - Displays interactive menu system
    - Provides guided workflow for users
    - Handles all functionality through menus
    
    CLI Mode (with arguments):
    - Processes command-line arguments
    - Executes specific functionality directly
    - Supports automation and scripting
    
    The function performs the following operations:
    1. Parse command-line arguments
    2. Determine operation mode (menu vs CLI)
    3. Execute appropriate functionality
    4. Handle errors and cleanup
    
    Command-line arguments support:
    - Configuration file management
    - Test execution (interactive/automated)
    - Template and pattern management
    - Log analysis and reporting
    - Output and logging control
    
    Error handling includes:
    - Configuration validation
    - File system errors
    - Hardware connection issues
    - User interruption (Ctrl+C)
    - Unexpected exceptions
    """
    # Parse command-line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Determine operation mode based on arguments
    # If no arguments provided, show interactive menu
    if len(sys.argv) == 1:
        # No arguments passed, show menu
        show_main_menu()
        return
    
    # Handle special command-line operations that exit immediately
    # These commands don't require full test execution
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
    
    # Validate configuration file exists and is valid
    if not Path(args.config).exists():
        print(f"❌ Configuration file not found: {args.config}")
        print("Use --generate-config to create a sample configuration file.")
        sys.exit(1)
    
    # Validate configuration file structure and content
    if not validate_config(args.config):
        sys.exit(1)
    
    try:
        # Load configuration file and apply command-line overrides
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Apply command-line argument overrides to configuration
        config = modify_config_for_args(config, args)
        
        # Initialize test runner with configuration
        runner = PowerCycleTestRunner()
        runner.config = config  # Override config
        
        # Configure logging system with specified level
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Execute tests based on mode (interactive vs automated)
        if args.interactive:
            # Interactive mode: User-guided test execution with prompts
            runner.run_interactive_test()
        else:
            # Automated mode: Direct test execution without user interaction
            print("Starting automated power cycle and UART validation test...")
            print(f"Configuration: {args.config}")
            print(f"Log Level: {args.log_level}")
            
            # Initialize hardware components and connections
            if not runner.initialize_components():
                print("❌ Failed to initialize components")
                sys.exit(1)
            
            try:
                # Execute the test suite and collect results
                results = runner.run_test()
                
                # Process and display test results
                if 'error' in results:
                    print(f"❌ Test failed: {results['error']}")
                    sys.exit(1)
                else:
                    print(f"✅ Test completed successfully!")
                    print(f"Success Rate: {results['success_rate']:.2%}")
                    print(f"Successful Cycles: {results['successful_cycles']}/{results['total_cycles']}")
                    
                    # Display generated report files
                    if results.get('report_files'):
                        print(f"\nReports generated:")
                        for format_type, filepath in results['report_files'].items():
                            print(f"  {format_type.upper()}: {filepath}")
            
            finally:
                # Ensure proper cleanup of hardware connections
                runner.cleanup_components()
    
    except KeyboardInterrupt:
        # Handle user interruption (Ctrl+C) gracefully
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        # Handle unexpected errors with detailed logging
        print(f"❌ Unexpected error: {e}")
        logging.exception("Unexpected error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
