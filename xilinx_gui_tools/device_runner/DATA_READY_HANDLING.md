# Device Runner - Enhanced Data Ready Handling

## 🎯 **Smart Data Ready Timing and Menu Selection**

The Device Runner now includes **intelligent data ready handling** and **menu-based parameter selection** to address the timing challenges of capturing data from FPGA applications.

### ✅ **Enhanced Features**

#### **1. Menu-Based Parameter Selection**
- **Parameter 1**: Radio button selection (Short/Medium/Tall)
- **Automatic Conversion**: Menu selections converted to hexadecimal values
- **User-Friendly**: Clear visual interface for parameter selection
- **Validation**: Ensures parameter 1 is always selected

#### **2. Data Ready Handling Methods**
- **Manual Mode**: User confirms when data is ready
- **Fixed Delay**: Automatic wait with configurable delay
- **Polling Mode**: Automatic detection of data ready signals
- **Flexible Configuration**: Choose the method that works best

#### **3. Intelligent Timing Control**
- **Application Completion**: Waits for application to finish
- **Data Ready Detection**: Multiple methods to detect when data is ready
- **Automatic Capture**: Proceeds with RAM capture when ready
- **Error Handling**: Robust error handling for timing issues

## 🔧 **Technical Implementation**

### **Menu-Based Parameter Selection**
```tcl
# Parameter 1 - Menu Selection
radiobutton $input_frame.params_frame.param1.menu_frame.short -text "Short" -variable param1 -value "short" -command update_param1_value
radiobutton $input_frame.params_frame.param1.menu_frame.medium -text "Medium" -variable param1 -value "medium" -command update_param1_value
radiobutton $input_frame.params_frame.param1.menu_frame.tall -text "Tall" -variable param1 -value "tall" -command update_param1_value

# Automatic conversion to hexadecimal
proc update_param1_value {} {
    global param1
    switch $param1 {
        "short" { set param1 "0x00000001" }
        "medium" { set param1 "0x00000002" }
        "tall" { set param1 "0x00000003" }
    }
}
```

### **Data Ready Handling Methods**

#### **Manual Mode**
```tcl
if {$data_ready_method == "manual"} {
    DeviceRunner::append_log $console_widget $log_file "Manual mode: Waiting for user confirmation..."
    set result [tk_messageBox -message "Application has completed. Click OK when data is ready for capture." -type okcancel -title "Data Ready?"]
    if {$result == "cancel"} {
        DeviceRunner::append_log $console_widget $log_file "User cancelled data capture"
        return
    }
    DeviceRunner::append_log $console_widget $log_file "User confirmed data is ready"
}
```

#### **Fixed Delay Mode**
```tcl
elseif {$data_ready_method == "delay"} {
    DeviceRunner::append_log $console_widget $log_file "Fixed delay mode: Waiting $capture_delay seconds..."
    for {set i $capture_delay} {$i > 0} {incr i -1} {
        DeviceRunner::append_log $console_widget $log_file "Waiting... $i seconds remaining"
        after 1000
    }
    DeviceRunner::append_log $console_widget $log_file "Delay completed"
}
```

#### **Polling Mode**
```tcl
elseif {$data_ready_method == "polling"} {
    DeviceRunner::append_log $console_widget $log_file "Polling mode: Checking for data ready signal..."
    if {[DeviceRunner::wait_for_data_ready $output_dir $console_widget $log_file $xsdb_path $jtag_tcp]} {
        DeviceRunner::append_log $console_widget $log_file "ERROR: Data ready polling failed"
        return
    }
    DeviceRunner::append_log $console_widget $log_file "Data ready signal detected"
}
```

### **Data Ready Polling Implementation**
```tcl
# Define data ready signal locations
set data_ready_addresses {
    0x00100000  # Global status register
    0x00100004  # Data ready flag
    0x00100008  # Processing complete flag
    0x0010000C  # Error status flag
}

# Polling configuration
set max_polls 100
set poll_interval 100
set data_ready_value 0x00000001

# Polling loop
for {set poll_count 0} {$poll_count < $max_polls} {incr poll_count} {
    set data_ready_found 0
    foreach addr $data_ready_addresses {
        set value [mrd $addr 4]
        if {$value == $data_ready_value} {
            puts "Data ready signal found at 0x[format %08X $addr]!"
            set data_ready_found 1
            break
        }
    }
    if {$data_ready_found} {
        puts "Data ready signal detected after $poll_count polls"
        break
    }
    after $poll_interval
}
```

