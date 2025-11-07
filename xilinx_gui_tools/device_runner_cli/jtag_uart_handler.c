/*
 * JTAG UART Handler for Device Runner CLI - Clean Implementation
 * 
 * This file implements a clean embedded side of the Device Runner CLI communication.
 * It runs on the FPGA PS (Processing System) in baremetal mode and handles 
 * commands sent from the Device Runner CLI via JTAG UART.
 * 
 * Features:
 * - Main menu with options
 * - Configuration submenu with string, hex, and list options
 * - Nice configuration display
 * - Banner display with page clearing
 * - Input echo for string and hex values
 * - Script/JTAG mode detection
 * 
 * Author: Device Runner CLI
 * Version: 2.0.0
 * Date: 2024
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>
#include "xil_printf.h"
#include "xil_io.h"

// UART I/O functions from BSP
char inbyte(void);
void outbyte(char c);

/* Buffer and Command Definitions */
#define BUFFER_SIZE 1024
#define MAX_COMMAND_LEN 256
#define MAX_RESPONSE_LEN 512
#define MAX_STRING_LEN 64

/* Command Register Definitions */
#define CMD_REG_ADDR 0xXXXX0000
#define RESP_REG_ADDR 0xXXXX0004

/* Startup Mode Detection */
#define STARTUP_MODE_REG_ADDR 0xXXXX0008
#define MODE_JTAG_INTERACTIVE 0x00000001
#define MODE_JTAG_SCRIPT     0x00000002
#define MODE_UART_INTERACTIVE 0x00000003
#define MODE_UART_SCRIPT     0x00000004

/* Application Modes */
#define MODE_INTERACTIVE 0
#define MODE_BACKGROUND  1

/* Shared Memory Definitions */
#define SHARED_MEM_BASE 0x10000000
#define SHARED_MEM_SIZE 0x1000

/* Register offsets in shared memory */
#define CMD_REG_OFFSET 0x0      /* Command register (bit field) */
#define RESP_REG_OFFSET 0x4     /* Response register */
#define DATA_AREA_OFFSET 0x8    /* Data area for command parameters */

/* Message types */
#define MSG_TYPE_INIT 1
#define MSG_TYPE_RUN_APP 2
#define MSG_TYPE_SET_PARAM 3
#define MSG_TYPE_GET_STATUS 4
#define MSG_TYPE_CAPTURE_RAM 5
#define MSG_TYPE_SET_CONFIG 6
#define MSG_TYPE_GET_CONFIG 7
#define MSG_TYPE_EXIT 8
#define MSG_TYPE_RESPONSE 9
#define MSG_TYPE_ERROR 10
#define MSG_TYPE_START_TEST 11
#define MSG_TYPE_RUN_TEST 12
#define MSG_TYPE_GET_TEST_STATUS 13
#define MSG_TYPE_RESET_PROCESSOR 14

/* Status codes */
#define MSG_STATUS_SUCCESS 0
#define MSG_STATUS_ERROR 1
#define MSG_STATUS_BUSY 2
#define MSG_STATUS_TIMEOUT 3
#define MSG_STATUS_INVALID 4

/* Response register values */
#define RESP_SUCCESS 0x00000001  /* Success response */
#define RESP_ERROR 0x00000002    /* Error response */
#define RESP_BUSY 0x00000004     /* Busy response */
#define RESP_READY 0x00000008    /* Ready response */

/* Configuration parameter types */
#define CONFIG_TYPE_STRING 1
#define CONFIG_TYPE_HEX 2
#define CONFIG_TYPE_LIST 3

/* Configuration Structure */
typedef struct {
    char device_name[MAX_STRING_LEN];
    uint32_t base_address;
    uint32_t operation_mode;  // 1=Short, 2=Medium, 3=Long
    uint32_t timeout_value;
    uint32_t debug_level;
} config_t;

