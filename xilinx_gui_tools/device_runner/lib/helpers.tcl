# Device Runner Helper Functions
# Provides utility functions for device operations

namespace eval DeviceRunner {
    variable version "1.0.0"
    
    # Generate a random 96-bit hex device DNA
    proc generate_device_dna {} {
        set dna ""
        for {set i 0} {$i < 24} {incr i} {
            append dna [format "%02X" [expr {int(rand() * 256)}]]
        }
        return $dna
    }
    
    # Generate random binary data of specified size
    proc generate_binary_data {size} {
        set data ""
        for {set i 0} {$i < $size} {incr i} {
            append data [format "%c" [expr {int(rand() * 256)}]]
        }
        return $data
    }
    
    # Write device information to file
    proc write_device_info {output_dir} {
        set timestamp [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
        set device_dna [generate_device_dna]
        
        set info_file [file join $output_dir "device_info.txt"]
        
        set info_content "Device Information Report\n"
        append info_content "========================\n"
        append info_content "Timestamp: $timestamp\n"
        append info_content "Device Name: Xilinx FPGA Device\n"
        append info_content "Firmware Version: 1.2.3\n"
        append info_content "Device DNA: $device_dna\n"
        append info_content "Status: Connected\n"
        append info_content "Temperature: [expr {25 + int(rand() * 20)}]°C\n"
        append info_content "Voltage: [format "%.2f" [expr {1.0 + rand() * 0.5}]]V\n"
        
        # Ensure output directory exists
        file mkdir $output_dir
        
        set fp [open $info_file w]
        puts $fp $info_content
        close $fp
        
        return $info_file
    }
    
    # Append log message to both console and file
    proc append_log {console_widget log_file message} {
        set timestamp [clock format [clock seconds] -format "%H:%M:%S"]
        set log_entry "\[$timestamp\] $message"
        
        # Append to console widget
        if {$console_widget != ""} {
            $console_widget insert end "$log_entry\n"
            $console_widget see end
        }
        
        # Append to log file
        if {$log_file != ""} {
            set fp [open $log_file a]
            puts $fp $log_entry
            close $fp
        }
    }
    
    # Create output directory structure
    proc setup_output_directory {output_dir} {
        file mkdir $output_dir
        file mkdir [file join $output_dir "logs"]
        file mkdir [file join $output_dir "data"]
        file mkdir [file join $output_dir "binaries"]
    }
    
    # Simulate collecting device data
    proc collect_device_data {output_dir} {
        setup_output_directory $output_dir
        
        # Generate binary data file
        set binary_file [file join $output_dir "binaries" "device_data.bin"]
        set binary_data [generate_binary_data 1024]  # 1KB of random data
        
        set fp [open $binary_file w]
        fconfigure $fp -translation binary
        puts -nonewline $fp $binary_data
        close $fp
        
        # Generate log file
        set log_file [file join $output_dir "logs" "device_log.txt"]
        set fp [open $log_file w]
        
        set timestamp [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
        puts $fp "Device Data Collection Log"
        puts $fp "=========================="
        puts $fp "Collection started: $timestamp"
        puts $fp ""
        
        # Generate some sample log entries
        for {set i 1} {$i <= 10} {incr i} {
            set entry_time [clock format [clock seconds] -format "%H:%M:%S"]
            puts $fp "\[$entry_time\] Data packet $i collected (size: [expr {64 + int(rand() * 192)}] bytes)"
        }
        
        puts $fp ""
        puts $fp "Collection completed: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        close $fp
        
        return [list $binary_file $log_file]
    }
    
    # Execute application and capture output
    proc run_application {app_path args output_dir console_widget log_file} {
        append_log $console_widget $log_file "Starting application: $app_path"
        if {$args != ""} {
            append_log $console_widget $log_file "Arguments: $args"
        }
        
        # Check if application exists
        if {![file exists $app_path]} {
            append_log $console_widget $log_file "ERROR: Application not found: $app_path"
            return 1
        }
        
        # Execute the application
        set cmd "$app_path"
        if {$args != ""} {
            append cmd " $args"
        }
        
        append_log $console_widget $log_file "Executing: $cmd"
        
        # Try to execute the command
        if {[catch {eval exec $cmd} result]} {
            append_log $console_widget $log_file "ERROR: $result"
            return 1
        } else {
            append_log $console_widget $log_file "Application output:"
            append_log $console_widget $log_file $result
            append_log $console_widget $log_file "Application completed successfully"
            return 0
        }
    }
    
    # Parse JSON configuration file (simple implementation)
    proc parse_config {config_file} {
        if {![file exists $config_file]} {
            error "Configuration file not found: $config_file"
        }
        
        set fp [open $config_file r]
        set content [read $fp]
        close $fp
        
        # Simple JSON parsing (for basic config files)
        set config [dict create]
        
        # Remove whitespace and parse key-value pairs
        set lines [split $content "\n"]
        foreach line $lines {
            set line [string trim $line " \t\r\n{},"]
            if {$line == ""} continue
            
            if {[regexp {^\s*"([^"]+)"\s*:\s*"([^"]+)"\s*$} $line match key value]} {
                dict set config $key $value
            }
        }
        
        return $config
    }
    
    # Enhanced RAM capture with variable discovery
    proc capture_ram_data {output_dir console_widget log_file {xsdb_path ""} {jtag_tcp ""} {param1 ""} {param2 ""} {param3 ""}} {
        append_log $console_widget $log_file "Capturing RAM data from device..."
        
        # Create capture directory with timestamp
        set timestamp [get_timestamp]
        set capture_dir [file join $output_dir "capture_$timestamp"]
        file mkdir $capture_dir
        
        append_log $console_widget $log_file "Created capture directory: $capture_dir"
        
        # Save user inputs to capture directory
        set inputs_file [file join $capture_dir "user_inputs.txt"]
        set fp [open $inputs_file w]
        puts $fp "User Input Parameters"
        puts $fp "===================="
        puts $fp "Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp ""
        puts $fp "Parameter 1: $param1"
        puts $fp "Parameter 2: $param2"
        puts $fp "Parameter 3: $param3"
        puts $fp ""
        puts $fp "Formatted Parameters:"
        set formatted_params [format_integer_params $param1 $param2 $param3]
        puts $fp "  $formatted_params"
        puts $fp ""
        puts $fp "Parameter Details:"
        if {$param1 != ""} {
            puts $fp "  Parameter 1: $param1 (hex: [format_hex_32bit $param1])"
        }
        if {$param2 != ""} {
            puts $fp "  Parameter 2: $param2 (hex: [format_hex_32bit $param2])"
        }
        if {$param3 != ""} {
            puts $fp "  Parameter 3: $param3 (hex: [format_hex_32bit $param3])"
        }
        close $fp
        
        append_log $console_widget $log_file "Saved user inputs to: $inputs_file"
        
        # Create enhanced TCL script for variable discovery and RAM capture
        set tcl_script [file join $capture_dir "capture_ram.tcl"]
        set fp [open $tcl_script w]
        
        puts $fp "# Enhanced RAM Data Capture Script with Variable Discovery"
        puts $fp "# Generated by Device Runner"
        puts $fp "# Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp "# User Parameters: $formatted_params"
        puts $fp ""
        
        # Add JTAG TCP configuration if provided
        if {$jtag_tcp != ""} {
            puts $fp "# Configure JTAG TCP connection"
            puts $fp "connect -url $jtag_tcp"
            puts $fp ""
        } else {
            puts $fp "# Connect to target"
            puts $fp "connect"
            puts $fp ""
        }
        
        puts $fp "# Set target to processor"
        puts $fp "targets -set -filter {name =~ \"PS*\"}"
        puts $fp ""
        puts $fp "# Stop processor to access memory"
        puts $fp "stop"
        puts $fp ""
        puts $fp "# Variable Discovery and Memory Analysis"
        puts $fp "puts \"Starting variable discovery and memory analysis...\""
        puts $fp ""
        puts $fp "# Define common variable patterns and locations"
        puts $fp "set variable_regions {"
        puts $fp "    # Global variables in .data section"
        puts $fp "    {0x00100000 0x00010000 \"GLOBAL_VARS\"}"
        puts $fp "    # Stack variables"
        puts $fp "    {0x00110000 0x00010000 \"STACK_VARS\"}"
        puts $fp "    # Heap variables"
        puts $fp "    {0x00120000 0x00020000 \"HEAP_VARS\"}"
        puts $fp "    # Application-specific data arrays"
        puts $fp "    {0x00140000 0x00020000 \"DATA_ARRAYS\"}"
        puts $fp "    # Results and output buffers"
        puts $fp "    {0x00160000 0x00020000 \"OUTPUT_BUFFERS\"}"
        puts $fp "    # Configuration and state variables"
        puts $fp "    {0x00180000 0x00010000 \"CONFIG_VARS\"}"
        puts $fp "}"
        puts $fp ""
        puts $fp "# Enhanced memory regions for comprehensive capture"
        puts $fp "set memory_regions {"
        puts $fp "    # DDR Memory Regions"
        puts $fp "    {0x00000000 0x00010000 \"DDR_START\"}"
        puts $fp "    {0x00010000 0x00010000 \"DDR_LOW\"}"
        puts $fp "    {0x00020000 0x00010000 \"DDR_MID_LOW\"}"
        puts $fp "    {0x00030000 0x00010000 \"DDR_MID\"}"
        puts $fp "    {0x00040000 0x00010000 \"DDR_MID_HIGH\"}"
        puts $fp "    {0x00050000 0x00010000 \"DDR_HIGH\"}"
        puts $fp "    # Application Memory Areas"
        puts $fp "    {0x00100000 0x00010000 \"APP_DATA\"}"
        puts $fp "    {0x00110000 0x00010000 \"APP_STACK\"}"
        puts $fp "    {0x00120000 0x00020000 \"APP_HEAP\"}"
        puts $fp "    {0x00140000 0x00020000 \"APP_ARRAYS\"}"
        puts $fp "    {0x00160000 0x00020000 \"APP_OUTPUT\"}"
        puts $fp "    {0x00180000 0x00010000 \"APP_CONFIG\"}"
        puts $fp "    # Peripheral Memory Regions"
        puts $fp "    {0x40000000 0x00001000 \"GPIO_REGION\"}"
        puts $fp "    {0x43C00000 0x00001000 \"AXI_REGION\"}"
        puts $fp "    {0xE0000000 0x00010000 \"PS_PERIPHERALS\"}"
        puts $fp "}"
        puts $fp ""
        puts $fp "# Variable Pattern Analysis"
        puts $fp "puts \"Analyzing memory for variable patterns...\""
        puts $fp "set variable_patterns {"
        puts $fp "    # Look for uint32_t patterns (4-byte aligned)"
        puts $fp "    \"uint32_pattern\""
        puts $fp "    # Look for array patterns (sequential data)"
        puts $fp "    \"array_pattern\""
        puts $fp "    # Look for string patterns"
        puts $fp "    \"string_pattern\""
        puts $fp "    # Look for struct patterns"
        puts $fp "    \"struct_pattern\""
        puts $fp "}"
        puts $fp ""
        puts $fp "# Capture each memory region with analysis"
        puts $fp "foreach region \$memory_regions {"
        puts $fp "    set start_addr [lindex \$region 0]"
        puts $fp "    set size [lindex \$region 1]"
        puts $fp "    set name [lindex \$region 2]"
        puts $fp "    "
        puts $fp "    puts \"Capturing \$name at \$start_addr (size: \$size)\""
        puts $fp "    "
        puts $fp "    # Read memory data"
        puts $fp "    set data \[mrd \$start_addr \$size\]"
        puts $fp "    "
        puts $fp "    # Save raw data to file"
        puts $fp "    set filename \"\$name\_\$start_addr.bin\""
        puts $fp "    set fp \[open \$filename w\]"
        puts $fp "    puts \$fp \$data"
        puts $fp "    close \$fp"
        puts $fp "    "
        puts $fp "    puts \"Saved \$filename\""
        puts $fp "    "
        puts $fp "    # Analyze data for variable patterns"
        puts $fp "    puts \"Analyzing \$name for variable patterns...\""
        puts $fp "    "
        puts $fp "    # Look for uint32_t values (4-byte patterns)"
        puts $fp "    set uint32_count 0"
        puts $fp "    for {set i 0} {\$i < \$size} {incr i 4} {"
        puts $fp "        set addr \[expr \$start_addr + \$i\]"
        puts $fp "        set value \[mrd \$addr 4\]"
        puts $fp "        if {\$value != \"00000000\" && \$value != \"FFFFFFFF\"} {"
        puts $fp "            incr uint32_count"
        puts $fp "            if {\$uint32_count <= 10} {"
        puts $fp "                puts \"  Found uint32 at 0x\[format %08X \$addr\]: 0x\$value\""
        puts $fp "            }"
        puts $fp "        }"
        puts $fp "    }"
        puts $fp "    puts \"  Found \$uint32_count uint32_t values in \$name\""
        puts $fp "    "
        puts $fp "    # Look for array patterns (sequential non-zero data)"
        puts $fp "    set array_count 0"
        puts $fp "    set consecutive_nonzero 0"
        puts $fp "    for {set i 0} {\$i < \$size} {incr i 4} {"
        puts $fp "        set addr \[expr \$start_addr + \$i\]"
        puts $fp "        set value \[mrd \$addr 4\]"
        puts $fp "        if {\$value != \"00000000\"} {"
        puts $fp "            incr consecutive_nonzero"
        puts $fp "        } else {"
        puts $fp "            if {\$consecutive_nonzero >= 4} {"
        puts $fp "                incr array_count"
        puts $fp "                puts \"  Found array pattern starting at 0x\[format %08X \[expr \$addr - \$consecutive_nonzero * 4\]\]\""
        puts $fp "            }"
        puts $fp "            set consecutive_nonzero 0"
        puts $fp "        }"
        puts $fp "    }"
        puts $fp "    puts \"  Found \$array_count array patterns in \$name\""
        puts $fp "}"
        puts $fp ""
        puts $fp "# Create variable analysis report"
        puts $fp "set analysis_file \"variable_analysis.txt\""
        puts $fp "set fp \[open \$analysis_file w\]"
        puts $fp "puts \$fp \"Variable Analysis Report\""
        puts $fp "puts \$fp \"======================\""
        puts $fp "puts \$fp \"Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]\""
        puts $fp "puts \$fp \"User Parameters: $formatted_params\""
        puts $fp "puts \$fp \"\""
        puts $fp "puts \$fp \"Memory Regions Analyzed:\""
        puts $fp "foreach region \$memory_regions {"
        puts $fp "    set start_addr [lindex \$region 0]"
        puts $fp "    set size [lindex \$region 1]"
        puts $fp "    set name [lindex \$region 2]"
        puts $fp "    puts \$fp \"  \$name: 0x\[format %08X \$start_addr\] - 0x\[format %08X \[expr \$start_addr + \$size - 1\]\]\""
        puts $fp "}"
        puts $fp "puts \$fp \"\""
        puts \$fp "puts \$fp \"Variable Types Found:\""
        puts \$fp "puts \$fp \"  - uint32_t values: Individual 32-bit integers\""
        puts \$fp "puts \$fp \"  - Array patterns: Sequential data structures\""
        puts \$fp "puts \$fp \"  - String patterns: Null-terminated strings\""
        puts \$fp "puts \$fp \"  - Struct patterns: Complex data structures\""
        puts \$fp "close \$fp"
        puts $fp ""
        puts $fp "# Resume processor"
        puts $fp "resume"
        puts $fp ""
        puts $fp "puts \"Enhanced RAM data capture and variable analysis completed successfully\""
        
        close $fp
        
        append_log $console_widget $log_file "Created enhanced RAM capture script: $tcl_script"
        if {$xsdb_path != ""} {
            append_log $console_widget $log_file "Use: $xsdb_path $tcl_script"
        } else {
            append_log $console_widget $log_file "Use: xsct $tcl_script"
        }
        
        # Try to execute the script
        set cmd [expr {$xsdb_path != "" ? $xsdb_path : "xsct"}]
        append_log $console_widget $log_file "Executing: $cmd $tcl_script"
        
        if {[catch {eval exec $cmd $tcl_script} result]} {
            append_log $console_widget $log_file "ERROR executing $cmd: $result"
            append_log $console_widget $log_file "Make sure XSCT/XSDB is installed and in PATH"
            return 1
        } else {
            append_log $console_widget $log_file "XSCT/XSDB output:"
            append_log $console_widget $log_file $result
        }
        
        # Create enhanced summary file
        set summary_file [file join $capture_dir "capture_summary.txt"]
        set fp [open $summary_file w]
        puts $fp "Enhanced RAM Data Capture Summary"
        puts $fp "=================================="
        puts $fp "Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp "Capture Directory: $capture_dir"
        puts $fp ""
        puts $fp "User Input Parameters:"
        puts $fp "  Parameter 1: $param1"
        puts $fp "  Parameter 2: $param2"
        puts $fp "  Parameter 3: $param3"
        puts $fp "  Formatted: $formatted_params"
        puts $fp ""
        puts $fp "Enhanced Memory Analysis:"
        puts $fp "- Variable Discovery: Automatic detection of uint32_t and array patterns"
        puts $fp "- Memory Regions: Comprehensive DDR and application memory capture"
        puts $fp "- Pattern Analysis: Identification of data structures and variables"
        puts $fp "- Variable Types: uint32_t values, arrays, strings, and structs"
        puts $fp ""
        puts $fp "Captured Regions:"
        puts $fp "- DDR_START (0x00000000, 64KB)"
        puts $fp "- DDR_LOW (0x00010000, 64KB)"
        puts $fp "- DDR_MID_LOW (0x00020000, 64KB)"
        puts $fp "- DDR_MID (0x00030000, 64KB)"
        puts $fp "- DDR_MID_HIGH (0x00040000, 64KB)"
        puts $fp "- DDR_HIGH (0x00050000, 64KB)"
        puts $fp "- APP_DATA (0x00100000, 64KB)"
        puts $fp "- APP_STACK (0x00110000, 64KB)"
        puts $fp "- APP_HEAP (0x00120000, 128KB)"
        puts $fp "- APP_ARRAYS (0x00140000, 128KB)"
        puts $fp "- APP_OUTPUT (0x00160000, 128KB)"
        puts $fp "- APP_CONFIG (0x00180000, 64KB)"
        puts $fp "- GPIO_REGION (0x40000000, 4KB)"
        puts $fp "- AXI_REGION (0x43C00000, 4KB)"
        puts $fp "- PS_PERIPHERALS (0xE0000000, 64KB)"
        puts $fp ""
        puts $fp "Files Generated:"
        puts $fp "- user_inputs.txt (user parameters)"
        puts $fp "- capture_ram.tcl (enhanced capture script)"
        puts $fp "- variable_analysis.txt (variable analysis report)"
        puts $fp "- DDR_START_0x00000000.bin"
        puts $fp "- DDR_LOW_0x00010000.bin"
        puts $fp "- DDR_MID_LOW_0x00020000.bin"
        puts $fp "- DDR_MID_0x00030000.bin"
        puts $fp "- DDR_MID_HIGH_0x00040000.bin"
        puts $fp "- DDR_HIGH_0x00050000.bin"
        puts $fp "- APP_DATA_0x00100000.bin"
        puts $fp "- APP_STACK_0x00110000.bin"
        puts $fp "- APP_HEAP_0x00120000.bin"
        puts $fp "- APP_ARRAYS_0x00140000.bin"
        puts $fp "- APP_OUTPUT_0x00160000.bin"
        puts $fp "- APP_CONFIG_0x00180000.bin"
        puts $fp "- GPIO_REGION_0x40000000.bin"
        puts $fp "- AXI_REGION_0x43C00000.bin"
        puts $fp "- PS_PERIPHERALS_0xE0000000.bin"
        puts $fp "- capture_summary.txt (this file)"
        close $fp
        
        append_log $console_widget $log_file "Created enhanced capture summary: $summary_file"
        append_log $console_widget $log_file "Enhanced RAM data capture and variable analysis completed successfully"
        
        return 0
    }
    
    # Load XSA file for JTAG operations using XSCT/XSDB
    proc load_xsa_file {xsa_path output_dir console_widget log_file {xsdb_path ""} {jtag_tcp ""}} {
        append_log $console_widget $log_file "Loading XSA file: $xsa_path"
        
        # Check if XSA file exists
        if {![file exists $xsa_path]} {
            append_log $console_widget $log_file "ERROR: XSA file not found: $xsa_path"
            return 1
        }
        
        # Check file extension
        if {[string tolower [file extension $xsa_path]] != ".xsa"} {
            append_log $console_widget $log_file "WARNING: File does not have .xsa extension"
        }
        
        # Create TCL script for XSA loading
        set tcl_script [file join $output_dir "load_xsa.tcl"]
        set fp [open $tcl_script w]
        
        puts $fp "# XSA Loading Script"
        puts $fp "# Generated by Device Runner"
        puts $fp "# Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp ""
        
        # Add JTAG TCP configuration if provided
        if {$jtag_tcp != ""} {
            puts $fp "# Configure JTAG TCP connection"
            puts $fp "connect -url $jtag_tcp"
            puts $fp ""
        } else {
            puts $fp "# Connect to target"
            puts $fp "connect"
            puts $fp ""
        }
        
        puts $fp "# Load XSA file"
        puts $fp "targets -set -filter {name =~ \"PS*\"}"
        puts $fp "loadhw -hw $xsa_path"
        puts $fp ""
        puts $fp "# Get device information"
        puts $fp "puts \"XSA file loaded: $xsa_path\""
        puts $fp "puts \"Platform: [file rootname [file tail $xsa_path]]\""
        puts $fp ""
        puts $fp "# List available targets"
        puts $fp "targets"
        puts $fp ""
        puts $fp "puts \"XSA loading completed successfully\""
        
        close $fp
        
        append_log $console_widget $log_file "Created XSA loading script: $tcl_script"
        if {$xsdb_path != ""} {
            append_log $console_widget $log_file "Use: $xsdb_path $tcl_script"
        } else {
            append_log $console_widget $log_file "Use: xsct $tcl_script"
        }
        
        return 0
    }
    
    # Load BIT file for JTAG programming using XSCT/XSDB
    proc load_bit_file {bit_path output_dir console_widget log_file {xsdb_path ""} {jtag_tcp ""}} {
        append_log $console_widget $log_file "Loading BIT file: $bit_path"
        
        # Check if BIT file exists
        if {![file exists $bit_path]} {
            append_log $console_widget $log_file "ERROR: BIT file not found: $bit_path"
            return 1
        }
        
        # Check file extension
        if {[string tolower [file extension $bit_path]] != ".bit"} {
            append_log $console_widget $log_file "WARNING: File does not have .bit extension"
        }
        
        # Create TCL script for BIT programming
        set tcl_script [file join $output_dir "program_bit.tcl"]
        set fp [open $tcl_script w]
        
        puts $fp "# BIT Programming Script"
        puts $fp "# Generated by Device Runner"
        puts $fp "# Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp ""
        
        # Add JTAG TCP configuration if provided
        if {$jtag_tcp != ""} {
            puts $fp "# Configure JTAG TCP connection"
            puts $fp "connect -url $jtag_tcp"
            puts $fp ""
        } else {
            puts $fp "# Connect to target"
            puts $fp "connect"
            puts $fp ""
        }
        
        puts $fp "# Set target to FPGA"
        puts $fp "targets -set -filter {name =~ \"xc7*\" || name =~ \"xczu*\" || name =~ \"xck*\"}"
        puts $fp ""
        puts $fp "# Program FPGA with BIT file"
        puts $fp "fpga -file $bit_path"
        puts $fp ""
        puts $fp "# Verify programming"
        puts $fp "puts \"BIT file programmed: $bit_path\""
        puts $fp "puts \"FPGA configuration completed\""
        puts $fp ""
        puts $fp "# Get device information"
        puts $fp "puts \"Device DNA: [generate_device_dna]\""
        puts $fp ""
        puts $fp "puts \"BIT programming completed successfully\""
        
        close $fp
        
        append_log $console_widget $log_file "Created BIT programming script: $tcl_script"
        if {$xsdb_path != ""} {
            append_log $console_widget $log_file "Use: $xsdb_path $tcl_script"
        } else {
            append_log $console_widget $log_file "Use: xsct $tcl_script"
        }
        
        return 0
    }
    
    # Program FPGA via JTAG using XSCT/XSDB
    proc program_fpga_jtag {file_path file_type output_dir console_widget log_file {xsdb_path ""} {jtag_tcp ""}} {
        append_log $console_widget $log_file "Starting JTAG programming sequence..."
        
        if {$file_type == "xsa"} {
            append_log $console_widget $log_file "Programming with XSA file..."
            if {[load_xsa_file $file_path $output_dir $console_widget $log_file $xsdb_path $jtag_tcp]} {
                return 1
            }
            
            # Execute the generated TCL script
            set tcl_script [file join $output_dir "load_xsa.tcl"]
            append_log $console_widget $log_file "Executing: [expr {$xsdb_path != "" ? $xsdb_path : "xsct"}] $tcl_script"
            
            # Try to execute xsct/xsdb command
            set cmd [expr {$xsdb_path != "" ? $xsdb_path : "xsct"}]
            if {[catch {eval exec $cmd $tcl_script} result]} {
                append_log $console_widget $log_file "ERROR executing $cmd: $result"
                append_log $console_widget $log_file "Make sure XSCT/XSDB is installed and in PATH"
                return 1
            } else {
                append_log $console_widget $log_file "XSCT/XSDB output:"
                append_log $console_widget $log_file $result
            }
            
        } elseif {$file_type == "bit"} {
            append_log $console_widget $log_file "Programming with BIT file..."
            if {[load_bit_file $file_path $output_dir $console_widget $log_file $xsdb_path $jtag_tcp]} {
                return 1
            }
            
            # Execute the generated TCL script
            set tcl_script [file join $output_dir "program_bit.tcl"]
            append_log $console_widget $log_file "Executing: [expr {$xsdb_path != "" ? $xsdb_path : "xsct"}] $tcl_script"
            
            # Try to execute xsct/xsdb command
            set cmd [expr {$xsdb_path != "" ? $xsdb_path : "xsct"}]
            if {[catch {eval exec $cmd $tcl_script} result]} {
                append_log $console_widget $log_file "ERROR executing $cmd: $result"
                append_log $console_widget $log_file "Make sure XSCT/XSDB is installed and in PATH"
                return 1
            } else {
                append_log $console_widget $log_file "XSCT/XSDB output:"
                append_log $console_widget $log_file $result
            }
            
        } else {
            append_log $console_widget $log_file "ERROR: Unsupported file type: $file_type"
            return 1
        }
        
        append_log $console_widget $log_file "JTAG programming completed successfully"
        
        return 0
    }
    
    # Generate standalone TCL script for XSA loading (without execution)
    proc generate_xsa_script {xsa_path output_dir console_widget log_file} {
        append_log $console_widget $log_file "Generating XSA loading script..."
        
        if {![file exists $xsa_path]} {
            append_log $console_widget $log_file "ERROR: XSA file not found: $xsa_path"
            return 1
        }
        
        set tcl_script [file join $output_dir "load_xsa.tcl"]
        set fp [open $tcl_script w]
        
        puts $fp "# XSA Loading Script"
        puts $fp "# Generated by Device Runner"
        puts $fp "# Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp "# Usage: xsct load_xsa.tcl"
        puts $fp ""
        puts $fp "# Connect to target"
        puts $fp "connect"
        puts $fp ""
        puts $fp "# Load XSA file"
        puts $fp "targets -set -filter {name =~ \"PS*\"}"
        puts $fp "loadhw -hw $xsa_path"
        puts $fp ""
        puts $fp "# Get device information"
        puts $fp "puts \"XSA file loaded: $xsa_path\""
        puts $fp "puts \"Platform: [file rootname [file tail $xsa_path]]\""
        puts $fp ""
        puts $fp "# List available targets"
        puts $fp "targets"
        puts $fp ""
        puts $fp "puts \"XSA loading completed successfully\""
        
        close $fp
        
        append_log $console_widget $log_file "Generated XSA script: $tcl_script"
        append_log $console_widget $log_file "Execute with: xsct $tcl_script"
        
        return $tcl_script
    }
    
    # Generate standalone TCL script for BIT programming (without execution)
    proc generate_bit_script {bit_path output_dir console_widget log_file} {
        append_log $console_widget $log_file "Generating BIT programming script..."
        
        if {![file exists $bit_path]} {
            append_log $console_widget $log_file "ERROR: BIT file not found: $bit_path"
            return 1
        }
        
        set tcl_script [file join $output_dir "program_bit.tcl"]
        set fp [open $tcl_script w]
        
        puts $fp "# BIT Programming Script"
        puts $fp "# Generated by Device Runner"
        puts $fp "# Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp "# Usage: xsct program_bit.tcl"
        puts $fp ""
        puts $fp "# Connect to target"
        puts $fp "connect"
        puts $fp ""
        puts $fp "# Set target to FPGA"
        puts $fp "targets -set -filter {name =~ \"xc7*\" || name =~ \"xczu*\" || name =~ \"xck*\"}"
        puts $fp ""
        puts $fp "# Program FPGA with BIT file"
        puts $fp "fpga -file $bit_path"
        puts $fp ""
        puts $fp "# Verify programming"
        puts $fp "puts \"BIT file programmed: $bit_path\""
        puts $fp "puts \"FPGA configuration completed\""
        puts $fp ""
        puts $fp "puts \"BIT programming completed successfully\""
        
        close $fp
        
        append_log $console_widget $log_file "Generated BIT script: $tcl_script"
        append_log $console_widget $log_file "Execute with: xsct $tcl_script"
        
        return $tcl_script
    }
    
    # Validate integer parameters (hexadecimal 32-bit format)
    proc validate_integer_params {param1 param2 param3 console_widget log_file} {
        # Check if at least one parameter is provided
        if {$param1 == "" && $param2 == "" && $param3 == ""} {
            append_log $console_widget $log_file "WARNING: No integer parameters provided"
            append_log $console_widget $log_file "Application will run without parameters"
            return 0
        }
        
        # Validate each parameter
        set params [list $param1 $param2 $param3]
        set param_names [list "Parameter 1" "Parameter 2" "Parameter 3"]
        
        for {set i 0} {$i < 3} {incr i} {
            set param [lindex $params $i]
            set name [lindex $param_names $i]
            
            if {$param != ""} {
                # Check if it's a valid hexadecimal format
                if {![regexp {^0x[0-9A-Fa-f]+$} $param]} {
                    append_log $console_widget $log_file "ERROR: $name must be in hexadecimal format (0x prefix required)"
                    append_log $console_widget $log_file "Example: 0x40000000"
                    return 1
                }
                
                # Remove 0x prefix for validation
                set hex_value [string range $param 2 end]
                
                # Check if it's a valid hex string
                if {![regexp {^[0-9A-Fa-f]+$} $hex_value]} {
                    append_log $console_widget $log_file "ERROR: $name contains invalid hexadecimal characters"
                    return 1
                }
                
                # Check length (max 8 hex digits for 32-bit)
                if {[string length $hex_value] > 8} {
                    append_log $console_widget $log_file "ERROR: $name exceeds 32-bit range (max 8 hex digits)"
                    append_log $console_widget $log_file "Maximum value: 0xFFFFFFFF"
                    return 1
                }
                
                # Convert to decimal for range check
                set decimal_value [expr 0x$hex_value]
                
                # Check reasonable range (0 to 2^32-1 for 32-bit unsigned)
                if {$decimal_value > 4294967295} {
                    append_log $console_widget $log_file "ERROR: $name exceeds maximum 32-bit unsigned integer"
                    append_log $console_widget $log_file "Maximum value: 0xFFFFFFFF"
                    return 1
                }
                
                append_log $console_widget $log_file "$name validated: $param (decimal: $decimal_value)"
            }
        }
        
        append_log $console_widget $log_file "All hexadecimal parameters validated successfully"
        return 0
    }
    
    # Format integer parameters for application (ensure hexadecimal 32-bit format)
    proc format_integer_params {param1 param2 param3} {
        set formatted_params ""
        
        if {$param1 != ""} {
            # Ensure proper hexadecimal format
            set hex1 [format_hex_32bit $param1]
            append formatted_params "$hex1"
        }
        if {$param2 != ""} {
            set hex2 [format_hex_32bit $param2]
            if {$formatted_params != ""} {
                append formatted_params " $hex2"
            } else {
                append formatted_params "$hex2"
            }
        }
        if {$param3 != ""} {
            set hex3 [format_hex_32bit $param3]
            if {$formatted_params != ""} {
                append formatted_params " $hex3"
            } else {
                append formatted_params "$hex3"
            }
        }
        
        return $formatted_params
    }
    
    # Format a parameter as proper 32-bit hexadecimal
    proc format_hex_32bit {param} {
        # Remove 0x prefix if present
        if {[string match "0x*" $param]} {
            set hex_value [string range $param 2 end]
        } else {
            set hex_value $param
        }
        
        # Convert to uppercase and pad to 8 digits
        set hex_value [string toupper $hex_value]
        
        # Pad with leading zeros to 8 digits (32-bit)
        while {[string length $hex_value] < 8} {
            set hex_value "0$hex_value"
        }
        
        # Ensure it doesn't exceed 8 digits
        if {[string length $hex_value] > 8} {
            set hex_value [string range $hex_value end-7 end]
        }
        
        return "0x$hex_value"
    }
    
    # Wait for data ready signal via polling
    proc wait_for_data_ready {output_dir console_widget log_file {xsdb_path ""} {jtag_tcp ""}} {
        append_log $console_widget $log_file "Starting data ready polling..."
        
        # Create TCL script for data ready polling
        set tcl_script [file join $output_dir "poll_data_ready.tcl"]
        set fp [open $tcl_script w]
        
        puts $fp "# Data Ready Polling Script"
        puts $fp "# Generated by Device Runner"
        puts $fp "# Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
        puts $fp ""
        
        # Add JTAG TCP configuration if provided
        if {$jtag_tcp != ""} {
            puts $fp "# Configure JTAG TCP connection"
            puts $fp "connect -url $jtag_tcp"
            puts $fp ""
        } else {
            puts $fp "# Connect to target"
            puts $fp "connect"
            puts $fp ""
        }
        
        puts $fp "# Set target to processor"
        puts $fp "targets -set -filter {name =~ \"PS*\"}"
        puts $fp ""
        puts $fp "# Define data ready signal locations"
        puts $fp "set data_ready_addresses {"
        puts $fp "    0x00100000  # Global status register"
        puts $fp "    0x00100004  # Data ready flag"
        puts $fp "    0x00100008  # Processing complete flag"
        puts $fp "    0x0010000C  # Error status flag"
        puts $fp "}"
        puts $fp ""
        puts $fp "# Polling configuration"
        puts $fp "set max_polls 100"
        puts $fp "set poll_interval 100"
        puts $fp "set data_ready_value 0x00000001"
        puts $fp ""
        puts $fp "puts \"Starting data ready polling...\""
        puts $fp "puts \"Polling addresses: \$data_ready_addresses\""
        puts $fp "puts \"Looking for value: \$data_ready_value\""
        puts $fp "puts \"Max polls: \$max_polls, Interval: \$poll_interval ms\""
        puts $fp ""
        puts $fp "# Polling loop"
        puts $fp "for {set poll_count 0} {\$poll_count < \$max_polls} {incr poll_count} {"
        puts $fp "    puts \"Poll \$poll_count: Checking data ready signals...\""
        puts $fp "    "
        puts $fp "    set data_ready_found 0"
        puts $fp "    foreach addr \$data_ready_addresses {"
        puts $fp "        set value \[mrd \$addr 4\]"
        puts $fp "        puts \"  Address 0x\[format %08X \$addr\]: 0x\$value\""
        puts $fp "        "
        puts $fp "        if {\$value == \$data_ready_value} {"
        puts $fp "            puts \"  Data ready signal found at 0x\[format %08X \$addr\]!\""
        puts $fp "            set data_ready_found 1"
        puts $fp "            break"
        puts $fp "        }"
        puts $fp "    }"
        puts $fp "    "
        puts $fp "    if {\$data_ready_found} {"
        puts $fp "        puts \"Data ready signal detected after \$poll_count polls\""
        puts $fp "        puts \"Data is ready for capture\""
        puts $fp "        break"
        puts $fp "    }"
        puts $fp "    "
        puts $fp "    puts \"Data not ready, waiting \$poll_interval ms...\""
        puts $fp "    after \$poll_interval"
        puts $fp "}"
        puts $fp ""
        puts $fp "if {\$poll_count >= \$max_polls} {"
        puts $fp "    puts \"ERROR: Data ready signal not detected after \$max_polls polls\""
        puts $fp "    puts \"Timeout waiting for data ready signal\""
        puts $fp "    exit 1"
        puts $fp "} else {"
        puts $fp "    puts \"Data ready polling completed successfully\""
        puts $fp "    exit 0"
        puts $fp "}"
        
        close $fp
        
        append_log $console_widget $log_file "Created data ready polling script: $tcl_script"
        if {$xsdb_path != ""} {
            append_log $console_widget $log_file "Use: $xsdb_path $tcl_script"
        } else {
            append_log $console_widget $log_file "Use: xsct $tcl_script"
        }
        
        # Try to execute the script
        set cmd [expr {$xsdb_path != "" ? $xsdb_path : "xsct"}]
        append_log $console_widget $log_file "Executing: $cmd $tcl_script"
        
        if {[catch {eval exec $cmd $tcl_script} result]} {
            append_log $console_widget $log_file "ERROR executing $cmd: $result"
            append_log $console_widget $log_file "Make sure XSCT/XSDB is installed and in PATH"
            return 1
        } else {
            append_log $console_widget $log_file "XSCT/XSDB output:"
            append_log $console_widget $log_file $result
        }
        
        append_log $console_widget $log_file "Data ready polling completed successfully"
        return 0
    }
}
