#!/usr/bin/env python3
"""
STM32 Log Capture Test Script

This script is specifically designed to capture and analyze logs from the STM32 Nucleo-F070RB
project located at F:\Programming\STM32\Workspace\nucleo-f070rb\Core\Src.

The STM32 project outputs numeric data via UART2 (115200 baud) in the format: "5\r\n"
This script captures that output and validates it using the test framework.

Features:
- Captures UART output from STM32 DEV_SAMPLE_FUNCTION
- Validates numeric patterns in the output
- Generates comprehensive reports (JSON, CSV, HTML, text)
- Supports power cycling tests
- Real-time log display
- Multiple test configurations

Usage:
    python stm32_log_capture_test.py
    python stm32_log_capture_test.py --port COM4
    python stm32_log_capture_test.py --interactive
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the libs directory to the path
sys.path.append(str(Path(__file__).parent / "libs"))

from libs.test_runner import PowerCycleTestRunner
from libs.report_generator import ReportGenerator


def setup_logging():
    """Setup logging configuration for STM32 test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"stm32_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )
    return logging.getLogger(__name__)


def create_stm32_test_config(port="COM3", cycles=5, test_type="numeric"):
    """
    Create STM32-specific test configuration.
    
    Args:
        port (str): COM port for UART connection
        cycles (int): Number of test cycles
        test_type (str): Type of test ('numeric', 'continuous', 'power_cycle')
    
    Returns:
        dict: Test configuration
    """
    base_config = {
        "power_supply": {
            "resource": "GPIB0::5::INSTR",
            "voltage": 3.3,
            "current_limit": 0.5
        },
        "uart_loggers": [
            {
                "port": port,
                "baud": 115200,
                "display": True
            }
        ],
        "output": {
            "log_directory": "./output/logs",
            "report_directory": "./output/reports",
            "detailed_logs": True,
            "timestamp_format": "%Y-%m-%d_%H-%M-%S",
            "log_level": "INFO"
        }
    }
    
    if test_type == "numeric":
        base_config["tests"] = [
            {
                "name": "STM32_Numeric_Output_Test",
                "description": "Capture and validate numeric output from STM32 DEV_SAMPLE_FUNCTION",
                "cycles": cycles,
                "on_time": 10,
                "off_time": 3,
                "cycle_delay": 2,
                "output_format": "json",
                "uart_patterns": [
                    {
                        "regex": "^(\\d+)\\r\\n$",
                        "expected": ["5"],
                        "description": "Capture numeric output from DEV_SAMPLE_FUNCTION"
                    }
                ]
            }
        ]
    elif test_type == "continuous":
        base_config["tests"] = [
            {
                "name": "STM32_Continuous_Logging_Test",
                "description": "Continuous logging test to capture all STM32 output",
                "cycles": 1,
                "on_time": 30,
                "off_time": 5,
                "output_format": "csv",
                "uart_patterns": [
                    {
                        "regex": ".*",
                        "expected": [],
                        "description": "Capture all output for analysis"
                    }
                ]
            }
        ]
    elif test_type == "power_cycle":
        base_config["tests"] = [
            {
                "name": "STM32_Power_Cycle_Test",
                "description": "Test STM32 behavior during power cycles",
                "cycles": cycles,
                "on_time": 8,
                "off_time": 4,
                "output_format": "html",
                "uart_patterns": [
                    {
                        "regex": "^(\\d+)\\r\\n$",
                        "expected": ["5"],
                        "description": "Verify numeric output after power cycle"
                    }
                ]
            }
        ]
    
    return base_config


def run_stm32_test(config, interactive=False):
    """
    Run STM32 log capture test.
    
    Args:
        config (dict): Test configuration
        interactive (bool): Run in interactive mode
    """
    logger = logging.getLogger(__name__)
    
    print("=" * 70)
    print("STM32 LOG CAPTURE TEST")
    print("=" * 70)
    print(f"STM32 Project: F:\\Programming\\STM32\\Workspace\\nucleo-f070rb\\Core\\Src")
    print(f"UART Port: {config['uart_loggers'][0]['port']}")
    print(f"Baud Rate: {config['uart_loggers'][0]['baud']}")
    print(f"Test Cycles: {sum(test.get('cycles', 1) for test in config['tests'])}")
    print("=" * 70)
    
    # Create test runner
    runner = PowerCycleTestRunner()
    runner.config = config
    
    try:
        # Initialize components
        if not runner.initialize_components():
            logger.error("Failed to initialize test components")
            print("❌ Failed to initialize components. Check your COM port and power supply connections.")
            return False
        
        if interactive:
            # Run interactive test
            runner.run_interactive_test()
        else:
            # Run automated test
            print("Starting automated STM32 log capture test...")
            results = runner.run_test()
            
            if 'error' in results:
                print(f"❌ Test failed: {results['error']}")
                return False
            else:
                print(f"✅ Test completed successfully!")
                print(f"Success Rate: {results['success_rate']:.2%}")
                print(f"Successful Cycles: {results['successful_cycles']}/{results['total_cycles']}")
                
                if results.get('report_files'):
                    print(f"\nReports generated:")
                    for format_type, filepath in results['report_files'].items():
                        print(f"  {format_type.upper()}: {filepath}")
                
                return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        print(f"❌ Test failed: {e}")
        return False
    finally:
        runner.cleanup_components()


def main():
    """Main entry point for STM32 log capture test."""
    parser = argparse.ArgumentParser(
        description="STM32 Log Capture Test Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stm32_log_capture_test.py                    # Run with default settings
  python stm32_log_capture_test.py --port COM4       # Use specific COM port
  python stm32_log_capture_test.py --interactive     # Interactive mode
  python stm32_log_capture_test.py --cycles 10       # Run 10 cycles
  python stm32_log_capture_test.py --test-type continuous  # Continuous logging test
        """
    )
    
    parser.add_argument(
        '--port',
        default='COM3',
        help='COM port for UART connection (default: COM3)'
    )
    
    parser.add_argument(
        '--cycles',
        type=int,
        default=5,
        help='Number of test cycles (default: 5)'
    )
    
    parser.add_argument(
        '--test-type',
        choices=['numeric', 'continuous', 'power_cycle'],
        default='numeric',
        help='Type of test to run (default: numeric)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--config-file',
        help='Use custom configuration file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run without actual hardware control'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    try:
        if args.config_file:
            # Load custom configuration
            with open(args.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded custom configuration from {args.config_file}")
        else:
            # Create STM32-specific configuration
            config = create_stm32_test_config(
                port=args.port,
                cycles=args.cycles,
                test_type=args.test_type
            )
            logger.info(f"Created STM32 test configuration for {args.test_type} test")
        
        # Save configuration for reference
        config_file = f"stm32_test_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_file}")
        
        # Run the test
        success = run_stm32_test(config, interactive=args.interactive)
        
        if success:
            print(f"\n✅ STM32 log capture test completed successfully!")
            print(f"Check the output directory for detailed logs and reports.")
        else:
            print(f"\n❌ STM32 log capture test failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

