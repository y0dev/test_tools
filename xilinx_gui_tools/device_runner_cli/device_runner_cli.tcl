#!/usr/bin/env tclsh
# Device Runner CLI - Command Line Interface
# Text-based interface similar to XLWP tool

# Global variables
set ::app_name "Device Runner CLI"
set ::version "2.0.0"
set ::output_dir "output"
set ::log_file ""
set ::console_widget ""

# Script mode configuration
set ::script_config_file ""
set ::script_config_array ""
set ::script_mode_enabled 0


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
set ::bit_file      ""

#--------------------------------------------------------------------
# This function parses an INI configuration file
#
#--------------------------------------------------------------------
#
# param ini_file: Path to the INI configuration file
#--------------------------------------------------------------------
proc parse_ini_file {ini_file} {
    global script_config_array
    
    if {![file exists $ini_file]} {
        puts "ERROR: INI file not found: $ini_file"
        return 0
    }
    
    puts "Parsing INI configuration file: $ini_file"
    log_message "Parsing INI configuration file: $ini_file"
    
    set fp [open $ini_file r]
    set current_section ""
    
    while {[gets $fp line] != -1} {
        # Remove leading/trailing whitespace
        set line [string trim $line]
        
        # Skip empty lines and comments
        if {$line == "" || [string match "#*" $line] || [string match ";*" $line]} {
            continue
        }
        
        # Check for section header [section]
        if {[string match "\[*\]" $line]} {
            set current_section [string range $line 1 end-1]
            puts "Found section: $current_section"
            continue
        }
        
        # Parse key=value pairs
        if {[string first "=" $line] > 0} {
            set key_value [split $line "="]
            set key [string trim [lindex $key_value 0]]
            set value [string trim [lindex $key_value 1]]
            
            # Remove quotes if present
            if {[string match "\"*\"" $value]} {
                set value [string range $value 1 end-1]
            }
            
            # Store in array with section prefix
            if {$current_section != ""} {
                set full_key "${current_section}.${key}"
            } else {
                set full_key $key
            }
            
            set script_config_array($full_key) $value
            puts "  $full_key = $value"
        }
    }
    
    close $fp
    puts "INI file parsing completed"
    log_message "INI file parsing completed"
    return 1
}

#--------------------------------------------------------------------
# This function gets an INI configuration value
#
#--------------------------------------------------------------------
#
# param key: Configuration key (with optional section prefix)
# param default_value: Default value if key not found (default: "")
#--------------------------------------------------------------------
proc get_ini_config {key {default_value ""}} {
    global script_config_array
    
    if {[info exists script_config_array($key)]} {
        return $script_config_array($key)
    } else {
        return $default_value
    }
}

#--------------------------------------------------------------------
# This function gets all INI configuration keys for a section
#
#--------------------------------------------------------------------
#
# param section: Section name to get keys from
#--------------------------------------------------------------------
proc get_ini_section_keys {section} {
    global script_config_array
    set keys {}
    
    foreach key [array names script_config_array "${section}.*"] {
        lappend keys [string range $key [expr [string length $section] + 1] end]
    }
    
    return $keys
}

#--------------------------------------------------------------------
# This function parses command line arguments and returns as array
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
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
    set args_array(bit_file)      ""

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
            "-ini_config" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(ini_config) [lindex $argv $i]
                    log_message "INI configuration file set to: $args_array(ini_config)"
                }
            }
            "-bit_file" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(bit_file) [lindex $argv $i]
                    log_message "Bit file set to: $args_array(bit_file)"
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
    set ::bit_file $args_array(bit_file)

    return [array get args_array]

}


#--------------------------------------------------------------------
# This function gets a specific command line argument
#
#--------------------------------------------------------------------
#
# param arg_name: Name of the argument to get
#--------------------------------------------------------------------
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

#--------------------------------------------------------------------
# This function sends output to stdout and log file if logging is on
#
#--------------------------------------------------------------------
#
# param str: String to output
# param nonewline: If 1, don't add newline (default: 0)
#--------------------------------------------------------------------
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