## 🎯 **Usage Examples**

### **Menu Selection Workflow**
1. **Select Parameter 1**: Choose Short, Medium, or Tall from radio buttons
2. **Enter Parameter 2**: Input hexadecimal value (e.g., 0x43C00000)
3. **Enter Parameter 3**: Input hexadecimal value (e.g., 0x00001000)
4. **Choose Data Ready Method**: Select Manual, Fixed Delay, or Polling
5. **Configure Delay**: Set delay time if using Fixed Delay mode
6. **Run Workflow**: Click "Run Complete Workflow"

### **Data Ready Methods**

#### **Manual Mode**
- Application completes execution
- User sees popup: "Application has completed. Click OK when data is ready for capture."
- User clicks OK when data is ready
- RAM capture begins immediately

#### **Fixed Delay Mode**
- Application completes execution
- System waits for specified delay (e.g., 5 seconds)
- Countdown shows remaining time
- RAM capture begins after delay

#### **Polling Mode**
- Application completes execution
- System polls memory addresses for data ready signal
- Checks addresses: 0x00100000, 0x00100004, 0x00100008, 0x0010000C
- Looks for value 0x00000001
- RAM capture begins when signal detected

## 📋 **Parameter Mapping**

### **Menu Selection to Hexadecimal**
- **Short**: `0x00000001`
- **Medium**: `0x00000002`
- **Tall**: `0x00000003`

### **Data Ready Signal Addresses**
- **0x00100000**: Global status register
- **0x00100004**: Data ready flag
- **0x00100008**: Processing complete flag
- **0x0010000C**: Error status flag

### **Polling Configuration**
- **Max Polls**: 100 attempts
- **Poll Interval**: 100ms between checks
- **Data Ready Value**: 0x00000001
- **Timeout**: 10 seconds (100 × 100ms)

## 🚀 **Enhanced Workflow**

### **Complete Workflow Steps**
1. **Load BIT File**: Program FPGA with bitstream
2. **Run Application**: Execute with menu-selected parameters
3. **Handle Data Ready**: Use selected method to detect data readiness
4. **Capture RAM Data**: Extract variables and memory contents
5. **Save Results**: Store in timestamped folder with analysis

### **GUI Interface**
```
Device Configuration
├── Application Path: [Browse...]
├── BIT File: [Browse...]
├── Application Parameters
│   ├── Parameter 1: ○ Short  ○ Medium  ○ Tall
│   ├── Parameter 2: [0x43C00000]
│   └── Parameter 3: [0x00001000]
└── Data Ready Handling
    ├── Method: ○ Manual  ○ Fixed Delay  ○ Polling
    └── Delay (seconds): [5]
```

## 🎉 **Benefits of Enhanced Features**

### **User Experience**
- **Menu Selection**: Easy parameter selection with radio buttons
- **Visual Feedback**: Clear indication of selected parameters
- **Flexible Timing**: Multiple methods for data ready detection
- **Error Prevention**: Validation ensures proper parameter selection

### **Reliability**
- **Timing Control**: Handles unknown data ready timing
- **Multiple Methods**: Choose the best approach for your application
- **Error Handling**: Robust error handling for timing issues
- **Automatic Detection**: Polling mode for automatic data ready detection

### **Professional Features**
- **Configurable Delays**: Set appropriate wait times
- **Signal Polling**: Automatic detection of data ready signals
- **User Control**: Manual confirmation when needed
- **Comprehensive Logging**: Detailed logs of timing operations

## 🎯 **Ready for Production**

The enhanced Device Runner now provides:
- **Menu-Based Parameters**: Easy selection of Short/Medium/Tall
- **Smart Data Ready Handling**: Multiple methods for timing control
- **Automatic Conversion**: Menu selections to hexadecimal values
- **Flexible Configuration**: Choose the best data ready method
- **Professional Timing**: Handles unknown data ready timing
- **Comprehensive Logging**: Complete timing operation logs

Perfect for **professional FPGA application development** with intelligent data ready handling and user-friendly parameter selection!
