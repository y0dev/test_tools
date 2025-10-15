#!/usr/bin/env python3
"""
Test Script for Serial Logger Data Parsing
This script demonstrates parsing the test data format and outputting to CSV, JSON, and TXT files.
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import re

# Add the libs directory to the path
sys.path.append(str(Path(__file__).parent.parent / "libs"))

from libs.serial_logger import SerialDataParser
from libs.output_manager import get_output_manager

def test_data_parsing():
    """Test the data parsing functionality with sample data."""
    print("=== Serial Logger Data Parsing Test ===")
    print()
    
    # Load the test configuration
    config_file = "config/serial_logger_test_config.json"
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    print(f"✅ Loaded configuration: {config['metadata']['name']}")
    print(f"   Description: {config['metadata']['description']}")
    print(f"   Patterns: {len(config['data_parsing']['patterns'])}")
    print()
    
    # Create parser
    parser = SerialDataParser(config)
    
    # Test with sample data
    test_file = "test_data/sample_test_log.txt"
    if not os.path.exists(test_file):
        print(f"❌ Test data file not found: {test_file}")
        return False
    
    print(f"📄 Parsing test data from: {test_file}")
    
    # Parse the data manually (since our test data format is different)
    results = []
    with open(test_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Create a dummy timestamp for testing
            timestamp = datetime.now()
            
            # Parse the line
            parsed_result = parser.parse_line(line, timestamp)
            if parsed_result:
                parsed_result['line_number'] = line_num
                parsed_result['pattern'] = parsed_result['pattern_name']
                parsed_result['data'] = line
                parsed_result['extracted_values'] = parsed_result['parsed_data']
                results.append(parsed_result)
    
    if not results:
        print("❌ No data could be parsed")
        return False
    
    print(f"✅ Parsed {len(results)} entries")
    print()
    
    # Display summary
    parser.display_summary(results)
    print()
    
    # Save results in different formats
    output_manager = get_output_manager()
    file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON output
    json_path = output_manager.get_parsed_data_path("serial_test", "json")
    
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📄 JSON output saved to: {json_path}")
    
    # CSV output
    csv_path = output_manager.get_parsed_data_path("serial_test", "csv")
    
    # Group results by pattern type for CSV
    pattern_groups = {}
    for result in results:
        pattern_name = result.get('pattern', 'unknown')
        if pattern_name not in pattern_groups:
            pattern_groups[pattern_name] = []
        pattern_groups[pattern_name].append(result)
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['Pattern', 'Timestamp', 'Data', 'Extracted_Values'])
        
        # Write data
        for pattern_name, pattern_results in pattern_groups.items():
            for result in pattern_results:
                timestamp = result.get('timestamp', '')
                data = result.get('data', '')
                extracted = result.get('extracted_values', {})
                
                # Convert extracted values to string
                extracted_str = ', '.join([f"{k}={v}" for k, v in extracted.items()])
                
                writer.writerow([pattern_name, timestamp, data, extracted_str])
    
    print(f"📄 CSV output saved to: {csv_path}")
    
    # TXT output (formatted)
    txt_path = output_manager.get_parsed_data_path("serial_test", "txt")
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("Serial Logger Parsing Results\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Entries: {len(results)}\n")
        f.write(f"Patterns Used: {len(pattern_groups)}\n\n")
        
        # Write results by pattern
        for pattern_name, pattern_results in pattern_groups.items():
            f.write(f"Pattern: {pattern_name}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Count: {len(pattern_results)}\n")
            
            for i, result in enumerate(pattern_results[:5]):  # Show first 5 examples
                f.write(f"  {i+1}. [{result.get('timestamp', '')}] {result.get('data', '')}\n")
                extracted = result.get('extracted_values', {})
                if extracted:
                    f.write(f"     Extracted: {extracted}\n")
            
            if len(pattern_results) > 5:
                f.write(f"     ... and {len(pattern_results) - 5} more entries\n")
            
            f.write("\n")
    
    print(f"📄 TXT output saved to: {txt_path}")
    
    # HTML output
    html_path = output_manager.get_parsed_data_path("serial_test", "html")
    parser.save_results(results, str(html_path))
    print(f"📄 HTML output saved to: {html_path}")
    
    # Generate detailed analysis
    analysis_path = output_manager.get_parsed_data_path("serial_analysis", "txt")
    
    with open(analysis_path, 'w', encoding='utf-8') as f:
        f.write("Detailed Analysis Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Test mode analysis
        test_mode_entries = [r for r in results if r.get('pattern') == 'test_mode']
        f.write("Test Mode Analysis:\n")
        f.write("-" * 20 + "\n")
        for entry in test_mode_entries:
            mode = entry.get('extracted_values', {}).get('mode', '')
            timestamp = entry.get('extracted_values', {}).get('timestamp', '')
            f.write(f"  {timestamp}: {mode}\n")
        f.write("\n")
        
        # Test results analysis
        test_pass_entries = [r for r in results if r.get('pattern') == 'test_pass']
        f.write(f"Test Pass Events: {len(test_pass_entries)}\n")
        
        test_start_entries = [r for r in results if r.get('pattern') == 'test_start']
        f.write(f"Test Start Events: {len(test_start_entries)}\n")
        
        test_end_entries = [r for r in results if r.get('pattern') == 'test_end']
        f.write(f"Test End Events: {len(test_end_entries)}\n\n")
        
        # Data analysis
        test_data_entries = [r for r in results if r.get('pattern') == 'test_data']
        f.write("Test Data Analysis:\n")
        f.write("-" * 20 + "\n")
        for entry in test_data_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            data1 = extracted.get('data1', '')
            data2 = extracted.get('data2', '')
            crc = extracted.get('crc', '')
            f.write(f"  {timestamp}: DATA1={data1}, DATA2={data2}, CRC={crc}\n")
        f.write("\n")
        
        # Measurement analysis
        test_info_entries = [r for r in results if r.get('pattern') == 'test_info']
        f.write("Measurement Analysis:\n")
        f.write("-" * 20 + "\n")
        for entry in test_info_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            voltage = extracted.get('voltage', '')
            temperature = extracted.get('temperature', '')
            f.write(f"  {timestamp}: Voltage={voltage}V, Temperature={temperature}°C\n")
        f.write("\n")
        
        # Array analysis
        uint8_entries = [r for r in results if r.get('pattern') == 'uint8_array']
        uint32_entries = [r for r in results if r.get('pattern') == 'uint32_array']
        f.write(f"UINT8 Array Entries: {len(uint8_entries)}\n")
        f.write(f"UINT32 Array Entries: {len(uint32_entries)}\n")
        f.write("\n")
        
        # Summary
        f.write("Summary:\n")
        f.write("-" * 10 + "\n")
        f.write(f"Total parsed entries: {len(results)}\n")
        f.write(f"Unique patterns matched: {len(pattern_groups)}\n")
        f.write(f"Test cycles completed: {len(test_pass_entries)}\n")
        f.write(f"Array tests completed: {len([r for r in results if r.get('pattern') == 'array_test_end'])}\n")
    
    print(f"📄 Analysis report saved to: {analysis_path}")
    
    print(f"\n📊 All output files saved to: {output_manager.base_output_dir / 'parsed_data'}")
    
    print()
    print("=== Test Results ===")
    print(f"✅ Successfully parsed {len(results)} entries")
    print(f"✅ Generated {len(pattern_groups)} different pattern types")
    print(f"✅ Output files created:")
    print(f"   - JSON: {json_file}")
    print(f"   - CSV: {csv_file}")
    print(f"   - TXT: {txt_file}")
    print(f"   - Analysis: {analysis_file}")
    
    return True

def test_pattern_matching():
    """Test individual pattern matching."""
    print("\n=== Pattern Matching Test ===")
    
    # Load configuration
    with open("config/serial_logger_test_config.json", 'r') as f:
        config = json.load(f)
    
    parser = SerialDataParser(config)
    
    # Test patterns
    test_lines = [
        "[01:21:32] UINT8_ARRAY: 0x01 0x02 0x03 0x04 0x05",
        "[01:21:50] DATA: 0x12345678, 0xDEADBEEF, CRC=0xA5A5A5A5",
        "[01:21:50] INFO: Test OK, Voltage=3.30V, Temp=27C",
        "[01:21:50] TEST_PASS",
        "[01:21:37] Test mode: ENABLED"
    ]
    
    print("Testing pattern matching:")
    for line in test_lines:
        print(f"\nTesting: {line}")
        timestamp = datetime.now()
        result = parser.parse_line(line, timestamp)
        if result:
            print(f"  ✅ Matched pattern: {result['pattern_name']}")
            print(f"  📊 Extracted: {result['parsed_data']}")
        else:
            print(f"  ❌ No pattern matched")

if __name__ == "__main__":
    print("Serial Logger Data Parsing Test Suite")
    print("=" * 50)
    
    # Run tests
    success = test_data_parsing()
    
    if success:
        test_pattern_matching()
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
