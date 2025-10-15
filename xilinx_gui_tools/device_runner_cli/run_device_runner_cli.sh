#!/bin/bash
# Launch Device Runner CLI (Linux/Mac)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Device Runner CLI..."
echo

# Check if Tcl is available
if ! command -v tclsh &> /dev/null; then
    echo "ERROR: Tcl/Tk not found in PATH"
    echo "Please install Tcl/Tk or add it to your PATH"
    echo
    echo "On Ubuntu/Debian: sudo apt-get install tcl"
    echo "On CentOS/RHEL: sudo yum install tcl"
    echo "On macOS: brew install tcl-tk"
    echo
    exit 1
fi

echo "Tcl/Tk found, launching Device Runner CLI..."
echo

# Launch the CLI application
tclsh "$SCRIPT_DIR/device_runner_cli.tcl" "$@"

echo
echo "Device Runner CLI exited"