/* Test Configuration Structure */
typedef struct {
    uint32_t number_of_tests;
    uint32_t current_test;
    uint32_t test_timeout;
    uint32_t test_retries;
    uint32_t tests_passed;
    uint32_t tests_failed;
    uint32_t test_in_progress;
    uint32_t test_requires_reset;
} test_config_t;

/* Test Case Structure */
typedef struct {
    char name[64];
    char description[128];
    uint32_t requires_reset;
    uint32_t status;  // 0=not run, 1=passed, 2=failed
} test_case_t;

#define MAX_TEST_CASES 32

/* Global Variables */
static volatile int running = 1;
static volatile int app_mode = MODE_INTERACTIVE;
static volatile int startup_mode = MODE_JTAG_INTERACTIVE;
static volatile int script_mode = 0;
static volatile int menu_active = 0;
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
static config_t config = {
    .device_name = "Default Device",
    .base_address = 0x43C00000,
    .operation_mode = 1,  // Short
    .timeout_value = 5000,
    .debug_level = 1
};

/* Function Prototypes */
static void clear_screen(void);
static void print_banner(void);
static void show_main_menu(void);
static void show_config_menu(void);
static void display_configuration(void);
static char get_char_input(void);
static void get_string_input(char *buffer, int max_len, const char *prompt);
static uint32_t get_hex_input(const char *prompt);
static uint32_t get_list_selection(const char *prompt, const char *options[], int num_options);
static void handle_main_menu_selection(char choice);
static void handle_config_menu_selection(char choice);
static void update_device_name(void);
static void update_base_address(void);
static void update_operation_mode(void);
static void update_timeout_value(void);
static void update_debug_level(void);
static int detect_startup_mode(void);
static void configure_startup_mode(void);
static void print_startup_banner(void);
static void run_interactive_mode(void);
static void run_script_mode(void);
static void delay_us(uint32_t delay);

/* Shared Memory Function Prototypes */
static void init_shared_memory(void);
static int read_data_area(char *buffer, int max_length);
static int write_data_area(const char *data);
static int process_shared_memory_message(void);
static int handle_shared_memory_init(void);
static int handle_shared_memory_run_app(void);
static int handle_shared_memory_set_param(const char *data);
static int handle_shared_memory_get_status(char *response, int max_len);
static int handle_shared_memory_capture_ram(void);
static int handle_shared_memory_set_config(const char *data);
static int handle_shared_memory_get_config(const char *config_name, char *response, int max_len);
static int handle_shared_memory_exit(void);
static int handle_shared_memory_start_test(const char *data);
static int handle_shared_memory_run_test(const char *data);
static int handle_shared_memory_get_test_status(char *response, int max_len);
static int handle_shared_memory_reset_processor(void);
static void reset_processor(void);
static void initialize_test_config(void);

/*
* Main Application Entry Point
* @return: int
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

/*
 * Clear Screen Function
 * @return: void
 */
static void clear_screen(void) {
    // Send ANSI escape sequence to clear screen
    xil_printf("\033[2J\033[H");
}

/*
 * Print Banner Function
 * @return: void
 */
