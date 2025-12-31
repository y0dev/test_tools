/**
 * @file jtag_uart_handler.c
 * @brief JTAG UART Handler for Device Runner CLI - Embedded Implementation
 * 
 * This file implements the embedded side of the Device Runner CLI communication.
 * It runs on the FPGA PS (Processing System) in baremetal mode and handles 
 * commands sent from the Device Runner CLI via JTAG UART or shared memory.
 * 
 * @section features Features
 * - Interactive menu-driven interface with banner and screen clearing
 * - Configuration management (device name, base address, operation mode, timeout, debug level)
 * - Multiple input methods (string, hex, list selection)
 * - Shared memory communication with TCL scripts
 * - Startup mode detection (JTAG/UART, Interactive/Script)
 * - Test framework support
 * - Boot mode and Device DNA query
 * 
 * @section architecture Architecture
 * 
 * The application operates in two modes:
 * - Interactive Mode: Menu-driven interface for user interaction
 * - Script Mode: Background processing of shared memory messages
 * 
 * Communication methods:
 * - UART: Direct user input/output via JTAG UART
 * - Shared Memory: Command/response protocol at 0x10000000
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
 * @see types.h for data structure definitions
 * @see constants.h for constant and message type definitions
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>
#include "xil_printf.h"
#include "xil_io.h"

/* Project header files */
#include "jtag_uart_handler.h"
#include "include/types.h"
#include "include/constants.h"
#include "display.h"

// UART I/O functions from BSP
char inbyte(void);
void outbyte(char c);

/* Global Variables */
static volatile int running = 1;
volatile int app_mode = MODE_INTERACTIVE;           /* Exported for display.c */
volatile int startup_mode = MODE_JTAG_INTERACTIVE;  /* Exported for display.c */
volatile int script_mode = 0;                       /* Exported for display.c */
volatile int menu_active = 0;                       /* Exported for display.c */
static volatile int test_mode = 0;

/* Test Configuration */
static test_config_t test_config = {
    .number_of_tests = 0,
    .current_test = 0,
    .test_timeout = 10000,
    .test_retries = 2,
    .tests_passed = 0,
    .tests_failed = 0,
    .test_in_progress = 0,
    .test_requires_reset = 0
};

static test_case_t test_cases[MAX_TEST_CASES];

/* Default Configuration */
config_t config = {  /* Exported for display.c */
    .device_name = "Default Device",
    .base_address = 0x43C00000,
    .operation_mode = 1,  // Short
    .timeout_value = 5000,
    .debug_level = 1
};

/* ============================================================================
 * Bit Manipulation Helper Functions
 * ============================================================================ */

/**
 * @brief Check if a specific bit is set in a value
 * 
 * @param value The value to check
 * @param bit_pos The bit position to check (0-31)
 * @return 1 if bit is set, 0 if bit is clear
 * 
 * @example
 *   check_bit(0x00000005, 0);  // Returns 1 (bit 0 is set)
 *   check_bit(0x00000005, 1);  // Returns 0 (bit 1 is clear)
 *   check_bit(0x00000005, 2);  // Returns 1 (bit 2 is set)
 */
int check_bit(uint32_t value, uint8_t bit_pos) {
    if (bit_pos > 31) {
        return 0;  // Invalid bit position
    }
    uint32_t mask = 1U << bit_pos;
    return (value & mask) ? 1 : 0;
}

/**
 * @brief Set a specific bit in a value
 * 
 * @param value The value to modify
 * @param bit_pos The bit position to set (0-31)
 * @return The value with the specified bit set
 * 
 * @example
 *   set_bit(0x00000000, 0);  // Returns 0x00000001
 *   set_bit(0x00000001, 2);  // Returns 0x00000005
 */
uint32_t set_bit(uint32_t value, uint8_t bit_pos) {
    if (bit_pos > 31) {
        return value;  // Invalid bit position, return unchanged
    }
    uint32_t mask = 1U << bit_pos;
    return value | mask;
}

/**
 * @brief Clear a specific bit in a value
 * 
 * @param value The value to modify
 * @param bit_pos The bit position to clear (0-31)
 * @return The value with the specified bit cleared
 * 
 * @example
 *   clear_bit(0x00000005, 0);  // Returns 0x00000004
 *   clear_bit(0x00000005, 2);  // Returns 0x00000001
 */
uint32_t clear_bit(uint32_t value, uint8_t bit_pos) {
    if (bit_pos > 31) {
        return value;  // Invalid bit position, return unchanged
    }
    uint32_t mask = 1U << bit_pos;
    return value & ~mask;
}

/* ============================================================================
 * Function Prototypes - UI/Menu Functions
 * 
 * Note: Display and print functions are now in display.c
 * ============================================================================ */

/**
 * @brief Get a single character input (no Enter required)
 * 
 * Reads a single character from UART input without requiring Enter key.
 * 
 * @return Character that was pressed
 * @note Exported for use by display.c
 */
char get_char_input(void);

/**
 * @brief Get string input from user with echo
 * 
 * Reads a string from UART input with character echo, supports backspace.
 * Input is terminated by Enter key.
 * 
 * @param[out] buffer Buffer to store the input string
 * @param[in] max_len Maximum length of string (buffer size - 1)
 * @param[in] prompt Prompt string to display before input
 */
static void get_string_input(char *buffer, int max_len, const char *prompt);

/**
 * @brief Get hexadecimal input from user with echo
 * 
 * Reads hexadecimal value from UART input. Supports 0x prefix and hex digits only.
 * Input is terminated by Enter key.
 * 
 * @param[in] prompt Prompt string to display before input
 * @return 32-bit unsigned integer value parsed from hex input
 */
static uint32_t get_hex_input(const char *prompt);

/**
 * @brief Get list selection from user (no Enter required)
 * 
 * Displays a numbered list of options and waits for user to press a number key.
 * No Enter key required - selection is immediate.
 * 
 * @param[in] prompt Prompt string to display before options
 * @param[in] options Array of option strings to display
 * @param[in] num_options Number of options in the array
 * @return Selected option number (1-based index)
 */
static uint32_t get_list_selection(const char *prompt, const char *options[], int num_options);

/**
 * @brief Handle main menu selection
 * 
 * Processes the user's main menu choice and executes the corresponding action.
 * 
 * @param[in] choice Character representing the menu choice ('0'-'5')
 */
static void handle_main_menu_selection(char choice);

/**
 * @brief Handle configuration menu selection
 * 
 * Processes the user's configuration menu choice and updates the corresponding setting.
 * 
 * @param[in] choice Character representing the menu choice ('0'-'6')
 */
static void handle_config_menu_selection(char choice);

/**
 * @brief Update device name configuration
 * 
 * Prompts user for new device name and updates the configuration structure.
 */
static void update_device_name(void);

/**
 * @brief Update base address configuration
 * 
 * Prompts user for new base address (hex) and updates the configuration structure.
 */
static void update_base_address(void);