#--------------------------------------------------------------------
# This function redirects TCP socket data to stdout
#
#--------------------------------------------------------------------
#
# param tcl_chan_id: TCL channel ID for the TCP socket
#--------------------------------------------------------------------
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

#--------------------------------------------------------------------
# This function parses a command string and sets register bit/value
#
#--------------------------------------------------------------------
#
# param command: Command string to parse and execute
#--------------------------------------------------------------------
proc device_command {command} {
    global log_file
    
    # Default command register address
    set command_addr 0xXXXX0000
    
    # Log the command
    log_message "Device Command: $command"
    
    # Parse command string and map to register value
    set cmd_value 0
    set cmd_parts [split [string trim $command] " "]
    set cmd_type [string tolower [lindex $cmd_parts 0]]
    
    # Map command strings to register values
    switch -exact $cmd_type {
        "init" {
            set cmd_value 2
        }
        "run_app" {
            set cmd_value 3
        }
        "get_status" {
            set cmd_value 4
        }
        "capture_ram" {
            set cmd_value 5
        }
        "exit" {
            set cmd_value 8
        }
        "!esp!" {
            # Special command for script mode
            set cmd_value 0x00000001
        }
        default {
            # Try to parse as numeric value
            if {[string is integer -strict $cmd_type]} {
                set cmd_value $cmd_type
            } else {
                # Unknown command - set bit 0 as generic trigger
                set cmd_value 1
                log_message "Unknown command, using generic trigger: $command"
            }
        }
    }
    
    # Write command value to register
    mwr $command_addr $cmd_value
    
    log_message "Command written to register 0x[format %08X $command_addr]: 0x[format %08X $cmd_value]"
    
    return ""
}

#--------------------------------------------------------------------
# This function parses a command and reads response from register
#
#--------------------------------------------------------------------
#
# param command: Command string to parse
# param timeout: Timeout in milliseconds (default: 5000)
#--------------------------------------------------------------------
proc device_response {command {timeout 5000}} {
    global log_file
    
    # Default response register address
    set response_addr 0xXXXX0004
    
    # Log the response request
    log_message "Requesting device response for: $command"
    
    # Parse command to determine what to read
    set cmd_parts [split [string trim $command] " "]
    set cmd_type [string tolower [lindex $cmd_parts 0]]
    
    # Wait for response with timeout
    set response_value 0
    set attempts 0
    set max_attempts [expr {$timeout / 100}]
    
    while {$attempts < $max_attempts} {
        set response_value [mrd $response_addr]
        
        # Check if response is ready (non-zero value)
        if {$response_value != 0} {
            break
        }
        
        incr attempts
        after 100
    }
    
    # Format response based on command type
    set response ""
    switch -glob $cmd_type {
        "mrd*" {
            # Memory read - return the value
            set addr [lindex $cmd_parts 1]
            if {$addr != ""} {
                set response "0x$addr: 0x[format %08X $response_value]"
            } else {
                set response "0x[format %08X $response_value]"
            }
        }
        "get_status" {
            set response "Status: 0x[format %08X $response_value]"
        }
        default {
            set response "Response: 0x[format %08X $response_value]"
        }
    }
    
    # Log the response
    log_message "Device Response: $response"
    
    return $response
}

# Source the shared memory messages module
if {[file exists "messages.tcl"]} {
    source messages.tcl
    puts "Loaded shared memory messages module"
} else {
    puts "Warning: messages.tcl not found - shared memory communication disabled"
}


