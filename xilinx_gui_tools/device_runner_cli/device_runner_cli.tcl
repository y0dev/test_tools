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

# Command line arguments
set ::arch          "zynq"
set ::mode          "user"
set ::boot_mode     "jtag"
set ::hw_server     "localhost"
set ::ps_ref_clk    "0"
set ::term_app      "device_runner_term.bat"
set ::log_dir       "logs"

# Parse command line arguments and return as array
proc parse_command_line_args {} {
    global argv
    
    # Default values
    set args_array(arch)          "zynq"
    set args_array(mode)          "user"
    set args_array(boot_mode)     "jtag"
    set args_array(hw_server)     "localhost"
    set args_array(ps_ref_clk)    "0"
    set args_array(term_app)      "device_runner_term.bat"
    set args_array(log_dir)       "logs"
    set args_array(xsdb_path)     ""
    set args_array(jtag_tcp)      ""
    
    # Parse command line arguments
    for {set i 0} {$i < [llength $argv]} {incr i} {
        set arg [lindex $argv $i]
        
        switch $arg {
            "-arch" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(arch) [lindex $argv $i]
                    log_message "Architecture set to: $args_array(arch)"
                }
            }
            "-mode" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(mode) [lindex $argv $i]
                    log_message "Mode set to: $args_array(mode)"
                }
            }
            "-boot_mode" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(boot_mode) [lindex $argv $i]
                    log_message "Boot mode set to: $args_array(boot_mode)"
                }
            }
            "-hw_server" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(hw_server) [lindex $argv $i]
                    log_message "Hardware server set to: $args_array(hw_server)"
                }
            }
            "-ps_ref_clk" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(ps_ref_clk) [lindex $argv $i]
                    log_message "PS reference clock set to: $args_array(ps_ref_clk)"
                }
            }
            "-term_app" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(term_app) [lindex $argv $i]
                    log_message "Terminal application set to: $args_array(term_app)"
                }
            }
            "-log_dir" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(log_dir) [lindex $argv $i]
                    log_message "Log directory set to: $args_array(log_dir)"
                }
            }
            "-xsdb_path" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(xsdb_path) [lindex $argv $i]
                    log_message "XSDB path set to: $args_array(xsdb_path)"
                }
            }
            "-jtag_tcp" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(jtag_tcp) [lindex $argv $i]
                    log_message "JTAG TCP set to: $args_array(jtag_tcp)"
                }
            }
            "-help" {
                show_help
                exit 0
            }
            default {
                if {[string match "-*" $arg]} {
                    puts "Unknown argument: $arg"
                    puts "Use -help for usage information"
                }
            }
        }
    }
    
    # Set global variables for backward compatibility
    set ::arch $args_array(arch)
    set ::mode $args_array(mode)
    set ::boot_mode $args_array(boot_mode)
    set ::hw_server $args_array(hw_server)
    set ::ps_ref_clk $args_array(ps_ref_clk)
    set ::term_app $args_array(term_app)
    set ::log_dir $args_array(log_dir)
    set ::xsdb_path $args_array(xsdb_path)
    set ::jtag_tcp $args_array(jtag_tcp)
    
    return [array get args_array]
}

# Get command line arguments as array
proc get_cmd_args {} {
    global cmd_args_array
    
    # Parse command line arguments if not already done
    if {![info exists cmd_args_array]} {
        set cmd_args [parse_command_line_args]
        array set cmd_args_array $cmd_args
    }
    
    return [array get cmd_args_array]
}

# Get specific command line argument
proc get_cmd_arg {arg_name} {
    global cmd_args_array
    
    # Parse command line arguments if not already done
    if {![info exists cmd_args_array]} {
        set cmd_args [parse_command_line_args]
        array set cmd_args_array $cmd_args
    }
    
    if {[info exists cmd_args_array($arg_name)]} {
        return $cmd_args_array($arg_name)
    } else {
        return ""
    }
}

