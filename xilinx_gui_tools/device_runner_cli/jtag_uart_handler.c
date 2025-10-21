/*
 * JTAG UART Handler for Device Runner CLI - Baremetal Version
 * 
 * This file implements the embedded side of the Device Runner CLI communication.
 * It runs on the FPGA PS (Processing System) in baremetal mode and handles 
 * commands sent from the Device Runner CLI via JTAG UART.
 * 
 * Author: Device Runner CLI
 * Version: 1.0.0
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

/* Non-blocking character check function */
int kbhit(void) {
    // This is a simplified implementation for baremetal
    // In a real implementation, you would check UART status register
    // For now, we'll use a simple approach
    return 0; // Always return 0 for non-blocking check
}

/* Buffer and Command Definitions */
#define BUFFER_SIZE 1024
#define MAX_COMMAND_LEN 256
#define MAX_RESPONSE_LEN 512

/* Command Register Definitions */
#define CMD_REG_ADDR 0xXXXX0000
#define RESP_REG_ADDR 0xXXXX0004

/* Command Definitions */
#define CMD_INIT "init"
#define CMD_RUN_APP "run_app"
#define CMD_SET_PARAM "set_param"
#define CMD_GET_STATUS "get_status"
#define CMD_CAPTURE_RAM "capture_ram"
#define CMD_EXIT "exit"
#define CMD_HELP "help"

/* Response Codes */
#define RESPONSE_OK "OK"
#define RESPONSE_ERROR "ERROR"
#define RESPONSE_READY "READY"
#define RESPONSE_DONE "DONE"

/* Specific Response Codes */
#define RESPONSE_INIT_OK "INIT_OK"
#define RESPONSE_RUN_OK "RUN_OK"
#define RESPONSE_PARAM_SET_OK "PARAM_SET_OK"
#define RESPONSE_RAM_CAPTURE_OK "RAM_CAPTURE_OK"
#define RESPONSE_EXIT_OK "EXIT_OK"

/* Status Values */
#define STATUS_IDLE "IDLE"
#define STATUS_INITIALIZED "INITIALIZED"
#define STATUS_RUNNING "RUNNING"
#define STATUS_COMPLETED "COMPLETED"
#define STATUS_EXITING "EXITING"

/* Application Modes */
#define MODE_INTERACTIVE 0
#define MODE_BACKGROUND  1

/* Startup Mode Detection */
#define STARTUP_MODE_REG_ADDR 0xXXXX0008
#define MODE_JTAG_INTERACTIVE 0x00000001
#define MODE_JTAG_SCRIPT     0x00000002
#define MODE_UART_INTERACTIVE 0x00000003
#define MODE_UART_SCRIPT     0x00000004

/* Global Variables */
static volatile int running = 1;
static volatile int app_mode = MODE_INTERACTIVE;  /* Default: Interactive mode */
static volatile int startup_mode = MODE_JTAG_INTERACTIVE;  /* Detected startup mode */
static volatile int script_mode = 0;  /* Script mode flag */
static uint32_t param1 = 0x00000001;  /* Default: Short */
static uint32_t param2 = 0x43C00000;  /* Default: Base address */
static uint32_t param3 = 0x00001000;  /* Default: Size */
static char app_status[64] = "IDLE";
static volatile int menu_active = 0;  /* Menu system active flag */

/* Function Prototypes */
static int send_response(const char *response);
static int receive_command(char *command, int max_len);
static void handle_command(const char *command);
static uint32_t handle_init_command(void);
static uint32_t handle_run_app_command(void);
static void handle_set_param_command(const char *command);
static uint32_t handle_get_status_command(void);
static uint32_t handle_capture_ram_command(void);
static void handle_exit_command(void);
static void handle_help_command(void);
static void handle_output_data_command(void);
static void handle_device_dna_command(void);
static void print_banner(void);
static void delay_us(uint32_t delay);
static void show_main_menu(void);
static void show_param_menu(void);
static void show_data_ready_menu(void);
static char get_char_input(void);
static void handle_menu_selection(char choice);
static uint32_t get_hex_input(void);
static void process_commands(void);
static uint32_t do_some_action(void);
static void run_interactive_mode(void);
static void run_background_mode(void);
static void switch_to_background_mode(void);
static void switch_to_interactive_mode(void);
static int check_for_mode_switch(void);
static int detect_startup_mode(void);
static void configure_startup_mode(void);
static void print_startup_banner(void);
static void run_script_message_handler(void);
static void run_interactive_menu_handler(void);
static void handle_script_message(const char *message);
static void process_uart_commands(void);

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
    
    // Initialize application
    handle_init_command();
    
    // Main application loop based on startup mode
    if (script_mode) {
        // Script mode: Handle messages continuously
        xil_printf("Entering script message handling mode...\r\n");
        run_script_message_handler();
    } else {
        // Interactive mode: Display menu and handle user input
        xil_printf("Entering interactive menu mode...\r\n");
        run_interactive_menu_handler();
    }
    
    xil_printf("\r\n=== JTAG UART Handler Exiting ===\r\n");
    return 0;
}

