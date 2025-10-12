# Xilinx JTAG Interface Library

This library provides a Python interface for connecting to and controlling Xilinx devices through JTAG using anxsct (AMD Xilinx System Control Tool) or xsdb (Xilinx Software Debugger) console interfaces.

## Features

- **Automatic Device Detection**: Scan and enumerate JTAG devices
- **Connection Management**: Handle anxsct/xsdb console connections
- **Common Operations**: Reset, program, debug, memory access
- **Integration**: Seamless integration with existing test framework
- **Comprehensive Logging**: Detailed logging of all JTAG operations
- **Error Handling**: Robust error handling and recovery

## Prerequisites

### Software Requirements
- Xilinx Vitis or Vivado installed
- anxsct or xsdb executable in PATH
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

### Basic Usage

```python
from libs.xilinx_jtag import XilinxJTAGInterface, JTAGConfig, JTAGInterface

# Create configuration
config = JTAGConfig(
    interface=JTAGInterface.ANXSCT,
    verbose_logging=True
)

# Connect and scan devices
with XilinxJTAGInterface(config) as jtag:
    devices = jtag.scan_devices()
    
    for device in devices:
        print(f"Device {device.index}: {device.name}")
        
        # Reset device
        jtag.reset_device(device.index)
        
        # Program bitstream
        jtag.program_device(device.index, "path/to/bitstream.bit")
```

### Integration with Test Framework

```python
from libs.jtag_test_runner import JTAGTestRunner

# Create test runner
runner = JTAGTestRunner("config/jtag_test_config.json")

# Initialize and run test
runner.initialize_components()
results = runner.run_jtag_test()
runner.cleanup_components()
```

## Configuration

### JTAG Configuration

Create a configuration file with JTAG settings:

```json
{
  "jtag": {
    "interface": "anxsct",
    "executable_path": null,
    "connection_timeout": 30,
    "command_timeout": 10,
    "auto_connect": true,
    "verbose_logging": false
  },
  "jtag_operations": [
    {
      "type": "reset",
      "device_index": 0,
      "description": "Reset device before power cycle"
    },
    {
      "type": "program",
      "device_index": 0,
      "bitstream_path": "./bitstreams/design.bit"
    }
  ]
}
```

### Supported Operations

- **reset**: Reset the target device
- **program**: Program bitstream to device
- **read_memory**: Read memory from device
- **write_memory**: Write memory to device
- **get_status**: Get device status

## Examples

### Device Detection Demo

```bash
python examples/xilinx_jtag_demo.py --test detection
```

### Comprehensive Test

```bash
python examples/xilinx_jtag_demo.py --test all
```

### Integration Demo

```bash
python scripts/jtag_integration_demo.py --create-config
python scripts/jtag_integration_demo.py --config config/jtag_integration_config.json
```

## Menu System Integration

The JTAG functionality is integrated into the main menu system:

1. Run `python main.py`
2. Select "4. JTAG Operations"
3. Choose from available JTAG operations:
   - Run JTAG Test
   - JTAG Device Detection
   - JTAG Demo
   - Generate JTAG Config

## API Reference

### XilinxJTAGInterface

Main class for JTAG operations.

#### Methods

- `connect()`: Connect to JTAG console
- `disconnect()`: Disconnect from JTAG console
- `scan_devices()`: Scan for available devices
- `reset_device(device_index)`: Reset a device
- `program_device(device_index, bitstream_path)`: Program a device
- `read_memory(device_index, address, size)`: Read memory
- `write_memory(device_index, address, data)`: Write memory
- `get_device_status(device_index)`: Get device status

### JTAGTestRunner

Extended test runner with JTAG support.

#### Methods

- `initialize_jtag_components()`: Initialize JTAG components
- `run_jtag_test()`: Run comprehensive JTAG test
- `execute_jtag_operations(cycle)`: Execute JTAG operations for a cycle

## Troubleshooting

### Common Issues

1. **Executable Not Found**
   - Ensure Xilinx tools are installed
   - Check PATH environment variable
   - Specify executable path in configuration

2. **No Devices Found**
   - Check JTAG cable connection
   - Verify device power
   - Check device configuration

3. **Connection Timeout**
   - Increase connection_timeout in configuration
   - Check JTAG cable functionality
   - Verify device is responsive

### Debug Mode

Enable verbose logging for detailed debugging:

```python
config = JTAGConfig(verbose_logging=True)
```

## File Structure

```
libs/
├── xilinx_jtag.py          # Main JTAG interface library
├── jtag_test_runner.py     # JTAG-enabled test runner
config/
├── xilinx_jtag_config.json # JTAG configuration template
examples/
├── xilinx_jtag_demo.py     # JTAG functionality demos
scripts/
├── jtag_integration_demo.py # Integration demonstration
```

## Contributing

When adding new JTAG operations:

1. Add operation type to `_execute_jtag_operation()`
2. Update configuration schema
3. Add tests and examples
4. Update documentation

## License

This library is part of the Automated Test Framework and follows the same license terms.