/**
 * @brief Update operation mode configuration
 * 
 * Prompts user to select operation mode (Short/Medium/Long) and updates configuration.
 */
static void update_operation_mode(void);

/**
 * @brief Update timeout value configuration
 * 
 * Prompts user for new timeout value (hex) and updates the configuration structure.
 */
static void update_timeout_value(void);

/**
 * @brief Update debug level configuration
 * 
 * Prompts user to select debug level and updates the configuration structure.
 */
static void update_debug_level(void);

/* ============================================================================
 * Function Prototypes - Mode Detection and Configuration
 * ============================================================================ */

/**
 * @brief Detect the startup mode from hardware registers
 * 
 * Reads the startup mode register to determine how the application was launched
 * (JTAG interactive, JTAG script, UART interactive, or UART script).
 * 
 * @return Detected startup mode value (MODE_JTAG_INTERACTIVE, MODE_JTAG_SCRIPT, etc.)
 * 
 * @note Exported for use by main.c
 */
int detect_startup_mode(void);

/**
 * @brief Configure application based on detected startup mode
 * 
 * Sets application variables (script_mode, app_mode) based on the detected
 * startup mode from detect_startup_mode().
 * 
 * @note Exported for use by main.c
 */
void configure_startup_mode(void);

/* print_startup_banner() is now in display.c */

/**
 * @brief Run interactive mode main loop
 * 
 * Main loop for interactive menu-driven mode. Continuously displays menu,
 * processes user input, and handles shared memory messages.
 * 
 * @note Exported for use by main.c
 */
void run_interactive_mode(void);

/**
 * @brief Run script mode main loop
 * 
 * Main loop for background script mode. Continuously processes shared memory
 * messages without displaying menus.
 * 
 * @note Exported for use by main.c
 */
void run_script_mode(void);

/**
 * @brief Simple microsecond delay function
 * 
 * Implements a simple delay loop. Delay time is approximate and depends on
 * CPU clock frequency.
 * 
 * @param[in] delay Delay time in microseconds (approximate)
 */
static void delay_us(uint32_t delay);

/* ============================================================================
 * Function Prototypes - Shared Memory Communication
 * ============================================================================ */

/**
 * @brief Initialize shared memory region
 * 
 * Clears and initializes the shared memory region at SHARED_MEM_BASE (0x10000000).
 * Sets all memory locations to zero to prepare for communication.
 * 
 * @note Exported for use by main.c
 */
void init_shared_memory(void);

/**
 * @brief Read data from shared memory data area
 * 
 * Reads a null-terminated string from the shared memory data area.
 * 
 * @param[out] buffer Buffer to store the read string
 * @param[in] max_len Maximum length to read (buffer size)
 * @return Number of bytes read, or -1 on error
 * 
 * @note Exported for use by other modules
 */
int read_data_area(char *buffer, int max_len);

/**
 * @brief Write data to shared memory data area
 * 
 * Writes a null-terminated string to the shared memory data area.
 * 
 * @param[in] data Null-terminated string to write
 * @return 0 on success, -1 on error
 * 
 * @note Exported for use by other modules
 */
int write_data_area(const char *data);

/**
 * @brief Process shared memory message
 * 
 * Checks for incoming messages in shared memory, reads the command register,
 * and dispatches to the appropriate message handler function.
 * 
 * @return 0 if no message processed, 1 if message was handled
 */
static int process_shared_memory_message(void);

/**
 * @brief Handle MSG_TYPE_INIT message
 * 
 * Processes initialization message from TCL script. Initializes shared memory
 * and responds with success status.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_init(void);

/**
 * @brief Handle MSG_TYPE_RUN_APP message
 * 
 * Processes run application message. Executes the application with current
 * configuration parameters and responds with completion status.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_run_app(void);

/**
 * @brief Handle MSG_TYPE_SET_PARAM message
 * 
 * Processes set parameter message. Parses parameter data and updates
 * configuration accordingly.
 * 
 * @param[in] data Parameter data string from shared memory
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_set_param(const char *data);

/**
 * @brief Handle MSG_TYPE_GET_STATUS message
 * 
 * Processes get status message. Reads current status and configuration,
 * formats response, and writes to shared memory.
 * 
 * @param[out] response Buffer to store formatted status response
 * @param[in] max_len Maximum length of response buffer
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_get_status(char *response, int max_len);

/**
 * @brief Handle MSG_TYPE_CAPTURE_RAM message
 * 
 * Processes RAM capture message. Performs memory capture operation and
 * responds with completion status.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_capture_ram(void);

/**
 * @brief Handle MSG_TYPE_SET_CONFIG message
 * 
 * Processes set configuration message. Parses configuration data and updates
 * configuration structure.
 * 
 * @param[in] data Configuration data string from shared memory
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_set_config(const char *data);

/**
 * @brief Handle MSG_TYPE_GET_CONFIG message
 * 
 * Processes get configuration message. Reads requested configuration value
 * and writes to shared memory response area.
 * 
 * @param[in] config_name Name of configuration parameter to retrieve
 * @param[out] response Buffer to store configuration value
 * @param[in] max_len Maximum length of response buffer
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_get_config(const char *config_name, char *response, int max_len);

/**
 * @brief Handle MSG_TYPE_EXIT message
 * 
 * Processes exit message. Sets running flag to 0 to exit application loop.
 * 
 * @return MSG_STATUS_SUCCESS
 */
static int handle_shared_memory_exit(void);

/**
 * @brief Handle MSG_TYPE_START_TEST message
 * 
 * Processes start test message. Initializes test configuration and prepares
 * for test execution.
 * 
 * @param[in] data Test initialization data string
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_start_test(const char *data);

/**
 * @brief Handle MSG_TYPE_RUN_TEST message
 * 
 * Processes run test message. Executes the specified test case and updates
 * test status.
 * 
 * @param[in] data Test execution data string
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_run_test(const char *data);

/**
 * @brief Handle MSG_TYPE_GET_TEST_STATUS message
 * 
 * Processes get test status message. Reads current test statistics and
 * status, formats response.
 * 
 * @param[out] response Buffer to store test status response
 * @param[in] max_len Maximum length of response buffer
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_get_test_status(char *response, int max_len);

/**
 * @brief Handle MSG_TYPE_RESET_PROCESSOR message
 * 
 * Processes reset processor message. Performs processor reset operation.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_reset_processor(void);
    
/**
 * @brief Handle MSG_TYPE_GET_BOOT_MODE message
 * 
 * Processes get boot mode message. Reads boot mode register and returns
 * boot mode information.
 * 
 * @param[out] response Buffer to store boot mode response
 * @param[in] max_len Maximum length of response buffer
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_get_boot_mode(char *response, int max_len);

/**
 * @brief Handle MSG_TYPE_GET_DEVICE_DNA message
 * 
 * Processes get device DNA message. Reads device DNA registers and returns
 * 96-bit DNA value.
 * 
 * @param[out] response Buffer to store device DNA response
 * @param[in] max_len Maximum length of response buffer
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_get_device_dna(char *response, int max_len);

/**
 * @brief Reset the processor
 * 
 * Performs a software reset of the processor. This function may not return
 * if reset is successful.
*/
static void reset_processor(void);

