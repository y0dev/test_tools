# Xilinx Tools Comprehensive Guide

This guide covers the complete Xilinx tools integration including JTAG operations, bootgen functionality, and Vivado project management. The framework provides Python interfaces for anxsct, xsdb, bootgen, and Vivado operations.

## Features

- **Multiple Tool Path Management**: Support for multiple Xilinx tool versions and paths
- **Bootgen Integration**: Generate boot.bin files using Xilinx bootgen tool
- **Vivado Project Management**: Bitstream generation and ELF file association
- **JTAG Operations**: Device detection, reset, programming, memory access
- **Configuration Management**: Flexible configuration system with templates
- **Comprehensive Logging**: Detailed logging of all operations
- **Error Handling**: Robust error handling and recovery

## Prerequisites

### Software Requirements
- Xilinx Vitis or Vivado installed
- anxsct, xsdb, bootgen, and vivado executables in PATH or configured paths
- Python 3.7 or higher

### Hardware Requirements
- Xilinx FPGA or SoC device
- JTAG programmer/debugger (e.g., Xilinx Platform Cable USB II)

## Installation

1. Ensure Xilinx tools are installed and in your PATH
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Basic Tool Management

```python
from libs.xilinx_tools_manager import XilinxToolsManager, XilinxToolsConfig

# Create configuration with multiple tool paths
config = XilinxToolsConfig(
    tool_paths={
        "anxsct": [
            "C:\\Xilinx\\Vitis\\2023.2\\bin\\anxsct.exe",
            "C:\\Xilinx\\Vitis\\2023.1\\bin\\anxsct.exe",
            "anxsct"
        ],
        "bootgen": [
            "C:\\Xilinx\\Vitis\\2023.2\\bin\\bootgen.exe",
            "bootgen"
        ],
        "vivado": [
            "C:\\Xilinx\\Vivado\\2023.2\\bin\\vivado.exe",
            "vivado"
        ]
    }
)

# Create tools manager
manager = XilinxToolsManager(config)

# Resolve tool paths
manager.resolve_tool_paths()

# Initialize tools
manager.initialize_jtag_interface()
manager.initialize_bootgen()
```

### Bootgen Operations

```python
# Generate boot image
bootgen_config = {
    "output_file": "boot.bin",
    "boot_mode": "sd",
    "arch": "zynqmp",
    "components": [
        {
            "name": "fsbl",
            "type": "fsbl",
            "file_path": "./boot_images/fsbl.elf"
        },
        {
            "name": "bitstream",
            "type": "bitstream",
            "file_path": "./bitstreams/design.bit"
        }
    ]
}

success = manager.generate_boot_image(bootgen_config)
```

### Vivado Operations

```python
# Add Vivado project
manager.add_vivado_project(
    "my_project",
    "./projects/my_project.xpr",
    "ps7_cortexa9_0"
)

# Generate bitstream
bitstream_path = manager.generate_vivado_bitstream("my_project")

# Associate ELF file
manager.associate_elf_with_project("my_project", "./boot_images/fsbl.elf")
```

### JTAG Operations

```python
# Run JTAG operations
operations = [
    {"type": "scan", "description": "Scan for devices"},
    {"type": "reset", "device_index": 0, "description": "Reset device"},
    {"type": "program", "device_index": 0, "bitstream_path": "design.bit"}
]

results = manager.run_jtag_operations(operations)
```

## Configuration

### Tool Paths Configuration

```json
{
  "xilinx_tools": {
    "tool_paths": {
      "anxsct": [
        "C:\\Xilinx\\Vitis\\2023.2\\bin\\anxsct.exe",
        "C:\\Xilinx\\Vitis\\2023.1\\bin\\anxsct.exe",
        "anxsct"
      ],
      "xsdb": [
        "C:\\Xilinx\\Vitis\\2023.2\\bin\\xsdb.exe",
        "C:\\Xilinx\\SDK\\2019.1\\bin\\xsdb.exe",
        "xsdb"
      ],
      "bootgen": [
        "C:\\Xilinx\\Vitis\\2023.2\\bin\\bootgen.exe",
        "C:\\Xilinx\\SDK\\2019.1\\bin\\bootgen.exe",
        "bootgen"
      ],
      "vivado": [
        "C:\\Xilinx\\Vivado\\2023.2\\bin\\vivado.exe",
        "C:\\Xilinx\\Vivado\\2023.1\\bin\\vivado.exe",
        "vivado"
      ]
    },
    "default_tool": "anxsct",
    "auto_detect_paths": true,
    "preferred_version": "2023.2"
  }
}
```

### Bootgen Configuration

```json
{
  "bootgen_config": {
    "output_file": "boot.bin",
    "boot_mode": "sd",
    "arch": "zynqmp",
    "boot_device": "sd0",
    "verbose": true,
    "components": [
      {
        "name": "fsbl",
        "type": "fsbl",
        "file_path": "./boot_images/fsbl.elf"
      },
      {
        "name": "bitstream",
        "type": "bitstream",
        "file_path": "./bitstreams/design.bit"
      },
      {
        "name": "pmufw",
        "type": "pmufw",
        "file_path": "./boot_images/pmufw.elf"
      },
      {
        "name": "atf",
        "type": "atf",
        "file_path": "./boot_images/bl31.elf"
      },
      {
        "name": "uboot",
        "type": "uboot",
        "file_path": "./boot_images/u-boot.elf"
      }
    ]
  }
}
```

### Vivado Projects Configuration

```json
{
  "vivado_projects": [
    {
      "name": "example_project",
      "project_path": "./projects/example_project.xpr",
      "target_cpu": "ps7_cortexa9_0",
      "bitstream_output_dir": "./bitstreams"
    }
  ]
}
```

