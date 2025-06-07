"""
ELLMa Commands Module

This module contains all command implementations for the ELLMa agent.
Commands are organized by functionality and can be dynamically loaded.
"""

from ellma.commands.base import BaseCommand, SimpleCommand, CommandError
from ellma.commands.system import SystemCommands
from ellma.commands.web import WebCommands
from ellma.commands.files import FileCommands
from ellma.commands.introspection import IntrospectionCommands
from ellma.commands.audio import AudioCommands

__all__ = [
    'BaseCommand',
    'SimpleCommand',
    'CommandError',
    'SystemCommands',
    'WebCommands',
    'FileCommands',
    'IntrospectionCommands',
    'AudioCommands'
]

# Command registry for built-in commands
BUILTIN_COMMANDS = {
    'system': SystemCommands,
    'web': WebCommands,
    'files': FileCommands,
    'sys': IntrospectionCommands,
    'audio': AudioCommands
}

def get_builtin_commands():
    """Get dictionary of built-in command classes"""
    return BUILTIN_COMMANDS.copy()

def register_builtin_command(name: str, command_class):
    """Register a new built-in command class"""
    BUILTIN_COMMANDS[name] = command_class