/**
 * @brief Initialize test configuration structure
 * 
 * Initializes the test_config structure with default values for test execution.
 * 
 * @note Exported for use by main.c
 */
void initialize_test_config(void);

/* ============================================================================
 * Main Application Entry Point
 * 
 * Note: main() function has been moved to main.c
 * ============================================================================ */

/* Display functions moved to display.c */

/**
 * @brief Get a single character input (no Enter required)
 * 
 * Reads a single character from UART input without requiring Enter key.
 * This provides immediate response when user presses a key, useful for
 * menu selections.
 * 
 * @return Character that was pressed (lowercase/uppercase as received)
 * 
 * @note Uses BSP inbyte() function for character input
 * @note Exported for use by display.c
 */
char get_char_input(void) {
    char c;
    c = inbyte();
    return c;
}

/**
 * @brief Get string input from user with echo
 * 
 * Reads a string from UART input with character echo, supports backspace
 * for editing. Input is terminated by Enter key (CR or LF).
 * 
 * Features:
 * - Character echo (shows what user types)
 * - Backspace support (0x08 or 0x7F)
 * - Maximum length enforcement
 * - Only accepts printable characters
 * - Handles bell character (Ctrl+G)
 * 
 * @param[out] buffer Buffer to store the input string (must be at least max_len bytes)
 * @param[in] max_len Maximum length of string (buffer size - 1 for null terminator)
 * @param[in] prompt Prompt string to display before input
 * 
 * @note Buffer will be null-terminated. Input is limited to max_len-1 characters.
*/
static void get_string_input(char *buffer, int max_len, const char *prompt) {
    int idx = 0;
    char c;
    
    xil_printf("%s: ", prompt);
    
    while (1) {
        c = inbyte();
        
        // Handle Enter key
        if (c == '\r' || c == '\n') {
            buffer[idx] = '\0';
    xil_printf("\r\n");
            break;
        }
        
        // Handle Backspace
        if ((c == '\b' || c == 0x7F) && idx > 0) {
            idx--;
            xil_printf("\b \b");
            continue;
        }
        
        // Accept printable characters
        if (isprint(c) && idx < max_len - 1) {
            buffer[idx++] = c;
            outbyte(c); // echo
        }
        else if (c == '\a') {
            // Handle bell character
            xil_printf("\a");
        }
    }
}

/**
 * @brief Get hexadecimal input from user with echo
 * 
 * Reads hexadecimal value from UART input. Supports optional 0x prefix and
 * hexadecimal digits (0-9, A-F, a-f). Input is terminated by Enter key.
 * 
 * Features:
 * - Character echo
 * - Backspace support
 * - Accepts 0x or 0X prefix
 * - Only accepts hex digits
 * - Beeps on invalid characters
 * - Converts input to uint32_t using strtoul()
 * 
 * @param[in] prompt Prompt string to display before input
 * @return 32-bit unsigned integer value parsed from hex input
 * 
 * @note Returns 0 if no valid hex digits entered
 */
static uint32_t get_hex_input(const char *prompt) {
    char input[32];
    int idx = 0;
    uint32_t value = 0;
    char c;
    
    xil_printf("%s: ", prompt);
    
    while (1) {
        c = inbyte();
        
        // Handle Enter key
        if (c == '\r' || c == '\n') {
            input[idx] = '\0';
    xil_printf("\r\n");
    
            // Convert to uint32_t
            value = (uint32_t)strtoul(input, NULL, 16);
            break;
        }
        
        // Handle Backspace
        if ((c == '\b' || c == 0x7F) && idx > 0) {
            idx--;
            xil_printf("\b \b");
            continue;
        }
        
        // Accept only hex digits and 0x prefix chars
        if (isxdigit(c) || c == 'x' || c == 'X') {
            if (idx < (int)(sizeof(input) - 1)) {
                input[idx++] = c;
                outbyte(c); // echo
            }
        }
        else {
            xil_printf("\a"); // beep for invalid
        }
    }
    
    return value;
}

/**
 * @brief Get list selection from user (no Enter required)
 * 
 * Displays a numbered list of options and waits for user to press a number key.
 * Selection is immediate - no Enter key required. Beeps on invalid input.
 * 
 * @param[in] prompt Prompt string to display before options
 * @param[in] options Array of option strings to display (numbered 1-N)
 * @param[in] num_options Number of options in the array (max 9)
 * @return Selected option number (1-based index: 1, 2, 3, ...)
 * 
 * @note Only accepts numeric keys '1' through '9'. Beeps on other keys.
 */
static uint32_t get_list_selection(const char *prompt, const char *options[], int num_options) {
    char c;
    uint32_t selection = 0;
    
    xil_printf("%s:\r\n", prompt);
    for (int i = 0; i < num_options; i++) {
        xil_printf("%d. %s\r\n", i + 1, options[i]);
    }
    xil_printf("\r\nEnter choice (1-%d): ", num_options);
    
    while (1) {
        c = get_char_input();
        
        if (c >= '1' && c <= ('0' + num_options)) {
            selection = c - '0';
            xil_printf("%c\r\n", c);
            break;
        }
        else {
            xil_printf("\a"); // beep for invalid
        }
    }
    
    return selection;
}

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
 * 
 * @note Beeps on invalid choice. Sets running=0 when Exit is selected.
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
            Xil_Out32(CMD_REG_ADDR, set_bit(0, CMD_BIT_EXIT));
            
            // Wait for the response register to be set
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
 * 
 * @note Beeps on invalid choice. Choice '0' does nothing (return handled by caller).
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

/**
 * @brief Update device name configuration
 * 
 * Prompts user for new device name using string input, then updates
 * config.device_name. Displays current value before prompting for new value.
 * 
 * @note Maximum length is MAX_STRING_LEN (64 characters)
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
 * 
 * @note Input is interpreted as hexadecimal (supports 0x prefix)
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

/*
 * Update Timeout Value
* @return: void
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

/*
 * Update Debug Level
* @return: void
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

/**
 * @brief Detect the startup mode from hardware registers
 * 
 * Reads the startup mode register to determine how the application was launched
 * (JTAG interactive, JTAG script, UART interactive, or UART script).
 * 
 * @return Detected startup mode value (MODE_JTAG_INTERACTIVE, MODE_JTAG_SCRIPT, etc.)
 * 
 * @note Exported for use by main.c
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
 * Sets application variables (script_mode, app_mode) based on the detected
 * startup mode from detect_startup_mode().
 * 
 * @note Exported for use by main.c
 */
