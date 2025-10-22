#!/usr/bin/env tclsh
# Shared Memory Messages for Device Runner CLI
# Communication protocol between TCL script and C application
# Shared memory region: 0x10000000 - 0x10000FFF (4KB)

# Global variables for shared memory communication
set ::shared_mem_base 0x10000000
set ::shared_mem_size 0x1000
set ::message_timeout 5000
set ::message_retries 3

# Message structure offsets in shared memory
set ::MSG_HEADER_SIZE 16
set ::MSG_DATA_SIZE [expr $::shared_mem_size - $::MSG_HEADER_SIZE]

# Message header offsets
set ::MSG_OFFSET_MAGIC 0      ;# Magic number (4 bytes)
set ::MSG_OFFSET_TYPE 4       ;# Message type (4 bytes)
set ::MSG_OFFSET_LENGTH 8     ;# Data length (4 bytes)
set ::MSG_OFFSET_STATUS 12    ;# Status/Response code (4 bytes)
set ::MSG_OFFSET_DATA 16      ;# Message data starts here

# Magic number for message validation
set ::MSG_MAGIC_NUMBER 0xDEADBEEF

# Message types
set ::MSG_TYPE_INIT 1
set ::MSG_TYPE_RUN_APP 2
set ::MSG_TYPE_SET_PARAM 3
set ::MSG_TYPE_GET_STATUS 4
set ::MSG_TYPE_CAPTURE_RAM 5
set ::MSG_TYPE_SET_CONFIG 6
set ::MSG_TYPE_GET_CONFIG 7
set ::MSG_TYPE_EXIT 8
set ::MSG_TYPE_RESPONSE 9
set ::MSG_TYPE_ERROR 10

# Status codes
set ::MSG_STATUS_SUCCESS 0
set ::MSG_STATUS_ERROR 1
set ::MSG_STATUS_BUSY 2
set ::MSG_STATUS_TIMEOUT 3
set ::MSG_STATUS_INVALID 4

# Configuration parameter types
set ::CONFIG_TYPE_STRING 1
set ::CONFIG_TYPE_HEX 2
set ::CONFIG_TYPE_LIST 3

# Initialize shared memory communication
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

# Write message header to shared memory
proc write_message_header {msg_type data_length status} {
    global shared_mem_base MSG_MAGIC_NUMBER
    global MSG_OFFSET_MAGIC MSG_OFFSET_TYPE MSG_OFFSET_LENGTH MSG_OFFSET_STATUS
    
    set base_addr $shared_mem_base
    
    # Write magic number
    mwr [expr $base_addr + $MSG_OFFSET_MAGIC] $MSG_MAGIC_NUMBER
    
    # Write message type
    mwr [expr $base_addr + $MSG_OFFSET_TYPE] $msg_type
    
    # Write data length
    mwr [expr $base_addr + $MSG_OFFSET_LENGTH] $data_length
    
    # Write status
    mwr [expr $base_addr + $MSG_OFFSET_STATUS] $status
    
    log_message "Message header written: type=$msg_type, length=$data_length, status=$status"
}

# Read message header from shared memory
proc read_message_header {} {
    global shared_mem_base MSG_MAGIC_NUMBER
    global MSG_OFFSET_MAGIC MSG_OFFSET_TYPE MSG_OFFSET_LENGTH MSG_OFFSET_STATUS
    
    set base_addr $shared_mem_base
    
    # Read header fields
    set magic [mrd [expr $base_addr + $MSG_OFFSET_MAGIC]]
    set msg_type [mrd [expr $base_addr + $MSG_OFFSET_TYPE]]
    set data_length [mrd [expr $base_addr + $MSG_OFFSET_LENGTH]]
    set status [mrd [expr $base_addr + $MSG_OFFSET_STATUS]]
    
    # Validate magic number
    if {$magic != $MSG_MAGIC_NUMBER} {
        return [list 0 0 0 0]  ;# Invalid message
    }
    
    return [list $msg_type $data_length $status $magic]
}

