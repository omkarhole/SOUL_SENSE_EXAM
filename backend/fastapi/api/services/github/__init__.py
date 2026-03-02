"""
GitHub service modules for SoulSense.

This package contains the decomposed GitHub service components:
- github_client: Handles HTTP communication with GitHub API
- github_processor: Handles data transformation and processing
- github_service: Orchestrates the client and processor with caching
"""

from .github_client import GitHubClient
from .github_processor import GitHubProcessor

__all__ = ["GitHubClient", "GitHubProcessor"]