# Device Runner CLI - Command Line Interface

## 🎯 **Text-Based FPGA Application Runner**

The Device Runner CLI provides a **command-line interface** similar to the XLWP tool, with ASCII art banners and menu-driven navigation for FPGA application development.

### ✅ **Features**

#### **1. ASCII Art Interface**
- **Professional Banner**: Large ASCII art "DEVICE RUNNER CLI"
- **Clean Interface**: Text-based menu system
- **Screen Clearing**: Automatic screen management
- **XLWP-Style**: Similar to Xilinx Lightweight Provisioning Tool

#### **2. Menu-Driven Navigation**
- **Main Menu**: Numbered options for easy navigation
- **Configuration Menus**: Separate menus for each configuration
- **Validation**: Input validation and error handling
- **User-Friendly**: Clear prompts and instructions

#### **3. Complete Workflow Support**
- **Application Configuration**: Set application path
- **BIT File Configuration**: Set BIT file path
- **Parameter Configuration**: Menu-based parameter selection during workflow
- **Workflow Execution**: Complete automation

## 🚀 **Quick Start**

### **Windows**
```bash
# Run the CLI application
run_device_runner_cli.bat
```

### **Linux/macOS**
```bash
# Make executable and run
chmod +x run_device_runner_cli.sh
./run_device_runner_cli.sh
```

### **Direct Tcl Execution**
```bash
# Run directly with Tcl
tclsh device_runner_cli.tcl

# Run with command line arguments
tclsh device_runner_cli.tcl -arch zynq -mode user -hw_server localhost
```

### **Command Line Arguments**
```bash
# Available options
device_runner_cli.tcl [options]

Options:
  -arch <arch>        Target architecture (default: zynqMP)
  -mode <mode>        Operation mode: user | script (default: user)
  -boot_mode <mode>   Boot mode: jtag | other (default: jtag)
  -hw_server <server> Hardware server address (default: localhost)
  -ps_ref_clk <freq>  PS reference clock frequency: 27|33|50|60 (default: 0)
  -term_app <app>     Terminal application (default: device_runner_term.bat)
  -log_dir <dir>      Log directory (default: logs)
  -bit_file <file>    FPGA bitstream file path
  -fsbl_path <file>   FSBL (First Stage Boot Loader) ELF file path
  -ini_config <file>  INI configuration file for script mode
  -xsdb_path <path>   Path to XSDB executable
  -jtag_tcp <url>     JTAG TCP connection URL
  -help               Show help message

Examples:
  device_runner_cli.tcl -arch zynqMP -mode user -hw_server localhost
  device_runner_cli.tcl -arch zynqMP -boot_mode jtag -bit_file bin/kv260_design.bit
  device_runner_cli.tcl -fsbl_path bin/fsbl.elf -bit_file bin/kv260_design.bit
  device_runner_cli.tcl -mode script -ini_config example_config.ini
  device_runner_cli.tcl -xsdb_path C:/Xilinx/Vitis/2023.2/bin/xsdb.exe
  device_runner_cli.tcl -jtag_tcp 192.168.1.100:3121
```

## 📋 **Menu System**

### **Main Menu**
```
::: Main Menu :::
1. Configure Application
2. Configure BIT File
3. Run Complete Workflow
4. View Configuration
5. View Logs
b. Build info
x. Exit Device Runner CLI
```

### **Workflow Parameter Configuration**
```
Step 2: Configuring parameters...

Parameter 1 - Select option:
1. Short
2. Medium
3. Tall

Parameter 1 selection (1-3) -> 2
Parameter 1 set to: Medium (0x00000002)

Parameter 2 - Enter hexadecimal value:
Parameter 2 (e.g., 0x43C00000) -> 0x43C00000
Parameter 2 set to: 0x43C00000

Parameter 3 - Enter hexadecimal value:
Parameter 3 (e.g., 0x00001000) -> 0x00001000
Parameter 3 set to: 0x00001000
```

## 🔧 **Configuration**

### **Application Configuration**
- **Path**: Full path to your application executable
- **Validation**: Checks if file exists
- **Logging**: All changes logged

### **BIT File Configuration**
- **Path**: Full path to your BIT file
- **Validation**: Checks if file exists
- **Logging**: All changes logged

### **Command Line Configuration**
- **Architecture**: Target FPGA architecture (default: zynq)
- **Mode**: Operation mode (default: user)
- **Hardware Server**: Server address for hardware connection (default: localhost)
- **PS Reference Clock**: Clock frequency setting (default: 0)
- **Terminal Application**: Terminal app for execution (default: device_runner_term.bat)
- **Log Directory**: Directory for log files (default: logs)
- **XSDB Path**: Path to XSDB executable (optional)
- **JTAG TCP**: JTAG TCP connection URL (optional)