# Write message data to shared memory
proc write_message_data {data} {
    global shared_mem_base MSG_OFFSET_DATA MSG_DATA_SIZE
    
    set data_length [string length $data]
    if {$data_length > $MSG_DATA_SIZE} {
        puts "ERROR: Message data too large ($data_length > $MSG_DATA_SIZE)"
        return 0
    }
    
    set base_addr [expr $shared_mem_base + $MSG_OFFSET_DATA]
    
    # Convert string to hex and write to memory
    set hex_data [binary encode hex $data]
    set hex_length [string length $hex_data]
    
    # Write data in 4-byte chunks
    for {set i 0} {$i < $hex_length} {incr i 8} {
        set chunk [string range $hex_data $i [expr $i + 7]]
        if {[string length $chunk] < 8} {
            set chunk [format "%08s" $chunk]
            regsub -all " " $chunk "0" chunk
        }
        mwr [expr $base_addr + $i/2] 0x$chunk
    }
    
    log_message "Message data written: $data_length bytes"
    return 1
}

# Read message data from shared memory
proc read_message_data {data_length} {
    global shared_mem_base MSG_OFFSET_DATA
    
    set base_addr [expr $shared_mem_base + $MSG_OFFSET_DATA]
    set hex_data ""
    
    # Read data in 4-byte chunks
    for {set i 0} {$i < $data_length} {incr i 4} {
        set chunk [mrd [expr $base_addr + $i]]
        set hex_chunk [format "%08X" $chunk]
        append hex_data $hex_chunk
    }
    
    # Convert hex to string
    set data [binary decode hex $hex_data]
    
    log_message "Message data read: $data_length bytes"
    return $data
}

# Send a message to the C application
proc send_message {msg_type data {timeout 5000} {retries 3}} {
    global shared_mem_base MSG_STATUS_SUCCESS MSG_STATUS_BUSY
    
    puts "Sending message: type=$msg_type, data='$data'"
    log_message "Sending message: type=$msg_type, data='$data'"
    
    # Write message header
    write_message_header $msg_type [string length $data] $MSG_STATUS_SUCCESS
    
    # Write message data
    if {[string length $data] > 0} {
        write_message_data $data
    }
    
    # Wait for response
    set response [wait_for_message_response $timeout $retries]
    
    return $response
}