#--------------------------------------------------------------------
# This function connects to device, resets cores and connects to target a53_0
#
#--------------------------------------------------------------------
#
# param hw_server_host: Hardware server hostname or IP address
# param bit_file_path: Path to bit file for FPGA programming (optional)
#--------------------------------------------------------------------
proc conn_device {hw_server_host {bit_file_path ""}} {
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

    # Step 4: Find and Reset APU
    targets -set -nocase -filter {name =~"APU*"}
    puts "Step 4: Resetting APU..."
    rst -processor
    after 1000
    
    # Step 4: Initialize PSU
    #puts "Step 4: Initializing PSU..."
    #source psu_init.tcl
    #psu_init
    
    # Step 5: Program FPGA with bit file
    puts "Step 5: Programming FPGA..."
    if {$bit_file_path != ""} {
        if {[file exists $bit_file_path]} {
            puts "Programming FPGA with: $bit_file_path"
            fpga -f $bit_file_path
            puts "FPGA programming completed"
        } else {
            puts "Warning: Bit file not found: $bit_file_path"
        }
    } else {
        puts "Warning: No bit file specified for FPGA programming"
    }

    # Step 6: Disabling debug firewall
    configparams force-mem-access 1
    
    # Step 7: Connect to target a53_0
    puts "Step 7: Connecting to target a53_0..."
    targets -set -nocase -filter {name =~ "*a53*#0"}
    
    # Step 8: Verify target is ready
    rst -processor

    # Download FSBL
    dow $fsbl_path
    set bp_47_40_fsbl_bp [bpadd -addr &XFsbl_Exit]
    con -block -timeout 60
    bpremove $bp_47_40_fsbl_bp
    

    # Check if Microblaze is enabled
    set microblaze_enabled 0
    if {[info exists ::microblaze_enable]} {
        set microblaze_enabled $::microblaze_enable
    } elseif {[info exists ::script_config_array]} {
        set microblaze_enabled [get_ini_config "microblaze.enable" "0"]
    }
    
    # Convert string values to boolean
    if {[string is boolean -strict $microblaze_enabled]} {
        set microblaze_enabled [expr {$microblaze_enabled ? 1 : 0}]
    } elseif {[string equal -nocase $microblaze_enabled "true"] || [string equal -nocase $microblaze_enabled "yes"] || [string equal $microblaze_enabled "1"]} {
        set microblaze_enabled 1
    } else {
        set microblaze_enabled 0
    }
    
    # Setup MDM and Microblaze only if enabled
    if {$microblaze_enabled} {
        puts "Microblaze enabled - Setting up MDM and downloading Microblaze app..."
        
        # Setup MDM
        configparams mdm-detect-bscan-mask 2

        # Reset Microblaze
        targets -set -nocase -filter {name =~ "*microblaze*#0" && bscan=="USER2" } 

        # Download Microblaze App
        if {[info exists mb_elf] && $mb_elf != ""} {
            dow $mb_elf
            after 1000
            con
        } else {
            puts "Warning: Microblaze enabled but mb_elf not defined"
        }
    } else {
        puts "Microblaze disabled - Skipping Microblaze setup"
    }

    # Reset A53
    targets -set -nocase -filter {name =~ "*a53*#0"}
    rst -processor

}


#--------------------------------------------------------------------
# This function shows help information
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
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
    puts "  -ini_config <file>      INI configuration file for script mode"
    puts "  -bit_file <file>        Bit file for FPGA programming"
    puts "  -xsdb_path <path>       Path to XSDB executable"
    puts "  -jtag_tcp <url>         JTAG TCP connection URL"
    puts "  -help                   Show this help message"
    puts ""
    puts "Script Mode with INI Configuration:"
    puts "  device_runner_cli.tcl -mode script -ini_config config.ini"
    puts ""
    puts "INI File Format:"
    puts "  [connection]"
    puts "  hw_server=localhost"
    puts "  [registers]"
    puts "  command_addr=0xXXXX0000"
    puts "  response_addr=0xXXXX0004"
    puts "  startup_mode_addr=0xXXXX0008"
    puts "  [commands]"
    puts "  cmd1=init"
    puts "  cmd2=run_app"
    puts "  cmd3=get_status"
    puts ""
    puts "Examples:"
    puts "  device_runner_cli.tcl -arch zynq -mode user -hw_server localhost"
    puts "  device_runner_cli.tcl -mode script -ini_config my_config.ini"
    puts "  device_runner_cli.tcl -bit_file design.bit -mode user"
    puts "  device_runner_cli.tcl -xsdb_path C:/Xilinx/Vitis/2023.2/bin/xsdb.exe"
    puts "  device_runner_cli.tcl -jtag_tcp 192.168.1.100:3121"
}

