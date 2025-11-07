#!/usr/bin/env tclsh
# Shared Memory Communication for Device Runner CLI
# Simple register-based communication protocol
# Shared memory region: 0x10000000 - 0x10000FFF (4KB)

# Global variables for shared memory communication
set ::shared_mem_base 0x10000000
set ::shared_mem_size 0x1000
set ::message_timeout 5000
set ::message_retries 3

# Register offsets in shared memory
set ::CMD_REG_OFFSET 0x0      ;# Command register (bit field)
set ::RESP_REG_OFFSET 0x4     ;# Response register
set ::DATA_AREA_OFFSET 0x8    ;# Data area for command parameters

# Command bit positions in command register
set ::CMD_BIT_INIT 0          ;# Bit 0: INIT command
set ::CMD_BIT_RUN_APP 1       ;# Bit 1: RUN_APP command
set ::CMD_BIT_SET_PARAM 2     ;# Bit 2: SET_PARAM command
set ::CMD_BIT_GET_STATUS 3    ;# Bit 3: GET_STATUS command
set ::CMD_BIT_CAPTURE_RAM 4   ;# Bit 4: CAPTURE_RAM command
set ::CMD_BIT_SET_CONFIG 5    ;# Bit 5: SET_CONFIG command
set ::CMD_BIT_GET_CONFIG 6    ;# Bit 6: GET_CONFIG command
set ::CMD_BIT_EXIT 7          ;# Bit 7: EXIT command

# Response register values
set ::RESP_SUCCESS 0x00000001  ;# Success response
set ::RESP_ERROR 0x00000002    ;# Error response
set ::RESP_BUSY 0x00000004     ;# Busy response
set ::RESP_READY 0x00000008    ;# Ready response

# Configuration parameter types
set ::CONFIG_TYPE_STRING 1
set ::CONFIG_TYPE_HEX 2
set ::CONFIG_TYPE_LIST 3

#--------------------------------------------------------------------
# This function initializes shared memory communication
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc init_shared_memory {} {
    global shared_mem_base shared_mem_size
    
    puts "Initializing shared memory communication..."
    puts "Base address: 0x[format %08X $shared_mem_base]"
    puts "Size: 0x[format %08X $shared_mem_size]"
    
    # Clear the shared memory region
    mwr $shared_mem_base 0 $shared_mem_size
    
    log_message "Shared memory initialized at 0x[format %08X $shared_mem_base]"
    return 1
}

#--------------------------------------------------------------------
# This function writes data to the shared memory data area
#
#--------------------------------------------------------------------
#
# param data: Data string to write to data area
#--------------------------------------------------------------------
proc write_data_area {data} {
    global shared_mem_base DATA_AREA_OFFSET shared_mem_size
    
    set data_length [string length $data]
    set max_data_size [expr $shared_mem_size - $DATA_AREA_OFFSET]
    
    if {$data_length > $max_data_size} {
        puts "ERROR: Data too large ($data_length > $max_data_size)"
        return 0
    }
    
    set base_addr [expr $shared_mem_base + $DATA_AREA_OFFSET]
    
    # Write data as string (null-terminated)
    # Write in 4-byte chunks
    set i 0
    while {$i < $data_length} {
        set chunk 0
        for {set j 0} {$j < 4 && ($i + $j) < $data_length} {incr j} {
            set char [string index $data [expr $i + $j]]
            set byte_val [expr {[scan $char %c] & 0xFF}]
            set chunk [expr $chunk | ($byte_val << ($j * 8))]
        }
        mwr [expr $base_addr + $i] $chunk
        incr i 4
    }
    
    # Write null terminator
    mwr [expr $base_addr + $i] 0
    
    log_message "Data written to data area: $data_length bytes"
    return 1
}

#--------------------------------------------------------------------
# This function reads data from the shared memory data area
#
#--------------------------------------------------------------------
#
# param max_length: Maximum number of bytes to read
#--------------------------------------------------------------------
proc read_data_area {max_length} {
    global shared_mem_base DATA_AREA_OFFSET
    
    set base_addr [expr $shared_mem_base + $DATA_AREA_OFFSET]
    set data ""
    
    # Read data in 4-byte chunks until null terminator or max length
    for {set i 0} {$i < $max_length} {incr i 4} {
        set chunk [mrd [expr $base_addr + $i]]
        
        # Extract bytes from chunk
        for {set j 0} {$j < 4 && ($i + $j) < $max_length} {incr j} {
            set byte_val [expr ($chunk >> ($j * 8)) & 0xFF]
            if {$byte_val == 0} {
                return $data
            }
            append data [format %c $byte_val]
        }
    }
    
    log_message "Data read from data area: [string length $data] bytes"
    return $data
}

