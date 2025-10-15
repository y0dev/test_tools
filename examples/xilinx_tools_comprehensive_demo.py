#!/usr/bin/env python3
"""
Xilinx Tools Comprehensive Demo

This script demonstrates all the enhanced Xilinx tools functionality including:
- Multiple tool path management
- Bootgen operations for generating boot.bin files
- Vivado project integration for bitstream generation
- ELF file association with projects
- JTAG operations with configurable tool paths

Usage:
    python examples/xilinx_tools_comprehensive_demo.py [config_file]

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

from xilinx_tools_manager import (
    XilinxToolsManager, 
    XilinxToolsConfig, 
    load_xilinx_tools_config,
    create_sample_xilinx_tools_config
)


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('xilinx_tools_demo.log')
        ]
    )


def demo_tool_path_resolution(manager: XilinxToolsManager):
    """Demonstrate tool path resolution."""
    print("\n" + "="*60)
    print("TOOL PATH RESOLUTION DEMO")
    print("="*60)
    
    try:
        # Resolve all tool paths
        resolved_paths = manager.resolve_tool_paths()
        
        print("Resolved tool paths:")
        for tool_name, path in resolved_paths.items():
            if path:
                print(f"  ✅ {tool_name}: {path}")
            else:
                print(f"  ❌ {tool_name}: Not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during tool path resolution: {e}")
        return False


def demo_bootgen_operations(manager: XilinxToolsManager):
    """Demonstrate bootgen operations."""
    print("\n" + "="*60)
    print("BOOTGEN OPERATIONS DEMO")
    print("="*60)
    
    try:
        # Initialize bootgen
        if not manager.initialize_bootgen():
            print("❌ Failed to initialize bootgen")
            return False
        
        print("✅ Bootgen initialized successfully")
        
        # Create a simple FSBL boot image configuration
        fsbl_config = {
            "output_file": "demo_boot.bin",
            "boot_mode": "sd",
            "arch": "zynq",
            "boot_device": "sd0",
            "verbose": True,
            "components": [
                {
                    "name": "fsbl",
                    "type": "fsbl",
                    "file_path": "./boot_images/fsbl.elf"
                },
                {
                    "name": "bitstream",
                    "type": "bitstream",
                    "file_path": "./bitstreams/design.bit"
                }
            ]
        }
        
        print("Boot image configuration:")
        print(json.dumps(fsbl_config, indent=2))
        
        # Note: This would fail if the files don't exist, but demonstrates the API
        print("\nNote: Boot image generation requires actual FSBL and bitstream files")
        print("To test with real files, ensure the following exist:")
        print("  - ./boot_images/fsbl.elf")
        print("  - ./bitstreams/design.bit")
        
        # Uncomment the following lines to actually generate boot image:
        # success = manager.generate_boot_image(fsbl_config)
        # if success:
        #     print("✅ Boot image generated successfully")
        # else:
        #     print("❌ Failed to generate boot image")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during bootgen operations: {e}")
        return False


def demo_vivado_operations(manager: XilinxToolsManager):
    """Demonstrate Vivado operations."""
    print("\n" + "="*60)
    print("VIVADO OPERATIONS DEMO")
    print("="*60)
    
    try:
        # Add a sample project (this would fail if project doesn't exist)
        sample_project_path = "./projects/sample_project.xpr"
        
        print(f"Attempting to add Vivado project: {sample_project_path}")
        print("Note: This will fail if the project file doesn't exist")
        
        # Uncomment the following lines to test with real project:
        # success = manager.add_vivado_project(
        #     "sample_project",
        #     sample_project_path,
        #     "ps7_cortexa9_0"
        # )
        # 
        # if success:
        #     print("✅ Vivado project added successfully")
        #     
        #     # Generate bitstream
        #     print("Generating bitstream...")
        #     bitstream_path = manager.generate_vivado_bitstream("sample_project")
        #     
        #     if bitstream_path:
        #         print(f"✅ Bitstream generated: {bitstream_path}")
        #     else:
        #         print("❌ Failed to generate bitstream")
        # else:
        #     print("❌ Failed to add Vivado project")
        
        print("To test Vivado operations, ensure you have:")
        print("  - A valid Vivado project (.xpr file)")
        print("  - Vivado installed and in PATH")
        print("  - Project configured for bitstream generation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Vivado operations: {e}")
        return False


def demo_jtag_operations(manager: XilinxToolsManager):
    """Demonstrate JTAG operations."""
    print("\n" + "="*60)
    print("JTAG OPERATIONS DEMO")
    print("="*60)
    
    try:
        # Initialize JTAG interface
        if not manager.initialize_jtag_interface():
            print("❌ Failed to initialize JTAG interface")
            return False
        
        print("✅ JTAG interface initialized successfully")
        
        # Define some sample JTAG operations
        operations = [
            {
                "type": "scan",
                "description": "Scan for JTAG devices"
            },
            {
                "type": "reset",
                "device_index": 0,
                "description": "Reset device 0"
            },
            {
                "type": "program",
                "device_index": 0,
                "bitstream_path": "./bitstreams/design.bit",
                "description": "Program device 0 with bitstream"
            }
        ]
        
        print("Sample JTAG operations:")
        for i, op in enumerate(operations):
            print(f"  {i+1}. {op['description']}")
        
        # Run JTAG operations
        print("\nRunning JTAG operations...")
        results = manager.run_jtag_operations(operations)
        
        print("JTAG operation results:")
        for i, result in enumerate(results):
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            print(f"  {i+1}. {result['type']}: {status}")
            if result.get('error'):
                print(f"     Error: {result['error']}")
            if result.get('devices'):
                print(f"     Devices found: {len(result['devices'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during JTAG operations: {e}")
        return False


def demo_configuration_management():
    """Demonstrate configuration management."""
    print("\n" + "="*60)
    print("CONFIGURATION MANAGEMENT DEMO")
    print("="*60)
    
    try:
        # Create sample configuration
        config = create_sample_xilinx_tools_config()
        
        print("Sample configuration created:")
        print(json.dumps(config, indent=2))
        
        # Save configuration
        config_file = "config/sample_xilinx_tools_config.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Sample configuration saved: {config_file}")
        
        # Load configuration
        loaded_config = load_xilinx_tools_config(config_file)
        print("✅ Configuration loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during configuration management: {e}")
        return False


def run_comprehensive_demo(config_file: str = None):
    """Run comprehensive demo of all Xilinx tools functionality."""
    print("\n" + "="*80)
    print("XILINX TOOLS COMPREHENSIVE DEMO")
    print("="*80)
    
    results = {
        'configuration_management': False,
        'tool_path_resolution': False,
        'bootgen_operations': False,
        'vivado_operations': False,
        'jtag_operations': False
    }
    
    try:
        # Configuration management
        results['configuration_management'] = demo_configuration_management()
        
        # Create tools manager
        if config_file and os.path.exists(config_file):
            config = load_xilinx_tools_config(config_file)
            print(f"Using configuration from: {config_file}")
        else:
            config = XilinxToolsConfig(
                tool_paths={
                    "anxsct": ["anxsct"],
                    "xsdb": ["xsdb"],
                    "bootgen": ["bootgen"],
                    "vivado": ["vivado"]
                }
            )
            print("Using default configuration")
        
        manager = XilinxToolsManager(config)
        
        # Tool path resolution
        results['tool_path_resolution'] = demo_tool_path_resolution(manager)
        
        # Bootgen operations
        results['bootgen_operations'] = demo_bootgen_operations(manager)
        
        # Vivado operations
        results['vivado_operations'] = demo_vivado_operations(manager)
        
        # JTAG operations
        results['jtag_operations'] = demo_jtag_operations(manager)
        
        # Get final status
        status = manager.get_status()
        print("\n" + "="*60)
        print("FINAL STATUS")
        print("="*60)
        print(json.dumps(status, indent=2))
        
        # Print summary
        print("\n" + "="*80)
        print("DEMO SUMMARY")
        print("="*80)
        
        total_demos = len(results)
        successful_demos = sum(1 for result in results.values() if result)
        
        for demo_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{demo_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Result: {successful_demos}/{total_demos} demos passed")
        
        if successful_demos == total_demos:
            print("🎉 All demos passed successfully!")
        else:
            print("⚠️  Some demos failed. Check the output above for details.")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during comprehensive demo: {e}")
        return results
    
    finally:
        # Cleanup
        try:
            manager.cleanup()
            print("✅ Tools manager cleaned up")
        except:
            pass


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Xilinx Tools Comprehensive Demo")
    parser.add_argument(
        '--config',
        help='Configuration file path'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--demo',
        choices=['all', 'config', 'paths', 'bootgen', 'vivado', 'jtag'],
        default='all',
        help='Specific demo to run'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    print("Xilinx Tools Comprehensive Demo")
    print("="*40)
    print(f"Configuration: {args.config or 'Default'}")
    print(f"Demo: {args.demo}")
    print(f"Verbose: {args.verbose}")
    
    try:
        if args.demo == 'all':
            success = run_comprehensive_demo(args.config)
        else:
            # Run specific demo
            config = None
            if args.config and os.path.exists(args.config):
                config = load_xilinx_tools_config(args.config)
            else:
                config = XilinxToolsConfig(tool_paths={
                    "anxsct": ["anxsct"],
                    "xsdb": ["xsdb"],
                    "bootgen": ["bootgen"],
                    "vivado": ["vivado"]
                })
            
            manager = XilinxToolsManager(config)
            
            if args.demo == 'config':
                demo_configuration_management()
            elif args.demo == 'paths':
                demo_tool_path_resolution(manager)
            elif args.demo == 'bootgen':
                demo_bootgen_operations(manager)
            elif args.demo == 'vivado':
                demo_vivado_operations(manager)
            elif args.demo == 'jtag':
                demo_jtag_operations(manager)
            
            manager.cleanup()
    
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