#--------------------------------------------------------------------
# This function initializes the application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
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
        puts "Bit file              : $::bit_file"
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
            # Check if INI config file is provided
            set ini_config [get_cmd_arg "ini_config"]
            if {$ini_config != ""} {
                puts "Script mode: Using INI configuration file $ini_config"
                set ::script_mode_enabled 1
                set ::script_config_file $ini_config
            } elseif {$term_app != "" && $term_app != "device_runner_term.bat"} {
                puts "Script mode: Using script file $term_app"
            } else {
                puts "ERROR: Script mode requires either -ini_config or -term_app"
                puts "Please set -ini_config to your INI file path or -term_app to your script file path"
                exit 1
            }
        } elseif {$mode == "user"} {
            puts "User mode             : Interactive operation"
            puts "Terminal Application  : $term_app"
        } else {
            puts "ERROR: Invalid mode '$mode'. Must be 'user' or 'script'"
            exit 1
        }
    }

    # If script mode is enabled, parse INI file and get hardware server and bit file
    if {$mode == "script" && $::script_mode_enabled} {
        puts "Parsing INI configuration file for script mode..."
        if {![parse_ini_file $::script_config_file]} {
            puts "ERROR: Failed to parse INI file: $::script_config_file"
            exit 1
        }
        
        # Get hardware server and bit file from INI file
        set ini_hw_server [get_ini_config "connection.hw_server" $hw_server]
        set ini_bit_file [get_ini_config "fpga.bit_file" $::bit_file]
        
        puts "Hardware server from INI: $ini_hw_server"
        puts "Bit file from INI: $ini_bit_file"
        
        # Use INI values
        set hw_server $ini_hw_server
        set ::bit_file $ini_bit_file
    }

    # Connect to device, reset cores and connect to target a53_0
    conn_device $hw_server $::bit_file

    # Initialize shared memory communication if available
    if {[info exists ::shared_mem_base]} {
        puts "Initializing shared memory communication..."
        init_shared_memory
        puts "Shared memory communication ready"
    } else {
        puts "Shared memory communication not available - using legacy mode"
    }

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
        puts "Running INI-based script mode..."
        run_script_mode_from_ini $::script_config_file
        
        if {$boot_mode == "jtag"} {
            puts "Downloading Device Application .elf file"
            dow $app_elf
        }
        puts "Place A53_0 into execution state..."
        con
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
    
}

#--------------------------------------------------------------------
# This function clears the screen
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc clear_screen {} {
    # Clear screen (works on most terminals)
    puts "\033\[2J\033\[H"
}

#--------------------------------------------------------------------
# This function shows the ASCII art banner
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc show_banner {} {
    puts ""
    puts "########  ######## ##     ## ####  ######  ########     ######  ##       #### "
    puts "##     ## ##       ##     ##  ##  ##    ## ##          ##    ## ##        ##  "
    puts "##     ## ##       ##     ##  ##  ##       ##          ##       ##        ##  "
    puts "##     ## ######   ##     ##  ##  ##       ######      ##       ##        ##  "
    puts "##     ## ##        ##   ##   ##  ##       ##          ##       ##        ##  "
    puts "##     ## ##         ## ##    ##  ##    ## ##          ##    ## ##        ##  "
    puts "########  ########    ###    ####  ######  ########     ######  ######## #### "
    puts ""
    puts ""
    puts "    FPGA Application Runner"
    puts "    Command Line Interface"
    puts "    Device Runner CLI v$::version"
    puts ""
}


#--------------------------------------------------------------------
# This function displays recent log entries
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
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
}


#--------------------------------------------------------------------
# This function exits the application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
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