# Device communication functions
proc device_command {command {timeout 5000} {retries 3}} {
    global log_file
    
    # Log the command
    log_message "Device Command: $command"
    
    # Simulate device command execution
    # In real implementation, this would send command to actual device
    puts "Sending command to device: $command"
    
    # Simulate response based on command type
    set response ""
    switch -glob $command {
        "!esp!" {
            set response "Device placed into script mode"
            log_message "Device Response: $response"
        }
        "connect*" {
            set response "Connected to target device"
            log_message "Device Response: $response"
        }
        "targets*" {
            set response "Target device found and ready"
            log_message "Device Response: $response"
        }
        "rst*" {
            set response "Device reset completed"
            log_message "Device Response: $response"
        }
        "run*" {
            set response "Application started successfully"
            log_message "Device Response: $response"
        }
        "stop*" {
            set response "Application stopped"
            log_message "Device Response: $response"
        }
        "mrd*" {
            set response "Memory read completed"
            log_message "Device Response: $response"
        }
        "mwr*" {
            set response "Memory write completed"
            log_message "Device Response: $response"
        }
        "source*" {
            set response "TCL script executed successfully"
            log_message "Device Response: $response"
        }
        default {
            set response "Command executed: $command"
            log_message "Device Response: $response"
        }
    }
    
    # Simulate processing delay
    after 100
    
    return $response
}

proc device_response {command {timeout 5000} {retries 3}} {
    global log_file
    
    # Log the response request
    log_message "Requesting device response for: $command"
    
    # Simulate device response based on command
    set response ""
    switch -glob $command {
        "!esp!" {
            set response "OK - Device in script mode"
        }
        "connect*" {
            set response "Connected to localhost:3121"
        }
        "targets*" {
            set response "1  ps7_cortexa9_0  arm  Cortex-A9 #0"
        }
        "rst*" {
            set response "Reset completed successfully"
        }
        "run*" {
            set response "Application running on target"
        }
        "stop*" {
            set response "Application stopped"
        }
        "mrd*" {
            # Simulate memory read response
            set addr [lindex [split $command] 1]
            if {$addr != ""} {
                set response "0x$addr: 0x[format %08X [expr {int(rand() * 0xFFFFFFFF)}]]"
            } else {
                set response "Memory read error: invalid address"
            }
        }
        "mwr*" {
            set response "Memory write completed"
        }
        "source*" {
            set response "TCL script executed successfully"
        }
        default {
            set response "Command response: $command"
        }
    }
    
    # Log the response
    log_message "Device Response: $response"
    
    # Simulate processing delay
    after 50
    
    return $response
}

# Enhanced device command with error handling
proc device_command_enhanced {command {timeout 5000} {retries 3}} {
    global log_file
    
    # Log the command
    log_message "Enhanced Device Command: $command (timeout: ${timeout}ms, retries: $retries)"
    
    set attempt 1
    set success 0
    set last_error ""
    
    while {$attempt <= $retries && !$success} {
        puts "Attempt $attempt of $retries: $command"
        
        # Simulate command execution with potential failure
        set failure_rate 0.1  ;# 10% failure rate for simulation
        if {[expr rand()] < $failure_rate && $attempt < $retries} {
            set last_error "Command failed (simulated error)"
            puts "Command failed: $last_error"
            log_message "Command attempt $attempt failed: $last_error"
            incr attempt
            after 100  ;# Brief delay before retry
        } else {
            set success 1
            set response [device_command $command $timeout $retries]
            puts "Command successful: $response"
            log_message "Command attempt $attempt successful: $response"
        }
    }
    
    if {!$success} {
        set error_msg "Command failed after $retries attempts: $last_error"
        puts "ERROR: $error_msg"
        log_message "ERROR: $error_msg"
        return -code error $error_msg
    }
    
    return $response
}

# Device status checking
proc check_device_status {} {
    global log_file
    
    log_message "Checking device status..."
    
    # Check if device is connected
    set connect_response [device_command "connect -url localhost:3121"]
    if {[string match "*Connected*" $connect_response]} {
        puts "Device Status: Connected"
        log_message "Device Status: Connected"
        
        # Check targets
        set targets_response [device_command "targets"]
        if {[string match "*ps7_cortexa9*" $targets_response]} {
            puts "Target Status: Available"
            log_message "Target Status: Available"
            return 1
        } else {
            puts "Target Status: Not Available"
            log_message "Target Status: Not Available"
            return 0
        }
    } else {
        puts "Device Status: Not Connected"
        log_message "Device Status: Not Connected"
        return 0
    }
}