# Wait for message response from C application
proc wait_for_message_response {{timeout 5000} {retries 3}} {
    global shared_mem_base MSG_TYPE_RESPONSE MSG_TYPE_ERROR
    global MSG_STATUS_SUCCESS MSG_STATUS_ERROR MSG_STATUS_BUSY
    
    puts "Waiting for message response..."
    
    for {set attempt 1} {$attempt <= $retries} {incr attempt} {
        puts "Attempt $attempt of $retries"
        
        for {set i 0} {$i < [expr $timeout / 100]} {incr i} {
            # Read message header
            set header [read_message_header]
            set msg_type [lindex $header 0]
            set data_length [lindex $header 1]
            set status [lindex $header 2]
            
            if {$msg_type == $MSG_TYPE_RESPONSE && $status == $MSG_STATUS_SUCCESS} {
                # Read response data
                set response_data [read_message_data $data_length]
                puts "Response received: '$response_data'"
                log_message "Response received: '$response_data'"
                return $response_data
            } elseif {$msg_type == $MSG_TYPE_ERROR} {
                set error_data [read_message_data $data_length]
                puts "Error response: '$error_data'"
                log_message "Error response: '$error_data'"
                return "ERROR: $error_data"
            } elseif {$status == $MSG_STATUS_BUSY} {
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
    return "ERROR: Timeout"
}

# Send INIT command
proc send_init_command {} {
    global MSG_TYPE_INIT
    
    puts "Sending INIT command..."
    set response [send_message $MSG_TYPE_INIT ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "INIT command failed: $response"
        return 0
    } else {
        puts "INIT command successful: $response"
        return 1
    }
}

# Send RUN_APP command
proc send_run_app_command {} {
    global MSG_TYPE_RUN_APP
    
    puts "Sending RUN_APP command..."
    set response [send_message $MSG_TYPE_RUN_APP ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "RUN_APP command failed: $response"
        return 0
    } else {
        puts "RUN_APP command successful: $response"
        return 1
    }
}

# Send SET_PARAM command
proc send_set_param_command {param_name param_value} {
    global MSG_TYPE_SET_PARAM
    
    set param_data "$param_name $param_value"
    puts "Sending SET_PARAM command: $param_data"
    set response [send_message $MSG_TYPE_SET_PARAM $param_data]
    
    if {[string match "ERROR:*" $response]} {
        puts "SET_PARAM command failed: $response"
        return 0
    } else {
        puts "SET_PARAM command successful: $response"
        return 1
    }
}

# Send GET_STATUS command
proc send_get_status_command {} {
    global MSG_TYPE_GET_STATUS
    
    puts "Sending GET_STATUS command..."
    set response [send_message $MSG_TYPE_GET_STATUS ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "GET_STATUS command failed: $response"
        return ""
    } else {
        puts "GET_STATUS command successful: $response"
        return $response
    }
}

# Send CAPTURE_RAM command
proc send_capture_ram_command {} {
    global MSG_TYPE_CAPTURE_RAM
    
    puts "Sending CAPTURE_RAM command..."
    set response [send_message $MSG_TYPE_CAPTURE_RAM ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "CAPTURE_RAM command failed: $response"
        return 0
    } else {
        puts "CAPTURE_RAM command successful: $response"
        return 1
    }
}

# Send SET_CONFIG command
proc send_set_config_command {config_name config_value config_type} {
    global MSG_TYPE_SET_CONFIG CONFIG_TYPE_STRING CONFIG_TYPE_HEX CONFIG_TYPE_LIST
    
    set config_data "$config_name|$config_value|$config_type"
    puts "Sending SET_CONFIG command: $config_data"
    set response [send_message $MSG_TYPE_SET_CONFIG $config_data]
    
    if {[string match "ERROR:*" $response]} {
        puts "SET_CONFIG command failed: $response"
        return 0
    } else {
        puts "SET_CONFIG command successful: $response"
        return 1
    }
}

# Send GET_CONFIG command
proc send_get_config_command {config_name} {
    global MSG_TYPE_GET_CONFIG
    
    puts "Sending GET_CONFIG command: $config_name"
    set response [send_message $MSG_TYPE_GET_CONFIG $config_name]
    
    if {[string match "ERROR:*" $response]} {
        puts "GET_CONFIG command failed: $response"
        return ""
    } else {
        puts "GET_CONFIG command successful: $response"
        return $response
    }
}

# Send EXIT command
proc send_exit_command {} {
    global MSG_TYPE_EXIT
    
    puts "Sending EXIT command..."
    set response [send_message $MSG_TYPE_EXIT ""]
    
    if {[string match "ERROR:*" $response]} {
        puts "EXIT command failed: $response"
        return 0
    } else {
        puts "EXIT command successful: $response"
        return 1
    }
}

# Clear shared memory
proc clear_shared_memory {} {
    global shared_mem_base shared_mem_size
    
    puts "Clearing shared memory..."
    mwr $shared_mem_base 0 $shared_mem_size
    log_message "Shared memory cleared"
}

# Read shared memory status
proc read_shared_memory_status {} {
    global shared_mem_base
    
    puts "Reading shared memory status..."
    puts "Base address: 0x[format %08X $shared_mem_base]"
    
    # Read first 64 bytes to show status
    for {set i 0} {$i < 16} {incr i} {
        set addr [expr $shared_mem_base + $i * 4]
        set value [mrd $addr]
        puts "0x[format %08X $addr]: 0x[format %08X $value]"
    }
}

# Test shared memory communication
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
