#!/bin/bash
# Launch Device Runner (Linux/macOS)
# This script launches the Device Runner Tcl/Tk application
#
# Usage:
#   ./run_device_runner.sh [options]
#
# Options:
#   --xsdb-path <path>     Path to XSDB executable
#   --jtag-tcp <host:port> JTAG TCP configuration (e.g., 192.168.1.100:3121)
#   --help                Show this help message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "   Device Runner v1.0.0 - Linux/macOS"
echo "========================================"
echo ""

# Parse command line arguments
XSDB_PATH=""
JTAG_TCP=""
HELP_SHOWN=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --xsdb-path)
            XSDB_PATH="$2"
            shift 2
            ;;
        --jtag-tcp)
            JTAG_TCP="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./run_device_runner.sh [options]"
            echo ""
            echo "Options:"
            echo "  --xsdb-path <path>     Path to XSDB executable"
            echo "  --jtag-tcp <host:port> JTAG TCP configuration"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_device_runner.sh"
            echo "  ./run_device_runner.sh --xsdb-path \"/opt/Xilinx/Vitis/2023.2/bin/xsdb\""
            echo "  ./run_device_runner.sh --jtag-tcp \"192.168.1.100:3121\""
            echo "  ./run_device_runner.sh --xsdb-path \"/opt/Xilinx/Vitis/2023.2/bin/xsdb\" --jtag-tcp \"192.168.1.100:3121\""
            echo ""
            HELP_SHOWN=1
            shift
            ;;
        *)
            # Pass through other arguments
            break
            ;;
    esac
done

# Check if Tcl is available
if ! command -v tclsh &> /dev/null; then
    echo "ERROR: Tcl/Tk is not installed or not in PATH"
    echo "Please install Tcl/Tk and try again"
    echo ""
    echo "Ubuntu/Debian: sudo apt-get install tcl tk"
    echo "CentOS/RHEL:   sudo yum install tcl tk"
    echo "macOS:         brew install tcl-tk"
    echo ""
    exit 1
fi

# Display configuration
if [[ -n "$XSDB_PATH" ]]; then
    echo "XSDB Path: $XSDB_PATH"
fi
if [[ -n "$JTAG_TCP" ]]; then
    echo "JTAG TCP: $JTAG_TCP"
fi

if [[ $HELP_SHOWN -eq 1 ]]; then
    exit 0
fi

echo "Launching Device Runner UI..."
echo ""

# Build command line arguments
ARGS=()
if [[ -n "$XSDB_PATH" ]]; then
    ARGS+=("--xsdb-path" "$XSDB_PATH")
fi
if [[ -n "$JTAG_TCP" ]]; then
    ARGS+=("--jtag-tcp" "$JTAG_TCP")
fi

# Launch the application with any passed arguments
tclsh "$SCRIPT_DIR/device_runner.tcl" "${ARGS[@]}" "$@"

echo ""
echo "Device Runner has exited."
