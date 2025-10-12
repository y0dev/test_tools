#!/usr/bin/env python3
"""
Xilinx JTAG Interface Library

This library provides a Python interface for connecting to and controlling
Xilinx devices through JTAG using anxsct (AMD Xilinx System Control Tool) 
or xsdb (Xilinx Software Debugger) console interfaces.

Key Features:
- Automatic detection of available JTAG devices
- Connection management for anxsct/xsdb consoles
- Common JTAG operations (reset, program, debug)
- Device state monitoring and control
- Error handling and logging
- Support for multiple device types (FPGA, SoC, etc.)

Author: Automated Test Framework
Version: 1.0.0
"""

import subprocess
import time
import logging
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class JTAGInterface(Enum):
    """Enumeration of supported JTAG interfaces."""
    ANXSCT = "anxsct"
    XSDB = "xsdb"


class DeviceState(Enum):
    """Enumeration of device states."""
    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RUNNING = "running"
    HALTED = "halted"
    RESET = "reset"


@dataclass
class JTAGDevice:
    """Data class representing a JTAG device."""
    index: int
    name: str
    idcode: str
    state: DeviceState
    interface: JTAGInterface
    description: str = ""


@dataclass
class JTAGConfig:
    """Configuration for JTAG operations."""
    interface: JTAGInterface = JTAGInterface.ANXSCT
    executable_path: Optional[str] = None
    connection_timeout: int = 30
    command_timeout: int = 10
    auto_connect: bool = True
    verbose_logging: bool = False


class XilinxJTAGError(Exception):
    """Custom exception for JTAG-related errors."""
    pass


