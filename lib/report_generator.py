import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging


class ReportGenerator:
    """
    Comprehensive report generation system for test results.
    Supports CSV, JSON, and text format outputs with detailed analysis.
    """
    
    def __init__(self, config: Dict, logger=None):
        """
        Initialize the report generator.
        
        :param config: Configuration dictionary
        :param logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.output_config = config.get('output', {})
        self.report_directory = Path(self.output_config.get('report_directory', './output/reports'))
        self.timestamp_format = self.output_config.get('timestamp_format', '%Y-%m-%d_%H-%M-%S')
        
        # Create report directory
        self.report_directory.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for this report session
        self.session_timestamp = datetime.now().strftime(self.timestamp_format)
    
    def generate_comprehensive_report(self, test_summary: Dict, 
                                    cycle_data: List[Dict] = None,
                                    uart_data: List[Dict] = None,
                                    validation_results: List[Dict] = None) -> Dict[str, str]:
        """
        Generate comprehensive reports in all formats.
        
        :param test_summary: Test summary data
        :param cycle_data: Detailed cycle data
        :param uart_data: UART data logs
        :param validation_results: Validation results
        :return: Dictionary with file paths of generated reports
        """
        report_files = {}
        
        try:
            # Generate CSV report
            csv_file = self.generate_csv_report(test_summary, cycle_data, uart_data, validation_results)
            if csv_file:
                report_files['csv'] = csv_file
            
            # Generate JSON report
            json_file = self.generate_json_report(test_summary, cycle_data, uart_data, validation_results)
            if json_file:
                report_files['json'] = json_file
            
            # Generate text summary
            text_file = self.generate_text_report(test_summary, cycle_data, uart_data, validation_results)
            if text_file:
                report_files['text'] = text_file
            
            # Generate HTML report
            html_file = self.generate_html_report(test_summary, cycle_data, uart_data, validation_results)
            if html_file:
                report_files['html'] = html_file
            
            self.logger.info(f"Generated {len(report_files)} report files")
            return report_files
            
        except Exception as e:
            self.logger.error(f"Error generating reports: {e}")
            return {}
    
    def generate_csv_report(self, test_summary: Dict, cycle_data: List[Dict] = None,
                          uart_data: List[Dict] = None, validation_results: List[Dict] = None) -> Optional[str]:
        """
        Generate CSV report with detailed test data.
        
        :param test_summary: Test summary data
        :param cycle_data: Detailed cycle data
        :param uart_data: UART data logs
        :param validation_results: Validation results
        :return: Path to generated CSV file
        """
        try:
            filename = self.output_config.get('csv_filename', f'test_results_{self.session_timestamp}.csv')
            filepath = self.report_directory / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Test Name', 'Session Timestamp', 'Cycle Number', 'Event Type', 
                    'Timestamp', 'Message', 'Success', 'Duration', 'Data'
                ])
                
                # Write test summary
                writer.writerow([
                    test_summary.get('test_name', ''),
                    test_summary.get('session_timestamp', ''),
                    'SUMMARY',
                    'test_summary',
                    test_summary.get('test_start_time', ''),
                    f"Total Cycles: {test_summary.get('total_cycles', 0)}, Success Rate: {test_summary.get('success_rate', 0):.2%}",
                    test_summary.get('success_rate', 0) > 0.8,
                    '',
                    json.dumps({
                        'total_cycles': test_summary.get('total_cycles', 0),
                        'successful_cycles': test_summary.get('successful_cycles', 0),
                        'failed_cycles': test_summary.get('failed_cycles', 0),
                        'total_uart_data_points': test_summary.get('total_uart_data_points', 0),
                        'total_validations': test_summary.get('total_validations', 0),
                        'total_errors': test_summary.get('total_errors', 0)
                    })
                ])
                
                # Write cycle data
                if cycle_data:
                    for cycle in cycle_data:
                        cycle_num = cycle.get('cycle_number', 0)
                        
                        # Cycle start
                        writer.writerow([
                            test_summary.get('test_name', ''),
                            test_summary.get('session_timestamp', ''),
                            cycle_num,
                            'cycle_start',
                            cycle.get('start_time', '').isoformat() if isinstance(cycle.get('start_time'), datetime) else str(cycle.get('start_time', '')),
                            f"Cycle {cycle_num} started",
                            '',
                            '',
                            json.dumps({'cycle_number': cycle_num})
                        ])
                        
                        # Events
                        for event in cycle.get('events', []):
                            writer.writerow([
                                test_summary.get('test_name', ''),
                                test_summary.get('session_timestamp', ''),
                                cycle_num,
                                'event',
                                event.get('timestamp', '').isoformat() if isinstance(event.get('timestamp'), datetime) else str(event.get('timestamp', '')),
                                event.get('message', ''),
                                '',
                                '',
                                json.dumps(event.get('data', {}))
                            ])
                        
                        # Validations
                        for validation in cycle.get('validations', []):
                            writer.writerow([
                                test_summary.get('test_name', ''),
                                test_summary.get('session_timestamp', ''),
                                cycle_num,
                                'validation',
                                validation.get('timestamp', '').isoformat() if isinstance(validation.get('timestamp'), datetime) else str(validation.get('timestamp', '')),
                                f"{validation.get('pattern_name', '')}: {'PASS' if validation.get('success') else 'FAIL'}",
                                validation.get('success', False),
                                '',
                                json.dumps({
                                    'pattern_name': validation.get('pattern_name', ''),
                                    'error_message': validation.get('error_message', '')
                                })
                            ])
                        
                        # Errors
                        for error in cycle.get('errors', []):
                            writer.writerow([
                                test_summary.get('test_name', ''),
                                test_summary.get('session_timestamp', ''),
                                cycle_num,
                                'error',
                                error.get('timestamp', '').isoformat() if isinstance(error.get('timestamp'), datetime) else str(error.get('timestamp', '')),
                                error.get('message', ''),
                                False,
                                '',
                                json.dumps({'exception': error.get('exception', '')})
                            ])
                        
                        # Cycle end
                        if 'end_time' in cycle:
                            writer.writerow([
                                test_summary.get('test_name', ''),
                                test_summary.get('session_timestamp', ''),
                                cycle_num,
                                'cycle_end',
                                cycle.get('end_time', '').isoformat() if isinstance(cycle.get('end_time'), datetime) else str(cycle.get('end_time', '')),
                                f"Cycle {cycle_num} {'PASSED' if cycle.get('success') else 'FAILED'}",
                                cycle.get('success', False),
                                str(cycle.get('duration', '')),
                                json.dumps({
                                    'success': cycle.get('success', False),
                                    'uart_data_count': cycle.get('uart_data_count', 0)
                                })
                            ])
            
            self.logger.info(f"CSV report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error generating CSV report: {e}")
            return None
    
    def generate_json_report(self, test_summary: Dict, cycle_data: List[Dict] = None,
                           uart_data: List[Dict] = None, validation_results: List[Dict] = None) -> Optional[str]:
        """
        Generate JSON report with structured test data.
        
        :param test_summary: Test summary data
        :param cycle_data: Detailed cycle data
        :param uart_data: UART data logs
        :param validation_results: Validation results
        :return: Path to generated JSON file
        """
        try:
            filename = self.output_config.get('json_filename', f'test_results_{self.session_timestamp}.json')
            filepath = self.report_directory / filename
            
            # Prepare comprehensive JSON data
            json_data = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'generator_version': '1.0.0',
                    'report_format': 'comprehensive_test_report'
                },
                'test_summary': test_summary,
                'cycle_data': cycle_data or [],
                'uart_data': uart_data or [],
                'validation_results': validation_results or [],
                'statistics': self._calculate_statistics(test_summary, cycle_data, validation_results),
                'configuration': self.config
            }
            
            # Convert datetime objects to strings
            json_data = self._serialize_datetime(json_data)
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error generating JSON report: {e}")
            return None
    
    def generate_text_report(self, test_summary: Dict, cycle_data: List[Dict] = None,
                           uart_data: List[Dict] = None, validation_results: List[Dict] = None) -> Optional[str]:
        """
        Generate human-readable text report.
        
        :param test_summary: Test summary data
        :param cycle_data: Detailed cycle data
        :param uart_data: UART data logs
        :param validation_results: Validation results
        :return: Path to generated text file
        """
        try:
            filename = self.output_config.get('text_filename', f'test_summary_{self.session_timestamp}.txt')
            filepath = self.report_directory / filename
            
            with open(filepath, 'w', encoding='utf-8') as textfile:
                # Write header
                textfile.write("=" * 80 + "\n")
                textfile.write(f"TEST REPORT: {test_summary.get('test_name', 'Unknown Test')}\n")
                textfile.write("=" * 80 + "\n\n")
                
                # Write test summary
                textfile.write("TEST SUMMARY\n")
                textfile.write("-" * 40 + "\n")
                textfile.write(f"Test Name: {test_summary.get('test_name', 'N/A')}\n")
                textfile.write(f"Session Timestamp: {test_summary.get('session_timestamp', 'N/A')}\n")
                textfile.write(f"Test Start Time: {test_summary.get('test_start_time', 'N/A')}\n")
                textfile.write(f"Test End Time: {test_summary.get('test_end_time', 'N/A')}\n")
                textfile.write(f"Total Cycles: {test_summary.get('total_cycles', 0)}\n")
                textfile.write(f"Successful Cycles: {test_summary.get('successful_cycles', 0)}\n")
                textfile.write(f"Failed Cycles: {test_summary.get('failed_cycles', 0)}\n")
                textfile.write(f"Success Rate: {test_summary.get('success_rate', 0):.2%}\n")
                textfile.write(f"Total UART Data Points: {test_summary.get('total_uart_data_points', 0)}\n")
                textfile.write(f"Total Validations: {test_summary.get('total_validations', 0)}\n")
                textfile.write(f"Total Errors: {test_summary.get('total_errors', 0)}\n")
                textfile.write(f"Average Cycle Duration: {test_summary.get('average_cycle_duration', 'N/A')}\n\n")
                
                # Write cycle details
                if cycle_data:
                    textfile.write("CYCLE DETAILS\n")
                    textfile.write("-" * 40 + "\n")
                    
                    for cycle in cycle_data:
                        cycle_num = cycle.get('cycle_number', 0)
                        success = cycle.get('success', False)
                        duration = cycle.get('duration', 'N/A')
                        
                        textfile.write(f"\nCycle {cycle_num}:\n")
                        textfile.write(f"  Status: {'PASSED' if success else 'FAILED'}\n")
                        textfile.write(f"  Duration: {duration}\n")
                        textfile.write(f"  UART Data Points: {cycle.get('uart_data_count', 0)}\n")
                        textfile.write(f"  Validations: {len(cycle.get('validations', []))}\n")
                        textfile.write(f"  Errors: {len(cycle.get('errors', []))}\n")
                        
                        # Write events
                        events = cycle.get('events', [])
                        if events:
                            textfile.write("  Events:\n")
                            for event in events:
                                timestamp = event.get('timestamp', 'N/A')
                                message = event.get('message', 'N/A')
                                textfile.write(f"    {timestamp}: {message}\n")
                        
                        # Write validations
                        validations = cycle.get('validations', [])
                        if validations:
                            textfile.write("  Validations:\n")
                            for validation in validations:
                                pattern_name = validation.get('pattern_name', 'N/A')
                                success = validation.get('success', False)
                                textfile.write(f"    {pattern_name}: {'PASS' if success else 'FAIL'}\n")
                        
                        # Write errors
                        errors = cycle.get('errors', [])
                        if errors:
                            textfile.write("  Errors:\n")
                            for error in errors:
                                message = error.get('message', 'N/A')
                                textfile.write(f"    {message}\n")
                
                # Write statistics
                stats = self._calculate_statistics(test_summary, cycle_data, validation_results)
                if stats:
                    textfile.write("\nSTATISTICS\n")
                    textfile.write("-" * 40 + "\n")
                    for key, value in stats.items():
                        textfile.write(f"{key}: {value}\n")
                
                textfile.write("\n" + "=" * 80 + "\n")
                textfile.write("End of Report\n")
                textfile.write("=" * 80 + "\n")
            
            self.logger.info(f"Text report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error generating text report: {e}")
            return None
    
    def generate_html_report(self, test_summary: Dict, cycle_data: List[Dict] = None,
                           uart_data: List[Dict] = None, validation_results: List[Dict] = None) -> Optional[str]:
        """
        Generate HTML report with visual charts and tables.
        
        :param test_summary: Test summary data
        :param cycle_data: Detailed cycle data
        :param uart_data: UART data logs
        :param validation_results: Validation results
        :return: Path to generated HTML file
        """
        try:
            filename = f'test_report_{self.session_timestamp}.html'
            filepath = self.report_directory / filename
            
            # Calculate statistics
            stats = self._calculate_statistics(test_summary, cycle_data, validation_results)
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {test_summary.get('test_name', 'Unknown Test')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
        .summary-card.success {{ border-left-color: #28a745; }}
        .summary-card.error {{ border-left-color: #dc3545; }}
        .cycle-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        .cycle-table th, .cycle-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .cycle-table th {{ background-color: #f2f2f2; }}
        .cycle-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .status-pass {{ color: #28a745; font-weight: bold; }}
        .status-fail {{ color: #dc3545; font-weight: bold; }}
        .chart-container {{ margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Report: {test_summary.get('test_name', 'Unknown Test')}</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card {'success' if test_summary.get('success_rate', 0) > 0.8 else 'error'}">
                <h3>Success Rate</h3>
                <p style="font-size: 24px; margin: 0;">{test_summary.get('success_rate', 0):.1%}</p>
            </div>
            <div class="summary-card">
                <h3>Total Cycles</h3>
                <p style="font-size: 24px; margin: 0;">{test_summary.get('total_cycles', 0)}</p>
            </div>
            <div class="summary-card success">
                <h3>Passed</h3>
                <p style="font-size: 24px; margin: 0;">{test_summary.get('successful_cycles', 0)}</p>
            </div>
            <div class="summary-card error">
                <h3>Failed</h3>
                <p style="font-size: 24px; margin: 0;">{test_summary.get('failed_cycles', 0)}</p>
            </div>
            <div class="summary-card">
                <h3>UART Data Points</h3>
                <p style="font-size: 24px; margin: 0;">{test_summary.get('total_uart_data_points', 0)}</p>
            </div>
            <div class="summary-card">
                <h3>Validations</h3>
                <p style="font-size: 24px; margin: 0;">{test_summary.get('total_validations', 0)}</p>
            </div>
        </div>
        
        <h2>Cycle Details</h2>
        <table class="cycle-table">
            <thead>
                <tr>
                    <th>Cycle</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>UART Data</th>
                    <th>Validations</th>
                    <th>Errors</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # Add cycle data rows
            if cycle_data:
                for cycle in cycle_data:
                    cycle_num = cycle.get('cycle_number', 0)
                    success = cycle.get('success', False)
                    duration = str(cycle.get('duration', 'N/A'))
                    uart_count = cycle.get('uart_data_count', 0)
                    validation_count = len(cycle.get('validations', []))
                    error_count = len(cycle.get('errors', []))
                    
                    status_class = 'status-pass' if success else 'status-fail'
                    status_text = 'PASSED' if success else 'FAILED'
                    
                    html_content += f"""
                <tr>
                    <td>{cycle_num}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{duration}</td>
                    <td>{uart_count}</td>
                    <td>{validation_count}</td>
                    <td>{error_count}</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
        
        <h2>Statistics</h2>
        <div class="chart-container">
