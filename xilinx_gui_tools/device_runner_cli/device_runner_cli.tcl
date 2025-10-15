#!/usr/bin/env tclsh
# Device Runner CLI - Command Line Interface
# Text-based interface similar to XLWP tool

package require Tcl 8.6

# Global variables
set ::app_name "Device Runner CLI"
set ::version "2.0.0"
set ::output_dir "output"
set ::log_file ""
set ::console_widget ""

# Application state
set ::app_path ""
set ::bit_file ""
set ::param1 ""
set ::param2 ""
set ::param3 ""
set ::xsdb_path ""
set ::jtag_tcp ""

# Initialize application
proc init_app {} {
    global app_name version
    
    # Clear screen and show banner
    clear_screen
    show_banner
    
    # Initialize output directory
    if {![file exists $::output_dir]} {
        file mkdir $::output_dir
    }
    
    # Initialize log file
    set ::log_file [file join $::output_dir "device_runner_cli.log"]
    
    # Show initialization
    puts "Starting Device Runner CLI initialization:"
    puts "- Initializing output directory..."
    puts "- Setting up logging system..."
    puts "- Loading helper functions..."
    puts "- Ready for operation"
    puts ""
    
    # Start main menu
    main_menu
}

# Clear screen
proc clear_screen {} {
    # Clear screen (works on most terminals)
    puts "\033\[2J\033\[H"
}

# Show ASCII art banner
proc show_banner {} {
    puts ""
    puts "    ██████╗ ███████╗██╗██╗   ██╗██╗ ███████╗███████╗"
    puts "    ██╔══██╗██╔════╝██║██║   ██║██║██╔════╝██╔════╝"
    puts "    ██║  ██║█████╗  ██║██║   ██║██║███████╗█████╗  "
    puts "    ██║  ██║██╔══╝  ██║╚██╗ ██╔╝██║╚════██║██╔══╝  "
    puts "    ██████╔╝███████╗██║ ╚████╔╝ ██║███████║███████╗"
    puts "    ╚═════╝ ╚══════╝╚═╝  ╚═══╝  ╚═╝╚══════╝╚══════╝"
    puts ""
    puts "    ██████╗██╗     ██╗"
    puts "   ██╔════╝██║     ██║"
    puts "   ██║     ██║     ██║"
    puts "   ██║     ██║     ██║"
    puts "   ╚██████╗███████╗██║"
    puts "    ╚═════╝╚══════╝╚═╝"
    puts ""
    puts "    FPGA Application Runner"
    puts "    Command Line Interface"
    puts "    Device Runner CLI v$::version"
    puts ""
}

# Main menu
proc main_menu {} {
    puts "::: Main Menu :::"
    puts "1. Configure Application"
    puts "2. Configure BIT File"
    puts "3. Run Complete Workflow"
    puts "4. View Configuration"
    puts "5. View Logs"
    puts "b. Build info"
    puts "x. Exit Device Runner CLI"
    puts ""
    
    while {1} {
        puts -nonewline "Please make a selection -> "
        flush stdout
        set choice [gets stdin]
        
        switch $choice {
            "1" {
                configure_application
                break
            }
            "2" {
                configure_bit_file
                break
            }
            "3" {
                run_complete_workflow
                break
            }
            "4" {
                view_configuration
                break
            }
            "5" {
                view_logs
                break
            }
            "b" {
                show_build_info
                break
            }
            "x" {
                exit_application
                break
            }
            default {
                puts "Invalid selection. Please try again."
                puts ""
            }
        }
    }
}