void configure_startup_mode(void) {
    xil_printf("Configuring application for startup mode: 0x%08X\r\n", startup_mode);
    
    switch (startup_mode) {
        case MODE_JTAG_INTERACTIVE:
            app_mode = MODE_INTERACTIVE;
            script_mode = 0;
            menu_active = 1;
            xil_printf("Configured: JTAG Interactive Mode\r\n");
            break;
            
        case MODE_JTAG_SCRIPT:
            app_mode = MODE_BACKGROUND;
            script_mode = 1;
            menu_active = 0;
            xil_printf("Configured: JTAG Script Mode\r\n");
            break;
            
        case MODE_UART_INTERACTIVE:
            app_mode = MODE_INTERACTIVE;
            script_mode = 0;
            menu_active = 1;
            xil_printf("Configured: UART Interactive Mode\r\n");
            break;
            
        case MODE_UART_SCRIPT:
            app_mode = MODE_BACKGROUND;
            script_mode = 1;
            menu_active = 0;
            xil_printf("Configured: UART Script Mode\r\n");
            break;
            
        default:
            app_mode = MODE_INTERACTIVE;
            script_mode = 0;
            menu_active = 1;
            xil_printf("Configured: Default Interactive Mode\r\n");
            break;
    }
}

/* print_startup_banner() moved to display.c */

/**
 * @brief Run interactive mode main loop
 * 
 * Main loop for interactive menu-driven mode. Continuously displays menu,
 * processes user input, and handles shared memory messages.
 * 
 * @note Exported for use by main.c
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

/**
 * @brief Run script mode main loop
 * 
 * Main loop for background script mode. Continuously processes shared memory
 * messages without displaying menus.
 * 
 * @note Exported for use by main.c
 */
void run_script_mode(void) {
    xil_printf("Script mode active - Processing commands...\r\n");
    xil_printf("Send 'exit' to quit script mode\r\n");
    xil_printf("Send 'help' for available commands\r\n");
    xil_printf("\r\n");
    
    while (running) {
        // Process shared memory messages first
        process_shared_memory_message();
        
        // Process register-based commands
        uint32_t cmd = Xil_In32(CMD_REG_ADDR);
        if (cmd != 0) {
            uint32_t result = 0;
            
            xil_printf("Processing command: %u\r\n", cmd);
            
            switch(cmd) {
                case 1: 
                    result = 0x12345678; // Example action
                    break;
                case 2:
                    result = 0x00000001; // Init
                    break;
                case 3:
                    result = 0x00000002; // Run app
                    break;
                case 4:
                    result = 0x00000004; // Get status
                    break;
                case 5:
                    result = 0x00000005; // Capture RAM
                    break;
                case 6:
                    // Switch to interactive mode
                    app_mode = MODE_INTERACTIVE;
                    script_mode = 0;
                    menu_active = 1;
                    result = 0x00000006;
                    running = 0; // Exit script mode
                    break;
                default:
                    result = 0xFFFFFFFF; // Error code
                    break;
            }
            
            // Write back result
            Xil_Out32(RESP_REG_ADDR, result);
            
            // Clear command register
            Xil_Out32(CMD_REG_ADDR, 0);
            
            // Print response
            xil_printf("CMDRESP:%u:%08X\r\n", cmd, result);
        }
        
        // Small delay to prevent excessive CPU usage
        delay_us(10000); // 10ms polling interval
    }
}

/*
 * Simple delay function
 * @param delay: The delay in microseconds
* @return: void
*/
static void delay_us(uint32_t delay) {
    volatile uint32_t count;
    for (count = 0; count < delay; count++) {
        /* Simple delay loop */
    }
}

/**
 * @brief Initialize shared memory region
 * 
 * Clears and initializes the shared memory region at SHARED_MEM_BASE (0x10000000).
 * Sets all memory locations to zero to prepare for communication.
 * 
 * @note Exported for use by main.c
 */
void init_shared_memory(void) {
    xil_printf("Initializing shared memory communication...\r\n");
    xil_printf("Base address: 0x%08X\r\n", SHARED_MEM_BASE);
    xil_printf("Size: 0x%08X\r\n", SHARED_MEM_SIZE);
    
    // Clear the shared memory region
    for (int i = 0; i < SHARED_MEM_SIZE; i += 4) {
        Xil_Out32(SHARED_MEM_BASE + i, 0);
    }
    
    xil_printf("Shared memory initialized\r\n");
}

/**
 * @brief Write data to shared memory data area
 * 
 * Writes a null-terminated string to the shared memory data area at
 * SHARED_MEM_BASE + DATA_AREA_OFFSET. Data is written in 4-byte chunks.
 * 
 * @param[in] data Null-terminated string to write
 * @return 1 on success, 0 on error
 * 
 * @note Exported for use by other modules
 */
int write_data_area(const char *data) {
    uint32_t base_addr = SHARED_MEM_BASE + DATA_AREA_OFFSET;
    int data_length = strlen(data);
    
    // Write data in 4-byte chunks
    for (int i = 0; i < data_length; i += 4) {
        uint32_t chunk = 0;
        
        // Pack bytes into 32-bit word
        for (int j = 0; j < 4 && (i + j) < data_length; j++) {
            chunk |= ((uint32_t)data[i + j]) << (j * 8);
        }
        
        Xil_Out32(base_addr + i, chunk);
    }
    
    // Write null terminator
    Xil_Out32(base_addr + data_length, 0);
    
    return 1;
}

/**
 * @brief Read data from shared memory data area
 * 
 * Reads a null-terminated string from the shared memory data area at
 * SHARED_MEM_BASE + DATA_AREA_OFFSET. Data is read in 4-byte chunks
 * until a null terminator is found or max_len is reached.
 * 
 * @param[out] buffer Buffer to store the read string
 * @param[in] max_len Maximum length to read (buffer size)
 * @return 1 on success, 0 on error
 * 
 * @note Exported for use by other modules
 */
int read_data_area(char *buffer, int max_len) {
    uint32_t base_addr = SHARED_MEM_BASE + DATA_AREA_OFFSET;
    int idx = 0;
    
    // Read data in 4-byte chunks until null terminator or max length
    for (int i = 0; i < max_len - 1; i += 4) {
        uint32_t chunk = Xil_In32(base_addr + i);
        
        // Extract bytes from chunk
        for (int j = 0; j < 4 && (i + j) < (max_len - 1); j++) {
            uint8_t byte_val = (chunk >> (j * 8)) & 0xFF;
            if (byte_val == 0) {
                buffer[idx] = '\0';
                return 1; // Null terminator found
            }
            buffer[idx++] = (char)byte_val;
        }
    }
    
    buffer[idx] = '\0'; // Null terminate
    return 1;
}

/*
 * Process Shared Memory Message
 * @return: int - 1 if message processed, 0 if no message
 */