### **Parameter Configuration**
- **Parameter 1**: Menu selection (Short/Medium/Tall) - configured during workflow
  - Short: `0x00000001`
  - Medium: `0x00000002`
  - Tall: `0x00000003`
- **Parameter 2**: Hexadecimal value (e.g., `0x43C00000`) - configured during workflow
- **Parameter 3**: Hexadecimal value (e.g., `0x00001000`) - configured during workflow

## 📁 **Output Structure**

```
output/
├── device_runner_cli.log              # Main log file
├── capture_20241201_143022/           # Timestamped capture folder
│   ├── user_inputs.txt                 # User parameters used
│   ├── capture_ram.tcl                 # Generated capture script
│   ├── program_bit.tcl                 # Generated BIT programming script
│   ├── poll_data_ready.tcl             # Generated polling script
│   ├── DDR_START_0x00000000.bin        # DDR start memory region
│   ├── DDR_LOW_0x00010000.bin          # DDR low memory region
│   ├── DDR_MID_LOW_0x00020000.bin      # DDR mid-low memory region
│   ├── DDR_MID_0x00030000.bin          # DDR mid memory region
│   ├── DDR_MID_HIGH_0x00040000.bin     # DDR mid-high memory region
│   ├── DDR_HIGH_0x00050000.bin         # DDR high memory region
│   ├── APP_DATA_0x00100000.bin         # Application data region
│   ├── APP_STACK_0x00110000.bin        # Application stack region
│   ├── APP_HEAP_0x00120000.bin         # Application heap region
│   ├── APP_ARRAYS_0x00140000.bin       # Application arrays region
│   ├── APP_OUTPUT_0x00160000.bin       # Application output region
│   ├── APP_CONFIG_0x00180000.bin       # Application config region
│   ├── GPIO_REGION_0x40000000.bin      # GPIO register region
│   ├── AXI_REGION_0x43C00000.bin       # AXI peripheral region
│   └── PS_PERIPHERALS_0xE0000000.bin   # PS peripherals region
└── capture_20241201_150145/           # Next capture folder
    └── ...
```

## 🎯 **Usage Examples**

### **Basic Workflow**
1. **Launch CLI**: Run `run_device_runner_cli.bat` or `./run_device_runner_cli.sh`
2. **Configure Application**: Select option 1, enter application path
3. **Configure BIT File**: Select option 2, enter BIT file path
4. **Run Workflow**: Select option 3, confirm and execute
5. **Configure Parameters**: During workflow, select Short/Medium/Tall and enter hex values

### **Workflow Execution Example**
```
::: Run Complete Workflow :::

Configuration:
  Application: C:\my_app\my_application.exe
  BIT file: C:\my_bit\my_design.bit
  Architecture: zynq
  Mode: user
  Hardware Server: localhost
  PS Reference Clock: 0
  Terminal Application: device_runner_term.bat
  Log Directory: logs

Start workflow? (y/[n]) -> y

Starting complete workflow...
Step 1: Loading BIT file...
Step 2: Configuring parameters...
Step 3: Running application...
Step 4: Capturing RAM data...

Step 1: Loading BIT file...
BIT file loaded successfully

Step 2: Configuring parameters...
Parameter 1 - Select option:
1. Short
2. Medium
3. Tall

Parameter 1 selection (1-3) -> 2
Parameter 1 set to: Medium (0x00000002)

Parameter 2 - Enter hexadecimal value:
Parameter 2 (e.g., 0x43C00000) -> 0x43C00000
Parameter 2 set to: 0x43C00000

Parameter 3 - Enter hexadecimal value:
Parameter 3 (e.g., 0x00001000) -> 0x00001000
Parameter 3 set to: 0x00001000

Step 3: Running application...
Application completed successfully

Step 4: Capturing RAM data...
RAM data captured successfully

Workflow completed successfully!
Results saved to: output
Logs saved to: logs
```

## 🔨 **Building the Application**

### **Prerequisites**
- Xilinx Vitis IDE installed
- Xilinx Vivado installed
- Target hardware platform (XSA file)

### **Building PS Application (`jtag_app.elf`)**
1. **Open Vitis IDE** and create a new application project
2. **Select Platform**: Use your hardware platform (XSA file)
3. **Source Files**: Add all files from `app/ps_src/`:
   - `main.c`
   - `jtag_uart_handler.c`
   - `display.c`
   - `include/types.h`
   - `include/constants.h`
   - Header files (`.h`)