class XilinxJTAGInterface:
    """
    Main class for interfacing with Xilinx JTAG devices.
    
    This class provides a high-level interface for connecting to and controlling
    Xilinx devices through JTAG. It supports both anxsct and xsdb console interfaces
    and provides methods for common operations like device detection, programming,
    debugging, and monitoring.
    """
    
    def __init__(self, config: Optional[JTAGConfig] = None):
        """
        Initialize the Xilinx JTAG interface.
        
        Args:
            config: Configuration object for JTAG operations. If None, uses defaults.
        """
        self.config = config or JTAGConfig()
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
        self.connected_devices: List[JTAGDevice] = []
        self.is_connected = False
        
        # Set up logging
        if self.config.verbose_logging:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def _find_executable(self, tool_paths_config: Optional[Dict[str, List[str]]] = None) -> str:
        """
        Find the appropriate JTAG executable (anxsct or xsdb).
        
        Args:
            tool_paths_config: Optional tool paths configuration
            
        Returns:
            Path to the executable
            
        Raises:
            XilinxJTAGError: If executable cannot be found
        """
        executable_name = self.config.interface.value
        
        # Check if path is explicitly provided
        if self.config.executable_path:
            if os.path.exists(self.config.executable_path):
                return self.config.executable_path
            else:
                raise XilinxJTAGError(f"Specified executable not found: {self.config.executable_path}")
        
        # Use configured tool paths if available
        if tool_paths_config and executable_name in tool_paths_config:
            for path in tool_paths_config[executable_name]:
                if os.path.exists(path):
                    self.logger.debug(f"Found {executable_name} at: {path}")
                    return path
                elif path == executable_name:  # Generic name, check PATH
                    try:
                        result = subprocess.run(
                            ["which", path] if os.name != "nt" else ["where", path],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            return path
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
        
        # Fallback to common installation paths
        common_paths = [
            # Windows paths
            r"C:\Xilinx\Vitis\*\bin\anxsct.exe",
            r"C:\Xilinx\SDK\*\bin\xsdb.exe",
            r"C:\Xilinx\Vivado\*\bin\xsdb.exe",
            # Linux paths
            "/opt/Xilinx/Vitis/*/bin/anxsct",
            "/opt/Xilinx/SDK/*/bin/xsdb",
            "/opt/Xilinx/Vivado/*/bin/xsdb",
            # Generic paths
            "anxsct",
            "xsdb"
        ]
        
        for path_pattern in common_paths:
            if "*" in path_pattern:
                # Handle wildcard paths
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    return matches[0]  # Use the first match
            else:
                # Check if executable exists in PATH
                try:
                    result = subprocess.run(
                        ["which", path_pattern] if os.name != "nt" else ["where", path_pattern],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return path_pattern
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        
        raise XilinxJTAGError(
            f"Could not find {executable_name} executable. "
            f"Please ensure Xilinx tools are installed and in PATH, "
            f"or specify the executable path in configuration."
        )
    
    def _execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[str, str, int]:
        """
        Execute a command in the JTAG console.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
            
        Raises:
            XilinxJTAGError: If command execution fails
        """
        if not self.process:
            raise XilinxJTAGError("JTAG console not connected")
        
        timeout = timeout or self.config.command_timeout
        
        try:
            # Send command to the console
            self.process.stdin.write(f"{command}\n")
            self.process.stdin.flush()
            
            # Read output with timeout
            stdout_lines = []
            stderr_lines = []
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Try to read from stdout
                    if self.process.stdout.readable():
                        line = self.process.stdout.readline()
                        if line:
                            stdout_lines.append(line.strip())
                            self.logger.debug(f"STDOUT: {line.strip()}")
                    
                    # Check if process is still running
                    if self.process.poll() is not None:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error reading output: {e}")
                    break
            
            # Get any remaining stderr
            if self.process.stderr.readable():
                stderr_content = self.process.stderr.read()
                if stderr_content:
                    stderr_lines.append(stderr_content.strip())
            
            stdout = "\n".join(stdout_lines)
            stderr = "\n".join(stderr_lines)
            
            self.logger.debug(f"Command '{command}' completed")
            self.logger.debug(f"STDOUT: {stdout}")
            if stderr:
                self.logger.debug(f"STDERR: {stderr}")
            
            return stdout, stderr, self.process.returncode or 0
            
        except Exception as e:
            raise XilinxJTAGError(f"Failed to execute command '{command}': {e}")
    
    def connect(self, tool_paths_config: Optional[Dict[str, List[str]]] = None) -> bool:
        """
        Connect to the JTAG console.
        
        Args:
            tool_paths_config: Optional tool paths configuration
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            executable_path = self._find_executable(tool_paths_config)
            self.logger.info(f"Connecting to JTAG console: {executable_path}")
            
            # Start the JTAG console process
            self.process = subprocess.Popen(
                [executable_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait for console to initialize
            time.sleep(2)
            
            # Test connection with a simple command
            stdout, stderr, return_code = self._execute_command("help", timeout=5)
            
            if return_code == 0 or "help" in stdout.lower():
                self.is_connected = True
                self.logger.info("Successfully connected to JTAG console")
                
                # Auto-connect to devices if enabled
                if self.config.auto_connect:
                    self.scan_devices()
                
                return True
            else:
                self.logger.error(f"Failed to connect to JTAG console: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to JTAG console: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the JTAG console."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                self.logger.warning(f"Error during disconnect: {e}")
            finally:
                self.process = None
                self.is_connected = False
                self.connected_devices.clear()
                self.logger.info("Disconnected from JTAG console")
    
    def scan_devices(self) -> List[JTAGDevice]:
        """
        Scan for available JTAG devices.
        
        Returns:
            List of detected JTAG devices
        """
        if not self.is_connected:
            raise XilinxJTAGError("Not connected to JTAG console")
        
        try:
            self.logger.info("Scanning for JTAG devices...")
            
            # Execute device scan command
            stdout, stderr, return_code = self._execute_command("connect", timeout=self.config.connection_timeout)
            
            devices = []
            
            # Parse device information from output
            lines = stdout.split('\n')
            for line in lines:
                # Look for device information patterns
                # This is a simplified parser - actual output may vary
                if "target" in line.lower() or "device" in line.lower():
                    # Extract device information
                    match = re.search(r'(\d+)\s+(\w+)\s+([0-9a-fA-F]+)', line)
                    if match:
                        index = int(match.group(1))
                        name = match.group(2)
                        idcode = match.group(3)
                        
                        device = JTAGDevice(
                            index=index,
                            name=name,
                            idcode=idcode,
                            state=DeviceState.CONNECTED,
                            interface=self.config.interface,
                            description=line.strip()
                        )
                        devices.append(device)
                        self.logger.info(f"Found device: {device.name} (ID: {device.idcode})")
            
            self.connected_devices = devices
            
            if not devices:
                self.logger.warning("No JTAG devices found")
            else:
                self.logger.info(f"Found {len(devices)} JTAG device(s)")
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Error scanning devices: {e}")
            return []
    
    def get_device_info(self, device_index: int) -> Optional[JTAGDevice]:
        """
        Get information about a specific device.
        
        Args:
            device_index: Index of the device
            
        Returns:
            Device information or None if not found
        """
        for device in self.connected_devices:
            if device.index == device_index:
                return device
        return None
    
    def reset_device(self, device_index: int) -> bool:
        """
        Reset a specific device.
        
        Args:
            device_index: Index of the device to reset
            
        Returns:
            True if reset successful, False otherwise
        """
        if not self.is_connected:
            raise XilinxJTAGError("Not connected to JTAG console")
        
        try:
            self.logger.info(f"Resetting device {device_index}...")
            
            # Select device and reset
            stdout, stderr, return_code = self._execute_command(f"targets {device_index}")
            if return_code != 0:
                self.logger.error(f"Failed to select device {device_index}")
                return False
            
            stdout, stderr, return_code = self._execute_command("rst")
            if return_code == 0:
                self.logger.info(f"Successfully reset device {device_index}")
                return True
            else:
                self.logger.error(f"Failed to reset device {device_index}: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error resetting device {device_index}: {e}")
            return False
    
    def program_device(self, device_index: int, bitstream_path: str) -> bool:
        """
        Program a device with a bitstream.
        
        Args:
            device_index: Index of the device to program
            bitstream_path: Path to the bitstream file
            
        Returns:
            True if programming successful, False otherwise
        """
        if not self.is_connected:
            raise XilinxJTAGError("Not connected to JTAG console")
        
        if not os.path.exists(bitstream_path):
            raise XilinxJTAGError(f"Bitstream file not found: {bitstream_path}")
        
        try:
            self.logger.info(f"Programming device {device_index} with {bitstream_path}...")
            
            # Select device
            stdout, stderr, return_code = self._execute_command(f"targets {device_index}")
            if return_code != 0:
                self.logger.error(f"Failed to select device {device_index}")
                return False
            
            # Program the device
            stdout, stderr, return_code = self._execute_command(
                f"fpga -f {bitstream_path}",
                timeout=60  # Longer timeout for programming
            )
            
            if return_code == 0 and "success" in stdout.lower():
                self.logger.info(f"Successfully programmed device {device_index}")
                return True
            else:
                self.logger.error(f"Failed to program device {device_index}: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error programming device {device_index}: {e}")
            return False
    
    def read_memory(self, device_index: int, address: int, size: int) -> Optional[bytes]:
        """
        Read memory from a device.
        
        Args:
            device_index: Index of the device
            address: Memory address to read from
            size: Number of bytes to read
            
        Returns:
            Memory data as bytes, or None if failed
        """
        if not self.is_connected:
            raise XilinxJTAGError("Not connected to JTAG console")
        
        try:
            self.logger.debug(f"Reading {size} bytes from address 0x{address:x} on device {device_index}")
            
            # Select device
            stdout, stderr, return_code = self._execute_command(f"targets {device_index}")
            if return_code != 0:
                return None
            
            # Read memory
            stdout, stderr, return_code = self._execute_command(
                f"mrd 0x{address:x} {size}"
            )
            
            if return_code == 0:
                # Parse memory data from output
                # This is a simplified parser - actual implementation may vary
                data = []
                for line in stdout.split('\n'):
                    if '0x' in line:
                        # Extract hex values
                        hex_values = re.findall(r'0x([0-9a-fA-F]+)', line)
                        for hex_val in hex_values:
                            data.append(int(hex_val, 16))
                
                return bytes(data[:size])  # Truncate to requested size
            else:
                self.logger.error(f"Failed to read memory: {stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading memory: {e}")
            return None
    
    def write_memory(self, device_index: int, address: int, data: bytes) -> bool:
        """
        Write memory to a device.
        
        Args:
            device_index: Index of the device
            address: Memory address to write to
            data: Data to write
            
        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected:
            raise XilinxJTAGError("Not connected to JTAG console")
        
        try:
            self.logger.debug(f"Writing {len(data)} bytes to address 0x{address:x} on device {device_index}")
            
            # Select device
            stdout, stderr, return_code = self._execute_command(f"targets {device_index}")
            if return_code != 0:
                return False
            
            # Convert data to hex string
            hex_data = data.hex()
            
            # Write memory
            stdout, stderr, return_code = self._execute_command(
                f"mwr 0x{address:x} 0x{hex_data}"
            )
            
            if return_code == 0:
                self.logger.debug("Successfully wrote memory")
                return True
            else:
                self.logger.error(f"Failed to write memory: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error writing memory: {e}")
            return False
    
    def get_device_status(self, device_index: int) -> Optional[DeviceState]:
        """
        Get the current status of a device.
        
        Args:
            device_index: Index of the device
            
        Returns:
            Current device state, or None if failed
        """
        if not self.is_connected:
            raise XilinxJTAGError("Not connected to JTAG console")
        
        try:
            # Select device and get status
            stdout, stderr, return_code = self._execute_command(f"targets {device_index}")
            if return_code != 0:
                return None
            
            stdout, stderr, return_code = self._execute_command("info")
            
            if return_code == 0:
                # Parse status from output
                if "running" in stdout.lower():
                    return DeviceState.RUNNING
                elif "halted" in stdout.lower():
                    return DeviceState.HALTED
                elif "reset" in stdout.lower():
                    return DeviceState.RESET
                else:
                    return DeviceState.UNKNOWN
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting device status: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def create_jtag_config_from_dict(config_dict: Dict[str, Any]) -> JTAGConfig:
    """
    Create a JTAGConfig object from a dictionary.
    
    Args:
        config_dict: Dictionary containing configuration parameters
        
    Returns:
        JTAGConfig object
    """
    config = JTAGConfig()
    
    if 'interface' in config_dict:
        try:
            config.interface = JTAGInterface(config_dict['interface'])
        except ValueError:
            config.interface = JTAGInterface.ANXSCT
    
    if 'executable_path' in config_dict:
        config.executable_path = config_dict['executable_path']
    
    if 'connection_timeout' in config_dict:
        config.connection_timeout = int(config_dict['connection_timeout'])
    
    if 'command_timeout' in config_dict:
        config.command_timeout = int(config_dict['command_timeout'])
    
    if 'auto_connect' in config_dict:
        config.auto_connect = bool(config_dict['auto_connect'])
    
    if 'verbose_logging' in config_dict:
        config.verbose_logging = bool(config_dict['verbose_logging'])
    
    return config


def load_jtag_config(config_file: str) -> JTAGConfig:
    """
    Load JTAG configuration from a JSON file.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        JTAGConfig object
        
    Raises:
        XilinxJTAGError: If configuration file cannot be loaded
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return create_jtag_config_from_dict(config_dict)
        
    except FileNotFoundError:
        raise XilinxJTAGError(f"Configuration file not found: {config_file}")
    except json.JSONDecodeError as e:
        raise XilinxJTAGError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise XilinxJTAGError(f"Error loading configuration: {e}")


# Example usage and testing functions
def test_jtag_connection():
    """Test function to verify JTAG connection."""
    config = JTAGConfig(verbose_logging=True)
    
    with XilinxJTAGInterface(config) as jtag:
        devices = jtag.scan_devices()
        print(f"Found {len(devices)} devices")
        
        for device in devices:
            print(f"Device {device.index}: {device.name} (ID: {device.idcode})")


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_jtag_connection()
