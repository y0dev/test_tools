# Project Overview

## Architecture

The Automated Power Cycle and UART Validation Framework is designed with a modular architecture that separates concerns and provides flexibility for different testing scenarios.

### Core Components

1. **TestRunner** (`libs/test_runner.py`) - Main orchestrator that coordinates all testing activities
2. **PowerSupply** (`libs/power_supply.py`) - Handles power supply control via GPIB/RS232
3. **UARTHandler** (`libs/uart_handler.py`) - Manages UART communication and data logging
4. **PatternValidator** (`libs/pattern_validator.py`) - Validates UART data against expected patterns
5. **TestLogger** (`libs/test_logger.py`) - Logs test data and results
6. **ReportGenerator** (`libs/report_generator.py`) - Generates reports in multiple formats
7. **TestTemplateLoader** (`libs/test_template_loader.py`) - Manages test template system
8. **ComprehensiveLogger** (`libs/comprehensive_logger.py`) - Multi-file logging system
9. **LogParser** (`libs/log_parser.py`) - Analyzes existing log files

### Data Flow

```
Configuration Files → TestRunner → PowerSupply/UARTHandler → PatternValidator → TestLogger → ReportGenerator
```

### Configuration System

The framework uses a two-tier configuration system:

1. **Main Configuration** (`config/config.json`) - Hardware settings and test references
2. **Test Templates** (`config/test_templates.json`) - Reusable test definitions with defaults

This separation allows for:
- Clean, minimal main configuration
- Reusable test definitions
- Easy maintenance and updates
- Flexible test customization

### Logging System

The comprehensive logging system creates multiple specialized log files:

- **Main Log** - Application-level events and errors
- **Power Supply Log** - All power supply operations and measurements
- **UART Log** - Serial communication and data capture
- **Test Execution Log** - Test cycle details and validation results
- **Error Log** - Error conditions and exceptions

### Output Structure

All output is organized in the `output/` directory:

- `output/logs/` - Log files with timestamps
- `output/reports/` - Generated test reports and analysis

### Template System

The template system provides:

- **Default Values** - Common settings for all tests
- **Template Definitions** - Reusable test patterns and validations
- **Override Capability** - Per-test customization of parameters
- **Validation** - Template existence and parameter validation

### Extensibility

The framework is designed for extensibility:

- **New Power Supplies** - Add new power supply classes
- **New UART Protocols** - Extend UART handler for different protocols
- **New Validation Patterns** - Add custom pattern validation logic
- **New Report Formats** - Implement additional report generators
- **New Test Types** - Create new test templates and patterns

## Design Principles

1. **Separation of Concerns** - Each component has a single responsibility
2. **Configuration-Driven** - Behavior controlled by configuration files
3. **Comprehensive Logging** - All operations are logged for debugging and analysis
4. **Template Reusability** - Test definitions can be reused and customized
5. **Error Handling** - Graceful error handling with detailed logging
6. **Backward Compatibility** - New features don't break existing functionality
7. **CLI Interface** - Easy-to-use command-line interface for all operations
