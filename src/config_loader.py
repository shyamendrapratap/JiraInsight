"""
Configuration Loader for Platform Engineering KPI Dashboard
Loads and validates configuration from YAML and environment variables
"""

import os
import yaml
import logging
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Load and manage configuration"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to config YAML file
        """
        self.logger = logging.getLogger(__name__)

        if config_path is None:
            # Default to config/config.yaml relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config = {}

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file and environment variables

        Returns:
            Configuration dictionary
        """
        # Load from YAML
        if self.config_path.exists():
            self.logger.info(f"Loading configuration from {self.config_path}")
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.logger.warning(f"Config file not found: {self.config_path}")
            self.config = {}

        # Override with environment variables
        self._load_from_env()

        # Validate configuration
        self._validate()

        return self.config

    def _load_from_env(self):
        """Load configuration from environment variables"""

        # JIRA settings
        if os.getenv("JIRA_API_TOKEN"):
            if "jira" not in self.config:
                self.config["jira"] = {}
            self.config["jira"]["token"] = os.getenv("JIRA_API_TOKEN")

        if os.getenv("JIRA_EMAIL"):
            if "jira" not in self.config:
                self.config["jira"] = {}
            self.config["jira"]["email"] = os.getenv("JIRA_EMAIL")

        if os.getenv("JIRA_URL"):
            if "jira" not in self.config:
                self.config["jira"] = {}
            # Override first URL if exists
            if "urls" not in self.config["jira"] or not self.config["jira"]["urls"]:
                self.config["jira"]["urls"] = [os.getenv("JIRA_URL")]
            else:
                self.config["jira"]["urls"][0] = os.getenv("JIRA_URL")

        # Support multiple URLs from env
        if os.getenv("JIRA_URLS"):
            if "jira" not in self.config:
                self.config["jira"] = {}
            urls = os.getenv("JIRA_URLS").split(",")
            self.config["jira"]["urls"] = [url.strip() for url in urls]

        # Dashboard settings
        if os.getenv("DASHBOARD_HOST"):
            if "dashboard" not in self.config:
                self.config["dashboard"] = {}
            self.config["dashboard"]["host"] = os.getenv("DASHBOARD_HOST")

        if os.getenv("DASHBOARD_PORT"):
            if "dashboard" not in self.config:
                self.config["dashboard"] = {}
            self.config["dashboard"]["port"] = int(os.getenv("DASHBOARD_PORT"))

        if os.getenv("DASHBOARD_DEBUG"):
            if "dashboard" not in self.config:
                self.config["dashboard"] = {}
            self.config["dashboard"]["debug"] = os.getenv("DASHBOARD_DEBUG").lower() == "true"

    def _validate(self):
        """Validate configuration"""
        errors = []

        # Check required fields
        if "jira" not in self.config:
            errors.append("Missing 'jira' configuration section")
        else:
            jira_config = self.config["jira"]

            if "urls" not in jira_config or not jira_config["urls"]:
                errors.append("Missing JIRA URL(s)")

            if "token" not in jira_config or not jira_config["token"]:
                errors.append("Missing JIRA API token")

            if "email" not in jira_config or not jira_config["email"]:
                errors.append("Missing JIRA email")

            # Check for placeholder values
            if jira_config.get("token") == "YOUR_JIRA_API_TOKEN_HERE":
                errors.append("JIRA API token not configured (placeholder value detected)")

        if "projects" not in self.config:
            errors.append("Missing 'projects' configuration section")
        else:
            projects_config = self.config["projects"]
            if "project_keys" not in projects_config or not projects_config["project_keys"]:
                errors.append("Missing project keys")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info("Configuration validated successfully")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key

        Args:
            key: Configuration key (supports dot notation, e.g., 'jira.token')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def save(self, output_path: str = None):
        """
        Save configuration to YAML file

        Args:
            output_path: Output path (default: overwrite current config)
        """
        if output_path is None:
            output_path = self.config_path

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

        self.logger.info(f"Configuration saved to {output_path}")
