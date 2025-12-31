/**
 * @file constants.h
 * @brief Constants and macro definitions for JTAG UART Handler
 * 
 * This header file contains all constant definitions, addresses, offsets,
 * message types, status codes, and configuration values used throughout
 * the application.
 * 
 * @author Device Runner CLI
 * @version 2.0.0
 * @date 2024
 */

#ifndef CONSTANTS_H
#define CONSTANTS_H

/* Command Register Definitions */
#define CMD_REG_OFFSET 0x0        ///< Command register address (placeholder)
#define RESP_REG_OFFSET 0x4      ///< Response register address (placeholder)

/* Startup Mode Detection */
#define STARTUP_MODE_REG_OFFSET 0x8  ///< Startup mode detection register address (placeholder)

/* Data Area Definitions */
#define DATA_AREA_OFFSET 0x100    ///< Data area offset for storing data
#define DATA_AREA_SIZE 0x200    ///< Data area size for storing data (512 bytes)


/* Magic Number Definitions */
#define MAGIC_NUMBER 0xDEADBEEF  ///< Magic number for shared memory communication

/**
 * @brief Startup mode enumeration values
 * 
 * Defines different startup modes for the application based on how it's launched.
 */
#define MODE_JTAG_INTERACTIVE 0x00000001  ///< Interactive mode via JTAG UART
#define MODE_JTAG_SCRIPT      0x00000002  ///< Script mode via JTAG UART
#define MODE_UART_INTERACTIVE 0x00000003  ///< Interactive mode via UART
#define MODE_UART_SCRIPT      0x00000004  ///< Script mode via UART

/**
 * @brief Application operation modes
 */
#define MODE_INTERACTIVE 0    ///< Interactive menu-driven mode
#define MODE_BACKGROUND  1    ///< Background command processing mode

/* Shared Memory Definitions */
#define SHARED_MEM_BASE 0x10000000    ///< Base address of shared memory region (256MB offset)
#define SHARED_MEM_SIZE 0x1000        ///< Size of shared memory region (4KB)

/* Boot Mode Register Definition */
#define BOOT_MODE_REG_ADDR 0xFF5E0200  ///< CRL_APB BOOT_MODE register (read-only)

/* Device DNA Register Definitions (PS DNA - 96-bit value in 3 registers) */
#define DNA_0_REG_ADDR 0xFFCC100C  ///< PS DNA register 0 (bits 31:0)
#define DNA_1_REG_ADDR 0xFFCC1010  ///< PS DNA register 1 (bits 63:32)
#define DNA_2_REG_ADDR 0xFFCC1014  ///< PS DNA register 2 (bits 95:64)

/* Register offsets in shared memory */
#define CMD_REG_OFFSET 0x0      ///< Command register offset (bit field)
#define RESP_REG_OFFSET 0x4     ///< Response register offset
#define DATA_AREA_OFFSET 0x8    ///< Data area offset for command parameters

/**
 * @brief Message type definitions
 * 
 * Message types used in shared memory communication protocol.
 */
#define MSG_TYPE_INIT            1   ///< Initialize application message
#define MSG_TYPE_RUN_APP         2   ///< Run application message
#define MSG_TYPE_SET_PARAM       3   ///< Set parameter message
#define MSG_TYPE_GET_STATUS      4   ///< Get status message
#define MSG_TYPE_CAPTURE_RAM     5   ///< Capture RAM message
#define MSG_TYPE_SET_CONFIG      6   ///< Set configuration message
#define MSG_TYPE_GET_CONFIG      7   ///< Get configuration message
#define MSG_TYPE_EXIT            8   ///< Exit application message
#define MSG_TYPE_RESPONSE        9   ///< Response message
#define MSG_TYPE_ERROR          10   ///< Error message
#define MSG_TYPE_START_TEST     11   ///< Start test message
#define MSG_TYPE_RUN_TEST       12   ///< Run test message
#define MSG_TYPE_GET_TEST_STATUS 13  ///< Get test status message
#define MSG_TYPE_RESET_PROCESSOR 14  ///< Reset processor message
#define MSG_TYPE_GET_BOOT_MODE  15   ///< Get boot mode message
#define MSG_TYPE_GET_DEVICE_DNA 16   ///< Get device DNA message

/**
 * @brief Status code definitions
 * 
 * Status codes returned by message processing functions.
 */
#define MSG_STATUS_SUCCESS  0   ///< Operation completed successfully
#define MSG_STATUS_ERROR    1   ///< Operation failed with error
#define MSG_STATUS_BUSY     2   ///< Operation in progress, not ready
#define MSG_STATUS_TIMEOUT  3   ///< Operation timed out
#define MSG_STATUS_INVALID  4   ///< Invalid request or parameter

/**
 * @brief Response register values
 * 
 * Bit flags used in the response register for different response types.
 */
#define RESP_SUCCESS 0x00000001  ///< Success response flag
#define RESP_ERROR   0x00000002  ///< Error response flag
#define RESP_BUSY    0x00000004  ///< Busy response flag
#define RESP_READY   0x00000008  ///< Ready response flag

/**
 * @brief Configuration parameter types
 * 
 * Types of configuration parameters that can be set.
 */
#define CONFIG_TYPE_STRING 1   ///< String type configuration parameter
#define CONFIG_TYPE_HEX    2   ///< Hexadecimal type configuration parameter
#define CONFIG_TYPE_LIST   3   ///< List/selection type configuration parameter

#endif /* CONSTANTS_H */