/* Send Response via UART */
static int send_response(const char *response) {
    xil_printf("%s\r\n", response);
    return 0;
}

/* Receive Command from UART */
static int receive_command(char *command, int max_len) {
    int c;
    int len = 0;
    
    /* Check if character is available */
    c = getchar();
    if (c == EOF) {
        return 0;
    }
    
    /* Read characters until newline or buffer full */
    while (c != '\n' && c != '\r' && len < max_len - 1) {
        command[len++] = (char)c;
        c = getchar();
        if (c == EOF) {
            break;
        }
    }
    
    command[len] = '\0';
    return len;
}


/* Handle Incoming Commands */
static void handle_command(const char *command) {
    char cmd[MAX_COMMAND_LEN];
    char *args;
    
    /* Copy command and find arguments */
    strncpy(cmd, command, sizeof(cmd) - 1);
    cmd[sizeof(cmd) - 1] = '\0';
    
    /* Remove trailing newline/carriage return */
    cmd[strcspn(cmd, "\r\n")] = '\0';
    
    /* Find arguments */
    args = strchr(cmd, ' ');
    if (args) {
        *args = '\0';
        args++;
    }
    
    /* Handle different commands */
    if (strcmp(cmd, CMD_INIT) == 0) {
        handle_init_command();
    } else if (strcmp(cmd, CMD_RUN_APP) == 0) {
        handle_run_app_command();
    } else if (strcmp(cmd, CMD_SET_PARAM) == 0) {
        handle_set_param_command(args);
    } else if (strcmp(cmd, CMD_GET_STATUS) == 0) {
        handle_get_status_command();
    } else if (strcmp(cmd, CMD_CAPTURE_RAM) == 0) {
        handle_capture_ram_command();
    } else if (strcmp(cmd, CMD_EXIT) == 0) {
        handle_exit_command();
    } else if (strcmp(cmd, CMD_HELP) == 0) {
        handle_help_command();
    } else {
        send_response("ERROR: Unknown command");
    }
}

/*
* Handle INIT Command
* @return: uint32_t - Result code
*/
static uint32_t handle_init_command(void) {
    xil_printf("Handling INIT command\r\n");
    
    /* Initialize application parameters */
    param1 = 0x00000001;  /* Short */
    param2 = 0x43C00000;  /* Base address */
    param3 = 0x00001000;  /* Size */
    
    /* Set status */
    strcpy(app_status, "INITIALIZED");
    
    /* Send response */
    send_response(RESPONSE_INIT_OK);
    
    return 0x00000001; // Success code
}

/*
* Handle RUN_APP Command
* @return: uint32_t - Result code
*/
static uint32_t handle_run_app_command(void) {
    xil_printf("Handling RUN_APP command\r\n");
    xil_printf("Parameters: P1=0x%08X, P2=0x%08X, P3=0x%08X\r\n", 
               param1, param2, param3);
    
    /* Set status to running */
    strcpy(app_status, "RUNNING");
    
    /* Simulate application execution */
    xil_printf("Running application with parameters...\r\n");
    
    /* Simulate processing time */
    delay_us(1000000); /* 1 second */
    
    /* Set status to completed */
    strcpy(app_status, "COMPLETED");
    
    /* Send response */
    send_response(RESPONSE_RUN_OK);
    
    return 0x00000002; // Success code
}

/*
* Handle SET_PARAM Command
* @param command: The command to handle
* @return: void
*/
static void handle_set_param_command(const char *command) {
    char param_name[16];
    uint32_t param_value;
    
    if (!command) {
        send_response("ERROR: Missing parameter arguments");
        return;
    }
    
    xil_printf("Handling SET_PARAM command: %s\r\n", command);
    
    /* Parse parameter name and value */
    if (sscanf(command, "%s 0x%X", param_name, &param_value) == 2) {
        if (strcmp(param_name, "param1") == 0) {
            param1 = param_value;
            xil_printf("Set param1 to 0x%08X\r\n", param1);
        } else if (strcmp(param_name, "param2") == 0) {
            param2 = param_value;
            xil_printf("Set param2 to 0x%08X\r\n", param2);
        } else if (strcmp(param_name, "param3") == 0) {
            param3 = param_value;
            xil_printf("Set param3 to 0x%08X\r\n", param3);
        } else {
            send_response("ERROR: Unknown parameter name");
            return;
        }
        
        send_response(RESPONSE_PARAM_SET_OK);
    } else {
        send_response("ERROR: Invalid parameter format");
    }
}

