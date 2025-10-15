#!/usr/bin/env python3
"""
JTAG Test Runner

This module extends the existing test framework to support JTAG operations
for Xilinx devices. It integrates JTAG functionality with the power cycle
and UART validation framework, enabling comprehensive hardware testing.

Key Features:
- JTAG device detection and management
- Integration with power cycling tests
- JTAG operations during test cycles
- Comprehensive logging of JTAG operations
- Support for bitstream programming and debugging

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
from libs.test_runner import PowerCycleTestRunner
from libs.xilinx_jtag import (
    XilinxJTAGInterface, 
    JTAGConfig, 
    JTAGInterface, 
    DeviceState,
    load_jtag_config,
    XilinxJTAGError
)


class JTAGTestRunner(PowerCycleTestRunner):
    """
    Extended test runner that includes JTAG functionality.
    
    This class extends the PowerCycleTestRunner to include JTAG operations
    for Xilinx devices. It provides comprehensive testing capabilities that
    combine power cycling, UART validation, and JTAG operations.
    
    Key Features:
    - JTAG device detection and management
    - Integration with power cycling tests
    - JTAG operations during test cycles
    - Comprehensive logging of JTAG operations
    - Support for bitstream programming and debugging
    
    Usage:
        runner = JTAGTestRunner()
        runner.config = config_dict
        runner.initialize_components()
        results = runner.run_jtag_test()
        runner.cleanup_components()
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the JTAG test runner.
        
        Args:
            config_file: Path to configuration JSON file
        """
        super().__init__(config_file)
        
        # JTAG-specific components
        self.jtag_interface = None
        self.jtag_config = None
        self.jtag_devices = []
        
        # JTAG test state
        self.jtag_enabled = False
        self.jtag_operations = []
        self.jtag_results = []
    
    def _load_jtag_config(self) -> Optional[JTAGConfig]:
        """
        Load JTAG configuration from the main config.
        
        Returns:
            JTAGConfig object or None if not configured
        """
        try:
            jtag_config_data = self.config.get('jtag', {})
            if not jtag_config_data:
                self.logger.info("No JTAG configuration found")
                return None
            
            # Create JTAG config from dictionary
            jtag_config = JTAGConfig()
            
            if 'interface' in jtag_config_data:
                try:
                    jtag_config.interface = JTAGInterface(jtag_config_data['interface'])
                except ValueError:
                    jtag_config.interface = JTAGInterface.ANXSCT
            
            if 'executable_path' in jtag_config_data:
                jtag_config.executable_path = jtag_config_data['executable_path']
            
            if 'connection_timeout' in jtag_config_data:
                jtag_config.connection_timeout = int(jtag_config_data['connection_timeout'])
            
            if 'command_timeout' in jtag_config_data:
                jtag_config.command_timeout = int(jtag_config_data['command_timeout'])
            
            if 'auto_connect' in jtag_config_data:
                jtag_config.auto_connect = bool(jtag_config_data['auto_connect'])
            
            if 'verbose_logging' in jtag_config_data:
                jtag_config.verbose_logging = bool(jtag_config_data['verbose_logging'])
            
            self.logger.info("JTAG configuration loaded successfully")
            return jtag_config
            
        except Exception as e:
            self.logger.error(f"Error loading JTAG configuration: {e}")
            return None
    
    def initialize_jtag_components(self) -> bool:
        """
        Initialize JTAG components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load JTAG configuration
            self.jtag_config = self._load_jtag_config()
            if not self.jtag_config:
                self.logger.info("JTAG not configured - skipping JTAG initialization")
                return True
            
            # Initialize JTAG interface
            self.jtag_interface = XilinxJTAGInterface(self.jtag_config)
            
            # Connect to JTAG console
            if not self.jtag_interface.connect():
                self.logger.error("Failed to connect to JTAG console")
                return False
            
            # Scan for devices
            self.jtag_devices = self.jtag_interface.scan_devices()
            if not self.jtag_devices:
                self.logger.warning("No JTAG devices found")
                return True  # Not a fatal error
            
            self.jtag_enabled = True
            self.logger.info(f"JTAG initialized successfully - found {len(self.jtag_devices)} device(s)")
            
            # Log device information
            for device in self.jtag_devices:
                self.logger.info(f"JTAG Device {device.index}: {device.name} (ID: {device.idcode})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing JTAG components: {e}")
            return False
    
    def cleanup_jtag_components(self):
        """Cleanup JTAG components."""
        try:
            if self.jtag_interface:
                self.jtag_interface.disconnect()
                self.jtag_interface = None
                self.logger.info("JTAG components cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up JTAG components: {e}")
    
    def initialize_components(self) -> bool:
        """
        Initialize all components including JTAG.
        
        Returns:
            True if all components initialized successfully
        """
        # Initialize base components
        if not super().initialize_components():
            return False
        
        # Initialize JTAG components
        if not self.initialize_jtag_components():
            return False
        
        return True
    
    def cleanup_components(self):
        """Cleanup all components including JTAG."""
        super().cleanup_components()
        self.cleanup_jtag_components()
    
    def execute_jtag_operations(self, cycle: int) -> Dict[str, Any]:
        """
        Execute JTAG operations for a test cycle.
        
        Args:
            cycle: Current test cycle number
            
        Returns:
            Dictionary containing JTAG operation results
        """
        if not self.jtag_enabled or not self.jtag_interface:
            return {'jtag_enabled': False}
        
        jtag_results = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'operations': [],
            'success': True,
            'errors': []
        }
        
        try:
            # Get JTAG operations from config
            jtag_ops = self.config.get('jtag_operations', [])
            
            for operation in jtag_ops:
                op_result = self._execute_jtag_operation(operation, cycle)
                jtag_results['operations'].append(op_result)
                
                if not op_result.get('success', True):
                    jtag_results['success'] = False
                    jtag_results['errors'].append(op_result.get('error', 'Unknown error'))
            
            # Store results
            self.jtag_results.append(jtag_results)
            
        except Exception as e:
            self.logger.error(f"Error executing JTAG operations: {e}")
            jtag_results['success'] = False
            jtag_results['errors'].append(str(e))
        
        return jtag_results
    
    def _execute_jtag_operation(self, operation: Dict[str, Any], cycle: int) -> Dict[str, Any]:
        """
        Execute a single JTAG operation.
        
        Args:
            operation: Operation configuration
            cycle: Current test cycle
            
        Returns:
            Operation result dictionary
        """
        op_type = operation.get('type', 'unknown')
        device_index = operation.get('device_index', 0)
        
        result = {
            'type': op_type,
            'device_index': device_index,
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': None
        }
        
        try:
            if op_type == 'reset':
                success = self.jtag_interface.reset_device(device_index)
                result['success'] = success
                if not success:
                    result['error'] = 'Device reset failed'
            
            elif op_type == 'program':
                bitstream_path = operation.get('bitstream_path')
                if bitstream_path:
                    success = self.jtag_interface.program_device(device_index, bitstream_path)
                    result['success'] = success
                    if not success:
                        result['error'] = 'Device programming failed'
                else:
                    result['error'] = 'No bitstream path specified'
            
            elif op_type == 'read_memory':
                address = operation.get('address', 0x40000000)
                size = operation.get('size', 4)
                data = self.jtag_interface.read_memory(device_index, address, size)
                result['success'] = data is not None
                result['data'] = data.hex() if data else None
                if not result['success']:
                    result['error'] = 'Memory read failed'
            
            elif op_type == 'write_memory':
                address = operation.get('address', 0x40000000)
                data_hex = operation.get('data', '12345678')
                data = bytes.fromhex(data_hex)
                success = self.jtag_interface.write_memory(device_index, address, data)
                result['success'] = success
                if not success:
                    result['error'] = 'Memory write failed'
            
            elif op_type == 'get_status':
                status = self.jtag_interface.get_device_status(device_index)
                result['success'] = status is not None
                result['status'] = status.value if status else 'Unknown'
                if not result['success']:
                    result['error'] = 'Status read failed'
            
            else:
                result['error'] = f'Unknown operation type: {op_type}'
            
            self.logger.debug(f"JTAG operation '{op_type}' completed: {result['success']}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error executing JTAG operation '{op_type}': {e}")
        
        return result
    
    def run_jtag_test(self) -> Dict[str, Any]:
        """
        Run a comprehensive test including JTAG operations.
        
        Returns:
            Test results dictionary
        """
        if not self.jtag_enabled:
            self.logger.warning("JTAG not enabled - running standard test")
            return self.run_test()
        
        self.logger.info("Starting JTAG-enabled test")
        
        # Initialize components if not already done
        if not self.power_supply or not self.uart_handler:
            if not self.initialize_components():
                return {'error': 'Failed to initialize components'}
        
        try:
            # Get test configuration
            tests = self.config.get('tests', [])
            if not tests:
                return {'error': 'No tests configured'}
            
            # Run tests
            all_results = []
            
            for test_index, test_config in enumerate(tests):
                self.current_test_index = test_index
                test_name = test_config.get('name', f'Test {test_index}')
                
                self.logger.info(f"Running test: {test_name}")
                
                # Run test cycles
                cycles = test_config.get('cycles', 1)
                test_results = []
                
                for cycle in range(cycles):
                    self.current_cycle = cycle + 1
                    
                    self.logger.info(f"Starting cycle {self.current_cycle}/{cycles}")
                    
                    # Execute JTAG operations before power cycle
                    jtag_results = self.execute_jtag_operations(cycle)
                    
                    # Run power cycle test
                    cycle_result = self._run_single_cycle(test_config, cycle)
                    
                    # Add JTAG results to cycle result
                    cycle_result['jtag'] = jtag_results
                    
                    test_results.append(cycle_result)
                    
                    # Wait between cycles
                    if cycle < cycles - 1:
                        wait_time = test_config.get('off_time', 3)
                        self.logger.info(f"Waiting {wait_time} seconds before next cycle")
                        time.sleep(wait_time)
                
                # Store test results
                test_summary = {
                    'test_name': test_name,
                    'test_index': test_index,
                    'cycles': cycles,
                    'results': test_results,
                    'success_rate': sum(1 for r in test_results if r.get('success', False)) / len(test_results)
                }
                
                all_results.append(test_summary)
            
            # Generate reports
            report_files = self._generate_reports(all_results)
            
            # Calculate overall success rate
            total_cycles = sum(len(test['results']) for test in all_results)
            successful_cycles = sum(
                sum(1 for r in test['results'] if r.get('success', False))
                for test in all_results
            )
            
            overall_success_rate = successful_cycles / total_cycles if total_cycles > 0 else 0
            
            return {
                'success_rate': overall_success_rate,
                'successful_cycles': successful_cycles,
                'total_cycles': total_cycles,
                'test_results': all_results,
                'jtag_results': self.jtag_results,
                'report_files': report_files
            }
            
        except Exception as e:
            self.logger.error(f"Error running JTAG test: {e}")
            return {'error': str(e)}
    
    def _generate_reports(self, test_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate comprehensive reports including JTAG data.
        
        Args:
            test_results: Test results data
            
        Returns:
            Dictionary of report file paths
        """
        try:
            # Create output directory
            output_dir = Path(self.config.get('output', {}).get('report_directory', './output/reports'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_files = {}
            
            # Generate JSON report
            json_file = output_dir / f'jtag_test_report_{timestamp}.json'
            with open(json_file, 'w') as f:
                json.dump({
                    'test_results': test_results,
                    'jtag_results': self.jtag_results,
                    'timestamp': timestamp,
                    'config': self.config
                }, f, indent=2)
            report_files['json'] = str(json_file)
            
            # Generate CSV report
            csv_file = output_dir / f'jtag_test_report_{timestamp}.csv'
            self._generate_csv_report(csv_file, test_results)
            report_files['csv'] = str(csv_file)
            
            # Generate HTML report
            html_file = output_dir / f'jtag_test_report_{timestamp}.html'
            self._generate_html_report(html_file, test_results)
            report_files['html'] = str(html_file)
            
            self.logger.info(f"Reports generated: {list(report_files.values())}")
            return report_files
            
        except Exception as e:
            self.logger.error(f"Error generating reports: {e}")
            return {}
    
    def _generate_csv_report(self, csv_file: Path, test_results: List[Dict[str, Any]]):
        """Generate CSV report with JTAG data."""
        import csv
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Test Name', 'Cycle', 'Success', 'Power Cycle Success', 
                'UART Success', 'JTAG Success', 'JTAG Operations', 'Errors'
            ])
            
            # Write data
            for test in test_results:
                for cycle_result in test['results']:
                    jtag_data = cycle_result.get('jtag', {})
                    jtag_ops = len(jtag_data.get('operations', []))
                    jtag_success = jtag_data.get('success', False)
                    
                    writer.writerow([
                        test['test_name'],
                        cycle_result.get('cycle', 0),
                        cycle_result.get('success', False),
                        cycle_result.get('power_cycle_success', False),
                        cycle_result.get('uart_success', False),
                        jtag_success,
                        jtag_ops,
                        '; '.join(jtag_data.get('errors', []))
                    ])
    
    def _generate_html_report(self, html_file: Path, test_results: List[Dict[str, Any]]):
        """Generate HTML report with JTAG data."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>JTAG Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .test-section {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .cycle-result {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .jtag-info {{ background-color: #e8f4fd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>JTAG Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        for test in test_results:
            html_content += f"""
    <div class="test-section">
        <h2>{test['test_name']}</h2>
        <p>Success Rate: {test['success_rate']:.2%}</p>
        <p>Total Cycles: {test['cycles']}</p>
"""
            
            for cycle_result in test['results']:
                success_class = "success" if cycle_result.get('success', False) else "failure"
                jtag_data = cycle_result.get('jtag', {})
                
                html_content += f"""
        <div class="cycle-result">
            <h3>Cycle {cycle_result.get('cycle', 0)}</h3>
            <p class="{success_class}">Overall Success: {cycle_result.get('success', False)}</p>
            <p>Power Cycle: {cycle_result.get('power_cycle_success', False)}</p>
            <p>UART Validation: {cycle_result.get('uart_success', False)}</p>
            
            <div class="jtag-info">
                <h4>JTAG Operations</h4>
                <p>JTAG Success: {jtag_data.get('success', False)}</p>
                <p>Operations Count: {len(jtag_data.get('operations', []))}</p>
"""
                
                if jtag_data.get('errors'):
                    html_content += f"<p>Errors: {'; '.join(jtag_data['errors'])}</p>"
                
                html_content += "</div></div>"
            
            html_content += "</div>"
        
        html_content += """
</body>
</html>
"""
        
        with open(html_file, 'w') as f:
            f.write(html_content)


def create_jtag_test_config() -> Dict[str, Any]:
    """
    Create a sample JTAG test configuration.
    
    Returns:
        Sample configuration dictionary
    """
    return {
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
        "jtag": {
            "interface": "anxsct",
            "executable_path": None,
            "connection_timeout": 30,
            "command_timeout": 10,
            "auto_connect": True,
            "verbose_logging": True
        },
        "jtag_operations": [
            {
                "type": "reset",
                "device_index": 0,
                "description": "Reset device before power cycle"
            },
            {
                "type": "get_status",
                "device_index": 0,
                "description": "Check device status"
            }
        ],
        "tests": [
            {
                "name": "JTAG Power Cycle Test",
                "description": "Test with JTAG operations during power cycling",
                "cycles": 3,
                "on_time": 5,
                "off_time": 3,
                "uart_patterns": [
                    {
                        "regex": "READY",
                        "expected": ["READY"]
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


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample configuration
    config = create_jtag_test_config()
    
    # Save configuration
    with open('config/jtag_test_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Sample JTAG test configuration created: config/jtag_test_config.json")
