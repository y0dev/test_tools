/**
 * @file constants.h
 * @brief Constants and macro definitions for JTAG UART Handler
 * 
 * This header file contains all constant definitions, addresses, offsets,
 * message types, status codes, and configuration values used throughout
 * the application.
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
 */

#ifndef CONSTANTS_H
#define CONSTANTS_H

/* Shared Memory Definitions */
#define SHARED_MEM_BASE 0x10000000    ///< Base address of shared memory region (256MB offset)
#define SHARED_MEM_SIZE 0x1000        ///< Size of shared memory region (4KB)

/* Command Register Definitions */
#define STARTUP_MODE_REG_OFFSET 0x0  ///< Startup mode detection register offset in shared memory
#define CMD_REG_OFFSET 0x4        ///< Command register address
#define RESP_REG_OFFSET 0x8      ///< Response register address

/* Data Area Definitions */
#define DATA_AREA_OFFSET 0x100    ///< Data area offset for storing data
#define DATA_AREA_SIZE 0x400    ///< Data area size for storing data (1KB)

/* Startup Mode Detection */
#define STARTUP_MODE_REG_ADDR (SHARED_MEM_BASE + STARTUP_MODE_REG_OFFSET)  ///< Startup mode detection register absolute address
#define CMD_REG_ADDR (SHARED_MEM_BASE + CMD_REG_OFFSET)  ///< Command register absolute address
#define RESP_REG_ADDR (SHARED_MEM_BASE + RESP_REG_OFFSET)  ///< Response register absolute address

/* Data Area Definitions */
#define DATA_AREA_ADDR (SHARED_MEM_BASE + DATA_AREA_OFFSET)  ///< Data area absolute address


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

/* Boot Mode Register Definition */
#define BOOT_MODE_REG_ADDR 0xFF5E0200  ///< CRL_APB BOOT_MODE register (read-only)

/* Device DNA Register Definitions (PS DNA - 96-bit value in 3 registers) */
#define DNA_0_REG_ADDR 0xFFCC100C  ///< PS DNA register 0 (bits 31:0)
#define DNA_1_REG_ADDR 0xFFCC1010  ///< PS DNA register 1 (bits 63:32)
#define DNA_2_REG_ADDR 0xFFCC1014  ///< PS DNA register 2 (bits 95:64)

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


/**
 * @brief Command register bit field layout
 * 
 * The 32-bit command register is split into two halves:
 * - Upper 16 bits (bits 31-16): TCL script commands
 * - Lower 16 bits (bits 15-0):  App/C application commands
 */

/* App Command Bit Positions (Lower 16 bits: 0-15) */
#define CMD_BIT_APP_INIT            0   ///< Bit 0:  App INIT command
#define CMD_BIT_APP_RUN_APP         1   ///< Bit 1:  App RUN_APP command
#define CMD_BIT_APP_SET_PARAM       2   ///< Bit 2:  App SET_PARAM command
#define CMD_BIT_APP_GET_STATUS      3   ///< Bit 3:  App GET_STATUS command
#define CMD_BIT_APP_CAPTURE_RAM     4   ///< Bit 4:  App CAPTURE_RAM command
#define CMD_BIT_APP_SET_CONFIG      5   ///< Bit 5:  App SET_CONFIG command
#define CMD_BIT_APP_GET_CONFIG      6   ///< Bit 6:  App GET_CONFIG command
#define CMD_BIT_APP_EXIT            7   ///< Bit 7:  App EXIT command
#define CMD_BIT_APP_START_TEST      8   ///< Bit 8:  App START_TEST command
#define CMD_BIT_APP_RUN_TEST        9   ///< Bit 9:  App RUN_TEST command
#define CMD_BIT_APP_GET_TEST_STATUS 10  ///< Bit 10: App GET_TEST_STATUS command
#define CMD_BIT_APP_RESET_PROCESSOR 11  ///< Bit 11: App RESET_PROCESSOR command
#define CMD_BIT_APP_GET_BOOT_MODE   12  ///< Bit 12: App GET_BOOT_MODE command
#define CMD_BIT_APP_GET_DEVICE_DNA  13  ///< Bit 13: App GET_DEVICE_DNA command
#define CMD_BIT_APP_RESERVED_14     14  ///< Bit 14: Reserved for future app commands
#define CMD_BIT_APP_RESERVED_15     15  ///< Bit 15: Reserved for future app commands