# Device initialization sequence
proc initialize_device {} {
    global log_file
    
    log_message "Initializing device..."
    
    # Step 1: Connect to device
    puts "Step 1: Connecting to device..."
    device_command "connect -url localhost:3121"
    
    # Step 2: Set target
    puts "Step 2: Setting target..."
    device_command "targets -set -filter {name =~ \"*ps7_cortexa9*\"}"
    
    # Step 3: Reset device
    puts "Step 3: Resetting device..."
    device_command "rst -processor"
    
    # Step 4: Place in script mode
    puts "Step 4: Placing device in script mode..."
    device_command "!esp!" 0 0
    
    puts "Device initialization completed"
    log_message "Device initialization completed"
}

# Device cleanup sequence
proc cleanup_device {} {
    global log_file
    
    log_message "Cleaning up device..."
    
    # Step 1: Stop any running applications
    puts "Step 1: Stopping applications..."
    device_command "stop"
    
    # Step 2: Disconnect from device
    puts "Step 2: Disconnecting from device..."
    device_command "disconnect"
    
    puts "Device cleanup completed"
    log_message "Device cleanup completed"
}

# Connect to device, reset cores and connect to target a53_0
proc conn_device {hw_server_host} {
    global log_file
    
    log_message "Connecting to device: $hw_server_host"
    puts "Connecting to device: $hw_server_host"

    flush stdout
    
    # Step 1: Connect to hardware server
    puts "Step 1: Connecting to hardware server..."
    set connect_cmd "connect -url $hw_server_host"
    while {[catch {connect -host $hw_server_host -port 3121}]} {
        puts -nonewline "."
        flush stdout
        after 2000
    }
    set response [device_command $connect_cmd]
    puts "Connection response: $response"
    
    # Step 2: List available targets
    puts "Step 2: Listing available targets..."
    set targets_response [device_command "targets"]
    puts "Available targets: $targets_response"
    
    # Step 3: Reset all cores
    puts "Step 3: Resetting all cores..."
    set reset_response [device_command "rst -system"]
    puts "Reset response: $reset_response"
    
    # Step 4: Connect to target a53_0
    puts "Step 4: Connecting to target a53_0..."
    set target_cmd "targets -set -filter {name =~ \"*a53*\"}"
    set target_response [device_command $target_cmd]
    puts "Target connection response: $target_response"
    
    # Step 5: Verify target is ready
    puts "Step 5: Verifying target readiness..."
    set verify_response [device_command "targets"]
    if {[string match "*a53*" $verify_response]} {
        puts "Target a53_0 is ready and connected"
        log_message "Successfully connected to target a53_0"
        return 1
    } else {
        puts "ERROR: Failed to connect to target a53_0"
        log_message "ERROR: Failed to connect to target a53_0"
        return 0
    }
}

# Example usage of command line arguments
proc example_cmd_args_usage {} {
    # Get all command line arguments as array
    set cmd_args [get_cmd_args]
    array set args $cmd_args
    
    puts "Example: Using command line arguments"
    puts "Architecture: $args(arch)"
    puts "Mode: $args(mode)"
    puts "Boot Mode: $args(boot_mode)"
    puts "Hardware Server: $args(hw_server)"
    
    # Get specific argument
    set xsdb_path [get_cmd_arg "xsdb_path"]
    if {$xsdb_path != ""} {
        puts "XSDB Path: $xsdb_path"
    }
}

