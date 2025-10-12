#!/usr/bin/env python3
"""
Xilinx JTAG Interface Example Scripts

This script demonstrates various JTAG operations using the Xilinx JTAG library.
It includes examples for:
- Device detection and enumeration
- Device reset operations
- Bitstream programming
- Memory read/write operations
- Device status monitoring

Usage:
    python examples/xilinx_jtag_demo.py [config_file]

Author: Automated Test Framework
Version: 1.0.0
"""

import sys
import os
import json
import logging
import time
from pathlib import Path

# Add the libs directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs'))

from xilinx_jtag import (
    XilinxJTAGInterface, 
    JTAGConfig, 
    JTAGInterface, 
    DeviceState,
    load_jtag_config,
    XilinxJTAGError
)


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('jtag_demo.log')
        ]
    )


def demo_device_detection(jtag: XilinxJTAGInterface):
    """Demonstrate device detection and enumeration."""
    print("\n" + "="*60)
    print("DEVICE DETECTION DEMO")
    print("="*60)
    
    try:
        # Scan for devices
        devices = jtag.scan_devices()
        
        if not devices:
            print("❌ No JTAG devices found")
            return False
        
        print(f"✅ Found {len(devices)} JTAG device(s):")
        
        for device in devices:
            print(f"\nDevice {device.index}:")
            print(f"  Name: {device.name}")
            print(f"  ID Code: {device.idcode}")
            print(f"  State: {device.state.value}")
            print(f"  Interface: {device.interface.value}")
            print(f"  Description: {device.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during device detection: {e}")
        return False


def demo_device_reset(jtag: XilinxJTAGInterface, device_index: int = 0):
    """Demonstrate device reset functionality."""
    print("\n" + "="*60)
    print("DEVICE RESET DEMO")
    print("="*60)
    
    try:
        print(f"Resetting device {device_index}...")
        
        # Get initial status
        initial_status = jtag.get_device_status(device_index)
        print(f"Initial device status: {initial_status.value if initial_status else 'Unknown'}")
        
        # Perform reset
        success = jtag.reset_device(device_index)
        
        if success:
            print("✅ Device reset successful")
            
            # Wait a moment and check status
            time.sleep(1)
            final_status = jtag.get_device_status(device_index)
            print(f"Final device status: {final_status.value if final_status else 'Unknown'}")
            
        else:
            print("❌ Device reset failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during device reset: {e}")
        return False


def demo_memory_operations(jtag: XilinxJTAGInterface, device_index: int = 0):
    """Demonstrate memory read/write operations."""
    print("\n" + "="*60)
    print("MEMORY OPERATIONS DEMO")
    print("="*60)
    
    try:
        test_address = 0x40000000
        test_data = b'\x12\x34\x56\x78'
        
        print(f"Testing memory operations on device {device_index}")
        print(f"Test address: 0x{test_address:x}")
        print(f"Test data: {test_data.hex()}")
        
        # Write test data
        print("\nWriting test data...")
        write_success = jtag.write_memory(device_index, test_address, test_data)
        
        if write_success:
            print("✅ Memory write successful")
            
            # Read back the data
            print("Reading back data...")
            read_data = jtag.read_memory(device_index, test_address, len(test_data))
            
            if read_data:
                print(f"✅ Memory read successful")
                print(f"Read data: {read_data.hex()}")
                
                # Compare data
                if read_data == test_data:
                    print("✅ Data verification successful - read data matches written data")
                else:
                    print("❌ Data verification failed - read data does not match written data")
                    print(f"Expected: {test_data.hex()}")
                    print(f"Actual: {read_data.hex()}")
            else:
                print("❌ Memory read failed")
        else:
            print("❌ Memory write failed")
        
        return write_success
        
    except Exception as e:
        print(f"❌ Error during memory operations: {e}")
        return False


def demo_bitstream_programming(jtag: XilinxJTAGInterface, device_index: int = 0, bitstream_path: str = None):
    """Demonstrate bitstream programming."""
    print("\n" + "="*60)
    print("BITSTREAM PROGRAMMING DEMO")
    print("="*60)
    
    if not bitstream_path:
        print("⚠️  No bitstream path provided - skipping programming demo")
        print("To test programming, provide a valid .bit file path")
        return True
    
    if not os.path.exists(bitstream_path):
        print(f"❌ Bitstream file not found: {bitstream_path}")
        return False
    
    try:
        print(f"Programming device {device_index} with bitstream: {bitstream_path}")
        
        # Program the device
        success = jtag.program_device(device_index, bitstream_path)
        
        if success:
            print("✅ Bitstream programming successful")
        else:
            print("❌ Bitstream programming failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during bitstream programming: {e}")
        return False


