/**
 * @file shared_memory.h
 * @brief Shared memory communication functions
 * 
 * This header file contains declarations for shared memory communication
 * functions, including initialization, read/write operations, and message
 * processing.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#ifndef SHARED_MEMORY_H
#define SHARED_MEMORY_H

#include <stdint.h>

/* Shared Memory Functions */
void init_shared_memory(void);
int read_data_area(char *buffer, int max_len);
int write_data_area(const char *data);
int process_shared_memory_message(void);

/* Shared memory command handlers (for use by other modules) */
int handle_shared_memory_init(void);
int handle_shared_memory_run_app(void);
int handle_shared_memory_exit(void);
int handle_shared_memory_set_param(const char *data);
int handle_shared_memory_get_status(char *response, int max_len);
int handle_shared_memory_capture_ram(void);

#endif /* SHARED_MEMORY_H */

