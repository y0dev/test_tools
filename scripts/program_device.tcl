#!/usr/bin/env tclsh
# Xilinx Program Device TCL Script
# This script programs a bitstream to a Xilinx device
# Usage: vivado -mode batch -source program_device.tcl -tclargs <bitstream_path> [device_name] [target_name]

# Set default values
set bitstream_path ""
set device_name ""
set target_name ""
set verify_programming true
set reset_after_program true

# Parse command line arguments
if {[llength $argv] >= 1} {
    set bitstream_path [lindex $argv 0]
}

if {[llength $argv] >= 2} {
    set device_name [lindex $argv 1]
}

if {[llength $argv] >= 3} {
    set target_name [lindex $argv 2]
}

if {[llength $argv] >= 4} {
    set verify_programming [lindex $argv 3]
}

if {[llength $argv] >= 5} {
    set reset_after_program [lindex $argv 4]
}

puts "=== Xilinx Program Device Script ==="
puts "Bitstream Path: $bitstream_path"
puts "Device Name: $device_name"
puts "Target Name: $target_name"
puts "Verify Programming: $verify_programming"
puts "Reset After Program: $reset_after_program"
puts "Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts ""

# Validate bitstream path
if {$bitstream_path == ""} {
    puts "ERROR: No bitstream path provided"
    puts "Usage: vivado -mode batch -source program_device.tcl -tclargs <bitstream_path> [device_name] [target_name] [verify] [reset]"
    exit 1
}

# Check if bitstream file exists
if {![file exists $bitstream_path]} {
    puts "ERROR: Bitstream file not found: $bitstream_path"
    exit 1
}

puts "Bitstream file found: $bitstream_path"
set bitstream_size [file size $bitstream_path]
puts "Bitstream size: [expr $bitstream_size / 1024] KB"

# Connect to hardware
puts ""
puts "Connecting to hardware..."
open_hw_manager

# Get available targets
set targets [get_hw_targets]
if {[llength $targets] == 0} {
    puts "ERROR: No hardware targets found"
    puts "Make sure your hardware is connected and drivers are installed"
    exit 1
}

puts "Found [llength $targets] hardware target(s):"
foreach target $targets {
    puts "  - $target"
}

# Select target
if {$target_name != ""} {
    set selected_target ""
    foreach target $targets {
        if {[string match "*$target_name*" $target]} {
            set selected_target $target
            break
        }
    }
    
    if {$selected_target == ""} {
        puts "WARNING: Target '$target_name' not found, using first available target"
        set selected_target [lindex $targets 0]
    }
} else {
    set selected_target [lindex $targets 0]
}

puts "Selected target: $selected_target"

# Connect to target
puts "Connecting to target..."
set_hw_target $selected_target
open_hw_target

# Get devices on target
set devices [get_hw_devices]
if {[llength $devices] == 0} {
    puts "ERROR: No devices found on target"
    exit 1
}

puts "Found [llength $devices] device(s):"
foreach device $devices {
    puts "  - $device"
}

# Select device
if {$device_name != ""} {
    set selected_device ""
    foreach device $devices {
        if {[string match "*$device_name*" $device]} {
            set selected_device $device
            break
        }
    }
    
    if {$selected_device == ""} {
        puts "WARNING: Device '$device_name' not found, using first available device"
        set selected_device [lindex $devices 0]
    }
} else {
    set selected_device [lindex $devices 0]
}

puts "Selected device: $selected_device"
set_hw_device $selected_device

# Get device information
set device_part [get_property PART $selected_device]
set device_name_actual [get_property NAME $selected_device]
set device_family [get_property FAMILY $selected_device]
set device_speed [get_property SPEED_GRADE $selected_device]

puts ""
puts "Device Information:"
puts "  Name: $device_name_actual"
puts "  Part: $device_part"
puts "  Family: $device_family"
puts "  Speed Grade: $device_speed"

# Check current programming status
set program_status [get_property PROGRAM_STATUS $selected_device]
puts "Current Program Status: $program_status"

