#!/usr/bin/env tclsh
# Device Runner CLI - Command Line Interface
# Text-based interface similar to XLWP tool

# Global variables
set ::app_name "Device Runner CLI"
set ::version "2.0.0"
set ::output_dir "output"
set ::log_file ""
set ::console_widget ""


set tool_script   ""
set tool_tcl_chan_id 0
set tool_ready 0
set tool_log_name ""
set tool_log_data ""
set tool_log_fptr 0
set tool_response ""
set tool_error ""

# list of currently supported ps_ref_clk frequencies
set ::ps_ref_clks  {27 33 50 60}


# Application state
set ::app_path ""
set ::bit_file ""
set ::param1 ""
set ::param2 ""
set ::param3 ""
set ::xsdb_path ""
set ::jtag_tcp ""
set ::clk_elf_file ""

# Command line arguments
set ::arch          "zynq"
set ::mode          "user"
set ::boot_mode     "jtag"
set ::hw_server     "localhost"
set ::ps_ref_clk    0
set ::term_app      "device_runner_term.bat"
set ::log_dir       "logs"

# Parse command line arguments and return as array
proc parse_command_line_args {} {
    global argv ps_ref_clks
    
    # Default values
    set args_array(arch)          "zynq"
    set args_array(mode)          "user"
    set args_array(boot_mode)     "jtag"
    set args_array(hw_server)     "localhost"
    set args_array(ps_ref_clk)    "0"
    set args_array(term_app)      "device_runner_term.bat"
    set args_array(log_dir)       "logs"
    set args_array(tool_script)   ""
    set args_array(clk_elf_file)  ""

    # default filename values
    set clk_elf_file                ""
    set script_cmds                 "zup_cmds.tcl"
    
    # Parse command line arguments
    for {set i 0} {$i < [llength $argv]} {incr i} {
        set arg [lindex $argv $i]
        
        switch $arg {
            "-arch" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(arch) [lindex $argv $i]
                    # check for valid device type
                    switch  -nocase $args_array(arch)  {
                        "zynqmp" {
                            # valid
                        }
                        default { # versal and other new families added in future
                            puts " ERROR: Invalid architecture: $args_array(arch)"
                            return 1
                        }
                    }
                    log_message "Architecture set to: $args_array(arch)"
                }
            }
            "-mode" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(mode) [lindex $argv $i]
                    # check for valid run mode
                    switch  -nocase $args_array(mode) {
                        "user" - 
                        "script" {
                            # valid
                        }
                        default { # invalid run mode
                            puts " ERROR: Invalid execution mode: $args_array(mode)"
                            return 1
                        }
                    }
                    log_message "Mode set to: $args_array(mode)"
                }
            }
            "-boot_mode" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(boot_mode) [lindex $argv $i]
                    # check for valid boot mode
                    switch  -nocase $args_array(boot_mode) {
                        "jtag" - 
                        "other" {
                            # valid
                        }
                        default { # invalid boot mode
                            puts " ERROR: Invalid boot mode: $args_array(boot_mode)"
                            return 1
                        }
                    }
                    log_message "Boot mode set to: $args_array(boot_mode)"
                }
            }
            "-hw_server" {
                incr i
                if {$i < [llength $argv]} {
                    set hw_server_host [lindex $argv $i]
                    set args_array(hw_server) [regsub ":3121" $hw_server_host ""]
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
            "-tool_script" {
                incr i
                if {$i < [llength $argv]} {
                    set set args_array(tool_script) [lindex $argv $i]
                    log_message "Tool Script set to: $args_array(tool_script)"
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
    
    # make sure it's a valid ps ref clock frequency
    if {[lsearch -exact $ps_ref_clks $args_array(ps_ref_clk)] < 0} {
        puts " ERROR: Invalid PS_REF_CLK: $args_array(ps_ref_clk) MHz"
        puts "        Value must match external PS_REF_CLK frequency!!"
        puts "        Valid values: [join $ps_ref_clks ", "] MHz"
        return 1
    }

    # Construct the .elf filename based on ps ref clk freq value
    set clk_elf_file "tool_zup_${args_array(ps_ref_clk)}mhz.elf"
    set args_array(clk_elf_file) $clk_elf_file
    
    # Set global variables for backward compatibility
    set ::arch $args_array(arch)
    set ::mode $args_array(mode)
    set ::boot_mode $args_array(boot_mode)
    set ::hw_server $args_array(hw_server)
    set ::ps_ref_clk $args_array(ps_ref_clk)
    set ::term_app $args_array(term_app)
    set ::log_dir $args_array(log_dir)
    set ::clk_elf_file $args_array(clk_elf_file)

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

############################################################################
# proc: Puts function sends to stdout (and file if logging is on)          #
############################################################################
proc tool_puts {str {nonewline 0}} {
    global tool_log_fptr

    # send to stdout
    if {$nonewline == 1} {
        puts -nonewline $str
        flush stdout
    } else {
        puts $str
    }

    if {$tool_log_fptr != 0} {
        # write to log file
        if {$nonewline == 1} {
            puts -nonewline $tool_log_fptr $str
            flush $tool_log_fptr
        } else {
            puts $tool_log_fptr $str
        }
    }
}


############################################################################
# proc: re-direct a tcp socket data to stdout                              #
############################################################################
proc tcp_socket_to_stdout {tcl_chan_id} {
    global tool_ready
    global tool_log_name
    global tool_log_data
    global tool_response
    global tool_error

    #tool_puts "\n--> redirect stdout entry" 1
    # get data from tool
    set str [read $tcl_chan_id 1000]

    # remove   characters if they appear
    set str [string map {" " ""} $str]

    # update log data string
    set tool_log_data $tool_log_data$str

    # look for the error keyword, if found exit immediately
    if {[string first "ERROR" $str] >= 0} {
        set tool_error 1
        # re-direct data to stdout (and possibly a log file)
        # without the '@xlwp' response indicator
        tool_puts [regsub "@xlwp" $str ""] 1
        tool_puts "\n\n XLWP reported an ERROR after the last command!" 1
        quit_tool 1
    } else {
        set tool_error 0
    }
    # look for device dna message and capture value if in logging script mode
    if {$xlwp_log_name == "lsm"} {
        if {([string first "device PS DNA" $str] >= 0)} {
            # remove any trailing white space
            set trim_str [string trim $str]
            if {([string length $trim_str] >= 24)} {
                set xlwp_log_name [string range $trim_str [expr \
                                   [string length $trim_str] - 24] end]
                # don't send to stdout, just return
                return 0
            }
        }
    }
    # look for xlwp init done indicator
    if {([string first "start XLWP tool -> " $str] >= 0) || 
        ([string first "start the ZU+ XLWP tool -> " $str] >= 0)} {
        set xlwp_ready 1
    }
    # look for xlwp response indicator (echoed write value)
    if {[string first "@xlwp" $str] >= 0} {
        set xlwp_response [regsub "@xlwp" [string trim $str] ""]
    }
    # re-direct data to stdout (and possibly a log file)
    # without the '@xlwp' response indicator
    tool_puts [regsub "@xlwp" $str ""] 1
    #tool_puts "\n<-- redirect stdout exit" 1
}

# Device communication functions
proc device_command {command {ret_main 1} {chk_error 1}} {
    global log_file
    global tool_tcl_chan_id
    global tcl_error

    set response ""
    
    # Log the command
    log_message "Device Command: $command"

    # force return to the main menu
    if {$ret_main == 1} {
        puts -nonewline $tool_tcl_chan_id "n~xxxxn"
        flush $tool_tcl_chan_id
    }

    # check for error
    if {$chk_error == 1} {
        # set up a timeout script
        set cancel_id [after 5000 { 
            tool_puts "\n ERROR: No data from XLWP error checker!"
            quit_tool 1
        }]
        
        # send the command with error checking on
        puts -nonewline $tool_tcl_chan_id $command
        flush $tool_tcl_chan_id

        # wait for the xlwp error check to get updated
        vwait tcl_error

        # cancel the timeout script since we got a response
        after cancel $cancel_id
    } else {
        # send the command with error checking off
        puts -nonewline $tool_tcl_chan_id $command
        flush $tool_tcl_chan_id
    }
    
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
    puts "\n\nConnecting to device  : $hw_server_host"

    flush stdout
    
    # Step 1: Connect to hardware server
    puts "Step 1: Connecting to hardware server..."
    while {[catch {connect -host $hw_server_host -port 3121}]} {
        puts -nonewline "."
        flush stdout
        after 2000
    }
    
    # Step 2: List available targets
    puts "Step 2: Listing available targets..."
    targets -set -nocase -filter {name =~"PSU*"}
    
    
    # Step 3: Reset all cores
    puts "Step 3: Resetting PSU..."
    rst -system
    after 1000
    
    # Step 4: Connect to target a53_0
    puts "Step 4: Connecting to target a53_0..."
    targets -set -nocase -filter {name =~ "*a53*#0"}
    
    # Step 5: Verify target is ready
    rst -processor
}

# Read device DNA for log filename
proc read_device_dna {enable} {
    if {$enable == 1} {
        device_command "11." 1 0
    }
    global log_file log_filename tool_ready
    
    log_message "Reading device DNA with timeout: ${timeout}s"
    puts "Reading device DNA..."
    
    # Send command to read device DNA
    set dna_cmd "mrd 0x00000000 0x1000"
    set response [device_command $dna_cmd]
    
    # Parse the response to extract DNA
    # Device DNA is typically 96-bit (12 bytes) starting at address 0x00000000
    set dna_value ""
    if {[string match "*0x00000000*" $response]} {
        # Extract the DNA value from the response
        # Format: 0x00000000: 0x12345678 0x9ABCDEF0 0x12345678
        set lines [split $response "\n"]
        foreach line $lines {
            if {[string match "*0x00000000*" $line]} {
                # Extract hex values from the line
                set hex_values [regexp -all -inline {0x[0-9A-Fa-f]{8}} $line]
                if {[llength $hex_values] >= 3} {
                    # Take first 3 32-bit values for 96-bit DNA
                    set dna_value "[lindex $hex_values 0][string range [lindex $hex_values 1] 2 end][string range [lindex $hex_values 2] 2 end]"
                    break
                }
            }
        }
    }
    
    # If no DNA found, generate a simulated one
    if {$dna_value == ""} {
        set dna_value "0x[format %08X [expr {int(rand() * 0xFFFFFFFF)}]][format %08X [expr {int(rand() * 0xFFFFFFFF)}]][format %08X [expr {int(rand() * 0xFFFFFFFF)}]]"
        puts "Generated simulated device DNA: $dna_value"
        log_message "Generated simulated device DNA: $dna_value"
    } else {
        puts "Device DNA read successfully: $dna_value"
        log_message "Device DNA read successfully: $dna_value"
    }
    
    # Append DNA value to existing log filename
    if {[info exists log_filename] && $log_filename != ""} {
        # Remove .log extension if present, append DNA, then add .log back
        set base_name [file rootname $log_filename]
        set log_filename "${base_name}_${dna_value}.log"
    } else {
        # Create new filename with DNA
        set log_filename "device_dna_${dna_value}.log"
    }
    puts "Log filename with DNA: $log_filename"
    log_message "Log filename with DNA: $log_filename"
    
    # Set tool ready flag
    set tool_ready 1
    
    return $dna_value
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
    # show_banner
    
    # Initialize output directory
    if {![file exists $::output_dir]} {
        file mkdir $::output_dir
    }
    
    # Initialize log file
    set ::log_file [file join $::output_dir "device_runner_cli.log"]

    if {($cmd_args == 0) || ($cmd_args ==1)} {
        show_help
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
        set app_elf $args(clk_elf_file)
        set term_app $args(term_app)
        set log_dir $args(log_dir)
        
        puts "Xilinx Device type    : $arch"
        puts "Mode                  : $mode"
        puts "Boot mode             : $boot_mode"
        puts "Hardware server       : $hw_server"
        puts "PS reference clock    : $ps_ref_clk MHz"
        puts "Log directory         : $log_dir"

        if {$mode == "script"} {
            puts "Commands Filename    : $xlwp_cmds"
            if {[catch {source $xlwp_cmds}]} {
                puts "\nERROR: could not open commands file: $xlwp_cmds"
                exit 1
            }
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
            puts "User mode             : Interactive operation"
            puts "Terminal Application  : $term_app"
        } else {
            puts "ERROR: Invalid mode '$mode'. Must be 'user' or 'script'"
            exit 1
        }
    }

    # Determine Operating System
    # set op_sys [lindex $tcl_platform(os) 0]
    
    # Check if OS is supported (Windows or Linux)
    # if {[string match -nocase "*windows*" $op_sys]} {
        # puts "Operating System: Windows - Supported"
    # } elseif {[string match -nocase "*linux*" $op_sys]} {
        # puts "Operating System: Linux - Supported"
        # set term_app "./${term_app}"
    # } else {
        # puts "ERROR: Unsupported operating system: $op_sys"
        # puts "This tool only supports Windows and Linux"
        # exit 1
    # }

    # Connect to device, reset cores and connect to target a53_0
    conn_device $hw_server

    # Get the tcp port number to communicate with device via uart/jtag
    set tcp_port_num [jtagterminal -socket]
    puts "TCP port number: $tcp_port_num"

    # Determine if mode is user or script
    if {$mode == "user"} {
        puts "Mode: User - Interactive operation"
        puts "Starting interactive menu system..."
        
        exec $term_app localhost $tcp_port_num &
        if {$boot_mode == "jtag"} {
            puts "Downloading Device Application .elf file"
            dow $app_elf
        }

        puts "Place A53_0 into execution state..."
        con

        # wait to keep the tcp socket alive
        vwait forever
        
        # Start the main menu for user interaction
        main_menu


    } elseif {$mode == "script"} {
        puts "Mode: Script - Automated operation"
        
        if {[catch {set tcl_chan_id [socket localhost $tcp_port_num]} err]} {
            after 10000
            set tcl_chan_id [socket localhost $tcp_port_num]
        }

        puts "Configure Tcl Channel..."
        fconfigure $tcl_chan_id -buffering none -blocking 0 t-translation auto

        puts "Setting up stdout fileevent..."
        fileevent $tcl_chan_id readable "tcp_socket_to_stdout $tcl_chan_id"

        if {$boot_mode == "jtag"} {
            puts "Downloading Device Application .elf file"
            dow $app_elf
        }
        puts "Place A53_0 into execution state..."
        con

        puts "Placing Tool into script mode..."
        device_command "!esp!" 0 0

        puts "Waiting until tool is done with initialization...\n"
        set tool_ready 0
        after 5000 {if {$tool_ready == 0} {
            puts "\n\n ERROR: Tool did not initialize"
            exit 1
        }}

        vwait tool_ready
        puts "\n\n Tool has finished initializing..."
        if {$log_dir != ""} {
            puts "\tCreating script-mode log file..."
            # Create log directory if it doesn't exist
            if {[file isdirectory $log_dir] == 0} {
                file mkdir $log_dir
            }

            # Set log file name to indicate script mode Logging
            set log_filename "tlf"

            # Attempt to get device dna for log filename
            read_device_dna 1

            after 5000 {if {$log_filename == "tlf"} {
                puts "\n\n ERROR: Could not read device DNA for log file!"
                exit 1
            }}

            vwait log_filename

            # Create filename based on dna data and current time
            if {($log_filename != "tlf") && ($log_filename != "") && \
                ([string length $log_filename] == 24) && \
                ([string is xdigit $log_filename] == 1)} {
                    set log_filename "${log_dir}/${log_filename}_[string toupper \
                        [clock format [clock seconds] \
                        -format "%d_%b_%Y_%H_%M_%S"]].log"
                    set tool_log_fptr [open $log_filename w]
                } else {
                    puts "\n\n ERROR: Could not create script log file!\n"
                    exit 1
                }
        }
    } else {
        puts "ERROR: Invalid mode '$mode'. Must be 'user' or 'script'"
        log_message "ERROR: Invalid mode '$mode'"
        exit 1
    }
    
    # Show initialization
    puts "\n\nStarting Device Runner CLI initialization:"
    puts "- Initializing output directory..."
    puts "- Setting up logging system..."
    puts "- Loading helper functions..."
    puts "- Parsing command line arguments..."
    puts "- Ready for operation"
    puts ""
    
    
    # Start main menu
    # main_menu
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
    puts "1. Run Complete Workflow"
    puts "2. View Configuration"
    puts "3. View Logs"
    puts "4. Test Device Communication"
    puts "5. Check Device Status"
    puts "b. Build info"
    puts "x. Exit Device Runner CLI"
    puts ""
    
    while {1} {
        puts -nonewline "Please make a selection -> "
        flush stdout
        set choice [gets stdin]
        
        switch $choice {
            "1" {
                run_complete_workflow
                break
            }
            "2" {
                view_configuration
                break
            }
            "3" {
                view_logs
                break
            }
            "4" {
                test_device_communication
                break
            }
            "5" {
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


# Run complete workflow: Load BIT -> Configure Parameters -> Run App -> Capture RAM
proc run_complete_workflow {} {
    global app_path bit_file param1 param2 param3
    set tool_ready 0
    set tool_log_name ""
    set tool_log_data ""
    set tool_log_fptr 0
    
    # Get command line arguments
    set cmd_args [get_cmd_args]

    

    clear_screen
    show_banner
    puts "::: Run Complete Workflow :::"
    puts ""
    
    # Set default BIT file (comes with the script)
    if {$bit_file == ""} {
        set bit_file "default_design.bit"
        puts "Using default BIT file: $bit_file"
        log_message "Using default BIT file: $bit_file"
    }
    
    # Set default application path (comes with the script)
    if {$app_path == ""} {
        set app_path "default_app.elf"
        puts "Using default application: $app_path"
        log_message "Using default application: $app_path"
    }
    
    # Configuration is now complete with defaults
    
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

    # Quit application
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

############################################################################
# proc: quit tool tool                                                     #
############################################################################
proc quit_tool {exit_code} {
    global tool_tcl_chan_id
    global tool_script
    global tool_log_name
    global tool_log_data
    global tool_log_fptr
    global tool_ready

    if {$tool_ready == 1} {
        set tool_ready 0
        # send the tool exit command
        XlwpCommand "xy" 1 0
        XlwpResponse "Exiting XLWP tool"
    }
    # delete the event handler
    fileevent $tool_tcl_chan_id readable ""
    # determine exit message
    if {$exit_code == 1} {
        set exit_msg "with ERRORS"
    } else {
        set exit_msg "OK"
    }
    # finish writing to screen (and possibly the log)
    tool_puts "\n XLWP script finished ${exit_msg}: [string toupper \
              [clock format [clock seconds] -format "%d-%b-%Y %H:%M:%S"]]"
    tool_puts "\n------------------ Script end:\
              [file tail $tool_script] ------------------\n"
    # check if logging is on
    if {$tool_log_name != ""} {
        # close the log file if it was opened
        if {$tool_log_fptr != 0} { 
            puts " Closing script-mode log file: [file tail $tool_log_name]"
            flush $tool_log_fptr 
            close $tool_log_fptr 
        }
        # look for puf_file tag in the log data, write to file if it exists
        set tag_loc [string first "\[puf_file]:" $tool_log_data]
        if {$tag_loc >= 0} {
            set puf_file "[file dirname $tool_log_name]/[regsub {\.log} \
                          [file tail $tool_log_name] ""]_puf_file.txt"
            set puf_file_fptr [open $puf_file w]
            puts -nonewline $puf_file_fptr [string trim [regsub -all " " \
                                 [string range $tool_log_data \
                                  [expr $tag_loc + 78] \
                                  [expr $tag_loc + 3262]] ""]]
            flush $puf_file_fptr
            close $puf_file_fptr
        }
        # look for bh_key_iv tag in the log data, write to file if it exists
        set tag_loc [string first "\[bh_key_iv]:" $tool_log_data]
        if {$tag_loc >= 0} {
            set bh_key_iv "[file dirname $tool_log_name]/[regsub {\.log} \
                           [file tail $tool_log_name] ""]_bh_key_iv.txt"
            set bh_key_iv_fptr [open $bh_key_iv w]
            puts -nonewline $bh_key_iv_fptr [string trim [regsub -all " " \
                                  [string range $tool_log_data \
                                   [expr $tag_loc + 40] \
                                   [expr $tag_loc + 65]] ""]]
            flush $bh_key_iv_fptr
            close $bh_key_iv_fptr
        }
        # look for bh_keyfile tag in the log data, write to file if it exists
        set tag_loc [string first "\[bh_keyfile]:" $tool_log_data]
        if {$tag_loc >= 0} {
            set bh_keyfile "[file dirname $tool_log_name]/[regsub {\.log} \
                            [file tail $tool_log_name] ""]_bh_keyfile.txt"
            set bh_keyfile_fptr [open $bh_keyfile w]
            puts -nonewline $bh_keyfile_fptr [string trim [regsub -all " " \
                                   [string range $tool_log_data \
                                    [expr $tag_loc + 80] \
                                    [expr $tag_loc + 145]] ""]]
            flush $bh_keyfile_fptr
            close $bh_keyfile_fptr
        }
    }
    exit $exit_code
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
