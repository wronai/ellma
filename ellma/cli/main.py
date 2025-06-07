"""
ELLMa CLI - Main Command Line Interface

This module provides the main CLI entry point for ELLMa with subcommands
for initialization, execution, evolution, and code generation.
"""

import os
import sys
import click
import json
import yaml
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from ellma import __version__, BANNER
from ellma.core.agent import ELLMa
from ellma.utils.logger import get_logger, setup_logging

# Import security commands
try:
    from ellma.security.cli import cli as security_cli
except ImportError as e:
    logger.warning(f"Failed to load security commands: {e}")
    security_cli = None

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="ELLMa")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', type=click.Path(), help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, config):
    """
    🧬 ELLMa - Evolutionary Local LLM Agent

    Self-improving AI assistant that evolves with your needs.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config

    # Setup logging
    if verbose:
        setup_logging(level='DEBUG')
    else:
        setup_logging(level='INFO')


@cli.command()
@click.option('--force', is_flag=True, help='Force initialization even if already initialized')
@click.pass_context
def init(ctx, force):
    """Initialize ELLMa agent and create necessary directories"""
    verbose = ctx.obj.get('verbose', False)

    console.print(BANNER)
    console.print("[yellow]🚀 Initializing ELLMa...[/yellow]")

    # Create directories
    home_dir = Path.home() / ".ellma"
    directories = [
        home_dir,
        home_dir / "models",
        home_dir / "modules",
        home_dir / "evolution",
        home_dir / "logs",
        home_dir / "config"
    ]

    for directory in directories:
        if directory.exists() and not force:
            if verbose:
                console.print(f"[dim]Directory exists: {directory}[/dim]")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ Created: {directory}[/green]")

    # Create default configuration
    config_file = home_dir / "config.yaml"
    if not config_file.exists() or force:
        default_config = {
            "model": {
                "path": str(home_dir / "models" / "mistral-7b.gguf"),
                "context_length": 4096,
                "temperature": 0.7,
                "threads": os.cpu_count()
            },
            "evolution": {
                "enabled": True,
                "auto_improve": True,
                "learning_rate": 0.1
            },
            "modules": {
                "auto_load": True,
                "custom_path": str(home_dir / "modules")
            },
            "logging": {
                "level": "INFO",
                "file": str(home_dir / "logs" / "ellma.log")
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, indent=2)
        console.print(f"[green]✅ Created config: {config_file}[/green]")

    console.print("\n[bold green]🎉 ELLMa initialized successfully![/bold green]")
    console.print("\nNext steps:")
    console.print("1. [bold]ellma setup --download-model[/bold] - Download Mistral 7B model")
    console.print("2. [bold]ellma shell[/bold] - Start interactive shell")
    console.print("3. [bold]ellma exec 'system.scan'[/bold] - Test with a command")

# Security commands
if security_cli:
    cli.add_command(security_cli, name="security")

# Setup and configuration commands
@cli.group()
def setup():
    """Setup and configuration commands"""
    pass


@setup.command('download-model')
@click.option('--model', default='mistral-7b',
              type=click.Choice(['mistral-7b', 'llama2-7b', 'codellama-7b']),
              help='Model to download')
@click.option('--force', is_flag=True, help='Force download even if model exists')
def download_model(model, force):
    """Download LLM model for local inference"""
    home_dir = Path.home() / ".ellma"
    models_dir = home_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Model URLs (these would be real URLs in production)
    model_urls = {
        'mistral-7b': {
            'url': 'https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf',
            'filename': 'mistral-7b.gguf',
            'size': '4.1GB'
        },
        'llama2-7b': {
            'url': 'https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf',
            'filename': 'llama2-7b.gguf',
            'size': '4.1GB'
        },
        'codellama-7b': {
            'url': 'https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf',
            'filename': 'codellama-7b.gguf',
            'size': '4.1GB'
        }
    }

    model_info = model_urls[model]
    model_path = models_dir / model_info['filename']

    if model_path.exists() and not force:
        console.print(f"[yellow]Model already exists: {model_path}[/yellow]")
        console.print("Use --force to re-download")
        return

    console.print(f"[yellow]📥 Downloading {model} model ({model_info['size']})...[/yellow]")
    console.print(f"[dim]This may take several minutes depending on your connection[/dim]")

    try:
        import requests

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
        ) as progress:
            task = progress.add_task(f"Downloading {model}...", total=None)

            # Download model (simplified - in production would show progress)
            response = requests.get(model_info['url'], stream=True)
            response.raise_for_status()

            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            progress.update(task, description=f"✅ Downloaded {model}")

        console.print(f"[green]✅ Model downloaded: {model_path}[/green]")

        # Update config to point to this model
        config_file = home_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            config['model']['path'] = str(model_path)

            with open(config_file, 'w') as f:
                yaml.dump(config, f, indent=2)

            console.print("[green]✅ Configuration updated[/green]")

    except ImportError:
        console.print("[red]❌ 'requests' library not installed[/red]")
        console.print("Install with: pip install requests")
    except Exception as e:
        console.print(f"[red]❌ Download failed: {e}[/red]")
        if model_path.exists():
            model_path.unlink()  # Remove partial download


@setup.command('verify')
@click.pass_context
def verify_setup(ctx):
    """Verify ELLMa installation and configuration"""
    verbose = ctx.obj.get('verbose', False)

    console.print("[yellow]🔍 Verifying ELLMa setup...[/yellow]")

    checks = []
    home_dir = Path.home() / ".ellma"

    # Check directories
    required_dirs = [home_dir, home_dir / "models", home_dir / "modules"]
    for directory in required_dirs:
        exists = directory.exists()
        checks.append(("Directory: " + str(directory), exists))

    # Check configuration
    config_file = home_dir / "config.yaml"
    config_exists = config_file.exists()
    checks.append(("Configuration file", config_exists))

    # Check model
    model_found = False
    if config_exists:
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            model_path = config.get('model', {}).get('path')
            if model_path and Path(model_path).exists():
                model_found = True
        except:
            pass
    checks.append(("LLM model", model_found))

    # Check dependencies
    deps_ok = True
    try:
        import llama_cpp
        import rich
        import click
        import yaml
        import prompt_toolkit
    except ImportError as e:
        deps_ok = False
        checks.append((f"Dependencies", False))

    if deps_ok:
        checks.append(("Dependencies", True))

    # Display results
    table = Table(title="🔍 Setup Verification")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")

    all_good = True
    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        table.add_row(check_name, status_icon)
        if not status:
            all_good = False

    console.print(table)

    if all_good:
        console.print("\n[bold green]🎉 Setup verification successful![/bold green]")
        console.print("ELLMa is ready to use. Try: [bold]ellma shell[/bold]")
    else:
        console.print("\n[bold red]❌ Setup issues found[/bold red]")
        console.print("Run: [bold]ellma init[/bold] and [bold]ellma setup download-model[/bold]")


@cli.command()
@click.pass_context
def shell(ctx):
    """Start interactive ELLMa shell"""
    config_path = ctx.obj.get('config')
    verbose = ctx.obj.get('verbose', False)

    try:
        console.print("[blue]🐚 Starting ELLMa shell...[/blue]")
        agent = ELLMa(config_path=config_path, verbose=verbose)
        agent.shell()
    except Exception as e:
        console.print(f"[red]❌ Failed to start shell: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())


@cli.command()
@click.argument('command')
@click.argument('args', nargs=-1)
@click.option('--output', '-o', help='Output file for results')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json', 'yaml']),
              help='Output format')
@click.pass_context
def exec(ctx, command, args, output, output_format):
    """Execute a single command"""
    config_path = ctx.obj.get('config')
    verbose = ctx.obj.get('verbose', False)

    try:
        agent = ELLMa(config_path=config_path, verbose=verbose)

        # Execute command
        full_command = f"{command} {' '.join(args)}".strip()
        console.print(f"[dim]Executing: {full_command}[/dim]")

        result = agent.execute(full_command)

        # Format output
        if output_format == 'json':
            if isinstance(result, (dict, list)):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = json.dumps({"result": str(result)}, indent=2)
        elif output_format == 'yaml':
            if isinstance(result, (dict, list)):
                formatted_result = yaml.dump(result, indent=2)
            else:
                formatted_result = yaml.dump({"result": str(result)}, indent=2)
        else:
            formatted_result = str(result)

        # Output result
        if output:
            with open(output, 'w') as f:
                f.write(formatted_result)
            console.print(f"[green]✅ Result saved to: {output}[/green]")
        else:
            console.print(formatted_result)

    except Exception as e:
        console.print(f"[red]❌ Command execution failed: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--cycles', default=1, help='Number of evolution cycles')
@click.option('--force', is_flag=True, help='Force evolution even if not recommended')
@click.pass_context
def evolve(ctx, cycles, force):
    """Trigger agent evolution and self-improvement"""
    config_path = ctx.obj.get('config')
    verbose = ctx.obj.get('verbose', False)

    try:
        agent = ELLMa(config_path=config_path, verbose=verbose)

        if not force:
            # Check if evolution is recommended
            status = agent.get_status()
            commands_executed = status['performance_metrics']['commands_executed']

            if commands_executed < 10:
                console.print("[yellow]⚠️  Evolution not recommended yet[/yellow]")
                console.print(f"Execute at least 10 commands first (current: {commands_executed})")
                console.print("Use --force to override")
                return

        for cycle in range(cycles):
            if cycles > 1:
                console.print(f"\n[cyan]🧬 Evolution cycle {cycle + 1}/{cycles}[/cyan]")

            results = agent.evolve()

            if results['status'] == 'success':
                console.print(f"[green]✅ Evolution cycle {cycle + 1} completed![/green]")
            else:
                console.print(f"[red]❌ Evolution cycle {cycle + 1} failed[/red]")
                break

    except Exception as e:
        console.print(f"[red]❌ Evolution failed: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())


@cli.group()
def generate():
    """Code generation commands"""
    pass


@generate.command()
@click.option('--task', required=True, help='Task description')
@click.option('--output', '-o', help='Output file')
@click.option('--execute', is_flag=True, help='Execute generated script')
@click.pass_context
def bash(ctx, task, output, execute):
    """Generate bash script"""
    config_path = ctx.obj.get('config')
    verbose = ctx.obj.get('verbose', False)

    try:
        agent = ELLMa(config_path=config_path, verbose=verbose)

        from ellma.generators.bash import BashGenerator
        generator = BashGenerator(agent)
        script = generator.generate(task)

        if output:
            with open(output, 'w') as f:
                f.write(script)
            os.chmod(output, 0o755)  # Make executable
            console.print(f"[green]✅ Bash script saved to: {output}[/green]")

            if execute:
                console.print(f"[yellow]🔄 Executing script...[/yellow]")
                os.system(f"bash {output}")
        else:
            console.print(script)

    except ImportError:
        console.print("[red]❌ Bash generator not available[/red]")
    except Exception as e:
        console.print(f"[red]❌ Generation failed: {e}[/red]")


@generate.command()
@click.option('--task', required=True, help='Task description')
@click.option('--output', '-o', help='Output file')
@click.pass_context
def python(ctx, task, output):
    """Generate Python code"""
    config_path = ctx.obj.get('config')
    verbose = ctx.obj.get('verbose', False)

    try:
        agent = ELLMa(config_path=config_path, verbose=verbose)

        from ellma.generators.python import PythonGenerator
        generator = PythonGenerator(agent)
        code = generator.generate(task)

        if output:
            with open(output, 'w') as f:
                f.write(code)
            console.print(f"[green]✅ Python code saved to: {output}[/green]")
        else:
            from rich.syntax import Syntax
            syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
            console.print(syntax)

    except ImportError:
        console.print("[red]❌ Python generator not available[/red]")
    except Exception as e:
        console.print(f"[red]❌ Generation failed: {e}[/red]")


@generate.command()
@click.option('--task', required=True, help='Task description')
@click.option('--output', '-o', help='Output directory')
@click.pass_context
def docker(ctx, task, output):
    """Generate Docker configuration"""
    config_path = ctx.obj.get('config')
    verbose = ctx.obj.get('verbose', False)

    try:
        agent = ELLMa(config_path=config_path, verbose=verbose)

        from ellma.generators.docker import DockerGenerator
        generator = DockerGenerator(agent)
        config = generator.generate(task)

        if output:
            output_dir = Path(output)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save Dockerfile
            dockerfile_path = output_dir / "Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(config.get('dockerfile', ''))

            # Save docker-compose.yml if present
            if 'docker_compose' in config:
                compose_path = output_dir / "docker-compose.yml"
                with open(compose_path, 'w') as f:
                    f.write(config['docker_compose'])

            console.print(f"[green]✅ Docker configuration saved to: {output_dir}[/green]")
        else:
            console.print(config.get('dockerfile', 'No Dockerfile generated'))

    except ImportError:
        console.print("[red]❌ Docker generator not available[/red]")
    except Exception as e:
        console.print(f"[red]❌ Generation failed: {e}[/red]")


@cli.command()
@click.pass_context
def status(ctx):
    """Show ELLMa agent status"""
    config_path = ctx.obj.get('config')
    verbose = ctx.obj.get('verbose', False)

    try:
        agent = ELLMa(config_path=config_path, verbose=verbose)
        status = agent.get_status()

        # Create status display
        table = Table(title="🤖 ELLMa Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Version", status['version'])
        table.add_row("Model Loaded", "✅ Yes" if status['model_loaded'] else "❌ No")
        table.add_row("Model Path", status['model_path'] or "Not found")
        table.add_row("Modules", str(status['modules_count']))
        table.add_row("Commands", str(status['commands_count']))

        metrics = status['performance_metrics']
        table.add_row("Commands Executed", str(metrics['commands_executed']))
        table.add_row("Success Rate",
                      f"{(metrics['successful_executions'] / max(metrics['commands_executed'], 1)) * 100:.1f}%")
        table.add_row("Evolution Cycles", str(metrics['evolution_cycles']))
        table.add_row("Modules Created", str(metrics['modules_created']))

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Failed to get status: {e}[/red]")


if __name__ == '__main__':
    cli()