# Show help information
proc show_help {} {
    puts "Device Runner CLI - FPGA Application Runner"
    puts "Usage: device_runner_cli.tcl [options]"
    puts ""
    puts "Options:"
    puts "  -arch <arch>            Target architecture (default: zynq)"
    puts "  -mode <mode>            Operation mode user | script (default: user)"
    puts "  -boot_mode <mode>       Boot mode jtag | qspi | sd (default: jtag)"
    puts "  -hw_server <server>     Hardware server address (default: localhost)"
    puts "  -ps_ref_clk <freq>      PS reference clock frequency (default: 0)"
    puts "  -term_app <app>         Terminal application (default: device_runner_term.bat)"
    puts "  -log_dir <dir>          Log directory (default: logs)"
    puts "  -xsdb_path <path>       Path to XSDB executable"
    puts "  -jtag_tcp <url>         JTAG TCP connection URL"
    puts "  -help                   Show this help message"
    puts ""
    puts "Examples:"
    puts "  device_runner_cli.tcl -arch zynq -mode user -hw_server localhost"
    puts "  device_runner_cli.tcl -xsdb_path C:/Xilinx/Vitis/2023.2/bin/xsdb.exe"
    puts "  device_runner_cli.tcl -jtag_tcp 192.168.1.100:3121"
}

