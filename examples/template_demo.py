#!/usr/bin/env python3
"""
Example demonstrating the new test template system.
This shows how to use template names instead of full test configurations.
"""

import json
from pathlib import Path

def demonstrate_template_system():
    """Demonstrate the template system functionality."""
    print("=" * 60)
    print("Test Template System Demonstration")
    print("=" * 60)
    
    # Show the simplified config.json
    print("\n1. Simplified config.json:")
    print("-" * 30)
    
    simple_config = {
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
        "tests": [
            {
                "name": "boot_data_test"  # Just the template name!
            },
            {
                "name": "power_cycle_test",
                "cycles": 3,  # Override default cycles
                "on_time": 3,  # Override default on_time
                "off_time": 2  # Override default off_time
            },
            {
                "name": "simple_ready_test",
                "cycles": 2  # Override default cycles
            }
        ]
    }
    
    print(json.dumps(simple_config, indent=2))
    
    # Show the test_templates.json
    print("\n2. test_templates.json:")
    print("-" * 30)
    
    templates_config = {
        "test_templates": {
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
            },
            "power_cycle_test": {
                "description": "Test multiple power cycles",
                "uart_patterns": [
                    {
                        "regex": "READY",
                        "expected": ["READY"]
                    }
                ],
                "output_format": "csv"
            },
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
        },
        "defaults": {
            "cycles": 1,
            "on_time": 5,
            "off_time": 3,
            "output_format": "json"
        }
    }
    
    print(json.dumps(templates_config, indent=2))
    
    # Show how templates are resolved
    print("\n3. Template Resolution Process:")
    print("-" * 30)
    
    print("For test: {\"name\": \"boot_data_test\"}")
    print("1. Load template 'boot_data_test' from test_templates.json")
    print("2. Apply defaults: cycles=1, on_time=5, off_time=3, output_format=json")
    print("3. Apply template: description, uart_patterns, output_format=json")
    print("4. Apply overrides: (none in this case)")
    print("5. Final resolved config:")
    
    resolved_config = {
        "name": "boot_data_test",
        "description": "Verify correct boot data is printed",
        "cycles": 1,
        "on_time": 5,
        "off_time": 3,
        "output_format": "json",
        "uart_patterns": [
            {
                "regex": "Data:\\s*(0x[0-9A-Fa-f]+),\\s*(0x[0-9A-Fa-f]+)",
                "expected": [["0x12345678", "0xDEADBEEF"]]
            },
            {
                "regex": "Version:\\s*v(\\d\\.\\d)",
                "expected": ["v1.2"]
            }
        ]
    }
    
    print(json.dumps(resolved_config, indent=2))
    
    print("\nFor test: {\"name\": \"power_cycle_test\", \"cycles\": 3, \"on_time\": 3, \"off_time\": 2}")
    print("1. Load template 'power_cycle_test'")
    print("2. Apply defaults: cycles=1, on_time=5, off_time=3, output_format=json")
    print("3. Apply template: description, uart_patterns, output_format=csv")
    print("4. Apply overrides: cycles=3, on_time=3, off_time=2")
    print("5. Final resolved config:")
    
    resolved_config2 = {
        "name": "power_cycle_test",
        "description": "Test multiple power cycles",
        "cycles": 3,  # Overridden
        "on_time": 3,  # Overridden
        "off_time": 2,  # Overridden
        "output_format": "csv",  # From template
        "uart_patterns": [
            {
                "regex": "READY",
                "expected": ["READY"]
            }
        ]
    }
    
    print(json.dumps(resolved_config2, indent=2))
    
    # Show benefits
    print("\n4. Benefits of Template System:")
    print("-" * 30)
    print("✅ Cleaner config.json - just template names and overrides")
    print("✅ Reusable test definitions - define once, use many times")
    print("✅ Default values - set common defaults for all tests")
    print("✅ Easy maintenance - update template, affects all tests using it")
    print("✅ Flexible overrides - customize specific tests as needed")
    print("✅ Better organization - separate test logic from test execution")
    
    # Show CLI commands
    print("\n5. New CLI Commands:")
    print("-" * 30)
    print("python main.py --list-templates     # List available templates")
    print("python main.py --generate-templates # Generate sample templates")
    print("python main.py --generate-config    # Generate sample config")
    print("python main.py --interactive        # Run tests interactively")


if __name__ == "__main__":
    demonstrate_template_system()
