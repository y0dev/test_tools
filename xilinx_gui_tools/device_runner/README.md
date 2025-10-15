# Device Runner

## 🎯 **Streamlined Device Runner for Custom Applications**

A focused Tcl/Tk tool designed specifically for running custom applications on FPGA devices, loading BIT files, and capturing RAM data after execution.

### ✅ **Core Features**

#### **1. Complete Workflow**
- **Load BIT File**: Program FPGA with your custom bitstream
- **Run Application**: Execute your custom application with 3 parameters
- **Capture RAM Data**: Automatically capture memory regions after execution
- **Organized Output**: Automatic folder structure with timestamps

#### **2. Simplified Interface**
- **Clean GUI**: Focused on essential functionality
- **Sequential Input**: Enter 3 hexadecimal parameters one by one
- **Single Button**: "Run Complete Workflow" executes everything
- **Real-time Console**: Live feedback during operations

#### **3. Automatic Output Organization**
- **Timestamped Folders**: `capture_YYYYMMDD_HHMMSS`
- **Structured Data**: Organized binary files and summaries
- **User Input Capture**: Complete traceability of parameters used
- **No Configuration**: Output directory is fixed and automatic

## 🚀 **Quick Start**

### **1. Launch the Application**
```bash
# Windows
run_device_runner.bat

# Linux/macOS
./run_device_runner.sh
```

### **2. Configure Your Setup**
1. **Select Application**: Browse and select your executable
2. **Select BIT File**: Browse and select your BIT file
3. **Enter Parameters**: Input 3 hexadecimal 32-bit values
   - Parameter 1: (e.g., 0x40000000)
   - Parameter 2: (e.g., 0x43C00000)
   - Parameter 3: (e.g., 0x00001000)

### **3. Run Complete Workflow**
Click **"Run Complete Workflow"** to execute:
1. Load BIT file to FPGA
2. Run your application with parameters
3. Capture RAM data from device
4. Save results to timestamped folder

## 📁 **Output Structure**

```
output/
├── device_runner.log              # Main log file
├── capture_20241201_143022/       # Timestamped capture folder
│   ├── user_inputs.txt             # User parameters used
│   ├── capture_ram.tcl             # Enhanced capture script
│   ├── variable_analysis.txt       # Variable analysis report
│   ├── capture_summary.txt         # Capture summary
│   ├── DDR_START_0x00000000.bin     # DDR start memory region
│   ├── DDR_LOW_0x00010000.bin      # DDR low memory region
│   ├── DDR_MID_LOW_0x00020000.bin  # DDR mid-low memory region
│   ├── DDR_MID_0x00030000.bin      # DDR mid memory region
│   ├── DDR_MID_HIGH_0x00040000.bin # DDR mid-high memory region
│   ├── DDR_HIGH_0x00050000.bin     # DDR high memory region
│   ├── APP_DATA_0x00100000.bin     # Application data region
│   ├── APP_STACK_0x00110000.bin    # Application stack region
│   ├── APP_HEAP_0x00120000.bin     # Application heap region
│   ├── APP_ARRAYS_0x00140000.bin   # Application arrays region
│   ├── APP_OUTPUT_0x00160000.bin   # Application output region
│   ├── APP_CONFIG_0x00180000.bin   # Application config region
│   ├── GPIO_REGION_0x40000000.bin  # GPIO register region
│   ├── AXI_REGION_0x43C00000.bin   # AXI peripheral region
│   └── PS_PERIPHERALS_0xE0000000.bin # PS peripherals region
└── capture_20241201_150145/       # Next capture folder
    └── ...
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

### **Menu-Based Parameter Selection**
- **Parameter 1**: Radio button selection (Short/Medium/Tall)
- **Automatic Conversion**: Menu selections converted to hexadecimal values
- **User-Friendly**: Clear visual interface for parameter selection
- **Validation**: Ensures parameter 1 is always selected

### **Data Ready Handling**
- **Manual Mode**: User confirms when data is ready
- **Fixed Delay**: Automatic wait with configurable delay
- **Polling Mode**: Automatic detection of data ready signals
- **Flexible Configuration**: Choose the method that works best

### **Parameter Format**
- **Hexadecimal 32-bit**: All parameters must use `0x` prefix
- **Validation**: Automatic validation before execution
- **Range**: 0x00000000 to 0xFFFFFFFF
- **Formatting**: Automatically padded to 8 digits

### **User Input Capture**
- **Complete Traceability**: All parameters saved with timestamps
- **Formatted Values**: Both raw and formatted parameter values
- **Parameter Details**: Individual parameter analysis
- **Reproducibility**: Exact parameters used for each run

### **Enhanced Memory Analysis**
- **Variable Discovery**: Automatic detection of uint32_t and array patterns
- **Memory Regions**: Comprehensive DDR and application memory capture
- **Pattern Analysis**: Identification of data structures and variables
- **Variable Types**: uint32_t values, arrays, strings, and structs

### **Generated Scripts**
The tool generates TCL scripts for XSCT/XSDB:
- **BIT Programming**: `program_bit.tcl`
- **RAM Capture**: `capture_ram.tcl`

## 🎯 **Usage Examples**

### **Basic Usage**
1. Launch Device Runner
2. Select your application executable
3. Select your BIT file
4. Enter parameters:
   - Parameter 1: `0x40000000`
   - Parameter 2: `0x43C00000`
   - Parameter 3: `0x00001000`
5. Click "Run Complete Workflow"

### **Command Line Options**
```bash
# With custom XSDB path
./run_device_runner.sh --xsdb-path "/opt/Xilinx/Vitis/2023.2/bin/xsdb"

