"""
Environment validation utilities for SoulSense application.

This module provides comprehensive validation for environment variables
with support for different environments and type checking.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urlparse
from pathlib import Path
from abc import ABC, abstractmethod

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("environment_validator")

# Load environment variables from .env file
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
load_dotenv(ENV_FILE)

# Constants for secret validation
SENSITIVE_KEYWORDS = {
    'secret', 'key', 'token', 'password', 'credential', 'auth', 'private', 
    'access_id', 'client_id', 'client_secret', 'api_key', 'api_token', 'dsn',
    'connection_string', 'pwd'
}

SAFE_DEV_PREFIXES = ('dev_', 'test_', 'dummy_', 'mock_', 'local_')


class SecretManager(ABC):
    """Abstract interface for secret management tools (Vault, AWS Secrets Manager, etc.)"""
    
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from the manager."""
        pass


class MockSecretManager(SecretManager):
    """Mock implementation of SecretManager for development."""
    
    def get_secret(self, key: str) -> Optional[str]:
        # In a real implementation, this would connect to a service
        return os.getenv(f"VAULT_{key}")


class EnvironmentValidator:
    """Validator for environment variables with type checking and validation."""

    def __init__(self, env: str = "development", secret_manager: Optional[SecretManager] = None):
        self.env = env.lower()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.secret_manager = secret_manager or MockSecretManager()

    def is_sensitive_key(self, key: str) -> bool:
        """Check if a key name suggests it contains sensitive information."""
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in SENSITIVE_KEYWORDS)

    def validate_required_string(self, key: str, value: Optional[str]) -> bool:
        """Validate required string variable."""
        if not value or not value.strip():
            self.errors.append(f"Required environment variable '{key}' is missing or empty")
            return False
        return True

    def validate_optional_string(self, key: str, value: Optional[str], default: str = "") -> str:
        """Validate optional string variable with default."""
        return value.strip() if value else default

    def validate_integer(self, key: str, value: Optional[str], min_val: Optional[int] = None,
                        max_val: Optional[int] = None) -> Optional[int]:
        """Validate integer variable."""
        if not value:
            return None
        try:
            int_val = int(value)
            if min_val is not None and int_val < min_val:
                self.errors.append(f"'{key}' must be >= {min_val}, got {int_val}")
                return None
            if max_val is not None and int_val > max_val:
                self.errors.append(f"'{key}' must be <= {max_val}, got {int_val}")
                return None
            return int_val
        except ValueError:
            self.errors.append(f"'{key}' must be a valid integer, got '{value}'")
            return None

    def validate_boolean(self, key: str, value: Optional[str]) -> Optional[bool]:
        """Validate boolean variable."""
        if not value:
            return None
        lower_val = value.lower()
        if lower_val in ('true', '1', 'yes', 'on'):
            return True
        elif lower_val in ('false', '0', 'no', 'off'):
            return False
        else:
            self.errors.append(f"'{key}' must be a valid boolean (true/false), got '{value}'")
            return None

    def validate_url(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate URL variable."""
        if not value:
            return None
        try:
            result = urlparse(value)
            if not result.scheme or not result.netloc:
                self.errors.append(f"'{key}' must be a valid URL, got '{value}'")
                return None
            return value
        except Exception:
            self.errors.append(f"'{key}' must be a valid URL, got '{value}'")
            return None

    def validate_email(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate email variable."""
        if not value:
            return None
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            self.errors.append(f"'{key}' must be a valid email address, got '{value}'")
            return None
        return value

    def check_secret_exposure(self, key: str, value: str) -> None:
        """
        Check if sensitive variables are exposed in development.
        Enforces strict naming conventions for secrets.
        """
        if self.is_sensitive_key(key):
            # In development/testing, secrets MUST have a safe prefix to avoid accidental prod leak
            if self.env in ("development", "testing"):
                if value and not value.startswith(SAFE_DEV_PREFIXES):
                    msg = (f"Security Risk: Potential real secret detected in '{self.env}' for key '{key}'. "
                          f"Secrets in development must start with one of {SAFE_DEV_PREFIXES}")
                    self.errors.append(msg)
                    logger.error(msg)
            
            # Check if secret should be managed by SecretManager
            managed_secret = self.secret_manager.get_secret(key)
            if managed_secret and value != managed_secret:
                self.warnings.append(f"Secret '{key}' differs from value in SecretManager (Vault/Cloud)")

    def get_masked_value(self, key: str, value: Any) -> str:
        """Get masked version of sensitive values for logging."""
        if not self.is_sensitive_key(key) or value is None:
            return str(value)
        
        str_val = str(value)
        if len(str_val) <= 8:
            return "*" * len(str_val)
        return f"{str_val[:4]}...{str_val[-4:]}"

    def validate_environment_variables(self, required_vars: Dict[str, Any],
                                     optional_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all environment variables."""
        validated = {}

        # Validate required variables
        for key, config in required_vars.items():
            var_type = config.get('type', 'string')
            value = os.getenv(key)

            if var_type == 'string':
                if self.validate_required_string(key, value):
                    validated[key] = value
                    self.check_secret_exposure(key, value)
            elif var_type == 'int':
                int_val = self.validate_integer(key, value, config.get('min'), config.get('max'))
                if int_val is not None:
                    validated[key] = int_val
            elif var_type == 'bool':
                bool_val = self.validate_boolean(key, value)
                if bool_val is not None:
                    validated[key] = bool_val
            elif var_type == 'url':
                url_val = self.validate_url(key, value)
                if url_val:
                    validated[key] = url_val
                    self.check_secret_exposure(key, value) # URLs can contain secrets/keys
            elif var_type == 'email':
                email_val = self.validate_email(key, value)
                if email_val:
                    validated[key] = email_val

        # Validate optional variables
        for key, config in optional_vars.items():
            var_type = config.get('type', 'string')
            default = config.get('default', '')
            value = os.getenv(key)

            if var_type == 'string':
                val = self.validate_optional_string(key, value, default)
                validated[key] = val
                if value: # Only check if explicitly provided, not the default
                    self.check_secret_exposure(key, val)
            elif var_type == 'int':
                int_val = self.validate_integer(key, value, config.get('min'), config.get('max'))
                validated[key] = int_val if int_val is not None else config.get('default', 0)
            elif var_type == 'bool':
                bool_val = self.validate_boolean(key, value)
                validated[key] = bool_val if bool_val is not None else config.get('default', False)

        return validated

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


def validate_environment_on_startup(env: str = "development") -> Dict[str, Any]:
    """
    Validate environment variables on application startup.
    """
    validator = EnvironmentValidator(env)

    # Define common variables
    common_optional = {
        'HOST': {'type': 'string', 'default': '127.0.0.1'},
        'PORT': {'type': 'int', 'default': 8000, 'min': 1, 'max': 65535},
        'JWT_ALGORITHM': {'type': 'string', 'default': 'HS256'},
        'JWT_EXPIRATION_HOURS': {'type': 'int', 'default': 24, 'min': 1},
    }

    if env in ['staging', 'production']:
        required_vars = {
            'APP_ENV': {'type': 'string'},
            'DATABASE_URL': {'type': 'string'},
            'JWT_SECRET_KEY': {'type': 'string'},
            'DATABASE_HOST': {'type': 'string'},
            'DATABASE_PORT': {'type': 'int', 'min': 1, 'max': 65535},
            'DATABASE_NAME': {'type': 'string'},
            'DATABASE_USER': {'type': 'string'},
            'DATABASE_PASSWORD': {'type': 'string'},
        }
        optional_vars = {
            **common_optional,
            'DEBUG': {'type': 'bool', 'default': False},
        }
    else:
        # Development/Testing defaults
        required_vars = {} 
        optional_vars = {
            **common_optional,
            'APP_ENV': {'type': 'string', 'default': env},
            'DATABASE_URL': {'type': 'string', 'default': 'sqlite:///../../data/soulsense.db'},
            'JWT_SECRET_KEY': {'type': 'string', 'default': 'dev_jwt_secret_must_be_long_enough_32_chars'},
            'DEBUG': {'type': 'bool', 'default': True},
            'WELCOME_MESSAGE': {'type': 'string', 'default': 'Welcome to Soul Sense (Dev Mode)!'},
        }

    validated_vars = validator.validate_environment_variables(required_vars, optional_vars)
    summary = validator.get_validation_summary()

    return {
        'validated_variables': validated_vars,
        'validation_summary': summary
    }


def log_environment_summary(validated_vars: Dict[str, Any], summary: Dict[str, Any], env: str = "development") -> None:
    """Log environment validation summary with masking."""
    validator = EnvironmentValidator(env)
    
    print("\n" + "="*50)
    print("ENVIRONMENT VALIDATION SUMMARY")
    print("="*50)
    print(f"Status:   {'[PASSED]' if summary['valid'] else '[FAILED]'}")
    print(f"Errors:   {summary['error_count']}")
    print(f"Warnings: {summary['warning_count']}")
    print("-"*50)

    if summary['errors']:
        print("\n[ERRORS]:")
        for error in summary['errors']:
            print(f" ! {error}")

    if summary['warnings']:
        print("\n[WARNINGS]:")
        for warning in summary['warnings']:
            print(f" * {warning}")

    print("\nCONFIGURATION (Masked):")
    for key, value in validated_vars.items():
        masked = validator.get_masked_value(key, value)
        print(f" - {key}: {masked}")
    print("="*50 + "\n")
