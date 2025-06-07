"""
Command-line interface for ELLMa security and environment management.
"""

import click
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger('ellma.security.cli')

@click.group(name='security', help='ELLMa security and environment management')
def cli():
    """Security and environment management commands."""
    pass

@cli.command(name='check', help='Check environment status')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def check_environment(verbose: bool):
    """Check the current environment status."""
    from ..security.core import check_environment, EnvironmentStatus
    
    result = check_environment()
    
    if result.status == EnvironmentStatus.VALID:
        click.echo(click.style("✓ Environment is valid", fg='green'))
    else:
        click.echo(click.style("✗ Environment has issues", fg='red'))
        click.echo(f"Status: {result.status.value}")
        if result.error:
            click.echo(f"Error: {result.error}")
        if result.missing_deps:
            click.echo("Missing dependencies:")
            for dep in result.missing_deps:
                click.echo(f"  - {dep}")
    
    if verbose:
        click.echo("\nDetailed environment information:")
        click.echo(f"Python: {result.current_python or 'Unknown'}")
        click.echo(f"Virtual environment: {'Yes' if result.is_venv else 'No'}")
        if result.venv_path:
            click.eof(f"Virtual environment path: {result.venv_path}")

@cli.command(name='install', help='Install dependencies')
@click.option('--group', '-g', help='Dependency group to install (e.g., dev, audio)')
@click.option('--no-dev', is_flag=True, help='Exclude development dependencies')
def install_dependencies(group: Optional[str], no_dev: bool):
    """Install project dependencies."""
    from ..security import install_dependencies as install_deps
    
    if no_dev:
        group = 'main'
    
    click.echo(f"Installing dependencies{' for group: ' + group if group else ''}...")
    success = install_deps(group=group)
    
    if success:
        click.echo(click.style("✓ Dependencies installed successfully", fg='green'))
    else:
        click.echo(click.style("✗ Failed to install dependencies", fg='red'), err=True)
        return 1
    return 0

@cli.command(name='repair', help='Attempt to repair the environment')
def repair_environment():
    """Attempt to repair the environment."""
    from ..security import ensure_environment
    
    click.echo("Attempting to repair environment...")
    success = ensure_environment(auto_repair=True)
    
    if success:
        click.echo(click.style("✓ Environment repaired successfully", fg='green'))
    else:
        click.echo(click.style("✗ Failed to repair environment", fg='red'), err=True)
        return 1
    return 0

def register_commands(click_group):
    """Register security commands with a Click group."""
    return cli.commands