# With JTAG TCP configuration
./run_device_runner.sh --jtag-tcp "192.168.1.100:3121"

# Combined options
./run_device_runner.sh --xsdb-path "/opt/Xilinx/Vitis/2023.2/bin/xsdb" --jtag-tcp "192.168.1.100:3121"
```

## 📋 **Common Parameter Values**

### **Device Addresses**
- **GPIO Base**: `0x41200000`
- **UART Base**: `0xE0001000`
- **Timer Base**: `0xF8F00200`
- **DDR Base**: `0x00100000`

### **Configuration Values**
- **Enable**: `0x00000001`
- **Disable**: `0x00000000`
- **Reset**: `0x000000FF`
- **Clear**: `0xFFFFFFFF`

### **Buffer Sizes**
- **1KB**: `0x00000400`
- **4KB**: `0x00001000`
- **16KB**: `0x00004000`
- **64KB**: `0x00010000`

## 🔍 **Troubleshooting**

### **Common Issues**
1. **"Application not found"**: Check file path and permissions
2. **"BIT file not found"**: Verify BIT file exists and is readable
3. **"Invalid parameter format"**: Use hexadecimal with 0x prefix
4. **"XSCT/XSDB not found"**: Install Xilinx tools or specify custom path

### **Error Messages**
- **Parameter Validation**: Clear error messages for invalid input
- **File Operations**: Specific error messages for missing files
- **JTAG Operations**: Detailed error messages for connection issues

## 🎉 **Benefits**

### **Simplicity**
- **Single Workflow**: One button executes everything
- **No Configuration**: Fixed output directory, automatic organization
- **Clear Interface**: Focused on essential functionality
- **Minimal Setup**: Just select files and enter parameters

### **Professional Features**
- **Automatic Organization**: Timestamped folders for each run
- **Comprehensive Capture**: Multiple memory regions captured
- **Detailed Logging**: Complete operation log with timestamps
- **Error Handling**: Robust error handling and user feedback

### **Development Ready**
- **Custom Applications**: Designed for your specific applications
- **BIT File Support**: Load your custom FPGA configurations
- **RAM Analysis**: Capture and analyze memory contents
- **Reproducible**: Consistent output structure for analysis

## 🎯 **Perfect For**

- **Custom Application Testing**: Test your applications on FPGA
- **Memory Analysis**: Capture and analyze RAM contents
- **Development Workflow**: Streamlined development process
- **Data Collection**: Automated data capture and organization
- **Research Projects**: Reproducible experimental setup

The Device Runner provides a **focused, professional solution** for running custom applications on FPGA devices with automatic RAM data capture and organized output!

## 📁 **Project Structure**

```
device_runner/
├── device_runner.tcl              # Main application
├── lib/
│    └── helpers.tcl              # Helper functions
├── run_device_runner.bat          # Windows launcher
├── run_device_runner.sh          # Linux/macOS launcher
├── sample_config.json             # Example configuration
├── example_user_inputs.txt        # Example user inputs file
├── example_capture_summary.txt    # Example capture summary
├── README.md                      # This documentation
└── USER_INPUT_CAPTURE.md         # User input capture guide
```