4. **Linker Script**: Use `app/ps_src/lscript.ld` or configure memory regions
5. **Build**: Compile and link the application
6. **Output**: Copy `jtag_app.elf` to `bin/` directory

### **Building FSBL (`fsbl.elf`)**
1. **Open Vitis IDE** and create a new FSBL project
2. **Select Platform**: Use your hardware platform (XSA file)
3. **Build**: The FSBL is automatically generated
4. **Output**: Copy `fsbl.elf` to `bin/` directory

### **Generating Bitstream (`kv260_design.bit`)**
1. **Open Vivado** and create/open your hardware design
2. **Add IP Cores**: Include any custom IP (e.g., AXI register write module)
3. **Create Block Design**: Connect Processing System and custom IP
4. **Generate Bitstream**: Run synthesis and implementation
5. **Output**: Export hardware and copy `.bit` file to `bin/` directory

### **Directory Setup**
After building, ensure your `bin/` directory contains:
```
bin/
├── fsbl.elf           # First Stage Boot Loader
├── jtag_app.elf       # Main PS application
└── kv260_design.bit   # FPGA bitstream (or your design name)
```

## 🔧 **Technical Details**

### **Shared Memory Communication**
The application uses shared memory for communication between the TCL CLI and the embedded application:

- **Base Address**: `0x10000000` (configurable)
- **Size**: `0x1000` (4KB, configurable in linker script)
- **Registers**:
  - Command Register: `0x10000000`
  - Response Register: `0x10000004`
  - Startup Mode Register: `0x10000008`

The shared memory region is defined in `app/ps_src/lscript.ld` and must match the addresses used in the TCL scripts. See `SHARED_MEMORY_COMMUNICATION.md` for detailed protocol information.

### **Memory Regions Captured**
- **DDR_START**: 0x00000000 - 0x0000FFFF (64KB)
- **DDR_LOW**: 0x00010000 - 0x0001FFFF (64KB)
- **DDR_MID_LOW**: 0x00020000 - 0x0002FFFF (64KB)
- **DDR_MID**: 0x00030000 - 0x0003FFFF (64KB)
- **DDR_MID_HIGH**: 0x00040000 - 0x0004FFFF (64KB)
- **DDR_HIGH**: 0x00050000 - 0x0005FFFF (64KB)
- **APP_DATA**: 0x00100000 - 0x0010FFFF (64KB)
- **APP_STACK**: 0x00110000 - 0x0011FFFF (64KB)
- **APP_HEAP**: 0x00120000 - 0x0013FFFF (128KB)
- **APP_ARRAYS**: 0x00140000 - 0x0015FFFF (128KB)
- **APP_OUTPUT**: 0x00160000 - 0x0017FFFF (128KB)
- **APP_CONFIG**: 0x00180000 - 0x0018FFFF (64KB)
- **GPIO_REGION**: 0x40000000 - 0x40000FFF (4KB)
- **AXI_REGION**: 0x43C00000 - 0x43C00FFF (4KB)
- **PS_PERIPHERALS**: 0xE0000000 - 0xE000FFFF (64KB)


## 📋 **Project Structure**

```
device_runner_cli/
├── device_runner_cli.tcl              # Main CLI application
├── messages.tcl                       # Shared memory message definitions
├── run_device_runner_cli.bat          # Windows launcher script
├── run_device_runner_cli.sh           # Linux/macOS launcher script
├── device_runner_term.bat             # Terminal launcher for JTAG UART
├── tt_jtag_uart.ini                   # Tera Term configuration file
├── example_config.ini                 # Example INI configuration file
├── example_test_config.ini            # Example test configuration file
├── bin/                               # Binary files directory
│   ├── fsbl.elf                       # First Stage Boot Loader ELF
│   ├── jtag_app.elf                   # Main PS application ELF (JTAG UART Handler)
│   └── kv260_design.bit               # FPGA bitstream file (KV260 example)
├── app/                               # Application source code
│   ├── ps_src/                        # Processing System (PS) source code
│   │   ├── main.c                     # Main application entry point
│   │   ├── jtag_uart_handler.c        # Core JTAG UART handler implementation
│   │   ├── jtag_uart_handler.h        # JTAG UART handler header
│   │   ├── display.c                  # Display and print functions
│   │   ├── display.h                  # Display functions header
│   │   ├── lscript.ld                 # Linker script (defines memory regions)
│   │   └── include/                   # Header files directory
│   │       ├── types.h                # Type definitions (config_t, test_config_t, etc.)
│   │       └── constants.h            # Constants and definitions
│   └── pl_src/                        # Programmable Logic (PL) source code
│       └── jtag_uart_handler_pl.c     # PL-side JTAG UART handler
├── lib/                               # Library modules (TCL scripts)
│   ├── device_runner.tcl              # Device runner helper functions
│   ├── jtag_reg.tcl                   # JTAG register operations and helpers
│   └── psu_init.tcl                   # PSU (Processing System Unit) initialization
├── output/                            # Output directory
│   └── device_runner_cli.log          # Application log file
└── README.md                          # This documentation
```