static void print_banner(void) {
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

/*
 * Show Main Menu
* @return: void
*/
static void show_main_menu(void) {
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

/*
 * Show Configuration Menu
 * @return: void
 */
static void show_config_menu(void) {
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

/*
 * Display Current Configuration
 * @return: void
 */
static void display_configuration(void) {
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

/*
 * Get Single Character Input (No Enter Required)
 * @return: char - The character pressed
 */
static char get_char_input(void) {
    char c;
    c = inbyte();
    return c;
}

/*
 * Get String Input with Echo
 * @param buffer: Buffer to store the string
 * @param max_len: Maximum length of string
 * @param prompt: Prompt to display
* @return: void
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

/*
 * Get Hex Input with Echo
 * @param prompt: Prompt to display
 * @return: uint32_t - The hex value entered
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

/*
 * Get List Selection (No Enter Required)
 * @param prompt: Prompt to display
 * @param options: Array of option strings
 * @param num_options: Number of options
 * @return: uint32_t - The selected option number
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

/*
 * Handle Main Menu Selection
 * @param choice: The menu choice
 * @return: void
 */
static void handle_main_menu_selection(char choice) {
    switch (choice) {
        case '1':
            display_configuration();
            break;
            
        case '2':
            show_config_menu();
            {
                char config_choice = get_char_input();
                handle_config_menu_selection(config_choice);
                    }
                    break;
                    
                case '3':
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
                    
                case '4':
            print_banner();
            xil_printf("=== SYSTEM STATUS ===\r\n");
            xil_printf("Startup Mode: 0x%08X\r\n", startup_mode);
            xil_printf("Script Mode: %s\r\n", script_mode ? "Active" : "Inactive");
            xil_printf("App Mode: %s\r\n", app_mode == MODE_INTERACTIVE ? "Interactive" : "Background");
            xil_printf("Menu Active: %s\r\n", menu_active ? "Yes" : "No");
            xil_printf("\r\nPress any key to continue...");
            get_char_input();
                    break;
                    
        case '5':
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
            
        case '0':
            print_banner();
            xil_printf("=== EXITING ===\r\n");
            xil_printf("Goodbye!\r\n");
            running = 0;
            break;
            
        default:
            xil_printf("\a"); // beep for invalid choice
            break;
    }
}

/*
 * Handle Configuration Menu Selection
 * @param choice: The menu choice
 * @return: void
 */
static void handle_config_menu_selection(char choice) {
    switch (choice) {
                case '1':
            update_device_name();
                    break;
                    
                case '2':
            update_base_address();
                    break;
                    
                case '3':
            update_operation_mode();
                    break;
                    
        case '4':
            update_timeout_value();
                    break;
            
        case '5':
            update_debug_level();
            break;
            
        case '6':
            display_configuration();
            break;
            
        case '0':
            // Back to main menu - handled by caller
            break;
            
        default:
            xil_printf("\a"); // beep for invalid choice
            break;
    }
}

/*
 * Update Device Name
 * @return: void
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

/*
 * Update Base Address
* @return: void
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

/*
 * Update Operation Mode
* @return: void
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

/*
* Detect Startup Mode
* @return: int - Detected startup mode
*/
static int detect_startup_mode(void) {
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

/*
* Configure Application Based on Startup Mode
* @return: void
*/
static void configure_startup_mode(void) {
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

/*
* Print Startup Banner with Mode Information
* @return: void
*/
static void print_startup_banner(void) {
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

/*
 * Run Interactive Mode
* @return: void
*/
static void run_interactive_mode(void) {
    while (running) {
        // Process shared memory messages first
        process_shared_memory_message();
        
        show_main_menu();
        char choice = get_char_input();
        handle_main_menu_selection(choice);
    }
}

/*
 * Run Script Mode
 * @return: void
 */
static void run_script_mode(void) {
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

/*
 * Initialize Shared Memory Communication
 * @return: void
 */
static void init_shared_memory(void) {
    xil_printf("Initializing shared memory communication...\r\n");
    xil_printf("Base address: 0x%08X\r\n", SHARED_MEM_BASE);
    xil_printf("Size: 0x%08X\r\n", SHARED_MEM_SIZE);
    
    // Clear the shared memory region
    for (int i = 0; i < SHARED_MEM_SIZE; i += 4) {
        Xil_Out32(SHARED_MEM_BASE + i, 0);
    }
    
    xil_printf("Shared memory initialized\r\n");
}

/*
 * Write Data Area to Shared Memory
 * @param data: Data string to write
 * @return: int - 1 if successful, 0 if error
 */
static int write_data_area(const char *data) {
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

/*
 * Read Data Area from Shared Memory
 * @param buffer: Buffer to store data
 * @param max_len: Maximum buffer length
 * @return: int - 1 if successful, 0 if error
 */
static int read_data_area(char *buffer, int max_len) {
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
    
    // Check if any command bit is set
    if (cmd_reg == 0) {
        return 0; // No command
    }
    
    char data_buffer[1024];
    int result = 0;
    uint32_t msg_type = 0;
    
    // Read data from data area if command requires it
    read_data_area(data_buffer, sizeof(data_buffer));
    
    // Check which command bit is set and process accordingly
    if (cmd_reg & (1 << 0)) {  // CMD_BIT_INIT
        msg_type = MSG_TYPE_INIT;
        result = handle_shared_memory_init();
    } else if (cmd_reg & (1 << 1)) {  // CMD_BIT_RUN_APP
        msg_type = MSG_TYPE_RUN_APP;
        result = handle_shared_memory_run_app();
    } else if (cmd_reg & (1 << 2)) {  // CMD_BIT_SET_PARAM
        msg_type = MSG_TYPE_SET_PARAM;
        result = handle_shared_memory_set_param(data_buffer);
    } else if (cmd_reg & (1 << 3)) {  // CMD_BIT_GET_STATUS
        msg_type = MSG_TYPE_GET_STATUS;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_status(response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, RESP_SUCCESS);
        }
    } else if (cmd_reg & (1 << 4)) {  // CMD_BIT_CAPTURE_RAM
        msg_type = MSG_TYPE_CAPTURE_RAM;
        result = handle_shared_memory_capture_ram();
    } else if (cmd_reg & (1 << 5)) {  // CMD_BIT_SET_CONFIG
        msg_type = MSG_TYPE_SET_CONFIG;
        result = handle_shared_memory_set_config(data_buffer);
    } else if (cmd_reg & (1 << 6)) {  // CMD_BIT_GET_CONFIG
        msg_type = MSG_TYPE_GET_CONFIG;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_config(data_buffer, response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, RESP_SUCCESS);
        }
    } else if (cmd_reg & (1 << 7)) {  // CMD_BIT_EXIT
        msg_type = MSG_TYPE_EXIT;
        result = handle_shared_memory_exit();
    } else if (cmd_reg & (1 << 8)) {  // CMD_BIT_START_TEST
        msg_type = MSG_TYPE_START_TEST;
        result = handle_shared_memory_start_test(data_buffer);
    } else if (cmd_reg & (1 << 9)) {  // CMD_BIT_RUN_TEST
        msg_type = MSG_TYPE_RUN_TEST;
        result = handle_shared_memory_run_test(data_buffer);
    } else if (cmd_reg & (1 << 10)) {  // CMD_BIT_GET_TEST_STATUS
        msg_type = MSG_TYPE_GET_TEST_STATUS;
        char response[MAX_RESPONSE_LEN];
        result = handle_shared_memory_get_test_status(response, sizeof(response));
        if (result) {
            write_data_area(response);
            uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
            Xil_Out32(resp_addr, RESP_SUCCESS);
        }
    } else if (cmd_reg & (1 << 11)) {  // CMD_BIT_RESET_PROCESSOR
        msg_type = MSG_TYPE_RESET_PROCESSOR;
        result = handle_shared_memory_reset_processor();
    } else {
        xil_printf("Unknown command bit in register: 0x%08X\r\n", cmd_reg);
        uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
        Xil_Out32(resp_addr, RESP_ERROR);
        // Clear command register
        Xil_Out32(SHARED_MEM_BASE + CMD_REG_OFFSET, 0);
        return 1;
    }
    
    xil_printf("Processing shared memory command: type=%u\r\n", msg_type);
    
    // Set response register
    uint32_t resp_addr = SHARED_MEM_BASE + RESP_REG_OFFSET;
    if (result) {
        Xil_Out32(resp_addr, RESP_SUCCESS);
    } else {
        Xil_Out32(resp_addr, RESP_ERROR);
    }
    
    // Clear command register after processing
    Xil_Out32(SHARED_MEM_BASE + CMD_REG_OFFSET, 0);
    
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
    config.base_address = 0x43C00000;
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

/*
 * Initialize Test Configuration
 * @return: void
 */
static void initialize_test_config(void) {
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