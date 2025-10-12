#!/usr/bin/env tclsh
# Xilinx Debug Session TCL Script
# This script demonstrates debugging operations with Xilinx devices
# Usage: vivado -mode batch -source debug_session.tcl -tclargs <project_path> [device_name]

# Set default values
set project_path ""
set device_name ""
set debug_mode "interactive"  ;# interactive, batch, or monitor

# Parse command line arguments
if {[llength $argv] >= 1} {
    set project_path [lindex $argv 0]
}

if {[llength $argv] >= 2} {
    set device_name [lindex $argv 1]
}

if {[llength $argv] >= 3} {
    set debug_mode [lindex $argv 2]
}

puts "=== Xilinx Debug Session Script ==="
puts "Project Path: $project_path"
puts "Device Name: $device_name"
puts "Debug Mode: $debug_mode"
puts "Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts ""

# Connect to hardware
puts "Connecting to hardware..."
open_hw_manager

# Get available targets
set targets [get_hw_targets]
if {[llength $targets] == 0} {
    puts "ERROR: No hardware targets found"
    exit 1
}

puts "Found [llength $targets] hardware target(s):"
foreach target $targets {
    puts "  - $target"
}

# Select target
if {$device_name != ""} {
    set selected_target ""
    foreach target $targets {
        if {[string match "*$device_name*" $target]} {
            set selected_target $target
            break
        }
    }
    
    if {$selected_target == ""} {
        puts "WARNING: Device '$device_name' not found, using first available target"
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
set selected_device [lindex $devices 0]
puts "Selected device: $selected_device"
set_hw_device $selected_device

# Get device information
set device_part [get_property PART $selected_device]
set device_name_actual [get_property NAME $selected_device]
puts "Device Part: $device_part"
puts "Device Name: $device_name_actual"

# Check if device is programmed
set program_status [get_property PROGRAM_STATUS $selected_device]
puts "Device Program Status: $program_status"

if {$program_status != "PROGRAMMED"} {
    puts "WARNING: Device is not programmed. Some debug operations may not work."
}

# Get debug cores
set debug_cores [get_hw_ila]
if {[llength $debug_cores] > 0} {
    puts "Found [llength $debug_cores] ILA debug core(s):"
    foreach core $debug_cores {
        puts "  - $core"
    }
} else {
    puts "No ILA debug cores found"
}

# Get VIO cores
set vio_cores [get_hw_vio]
if {[llength $vio_cores] > 0} {
    puts "Found [llength $vio_cores] VIO debug core(s):"
    foreach core $vio_cores {
        puts "  - $core"
    }
} else {
    puts "No VIO debug cores found"
}

# Debug operations based on mode
if {$debug_mode == "interactive"} {
    puts ""
    puts "=== Interactive Debug Mode ==="
    puts "Debug session ready for interactive commands"
    puts "Available commands:"
    puts "  - run_hw_ila <core_name>  : Run ILA capture"
    puts "  - display_hw_ila_data <core_name> : Display captured data"
    puts "  - set_property <property> <value> <core_name> : Set debug properties"
    puts "  - get_property <property> <core_name> : Get debug properties"
    
    # Keep session open for interactive use
    puts "Debug session active. Use 'exit' to close."
    
} elseif {$debug_mode == "batch"} {
    puts ""
    puts "=== Batch Debug Mode ==="
    
    # Run ILA captures if available
    foreach ila_core $debug_cores {
        puts "Running ILA capture on: $ila_core"
        run_hw_ila $ila_core
        wait_on_hw_ila $ila_core
        
        # Display captured data
        puts "Displaying captured data from: $ila_core"
        display_hw_ila_data $ila_core
        
        # Save captured data
        set data_file "./debug_data_${ila_core}_[clock format [clock seconds] -format "%Y%m%d_%H%M%S"].csv"
        write_hw_ila_data -csv_file $data_file $ila_core
        puts "Captured data saved to: $data_file"
    }
    
    # Run VIO operations if available
    foreach vio_core $vio_cores {
        puts "Reading VIO values from: $vio_core"
        refresh_hw_vio $vio_core
        
        # Get VIO properties
        set vio_inputs [get_property INPUT_PROBES $vio_core]
        set vio_outputs [get_property OUTPUT_PROBES $vio_core]
        
        puts "VIO Inputs: $vio_inputs"
        puts "VIO Outputs: $vio_outputs"
    }
    
} elseif {$debug_mode == "monitor"} {
    puts ""
    puts "=== Monitor Debug Mode ==="
    puts "Starting continuous monitoring..."
    
    set monitor_count 0
    set max_monitor_cycles 10
    
    while {$monitor_count < $max_monitor_cycles} {
        puts "Monitor cycle: [expr $monitor_count + 1]/$max_monitor_cycles"
        
        # Monitor ILA cores
        foreach ila_core $debug_cores {
            set trigger_status [get_property TRIGGER_STATUS $ila_core]
            puts "ILA $ila_core trigger status: $trigger_status"
            
            if {$trigger_status == "TRIGGERED"} {
                puts "Trigger detected on $ila_core, capturing data..."
                run_hw_ila $ila_core
                wait_on_hw_ila $ila_core
                
                # Save triggered data
                set data_file "./triggered_data_${ila_core}_[clock format [clock seconds] -format "%Y%m%d_%H%M%S"].csv"
                write_hw_ila_data -csv_file $data_file $ila_core
                puts "Triggered data saved to: $data_file"
            }
        }
        
        # Monitor VIO cores
        foreach vio_core $vio_cores {
            refresh_hw_vio $vio_core
            puts "VIO $vio_core refreshed"
        }
        
        incr monitor_count
        after 1000  ;# Wait 1 second between cycles
    }
    
    puts "Monitoring completed"
}

# Generate debug report
puts ""
puts "=== Generating Debug Report ==="
set report_file "./debug_report_[clock format [clock seconds] -format "%Y%m%d_%H%M%S"].txt"

set report_fp [open $report_file w]
puts $report_fp "Xilinx Debug Session Report"
puts $report_fp "Generated: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts $report_fp ""
puts $report_fp "Target: $selected_target"
puts $report_fp "Device: $device_name_actual ($device_part)"
puts $report_fp "Program Status: $program_status"
puts $report_fp ""
puts $report_fp "Debug Cores:"
puts $report_fp "  ILA Cores: [llength $debug_cores]"
foreach core $debug_cores {
    puts $report_fp "    - $core"
}
puts $report_fp "  VIO Cores: [llength $vio_cores]"
foreach core $vio_cores {
    puts $report_fp "    - $core"
}
puts $report_fp ""
puts $report_fp "Debug Mode: $debug_mode"
puts $report_fp "Session Status: Completed"
close $report_fp

puts "Debug report saved to: $report_file"

# Close hardware connection
puts ""
puts "Closing hardware connection..."
close_hw_target
close_hw_manager

puts ""
puts "=== Debug Session Complete ==="
puts "Device: $device_name_actual"
puts "Debug Mode: $debug_mode"
puts "Report: $report_file"

puts "Script completed successfully"
exit 0