## Bootgen Templates

The framework includes pre-configured bootgen templates for common scenarios:

### Zynq-7000 FSBL Boot Image
```json
{
  "zynq_fsbl": {
    "description": "Simple Zynq-7000 FSBL boot image",
    "output_file": "zynq_fsbl_boot.bin",
    "boot_mode": "sd",
    "arch": "zynq",
    "components": [
      {"name": "fsbl", "type": "fsbl", "file_path": "./boot_images/fsbl.elf"},
      {"name": "bitstream", "type": "bitstream", "file_path": "./bitstreams/zynq_design.bit"}
    ]
  }
}
```

### Complete ZynqMP Boot Image
```json
{
  "zynqmp_complete": {
    "description": "Complete ZynqMP boot image with all components",
    "output_file": "zynqmp_complete_boot.bin",
    "boot_mode": "sd",
    "arch": "zynqmp",
    "components": [
      {"name": "fsbl", "type": "fsbl", "file_path": "./boot_images/fsbl.elf"},
      {"name": "pmufw", "type": "pmufw", "file_path": "./boot_images/pmufw.elf"},
      {"name": "bitstream", "type": "bitstream", "file_path": "./bitstreams/zynqmp_design.bit"},
      {"name": "atf", "type": "atf", "file_path": "./boot_images/bl31.elf"},
      {"name": "uboot", "type": "uboot", "file_path": "./boot_images/u-boot.elf"}
    ]
  }
}
```

## Examples

### Comprehensive Demo
```bash
python examples/xilinx_tools_comprehensive_demo.py --config config/xilinx_tools_config.json
```

### Specific Operations
```bash
# Tool path resolution demo
python examples/xilinx_tools_comprehensive_demo.py --demo paths

# Bootgen operations demo
python examples/xilinx_tools_comprehensive_demo.py --demo bootgen

# Vivado operations demo
python examples/xilinx_tools_comprehensive_demo.py --demo vivado

# JTAG operations demo
python examples/xilinx_tools_comprehensive_demo.py --demo jtag
```

## Menu System Integration

The enhanced functionality is integrated into the main menu system:

1. Run `python main.py`
2. Select "4. JTAG Operations"
3. Choose from available operations:
   - Run JTAG Test
   - JTAG Device Detection
   - Generate Boot Image
   - Vivado Operations
   - JTAG Demo
   - Generate JTAG Config

### Vivado Operations Submenu
- Generate Bitstream
- Associate ELF File
- Add Project
- List Projects

## API Reference

### XilinxToolsManager

Main class for managing all Xilinx tools.

#### Methods

- `resolve_tool_paths()`: Resolve all configured tool paths
- `initialize_jtag_interface(jtag_config)`: Initialize JTAG interface
- `initialize_bootgen(bootgen_config)`: Initialize bootgen
- `add_vivado_project(name, path, target_cpu)`: Add Vivado project
- `generate_boot_image(config_dict)`: Generate boot image
- `generate_vivado_bitstream(project_name)`: Generate bitstream
- `associate_elf_with_project(project_name, elf_path)`: Associate ELF file
- `run_jtag_operations(operations)`: Run JTAG operations
- `get_status()`: Get status of all tools
- `cleanup()`: Cleanup all tool instances

### XilinxBootgen

Class for bootgen operations.

#### Methods

- `generate_boot_image()`: Generate boot image
- `create_fsbl_boot_image(fsbl_path, bitstream_path)`: Create FSBL boot image
- `create_zynqmp_boot_image(fsbl_path, pmufw_path, bitstream_path, atf_path, uboot_path)`: Create ZynqMP boot image

### VivadoProjectManager

Class for Vivado project operations.

#### Methods

- `generate_bitstream(output_dir)`: Generate bitstream
- `associate_elf_file(elf_path, target_cpu)`: Associate ELF file

## File Structure

```
libs/
├── xilinx_jtag.py              # JTAG interface library
├── xilinx_bootgen.py           # Bootgen utility library
├── xilinx_tools_manager.py     # Centralized tools manager
├── jtag_test_runner.py         # JTAG-enabled test runner
config/
├── xilinx_jtag_config.json     # JTAG configuration
├── bootgen_templates.json       # Bootgen templates
examples/
├── xilinx_jtag_demo.py          # JTAG functionality demos
├── xilinx_tools_comprehensive_demo.py # Comprehensive demo
scripts/
├── jtag_integration_demo.py     # Integration demonstration
docs/
├── xilinx_jtag_guide.md         # Original JTAG guide
├── xilinx_tools_comprehensive_guide.md # This comprehensive guide
```

## Troubleshooting

### Common Issues

1. **Tool Executable Not Found**
   - Ensure Xilinx tools are installed
   - Check PATH environment variable
   - Configure tool paths in configuration file
   - Use absolute paths for tool executables

2. **Bootgen Generation Fails**
   - Verify all component files exist
   - Check file paths in configuration
   - Ensure bootgen is in PATH or configured
   - Check bootgen syntax and component types

3. **Vivado Operations Fail**
   - Verify Vivado project file exists
   - Check Vivado installation
   - Ensure project is properly configured
   - Check target CPU name

4. **JTAG Connection Issues**
   - Check JTAG cable connection
   - Verify device power
   - Check device configuration
   - Ensure anxsct/xsdb is available

### Debug Mode

Enable verbose logging for detailed debugging:

```python
config = XilinxToolsConfig(verbose_logging=True)
```

## Contributing

When adding new functionality:

1. Add new tool paths to configuration schema
2. Update XilinxToolsManager with new methods
3. Add configuration templates
4. Create examples and demos
5. Update documentation

## License

This library is part of the Automated Test Framework and follows the same license terms.