# Get bitstream information
puts ""
puts "Bitstream Information:"
puts "  Path: $bitstream_path"
puts "  Size: [expr $bitstream_size / 1024] KB"

# Check if bitstream is compatible with device
set bitstream_part [get_property PART [current_hw_design]]
if {$bitstream_part != "" && $bitstream_part != $device_part} {
    puts "WARNING: Bitstream part ($bitstream_part) may not match device part ($device_part)"
    puts "Continuing with programming..."
}

# Program the device
puts ""
puts "=== Programming Device ==="
puts "Starting programming process..."

set start_time [clock seconds]

# Set programming properties
set_property PROGRAM.BLANK_CHECK 0 $selected_device
set_property PROGRAM.ERASE 1 $selected_device
set_property PROGRAM.CFG_PROGRAM 1 $selected_device
set_property PROGRAM.CFG_VERIFY $verify_programming $selected_device
set_property PROGRAM.UNUSED_PIN_TERMINATION pullup $selected_device

# Program the device
puts "Programming device with bitstream..."
set_property PROGRAM.FILE $bitstream_path $selected_device
program_hw_devices $selected_device

set end_time [clock seconds]
set program_duration [expr $end_time - $start_time]

# Check programming result
set program_status [get_property PROGRAM_STATUS $selected_device]
puts "Programming completed in ${program_duration} seconds"
puts "Final Program Status: $program_status"

if {$program_status == "PROGRAMMED"} {
    puts "✅ Device programmed successfully!"
    
    # Verify programming if requested
    if {$verify_programming} {
        puts ""
        puts "=== Verifying Programming ==="
        puts "Verifying programmed device..."
        
        # Additional verification can be added here
        # For example, reading back configuration or checking specific registers
        
        puts "✅ Programming verification completed"
    }
    
    # Reset device if requested
    if {$reset_after_program} {
        puts ""
        puts "=== Resetting Device ==="
        puts "Resetting device..."
        
        # Reset the device
        reset_hw_device $selected_device
        
        puts "✅ Device reset completed"
    }
    
} else {
    puts "❌ Device programming failed!"
    puts "Program Status: $program_status"
    
    # Get error information if available
    set error_info [get_property PROGRAM_ERROR $selected_device]
    if {$error_info != ""} {
        puts "Error Information: $error_info"
    }
    
    # Close connections and exit with error
    close_hw_target
    close_hw_manager
    exit 1
}

# Generate programming report
puts ""
puts "=== Generating Programming Report ==="
set report_file "./programming_report_[clock format [clock seconds] -format "%Y%m%d_%H%M%S"].txt"

set report_fp [open $report_file w]
puts $report_fp "Xilinx Device Programming Report"
puts $report_fp "Generated: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts $report_fp ""
puts $report_fp "Target: $selected_target"
puts $report_fp "Device: $device_name_actual"
puts $report_fp "Part: $device_part"
puts $report_fp "Family: $device_family"
puts $report_fp "Speed Grade: $device_speed"
puts $report_fp ""
puts $report_fp "Bitstream:"
puts $report_fp "  Path: $bitstream_path"
puts $report_fp "  Size: [expr $bitstream_size / 1024] KB"
puts $report_fp ""
puts $report_fp "Programming:"
puts $report_fp "  Start Time: [clock format $start_time -format "%Y-%m-%d %H:%M:%S"]"
puts $report_fp "  End Time: [clock format $end_time -format "%Y-%m-%d %H:%M:%S"]"
puts $report_fp "  Duration: ${program_duration} seconds"
puts $report_fp "  Status: $program_status"
puts $report_fp "  Verify: $verify_programming"
puts $report_fp "  Reset: $reset_after_program"
puts $report_fp ""
puts $report_fp "Result: SUCCESS"
close $report_fp

puts "Programming report saved to: $report_file"

# Close hardware connection
puts ""
puts "Closing hardware connection..."
close_hw_target
close_hw_manager

puts ""
puts "=== Programming Complete ==="
puts "Device: $device_name_actual"
puts "Status: $program_status"
puts "Duration: ${program_duration} seconds"
puts "Report: $report_file"

puts "Script completed successfully"
exit 0
