import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ComprehensiveLogger:
    """
    Comprehensive logging setup that ensures all operations are logged.
    Creates multiple log files for different types of operations.
    """
    
    def __init__(self, log_directory: str = "./output/logs", log_level: str = "INFO"):
        """
        Initialize comprehensive logging.
        
        :param log_directory: Directory for log files
        :param log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for this session
        self.session_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Setup logging
        self._setup_logging(log_level)
    
    def _setup_logging(self, log_level: str):
        """Setup comprehensive logging configuration."""
        level = getattr(logging, log_level.upper())
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Main application log
        main_log_file = self.log_directory / f"main_{self.session_timestamp}.log"
        main_handler = logging.FileHandler(main_log_file, encoding='utf-8')
        main_handler.setLevel(level)
        main_handler.setFormatter(detailed_formatter)
        
        # Power supply operations log
        ps_log_file = self.log_directory / f"power_supply_{self.session_timestamp}.log"
        ps_handler = logging.FileHandler(ps_log_file, encoding='utf-8')
        ps_handler.setLevel(logging.DEBUG)
        ps_handler.setFormatter(detailed_formatter)
        
        # UART operations log
        uart_log_file = self.log_directory / f"uart_operations_{self.session_timestamp}.log"
        uart_handler = logging.FileHandler(uart_log_file, encoding='utf-8')
        uart_handler.setLevel(logging.DEBUG)
        uart_handler.setFormatter(detailed_formatter)
        
        # Test execution log
        test_log_file = self.log_directory / f"test_execution_{self.session_timestamp}.log"
        test_handler = logging.FileHandler(test_log_file, encoding='utf-8')
        test_handler.setLevel(logging.DEBUG)
        test_handler.setFormatter(detailed_formatter)
        
        # Error log
        error_log_file = self.log_directory / f"errors_{self.session_timestamp}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()  # Clear existing handlers
        
        # Add handlers
        root_logger.addHandler(main_handler)
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        self._configure_logger('lib.power_supply', [ps_handler])
        self._configure_logger('lib.uart_handler', [uart_handler])
        self._configure_logger('lib.test_runner', [test_handler])
        self._configure_logger('lib.test_logger', [test_handler])
        self._configure_logger('lib.pattern_validator', [test_handler])
        self._configure_logger('lib.report_generator', [test_handler])
        self._configure_logger('lib.test_template_loader', [test_handler])
        self._configure_logger('lib.log_parser', [test_handler])
        
        # Error logger
        error_logger = logging.getLogger('errors')
        error_logger.addHandler(error_handler)
        error_logger.setLevel(logging.ERROR)
        
        # Log initialization
        logger = logging.getLogger(__name__)
        logger.info(f"Comprehensive logging initialized")
        logger.info(f"Log directory: {self.log_directory}")
        logger.info(f"Session timestamp: {self.session_timestamp}")
        logger.info(f"Log level: {log_level}")
    
    def _configure_logger(self, logger_name: str, handlers: list):
        """Configure a specific logger with handlers."""
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        for handler in handlers:
            logger.addHandler(handler)
    
    def log_system_info(self):
        """Log system information."""
        logger = logging.getLogger(__name__)
        
        logger.info("System Information:")
        logger.info(f"  Python version: {sys.version}")
        logger.info(f"  Platform: {sys.platform}")
        logger.info(f"  Working directory: {Path.cwd()}")
        logger.info(f"  Log directory: {self.log_directory}")
    
    def log_configuration(self, config: dict):
        """Log configuration information."""
        logger = logging.getLogger(__name__)
        
        logger.info("Configuration loaded:")
        logger.info(f"  Power supply: {config.get('power_supply', {}).get('resource', 'N/A')}")
        logger.info(f"  UART loggers: {len(config.get('uart_loggers', []))}")
        logger.info(f"  Tests: {len(config.get('tests', []))}")
        
        # Log test details
        for i, test in enumerate(config.get('tests', [])):
            logger.info(f"  Test {i+1}: {test.get('name', 'N/A')}")
    
    def log_test_start(self, test_name: str, cycles: int):
        """Log test start information."""
        logger = logging.getLogger('lib.test_runner')
        logger.info(f"Starting test: {test_name}")
        logger.info(f"  Cycles: {cycles}")
        logger.info(f"  Start time: {datetime.now()}")
    
    def log_test_end(self, test_name: str, success_rate: float, duration: str):
        """Log test end information."""
        logger = logging.getLogger('lib.test_runner')
        logger.info(f"Test completed: {test_name}")
        logger.info(f"  Success rate: {success_rate:.2%}")
        logger.info(f"  Duration: {duration}")
        logger.info(f"  End time: {datetime.now()}")
    
    def log_power_supply_operation(self, operation: str, details: str = ""):
        """Log power supply operations."""
        logger = logging.getLogger('lib.power_supply')
        logger.info(f"Power supply operation: {operation}")
        if details:
            logger.info(f"  Details: {details}")
    
    def log_uart_operation(self, operation: str, port: str = "", details: str = ""):
        """Log UART operations."""
        logger = logging.getLogger('lib.uart_handler')
        logger.info(f"UART operation: {operation}")
        if port:
            logger.info(f"  Port: {port}")
        if details:
            logger.info(f"  Details: {details}")
    
    def log_pattern_validation(self, pattern_name: str, success: bool, details: str = ""):
        """Log pattern validation results."""
        logger = logging.getLogger('lib.pattern_validator')
        status = "PASS" if success else "FAIL"
        logger.info(f"Pattern validation: {pattern_name} - {status}")
        if details:
            logger.info(f"  Details: {details}")
    
    def log_report_generation(self, report_type: str, file_path: str):
        """Log report generation."""
        logger = logging.getLogger('lib.report_generator')
        logger.info(f"Report generated: {report_type}")
        logger.info(f"  File: {file_path}")
    
    def get_log_files(self) -> dict:
        """Get list of log files created."""
        log_files = {}
        
        for log_file in self.log_directory.glob(f"*_{self.session_timestamp}.log"):
            if 'main_' in log_file.name:
                log_files['main'] = str(log_file)
            elif 'power_supply_' in log_file.name:
                log_files['power_supply'] = str(log_file)
            elif 'uart_operations_' in log_file.name:
                log_files['uart'] = str(log_file)
            elif 'test_execution_' in log_file.name:
                log_files['test'] = str(log_file)
            elif 'errors_' in log_file.name:
                log_files['errors'] = str(log_file)
        
        return log_files


# Example usage
if __name__ == "__main__":
    # Initialize comprehensive logging
    logger_setup = ComprehensiveLogger()
    
    # Log system info
    logger_setup.log_system_info()
    
    # Example configuration
    config = {
        'power_supply': {'resource': 'GPIB0::5::INSTR'},
        'uart_loggers': [{'port': 'COM3', 'baud': 115200}],
        'tests': [{'name': 'test1'}, {'name': 'test2'}]
    }
    
    # Log configuration
    logger_setup.log_configuration(config)
    
    # Log some operations
    logger_setup.log_power_supply_operation("Connect", "GPIB0::5::INSTR")
    logger_setup.log_uart_operation("Connect", "COM3", "115200 baud")
    logger_setup.log_pattern_validation("boot_pattern", True, "Pattern matched")
    
    # Get log files
    log_files = logger_setup.get_log_files()
    print(f"Log files created: {log_files}")