#--------------------------------------------------------------------
# This function sends a message to the C application
#
#--------------------------------------------------------------------
#
# param msg_type: Command type (maps to bit position)
# data: Optional data to write to data area
#--------------------------------------------------------------------
proc send_message {msg_type data {timeout 5000} {retries 3}} {
    global shared_mem_base CMD_REG_OFFSET RESP_REG_OFFSET
    global CMD_BIT_INIT CMD_BIT_RUN_APP CMD_BIT_SET_PARAM CMD_BIT_GET_STATUS
    global CMD_BIT_CAPTURE_RAM CMD_BIT_SET_CONFIG CMD_BIT_GET_CONFIG CMD_BIT_EXIT
    
    puts "Sending message: type=$msg_type, data='$data'"
    log_message "Sending message: type=$msg_type, data='$data'"
    
    # Map command type to bit position
    set bit_pos 0
    switch $msg_type {
        $CMD_BIT_INIT { set bit_pos $CMD_BIT_INIT }
        $CMD_BIT_RUN_APP { set bit_pos $CMD_BIT_RUN_APP }
        $CMD_BIT_SET_PARAM { set bit_pos $CMD_BIT_SET_PARAM }
        $CMD_BIT_GET_STATUS { set bit_pos $CMD_BIT_GET_STATUS }
        $CMD_BIT_CAPTURE_RAM { set bit_pos $CMD_BIT_CAPTURE_RAM }
        $CMD_BIT_SET_CONFIG { set bit_pos $CMD_BIT_SET_CONFIG }
        $CMD_BIT_GET_CONFIG { set bit_pos $CMD_BIT_GET_CONFIG }
        $CMD_BIT_EXIT { set bit_pos $CMD_BIT_EXIT }
        default {
            puts "ERROR: Unknown command type: $msg_type"
            return "ERROR: Unknown command type"
        }
    }
    
    # Write data to data area if provided
    if {[string length $data] > 0} {
        write_data_area $data
    }
    
    # Set the appropriate bit in command register
    set cmd_reg_addr [expr $shared_mem_base + $CMD_REG_OFFSET]
    set cmd_value [expr 1 << $bit_pos]
    mwr $cmd_reg_addr $cmd_value
    
    log_message "Command bit $bit_pos set in command register: 0x[format %08X $cmd_value]"
    
    # Wait for response
    set response [wait_for_message_response $timeout $retries]
    
    # Clear command register after processing
    mwr $cmd_reg_addr 0
    
    return $response
}

#--------------------------------------------------------------------
# This function waits for a message response from the C application
#
#--------------------------------------------------------------------
#
# param timeout: Timeout in milliseconds (default: 5000)
# param retries: Number of retry attempts (default: 3)
#--------------------------------------------------------------------
proc wait_for_message_response {{timeout 5000} {retries 3}} {
    global shared_mem_base RESP_REG_OFFSET
    global RESP_SUCCESS RESP_ERROR RESP_BUSY RESP_READY
    
    puts "Waiting for message response..."
    
    set resp_reg_addr [expr $shared_mem_base + $RESP_REG_OFFSET]
    
    for {set attempt 1} {$attempt <= $retries} {incr attempt} {
        puts "Attempt $attempt of $retries"
        
        for {set i 0} {$i < [expr $timeout / 100]} {incr i} {
            # Read response register
            set resp_value [mrd $resp_reg_addr]
            
            if {[expr $resp_value & $RESP_SUCCESS]} {
                # Success response - read data if available
                set response_data [read_data_area 1024]
                puts "Response received: '$response_data'"
                log_message "Response received: '$response_data'"
                # Clear response register
                mwr $resp_reg_addr 0
                return $response_data
            } elseif {[expr $resp_value & $RESP_ERROR]} {
                # Error response - read error data
                set error_data [read_data_area 1024]
                puts "Error response: '$error_data'"
                log_message "Error response: '$error_data'"
                # Clear response register
                mwr $resp_reg_addr 0
                return "ERROR: $error_data"
            } elseif {[expr $resp_value & $RESP_BUSY]} {
                # Application is busy, wait a bit more
                after 100
                continue
            }
            
            after 100
        }
        
        puts "Timeout on attempt $attempt, retrying..."
        after 1000
    }
    
    puts "ERROR: No response after $retries attempts"
    log_message "ERROR: No response after $retries attempts"
    # Clear response register
    mwr $resp_reg_addr 0
    return "ERROR: Timeout"
}

