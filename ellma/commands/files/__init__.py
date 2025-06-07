"""
File Operations Module.

This module provides a comprehensive set of file and directory operations
organized into logical components for better maintainability and organization.
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .base_operations import FileOperationsMixin
from .read_write import FileReadWrite
from .search_ops import FileSearchOperations
from .file_ops import FileManagementOperations


class FileCommands(FileOperationsMixin, FileReadWrite, FileSearchOperations, FileManagementOperations):
    """
    Unified interface for all file operations.
    
    This class combines functionality from multiple mixins to provide
    a comprehensive set of file operations while maintaining a clean
    and organized codebase.
    """
    
    def __init__(self, agent):
        """Initialize the file commands with an agent reference."""
        # Initialize all parent classes
        FileOperationsMixin.__init__(self)
        FileReadWrite.__init__(self, agent)
        FileSearchOperations.__init__(self, agent)
        FileManagementOperations.__init__(self, agent)
        
        self.agent = agent
        self.name = "files"
        self.description = "File and directory operations"
    
    # Add any additional methods that need to coordinate between different
    # operation types or provide higher-level functionality
    
    @classmethod
    def get_commands(cls) -> Dict[str, Any]:
        """
        Get a dictionary of available commands and their metadata.
        
        Returns:
            Dictionary mapping command names to their metadata
        """
        # This method can be used by the agent to discover available commands
        commands = {}
        
        # Get methods from all parent classes
        for base in cls.__bases__:
            if hasattr(base, 'get_commands'):
                commands.update(base.get_commands())
        
        return commands


# Export the main class
__all__ = ['FileCommands']