def demo_device_status_monitoring(jtag: XilinxJTAGInterface, device_index: int = 0):
    """Demonstrate device status monitoring."""
    print("\n" + "="*60)
    print("DEVICE STATUS MONITORING DEMO")
    print("="*60)
    
    try:
        print(f"Monitoring device {device_index} status...")
        
        # Monitor status for a few cycles
        for i in range(5):
            status = jtag.get_device_status(device_index)
            status_str = status.value if status else "Unknown"
            print(f"Cycle {i+1}: Device status = {status_str}")
            time.sleep(1)
        
        print("✅ Status monitoring completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during status monitoring: {e}")
        return False


def run_comprehensive_test(jtag: XilinxJTAGInterface, config_file: str = None):
    """Run a comprehensive test of all JTAG functionality."""
    print("\n" + "="*80)
    print("COMPREHENSIVE JTAG FUNCTIONALITY TEST")
    print("="*80)
    
    results = {
        'device_detection': False,
        'device_reset': False,
        'memory_operations': False,
        'bitstream_programming': False,
        'status_monitoring': False
    }
    
    # Load configuration if provided
    bitstream_path = None
    device_index = 0
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Extract test parameters
            if 'devices' in config_data and len(config_data['devices']) > 0:
                device_config = config_data['devices'][0]
                device_index = device_config.get('device_index', 0)
                bitstream_path = device_config.get('bitstream_path')
            
            print(f"Using configuration from: {config_file}")
            print(f"Target device index: {device_index}")
            if bitstream_path:
                print(f"Bitstream path: {bitstream_path}")
            
        except Exception as e:
            print(f"⚠️  Error loading configuration: {e}")
            print("Using default parameters")
    
    # Run all demos
    try:
        # Device detection
        results['device_detection'] = demo_device_detection(jtag)
        
        if results['device_detection']:
            # Device reset
            results['device_reset'] = demo_device_reset(jtag, device_index)
            
            # Memory operations
            results['memory_operations'] = demo_memory_operations(jtag, device_index)
            
            # Bitstream programming (if bitstream provided)
            if bitstream_path:
                results['bitstream_programming'] = demo_bitstream_programming(jtag, device_index, bitstream_path)
            else:
                results['bitstream_programming'] = demo_bitstream_programming(jtag, device_index)
            
            # Status monitoring
            results['status_monitoring'] = demo_device_status_monitoring(jtag, device_index)
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed successfully!")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during comprehensive test: {e}")
        return results


def main():
    """Main function to run JTAG demos."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Xilinx JTAG Interface Demo")
    parser.add_argument(
        '--config', 
        default='config/xilinx_jtag_config.json',
        help='Configuration file path'
    )
    parser.add_argument(
        '--interface',
        choices=['anxsct', 'xsdb'],
        default='anxsct',
        help='JTAG interface to use'
    )
    parser.add_argument(
        '--executable-path',
        help='Path to JTAG executable'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--test',
        choices=['detection', 'reset', 'memory', 'programming', 'status', 'all'],
        default='all',
        help='Specific test to run'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    # Create JTAG configuration
    config = JTAGConfig(
        interface=JTAGInterface(args.interface),
        executable_path=args.executable_path,
        verbose_logging=args.verbose
    )
    
    print("Xilinx JTAG Interface Demo")
    print("="*40)
    print(f"Interface: {config.interface.value}")
    print(f"Executable: {config.executable_path or 'Auto-detect'}")
    print(f"Verbose: {config.verbose_logging}")
    print(f"Test: {args.test}")
    
    try:
        # Connect to JTAG interface
        with XilinxJTAGInterface(config) as jtag:
            print("✅ Connected to JTAG interface")
            
            # Run specific test or comprehensive test
            if args.test == 'all':
                run_comprehensive_test(jtag, args.config)
            elif args.test == 'detection':
                demo_device_detection(jtag)
            elif args.test == 'reset':
                demo_device_reset(jtag)
            elif args.test == 'memory':
                demo_memory_operations(jtag)
            elif args.test == 'programming':
                demo_bitstream_programming(jtag)
            elif args.test == 'status':
                demo_device_status_monitoring(jtag)
    
    except XilinxJTAGError as e:
        print(f"❌ JTAG Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