/*
* Handle GET_STATUS Command
* @return: uint32_t - Result code
*/
static uint32_t handle_get_status_command(void) {
    char status_response[MAX_RESPONSE_LEN];
    
    xil_printf("Handling GET_STATUS command\r\n");
    
    /* Format status response */
    snprintf(status_response, sizeof(status_response),
             "STATUS: %s, P1: 0x%08X, P2: 0x%08X, P3: 0x%08X",
             app_status, param1, param2, param3);
    
    /* Send response */
    send_response(status_response);
    
    return 0x00000004; // Success code
}

/*
* Handle CAPTURE_RAM Command
* @return: uint32_t - Result code
*/
static uint32_t handle_capture_ram_command(void) {
    xil_printf("Handling CAPTURE_RAM command\r\n");
    
    /* Simulate RAM capture */
    xil_printf("Capturing RAM data...\r\n");
    xil_printf("Base Address: 0x%08X\r\n", param2);
    xil_printf("Size: 0x%08X bytes\r\n", param3);
    
    /* Simulate processing time */
    delay_us(500000); /* 0.5 seconds */
    
    /* Send response with captured data info */
    send_response(RESPONSE_RAM_CAPTURE_OK);
    
    return 0x00000005; // Success code
}

/*
* Handle EXIT Command
* @return: void
*/
static void handle_exit_command(void) {
    xil_printf("Handling EXIT command\r\n");
    
    /* Set status */
    strcpy(app_status, "EXITING");
    
    /* Send response */
    send_response(RESPONSE_EXIT_OK);
    
    /* Stop main loop */
    running = 0;
}

/*
* Handle HELP Command
* @return: void
*/
static void handle_help_command(void) {
    xil_printf("Handling HELP command\r\n");
    
    /* Send help information */
    xil_printf("\r\n=== JTAG UART Handler Help ===\r\n");
    xil_printf("Available Commands:\r\n");
    xil_printf("  init, run_app, set_param, get_status, capture_ram\r\n");
    xil_printf("  output_data, device_dna, exit, help\r\n");
    xil_printf("\r\n");
    xil_printf("Startup Mode Detection:\r\n");
    xil_printf("  Register 0xXXXX0008: Startup mode configuration\r\n");
    xil_printf("  0x00000001: JTAG Interactive Mode\r\n");
    xil_printf("  0x00000002: JTAG Script Mode\r\n");
    xil_printf("  0x00000003: UART Interactive Mode\r\n");
    xil_printf("  0x00000004: UART Script Mode\r\n");
    xil_printf("\r\n");
    xil_printf("Application Modes:\r\n");
    xil_printf("  Interactive Mode: Use menu system\r\n");
    xil_printf("  Background Mode: Commands via memory registers\r\n");
    xil_printf("\r\n");
    xil_printf("Mode Switching:\r\n");
    xil_printf("  Interactive -> Background: Menu option 9\r\n");
    xil_printf("  Background -> Interactive: Register command 6\r\n");
    xil_printf("\r\n");
    xil_printf("Register Commands (Background Mode):\r\n");
    xil_printf("  1: do_some_action\r\n");
    xil_printf("  2: init\r\n");
    xil_printf("  3: run_app\r\n");
    xil_printf("  4: get_status\r\n");
    xil_printf("  5: capture_ram\r\n");
    xil_printf("  6: switch_to_interactive\r\n");
    xil_printf("\r\n");
    xil_printf("Current Configuration:\r\n");
    xil_printf("  Startup Mode: 0x%08X\r\n", startup_mode);
    xil_printf("  Script Mode: %s\r\n", script_mode ? "Active" : "Inactive");
    xil_printf("  App Mode: %s\r\n", app_mode == MODE_INTERACTIVE ? "Interactive" : "Background");
    xil_printf("\r\n");
    
    if (script_mode) {
        xil_printf("Script Mode Operation:\r\n");
        xil_printf("  - Processes UART messages continuously\r\n");
        xil_printf("  - Handles register commands in background\r\n");
        xil_printf("  - Send 'exit' to quit\r\n");
        xil_printf("  - Send 'help' for command list\r\n");
    } else {
        xil_printf("Interactive Mode Operation:\r\n");
        xil_printf("  - Displays menu system\r\n");
        xil_printf("  - Handles user menu selections\r\n");
        xil_printf("  - Processes register commands in background\r\n");
        xil_printf("  - Use menu option 0 to exit\r\n");
    }
    xil_printf("\r\n");
    
    send_response("HELP: Available commands: init, run_app, set_param, get_status, capture_ram, output_data, device_dna, exit, help");
}

