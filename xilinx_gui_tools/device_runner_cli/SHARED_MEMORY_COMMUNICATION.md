# Shared Memory Communication System

## Overview
This system implements a shared memory communication protocol between the TCL script (`device_runner_cli.tcl`) and the C application (`jtag_uart_handler.c`) using a 4KB shared memory region at address `0x10000000`.

## Files Created/Modified

### 1. `messages.tcl` (New)
- **Purpose**: Defines the shared memory communication protocol
- **Key Features**:
  - Message structure with header and data sections
  - Magic number validation (0xDEADBEEF)
  - Message types for different commands
  - Status codes for responses
  - Functions for reading/writing shared memory
  - Command functions for each operation type

### 2. `jtag_uart_handler.c` (Modified)
- **Added**: Complete shared memory communication support
- **Key Features**:
  - Shared memory definitions and constants
  - Message processing functions
  - Command handlers for all message types
  - Integration with existing menu system
  - Automatic shared memory initialization

### 3. `device_runner_cli.tcl` (Modified)
- **Added**: Shared memory communication integration
- **Key Features**:
  - Automatic loading of `messages.tcl`
  - Enhanced command functions using shared memory
  - Fallback to legacy register-based communication
  - Test function for validation
  - Integration with existing script mode

## Shared Memory Layout

```
Address Range: 0x10000000 - 0x10000FFF (4KB)

Offset  Size    Field           Description
------  ----    -----           -----------
0x00    4       Magic           Magic number (0xDEADBEEF)
0x04    4       Type            Message type
0x08    4       Length          Data length
0x0C    4       Status          Status/Response code
0x10    4080    Data            Message data (up to 4080 bytes)
```

## Message Types

| Type | Value | Description |
|------|-------|-------------|
| MSG_TYPE_INIT | 1 | Initialize application |
| MSG_TYPE_RUN_APP | 2 | Run application |
| MSG_TYPE_SET_PARAM | 3 | Set parameter |
| MSG_TYPE_GET_STATUS | 4 | Get status |
| MSG_TYPE_CAPTURE_RAM | 5 | Capture RAM |
| MSG_TYPE_SET_CONFIG | 6 | Set configuration |
| MSG_TYPE_GET_CONFIG | 7 | Get configuration |
| MSG_TYPE_EXIT | 8 | Exit application |
| MSG_TYPE_RESPONSE | 9 | Response message |
| MSG_TYPE_ERROR | 10 | Error message |

## Status Codes

| Code | Value | Description |
|------|-------|-------------|
| MSG_STATUS_SUCCESS | 0 | Success |
| MSG_STATUS_ERROR | 1 | Error |
| MSG_STATUS_BUSY | 2 | Busy |
| MSG_STATUS_TIMEOUT | 3 | Timeout |
| MSG_STATUS_INVALID | 4 | Invalid |

## Configuration Types

| Type | Value | Description |
|------|-------|-------------|
| CONFIG_TYPE_STRING | 1 | String configuration |
| CONFIG_TYPE_HEX | 2 | Hexadecimal value |
| CONFIG_TYPE_LIST | 3 | List selection |

## Usage Examples

### From TCL Script:
```tcl
# Initialize shared memory
init_shared_memory

# Send commands
send_init_command
send_set_config_command "device_name" "My Device" 1
send_set_config_command "base_address" "0x43C00000" 2
send_run_app_command
send_get_status_command
send_exit_command

# Test all functionality
test_shared_memory_communication
```

### From C Application:
The C application automatically processes shared memory messages in both interactive and script modes. Messages are processed in the main loop before handling other inputs.

## Command Examples

### Basic Commands:
- `init` - Initialize the application
- `run_app` - Run the application with current configuration
- `get_status` - Get current status
- `capture_ram` - Capture RAM data
- `exit` - Exit the application

### Parameter Commands:
- `set_param param1 2` - Set parameter 1 to value 2
- `set_param param2 0x43C00000` - Set parameter 2 to hex value
- `set_param param3 5000` - Set parameter 3 to decimal value

### Configuration Commands:
- `set_config device_name MyDevice 1` - Set device name (string)
- `set_config base_address 0x43C00000 2` - Set base address (hex)
- `set_config operation_mode 2 3` - Set operation mode (list)
- `get_config device_name` - Get device name
- `get_config base_address` - Get base address

## Error Handling

- **Magic Number Validation**: Ensures message integrity
- **Timeout Handling**: Configurable timeouts for responses
- **Retry Logic**: Automatic retries on failure
- **Error Messages**: Detailed error reporting
- **Fallback Support**: Legacy register-based communication as backup

## Integration Points

1. **TCL Script**: Automatically loads `messages.tcl` and uses shared memory when available
2. **C Application**: Processes shared memory messages in main loops
3. **Script Mode**: Uses shared memory for automated command execution
4. **Interactive Mode**: Shared memory works alongside menu system

## Testing

Use the `test_shared_memory_communication` function to validate the entire system:

```tcl
test_shared_memory_communication
```

This will test all command types and verify proper communication between TCL and C application.

## Benefits

1. **Efficient Communication**: Direct memory access without UART overhead
2. **Structured Protocol**: Well-defined message format
3. **Error Handling**: Robust error detection and reporting
4. **Backward Compatibility**: Falls back to legacy methods
5. **Extensible**: Easy to add new message types
6. **Testable**: Built-in testing and validation functions
