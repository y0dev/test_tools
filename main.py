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
from pathlib import Path
from datetime import datetime

from lib.test_runner import PowerCycleTestRunner
from lib.report_generator import ReportGenerator


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
        print("4. Help & Documentation")
        print("5. Exit")
        print()
        
        try:
            choice = input("Select an option (1-5): ").strip()
            
            if choice == '1':
                run_tests_menu()
            elif choice == '2':
                configuration_menu()
            elif choice == '3':
                log_analysis_menu()
            elif choice == '4':
                help_menu()
            elif choice == '5':
                print("Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
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
            results = runner.run_test()
            
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
    print("├── config/                    # Configuration files")
    print("│   ├── config.json           # Main configuration")
    print("│   ├── test_templates.json   # Test templates")
    print("│   └── example_*.json        # Example configurations")
    print("├── lib/                      # Core framework modules")
    print("│   ├── test_runner.py       # Main test orchestrator")
    print("│   ├── power_supply.py      # Power supply control")
    print("│   ├── uart_handler.py      # UART communication")
    print("│   ├── pattern_validator.py # Pattern validation")
    print("│   ├── test_logger.py       # Test logging")
    print("│   ├── report_generator.py  # Report generation")
    print("│   ├── test_template_loader.py # Template system")
    print("│   ├── comprehensive_logger.py # Multi-file logging")
    print("│   └── log_parser.py         # Log analysis")
    print("├── examples/                 # Example scripts")
    print("├── docs/                     # Documentation")
    print("├── scripts/                  # Utility scripts")
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
    print()
    print("2. Edit Configuration:")
    print("   - config/config.json - Hardware settings")
    print("   - config/test_templates.json - Test definitions")
    print()
    print("3. Run Tests:")
    print("   python main.py --interactive")
    print("   # or just: python main.py")
    print()
    print("4. Analyze Results:")
    print("   python main.py --parse-logs")
    print()
    print("5. View Examples:")
    print("   python examples/template_demo.py")
    print("   python examples/log_parsing_demo.py")
    print()
    print("6. Read Documentation:")
    print("   - docs/README.md - Detailed documentation")
    print("   - docs/configuration_guide.md - Configuration guide")
    print("   - docs/usage_guide.md - Usage instructions")
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
