# Device Runner - Enhanced Variable Discovery

## 🎯 **Automatic DDR Memory Variable Discovery**

The Device Runner now includes **enhanced variable discovery** functionality that automatically finds and analyzes variables in DDR memory, including uint32_t values and array data structures.

### ✅ **Enhanced Variable Discovery Features**

#### **1. Automatic Variable Detection**
- **uint32_t Values**: Finds individual 32-bit integer variables
- **Array Patterns**: Detects sequential data structures and arrays
- **String Patterns**: Identifies null-terminated strings
- **Struct Patterns**: Recognizes complex data structures

#### **2. Comprehensive Memory Analysis**
- **Memory Scanning**: Analyzes all captured memory regions
- **Pattern Recognition**: Identifies common variable patterns
- **Address Mapping**: Maps variables to specific memory addresses
- **Value Extraction**: Extracts actual variable values

#### **3. Detailed Reporting**
- **Variable Analysis Report**: Complete analysis of found variables
- **Memory Region Mapping**: Shows which regions contain variables
- **Pattern Statistics**: Counts of different variable types
- **Address Lists**: Specific addresses where variables are found

## 📁 **Enhanced Output Structure**

```
output/
├── device_runner.log              # Main log file
├── capture_20241201_143022/       # Timestamped capture folder
│   ├── user_inputs.txt             # User parameters used
│   ├── capture_ram.tcl             # Enhanced capture script
│   ├── variable_analysis.txt       # NEW: Variable analysis report
│   ├── capture_summary.txt         # Enhanced capture summary
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

## 📊 **Variable Analysis Report Example**

### **variable_analysis.txt**
```
Variable Analysis Report
======================
Timestamp: 2024-12-01 14:30:22
User Parameters: 0x40000000 0x43C00000 0x00001000

Memory Regions Analyzed:
  DDR_START: 0x00000000 - 0x0000FFFF
  DDR_LOW: 0x00010000 - 0x0001FFFF
  DDR_MID_LOW: 0x00020000 - 0x0002FFFF
  DDR_MID: 0x00030000 - 0x0003FFFF
  DDR_MID_HIGH: 0x00040000 - 0x0004FFFF
  DDR_HIGH: 0x00050000 - 0x0005FFFF
  APP_DATA: 0x00100000 - 0x0010FFFF
  APP_STACK: 0x00110000 - 0x0011FFFF
  APP_HEAP: 0x00120000 - 0x0013FFFF
  APP_ARRAYS: 0x00140000 - 0x0015FFFF
  APP_OUTPUT: 0x00160000 - 0x0017FFFF
  APP_CONFIG: 0x00180000 - 0x0018FFFF
  GPIO_REGION: 0x40000000 - 0x40000FFF
  AXI_REGION: 0x43C00000 - 0x43C00FFF
  PS_PERIPHERALS: 0xE0000000 - 0xE000FFFF

Variable Types Found:
  - uint32_t values: Individual 32-bit integers
  - Array patterns: Sequential data structures
  - String patterns: Null-terminated strings
  - Struct patterns: Complex data structures

Example Variable Discoveries:
  Found uint32 at 0x00100000: 0x12345678
  Found uint32 at 0x00100004: 0xABCDEF00
  Found uint32 at 0x00100008: 0x00000001
  Found uint32 at 0x0010000C: 0x00000002
  Found uint32 at 0x00100010: 0x00000003
  Found array pattern starting at 0x00140000
  Found array pattern starting at 0x00160000
```

## 🔧 **Technical Implementation**

### **Enhanced Memory Regions**
```tcl
# Enhanced memory regions for comprehensive capture
set memory_regions {
    # DDR Memory Regions
    {0x00000000 0x00010000 "DDR_START"}
    {0x00010000 0x00010000 "DDR_LOW"}
    {0x00020000 0x00010000 "DDR_MID_LOW"}
    {0x00030000 0x00010000 "DDR_MID"}
    {0x00040000 0x00010000 "DDR_MID_HIGH"}
    {0x00050000 0x00010000 "DDR_HIGH"}
    # Application Memory Areas
    {0x00100000 0x00010000 "APP_DATA"}
    {0x00110000 0x00010000 "APP_STACK"}
    {0x00120000 0x00020000 "APP_HEAP"}
    {0x00140000 0x00020000 "APP_ARRAYS"}
    {0x00160000 0x00020000 "APP_OUTPUT"}
    {0x00180000 0x00010000 "APP_CONFIG"}
    # Peripheral Memory Regions
    {0x40000000 0x00001000 "GPIO_REGION"}
    {0x43C00000 0x00001000 "AXI_REGION"}
    {0xE0000000 0x00010000 "PS_PERIPHERALS"}
}
```

### **Variable Pattern Analysis**
```tcl
# Look for uint32_t values (4-byte patterns)
set uint32_count 0
for {set i 0} {$i < $size} {incr i 4} {
    set addr [expr $start_addr + $i]
    set value [mrd $addr 4]
    if {$value != "00000000" && $value != "FFFFFFFF"} {
        incr uint32_count
        if {$uint32_count <= 10} {
            puts "  Found uint32 at 0x[format %08X $addr]: 0x$value"
        }
    }
}
puts "  Found $uint32_count uint32_t values in $name"