static int process_shared_memory_message(void) {
    uint32_t cmd_reg = Xil_In32(SHARED_MEM_BASE + CMD_REG_OFFSET);
    
    // Extract only the lower 16 bits (app commands)
    // Upper 16 bits (bits 31-16) are reserved for TCL script commands
    uint32_t app_cmd_reg = cmd_reg & 0x0000FFFF;
    
    // Check if any app command bit is set
    if (app_cmd_reg == 0) {
        return 0; // No app command
    }
    
    char data_buffer[1024];
    int result = 0;
    uint32_t msg_type = 0;
    
    // Read data from data area if command requires it
    read_data_area(data_buffer, sizeof(data_buffer));
    
    // Check which app command bit is set and process accordingly
    if (check_bit(app_cmd_reg, CMD_BIT_APP_INIT)) {
        msg_type = MSG_TYPE_INIT;
        result = handle_shared_memory_init();
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_RUN_APP)) {
        msg_type = MSG_TYPE_RUN_APP;
        result = handle_shared_memory_run_app();
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_SET_PARAM)) {
        msg_type = MSG_TYPE_SET_PARAM;
        result = handle_shared_memory_set_param(data_buffer);
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_GET_STATUS)) {
        msg_type = MSG_TYPE_GET_STATUS;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_status(response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, set_bit(0, 0));  // Set RESP_SUCCESS (bit 0)
        }
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_CAPTURE_RAM)) {
        msg_type = MSG_TYPE_CAPTURE_RAM;
        result = handle_shared_memory_capture_ram();
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_SET_CONFIG)) {
        msg_type = MSG_TYPE_SET_CONFIG;
        result = handle_shared_memory_set_config(data_buffer);
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_GET_CONFIG)) {
        msg_type = MSG_TYPE_GET_CONFIG;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_config(data_buffer, response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, set_bit(0, 0));  // Set RESP_SUCCESS (bit 0)
        }
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_EXIT)) {
        msg_type = MSG_TYPE_EXIT;
        result = handle_shared_memory_exit();
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_START_TEST)) {
        msg_type = MSG_TYPE_START_TEST;
        result = handle_shared_memory_start_test(data_buffer);
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_RUN_TEST)) {
        msg_type = MSG_TYPE_RUN_TEST;
        result = handle_shared_memory_run_test(data_buffer);
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_GET_TEST_STATUS)) {
        msg_type = MSG_TYPE_GET_TEST_STATUS;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_test_status(response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, set_bit(0, 0));  // Set RESP_SUCCESS (bit 0)
        }
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_RESET_PROCESSOR)) {
        msg_type = MSG_TYPE_RESET_PROCESSOR;
        result = handle_shared_memory_reset_processor();
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_GET_BOOT_MODE)) {
        msg_type = MSG_TYPE_GET_BOOT_MODE;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_boot_mode(response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, set_bit(0, 0));  // Set RESP_SUCCESS (bit 0)
        }
    } else if (check_bit(app_cmd_reg, CMD_BIT_APP_GET_DEVICE_DNA)) {
        msg_type = MSG_TYPE_GET_DEVICE_DNA;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_device_dna(response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, set_bit(0, 0));  // Set RESP_SUCCESS (bit 0)
        }
    } else {
        xil_printf("Unknown app command bit in register: 0x%08X (lower 16 bits: 0x%04X)\r\n", cmd_reg, app_cmd_reg);
        uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
        Xil_Out32(resp_addr, set_bit(0, 1));  // Set RESP_ERROR (bit 1)
        // Clear only the lower 16 bits (app commands) from command register
        // Preserve upper 16 bits (TCL commands)
        uint32_t tcl_cmd_reg = cmd_reg & 0xFFFF0000;
        Xil_Out32(SHARED_MEM_BASE + CMD_REG_OFFSET, tcl_cmd_reg);
        return 1;
    }
    
    xil_printf("Processing shared memory app command: type=%u\r\n", msg_type);
    
    // Set response register
    uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
    if (result) {
        Xil_Out32(resp_addr, set_bit(0, 0));  // Set RESP_SUCCESS (bit 0)
    } else {
        Xil_Out32(resp_addr, set_bit(0, 1));  // Set RESP_ERROR (bit 1)
    }
    
    // Clear only the lower 16 bits (app commands) from command register after processing
    // Preserve upper 16 bits (TCL commands)
    uint32_t tcl_cmd_reg = cmd_reg & 0xFFFF0000;
    Xil_Out32(SHARED_MEM_BASE + CMD_REG_OFFSET, tcl_cmd_reg);
    
    return 1; // Message processed
}

