/**
 * @file test_mode.h
 * @brief Test mode functions
 * 
 * This header file contains declarations for test mode operations,
 * including test configuration and execution.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#ifndef TEST_MODE_H
#define TEST_MODE_H

void run_test_mode(void);
void initialize_test_config(void);

/* Test command handlers - exported for use by shared_memory.c */
int handle_shared_memory_start_test(const char *data);
int handle_shared_memory_run_test(const char *data);
int handle_shared_memory_get_test_status(char *response, int max_len);

#endif /* TEST_MODE_H */

