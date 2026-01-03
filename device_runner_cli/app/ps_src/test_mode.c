/**
 * @file test_mode.c
 * @brief Test mode implementation
 * 
 * This file implements test mode functionality including test configuration,
 * test execution, and test status reporting. Test mode processes register-based
 * commands via shared memory with test-specific functionality.
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
extern volatile int startup_mode;
extern volatile int test_mode;
extern test_config_t test_config;
extern test_case_t test_cases[];

/* Forward declarations */
static void reset_processor(void);

/* ============================================================================
 * Test Mode Main Loop
 * ============================================================================ */

/**
 * @brief Run test mode main loop
 * 
 * Main loop for test mode. Continuously processes shared memory messages
 * with test-specific command handling.
 */
void run_test_mode(void) {
    xil_printf("Test Mode: Processing register-based test commands\r\n");
    xil_printf("Commands sent via shared memory registers\r\n");
    xil_printf("\r\n");
    
    while (running) {
        // Process shared memory messages (TCL commands via upper 16 bits)
        // Test-specific commands are handled by shared_memory.c which calls
        // test mode handlers for START_TEST, RUN_TEST, GET_TEST_STATUS
        process_shared_memory_message();
        
        // Small delay to prevent excessive CPU usage
        delay_us(10000); // 10ms polling interval
    }
}

/* ============================================================================
 * Test Configuration and Initialization
 * ============================================================================ */

/**
 * @brief Initialize test configuration structure
 * 
 * Initializes the test_config structure with default values for test execution.
 */
void initialize_test_config(void) {
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

/**
 * @brief Reset the processor
 * 
 * Performs a software reset of the processor. Resets configuration and test state.
 */
static void reset_processor(void) {
    xil_printf("Resetting processor...\r\n");
    
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

/* ============================================================================
 * Test Command Handlers
 * ============================================================================ */

/**
 * @brief Handle MSG_TYPE_START_TEST message
 * 
 * Processes start test message. Initializes test configuration and prepares
 * for test execution.
 * 
 * @param[in] data Test initialization data string
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by shared_memory.c
 */
int handle_shared_memory_start_test(const char *data) {
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

/**
 * @brief Handle MSG_TYPE_RUN_TEST message
 * 
 * Processes run test message. Executes the specified test case and updates
 * test status.
 * 
 * @param[in] data Test execution data string
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by shared_memory.c
 */
int handle_shared_memory_run_test(const char *data) {
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
            
            if (test_passed) {
                test_cases[test_idx].status = 1; // Passed
                test_config.tests_passed++;
                status_str = "PASSED";
            } else {
                test_cases[test_idx].status = 2; // Failed
                test_config.tests_failed++;
                status_str = "FAILED";
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

/**
 * @brief Handle MSG_TYPE_GET_TEST_STATUS message
 * 
 * Processes get test status message. Reads current test statistics and
 * status, formats response.
 * 
 * @param[out] response Buffer to store test status response
 * @param[in] max_len Maximum length of response buffer
 * @return MSG_STATUS_SUCCESS on success, MSG_STATUS_ERROR on failure
 * 
 * @note Exported for use by shared_memory.c
 */
int handle_shared_memory_get_test_status(char *response, int max_len) {
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

