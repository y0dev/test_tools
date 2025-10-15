# STM32 Log Capture Test Framework

This directory contains specialized test configurations and scripts for capturing and analyzing logs from your STM32 Nucleo-F070RB project located at `F:\Programming\STM32\Workspace\nucleo-f070rb\Core\Src`.

## Overview

The STM32 project outputs numeric data via UART2 (115200 baud) in the format: `"5\r\n"` through the `DEV_SAMPLE_FUNCTION()`. This test framework can capture, validate, and analyze this output.

## Files Created

### Configuration Files
- `config/stm32_log_capture_config.json` - Main configuration for STM32 log capture
- `config/stm32_test_templates.json` - STM32-specific test templates

### Test Scripts
- `stm32_log_capture_test.py` - Main test script for STM32 log capture
- `examples/stm32_log_example.py` - Example scripts demonstrating different usage patterns

## Quick Start

### 1. Basic Log Capture
```bash
# Run with default settings (COM3, 5 cycles)
python stm32_log_capture_test.py

# Use specific COM port
python stm32_log_capture_test.py --port COM4

# Run interactive mode
python stm32_log_capture_test.py --interactive
```

### 2. Different Test Types
```bash
# Numeric output validation (default)
python stm32_log_capture_test.py --test-type numeric

# Continuous logging
python stm32_log_capture_test.py --test-type continuous

# Power cycle testing
python stm32_log_capture_test.py --test-type power_cycle
```

### 3. Examples
```bash
# Run example scripts
python examples/stm32_log_example.py
```

## STM32 Project Analysis

Based on the analysis of your STM32 project:

### Hardware Configuration
- **MCU**: STM32F070RB
- **UART**: USART2
- **Baud Rate**: 115200
- **Data Format**: 8N1 (8 data bits, no parity, 1 stop bit)

### Software Behavior
- **Main Loop**: Infinite loop with button/LED interaction
- **Output Function**: `DEV_SAMPLE_FUNCTION()` outputs numeric data
- **Output Format**: `"5\r\n"` (number followed by carriage return and newline)
- **Timing**: Function called continuously in main loop

### Expected Output Patterns
1. **Numeric Output**: `^(\\d+)\\r\\n$` - Captures the numeric value
2. **Any Output**: `.*` - Captures all output for analysis
3. **Error Detection**: `ERROR|Error|error` - Detects error conditions

## Test Configurations

### 1. Numeric Output Test
- **Purpose**: Validate that STM32 outputs expected numeric values
- **Pattern**: `^(\\d+)\\r\\n$`
- **Expected**: `["5"]`
- **Cycles**: 5 (configurable)
- **Output Format**: JSON

### 2. Continuous Logging Test
- **Purpose**: Capture all STM32 output for analysis
- **Pattern**: `.*` (matches everything)
- **Expected**: `[]` (no specific validation)
- **Cycles**: 1
- **Duration**: 30 seconds
- **Output Format**: CSV

### 3. Power Cycle Test
- **Purpose**: Test STM32 behavior during power cycles
- **Pattern**: `^(\\d+)\\r\\n$`
- **Expected**: `["5"]`
- **Cycles**: 3
- **Power On**: 8 seconds
- **Power Off**: 4 seconds
- **Output Format**: HTML

## Usage Examples

### Example 1: Simple Log Capture
```python
from libs.uart_handler import UARTHandler, UARTDataLogger

# Configure UART
uart_config = {
    'port': 'COM3',
    'baud_rate': 115200,
    'data_bits': 8,
    'parity': 'N',
    'stop_bits': 1,
    'timeout': 1.0,
    'buffer_size': 1024
}

# Create handler and logger
uart_handler = UARTHandler(uart_config)
uart_handler.connect()
uart_logger = UARTDataLogger(uart_handler, "stm32_logs.log")

# Start logging
uart_handler.start_logging()
time.sleep(30)  # Log for 30 seconds
uart_handler.stop_logging()

# Get captured data
log_data = uart_logger.get_log_data()
print(f"Captured {len(log_data)} data points")
```

### Example 2: Pattern Validation
```python
from libs.pattern_validator import PatternValidator

# Create pattern validator
validator = PatternValidator()

# Define pattern to validate
pattern = {
    'name': 'numeric_output',
    'pattern': '^(\\d+)\\r\\n$',
    'pattern_type': 'regex',
    'timeout': 5.0,
    'required': True,
    'expected': ['5']
}

# Validate pattern
result = validator.wait_for_pattern_in_stream(uart_handler, pattern, 5.0)
if result and result.success:
    print("✅ Pattern validated successfully!")
    print(f"Extracted: {result.extracted_values}")
```

