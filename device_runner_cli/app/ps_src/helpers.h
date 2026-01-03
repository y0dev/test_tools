/**
 * @file helpers.h
 * @brief Common helper functions for JTAG UART Handler
 * 
 * This header file contains declarations for common utility functions used
 * throughout the application, including bit manipulation, delay, and input
 * handling functions.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 * 
 * History:
 * 2025-12-31 - Initial version
 */

#ifndef HELPERS_H
#define HELPERS_H

#include <stdint.h>

/* Bit Manipulation Functions */
int check_bit(uint32_t value, uint8_t bit_pos);
uint32_t set_bit(uint32_t value, uint8_t bit_pos);
uint32_t clear_bit(uint32_t value, uint8_t bit_pos);

/* Delay Functions */
void delay_us(uint32_t delay);

/* Input Functions */
char get_char_input(void);
void get_string_input(char *buffer, int max_len, const char *prompt);
uint32_t get_hex_input(const char *prompt);
uint32_t get_list_selection(const char *prompt, const char *options[], int num_options);

#endif /* HELPERS_H */

