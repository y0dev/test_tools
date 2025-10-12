#!/usr/bin/env python3
"""
Xilinx JTAG Integration Script

This script demonstrates how to integrate the Xilinx JTAG library
with the existing test framework. It shows how to:
- Connect to JTAG devices
- Perform JTAG operations during power cycling
- Generate comprehensive test reports

Usage:
    python scripts/jtag_integration_demo.py [config_file]

Author: Automated Test Framework
Version: 1.0.0
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add the libs directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs'))

from jtag_test_runner import JTAGTestRunner, create_jtag_test_config


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('jtag_integration_demo.log')
        ]
    )


def create_sample_config():
    """Create a sample JTAG test configuration."""
    config = create_jtag_test_config()
    
    # Save configuration
    config_file = Path('config/jtag_integration_config.json')
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Sample configuration created: {config_file}")
    return str(config_file)


def run_jtag_integration_test(config_file: str):
    """
    Run a JTAG integration test.
    
    Args:
        config_file: Path to configuration file
    """
    print("\n" + "="*80)
    print("XILINX JTAG INTEGRATION TEST")
    print("="*80)
    
    try:
        # Create test runner
        runner = JTAGTestRunner(config_file)
        
        print("✅ Test runner initialized")
        
        # Initialize components
        print("Initializing components...")
        if not runner.initialize_components():
            print("❌ Failed to initialize components")
            return False
        
        print("✅ Components initialized successfully")
        
        # Run JTAG test
        print("Starting JTAG test...")
        results = runner.run_jtag_test()
        
        if 'error' in results:
            print(f"❌ Test failed: {results['error']}")
            return False
        
        # Display results
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        
        print(f"Overall Success Rate: {results['success_rate']:.2%}")
        print(f"Successful Cycles: {results['successful_cycles']}/{results['total_cycles']}")
        
        if results.get('jtag_results'):
            print(f"JTAG Operations: {len(results['jtag_results'])}")
        
        if results.get('report_files'):
            print("\nReports generated:")
            for format_type, filepath in results['report_files'].items():
                print(f"  {format_type.upper()}: {filepath}")
        
        print("✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            runner.cleanup_components()
            print("✅ Components cleaned up")
        except:
            pass


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Xilinx JTAG Integration Demo")
    parser.add_argument(
        '--config',
        help='Configuration file path (default: create sample config)'
    )
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create sample configuration and exit'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level)
    
    # Create sample config if requested
    if args.create_config:
        create_sample_config()
        return
    
    # Use provided config or create sample
    if args.config:
        config_file = args.config
    else:
        print("No configuration file provided. Creating sample configuration...")
        config_file = create_sample_config()
    
    # Check if config file exists
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return
    
    # Run the test
    success = run_jtag_integration_test(config_file)
    
    if success:
        print("\n🎉 JTAG integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ JTAG integration test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
