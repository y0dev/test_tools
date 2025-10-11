import json
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


class LogParser:
    """
    Parse and analyze existing log files from the test framework.
    Can extract test results, patterns, and generate reports without running tests.
    """
    
    def __init__(self, log_directory: str = "./output/logs"):
        """
        Initialize the log parser.
        
        :param log_directory: Directory containing log files
        """
        self.log_directory = Path(log_directory)
        self.logger = logging.getLogger(__name__)
        
    def find_log_files(self) -> Dict[str, List[Path]]:
        """
        Find all log files in the log directory.
        
        :return: Dictionary categorizing log files by type
        """
        log_files = {
            'test_logs': [],
            'uart_logs': [],
            'validation_logs': [],
            'error_logs': [],
            'general_logs': []
        }
        
        if not self.log_directory.exists():
            self.logger.warning(f"Log directory does not exist: {self.log_directory}")
            return log_files
        
        for log_file in self.log_directory.glob("*.log"):
            filename = log_file.name.lower()
            
            if 'test' in filename or 'main' in filename:
                log_files['test_logs'].append(log_file)
            elif 'uart' in filename:
                log_files['uart_logs'].append(log_file)
            elif 'validation' in filename:
                log_files['validation_logs'].append(log_file)
            elif 'error' in filename:
                log_files['error_logs'].append(log_file)
            else:
                log_files['general_logs'].append(log_file)
        
        return log_files
    
    def parse_test_log(self, log_file: Path) -> Dict[str, Any]:
        """
        Parse a test log file to extract test information.
        
        :param log_file: Path to test log file
        :return: Parsed test information
        """
        test_info = {
            'file': str(log_file),
            'test_name': 'Unknown',
            'session_timestamp': None,
            'cycles': [],
            'start_time': None,
            'end_time': None,
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0
        }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_cycle = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract timestamp and message
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                if timestamp_match:
                    timestamp_str = timestamp_match.group(1)
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    except ValueError:
                        timestamp = None
                else:
                    timestamp = None
                
                # Parse different log entry types
                if 'Test session started:' in line:
                    test_info['test_name'] = line.split('Test session started: ')[-1]
                    test_info['start_time'] = timestamp
                elif 'Test session ended' in line:
                    test_info['end_time'] = timestamp
                elif 'Starting cycle' in line:
                    cycle_match = re.search(r'cycle (\d+)', line)
                    if cycle_match:
                        cycle_num = int(cycle_match.group(1))
                        current_cycle = {
                            'cycle_number': cycle_num,
                            'start_time': timestamp,
                            'events': [],
                            'validations': [],
                            'errors': []
                        }
                        test_info['cycles'].append(current_cycle)
                elif 'Cycle' in line and 'PASSED' in line:
                    if current_cycle:
                        current_cycle['success'] = True
                        current_cycle['end_time'] = timestamp
                        test_info['successful_cycles'] += 1
                elif 'Cycle' in line and 'FAILED' in line:
                    if current_cycle:
                        current_cycle['success'] = False
                        current_cycle['end_time'] = timestamp
                        test_info['failed_cycles'] += 1
                elif 'Pattern' in line and ('PASS' in line or 'FAIL' in line):
                    if current_cycle:
                        pattern_match = re.search(r"Pattern '([^']+)'", line)
                        success = 'PASS' in line
                        if pattern_match:
                            current_cycle['validations'].append({
                                'pattern_name': pattern_match.group(1),
                                'success': success,
                                'timestamp': timestamp
                            })
                elif 'ERROR' in line or 'Error:' in line:
                    if current_cycle:
                        current_cycle['errors'].append({
                            'message': line,
                            'timestamp': timestamp
                        })
            
            test_info['total_cycles'] = len(test_info['cycles'])
            
        except Exception as e:
            self.logger.error(f"Error parsing test log {log_file}: {e}")
        
        return test_info
    
    def parse_uart_log(self, log_file: Path) -> List[Dict[str, Any]]:
        """
        Parse a UART log file to extract UART data.
        
        :param log_file: Path to UART log file
        :return: List of UART data entries
        """
        uart_data = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse CSV format: timestamp,cycle,data
                parts = line.split(',', 2)
                if len(parts) >= 3:
                    try:
                        timestamp_str = parts[0]
                        cycle = parts[1] if parts[1] != 'N/A' else None
                        data = parts[2]
                        
                        timestamp = datetime.fromisoformat(timestamp_str)
                        
                        uart_data.append({
                            'timestamp': timestamp,
                            'cycle': cycle,
                            'data': data
                        })
                    except (ValueError, IndexError):
                        # Try to parse as simple timestamp format
                        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                        if timestamp_match:
                            timestamp_str = timestamp_match.group(1)
                            try:
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                data = line[len(timestamp_str):].strip()
                                uart_data.append({
                                    'timestamp': timestamp,
                                    'cycle': None,
                                    'data': data
                                })
                            except ValueError:
                                pass
        
        except Exception as e:
            self.logger.error(f"Error parsing UART log {log_file}: {e}")
        
        return uart_data
    
    def analyze_logs(self) -> Dict[str, Any]:
        """
        Analyze all log files and generate comprehensive report.
        
        :return: Comprehensive analysis of all logs
        """
        log_files = self.find_log_files()
        analysis = {
            'log_files_found': log_files,
            'test_sessions': [],
            'uart_data': [],
            'summary': {
                'total_test_sessions': 0,
                'total_cycles': 0,
                'successful_cycles': 0,
                'failed_cycles': 0,
                'total_uart_entries': 0
            }
        }
        
        # Parse test logs
        for test_log in log_files['test_logs']:
            test_info = self.parse_test_log(test_log)
            analysis['test_sessions'].append(test_info)
            analysis['summary']['total_test_sessions'] += 1
            analysis['summary']['total_cycles'] += test_info['total_cycles']
            analysis['summary']['successful_cycles'] += test_info['successful_cycles']
            analysis['summary']['failed_cycles'] += test_info['failed_cycles']
        
        # Parse UART logs
        for uart_log in log_files['uart_logs']:
            uart_data = self.parse_uart_log(uart_log)
            analysis['uart_data'].extend(uart_data)
            analysis['summary']['total_uart_entries'] += len(uart_data)
        
        # Calculate success rate
        if analysis['summary']['total_cycles'] > 0:
            analysis['summary']['success_rate'] = (
                analysis['summary']['successful_cycles'] / analysis['summary']['total_cycles']
            )
        else:
            analysis['summary']['success_rate'] = 0
        
        return analysis
    
    def generate_report_from_logs(self, output_file: str = None) -> str:
        """
        Generate a comprehensive report from existing log files.
        
        :param output_file: Output file path (optional)
        :return: Path to generated report file
        """
        analysis = self.analyze_logs()
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_file = f"./output/reports/log_analysis_{timestamp}.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {key: serialize_datetime(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            else:
                return obj
        
        serialized_analysis = serialize_datetime(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serialized_analysis, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Log analysis report generated: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """Print a summary of log analysis to console."""
        analysis = self.analyze_logs()
        summary = analysis['summary']
        
        print("=" * 60)
        print("LOG ANALYSIS SUMMARY")
        print("=" * 60)
        
        print(f"Log Directory: {self.log_directory}")
        print(f"Test Sessions Found: {summary['total_test_sessions']}")
        print(f"Total Cycles: {summary['total_cycles']}")
        print(f"Successful Cycles: {summary['successful_cycles']}")
        print(f"Failed Cycles: {summary['failed_cycles']}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        print(f"UART Data Entries: {summary['total_uart_entries']}")
        
        print(f"\nLog Files Found:")
        for category, files in analysis['log_files_found'].items():
            if files:
                print(f"  {category}: {len(files)} files")
                for file in files:
                    print(f"    - {file.name}")
        
        print(f"\nTest Sessions:")
        for i, session in enumerate(analysis['test_sessions'], 1):
            print(f"  Session {i}: {session['test_name']}")
            print(f"    Cycles: {session['total_cycles']} (Success: {session['successful_cycles']}, Failed: {session['failed_cycles']})")
            if session['start_time'] and session['end_time']:
                duration = session['end_time'] - session['start_time']
                print(f"    Duration: {duration}")
    
    def export_to_csv(self, output_file: str = None) -> str:
        """
        Export log analysis to CSV format.
        
        :param output_file: Output CSV file path
        :return: Path to generated CSV file
        """
        analysis = self.analyze_logs()
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_file = f"./output/reports/log_analysis_{timestamp}.csv"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write summary
            writer.writerow(['SUMMARY'])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Test Sessions', analysis['summary']['total_test_sessions']])
            writer.writerow(['Total Cycles', analysis['summary']['total_cycles']])
            writer.writerow(['Successful Cycles', analysis['summary']['successful_cycles']])
            writer.writerow(['Failed Cycles', analysis['summary']['failed_cycles']])
            writer.writerow(['Success Rate', f"{analysis['summary']['success_rate']:.2%}"])
            writer.writerow(['UART Data Entries', analysis['summary']['total_uart_entries']])
            writer.writerow([])
            
            # Write test sessions
            writer.writerow(['TEST SESSIONS'])
            writer.writerow(['Session', 'Test Name', 'Total Cycles', 'Successful', 'Failed', 'Start Time', 'End Time'])
            
            for i, session in enumerate(analysis['test_sessions'], 1):
                writer.writerow([
                    i,
                    session['test_name'],
                    session['total_cycles'],
                    session['successful_cycles'],
                    session['failed_cycles'],
                    session['start_time'].isoformat() if session['start_time'] else '',
                    session['end_time'].isoformat() if session['end_time'] else ''
                ])
            
            writer.writerow([])
            
            # Write UART data
            writer.writerow(['UART DATA'])
            writer.writerow(['Timestamp', 'Cycle', 'Data'])
            
            for entry in analysis['uart_data']:
                writer.writerow([
                    entry['timestamp'].isoformat(),
                    entry['cycle'] or '',
                    entry['data']
                ])
        
        self.logger.info(f"Log analysis CSV exported: {output_path}")
        return str(output_path)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create log parser
    parser = LogParser("./output/logs")
    
    # Print summary
    parser.print_summary()
    
    # Generate reports
    json_report = parser.generate_report_from_logs()
    csv_report = parser.export_to_csv()
    
    print(f"\nReports generated:")
    print(f"  JSON: {json_report}")
    print(f"  CSV: {csv_report}")