/* TCL Script Command Bit Positions (Upper 16 bits: 16-31) */
#define CMD_BIT_TCL_INIT            16  ///< Bit 16: TCL INIT command
#define CMD_BIT_TCL_RUN_APP         17  ///< Bit 17: TCL RUN_APP command
#define CMD_BIT_TCL_SET_PARAM       18  ///< Bit 18: TCL SET_PARAM command
#define CMD_BIT_TCL_GET_STATUS      19  ///< Bit 19: TCL GET_STATUS command
#define CMD_BIT_TCL_CAPTURE_RAM     20  ///< Bit 20: TCL CAPTURE_RAM command
#define CMD_BIT_TCL_SET_CONFIG      21  ///< Bit 21: TCL SET_CONFIG command
#define CMD_BIT_TCL_GET_CONFIG      22  ///< Bit 22: TCL GET_CONFIG command
#define CMD_BIT_TCL_EXIT            23  ///< Bit 23: TCL EXIT command
#define CMD_BIT_TCL_START_TEST      24  ///< Bit 24: TCL START_TEST command
#define CMD_BIT_TCL_RUN_TEST        25  ///< Bit 25: TCL RUN_TEST command
#define CMD_BIT_TCL_GET_TEST_STATUS 26  ///< Bit 26: TCL GET_TEST_STATUS command
#define CMD_BIT_TCL_RESET_PROCESSOR 27  ///< Bit 27: TCL RESET_PROCESSOR command
#define CMD_BIT_TCL_GET_BOOT_MODE   28  ///< Bit 28: TCL GET_BOOT_MODE command
#define CMD_BIT_TCL_GET_DEVICE_DNA  29  ///< Bit 29: TCL GET_DEVICE_DNA command
#define CMD_BIT_TCL_RESERVED_30     30  ///< Bit 30: Reserved for future TCL commands
#define CMD_BIT_TCL_RESERVED_31     31  ///< Bit 31: Reserved for future TCL commands

/* Legacy aliases for backward compatibility (use app command bits) */
#define CMD_BIT_INIT            CMD_BIT_APP_INIT
#define CMD_BIT_RUN_APP         CMD_BIT_APP_RUN_APP
#define CMD_BIT_SET_PARAM       CMD_BIT_APP_SET_PARAM
#define CMD_BIT_GET_STATUS      CMD_BIT_APP_GET_STATUS
#define CMD_BIT_CAPTURE_RAM     CMD_BIT_APP_CAPTURE_RAM
#define CMD_BIT_SET_CONFIG      CMD_BIT_APP_SET_CONFIG
#define CMD_BIT_GET_CONFIG      CMD_BIT_APP_GET_CONFIG
#define CMD_BIT_EXIT            CMD_BIT_APP_EXIT
#define CMD_BIT_START_TEST      CMD_BIT_APP_START_TEST
#define CMD_BIT_RUN_TEST        CMD_BIT_APP_RUN_TEST
#define CMD_BIT_GET_TEST_STATUS CMD_BIT_APP_GET_TEST_STATUS
#define CMD_BIT_RESET_PROCESSOR CMD_BIT_APP_RESET_PROCESSOR
#define CMD_BIT_GET_BOOT_MODE   CMD_BIT_APP_GET_BOOT_MODE
#define CMD_BIT_GET_DEVICE_DNA  CMD_BIT_APP_GET_DEVICE_DNA

#endif /* CONSTANTS_H */

