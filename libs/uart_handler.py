import serial
import time
import threading
import queue
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging


class UARTHandler:
    """
    Handles UART communication for logging and pattern detection.
    Supports continuous data logging with pattern matching capabilities.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize UART handler with configuration.
        
        :param config: UART configuration dictionary
        """
        self.config = config
        self.serial_conn = None
        self.is_logging = False
        self.log_thread = None
        self.data_queue = queue.Queue()
        self.pattern_callbacks = []
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """
        Establish UART connection.
        
        :return: True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.config['port'],
                baudrate=self.config['baud_rate'],
                bytesize=self.config.get('data_bits', 8),
                parity=self.config.get('parity', 'N'),
                stopbits=self.config.get('stop_bits', 1),
                timeout=self.config.get('timeout', 1.0)
            )
            
            # Clear any existing data
            self.serial_conn.flushInput()
            self.serial_conn.flushOutput()
            
            self.logger.info(f"UART connected to {self.config['port']} at {self.config['baud_rate']} baud")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to UART {self.config['port']}: {e}")
            return False
    
    def disconnect(self):
        """Close UART connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.stop_logging()
            self.serial_conn.close()
            self.logger.info("UART connection closed")
    
    def start_logging(self):
        """Start continuous UART data logging in a separate thread."""
        if not self.serial_conn or not self.serial_conn.is_open:
            self.logger.error("UART not connected. Cannot start logging.")
            return False
            
        if self.is_logging:
            self.logger.warning("UART logging already active")
            return True
            
        self.is_logging = True
        self.log_thread = threading.Thread(target=self._log_data, daemon=True)
        self.log_thread.start()
        self.logger.info("UART logging started")
        return True
    
    def stop_logging(self):
        """Stop UART data logging."""
        self.is_logging = False
        if self.log_thread:
            self.log_thread.join(timeout=2.0)
        self.logger.info("UART logging stopped")
    
    def _log_data(self):
        """Internal method for continuous data logging."""
        buffer = ""
        
        while self.is_logging:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            timestamp = datetime.now()
                            log_entry = {
                                'timestamp': timestamp,
                                'data': line,
                                'raw_data': data
                            }
                            
                            # Add to queue for processing
                            self.data_queue.put(log_entry)
                            
                            # Check patterns
                            self._check_patterns(line, timestamp)
                            
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                self.logger.error(f"Error in UART logging thread: {e}")
                break
    
    def _check_patterns(self, data: str, timestamp: datetime):
        """Check data against registered patterns."""
        for callback in self.pattern_callbacks:
            try:
                callback(data, timestamp)
            except Exception as e:
                self.logger.error(f"Error in pattern callback: {e}")
    
    def register_pattern_callback(self, callback: Callable[[str, datetime], None]):
        """
        Register a callback function for pattern matching.
        
        :param callback: Function that takes (data, timestamp) parameters
        """
        self.pattern_callbacks.append(callback)
    
    def read_data(self, timeout: float = None) -> Optional[Dict]:
        """
        Read data from the queue.
        
        :param timeout: Maximum time to wait for data
        :return: Log entry dictionary or None if timeout
        """
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def read_all_data(self) -> List[Dict]:
        """
        Read all available data from the queue.
        
        :return: List of log entries
        """
        data_list = []
        while not self.data_queue.empty():
            try:
                data_list.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return data_list
    
    def clear_buffer(self):
        """Clear the data queue."""
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break
    
    def wait_for_pattern(self, pattern: str, timeout: float = 10.0, 
                        pattern_type: str = "contains") -> Optional[Dict]:
        """
        Wait for a specific pattern in UART data.
        
        :param pattern: Pattern to search for
        :param timeout: Maximum time to wait
        :param pattern_type: Type of pattern matching ("contains", "regex", "exact")
        :return: Log entry containing the pattern or None if timeout
        """
        import re
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            data_entry = self.read_data(timeout=0.1)
            if data_entry:
                data = data_entry['data']
                match = False
                
                if pattern_type == "contains":
                    match = pattern.lower() in data.lower()
                elif pattern_type == "exact":
                    match = pattern == data
                elif pattern_type == "regex":
                    match = bool(re.search(pattern, data))
                
                if match:
                    return data_entry
        
        return None
    
    def get_statistics(self) -> Dict:
        """
        Get UART communication statistics.
        
        :return: Dictionary with statistics
        """
        return {
            'is_connected': self.serial_conn and self.serial_conn.is_open,
            'is_logging': self.is_logging,
            'queue_size': self.data_queue.qsize(),
            'port': self.config['port'],
            'baud_rate': self.config['baud_rate']
        }


class UARTDataLogger:
    """
    Enhanced UART data logger with file output capabilities.
    """
    
    def __init__(self, uart_handler: UARTHandler, log_file: str = None):
        """
        Initialize UART data logger.
        
        :param uart_handler: UARTHandler instance
        :param log_file: Optional log file path
        """
        self.uart_handler = uart_handler
        self.log_file = log_file
        self.logger = logging.getLogger(__name__ + ".DataLogger")
        self.log_data = []
        
        # Register callback for data logging
        self.uart_handler.register_pattern_callback(self._log_data_callback)
    
    def _log_data_callback(self, data: str, timestamp: datetime):
        """Callback for logging UART data."""
        log_entry = {
            'timestamp': timestamp,
            'data': data,
            'cycle_number': getattr(self, 'current_cycle', None)
        }
        
        self.log_data.append(log_entry)
        
        # Write to file if specified
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{timestamp.isoformat()},{log_entry['cycle_number']},{data}\n")
            except Exception as e:
                self.logger.error(f"Failed to write to log file: {e}")
    
    def set_cycle_number(self, cycle_number: int):
        """Set current cycle number for logging."""
        self.current_cycle = cycle_number
    
    def get_log_data(self) -> List[Dict]:
        """Get all logged data."""
        return self.log_data.copy()
    
    def clear_log_data(self):
        """Clear logged data."""
        self.log_data.clear()
    
    def export_to_csv(self, filename: str):
        """Export log data to CSV file."""
        import csv
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'cycle_number', 'data']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for entry in self.log_data:
                    writer.writerow({
                        'timestamp': entry['timestamp'].isoformat(),
                        'cycle_number': entry['cycle_number'],
                        'data': entry['data']
                    })
            
            self.logger.info(f"Log data exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration
    uart_config = {
        'port': 'COM4',
        'baud_rate': 115200,
        'data_bits': 8,
        'parity': 'N',
        'stop_bits': 1,
        'timeout': 1.0
    }
    
    # Create UART handler
    uart = UARTHandler(uart_config)
    
    try:
        # Connect and start logging
        if uart.connect():
            uart.start_logging()
            
            # Wait for some data
            time.sleep(5)
            
            # Read available data
            data = uart.read_all_data()
            print(f"Received {len(data)} data entries")
            
            # Wait for specific pattern
            pattern_match = uart.wait_for_pattern("READY", timeout=5.0)
            if pattern_match:
                print(f"Pattern found: {pattern_match}")
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        uart.disconnect()
