/**
 * @file display.c
 * @brief Display and print function implementations for JTAG UART Handler
 * 
 * This file implements all display and printing functions used for
 * user interface, menus, banners, and status displays.
 * 
 * @author Device Runner CLI
 * @version 2.0.0
 * @date 2024
 */

#include <stdio.h>
#include <stdint.h>
#include "xil_printf.h"
#include "include/types.h"
#include "include/constants.h"
#include "display.h"

/* External references - declared in jtag_uart_handler.c */
char get_char_input(void);  /* Forward declaration - implemented in main file */

/**
 * @brief Clear the terminal screen using ANSI escape sequences
 * 
 * Sends ANSI escape sequence (\033[2J\033[H) to clear screen and move cursor
 * to home position. Works with ANSI-compatible terminals.
 * 
 * @note Requires terminal to support ANSI escape sequences (most modern
 *       terminals do, including Tera Term and PuTTY)
 */
void clear_screen(void) {
    // Send ANSI escape sequence to clear screen
    xil_printf("\033[2J\033[H");
}

/**
 * @brief Print the application banner
 * 
 * Displays the ASCII art banner showing "Device Runner" and version information.
 * Clears the screen first, then prints formatted banner with version and
 * platform information.
 * 
 * Banner includes:
 * - ASCII art "Device Runner" text
 * - Version number (v2.0.0)
 * - Platform identifier (PS Version)
 * - Brief description
 */
void print_banner(void) {
    clear_screen();
    xil_printf("\r\n");
    xil_printf("########  ######## ##     ## ####  ######  ########     ######  ##       #### \r\n");
    xil_printf("##     ## ##       ##     ##  ##  ##    ## ##          ##    ## ##        ##  \r\n");
    xil_printf("##     ## ##       ##     ##  ##  ##       ##          ##       ##        ##  \r\n");
    xil_printf("##     ## ######   ##     ##  ##  ##       ######      ##       ##        ##  \r\n");
    xil_printf("##     ## ##        ##   ##   ##  ##       ##          ##       ##        ##  \r\n");
    xil_printf("##     ## ##         ## ##    ##  ##    ## ##          ##    ## ##        ##  \r\n");
    xil_printf("########  ########    ###    ####  ######  ########     ######  ######## #### \r\n");
    xil_printf("\r\n");
    xil_printf("    JTAG UART Handler v2.0.0 (PS Version)\r\n");
    xil_printf("    FPGA PS Baremetal Communication Interface\r\n");
    xil_printf("\r\n");
}

/**
 * @brief Display the main menu options
 * 
 * Shows the main menu with all available options:
 * - View Configuration
 * - Configure Settings
 * - Run Application
 * - Get Status
 * - Help
 * - Exit
 * 
 * Prompts user to enter a choice (0-5).
 */
void show_main_menu(void) {
    print_banner();
    xil_printf("=== MAIN MENU ===\r\n");
    xil_printf("1. View Configuration\r\n");
    xil_printf("2. Configure Settings\r\n");
    xil_printf("3. Run Application\r\n");
    xil_printf("4. Get Status\r\n");
    xil_printf("5. Help\r\n");
    xil_printf("0. Exit\r\n");
    xil_printf("\r\nEnter choice (0-5): ");
}

/**
 * @brief Display the configuration menu options
 * 
 * Shows the configuration submenu with options to modify:
 * - Device Name
 * - Base Address
 * - Operation Mode
 * - Timeout Value
 * - Debug Level
 * - View Configuration (display current settings)
 * - Back to Main Menu
 * 
 * Prompts user to enter a choice (0-6).
 */
void show_config_menu(void) {
    print_banner();
    xil_printf("=== CONFIGURATION MENU ===\r\n");
    xil_printf("1. Device Name (String)\r\n");
    xil_printf("2. Base Address (Hex)\r\n");
    xil_printf("3. Operation Mode (List)\r\n");
    xil_printf("4. Timeout Value (Hex)\r\n");
    xil_printf("5. Debug Level (List)\r\n");
    xil_printf("6. View Current Configuration\r\n");
    xil_printf("0. Back to Main Menu\r\n");
    xil_printf("\r\nEnter choice (0-6): ");
}

/**
 * @brief Display current configuration values
 * 
 * Prints all current configuration parameters in a formatted display:
 * - Device name
 * - Base address (hex)
 * - Operation mode (number and text)
 * - Timeout value (hex and decimal)
 * - Debug level (number and text)
 * 
 * Waits for user keypress before returning to menu.
 */
void display_configuration(void) {
    print_banner();
    xil_printf("=== CURRENT CONFIGURATION ===\r\n");
    xil_printf("\r\n");
    xil_printf("Device Name:     %s\r\n", config.device_name);
    xil_printf("Base Address:    0x%08X\r\n", config.base_address);
    
    const char *mode_names[] = {"", "Short", "Medium", "Long"};
    xil_printf("Operation Mode:  %d (%s)\r\n", config.operation_mode, 
               mode_names[config.operation_mode]);
    
    xil_printf("Timeout Value:   0x%08X (%u ms)\r\n", config.timeout_value, config.timeout_value);
    
    const char *debug_names[] = {"", "Low", "Medium", "High", "Verbose"};
    xil_printf("Debug Level:     %d (%s)\r\n", config.debug_level, 
               debug_names[config.debug_level]);
    
    xil_printf("\r\n");
    xil_printf("Press any key to continue...");
    get_char_input();
}

/**
 * @brief Print startup banner with mode information
 * 
 * Displays the application banner along with detected startup mode and
 * operational mode information. Shows whether script mode or interactive
 * mode is active.
 * 
 * Displays different messages based on startup_mode:
 * - MODE_JTAG_INTERACTIVE
 * - MODE_JTAG_SCRIPT
 * - MODE_UART_INTERACTIVE
 * - MODE_UART_SCRIPT
 */
void print_startup_banner(void) {
    print_banner();
    
    // Print mode-specific information
    switch (startup_mode) {
        case MODE_JTAG_INTERACTIVE:
            xil_printf("=== STARTUP MODE: JTAG INTERACTIVE ===\r\n");
            xil_printf("Interface: JTAG UART\r\n");
            xil_printf("Operation: Interactive Menu System\r\n");
            break;
            
        case MODE_JTAG_SCRIPT:
            xil_printf("=== STARTUP MODE: JTAG SCRIPT ===\r\n");
            xil_printf("Interface: JTAG UART\r\n");
            xil_printf("Operation: Background Command Processing\r\n");
            break;
            
        case MODE_UART_INTERACTIVE:
            xil_printf("=== STARTUP MODE: UART INTERACTIVE ===\r\n");
            xil_printf("Interface: UART\r\n");
            xil_printf("Operation: Interactive Menu System\r\n");
            break;
            
        case MODE_UART_SCRIPT:
            xil_printf("=== STARTUP MODE: UART SCRIPT ===\r\n");
            xil_printf("Interface: UART\r\n");
            xil_printf("Operation: Background Command Processing\r\n");
            break;
            
        default:
            xil_printf("=== STARTUP MODE: DEFAULT INTERACTIVE ===\r\n");
            xil_printf("Interface: JTAG UART\r\n");
            xil_printf("Operation: Interactive Menu System\r\n");
            break;
    }
    
    xil_printf("\r\n");
    
    if (script_mode) {
        xil_printf("Script Mode Active - Commands processed via messages\r\n");
    } else {
        xil_printf("Interactive Mode Active - Use menu system\r\n");
    }
    
    xil_printf("\r\n");
}

