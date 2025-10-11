# Test Creation and Framework Extension Guide

## Overview

This guide explains how to create new tests and extend the Automated Power Cycle and UART Validation Framework to support new test types and output formats. The framework is designed to be modular and extensible, allowing developers to add custom functionality while maintaining consistency with the existing architecture.

## Table of Contents

1. [Understanding the Framework Architecture](#understanding-the-framework-architecture)
2. [Creating New Test Templates](#creating-new-test-templates)
3. [Adding Custom Test Types](#adding-custom-test-types)
4. [Implementing New Output Formats](#implementing-new-output-formats)
5. [Extending Hardware Support](#extending-hardware-support)
6. [Adding Custom Validation Patterns](#adding-custom-validation-patterns)
7. [Testing and Validation](#testing-and-validation)
8. [Best Practices](#best-practices)

## Understanding the Framework Architecture

### Core Components

The framework follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   main.py      │    │  test_runner.py │    │ power_supply.py │
│   (CLI/Menu)   │───▶│  (Orchestrator) │───▶│  (Hardware)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ template_loader │    │  uart_handler   │    │ pattern_validator│
│  (Templates)    │    │  (Data Logging) │    │  (Validation)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ report_generator│    │ comprehensive_  │    │   test_logger   │
│  (Output)       │    │    logger       │    │  (Data Storage) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Configuration Loading** → Template resolution → Test definition
2. **Hardware Initialization** → Power supply + UART connections
3. **Test Execution** → Power cycling + UART data collection
4. **Pattern Validation** → Data analysis + result generation
5. **Report Generation** → Multiple output formats

## Creating New Test Templates

### Step 1: Define Test Template

Add a new test template to `config/test_templates.json`:

```json
{
  "test_templates": {
    "my_custom_test": {
      "description": "Custom test for specific hardware validation",
      "uart_patterns": [
        {
          "regex": "CustomPattern:\\s*(\\w+)",
          "expected": ["SUCCESS", "OK", "READY"]
        },
        {
          "regex": "Data:\\s*(\\d+),\\s*(\\d+)",
          "expected": [["123", "456"]]
        }
      ],
      "output_format": "json",
      "custom_settings": {
        "timeout": 10,
        "retry_count": 3,
        "special_validation": true
      }
    }
  }
}
```

### Step 2: Use Template in Configuration

Reference the template in `config/config.json`:

```json
{
  "tests": [
    {
      "name": "my_custom_test",
      "cycles": 5,
      "on_time": 3,
      "off_time": 2
    }
  ]
}
```

### Step 3: Template Resolution Process

The framework automatically resolves templates using this process:

1. **Load defaults** from `test_templates.json`
2. **Apply template** settings
3. **Apply test overrides** from config
4. **Validate** final configuration

## Adding Custom Test Types

### Step 1: Create Custom Test Handler

Create a new file `lib/custom_test_handler.py`:

```python
#!/usr/bin/env python3
"""
Custom Test Handler

Handles specialized test types that require custom logic beyond
standard power cycling and UART validation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime


class CustomTestHandler:
    """
    Custom test handler for specialized test scenarios.
    
    This class provides a framework for implementing custom test logic
    that extends beyond standard power cycling and UART validation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize custom test handler.
        
        Args:
            config (dict): Test configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.results = []
    
    def execute_custom_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute custom test logic.
        
        Args:
            test_config (dict): Test-specific configuration
            
        Returns:
            dict: Test execution results
        """
        test_name = test_config.get('name', 'Custom Test')
        self.logger.info(f"Starting custom test: {test_name}")
        
        # Custom test logic here
        start_time = datetime.now()
        
        try:
            # Example: Custom hardware interaction
            result = self._perform_custom_operation(test_config)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'test_name': test_name,
                'status': 'PASS' if result['success'] else 'FAIL',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration,
                'custom_data': result['data'],
                'message': result['message']
            }
            
        except Exception as e:
            self.logger.error(f"Custom test failed: {e}")
            return {
                'test_name': test_name,
                'status': 'FAIL',
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _perform_custom_operation(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform custom test operation.
        
        Args:
            test_config (dict): Test configuration
            
        Returns:
            dict: Operation results
        """
        # Implement your custom test logic here
        # This is where you would add:
        # - Custom hardware interactions
        # - Specialized data processing
        # - Custom validation logic
        # - External system integration
        
        return {
            'success': True,
            'data': {'custom_value': 123},
            'message': 'Custom operation completed successfully'
        }
```

### Step 2: Integrate with Test Runner

Modify `lib/test_runner.py` to support custom test types:

```python
# Add import
from lib.custom_test_handler import CustomTestHandler

# Add to PowerCycleTestRunner class
def run_custom_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute custom test type.
    
    Args:
        test_config (dict): Test configuration
        
    Returns:
        dict: Test execution results
    """
    try:
        # Initialize custom test handler
        custom_handler = CustomTestHandler(self.config)
        
        # Execute custom test
        result = custom_handler.execute_custom_test(test_config)
        
        # Log results
        self.logger.info(f"Custom test completed: {result['status']}")
        
        return result
        
    except Exception as e:
        self.logger.error(f"Custom test execution failed: {e}")
        return {
            'test_name': test_config.get('name', 'Custom Test'),
            'status': 'FAIL',
            'error': str(e)
        }

# Modify the main test execution logic
def run_single_cycle(self, cycle_number: int) -> Dict[str, Any]:
    """Execute a single test cycle with support for custom test types."""
    current_test = self.get_current_test_config()
    test_type = current_test.get('test_type', 'standard')
    
    if test_type == 'custom':
        # Execute custom test
        return self.run_custom_test(current_test)
    else:
        # Execute standard power cycle test
        return self._run_standard_cycle(cycle_number, current_test)
```

### Step 3: Update Template System

Extend the template system to support custom test types:

```json
{
  "test_templates": {
    "custom_hardware_test": {
      "description": "Custom hardware validation test",
      "test_type": "custom",
      "custom_settings": {
        "hardware_type": "special_device",
        "validation_method": "custom_algorithm",
        "timeout": 30
      },
      "output_format": "json"
    }
  }
}
```

## Implementing New Output Formats

### Step 1: Create Custom Report Generator

Create a new file `lib/custom_report_generator.py`:

```python
#!/usr/bin/env python3
"""
Custom Report Generator

Generates reports in custom formats beyond the standard JSON, CSV, HTML, and text.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class CustomReportGenerator:
    """
    Custom report generator for specialized output formats.
    
    This class provides a framework for implementing custom report formats
    that extend beyond the standard output options.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize custom report generator.
        
        Args:
            config (dict): Configuration dictionary
            logger (logging.Logger): Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.output_config = config.get('output', {})
        self.report_directory = Path(self.output_config.get('report_directory', './output/reports'))
        self.report_directory.mkdir(parents=True, exist_ok=True)
    
    def generate_xml_report(self, test_summary: Dict[str, Any], 
                          cycle_data: List[Dict[str, Any]] = None,
                          uart_data: List[Dict[str, Any]] = None) -> str:
        """
        Generate XML format report.
        
        Args:
            test_summary (dict): Test summary data
            cycle_data (list): Cycle execution data
            uart_data (list): UART data collected
            
        Returns:
            str: Path to generated XML file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"test_results_{timestamp}.xml"
        filepath = self.report_directory / filename
        
        # Generate XML content
        xml_content = self._create_xml_content(test_summary, cycle_data, uart_data)
        
        # Write XML file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        self.logger.info(f"XML report generated: {filepath}")
        return str(filepath)
    
    def generate_yaml_report(self, test_summary: Dict[str, Any], 
                            cycle_data: List[Dict[str, Any]] = None,
                            uart_data: List[Dict[str, Any]] = None) -> str:
        """
        Generate YAML format report.
        
        Args:
            test_summary (dict): Test summary data
            cycle_data (list): Cycle execution data
            uart_data (list): UART data collected
            
        Returns:
            str: Path to generated YAML file
        """
        import yaml
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"test_results_{timestamp}.yaml"
        filepath = self.report_directory / filename
        
        # Prepare data for YAML
        yaml_data = {
            'test_summary': test_summary,
            'cycle_data': cycle_data or [],
            'uart_data': uart_data or [],
            'generated_at': datetime.now().isoformat(),
            'framework_version': '1.0.0'
        }
        
        # Write YAML file
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"YAML report generated: {filepath}")
        return str(filepath)
    
    def generate_excel_report(self, test_summary: Dict[str, Any], 
                             cycle_data: List[Dict[str, Any]] = None,
                             uart_data: List[Dict[str, Any]] = None) -> str:
        """
        Generate Excel format report.
        
        Args:
            test_summary (dict): Test summary data
            cycle_data (list): Cycle execution data
            uart_data (list): UART data collected
            
        Returns:
            str: Path to generated Excel file
        """
        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            self.logger.error("Required packages not installed: pandas, openpyxl")
            raise ImportError("Install pandas and openpyxl for Excel support")
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"test_results_{timestamp}.xlsx"
        filepath = self.report_directory / filename
        
        # Create Excel workbook
        wb = Workbook()
        
        # Summary sheet
        ws_summary = wb.active
        ws_summary.title = "Test Summary"
        self._create_summary_sheet(ws_summary, test_summary)
        
        # Cycle data sheet
        if cycle_data:
            ws_cycles = wb.create_sheet("Cycle Data")
            self._create_cycle_sheet(ws_cycles, cycle_data)
        
        # UART data sheet
        if uart_data:
            ws_uart = wb.create_sheet("UART Data")
            self._create_uart_sheet(ws_uart, uart_data)
        
        # Save workbook
        wb.save(filepath)
        
        self.logger.info(f"Excel report generated: {filepath}")
        return str(filepath)
    
    def _create_xml_content(self, test_summary: Dict[str, Any], 
                           cycle_data: List[Dict[str, Any]], 
                           uart_data: List[Dict[str, Any]]) -> str:
        """Create XML content for report."""
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<test_results>',
            f'  <generated_at>{datetime.now().isoformat()}</generated_at>',
            f'  <framework_version>1.0.0</framework_version>',
            '  <test_summary>',
            f'    <total_cycles>{test_summary.get("total_cycles", 0)}</total_cycles>',
            f'    <successful_cycles>{test_summary.get("successful_cycles", 0)}</successful_cycles>',
            f'    <failed_cycles>{test_summary.get("failed_cycles", 0)}</failed_cycles>',
            f'    <success_rate>{test_summary.get("success_rate", 0):.2%}</success_rate>',
            '  </test_summary>',
            '  <cycle_data>'
        ]
        
        # Add cycle data
        for cycle in cycle_data or []:
            xml_lines.extend([
                '    <cycle>',
                f'      <cycle_number>{cycle.get("cycle_number", 0)}</cycle_number>',
                f'      <status>{cycle.get("status", "UNKNOWN")}</status>',
                f'      <start_time>{cycle.get("start_time", "")}</start_time>',
                f'      <end_time>{cycle.get("end_time", "")}</end_time>',
                '    </cycle>'
            ])
        
        xml_lines.extend(['  </cycle_data>', '</test_results>'])
        return '\n'.join(xml_lines)
    
    def _create_summary_sheet(self, ws, test_summary: Dict[str, Any]):
        """Create summary sheet in Excel workbook."""
        # Add headers
        ws['A1'] = 'Test Summary'
        ws['A1'].font = Font(bold=True, size=14)
        
        # Add data
        row = 3
        for key, value in test_summary.items():
            ws[f'A{row}'] = key.replace('_', ' ').title()
            ws[f'B{row}'] = value
            row += 1
    
    def _create_cycle_sheet(self, ws, cycle_data: List[Dict[str, Any]]):
        """Create cycle data sheet in Excel workbook."""
        if not cycle_data:
            return
        
        # Add headers
        headers = list(cycle_data[0].keys())
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header.replace('_', ' ').title()
            cell.font = Font(bold=True)
        
        # Add data
        for row, cycle in enumerate(cycle_data, 2):
            for col, header in enumerate(headers, 1):
                ws.cell(row=row, column=col).value = cycle.get(header, '')
    
    def _create_uart_sheet(self, ws, uart_data: List[Dict[str, Any]]):
        """Create UART data sheet in Excel workbook."""
        if not uart_data:
            return
        
        # Add headers
        headers = list(uart_data[0].keys())
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header.replace('_', ' ').title()
            cell.font = Font(bold=True)
        
        # Add data
        for row, data in enumerate(uart_data, 2):
            for col, header in enumerate(headers, 1):
                ws.cell(row=row, column=col).value = data.get(header, '')
```

### Step 2: Integrate with Report Generator

Modify `lib/report_generator.py` to support custom formats:

```python
# Add import
from lib.custom_report_generator import CustomReportGenerator

# Add to ReportGenerator class
def generate_custom_report(self, test_summary: Dict[str, Any], 
                          cycle_data: List[Dict[str, Any]] = None,
                          uart_data: List[Dict[str, Any]] = None,
                          format_type: str = 'xml') -> str:
    """
    Generate report in custom format.
    
    Args:
        test_summary (dict): Test summary data
        cycle_data (list): Cycle execution data
        uart_data (list): UART data collected
        format_type (str): Custom format type (xml, yaml, excel)
        
    Returns:
        str: Path to generated report file
    """
    custom_generator = CustomReportGenerator(self.config, self.logger)
    
    if format_type == 'xml':
        return custom_generator.generate_xml_report(test_summary, cycle_data, uart_data)
    elif format_type == 'yaml':
        return custom_generator.generate_yaml_report(test_summary, cycle_data, uart_data)
    elif format_type == 'excel':
        return custom_generator.generate_excel_report(test_summary, cycle_data, uart_data)
    else:
        raise ValueError(f"Unsupported custom format: {format_type}")

# Update the main report generation method
def generate_comprehensive_report(self, test_summary: Dict[str, Any], 
                                cycle_data: List[Dict[str, Any]] = None,
                                uart_data: List[Dict[str, Any]] = None,
                                validation_results: List[Dict[str, Any]] = None) -> Dict[str, str]:
    """Generate comprehensive reports in multiple formats."""
    report_files = {}
    
    # Standard formats
    report_files['json'] = self.generate_json_report(test_summary, cycle_data, uart_data)
    report_files['csv'] = self.generate_csv_report(test_summary, cycle_data, uart_data)
    report_files['html'] = self.generate_html_report(test_summary, cycle_data, uart_data)
    report_files['text'] = self.generate_text_report(test_summary, cycle_data, uart_data)
    
    # Custom formats
    try:
        report_files['xml'] = self.generate_custom_report(test_summary, cycle_data, uart_data, 'xml')
        report_files['yaml'] = self.generate_custom_report(test_summary, cycle_data, uart_data, 'yaml')
        report_files['excel'] = self.generate_custom_report(test_summary, cycle_data, uart_data, 'excel')
    except ImportError as e:
        self.logger.warning(f"Custom format not available: {e}")
    
    return report_files
```

### Step 3: Update Template System

Add support for custom output formats in templates:

```json
{
  "test_templates": {
    "excel_report_test": {
      "description": "Test with Excel report output",
      "uart_patterns": [
        {
          "regex": "READY",
          "expected": ["READY"]
        }
      ],
      "output_format": "excel"
    },
    "xml_report_test": {
      "description": "Test with XML report output",
      "uart_patterns": [
        {
          "regex": "Data:\\s*(\\w+)",
          "expected": ["SUCCESS"]
        }
      ],
      "output_format": "xml"
    }
  }
}
```

## Extending Hardware Support

### Step 1: Create New Power Supply Class

Create a new file `lib/custom_power_supply.py`:

```python
#!/usr/bin/env python3
"""
Custom Power Supply Implementation

Example implementation for extending power supply support to new hardware.
"""

import logging
from typing import Dict, Any, Optional
from lib.power_supply import PowerSupplyBase


class CustomPowerSupply(PowerSupplyBase):
    """
    Custom power supply implementation for specialized hardware.
    
    This class demonstrates how to extend the framework to support
    new power supply hardware beyond the standard Keysight E3632A.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize custom power supply.
        
        Args:
            config (dict): Power supply configuration
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.connection_type = config.get('connection_type', 'custom')
        self.device_id = config.get('device_id', 'default')
        
        # Custom hardware-specific settings
        self.custom_settings = config.get('custom_settings', {})
    
    def connect(self) -> bool:
        """
        Establish connection to custom power supply.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Implement custom connection logic
            self.logger.info(f"Connecting to custom power supply: {self.device_id}")
            
            # Example: Custom hardware initialization
            self._initialize_custom_hardware()
            
            self.connected = True
            self.logger.info("Custom power supply connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to custom power supply: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from custom power supply.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            if self.connected:
                # Implement custom disconnection logic
                self.logger.info("Disconnecting from custom power supply")
                
                # Example: Custom hardware cleanup
                self._cleanup_custom_hardware()
                
                self.connected = False
                self.logger.info("Custom power supply disconnected")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect from custom power supply: {e}")
            return False
    
    def set_voltage(self, voltage: float) -> bool:
        """
        Set output voltage on custom power supply.
        
        Args:
            voltage (float): Voltage value to set
            
        Returns:
            bool: True if voltage set successfully, False otherwise
        """
        try:
            if not self.connected:
                self.logger.error("Power supply not connected")
                return False
            
            # Implement custom voltage setting logic
            self.logger.info(f"Setting voltage to {voltage}V")
            
            # Example: Custom hardware command
            success = self._send_custom_command(f"VOLT {voltage}")
            
            if success:
                self.voltage = voltage
                self.logger.info(f"Voltage set to {voltage}V successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set voltage: {e}")
            return False
    
    def set_current_limit(self, current: float) -> bool:
        """
        Set current limit on custom power supply.
        
        Args:
            current (float): Current limit value to set
            
        Returns:
            bool: True if current limit set successfully, False otherwise
        """
        try:
            if not self.connected:
                self.logger.error("Power supply not connected")
                return False
            
            # Implement custom current limit setting logic
            self.logger.info(f"Setting current limit to {current}A")
            
            # Example: Custom hardware command
            success = self._send_custom_command(f"CURR {current}")
            
            if success:
                self.current_limit = current
                self.logger.info(f"Current limit set to {current}A successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set current limit: {e}")
            return False
    
    def enable_output(self) -> bool:
        """
        Enable output on custom power supply.
        
        Returns:
            bool: True if output enabled successfully, False otherwise
        """
        try:
            if not self.connected:
                self.logger.error("Power supply not connected")
                return False
            
            # Implement custom output enable logic
            self.logger.info("Enabling power supply output")
            
            # Example: Custom hardware command
            success = self._send_custom_command("OUTP ON")
            
            if success:
                self.output_enabled = True
                self.logger.info("Power supply output enabled")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to enable output: {e}")
            return False
    
    def disable_output(self) -> bool:
        """
        Disable output on custom power supply.
        
        Returns:
            bool: True if output disabled successfully, False otherwise
        """
        try:
            if not self.connected:
                self.logger.error("Power supply not connected")
                return False
            
            # Implement custom output disable logic
            self.logger.info("Disabling power supply output")
            
            # Example: Custom hardware command
            success = self._send_custom_command("OUTP OFF")
            
            if success:
                self.output_enabled = False
                self.logger.info("Power supply output disabled")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to disable output: {e}")
            return False
    
    def measure_voltage(self) -> Optional[float]:
        """
        Measure actual output voltage from custom power supply.
        
        Returns:
            float: Measured voltage value, None if measurement failed
        """
        try:
            if not self.connected:
                self.logger.error("Power supply not connected")
                return None
            
            # Implement custom voltage measurement logic
            voltage = self._read_custom_voltage()
            
            if voltage is not None:
                self.logger.debug(f"Measured voltage: {voltage}V")
            
            return voltage
            
        except Exception as e:
            self.logger.error(f"Failed to measure voltage: {e}")
            return None
    
    def measure_current(self) -> Optional[float]:
        """
        Measure actual output current from custom power supply.
        
        Returns:
            float: Measured current value, None if measurement failed
        """
        try:
            if not self.connected:
                self.logger.error("Power supply not connected")
                return None
            
            # Implement custom current measurement logic
            current = self._read_custom_current()
            
            if current is not None:
                self.logger.debug(f"Measured current: {current}A")
            
            return current
            
        except Exception as e:
            self.logger.error(f"Failed to measure current: {e}")
            return None
    
    def _initialize_custom_hardware(self):
        """Initialize custom hardware-specific settings."""
        # Implement custom hardware initialization
        # This could include:
        # - Device-specific configuration
        # - Communication protocol setup
        # - Calibration procedures
        # - Error checking
        pass
    
    def _cleanup_custom_hardware(self):
        """Cleanup custom hardware-specific resources."""
        # Implement custom hardware cleanup
        # This could include:
        # - Closing communication channels
        # - Resetting device state
        # - Releasing resources
        pass
    
    def _send_custom_command(self, command: str) -> bool:
        """
        Send custom command to hardware.
        
        Args:
            command (str): Command to send
            
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        # Implement custom command sending logic
        # This could include:
        # - Serial communication
        # - Network protocols
        # - Custom APIs
        # - Error handling
        return True
    
    def _read_custom_voltage(self) -> Optional[float]:
        """
        Read voltage from custom hardware.
        
        Returns:
            float: Voltage value, None if read failed
        """
        # Implement custom voltage reading logic
        return 5.0  # Example value
    
    def _read_custom_current(self) -> Optional[float]:
        """
        Read current from custom hardware.
        
        Returns:
            float: Current value, None if read failed
        """
        # Implement custom current reading logic
        return 0.1  # Example value
```

### Step 2: Update Power Supply Factory

Modify `lib/power_supply.py` to support custom power supplies:

```python
# Add import
from lib.custom_power_supply import CustomPowerSupply

# Update PowerSupplyFactory class
class PowerSupplyFactory:
    """Factory for creating power supply instances based on configuration."""
    
    @staticmethod
    def create_power_supply(config: Dict[str, Any]):
        """
        Create power supply instance based on configuration.
        
        Args:
            config (dict): Power supply configuration
            
        Returns:
            PowerSupplyBase: Appropriate power supply instance
            
        Raises:
            ValueError: If configuration is invalid or unsupported
        """
        # Check for custom power supply type
        if config.get('type') == 'custom':
            return CustomPowerSupply(config)
        
        # Check for GPIB connection
        if 'resource' in config:
            if not PYVISA_AVAILABLE:
                raise ImportError("PyVISA not available for GPIB communication")
            return KeysightE3632A_GPIB(config)
        
        # Check for RS232 connection
        if 'port' in config:
            return KeysightE3632A_RS232(config)
        
        # Default to RS232 if no specific connection type
        if 'connection_type' in config:
            if config['connection_type'] == 'gpib':
                if not PYVISA_AVAILABLE:
                    raise ImportError("PyVISA not available for GPIB communication")
                return KeysightE3632A_GPIB(config)
            elif config['connection_type'] == 'rs232':
                return KeysightE3632A_RS232(config)
        
        raise ValueError("Invalid power supply configuration: missing connection type")
```

### Step 3: Update Configuration

Add support for custom power supply configuration:

```json
{
  "power_supply": {
    "type": "custom",
    "device_id": "custom_device_001",
    "connection_type": "custom",
    "voltage": 5.0,
    "current_limit": 0.5,
    "custom_settings": {
      "protocol": "custom_protocol",
      "timeout": 5,
      "retry_count": 3
    }
  }
}
```

## Adding Custom Validation Patterns

### Step 1: Create Custom Pattern Validator

Create a new file `lib/custom_pattern_validator.py`:

```python
#!/usr/bin/env python3
"""
Custom Pattern Validator

Extends pattern validation capabilities beyond standard regex patterns.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class CustomPatternValidator:
    """
    Custom pattern validator for specialized validation scenarios.
    
    This class provides extended pattern validation capabilities
    beyond standard regex matching, including:
    - JSON structure validation
    - Numeric range validation
    - Time-based pattern validation
    - Custom algorithm validation
    """
    
    def __init__(self):
        """Initialize custom pattern validator."""
        self.logger = logging.getLogger(__name__)
        self.validation_results = []
    
    def validate_custom_pattern(self, pattern_config: Dict[str, Any], 
                               data: str) -> Dict[str, Any]:
        """
        Validate data against custom pattern configuration.
        
        Args:
            pattern_config (dict): Pattern configuration
            data (str): Data to validate
            
        Returns:
            dict: Validation results
        """
        pattern_type = pattern_config.get('type', 'regex')
        pattern_name = pattern_config.get('name', 'Custom Pattern')
        
        try:
            if pattern_type == 'json_structure':
                result = self._validate_json_structure(pattern_config, data)
            elif pattern_type == 'numeric_range':
                result = self._validate_numeric_range(pattern_config, data)
            elif pattern_type == 'time_based':
                result = self._validate_time_based(pattern_config, data)
            elif pattern_type == 'custom_algorithm':
                result = self._validate_custom_algorithm(pattern_config, data)
            else:
                result = self._validate_regex_pattern(pattern_config, data)
            
            return {
                'pattern_name': pattern_name,
                'pattern_type': pattern_type,
                'success': result['success'],
                'matched_data': result.get('matched_data'),
                'message': result.get('message', ''),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Custom pattern validation failed: {e}")
            return {
                'pattern_name': pattern_name,
                'pattern_type': pattern_type,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _validate_json_structure(self, pattern_config: Dict[str, Any], 
                               data: str) -> Dict[str, Any]:
        """
        Validate JSON structure and content.
        
        Args:
            pattern_config (dict): Pattern configuration
            data (str): Data to validate
            
        Returns:
            dict: Validation results
        """
        try:
            # Parse JSON data
            json_data = json.loads(data)
            
            # Check required fields
            required_fields = pattern_config.get('required_fields', [])
            for field in required_fields:
                if field not in json_data:
                    return {
                        'success': False,
                        'message': f"Missing required field: {field}"
                    }
            
            # Check field values
            field_checks = pattern_config.get('field_checks', {})
            for field, expected_value in field_checks.items():
                if field in json_data:
                    if json_data[field] != expected_value:
                        return {
                            'success': False,
                            'message': f"Field {field} value mismatch: expected {expected_value}, got {json_data[field]}"
                        }
            
            return {
                'success': True,
                'matched_data': json_data,
                'message': 'JSON structure validation passed'
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'message': f"Invalid JSON format: {e}"
            }
    
    def _validate_numeric_range(self, pattern_config: Dict[str, Any], 
                               data: str) -> Dict[str, Any]:
        """
        Validate numeric values within specified ranges.
        
        Args:
            pattern_config (dict): Pattern configuration
            data (str): Data to validate
            
        Returns:
            dict: Validation results
        """
        try:
            # Extract numeric value from data
            value_pattern = pattern_config.get('value_pattern', r'(\d+\.?\d*)')
            match = re.search(value_pattern, data)
            
            if not match:
                return {
                    'success': False,
                    'message': 'No numeric value found in data'
                }
            
            value = float(match.group(1))
            
            # Check range
            min_value = pattern_config.get('min_value', float('-inf'))
            max_value = pattern_config.get('max_value', float('inf'))
            
            if min_value <= value <= max_value:
                return {
                    'success': True,
                    'matched_data': value,
                    'message': f'Numeric value {value} within range [{min_value}, {max_value}]'
                }
            else:
                return {
                    'success': False,
                    'message': f'Numeric value {value} outside range [{min_value}, {max_value}]'
                }
                
        except (ValueError, TypeError) as e:
            return {
                'success': False,
                'message': f'Error parsing numeric value: {e}'
            }
    
    def _validate_time_based(self, pattern_config: Dict[str, Any], 
                           data: str) -> Dict[str, Any]:
        """
        Validate time-based patterns and sequences.
        
        Args:
            pattern_config (dict): Pattern configuration
            data (str): Data to validate
            
        Returns:
            dict: Validation results
        """
        try:
            # Extract timestamp from data
            time_pattern = pattern_config.get('time_pattern', r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
            match = re.search(time_pattern, data)
            
            if not match:
                return {
                    'success': False,
                    'message': 'No timestamp found in data'
                }
            
            timestamp_str = match.group(1)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Check time constraints
            min_time = pattern_config.get('min_time')
            max_time = pattern_config.get('max_time')
            
            if min_time and timestamp < datetime.strptime(min_time, '%Y-%m-%d %H:%M:%S'):
                return {
                    'success': False,
                    'message': f'Timestamp {timestamp_str} before minimum time {min_time}'
                }
            
            if max_time and timestamp > datetime.strptime(max_time, '%Y-%m-%d %H:%M:%S'):
                return {
                    'success': False,
                    'message': f'Timestamp {timestamp_str} after maximum time {max_time}'
                }
            
            return {
                'success': True,
                'matched_data': timestamp_str,
                'message': f'Timestamp {timestamp_str} within valid range'
            }
            
        except ValueError as e:
            return {
                'success': False,
                'message': f'Error parsing timestamp: {e}'
            }
    
    def _validate_custom_algorithm(self, pattern_config: Dict[str, Any], 
                                 data: str) -> Dict[str, Any]:
        """
        Validate using custom algorithm.
        
        Args:
            pattern_config (dict): Pattern configuration
            data (str): Data to validate
            
        Returns:
            dict: Validation results
        """
        try:
            # Get custom algorithm parameters
            algorithm = pattern_config.get('algorithm', 'checksum')
            parameters = pattern_config.get('parameters', {})
            
            if algorithm == 'checksum':
                return self._validate_checksum(data, parameters)
            elif algorithm == 'hash':
                return self._validate_hash(data, parameters)
            elif algorithm == 'sequence':
                return self._validate_sequence(data, parameters)
            else:
                return {
                    'success': False,
                    'message': f'Unknown algorithm: {algorithm}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Custom algorithm validation failed: {e}'
            }
    
    def _validate_checksum(self, data: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate checksum algorithm."""
        expected_checksum = parameters.get('expected_checksum')
        checksum_type = parameters.get('checksum_type', 'simple')
        
        if checksum_type == 'simple':
            calculated_checksum = sum(ord(c) for c in data) % 256
        elif checksum_type == 'crc16':
            # Implement CRC16 calculation
            calculated_checksum = self._calculate_crc16(data)
        else:
            return {
                'success': False,
                'message': f'Unknown checksum type: {checksum_type}'
            }
        
        if calculated_checksum == expected_checksum:
            return {
                'success': True,
                'matched_data': calculated_checksum,
                'message': f'Checksum validation passed: {calculated_checksum}'
            }
        else:
            return {
                'success': False,
                'message': f'Checksum mismatch: expected {expected_checksum}, got {calculated_checksum}'
            }
    
    def _validate_hash(self, data: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate hash algorithm."""
        import hashlib
        
        expected_hash = parameters.get('expected_hash')
        hash_type = parameters.get('hash_type', 'md5')
        
        if hash_type == 'md5':
            calculated_hash = hashlib.md5(data.encode()).hexdigest()
        elif hash_type == 'sha1':
            calculated_hash = hashlib.sha1(data.encode()).hexdigest()
        elif hash_type == 'sha256':
            calculated_hash = hashlib.sha256(data.encode()).hexdigest()
        else:
            return {
                'success': False,
                'message': f'Unknown hash type: {hash_type}'
            }
        
        if calculated_hash == expected_hash:
            return {
                'success': True,
                'matched_data': calculated_hash,
                'message': f'Hash validation passed: {calculated_hash}'
            }
        else:
            return {
                'success': False,
                'message': f'Hash mismatch: expected {expected_hash}, got {calculated_hash}'
            }
    
    def _validate_sequence(self, data: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sequence pattern."""
        expected_sequence = parameters.get('expected_sequence', [])
        sequence_pattern = parameters.get('sequence_pattern', r'(\w+)')
        
        matches = re.findall(sequence_pattern, data)
        
        if matches == expected_sequence:
            return {
                'success': True,
                'matched_data': matches,
                'message': f'Sequence validation passed: {matches}'
            }
        else:
            return {
                'success': False,
                'message': f'Sequence mismatch: expected {expected_sequence}, got {matches}'
            }
    
    def _calculate_crc16(self, data: str) -> int:
        """Calculate CRC16 checksum."""
        # Simple CRC16 implementation
        crc = 0xFFFF
        for byte in data.encode():
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF
    
    def _validate_regex_pattern(self, pattern_config: Dict[str, Any], 
                              data: str) -> Dict[str, Any]:
        """Validate standard regex pattern."""
        pattern = pattern_config.get('pattern', '')
        expected = pattern_config.get('expected', [])
        
        match = re.search(pattern, data)
        
        if match:
            matched_groups = match.groups()
            
            if expected:
                if isinstance(expected[0], list):
                    # Multiple capture groups
                    if matched_groups == tuple(expected[0]):
                        return {
                            'success': True,
                            'matched_data': matched_groups,
                            'message': f'Pattern matched: {matched_groups}'
                        }
                else:
                    # Single capture group
                    if matched_groups[0] in expected:
                        return {
                            'success': True,
                            'matched_data': matched_groups[0],
                            'message': f'Pattern matched: {matched_groups[0]}'
                        }
            else:
                return {
                    'success': True,
                    'matched_data': match.group(0),
                    'message': f'Pattern matched: {match.group(0)}'
                }
        
        return {
            'success': False,
            'message': 'Pattern did not match'
        }
```

### Step 2: Integrate with Pattern Validator

Modify `lib/pattern_validator.py` to support custom patterns:

```python
# Add import
from lib.custom_pattern_validator import CustomPatternValidator

# Update PatternValidator class
class PatternValidator:
    """Validates UART data against expected patterns."""
    
    def __init__(self):
        """Initialize pattern validator."""
        self.logger = logging.getLogger(__name__)
        self.custom_validator = CustomPatternValidator()
    
    def validate_patterns(self, patterns: List[Dict[str, Any]], 
                         uart_data: List[str]) -> List[ValidationResult]:
        """
        Validate UART data against multiple patterns.
        
        Args:
            patterns (list): List of pattern configurations
            uart_data (list): UART data to validate
            
        Returns:
            list: List of validation results
        """
        results = []
        
        for pattern in patterns:
            # Check if this is a custom pattern type
            if pattern.get('type') in ['json_structure', 'numeric_range', 'time_based', 'custom_algorithm']:
                result = self._validate_custom_pattern(pattern, uart_data)
            else:
                result = self._validate_standard_pattern(pattern, uart_data)
            
            results.append(result)
        
        return results
    
    def _validate_custom_pattern(self, pattern: Dict[str, Any], 
                                uart_data: List[str]) -> ValidationResult:
        """Validate custom pattern type."""
        pattern_name = pattern.get('name', 'Custom Pattern')
        
        # Combine UART data for validation
        combined_data = '\n'.join(uart_data)
        
        # Use custom validator
        result = self.custom_validator.validate_custom_pattern(pattern, combined_data)
        
        return ValidationResult(
            pattern_name=pattern_name,
            success=result['success'],
            matched_data=result.get('matched_data'),
            message=result.get('message', ''),
            timestamp=result.get('timestamp', datetime.now().isoformat())
        )
```

### Step 3: Update Template System

Add support for custom pattern types in templates:

```json
{
  "test_templates": {
    "json_validation_test": {
      "description": "Test with JSON structure validation",
      "uart_patterns": [
        {
          "name": "json_status_check",
          "type": "json_structure",
          "required_fields": ["status", "code"],
          "field_checks": {
            "status": "OK",
            "code": 200
          }
        }
      ],
      "output_format": "json"
    },
    "numeric_range_test": {
      "description": "Test with numeric range validation",
      "uart_patterns": [
        {
          "name": "voltage_check",
          "type": "numeric_range",
          "value_pattern": "Voltage:\\s*(\\d+\\.\\d+)",
          "min_value": 4.8,
          "max_value": 5.2
        }
      ],
      "output_format": "csv"
    },
    "checksum_validation_test": {
      "description": "Test with checksum validation",
      "uart_patterns": [
        {
          "name": "data_checksum",
          "type": "custom_algorithm",
          "algorithm": "checksum",
          "parameters": {
            "checksum_type": "crc16",
            "expected_checksum": 12345
          }
        }
      ],
      "output_format": "xml"
    }
  }
}
```

## Testing and Validation

### Step 1: Create Test Cases

Create test cases for your custom implementations:

```python
#!/usr/bin/env python3
"""
Test cases for custom framework extensions.
"""

import unittest
import json
from lib.custom_test_handler import CustomTestHandler
from lib.custom_report_generator import CustomReportGenerator
from lib.custom_pattern_validator import CustomPatternValidator


class TestCustomExtensions(unittest.TestCase):
    """Test cases for custom framework extensions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'name': 'test_custom',
            'test_type': 'custom',
            'custom_settings': {
                'timeout': 10,
                'retry_count': 3
            }
        }
        
        self.pattern_config = {
            'name': 'test_pattern',
            'type': 'json_structure',
            'required_fields': ['status'],
            'field_checks': {'status': 'OK'}
        }
    
    def test_custom_test_handler(self):
        """Test custom test handler functionality."""
        handler = CustomTestHandler({})
        result = handler.execute_custom_test(self.test_config)
        
        self.assertIn('test_name', result)
        self.assertIn('status', result)
        self.assertIn('start_time', result)
        self.assertIn('end_time', result)
    
    def test_custom_pattern_validator_json(self):
        """Test custom pattern validator with JSON structure."""
        validator = CustomPatternValidator()
        data = '{"status": "OK", "code": 200}'
        
        result = validator.validate_custom_pattern(self.pattern_config, data)
        
        self.assertTrue(result['success'])
        self.assertIn('matched_data', result)
    
    def test_custom_report_generator_xml(self):
        """Test custom report generator with XML output."""
        generator = CustomReportGenerator({})
        test_summary = {
            'total_cycles': 5,
            'successful_cycles': 4,
            'failed_cycles': 1,
            'success_rate': 0.8
        }
        
        filepath = generator.generate_xml_report(test_summary)
        
        self.assertTrue(filepath.endswith('.xml'))
        # Verify file exists and contains expected content
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertIn('<test_results>', content)
            self.assertIn('<total_cycles>5</total_cycles>', content)


if __name__ == '__main__':
    unittest.main()
```

### Step 2: Integration Testing

Create integration tests to verify custom extensions work with the main framework:

```python
#!/usr/bin/env python3
"""
Integration tests for custom framework extensions.
"""

import unittest
import tempfile
import json
from pathlib import Path
from lib.test_runner import PowerCycleTestRunner


class TestCustomIntegration(unittest.TestCase):
    """Integration tests for custom framework extensions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_config.json'
        
        # Create test configuration with custom elements
        self.config = {
            'power_supply': {
                'type': 'custom',
                'device_id': 'test_device',
                'voltage': 5.0,
                'current_limit': 0.5
            },
            'uart_loggers': [
                {
                    'port': 'COM1',
                    'baud': 115200,
                    'display': False
                }
            ],
            'tests': [
                {
                    'name': 'custom_test',
                    'test_type': 'custom',
                    'cycles': 1,
                    'on_time': 1,
                    'off_time': 1,
                    'output_format': 'xml'
                }
            ]
        }
        
        # Write configuration file
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
    
    def test_custom_test_execution(self):
        """Test execution of custom test type."""
        runner = PowerCycleTestRunner()
        runner.config = self.config
        
        # Test should complete without errors
        # (Note: This is a simplified test - real hardware would be needed for full testing)
        self.assertIsNotNone(runner.config)
        self.assertEqual(runner.config['tests'][0]['test_type'], 'custom')
    
    def test_custom_output_format(self):
        """Test custom output format generation."""
        runner = PowerCycleTestRunner()
        runner.config = self.config
        
        # Verify custom output format is recognized
        test_config = runner.config['tests'][0]
        self.assertEqual(test_config['output_format'], 'xml')
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)


if __name__ == '__main__':
    unittest.main()
```

## Best Practices

### 1. Code Organization

- **Modular Design**: Keep custom extensions in separate modules
- **Clear Interfaces**: Define clear interfaces between custom and standard components
- **Error Handling**: Implement comprehensive error handling and logging
- **Documentation**: Document all custom functionality thoroughly

### 2. Configuration Management

- **Template System**: Use the template system for configuration management
- **Validation**: Validate all custom configuration parameters
- **Defaults**: Provide sensible defaults for custom settings
- **Backward Compatibility**: Maintain compatibility with existing configurations

### 3. Testing Strategy

- **Unit Tests**: Create unit tests for all custom functionality
- **Integration Tests**: Test custom extensions with the main framework
- **Error Cases**: Test error handling and edge cases
- **Performance**: Consider performance implications of custom extensions

### 4. Maintenance

- **Version Control**: Use version control for all custom extensions
- **Change Log**: Maintain a change log for custom modifications
- **Dependencies**: Document all external dependencies
- **Updates**: Plan for framework updates and compatibility

### 5. Deployment

- **Installation**: Provide clear installation instructions
- **Configuration**: Document configuration requirements
- **Troubleshooting**: Provide troubleshooting guides
- **Support**: Establish support channels for custom extensions

## Conclusion

This guide provides a comprehensive framework for extending the Automated Power Cycle and UART Validation Framework. By following these patterns and best practices, developers can:

- Create custom test types for specialized hardware
- Implement new output formats for different reporting needs
- Extend hardware support for new devices
- Add custom validation patterns for specialized data analysis
- Maintain code quality and compatibility

The modular architecture of the framework makes it easy to extend while maintaining the existing functionality and user experience.
