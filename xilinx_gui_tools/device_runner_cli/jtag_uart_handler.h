/*
 * JTAG UART Handler - Command Definitions Header
 * 
 * This header file defines the command protocol between the Device Runner CLI
 * and the embedded JTAG UART handler running on the FPGA PS.
 * 
 * Author: Device Runner CLI
 * Version: 1.0.0
 * Date: 2024
 */

#ifndef JTAG_UART_HANDLER_H
#define JTAG_UART_HANDLER_H

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

/* Default Parameter Values */
#define DEFAULT_PARAM1 0x00000001  /* Short */
#define DEFAULT_PARAM2 0x43C00000  /* Base address */
#define DEFAULT_PARAM3 0x00001000  /* Size */

/* Communication Constants */
#define MAX_COMMAND_LEN 256
#define MAX_RESPONSE_LEN 512
#define BUFFER_SIZE 1024

/* Function Prototypes */
int init_jtag_uart(void);
void cleanup_jtag_uart(void);
int send_response(const char *response);
int receive_command(char *command, int max_len);
void handle_command(const char *command);

#endif /* JTAG_UART_HANDLER_H */