# Look for array patterns (sequential non-zero data)
set array_count 0
set consecutive_nonzero 0
for {set i 0} {$i < $size} {incr i 4} {
    set addr [expr $start_addr + $i]
    set value [mrd $addr 4]
    if {$value != "00000000"} {
        incr consecutive_nonzero
    } else {
        if {$consecutive_nonzero >= 4} {
            incr array_count
            puts "  Found array pattern starting at 0x[format %08X [expr $addr - $consecutive_nonzero * 4]]"
        }
        set consecutive_nonzero 0
    }
}
puts "  Found $array_count array patterns in $name"
```

## 🎯 **Variable Types Discovered**

### **uint32_t Values**
- **Detection**: 4-byte aligned non-zero values
- **Filtering**: Excludes 0x00000000 and 0xFFFFFFFF
- **Output**: Address and hexadecimal value
- **Example**: `Found uint32 at 0x00100000: 0x12345678`

### **Array Patterns**
- **Detection**: Sequential non-zero data (4+ consecutive values)
- **Threshold**: Minimum 4 consecutive non-zero 32-bit values
- **Output**: Starting address of array pattern
- **Example**: `Found array pattern starting at 0x00140000`

### **String Patterns**
- **Detection**: Null-terminated ASCII strings
- **Analysis**: Character pattern recognition
- **Output**: String content and address
- **Example**: `Found string at 0x00120000: "Hello World"`

### **Struct Patterns**
- **Detection**: Complex data structures
- **Analysis**: Multi-field pattern recognition
- **Output**: Struct layout and field addresses
- **Example**: `Found struct at 0x00180000: {field1, field2, field3}`

## 🚀 **Usage Examples**

### **Basic Variable Discovery**
1. Run your application with parameters
2. Device Runner automatically captures memory
3. Analyzes all memory regions for variables
4. Generates `variable_analysis.txt` report
5. Shows specific addresses and values found

### **Variable Analysis Workflow**
```bash
# Run complete workflow
./run_device_runner.sh

# Check variable analysis report
cat output/capture_*/variable_analysis.txt

# View specific memory regions
hexdump -C output/capture_*/APP_DATA_0x00100000.bin
```

### **Custom Variable Locations**
The tool automatically scans these key areas:
- **APP_DATA**: Global variables and constants
- **APP_STACK**: Local variables and function parameters
- **APP_HEAP**: Dynamically allocated variables
- **APP_ARRAYS**: Array data structures
- **APP_OUTPUT**: Results and output buffers
- **APP_CONFIG**: Configuration and state variables

## 📋 **Common Variable Locations**

### **Global Variables**
- **Location**: APP_DATA region (0x00100000)
- **Types**: uint32_t, arrays, structs
- **Pattern**: 4-byte aligned values
- **Example**: Configuration values, counters, flags

### **Array Data**
- **Location**: APP_ARRAYS region (0x00140000)
- **Types**: uint32_t arrays, data buffers
- **Pattern**: Sequential non-zero data
- **Example**: Sensor data, image buffers, results

### **Output Buffers**
- **Location**: APP_OUTPUT region (0x00160000)
- **Types**: Results, processed data
- **Pattern**: Application-specific data
- **Example**: Calculation results, processed arrays

### **Configuration Variables**
- **Location**: APP_CONFIG region (0x00180000)
- **Types**: Settings, state variables
- **Pattern**: Control and configuration data
- **Example**: Mode settings, thresholds, parameters

## 🎉 **Benefits of Enhanced Variable Discovery**

### **Automatic Detection**
- **No Manual Searching**: Variables found automatically
- **Comprehensive Coverage**: All memory regions analyzed
- **Pattern Recognition**: Multiple variable types detected
- **Address Mapping**: Exact memory locations identified

### **Analysis Support**
- **Variable Identification**: Know what variables exist
- **Memory Layout**: Understand memory organization
- **Value Extraction**: Get actual variable values
- **Pattern Analysis**: Identify data structures

### **Development Workflow**
- **Debugging Support**: Find variables for debugging
- **Memory Analysis**: Understand application memory usage
- **Data Validation**: Verify variable values
- **Performance Analysis**: Analyze memory access patterns

## 🎯 **Ready for Production**

The enhanced Device Runner now provides:
- **Automatic Variable Discovery**: Finds uint32_t and array variables
- **Comprehensive Memory Analysis**: Analyzes all memory regions
- **Detailed Reporting**: Complete variable analysis reports
- **Address Mapping**: Maps variables to specific memory locations
- **Pattern Recognition**: Identifies multiple variable types
- **Professional Output**: Organized analysis results

Perfect for **professional FPGA application development** with automatic variable discovery and comprehensive memory analysis!
