#!/usr/bin/env tclsh
# Device Runner - Simplified Version
# Focused on: Load BIT file, Run application, Capture RAM data

package require Tk

# Source the helper library
set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir "lib" "helpers.tcl"]

# Global variables
set ::app_name "Device Runner"
set ::version "2.0.0"
set ::output_dir "output"
set ::log_file ""
set ::console_widget ""

# GUI Variables
set ::app_path ""
set ::bit_file ""
set ::param1 ""
set ::param2 ""
set ::param3 ""
set ::xsdb_path ""
set ::jtag_tcp ""
set ::data_ready_method "manual"
set ::capture_delay 5

# Initialize application
proc init_app {} {
    global app_name version
    
    # Parse command line arguments
    parse_command_line_args
    
    # Check command line arguments for batch mode
    if {[llength $::argv] >= 2 && [lindex $::argv 0] == "--batch"} {
        set config_file [lindex $::argv 1]
        run_batch_mode $config_file
    } else {
        create_gui
    }
}

# Parse command line arguments
proc parse_command_line_args {} {
    global argv xsdb_path jtag_tcp
    
    set i 0
    while {$i < [llength $argv]} {
        set arg [lindex $argv $i]
        
        if {$arg == "--xsdb-path"} {
            incr i
            if {$i < [llength $argv]} {
                set xsdb_path [lindex $argv $i]
            }
        } elseif {$arg == "--jtag-tcp"} {
            incr i
            if {$i < [llength $argv]} {
                set jtag_tcp [lindex $argv $i]
            }
        } elseif {$arg == "--help"} {
            show_help
            exit 0
        }
        incr i
    }
}

# Show help message
proc show_help {} {
    global app_name version
    
    puts "$app_name v$version"
    puts "================"
    puts ""
    puts "Usage: tclsh device_runner.tcl [options]"
    puts ""
    puts "Options:"
    puts "  --xsdb-path <path>     Path to XSDB executable"
    puts "  --jtag-tcp <host:port> JTAG TCP configuration"
    puts "  --batch <config.json>  Run in batch mode with config file"
    puts "  --help                Show this help message"
    puts ""
    puts "Examples:"
    puts "  tclsh device_runner.tcl"
    puts "  tclsh device_runner.tcl --xsdb-path \"/opt/Xilinx/Vitis/2023.2/bin/xsdb\""
    puts "  tclsh device_runner.tcl --jtag-tcp \"192.168.1.100:3121\""
    puts "  tclsh device_runner.tcl --batch sample_config.json"
    puts ""
}

