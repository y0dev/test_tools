# Automated Power Cycle and UART Validation Framework

A comprehensive Python framework for automated hardware testing that combines power cycling capabilities with UART data validation. This framework is designed for testing embedded devices, microcontrollers, and other hardware that requires power cycling and UART communication validation.

## Features

- **Automated Power Cycling**: Control Keysight E3632A power supply via RS232/GPIB
- **UART Data Logging**: Real-time UART data capture and logging
- **Pattern Validation**: Advanced pattern matching with multiple validation types
- **Comprehensive Reporting**: Generate reports in CSV, JSON, HTML, and text formats
- **Configurable Testing**: JSON-based configuration for easy customization
- **Multi-DUT Support**: Scale for multiple devices under test
- **Real-time Monitoring**: Live test progress and status updates
- **Error Handling**: Robust error detection and recovery

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd test_tool

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Sample Configuration

```bash
python main.py --generate-config
```

This creates a `sample_config.json` file that you can customize for your hardware setup.

### 3. Configure Your Hardware

Edit `config.json` (or `sample_config.json`) with your specific hardware settings:

```json
{
  "power_supply": {
    "port": "COM3",        # Your power supply COM port
    "voltage": 5.0,        # Output voltage
    "current_limit": 1.0  # Current limit
  },
  "uart": {
    "port": "COM4",        # Your UART COM port
    "baud_rate": 115200    # UART baud rate
  }
}
```

### 4. Run Tests

```bash
# Interactive mode (recommended for first run)
python main.py --interactive

# Automated mode
python main.py

# With custom configuration
python main.py -c my_config.json
```

## Configuration

The framework uses JSON configuration files to define test parameters. Key sections include:

### Test Configuration
```json
{
  "test_config": {
    "test_name": "My Power Cycle Test",
    "total_cycles": 10,
    "power_on_duration": 5.0,
    "power_off_duration": 3.0,
    "cycle_delay": 2.0
  }
}
```

### Power Supply Settings
```json
{
  "power_supply": {
    "connection_type": "rs232",
    "port": "COM3",
    "baud_rate": 9600,
    "voltage": 5.0,
    "current_limit": 1.0
  }
}
```

### UART Settings
```json
{
  "uart": {
    "port": "COM4",
    "baud_rate": 115200,
    "data_bits": 8,
    "parity": "none",
    "stop_bits": 1
  }
}
```

### Test Configuration with Per-Test Output Format
```json
{
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
        }
      ]
    },
    {
      "name": "Power Cycle Test",
      "description": "Test multiple power cycles",
      "cycles": 3,
      "on_time": 3,
      "off_time": 2,
      "output_format": "csv",
      "uart_patterns": [
        {
          "regex": "READY",
          "expected": ["READY"]
        }
      ]
    }
  ]
}
```

## Command Line Interface

The framework provides a comprehensive CLI with multiple options:

```bash
# Basic usage
python main.py

# Interactive mode with prompts
python main.py --interactive

# Custom configuration file
python main.py -c my_config.json

# Override number of cycles
python main.py --cycles 5

# Set log level
python main.py --log-level DEBUG

# Validate configuration
python main.py --validate-config

# List available pattern types
python main.py --list-patterns

# Generate sample configuration
python main.py --generate-config
```

## Validation Pattern Types

The framework supports multiple pattern validation types:

### 1. Contains
Simple string containment check:
```json
{
  "name": "boot_ready",
  "pattern": "READY",
  "pattern_type": "contains"
}
```

### 2. Regex
Regular expression pattern matching:
```json
{
  "name": "version_info",
  "pattern": "Version: \\d+\\.\\d+",
  "pattern_type": "regex"
}
```

### 3. Exact
Exact string match:
```json
{
  "name": "status_ok",
  "pattern": "OK",
  "pattern_type": "exact"
}
```

### 4. Numeric Range
Numeric value within range:
```json
{
  "name": "voltage_check",
  "pattern": "3.0,3.6",
  "pattern_type": "numeric_range"
}
```

### 5. JSON Key
JSON key existence check:
```json
{
  "name": "json_status",
  "pattern": "status",
  "pattern_type": "json_key"
}
```

## Report Generation

The framework generates comprehensive reports in multiple formats:

