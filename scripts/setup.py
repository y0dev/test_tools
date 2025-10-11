#!/usr/bin/env python3
"""
Quick setup script for the Automated Power Cycle and UART Validation Framework.
This script helps users get started quickly by setting up the project structure.
"""

import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        'output',
        'output/logs',
        'output/reports',
        'config',
        'examples',
        'docs',
        'scripts'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory created: {directory}")


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import pyserial
        import pyvisa
        print("✅ Required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False


def generate_sample_files():
    """Generate sample configuration files."""
    try:
        # Import main module
        sys.path.append('.')
        from main import generate_sample_config, generate_sample_templates
        
        print("Generating sample configuration files...")
        generate_sample_config()
        generate_sample_templates()
        
        print("✅ Sample files generated successfully")
        return True
    except Exception as e:
        print(f"❌ Error generating sample files: {e}")
        return False


def show_next_steps():
    """Show next steps for the user."""
    print("\n" + "=" * 60)
    print("SETUP COMPLETE - NEXT STEPS")
    print("=" * 60)
    
    print("\n1. Edit Configuration Files:")
    print("   - config/config.json - Main configuration")
    print("   - config/test_templates.json - Test templates")
    
    print("\n2. Run Tests:")
    print("   python main.py --interactive")
    
    print("\n3. Analyze Logs:")
    print("   python main.py --parse-logs")
    
    print("\n4. View Examples:")
    print("   python examples/template_demo.py")
    print("   python examples/log_parsing_demo.py")
    
    print("\n5. Read Documentation:")
    print("   - docs/README.md - Detailed documentation")
    print("   - docs/configuration_guide.md - Configuration guide")
    print("   - docs/usage_guide.md - Usage guide")
    
    print("\n6. Available Commands:")
    print("   python main.py --help")


def main():
    """Main setup function."""
    print("=" * 60)
    print("AUTOMATED POWER CYCLE AND UART VALIDATION FRAMEWORK")
    print("QUICK SETUP SCRIPT")
    print("=" * 60)
    
    # Create directories
    print("\n1. Creating directories...")
    create_directories()
    
    # Check dependencies
    print("\n2. Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Setup incomplete due to missing dependencies")
        return False
    
    # Generate sample files
    print("\n3. Generating sample files...")
    if not generate_sample_files():
        print("\n❌ Setup incomplete due to file generation errors")
        return False
    
    # Show next steps
    show_next_steps()
    
    print("\n✅ Setup completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
