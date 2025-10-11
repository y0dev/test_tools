import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import queue


class TestLogger:
    """
    Comprehensive logging system for test automation with timestamp support.
    Provides structured logging for test cycles, UART data, and validation results.
    """
    
    def __init__(self, config: Dict, test_name: str = None):
        """
        Initialize the test logger.
        
        :param config: Configuration dictionary
        :param test_name: Optional test name for log files
        """
        self.config = config
        self.test_name = test_name or config.get('test_config', {}).get('test_name', 'test')
        self.log_directory = Path(config.get('output', {}).get('log_directory', './output/logs'))
        self.timestamp_format = config.get('output', {}).get('timestamp_format', '%Y-%m-%d_%H-%M-%S')
        
        # Create log directory
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for this test session
        self.session_timestamp = datetime.now().strftime(self.timestamp_format)
        
        # Initialize loggers
        self._setup_loggers()
        
        # Test cycle tracking
        self.current_cycle = 0
        self.test_start_time = None
        self.cycle_data = []
        
        # Thread-safe logging queue
        self.log_queue = queue.Queue()
        self.log_thread = None
        self.is_logging = True
        
        # Start background logging thread
        self._start_logging_thread()
    
    def _setup_loggers(self):
        """Setup different loggers for different purposes."""
        # Main test logger
        self.test_logger = logging.getLogger('test_main')
        self.test_logger.setLevel(logging.INFO)
        
        # UART data logger
        self.uart_logger = logging.getLogger('uart_data')
        self.uart_logger.setLevel(logging.DEBUG)
        
        # Validation logger
        self.validation_logger = logging.getLogger('validation')
        self.validation_logger.setLevel(logging.INFO)
        
        # Error logger
        self.error_logger = logging.getLogger('errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Setup file handlers
        self._setup_file_handlers()
        
        # Setup console handler
        self._setup_console_handler()
    
    def _setup_file_handlers(self):
        """Setup file handlers for different log types."""
        # Main test log
        test_log_file = self.log_directory / f"{self.test_name}_{self.session_timestamp}.log"
        test_handler = logging.FileHandler(test_log_file, encoding='utf-8')
        test_handler.setLevel(logging.INFO)
        test_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        test_handler.setFormatter(test_formatter)
        self.test_logger.addHandler(test_handler)
        
        # UART data log
        uart_log_file = self.log_directory / f"uart_{self.session_timestamp}.log"
        uart_handler = logging.FileHandler(uart_log_file, encoding='utf-8')
        uart_handler.setLevel(logging.DEBUG)
        uart_formatter = logging.Formatter('%(asctime)s - %(message)s')
        uart_handler.setFormatter(uart_formatter)
        self.uart_logger.addHandler(uart_handler)
        
        # Validation log
        validation_log_file = self.log_directory / f"validation_{self.session_timestamp}.log"
        validation_handler = logging.FileHandler(validation_log_file, encoding='utf-8')
        validation_handler.setLevel(logging.INFO)
        validation_handler.setFormatter(test_formatter)
        self.validation_logger.addHandler(validation_handler)
        
        # Error log
        error_log_file = self.log_directory / f"errors_{self.session_timestamp}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(test_formatter)
        self.error_logger.addHandler(error_handler)
    
    def _setup_console_handler(self):
        """Setup console handler for real-time output."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add to all loggers
        for logger in [self.test_logger, self.validation_logger, self.error_logger]:
            logger.addHandler(console_handler)
    
    def _start_logging_thread(self):
        """Start background thread for processing log queue."""
        self.log_thread = threading.Thread(target=self._process_log_queue, daemon=True)
        self.log_thread.start()
    
    def _process_log_queue(self):
        """Process log queue in background thread."""
        while self.is_logging:
            try:
                log_entry = self.log_queue.get(timeout=1.0)
                self._write_log_entry(log_entry)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing log queue: {e}")
    
    def _write_log_entry(self, log_entry: Dict):
        """Write log entry to appropriate file."""
        try:
            log_type = log_entry.get('type', 'general')
            timestamp = log_entry.get('timestamp', datetime.now())
            message = log_entry.get('message', '')
            data = log_entry.get('data', {})
            
            # Format log line
            log_line = f"{timestamp.isoformat()},{log_entry.get('cycle', 'N/A')},{log_type},{message}"
            
            if data:
                log_line += f",{json.dumps(data)}"
            
            log_line += "\n"
            
            # Write to appropriate log file
            if log_type == 'uart':
                uart_log_file = self.log_directory / f"uart_{self.session_timestamp}.log"
                with open(uart_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
            elif log_type == 'validation':
                validation_log_file = self.log_directory / f"validation_{self.session_timestamp}.log"
                with open(validation_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
            else:
                # General log
                general_log_file = self.log_directory / f"general_{self.session_timestamp}.log"
                with open(general_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
                    
        except Exception as e:
            print(f"Error writing log entry: {e}")
    
    def start_test(self):
        """Mark the start of a test session."""
        self.test_start_time = datetime.now()
        self.test_logger.info(f"Test session started: {self.test_name}")
        self.test_logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
    
    def end_test(self):
        """Mark the end of a test session."""
        if self.test_start_time:
            duration = datetime.now() - self.test_start_time
            self.test_logger.info(f"Test session ended. Duration: {duration}")
        
        # Stop logging thread
        self.is_logging = False
        if self.log_thread:
            self.log_thread.join(timeout=2.0)
    
    def start_cycle(self, cycle_number: int):
        """Mark the start of a test cycle."""
        self.current_cycle = cycle_number
        cycle_start_time = datetime.now()
        
        cycle_info = {
            'cycle_number': cycle_number,
            'start_time': cycle_start_time,
            'events': [],
            'validations': [],
            'uart_data_count': 0,
            'errors': []
        }
        
        self.cycle_data.append(cycle_info)
        self.test_logger.info(f"Starting cycle {cycle_number}")
        
        # Queue log entry
        self.log_queue.put({
            'type': 'cycle_start',
            'timestamp': cycle_start_time,
            'cycle': cycle_number,
            'message': f"Cycle {cycle_number} started",
            'data': {'cycle_number': cycle_number}
        })
    
    def end_cycle(self, cycle_number: int, success: bool = True):
        """Mark the end of a test cycle."""
        cycle_end_time = datetime.now()
        
        # Find current cycle data
        current_cycle_data = None
        for cycle in self.cycle_data:
            if cycle['cycle_number'] == cycle_number:
                current_cycle_data = cycle
                break
        
        if current_cycle_data:
            current_cycle_data['end_time'] = cycle_end_time
            current_cycle_data['success'] = success
            current_cycle_data['duration'] = cycle_end_time - current_cycle_data['start_time']
        
        status = "PASSED" if success else "FAILED"
        self.test_logger.info(f"Cycle {cycle_number} {status}")
        
        # Queue log entry
        self.log_queue.put({
            'type': 'cycle_end',
            'timestamp': cycle_end_time,
            'cycle': cycle_number,
            'message': f"Cycle {cycle_number} {status}",
            'data': {
                'cycle_number': cycle_number,
                'success': success,
                'duration': str(current_cycle_data['duration']) if current_cycle_data else None
            }
        })
    
    def log_uart_data(self, data: str, cycle_number: int = None):
        """Log UART data."""
        cycle = cycle_number or self.current_cycle
        
        # Update cycle data
        for cycle_data in self.cycle_data:
            if cycle_data['cycle_number'] == cycle:
                cycle_data['uart_data_count'] += 1
                break
        
        self.uart_logger.debug(f"Cycle {cycle}: {data}")
        
        # Queue log entry
        self.log_queue.put({
            'type': 'uart',
            'timestamp': datetime.now(),
            'cycle': cycle,
            'message': data,
            'data': {'data_length': len(data)}
        })
    
    def log_validation_result(self, result, cycle_number: int = None):
        """Log validation result."""
        cycle = cycle_number or self.current_cycle
        
        # Update cycle data
        for cycle_data in self.cycle_data:
            if cycle_data['cycle_number'] == cycle:
                cycle_data['validations'].append({
                    'pattern_name': result.pattern_name,
                    'success': result.success,
                    'timestamp': result.match_time,
                    'error_message': result.error_message
                })
                break
        
        level = logging.INFO if result.success else logging.WARNING
        self.validation_logger.log(level, f"Cycle {cycle}: {result.pattern_name} - {'PASS' if result.success else 'FAIL'}")
        
        if result.error_message:
            self.error_logger.error(f"Cycle {cycle}: {result.pattern_name} - {result.error_message}")
        
        # Queue log entry
        self.log_queue.put({
            'type': 'validation',
            'timestamp': result.match_time or datetime.now(),
            'cycle': cycle,
            'message': f"{result.pattern_name}: {'PASS' if result.success else 'FAIL'}",
            'data': {
                'pattern_name': result.pattern_name,
                'success': result.success,
                'error_message': result.error_message,
                'extracted_values': result.extracted_values
            }
        })
    
    def log_error(self, error_message: str, cycle_number: int = None, exception: Exception = None):
        """Log error message."""
        cycle = cycle_number or self.current_cycle
        
        # Update cycle data
        for cycle_data in self.cycle_data:
            if cycle_data['cycle_number'] == cycle:
                cycle_data['errors'].append({
                    'message': error_message,
                    'timestamp': datetime.now(),
                    'exception': str(exception) if exception else None
                })
                break
        
        self.error_logger.error(f"Cycle {cycle}: {error_message}")
        if exception:
            self.error_logger.exception(f"Exception details: {exception}")
        
        # Queue log entry
        self.log_queue.put({
            'type': 'error',
            'timestamp': datetime.now(),
            'cycle': cycle,
            'message': error_message,
            'data': {
                'exception': str(exception) if exception else None
            }
        })
    
    def log_event(self, event_message: str, cycle_number: int = None, data: Dict = None):
        """Log general event."""
        cycle = cycle_number or self.current_cycle
        
        # Update cycle data
        for cycle_data in self.cycle_data:
            if cycle_data['cycle_number'] == cycle:
                cycle_data['events'].append({
                    'message': event_message,
                    'timestamp': datetime.now(),
                    'data': data or {}
                })
                break
        
        self.test_logger.info(f"Cycle {cycle}: {event_message}")
        
        # Queue log entry
        self.log_queue.put({
            'type': 'event',
            'timestamp': datetime.now(),
            'cycle': cycle,
            'message': event_message,
            'data': data or {}
        })
    
    def get_test_summary(self) -> Dict:
        """Get comprehensive test summary."""
        if not self.cycle_data:
            return {'error': 'No test cycles completed'}
        
        total_cycles = len(self.cycle_data)
        successful_cycles = sum(1 for cycle in self.cycle_data if cycle.get('success', False))
        failed_cycles = total_cycles - successful_cycles
        
        total_uart_data = sum(cycle.get('uart_data_count', 0) for cycle in self.cycle_data)
        total_validations = sum(len(cycle.get('validations', [])) for cycle in self.cycle_data)
        total_errors = sum(len(cycle.get('errors', [])) for cycle in self.cycle_data)
        
        # Calculate average cycle duration
        durations = [cycle.get('duration') for cycle in self.cycle_data if cycle.get('duration')]
        avg_duration = sum(durations, datetime.now() - datetime.now()) / len(durations) if durations else None
        
        return {
            'test_name': self.test_name,
            'session_timestamp': self.session_timestamp,
            'test_start_time': self.test_start_time.isoformat() if self.test_start_time else None,
            'test_end_time': datetime.now().isoformat(),
            'total_cycles': total_cycles,
            'successful_cycles': successful_cycles,
            'failed_cycles': failed_cycles,
            'success_rate': successful_cycles / total_cycles if total_cycles > 0 else 0,
            'total_uart_data_points': total_uart_data,
            'total_validations': total_validations,
            'total_errors': total_errors,
            'average_cycle_duration': str(avg_duration) if avg_duration else None,
            'cycle_details': self.cycle_data
        }
    
    def export_logs_to_csv(self, filename: str = None):
        """Export all logs to CSV format."""
        if not filename:
            filename = self.log_directory / f"test_logs_{self.session_timestamp}.csv"
        
        import csv
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'cycle', 'type', 'message', 'data']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                # Write cycle data
                for cycle in self.cycle_data:
                    # Cycle start
                    writer.writerow({
                        'timestamp': cycle['start_time'].isoformat(),
                        'cycle': cycle['cycle_number'],
                        'type': 'cycle_start',
                        'message': f"Cycle {cycle['cycle_number']} started",
                        'data': json.dumps({'cycle_number': cycle['cycle_number']})
                    })
                    
                    # Events
                    for event in cycle.get('events', []):
                        writer.writerow({
                            'timestamp': event['timestamp'].isoformat(),
                            'cycle': cycle['cycle_number'],
                            'type': 'event',
                            'message': event['message'],
                            'data': json.dumps(event['data'])
                        })
                    
                    # Validations
                    for validation in cycle.get('validations', []):
                        writer.writerow({
                            'timestamp': validation['timestamp'].isoformat(),
                            'cycle': cycle['cycle_number'],
                            'type': 'validation',
                            'message': f"{validation['pattern_name']}: {'PASS' if validation['success'] else 'FAIL'}",
                            'data': json.dumps({
                                'pattern_name': validation['pattern_name'],
                                'success': validation['success'],
                                'error_message': validation['error_message']
                            })
                        })
                    
                    # Errors
                    for error in cycle.get('errors', []):
                        writer.writerow({
                            'timestamp': error['timestamp'].isoformat(),
                            'cycle': cycle['cycle_number'],
                            'type': 'error',
                            'message': error['message'],
                            'data': json.dumps({'exception': error['exception']})
                        })
                    
                    # Cycle end
                    if 'end_time' in cycle:
                        writer.writerow({
                            'timestamp': cycle['end_time'].isoformat(),
                            'cycle': cycle['cycle_number'],
                            'type': 'cycle_end',
                            'message': f"Cycle {cycle['cycle_number']} {'PASSED' if cycle.get('success') else 'FAILED'}",
                            'data': json.dumps({
                                'success': cycle.get('success', False),
                                'duration': str(cycle.get('duration', ''))
                            })
                        })
            
            self.test_logger.info(f"Logs exported to CSV: {filename}")
            return str(filename)
            
        except Exception as e:
            self.error_logger.error(f"Failed to export CSV: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'test_config': {
            'test_name': 'Example Test',
            'total_cycles': 3
        },
        'output': {
            'log_directory': 'logs',
            'timestamp_format': '%Y-%m-%d_%H-%M-%S'
        }
    }
    
    # Create logger
    logger = TestLogger(config)
    
    try:
        # Start test
        logger.start_test()
        
        # Simulate test cycles
        for cycle in range(1, 4):
            logger.start_cycle(cycle)
            
            # Simulate some events
            logger.log_event(f"Power cycle {cycle} started", cycle)
            logger.log_uart_data(f"Boot sequence {cycle}", cycle)
            logger.log_uart_data(f"Ready signal {cycle}", cycle)
            
            # Simulate validation
            from libs.pattern_validator import ValidationResult
            result = ValidationResult(
                pattern_name="boot_test",
                success=True,
                matched_data=f"Boot sequence {cycle}",
                match_time=datetime.now()
            )
            logger.log_validation_result(result, cycle)
            
            # End cycle
            logger.end_cycle(cycle, success=True)
        
        # End test
        logger.end_test()
        
        # Get summary
        summary = logger.get_test_summary()
        print("Test Summary:")
        print(json.dumps(summary, indent=2))
        
        # Export to CSV
        csv_file = logger.export_logs_to_csv()
        print(f"Logs exported to: {csv_file}")
        
    except Exception as e:
        logger.log_error(f"Test failed: {e}", exception=e)
        logger.end_test()