# Create the GUI interface
proc create_gui {} {
    global app_name version console_widget output_dir log_file
    global app_path bit_file param1 param2 param3
    global xsdb_path jtag_tcp
    
    # Create main window
    wm title . $app_name
    wm geometry . "600x500"
    wm resizable . 1 1
    
    # Create main frame
    set main_frame [frame .main -padx 10 -pady 10]
    pack $main_frame -fill both -expand 1
    
    # Title
    label $main_frame.title -text $app_name -font {Arial 16 bold}
    pack $main_frame.title -pady {0 20}
    
    # Input section
    set input_frame [frame $main_frame.input -relief groove -bd 2 -padx 10 -pady 10]
    pack $input_frame -fill x -pady {0 10}
    
    label $input_frame.label -text "Device Configuration" -font {Arial 12 bold}
    pack $input_frame.label -anchor w
    
    # Application path
    frame $input_frame.app_path
    pack $input_frame.app_path -fill x -pady 5
    label $input_frame.app_path.label -text "Application Path:" -width 15 -anchor w
    pack $input_frame.app_path.label -side left
    entry $input_frame.app_path.entry -textvariable app_path -width 50
    pack $input_frame.app_path.entry -side left -fill x -expand 1
    button $input_frame.app_path.browse -text "Browse..." -command browse_app_path
    pack $input_frame.app_path.browse -side right -padx {5 0}
    
    # BIT file
    frame $input_frame.bit_file
    pack $input_frame.bit_file -fill x -pady 5
    label $input_frame.bit_file.label -text "BIT File:" -width 15 -anchor w
    pack $input_frame.bit_file.label -side left
    entry $input_frame.bit_file.entry -textvariable bit_file -width 50
    pack $input_frame.bit_file.entry -side left -fill x -expand 1
    button $input_frame.bit_file.browse -text "Browse..." -command browse_bit_file
    pack $input_frame.bit_file.browse -side right -padx {5 0}
    
    # Sequential Parameter Input
    frame $input_frame.params_frame -relief groove -bd 2 -padx 10 -pady 10
    pack $input_frame.params_frame -fill x -pady 10
    
    label $input_frame.params_frame.label -text "Application Parameters" -font {Arial 12 bold}
    pack $input_frame.params_frame.label -anchor w
    
    # Parameter 1 - Menu Selection
    frame $input_frame.params_frame.param1
    pack $input_frame.params_frame.param1 -fill x -pady 3
    label $input_frame.params_frame.param1.label -text "Parameter 1:" -width 15 -anchor w
    pack $input_frame.params_frame.param1.label -side left
    frame $input_frame.params_frame.param1.menu_frame
    pack $input_frame.params_frame.param1.menu_frame -side left -padx {10 0}
    radiobutton $input_frame.params_frame.param1.menu_frame.short -text "Short" -variable param1 -value "short" -command update_param1_value
    pack $input_frame.params_frame.param1.menu_frame.short -side left -padx {0 5}
    radiobutton $input_frame.params_frame.param1.menu_frame.medium -text "Medium" -variable param1 -value "medium" -command update_param1_value
    pack $input_frame.params_frame.param1.menu_frame.medium -side left -padx {0 5}
    radiobutton $input_frame.params_frame.param1.menu_frame.tall -text "Tall" -variable param1 -value "tall" -command update_param1_value
    pack $input_frame.params_frame.param1.menu_frame.tall -side left -padx {0 5}
    label $input_frame.params_frame.param1.desc -text "(Select from menu)" -font {Arial 9 italic}
    pack $input_frame.params_frame.param1.desc -side left -padx {10 0}
    
    # Parameter 2
    frame $input_frame.params_frame.param2
    pack $input_frame.params_frame.param2 -fill x -pady 3
    label $input_frame.params_frame.param2.label -text "Parameter 2:" -width 15 -anchor w
    pack $input_frame.params_frame.param2.label -side left
    entry $input_frame.params_frame.param2.entry -textvariable param2 -width 20
    pack $input_frame.params_frame.param2.entry -side left -padx {10 0}
    label $input_frame.params_frame.param2.desc -text "(e.g., 0x43C00000)" -font {Arial 9 italic}
    pack $input_frame.params_frame.param2.desc -side left -padx {10 0}
    
    # Parameter 3
    frame $input_frame.params_frame.param3
    pack $input_frame.params_frame.param3 -fill x -pady 3
    label $input_frame.params_frame.param3.label -text "Parameter 3:" -width 15 -anchor w
    pack $input_frame.params_frame.param3.label -side left
    entry $input_frame.params_frame.param3.entry -textvariable param3 -width 20
    pack $input_frame.params_frame.param3.entry -side left -padx {10 0}
    label $input_frame.params_frame.param3.desc -text "(e.g., 0x00001000)" -font {Arial 9 italic}
    pack $input_frame.params_frame.param3.desc -side left -padx {10 0}
    
    # Data Ready Handling
    frame $input_frame.data_ready_frame -relief groove -bd 2 -padx 10 -pady 10
    pack $input_frame.data_ready_frame -fill x -pady 10
    
    label $input_frame.data_ready_frame.label -text "Data Ready Handling" -font {Arial 12 bold}
    pack $input_frame.data_ready_frame.label -anchor w
    
    # Data Ready Method
    frame $input_frame.data_ready_frame.method
    pack $input_frame.data_ready_frame.method -fill x -pady 3
    label $input_frame.data_ready_frame.method.label -text "Method:" -width 15 -anchor w
    pack $input_frame.data_ready_frame.method.label -side left
    frame $input_frame.data_ready_frame.method.radio_frame
    pack $input_frame.data_ready_frame.method.radio_frame -side left -padx {10 0}
    radiobutton $input_frame.data_ready_frame.method.radio_frame.manual -text "Manual" -variable data_ready_method -value "manual" -command update_data_ready_method
    pack $input_frame.data_ready_frame.method.radio_frame.manual -side left -padx {0 5}
    radiobutton $input_frame.data_ready_frame.method.radio_frame.delay -text "Fixed Delay" -variable data_ready_method -value "delay" -command update_data_ready_method
    pack $input_frame.data_ready_frame.method.radio_frame.delay -side left -padx {0 5}
    radiobutton $input_frame.data_ready_frame.method.radio_frame.polling -text "Polling" -variable data_ready_method -value "polling" -command update_data_ready_method
    pack $input_frame.data_ready_frame.method.radio_frame.polling -side left -padx {0 5}
    
    # Delay Configuration
    frame $input_frame.data_ready_frame.delay_config
    pack $input_frame.data_ready_frame.delay_config -fill x -pady 3
    label $input_frame.data_ready_frame.delay_config.label -text "Delay (seconds):" -width 15 -anchor w
    pack $input_frame.data_ready_frame.delay_config.label -side left
    entry $input_frame.data_ready_frame.delay_config.entry -textvariable capture_delay -width 10
    pack $input_frame.data_ready_frame.delay_config.entry -side left -padx {10 0}
    label $input_frame.data_ready_frame.delay_config.desc -text "(Wait time before capture)" -font {Arial 9 italic}
    pack $input_frame.data_ready_frame.delay_config.desc -side left -padx {10 0}
    
    # Button section
    set button_frame [frame $main_frame.buttons]
    pack $button_frame -fill x -pady 10
    
    button $button_frame.run_workflow -text "Run Complete Workflow" -command run_complete_workflow -width 20
    pack $button_frame.run_workflow -side left -padx {0 5}
    
    button $button_frame.clear_log -text "Clear Log" -command clear_log -width 15
    pack $button_frame.clear_log -side left -padx 5
    
    button $button_frame.exit -text "Exit" -command exit_app -width 15
    pack $button_frame.exit -side right
    
    # Console section
    set console_frame [frame $main_frame.console -relief groove -bd 2 -padx 10 -pady 10]
    pack $console_frame -fill both -expand 1 -pady {10 0}
    
    label $console_frame.label -text "Console Output" -font {Arial 12 bold}
    pack $console_frame.label -anchor w
    
    # Create text widget with scrollbar
    frame $console_frame.text_frame
    pack $console_frame.text_frame -fill both -expand 1 -pady 5
    
    text $console_frame.text_frame.text -height 12 -width 80 -wrap word -state disabled
    scrollbar $console_frame.text_frame.scrollbar -orient vertical -command "$console_frame.text_frame.text yview"
    $console_frame.text_frame.text configure -yscrollcommand "$console_frame.text_frame.scrollbar set"
    
    pack $console_frame.text_frame.scrollbar -side right -fill y
    pack $console_frame.text_frame.text -side left -fill both -expand 1
    
    set console_widget $console_frame.text_frame.text
    
    # Initialize log file
    set log_file [file join $output_dir "device_runner.log"]
    DeviceRunner::setup_output_directory $output_dir
    
    # Add initial message
    DeviceRunner::append_log $console_widget $log_file "Device Runner v$version started"
    DeviceRunner::append_log $console_widget $log_file "Ready for complete workflow"
}

