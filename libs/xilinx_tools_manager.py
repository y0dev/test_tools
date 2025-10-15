#!/usr/bin/env python3
"""
Xilinx Tools Manager

This module provides a centralized manager for all Xilinx tools including
JTAG, bootgen, and Vivado operations. It handles tool path management,
configuration, and provides a unified interface for all Xilinx operations.

Key Features:
- Centralized tool path management
- Multiple tool version support
- Configuration-based tool selection
- Integration with existing framework
- Comprehensive error handling

Author: Automated Test Framework
Version: 1.0.0
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from libs.xilinx_jtag import XilinxJTAGInterface, JTAGConfig, JTAGInterface
from libs.xilinx_bootgen import XilinxBootgen, BootgenConfig, VivadoProjectManager


@dataclass
class XilinxToolsConfig:
    """Configuration for Xilinx tools management."""
    tool_paths: Dict[str, List[str]]
    default_tool: str = "anxsct"
    auto_detect_paths: bool = True
    preferred_version: Optional[str] = None
    verbose_logging: bool = False


class XilinxToolsManager:
    """
    Centralized manager for all Xilinx tools.
    
    This class provides a unified interface for managing Xilinx tools
    including JTAG, bootgen, and Vivado operations. It handles tool
    path resolution, configuration management, and provides high-level
    operations for common tasks.
    """
    
    def __init__(self, config: Optional[XilinxToolsConfig] = None):
        """
        Initialize the Xilinx tools manager.
        
        Args:
            config: Xilinx tools configuration
        """
        self.config = config or XilinxToolsConfig(tool_paths={})
        self.logger = logging.getLogger(__name__)
        
        if self.config.verbose_logging:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        
        # Tool instances
        self.jtag_interface = None
        self.bootgen = None
        self.vivado_projects = {}
        
        # Resolved tool paths
        self.resolved_paths = {}
    
    def _find_tool_executable(self, tool_name: str) -> Optional[str]:
        """
        Find executable for a specific tool.
        
        Args:
            tool_name: Name of the tool to find
            
        Returns:
            Path to executable or None if not found
        """
        if tool_name not in self.config.tool_paths:
            self.logger.warning(f"No paths configured for tool: {tool_name}")
            return None
        
        # Try configured paths in order
        for path in self.config.tool_paths[tool_name]:
            if os.path.exists(path):
                self.logger.debug(f"Found {tool_name} at: {path}")
                return path
            elif path == tool_name:  # Generic name, check PATH
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
        
        self.logger.warning(f"Could not find executable for tool: {tool_name}")
        return None
    
    def resolve_tool_paths(self) -> Dict[str, Optional[str]]:
        """
        Resolve all tool paths.
        
        Returns:
            Dictionary of tool names to resolved paths
        """
        resolved = {}
        
        for tool_name in self.config.tool_paths:
            resolved[tool_name] = self._find_tool_executable(tool_name)
        
        self.resolved_paths = resolved
        self.logger.info(f"Resolved tool paths: {resolved}")
        return resolved
    
    def get_tool_path(self, tool_name: str) -> Optional[str]:
        """
        Get resolved path for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Resolved path or None if not found
        """
        if not self.resolved_paths:
            self.resolve_tool_paths()
        
        return self.resolved_paths.get(tool_name)
    
    def initialize_jtag_interface(self, jtag_config: Optional[JTAGConfig] = None) -> bool:
        """
        Initialize JTAG interface with resolved tool paths.
        
        Args:
            jtag_config: Optional JTAG configuration
            
        Returns:
            True if initialization successful
        """
        try:
            if not jtag_config:
                jtag_config = JTAGConfig()
            
            # Set executable path if resolved
            tool_path = self.get_tool_path(jtag_config.interface.value)
            if tool_path:
                jtag_config.executable_path = tool_path
            
            self.jtag_interface = XilinxJTAGInterface(jtag_config)
            
            # Connect with tool paths configuration
            success = self.jtag_interface.connect(self.config.tool_paths)
            
            if success:
                self.logger.info("JTAG interface initialized successfully")
            else:
                self.logger.error("Failed to initialize JTAG interface")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error initializing JTAG interface: {e}")
            return False
    
    def initialize_bootgen(self, bootgen_config: Optional[BootgenConfig] = None) -> bool:
        """
        Initialize bootgen with resolved tool paths.
        
        Args:
            bootgen_config: Optional bootgen configuration
            
        Returns:
            True if initialization successful
        """
        try:
            if not bootgen_config:
                bootgen_config = BootgenConfig(output_file="boot.bin", components=[])
            
            # Set bootgen path if resolved
            tool_path = self.get_tool_path("bootgen")
            if tool_path:
                bootgen_config.bootgen_path = tool_path
            
            self.bootgen = XilinxBootgen(bootgen_config)
            
            self.logger.info("Bootgen initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing bootgen: {e}")
            return False
    
    def add_vivado_project(self, name: str, project_path: str, 
                          target_cpu: str = "ps7_cortexa9_0") -> bool:
        """
        Add a Vivado project to the manager.
        
        Args:
            name: Project name
            project_path: Path to .xpr file
            target_cpu: Target CPU name
            
        Returns:
            True if project added successfully
        """
        try:
            vivado_path = self.get_tool_path("vivado")
            
            project_manager = VivadoProjectManager(
                project_path=project_path,
                vivado_path=vivado_path
            )
            
            self.vivado_projects[name] = {
                'manager': project_manager,
                'target_cpu': target_cpu,
                'project_path': project_path
            }
            
            self.logger.info(f"Added Vivado project: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding Vivado project {name}: {e}")
            return False
    
    def generate_boot_image(self, config_dict: Dict[str, Any]) -> bool:
        """
        Generate boot image using bootgen.
        
        Args:
            config_dict: Bootgen configuration dictionary
            
        Returns:
            True if generation successful
        """
        try:
            if not self.bootgen:
                if not self.initialize_bootgen():
                    return False
            
            # Update bootgen configuration
            from libs.xilinx_bootgen import create_bootgen_config_from_dict
            bootgen_config = create_bootgen_config_from_dict(config_dict)
            
            # Set bootgen path
            tool_path = self.get_tool_path("bootgen")
            if tool_path:
                bootgen_config.bootgen_path = tool_path
            
            self.bootgen.config = bootgen_config
            
            # Generate boot image
            success = self.bootgen.generate_boot_image()
            
            if success:
                self.logger.info(f"Boot image generated: {bootgen_config.output_file}")
            else:
                self.logger.error("Failed to generate boot image")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error generating boot image: {e}")
            return False
    
    def generate_vivado_bitstream(self, project_name: str, output_dir: Optional[str] = None, custom_tcl: Optional[str] = None) -> Optional[str]:
        """
        Generate bitstream for a Vivado project.
        
        Args:
            project_name: Name of the project
            output_dir: Output directory for bitstream
            custom_tcl: Path to custom TCL script for bitstream generation
            
        Returns:
            Path to generated bitstream or None if failed
        """
        try:
            if project_name not in self.vivado_projects:
                self.logger.error(f"Project not found: {project_name}")
                return None
            
            project_info = self.vivado_projects[project_name]
            project_manager = project_info['manager']
            
            # Check if custom TCL is enabled in config
            project_config = project_info.get('config', {})
            tcl_script_path = None
            
            if custom_tcl:
                tcl_script_path = custom_tcl
            elif project_config.get('custom_tcl_enabled', False):
                tcl_scripts = project_config.get('tcl_scripts', {})
                tcl_script_path = tcl_scripts.get('bitstream_generation')
                if tcl_script_path:
                    self.logger.info(f"Using configured TCL script: {tcl_script_path}")
            
            # Generate bitstream
            bitstream_path = project_manager.generate_bitstream(output_dir, tcl_script_path)
            
            if bitstream_path:
                self.logger.info(f"Bitstream generated: {bitstream_path}")
            else:
                self.logger.error("Failed to generate bitstream")
            
            return bitstream_path
            
        except Exception as e:
            self.logger.error(f"Error generating bitstream for {project_name}: {e}")
            return None
    
    def run_vivado_tcl_script(self, project_name: str, tcl_script_path: str, script_type: str = "custom", args: Optional[List[str]] = None) -> bool:
        """
        Run a TCL script for a Vivado project.
        
        Args:
            project_name: Name of the project
            tcl_script_path: Path to TCL script (or script type if using config)
            script_type: Type of script (bitstream_generation, programming, debug, custom)
            args: Optional arguments to pass to the script
            
        Returns:
            True if script executed successfully, False otherwise
        """
        try:
            if project_name not in self.vivado_projects:
                self.logger.error(f"Project not found: {project_name}")
                return False
            
            project_info = self.vivado_projects[project_name]
            project_manager = project_info['manager']
            
            # Determine actual TCL script path
            actual_tcl_path = tcl_script_path
            
            # If script_type is not "custom", try to get from config
            if script_type != "custom":
                project_config = project_info.get('config', {})
                if project_config and project_config.get('custom_tcl_enabled', False):
                    tcl_scripts = project_config.get('tcl_scripts', {})
                    config_tcl_path = tcl_scripts.get(script_type)
                    if config_tcl_path and os.path.exists(config_tcl_path):
                        actual_tcl_path = config_tcl_path
                        self.logger.info(f"Using configured TCL script for {script_type}: {actual_tcl_path}")
                    else:
                        self.logger.warning(f"Configured TCL script for {script_type} not found: {config_tcl_path}")
            
            # Run the TCL script
            success = project_manager.run_tcl_script(actual_tcl_path, args)
            
            if success:
                self.logger.info(f"TCL script executed successfully: {actual_tcl_path}")
            else:
                self.logger.error(f"TCL script failed: {actual_tcl_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error running TCL script: {e}")
            return False
    
    def associate_elf_with_project(self, project_name: str, elf_path: str) -> bool:
        """
        Associate ELF file with a Vivado project.
        
        Args:
            project_name: Name of the project
            elf_path: Path to ELF file
            
        Returns:
            True if association successful
        """
        try:
            if project_name not in self.vivado_projects:
                self.logger.error(f"Project not found: {project_name}")
                return False
            
            project_info = self.vivado_projects[project_name]
            project_manager = project_info['manager']
            target_cpu = project_info['target_cpu']
            
            # Associate ELF file
            success = project_manager.associate_elf_file(elf_path, target_cpu)
            
            if success:
                self.logger.info(f"ELF file associated with project {project_name}")
            else:
                self.logger.error(f"Failed to associate ELF file with project {project_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error associating ELF file with {project_name}: {e}")
            return False
    
    def run_jtag_operations(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run JTAG operations.
        
        Args:
            operations: List of JTAG operations
            
        Returns:
            List of operation results
        """
        if not self.jtag_interface:
            self.logger.error("JTAG interface not initialized")
            return []
        
        results = []
        
        for operation in operations:
            try:
                op_type = operation.get('type', 'unknown')
                device_index = operation.get('device_index', 0)
                
                result = {
                    'type': op_type,
                    'device_index': device_index,
                    'success': False,
                    'error': None
                }
                
                if op_type == 'reset':
                    success = self.jtag_interface.reset_device(device_index)
                    result['success'] = success
                    if not success:
                        result['error'] = 'Device reset failed'
                
                elif op_type == 'program':
                    bitstream_path = operation.get('bitstream_path')
                    if bitstream_path:
                        success = self.jtag_interface.program_device(device_index, bitstream_path)
                        result['success'] = success
                        if not success:
                            result['error'] = 'Device programming failed'
                    else:
                        result['error'] = 'No bitstream path specified'
                
                elif op_type == 'scan':
                    devices = self.jtag_interface.scan_devices()
                    result['success'] = True
                    result['devices'] = [{'index': d.index, 'name': d.name, 'idcode': d.idcode} for d in devices]
                
                else:
                    result['error'] = f'Unknown operation type: {op_type}'
                
                results.append(result)
                
            except Exception as e:
                result = {
                    'type': operation.get('type', 'unknown'),
                    'success': False,
                    'error': str(e)
                }
                results.append(result)
        
        return results
    
    def cleanup(self):
        """Cleanup all tool instances."""
        try:
            if self.jtag_interface:
                self.jtag_interface.disconnect()
                self.jtag_interface = None
            
            self.bootgen = None
            self.vivado_projects.clear()
            
            self.logger.info("Xilinx tools manager cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all tools.
        
        Returns:
            Dictionary containing tool status information
        """
        status = {
            'tool_paths': self.resolved_paths,
            'jtag_connected': self.jtag_interface.is_connected if self.jtag_interface else False,
            'bootgen_available': self.bootgen is not None,
            'vivado_projects': list(self.vivado_projects.keys()),
            'config': {
                'default_tool': self.config.default_tool,
                'auto_detect_paths': self.config.auto_detect_paths,
                'preferred_version': self.config.preferred_version
            }
        }
        
        return status


def load_xilinx_tools_config(config_file: str) -> XilinxToolsConfig:
    """
    Load Xilinx tools configuration from file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        XilinxToolsConfig object
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        xilinx_tools_data = config_data.get('xilinx_tools', {})
        
        config = XilinxToolsConfig(
            tool_paths=xilinx_tools_data.get('tool_paths', {}),
            default_tool=xilinx_tools_data.get('default_tool', 'anxsct'),
            auto_detect_paths=xilinx_tools_data.get('auto_detect_paths', True),
            preferred_version=xilinx_tools_data.get('preferred_version'),
            verbose_logging=xilinx_tools_data.get('verbose_logging', False)
        )
        
        return config
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise RuntimeError(f"Error loading configuration: {e}")


def create_sample_xilinx_tools_config() -> Dict[str, Any]:
    """
    Create a sample Xilinx tools configuration.
    
    Returns:
        Sample configuration dictionary
    """
    return {
        "xilinx_tools": {
            "tool_paths": {
                "anxsct": [
                    "C:\\Xilinx\\Vitis\\2023.2\\bin\\anxsct.exe",
                    "C:\\Xilinx\\Vitis\\2023.1\\bin\\anxsct.exe",
                    "C:\\Xilinx\\Vitis\\2022.2\\bin\\anxsct.exe",
                    "anxsct"
                ],
                "xsdb": [
                    "C:\\Xilinx\\Vitis\\2023.2\\bin\\xsdb.exe",
                    "C:\\Xilinx\\SDK\\2019.1\\bin\\xsdb.exe",
                    "C:\\Xilinx\\Vivado\\2023.2\\bin\\xsdb.exe",
                    "xsdb"
                ],
                "bootgen": [
                    "C:\\Xilinx\\Vitis\\2023.2\\bin\\bootgen.exe",
                    "C:\\Xilinx\\SDK\\2019.1\\bin\\bootgen.exe",
                    "C:\\Xilinx\\Vivado\\2023.2\\bin\\bootgen.exe",
                    "bootgen"
                ],
                "vivado": [
                    "C:\\Xilinx\\Vivado\\2023.2\\bin\\vivado.exe",
                    "C:\\Xilinx\\Vivado\\2023.1\\bin\\vivado.exe",
                    "C:\\Xilinx\\Vivado\\2022.2\\bin\\vivado.exe",
                    "vivado"
                ]
            },
            "default_tool": "anxsct",
            "auto_detect_paths": True,
            "preferred_version": "2023.2",
            "verbose_logging": False
        },
        "bootgen_config": {
            "output_file": "boot.bin",
            "boot_mode": "sd",
            "arch": "zynqmp",
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
        },
        "vivado_projects": [
            {
                "name": "example_project",
                "project_path": "./projects/example_project.xpr",
                "target_cpu": "ps7_cortexa9_0"
            }
        ]
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create tools manager
    config = XilinxToolsConfig(
        tool_paths={
            "anxsct": ["anxsct"],
            "bootgen": ["bootgen"],
            "vivado": ["vivado"]
        }
    )
    
    manager = XilinxToolsManager(config)
    
    # Resolve tool paths
    paths = manager.resolve_tool_paths()
    print(f"Resolved paths: {paths}")
    
    # Get status
    status = manager.get_status()
    print(f"Status: {status}")
    
    print("Xilinx tools manager ready")