### Example 3: Log Analysis
```python
from libs.log_parser import LogParser

# Create log parser
parser = LogParser("./output/logs")

# Analyze logs
analysis = parser.analyze_logs()
parser.print_summary()

# Generate reports
json_report = parser.generate_report_from_logs()
csv_report = parser.export_to_csv()
```

## Hardware Setup

### Required Hardware
1. **STM32 Nucleo-F070RB Board**
2. **USB Cable** (for UART communication)
3. **Power Supply** (optional, for power cycling tests)
4. **Computer** with available COM port

### Connection Steps
1. Connect STM32 board to computer via USB
2. Identify COM port (usually COM3, COM4, etc.)
3. Ensure STM32 project is running and outputting data
4. Run test script with correct COM port

### COM Port Identification
- **Windows**: Device Manager → Ports (COM & LPT)
- **Linux**: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`
- **macOS**: `ls /dev/cu.usbmodem*`

## Troubleshooting

### Common Issues

1. **COM Port Not Found**
   - Check USB connection
   - Verify STM32 board is powered
   - Check Device Manager for COM port

2. **No Data Received**
   - Verify STM32 project is running
   - Check baud rate (115200)
   - Verify UART configuration

3. **Permission Denied**
   - Run as administrator (Windows)
   - Add user to dialout group (Linux): `sudo usermod -a -G dialout $USER`

4. **Pattern Validation Fails**
   - Check expected pattern format
   - Verify STM32 output format
   - Increase timeout value

### Debug Tips

1. **Enable Debug Logging**
   ```bash
   python stm32_log_capture_test.py --log-level DEBUG
   ```

2. **Test UART Connection**
   ```python
   # Simple connection test
   uart_handler = UARTHandler({'port': 'COM3', 'baud_rate': 115200})
   if uart_handler.connect():
       print("✅ UART connected successfully")
   else:
       print("❌ UART connection failed")
   ```

3. **Check Raw Data**
   ```python
   # Capture raw data without validation
   uart_handler.start_logging()
   time.sleep(5)
   raw_data = uart_handler.get_received_data()
   print(f"Raw data: {raw_data}")
   ```

## Output Files

### Log Files
- **Location**: `./output/logs/`
- **Format**: Timestamped log files
- **Content**: UART data, test events, validation results

### Report Files
- **Location**: `./output/reports/`
- **Formats**: JSON, CSV, HTML, Text
- **Content**: Test summaries, cycle results, pattern validations

### Example Output Structure
```
output/
├── logs/
│   ├── uart_data_0_20250101_120000.log
│   ├── test_logger_20250101_120000.log
│   └── comprehensive_logger_20250101_120000.log
└── reports/
    ├── STM32_Numeric_Output_Test_20250101_120000.json
    ├── STM32_Numeric_Output_Test_20250101_120000.csv
    └── STM32_Numeric_Output_Test_20250101_120000.html
```

## Advanced Usage

### Custom Patterns
```python
# Define custom validation patterns
custom_patterns = [
    {
        "regex": "^(\\d+)\\r\\n$",
        "expected": ["5"],
        "description": "Numeric output validation"
    },
    {
        "regex": "ERROR|Error|error",
        "expected": [],
        "description": "Error detection"
    }
]
```

### Power Cycling (if power supply available)
```python
# Configure power supply
power_config = {
    "resource": "GPIB0::5::INSTR",  # Adjust for your power supply
    "voltage": 3.3,
    "current_limit": 0.5
}
```

### Multiple UART Ports
```python
# Configure multiple UART loggers
uart_loggers = [
    {"port": "COM3", "baud": 115200, "display": True},
    {"port": "COM4", "baud": 115200, "display": False}
]
```

## Integration with Main Framework

The STM32 log capture functionality integrates seamlessly with the main test framework:

```bash
# Use STM32 configuration with main framework
python main.py -c config/stm32_log_capture_config.json

# Use STM32 templates
python main.py --list-templates
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main framework documentation
3. Examine the example scripts
4. Check log files for detailed error information

## Version History

- **v1.0**: Initial STM32 log capture implementation
- **v1.1**: Added multiple test types and examples
- **v1.2**: Enhanced pattern validation and reporting


