#!/usr/bin/env tclsh
# JTAG Script Mode Command Execution
# 
# This file contains predetermined commands for JTAG Script Mode.
# Commands are sent via shared memory registers (TCL command bits).
#
# @author Devontae Reid (devdoesit17@gmail.com)
# @version 1.0.0
# @date 2025-12-31

# messages.tcl should be sourced by device_runner_cli.tcl before this file
# Check if messages.tcl functions are available
if {![info exists ::shared_mem_base]} {
    puts "WARNING: messages.tcl not sourced - shared memory functions may be unavailable"
}

#--------------------------------------------------------------------
# This function executes the predetermined JTAG script mode commands
#
# Executes a sequence of predetermined commands for JTAG script mode:
# 1. INIT - Initialize the application
# 2. GET_STATUS - Get current status
# 3. SET_CONFIG - Set configuration parameters
# 4. GET_CONFIG - Verify configuration
# 5. RUN_APP - Run the application
# 6. GET_STATUS - Get status after execution
#
# @return 0 on success, 1 on failure
#--------------------------------------------------------------------
proc execute_jtag_script_commands {} {
    puts "=== Executing JTAG Script Mode Commands ==="
    log_message "Starting JTAG script mode command execution"
    
    set error_count 0
    
    # Command 1: INIT
    puts "\n[1/6] Sending INIT command..."
    if {[catch {send_init_command} result]} {
        puts "ERROR: INIT command failed: $result"
        log_message "ERROR: INIT command failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: INIT command returned error: $result"
            log_message "ERROR: INIT command returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: INIT command completed"
        }
    }
    
    # Command 2: GET_STATUS
    puts "\n[2/6] Sending GET_STATUS command..."
    if {[catch {send_get_status_command} result]} {
        puts "ERROR: GET_STATUS command failed: $result"
        log_message "ERROR: GET_STATUS command failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: GET_STATUS command returned error: $result"
            log_message "ERROR: GET_STATUS command returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Status: $result"
        }
    }
    
    # Command 3: SET_CONFIG
    puts "\n[3/6] Sending SET_CONFIG commands..."
    # Set device name
    if {[catch {send_set_config_command "device_name" "JTAG_Script_Device" $::CONFIG_TYPE_STRING} result]} {
        puts "ERROR: SET_CONFIG (device_name) failed: $result"
        log_message "ERROR: SET_CONFIG (device_name) failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: SET_CONFIG (device_name) returned error: $result"
            log_message "ERROR: SET_CONFIG (device_name) returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Device name configured"
        }
    }
    
    # Set base address
    if {[catch {send_set_config_command "base_address" "0x43C00000" $::CONFIG_TYPE_HEX} result]} {
        puts "ERROR: SET_CONFIG (base_address) failed: $result"
        log_message "ERROR: SET_CONFIG (base_address) failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: SET_CONFIG (base_address) returned error: $result"
            log_message "ERROR: SET_CONFIG (base_address) returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Base address configured"
        }
    }
    
    # Command 4: GET_CONFIG
    puts "\n[4/6] Sending GET_CONFIG commands..."
    if {[catch {send_get_config_command "device_name"} result]} {
        puts "ERROR: GET_CONFIG (device_name) failed: $result"
        log_message "ERROR: GET_CONFIG (device_name) failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: GET_CONFIG (device_name) returned error: $result"
            log_message "ERROR: GET_CONFIG (device_name) returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Device name: $result"
        }
    }
    
    # Command 5: RUN_APP
    puts "\n[5/6] Sending RUN_APP command..."
    if {[catch {send_run_app_command} result]} {
        puts "ERROR: RUN_APP command failed: $result"
        log_message "ERROR: RUN_APP command failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: RUN_APP command returned error: $result"
            log_message "ERROR: RUN_APP command returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Application execution completed"
        }
    }
    
    # Command 6: GET_STATUS (final)
    puts "\n[6/6] Sending final GET_STATUS command..."
    if {[catch {send_get_status_command} result]} {
        puts "ERROR: GET_STATUS command failed: $result"
        log_message "ERROR: GET_STATUS command failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: GET_STATUS command returned error: $result"
            log_message "ERROR: GET_STATUS command returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Final status: $result"
        }
    }
    
    puts "\n=== JTAG Script Mode Command Execution Complete ==="
    puts "Errors: $error_count"
    log_message "JTAG script mode command execution completed with $error_count errors"
    
    if {$error_count > 0} {
        return 1
    }
    return 0
}

puts "JTAG script commands module loaded"

