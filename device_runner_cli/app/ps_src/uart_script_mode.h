/**
 * @file uart_script_mode.h
 * @brief UART script mode functions
 * 
 * This header file contains declarations for UART script mode operations,
 * including UART command handling and communication.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#ifndef UART_SCRIPT_MODE_H
#define UART_SCRIPT_MODE_H

void run_uart_script_mode(void);
int init_jtag_uart(void);
void cleanup_jtag_uart(void);
int send_response(const char *response);
int receive_command(char *command, int max_len);
void handle_command(const char *command);

#endif /* UART_SCRIPT_MODE_H */