# Update parameter 1 value based on menu selection
proc update_param1_value {} {
    global param1
    # Convert menu selection to hexadecimal value
    switch $param1 {
        "short" {
            set param1 "0x00000001"
        }
        "medium" {
            set param1 "0x00000002"
        }
        "tall" {
            set param1 "0x00000003"
        }
    }
}

# Update data ready method handling
proc update_data_ready_method {} {
    global data_ready_method capture_delay
    # Enable/disable delay entry based on method
    if {$data_ready_method == "delay"} {
        # Enable delay configuration
        .main.input.data_ready_frame.delay_config.entry configure -state normal
    } else {
        # Disable delay configuration
        .main.input.data_ready_frame.delay_config.entry configure -state disabled
    }
}

# Browse for application path
proc browse_app_path {} {
    global app_path
    set filename [tk_getOpenFile -title "Select Application" -filetypes {
        {"Executable files" {.exe .bin .elf}}
        {"All files" {*}}
    }]
    if {$filename != ""} {
        set app_path $filename
    }
}

# Browse for BIT file
proc browse_bit_file {} {
    global bit_file
    set filename [tk_getOpenFile -title "Select BIT File" -filetypes {
        {"BIT files" {.bit}}
        {"All files" {*}}
    }]
    if {$filename != ""} {
        set bit_file $filename
    }
}

