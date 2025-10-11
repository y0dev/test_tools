#!/usr/bin/env python3
"""
Example script demonstrating log parsing functionality.
This shows how to analyze existing log files without running the full test system.
"""

import sys
from pathlib import Path

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / 'lib'))

from log_parser import LogParser


def demonstrate_log_parsing():
    """Demonstrate log parsing capabilities."""
    print("=" * 60)
    print("LOG PARSING DEMONSTRATION")
    print("=" * 60)
    
    # Create log parser
    parser = LogParser("./output/logs")
    
    print("\n1. Finding Log Files:")
    print("-" * 30)
    
    log_files = parser.find_log_files()
    
    for category, files in log_files.items():
        if files:
            print(f"{category}: {len(files)} files")
            for file in files:
                print(f"  - {file.name}")
        else:
            print(f"{category}: No files found")
    
    print("\n2. Analyzing Logs:")
    print("-" * 30)
    
    analysis = parser.analyze_logs()
    summary = analysis['summary']
    
    print(f"Total Test Sessions: {summary['total_test_sessions']}")
    print(f"Total Cycles: {summary['total_cycles']}")
    print(f"Successful Cycles: {summary['successful_cycles']}")
    print(f"Failed Cycles: {summary['failed_cycles']}")
    print(f"Success Rate: {summary['success_rate']:.2%}")
    print(f"UART Data Entries: {summary['total_uart_entries']}")
    
    print("\n3. Test Session Details:")
    print("-" * 30)
    
    for i, session in enumerate(analysis['test_sessions'], 1):
        print(f"\nSession {i}: {session['test_name']}")
        print(f"  File: {Path(session['file']).name}")
        print(f"  Cycles: {session['total_cycles']}")
        print(f"  Success Rate: {session['successful_cycles']}/{session['total_cycles']}")
        
        if session['start_time'] and session['end_time']:
            duration = session['end_time'] - session['start_time']
            print(f"  Duration: {duration}")
        
        # Show cycle details
        for cycle in session['cycles']:
            status = "PASS" if cycle.get('success') else "FAIL"
            print(f"    Cycle {cycle['cycle_number']}: {status}")
            
            if cycle.get('validations'):
                print(f"      Validations: {len(cycle['validations'])}")
                for validation in cycle['validations']:
                    pattern_status = "PASS" if validation['success'] else "FAIL"
                    print(f"        {validation['pattern_name']}: {pattern_status}")
            
            if cycle.get('errors'):
                print(f"      Errors: {len(cycle['errors'])}")
                for error in cycle['errors']:
                    print(f"        {error['message']}")
    
    print("\n4. UART Data Sample:")
    print("-" * 30)
    
    uart_data = analysis['uart_data']
    if uart_data:
        print(f"Total UART entries: {len(uart_data)}")
        print("Sample entries:")
        for i, entry in enumerate(uart_data[:5]):  # Show first 5 entries
            print(f"  {i+1}. {entry['timestamp']} - {entry['data']}")
        if len(uart_data) > 5:
            print(f"  ... and {len(uart_data) - 5} more entries")
    else:
        print("No UART data found")
    
    print("\n5. Generating Reports:")
    print("-" * 30)
    
    try:
        # Generate JSON report
        json_report = parser.generate_report_from_logs()
        print(f"JSON report: {json_report}")
        
        # Generate CSV report
        csv_report = parser.export_to_csv()
        print(f"CSV report: {csv_report}")
        
        print("\nReports generated successfully!")
        
    except Exception as e:
        print(f"Error generating reports: {e}")
    
    print("\n6. Benefits of Log Parsing:")
    print("-" * 30)
    print("✅ Analyze historical test data without re-running tests")
    print("✅ Generate reports from existing log files")
    print("✅ Extract test statistics and success rates")
    print("✅ Review UART data patterns and validation results")
    print("✅ Debug test failures from log files")
    print("✅ Export data for further analysis")


def show_cli_usage():
    """Show CLI usage examples."""
    print("\n" + "=" * 60)
    print("CLI USAGE EXAMPLES")
    print("=" * 60)
    
    print("\nParse existing logs:")
    print("  python main.py --parse-logs")
    print("  python main.py --parse-logs --log-dir ./custom/logs")
    
    print("\nGenerate sample files:")
    print("  python main.py --generate-config")
    print("  python main.py --generate-templates")
    
    print("\nList available templates:")
    print("  python main.py --list-templates")
    
    print("\nRun tests with comprehensive logging:")
    print("  python main.py --interactive")
    print("  python main.py --log-level DEBUG")


if __name__ == "__main__":
    try:
        demonstrate_log_parsing()
        show_cli_usage()
        
    except Exception as e:
        print(f"Demonstration error: {e}")
        print("\nThis is expected if no log files exist yet.")
        print("Run some tests first to generate log files, then try again.")
        
        # Show how to create sample log files for testing
        print("\nTo create sample log files for testing:")
        print("1. Run: python main.py --generate-config")
        print("2. Run: python main.py --generate-templates") 
        print("3. Run: python main.py --interactive")
        print("4. Then run this script again to see log parsing in action")