/*
* Handle OUTPUT_DATA Command
* @return: void
*/
static void handle_output_data_command(void) {
    xil_printf("Handling OUTPUT_DATA command\r\n");
    
    /* Output application data */
    xil_printf("=== Application Data Output ===\r\n");
    xil_printf("Parameters Used:\r\n");
    xil_printf("  Param1 (Height): 0x%08X\r\n", param1);
    xil_printf("  Param2 (Base):   0x%08X\r\n", param2);
    xil_printf("  Param3 (Size):   0x%08X\r\n", param3);
    xil_printf("\r\n");
    xil_printf("Application Status: %s\r\n", app_status);
    xil_printf("\r\n");
    xil_printf("Simulated Data Output:\r\n");
    xil_printf("  Memory Region: 0x%08X - 0x%08X\r\n", param2, param2 + param3 - 1);
    xil_printf("  Data Size: %d bytes\r\n", param3);
    xil_printf("  Data Format: 32-bit words\r\n");
    xil_printf("\r\n");
    
    /* Simulate data output */
    xil_printf("Data Values:\r\n");
    for (int i = 0; i < 8 && i < (param3 / 4); i++) {
        uint32_t addr = param2 + (i * 4);
        uint32_t value = 0x12345678 + (i * 0x11111111);
        xil_printf("  0x%08X: 0x%08X\r\n", addr, value);
    }
    if (param3 > 32) {
        xil_printf("  ... (showing first 8 values)\r\n");
    }
    
    /* Send response */
    send_response(RESPONSE_OK);
}