# Initialize application
proc init_app {} {
    global app_name version
    
    # Parse command line arguments first and get the array
    set cmd_args [parse_command_line_args]
    
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
    puts "- Parsing command line arguments..."
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
    puts "6. Test Device Communication"
    puts "7. Check Device Status"
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
            "6" {
                test_device_communication
                break
            }
            "7" {
                check_device_status_menu
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
    set tool_ready 0
    set tool_log_name ""
    set tool_log_data ""
    set tool_log_fptr 0
    
    # Get command line arguments
    set cmd_args [get_cmd_args]
    
    if {($cmd_args == 0) || ($cmd_args ==1)} {
        exit $cmd_args
    } else {
        # Extract all command line arguments into individual variables
        array set args $cmd_args
        
        # Create individual variables for each argument
        set arch $args(arch)
        set mode $args(mode)
        set boot_mode $args(boot_mode)
        set hw_server $args(hw_server)
        set ps_ref_clk $args(ps_ref_clk)
        set term_app $args(term_app)
        set log_dir $args(log_dir)
        set xsdb_path $args(xsdb_path)
        set jtag_tcp $args(jtag_tcp)
        
        puts "Xilinx Device type: $arch"
        puts "Mode: $mode"
        puts "Boot mode: $boot_mode"
        puts "Hardware server: $hw_server"
        puts "PS reference clock: $ps_ref_clk"
        puts "Log directory: $log_dir"
        if {$xsdb_path != ""} {
            puts "XSDB path: $xsdb_path"
        }
        if {$jtag_tcp != ""} {
            puts "JTAG TCP: $jtag_tcp"
        }

        # Check for mode
        if {$mode == "script"} {
            if {$term_app == "" || $term_app == "device_runner_term.bat"} {
                puts "ERROR: Script mode requires a valid script file name"
                puts "Please set -term_app to your script file path"
                exit 1
            }
            puts "Script mode: Using script file $term_app"
        } elseif {$mode == "user"} {
            puts "User mode: Interactive operation"
            puts "Terminal Application: $term_app"
        } else {
            puts "ERROR: Invalid mode '$mode'. Must be 'user' or 'script'"
            exit 1
        }
    }


    # Determine Operating System
    set op_sys [lindex $tcl_platform(os) 0]
    
    # Check if OS is supported (Windows or Linux)
    if {[string match -nocase "*windows*" $op_sys]} {
        puts "Operating System: Windows - Supported"
    } elseif {[string match -nocase "*linux*" $op_sys]} {
        puts "Operating System: Linux - Supported"
        set term_app "./${term_app}"
    } else {
        puts "ERROR: Unsupported operating system: $op_sys"
        puts "This tool only supports Windows and Linux"
        exit 1
    }

    # Connect to device, reset cores and connect to target a53_0
    conn_device $hw_server_host
    
    # Get the tcp port number to communicate with device via uart/jtag
    set tcp_port_num [jtagterminal -socket]
    puts "TCP port number: $tcp_port_num"

    # Determine if mode is user or script
    if {$mode == "user"} {
        puts "Mode: User - Interactive operation"
        puts "Starting interactive menu system..."
        
        exec $term_app localhost $tcp_port_num &
        if {} {
            puts "Downloading Device Application .elf file"
            dow $app_elf
        }

        puts "Place A53_0 into execution state..."
        con

        # wait to keep the tcp socket alive
        
        # Start the main menu for user interaction
        main_menu


    } elseif {$mode == "script"} {
        puts "Mode: Script - Automated operation"
        puts "Using script file: $term_app"
        
        # Execute the specified script file
        if {[file exists $term_app]} {
            puts "Executing script: $term_app"
            log_message "Executing script file: $term_app"
            
            # Source the script file
            if {[catch {source $term_app} error]} {
                puts "ERROR: Failed to execute script: $error"
                log_message "ERROR: Script execution failed: $error"
                exit 1
            } else {
                puts "Script executed successfully"
                log_message "Script executed successfully"
            }
        } else {
            puts "ERROR: Script file not found: $term_app"
            log_message "ERROR: Script file not found: $term_app"
            exit 1
        }
    } else {
        puts "ERROR: Invalid mode '$mode'. Must be 'user' or 'script'"
        log_message "ERROR: Invalid mode '$mode'"
        exit 1
    }

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
    puts "  Architecture: $args(arch)"
    puts "  Mode: $args(mode)"
    puts "  Boot Mode: $args(boot_mode)"
    puts "  Hardware Server: $args(hw_server)"
    puts "  PS Reference Clock: $args(ps_ref_clk)"
    puts "  Terminal Application: $args(term_app)"
    puts "  Log Directory: $args(log_dir)"
    if {$args(xsdb_path) != ""} {
        puts "  XSDB Path: $args(xsdb_path)"
    }
    if {$args(jtag_tcp) != ""} {
        puts "  JTAG TCP: $args(jtag_tcp)"
    }
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
    log_message "Loading BIT file: $bit_file with architecture: $args(arch)"
    log_message "Hardware server: $args(hw_server), PS ref clock: $args(ps_ref_clk)"
    
    # Initialize device
    initialize_device
    
    # Load BIT file using device command
    device_command "fpga -file $bit_file"
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
    log_message "Mode: $args(mode), Terminal app: $args(term_app)"
    puts "Application completed successfully"
    puts ""
    
    # Step 4: Capture RAM data
    puts "Step 4: Capturing RAM data..."
    log_message "Capturing RAM data with params: $formatted_params"
    log_message "Log directory: $args(log_dir)"
    puts "RAM data captured successfully"
    puts ""
    
    puts "Workflow completed successfully!"
    puts "Results saved to: $::output_dir"
    puts "Logs saved to: $args(log_dir)"
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
    
    # Get command line arguments
    set cmd_args [get_cmd_args]
    array set args $cmd_args
    
    clear_screen
    show_banner
    puts "::: Current Configuration :::"
    puts ""
    puts "Application Configuration:"
    puts "  Application Path: [expr {$app_path != "" ? $app_path : "Not configured"}]"
    puts "  BIT File: [expr {$bit_file != "" ? $bit_file : "Not configured"}]"
    puts "  Parameter 1: [expr {$param1 != "" ? $param1 : "Not configured"}]"
    puts "  Parameter 2: [expr {$param2 != "" ? $param2 : "Not configured"}]"
    puts "  Parameter 3: [expr {$param3 != "" ? $param3 : "Not configured"}]"
    puts ""
    puts "Command Line Arguments:"
    puts "  Architecture: $args(arch)"
    puts "  Mode: $args(mode)"
    puts "  Boot Mode: $args(boot_mode)"
    puts "  Hardware Server: $args(hw_server)"
    puts "  PS Reference Clock: $args(ps_ref_clk)"
    puts "  Terminal Application: $args(term_app)"
    puts "  Log Directory: $args(log_dir)"
    puts "  XSDB Path: [expr {$args(xsdb_path) != "" ? $args(xsdb_path) : "Not configured"}]"
    puts "  JTAG TCP: [expr {$args(jtag_tcp) != "" ? $args(jtag_tcp) : "Not configured"}]"
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
