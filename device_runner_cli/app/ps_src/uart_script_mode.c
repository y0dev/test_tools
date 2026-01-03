/**
 * @file uart_script_mode.c
 * @brief UART script mode implementation
 * 
 * This file implements UART script mode functionality. UART script mode
 * processes commands received via UART interface (start, stop, exit).
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>
#include "xil_printf.h"

#include "include/constants.h"
#include "include/types.h"
#include "jtag_uart_handler.h"
#include "uart_script_mode.h"
#include "shared_memory.h"
#include "helpers.h"

// UART I/O functions from BSP
char inbyte(void);
void outbyte(char c);

/* External global variables */
extern volatile int running;
extern volatile int startup_mode;
extern config_t config;

/* ============================================================================
 * UART Script Mode Main Loop
 * ============================================================================ */

/**
 * @brief Run UART script mode main loop
 * 
 * Main loop for UART script mode. Continuously listens for UART commands
 * (start, stop, exit) and processes them accordingly.
 */
void run_uart_script_mode(void) {
    xil_printf("UART Script Mode: Listening for UART commands (start, stop, exit)\r\n");
    xil_printf("Send 'start' to start execution\r\n");
    xil_printf("Send 'stop' to stop execution\r\n");
    xil_printf("Send 'exit' to quit script mode\r\n");
    xil_printf("Send 'help' for available commands\r\n");
    xil_printf("\r\n");
    
    while (running) {
        // Process UART commands
        char uart_command[MAX_COMMAND_LEN];
        if (receive_command(uart_command, sizeof(uart_command)) > 0) {
            handle_command(uart_command);
        }
    }
}

/* ============================================================================
 * UART Communication Functions
 * ============================================================================ */

/**
 * @brief Initialize JTAG UART communication
 * 
 * Initializes the JTAG UART interface for communication. This function
 * performs any necessary setup for UART communication, though in most
 * Xilinx BSP systems, the UART is already initialized during system startup.
 * 
 * @return 0 on success, -1 on error
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
 * Parses and processes a command string received from UART. Command strings
 * should match the command definitions in jtag_uart_handler.h.
 * 
 * Supported commands:
 * - CMD_START ("start"): Start application execution (UART script mode only)
 * - CMD_STOP ("stop"): Stop application execution (UART script mode only)
 * - CMD_EXIT ("exit"): Exit the application
 * - CMD_HELP ("help"): Display help information
 * 
 * @param[in] command Null-terminated command string to process
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
    if (strcmp(command, CMD_START) == 0) {
        xil_printf("Command: START\r\n");
        // Start application execution (UART script mode)
        if (startup_mode == MODE_UART_SCRIPT) {
            // Initialize and start the application
            handle_shared_memory_init();
            handle_shared_memory_run_app();
            send_response("START_OK");
        } else {
            send_response(RESPONSE_ERROR);
        }
    }
    else if (strcmp(command, CMD_STOP) == 0) {
        xil_printf("Command: STOP\r\n");
        // Stop application execution (UART script mode)
        if (startup_mode == MODE_UART_SCRIPT) {
            // Stop the application (could set a flag or call a stop function)
            send_response("STOP_OK");
        } else {
            send_response(RESPONSE_ERROR);
        }
    }
    else if (strcmp(command, CMD_EXIT) == 0) {
        xil_printf("Command: EXIT\r\n");
        handle_shared_memory_exit();
        send_response(RESPONSE_EXIT_OK);
        // In UART script mode, exit should stop the application
        if (startup_mode == MODE_UART_SCRIPT) {
            running = 0;
        }
    }
    else if (strcmp(command, CMD_INIT) == 0) {
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
    else if (strcmp(command, CMD_HELP) == 0) {
        xil_printf("Command: HELP\r\n");
        xil_printf("Available commands:\r\n");
        if (startup_mode == MODE_UART_SCRIPT) {
            xil_printf("  %s - Start application execution\r\n", CMD_START);
            xil_printf("  %s - Stop application execution\r\n", CMD_STOP);
            xil_printf("  %s - Exit application\r\n", CMD_EXIT);
        } else {
            xil_printf("  %s - Initialize application\r\n", CMD_INIT);
            xil_printf("  %s - Run application\r\n", CMD_RUN_APP);
            xil_printf("  %s <param> <value> - Set parameter\r\n", CMD_SET_PARAM);
            xil_printf("  %s - Get status\r\n", CMD_GET_STATUS);
            xil_printf("  %s - Capture RAM\r\n", CMD_CAPTURE_RAM);
            xil_printf("  %s - Exit application\r\n", CMD_EXIT);
        }
        xil_printf("  %s - Show this help\r\n", CMD_HELP);
    }
    else {
        xil_printf("Unknown command: %s\r\n", command);
        xil_printf("Type '%s' for available commands\r\n", CMD_HELP);
        send_response(RESPONSE_ERROR);
    }
}

