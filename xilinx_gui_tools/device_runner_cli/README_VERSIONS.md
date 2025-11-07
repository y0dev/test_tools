# JTAG UART Handler - PS and PL Versions

This directory contains **two versions** of the JTAG UART Handler for Device Runner CLI:

1. **PS Version** (`jtag_uart_handler.c`) - Runs on FPGA PS (Processing System)
2. **PL Version** (`jtag_uart_handler_pl.c`) - Runs on FPGA PL (Programmable Logic)

## Files

### PS Version (Processing System)
- `jtag_uart_handler.c` - Main C source file for PS
- `jtag_uart_handler.h` - Header file with command definitions
- `Makefile` - Build configuration for PS (if exists)

### PL Version (Programmable Logic)
- `jtag_uart_handler_pl.c` - Main C source file for PL
- `Makefile.pl` - Build configuration for PL

### Common Files
- `JTAG_UART_HANDLER.md` - Documentation
- `README.md` - This file

## Key Differences

### PS Version Features
- **UART Driver**: `XUartPs` (PS UART)
- **Device ID**: `XPAR_PS7_UART_1_DEVICE_ID`
- **Interrupt**: `XPAR_PS7_UART_1_INTR`
- **Target**: ARM Cortex-A9/A53/A72 processors
- **Use Case**: PS-based applications

### PL Version Features
- **UART Driver**: `XUartLite` (AXI UART Lite)
- **Device ID**: `XPAR_AXI_UARTLITE_0_DEVICE_ID`
- **Interrupt**: `XPAR_FABRIC_AXI_UARTLITE_0_INTERRUPT_INTR`
- **Target**: MicroBlaze or ARM processors in PL
- **Use Case**: PL-based applications

## Command Protocol

Both versions support the same command protocol:

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Initialize the handler | `init` |
| `run_app` | Run the application with current parameters | `run_app` |
| `set_param` | Set a parameter value | `set_param param1 0x00000002` |
| `get_status` | Get current status and parameters | `get_status` |
| `capture_ram` | Capture RAM data | `capture_ram` |
| `exit` | Exit the handler | `exit` |
| `help` | Show available commands | `help` |

## Building

### Prerequisites
- **Xilinx SDK** or **Xilinx Vitis** installed
- **ARM cross-compilation toolchain** (included with Xilinx tools)
- Make utility

### PS Version Build
```bash
# Build for ARM 32-bit
make -f Makefile arm

# Build for AArch64
make -f Makefile aarch64

# Debug build
make -f Makefile debug
```

### PL Version Build
```bash
# Build for ARM 32-bit
make -f Makefile.pl arm

# Build for AArch64
make -f Makefile.pl aarch64

# Debug build
make -f Makefile.pl debug
```

### Environment Variables
```bash
# Set Xilinx SDK path
export XILINX_SDK_PATH=/opt/Xilinx/SDK/2019.1

# Set Xilinx Vitis path
export XILINX_VITIS_PATH=/opt/Xilinx/Vitis/2023.2
```

## Hardware Configuration

### PS Version Hardware
- **PS7 Configuration**: Enable UART in PS
- **JTAG UART**: Connect to PS UART
- **Interrupt Controller**: Enable ScuGic
- **Target**: ARM processor in PS

### PL Version Hardware
- **AXI UART Lite**: Add UART Lite IP to PL
- **JTAG UART**: Connect to AXI UART Lite
- **Interrupt Controller**: Connect to PS ScuGic
- **Target**: MicroBlaze or ARM processor in PL

## Usage

### 1. Choose Version
- **PS Version**: For PS-based applications
- **PL Version**: For PL-based applications

### 2. Compile Application
```bash
# PS Version
make -f Makefile arm

# PL Version
make -f Makefile.pl arm
```

### 3. Hardware Setup
- **PS Version**: Configure PS7 with UART enabled
- **PL Version**: Add AXI UART Lite IP to PL

### 4. Program FPGA
- Generate bitstream with UART configuration
- Program FPGA with bitstream

### 5. Run Application
- The baremetal application starts automatically
- Sends `READY` response
- Waits for commands from Device Runner CLI

## Communication Flow

Both versions follow the same communication flow:

1. **Handler Startup**
   - Initializes UART driver
   - Configures interrupt controller
   - Sends `READY` response
   - Waits for commands

2. **Command Processing**
   - Receives command via UART interrupt
   - Processes command
   - Sends response back

3. **Application Execution**
   - Receives `run_app` command
   - Executes application with current parameters
   - Sends completion status

4. **RAM Capture**
   - Receives `capture_ram` command
   - Captures RAM data at specified address
   - Sends capture completion status

## Parameter Management

Both versions manage three parameters:

- **param1**: Application mode (Short/Medium/Tall)
- **param2**: Base address for RAM operations
- **param3**: Size/length for RAM operations

### Setting Parameters
```bash
# Set parameter 1 to Medium (0x00000002)
set_param param1 0x00000002

# Set parameter 2 to custom address
set_param param2 0x43C00000

# Set parameter 3 to custom size
set_param param3 0x00002000
```

## Error Handling

Both versions include comprehensive error handling:

- **UART Errors**: Retries and error reporting
- **Invalid Commands**: Error responses with descriptions
- **Parameter Validation**: Range and format checking
- **Interrupt Handling**: Proper interrupt management

## Debugging

### Enable Debug Output
```bash
# PS Version
make -f Makefile debug

# PL Version
make -f Makefile.pl debug
```

### Debug Features
- Verbose command logging via `xil_printf`
- Parameter value tracking
- Communication status monitoring
- Error detail reporting

## Integration with Device Runner CLI

Both versions work seamlessly with the Device Runner CLI:

1. **Automatic Connection**: CLI connects to handler automatically
2. **Command Synchronization**: Commands are processed in order
3. **Status Reporting**: Real-time status updates
4. **Error Propagation**: Errors are reported back to CLI

## Troubleshooting

### Common Issues

1. **UART Not Working**
   - **PS Version**: Check PS7 configuration
   - **PL Version**: Check AXI UART Lite configuration
   - Verify UART is enabled in hardware
   - Check interrupt configuration

2. **Build Errors**
   - Verify Xilinx toolchain installation
   - Check Makefile paths
   - Ensure all dependencies are available

3. **Communication Errors**
   - Verify JTAG UART connection
   - Check baud rate settings
   - Test with simple terminal

### Debug Steps

1. **Test UART Communication**
   - Use Xilinx SDK terminal
   - Send simple commands manually
   - Verify responses are received

2. **Verify Handler Startup**
   - Check for initialization messages
   - Verify READY response is sent
   - Monitor for error messages

3. **Test Command Processing**
   - Send simple commands manually
   - Verify responses are received
   - Check parameter handling

## License

This software is part of the Device Runner CLI project and follows the same licensing terms.