#--------------------------------------------------------------------
# This function sends an INIT command to the C application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc send_init_command {} {
    global CMD_BIT_INIT
    
    puts "Sending INIT command..."
    set response [send_message $CMD_BIT_INIT ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "INIT command failed: $response"
        return 0
    } else {
        puts "INIT command successful: $response"
        return 1
    }
}

#--------------------------------------------------------------------
# This function sends a RUN_APP command to the C application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc send_run_app_command {} {
    global CMD_BIT_RUN_APP
    
    puts "Sending RUN_APP command..."
    set response [send_message $CMD_BIT_RUN_APP ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "RUN_APP command failed: $response"
        return 0
    } else {
        puts "RUN_APP command successful: $response"
        return 1
    }
}

#--------------------------------------------------------------------
# This function sends a SET_PARAM command to the C application
#
#--------------------------------------------------------------------
#
# param param_name: Parameter name to set
# param param_value: Parameter value to set
#--------------------------------------------------------------------
proc send_set_param_command {param_name param_value} {
    global CMD_BIT_SET_PARAM
    
    set param_data "$param_name $param_value"
    puts "Sending SET_PARAM command: $param_data"
    set response [send_message $CMD_BIT_SET_PARAM $param_data]
    
    if {[string match "ERROR:*" $response]} {
        puts "SET_PARAM command failed: $response"
        return 0
    } else {
        puts "SET_PARAM command successful: $response"
        return 1
    }
}

#--------------------------------------------------------------------
# This function sends a GET_STATUS command to the C application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc send_get_status_command {} {
    global CMD_BIT_GET_STATUS
    
    puts "Sending GET_STATUS command..."
    set response [send_message $CMD_BIT_GET_STATUS ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "GET_STATUS command failed: $response"
        return ""
    } else {
        puts "GET_STATUS command successful: $response"
        return $response
    }
}

#--------------------------------------------------------------------
# This function sends a CAPTURE_RAM command to the C application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc send_capture_ram_command {} {
    global CMD_BIT_CAPTURE_RAM
    
    puts "Sending CAPTURE_RAM command..."
    set response [send_message $CMD_BIT_CAPTURE_RAM ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "CAPTURE_RAM command failed: $response"
        return 0
    } else {
        puts "CAPTURE_RAM command successful: $response"
        return 1
    }
}

#--------------------------------------------------------------------
# This function sends a SET_CONFIG command to the C application
#
#--------------------------------------------------------------------
#
# param config_name: Configuration name to set
# param config_value: Configuration value to set
# param config_type: Configuration type (1=string, 2=hex, 3=list)
#--------------------------------------------------------------------
proc send_set_config_command {config_name config_value config_type} {
    global CMD_BIT_SET_CONFIG CONFIG_TYPE_STRING CONFIG_TYPE_HEX CONFIG_TYPE_LIST
    
    set config_data "$config_name|$config_value|$config_type"
    puts "Sending SET_CONFIG command: $config_data"
    set response [send_message $CMD_BIT_SET_CONFIG $config_data]
    
    if {[string match "ERROR:*" $response]} {
        puts "SET_CONFIG command failed: $response"
        return 0
    } else {
        puts "SET_CONFIG command successful: $response"
        return 1
    }
}

#--------------------------------------------------------------------
# This function sends a GET_CONFIG command to the C application
#
#--------------------------------------------------------------------
#
# param config_name: Configuration name to get
#--------------------------------------------------------------------
proc send_get_config_command {config_name} {
    global CMD_BIT_GET_CONFIG
    
    puts "Sending GET_CONFIG command: $config_name"
    set response [send_message $CMD_BIT_GET_CONFIG $config_name]
    
    if {[string match "ERROR:*" $response]} {
        puts "GET_CONFIG command failed: $response"
        return ""
    } else {
        puts "GET_CONFIG command successful: $response"
        return $response
    }
}

