#!/usr/bin/env tclsh
# Test Script Mode Command Execution
# 
# This file contains predetermined commands for Test Mode.
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
# This function executes the predetermined test script mode commands
#
# Executes a sequence of predetermined commands for test mode:
# 1. INIT - Initialize the application
# 2. START_TEST - Initialize test configuration
# 3. RUN_TEST - Execute test cases
# 4. GET_TEST_STATUS - Check test progress
# 5. GET_TEST_STATUS - Final test results
# 6. GET_STATUS - Get overall system status
#
# @return 0 on success, 1 on failure
#--------------------------------------------------------------------
proc execute_test_script_commands {} {
    puts "=== Executing Test Script Mode Commands ==="
    log_message "Starting test script mode command execution"
    
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
    
    # Command 2: START_TEST
    puts "\n[2/6] Sending START_TEST command..."
    set num_tests 3
    set test_timeout 10000
    set test_retries 2
    if {[catch {send_start_test_command $num_tests $test_timeout $test_retries} result]} {
        puts "ERROR: START_TEST command failed: $result"
        log_message "ERROR: START_TEST command failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: START_TEST command returned error: $result"
            log_message "ERROR: START_TEST command returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Test configuration initialized ($num_tests tests)"
        }
    }
    
    # Command 3: RUN_TEST - Execute test cases
    puts "\n[3/6] Sending RUN_TEST commands..."
    set test_cases {
        {1 "Basic Functionality Test" "Test basic application functionality" 0}
        {2 "Configuration Test" "Test configuration parameter handling" 0}
        {3 "Performance Test" "Test application performance under load" 1}
    }
    
    foreach test_case $test_cases {
        set test_num [lindex $test_case 0]
        set test_name [lindex $test_case 1]
        set test_desc [lindex $test_case 2]
        set requires_reset [lindex $test_case 3]
        
        puts "  Running test $test_num: $test_name"
        if {[catch {send_run_test_command $test_num $test_name $test_desc $requires_reset} result]} {
            puts "  ERROR: RUN_TEST ($test_num) failed: $result"
            log_message "ERROR: RUN_TEST ($test_num) failed: $result"
            incr error_count
        } else {
            if {[string match "ERROR:*" $result]} {
                puts "  ERROR: RUN_TEST ($test_num) returned error: $result"
                log_message "ERROR: RUN_TEST ($test_num) returned error: $result"
                incr error_count
            } else {
                puts "  SUCCESS: Test $test_num completed"
            }
        }
        
        # Small delay between tests
        after 500
    }
    
    # Command 4: GET_TEST_STATUS (mid-execution)
    puts "\n[4/6] Sending GET_TEST_STATUS command (mid-execution)..."
    if {[catch {send_get_test_status_command} result]} {
        puts "ERROR: GET_TEST_STATUS command failed: $result"
        log_message "ERROR: GET_TEST_STATUS command failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: GET_TEST_STATUS command returned error: $result"
            log_message "ERROR: GET_TEST_STATUS command returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Test status: $result"
        }
    }
    
    # Command 5: GET_TEST_STATUS (final)
    puts "\n[5/6] Sending GET_TEST_STATUS command (final)..."
    if {[catch {send_get_test_status_command} result]} {
        puts "ERROR: GET_TEST_STATUS command failed: $result"
        log_message "ERROR: GET_TEST_STATUS command failed: $result"
        incr error_count
    } else {
        if {[string match "ERROR:*" $result]} {
            puts "ERROR: GET_TEST_STATUS command returned error: $result"
            log_message "ERROR: GET_TEST_STATUS command returned error: $result"
            incr error_count
        } else {
            puts "SUCCESS: Final test status: $result"
        }
    }
    
    # Command 6: GET_STATUS (system status)
    puts "\n[6/6] Sending GET_STATUS command (system status)..."
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
            puts "SUCCESS: System status: $result"
        }
    }
    
    puts "\n=== Test Script Mode Command Execution Complete ==="
    puts "Errors: $error_count"
    log_message "Test script mode command execution completed with $error_count errors"
    
    if {$error_count > 0} {
        return 1
    }
    return 0
}

puts "Test script commands module loaded"

