/*
 * JTAG UART Handler for Device Runner CLI - PL Version
 * 
 * This file implements the embedded side of the Device Runner CLI communication.
 * It runs on the FPGA PL (Programmable Logic) and handles commands sent from
 * the Device Runner CLI via JTAG UART.
 * 
 * Author: Device Runner CLI
 * Version: 1.0.0
 * Date: 2024
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "xil_printf.h"

/* Buffer and Command Definitions */
#define BUFFER_SIZE 1024
#define MAX_COMMAND_LEN 256
#define MAX_RESPONSE_LEN 512

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

/* Global Variables */
static volatile int running = 1;
static uint32_t param1 = 0x00000001;  /* Default: Short */
static uint32_t param2 = 0x43C00000;  /* Default: Base address */
static uint32_t param3 = 0x00001000;  /* Default: Size */
static char app_status[64] = "IDLE";

/* Function Prototypes */
static int send_response(const char *response);
static int receive_command(char *command, int max_len);
static void handle_command(const char *command);
static void handle_init_command(void);
static void handle_run_app_command(void);
static void handle_set_param_command(const char *command);
static void handle_get_status_command(void);
static void handle_capture_ram_command(void);
static void handle_exit_command(void);
static void handle_help_command(void);
static void print_banner(void);
static void delay_us(uint32_t delay);
static void show_main_menu(void);
static void show_param_menu(void);
static void show_data_ready_menu(void);
static char get_char_input(void);
static void handle_menu_selection(char choice);

/* Main Application Entry Point */
int main(void) {
    char choice;
    
    /* Print startup banner */
    print_banner();
    
    xil_printf("JTAG UART Handler (PL) started successfully\r\n");
    xil_printf("Waiting for commands...\r\n\r\n");
    
    /* Send ready signal */
    send_response(RESPONSE_READY);
    
    /* Main menu loop */
    while (running) {
        show_main_menu();
        choice = get_char_input();
        handle_menu_selection(choice);
        
        /* Small delay to prevent busy waiting */
        delay_us(1000); /* 1ms delay */
    }
    
    xil_printf("JTAG UART Handler (PL) stopped\r\n");
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

/* Handle INIT Command */
static void handle_init_command(void) {
    xil_printf("Handling INIT command\r\n");
    
    /* Initialize application parameters */
    param1 = 0x00000001;  /* Short */
    param2 = 0x43C00000;  /* Base address */
    param3 = 0x00001000;  /* Size */
    
    /* Set status */
    strcpy(app_status, "INITIALIZED");
    
    /* Send response */
    send_response(RESPONSE_INIT_OK);
}

/* Handle RUN_APP Command */
static void handle_run_app_command(void) {
    xil_printf("Handling RUN_APP command\r\n");
    xil_printf("Parameters: P1=0x%08X, P2=0x%08X, P3=0x%08X\r\n", 
               param1, param2, param3);
    
    /* Set status to running */
    strcpy(app_status, "RUNNING");
    
    /* Simulate application execution */
    xil_printf("Running PL application with parameters...\r\n");
    
    /* Simulate processing time */
    delay_us(1000000); /* 1 second */
    
    /* Set status to completed */
    strcpy(app_status, "COMPLETED");
    
    /* Send response */
    send_response(RESPONSE_RUN_OK);
}

/* Handle SET_PARAM Command */
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

/* Handle GET_STATUS Command */
static void handle_get_status_command(void) {
    char status_response[MAX_RESPONSE_LEN];
    
    xil_printf("Handling GET_STATUS command\r\n");
    
    /* Format status response */
    snprintf(status_response, sizeof(status_response),
             "STATUS: %s, P1: 0x%08X, P2: 0x%08X, P3: 0x%08X",
             app_status, param1, param2, param3);
    
    /* Send response */
    send_response(status_response);
}

/* Handle CAPTURE_RAM Command */
static void handle_capture_ram_command(void) {
    xil_printf("Handling CAPTURE_RAM command\r\n");
    
    /* Simulate RAM capture */
    xil_printf("Capturing PL RAM data...\r\n");
    xil_printf("Base Address: 0x%08X\r\n", param2);
    xil_printf("Size: 0x%08X bytes\r\n", param3);
    
    /* Simulate processing time */
    delay_us(500000); /* 0.5 seconds */
    
    /* Send response with captured data info */
    send_response(RESPONSE_RAM_CAPTURE_OK);
}

/* Handle EXIT Command */
static void handle_exit_command(void) {
    xil_printf("Handling EXIT command\r\n");
    
    /* Set status */
    strcpy(app_status, "EXITING");
    
    /* Send response */
    send_response(RESPONSE_EXIT_OK);
    
    /* Stop main loop */
    running = 0;
}

/* Handle HELP Command */
static void handle_help_command(void) {
    xil_printf("Handling HELP command\r\n");
    
    /* Send help information */
    send_response("HELP: Available commands: init, run_app, set_param, get_status, capture_ram, exit, help");
}

/* Simple delay function */
static void delay_us(uint32_t delay) {
    volatile uint32_t count;
    for (count = 0; count < delay; count++) {
        /* Simple delay loop */
    }
}

/* Print Startup Banner */
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
    xil_printf("    ██████╗██╗     ██╗\r\n");
    xil_printf("   ██╔════╝██║     ██║\r\n");
    xil_printf("   ██║     ██║     ██║\r\n");
    xil_printf("   ██║     ██║     ██║\r\n");
    xil_printf("   ╚██████╗███████╗██║\r\n");
    xil_printf("    ╚═════╝╚══════╝╚═╝\r\n");
    xil_printf("\r\n");
    xil_printf("    JTAG UART Handler v1.0.0 (PL Version)\r\n");
    xil_printf("    FPGA PL Baremetal Communication Interface\r\n");
    xil_printf("\r\n");
}

/* Show Main Menu */
static void show_main_menu(void) {
    xil_printf("\r\n=== JTAG UART Handler Menu (PL) ===\r\n");
    xil_printf("1. Initialize\r\n");
    xil_printf("2. Set Parameters\r\n");
    xil_printf("3. Run Application\r\n");
    xil_printf("4. Get Status\r\n");
    xil_printf("5. Capture RAM\r\n");
    xil_printf("6. Help\r\n");
    xil_printf("7. Exit\r\n");
    xil_printf("Enter choice (1-7): ");
}

/* Show Parameter Menu */
static void show_param_menu(void) {
    xil_printf("\r\n=== Parameter Configuration (PL) ===\r\n");
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
    xil_printf("\r\n=== Data Ready Handling (PL) ===\r\n");
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
            xil_printf("\r\nInitializing PL...\r\n");
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
            xil_printf("\r\nRunning PL application...\r\n");
            handle_run_app_command();
            break;
            
        case '4':
            xil_printf("\r\nGetting PL status...\r\n");
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
                    xil_printf("\r\nPolling mode: Checking PL status...\r\n");
                    break;
                    
                default:
                    xil_printf("Invalid choice\r\n");
                    break;
            }
            handle_capture_ram_command();
            break;
            
        case '6':
            xil_printf("\r\nShowing PL help...\r\n");
            handle_help_command();
            break;
            
        case '7':
            xil_printf("\r\nExiting PL handler...\r\n");
            handle_exit_command();
            break;
            
        default:
            xil_printf("Invalid choice. Please enter 1-7.\r\n");
            break;
    }
}
