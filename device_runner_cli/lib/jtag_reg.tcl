#--------------------------------------------------------------------
# Helper Functions for JTAG and Device Management
#--------------------------------------------------------------------
# This file contains utility functions for:
# - JTAG operations (status, control, IDCODE, DNA)
# - Boot mode configuration (get/set)
# - Target and TAP identification
# - Architecture detection
# - Binary/hexadecimal conversions
#--------------------------------------------------------------------

#--------------------------------------------------------------------
# This function reads the current boot mode from a Xilinx device
#
# Connects to the device via JTAG, detects the architecture, and reads
# the boot mode configuration register. Supports Zynq UltraScale+ MPSoC
# and Versal architectures.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -connect <0|1> : Connect to JTAG targets (default: 0)
#             -remote <addr> : Remote hardware server address (if connect=1)
#             -arch <arch>   : Target architecture (optional, auto-detected)
#             -tap_id <id>   : TAP ID for multi-device chains (required if multiple TAPs)
#             -help          : Show help message
# return: Boot mode string (4-bit binary) or empty string on error
# example: get_bootmode -connect 1 -tap_id 0
#--------------------------------------------------------------------
proc get_bootmode {args} {
    set connect 0
    set remote 0
    set help 0
    set arch 0
    set tap_id ""
    set index 0
    
    # Parse command line arguments
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-connect"} {
            set connect [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-remote"} {
            set remote [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-arch"} {
            set arch [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-tap_id"} {
            set tap_id [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-help"} {
            set help 1
        }
    }
    
    # Show help if requested
    if {$help != 0} {
        help -read_bootmode
        return
    }

    # Connect to JTAG if requested
    if {$connect == 1} {
        puts "INFO: Connecting to JTAG Targets"
        if {$remote == 0} {
            connect
        } else {
            puts "Info: Connecting to remote hw_server: $remote"
            connect -url TCP:${remote}:3121
        }
    }

    # Validate TAP devices are available
    if {[llength [get_tap_ids]] == 0} {
        puts "Error: No TAP devices found on chain."
        return ""
    } else {
        puts "Info: Found TAPs at [get_tap_ids]"
    }

    # Handle multiple TAP devices
    if {[llength [get_tap_ids]] > 1 && $tap_id == ""} {
        puts "INFO: Multiple TAP [get_tap_ids] devices found on chain."
        puts "      Please use the -tap_id switch to select your device"
        return ""
    }

    # Validate and find TAP ID index if specified
    if {$tap_id != ""} {
        set tap_ids [get_tap_ids]
        set tap_id_found 0
        for {set i 0} {$i < [llength $tap_ids]} {incr i} {
            if {[lindex $tap_ids $i] == $tap_id} {
                set index $i
                set tap_id_found 1
                break
            }
        }
        if {$tap_id_found == 0} {
            puts "Error: Invalid -tap_id ${tap_id}. Valid TAP are [get_tap_ids] devices found on chain."
            return ""
        }
    }

    # Auto-detect architecture
    set arch [get_arch -tap_id $tap_id]
    puts "Info Auto-detected Arch detected is $arch"

    # Read boot mode based on architecture
    if {$arch == "zynqMP"} {
        puts "Info: Connecting to target ID [lindex [get_target -filter "PSU"] $index]"
        targets [lindex [get_target -filter "PSU"] $index]
        # Read boot mode register at 0xFF5E0200 (last 4 bits)
        set bootmode [string range [hex2bin [lindex [split [mrd 0xff5e0200]] end-1]] end-3 end]
        
        # Decode boot mode values (see UG1085 table 11-1)
        if {$bootmode == "0000"} {
            puts "Bootmode: $bootmode = PS JTAG"
        } elseif {$bootmode == "0001"} {
            puts "Bootmode: $bootmode = QUAD-SPI (24b)"
        } elseif {$bootmode == "0010"} {
            puts "Bootmode: $bootmode = QUAD-SPI (32b)"
        } elseif {$bootmode == "0011"} {
            puts "Bootmode: $bootmode = SD0 (2.0)"
        } elseif {$bootmode == "0100"} {
            puts "Bootmode: $bootmode = NAND"
        } elseif {$bootmode == "0101"} {
            puts "Bootmode: $bootmode = SD1 (2.0)"
        } elseif {$bootmode == "0110"} {
            puts "Bootmode: $bootmode = eMMC (1.8V)"
        } elseif {$bootmode == "0111"} {
            puts "Bootmode: $bootmode = USB0 (2.0)"
        } elseif {$bootmode == "1000"} {
            puts "Bootmode: $bootmode = PJTAG (MIO #0)"
        } elseif {$bootmode == "1001"} {
            puts "Bootmode: $bootmode = PJTAG (MIO #1)"
        } elseif {$bootmode == "1110"} {
            puts "Bootmode: $bootmode = SD1 LS (3.0)"
        } else {
            puts "Bootmode: $bootmode = unknown"
            puts "See table 11-1 in UG1085"
        }
    } elseif {$arch == "versal"} {
        puts "Info: Connecting to target ID [lindex [get_target -filter "Versal"] $index]"
        targets [lindex [get_target -filter "Versal"] $index]
        # Read boot mode register at 0xF1260200 (last 4 bits)
        set bootmode [string range [hex2bin [lindex [split [mrd 0xF1260200]] end-1]] end-3 end]
        
        # Decode boot mode values (see AM012 table 13)
        if {$bootmode == "0000"} {
            puts "Bootmode: $bootmode = JTAG"
        } elseif {$bootmode == "0001"} {
            puts "Bootmode: $bootmode = QUAD-SPI (24b)"
        } elseif {$bootmode == "0010"} {
            puts "Bootmode: $bootmode = QUAD-SPI (32b)"
        } elseif {$bootmode == "0011"} {
            puts "Bootmode: $bootmode = SD0 (3.0)"
        } elseif {$bootmode == "0101"} {
            puts "Bootmode: $bootmode = SD1 (2.0)"
        } elseif {$bootmode == "0110"} {
            puts "Bootmode: $bootmode = eMMC1 (4.51)"
        } elseif {$bootmode == "1010"} {
            puts "Bootmode: $bootmode = SelectMAP"
        } elseif {$bootmode == "1110"} {
            puts "Bootmode: $bootmode = SD1 (3.0)"
        } elseif {$bootmode == "1000"} {
            puts "Bootmode: $bootmode = OSPI"
        } else {
            puts "Bootmode: $bootmode = unknown"
            puts "See table 13 in AM012"
        }
    } else {
        puts "INFO: Invalid arch: $arch. Supported -arch are zynq, zynqMP, and versal"
    }
    
    if {$connect == 1} {
        puts "INFO: Disconnecting"
    }
    
    return $bootmode
}

#--------------------------------------------------------------------
# This function sets the boot mode on a Xilinx device
#
# Connects to the device via JTAG, detects the architecture, and writes
# the boot mode configuration register. Supports Zynq UltraScale+ MPSoC
# and Versal architectures.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -bootmode <hex> : Boot mode value in hex (e.g., 0x0, 0x3)
#             -connect <0|1>  : Connect to JTAG targets (default: 0)
#             -remote <addr>  : Remote hardware server address (if connect=1)
#             -arch <arch>    : Target architecture (optional, auto-detected)
#             -tap_id <id>    : TAP ID for multi-device chains
#             -list           : List all supported boot modes for architecture
#             -help           : Show help message
# return: Nothing
# example: set_bootmode -bootmode 0x3 -connect 1 -tap_id 0
#--------------------------------------------------------------------
proc set_bootmode {args} {
    set connect 0
    set remote 0
    set help 0
    set arch 0
    set list 0
    set bootmode 0x0
    set tap_id ""
    set index 0

    # Define supported boot modes for Zynq UltraScale+ MPSoC
    array set zynqMP {
        0x0 "PS JTAG"
        0x1 "QUAD-SPI (24b)"
        0x2 "QUAD-SPI (32b)"
        0x3 "SD0 (2.0)"
        0x4 "NAND"
        0x5 "SD1(2.0)"
        0x6 "eMMC (1.8V)"
        0x7 "USB0 (2.0)"
        0x8 "PJTAG (MIO #0)"
        0x9 "PJTAG (MIO #1)"
        0xE "SD1 LS (3.0)"
    }

    # Define supported boot modes for Versal
    array set versal {
        0x0 "PS JTAG"
        0x1 "QUAD-SPI (24b)"
        0x2 "QUAD-SPI (32b)"
        0x3 "SD0 (2.0)"
        0x5 "SD1(2.0)"
        0x6 "eMMC1"
        0x8 "OSPI"
        0x9 "SelectMap"
        0xE "SD1 (3.0)"
    }

    # Parse command line arguments
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-connect"} {
            set connect [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-remote"} {
            set remote [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-arch"} {
            set arch [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-tap_id"} {
            set tap_id [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-bootmode"} {
            # Parse hex value (supports both 0x... and ... formats)
            set bootmode [split [string tolower [lindex $args [expr {$i + 1}]]] "x"]
            set bootmode 0x[string toupper [lindex $bootmode end]]
        }
        if {[lindex $args $i] == "-help"} {
            set help 1
        }
        if {[lindex $args $i] == "-list"} {
            set list 1
        }
    }
    
    # Show help if requested
    if {$help != 0} {
        help -set_bootmode
        return
    }

    # Connect to JTAG if requested
    if {$connect == 1} {
        puts "INFO: Connecting to JTAG Targets"
        if {$remote == 0} {
            connect
        } else {
            puts "Info: Connecting to remote hw_server: $remote"
            connect -url TCP:${remote}:3121
        }
    }

    # Validate TAP devices are available
    if {[llength [get_tap_ids]] == 0} {
        puts "Error: No TAP devices found on chain."
        return ""
    }

    # Handle multiple TAP devices
    if {[llength [get_tap_ids]] > 1 && $tap_id == ""} {
        puts "INFO: Multiple TAP [get_tap_ids] devices found on chain."
        puts "      Please use the -tap_id switch to select your device"
        return ""
    }

    # Validate and find TAP ID index if specified
    if {$tap_id != ""} {
        set tap_ids [get_tap_ids]
        set tap_id_found 0
        for {set i 0} {$i < [llength $tap_ids]} {incr i} {
            if {[lindex $tap_ids $i] == $tap_id} {
                set index $i
                set tap_id_found 1
                break
            }
        }
        if {$tap_id_found == 0} {
            puts "Error: Invalid -tap_id ${tap_id}. Valid TAP are [get_tap_ids] devices found on chain."
            return ""
        }
    }

    # Auto-detect architecture
    set arch [get_arch -tap_id $tap_id]
    puts "Info Auto-detected Arch detected is $arch"

    # List supported boot modes if requested
    if {$list != 0} {
        if {$arch == "zynqMP"} {
            foreach name [array names zynqMP] {
                puts "$name is $zynqMP($name)"
            }
        } elseif {$arch == "versal"} {
            foreach name [array names versal] {
                puts "$name is $versal($name)"
            }
        } else {
            puts "INFO: Invalid arch: $arch. Supported -arch are zynqMP, and versal"
        }
        return ""
    }

    # Set boot mode for Zynq UltraScale+ MPSoC
    if {$arch == "zynqMP"} {
        set found 0
        foreach name [array names zynqMP] {
            if {$name == $bootmode} {
                set found 1
                break
            }
        }
        if {$found != 1} {
            puts "Error: Unsupported Bootmode: ${bootmode}. Use the -list command to see a list of supported bootmodes"
        } else {
            puts "Info: Setting Bootmode to $zynqMP($bootmode)"
            targets [lindex [get_target -filter "PSU"] $index]
            stop
            # Clear register and set boot mode
            mwr 0xffca0010 0x0
            mwr 0xff5e0200 ${bootmode}100
            rst -system
            after 1000
            con
        }
    } elseif {$arch == "versal"} {
        set found 0
        foreach name [array names versal] {
            if {$name == $bootmode} {
                set found 1
                break
            }
        }
        if {$found != 1} {
            puts "Error: Unsupported Bootmode: ${bootmode}. Use the -list command to see a list of supported bootmodes"
        } else {
            puts "Info: Setting Bootmode to $versal($bootmode)"
            targets [lindex [get_target -filter "Versal"] $index]
            stop
            # Clear register and set boot mode
            mwr 0xF1110004  0x0
            mwr 0xF1260200 ${bootmode}100
            mwr -force 0xF1260138 0
            rst -system
            after 1000
            con
        }
    } else {
        puts "INFO: Invalid arch: $arch. Supported -arch are zynqMP, and versal"
    }
    
    if {$connect == 1} {
        puts "INFO: Disconnecting"
    }
}

#--------------------------------------------------------------------
# This function reads the JTAG status register from the PL TAP
#
# Connects to the device, reads the JTAG status register, and displays
# the status value. For Versal devices, also performs a status lookup.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -connect <0|1> : Connect to JTAG targets (default: 0)
#             -remote <addr> : Remote hardware server address (if connect=1)
#             -tap_id <id>   : TAP ID for multi-device chains
#             -help          : Show help message
# return: Nothing (displays status)
# example: read_status -connect 1 -tap_id 0
#--------------------------------------------------------------------
proc read_status {args} {
    set connect 0
    set remote 0
    set tap_id ""
    set help 0
    
    # Parse command line arguments
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-connect"} {
            set connect [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-remote"} {
            set remote [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-tap_id"} {
            set tap_id [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-help"} {
            set help 1
        }
    }
    
    # Show help if requested
    if {$help != 0} {
        help -read_status
    } else {
        # Connect to JTAG if requested
        if {$connect == 1} {
            puts "INFO: Connecting to JTAG Targets"
            if {$remote == 0} {
                connect
            } else {
                puts "Info: Connecting to remote hw_server: $remote"
                connect -url TCP:${remote}:3121
            }
        }
        
        # Validate TAP devices are available
        if {[llength [get_tap_ids]] == 0} {
            puts "Error: No TAP devices found on chain."
            return ""
        } elseif {[llength [get_tap_ids]] == 1} {
            # Auto-select single TAP
            set tap_id [lindex [get_tap_ids] 0]
        }

        # Handle multiple TAP devices
        if {[llength [get_tap_ids]] > 1 && $tap_id == ""} {
            puts "INFO: Multiple TAP [get_tap_ids] devices found on chain."
            puts "      Please use the -tap_id switch to select your device"
            return ""
        }

        # Validate and find TAP ID index if specified
        if {$tap_id != ""} {
            set tap_ids [get_tap_ids]
            set tap_id_found 0
            for {set i 0} {$i < [llength $tap_ids]} {incr i} {
                if {[lindex $tap_ids $i] == $tap_id} {
                    set index $i
                    set tap_id_found 1
                    break
                }
            }
            if {$tap_id_found == 0} {
                puts "Error: Invalid -tap_id ${tap_id}. Valid TAP are [get_tap_ids] devices found on chain."
                return ""
            }
        }

        # Read and display JTAG status
        puts "INFO: Setting TAP ID to $tap_id"
        set arch [get_arch -tap_id $tap_id]
        jtag targets $tap_id
        puts "JTAG Status at TAP at index $tap_id"
        puts [jtag_status $arch]
        
        # For Versal, perform additional status lookup
        if {$arch == "versal"} {
            versal_jtag_status_lookup [jtag_status $arch]
        }

        if {$connect == 1} {
            puts "INFO: Disconnecting"
        }
    }
}

#--------------------------------------------------------------------
# This function reads the error status register from the PL TAP
#
# Connects to the device, reads the JTAG error status register, and
# displays any detected errors with detailed error lookup information.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -connect <0|1> : Connect to JTAG targets (default: 0)
#             -remote <addr> : Remote hardware server address (if connect=1)
#             -tap_id <id>   : TAP ID for multi-device chains
#             -help          : Show help message
# return: Nothing (displays error status)
# example: read_error_status -connect 1 -tap_id 0
#--------------------------------------------------------------------
proc read_error_status {args} {
    set connect 0
    set remote 0
    set tap_id ""
    set help 0
    set tap 0
    
    # Parse command line arguments
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-connect"} {
            set connect [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-remote"} {
            set remote [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-tap_id"} {
            set tap_id [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-help"} {
            set help 1
        }
    }
    
    # Show help if requested
    if {$help != 0} {
        help -read_error_status
    } else {
        # Connect to JTAG if requested
        if {$connect == 1} {
            puts "INFO: Connecting to JTAG Targets"
            if {$remote == 0} {
                connect
            } else {
                puts "Info: Connecting to remote hw_server: $remote"
                connect -url TCP:${remote}:3121
            }
        }
        
        # Validate TAP devices are available
        if {[llength [get_tap_ids]] == 0} {
            puts "Error: No TAP devices found on chain."
            return ""
        } elseif {[llength [get_tap_ids]] == 1} {
            # Auto-select single TAP
            set tap_id [lindex [get_tap_ids] 0]
        }

        # Handle multiple TAP devices
        if {[llength [get_tap_ids]] > 1 && $tap_id == ""} {
            puts "INFO: Multiple TAP [get_tap_ids] devices found on chain."
            puts "      Please use the -tap_id switch to select your device"
            return ""
        }

        # Validate and find TAP ID index if specified
        if {$tap_id != ""} {
            set tap_ids [get_tap_ids]
            set tap_id_found 0
            for {set i 0} {$i < [llength $tap_ids]} {incr i} {
                if {[lindex $tap_ids $i] == $tap_id} {
                    set index $i
                    set tap_id_found 1
                    break
                }
            }
            if {$tap_id_found == 0} {
                puts "Error: Invalid -tap_id ${tap_id}. Valid TAP are [get_tap_ids] devices found on chain."
                return ""
            }
        }

        # Read and display error status
        puts "INFO: Setting TAP ID to $tap_id"
        set arch [get_arch -tap_id $tap_id]
        jtag targets $tap_id
        puts "Error Status at TAP at index $tap_id"
        set error_status [error_status $arch]
        
        if {$error_status == 0} {
            puts "No Error(s) detected"
        } else {
            puts $error_status
            # Perform error lookup for detailed error information
            error_lookup $error_status $arch
        }
        
        if {$connect == 1} {
            puts "INFO: Disconnecting"
        }
    }
}

#--------------------------------------------------------------------
# This function writes a control value to the PL TAP via JTAG
#
# Connects to the device and writes a control value to the JTAG control
# register. Used for various PL TAP control operations.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -value <val>   : Control value to write (required)
#             -connect <0|1> : Connect to JTAG targets (default: 0)
#             -remote <addr> : Remote hardware server address (if connect=1)
#             -tap_id <id>   : TAP ID for multi-device chains
#             -help          : Show help message
# return: Nothing
# example: write_jtag_cntrl -value 3 -connect 1 -tap_id 0
#--------------------------------------------------------------------
proc write_jtag_cntrl {args} {
    set connect 0
    set remote 0
    set value ""
    set tap_id ""
    set help 0
    set tap 0
    
    # Parse command line arguments
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-connect"} {
            set connect [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-remote"} {
            set remote [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-value"} {
            set value [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-tap_id"} {
            set tap_id [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-help"} {
            set help 1
        }
    }
    
    # Show help if requested
    if {$help != 0} {
        help -write_jtag_cntrl
    } else {
        # Validate required parameter
        if {$value == ""} {
            puts "Error: No -value passed"
            return ""
        }
        
        # Connect to JTAG if requested
        if {$connect == 1} {
            puts "INFO: Connecting to JTAG Targets"
            if {$remote == 0} {
                connect
            } else {
                puts "Info: Connecting to remote hw_server: $remote"
                connect -url TCP:${remote}:3121
            }
        }
        
        # Validate TAP devices are available
        if {[llength [get_tap_ids]] == 0} {
            puts "Error: No TAP devices found on chain."
            return ""
        } elseif {[llength [get_tap_ids]] == 1} {
            # Auto-select single TAP
            set tap_id [lindex [get_tap_ids] 0]
        }

        # Handle multiple TAP devices
        if {[llength [get_tap_ids]] > 1 && $tap_id == ""} {
            puts "INFO: Multiple TAP [get_tap_ids] devices found on chain."
            puts "      Please use the -tap_id switch to select your device"
            return ""
        }

        # Validate and find TAP ID index if specified
        if {$tap_id != ""} {
            set tap_ids [get_tap_ids]
            set tap_id_found 0
            for {set i 0} {$i < [llength $tap_ids]} {incr i} {
                if {[lindex $tap_ids $i] == $tap_id} {
                    set index $i
                    set tap_id_found 1
                    break
                }
            }
            if {$tap_id_found == 0} {
                puts "Error: Invalid -tap_id ${tap_id}. Valid TAP are [get_tap_ids] devices found on chain."
                return ""
            }
        }

        # Write control value
        puts "INFO: Setting TAP ID to $tap_id"
        set arch [get_arch -tap_id $tap_id]
        puts "Write JTAG CNTRL TAP at index $tap_id with value $value"
        jtag targets $tap_id
        jtag_ctrl -arch $arch -value $value

        if {$connect == 1} {
            puts "INFO: Disconnecting"
        }
    }
}

#--------------------------------------------------------------------
# This function retrieves all node IDs from the current JTAG target
#
# Parses JTAG target properties to extract all node_id values.
#
#--------------------------------------------------------------------
#
# return: List of node IDs
# example: get_node_ids
#--------------------------------------------------------------------
proc get_node_ids {} {
    set node_ids ""
    set info [split [jtag target -target-properties] " "]
    
    # Extract all node_id values
    for {set j 0} {$j < [llength $info]} {incr j} {
        if {[lindex $info $j] == "node_id"} {
            lappend node_ids [lindex $info [expr {$j + 1}]]
        }
    }
    
    return [split $node_ids]
}

#--------------------------------------------------------------------
# This function retrieves all TAP (Test Access Port) IDs from the JTAG scan chain
#
# The function scans the JTAG chain, matches IDCODEs, and extracts unique TAP node IDs.
# This is useful for identifying multiple devices on the same JTAG chain.
#
#--------------------------------------------------------------------
#
# return: List of unique TAP IDs (node IDs) found on the JTAG chain, sorted
# example: get_tap_ids
#          Returns: "0 1 2" if three TAP devices are found
#--------------------------------------------------------------------
proc get_tap_ids {} {
    set tap_ids ""
    
    # Get the scan chain information
    set scan_chain [get_scan_chain]
    set scan_chain [split $scan_chain]
    
    # Iterate through the scan chain (IDCODEs are at even indices)
    for {set i 0} {$i < [llength $scan_chain]} {incr i} {
        # Process only even indices (where IDCODEs are located)
        if {![expr {$i % 2}]} {
            # Get target properties for current JTAG target
            set info [split [jtag target -target-properties] " "]
            
            # Parse properties to find node_id and idcode
            for {set j 0} {$j < [llength $info]} {incr j} {
                # Extract node_id when found
                if {[lindex $info $j] == "node_id"} {
                    set index [lindex $info [expr {$j + 1}]]
                }
                
                # Match IDCODE from target properties with scan chain IDCODE
                if {[lindex $info $j] == "idcode"} {
                    if {[lindex $info [expr {$j + 1}]] == [lindex $scan_chain $i]} {
                        # Match found - add the corresponding node_id to the list
                        lappend tap_ids $index
                    }
                }
            }
        }
    }
    
    # Return sorted unique list of TAP IDs
    return [lsort -unique [split $tap_ids]]
}

#--------------------------------------------------------------------
# This function retrieves JTAG target IDs from the JTAG chain based on a filter
#
# Similar to get_target but uses jtag targets command instead of targets command.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -filter <pattern> : Filter pattern to match target names (e.g., "PSU*", "APU*")
# return: List of target IDs matching the filter criteria
# example: get_jtag_targets -filter "PSU"
#--------------------------------------------------------------------
proc get_jtag_targets {args} {
    set filter ""
    set ret_targets ""
    
    # Parse arguments to find -filter option
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-filter"} {
            set filter [lindex $args [expr {$i + 1}]]
        }
    }

    # Get target properties matching the filter
    set info [split [jtag targets -target-properties -filter {name =~ "${filter}*"}] " "]
    
    # Extract target IDs from the properties
    for {set i 0} {$i < [llength $info]} {incr i} {
        if {[lindex $info $i] == "node_id"} {
            set target_id [lindex $info [expr {$i + 1}]]
            lappend ret_targets $target_id
        }
    }
    
    return $ret_targets
}

#--------------------------------------------------------------------
# This function determines the Xilinx architecture by reading the ARM DAP IDCODE
# from the JTAG chain. It identifies Zynq, Zynq UltraScale+, or Versal devices.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -tap_id <tap_id> : Optional TAP ID to specify which device to query
#                                (required if multiple TAP devices are on the chain)
# return: Architecture string ("zynq", "zynqMP", "versal") or empty string on error
# example: get_arch
# example: get_arch -tap_id 0
#--------------------------------------------------------------------
proc get_arch {args} {
    set tap_id ""
    set index 0
    
    # Parse arguments to find -tap_id option
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-tap_id"} {
            set tap_id [lindex $args [expr {$i + 1}]]
        }
    }
    
    # Check if any TAP devices are found on the chain
    if {[llength [get_tap_ids]] == 0} {
        puts "Error: No TAP devices found on chain."
        return ""
    }

    # If multiple TAP devices exist and no tap_id specified, prompt user
    if {[llength [get_tap_ids]] > 1 && $tap_id == ""} {
        puts "INFO: Multiple TAP [get_tap_ids] devices found on chain."
        puts "      Please use the -tap_id switch to select your device"
        return ""
    }

    # If tap_id is specified, validate it and find the corresponding index
    if {$tap_id != ""} {
        set tap_ids [get_tap_ids]
        set tap_id_found 0
        
        # Find the index of the specified tap_id
        for {set i 0} {$i < [llength $tap_ids]} {incr i} {
            if {[lindex $tap_ids $i] == $tap_id} {
                set index $i
                set tap_id_found 1
                break
            }
        }
        
        # Validate that the tap_id exists
        if {$tap_id_found == 0} {
            puts "Error: Invalid -tap_id ${tap_id}. Valid TAP are [get_tap_ids] devices found on chain."
            return ""
        }
    }

    # Get ARM DAP IDCODEs from the JTAG chain
    set dap_idcodes [get_idcode -filter "arm_dap" -param "idcode"]
    
    # Verify that there are enough DAP devices for the selected index
    if {[expr {[llength $dap_idcodes] - 1}] < $index} {
        puts "Error: Cant find responding arm_dap for TAP ${tap_id}. Please run jtag targets to evaluate the jtag targets"
        return ""
    }

    # Get the specific DAP IDCODE for the selected device
    set dap_idcode [lindex [get_idcode -filter "arm_dap" -param "idcode"] $index]

    # Map IDCODE to architecture
    # 0x4ba00477 = Zynq-7000 series
    # 0x5ba00477 = Zynq UltraScale+ MPSoC
    # 0x6ba00477 or 0x4ba06477 = Versal
    if {$dap_idcode == "4ba00477"} {
        return "zynq"
    } elseif {$dap_idcode == "5ba00477"} {
        return "zynqMP"
    } elseif {$dap_idcode == "6ba00477" || $dap_idcode == "4ba06477"} {
        return "versal"
    } else {
        return ""
    }
}

#--------------------------------------------------------------------
# This function retrieves target IDs from the JTAG chain based on a filter
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -filter <pattern> : Filter pattern to match target names (e.g., "PSU*", "APU*")
# return: List of target IDs matching the filter criteria
# example: get_target -filter "PSU"
#--------------------------------------------------------------------
proc get_target {args} {
    set filter ""
    set ret_targets ""
    
    # Parse arguments to find -filter option
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-filter"} {
            set filter [lindex $args [expr {$i + 1}]]
        }
    }

    # Get target properties matching the filter
    set info [split [targets -target-properties -filter {name =~ "${filter}*"}] " "]
    
    # Extract target IDs from the properties
    for {set i 0} {$i < [llength $info]} {incr i} {
        if {[lindex $info $i] == "target_id"} {
            set target_id [lindex $info [expr {$i + 1}]]
            lappend ret_targets $target_id
        }
    }

    return $ret_targets
}

#--------------------------------------------------------------------
# This function retrieves the JTAG scan chain and reorders it to TAP-DAP format
#
# The function reads the scan chain, identifies ARM DAP devices, and reorders
# the chain so that TAP comes before DAP for proper sequencing.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list (currently unused)
# return: Scan chain list with TAP-DAP ordering
# example: get_scan_chain
#--------------------------------------------------------------------
proc get_scan_chain {args} {
    set scan_chain ""
    
    # Get target properties and extract IDCODEs
    set info [split [jtag target -target-properties] " "]
    for {set i 0} {$i < [llength $info]} {incr i} {
        if {[string trim [lindex $info $i] "{}"] == "idcode"} {
            lappend scan_chain [string trim [lindex $info [expr {$i + 1}]] "{}"]
        }
    }
    
    # Reorder scan chain to TAP-DAP format (TAP before DAP)
    set scan_chain [split $scan_chain]
    for {set i 0} {$i < [llength $scan_chain]} {incr i} {
        # Process even indices (where TAP IDCODEs are located)
        if {![expr {$i % 2}]} {
            # Check if this is an ARM DAP IDCODE (Zynq/ZynqMP/Versal)
            if {[lindex $scan_chain $i] == "4ba00477" || 
                [lindex $scan_chain $i] == "5ba00477" || 
                [lindex $scan_chain $i] == "6ba00477"} {
                # Swap TAP and DAP positions
                set temp_dap [lindex $scan_chain $i]
                set temp_tap [lindex $scan_chain [expr {$i + 1}]]
                set scan_chain [lreplace $scan_chain [expr {$i + 1}] [expr {$i + 1}] $temp_dap]
                set scan_chain [lreplace $scan_chain $i $i $temp_tap]
            }
        }
    }
    
    return $scan_chain
}

#--------------------------------------------------------------------
# This function retrieves IDCODE values from JTAG targets matching a filter
#
# Parses JTAG target properties to extract specific parameter values (like IDCODE)
# for targets that match the given filter pattern.
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -filter <pattern> : Filter pattern to match target names (e.g., "arm_dap")
#             -param <param>    : Parameter name to extract (e.g., "idcode")
# return: List of parameter values matching the filter
# example: get_idcode -filter "arm_dap" -param "idcode"
#--------------------------------------------------------------------
proc get_idcode {args} {
    set filter ""
    set param ""
    set ret_idcode ""
    
    # Parse arguments to find -filter and -param options
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-filter"} {
            set filter [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-param"} {
            set param [lindex $args [expr {$i + 1}]]
        }
    }

    # Validate required parameters
    if {$param == ""} {
        puts "Error: No -param passed"
        return ""
    }

    if {$filter == ""} {
        puts "Error: No -filter passed"
        return ""
    }

    # Get target properties matching the filter
    set info [split [jtag targets -target-properties -filter {name =~ "${filter}*"}] " "]
    
    # Parse properties to find matching filter and extract parameter values
    for {set i 0} {$i < [llength $info]} {incr i} {
        if {[string trim [lindex $info $i] "{}"] == $filter} {
            # Found matching filter, search for the requested parameter
            for {set j $i} {$j < [llength $info]} {incr j} {
                if {[string trim [lindex $info $j] "{}"] == $param} {
                    # Found the parameter, extract its value
                    lappend ret_idcode [string trim [lindex $info [expr {$j + 1}]] "{}"]
                }
            }
        }
    }
    
    return $ret_idcode
}

#--------------------------------------------------------------------
# This function reads the JTAG status register from the PL TAP
#
# Performs a JTAG sequence to read the status register. The capture width
# varies by architecture (32 bits for Zynq/ZynqMP, 36 bits for Versal).
#
#--------------------------------------------------------------------
#
# param arch: Target architecture ("zynq", "zynqMP", or "versal")
# return: Status register value as hexadecimal string with 0x prefix
# example: jtag_status "zynqMP"
#--------------------------------------------------------------------
proc jtag_status {arch} {
    # Create JTAG sequence
    set s [jtag seq]
    $s state RESET
    
    # Shift instruction register (IR) with value 0x2020 (status register select)
    $s irshift -state IDLE -int 12 2020
    
    # Capture data register (DR) - width depends on architecture
    if {$arch == "zynqMP" || $arch == "zynq"} {
        $s drshift -state IDLE -tdi 0 -capture 32
    } elseif {$arch == "versal"} {
        $s drshift -state IDLE -tdi 0 -capture 36
    }
    
    # Execute sequence and get result
    set r [$s run]
    $s delete
    
    # Convert binary result to hexadecimal string (byte-reversed)
    binary scan [string reverse [binary format H* $r]] H* x
    return 0x$x
}

#--------------------------------------------------------------------
# This function writes a control value to the PL TAP via JTAG
#
# Performs a JTAG sequence to write a value to the control register.
# The data register width varies by architecture (32 bits for Zynq/ZynqMP,
# 36 bits for Versal).
#
#--------------------------------------------------------------------
#
# param args: Variable arguments list, supports:
#             -arch <arch>   : Target architecture ("zynq", "zynqMP", or "versal")
#                             (default: "zynq")
#             -value <value> : Control value to write (default: 3)
# example: jtag_ctrl -arch "zynqMP" -value 5
#--------------------------------------------------------------------
proc jtag_ctrl {args} {
    set arch "zynq"
    set v 3
    
    # Parse arguments to find -arch and -value options
    for {set i 0} {$i < [llength $args]} {incr i} {
        if {[lindex $args $i] == "-arch"} {
            set arch [lindex $args [expr {$i + 1}]]
        }
        if {[lindex $args $i] == "-value"} {
            set v [lindex $args [expr {$i + 1}]]
        }
    }
    
    puts "Info: sending value $v to PL TAP on arch $arch"
    
    # Create JTAG sequence
    set s [jtag seq]
    $s state RESET
    
    # Shift instruction register (IR) with value 0x2084 (control register select)
    $s irshift -state IDLE -int 12 2084
    
    # Shift data register (DR) - width depends on architecture
    if {$arch == "zynqMP" || $arch == "zynq"} {
        $s drshift -state IDLE -int 32 $v
    } elseif {$arch == "versal"} {
        $s drshift -state IDLE -int 36 $v
    }
    
    # Execute sequence
    $s run
    $s delete
}

#--------------------------------------------------------------------
# This function reads the Device DNA (Device Non-Volatile Address) via JTAG
#
# Performs a JTAG sequence to read the unique Device DNA identifier.
# The DNA is 128 bits for all supported architectures.
#
#--------------------------------------------------------------------
#
# param arch: Target architecture ("zynq", "zynqMP", or "versal")
# return: Device DNA value as hexadecimal string with 0x prefix
# example: jtag_dna "zynqMP"
#--------------------------------------------------------------------
proc jtag_dna {arch} {
    # Create JTAG sequence
    set s [jtag seq]
    $s state RESET
    
    # Shift instruction register (IR) with value 0x3200 (DNA register select)
    $s irshift -state IDLE -int 12 3200
    
    # Capture 128-bit DNA register (same for all architectures)
    if {$arch == "zynqMP" || $arch == "zynq"} {
        $s drshift -state IDLE -tdi 0 -capture 128
    } elseif {$arch == "versal"} {
        $s drshift -state IDLE -tdi 0 -capture 128
    }
    
    # Execute sequence and get result
    set r [$s run]
    $s delete
    
    # Convert binary result to hexadecimal string (byte-reversed)
    binary scan [string reverse [binary format H* $r]] H* x
    return 0x$x
}

#--------------------------------------------------------------------
# This function reads the IDCODE register from the PL TAP via JTAG
#
# Performs a JTAG sequence to read the IDCODE register directly from
# the PL TAP. This is a low-level IDCODE read operation.
#
#--------------------------------------------------------------------
#
# param arch: Target architecture ("zynq", "zynqMP", or "versal")
# return: IDCODE value as hexadecimal string with 0x prefix
# example: jtag_idcode "zynqMP"
#--------------------------------------------------------------------
proc jtag_idcode {arch} {
    # Create JTAG sequence
    set s [jtag seq]
    $s state RESET
    
    # Shift instruction register (IR) with value 0x2400 (IDCODE register select)
    $s irshift -state IDLE -int 12 2400
    
    # Capture 32-bit IDCODE register (same for all architectures)
    if {$arch == "zynqMP" || $arch == "zynq"} {
        $s drshift -state IDLE -tdi 0 -capture 32
    } elseif {$arch == "versal"} {
        $s drshift -state IDLE -tdi 0 -capture 32
    }
    
    # Execute sequence and get result
    set r [$s run]
    $s delete
    
    # Convert binary result to hexadecimal string (byte-reversed)
    binary scan [string reverse [binary format H* $r]] H* x
    return 0x$x
}

#--------------------------------------------------------------------
# This function reads the error status register from the PL TAP via JTAG
#
# Performs a JTAG sequence to read the error status register. The capture
# width varies by architecture (121 bits for Zynq/ZynqMP, 161 bits for Versal).
#
#--------------------------------------------------------------------
#
# param arch: Target architecture ("zynq", "zynqMP", or "versal")
# return: Error status register value as hexadecimal string
# example: error_status "zynqMP"
#--------------------------------------------------------------------
proc error_status {arch} {
    # Create JTAG sequence
    set s [jtag seq]
    $s state RESET
    
    # Shift instruction register (IR) with value 0x4004 (error status register select)
    $s irshift -state IDLE -int 12 4004
    
    # Capture data register (DR) - width depends on architecture
    # TDI=1 to trigger error capture
    if {$arch == "zynqMP" || $arch == "zynq"} {
        $s drshift -state IDLE -tdi 1 -capture 121
    } elseif {$arch == "versal"} {
        $s drshift -state IDLE -tdi 1 -capture 161
    }
    
    # Execute sequence and get result
    set r [$s run]
    $s delete
    
    # Convert binary result to hexadecimal string (byte-reversed)
    binary scan [string reverse [binary format H* $r]] H* x
    return $x
}

#--------------------------------------------------------------------
# This function converts a hexadecimal string to binary format
#
#--------------------------------------------------------------------
#
# param hex: Hexadecimal string to convert
# return: Binary representation of the hexadecimal input
# example: hex2bin "FF"
#          Returns: "11111111"
#--------------------------------------------------------------------
proc hex2bin {hex} {
    binary scan [binary format H* $hex] B* bin
    return $bin
}

#--------------------------------------------------------------------
# This function converts a binary string to hexadecimal format
#
#--------------------------------------------------------------------
#
# param bin: Binary string to convert
# return: Hexadecimal representation of the binary input
# example: bin2hex "11111111"
#          Returns: "FF"
#--------------------------------------------------------------------
proc bin2hex {bin} {
    set result ""
    
    # Pad binary string to multiple of 4 bits
    set prepend [string repeat 0 [expr (4-[string length $bin]%4)%4]]
    
    # Process binary string in groups of 4 bits
    foreach g [regexp -all -inline {[01]{4}} $prepend$bin] {
        # Convert each 4-bit group to hex
        foreach {b3 b2 b1 b0} [split $g ""] {
            append result [format %X [expr {$b3*8+$b2*4+$b1*2+$b0}]]
        }
    }
    
    return $result
}

#--------------------------------------------------------------------
# This function displays help information for JTAG utility commands
#
#--------------------------------------------------------------------
#
# param args: Optional command name to show specific help
#             If empty, shows list of all supported commands
# return: Nothing (displays help text)
# example: help
# example: help -get_bootmode
#--------------------------------------------------------------------
proc help {args} {
    if {[string length $args] == 0} {
        puts "JTAG Util v1.2"
        puts "Supported commands:"
        puts "* get_bootmode"
        puts "* set_bootmode"
        puts "* read_status"
        puts "* read_error_status"
        puts "* write_jtag_cntrl"
    } else {
        if {$args == "-get_bootmode"} {
            puts "get_bootmode:"
            puts "Optional: -connect <0,1>. If users want to connect to JTAG Targets. Default 0"
            puts "Optional: -remote <IP ADDR>. Only used if connect is set to 1"
            puts "Optional: -tap_id <TAP ID>. However, if there is more than one device on the chain then this is expected"
            puts "******************************"
            puts "Returns: bootmode"
        }
        if {$args == "-set_bootmode"} {
            puts "set_bootmode:"
            puts "Expected -bootmode default JTAG"
            puts "Optional: -connect <0,1>. If users want to connect to JTAG Targets. Default 0"
            puts "Optional: -remote <IP ADDR>. Only used if connect is set to 1"
            puts "Optional: -list (List all the supported bootmodes for an arch"
            puts "Optional: -tap_id <TAP ID>. However, if there is more than one device on the chain then this is expected"
            puts "******************************"
            puts "Returns: Nothing"
        }
        if {$args == "-read_status"} {
            puts "read_status:"
            puts "Optional: -connect <0,1>. If users want to connect to JTAG Targets. Default 0"
            puts "Optional: -remote <IP ADDR>. Only used if connect is set to 1"
            puts "Optional: -tap_id <TAP ID>. However, if there is more than one device on the chain then this is expected"
            puts "******************************"
            puts "Returns: jtag status"
        }
        if {$args == "-read_error_status"} {
            puts "read_error_status:"
            puts "Optional: -connect <0,1>. If users want to connect to JTAG Targets. Default 0"
            puts "Optional: -remote <IP ADDR>. Only used if connect is set to 1"
            puts "Optional: -tap_id <TAP ID>. However, if there is more than one device on the chain then this is expected"
            puts "******************************"
            puts "Returns: boot error"
        }
        if {$args == "-write_jtag_cntrl"} {
            puts "write_jtag_cntrl:"
            puts "Optional: -connect <0,1>. If users want to connect to JTAG Targets. Default 0"
            puts "Optional: -remote <IP ADDR>. Only used if connect is set to 1"
            puts "Expected: write_jtag_cntrl -value <value>"
            puts "Optional: -tap_id <TAP ID>. However, if there is more than one device on the chain then this is expected"
            puts "******************************"
            puts "Returns: Nothing on Success"
        }
    }
}