# Run complete workflow: Load BIT -> Run App -> Wait for Data -> Capture RAM
proc run_complete_workflow {} {
    global app_path bit_file param1 param2 param3 output_dir console_widget log_file
    global xsdb_path jtag_tcp data_ready_method capture_delay
    
    # Validate inputs
    if {$app_path == ""} {
        DeviceRunner::append_log $console_widget $log_file "ERROR: Please select an application"
        return
    }
    
    if {$bit_file == ""} {
        DeviceRunner::append_log $console_widget $log_file "ERROR: Please select a BIT file"
        return
    }
    
    if {$param1 == ""} {
        DeviceRunner::append_log $console_widget $log_file "ERROR: Please select Parameter 1 (Short/Medium/Tall)"
        return
    }
    
    # Validate integer parameters
    set validation_result [DeviceRunner::validate_integer_params $param1 $param2 $param3 $console_widget $log_file]
    if {$validation_result != 0} {
        return
    }
    
    DeviceRunner::append_log $console_widget $log_file "Starting complete workflow..."
    
    # Step 1: Load BIT file
    DeviceRunner::append_log $console_widget $log_file "Step 1: Loading BIT file..."
    if {[DeviceRunner::program_fpga_jtag $bit_file "bit" $output_dir $console_widget $log_file $xsdb_path $jtag_tcp]} {
        DeviceRunner::append_log $console_widget $log_file "ERROR: BIT loading failed"
        return
    }
    DeviceRunner::append_log $console_widget $log_file "BIT file loaded successfully"
    
    # Step 2: Run application with parameters
    DeviceRunner::append_log $console_widget $log_file "Step 2: Running application..."
    set formatted_params [DeviceRunner::format_integer_params $param1 $param2 $param3]
    set full_args "$formatted_params"
    
    if {[DeviceRunner::run_application $app_path $full_args $output_dir $console_widget $log_file]} {
        DeviceRunner::append_log $console_widget $log_file "ERROR: Application execution failed"
        return
    }
    DeviceRunner::append_log $console_widget $log_file "Application completed successfully"
    
    # Step 3: Handle data ready timing
    DeviceRunner::append_log $console_widget $log_file "Step 3: Handling data ready timing..."
    if {$data_ready_method == "manual"} {
        DeviceRunner::append_log $console_widget $log_file "Manual mode: Waiting for user confirmation..."
        set result [tk_messageBox -message "Application has completed. Click OK when data is ready for capture." -type okcancel -title "Data Ready?"]
        if {$result == "cancel"} {
            DeviceRunner::append_log $console_widget $log_file "User cancelled data capture"
            return
        }
        DeviceRunner::append_log $console_widget $log_file "User confirmed data is ready"
    } elseif {$data_ready_method == "delay"} {
        DeviceRunner::append_log $console_widget $log_file "Fixed delay mode: Waiting $capture_delay seconds..."
        for {set i $capture_delay} {$i > 0} {incr i -1} {
            DeviceRunner::append_log $console_widget $log_file "Waiting... $i seconds remaining"
            after 1000
        }
        DeviceRunner::append_log $console_widget $log_file "Delay completed"
    } elseif {$data_ready_method == "polling"} {
        DeviceRunner::append_log $console_widget $log_file "Polling mode: Checking for data ready signal..."
        if {[DeviceRunner::wait_for_data_ready $output_dir $console_widget $log_file $xsdb_path $jtag_tcp]} {
            DeviceRunner::append_log $console_widget $log_file "ERROR: Data ready polling failed"
            return
        }
        DeviceRunner::append_log $console_widget $log_file "Data ready signal detected"
    }
    
    # Step 4: Capture RAM data
    DeviceRunner::append_log $console_widget $log_file "Step 4: Capturing RAM data..."
    if {[DeviceRunner::capture_ram_data $output_dir $console_widget $log_file $xsdb_path $jtag_tcp $param1 $param2 $param3]} {
        DeviceRunner::append_log $console_widget $log_file "ERROR: RAM data capture failed"
        return
    }
    DeviceRunner::append_log $console_widget $log_file "RAM data captured successfully"
    
    DeviceRunner::append_log $console_widget $log_file "Complete workflow finished successfully!"
}

# Clear log
proc clear_log {} {
    global console_widget
    $console_widget configure -state normal
    $console_widget delete 1.0 end
    $console_widget configure -state disabled
}

# Exit application
proc exit_app {} {
    exit 0
}

# Batch mode (simplified)
proc run_batch_mode {config_file} {
    global output_dir log_file
    
    puts "Batch mode not implemented in simplified version"
    puts "Use GUI mode for complete workflow"
    exit 1
}

# Start the application
init_app