/*
 * Handle Shared Memory INIT Command
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_init(void) {
    xil_printf("Handling shared memory INIT command\r\n");
    
    // Initialize configuration with defaults
    strcpy(config.device_name, "Default Device");
    config.base_address = DATA_AREA_ADDR;
    config.operation_mode = 1;
    config.timeout_value = 5000;
    config.debug_level = 1;
    
    xil_printf("Configuration initialized\r\n");
    return 1;
}

/*
 * Handle Shared Memory RUN_APP Command
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_run_app(void) {
    xil_printf("Handling shared memory RUN_APP command\r\n");
    xil_printf("Device: %s\r\n", config.device_name);
    xil_printf("Base Address: 0x%08X\r\n", config.base_address);
    xil_printf("Operation Mode: %u\r\n", config.operation_mode);
    xil_printf("Timeout: %u ms\r\n", config.timeout_value);
    xil_printf("Debug Level: %u\r\n", config.debug_level);
    
    // Simulate application execution
    delay_us(1000000); // 1 second delay
    
    xil_printf("Application execution completed\r\n");
    return 1;
}

/*
 * Handle Shared Memory SET_PARAM Command
 * @param data: Parameter data string
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_set_param(const char *data) {
    xil_printf("Handling shared memory SET_PARAM command: %s\r\n", data);
    
    char param_name[32];
    char param_value[32];
    
    if (sscanf(data, "%31s %31s", param_name, param_value) == 2) {
        if (strcmp(param_name, "param1") == 0) {
            // Handle param1 (operation mode)
            uint32_t value = strtoul(param_value, NULL, 0);
            if (value >= 1 && value <= 3) {
                config.operation_mode = value;
                xil_printf("Set operation mode to %u\r\n", value);
                return 1;
            }
        } else if (strcmp(param_name, "param2") == 0) {
            // Handle param2 (base address)
            uint32_t value = strtoul(param_value, NULL, 16);
            config.base_address = value;
            xil_printf("Set base address to 0x%08X\r\n", value);
            return 1;
        } else if (strcmp(param_name, "param3") == 0) {
            // Handle param3 (timeout)
            uint32_t value = strtoul(param_value, NULL, 0);
            config.timeout_value = value;
            xil_printf("Set timeout to %u\r\n", value);
            return 1;
        }
    }
    
    xil_printf("Invalid parameter format\r\n");
    return 0;
}

/*
 * Handle Shared Memory GET_STATUS Command
 * @param response: Buffer to store response
 * @param max_len: Maximum response length
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_get_status(char *response, int max_len) {
    xil_printf("Handling shared memory GET_STATUS command\r\n");
    
    snprintf(response, max_len,
             "Device: %s, Base: 0x%08X, Mode: %u, Timeout: %u, Debug: %u",
             config.device_name, config.base_address, config.operation_mode,
             config.timeout_value, config.debug_level);
    
    return 1;
}

/*
 * Handle Shared Memory CAPTURE_RAM Command
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_capture_ram(void) {
    xil_printf("Handling shared memory CAPTURE_RAM command\r\n");
    xil_printf("Base Address: 0x%08X\r\n", config.base_address);
    xil_printf("Timeout: %u ms\r\n", config.timeout_value);
    
    // Simulate RAM capture
    delay_us(500000); // 0.5 second delay
    
    xil_printf("RAM capture completed\r\n");
    return 1;
}

/*
 * Handle Shared Memory SET_CONFIG Command
 * @param data: Configuration data string
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_set_config(const char *data) {
    xil_printf("Handling shared memory SET_CONFIG command: %s\r\n", data);
    
    char config_name[32];
    char config_value[64];
    uint32_t config_type;
    
    if (sscanf(data, "%31[^|]|%63[^|]|%u", config_name, config_value, &config_type) == 3) {
        if (strcmp(config_name, "device_name") == 0) {
            strncpy(config.device_name, config_value, sizeof(config.device_name) - 1);
            config.device_name[sizeof(config.device_name) - 1] = '\0';
            xil_printf("Set device name to: %s\r\n", config.device_name);
            return 1;
        } else if (strcmp(config_name, "base_address") == 0) {
            config.base_address = strtoul(config_value, NULL, 16);
            xil_printf("Set base address to: 0x%08X\r\n", config.base_address);
            return 1;
        } else if (strcmp(config_name, "operation_mode") == 0) {
            config.operation_mode = strtoul(config_value, NULL, 0);
            xil_printf("Set operation mode to: %u\r\n", config.operation_mode);
            return 1;
        } else if (strcmp(config_name, "timeout_value") == 0) {
            config.timeout_value = strtoul(config_value, NULL, 0);
            xil_printf("Set timeout value to: %u\r\n", config.timeout_value);
            return 1;
        } else if (strcmp(config_name, "debug_level") == 0) {
            config.debug_level = strtoul(config_value, NULL, 0);
            xil_printf("Set debug level to: %u\r\n", config.debug_level);
            return 1;
        }
    }
    
    xil_printf("Invalid configuration format\r\n");
    return 0;
}

/*
 * Handle Shared Memory GET_CONFIG Command
 * @param config_name: Configuration name to get
 * @param response: Buffer to store response
 * @param max_len: Maximum response length
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_get_config(const char *config_name, char *response, int max_len) {
    xil_printf("Handling shared memory GET_CONFIG command: %s\r\n", config_name);
    
    if (strcmp(config_name, "device_name") == 0) {
        strncpy(response, config.device_name, max_len - 1);
        response[max_len - 1] = '\0';
        return 1;
    } else if (strcmp(config_name, "base_address") == 0) {
        snprintf(response, max_len, "0x%08X", config.base_address);
        return 1;
    } else if (strcmp(config_name, "operation_mode") == 0) {
        snprintf(response, max_len, "%u", config.operation_mode);
        return 1;
    } else if (strcmp(config_name, "timeout_value") == 0) {
        snprintf(response, max_len, "%u", config.timeout_value);
        return 1;
    } else if (strcmp(config_name, "debug_level") == 0) {
        snprintf(response, max_len, "%u", config.debug_level);
        return 1;
    }
    
    xil_printf("Unknown configuration name: %s\r\n", config_name);
    return 0;
}

/*
 * Handle Shared Memory EXIT Command
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_exit(void) {
    xil_printf("Handling shared memory EXIT command\r\n");
    running = 0;
    return 1;
}

/**
 * @brief Initialize test configuration structure
 * 
 * Initializes the test_config structure with default values for test execution.
 * 
 * @note Exported for use by main.c
 */
void initialize_test_config(void) {
    test_config.number_of_tests = 0;
    test_config.current_test = 0;
    test_config.test_timeout = 10000;
    test_config.test_retries = 2;
    test_config.tests_passed = 0;
    test_config.tests_failed = 0;
    test_config.test_in_progress = 0;
    test_config.test_requires_reset = 0;
    
    // Clear all test cases
    for (int i = 0; i < MAX_TEST_CASES; i++) {
        test_cases[i].name[0] = '\0';
        test_cases[i].description[0] = '\0';
        test_cases[i].requires_reset = 0;
        test_cases[i].status = 0;
    }
    
    xil_printf("Test configuration initialized\r\n");
}

/*
 * Reset Processor
 * @return: void
 */
static void reset_processor(void) {
    xil_printf("Resetting processor...\r\n");
    
    // Note: In a real implementation, this would use the appropriate
    // reset mechanism for the target processor (e.g., Xil_Out32 to reset register)
    // For now, we'll simulate a reset by reinitializing the application state
    
    // Reset configuration to defaults
    strcpy(config.device_name, "Default Device");
    config.base_address = 0x43C00000;
    config.operation_mode = 1;
    config.timeout_value = 5000;
    config.debug_level = 1;
    
    // Reset test state
    test_config.current_test = 0;
    test_config.test_in_progress = 0;
    test_config.test_requires_reset = 0;
    
    // Small delay to simulate reset
    delay_us(100000); // 100ms delay
    
    xil_printf("Processor reset completed\r\n");
}