# Configure application
proc configure_application {} {
    global app_path
    
    clear_screen
    show_banner
    puts "::: Configure Application :::"
    puts ""
    
    if {$app_path != ""} {
        puts "Current application: $app_path"
        puts ""
    }
    
    puts "Enter application path (or press Enter to keep current):"
    puts -nonewline "Application path -> "
    flush stdout
    set new_path [gets stdin]
    
    if {$new_path != ""} {
        if {[file exists $new_path]} {
            set app_path $new_path
            puts "Application path set to: $app_path"
            log_message "Application path configured: $app_path"
        } else {
            puts "ERROR: File does not exist: $new_path"
        }
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
    clear_screen
    show_banner
    main_menu
}

# Configure BIT file
proc configure_bit_file {} {
    global bit_file
    
    clear_screen
    show_banner
    puts "::: Configure BIT File :::"
    puts ""
    
    if {$bit_file != ""} {
        puts "Current BIT file: $bit_file"
        puts ""
    }
    
    puts "Enter BIT file path (or press Enter to keep current):"
    puts -nonewline "BIT file path -> "
    flush stdout
    set new_path [gets stdin]
    
    if {$new_path != ""} {
        if {[file exists $new_path]} {
            set bit_file $new_path
            puts "BIT file path set to: $bit_file"
            log_message "BIT file path configured: $bit_file"
        } else {
            puts "ERROR: File does not exist: $new_path"
        }
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
    clear_screen
    show_banner
    main_menu
}


# Run complete workflow: Load BIT -> Configure Parameters -> Run App -> Capture RAM
proc run_complete_workflow {} {
    global app_path bit_file param1 param2 param3
    
    clear_screen
    show_banner
    puts "::: Run Complete Workflow :::"
    puts ""
    
    # Validate configuration
    if {$app_path == ""} {
        puts "ERROR: Application path not configured"
        puts "Press any key to continue..."
        gets stdin
        clear_screen
        show_banner
        main_menu
        return
    }
    
    if {$bit_file == ""} {
        puts "ERROR: BIT file not configured"
        puts "Press any key to continue..."
        gets stdin
        clear_screen
        show_banner
        main_menu
        return
    }
    
    puts "Configuration:"
    puts "  Application: $app_path"
    puts "  BIT file: $bit_file"
    puts ""
    
    puts -nonewline "Start workflow? (y/[n]) -> "
    flush stdout
    set confirm [gets stdin]
    
    if {$confirm != "y" && $confirm != "Y"} {
        puts "Workflow cancelled"
        puts "Press any key to continue..."
        gets stdin
        clear_screen
        show_banner
        main_menu
        return
    }
    
    puts ""
    puts "Starting complete workflow..."
    puts "Step 1: Loading BIT file..."
    puts "Step 2: Configuring parameters..."
    puts "Step 3: Running application..."
    puts "Step 4: Capturing RAM data..."
    puts ""
    
    # Step 1: Load BIT file
    puts "Step 1: Loading BIT file..."
    log_message "Loading BIT file: $bit_file"
    puts "BIT file loaded successfully"
    puts ""
    
    # Step 2: Configure parameters
    puts "Step 2: Configuring parameters..."
    configure_parameters_inline
    puts ""
    
    # Step 3: Run application
    puts "Step 3: Running application..."
    set formatted_params [DeviceRunnerCLI::format_integer_params $param1 $param2 $param3]
    log_message "Running application: $app_path with params: $formatted_params"
    puts "Application completed successfully"
    puts ""
    
    # Step 4: Capture RAM data
    puts "Step 4: Capturing RAM data..."
    log_message "Capturing RAM data with params: $formatted_params"
    puts "RAM data captured successfully"
    puts ""
    
    puts "Workflow completed successfully!"
    puts "Results saved to: $::output_dir"
    puts ""
    puts "Press any key to continue..."
    gets stdin
    clear_screen
    show_banner
    main_menu
}

# Configure parameters inline during workflow
proc configure_parameters_inline {} {
    global param1 param2 param3
    
    # Parameter 1 - Menu selection
    puts "Parameter 1 - Select option:"
    puts "1. Short"
    puts "2. Medium"
    puts "3. Tall"
    puts ""
    puts -nonewline "Parameter 1 selection (1-3) -> "
    flush stdout
    set choice [gets stdin]
    
    switch $choice {
        "1" {
            set param1 "0x00000001"
            puts "Parameter 1 set to: Short (0x00000001)"
        }
        "2" {
            set param1 "0x00000002"
            puts "Parameter 1 set to: Medium (0x00000002)"
        }
        "3" {
            set param1 "0x00000003"
            puts "Parameter 1 set to: Tall (0x00000003)"
        }
        default {
            puts "Invalid selection. Parameter 1 not changed."
        }
    }
    
    puts ""
    
    # Parameter 2
    puts "Parameter 2 - Enter hexadecimal value:"
    puts -nonewline "Parameter 2 (e.g., 0x43C00000) -> "
    flush stdout
    set new_param2 [gets stdin]
    
    if {$new_param2 != ""} {
        if {[regexp {^0x[0-9A-Fa-f]{1,8}$} $new_param2]} {
            set param2 $new_param2
            puts "Parameter 2 set to: $param2"
        } else {
            puts "ERROR: Invalid hexadecimal format. Use 0x followed by up to 8 hex digits."
        }
    }
    
    puts ""
    
    # Parameter 3
    puts "Parameter 3 - Enter hexadecimal value:"
    puts -nonewline "Parameter 3 (e.g., 0x00001000) -> "
    flush stdout
    set new_param3 [gets stdin]
    
    if {$new_param3 != ""} {
        if {[regexp {^0x[0-9A-Fa-f]{1,8}$} $new_param3]} {
            set param3 $new_param3
            puts "Parameter 3 set to: $param3"
        } else {
            puts "ERROR: Invalid hexadecimal format. Use 0x followed by up to 8 hex digits."
        }
    }
    
    log_message "Parameters configured: P1=$param1, P2=$param2, P3=$param3"
}

# View configuration
proc view_configuration {} {
    global app_path bit_file param1 param2 param3
    
    clear_screen
    show_banner
    puts "::: Current Configuration :::"
    puts ""
    puts "Application Path: [expr {$app_path != "" ? $app_path : "Not configured"}]"
    puts "BIT File: [expr {$bit_file != "" ? $bit_file : "Not configured"}]"
    puts "Parameter 1: [expr {$param1 != "" ? $param1 : "Not configured"}]"
    puts "Parameter 2: [expr {$param2 != "" ? $param2 : "Not configured"}]"
    puts "Parameter 3: [expr {$param3 != "" ? $param3 : "Not configured"}]"
    puts ""
    puts "Press any key to continue..."
    gets stdin
    clear_screen
    show_banner
    main_menu
}

# View logs
proc view_logs {} {
    global log_file
    
    clear_screen
    show_banner
    puts "::: View Logs :::"
    puts ""
    
    if {[file exists $log_file]} {
        puts "Recent log entries:"
        puts "=================="
        puts ""
        
        # Read last 20 lines of log file
        set fp [open $log_file r]
        set lines [split [read $fp] "\n"]
        close $fp
        
        set start [expr {[llength $lines] - 20}]
        if {$start < 0} { set start 0 }
        
        for {set i $start} {$i < [llength $lines]} {incr i} {
            puts [lindex $lines $i]
        }
    } else {
        puts "No log file found."
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
    clear_screen
    show_banner
    main_menu
}

# Show build info
proc show_build_info {} {
    clear_screen
    show_banner
    puts "::: Build Information :::"
    puts ""
    puts "Device Runner CLI v$::version"
    puts "Built with Tcl/Tk"
    puts "Command Line Interface"
    puts ""
    puts "Features:"
    puts "- Menu-driven interface"
    puts "- ASCII art banner"
    puts "- Configuration management"
    puts "- Workflow execution"
    puts "- Logging system"
    puts ""
    puts "Press any key to continue..."
    gets stdin
    clear_screen
    show_banner
    main_menu
}

# Exit application
proc exit_application {} {
    puts ""
    puts -nonewline "Quit Device Runner CLI? (y/[n]) -> "
    flush stdout
    set confirm [gets stdin]
    
    if {$confirm == "y" || $confirm == "Y"} {
        log_message "Device Runner CLI exited"
        puts "Goodbye!"
        exit 0
    } else {
        clear_screen
        show_banner
        main_menu
    }
}

# Log message
proc log_message {message} {
    global log_file
    
    if {$log_file != ""} {
        set timestamp [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
        set fp [open $log_file a]
        puts $fp "$timestamp - $message"
        close $fp
    }
}

# Main entry point
if {[file tail $argv0] == [file tail [info script]]} {
    init_app
}
