/**
 * @file jtag_script_mode.c
 * @brief JTAG script mode implementation
 * 
 * This file implements JTAG script mode functionality. JTAG script mode
 * processes register-based commands via shared memory (TCL command bits).
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#include <stdint.h>
#include "xil_printf.h"

#include "include/constants.h"
#include "helpers.h"
#include "shared_memory.h"
#include "jtag_script_mode.h"

/* External global variables */
extern volatile int running;
extern volatile int startup_mode;

/* ============================================================================
 * JTAG Script Mode Main Loop
 * ============================================================================ */

/**
 * @brief Run JTAG script mode main loop
 * 
 * Main loop for JTAG script mode. Continuously processes shared memory
 * messages (TCL commands via upper 16 bits) without displaying menus.
 */
void run_jtag_script_mode(void) {
    xil_printf("JTAG Script Mode: Processing register-based commands\r\n");
    xil_printf("Commands sent via shared memory registers\r\n");
    xil_printf("\r\n");
    
    while (running) {
        // Process shared memory messages (TCL commands via upper 16 bits)
        // The process_shared_memory_message() function handles TCL command bits
        process_shared_memory_message();
        
        // Small delay to prevent excessive CPU usage
        delay_us(10000); // 10ms polling interval
    }
}

