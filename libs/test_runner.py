#!/usr/bin/env python3
"""
Power Cycle Test Runner

Main orchestrator for automated power cycling and UART validation tests.
This module serves as the central coordinator for the entire test framework,
managing hardware control, test execution, data collection, and reporting.

Key Responsibilities:
- Initialize and manage hardware components (power supply, UART)
- Execute test cycles with power cycling and UART validation
- Coordinate pattern validation and data collection
- Generate comprehensive test reports
- Handle template-based test configuration
- Provide comprehensive logging and error handling

Architecture:
- Uses factory pattern for power supply initialization
- Supports multiple UART loggers for concurrent data collection
- Implements template-based test configuration system
- Provides both interactive and automated execution modes
- Integrates comprehensive logging for debugging and analysis

Author: Automated Test Framework
Version: 1.0.0
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Core framework imports
from libs.power_supply import PowerSupplyFactory
from libs.uart_handler import UARTHandler, UARTDataLogger
from libs.pattern_validator import PatternValidator, ValidationResult
from libs.test_logger import TestLogger
from libs.report_generator import ReportGenerator
from libs.test_template_loader import TestTemplateLoader
from libs.comprehensive_logger import ComprehensiveLogger


class PowerCycleTestRunner:
    """
    Main test runner that orchestrates power cycling and UART validation.
    
    This class serves as the central coordinator for the entire test framework.
    It manages the complete test lifecycle from initialization through cleanup,
    coordinating all hardware components and data collection processes.
    
    Key Features:
    - Hardware abstraction and management
    - Template-based test configuration
    - Multi-threaded UART data collection
    - Comprehensive logging and error handling
    - Interactive and automated execution modes
    - Real-time test progress monitoring
    
    Architecture:
    - Uses factory pattern for power supply initialization
    - Supports multiple concurrent UART connections
    - Implements template resolution for test configuration
    - Provides comprehensive logging across all components
    - Handles graceful error recovery and cleanup
    
    Usage:
        runner = PowerCycleTestRunner()
        runner.config = config_dict
        runner.initialize_components()
        results = runner.run_test()
        runner.cleanup_components()
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the test runner with configuration.
        
        This constructor sets up the test runner with default configuration
        and initializes all internal state variables. The actual configuration
        loading and component initialization happens in separate methods to
        allow for flexible configuration management.
        
        Args:
            config_file (str): Path to configuration JSON file (optional)
            
        Attributes:
            config_file (str): Path to configuration file
            config (dict): Loaded configuration dictionary
            power_supply: Power supply control instance
            uart_handlers (list): List of UART handler instances
            uart_loggers (list): List of UART data logger instances
            pattern_validator: Pattern validation instance
            test_logger: Test data logging instance
            report_generator: Report generation instance
            template_loader: Test template management instance
            comprehensive_logger: Multi-file logging instance
            is_running (bool): Test execution state flag
            current_cycle (int): Current test cycle number
            current_test_index (int): Current test index in test list
            test_results (list): Collected test results
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.power_supply = None
        self.uart_handler = None
        self.uart_logger = None
        self.pattern_validator = None
        self.test_logger = None
        self.report_generator = None
        self.template_loader = None
        self.comprehensive_logger = None
        
        # Test state
        self.is_running = False
        self.current_cycle = 0
        self.current_test_index = 0
        self.test_results = []
        
    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('output', {})
        log_level = log_config.get('log_level', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f"test_runner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            ]
        )
    
    def initialize_components(self) -> bool:
        """
        Initialize all test components.
        
        :return: True if all components initialized successfully
        """
        try:
            self.logger.info("Initializing test components...")
            
            # Initialize power supply
            ps_config = self.config.get('power_supply', {})
            if ps_config:
                self.power_supply = PowerSupplyFactory.create_power_supply(ps_config)
                self.logger.info("Power supply initialized")
                if self.comprehensive_logger:
                    self.comprehensive_logger.log_power_supply_operation("Initialize", str(ps_config))
            
            # Initialize UART handlers for all configured loggers
            uart_loggers_config = self.config.get('uart_loggers', [])
            self.uart_handlers = []
            self.uart_loggers = []
            
            for i, uart_config in enumerate(uart_loggers_config):
                # Convert new config format to old format
                old_format_config = {
                    'port': uart_config['port'],
                    'baud_rate': uart_config['baud'],
                    'data_bits': 8,
                    'parity': 'N',
                    'stop_bits': 1,
                    'timeout': 1.0,
                    'buffer_size': 1024
                }
                
                uart_handler = UARTHandler(old_format_config)
                if not uart_handler.connect():
                    self.logger.error(f"Failed to connect to UART {uart_config['port']}")
                    return False
                
                self.uart_handlers.append(uart_handler)
                
                # Initialize UART data logger
                log_dir = self.config.get('output', {}).get('log_directory', 'logs')
                uart_log_file = Path(log_dir) / f"uart_data_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                uart_logger = UARTDataLogger(uart_handler, str(uart_log_file))
                self.uart_loggers.append(uart_logger)
            
            # For backward compatibility, set primary handlers
            if self.uart_handlers:
                self.uart_handler = self.uart_handlers[0]
                self.uart_logger = self.uart_loggers[0]
            
            # Initialize template loader first to get output config
            self.template_loader = TestTemplateLoader()
            
            # Merge template output config with main config
            if self.template_loader and hasattr(self.template_loader, 'templates'):
                template_output = self.template_loader.templates.get('output', {})
                if template_output:
                    if 'output' not in self.config:
                        self.config['output'] = {}
                    self.config['output'].update(template_output)
            
            # Ensure output directories exist
            output_config = self.config.get('output', {})
            log_dir = output_config.get('log_directory', './output/logs')
            report_dir = output_config.get('report_directory', './output/reports')
            log_level = output_config.get('log_level', 'INFO')
            
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            Path(report_dir).mkdir(parents=True, exist_ok=True)
            
            # Initialize comprehensive logger
            self.comprehensive_logger = ComprehensiveLogger(log_dir, log_level)
            self.comprehensive_logger.log_system_info()
            self.comprehensive_logger.log_configuration(self.config)
            
            # Initialize test logger
            self.test_logger = TestLogger(self.config)
            
            # Initialize report generator
            self.report_generator = ReportGenerator(self.config, self.logger)
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def cleanup_components(self):
        """Cleanup all test components."""
        try:
            self.logger.info("Cleaning up components...")
            
            # Cleanup all UART handlers
            for uart_handler in getattr(self, 'uart_handlers', []):
                uart_handler.disconnect()
            
            if self.power_supply:
                self.power_supply.close()
            
            if self.test_logger:
                self.test_logger.end_test()
            
            self.logger.info("Components cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_current_test_config(self) -> Dict:
        """Get the current test configuration with template resolution."""
        tests = self.config.get('tests', [])
        if self.current_test_index < len(tests):
            test_config = tests[self.current_test_index]
            
            # Resolve template if template loader is available
            if self.template_loader:
                try:
                    return self.template_loader.resolve_test_config(test_config)
                except Exception as e:
                    self.logger.error(f"Error resolving test template: {e}")
                    return test_config
            
            return test_config
        return {}
    
    def power_cycle_device(self, cycle_number: int) -> bool:
        """
        Perform a complete power cycle on the device.
        
        :param cycle_number: Current cycle number for logging
        :return: True if power cycle completed successfully
        """
        try:
            # Get current test configuration
            current_test = self.get_current_test_config()
            power_on_duration = current_test.get('on_time', 5.0)
            power_off_duration = current_test.get('off_time', 3.0)
            
            self.logger.info(f"Starting power cycle {cycle_number}")
            self.test_logger.log_event(f"Power cycle {cycle_number} started", cycle_number)
            
            # Turn power off
            self.power_supply.output_off()
            self.test_logger.log_event("Power turned OFF", cycle_number)
            time.sleep(power_off_duration)
            
            # Turn power on
            self.power_supply.output_on()
            self.test_logger.log_event("Power turned ON", cycle_number)
            time.sleep(power_on_duration)
            
            self.logger.info(f"Power cycle {cycle_number} completed")
            self.test_logger.log_event(f"Power cycle {cycle_number} completed", cycle_number)
            return True
            
        except Exception as e:
            self.logger.error(f"Power cycle {cycle_number} failed: {e}")
            self.test_logger.log_error(f"Power cycle failed: {e}", cycle_number, e)
            return False
    
    def validate_patterns(self, cycle_number: int) -> List[ValidationResult]:
        """
        Validate UART patterns for the current cycle.
        
        :param cycle_number: Current cycle number
        :return: List of validation results
        """
        current_test = self.get_current_test_config()
        uart_patterns = current_test.get('uart_patterns', [])
        results = []
        
        try:
            self.logger.info(f"Starting pattern validation for cycle {cycle_number}")
            
            for i, pattern_config in enumerate(uart_patterns):
                pattern_name = f"pattern_{i}"
                regex_pattern = pattern_config.get('regex', '')
                expected_values = pattern_config.get('expected', [])
                timeout = 10.0  # Default timeout
                
                self.logger.info(f"Waiting for pattern: {pattern_name}")
                
                # Convert new format to old format for validation
                old_format_pattern = {
                    'name': pattern_name,
                    'pattern': regex_pattern,
                    'pattern_type': 'regex',
                    'timeout': timeout,
                    'required': True,
                    'expected': expected_values
                }
                
                # Wait for pattern in UART stream
                result = self.pattern_validator.wait_for_pattern_in_stream(
                    self.uart_handler, old_format_pattern, timeout
                )
                
                if result:
                    # Check if the extracted values match expected values
                    if expected_values and result.extracted_values:
                        extracted_groups = result.extracted_values.get('groups', [])
                        if extracted_groups:
                            # Compare extracted values with expected
                            match_found = False
                            for expected_set in expected_values:
                                if isinstance(expected_set, list):
                                    if len(extracted_groups) >= len(expected_set):
                                        if all(str(extracted_groups[j]) == str(expected_set[j]) for j in range(len(expected_set))):
                                            match_found = True
                                            break
                                else:
                                    if str(extracted_groups[0]) == str(expected_set):
                                        match_found = True
                                        break
                            
                            if not match_found:
                                result.success = False
                                result.error_message = f"Extracted values {extracted_groups} do not match expected {expected_values}"
                    
                    results.append(result)
                    self.test_logger.log_validation_result(result, cycle_number)
                    
                    if result.success:
                        self.logger.info(f"Pattern '{pattern_name}' validated successfully")
                    else:
                        self.logger.warning(f"Pattern '{pattern_name}' validation failed")
                else:
                    # Create timeout result
                    timeout_result = ValidationResult(
                        pattern_name=pattern_name,
                        success=False,
                        timeout_reached=True,
                        error_message=f"Pattern '{pattern_name}' not found within {timeout} seconds"
                    )
                    results.append(timeout_result)
                    self.test_logger.log_validation_result(timeout_result, cycle_number)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Pattern validation failed for cycle {cycle_number}: {e}")
            self.test_logger.log_error(f"Pattern validation failed: {e}", cycle_number, e)
            return results
    
    def run_single_cycle(self, cycle_number: int) -> Dict:
        """
        Run a single test cycle.
        
        :param cycle_number: Cycle number to run
        :return: Cycle result dictionary
        """
        cycle_start_time = datetime.now()
        cycle_result = {
            'cycle_number': cycle_number,
            'start_time': cycle_start_time,
            'power_cycle_success': False,
            'validation_results': [],
            'success': False,
            'errors': []
        }
        
        try:
            self.logger.info(f"Starting test cycle {cycle_number}")
            self.test_logger.start_cycle(cycle_number)
            self.uart_logger.set_cycle_number(cycle_number)
            
            # Perform power cycle
            power_success = self.power_cycle_device(cycle_number)
            cycle_result['power_cycle_success'] = power_success
            
            if not power_success:
                cycle_result['errors'].append("Power cycle failed")
                return cycle_result
            
            # Start UART logging
            if not self.uart_handler.start_logging():
                cycle_result['errors'].append("Failed to start UART logging")
                return cycle_result
            
            # Wait for device to stabilize
            current_test = self.get_current_test_config()
            cycle_delay = current_test.get('cycle_delay', 2.0)
            time.sleep(cycle_delay)
            
            # Validate patterns
            validation_results = self.validate_patterns(cycle_number)
            cycle_result['validation_results'] = validation_results
            
            # Stop UART logging
            self.uart_handler.stop_logging()
            
            # Determine cycle success
            current_test = self.get_current_test_config()
            uart_patterns = current_test.get('uart_patterns', [])
            
            # All patterns are required by default in new format
            required_success = all(r.success for r in validation_results) if validation_results else True
            
            cycle_result['success'] = power_success and required_success
            
            if not cycle_result['success']:
                failed_patterns = [r.pattern_name for r in validation_results if not r.success]
                cycle_result['errors'].append(f"Required patterns failed: {failed_patterns}")
            
            cycle_end_time = datetime.now()
            cycle_result['end_time'] = cycle_end_time
            cycle_result['duration'] = cycle_end_time - cycle_start_time
            
            self.test_logger.end_cycle(cycle_number, cycle_result['success'])
            
            self.logger.info(f"Cycle {cycle_number} completed: {'PASS' if cycle_result['success'] else 'FAIL'}")
            return cycle_result
            
        except Exception as e:
            self.logger.error(f"Cycle {cycle_number} failed with exception: {e}")
            cycle_result['errors'].append(str(e))
            cycle_result['end_time'] = datetime.now()
            cycle_result['duration'] = cycle_result['end_time'] - cycle_start_time
            
            self.test_logger.log_error(f"Cycle failed: {e}", cycle_number, e)
            self.test_logger.end_cycle(cycle_number, False)
            
            return cycle_result
    
    def run_test(self) -> Dict:
        """
        Run the complete test suite.
        
        :return: Test results dictionary
        """
        if self.is_running:
            self.logger.warning("Test is already running")
            return {}
        
        self.is_running = True
        test_start_time = datetime.now()
        
        try:
            self.logger.info("Starting automated power cycle and UART validation test")
            self.test_logger.start_test()
            
            # Get test configuration
            tests = self.config.get('tests', [])
            if not tests:
                self.logger.error("No tests configured")
                return {'error': 'No tests configured'}
            
            self.logger.info(f"Running {len(tests)} test(s)")
            
            # Resolve all test configurations
            resolved_tests = []
            for test_config in tests:
                try:
                    if self.template_loader:
                        resolved_config = self.template_loader.resolve_test_config(test_config)
                        resolved_tests.append(resolved_config)
                    else:
                        resolved_tests.append(test_config)
                except Exception as e:
                    self.logger.error(f"Error resolving test template: {e}")
                    resolved_tests.append(test_config)
            
            self.logger.info(f"Running {len(resolved_tests)} test(s)")
            
            # Run each test
            for test_index, test_config in enumerate(resolved_tests):
                self.current_test_index = test_index
                test_name = test_config.get('name', f'Test_{test_index}')
                total_cycles = test_config.get('cycles', 1)
                
                self.logger.info(f"Running test: {test_name} ({total_cycles} cycles)")
                
                # Run test cycles
                for cycle_num in range(1, total_cycles + 1):
                    self.current_cycle = cycle_num
                    
                    self.logger.info(f"Running cycle {cycle_num}/{total_cycles}")
                    cycle_result = self.run_single_cycle(cycle_num)
                    cycle_result['test_name'] = test_name
                    cycle_result['test_index'] = test_index
                    self.test_results.append(cycle_result)
                    
                    # Log cycle result
                    status = "PASSED" if cycle_result['success'] else "FAILED"
                    self.logger.info(f"Cycle {cycle_num} {status}")
                    
                    # Add delay between cycles if specified
                    if cycle_num < total_cycles:
                        cycle_delay = test_config.get('cycle_delay', 2.0)
                        if cycle_delay > 0:
                            time.sleep(cycle_delay)
            
            # Generate test summary
            test_end_time = datetime.now()
            test_duration = test_end_time - test_start_time
            
            successful_cycles = sum(1 for r in self.test_results if r['success'])
            failed_cycles = len(self.test_results) - successful_cycles
            
            test_summary = {
                'test_name': 'Multi-Test Suite',
                'session_timestamp': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                'test_start_time': test_start_time.isoformat(),
                'test_end_time': test_end_time.isoformat(),
                'test_duration': str(test_duration),
                'total_tests': len(tests),
                'total_cycles': len(self.test_results),
                'successful_cycles': successful_cycles,
                'failed_cycles': failed_cycles,
                'success_rate': successful_cycles / len(self.test_results) if self.test_results else 0,
                'total_uart_data_points': sum(len(logger.get_log_data()) for logger in self.uart_loggers),
                'total_validations': sum(len(r['validation_results']) for r in self.test_results),
                'total_errors': sum(len(r['errors']) for r in self.test_results),
                'cycle_details': self.test_results,
                'tests_run': [{'name': t.get('name'), 'cycles': t.get('cycles', 1)} for t in tests]
            }
            
            self.logger.info(f"Test completed. Success rate: {test_summary['success_rate']:.2%}")
            
            # Generate reports for each test
            self.logger.info("Generating test reports...")
            all_report_files = {}
            
            # Group results by test
            test_results_by_test = {}
            for result in self.test_results:
                test_name = result.get('test_name', 'Unknown')
                if test_name not in test_results_by_test:
                    test_results_by_test[test_name] = []
                test_results_by_test[test_name].append(result)
            
            # Generate reports for each test
            for test_name, test_cycle_results in test_results_by_test.items():
                # Find the resolved test configuration to get output format
                test_config = None
                for test in resolved_tests:
                    if test.get('name') == test_name:
                        test_config = test
                        break
                
                output_format = test_config.get('output_format', 'json') if test_config else 'json'
                
                # Create test-specific summary
                test_summary_specific = test_summary.copy()
                test_summary_specific['test_name'] = test_name
                test_summary_specific['total_cycles'] = len(test_cycle_results)
                test_summary_specific['successful_cycles'] = sum(1 for r in test_cycle_results if r['success'])
                test_summary_specific['failed_cycles'] = len(test_cycle_results) - test_summary_specific['successful_cycles']
                test_summary_specific['success_rate'] = test_summary_specific['successful_cycles'] / len(test_cycle_results) if test_cycle_results else 0
                test_summary_specific['cycle_details'] = test_cycle_results
                
                # Generate reports based on output format
                if output_format.lower() == 'json':
                    report_files = self.report_generator.generate_json_report(
                        test_summary_specific, 
                        test_cycle_results,
                        [logger.get_log_data() for logger in self.uart_loggers]
                    )
                    if report_files:
                        all_report_files[f"{test_name}_json"] = report_files
                elif output_format.lower() == 'csv':
                    report_files = self.report_generator.generate_csv_report(
                        test_summary_specific, 
                        test_cycle_results,
                        [logger.get_log_data() for logger in self.uart_loggers]
                    )
                    if report_files:
                        all_report_files[f"{test_name}_csv"] = report_files
                elif output_format.lower() == 'text':
                    report_files = self.report_generator.generate_text_report(
                        test_summary_specific, 
                        test_cycle_results,
                        [logger.get_log_data() for logger in self.uart_loggers]
                    )
                    if report_files:
                        all_report_files[f"{test_name}_text"] = report_files
                elif output_format.lower() == 'html':
                    report_files = self.report_generator.generate_html_report(
                        test_summary_specific, 
                        test_cycle_results,
                        [logger.get_log_data() for logger in self.uart_loggers]
                    )
                    if report_files:
                        all_report_files[f"{test_name}_html"] = report_files
                else:
                    # Default to comprehensive report
                    report_files = self.report_generator.generate_comprehensive_report(
                        test_summary_specific, 
                        test_cycle_results,
                        [logger.get_log_data() for logger in self.uart_loggers]
                    )
                    if report_files:
                        all_report_files[f"{test_name}_comprehensive"] = report_files
            
            # Also generate overall comprehensive report
            comprehensive_report_files = self.report_generator.generate_comprehensive_report(
                test_summary, 
                self.test_results,
                [logger.get_log_data() for logger in self.uart_loggers]
            )
            if comprehensive_report_files:
                all_report_files['overall_comprehensive'] = comprehensive_report_files
            
            report_files = all_report_files
            
            test_summary['report_files'] = report_files
            
            return test_summary
            
        except Exception as e:
            self.logger.error(f"Test failed with exception: {e}")
            return {'error': str(e)}
        
        finally:
            self.is_running = False
            self.test_logger.end_test()
    
    def run_interactive_test(self):
        """Run test in interactive mode with user prompts."""
        print("=" * 60)
        print("Automated Power Cycle and UART Validation Framework")
        print("=" * 60)
        
        if not self.initialize_components():
            print("Failed to initialize components. Exiting.")
            return
        
        try:
            # Display configuration
            tests = self.config.get('tests', [])
            print(f"\nTest Configuration:")
            print(f"  Number of Tests: {len(tests)}")
            
            # Resolve test configurations for display
            resolved_tests = []
            for test_config in tests:
                try:
                    if self.template_loader:
                        resolved_config = self.template_loader.resolve_test_config(test_config)
                        resolved_tests.append(resolved_config)
                    else:
                        resolved_tests.append(test_config)
                except Exception as e:
                    print(f"  Warning: Error resolving test template: {e}")
                    resolved_tests.append(test_config)
            
            for i, test in enumerate(resolved_tests):
                print(f"\nTest {i+1}: {test.get('name', 'N/A')}")
                print(f"  Description: {test.get('description', 'N/A')}")
                print(f"  Cycles: {test.get('cycles', 1)}")
                print(f"  Power On Duration: {test.get('on_time', 5.0)}s")
                print(f"  Power Off Duration: {test.get('off_time', 3.0)}s")
                print(f"  Output Format: {test.get('output_format', 'default')}")
                
                # Display UART patterns
                patterns = test.get('uart_patterns', [])
                print(f"  UART Patterns ({len(patterns)}):")
                for j, pattern in enumerate(patterns):
                    print(f"    - Pattern {j+1}: {pattern.get('regex', 'N/A')}")
                    if pattern.get('expected'):
                        print(f"      Expected: {pattern.get('expected')}")
            
            # Display UART loggers
            uart_loggers = self.config.get('uart_loggers', [])
            print(f"\nUART Loggers ({len(uart_loggers)}):")
            for logger in uart_loggers:
                print(f"  - Port: {logger.get('port', 'N/A')}, Baud: {logger.get('baud', 'N/A')}")
            
            # Display available templates if template loader is available
            if self.template_loader:
                available_templates = self.template_loader.get_available_templates()
                print(f"\nAvailable Test Templates ({len(available_templates)}):")
                for template in available_templates:
                    print(f"  - {template}")
            
            # Confirm test start
            response = input(f"\nStart test? (y/n): ").lower().strip()
            if response != 'y':
                print("Test cancelled by user.")
                return
            
            # Run test
            print("\nStarting test...")
            results = self.run_test()
            
            if 'error' in results:
                print(f"\nTest failed: {results['error']}")
            else:
                print(f"\nTest completed successfully!")
                print(f"Success Rate: {results['success_rate']:.2%}")
                print(f"Successful Cycles: {results['successful_cycles']}/{results['total_cycles']}")
                
                if results.get('report_files'):
                    print(f"\nReports generated:")
                    for format_type, filepath in results['report_files'].items():
                        print(f"  {format_type.upper()}: {filepath}")
        
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
        except Exception as e:
            print(f"\nTest failed: {e}")
        finally:
            self.cleanup_components()


# Example usage
if __name__ == "__main__":
    # Create and run test
    runner = PowerCycleTestRunner("config.json")
    runner.run_interactive_test()