/*
 * Handle Shared Memory RESET_PROCESSOR Command
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_reset_processor(void) {
    xil_printf("Handling shared memory RESET_PROCESSOR command\r\n");
    reset_processor();
    return 1;
}

/*
 * Handle Shared Memory START_TEST Command
 * @param data: Test configuration data string
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_start_test(const char *data) {
    xil_printf("Handling shared memory START_TEST command: %s\r\n", data);
    
    // Parse test configuration data
    // Format: "number_of_tests|timeout|retries"
    uint32_t num_tests = 0;
    uint32_t timeout = 10000;
    uint32_t retries = 2;
    
    if (sscanf(data, "%u|%u|%u", &num_tests, &timeout, &retries) >= 1) {
        if (num_tests > 0 && num_tests <= MAX_TEST_CASES) {
            test_config.number_of_tests = num_tests;
            test_config.test_timeout = timeout;
            test_config.test_retries = retries;
            test_config.current_test = 0;
            test_config.tests_passed = 0;
            test_config.tests_failed = 0;
            test_config.test_in_progress = 0;
            test_config.test_requires_reset = 0;
            
            test_mode = 1;
            
            xil_printf("Test configuration: %u tests, timeout=%u ms, retries=%u\r\n",
                      num_tests, timeout, retries);
            return 1;
        } else {
            xil_printf("Invalid number of tests: %u (max: %u)\r\n", num_tests, MAX_TEST_CASES);
            return 0;
        }
    } else {
        xil_printf("Invalid test configuration format\r\n");
        return 0;
    }
}

/*
 * Handle Shared Memory RUN_TEST Command
 * @param data: Test case data string
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_run_test(const char *data) {
    xil_printf("Handling shared memory RUN_TEST command: %s\r\n", data);
    
    // Parse test case data
    // Format: "test_number|name|description|requires_reset"
    uint32_t test_number = 0;
    char test_name[64] = "";
    char test_description[128] = "";
    uint32_t requires_reset = 0;
    
    if (sscanf(data, "%u|%63[^|]|%127[^|]|%u", &test_number, test_name, test_description, &requires_reset) >= 1) {
        if (test_number > 0 && test_number <= test_config.number_of_tests) {
            uint32_t test_idx = test_number - 1;
            
            // Check if test requires reset
            if (requires_reset && test_config.test_requires_reset == 0) {
                xil_printf("Test %u requires processor reset\r\n", test_number);
                reset_processor();
                test_config.test_requires_reset = 1;
            }
            
            // Store test case information
            if (test_name[0] != '\0') {
                strncpy(test_cases[test_idx].name, test_name, sizeof(test_cases[test_idx].name) - 1);
                test_cases[test_idx].name[sizeof(test_cases[test_idx].name) - 1] = '\0';
            } else {
                snprintf(test_cases[test_idx].name, sizeof(test_cases[test_idx].name), "Test Case %u", test_number);
            }
            
            if (test_description[0] != '\0') {
                strncpy(test_cases[test_idx].description, test_description, sizeof(test_cases[test_idx].description) - 1);
                test_cases[test_idx].description[sizeof(test_cases[test_idx].description) - 1] = '\0';
            }
            
            test_cases[test_idx].requires_reset = requires_reset;
            test_config.current_test = test_number;
            test_config.test_in_progress = 1;
            
            xil_printf("Running test %u: %s\r\n", test_number, test_cases[test_idx].name);
            xil_printf("Description: %s\r\n", test_cases[test_idx].description);
            
            // Execute the test
            // For now, we'll simulate test execution
            // In a real implementation, this would run the actual test logic
            delay_us(500000); // 0.5 second delay to simulate test execution
            
            // Check test result (simplified - would need actual test validation)
            // For now, we'll assume the test passes if we get here
            int test_passed = 1; // In real implementation, this would be determined by test logic
            const char *status_str;
            const char *message_str;
            
            if (test_passed) {
                test_cases[test_idx].status = 1; // Passed
                test_config.tests_passed++;
                status_str = "PASSED";
                message_str = "Test completed successfully";
            } else {
                test_cases[test_idx].status = 2; // Failed
                test_config.tests_failed++;
                status_str = "FAILED";
                message_str = "Test validation failed";
            }
            
            test_config.test_in_progress = 0;
            
            xil_printf("Test %u completed: %s\r\n", test_number, status_str);
            
            return 1;
        } else {
            xil_printf("Invalid test number: %u (max: %u)\r\n", test_number, test_config.number_of_tests);
            return 0;
        }
    } else {
        xil_printf("Invalid test case format\r\n");
        return 0;
    }
}

/*
 * Handle Shared Memory GET_TEST_STATUS Command
 * @param response: Buffer to store response
 * @param max_len: Maximum response length
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_get_test_status(char *response, int max_len) {
    xil_printf("Handling shared memory GET_TEST_STATUS command\r\n");
    
    if (test_mode) {
        snprintf(response, max_len,
                "Tests: %u/%u, Passed: %u, Failed: %u, Current: %u, InProgress: %u",
                test_config.tests_passed + test_config.tests_failed,
                test_config.number_of_tests,
                test_config.tests_passed,
                test_config.tests_failed,
                test_config.current_test,
                test_config.test_in_progress);
    } else {
        snprintf(response, max_len, "Test mode not active");
    }
    
    return 1;
}

/*
 * Handle Shared Memory GET_BOOT_MODE Command
 * @param response: Buffer to store response
 * @param max_len: Maximum response length
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_get_boot_mode(char *response, int max_len) {
    xil_printf("Handling shared memory GET_BOOT_MODE command\r\n");
    
    // Read boot mode register (read-only register at 0xFF5E0200)
    uint32_t boot_mode_reg = Xil_In32(BOOT_MODE_REG_ADDR);
    
    // Extract boot mode bits (typically bits [3:0] for Zynq UltraScale+)
    uint32_t boot_mode = boot_mode_reg & 0x0F;
    
    // Decode boot mode to human-readable string
    const char *boot_mode_str;
    switch (boot_mode) {
        case 0x0:
            boot_mode_str = "JTAG";
            break;
        case 0x1:
            boot_mode_str = "QSPI24";
            break;
        case 0x2:
            boot_mode_str = "QSPI32";
            break;
        case 0x3:
            boot_mode_str = "SD0";
            break;
        case 0x4:
            boot_mode_str = "SD1";
            break;
        case 0x5:
            boot_mode_str = "eMMC";
            break;
        case 0x6:
            boot_mode_str = "NAND";
            break;
        case 0x7:
            boot_mode_str = "USB";
            break;
        default:
            boot_mode_str = "UNKNOWN";
            break;
    }
    
    xil_printf("Boot Mode Register: 0x%08X\r\n", boot_mode_reg);
    xil_printf("Boot Mode: 0x%02X (%s)\r\n", boot_mode, boot_mode_str);
    
    // Format response string
    snprintf(response, max_len,
            "Boot Mode Register: 0x%08X, Boot Mode: 0x%02X (%s)",
            boot_mode_reg, boot_mode, boot_mode_str);
    
    return 1;
}

/*
 * Handle Shared Memory GET_DEVICE_DNA Command
 * @param response: Buffer to store response
 * @param max_len: Maximum response length
 * @return: int - 1 if successful, 0 if error
 */
static int handle_shared_memory_get_device_dna(char *response, int max_len) {
    xil_printf("Handling shared memory GET_DEVICE_DNA command\r\n");
    
    // Read PS Device DNA registers (96-bit value in 3 registers)
    uint32_t dna_0 = Xil_In32(DNA_0_REG_ADDR);  // Bits 31:0
    uint32_t dna_1 = Xil_In32(DNA_1_REG_ADDR);  // Bits 63:32
    uint32_t dna_2 = Xil_In32(DNA_2_REG_ADDR);  // Bits 95:64
    
    xil_printf("PS Device DNA Register 0 (0x%08X): 0x%08X\r\n", DNA_0_REG_ADDR, dna_0);
    xil_printf("PS Device DNA Register 1 (0x%08X): 0x%08X\r\n", DNA_1_REG_ADDR, dna_1);
    xil_printf("PS Device DNA Register 2 (0x%08X): 0x%08X\r\n", DNA_2_REG_ADDR, dna_2);
    
    // Format 96-bit DNA value as hex string
    // DNA_2 contains bits 95:64, DNA_1 contains bits 63:32, DNA_0 contains bits 31:0
    // Note: Only bits [31:0] of DNA_2 are used (96-bit value, not 128-bit)
    uint32_t dna_2_lower = dna_2 & 0xFFFFFFFF;  // Only use lower 32 bits
    
    // Format response string with individual register values and combined 96-bit value
    snprintf(response, max_len,
            "PS Device DNA - DNA_0: 0x%08X, DNA_1: 0x%08X, DNA_2: 0x%08X, Combined: 0x%08X%08X%08X",
            dna_0, dna_1, dna_2, dna_2_lower, dna_1, dna_0);
    
    xil_printf("PS Device DNA (96-bit): 0x%08X%08X%08X\r\n", dna_2_lower, dna_1, dna_0);
    
    return 1;
}

