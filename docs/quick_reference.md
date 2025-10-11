# Quick Reference: Test Creation and Framework Extension

## Overview

This quick reference provides essential information for creating custom tests and extending the Automated Power Cycle and UART Validation Framework.

## Creating a New Test Template

### 1. Add Template to `config/test_templates.json`

```json
{
  "test_templates": {
    "my_custom_test": {
      "description": "Description of your test",
      "test_type": "custom",  // Optional: for custom test types
      "uart_patterns": [      // Optional: for UART validation
        {
          "name": "pattern_name",
          "regex": "pattern_regex",
          "expected": ["expected_value"]
        }
      ],
      "output_format": "json", // json, csv, html, text, xml, yaml, excel
      "custom_settings": {     // Optional: for custom test parameters
        "param1": "value1",
        "param2": "value2"
      }
    }
  }
}
```

### 2. Use Template in `config/config.json`

```json
{
  "tests": [
    {
      "name": "my_custom_test",
      "cycles": 3,
      "on_time": 5,
      "off_time": 2
    }
  ]
}
```

## Custom Test Types

### 1. Create Custom Test Handler

```python
# libs/custom_test_handler.py
class CustomTestHandler:
    def __init__(self, config):
        self.config = config
    
    def execute_custom_test(self, test_config):
        # Implement your custom test logic
        return {
            'test_name': test_config.get('name'),
            'status': 'PASS',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'custom_data': {}
        }
```

### 2. Integrate with Test Runner

```python
# libs/test_runner.py
def run_custom_test(self, test_config):
    custom_handler = CustomTestHandler(self.config)
    return custom_handler.execute_custom_test(test_config)
```

## Custom Output Formats

### 1. Create Custom Report Generator

```python
# libs/custom_report_generator.py
class CustomReportGenerator:
    def generate_xml_report(self, test_summary, cycle_data, uart_data):
        # Generate XML report
        return filepath
    
    def generate_yaml_report(self, test_summary, cycle_data, uart_data):
        # Generate YAML report
        return filepath
    
    def generate_excel_report(self, test_summary, cycle_data, uart_data):
        # Generate Excel report
        return filepath
```

### 2. Integrate with Report Generator

```python
# libs/report_generator.py
def generate_custom_report(self, test_summary, cycle_data, uart_data, format_type):
    custom_generator = CustomReportGenerator(self.config, self.logger)
    
    if format_type == 'xml':
        return custom_generator.generate_xml_report(test_summary, cycle_data, uart_data)
    elif format_type == 'yaml':
        return custom_generator.generate_yaml_report(test_summary, cycle_data, uart_data)
    elif format_type == 'excel':
        return custom_generator.generate_excel_report(test_summary, cycle_data, uart_data)
```

## Custom Validation Patterns

### 1. JSON Structure Validation

```json
{
  "name": "json_status",
  "type": "json_structure",
  "required_fields": ["status", "code"],
  "field_checks": {
    "status": "OK",
    "code": 200
  }
}
```

### 2. Numeric Range Validation

```json
{
  "name": "voltage_check",
  "type": "numeric_range",
  "value_pattern": "Voltage:\\s*(\\d+\\.\\d+)",
  "min_value": 4.8,
  "max_value": 5.2
}
```

### 3. Time-Based Validation

```json
{
  "name": "timestamp_check",
  "type": "time_based",
  "time_pattern": "(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})",
  "min_time": "2024-01-01 00:00:00",
  "max_time": "2024-12-31 23:59:59"
}
```

### 4. Custom Algorithm Validation

```json
{
  "name": "checksum_validation",
  "type": "custom_algorithm",
  "algorithm": "checksum",
  "parameters": {
    "checksum_type": "crc16",
    "expected_checksum": 12345
  }
}
```

## Custom Hardware Support

### 1. Create Custom Power Supply

