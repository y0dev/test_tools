# Project Structure

## Overview

The Automated Power Cycle and UART Validation Framework has been organized into a clean, logical structure that separates concerns and makes the project easy to navigate and maintain.

## Directory Structure

```
test_tool/
├── main.py                    # Main CLI entry point
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview and quick start
├── config/                    # Configuration files
│   ├── config.json           # Main configuration
│   ├── test_templates.json   # Test template definitions
│   └── example_multi_test_config.json # Example configuration
├── libs/                      # Core framework modules
│   ├── comprehensive_logger.py # Multi-file logging system
│   ├── log_parser.py         # Log file analysis
│   ├── pattern_validator.py  # UART pattern validation
│   ├── power_supply.py      # Power supply control
│   ├── report_generator.py   # Report generation
│   ├── test_logger.py       # Test data logging
│   ├── test_runner.py       # Main test orchestrator
│   ├── test_template_loader.py # Template system
│   └── uart_handler.py      # UART communication
├── examples/                 # Example scripts and demos
│   ├── template_demo.py     # Template system demonstration
│   ├── log_parsing_demo.py  # Log parsing demonstration
│   ├── test_new_config.py   # New configuration format demo
│   └── example_demo.py      # General framework demo
├── docs/                     # Documentation
│   ├── README.md            # Detailed documentation
│   ├── project_overview.md  # Architecture and design
│   ├── configuration_guide.md # Configuration reference
│   └── usage_guide.md       # Usage instructions
├── scripts/                  # Utility scripts
│   ├── setup.py            # Quick setup script
│   └── cleanup.py          # Cleanup script
└── output/                   # Generated output (created at runtime)
    ├── logs/                # Log files
    └── reports/             # Test reports
```

## File Descriptions

### Root Level
- **`main.py`** - Main CLI entry point with all command-line interface functionality
- **`requirements.txt`** - Python package dependencies
- **`README.md`** - Project overview, quick start guide, and basic usage

### Configuration (`config/`)
- **`config.json`** - Main configuration file with hardware settings and test references
- **`test_templates.json`** - Test template definitions with reusable test patterns
- **`example_multi_test_config.json`** - Example configuration showing multiple tests

### Core Framework (`libs/`)
- **`test_runner.py`** - Main orchestrator that coordinates all testing activities
- **`power_supply.py`** - Power supply control via GPIB/RS232 with factory pattern
- **`uart_handler.py`** - UART communication and data logging
- **`pattern_validator.py`** - UART data pattern validation using regex
- **`test_logger.py`** - Test data logging and session management
- **`report_generator.py`** - Report generation in multiple formats (JSON, CSV, HTML, text)
- **`test_template_loader.py`** - Test template system with resolution and validation
- **`comprehensive_logger.py`** - Multi-file logging system with detailed operation tracking
- **`log_parser.py`** - Log file analysis and historical data extraction

### Examples (`examples/`)
- **`template_demo.py`** - Demonstrates the template system functionality
- **`log_parsing_demo.py`** - Shows how to analyze existing log files
- **`test_new_config.py`** - Example of using the new configuration format
- **`example_demo.py`** - General framework demonstration

### Documentation (`docs/`)
- **`README.md`** - Comprehensive documentation with detailed explanations
- **`project_overview.md`** - Architecture, design principles, and component relationships
- **`configuration_guide.md`** - Complete configuration reference with examples
- **`usage_guide.md`** - Step-by-step usage instructions and best practices

### Utility Scripts (`scripts/`)
- **`setup.py`** - Quick setup script for new users
- **`cleanup.py`** - Cleanup script for old log files and reports

### Output (`output/`)
- **`logs/`** - Generated log files with timestamps
- **`reports/`** - Generated test reports and analysis

## Design Principles

### Separation of Concerns
- **Configuration** - All configuration files in `config/` directory
- **Core Logic** - All framework modules in `libs/` directory
- **Examples** - All demonstration code in `examples/` directory
- **Documentation** - All documentation in `docs/` directory
- **Utilities** - All utility scripts in `scripts/` directory

### Modularity
- Each module has a single responsibility
- Clear interfaces between components
- Easy to extend and modify

### Maintainability
- Logical file organization
- Clear naming conventions
- Comprehensive documentation
- Example code for reference

### Usability
- Simple CLI interface
- Clear project structure
- Quick setup scripts
- Comprehensive documentation

## Benefits of This Structure

1. **Easy Navigation** - Clear directory structure makes it easy to find files
2. **Separation of Concerns** - Different types of files are organized logically
3. **Maintainability** - Easy to update and modify individual components
4. **Documentation** - Comprehensive documentation in dedicated directory
5. **Examples** - Clear examples for users to learn from
6. **Utilities** - Helper scripts for common tasks
7. **Scalability** - Structure supports growth and new features
8. **Professional** - Clean, professional project organization

## Getting Started

1. **Quick Setup**: Run `python scripts/setup.py` to get started quickly
2. **Read Documentation**: Start with `README.md` and `docs/README.md`
3. **Run Examples**: Try the examples in `examples/` directory
4. **Customize**: Edit configuration files in `config/` directory
5. **Run Tests**: Use `python main.py --interactive` to run tests

This structure provides a clean, professional, and maintainable codebase that is easy to understand, use, and extend.