#--------------------------------------------------------------------
# This function sends an EXIT command to the C application
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc send_exit_command {} {
    global CMD_BIT_EXIT
    
    puts "Sending EXIT command..."
    set response [send_message $CMD_BIT_EXIT ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "EXIT command failed: $response"
        return 0
    } else {
        puts "EXIT command successful: $response"
        return 1
    }
}

#--------------------------------------------------------------------
# This function clears the shared memory region
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc clear_shared_memory {} {
    global shared_mem_base shared_mem_size
    
    puts "Clearing shared memory..."
    mwr $shared_mem_base 0 $shared_mem_size
    log_message "Shared memory cleared"
}

#--------------------------------------------------------------------
# This function reads and displays the shared memory status
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc read_shared_memory_status {} {
    global shared_mem_base CMD_REG_OFFSET RESP_REG_OFFSET DATA_AREA_OFFSET
    
    puts "Reading shared memory status..."
    puts "Base address: 0x[format %08X $shared_mem_base]"
    
    # Read command register
    set cmd_reg [mrd [expr $shared_mem_base + $CMD_REG_OFFSET]]
    puts "Command Register (0x[format %08X [expr $shared_mem_base + $CMD_REG_OFFSET]]): 0x[format %08X $cmd_reg]"
    
    # Read response register
    set resp_reg [mrd [expr $shared_mem_base + $RESP_REG_OFFSET]]
    puts "Response Register (0x[format %08X [expr $shared_mem_base + $RESP_REG_OFFSET]]): 0x[format %08X $resp_reg]"
    
    # Read first few words of data area
    puts "Data Area (first 4 words):"
    for {set i 0} {$i < 4} {incr i} {
        set addr [expr $shared_mem_base + $DATA_AREA_OFFSET + $i * 4]
        set value [mrd $addr]
        puts "  0x[format %08X $addr]: 0x[format %08X $value]"
    }
}

#--------------------------------------------------------------------
# This function tests shared memory communication
#
#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
proc test_shared_memory {} {
    puts "Testing shared memory communication..."
    
    # Initialize shared memory
    init_shared_memory
    
    # Test INIT command
    puts "\n=== Testing INIT Command ==="
    send_init_command
    
    # Test GET_STATUS command
    puts "\n=== Testing GET_STATUS Command ==="
    set status [send_get_status_command]
    puts "Status: $status"
    
    # Test SET_CONFIG command
    puts "\n=== Testing SET_CONFIG Command ==="
    send_set_config_command "device_name" "Test Device" 1
    send_set_config_command "base_address" "0x43C00000" 2
    send_set_config_command "operation_mode" "2" 3
    
    # Test GET_CONFIG command
    puts "\n=== Testing GET_CONFIG Command ==="
    set device_name [send_get_config_command "device_name"]
    set base_address [send_get_config_command "base_address"]
    set operation_mode [send_get_config_command "operation_mode"]
    
    puts "Device Name: $device_name"
    puts "Base Address: $base_address"
    puts "Operation Mode: $operation_mode"
    
    # Test RUN_APP command
    puts "\n=== Testing RUN_APP Command ==="
    send_run_app_command
    
    # Test CAPTURE_RAM command
    puts "\n=== Testing CAPTURE_RAM Command ==="
    send_capture_ram_command
    
    puts "\nShared memory communication test completed"
}

# Log message function (if not already defined)
if {![info exists log_message]} {
    #--------------------------------------------------------------------
    # This function logs a message to the log file
    #
    #--------------------------------------------------------------------
    #
    # param message: Message string to log
    #--------------------------------------------------------------------
    proc log_message {message} {
        global log_file
        
        if {[info exists log_file] && $log_file != ""} {
            set timestamp [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
            set fp [open $log_file a]
            puts $fp "$timestamp - $message"
            close $fp
        }
    }
}

puts "Shared memory messages module loaded"
puts "Base address: 0x[format %08X $::shared_mem_base]"
puts "Size: 0x[format %08X $::shared_mem_size]"


