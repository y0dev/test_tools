#!/usr/bin/env python3
"""
Python 3.7 Wheel Installation Script
This script helps install the downloaded wheels for Python 3.7 compatibility.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if running Python 3.7."""
    if sys.version_info[:2] != (3, 7):
        print(f"❌ This script is designed for Python 3.7, but you're running Python {sys.version_info.major}.{sys.version_info.minor}")
        print("Please run this script with Python 3.7")
        return False
    print(f"✅ Running Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_from_wheels():
    """Install packages from the wheels directory."""
    wheels_dir = Path("wheels")
    requirements_file = Path("requirements_python37.txt")
    
    if not wheels_dir.exists():
        print("❌ Wheels directory not found. Please run the wheel download first.")
        return False
    
    if not requirements_file.exists():
        print("❌ Python 3.7 requirements file not found.")
        return False
    
    print("📦 Installing packages from wheels...")
    print(f"Wheels directory: {wheels_dir.absolute()}")
    print(f"Requirements file: {requirements_file.absolute()}")
    print()
    
    try:
        # Install from wheels directory
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--find-links", str(wheels_dir),
            "--no-index",
            "-r", str(requirements_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Installation completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Installation failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during installation: {e}")
        return False

def list_available_wheels():
    """List all available wheels."""
    wheels_dir = Path("wheels")
    
    if not wheels_dir.exists():
        print("❌ Wheels directory not found.")
        return
    
    print("📦 Available wheels:")
    print("-" * 50)
    
    wheel_files = list(wheels_dir.glob("*.whl"))
    wheel_files.sort()
    
    for wheel_file in wheel_files:
        print(f"  {wheel_file.name}")
    
    print(f"\nTotal: {len(wheel_files)} wheel files")

def install_core_packages():
    """Install only core packages."""
    wheels_dir = Path("wheels")
    
    if not wheels_dir.exists():
        print("❌ Wheels directory not found.")
        return False
    
    core_packages = [
        "pyserial-3.5-py2.py3-none-any.whl",
        "numpy-1.21.6-cp37-cp37m-win_amd64.whl",
        "PyVISA-1.12.0-py3-none-any.whl",
        "psutil-7.1.0-cp37-abi3-win_amd64.whl",
        "typing_extensions-4.7.1-py3-none-any.whl"
    ]
    
    print("📦 Installing core packages...")
    
    try:
        for package in core_packages:
            wheel_path = wheels_dir / package
            if wheel_path.exists():
                print(f"Installing {package}...")
                cmd = [sys.executable, "-m", "pip", "install", "--find-links", str(wheels_dir), "--no-index", str(wheel_path)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ {package} installed successfully")
                else:
                    print(f"❌ Failed to install {package}")
                    print(result.stderr)
            else:
                print(f"❌ Wheel not found: {package}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error installing core packages: {e}")
        return False

def main():
    """Main function."""
    print("Python 3.7 Wheel Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    print()
    print("Options:")
    print("1. List available wheels")
    print("2. Install core packages only")
    print("3. Install all packages from requirements")
    print("4. Exit")
    print()
    
    while True:
        try:
            choice = input("Select an option (1-4): ").strip()
            
            if choice == '1':
                list_available_wheels()
            elif choice == '2':
                install_core_packages()
            elif choice == '3':
                install_from_wheels()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
