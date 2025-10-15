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
```

## 🔧 **Technical Details**

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
├── lib/
│    └── helpers.tcl                   # Helper functions
├── run_device_runner_cli.bat          # Windows launcher
├── run_device_runner_cli.sh          # Linux/macOS launcher
└── README.md                          # This documentation
```

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
