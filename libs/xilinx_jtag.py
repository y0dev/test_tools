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
import threading
import signal
import psutil
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


class TerminalProcessManager:
    """
    Manages Xilinx tools running in separate terminal windows.
    
    This class provides functionality to launch xsct/xsdb in separate terminals,
    monitor their health, capture output, and provide control commands.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize terminal process manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.processes: Dict[str, Dict[str, Any]] = {}
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.running = False
        
    def launch_in_separate_terminal(self, tool_name: str, executable_path: str, 
                                  args: List[str] = None, title: str = None) -> bool:
        """
        Launch a Xilinx tool in a separate terminal window.
        
        Args:
            tool_name: Name identifier for the process
            executable_path: Path to the executable
            args: Command line arguments
            title: Terminal window title
            
        Returns:
            True if launched successfully, False otherwise
        """
        try:
            if args is None:
                args = []
            
            if title is None:
                title = f"{tool_name} - Xilinx Tool"
            
            # Determine platform-specific command
            if os.name == 'nt':  # Windows
                cmd = self._create_windows_terminal_command(executable_path, args, title)
            else:  # Linux/Mac
                cmd = self._create_unix_terminal_command(executable_path, args, title)
            
            self.logger.info(f"Launching {tool_name} in separate terminal: {cmd}")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Store process information
            self.processes[tool_name] = {
                'process': process,
                'executable': executable_path,
                'args': args,
                'title': title,
                'start_time': time.time(),
                'status': 'running',
                'output_buffer': [],
                'error_buffer': []
            }
            
            # Start monitoring thread
            self._start_monitoring(tool_name)
            
            self.logger.info(f"Successfully launched {tool_name} (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch {tool_name}: {e}")
            return False
    
    def _create_windows_terminal_command(self, executable_path: str, args: List[str], title: str) -> List[str]:
        """Create Windows command to launch tool in separate terminal."""
        cmd_args = ' '.join([executable_path] + args)
        
        # Use Windows Terminal if available, otherwise cmd
        if self._is_windows_terminal_available():
            return [
                'wt.exe', 
                '--title', title,
                '--', 'cmd.exe', '/k', cmd_args
            ]
        else:
            return [
                'cmd.exe', '/k', 
                f'title {title} && {cmd_args}'
            ]
    
    def _create_unix_terminal_command(self, executable_path: str, args: List[str], title: str) -> List[str]:
        """Create Unix command to launch tool in separate terminal."""
        cmd_args = ' '.join([executable_path] + args)
        
        # Try different terminal emulators
        terminals = ['gnome-terminal', 'xterm', 'konsole', 'terminator']
        
        for terminal in terminals:
            if self._is_command_available(terminal):
                if terminal == 'gnome-terminal':
                    return [terminal, '--title', title, '--', 'bash', '-c', f'{cmd_args}; exec bash']
                elif terminal == 'xterm':
                    return [terminal, '-title', title, '-e', 'bash', '-c', f'{cmd_args}; exec bash']
                elif terminal == 'konsole':
                    return [terminal, '--title', title, '-e', 'bash', '-c', f'{cmd_args}; exec bash']
                elif terminal == 'terminator':
                    return [terminal, '--title', title, '-e', f'bash -c "{cmd_args}; exec bash"']
        
        # Fallback to xterm
        return ['xterm', '-title', title, '-e', 'bash', '-c', f'{cmd_args}; exec bash']
    
    def _is_windows_terminal_available(self) -> bool:
        """Check if Windows Terminal is available."""
        try:
            result = subprocess.run(['wt.exe', '--help'], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            result = subprocess.run(['which', command], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    
    def _start_monitoring(self, tool_name: str):
        """Start monitoring thread for a process."""
        def monitor_process():
            process_info = self.processes[tool_name]
            process = process_info['process']
            
            while process_info['status'] == 'running':
                try:
                    # Check if process is still alive
                    if process.poll() is not None:
                        process_info['status'] = 'terminated'
                        process_info['end_time'] = time.time()
                        self.logger.info(f"Process {tool_name} terminated (exit code: {process.returncode})")
                        break
                    
                    # Read output
                    try:
                        # Non-blocking read
                        if process.stdout.readable():
                            line = process.stdout.readline()
                            if line:
                                process_info['output_buffer'].append(line.strip())
                                self.logger.debug(f"{tool_name} output: {line.strip()}")
                        
                        if process.stderr.readable():
                            line = process.stderr.readline()
                            if line:
                                process_info['error_buffer'].append(line.strip())
                                self.logger.debug(f"{tool_name} error: {line.strip()}")
                    
                    except:
                        pass  # Non-blocking read may fail
                    
                    time.sleep(0.1)  # Small delay to prevent busy waiting
                    
                except Exception as e:
                    self.logger.error(f"Error monitoring {tool_name}: {e}")
                    break
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()
        self.monitoring_threads[tool_name] = monitor_thread
    
    def get_process_status(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a process.
        
        Args:
            tool_name: Name of the process
            
        Returns:
            Status dictionary or None if not found
        """
        if tool_name not in self.processes:
            return None
        
        process_info = self.processes[tool_name]
        process = process_info['process']
        
        status = {
            'name': tool_name,
            'pid': process.pid if process.poll() is None else None,
            'status': process_info['status'],
            'start_time': process_info['start_time'],
            'end_time': process_info.get('end_time'),
            'executable': process_info['executable'],
            'title': process_info['title'],
            'output_lines': len(process_info['output_buffer']),
            'error_lines': len(process_info['error_buffer']),
            'is_running': process.poll() is None
        }
        
        return status
    
    def kill_process(self, tool_name: str, force: bool = False) -> bool:
        """
        Kill a running process.
        
        Args:
            tool_name: Name of the process
            force: Whether to force kill (SIGKILL)
            
        Returns:
            True if killed successfully, False otherwise
        """
        try:
            if tool_name not in self.processes:
                self.logger.error(f"Process {tool_name} not found")
                return False
            
            process_info = self.processes[tool_name]
            process = process_info['process']
            
            if process.poll() is not None:
                self.logger.warning(f"Process {tool_name} is already terminated")
                return True
            
            self.logger.info(f"Killing process {tool_name} (PID: {process.pid})")
            
            if force:
                process.kill()
            else:
                process.terminate()
            
            # Wait for process to terminate
            try:
                process.wait(timeout=5)
                process_info['status'] = 'killed'
                process_info['end_time'] = time.time()
                self.logger.info(f"Process {tool_name} killed successfully")
                return True
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Process {tool_name} did not terminate, force killing")
                process.kill()
                process_info['status'] = 'force_killed'
                process_info['end_time'] = time.time()
                return True
                
        except Exception as e:
            self.logger.error(f"Error killing process {tool_name}: {e}")
            return False
    
    def send_command(self, tool_name: str, command: str) -> bool:
        """
        Send a command to a running process.
        
        Args:
            tool_name: Name of the process
            command: Command to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if tool_name not in self.processes:
                self.logger.error(f"Process {tool_name} not found")
                return False
            
            process_info = self.processes[tool_name]
            process = process_info['process']
            
            if process.poll() is not None:
                self.logger.error(f"Process {tool_name} is not running")
                return False
            
            process.stdin.write(command + '\n')
            process.stdin.flush()
            
            self.logger.info(f"Sent command to {tool_name}: {command}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending command to {tool_name}: {e}")
            return False
    
    def get_output(self, tool_name: str, lines: int = 10) -> List[str]:
        """
        Get recent output from a process.
        
        Args:
            tool_name: Name of the process
            lines: Number of recent lines to return
            
        Returns:
            List of output lines
        """
        if tool_name not in self.processes:
            return []
        
        output_buffer = self.processes[tool_name]['output_buffer']
        return output_buffer[-lines:] if lines > 0 else output_buffer
    
    def get_errors(self, tool_name: str, lines: int = 10) -> List[str]:
        """
        Get recent errors from a process.
        
        Args:
            tool_name: Name of the process
            lines: Number of recent lines to return
            
        Returns:
            List of error lines
        """
        if tool_name not in self.processes:
            return []
        
        error_buffer = self.processes[tool_name]['error_buffer']
        return error_buffer[-lines:] if lines > 0 else error_buffer
    
    def list_processes(self) -> List[Dict[str, Any]]:
        """
        List all managed processes.
        
        Returns:
            List of process status dictionaries
        """
        return [self.get_process_status(name) for name in self.processes.keys()]
    
    def cleanup(self):
        """Cleanup all managed processes."""
        for tool_name in list(self.processes.keys()):
            self.kill_process(tool_name, force=True)
        
        self.processes.clear()
        self.monitoring_threads.clear()


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
        self.terminal_manager = TerminalProcessManager(self.logger)
        
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
    
    def launch_in_separate_terminal(self, tool_name: str = None, args: List[str] = None) -> bool:
        """
        Launch the JTAG tool in a separate terminal window.
        
        Args:
            tool_name: Name identifier for the process (defaults to interface type)
            args: Additional command line arguments
            
        Returns:
            True if launched successfully, False otherwise
        """
        try:
            if tool_name is None:
                tool_name = f"{self.config.interface_type.value}_terminal"
            
            if args is None:
                args = []
            
            # Find the executable
            executable_path = self._find_executable()
            
            # Create title
            title = f"Xilinx {self.config.interface_type.value.upper()} - JTAG Interface"
            
            # Launch in separate terminal
            success = self.terminal_manager.launch_in_separate_terminal(
                tool_name, executable_path, args, title
            )
            
            if success:
                self.logger.info(f"Launched {self.config.interface_type.value} in separate terminal")
                return True
            else:
                self.logger.error(f"Failed to launch {self.config.interface_type.value} in separate terminal")
                return False
                
        except Exception as e:
            self.logger.error(f"Error launching tool in separate terminal: {e}")
            return False
    
    def get_terminal_process_status(self, tool_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get status of the terminal process.
        
        Args:
            tool_name: Name of the process (defaults to interface type)
            
        Returns:
            Status dictionary or None if not found
        """
        if tool_name is None:
            tool_name = f"{self.config.interface_type.value}_terminal"
        
        return self.terminal_manager.get_process_status(tool_name)
    
    def kill_terminal_process(self, tool_name: str = None, force: bool = False) -> bool:
        """
        Kill the terminal process.
        
        Args:
            tool_name: Name of the process (defaults to interface type)
            force: Whether to force kill
            
        Returns:
            True if killed successfully, False otherwise
        """
        if tool_name is None:
            tool_name = f"{self.config.interface_type.value}_terminal"
        
        return self.terminal_manager.kill_process(tool_name, force)
    
    def send_terminal_command(self, command: str, tool_name: str = None) -> bool:
        """
        Send a command to the terminal process.
        
        Args:
            command: Command to send
            tool_name: Name of the process (defaults to interface type)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if tool_name is None:
            tool_name = f"{self.config.interface_type.value}_terminal"
        
        return self.terminal_manager.send_command(tool_name, command)
    
    def get_terminal_output(self, tool_name: str = None, lines: int = 10) -> List[str]:
        """
        Get recent output from the terminal process.
        
        Args:
            tool_name: Name of the process (defaults to interface type)
            lines: Number of recent lines to return
            
        Returns:
            List of output lines
        """
        if tool_name is None:
            tool_name = f"{self.config.interface_type.value}_terminal"
        
        return self.terminal_manager.get_output(tool_name, lines)
    
    def get_terminal_errors(self, tool_name: str = None, lines: int = 10) -> List[str]:
        """
        Get recent errors from the terminal process.
        
        Args:
            tool_name: Name of the process (defaults to interface type)
            lines: Number of recent lines to return
            
        Returns:
            List of error lines
        """
        if tool_name is None:
            tool_name = f"{self.config.interface_type.value}_terminal"
        
        return self.terminal_manager.get_errors(tool_name, lines)
    
    def list_terminal_processes(self) -> List[Dict[str, Any]]:
        """
        List all managed terminal processes.
        
        Returns:
            List of process status dictionaries
        """
        return self.terminal_manager.list_processes()
    
    def cleanup_terminal_processes(self):
        """Cleanup all terminal processes."""
        self.terminal_manager.cleanup()
    
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
                
                # Cleanup terminal processes
                self.cleanup_terminal_processes()
                
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
