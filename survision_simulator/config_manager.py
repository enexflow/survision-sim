import json
import os
import logging
import logging.config
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manages the configuration for the Survision device simulator.
    Handles loading from and saving to a JSON file.
    """
    
    DEFAULT_CONFIG = {
        "ipAddress": "127.0.0.1",
        "httpPort": 8080,
        "wsPort": 10001,
        "recognitionSuccessRate": 75,
        "defaultContext": "F",
        "plateReliability": 80
    }
    
    def __init__(self, config_file_path: str = "config.json"):
        """
        Initialize the ConfigManager with a path to the configuration file.
        
        Args:
            config_file_path: Path to the configuration file
        """
        self.config_file_path = config_file_path
        self.logger = logging.getLogger("simulator.config")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults if file doesn't exist.
        
        Returns:
            Dict containing configuration values
        """
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Error loading config file: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save the current configuration to file.
        
        Args:
            config: Configuration to save, defaults to current config
        """
        config_to_save = self.config if config is None else config
        
        try:
            with open(self.config_file_path, 'w') as f:
                json.dump(config_to_save, f, indent=2)
        except IOError as e:
            self.logger.error(f"Error saving config file: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Dict containing configuration values
        """
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update the configuration with new values.
        
        Args:
            updates: Dict containing configuration updates
        """
        self.config.update(updates)
        self.save_config()
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set a specific configuration value.
        
        Args:
            key: Configuration key
            value: New value
        """
        self.config[key] = value
        self.save_config()