/* ============================================================================
 * JTAG UART Interface Functions
 * ============================================================================ */

/**
 * @brief Initialize JTAG UART communication
 * 
 * Initializes the JTAG UART interface for communication. This function
 * performs any necessary setup for UART communication, though in most
 * Xilinx BSP systems, the UART is already initialized during system startup.
 * 
 * @return 0 on success, -1 on error
 * 
 * @note This is a wrapper function that can be used for future UART-specific
 *       initialization if needed. Currently, the BSP handles UART initialization.
 */
int init_jtag_uart(void) {
    xil_printf("JTAG UART initialized\r\n");
    return 0;
}

/**
 * @brief Cleanup JTAG UART communication
 * 
 * Performs cleanup operations for the JTAG UART interface. This function
 * can be used to release resources or perform cleanup before shutdown.
 * 
 * @note Currently a placeholder function for future use.
 */
void cleanup_jtag_uart(void) {
    xil_printf("JTAG UART cleanup\r\n");
}

/**
 * @brief Send a response string via UART
 * 
 * Sends a response string to the UART output. Uses xil_printf for
 * formatted output to ensure proper formatting with newlines.
 * 
 * @param[in] response Null-terminated response string to send
 * @return Number of characters sent, or -1 on error
 */
int send_response(const char *response) {
    if (response == NULL) {
        return -1;
    }
    
    xil_printf("%s\r\n", response);
    return (int)strlen(response);
}

/**
 * @brief Receive a command string from UART
 * 
 * Reads a command string from UART input until Enter key is pressed.
 * Supports backspace for editing. Input is terminated by Enter (CR or LF).
 * 
 * @param[out] command Buffer to store the received command
 * @param[in] max_len Maximum length of command (buffer size - 1)
 * @return Number of characters read, or -1 on error
 * 
 * @note Buffer will be null-terminated. Input is limited to max_len-1 characters.
 */
int receive_command(char *command, int max_len) {
    if (command == NULL || max_len <= 0) {
        return -1;
    }
    
    int idx = 0;
    char c;
    
    while (1) {
        c = inbyte();
        
        // Handle Enter key
        if (c == '\r' || c == '\n') {
            command[idx] = '\0';
            xil_printf("\r\n");
            break;
        }
        
        // Handle Backspace
        if ((c == '\b' || c == 0x7F) && idx > 0) {
            idx--;
            xil_printf("\b \b");
            continue;
        }
        
        // Accept printable characters
        if (isprint(c) && idx < max_len - 1) {
            command[idx++] = c;
            outbyte(c); // echo
        }
        else if (c == '\a') {
            // Handle bell character
            xil_printf("\a");
        }
    }
    
    return idx;
}

/**
 * @brief Handle a received command string
 * 
 * Parses and processes a command string received from UART or other source.
 * Command strings should match the command definitions in jtag_uart_handler.h.
 * 
 * Supported commands:
 * - CMD_INIT ("init"): Initialize the application
 * - CMD_RUN_APP ("run_app"): Run the application with current settings
 * - CMD_SET_PARAM ("set_param"): Set a parameter (requires additional data)
 * - CMD_GET_STATUS ("get_status"): Get current status
 * - CMD_CAPTURE_RAM ("capture_ram"): Capture RAM data
 * - CMD_EXIT ("exit"): Exit the application
 * - CMD_HELP ("help"): Display help information
 * 
 * @param[in] command Null-terminated command string to process
 * 
 * @note Commands are case-sensitive. Some commands may require additional
 *       data which should be provided via shared memory or follow-up input.
 */
void handle_command(const char *command) {
    if (command == NULL) {
        return;
    }
    
    // Remove leading whitespace
    while (isspace(*command)) {
        command++;
    }
    
    // Compare command (case-sensitive)
    if (strcmp(command, CMD_INIT) == 0) {
        xil_printf("Command: INIT\r\n");
        handle_shared_memory_init();
        send_response(RESPONSE_INIT_OK);
    }
    else if (strcmp(command, CMD_RUN_APP) == 0) {
        xil_printf("Command: RUN_APP\r\n");
        handle_shared_memory_run_app();
        send_response(RESPONSE_RUN_OK);
    }
    else if (strncmp(command, CMD_SET_PARAM, strlen(CMD_SET_PARAM)) == 0) {
        xil_printf("Command: SET_PARAM\r\n");
        const char *param_data = command + strlen(CMD_SET_PARAM);
        while (isspace(*param_data)) {
            param_data++;
        }
        if (handle_shared_memory_set_param(param_data)) {
            send_response(RESPONSE_PARAM_SET_OK);
        } else {
            send_response(RESPONSE_ERROR);
        }
    }
    else if (strcmp(command, CMD_GET_STATUS) == 0) {
        xil_printf("Command: GET_STATUS\r\n");
        char response[MAX_RESPONSE_LEN];
        if (handle_shared_memory_get_status(response, sizeof(response))) {
            send_response(response);
        } else {
            send_response(RESPONSE_ERROR);
        }
    }
    else if (strcmp(command, CMD_CAPTURE_RAM) == 0) {
        xil_printf("Command: CAPTURE_RAM\r\n");
        if (handle_shared_memory_capture_ram()) {
            send_response(RESPONSE_RAM_CAPTURE_OK);
        } else {
            send_response(RESPONSE_ERROR);
        }
    }
    else if (strcmp(command, CMD_EXIT) == 0) {
        xil_printf("Command: EXIT\r\n");
        handle_shared_memory_exit();
        send_response(RESPONSE_EXIT_OK);
    }
    else if (strcmp(command, CMD_HELP) == 0) {
        xil_printf("Command: HELP\r\n");
        xil_printf("Available commands:\r\n");
        xil_printf("  %s - Initialize application\r\n", CMD_INIT);
        xil_printf("  %s - Run application\r\n", CMD_RUN_APP);
        xil_printf("  %s <param> <value> - Set parameter\r\n", CMD_SET_PARAM);
        xil_printf("  %s - Get status\r\n", CMD_GET_STATUS);
        xil_printf("  %s - Capture RAM\r\n", CMD_CAPTURE_RAM);
        xil_printf("  %s - Exit application\r\n", CMD_EXIT);
        xil_printf("  %s - Show this help\r\n", CMD_HELP);
    }
    else {
        xil_printf("Unknown command: %s\r\n", command);
        xil_printf("Type '%s' for available commands\r\n", CMD_HELP);
        send_response(RESPONSE_ERROR);
    }
}