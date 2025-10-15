#!/usr/bin/env python3
"""
Automated Serial Setup Engine
This module provides automated serial communication with menu-driven configuration steps.
"""

import serial
import time
import json
import logging
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

class StepType(Enum):
    """Types of automation steps."""
    WAIT_FOR_PROMPT = "wait_for_prompt"
    SEND_COMMAND = "send_command"
    SEND_INPUT = "send_input"
    MENU_INTERACTION = "menu_interaction"
    COMPLETION = "completion"
    ERROR_HANDLER = "error_handler"

class AutomationStatus(Enum):
    """Status of automation execution."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    STOPPED = "stopped"

class AutomatedSerialSetup:
    """
    Automated serial setup engine with menu-driven configuration.
    
    This class handles automated serial communication based on predefined steps
    and can interact with menu-driven interfaces.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the automated serial setup.
        
        Args:
            config: Configuration dictionary containing automation steps and settings
        """
        self.config = config
        self.automation_config = config.get('automation', {})
        self.steps = config.get('steps', [])
        self.serial_config = config.get('serial', {})
        
        # Setup logging
        self.logger = logging.getLogger('automated_serial')
        self._setup_logging()
        
        # Serial connection
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
        
        # Automation state
        self.current_step_id: Optional[str] = None
        self.step_history: List[Dict[str, Any]] = []
        self.status = AutomationStatus.STOPPED
        self.running = False
        self.paused = False
        
        # Step execution tracking
        self.step_results: Dict[str, Any] = {}
        self.retry_counts: Dict[str, int] = {}
        
        # Callbacks
        self.step_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        # Data parser for logging
        self.data_parser = None
        if config.get('data_parsing', {}).get('enabled', False):
            from libs.serial_logger import SerialDataParser
            self.data_parser = SerialDataParser(config)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging_config = self.config.get('logging', {})
        
        # Create log directory
        log_dir = Path(logging_config.get('log_directory', './output/automated_serial_logs'))
        if logging_config.get('use_date_hierarchy', False):
            date_format = logging_config.get('date_format', '%Y/%m_%b/%m_%d')
            date_path = datetime.now().strftime(date_format)
            log_dir = log_dir / date_path
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate log file name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"automated_serial_{timestamp}.txt"
        self.log_file_path = log_dir / log_filename
        
        # Setup file handler
        file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def connect(self) -> bool:
        """
        Connect to the serial device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to {self.serial_config['port']} at {self.serial_config['baud']} baud")
            
            self.serial_conn = serial.Serial(
                port=self.serial_config['port'],
                baudrate=self.serial_config['baud'],
                timeout=self.serial_config.get('timeout', 1.0),
                parity=self.serial_config.get('parity', 'N'),
                stopbits=self.serial_config.get('stopbits', 1),
                bytesize=self.serial_config.get('bytesize', 8)
            )
            
            self.connected = True
            self.logger.info("Serial connection established successfully")
            self._log_structured("connection_established", port=self.serial_config['port'], baud=self.serial_config['baud'])
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to serial device: {e}")
            self._log_structured("connection_failed", error=str(e))
            return False
    
    def disconnect(self):
        """Disconnect from the serial device."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.connected = False
            self.logger.info("Serial connection closed")
            self._log_structured("connection_closed")
    
    def _log_structured(self, event_type: str, **kwargs):
        """
        Log structured data for parsing.
        
        Args:
            event_type: Type of event
            kwargs: Additional data to log
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {event_type}"
        
        for key, value in kwargs.items():
            log_entry += f" {key}={value}"
        
        self.logger.info(log_entry)
        print(log_entry)
    
    def _send_command(self, command: str) -> bool:
        """
        Send a command to the serial device.
        
        Args:
            command: Command to send
            
        Returns:
            bool: True if command sent successfully
        """
        try:
            if not self.connected or not self.serial_conn:
                return False
            
            self.logger.info(f"Sending command: {command}")
            self._log_structured("command_sent", command=command)
            
            command_bytes = (command + '\r\n').encode('utf-8')
            self.serial_conn.write(command_bytes)
            self.serial_conn.flush()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send command '{command}': {e}")
            self._log_structured("command_failed", command=command, error=str(e))
            return False
    
    def _read_response(self, timeout: float = 5.0) -> str:
        """
        Read response from the serial device.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            str: Response received
        """
        try:
            if not self.connected or not self.serial_conn:
                return ""
            
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                    response += data
                    
                    # Check if we have a complete response
                    if '\n' in response or '\r' in response:
                        break
                
                time.sleep(0.1)
            
            response = response.strip()
            if response:
                self.logger.info(f"Received response: {response}")
                self._log_structured("response_received", response=response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to read response: {e}")
            self._log_structured("response_failed", error=str(e))
            return ""
    
    def _wait_for_pattern(self, pattern: str, timeout: float = 5.0) -> bool:
        """
        Wait for a specific pattern in the response.
        
        Args:
            pattern: Regex pattern to wait for
            timeout: Timeout in seconds
            
        Returns:
            bool: True if pattern found, False if timeout
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                response = self._read_response(0.5)
                if response and re.search(pattern, response, re.IGNORECASE):
                    self.logger.info(f"Pattern '{pattern}' found in response")
                    return True
                time.sleep(0.1)
            
            self.logger.warning(f"Pattern '{pattern}' not found within {timeout}s timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for pattern '{pattern}': {e}")
            return False
    
    def _execute_step(self, step: Dict[str, Any]) -> bool:
        """
        Execute a single automation step.
        
        Args:
            step: Step configuration dictionary
            
        Returns:
            bool: True if step executed successfully
        """
        step_id = step.get('id', 'unknown')
        step_name = step.get('name', 'Unknown Step')
        step_type = step.get('type', '')
        
        self.logger.info(f"Executing step: {step_id} - {step_name}")
        self._log_structured("step_start", step_id=step_id, step_name=step_name, step_type=step_type)
        
        try:
            if step_type == StepType.WAIT_FOR_PROMPT.value:
                return self._execute_wait_for_prompt(step)
            elif step_type == StepType.SEND_COMMAND.value:
                return self._execute_send_command(step)
            elif step_type == StepType.SEND_INPUT.value:
                return self._execute_send_input(step)
            elif step_type == StepType.MENU_INTERACTION.value:
                return self._execute_menu_interaction(step)
            elif step_type == StepType.COMPLETION.value:
                return self._execute_completion(step)
            elif step_type == StepType.ERROR_HANDLER.value:
                return self._execute_error_handler(step)
            else:
                self.logger.error(f"Unknown step type: {step_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing step {step_id}: {e}")
            self._log_structured("step_error", step_id=step_id, error=str(e))
            return False
    
    def _execute_wait_for_prompt(self, step: Dict[str, Any]) -> bool:
        """Execute wait for prompt step."""
        pattern = step.get('prompt_pattern', '>')
        timeout = step.get('timeout', 5.0)
        
        self.logger.info(f"Waiting for prompt pattern: {pattern}")
        success = self._wait_for_pattern(pattern, timeout)
        
        if success:
            self._log_structured("prompt_found", pattern=pattern)
        else:
            self._log_structured("prompt_timeout", pattern=pattern, timeout=timeout)
        
        return success
    
    def _execute_send_command(self, step: Dict[str, Any]) -> bool:
        """Execute send command step."""
        command = step.get('command', '')
        wait_for_response = step.get('wait_for_response', False)
        response_pattern = step.get('response_pattern', '')
        timeout = step.get('timeout', 5.0)
        
        if not self._send_command(command):
            return False
        
        if wait_for_response:
            if response_pattern:
                return self._wait_for_pattern(response_pattern, timeout)
            else:
                response = self._read_response(timeout)
                return bool(response)
        
        return True
    
    def _execute_send_input(self, step: Dict[str, Any]) -> bool:
        """Execute send input step."""
        input_value = step.get('input_value', '')
        wait_for_response = step.get('wait_for_response', False)
        response_pattern = step.get('response_pattern', '')
        timeout = step.get('timeout', 5.0)
        
        self.logger.info(f"Sending input: {input_value}")
        self._log_structured("input_sent", input_value=input_value)
        
        if not self._send_command(input_value):
            return False
        
        if wait_for_response:
            if response_pattern:
                return self._wait_for_pattern(response_pattern, timeout)
            else:
                response = self._read_response(timeout)
                return bool(response)
        
        return True
    
    def _execute_menu_interaction(self, step: Dict[str, Any]) -> bool:
        """Execute menu interaction step."""
        menu_options = step.get('menu_options', [])
        selection = step.get('selection', '')
        wait_for_response = step.get('wait_for_response', False)
        response_pattern = step.get('response_pattern', '')
        timeout = step.get('timeout', 5.0)
        
        self.logger.info(f"Menu interaction - selecting: {selection}")
        self._log_structured("menu_interaction", selection=selection, menu_options=menu_options)
        
        # Display menu options
        if menu_options:
            self.logger.info("Available menu options:")
            for option in menu_options:
                self.logger.info(f"  {option}")
        
        # Send selection
        if not self._send_command(selection):
            return False
        
        if wait_for_response:
            if response_pattern:
                return self._wait_for_pattern(response_pattern, timeout)
            else:
                response = self._read_response(timeout)
                return bool(response)
        
        return True
    
    def _execute_completion(self, step: Dict[str, Any]) -> bool:
        """Execute completion step."""
        message = step.get('message', 'Automation completed successfully!')
        
        self.logger.info(message)
        self._log_structured("automation_completed", message=message)
        
        self.status = AutomationStatus.COMPLETED
        self.running = False
        
        if self.completion_callback:
            self.completion_callback(self.step_results)
        
        return True
    
    def _execute_error_handler(self, step: Dict[str, Any]) -> bool:
        """Execute error handler step."""
        retry_steps = step.get('retry_steps', [])
        max_retries = step.get('max_retries', 2)
        fallback_action = step.get('fallback_action', 'stop')
        
        self.logger.error("Error handler activated")
        self._log_structured("error_handler_activated", retry_steps=retry_steps, max_retries=max_retries)
        
        # Implement retry logic
        for retry_step_id in retry_steps:
            if self.retry_counts.get(retry_step_id, 0) < max_retries:
                self.retry_counts[retry_step_id] = self.retry_counts.get(retry_step_id, 0) + 1
                self.logger.info(f"Retrying step: {retry_step_id}")
                return self.run_from_step(retry_step_id)
        
        # If all retries exhausted, handle fallback
        if fallback_action == 'stop':
            self.status = AutomationStatus.FAILED
            self.running = False
            if self.error_callback:
                self.error_callback("All retry attempts exhausted")
        
        return False
    
    def run_from_step(self, step_id: str) -> bool:
        """
        Run automation starting from a specific step.
        
        Args:
            step_id: ID of the step to start from
            
        Returns:
            bool: True if automation completed successfully
        """
        if not self.connected:
            if not self.connect():
                return False
        
        self.running = True
        self.status = AutomationStatus.RUNNING
        self.current_step_id = step_id
        
        self.logger.info(f"Starting automation from step: {step_id}")
        self._log_structured("automation_started", start_step=step_id)
        
        try:
            while self.running and not self.paused:
                # Find current step
                current_step = None
                for step in self.steps:
                    if step.get('id') == self.current_step_id:
                        current_step = step
                        break
                
                if not current_step:
                    self.logger.error(f"Step not found: {self.current_step_id}")
                    self.status = AutomationStatus.FAILED
                    return False
                
                # Execute step
                step_success = self._execute_step(current_step)
                
                # Record step result
                step_result = {
                    'step_id': self.current_step_id,
                    'step_name': current_step.get('name', ''),
                    'success': step_success,
                    'timestamp': datetime.now().isoformat(),
                    'retry_count': self.retry_counts.get(self.current_step_id, 0)
                }
                self.step_history.append(step_result)
                self.step_results[self.current_step_id] = step_result
                
                # Call step callback
                if self.step_callback:
                    self.step_callback(step_result)
                
                # Determine next step
                if step_success:
                    next_step_id = current_step.get('on_success')
                else:
                    next_step_id = current_step.get('on_failure')
                
                if next_step_id == 'completion':
                    self.status = AutomationStatus.COMPLETED
                    self.running = False
                    break
                elif next_step_id:
                    self.current_step_id = next_step_id
                else:
                    self.logger.error(f"No next step defined for: {self.current_step_id}")
                    self.status = AutomationStatus.FAILED
                    return False
                
                # Wait between steps
                wait_time = self.automation_config.get('wait_between_steps', 0.5)
                if wait_time > 0:
                    time.sleep(wait_time)
            
            return self.status == AutomationStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Error during automation: {e}")
            self.status = AutomationStatus.FAILED
            return False
    
    def run(self) -> bool:
        """
        Run the complete automation sequence.
        
        Returns:
            bool: True if automation completed successfully
        """
        return self.run_from_step(self.steps[0].get('id') if self.steps else 'step_1')
    
    def pause(self):
        """Pause the automation."""
        self.paused = True
        self.logger.info("Automation paused")
        self._log_structured("automation_paused")
    
    def resume(self):
        """Resume the automation."""
        self.paused = False
        self.logger.info("Automation resumed")
        self._log_structured("automation_resumed")
    
    def stop(self):
        """Stop the automation."""
        self.running = False
        self.status = AutomationStatus.STOPPED
        self.logger.info("Automation stopped")
        self._log_structured("automation_stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current automation status.
        
        Returns:
            Dict containing status information
        """
        return {
            'status': self.status.value,
            'current_step': self.current_step_id,
            'running': self.running,
            'paused': self.paused,
            'connected': self.connected,
            'steps_completed': len(self.step_history),
            'total_steps': len(self.steps),
            'step_results': self.step_results
        }
    
    def set_callbacks(self, step_callback: Optional[Callable] = None,
                     completion_callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None):
        """
        Set callback functions for automation events.
        
        Args:
            step_callback: Called after each step execution
            completion_callback: Called when automation completes
            error_callback: Called when automation fails
        """
        self.step_callback = step_callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback

def load_automation_config(config_file: str) -> Dict[str, Any]:
    """
    Load automation configuration from file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dict containing configuration
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration file {config_file}: {e}")
        return {}

if __name__ == "__main__":
    # Example usage
    config = load_automation_config("config/automated_serial_setup_config.json")
    
    if config:
        automation = AutomatedSerialSetup(config)
        
        # Set up callbacks
        def on_step_complete(step_result):
            print(f"Step completed: {step_result['step_name']} - {'Success' if step_result['success'] else 'Failed'}")
        
        def on_completion(results):
            print("Automation completed successfully!")
            print(f"Completed {len(results)} steps")
        
        def on_error(error_message):
            print(f"Automation failed: {error_message}")
        
        automation.set_callbacks(on_step_complete, on_completion, on_error)
        
        # Run automation
        success = automation.run()
        
        if success:
            print("✅ Automation completed successfully!")
        else:
            print("❌ Automation failed!")
        
        automation.disconnect()
    else:
        print("❌ Failed to load configuration")
