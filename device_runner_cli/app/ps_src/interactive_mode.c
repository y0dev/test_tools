/**
 * @file interactive_mode.c
 * @brief Interactive mode implementation
 * 
 * This file implements interactive mode functionality including menu-driven
 * interface, user input handling, and configuration management.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "xil_printf.h"
#include "xil_io.h"

#include "include/constants.h"
#include "include/types.h"
#include "helpers.h"
#include "shared_memory.h"
#include "display.h"
#include "interactive_mode.h"

/* External global variables */
extern config_t config;
extern volatile int running;
extern volatile int startup_mode;
extern volatile int script_mode;
extern volatile int app_mode;
extern volatile int menu_active;

/* Forward declarations */
static void handle_main_menu_selection(char choice);
static void handle_config_menu_selection(char choice);
static void update_device_name(void);
static void update_base_address(void);
static void update_operation_mode(void);
static void update_timeout_value(void);
static void update_debug_level(void);

/* ============================================================================
 * Interactive Mode Main Loop
 * ============================================================================ */

/**
 * @brief Run interactive mode main loop
 * 
 * Main loop for interactive menu-driven mode. Continuously displays menu,
 * processes user input, and handles shared memory messages.
 */
void run_interactive_mode(void) {
    while (running) {
        // Process shared memory messages first
        process_shared_memory_message();
        
        show_main_menu();
        char choice = get_char_input();
        handle_main_menu_selection(choice);
    }
}

/* ============================================================================
 * Menu Selection Handlers
 * ============================================================================ */

/**
 * @brief Handle main menu selection
 * 
 * Processes the user's main menu choice and executes the corresponding action:
 * - '1': Display current configuration
 * - '2': Show configuration menu
 * - '3': Run application with current settings
 * - '4': Display system status
 * - '5': Show help information
 * - '0': Exit application
 * 
 * @param[in] choice Character representing the menu choice ('0'-'5')
 */
static void handle_main_menu_selection(char choice) {
    switch (choice) {
        case '1':
        {
            display_configuration();
            break;
        }
            
        case '2': 
        {
            show_config_menu();
            char config_choice = get_char_input();
            handle_config_menu_selection(config_choice);
            break;
        }
                    
        case '3': 
        {
            print_banner();
            xil_printf("=== RUNNING APPLICATION ===\r\n");
            xil_printf("Device: %s\r\n", config.device_name);
            xil_printf("Base Address: 0x%08X\r\n", config.base_address);
            xil_printf("Operation Mode: %d\r\n", config.operation_mode);
            xil_printf("Timeout: %u ms\r\n", config.timeout_value);
            xil_printf("Debug Level: %d\r\n", config.debug_level);
            xil_printf("\r\nApplication running...\r\n");
            delay_us(2000000); // 2 second delay
            xil_printf("Application completed.\r\n");
            xil_printf("\r\nPress any key to continue...");
            get_char_input();
            break;
        }
                    
        case '4':
        {
            print_banner();
            xil_printf("=== SYSTEM STATUS ===\r\n");
            xil_printf("Startup Mode: 0x%08X\r\n", startup_mode);
            xil_printf("Script Mode: %s\r\n", script_mode ? "Active" : "Inactive");
            xil_printf("App Mode: %s\r\n", app_mode == MODE_INTERACTIVE ? "Interactive" : "Background");
            xil_printf("Menu Active: %s\r\n", menu_active ? "Yes" : "No");
            xil_printf("\r\nPress any key to continue...");
            get_char_input();
            break;
        }
            
        case '5':
        {
            print_banner();
            xil_printf("=== HELP ===\r\n");
            xil_printf("Main Menu Options:\r\n");
            xil_printf("1. View Configuration - Display current settings\r\n");
            xil_printf("2. Configure Settings - Modify configuration parameters\r\n");
            xil_printf("3. Run Application - Execute with current configuration\r\n");
            xil_printf("4. Get Status - Display system status\r\n");
            xil_printf("5. Help - Show this help information\r\n");
            xil_printf("0. Exit - Exit the application\r\n");
            xil_printf("\r\nConfiguration Options:\r\n");
            xil_printf("1. Device Name - String input with echo\r\n");
            xil_printf("2. Base Address - Hex input with echo\r\n");
            xil_printf("3. Operation Mode - List selection (no Enter required)\r\n");
            xil_printf("4. Timeout Value - Hex input with echo\r\n");
            xil_printf("5. Debug Level - List selection (no Enter required)\r\n");
            xil_printf("\r\nPress any key to continue...");
            get_char_input();
            break;
        }
            
        case '0':
        {
            print_banner();
            xil_printf("=== EXITING ===\r\n");
            xil_printf("Goodbye!\r\n");
            
            // Set the EXIT bit in the command register
            Xil_Out32(CMD_REG_ADDR, set_bit(0, CMD_BIT_APP_EXIT));
            
            // Wait for the response register to be cleared
            while (Xil_In32(RESP_REG_ADDR) != 0) {
                delay_us(100);
            }
            
            running = 0;
            break;
        }
            
        default: 
        {
            xil_printf("\a"); // beep for invalid choice
            break;
        }
    }
}