"""
            
            # Add statistics
            if stats:
                for key, value in stats.items():
                    html_content += f"<p><strong>{key}:</strong> {value}</p>\n"
            
            html_content += f"""
        </div>
        
        <div class="footer">
            <p>Report generated by Automated Power Cycle and UART Validation Framework</p>
            <p>Session: {test_summary.get('session_timestamp', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
"""
            
            with open(filepath, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            self.logger.info(f"HTML report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return None
    
    def _calculate_statistics(self, test_summary: Dict, cycle_data: List[Dict] = None,
                            validation_results: List[Dict] = None) -> Dict[str, Any]:
        """Calculate additional statistics for reports."""
        stats = {}
        
        try:
            if cycle_data:
                # Calculate cycle duration statistics
                durations = []
                for cycle in cycle_data:
                    if 'duration' in cycle and cycle['duration']:
                        durations.append(cycle['duration'])
                
                if durations:
                    # Convert to seconds for calculation
                    duration_seconds = []
                    for duration in durations:
                        if hasattr(duration, 'total_seconds'):
                            duration_seconds.append(duration.total_seconds())
                    
                    if duration_seconds:
                        stats['min_cycle_duration'] = f"{min(duration_seconds):.2f}s"
                        stats['max_cycle_duration'] = f"{max(duration_seconds):.2f}s"
                        stats['avg_cycle_duration'] = f"{sum(duration_seconds)/len(duration_seconds):.2f}s"
                
                # Calculate validation success rates by pattern
                pattern_stats = {}
                for cycle in cycle_data:
                    for validation in cycle.get('validations', []):
                        pattern_name = validation.get('pattern_name', 'unknown')
                        if pattern_name not in pattern_stats:
                            pattern_stats[pattern_name] = {'total': 0, 'successful': 0}
                        
                        pattern_stats[pattern_name]['total'] += 1
                        if validation.get('success', False):
                            pattern_stats[pattern_name]['successful'] += 1
                
                for pattern_name, data in pattern_stats.items():
                    success_rate = data['successful'] / data['total'] if data['total'] > 0 else 0
                    stats[f'{pattern_name}_success_rate'] = f"{success_rate:.1%}"
            
            # Overall test health score
            success_rate = test_summary.get('success_rate', 0)
            if success_rate >= 0.95:
                stats['test_health'] = 'Excellent'
            elif success_rate >= 0.8:
                stats['test_health'] = 'Good'
            elif success_rate >= 0.6:
                stats['test_health'] = 'Fair'
            else:
                stats['test_health'] = 'Poor'
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
        
        return stats
    
    def _serialize_datetime(self, obj):
        """Recursively serialize datetime objects to strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        else:
            return obj


# Example usage
if __name__ == "__main__":
    # Example test data
    test_summary = {
        'test_name': 'Power Cycle Test',
        'session_timestamp': '2024-01-15_14-30-00',
        'test_start_time': '2024-01-15T14:30:00',
        'test_end_time': '2024-01-15T14:45:00',
        'total_cycles': 3,
        'successful_cycles': 2,
        'failed_cycles': 1,
        'success_rate': 0.67,
        'total_uart_data_points': 15,
        'total_validations': 9,
        'total_errors': 2
    }
    
    cycle_data = [
        {
            'cycle_number': 1,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'success': True,
            'duration': datetime.now() - datetime.now(),
            'uart_data_count': 5,
            'validations': [
                {'pattern_name': 'boot_test', 'success': True, 'timestamp': datetime.now()},
                {'pattern_name': 'ready_test', 'success': True, 'timestamp': datetime.now()}
            ],
            'errors': []
        },
        {
            'cycle_number': 2,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'success': True,
            'duration': datetime.now() - datetime.now(),
            'uart_data_count': 5,
            'validations': [
                {'pattern_name': 'boot_test', 'success': True, 'timestamp': datetime.now()},
                {'pattern_name': 'ready_test', 'success': True, 'timestamp': datetime.now()}
            ],
            'errors': []
        },
        {
            'cycle_number': 3,
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'success': False,
            'duration': datetime.now() - datetime.now(),
            'uart_data_count': 5,
            'validations': [
                {'pattern_name': 'boot_test', 'success': False, 'timestamp': datetime.now()},
                {'pattern_name': 'ready_test', 'success': False, 'timestamp': datetime.now()}
            ],
            'errors': [
                {'message': 'Boot sequence timeout', 'timestamp': datetime.now()}
            ]
        }
    ]
    
    # Example configuration
    config = {
        'output': {
            'report_directory': 'reports',
            'csv_filename': 'test_results.csv',
            'json_filename': 'test_results.json',
            'text_filename': 'test_summary.txt'
        }
    }
    
    # Generate reports
    generator = ReportGenerator(config)
    report_files = generator.generate_comprehensive_report(test_summary, cycle_data)
    
    print("Generated report files:")
    for format_type, filepath in report_files.items():
        print(f"  {format_type.upper()}: {filepath}")