```python
# libs/custom_power_supply.py
class CustomPowerSupply(PowerSupplyBase):
    def __init__(self, config):
        super().__init__(config)
        self.device_id = config.get('device_id')
    
    def connect(self):
        # Implement custom connection logic
        return True
    
    def set_voltage(self, voltage):
        # Implement custom voltage setting
        return True
    
    def enable_output(self):
        # Implement custom output enable
        return True
```

### 2. Update Power Supply Factory

```python
# libs/power_supply.py
class PowerSupplyFactory:
    @staticmethod
    def create_power_supply(config):
        if config.get('type') == 'custom':
            return CustomPowerSupply(config)
        # ... existing logic
```

## Configuration Examples

### Custom Test Configuration

```json
{
  "power_supply": {
    "type": "custom",
    "device_id": "custom_device_001",
    "voltage": 5.0,
    "current_limit": 0.5
  },
  "uart_loggers": [
    {
      "port": "COM3",
      "baud": 115200,
      "display": true
    }
  ],
  "tests": [
    {
      "name": "temperature_test",
      "test_type": "custom",
      "cycles": 3,
      "on_time": 10,
      "off_time": 5,
      "output_format": "excel",
      "temperature_settings": {
        "min_temperature": 20.0,
        "max_temperature": 80.0
      }
    }
  ]
}
```

### Template with Custom Settings

```json
{
  "test_templates": {
    "custom_hardware_test": {
      "description": "Custom hardware validation",
      "test_type": "custom",
      "output_format": "xml",
      "custom_settings": {
        "hardware_type": "special_device",
        "validation_method": "custom_algorithm",
        "timeout": 30
      }
    }
  }
}
```

## Testing Your Extensions

### 1. Unit Tests

```python
import unittest

class TestCustomExtensions(unittest.TestCase):
    def test_custom_test_handler(self):
        handler = CustomTestHandler({})
        result = handler.execute_custom_test({'name': 'test'})
        self.assertIn('status', result)
    
    def test_custom_pattern_validator(self):
        validator = CustomPatternValidator()
        result = validator.validate_custom_pattern(pattern_config, data)
        self.assertTrue(result['success'])
```

### 2. Integration Tests

```python
def test_custom_integration(self):
    runner = PowerCycleTestRunner()
    runner.config = custom_config
    # Test custom functionality
```

## Best Practices

### Code Organization
- Keep custom extensions in separate modules
- Use clear, descriptive names
- Implement comprehensive error handling
- Document all custom functionality

### Configuration
- Use the template system for configuration
- Validate all custom parameters
- Provide sensible defaults
- Maintain backward compatibility

### Testing
- Create unit tests for custom functionality
- Test integration with main framework
- Test error handling and edge cases
- Consider performance implications

### Maintenance
- Use version control for all extensions
- Document dependencies and requirements
- Plan for framework updates
- Provide clear installation instructions

## Common Patterns

### Custom Test Pattern

```python
class CustomTest:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def execute_test(self):
        start_time = datetime.now()
        try:
            # Test logic here
            return {
                'test_name': self.config.get('name'),
                'status': 'PASS',
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'results': {}
            }
        except Exception as e:
            return {
                'test_name': self.config.get('name'),
                'status': 'FAIL',
                'error': str(e)
            }
```

### Custom Report Pattern

```python
class CustomReportGenerator:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
    
    def generate_custom_report(self, data):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"custom_report_{timestamp}.ext"
        filepath = Path(self.output_dir) / filename
        
        # Generate report content
        content = self._create_report_content(data)
        
        # Write file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return str(filepath)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Configuration Errors**: Validate JSON syntax and required fields
3. **Permission Errors**: Check file system permissions
4. **Hardware Errors**: Verify hardware connections and drivers

### Debug Tips

1. Enable debug logging: `--log-level DEBUG`
2. Use dry run mode: `--dry-run`
3. Validate configuration: `--validate-config`
4. Check log files in `output/logs/`

## Resources

- **Main Documentation**: `docs/test_creation_guide.md`
- **Examples**: `examples/custom_temperature_test.py`
- **Configuration**: `config/custom_test_config.json`
- **Templates**: `config/custom_test_templates.json`
- **Framework Code**: `libs/` directory
