/**
 * @file display.h
 * @brief Display and print function declarations for JTAG UART Handler
 * 
 * This header file declares all display and printing functions used for
 * user interface, menus, banners, and status displays.
 * 
 * @author Device Runner CLI
 * @version 2.0.0
 * @date 2024
 */

#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>
#include "include/types.h"
#include "include/constants.h"

/* External references to global configuration and state */
extern config_t config;
extern volatile int startup_mode;
extern volatile int script_mode;
extern volatile int app_mode;
extern volatile int menu_active;

/* Forward declarations for input functions */
char get_char_input(void);  /* Implemented in jtag_uart_handler.c */

/**
 * @brief Clear the terminal screen using ANSI escape sequences
 * 
 * Sends ANSI escape sequence to clear screen and move cursor to home position.
 * Works with ANSI-compatible terminals.
 */
void clear_screen(void);

/**
 * @brief Print the application banner
 * 
 * Displays the ASCII art banner showing "Device Runner" and version information.
 * Clears the screen first, then prints formatted banner with version and
 * platform information.
 */
void print_banner(void);

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
void show_main_menu(void);

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
void show_config_menu(void);

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
void display_configuration(void);

/**
 * @brief Print startup banner with mode information
 * 
 * Displays the application banner along with detected startup mode and
 * operational mode information. Shows whether script mode or interactive
 * mode is active.
 */
void print_startup_banner(void);

#endif /* DISPLAY_H */

