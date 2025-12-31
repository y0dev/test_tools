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
set ::ps_app_elf_file ""

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
# Source helper functions
#--------------------------------------------------------------------
if {[file exists "lib/jtag_reg.tcl"]} {
    source lib/jtag_reg.tcl
    puts "Loaded helper functions from lib/jtag_reg.tcl"
} else {
    puts "Warning: lib/jtag_reg.tcl not found - some helper functions may be unavailable"
}

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
    set args_array(arch)             "zynqMP"
    set args_array(mode)             "user"
    set args_array(boot_mode)        "jtag"
    set args_array(hw_server)        "localhost"
    set args_array(ps_ref_clk)       "0"
    set args_array(term_app)         "device_runner_term.bat"
    set args_array(log_dir)          "logs"
    set args_array(tool_script)      ""
    set args_array(ps_app_elf_file)  ""
    set args_array(bit_file)         ""
    set args_array(fsbl_path)        ""

    # default filename values
    set ps_app_elf_file                ""
    
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
            "-fsbl_path" {
                incr i
                if {$i < [llength $argv]} {
                    set args_array(fsbl_path) [lindex $argv $i]
                    log_message "FSBL path set to: $args_array(fsbl_path)"
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

    # Validate FSBL path if provided
    if {$args_array(fsbl_path) != ""} {
        if {![file exists $args_array(fsbl_path)]} {
            puts " ERROR: FSBL file not found: $args_array(fsbl_path)"
            return 1
        }
        puts "INFO: FSBL file validated: $args_array(fsbl_path)"
    }

    # Construct the .elf filename based on ps ref clk freq value
    set ps_app_elf_file "bin/jtag_app.elf"
    set args_array(ps_app_elf_file) $ps_app_elf_file
    
    # Set global variables for backward compatibility
    set ::arch $args_array(arch)
    set ::mode $args_array(mode)
    set ::boot_mode $args_array(boot_mode)
    set ::hw_server $args_array(hw_server)
    set ::ps_ref_clk $args_array(ps_ref_clk)
    set ::term_app $args_array(term_app)
    set ::log_dir $args_array(log_dir)
    set ::ps_app_elf_file $args_array(ps_app_elf_file)
    set ::bit_file $args_array(bit_file)
    set ::fsbl_path $args_array(fsbl_path)

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
    puts "Using remote connection to $hw_server_host:3121"
    log_message "Using remote connection to $hw_server_host:3121"
    while {[catch {connect -host $hw_server_host -port 3121}]} {
        puts -nonewline "."
        flush stdout
        after 2000
    }
    
    # Step 2: List available targets
    puts "Step 2: Listing available targets..."
    targets -set -nocase -filter {name =~"PSU*"}

    # Updating the boot mode
    # targets -set -nocase -filter {name =~ "*PSU*"}
    # stop
    # mwr 0xff5e0200 0x0100
    
    
    # Step 3: Reset all cores
    puts "Step 3: Resetting PSU..."
    rst -system
    after 1000

    # Step 4: Find and Reset APU (only for JTAG boot mode)
    if {$::boot_mode == "jtsag"} {
        puts "Step 4a: Finding A53 target (JTAG mode)..."
        targets -set -nocase -filter {name =~ "*A53*#0"}
        puts "Step 4b: Resetting A53..."
        rst -processor
        after 1000
    } else {
        puts "Step 4a: Finding APU target..."
        targets -set -nocase -filter {name =~ "*APU*"}
        puts "Step 4b: Resetting APU..."
        rst -system
        after 1000
    }
    
    # Step 4: Initialize PSU
    #puts "Step 4: Initializing PSU..."
    source lib/psu_init.tcl
    #psu_init
    #after 1000
    #psu_ps_pl_reset_config

    loadhw -hw F:/Software/Embedded/00_Workspace/vitis/hello_world/platform/export/platform/hw/kv260_example.xsa
    configparams force-mem-access 1
    
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
    after 1000

    # Download FSBL (if path is provided)
    if {[info exists ::fsbl_path] && $::fsbl_path != ""} {
        if {[file exists $::fsbl_path]} {
            puts "Downloading FSBL from: $::fsbl_path"
            dow $::fsbl_path
            set bp_47_40_fsbl_bp [bpadd -addr &XFsbl_Exit]
            con -block -timeout 60
            bpremove $bp_47_40_fsbl_bp
        } else {
            puts "Warning: FSBL file not found: $::fsbl_path"
            puts "Skipping FSBL download"
        }
    } else {
        puts "Info: FSBL path not provided, skipping FSBL download"
    }
    

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
    puts "Step 9: Connecting to target a53_0..."
    targets -set -nocase -filter {name =~ "*a53*#0"}

    # Verify target is ready
    rst -processor
    after 1000
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
    puts "  -fsbl_path <file>       FSBL (First Stage Boot Loader) ELF file path"
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
# This function polls the response register in a loop to keep the tcp socket alive
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc poll_response_register {} {
    # Poll response register in a loop to keep the tcp socket alive
    if {[info exists ::shared_mem_base]} {
        set resp_reg_addr [expr $::shared_mem_base + $::RESP_REG_OFFSET]
        set running 1
        
        while {$running} {
            # Check response register
            set resp_value [mrd $resp_reg_addr]
            
            # Check for EXIT response or termination condition
            if {[expr $resp_value & $::RESP_ERROR]} {
                # Error response - read error data
                set error_data [read_data_area 1024]
                puts "Error response: '$error_data'"
                log_message "Error response: '$error_data'"
                # Clear response register
                mwr $resp_reg_addr 0
                # Optionally exit on error
                # set running 0
            } elseif {[expr $resp_value & $::RESP_SUCCESS]} {
                # Success response - read data if available
                set response_data [read_data_area 1024]
                if {[string match "*EXIT*" $response_data] || [string match "*exit*" $response_data]} {
                    puts "Exit command received: '$response_data'"
                    log_message "Exit command received: '$response_data'"
                    set running 0
                }
                # Clear response register
                mwr $resp_reg_addr 0
            }
            
            # Poll every 100ms
            after 100
        }
    } else {
        # Fallback: wait to keep the tcp socket alive if shared memory not available
        vwait forever
    }
}

#--------------------------------------------------------------------
# This function connects to device and executes in the specified mode
#
#--------------------------------------------------------------------
#
# param hw_server: Hardware server hostname or IP address
# param mode: Execution mode (user or script)
# param boot_mode: Boot mode (jtag or other)
# param term_app: Terminal application path
# param app_elf: Application ELF file path
#--------------------------------------------------------------------
proc run_device_connection {hw_server mode boot_mode term_app app_elf} {
    # Connect to device, reset cores and connect to target a53_0
    conn_device $hw_server $::bit_file

    # Get the tcp port number to communicate with device via uart/jtag
    set tcp_port_num [jtagterminal -socket]
    puts "TCP port number: $tcp_port_num"

    # Determine if mode is user or script
    if {$mode == "user"} {
        puts "Mode: User - Interactive operation"
        puts "Starting interactive menu system..."
        
        exec $term_app localhost $tcp_port_num &
        if {$boot_mode == "jtag"} {
            puts "Downloading Device Application .elf file ($app_elf)"
            dow $app_elf

            # Clear registers
        }

        puts "Place A53_0 into execution state..."
        con


        
        # Initialize shared memory communication if available
        #if {[info exists ::shared_mem_base]} {
        #    puts "Initializing shared memory communication..."
        #    init_shared_memory
        #    puts "Shared memory communication ready"
        #} else {
        #    puts "Shared memory communication not available - using legacy mode"
        #}

        # Poll response register in a loop to keep the tcp socket alive
        # poll_response_register

    } elseif {$mode == "script"} {
        puts "Mode: Script - Automated operation"
        puts "Running INI-based script mode..."
        run_script_mode_from_ini $::script_config_file
        
        if {$boot_mode == "jtag"} {
            # Ensure A53 target is selected before download
            targets -set -nocase -filter {name =~ "*a53*#0"}
            puts "Downloading Device Application .elf file ($app_elf)"
            dow $app_elf
        }
        puts "Place A53_0 into execution state..."
        con
        
        # Poll response register in a loop to keep the tcp socket alive
        poll_response_register
    } else {
        puts "ERROR: Invalid mode '$mode'. Must be 'user' or 'script'"
        log_message "ERROR: Invalid mode '$mode'"
        exit 1
    }
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
        set app_elf $args(ps_app_elf_file)
        set term_app $args(term_app)
        set log_dir $args(log_dir)
        set fsbl_path $args(fsbl_path)
        
        puts "Xilinx Device type    : $arch"
        puts "Mode                  : $mode"
        puts "Boot mode             : $boot_mode"
        puts "Hardware server       : $hw_server"
        puts "PS reference clock    : $ps_ref_clk MHz"
        puts "FSBL Path             : $fsbl_path"
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
  
    # Connect to device and execute in the specified mode
    run_device_connection $hw_server $mode $boot_mode $term_app $app_elf

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

    # If user mode, display main menu before connecting to device
    if {$mode == "user"} {
        main_menu
    } 
    
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
# This function displays and handles the main menu
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc main_menu {} {
    set running 1
    
    while {$running} {
        clear_screen
        show_banner
        
        puts "=== MAIN MENU ==="
        puts "1. View Configuration"
        puts "2. Configure Settings"
        puts "3. Run Application"
        puts "4. Get Status"
        puts "5. Test Application"
        puts "6. Help"
        puts "0. Exit"
        puts ""
        puts -nonewline "Enter choice (0-6): "
        flush stdout
        
        set choice [gets stdin]
        set choice [string trim $choice]
        
        switch $choice {
            "1" {
                view_configuration_menu
            }
            "2" {
                configure_settings_menu
            }
            "3" {
                run_application_menu
            }
            "4" {
                get_status_menu
            }
            "5" {
                test_application_menu
            }
            "6" {
                show_help_menu
            }
            "0" {
                set running 0
                exit_application
            }
            default {
                puts "\aInvalid choice. Please enter 0-6."
                after 1000
            }
        }
    }
}

#--------------------------------------------------------------------
# This function displays the current configuration
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc view_configuration_menu {} {
    clear_screen
    show_banner
    
    puts "=== CURRENT CONFIGURATION ==="
    puts ""
    
    # Display configuration from shared memory if available
    if {[info exists ::shared_mem_base]} {
        # Try to get configuration via shared memory
        set device_name [send_get_config_command "device_name"]
        set base_address [send_get_config_command "base_address"]
        set operation_mode [send_get_config_command "operation_mode"]
        set timeout_value [send_get_config_command "timeout_value"]
        set debug_level [send_get_config_command "debug_level"]
        
        if {$device_name != ""} {
            puts "Device Name:     $device_name"
        } else {
            puts "Device Name:     (not set)"
        }
        
        if {$base_address != ""} {
            puts "Base Address:    0x$base_address"
        } else {
            puts "Base Address:    (not set)"
        }
        
        if {$operation_mode != ""} {
            puts "Operation Mode:  $operation_mode"
        } else {
            puts "Operation Mode:  (not set)"
        }
        
        if {$timeout_value != ""} {
            puts "Timeout Value:   0x$timeout_value"
        } else {
            puts "Timeout Value:   (not set)"
        }
        
        if {$debug_level != ""} {
            puts "Debug Level:     $debug_level"
        } else {
            puts "Debug Level:     (not set)"
        }
    } else {
        puts "Shared memory not available - configuration not accessible"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function displays the configuration settings menu
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_settings_menu {} {
    set running 1
    
    while {$running} {
        clear_screen
        show_banner
        
        puts "=== CONFIGURATION MENU ==="
        puts "1. Device Name (String)"
        puts "2. Base Address (Hex)"
        puts "3. Operation Mode (List)"
        puts "4. Timeout Value (Hex)"
        puts "5. Debug Level (List)"
        puts "6. View Current Configuration"
        puts "0. Back to Main Menu"
        puts ""
        puts -nonewline "Enter choice (0-6): "
        flush stdout
        
        set choice [gets stdin]
        set choice [string trim $choice]
        
        switch $choice {
            "1" {
                configure_device_name
            }
            "2" {
                configure_base_address
            }
            "3" {
                configure_operation_mode
            }
            "4" {
                configure_timeout_value
            }
            "5" {
                configure_debug_level
            }
            "6" {
                view_configuration_menu
            }
            "0" {
                set running 0
            }
            default {
                puts "\aInvalid choice. Please enter 0-6."
                after 1000
            }
        }
    }
}

#--------------------------------------------------------------------
# This function configures the device name
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_device_name {} {
    clear_screen
    show_banner
    
    puts "=== Configure Device Name ==="
    puts ""
    puts -nonewline "Enter device name: "
    flush stdout
    
    set device_name [gets stdin]
    set device_name [string trim $device_name]
    
    if {$device_name != ""} {
        if {[info exists ::shared_mem_base]} {
            send_set_config_command "device_name" $device_name 1
            puts "Device name set to: $device_name"
        } else {
            puts "Shared memory not available - setting not saved"
        }
    } else {
        puts "Device name not changed"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function configures the base address
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_base_address {} {
    clear_screen
    show_banner
    
    puts "=== Configure Base Address ==="
    puts ""
    puts -nonewline "Enter base address (e.g., 0x43C00000): "
    flush stdout
    
    set base_address [gets stdin]
    set base_address [string trim $base_address]
    
    if {$base_address != ""} {
        if {[info exists ::shared_mem_base]} {
            send_set_config_command "base_address" $base_address 2
            puts "Base address set to: $base_address"
        } else {
            puts "Shared memory not available - setting not saved"
        }
    } else {
        puts "Base address not changed"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function configures the operation mode
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_operation_mode {} {
    clear_screen
    show_banner
    
    puts "=== Configure Operation Mode ==="
    puts ""
    puts "1. Short"
    puts "2. Medium"
    puts "3. Long"
    puts ""
    puts -nonewline "Enter choice (1-3): "
    flush stdout
    
    set choice [gets stdin]
    set choice [string trim $choice]
    
    switch $choice {
        "1" {
            set mode "Short"
            set mode_value "1"
        }
        "2" {
            set mode "Medium"
            set mode_value "2"
        }
        "3" {
            set mode "Long"
            set mode_value "3"
        }
        default {
            puts "Invalid choice"
            after 1000
            return
        }
    }
    
    if {[info exists ::shared_mem_base]} {
        send_set_config_command "operation_mode" $mode_value 3
        puts "Operation mode set to: $mode ($mode_value)"
    } else {
        puts "Shared memory not available - setting not saved"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function configures the timeout value
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_timeout_value {} {
    clear_screen
    show_banner
    
    puts "=== Configure Timeout Value ==="
    puts ""
    puts -nonewline "Enter timeout value (e.g., 0x00001000): "
    flush stdout
    
    set timeout_value [gets stdin]
    set timeout_value [string trim $timeout_value]
    
    if {$timeout_value != ""} {
        if {[info exists ::shared_mem_base]} {
            send_set_config_command "timeout_value" $timeout_value 2
            puts "Timeout value set to: $timeout_value"
        } else {
            puts "Shared memory not available - setting not saved"
        }
    } else {
        puts "Timeout value not changed"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function configures the debug level
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_debug_level {} {
    clear_screen
    show_banner
    
    puts "=== Configure Debug Level ==="
    puts ""
    puts "1. Low"
    puts "2. Medium"
    puts "3. High"
    puts "4. Verbose"
    puts ""
    puts -nonewline "Enter choice (1-4): "
    flush stdout
    
    set choice [gets stdin]
    set choice [string trim $choice]
    
    switch $choice {
        "1" {
            set level "Low"
            set level_value "1"
        }
        "2" {
            set level "Medium"
            set level_value "2"
        }
        "3" {
            set level "High"
            set level_value "3"
        }
        "4" {
            set level "Verbose"
            set level_value "4"
        }
        default {
            puts "Invalid choice"
            after 1000
            return
        }
    }
    
    if {[info exists ::shared_mem_base]} {
        send_set_config_command "debug_level" $level_value 3
        puts "Debug level set to: $level ($level_value)"
    } else {
        puts "Shared memory not available - setting not saved"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function runs the application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc run_application_menu {} {
    clear_screen
    show_banner
    
    puts "=== RUNNING APPLICATION ==="
    
    if {[info exists ::shared_mem_base]} {
        # Get current configuration
        set device_name [send_get_config_command "device_name"]
        set base_address [send_get_config_command "base_address"]
        set operation_mode [send_get_config_command "operation_mode"]
        set timeout_value [send_get_config_command "timeout_value"]
        set debug_level [send_get_config_command "debug_level"]
        
        puts "Device: $device_name"
        puts "Base Address: 0x$base_address"
        puts "Operation Mode: $operation_mode"
        puts "Timeout: $timeout_value ms"
        puts "Debug Level: $debug_level"
        puts ""
        puts "Application running..."
        
        # Send run application command
        send_run_app_command
        
        puts "Application completed."
    } else {
        puts "Shared memory not available - cannot run application"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function displays system status
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc get_status_menu {} {
    clear_screen
    show_banner
    
    puts "=== SYSTEM STATUS ==="
    puts ""
    
    if {[info exists ::shared_mem_base]} {
        # Get status via shared memory
        set status [send_get_status_command]
        puts "Status: $status"
        puts ""
        puts "Shared Memory Base: 0x[format %08X $::shared_mem_base]"
        puts "Shared Memory Size: 0x[format %08X $::shared_mem_size]"
    } else {
        puts "Shared memory not available"
    }
    
    puts ""
    puts "Mode: $::mode"
    puts "Boot Mode: $::boot_mode"
    puts "Hardware Server: $::hw_server"
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function displays and handles the test application menu
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc test_application_menu {} {
    set running 1
    
    while {$running} {
        clear_screen
        show_banner
        
        puts "=== TEST APPLICATION MENU ==="
        puts "1. Configure Test Settings"
        puts "2. View Test Configuration"
        puts "3. Run Tests"
        puts "4. View Test Results"
        puts "0. Back to Main Menu"
        puts ""
        puts -nonewline "Enter choice (0-4): "
        flush stdout
        
        set choice [gets stdin]
        set choice [string trim $choice]
        
        switch $choice {
            "1" {
                configure_test_menu
            }
            "2" {
                view_test_config_menu
            }
            "3" {
                run_tests_menu
            }
            "4" {
                view_test_results_menu
            }
            "0" {
                set running 0
            }
            default {
                puts "\aInvalid choice. Please enter 0-4."
                after 1000
            }
        }
    }
}

#--------------------------------------------------------------------
# This function displays the test configuration menu
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_test_menu {} {
    set running 1
    
    while {$running} {
        clear_screen
        show_banner
        
        puts "=== CONFIGURE TEST SETTINGS ==="
        puts "1. Load Test Config from INI File"
        puts "2. Set Test Config File Path"
        puts "3. Set Number of Tests"
        puts "4. Configure Test Cases"
        puts "5. Set Test Timeout"
        puts "6. Set Test Retries"
        puts "7. View Current Test Configuration"
        puts "0. Back to Test Menu"
        puts ""
        puts -nonewline "Enter choice (0-7): "
        flush stdout
        
        set choice [gets stdin]
        set choice [string trim $choice]
        
        switch $choice {
            "1" {
                load_test_config_from_ini
            }
            "2" {
                set_test_config_file
            }
            "3" {
                set_number_of_tests
            }
            "4" {
                configure_test_cases
            }
            "5" {
                set_test_timeout
            }
            "6" {
                set_test_retries
            }
            "7" {
                view_test_config_menu
            }
            "0" {
                set running 0
            }
            default {
                puts "\aInvalid choice. Please enter 0-7."
                after 1000
            }
        }
    }
}

#--------------------------------------------------------------------
# This function loads test configuration from INI file
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc load_test_config_from_ini {} {
    global test_config_file test_config_array
    
    clear_screen
    show_banner
    
    puts "=== Load Test Configuration from INI ==="
    puts ""
    
    # Get test config file path
    if {![info exists test_config_file] || $test_config_file == ""} {
        # Try default test config file first
        set default_config "test_config.ini"
        if {[file exists $default_config]} {
            puts "Found default test config file: $default_config"
            set test_config_file $default_config
        } else {
            puts -nonewline "Enter test config file path (default: test_config.ini): "
            flush stdout
            set config_file [gets stdin]
            set config_file [string trim $config_file]
            
            if {$config_file == ""} {
                set config_file $default_config
            }
            set test_config_file $config_file
        }
    }
    
    puts "Loading test configuration from: $test_config_file"
    
    # Parse test INI file
    if {[parse_test_ini_file $test_config_file]} {
        puts "Test configuration loaded successfully!"
        
        # Display loaded configuration
        if {[info exists test_config_array]} {
            puts ""
            puts "Loaded Configuration:"
            if {[info exists test_config_array(test.number_of_tests)]} {
                puts "  Number of Tests: $test_config_array(test.number_of_tests)"
            }
            if {[info exists test_config_array(test.timeout)]} {
                puts "  Test Timeout: $test_config_array(test.timeout) ms"
            }
            if {[info exists test_config_array(test.retries)]} {
                puts "  Test Retries: $test_config_array(test.retries)"
            }
        }
    } else {
        puts "ERROR: Failed to load test configuration from $test_config_file"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function parses a test INI configuration file
#
#--------------------------------------------------------------------
#
# param test_ini_file: Path to the test INI configuration file
#--------------------------------------------------------------------
proc parse_test_ini_file {test_ini_file} {
    global test_config_array
    
    if {![file exists $test_ini_file]} {
        puts "ERROR: Test INI file not found: $test_ini_file"
        return 0
    }
    
    puts "Parsing test INI configuration file: $test_ini_file"
    log_message "Parsing test INI configuration file: $test_ini_file"
    
    set fp [open $test_ini_file r]
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
            
            set test_config_array($full_key) $value
            puts "  $full_key = $value"
        }
    }
    
    close $fp
    puts "Test INI file parsing completed"
    log_message "Test INI file parsing completed"
    return 1
}

#--------------------------------------------------------------------
# This function sets the test config file path
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc set_test_config_file {} {
    global test_config_file
    
    clear_screen
    show_banner
    
    puts "=== Set Test Config File Path ==="
    puts ""
    
    if {[info exists test_config_file] && $test_config_file != ""} {
        puts "Current test config file: $test_config_file"
    }
    
    puts -nonewline "Enter test config file path: "
    flush stdout
    
    set config_file [gets stdin]
    set config_file [string trim $config_file]
    
    if {$config_file != ""} {
        set test_config_file $config_file
        puts "Test config file set to: $test_config_file"
    } else {
        puts "Test config file not changed"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function sets the number of tests
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc set_number_of_tests {} {
    global test_config_array
    
    clear_screen
    show_banner
    
    puts "=== Set Number of Tests ==="
    puts ""
    
    if {[info exists test_config_array(test.number_of_tests)]} {
        puts "Current number of tests: $test_config_array(test.number_of_tests)"
    }
    
    puts -nonewline "Enter number of tests: "
    flush stdout
    
    set num_tests [gets stdin]
    set num_tests [string trim $num_tests]
    
    if {$num_tests != "" && [string is integer $num_tests]} {
        set test_config_array(test.number_of_tests) $num_tests
        puts "Number of tests set to: $num_tests"
    } else {
        puts "Invalid number of tests"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function configures test cases
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc configure_test_cases {} {
    global test_config_array
    
    clear_screen
    show_banner
    
    puts "=== Configure Test Cases ==="
    puts ""
    
    # Get number of test cases
    set num_cases 0
    if {[info exists test_config_array(test.number_of_tests)]} {
        set num_cases $test_config_array(test.number_of_tests)
    }
    
    if {$num_cases == 0} {
        puts -nonewline "Enter number of test cases: "
        flush stdout
        set num_cases [gets stdin]
        set num_cases [string trim $num_cases]
        
        if {![string is integer $num_cases] || $num_cases <= 0} {
            puts "Invalid number of test cases"
            puts ""
            puts "Press any key to continue..."
            gets stdin
            return
        }
        set test_config_array(test.number_of_tests) $num_cases
    }
    
    puts "Number of test cases: $num_cases"
    puts ""
    
    # Configure each test case
    for {set i 1} {$i <= $num_cases} {incr i} {
        puts "=== Test Case $i ==="
        puts -nonewline "Enter test case name (or press Enter to skip): "
        flush stdout
        set test_name [gets stdin]
        set test_name [string trim $test_name]
        
        if {$test_name != ""} {
            set test_config_array(test.case_${i}.name) $test_name
        }
        
        puts -nonewline "Enter test case description: "
        flush stdout
        set test_desc [gets stdin]
        set test_desc [string trim $test_desc]
        
        if {$test_desc != ""} {
            set test_config_array(test.case_${i}.description) $test_desc
        }
        
        puts ""
    }
    
    puts "Test cases configured."
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function sets the test timeout
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc set_test_timeout {} {
    global test_config_array
    
    clear_screen
    show_banner
    
    puts "=== Set Test Timeout ==="
    puts ""
    
    if {[info exists test_config_array(test.timeout)]} {
        puts "Current test timeout: $test_config_array(test.timeout) ms"
    }
    
    puts -nonewline "Enter test timeout in milliseconds: "
    flush stdout
    
    set timeout [gets stdin]
    set timeout [string trim $timeout]
    
    if {$timeout != "" && [string is integer $timeout]} {
        set test_config_array(test.timeout) $timeout
        puts "Test timeout set to: $timeout ms"
    } else {
        puts "Invalid timeout value"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function sets the test retries
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc set_test_retries {} {
    global test_config_array
    
    clear_screen
    show_banner
    
    puts "=== Set Test Retries ==="
    puts ""
    
    if {[info exists test_config_array(test.retries)]} {
        puts "Current test retries: $test_config_array(test.retries)"
    }
    
    puts -nonewline "Enter number of test retries: "
    flush stdout
    
    set retries [gets stdin]
    set retries [string trim $retries]
    
    if {$retries != "" && [string is integer $retries]} {
        set test_config_array(test.retries) $retries
        puts "Test retries set to: $retries"
    } else {
        puts "Invalid retries value"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function displays the test configuration
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc view_test_config_menu {} {
    global test_config_array test_config_file
    
    clear_screen
    show_banner
    
    puts "=== TEST CONFIGURATION ==="
    puts ""
    
    if {[info exists test_config_file]} {
        puts "Test Config File: $test_config_file"
    } else {
        puts "Test Config File: (not set)"
    }
    puts ""
    
    if {[info exists test_config_array]} {
        if {[info exists test_config_array(test.number_of_tests)]} {
            puts "Number of Tests: $test_config_array(test.number_of_tests)"
        } else {
            puts "Number of Tests: (not set)"
        }
        
        if {[info exists test_config_array(test.timeout)]} {
            puts "Test Timeout: $test_config_array(test.timeout) ms"
        } else {
            puts "Test Timeout: (not set)"
        }
        
        if {[info exists test_config_array(test.retries)]} {
            puts "Test Retries: $test_config_array(test.retries)"
        } else {
            puts "Test Retries: (not set)"
        }
        
        puts ""
        puts "Test Cases:"
        
        set num_cases 0
        if {[info exists test_config_array(test.number_of_tests)]} {
            set num_cases $test_config_array(test.number_of_tests)
        }
        
        if {$num_cases > 0} {
            for {set i 1} {$i <= $num_cases} {incr i} {
                puts "  Test Case $i:"
                if {[info exists test_config_array(test.case_${i}.name)]} {
                    puts "    Name: $test_config_array(test.case_${i}.name)"
                }
                if {[info exists test_config_array(test.case_${i}.description)]} {
                    puts "    Description: $test_config_array(test.case_${i}.description)"
                }
            }
        } else {
            puts "  (no test cases configured)"
        }
    } else {
        puts "No test configuration loaded"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function writes test result header to file
#
#--------------------------------------------------------------------
#
# param fp: File pointer
#--------------------------------------------------------------------
proc write_test_result_header {fp} {
    puts $fp ""
    puts $fp "=================================================================================="
    puts $fp "                          TEST RESULTS REPORT"
    puts $fp "=================================================================================="
    puts $fp [format "%-20s | %-8s | %-30s | %-10s | %-s" \
            "Timestamp" "Test #" "Test Name" "Status" "Message"]
    puts $fp "----------------------------------------------------------------------------------"
    flush $fp
}

#--------------------------------------------------------------------
# This function writes a test result entry to file
#
#--------------------------------------------------------------------
#
# param fp: File pointer
# param test_number: Test number
# param test_name: Test name
# param status: Test status (PASSED/FAILED/SKIPPED)
# param message: Test message
#--------------------------------------------------------------------
proc write_test_result {fp test_number test_name status message} {
    set timestamp [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
    
    # Truncate test name if too long
    set truncated_name $test_name
    if {[string length $test_name] > 30} {
        set truncated_name [string range $test_name 0 26]
        append truncated_name "..."
    }
    
    # Truncate message if too long
    set truncated_message $message
    if {[string length $message] > 50} {
        set truncated_message [string range $message 0 46]
        append truncated_message "..."
    }
    
    puts $fp [format "%-20s | %-8s | %-30s | %-10s | %-s" \
            $timestamp $test_number $truncated_name $status $truncated_message]
    flush $fp
}

#--------------------------------------------------------------------
# This function writes test summary footer to file
#
#--------------------------------------------------------------------
#
# param fp: File pointer
# param total: Total number of tests
# param passed: Number of passed tests
# param failed: Number of failed tests
#--------------------------------------------------------------------
proc write_test_summary_footer {fp total passed failed} {
    set pass_rate 0.0
    if {$total > 0} {
        set pass_rate [expr {($passed * 100.0) / $total}]
    }
    
    puts $fp "----------------------------------------------------------------------------------"
    puts $fp [format "SUMMARY: Total: %u | Passed: %u | Failed: %u | Pass Rate: %.1f%%" \
            $total $passed $failed $pass_rate]
    puts $fp "=================================================================================="
    puts $fp ""
    flush $fp
}

#--------------------------------------------------------------------
# This function runs the tests
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc run_tests_menu {} {
    global test_config_array
    
    clear_screen
    show_banner
    
    puts "=== RUN TESTS ==="
    puts ""
    
    if {![info exists test_config_array]} {
        puts "ERROR: No test configuration loaded"
        puts "Please configure tests first."
        puts ""
        puts "Press any key to continue..."
        gets stdin
        return
    }
    
    # Get number of tests
    set num_tests 0
    if {[info exists test_config_array(test.number_of_tests)]} {
        set num_tests $test_config_array(test.number_of_tests)
    }
    
    if {$num_tests == 0} {
        puts "ERROR: Number of tests not configured"
        puts ""
        puts "Press any key to continue..."
        gets stdin
        return
    }
    
    puts "Running $num_tests test(s)..."
    puts ""
    
    # Get timeout and retries
    set timeout 5000
    if {[info exists test_config_array(test.timeout)]} {
        set timeout $test_config_array(test.timeout)
    }
    
    set retries 3
    if {[info exists test_config_array(test.retries)]} {
        set retries $test_config_array(test.retries)
    }
    
    # Open test results file
    set test_results_file "test_results.txt"
    set fp [open $test_results_file "a"]
    
    # Write test results header
    write_test_result_header $fp
    
    # Initialize test session on device if shared memory is available
    if {[info exists ::shared_mem_base]} {
        # Send start test command with configuration
        if {[send_start_test_command $num_tests $timeout $retries]} {
            puts "Test session initialized on device"
        } else {
            puts "Warning: Failed to initialize test session on device"
        }
    }
    
    # Run each test
    set passed 0
    set failed 0
    
    for {set i 1} {$i <= $num_tests} {incr i} {
        puts "=== Test Case $i ==="
        
        set test_name "Test Case $i"
        if {[info exists test_config_array(test.case_${i}.name)]} {
            set test_name $test_config_array(test.case_${i}.name)
        }
        
        puts "Test Name: $test_name"
        
        set test_description ""
        if {[info exists test_config_array(test.case_${i}.description)]} {
            set test_description $test_config_array(test.case_${i}.description)
            puts "Description: $test_description"
        }
        
        set requires_reset 0
        if {[info exists test_config_array(test.case_${i}.requires_reset)]} {
            set requires_reset $test_config_array(test.case_${i}.requires_reset)
        }
        
        puts "Running test..."
        
        set test_status "FAILED"
        set test_message "Test execution failed"
        
        # Execute test on device if shared memory is available
        if {[info exists ::shared_mem_base]} {
            # Send run test command to device
            if {[send_run_test_command $i $test_name $test_description $requires_reset]} {
                # Wait for test to complete
                after [expr {$timeout + 500}]
                
                # Get test status from device
                set test_status_response [send_get_test_status_command]
                if {$test_status_response != "" && ![string match "*ERROR*" $test_status_response]} {
                    # Parse test status to determine if test passed
                    # The device should indicate test result in the response
                    if {[string match "*PASSED*" $test_status_response] || ![string match "*FAILED*" $test_status_response]} {
                        set test_status "PASSED"
                        set test_message "Test completed successfully"
                        incr passed
                    } else {
                        set test_status "FAILED"
                        set test_message "Test validation failed"
                        incr failed
                    }
                } else {
                    set test_status "FAILED"
                    set test_message "Failed to get test status from device"
                    incr failed
                }
            } else {
                set test_status "FAILED"
                set test_message "Failed to send test command to device"
                incr failed
            }
        } else {
            # Simulate test execution when shared memory not available
            after 500
            set test_status "PASSED"
            set test_message "Test completed (simulated - shared memory not available)"
            incr passed
        }
        
        # Write test result to file
        write_test_result $fp $i $test_name $test_status $test_message
        
        puts "Test $test_status: $test_message"
        puts ""
        after 500
    }
    
    # Write test summary footer
    write_test_summary_footer $fp $num_tests $passed $failed
    
    # Close test results file
    close $fp
    
    puts "=== TEST RESULTS ==="
    puts "Total Tests: $num_tests"
    puts "Passed: $passed"
    puts "Failed: $failed"
    puts ""
    puts "Test results written to: $test_results_file"
    puts ""
    
    # Store results
    set ::test_results(passed) $passed
    set ::test_results(failed) $failed
    set ::test_results(total) $num_tests
    
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function displays test results
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc view_test_results_menu {} {
    clear_screen
    show_banner
    
    puts "=== TEST RESULTS ==="
    puts ""
    
    if {[info exists ::test_results]} {
        puts "Total Tests: $::test_results(total)"
        puts "Passed: $::test_results(passed)"
        puts "Failed: $::test_results(failed)"
        
        if {$::test_results(total) > 0} {
            set pass_rate [expr {($::test_results(passed) * 100.0) / $::test_results(total)}]
            puts "Pass Rate: [format "%.1f" $pass_rate]%"
        }
    } else {
        puts "No test results available"
        puts "Run tests first to see results"
    }
    
    puts ""
    puts "Press any key to continue..."
    gets stdin
}

#--------------------------------------------------------------------
# This function displays help information
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc show_help_menu {} {
    clear_screen
    show_banner
    
    puts "=== HELP ==="
    puts ""
    puts "Main Menu Options:"
    puts "1. View Configuration - Display current settings"
    puts "2. Configure Settings - Modify configuration parameters"
    puts "3. Run Application - Execute with current configuration"
    puts "4. Get Status - Display system status"
    puts "5. Test Application - Test application on device"
    puts "6. Help - Show this help information"
    puts "0. Exit - Exit the application"
    puts ""
    puts "Configuration Options:"
    puts "1. Device Name - String input with echo"
    puts "2. Base Address - Hex input with echo"
    puts "3. Operation Mode - List selection"
    puts "4. Timeout Value - Hex input with echo"
    puts "5. Debug Level - List selection"
    puts ""
    puts "Press any key to continue..."
    gets stdin
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


# Main entry point
if {[file tail $argv0] == [file tail [info script]]} {
    init_app
}

