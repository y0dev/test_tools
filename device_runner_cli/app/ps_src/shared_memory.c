/**
 * @file shared_memory.c
 * @brief Shared memory communication functions implementation
 * 
 * This file implements shared memory communication functions including
 * initialization, read/write operations, message processing, and all
 * shared memory command handlers.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "xil_printf.h"
#include "xil_io.h"

#include "include/constants.h"
#include "include/types.h"
#include "helpers.h"
#include "shared_memory.h"
#include "test_mode.h"

/* External global variables */
extern config_t config;
extern volatile int running;
extern volatile int test_mode;
extern test_config_t test_config;
extern test_case_t test_cases[];

/* Forward declarations for handler functions */
// Exported functions (declared in shared_memory.h) - no forward declaration needed
// Internal functions
static int handle_shared_memory_set_config(const char *data);
static int handle_shared_memory_get_config(const char *config_name, char *response, int max_len);
static int handle_shared_memory_reset_processor(void);
static int handle_shared_memory_get_boot_mode(char *response, int max_len);
static int handle_shared_memory_get_device_dna(char *response, int max_len);

/* ============================================================================
 * Shared Memory Basic Operations
 * ============================================================================ */

/**
 * @brief Initialize shared memory region
 * 
 * Clears and initializes the shared memory region at SHARED_MEM_BASE (0x10000000).
 * Sets all memory locations to zero to prepare for communication.
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

/* ============================================================================
 * Shared Memory Message Processing
 * ============================================================================ */

/**
 * @brief Process shared memory message
 * 
 * Checks for incoming messages in shared memory, reads the command register,
 * and dispatches to the appropriate message handler function.
 * 
 * @return 0 if no message processed, 1 if message was handled
 */
int process_shared_memory_message(void) {
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

/* ============================================================================
 * Shared Memory Command Handlers
 * ============================================================================ */

/**
 * @brief Handle MSG_TYPE_INIT message
 * 
 * Processes initialization message from TCL script. Initializes shared memory
 * and responds with success status.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by uart_script_mode.c
 */
int handle_shared_memory_init(void) {
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

/**
 * @brief Handle MSG_TYPE_RUN_APP message
 * 
 * Processes run application message. Executes the application with current
 * configuration parameters and responds with completion status.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by uart_script_mode.c
 */
int handle_shared_memory_run_app(void) {
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

/**
 * @brief Handle MSG_TYPE_SET_PARAM message
 * 
 * Processes set parameter message. Parses parameter data and updates
 * configuration accordingly.
 * 
 * @param[in] data Parameter data string from shared memory
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by other modules
 */
int handle_shared_memory_set_param(const char *data) {
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

/**
 * @brief Handle MSG_TYPE_GET_STATUS message
 * 
 * Processes get status message. Reads current status and configuration,
 * formats response, and writes to shared memory.
 * 
 * @param[out] response Buffer to store formatted status response
 * @param[in] max_len Maximum length of response buffer
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by other modules
 */
int handle_shared_memory_get_status(char *response, int max_len) {
    xil_printf("Handling shared memory GET_STATUS command\r\n");
    
    snprintf(response, max_len,
             "Device: %s, Base: 0x%08X, Mode: %u, Timeout: %u, Debug: %u",
             config.device_name, config.base_address, config.operation_mode,
             config.timeout_value, config.debug_level);
    
    return 1;
}

/**
 * @brief Handle MSG_TYPE_CAPTURE_RAM message
 * 
 * Processes RAM capture message. Performs memory capture operation and
 * responds with completion status.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by other modules
 */
int handle_shared_memory_capture_ram(void) {
    xil_printf("Handling shared memory CAPTURE_RAM command\r\n");
    xil_printf("Base Address: 0x%08X\r\n", config.base_address);
    xil_printf("Timeout: %u ms\r\n", config.timeout_value);
    
    // Simulate RAM capture
    delay_us(500000); // 0.5 second delay
    
    xil_printf("RAM capture completed\r\n");
    return 1;
}

/**
 * @brief Handle MSG_TYPE_SET_CONFIG message
 * 
 * Processes set configuration message. Parses configuration data and updates
 * configuration structure.
 * 
 * @param[in] data Configuration data string from shared memory
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
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

/**
 * @brief Handle MSG_TYPE_EXIT message
 * 
 * Processes exit message. Sets running flag to 0 to exit application loop.
 * 
 * @return MSG_STATUS_SUCCESS
 * 
 * @note Exported for use by uart_script_mode.c and interactive_mode.c
 */
int handle_shared_memory_exit(void) {
    xil_printf("Handling shared memory EXIT command\r\n");
    running = 0;
    return 1;
}

/**
 * @brief Handle MSG_TYPE_RESET_PROCESSOR message
 * 
 * Processes reset processor message. Calls reset_processor() from test_mode.c
 * to perform processor reset operation.
 * 
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 */
static int handle_shared_memory_reset_processor(void) {
    xil_printf("Handling shared memory RESET_PROCESSOR command\r\n");
    
    // Reset configuration to defaults
    strcpy(config.device_name, "Default Device");
    config.base_address = 0x43C00000;
    config.operation_mode = 1;
    config.timeout_value = 5000;
    config.debug_level = 1;
    
    // Reset test state if in test mode
    if (test_mode && test_config.number_of_tests > 0) {
        test_config.current_test = 0;
        test_config.test_in_progress = 0;
        test_config.test_requires_reset = 0;
    }
    
    // Small delay to simulate reset
    delay_us(100000); // 100ms delay
    
    xil_printf("Processor reset completed\r\n");
    return 1;
}

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
static int handle_shared_memory_get_boot_mode(char *response, int max_len) {
    xil_printf("Handling shared memory GET_BOOT_MODE command\r\n");
    
    // Read boot mode register (read-only register at 0xFF5E0200)
    uint32_t boot_mode_reg = Xil_In32(BOOT_MODE_REG_ADDR);
    
    // Extract boot mode bits (typically bits [3:0] for Zynq UltraScale+)
    uint32_t boot_mode = boot_mode_reg & 0x0F;
    
    // Decode boot mode to human-readable string
    const char *boot_mode_str;
    switch (boot_mode) {
        case 0x0: boot_mode_str = "JTAG"; break;
        case 0x1: boot_mode_str = "QSPI24"; break;
        case 0x2: boot_mode_str = "QSPI32"; break;
        case 0x3: boot_mode_str = "SD0"; break;
        case 0x4: boot_mode_str = "SD1"; break;
        case 0x5: boot_mode_str = "eMMC"; break;
        case 0x6: boot_mode_str = "NAND"; break;
        case 0x7: boot_mode_str = "USB"; break;
        default: boot_mode_str = "UNKNOWN"; break;
    }
    
    xil_printf("Boot Mode Register: 0x%08X\r\n", boot_mode_reg);
    xil_printf("Boot Mode: 0x%02X (%s)\r\n", boot_mode, boot_mode_str);
    
    // Format response string
    snprintf(response, max_len,
            "Boot Mode Register: 0x%08X, Boot Mode: 0x%02X (%s)",
            boot_mode_reg, boot_mode, boot_mode_str);
    
    return 1;
}

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