#--------------------------------------------------------------------
# This function quits the tool
#
#--------------------------------------------------------------------
#
# param exit_code: Exit code (0=success, 1=error)
#--------------------------------------------------------------------
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

#--------------------------------------------------------------------
# This function logs a message to the log file
#
#--------------------------------------------------------------------
#
# param message: Message string to log
#--------------------------------------------------------------------
proc log_message {message} {
    global log_file
    
    if {$log_file != ""} {
        set timestamp [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
        set fp [open $log_file a]
        puts $fp "$timestamp - $message"
        close $fp
    }
}

#--------------------------------------------------------------------
# This function generates BOOT.bin with archiving functionality
#
#--------------------------------------------------------------------
#
# param output_bin: Output BOOT.bin file path (default: "./BOOT.bin")
# param bif_file: BIF file path (default: "./boot.bif")
# param arch: Target architecture (default: "zynqmp")
#--------------------------------------------------------------------
proc generate_boot_bin {{output_bin "./BOOT.bin"} {bif_file "./boot.bif"} {arch "zynqmp"}} {
    # Check if a previous BOOT.bin exists
    if {[file exists $output_bin]} {
        # Generate timestamp (YYYYMMDD_HHMMSS)
        set timestamp [clock format [clock seconds] -format "%Y%m%d_%H%M%S"]
        
        # Create archive directory if not exists
        set archive_dir "./boot_archive"
        file mkdir $archive_dir

        # Build archived filename
        set archived_file "$archive_dir/BOOT_$timestamp.bin"
        
        # Move old BOOT.bin to archive
        file rename -force $output_bin $archived_file
        puts "Archived old BOOT.bin to $archived_file"
    }

    # Now generate the new one
    puts "Generating new BOOT.bin..."
    exec bootgen -image $bif_file -arch $arch -o i $output_bin -w on
    puts "New BOOT.bin created at $output_bin"
}

#--------------------------------------------------------------------
# This function runs INI-based script mode
#
#--------------------------------------------------------------------
#
# param ini_file: Path to INI configuration file
#--------------------------------------------------------------------
proc run_script_mode_from_ini {ini_file} {
    global script_config_array script_mode_enabled
    
    puts "Starting INI-based script mode..."
    log_message "Starting INI-based script mode with file: $ini_file"
    
    # Parse INI configuration file
    if {![parse_ini_file $ini_file]} {
        puts "ERROR: Failed to parse INI file: $ini_file"
        return 0
    }
    
    # Get configuration values
    set hw_server [get_ini_config "connection.hw_server" "localhost"]
    set command_addr [get_ini_config "registers.command_addr" "0xXXXX0000"]
    set response_addr [get_ini_config "registers.response_addr" "0xXXXX0004"]
    set startup_mode_addr [get_ini_config "registers.startup_mode_addr" "0xXXXX0008"]
    set log_file [get_ini_config "logging.log_file" "script_log.txt"]
    set timeout [get_ini_config "timing.timeout" "5000"]
    set retries [get_ini_config "timing.retries" "3"]
    set bit_file [get_ini_config "fpga.bit_file" ""]
    
    puts "Configuration loaded:"
    puts "  Hardware Server: $hw_server"
    puts "  Command Address: $command_addr"
    puts "  Response Address: $response_addr"
    puts "  Startup Mode Address: $startup_mode_addr"
    puts "  Log File: $log_file"
    puts "  Timeout: ${timeout}ms"
    puts "  Retries: $retries"
    puts "  Bit File: $bit_file"
    
    # Set script mode in startup register
    puts "Setting script mode in startup register..."
    mwr $startup_mode_addr 0x00000002  ;# JTAG Script Mode
    
    # Connect to hardware server
    puts "Connecting to hardware server: $hw_server"
    connect -url tcp:$hw_server:3121
    
    # Set target to A53 core
    puts "Setting target to A53 core..."
    targets -set -filter {name =~ "*A53*#0"}
    
    # Start JTAG terminal logging
    puts "Starting JTAG terminal logging to: $log_file"
    jtagterminal -start -file $log_file
    
    # Continue execution
    puts "Continuing execution..."
    con
    
    # Execute script commands from INI file
    execute_script_commands_from_ini
    
    # Stop JTAG terminal logging
    puts "Stopping JTAG terminal logging..."
    jtagterminal -stop
    
    log_message "INI-based script mode completed"
    puts "INI-based script mode completed"
    return 1
}

#--------------------------------------------------------------------
# This function executes script commands from INI configuration
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc execute_script_commands_from_ini {} {
    global script_config_array
    
    puts "Executing script commands from INI configuration..."
    
    # Get command sequence from INI
    set command_keys [get_ini_section_keys "commands"]
    
    if {[llength $command_keys] == 0} {
        puts "No commands found in INI file"
        return
    }
    
    foreach cmd_key $command_keys {
        set full_key "commands.$cmd_key"
        set command [get_ini_config $full_key]
        
        if {$command != ""} {
            puts "Executing command: $command"
            execute_script_command $command
        }
    }
}

#--------------------------------------------------------------------
# This function executes an individual script command
#
#--------------------------------------------------------------------
#
# param command: Command string to execute
#--------------------------------------------------------------------
proc execute_script_command {command} {
    global script_config_array
    
    # Use shared memory communication if available
    if {[info exists ::shared_mem_base]} {
        puts "Executing script command via shared memory: $command"
        set response [device_command_shared_memory $command]
        puts "Command response: $response"
        return $response
    }
    
    # Fallback to legacy register-based communication
    set command_addr [get_ini_config "registers.command_addr" "0xXXXX0000"]
    set response_addr [get_ini_config "registers.response_addr" "0xXXXX0004"]
    set timeout [get_ini_config "timing.timeout" "5000"]
    
    # Parse command and execute
    set cmd_parts [split $command " "]
    set cmd_type [lindex $cmd_parts 0]
    
    switch $cmd_type {
        "init" {
            puts "Executing INIT command..."
            mwr $command_addr 2  ;# Command 2 = init
            wait_for_response $response_addr $timeout
        }
        "run_app" {
            puts "Executing RUN_APP command..."
            mwr $command_addr 3  ;# Command 3 = run_app
            wait_for_response $response_addr $timeout
        }
        "set_param" {
            set param_name [lindex $cmd_parts 1]
            set param_value [lindex $cmd_parts 2]
            puts "Executing SET_PARAM command: $param_name = $param_value"
            # For now, just execute as init (would need parameter handling)
            mwr $command_addr 2
            wait_for_response $response_addr $timeout
        }
        "get_status" {
            puts "Executing GET_STATUS command..."
            mwr $command_addr 4  ;# Command 4 = get_status
            wait_for_response $response_addr $timeout
        }
        "capture_ram" {
            puts "Executing CAPTURE_RAM command..."
            mwr $command_addr 5  ;# Command 5 = capture_ram
            wait_for_response $response_addr $timeout
        }
        "delay" {
            set delay_ms [lindex $cmd_parts 1]
            puts "Executing DELAY command: ${delay_ms}ms"
            after $delay_ms
        }
        "exit" {
            puts "Executing EXIT command..."
            mwr $command_addr 0  ;# Clear command register
            return
        }
        default {
            puts "Unknown command: $cmd_type"
        }
    }
}

#--------------------------------------------------------------------
# This function waits for response from device
#
#--------------------------------------------------------------------
#
# param response_addr: Response register address
# param timeout: Timeout in milliseconds
#--------------------------------------------------------------------
proc wait_for_response {response_addr timeout} {
    puts "Waiting for response from address: $response_addr"
    
    for {set i 0} {$i < [expr $timeout / 100]} {incr i} {
        set resp [mrd $response_addr]
        if {$resp != 0} {
            puts "Command response: $resp"
            log_message "Command response received: $resp"
            return $resp
        }
        after 100
    }
    
    puts "Timeout waiting for response"
    log_message "Timeout waiting for response from $response_addr"
    return 0
}

#--------------------------------------------------------------------
# This function handles JTAG UART communication
#
#--------------------------------------------------------------------
#
# param hw_server_host: Hardware server hostname or IP address
# param command_addr: Command register address (default: "0xXXXX0000")
# param response_addr: Response register address (default: "0xXXXX0004")
# param log_file: Log file path (default: "hostlog.txt")
#--------------------------------------------------------------------
proc jtag_uart_communication {hw_server_host {command_addr "0xXXXX0000"} {response_addr "0xXXXX0004"} {log_file "hostlog.txt"}} {
    global log_file
    
    log_message "Starting JTAG UART communication with server: $hw_server_host"
    puts "Starting JTAG UART communication..."
    
    # Connect to hardware server
    puts "Connecting to hardware server: $hw_server_host"
    connect -url tcp:$hw_server_host:3121
    
    # Set target to A53 core
    puts "Setting target to A53 core..."
    targets -set -filter {name =~ "*A53*#0"}
    
    # Start JTAG terminal logging
    puts "Starting JTAG terminal logging to: $log_file"
    jtagterminal -start -file $log_file
    
    # Continue execution
    puts "Continuing execution..."
    con
    
    # Issue command #1
    puts "Issuing command to address: $command_addr"
    mwr $command_addr 1
    
    # Wait/poll response register
    puts "Polling response register at: $response_addr"
    for {set i 0} {$i < 100} {incr i} {
        set resp [mrd $response_addr]
        if {$resp != 0} {
            puts "Command response: $resp"
            log_message "Command response received: $resp"
            break
        }
        after 100
    }
    
    # Stop JTAG terminal logging
    puts "Stopping JTAG terminal logging..."
    jtagterminal -stop
    
    log_message "JTAG UART communication completed"
    puts "JTAG UART communication completed"
}

#--------------------------------------------------------------------
# This function tests shared memory communication
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc test_shared_memory_communication {} {
    puts "=== Testing Shared Memory Communication ==="
    
    # Check if shared memory is available
    if {![info exists ::shared_mem_base]} {
        puts "ERROR: Shared memory not available"
        return 0
    }
    
    puts "Shared memory base: 0x[format %08X $::shared_mem_base]"
    puts "Shared memory size: 0x[format %08X $::shared_mem_size]"
    
    # Test basic commands
    puts "\n--- Testing INIT Command ---"
    set result [device_command_shared_memory "init"]
    puts "INIT Result: $result"
    
    puts "\n--- Testing SET_CONFIG Commands ---"
    set result [device_command_shared_memory "set_config device_name TestDevice 1"]
    puts "SET_CONFIG device_name Result: $result"
    
    set result [device_command_shared_memory "set_config base_address 0x43C00000 2"]
    puts "SET_CONFIG base_address Result: $result"
    
    set result [device_command_shared_memory "set_config operation_mode 2 3"]
    puts "SET_CONFIG operation_mode Result: $result"
    
    puts "\n--- Testing GET_CONFIG Commands ---"
    set result [device_command_shared_memory "get_config device_name"]
    puts "GET_CONFIG device_name Result: $result"
    
    set result [device_command_shared_memory "get_config base_address"]
    puts "GET_CONFIG base_address Result: $result"
    
    set result [device_command_shared_memory "get_config operation_mode"]
    puts "GET_CONFIG operation_mode Result: $result"
    
    puts "\n--- Testing GET_STATUS Command ---"
    set result [device_command_shared_memory "get_status"]
    puts "GET_STATUS Result: $result"
    
    puts "\n--- Testing RUN_APP Command ---"
    set result [device_command_shared_memory "run_app"]
    puts "RUN_APP Result: $result"
    
    puts "\n--- Testing CAPTURE_RAM Command ---"
    set result [device_command_shared_memory "capture_ram"]
    puts "CAPTURE_RAM Result: $result"
    
    puts "\n=== Shared Memory Communication Test Completed ==="
    return 1
}

# Main entry point
if {[file tail $argv0] == [file tail [info script]]} {
    init_app
}

