/**
 * @file helpers.c
 * @brief Common helper functions implementation
 * 
 * This file implements common utility functions including bit manipulation,
 * delay, and input handling functions.
 * 
 * @author Devontae Reid    (devdoesit17@gmail.com)
 * @version 1.0.0
 * @date 2025-12-31
 * @copyright Copyright (c) 2025 Devontae Reid
 * @license MIT License
 */

#include <stdint.h>
#include <ctype.h>
#include "xil_printf.h"
#include "helpers.h"

// UART I/O functions from BSP
char inbyte(void);
void outbyte(char c);

/* ============================================================================
 * Bit Manipulation Helper Functions
 * ============================================================================ */

/**
 * @brief Check if a specific bit is set in a value
 * 
 * @param value The value to check
 * @param bit_pos The bit position to check (0-31)
 * @return 1 if bit is set, 0 if bit is clear
 */
int check_bit(uint32_t value, uint8_t bit_pos) {
    if (bit_pos > 31) {
        return 0;  // Invalid bit position
    }
    uint32_t mask = 1U << bit_pos;
    return (value & mask) ? 1 : 0;
}

/**
 * @brief Set a specific bit in a value
 * 
 * @param value The value to modify
 * @param bit_pos The bit position to set (0-31)
 * @return The value with the specified bit set
 */
uint32_t set_bit(uint32_t value, uint8_t bit_pos) {
    if (bit_pos > 31) {
        return value;  // Invalid bit position, return unchanged
    }
    uint32_t mask = 1U << bit_pos;
    return value | mask;
}

/**
 * @brief Clear a specific bit in a value
 * 
 * @param value The value to modify
 * @param bit_pos The bit position to clear (0-31)
 * @return The value with the specified bit cleared
 */
uint32_t clear_bit(uint32_t value, uint8_t bit_pos) {
    if (bit_pos > 31) {
        return value;  // Invalid bit position, return unchanged
    }
    uint32_t mask = 1U << bit_pos;
    return value & ~mask;
}

/* ============================================================================
 * Delay Functions
 * ============================================================================ */

/**
 * @brief Simple microsecond delay function
 * 
 * Implements a simple delay loop. Delay time is approximate and depends on
 * CPU clock frequency.
 * 
 * @param[in] delay Delay time in microseconds (approximate)
 */
void delay_us(uint32_t delay) {
    volatile uint32_t count;
    for (count = 0; count < delay; count++) {
        /* Simple delay loop */
    }
}

/* ============================================================================
 * Input Functions
 * ============================================================================ */

/**
 * @brief Get a single character input (no Enter required)
 * 
 * Reads a single character from UART input without requiring Enter key.
 * This provides immediate response when user presses a key, useful for
 * menu selections.
 * 
 * @return Character that was pressed (lowercase/uppercase as received)
 */
char get_char_input(void) {
    char c;
    c = inbyte();
    return c;
}

/**
 * @brief Get string input from user with echo
 * 
 * Reads a string from UART input with character echo, supports backspace
 * for editing. Input is terminated by Enter key (CR or LF).
 * 
 * @param[out] buffer Buffer to store the input string (must be at least max_len bytes)
 * @param[in] max_len Maximum length of string (buffer size - 1 for null terminator)
 * @param[in] prompt Prompt string to display before input
 */
void get_string_input(char *buffer, int max_len, const char *prompt) {
    int idx = 0;
    char c;
    
    xil_printf("%s: ", prompt);
    
    while (1) {
        c = inbyte();
        
        // Handle Enter key
        if (c == '\r' || c == '\n') {
            buffer[idx] = '\0';
            xil_printf("\r\n");
            break;
        }
        
        // Handle Backspace
        if ((c == '\b' || c == 0x7F) && idx > 0) {
            idx--;
            xil_printf("\b \b");
            continue;
        }
        
        // Accept printable characters
        if (isprint(c) && idx < max_len - 1) {
            buffer[idx++] = c;
            outbyte(c); // echo
        }
        else if (c == '\a') {
            // Handle bell character
            xil_printf("\a");
        }
    }
}

/**
 * @brief Get hexadecimal input from user with echo
 * 
 * Reads hexadecimal value from UART input. Supports optional 0x prefix and
 * hexadecimal digits (0-9, A-F, a-f). Input is terminated by Enter key.
 * 
 * @param[in] prompt Prompt string to display before input
 * @return 32-bit unsigned integer value parsed from hex input
 */
uint32_t get_hex_input(const char *prompt) {
    char input[32];
    int idx = 0;
    uint32_t value = 0;
    char c;
    
    xil_printf("%s: ", prompt);
    
    while (1) {
        c = inbyte();
        
        // Handle Enter key
        if (c == '\r' || c == '\n') {
            input[idx] = '\0';
            xil_printf("\r\n");
            
            // Convert to uint32_t
            extern unsigned long strtoul(const char *nptr, char **endptr, int base);
            value = (uint32_t)strtoul(input, NULL, 16);
            break;
        }
        
        // Handle Backspace
        if ((c == '\b' || c == 0x7F) && idx > 0) {
            idx--;
            xil_printf("\b \b");
            continue;
        }
        
        // Accept only hex digits and 0x prefix chars
        if (isxdigit(c) || c == 'x' || c == 'X') {
            if (idx < (int)(sizeof(input) - 1)) {
                input[idx++] = c;
                outbyte(c); // echo
            }
        }
        else {
            xil_printf("\a"); // beep for invalid
        }
    }
    
    return value;
}

/**
 * @brief Get list selection from user (no Enter required)
 * 
 * Displays a numbered list of options and waits for user to press a number key.
 * Selection is immediate - no Enter key required. Beeps on invalid input.
 * 
 * @param[in] prompt Prompt string to display before options
 * @param[in] options Array of option strings to display (numbered 1-N)
 * @param[in] num_options Number of options in the array (max 9)
 * @return Selected option number (1-based index: 1, 2, 3, ...)
 */
uint32_t get_list_selection(const char *prompt, const char *options[], int num_options) {
    char c;
    uint32_t selection = 0;
    
    xil_printf("%s:\r\n", prompt);
    for (int i = 0; i < num_options; i++) {
        xil_printf("%d. %s\r\n", i + 1, options[i]);
    }
    xil_printf("\r\nEnter choice (1-%d): ", num_options);
    
    while (1) {
        c = get_char_input();
        
        if (c >= '1' && c <= ('0' + num_options)) {
            selection = c - '0';
            xil_printf("%c\r\n", c);
            break;
        }
        else {
            xil_printf("\a"); // beep for invalid
        }
    }
    
    return selection;
}

