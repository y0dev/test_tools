/**
 * @file types.h
 * @brief Type definitions and data structures for JTAG UART Handler
 * 
 * This header file contains all type definitions, structures, and enumerations
 * used throughout the JTAG UART Handler application.
 * 
 * @author Device Runner CLI
 * @version 2.0.0
 * @date 2024
 */

#ifndef TYPES_H
#define TYPES_H

#include <stdint.h>

/* Buffer and Command Definitions */
#define BUFFER_SIZE 1024        ///< Size of general purpose buffers
#define MAX_COMMAND_LEN 256     ///< Maximum length of a command string
#define MAX_RESPONSE_LEN 512    ///< Maximum length of a response string
#define MAX_STRING_LEN 64       ///< Maximum length of configuration strings
#define MAX_TEST_CASES 32       ///< Maximum number of test cases supported

/**
 * @brief Configuration structure for device settings
 * 
 * This structure stores configuration parameters for the device and application.
 * It includes device name, base address, operation mode, timeout values, and
 * debug level settings.
 */
typedef struct {
    char device_name[MAX_STRING_LEN];   ///< Device name string (max 64 chars)
    uint32_t base_address;              ///< Base address for device registers (e.g., 0x43C00000)
    uint32_t operation_mode;            ///< Operation mode: 1=Short, 2=Medium, 3=Long
    uint32_t timeout_value;             ///< Timeout value in milliseconds
    uint32_t debug_level;               ///< Debug level (0=off, 1=minimal, 2=verbose)
} config_t;

/**
 * @brief Test configuration structure
 * 
 * This structure maintains the state and configuration of test execution.
 * It tracks test statistics, current test progress, and test parameters.
 */
typedef struct {
    uint32_t number_of_tests;       ///< Total number of tests to run
    uint32_t current_test;          ///< Index of currently executing test (0-based)
    uint32_t test_timeout;          ///< Timeout per test in milliseconds
    uint32_t test_retries;          ///< Number of retry attempts for failed tests
    uint32_t tests_passed;          ///< Count of successfully passed tests
    uint32_t tests_failed;          ///< Count of failed tests
    uint32_t test_in_progress;      ///< Flag: 1 if test is running, 0 if idle
    uint32_t test_requires_reset;   ///< Flag: 1 if test requires processor reset
} test_config_t;

/**
 * @brief Test case structure
 * 
 * This structure represents a single test case with its name, description,
 * requirements, and execution status.
 */
typedef struct {
    char name[64];                  ///< Test case name (max 64 chars)
    char description[128];          ///< Test case description (max 128 chars)
    uint32_t requires_reset;        ///< Flag: 1 if test requires reset before execution
    uint32_t status;                ///< Test status: 0=not run, 1=passed, 2=failed
} test_case_t;

#endif /* TYPES_H */

