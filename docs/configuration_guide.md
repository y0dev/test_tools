# Configuration Guide

## Overview

The framework uses a two-tier configuration system to provide flexibility and maintainability:

1. **Main Configuration** (`config/config.json`) - Hardware settings and test references
2. **Test Templates** (`config/test_templates.json`) - Reusable test definitions with defaults

## Main Configuration (`config/config.json`)

### Power Supply Configuration

```json
{
  "power_supply": {
    "resource": "GPIB0::5::INSTR",  // GPIB resource string
    "voltage": 5.0,                 // Output voltage
    "current_limit": 0.5           // Current limit in amps
  }
}
```

**Alternative RS232 Configuration:**
```json
{
  "power_supply": {
    "port": "COM1",                // Serial port
    "baudrate": 9600,              // Baud rate
    "voltage": 5.0,
    "current_limit": 0.5
  }
}
```

### UART Logger Configuration

```json
{
  "uart_loggers": [
    {
      "port": "COM3",              // Serial port
      "baud": 115200,              // Baud rate
      "display": true              // Show UART data in console
    }
  ]
}
```

### Test Configuration

```json
{
  "tests": [
    {
      "name": "boot_data_test"     // References template name
    },
    {
      "name": "power_cycle_test",
      "cycles": 3,                 // Override default cycles
      "on_time": 3,               // Override default on_time
      "off_time": 2               // Override default off_time
    }
  ]
}
```

## Test Templates (`config/test_templates.json`)

### Template Structure

```json
{
  "test_templates": {
    "template_name": {
      "description": "Test description",
      "uart_patterns": [
        {
          "regex": "pattern_regex",
          "expected": ["expected_value"]
        }
      ],
      "output_format": "json"
    }
  },
  "defaults": {
    "cycles": 1,
    "on_time": 5,
    "off_time": 3,
    "output_format": "json"
  },
  "output": {
    "log_directory": "./output/logs",
    "report_directory": "./output/reports",
    "detailed_logs": true,
    "timestamp_format": "%Y-%m-%d_%H-%M-%S",
    "log_level": "INFO"
  }
}
```

### Template Examples

#### Boot Data Test
```json
{
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
  }
}
```

#### Simple Ready Test
```json
{
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
}
```

#### Power Cycle Test
```json
{
  "power_cycle_test": {
    "description": "Test multiple power cycles",
    "uart_patterns": [
      {
        "regex": "READY",
        "expected": ["READY"]
      }
    ],
    "output_format": "csv"
  }
}
```

## Pattern Validation

### Regex Patterns

The framework uses Python regex patterns for UART data validation:

```json
{
  "regex": "Data:\\s*(0x[0-9A-Fa-f]+)",  // Matches "Data: 0x12345678"
  "expected": ["0x12345678"]              // Expected captured group
}
```

### Multiple Capture Groups

```json
{
  "regex": "Data:\\s*(0x[0-9A-Fa-f]+),\\s*(0x[0-9A-Fa-f]+)",
  "expected": [["0x12345678", "0xDEADBEEF"]]  // List of lists for multiple groups
}
```

### Multiple Expected Values

```json
{
  "regex": "Version:\\s*v(\\d+\\.\\d+)",
  "expected": ["v1.0", "v1.1", "v1.2"]  // Any of these values accepted
}
```

## Output Configuration

### Log Directory
```json
{
  "output": {
    "log_directory": "./output/logs",      // Log file location
    "report_directory": "./output/reports", // Report file location
    "detailed_logs": true,                 // Enable detailed logging
    "timestamp_format": "%Y-%m-%d_%H-%M-%S", // Timestamp format
    "log_level": "INFO"                    // Logging level
  }
}
```

### Log Levels
- `DEBUG` - Detailed debugging information
- `INFO` - General information (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

## Template Resolution Process

When a test is executed, the framework resolves the configuration as follows:

1. **Load Defaults** - Apply default values from `defaults` section
2. **Load Template** - Apply template-specific settings
3. **Apply Overrides** - Apply test-specific overrides
4. **Validate** - Ensure all required fields are present

### Example Resolution

**Input Test Config:**
```json
{
  "name": "boot_data_test",
  "cycles": 2
}
```

**Resolved Configuration:**
```json
{
  "name": "boot_data_test",
  "description": "Verify correct boot data is printed",
  "cycles": 2,                    // Overridden
  "on_time": 5,                   // Default
  "off_time": 3,                  // Default
  "output_format": "json",        // From template
  "uart_patterns": [...]          // From template
}
```

## Configuration Validation

The framework validates configurations to ensure:

- Required fields are present
- Template names exist
- UART patterns are valid regex
- Output formats are supported
- Hardware settings are reasonable

### Validation Commands

```bash
# Validate main configuration
python main.py --validate-config

# Validate with custom config file
python main.py --validate-config --config config/my_config.json
```

## Best Practices

1. **Use Templates** - Define common test patterns in templates
2. **Override Sparingly** - Only override what's different from defaults
3. **Descriptive Names** - Use clear, descriptive template names
4. **Test Patterns** - Validate regex patterns before using
5. **Backup Configs** - Keep backup copies of working configurations
6. **Version Control** - Track configuration changes in version control
7. **Documentation** - Document custom templates and their purposes