/*
* Handle DEVICE_DNA Command
* @return: void
*/
static void handle_device_dna_command(void) {
    xil_printf("Handling DEVICE_DNA command\r\n");
    
    /* Generate simulated 96-bit device DNA */
    uint32_t dna_low = 0x12345678;
    uint32_t dna_mid = 0x9ABCDEF0;
    uint32_t dna_high = 0x13579BDF;
    
    xil_printf("=== Device DNA (PS) ===\r\n");
    xil_printf("Device DNA (96-bit):\r\n");
    xil_printf("  High: 0x%08X\r\n", dna_high);
    xil_printf("  Mid:  0x%08X\r\n", dna_mid);
    xil_printf("  Low:  0x%08X\r\n", dna_low);
    xil_printf("\r\n");
    xil_printf("Full DNA: 0x%08X%08X%08X\r\n", dna_high, dna_mid, dna_low);
    xil_printf("\r\n");
    
    /* Send response with DNA */
    char dna_response[MAX_RESPONSE_LEN];
    snprintf(dna_response, sizeof(dna_response),
             "DEVICE_DNA: 0x%08X%08X%08X", dna_high, dna_mid, dna_low);
    send_response(dna_response);
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
* Print Startup Banner
* @return: void
*/
static void print_banner(void) {
    xil_printf("\r\n");
    xil_printf("########  ######## ##     ## ####  ######  ########     ######  ##       #### \r\n");
    xil_printf("##     ## ##       ##     ##  ##  ##    ## ##          ##    ## ##        ##  \r\n");
    xil_printf("##     ## ##       ##     ##  ##  ##       ##          ##       ##        ##  \r\n");
    xil_printf("##     ## ######   ##     ##  ##  ##       ######      ##       ##        ##  \r\n");
    xil_printf("##     ## ##        ##   ##   ##  ##       ##          ##       ##        ##  \r\n");
    xil_printf("##     ## ##         ## ##    ##  ##    ## ##          ##    ## ##        ##  \r\n");
    xil_printf("########  ########    ###    ####  ######  ########     ######  ######## #### \r\n");
    xil_printf("\r\n");
    xil_printf("    JTAG UART Handler v1.0.0 (PS Version)\r\n");
    xil_printf("    FPGA PS Baremetal Communication Interface\r\n");
    xil_printf("\r\n");
}

/* Show Main Menu */
static void show_main_menu(void) {
    xil_printf("\r\n=== JTAG UART Handler Menu ===\r\n");
    xil_printf("1. Initialize\r\n");
    xil_printf("2. Set Parameters\r\n");
    xil_printf("3. Run Application\r\n");
    xil_printf("4. Get Status\r\n");
    xil_printf("5. Capture RAM\r\n");
    xil_printf("6. Output Data\r\n");
    xil_printf("7. Get Device DNA\r\n");
    xil_printf("8. Help\r\n");
    xil_printf("9. Switch to Background Mode\r\n");
    xil_printf("0. Exit\r\n");
    xil_printf("Enter choice (0-9): ");
}

/* Show Parameter Menu */
static void show_param_menu(void) {
    xil_printf("\r\n=== Parameter Configuration ===\r\n");
    xil_printf("Current Parameters:\r\n");
    xil_printf("  Param1: 0x%08X\r\n", param1);
    xil_printf("  Param2: 0x%08X\r\n", param2);
    xil_printf("  Param3: 0x%08X\r\n", param3);
    xil_printf("\r\n");
    xil_printf("1. Set Param1 (Height: Short/Medium/Tall)\r\n");
    xil_printf("2. Set Param2 (Base Address)\r\n");
    xil_printf("3. Set Param3 (Size)\r\n");
    xil_printf("4. Back to Main Menu\r\n");
    xil_printf("Enter choice (1-4): ");
}

/* Show Data Ready Menu */
static void show_data_ready_menu(void) {
    xil_printf("\r\n=== Data Ready Handling ===\r\n");
    xil_printf("1. Manual Mode (Press Enter when ready)\r\n");
    xil_printf("2. Fixed Delay (5 seconds)\r\n");
    xil_printf("3. Polling Mode (Check status)\r\n");
    xil_printf("Enter choice (1-3): ");
}

/* Get Single Character Input */
static char get_char_input(void) {
    int c;
    c = getchar();
    if (c == EOF) {
        return 0;
    }
    /* Clear any remaining characters in buffer */
    while (getchar() != '\n' && getchar() != EOF);
    return (char)c;
}

/* Handle Menu Selection */
static void handle_menu_selection(char choice) {
    char param_choice;
    char data_choice;
    uint32_t new_value;
    
    switch (choice) {
        case '1':
            xil_printf("\r\nInitializing...\r\n");
            handle_init_command();
            break;
            
        case '2':
            show_param_menu();
            param_choice = get_char_input();
            switch (param_choice) {
                case '1':
                    xil_printf("\r\nHeight Selection:\r\n");
                    xil_printf("1. Short (0x00000001)\r\n");
                    xil_printf("2. Medium (0x00000002)\r\n");
                    xil_printf("3. Tall (0x00000003)\r\n");
                    xil_printf("Enter choice (1-3): ");
                    param_choice = get_char_input();
                    switch (param_choice) {
                        case '1': param1 = 0x00000001; break;
                        case '2': param1 = 0x00000002; break;
                        case '3': param1 = 0x00000003; break;
                        default: xil_printf("Invalid choice\r\n"); break;
                    }
                    xil_printf("Param1 set to 0x%08X\r\n", param1);
                    break;
                    
                case '2':
                    xil_printf("\r\nEnter Param2 value (hex): ");
                    if (scanf("%X", &new_value) == 1) {
                        param2 = new_value;
                        xil_printf("Param2 set to 0x%08X\r\n", param2);
                    } else {
                        xil_printf("Invalid input\r\n");
                    }
                    break;
                    
                case '3':
                    xil_printf("\r\nEnter Param3 value (hex): ");
                    if (scanf("%X", &new_value) == 1) {
                        param3 = new_value;
                        xil_printf("Param3 set to 0x%08X\r\n", param3);
                    } else {
                        xil_printf("Invalid input\r\n");
                    }
                    break;
                    
                case '4':
                    xil_printf("\r\nReturning to main menu...\r\n");
                    break;
                    
                default:
                    xil_printf("Invalid choice\r\n");
                    break;
            }
            break;
            
        case '3':
            xil_printf("\r\nRunning application...\r\n");
            handle_run_app_command();
            break;
            
        case '4':
            xil_printf("\r\nGetting status...\r\n");
            handle_get_status_command();
            break;
            
        case '5':
            show_data_ready_menu();
            data_choice = get_char_input();
            switch (data_choice) {
                case '1':
                    xil_printf("\r\nManual mode: Press Enter when data is ready...\r\n");
                    getchar(); /* Wait for Enter */
                    xil_printf("Data ready confirmed\r\n");
                    break;
                    
                case '2':
                    xil_printf("\r\nFixed delay: Waiting 5 seconds...\r\n");
                    delay_us(5000000); /* 5 seconds */
                    xil_printf("Delay completed\r\n");
                    break;
                    
                case '3':
                    xil_printf("\r\nPolling mode: Checking status...\r\n");
                    break;
                    
                default:
                    xil_printf("Invalid choice\r\n");
                    break;
            }
            handle_capture_ram_command();
            break;
            
        case '6':
            xil_printf("\r\nOutputting data...\r\n");
            handle_output_data_command();
            break;
            
        case '7':
            xil_printf("\r\nGetting device DNA...\r\n");
            handle_device_dna_command();
            break;
            
        case '8':
            xil_printf("\r\nShowing help...\r\n");
            handle_help_command();
            break;
            
        case '9':
            xil_printf("\r\nSwitching to Background Mode...\r\n");
            switch_to_background_mode();
            break;
            
        case '0':
            xil_printf("\r\nExiting...\r\n");
            handle_exit_command();
            break;
            
        default:
            xil_printf("Invalid choice. Please enter 0-9.\r\n");
            break;
    }
}

/*
* Check for Mode Switch Commands
* @return: int - 1 if mode switch occurred, 0 otherwise
*/
static int check_for_mode_switch(void) {
    // In interactive mode, mode switching is handled by menu system
    // In background mode, we check for special characters
    if (app_mode == MODE_BACKGROUND) {
        // Check if there's any input available
        // This is a simplified check - in real implementation you'd check UART status
        return 0; // For now, mode switching in background is handled by register commands
    }
    
    return 0;
}

/*
* Run Interactive Mode
* @return: void
*/
static void run_interactive_mode(void) {
    static int menu_shown = 0;
    
    if (!menu_shown) {
        show_main_menu();
        menu_shown = 1;
        menu_active = 1;
    }
    
    // Check for menu input using existing get_char_input
    // This will block until input is received
    char choice = get_char_input();
    if (choice != 0) {
        handle_menu_selection(choice);
        menu_shown = 0; // Show menu again after selection
    }
}

/*
* Run Background Mode
* @return: void
*/
static void run_background_mode(void) {
    // Process commands from registers
    process_commands();
    
    // Small delay for polling interval
    delay_us(10000); // 10ms polling interval
}

/*
* Switch to Background Mode
* @return: void
*/
static void switch_to_background_mode(void) {
    app_mode = MODE_BACKGROUND;
    menu_active = 0;
    xil_printf("\r\n=== Switched to Background Mode ===\r\n");
    xil_printf("Commands processed via memory registers\r\n");
    xil_printf("Press 'i' + Enter to return to interactive mode\r\n");
    xil_printf("Press 'q' + Enter to quit\r\n");
}

/*
* Switch to Interactive Mode
* @return: void
*/
static void switch_to_interactive_mode(void) {
    app_mode = MODE_INTERACTIVE;
    menu_active = 1;
    xil_printf("\r\n=== Switched to Interactive Mode ===\r\n");
    xil_printf("Use menu system for commands\r\n");
    xil_printf("Press 'b' + Enter to switch to background mode\r\n");
    xil_printf("Press 'q' + Enter to quit\r\n");
}

/*
* Detect Startup Mode
* Checks register and UART for startup mode configuration
* @return: int - Detected startup mode
*/
static int detect_startup_mode(void) {
    uint32_t mode_reg_value = 0;
    int uart_input_available = 0;
    char test_char;
    
    xil_printf("Detecting startup mode...\r\n");
    
    // Method 1: Check startup mode register
    mode_reg_value = Xil_In32(STARTUP_MODE_REG_ADDR);
    if (mode_reg_value != 0) {
        xil_printf("Startup mode from register: 0x%08X\r\n", mode_reg_value);
        return mode_reg_value;
    }
    
    // Method 2: Check for UART input (script mode indicator)
    // Wait briefly for any incoming characters
    delay_us(100000); // 100ms delay
    
    // Check if there's any input on UART (simplified check)
    // In real implementation, you would check UART status register
    uart_input_available = 0; // Placeholder - would check UART status
    
    if (uart_input_available) {
        xil_printf("UART input detected - Script mode\r\n");
        return MODE_UART_SCRIPT;
    }
    
    // Method 3: Check for specific startup sequence
    // Look for magic sequence or configuration
    delay_us(50000); // Additional 50ms delay
    
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
    xil_printf("\r\n");
    xil_printf("########  ######## ##     ## ####  ######  ########     ######  ##       #### \r\n");
    xil_printf("##     ## ##       ##     ##  ##  ##    ## ##          ##    ## ##        ##  \r\n");
    xil_printf("##     ## ##       ##     ##  ##  ##       ##          ##       ##        ##  \r\n");
    xil_printf("##     ## ######   ##     ##  ##  ##       ######      ##       ##        ##  \r\n");
    xil_printf("##     ## ##        ##   ##   ##  ##       ##          ##       ##        ##  \r\n");
    xil_printf("##     ## ##         ## ##    ##  ##    ## ##          ##    ## ##        ##  \r\n");
    xil_printf("########  ########    ###    ####  ######  ########     ######  ######## #### \r\n");
    xil_printf("\r\n");
    xil_printf("    JTAG UART Handler v1.0.0 (PS Version)\r\n");
    xil_printf("    FPGA PS Baremetal Communication Interface\r\n");
    xil_printf("\r\n");
    
    // Print mode-specific information
    switch (startup_mode) {
        case MODE_JTAG_INTERACTIVE:
            xil_printf("=== STARTUP MODE: JTAG INTERACTIVE ===\r\n");
            xil_printf("Interface: JTAG UART\r\n");
            xil_printf("Operation: Interactive Menu System\r\n");
            xil_printf("Commands: Via menu selections\r\n");
            break;
            
        case MODE_JTAG_SCRIPT:
            xil_printf("=== STARTUP MODE: JTAG SCRIPT ===\r\n");
            xil_printf("Interface: JTAG UART\r\n");
            xil_printf("Operation: Background Command Processing\r\n");
            xil_printf("Commands: Via memory registers\r\n");
            break;
            
        case MODE_UART_INTERACTIVE:
            xil_printf("=== STARTUP MODE: UART INTERACTIVE ===\r\n");
            xil_printf("Interface: UART\r\n");
            xil_printf("Operation: Interactive Menu System\r\n");
            xil_printf("Commands: Via menu selections\r\n");
            break;
            
        case MODE_UART_SCRIPT:
            xil_printf("=== STARTUP MODE: UART SCRIPT ===\r\n");
            xil_printf("Interface: UART\r\n");
            xil_printf("Operation: Background Command Processing\r\n");
            xil_printf("Commands: Via memory registers\r\n");
            break;
            
        default:
            xil_printf("=== STARTUP MODE: DEFAULT INTERACTIVE ===\r\n");
            xil_printf("Interface: JTAG UART\r\n");
            xil_printf("Operation: Interactive Menu System\r\n");
            xil_printf("Commands: Via menu selections\r\n");
            break;
    }
    
    xil_printf("\r\n");
    
    if (script_mode) {
        xil_printf("Script Mode Active - Commands processed via messages\r\n");
        xil_printf("Message Sources: UART and Memory Registers\r\n");
        xil_printf("Commands: init, run_app, set_param, get_status, capture_ram, exit, help\r\n");
        xil_printf("Register Commands: 1-6 (see help for details)\r\n");
    } else {
        xil_printf("Interactive Mode Active - Use menu system\r\n");
        xil_printf("Menu Options: 1-9 (see menu for details)\r\n");
        xil_printf("Press '9' in menu to switch to background mode\r\n");
    }
    
    xil_printf("\r\n");
}

/*
* Run Script Message Handler
* Continuously processes messages in script mode
* @return: void
*/
static void run_script_message_handler(void) {
    char message_buffer[MAX_COMMAND_LEN];
    int message_len;
    
    xil_printf("Script mode active - Processing messages...\r\n");
    xil_printf("Send 'exit' to quit script mode\r\n");
    xil_printf("Send 'help' for available commands\r\n");
    xil_printf("\r\n");
    
    while (running) {
        // Process register-based commands
        process_commands();
        
        // Process UART-based commands
        process_uart_commands();
        
        // Small delay to prevent excessive CPU usage
        delay_us(10000); // 10ms polling interval
    }
}

/*
* Run Interactive Menu Handler
* Displays menu and handles user input in interactive mode
* @return: void
*/
static void run_interactive_menu_handler(void) {
    static int menu_shown = 0;
    
    xil_printf("Interactive mode active - Menu system ready\r\n");
    xil_printf("Use menu options for commands\r\n");
    xil_printf("\r\n");
    
    while (running) {
        // Show menu if not already shown
        if (!menu_shown) {
            show_main_menu();
            menu_shown = 1;
            menu_active = 1;
        }
        
        // Check for menu input
        char choice = get_char_input();
        if (choice != 0) {
            handle_menu_selection(choice);
            menu_shown = 0; // Show menu again after selection
        }
        
        // Also process register commands in background
        process_commands();
        
        // Small delay to prevent excessive CPU usage
        delay_us(1000);
    }
}

/*
* Handle Script Message
* Processes individual script messages
* @param message: The message to process
* @return: void
*/
static void handle_script_message(const char *message) {
    char cmd[MAX_COMMAND_LEN];
    char *args;
    
    if (!message) return;
    
    xil_printf("Script message received: %s\r\n", message);
    
    /* Copy command and find arguments */
    strncpy(cmd, message, sizeof(cmd) - 1);
    cmd[sizeof(cmd) - 1] = '\0';
    
    /* Remove trailing newline/carriage return */
    cmd[strcspn(cmd, "\r\n")] = '\0';
    
    /* Find arguments */
    args = strchr(cmd, ' ');
    if (args) {
        *args = '\0';
        args++;
    }
    
    /* Handle different commands */
    if (strcmp(cmd, CMD_INIT) == 0) {
        handle_init_command();
    } else if (strcmp(cmd, CMD_RUN_APP) == 0) {
        handle_run_app_command();
    } else if (strcmp(cmd, CMD_SET_PARAM) == 0) {
        handle_set_param_command(args);
    } else if (strcmp(cmd, CMD_GET_STATUS) == 0) {
        handle_get_status_command();
    } else if (strcmp(cmd, CMD_CAPTURE_RAM) == 0) {
        handle_capture_ram_command();
    } else if (strcmp(cmd, CMD_EXIT) == 0) {
        xil_printf("Script mode exit command received\r\n");
        running = 0;
    } else if (strcmp(cmd, CMD_HELP) == 0) {
        handle_help_command();
    } else {
        xil_printf("Unknown script command: %s\r\n", cmd);
        send_response("ERROR: Unknown command");
    }
}

/*
* Process UART Commands
* Checks for and processes UART-based commands
* @return: void
*/
static void process_uart_commands(void) {
    char command[MAX_COMMAND_LEN];
    int len;
    
    // Try to receive a command from UART
    len = receive_command(command, MAX_COMMAND_LEN);
    if (len > 0) {
        handle_script_message(command);
    }
}

/*
* Process Commands from Command Register
* Polls the command register and processes any commands received
* @return: void
*/
static void process_commands(void) {
    uint32_t cmd = Xil_In32(CMD_REG_ADDR);
    if (cmd != 0) {
        uint32_t result = 0;
        
        xil_printf("Processing command: %u\r\n", cmd);
        
        switch(cmd) {
            case 1: 
                result = do_some_action(); 
                break;
            case 2:
                result = handle_init_command();
                break;
            case 3:
                result = handle_run_app_command();
                break;
            case 4:
                result = handle_get_status_command();
                break;
            case 5:
                result = handle_capture_ram_command();
                break;
            case 6:
                // Switch to interactive mode
                switch_to_interactive_mode();
                result = 0x00000006; // Mode switch success code
                break;
            default:
                result = 0xFFFFFFFF; // Error code for unknown command
                xil_printf("Unknown command: %u\r\n", cmd);
                break;
        }
        
        // Write back result
        Xil_Out32(RESP_REG_ADDR, result);
        
        // Clear command register
        Xil_Out32(CMD_REG_ADDR, 0);
        
        // Also print via JTAG UART for host parsing
        xil_printf("CMDRESP:%u:%08X\r\n", cmd, result);
    }
}

/*
* Do Some Action - Example command handler
* @return: uint32_t - Result code
*/
static uint32_t do_some_action(void) {
    xil_printf("Executing do_some_action()\r\n");
    
    // Simulate some processing
    delay_us(100000); // 0.1 second delay
    
    // Return success code
    return 0x12345678;
}

/*
* Get Hex Input from UART
* @return: uint32_t - The hex value entered by user
*/
static uint32_t get_hex_input(void)
{
    char input[32];
    int idx = 0;
    uint32_t value = 0;
    char c;

    xil_printf("Enter hex value (with or without 0x prefix): ");

    while (1)
    {
        c = inbyte();  // blocking UART read

        // Handle Enter key
        if (c == '\r' || c == '\n')
        {
            input[idx] = '\0';
            xil_printf("\r\n");

            // Convert to uint32_t
            value = (uint32_t)strtoul(input, NULL, 16);

            xil_printf("You entered: 0x%08lX (%lu)\r\n", 
                       (unsigned long)value, (unsigned long)value);

            return value;  // ✅ exit and return value
        }

        // Handle Backspace
        if ((c == '\b' || c == 0x7F) && idx > 0)
        {
            idx--;
            xil_printf("\b \b");
            continue;
        }

        // Accept only hex digits and 0x prefix chars
        if (isxdigit(c) || c == 'x' || c == 'X')
        {
            if (idx < (int)(sizeof(input) - 1))
            {
                input[idx++] = c;
                outbyte(c); // echo
            }
        }
        else
        {
            xil_printf("\a"); // beep for invalid
        }
    }
}