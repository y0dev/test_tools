# Automated Power Cycle and UART Validation Framework

A comprehensive Python framework for automated hardware testing, power cycling, and UART validation with configurable test templates and comprehensive logging.

## 🚀 Quick Start

```bash
# Generate sample configuration files
python main.py --generate-config
python main.py --generate-templates

# List available test templates
python main.py --list-templates

# Run tests interactively
python main.py --interactive

# Parse existing log files
python main.py --parse-logs
```

## 📁 Project Structure

```
test_tool/
├── main.py                    # Main CLI entry point
├── requirements.txt           # Python dependencies
├── config/                    # Configuration files
│   ├── config.json           # Main configuration
│   ├── test_templates.json   # Test template definitions
│   └── sample_config.json    # Sample configuration
├── lib/                      # Core framework modules
│   ├── comprehensive_logger.py # Multi-file logging system
│   ├── log_parser.py         # Log file analysis
│   ├── pattern_validator.py  # UART pattern validation
│   ├── power_supply.py      # Power supply control
│   ├── report_generator.py   # Report generation
│   ├── test_logger.py       # Test data logging
│   ├── test_runner.py       # Main test orchestrator
│   ├── test_template_loader.py # Template system
│   ├── uart_handler.py      # UART communication
│   └── exports/             # Export functionality
│       ├── __init__.py      # Export module initialization
│       ├── csv_exporter.py  # CSV export with easy-to-read formatting
│       ├── json_exporter.py # JSON export with structured data
│       └── html_exporter.py # HTML export with CSS/JS
├── examples/                 # Example scripts and demos
│   ├── template_demo.py     # Template system demo
│   ├── log_parsing_demo.py  # Log parsing demo
│   ├── test_new_config.py   # New config format demo
│   └── example_demo.py      # General demo
├── docs/                     # Documentation
│   └── README.md            # Detailed documentation
├── scripts/                  # Utility scripts (empty)
└── output/                   # Generated output (created at runtime)
    ├── logs/                 # Log files
    └── reports/              # Test reports
```

## 🛠️ Features

- **Automated Power Cycling** - Control Keysight E3632A power supply via GPIB/RS232
- **UART Validation** - Log and validate serial data patterns
- **Test Templates** - Reusable test definitions with defaults
- **Comprehensive Logging** - Multi-file logging system with detailed operation tracking
- **Log Analysis** - Parse existing log files without running tests
- **Multiple Output Formats** - JSON, CSV, HTML, and text reports with professional styling
- **Export System** - Dedicated export classes for CSV, JSON, and HTML with embedded CSS/JS
- **Interactive Mode** - User-friendly test execution
- **Template System** - Clean configuration with reusable test definitions

## 📋 Configuration

### Main Configuration (`config/config.json`)
```json
{
  "power_supply": {
    "resource": "GPIB0::5::INSTR",
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
      "name": "boot_data_test"  // References template
    }
  ]
}
```

### Test Templates (`config/test_templates.json`)
```json
{
  "test_templates": {
    "boot_data_test": {
      "description": "Verify correct boot data is printed",
      "uart_patterns": [
        {
          "regex": "Data:\\s*(0x[0-9A-Fa-f]+)",
          "expected": ["0x12345678"]
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
  }
}
```

## 🎮 CLI Commands

### Configuration Management
```bash
python main.py --generate-config      # Generate sample config
python main.py --generate-templates   # Generate sample templates
python main.py --list-templates       # List available templates
python main.py --validate-config     # Validate configuration
```

### Test Execution
```bash
python main.py --interactive          # Interactive test mode
python main.py --log-level DEBUG     # Set logging level
python main.py --cycles 5            # Override cycle count
```

### Log Analysis
```bash
python main.py --parse-logs           # Parse existing logs
python main.py --parse-logs --log-dir ./custom/logs  # Custom log directory
```

## 📊 Output Structure

### Log Files (`output/logs/`)
- `main_[timestamp].log` - Main application logs
- `power_supply_[timestamp].log` - Power supply operations
- `uart_operations_[timestamp].log` - UART operations
- `test_execution_[timestamp].log` - Test execution details
- `errors_[timestamp].log` - Error logs only

### Reports (`output/reports/`)
- `test_results_[timestamp].json` - Test results in JSON format
- `test_results_[timestamp].csv` - Test results in CSV format with easy-to-read formatting
- `test_results_[timestamp].html` - Interactive HTML reports with embedded CSS and JavaScript
- `log_analysis_[timestamp].json` - Log analysis results
- `log_analysis_[timestamp].csv` - Log analysis in CSV format

## 🔧 Hardware Requirements

- **Power Supply**: Keysight E3632A (or compatible SCPI power supply)
- **Connection**: GPIB or RS232
- **UART**: Serial port for device communication
- **Python**: 3.7+ with required packages

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample configuration
python main.py --generate-config
python main.py --generate-templates

# Edit configuration files
# config/config.json - Main configuration
# config/test_templates.json - Test templates
```

## 🚀 Usage Examples

### Basic Test Execution
```bash
# Run with default configuration
python main.py --interactive

# Run with custom configuration
python main.py --config config/my_config.json --interactive
```

### Log Analysis
```bash
# Analyze existing logs
python main.py --parse-logs

# Generate reports from logs
python main.py --parse-logs --log-dir ./output/logs
```

### Template Management
```bash
# List available templates
python main.py --list-templates

# Generate new template file
python main.py --generate-templates
```

## 📊 Export System

The framework includes a comprehensive export system with dedicated classes for different output formats:

### CSV Export (`lib/exports/csv_exporter.py`)
- Easy-to-read formatting with proper headers and sections
- Comprehensive test results with cycle data, UART data, and validation results
- Simple data export for custom datasets
- Cycle analysis export with detailed statistics

### JSON Export (`lib/exports/json_exporter.py`)
- Structured data organization with metadata
- Comprehensive statistics and analysis
- Configuration export capabilities
- Human-readable formatting with proper indentation

### HTML Export (`lib/exports/html_exporter.py`)
- Professional styling with embedded CSS
- Interactive features with embedded JavaScript
- Responsive design for different screen sizes
- Data visualization with charts and graphs
- Collapsible sections for better organization
- Print-friendly styling

### Usage Example
```python
from lib.exports import CSVExporter, JSONExporter, HTMLExporter

# Create exporters
csv_exporter = CSVExporter()
json_exporter = JSONExporter()
html_exporter = HTMLExporter()

# Export test results
csv_file = csv_exporter.export_test_results(test_summary, cycle_data)
json_file = json_exporter.export_test_results(test_summary, cycle_data)
html_file = html_exporter.export_test_results(test_summary, cycle_data)
```

## 📚 Documentation

- **Detailed Documentation**: See `docs/README.md` for comprehensive documentation
- **Examples**: Check `examples/` directory for usage examples
- **Configuration**: See `config/` directory for sample configurations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.