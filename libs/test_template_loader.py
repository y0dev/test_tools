import json
import logging
from pathlib import Path
from typing import Dict, List, Optional


class TestTemplateLoader:
    """
    Loads and manages test templates from configuration files.
    Provides template resolution and default value application.
    """
    
    def __init__(self, template_file: str = "config/test_templates.json"):
        """
        Initialize the test template loader.
        
        :param template_file: Path to the test templates JSON file
        """
        self.template_file = template_file
        self.templates = {}
        self.defaults = {}
        self.logger = logging.getLogger(__name__)
        
        self._load_templates()
    
    def _load_templates(self):
        """Load test templates from the configuration file."""
        try:
            template_path = Path(self.template_file)
            if not template_path.exists():
                self.logger.warning(f"Test templates file not found: {self.template_file}")
                return
            
            with open(template_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.templates = data.get('test_templates', {})
            self.defaults = data.get('defaults', {})
            
            self.logger.info(f"Loaded {len(self.templates)} test templates")
            self.logger.debug(f"Available templates: {list(self.templates.keys())}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in templates file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading test templates: {e}")
    
    def resolve_test_config(self, test_config: Dict) -> Dict:
        """
        Resolve a test configuration by applying template and defaults.
        
        :param test_config: Test configuration dictionary
        :return: Resolved test configuration
        """
        template_name = test_config.get('name')
        
        if not template_name:
            raise ValueError("Test configuration must have a 'name' field")
        
        # Get template
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Test template '{template_name}' not found")
        
        # Start with defaults
        resolved_config = self.defaults.copy()
        
        # Apply template
        resolved_config.update(template)
        
        # Apply test-specific overrides
        resolved_config.update(test_config)
        
        # Ensure name is preserved
        resolved_config['name'] = template_name
        
        self.logger.debug(f"Resolved test '{template_name}': {resolved_config}")
        return resolved_config
    
    def get_available_templates(self) -> List[str]:
        """
        Get list of available test template names.
        
        :return: List of template names
        """
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict]:
        """
        Get information about a specific template.
        
        :param template_name: Name of the template
        :return: Template information dictionary or None if not found
        """
        template = self.templates.get(template_name)
        if not template:
            return None
        
        return {
            'name': template_name,
            'description': template.get('description', 'No description'),
            'patterns_count': len(template.get('uart_patterns', [])),
            'output_format': template.get('output_format', 'default'),
            'has_custom_settings': any(key in template for key in ['cycles', 'on_time', 'off_time'])
        }
    
    def list_templates(self) -> None:
        """Print available templates to console."""
        print("Available Test Templates:")
        print("=" * 50)
        
        if not self.templates:
            print("No templates available")
            return
        
        for template_name in sorted(self.templates.keys()):
            info = self.get_template_info(template_name)
            if info:
                print(f"\n{template_name}:")
                print(f"  Description: {info['description']}")
                print(f"  Patterns: {info['patterns_count']}")
                print(f"  Output Format: {info['output_format']}")
                if info['has_custom_settings']:
                    print(f"  Custom Settings: Yes")
    
    def validate_test_config(self, test_config: Dict) -> bool:
        """
        Validate a test configuration against available templates.
        
        :param test_config: Test configuration to validate
        :return: True if valid, False otherwise
        """
        template_name = test_config.get('name')
        
        if not template_name:
            self.logger.error("Test configuration missing 'name' field")
            return False
        
        if template_name not in self.templates:
            self.logger.error(f"Unknown test template: {template_name}")
            return False
        
        # Check for valid override fields
        valid_overrides = {'cycles', 'on_time', 'off_time', 'output_format'}
        invalid_fields = set(test_config.keys()) - valid_overrides - {'name'}
        
        if invalid_fields:
            self.logger.warning(f"Unknown fields in test config: {invalid_fields}")
        
        return True
    
    def create_sample_template(self, template_name: str, description: str = "") -> Dict:
        """
        Create a sample template configuration.
        
        :param template_name: Name for the template
        :param description: Description for the template
        :return: Sample template dictionary
        """
        return {
            "description": description or f"Sample test template: {template_name}",
            "uart_patterns": [
                {
                    "regex": "READY",
                    "expected": ["READY"]
                }
            ],
            "output_format": "json"
        }


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create template loader
    loader = TestTemplateLoader()
    
    # List available templates
    loader.list_templates()
    
    # Test template resolution
    test_config = {
        "name": "boot_data_test",
        "cycles": 2
    }
    
    try:
        resolved = loader.resolve_test_config(test_config)
        print(f"\nResolved config: {json.dumps(resolved, indent=2)}")
    except Exception as e:
        print(f"Error resolving config: {e}")
