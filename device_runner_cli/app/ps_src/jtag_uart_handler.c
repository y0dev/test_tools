/**
 * @file jtag_uart_handler.c
 * @brief JTAG UART Handler - Main Coordinator
 * 
 * This file serves as the main coordinator for the JTAG UART Handler application.
 * It contains global variables, mode detection, configuration, and routing to
 * mode-specific implementations.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 2.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 * 
 * History:
 * 2025-12-31 - Refactored: Split into separate mode files (v2.0.0)
 * 
 * @see interactive_mode.c for interactive mode implementation
 * @see jtag_script_mode.c for JTAG script mode implementation
 * @see test_mode.c for test mode implementation
 * @see uart_script_mode.c for UART script mode implementation
 * @see shared_memory.c for shared memory communication
 * @see helpers.c for common utility functions
 */

#include <stdint.h>
#include "xil_printf.h"
#include "xil_io.h"

/* Project header files */
#include "jtag_uart_handler.h"
#include "include/types.h"
#include "include/constants.h"
#include "interactive_mode.h"
#include "jtag_script_mode.h"
#include "test_mode.h"
#include "uart_script_mode.h"

/* ============================================================================
 * Global Variables
 * ============================================================================ */

/* Application State Variables */
volatile int running = 1;                          /* Main application loop flag */
volatile int app_mode = MODE_INTERACTIVE;          /* Current app mode (interactive/background) */
volatile int startup_mode = MODE_JTAG_INTERACTIVE; /* Startup mode from hardware */
volatile int script_mode = 0;                      /* Script mode flag */
volatile int menu_active = 0;                      /* Menu active flag */
volatile int test_mode = 0;                        /* Test mode flag (exported for other modules) */

/* Test Configuration (exported for test_mode.c and shared_memory.c) */
test_config_t test_config = {
    .number_of_tests = 0,
    .current_test = 0,
    .test_timeout = 10000,
    .test_retries = 2,
    .tests_passed = 0,
    .tests_failed = 0,
    .test_in_progress = 0,
    .test_requires_reset = 0
};

test_case_t test_cases[MAX_TEST_CASES];

/* Default Configuration */
config_t config = {
    .device_name = "Default Device",
    .base_address = DATA_AREA_ADDR,
    .operation_mode = 1,  // Short
    .timeout_value = 5000,
    .debug_level = 1
};

/* ============================================================================
 * Mode Detection and Configuration
 * ============================================================================ */

/**
 * @brief Detect the startup mode from hardware registers
 * 
 * Reads the startup mode register to determine how the application was launched
 * (JTAG interactive, JTAG script, UART interactive, UART script, or test).
 * 
 * @return Detected startup mode value (MODE_JTAG_INTERACTIVE, MODE_JTAG_SCRIPT, etc.)
 */
int detect_startup_mode(void) {
    uint32_t mode_reg_value = 0;
    
    xil_printf("Detecting startup mode...\r\n");
    
    // Check startup mode register
    mode_reg_value = Xil_In32(STARTUP_MODE_REG_ADDR);
    if (mode_reg_value != 0) {
        xil_printf("Startup mode from register: 0x%08X\r\n", mode_reg_value);
        return mode_reg_value;
    }
    
    // Default to JTAG Interactive mode
    xil_printf("No specific mode detected - Defaulting to JTAG Interactive\r\n");
    return MODE_JTAG_INTERACTIVE;
}

/**
 * @brief Configure application based on detected startup mode
 * 
 * Sets application variables (script_mode, app_mode, menu_active, test_mode)
 * based on the detected startup mode from detect_startup_mode().
 */
void configure_startup_mode(void) {
    xil_printf("Configuring application for startup mode: 0x%08X\r\n", startup_mode);
    
    switch (startup_mode) {
        case MODE_JTAG_INTERACTIVE:
        {
            app_mode = MODE_INTERACTIVE;
            script_mode = 0;
            menu_active = 1;
            test_mode = 0;
            xil_printf("Configured: JTAG Interactive Mode\r\n");
            break;
        }

        case MODE_JTAG_SCRIPT:
        {
            // JTAG Script Mode: Commands sent through registers
            app_mode = MODE_BACKGROUND;
            script_mode = 1;
            menu_active = 0;
            test_mode = 0;
            xil_printf("Configured: JTAG Script Mode (register-based commands)\r\n");
            break;
        }
            
        case MODE_UART_INTERACTIVE:
        {
            app_mode = MODE_INTERACTIVE;
            script_mode = 0;
            menu_active = 1;
            test_mode = 0;
            xil_printf("Configured: UART Interactive Mode\r\n");
            break;
        }

        case MODE_UART_SCRIPT:
        {
            // UART Script Mode: Commands sent over UART (start, stop, exit)
            app_mode = MODE_BACKGROUND;
            script_mode = 1;
            menu_active = 0;
            test_mode = 0;
            xil_printf("Configured: UART Script Mode (UART commands: start, stop, exit)\r\n");
            break;
        }

        case MODE_TEST: 
        {
            app_mode = MODE_BACKGROUND;
            script_mode = 1;
            menu_active = 0;
            test_mode = 1;
            xil_printf("Configured: Test Mode\r\n");
            xil_printf("Test Mode: Processing register-based test commands\r\n");
            xil_printf("Commands sent via shared memory registers\r\n");
            break;
        }
            
        default:
        {
            app_mode = MODE_INTERACTIVE;
            script_mode = 0;
            menu_active = 1;
            test_mode = 0;
            xil_printf("Configured: Default Interactive Mode\r\n");
            break;
        }
    }
}

/* ============================================================================
 * Mode Execution Routing
 * ============================================================================ */

/**
 * @brief Run script mode main loop
 * 
 * Routes to the appropriate script mode implementation based on startup_mode:
 * - MODE_JTAG_SCRIPT: Routes to run_jtag_script_mode()
 * - MODE_TEST: Routes to run_test_mode()
 * - MODE_UART_SCRIPT: Routes to run_uart_script_mode()
 * 
 * @note Exported for use by main.c
 */
void run_script_mode(void) {
    // Route to appropriate mode-specific implementation
    if (startup_mode == MODE_JTAG_SCRIPT) {
        run_jtag_script_mode();
    } else if (startup_mode == MODE_TEST) {
        run_test_mode();
    } else if (startup_mode == MODE_UART_SCRIPT) {
        run_uart_script_mode();
    } else {
        xil_printf("ERROR: Unknown startup mode for script mode: 0x%08X\r\n", startup_mode);
        xil_printf("Defaulting to JTAG Script Mode\r\n");
        run_jtag_script_mode();
    }
}