- **CSV**: Detailed test data for analysis
- **JSON**: Structured data for programmatic processing  
- **HTML**: Visual reports with charts and tables
- **Text**: Human-readable summary reports

### Per-Test Output Format

Each test can specify its own output format using the `output_format` field:

```json
{
  "name": "My Test",
  "output_format": "json",  // Options: json, csv, html, text, or comprehensive
  "uart_patterns": [...]
}
```

**Supported Output Formats:**
- `json` - JSON format only
- `csv` - CSV format only  
- `html` - HTML format only
- `text` - Text format only
- `comprehensive` - All formats (default if not specified)

**Benefits:**
- Different tests can have different reporting requirements
- Reduces file clutter by generating only needed formats
- Allows for test-specific report customization
- Maintains overall comprehensive report for complete test suite

Reports are automatically generated after test completion and saved to the configured output directory.

## Hardware Requirements

### Power Supply
- Keysight E3632A (or compatible SCPI power supply)
- RS232 or GPIB connection
- Appropriate voltage/current ratings for your DUT

### UART Interface
- USB-to-Serial adapter or built-in serial port
- Compatible with your device's UART settings
- Sufficient buffer size for data logging

### Computer
- Windows/Linux/macOS
- Python 3.7 or higher
- Available COM ports for hardware connections

## Project Structure

```
test_tool/
├── main.py                 # Main entry point and CLI
├── config.json            # Default configuration
├── requirements.txt       # Python dependencies
├── libs/                   # Core framework modules
│   ├── power_supply.py    # Power supply control
│   ├── uart_handler.py    # UART communication
│   ├── pattern_validator.py # Pattern validation
│   ├── test_logger.py     # Logging system
│   ├── report_generator.py # Report generation
│   └── test_runner.py     # Main test orchestrator
├── logs/                  # Test logs (created automatically)
└── reports/               # Test reports (created automatically)
```

## API Reference

### PowerCycleTestRunner

Main test orchestrator class:

```python
from lib.test_runner import PowerCycleTestRunner

# Initialize runner
runner = PowerCycleTestRunner("config.json")

# Initialize components
runner.initialize_components()

# Run test
results = runner.run_test()

# Cleanup
runner.cleanup_components()
```

### UARTHandler

UART communication handler:

```python
from lib.uart_handler import UARTHandler

# Initialize handler
uart = UARTHandler(uart_config)

# Connect and start logging
uart.connect()
uart.start_logging()

# Wait for pattern
result = uart.wait_for_pattern("READY", timeout=5.0)

# Disconnect
uart.disconnect()
```

### PatternValidator

Pattern validation system:

```python
from lib.pattern_validator import PatternValidator

# Initialize validator
validator = PatternValidator()

# Validate pattern
result = validator.validate_pattern(data, pattern_config)

# Wait for pattern in stream
result = validator.wait_for_pattern_in_stream(uart_handler, pattern_config)
```

## Troubleshooting

### Common Issues

1. **Power Supply Connection Failed**
   - Check COM port availability
   - Verify power supply is powered on
   - Confirm RS232 cable connections
   - Check baud rate settings

2. **UART Connection Failed**
   - Verify COM port is not in use by another application
   - Check UART settings (baud rate, parity, etc.)
   - Confirm device is connected and powered

3. **Pattern Validation Failures**
   - Review UART data logs for actual device output
   - Adjust pattern regex if needed
   - Increase timeout values for slow devices
   - Check if patterns are case-sensitive

4. **Configuration Errors**
   - Use `python main.py --validate-config` to check configuration
   - Ensure all required fields are present
   - Verify JSON syntax is correct

### Debug Mode

Run with debug logging for detailed information:

```bash
python main.py --log-level DEBUG
```

This provides detailed logs of all operations, including UART data and power supply commands.

## Contributing

This framework is designed to be modular and extensible. Key areas for enhancement:

- Additional power supply models
- Enhanced pattern validation types
- Database logging integration
- Web-based monitoring interface
- Multi-threaded testing for multiple DUTs

## License

This project is provided as-is for educational and development purposes. Please ensure compliance with your organization's policies when using with proprietary hardware.

## Support

For issues, questions, or feature requests, please refer to the project documentation or create an issue in the project repository.