### **📦 Directory Details**

#### **`bin/` - Binary Files**
Contains all compiled binary files required for device operation:

- **`fsbl.elf`**: First Stage Boot Loader ELF file
  - Boots the processing system
  - Initializes hardware and loads the main application
  - Required for boot modes other than pure JTAG

- **`jtag_app.elf`**: Main Processing System Application
  - JTAG UART Handler application
  - Runs on the A53 cores (Cortex-A53)
  - Communicates via JTAG UART interface
  - Handles commands, configuration, and shared memory communication
  - Compiled from sources in `app/ps_src/`

- **`kv260_design.bit`**: FPGA Bitstream File
  - Programmable Logic (PL) configuration
  - Example design for KV260 development board
  - Contains custom IP cores and hardware configuration
  - Used to program the FPGA fabric

#### **`app/` - Application Source Code**
Contains all source code for the embedded application:

##### **`app/ps_src/` - Processing System Source**
Source code that runs on the ARM Cortex-A53 processors:

- **`main.c`**: Application entry point
  - Initializes the system
  - Detects startup mode (interactive/script)
  - Coordinates initialization and mode execution

- **`jtag_uart_handler.c`**: Core application logic
  - JTAG UART communication protocol
  - Command parsing and execution
  - Shared memory management
  - Configuration handling
  - Test execution framework

- **`jtag_uart_handler.h`**: Header file with function declarations and constants

- **`display.c` / `display.h`**: Display and user interface functions
  - Screen clearing
  - Banner display
  - Menu rendering
  - Configuration display

- **`lscript.ld`**: Linker script
  - Defines memory regions (DDR, OCM, shared memory)
  - Section placements
  - Stack and heap configuration

- **`include/types.h`**: Type definitions
  - `config_t`: Application configuration structure
  - `test_config_t`: Test configuration structure
  - `test_case_t`: Test case structure

- **`include/constants.h`**: Constants and definitions
  - Command definitions
  - Response codes
  - Memory addresses
  - Buffer sizes

##### **`app/pl_src/` - Programmable Logic Source**
Source code that runs on the PL side (MicroBlaze or PL IP):

- **`jtag_uart_handler_pl.c`**: PL-side JTAG UART handler
  - Hardware-level JTAG UART interface
  - Low-level communication handling

#### **`lib/` - Library Modules (TCL)**
TCL library modules providing reusable functionality:

- **`device_runner.tcl`**: Device runner helper functions
  - Device connection utilities
  - Configuration validation
  - Parameter handling
  - Common device operations

- **`jtag_reg.tcl`**: JTAG register operations
  - JTAG register read/write operations
  - Register access helpers
  - Low-level JTAG interface functions

- **`psu_init.tcl`**: Processing System Unit initialization
  - PSU initialization sequences
  - Clock configuration
  - Peripheral setup
  - Large initialization script for Zynq UltraScale+ devices

## 🎉 **Benefits of CLI Version**

### **Professional Interface**
- **ASCII Art**: Professional-looking banner
- **Menu System**: Easy navigation and configuration
- **Screen Management**: Clean, organized interface
- **XLWP-Style**: Familiar interface for FPGA developers

### **Command Line Benefits**
- **Remote Access**: Can run over SSH/remote connections
- **Automation**: Easy to script and automate
- **Lightweight**: No GUI dependencies
- **Cross-Platform**: Works on any system with Tcl

### **Complete Functionality**
- **All Features**: Same functionality as GUI version
- **Configuration**: Full configuration management
- **Workflow**: Complete automation workflow
- **Logging**: Comprehensive logging system

## 🎯 **Ready for Production**

The Device Runner CLI provides:
- **Professional Interface**: ASCII art and menu-driven navigation
- **Complete Functionality**: All features of the GUI version
- **Command Line Benefits**: Remote access and automation
- **XLWP-Style**: Familiar interface for FPGA developers
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Comprehensive Logging**: Complete operation logs

Perfect for **professional FPGA application development** with a command-line interface that matches the style of Xilinx tools!