/**
 * @brief Handle configuration menu selection
 * 
 * Processes the user's configuration menu choice and updates the corresponding setting:
 * - '1': Update device name
 * - '2': Update base address
 * - '3': Update operation mode
 * - '4': Update timeout value
 * - '5': Update debug level
 * - '6': Display current configuration
 * - '0': Return to main menu (handled by caller)
 * 
 * @param[in] choice Character representing the menu choice ('0'-'6')
 */
static void handle_config_menu_selection(char choice) {
    switch (choice) {
        case '1': 
        {
            update_device_name();
            break;
        }
        case '2': 
        {
            update_base_address();
            break;
        }
        case '3': 
        {
            update_operation_mode();
            break;
        }
                    
        case '4': 
        {
            update_timeout_value();
            break;
        }
        case '5': 
        {
            update_debug_level();
            break;
        }
        case '6': 
        {
            display_configuration();
            break;
        }
        case '0': 
        {
            // Back to main menu - handled by caller
            break;
        }
        default: 
        {
            xil_printf("\a"); // beep for invalid choice
            break;
        }
    }
}

/* ============================================================================
 * Configuration Update Functions
 * ============================================================================ */

/**
 * @brief Update device name configuration
 * 
 * Prompts user for new device name using string input, then updates
 * config.device_name. Displays current value before prompting for new value.
 */
static void update_device_name(void) {
    print_banner();
    xil_printf("=== UPDATE DEVICE NAME ===\r\n");
    xil_printf("Current: %s\r\n", config.device_name);
    xil_printf("\r\n");
    
    get_string_input(config.device_name, MAX_STRING_LEN, "Enter new device name");
    
    xil_printf("\r\nDevice name updated to: %s\r\n", config.device_name);
    xil_printf("Press any key to continue...");
    get_char_input();
}

/**
 * @brief Update base address configuration
 * 
 * Prompts user for new base address using hex input, then updates
 * config.base_address. Displays current value before prompting for new value.
 */
static void update_base_address(void) {
    print_banner();
    xil_printf("=== UPDATE BASE ADDRESS ===\r\n");
    xil_printf("Current: 0x%08X\r\n", config.base_address);
    xil_printf("\r\n");
    
    config.base_address = get_hex_input("Enter new base address (hex)");
    
    xil_printf("\r\nBase address updated to: 0x%08X\r\n", config.base_address);
    xil_printf("Press any key to continue...");
    get_char_input();
}

/**
 * @brief Update operation mode configuration
 * 
 * Prompts user to select operation mode from a list:
 * - 1: Short
 * - 2: Medium
 * - 3: Long
 * 
 * Updates config.operation_mode with the selected value.
 */
static void update_operation_mode(void) {
    const char *options[] = {"Short", "Medium", "Long"};
    
    print_banner();
    xil_printf("=== UPDATE OPERATION MODE ===\r\n");
    xil_printf("Current: %d (%s)\r\n", config.operation_mode, 
               options[config.operation_mode - 1]);
    xil_printf("\r\n");
    
    config.operation_mode = get_list_selection("Select operation mode", options, 3);
    
    xil_printf("\r\nOperation mode updated to: %d (%s)\r\n", 
               config.operation_mode, options[config.operation_mode - 1]);
    xil_printf("Press any key to continue...");
    get_char_input();
}

/**
 * @brief Update timeout value configuration
 * 
 * Prompts user for new timeout value using hex input, then updates
 * config.timeout_value. Displays current value before prompting for new value.
 */
static void update_timeout_value(void) {
    print_banner();
    xil_printf("=== UPDATE TIMEOUT VALUE ===\r\n");
    xil_printf("Current: 0x%08X (%u ms)\r\n", config.timeout_value, config.timeout_value);
    xil_printf("\r\n");
    
    config.timeout_value = get_hex_input("Enter new timeout value (hex)");
    
    xil_printf("\r\nTimeout value updated to: 0x%08X (%u ms)\r\n", 
               config.timeout_value, config.timeout_value);
    xil_printf("Press any key to continue...");
    get_char_input();
}

/**
 * @brief Update debug level configuration
 * 
 * Prompts user to select debug level from a list:
 * - 1: Low
 * - 2: Medium
 * - 3: High
 * - 4: Verbose
 * 
 * Updates config.debug_level with the selected value.
 */
static void update_debug_level(void) {
    const char *options[] = {"Low", "Medium", "High", "Verbose"};
    
    print_banner();
    xil_printf("=== UPDATE DEBUG LEVEL ===\r\n");
    xil_printf("Current: %d (%s)\r\n", config.debug_level, 
               options[config.debug_level - 1]);
    xil_printf("\r\n");
    
    config.debug_level = get_list_selection("Select debug level", options, 4);
    
    xil_printf("\r\nDebug level updated to: %d (%s)\r\n", 
               config.debug_level, options[config.debug_level - 1]);
    xil_printf("Press any key to continue...");
    get_char_input();
}

