#!/usr/bin/env python3
"""
Power Supply Test Script with Data Parsing
This script demonstrates parsing power supply test data and outputting to CSV, JSON, and TXT files.
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

def test_power_supply_parsing():
    """Test the power supply data parsing functionality with sample data."""
    print("=== Power Supply Data Parsing Test ===")
    print()
    
    # Load the test configuration
    config_file = "config/power_supply_test_config.json"
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
    test_file = "test_data/sample_power_supply_log.txt"
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
    file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON output
    json_file = f"test_output/power_supply_parsed_{file_timestamp}.json"
    os.makedirs("test_output", exist_ok=True)
    
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📄 JSON output saved to: {json_file}")
    
    # CSV output
    csv_file = f"test_output/power_supply_parsed_{file_timestamp}.csv"
    
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
    
    print(f"📄 CSV output saved to: {csv_file}")
    
    # TXT output (formatted)
    txt_file = f"test_output/power_supply_parsed_{file_timestamp}.txt"
    
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("Power Supply Test Parsing Results\n")
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
    
    print(f"📄 TXT output saved to: {txt_file}")
    
    # Generate detailed analysis
    analysis_file = f"test_output/power_supply_analysis_{file_timestamp}.txt"
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        f.write("Power Supply Test Analysis Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Connection analysis
        connection_entries = [r for r in results if r.get('pattern') == 'connection_status']
        f.write("Connection Analysis:\n")
        f.write("-" * 20 + "\n")
        for entry in connection_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            status = extracted.get('status', '')
            resource = extracted.get('resource', '')
            f.write(f"  {timestamp}: {status} {resource}\n")
        f.write("\n")
        
        # Instrument identification
        id_entries = [r for r in results if r.get('pattern') == 'instrument_id']
        f.write("Instrument Information:\n")
        f.write("-" * 20 + "\n")
        for entry in id_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            instrument_id = extracted.get('instrument_id', '')
            f.write(f"  {timestamp}: {instrument_id}\n")
        f.write("\n")
        
        # Voltage analysis
        voltage_set_entries = [r for r in results if r.get('pattern') == 'voltage_set']
        voltage_measured_entries = [r for r in results if r.get('pattern') == 'voltage_measured']
        f.write("Voltage Analysis:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Voltage Settings: {len(voltage_set_entries)}\n")
        f.write(f"Voltage Measurements: {len(voltage_measured_entries)}\n")
        
        f.write("\nVoltage Settings:\n")
        for entry in voltage_set_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            voltage = extracted.get('voltage', '')
            f.write(f"  {timestamp}: {voltage}V\n")
        
        f.write("\nVoltage Measurements:\n")
        for entry in voltage_measured_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            voltage = extracted.get('voltage', '')
            f.write(f"  {timestamp}: {voltage}V\n")
        f.write("\n")
        
        # Current analysis
        current_set_entries = [r for r in results if r.get('pattern') == 'current_set']
        f.write("Current Analysis:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Current Settings: {len(current_set_entries)}\n")
        for entry in current_set_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            current = extracted.get('current', '')
            f.write(f"  {timestamp}: {current}A\n")
        f.write("\n")
        
        # Cycle analysis
        cycle_start_entries = [r for r in results if r.get('pattern') == 'cycle_start']
        cycle_complete_entries = [r for r in results if r.get('pattern') == 'cycle_complete']
        f.write("Power Cycle Analysis:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Cycle Starts: {len(cycle_start_entries)}\n")
        f.write(f"Cycle Completions: {len(cycle_complete_entries)}\n")
        
        f.write("\nCycle Details:\n")
        for entry in cycle_complete_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            current_cycle = extracted.get('current_cycle', '')
            total_cycles = extracted.get('total_cycles', '')
            duration = extracted.get('duration', '')
            f.write(f"  {timestamp}: Cycle {current_cycle}/{total_cycles} completed in {duration}s\n")
        f.write("\n")
        
        # Ramp cycle analysis
        ramp_start_entries = [r for r in results if r.get('pattern') == 'ramp_cycle_start']
        ramp_complete_entries = [r for r in results if r.get('pattern') == 'ramp_cycle_complete']
        voltage_step_entries = [r for r in results if r.get('pattern') == 'voltage_step']
        f.write("Voltage Ramp Analysis:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Ramp Cycle Starts: {len(ramp_start_entries)}\n")
        f.write(f"Ramp Cycle Completions: {len(ramp_complete_entries)}\n")
        f.write(f"Voltage Steps: {len(voltage_step_entries)}\n")
        
        f.write("\nRamp Cycle Details:\n")
        for entry in ramp_complete_entries:
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            current_cycle = extracted.get('current_cycle', '')
            total_cycles = extracted.get('total_cycles', '')
            duration = extracted.get('duration', '')
            f.write(f"  {timestamp}: Ramp Cycle {current_cycle}/{total_cycles} completed in {duration}s\n")
        
        f.write("\nVoltage Steps:\n")
        for entry in voltage_step_entries[:10]:  # Show first 10 steps
            extracted = entry.get('extracted_values', {})
            timestamp = extracted.get('timestamp', '')
            step = extracted.get('step', '')
            voltage_set = extracted.get('voltage_set', '')
            voltage_measured = extracted.get('voltage_measured', '')
            f.write(f"  {timestamp}: Step {step} - Set: {voltage_set}V, Measured: {voltage_measured}V\n")
        f.write("\n")
        
        # Output control analysis
        output_on_entries = [r for r in results if r.get('pattern') == 'output_on']
        output_off_entries = [r for r in results if r.get('pattern') == 'output_off']
        f.write("Output Control Analysis:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Output ON Events: {len(output_on_entries)}\n")
        f.write(f"Output OFF Events: {len(output_off_entries)}\n")
        f.write("\n")
        
        # Summary
        f.write("Summary:\n")
        f.write("-" * 10 + "\n")
        f.write(f"Total parsed entries: {len(results)}\n")
        f.write(f"Unique patterns matched: {len(pattern_groups)}\n")
        f.write(f"Power cycles completed: {len(cycle_complete_entries)}\n")
        f.write(f"Ramp cycles completed: {len(ramp_complete_entries)}\n")
        f.write(f"Voltage steps executed: {len(voltage_step_entries)}\n")
        f.write(f"Output control events: {len(output_on_entries) + len(output_off_entries)}\n")
    
    print(f"📄 Analysis report saved to: {analysis_file}")
    
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
    with open("config/power_supply_test_config.json", 'r') as f:
        config = json.load(f)
    
    parser = SerialDataParser(config)
    
    # Test patterns
    test_lines = [
        "[01:21:34] Setting voltage to 3.30 V",
        "[01:21:37] Measured voltage: 3.28 V",
        "[01:21:38] Starting cycle 1/3",
        "[01:21:44] Cycle 1/3 completed successfully in 8.50s",
        "[01:21:39] Voltage step 0: 0.00V (measured: 0.00V)",
        "[01:21:33] Instrument identification: Keysight Technologies,E3632A,MY12345678,1.0.0"
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
    print("Power Supply Data Parsing Test Suite")
    print("=" * 50)
    
    # Run tests
    success = test_power_supply_parsing()
    
    if success:
        test_pattern_matching()
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
