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
#include "xuartlite.h"
#include "xscugic.h"
#include "xil_exception.h"
#include "xparameters.h"

/* JTAG UART Configuration for PL */
#define UART_DEVICE_ID XPAR_AXI_UARTLITE_0_DEVICE_ID
#define INTC_DEVICE_ID XPAR_PS7_SCUGIC_SINGLE_DEVICE_ID
#define UART_INT_IRQ_ID XPAR_FABRIC_AXI_UARTLITE_0_INTERRUPT_INTR

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
static XUartLite UartLite;
static XScuGic InterruptController;
static volatile int running = 1;
static uint32_t param1 = 0x00000001;  /* Default: Short */
static uint32_t param2 = 0x43C00000;  /* Default: Base address */
static uint32_t param3 = 0x00001000;  /* Default: Size */
static char app_status[64] = "IDLE";
static char rx_buffer[BUFFER_SIZE];
static int rx_count = 0;

/* Function Prototypes */
static int init_uart(void);
static int init_interrupts(void);
static void uart_interrupt_handler(void *CallBackRef, unsigned int EventData);
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

/* Main Application Entry Point */
int main(void) {
    char command[MAX_COMMAND_LEN];
    int ret;
    
    /* Initialize UART */
    if (init_uart() != XST_SUCCESS) {
        xil_printf("ERROR: Failed to initialize UART\r\n");
        return -1;
    }
    
    /* Initialize interrupts */
    if (init_interrupts() != XST_SUCCESS) {
        xil_printf("ERROR: Failed to initialize interrupts\r\n");
        return -1;
    }
    
    /* Print startup banner */
    print_banner();
    
    xil_printf("JTAG UART Handler (PL) started successfully\r\n");
    xil_printf("UART Device ID: %d\r\n", UART_DEVICE_ID);
    xil_printf("Waiting for commands...\r\n\r\n");
    
    /* Send ready signal */
    send_response(RESPONSE_READY);
    
    /* Main command loop */
    while (running) {
        /* Check for received data */
        if (rx_count > 0) {
            /* Process received command */
            memcpy(command, rx_buffer, rx_count);
            command[rx_count] = '\0';
            
            xil_printf("Received command: %s\r\n", command);
            handle_command(command);
            
            /* Clear buffer */
            rx_count = 0;
            memset(rx_buffer, 0, sizeof(rx_buffer));
        }
        
        /* Small delay to prevent busy waiting */
        delay_us(1000); /* 1ms delay */
    }
    
    xil_printf("JTAG UART Handler (PL) stopped\r\n");
    return 0;
}

/* Initialize UART */
static int init_uart(void) {
    XUartLite_Config *Config;
    int Status;
    
    /* Initialize the UART driver */
    Config = XUartLite_LookupConfig(UART_DEVICE_ID);
    if (NULL == Config) {
        return XST_FAILURE;
    }
    
    Status = XUartLite_CfgInitialize(&UartLite, Config, Config->RegBaseAddr);
    if (Status != XST_SUCCESS) {
        return XST_FAILURE;
    }
    
    /* Set up interrupt handler */
    XUartLite_SetRecvHandler(&UartLite, uart_interrupt_handler, &UartLite);
    
    /* Enable interrupts */
    XUartLite_EnableInterrupt(&UartLite);
    
    return XST_SUCCESS;
}

/* Initialize Interrupts */
static int init_interrupts(void) {
    int Status;
    
    /* Initialize the interrupt controller */
    Status = XScuGic_ConfigIntr(&InterruptController, UART_INT_IRQ_ID,
                                XIL_EXCEPTION_TYPE_INT, XPAR_PS7_SCUGIC_SINGLE_CPU_BASE);
    if (Status != XST_SUCCESS) {
        return XST_FAILURE;
    }
    
    /* Connect the interrupt handler */
    Status = XScuGic_Connect(&InterruptController, UART_INT_IRQ_ID,
                             (Xil_ExceptionHandler)XUartLite_InterruptHandler,
                             &UartLite);
    if (Status != XST_SUCCESS) {
        return XST_FAILURE;
    }
    
    /* Enable the interrupt */
    XScuGic_Enable(&InterruptController, UART_INT_IRQ_ID);
    
    /* Initialize the exception table */
    Xil_ExceptionInit();
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_INT,
                                  (Xil_ExceptionHandler)XScuGic_InterruptHandler,
                                  &InterruptController);
    
    /* Enable exceptions */
    Xil_ExceptionEnable();
    
    return XST_SUCCESS;
}

/* UART Interrupt Handler */
static void uart_interrupt_handler(void *CallBackRef, unsigned int EventData) {
    XUartLite *UartInstancePtr = (XUartLite *)CallBackRef;
    uint32_t ReceivedCount;
    uint8_t Buffer[BUFFER_SIZE];
    
    /* Receive data from UART */
    ReceivedCount = XUartLite_Recv(UartInstancePtr, Buffer, sizeof(Buffer));
    
    if (ReceivedCount > 0) {
        /* Copy received data to buffer */
        if (rx_count + ReceivedCount < BUFFER_SIZE) {
            memcpy(rx_buffer + rx_count, Buffer, ReceivedCount);
            rx_count += ReceivedCount;
        }
    }
}

/* Send Response via UART */
static int send_response(const char *response) {
    int len;
    int bytes_sent;
    
    len = strlen(response);
    bytes_sent = XUartLite_Send(&UartLite, (u8*)response, len);
    
    if (bytes_sent != len) {
        xil_printf("Failed to send response\r\n");
        return -1;
    }
    
    /* Send newline */
    XUartLite_Send(&UartLite, (u8*)"\r\n", 2);
    
    xil_printf("Sent response: %s\r\n", response);
    return 0;
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
