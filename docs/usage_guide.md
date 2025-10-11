# Usage Guide

## Getting Started

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample configuration files
python main.py --generate-config
python main.py --generate-templates
```

### 2. Configuration

Edit the generated configuration files:

- `config/config.json` - Main configuration
- `config/test_templates.json` - Test templates

### 3. Run Tests

```bash
# Interactive mode (recommended for beginners)
python main.py --interactive

# Non-interactive mode
python main.py
```

## Command Line Interface

### Configuration Management

#### Generate Sample Files
```bash
# Generate sample configuration
python main.py --generate-config

# Generate sample templates
python main.py --generate-templates

# Generate both
python main.py --generate-config --generate-templates
```

#### List Available Options
```bash
# List available test templates
python main.py --list-templates

# List validation patterns
python main.py --list-patterns
```

#### Validate Configuration
```bash
# Validate default configuration
python main.py --validate-config

# Validate custom configuration
python main.py --validate-config --config config/my_config.json
```

### Test Execution

#### Interactive Mode
```bash
# Run tests with user prompts
python main.py --interactive

# Interactive mode with custom config
python main.py --interactive --config config/my_config.json
```

#### Non-Interactive Mode
```bash
# Run tests automatically
python main.py

# Run with custom configuration
python main.py --config config/my_config.json
```

#### Override Parameters
```bash
# Override number of cycles
python main.py --cycles 5

# Set logging level
python main.py --log-level DEBUG

# Set output directory
python main.py --output-dir ./custom_output
```

### Log Analysis

#### Parse Existing Logs
```bash
# Parse logs in default directory
python main.py --parse-logs

# Parse logs in custom directory
python main.py --parse-logs --log-dir ./custom_logs
```

## Test Execution Workflow

### 1. Pre-Test Setup

```bash
# Generate configuration files
python main.py --generate-config
python main.py --generate-templates

# Edit configuration files
# config/config.json - Hardware settings
# config/test_templates.json - Test definitions
```

### 2. Test Execution

```bash
# Run tests interactively
python main.py --interactive

# Review test configuration
# Confirm test parameters
# Start test execution
```

### 3. Post-Test Analysis

```bash
# Parse generated logs
python main.py --parse-logs

# Review reports in output/reports/
# Analyze test results
# Debug any failures
```

## Interactive Mode

Interactive mode provides a user-friendly interface for test execution:

### Configuration Display
- Shows test configuration
- Displays available templates
- Lists UART loggers
- Shows test parameters

### User Prompts
- Confirm test start
- Review test parameters
- Handle errors gracefully
- Provide progress updates

### Example Interactive Session
```
Test Configuration:
  Number of Tests: 2

Test 1: boot_data_test
  Description: Verify correct boot data is printed
  Cycles: 1
  Power On Duration: 5.0s
  Power Off Duration: 3.0s
  Output Format: json
  UART Patterns (2):
    - Pattern 1: Data:\s*(0x[0-9A-Fa-f]+)
    - Pattern 2: Version:\s*v(\d\.\d)

Test 2: power_cycle_test
  Description: Test multiple power cycles
  Cycles: 3
  Power On Duration: 3.0s
  Power Off Duration: 2.0s
  Output Format: csv
  UART Patterns (1):
    - Pattern 1: READY

UART Loggers (1):
  - Port: COM3, Baud: 115200

Available Test Templates (5):
  - boot_data_test
  - power_cycle_test
  - simple_ready_test
  - version_check_test
  - comprehensive_test

Start test? (y/n): y
```

## Log Analysis

### Understanding Log Files

The framework generates multiple log files:

- `main_[timestamp].log` - Application events
- `power_supply_[timestamp].log` - Power supply operations
- `uart_operations_[timestamp].log` - UART communication
- `test_execution_[timestamp].log` - Test execution details
- `errors_[timestamp].log` - Error conditions

### Log Analysis Commands

```bash
# Basic log analysis
python main.py --parse-logs

# Custom log directory
python main.py --parse-logs --log-dir ./custom_logs

# Generate reports
python main.py --parse-logs
# Generates: log_analysis_[timestamp].json and log_analysis_[timestamp].csv
```

### Log Analysis Output

```
LOG ANALYSIS SUMMARY
============================================================
Log Directory: ./output/logs
Test Sessions Found: 2
Total Cycles: 4
Successful Cycles: 3
Failed Cycles: 1
Success Rate: 75.00%
UART Data Entries: 156

Log Files Found:
  test_logs: 2 files
    - test_execution_2024-01-15_14-30-25.log
    - test_execution_2024-01-15_14-35-10.log
  uart_logs: 2 files
    - uart_operations_2024-01-15_14-30-25.log
    - uart_operations_2024-01-15_14-35-10.log

Test Sessions:
  Session 1: boot_data_test
    Cycles: 1 (Success: 1, Failed: 0)
    Duration: 0:00:08
  Session 2: power_cycle_test
    Cycles: 3 (Success: 2, Failed: 1)
    Duration: 0:00:15
```

## Troubleshooting

### Common Issues

#### Configuration Errors
```bash
# Validate configuration
python main.py --validate-config

# Check for missing templates
python main.py --list-templates
```

#### Hardware Connection Issues
```bash
# Check power supply connection
python main.py --log-level DEBUG

# Verify UART port availability
python main.py --interactive
```

#### Log Analysis Issues
```bash
# Check log directory exists
ls -la output/logs/

# Verify log file permissions
python main.py --parse-logs
```

### Debug Mode

```bash
# Enable debug logging
python main.py --log-level DEBUG

# Run with verbose output
python main.py --interactive --log-level DEBUG
```

### Error Handling

The framework provides comprehensive error handling:

- **Configuration Errors** - Detailed validation messages
- **Hardware Errors** - Connection and communication issues
- **Test Errors** - Pattern validation failures
- **Logging Errors** - File system and permission issues

## Advanced Usage

### Custom Test Templates

1. **Create Custom Template**
```json
{
  "my_custom_test": {
    "description": "Custom test description",
    "uart_patterns": [
      {
        "regex": "CustomPattern",
        "expected": ["ExpectedValue"]
      }
    ],
    "output_format": "json"
  }
}
```

2. **Use Custom Template**
```json
{
  "tests": [
    {
      "name": "my_custom_test",
      "cycles": 2
    }
  ]
}
```

### Multiple UART Loggers

```json
{
  "uart_loggers": [
    {
      "port": "COM3",
      "baud": 115200,
      "display": true
    },
    {
      "port": "COM4",
      "baud": 9600,
      "display": false
    }
  ]
}
```

### Custom Output Formats

```json
{
  "tests": [
    {
      "name": "my_test",
      "output_format": "comprehensive"  // All formats
    }
  ]
}
```

## Best Practices

1. **Start Simple** - Begin with basic templates and gradually add complexity
2. **Test Incrementally** - Test individual components before full integration
3. **Use Interactive Mode** - Interactive mode helps understand the system
4. **Monitor Logs** - Regularly check log files for issues
5. **Backup Configurations** - Keep working configuration backups
6. **Document Customizations** - Document any custom templates or modifications
7. **Version Control** - Track configuration changes in version control
8. **Regular Maintenance** - Clean up old log files periodically
