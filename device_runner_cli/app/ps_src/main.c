/**
 * @file main.c
 * @brief Main application entry point for JTAG UART Handler
 * 
 * This file contains the main() function that initializes and runs the
 * JTAG UART Handler application. It coordinates startup mode detection,
 * configuration, initialization, and entry into the appropriate mode
 * (interactive or script).
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.1.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 * @note This file is part of the Device Runner CLI project.
 * @note This file is licensed under the MIT License.
 * @note This file is part of the Device Runner CLI project.
 * 
 * History:
 * 2025-12-31 - Initial version
 * 
 * @see jtag_uart_handler.c for core application logic
 * @see display.h for display and print functions
 */

#include <stdio.h>
#include "xil_printf.h"

/* Project header files */
#include "include/types.h"
#include "include/constants.h"
#include "display.h"
#include "jtag_uart_handler.h"

/**
 * @brief Main application entry point
 * 
 * Initializes the JTAG UART Handler application:
 * 1. Detects startup mode (JTAG/UART, Interactive/Script)
 * 2. Configures application based on detected mode
 * 3. Prints startup banner
 * 4. Initializes shared memory communication
 * 5. Initializes test configuration
 * 6. Enters main loop (interactive or script mode)
 * 
 * @return 0 on normal exit (typically never reached in interactive mode)
 * 
 * @note In script mode, the application runs until MSG_TYPE_EXIT is received.
 *       In interactive mode, the application runs until user selects Exit.
 */
int main(void) {
    xil_printf("\r\n=== JTAG UART Handler Starting ===\r\n");
    
    // Detect startup mode (JTAG vs Script)
    startup_mode = detect_startup_mode();
    
    // Configure application based on detected mode
    configure_startup_mode();
    
    // Print startup banner with mode information
    print_startup_banner();
    
    // Initialize shared memory communication
    init_shared_memory();
    
    // Initialize test configuration
    initialize_test_config();
    
    // Main application loop based on startup mode
    if (script_mode) {
        xil_printf("Entering script mode...\r\n");
        run_script_mode();
    } else {
        xil_printf("Entering interactive mode...\r\n");
        run_interactive_mode();
    }
    
    xil_printf("\r\n=== JTAG UART Handler Exiting ===\r\n");
    return 0;
}

