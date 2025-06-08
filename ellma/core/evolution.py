"""
ELLMa Evolution Engine - Self-Improvement System

This module implements the core evolution mechanism that allows ELLMa to
analyze its performance, identify improvement opportunities, and automatically
generate new capabilities.
"""

import os
import json
import time
import tempfile
import importlib
import subprocess
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ellma.utils.evolution_utils import (
    setup_evolution_environment,
    check_system_resources,
    cleanup_resources,
    log_evolution_result,
    EvolutionConfig
)

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from ellma import EvolutionError
from ellma.utils.logger import get_logger
from .module_generator import ModuleGenerator
from .error_logger import log_error

logger = get_logger(__name__)


class EvolutionEngine:
    """
    Core Evolution Engine for ELLMa

    Handles the self-improvement cycle:
    1. Analysis - Examine current capabilities and performance
    2. Identification - Find improvement opportunities  
    3. Generation - Create new modules and enhancements
    4. Testing - Validate new capabilities
    5. Integration - Deploy improvements
    6. Learning - Update knowledge base
    """

    def __init__(self, agent, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Evolution Engine with enhanced configuration

        Args:
            agent: ELLMa agent instance
            config: Optional configuration overrides for evolution
        """
        # Initialize basic attributes first
        self.agent = agent
        self.console = Console()
        self.evolution_log = []
        self.capabilities = set()
        self.improvement_suggestions = []
        self.last_evolution_time = None
        self.is_evolving = False
        self.current_cycle = None
        
        # Set up evolution configuration and environment
        self.config = EvolutionConfig(config or {})
        self.evolution_env = setup_evolution_environment(config or {})
        
        # Initialize configuration from agent config
        self._load_configuration()
        
        # Initialize metrics tracking
        self.evolution_metrics = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'modules_created': 0,
            'modules_removed': 0,
            'performance_improvement': 0.0,
            'modules': {},
            'resource_usage': {}
        }
        
        # Initialize module generator
        self.module_generator = ModuleGenerator(
            base_path=str(Path(__file__).parent.parent.parent / "modules")
        )
        
        # Set up directories and load history
        try:
            self._setup_directories()
            self._load_evolution_history()
        except Exception as e:
            logger.error(f"Failed to initialize evolution engine: {e}")
            if self.console:
                self.console.print(f"[red]Failed to initialize evolution engine: {e}[/red]")
            raise
        
        # Log successful initialization
        logger.info("Evolution Engine initialized with config: %s", self.config.__dict__)
        if self.console:
            self.console.print("[green]✓ Evolution Engine initialized[/green]")

    def _setup_directories(self) -> None:
        """Set up required directories for evolution.
        
        Creates the following directory structure:
        - evolution/
          - generated/    # For generated module code
          - logs/        # For evolution logs
          - history/     # For evolution history
          - backups/     # For backup of previous versions
        """
        try:
            # Base directory for evolution
            base_dir = Path(".ellma/evolution")
            self.evolution_dir = base_dir
            
            # Define directory structure
            self.directories = {
                'base': base_dir,
                'generated': base_dir / 'generated',
                'logs': base_dir / 'logs',
                'history': base_dir / 'history',
                'backups': base_dir / 'backups'
            }
            
            # Create directories if they don't exist
            for dir_path in self.directories.values():
                dir_path.mkdir(parents=True, exist_ok=True)
                
            logger.info(f"Evolution directories set up at: {base_dir.absolute()}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to set up evolution directories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if hasattr(self, 'console'):
                self.console.print(f"[red]Error: {error_msg}[/red]")
            raise RuntimeError(error_msg) from e

    def _log_step(self, step_name: str, message: str, status: str = 'in_progress', **kwargs) -> None:
        """Log a step in the evolution process.
        
        Args:
            step_name: Name of the current step (e.g., 'analysis', 'integration')
            message: Message to log
            status: Status of the step ('in_progress', 'completed', 'failed')
            **kwargs: Additional key-value pairs to include in the log entry
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'step': step_name,
            'message': message,
            'status': status,
            **kwargs
        }
        
        if not hasattr(self, 'current_cycle') or self.current_cycle is None:
            self.current_cycle = {}
        
        if 'steps' not in self.current_cycle:
            self.current_cycle['steps'] = []
            
        self.current_cycle['steps'].append(log_entry)
        
        status_emoji = {
            'in_progress': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(status, 'ℹ️')
        
        log_message = f"{status_emoji} [{step_name.upper()}] {message}"
        if 'error' in kwargs:
            log_message += f"\nError: {kwargs['error']}"
            
        logger.info(log_message)
        self.console.print(f"[bold]{log_message}[/bold]")

    def _load_evolution_history(self) -> None:
        """Load evolution history from disk if it exists."""
        history_file = self.directories['history'] / 'evolution_history.json'
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.evolution_history = json.load(f)
                logger.info(f"Loaded evolution history from {history_file}")
            except Exception as e:
                logger.error(f"Failed to load evolution history: {e}")
                self.evolution_history = {}
        else:
            self.evolution_history = {}
            logger.info("No previous evolution history found, starting fresh")
        
        # Create directories if they don't exist
        for dir_path in self.directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Evolution directories set up at: {base_dir.absolute()}")
        
    def _load_configuration(self):
        """Load and validate evolution configuration"""
        # Default configuration
        default_config = {
            'enabled': True,
            'auto_evolve': True,
            'max_evolution_attempts': 3,
            'backup_before_evolution': True,
            'max_modules_to_generate': 5,
            'min_success_rate': 0.7,
            'max_failure_rate': 0.2,
            'resource_limits': {
                'max_memory_mb': 4096,
                'min_disk_space_gb': 5,
                'max_cpu_percent': 80
            }
        }
        
        # Merge with agent config
        self.config = {**default_config, **self.agent.config.get("evolution", {})}
        logger.info(f"Loaded evolution configuration: {self.config}")
        
        # Set enabled flag
        self.enabled = self.config.get('enabled', True)
        
        # Core settings
        self.enabled = self.evolution_config.get("enabled", True)
        self.auto_improve = self.evolution_config.get("auto_improve", True)
        self.evolution_interval = self.evolution_config.get("evolution_interval", 50)
        self.max_modules = self.evolution_config.get("max_modules", 100)
        self.backup_before_evolution = self.evolution_config.get("backup_before_evolution", True)
        
        # Learning parameters
        self.learning_rate = max(0.0, min(1.0, self.evolution_config.get("learning_rate", 0.1)))
        self.exploration_rate = max(0.0, min(1.0, self.evolution_config.get("exploration_rate", 0.2)))
        self.max_depth = max(1, self.evolution_config.get("max_depth", 5))
        self.max_iterations = max(1, self.evolution_config.get("max_iterations", 100))
        self.early_stopping = self.evolution_config.get("early_stopping", True)
        
        # Resource management
        self.max_memory_mb = max(256, self.evolution_config.get("max_memory_mb", 4096))
        self.max_runtime_minutes = max(1, self.evolution_config.get("max_runtime_minutes", 30))
        self.cpu_threads = max(0, self.evolution_config.get("cpu_threads", 0))
        
        # Advanced settings
        self.enable_parallel = self.evolution_config.get("enable_parallel", True)
        self.enable_rollback = self.evolution_config.get("enable_rollback", True)
        self.enable_benchmark = self.evolution_config.get("enable_benchmark", True)
        self.log_level = self.evolution_config.get("log_level", "INFO").upper()
        
        # Module settings
        self.allow_new_modules = self.evolution_config.get("allow_new_modules", True)
        self.allow_module_removal = self.evolution_config.get("allow_module_removal", False)
        self.min_module_usage = max(0, self.evolution_config.get("min_module_usage", 5))
        
        # Performance targets
        self.target_success_rate = max(0.0, min(1.0, self.evolution_config.get("target_success_rate", 0.95)))
        self.target_execution_time = max(0.1, self.evolution_config.get("target_execution_time", 1.0))
        self.min_improvement = max(0.0, self.evolution_config.get("min_improvement", 0.01))
        
        # Set logger level
        logger.setLevel(self.log_level)

    def evolve(self, force: bool = False) -> Dict:
        """
        Execute a full evolution cycle with enhanced logging and error handling.
        
        Args:
            force: If True, skip pre-flight checks
            
        Returns:
            Dict containing evolution results
        """
        # Initialize integration_results with default values
        integration_results = {
            'modules_created': 0,
            'modules_removed': 0,
            'integrated': [],
            'failed': []
        }
        
        logger.info("🔍 Starting evolution cycle")
        
        # Check if evolution is already in progress
        if self.is_evolving:
            error_msg = "Evolution already in progress"
            logger.warning(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }
        
        # Set up evolution environment
        self.is_evolving = True
        start_time = time.time()
        
        # Initialize cycle tracking
        self.current_cycle = {
            'start_time': start_time,
            'status': 'started',
            'steps': [],
            'metrics': {},
            'errors': []
        }
        
        try:
            # Check system resources
            if not force:
                resource_check = check_system_resources(self.config)
                self.current_cycle['resource_check'] = resource_check
                
                if not resource_check.get('has_resources', False):
                    error_msg = "Insufficient system resources for evolution"
                    logger.error(error_msg)
                    self.current_cycle['status'] = 'failed'
                    self.current_cycle['error'] = error_msg
                    return {
                        "status": "error",
                        "message": error_msg,
                        "resource_check": resource_check
                    }
            
            # Log start of evolution
            logger.info("🚀 Beginning evolution process with config: %s", self.config.__dict__)
            self.console.print("\n[bold blue]🚀 Starting Evolution Cycle[/bold blue]")
            
            # Track evolution metrics
            self.evolution_metrics['total_cycles'] += 1
            self.current_cycle['metrics'] = {
                'modules_before': len(self.agent.modules),
                'commands_before': len(self.agent.commands),
                'start_time': datetime.now().isoformat()
            }
            logger.info("🔧 Starting evolution cycle")
            
            # Initialize logs and metrics if they don't exist
            if not hasattr(self, 'evolution_log'):
                self.evolution_log = []
            if not hasattr(self, 'evolution_metrics'):
                self.evolution_metrics = {
                    'total_cycles': 0,
                    'successful_cycles': 0,
                    'failed_cycles': 0,
                    'modules_created': 0,
                    'modules_removed': 0,
                    'performance_improvement': 0.0
                }
            
            # 1. Analysis Phase
            self._log_step('analysis', "Analyzing current system state")
            try:
                analysis_results = self._analyze_system()
                if not hasattr(self, 'current_cycle') or self.current_cycle is None:
                    self.current_cycle = {}
                self.current_cycle['analysis'] = analysis_results
                self._log_step('analysis', "Analysis completed", status='completed')
                
                # 2. Opportunity Identification
                self._log_step('opportunity_identification', "Identifying improvement opportunities")
                try:
                    opportunities = self._identify_opportunities(analysis_results)
                    self.current_cycle['opportunities'] = opportunities
                    self._log_step('opportunity_identification', 
                                 f"Found {len(opportunities)} opportunities", 
                                 status='completed')
                    
                    # 3. Solution Generation
                    self._log_step('solution_generation', "Generating solutions")
                    try:
                        solutions = self._generate_solutions(opportunities)
                        self.current_cycle['solutions'] = solutions
                        self._log_step('solution_generation', 
                                     f"Generated {len(solutions)} solutions", 
                                     status='completed')
                        
                        # 4. Solution Testing
                        self._log_step('solution_testing', "Testing solutions")
                        try:
                            validated_solutions = self._test_solutions(solutions)
                            self.current_cycle['validated_solutions'] = validated_solutions
                            self._log_step('solution_testing', 
                                         f"Validated {len(validated_solutions)} solutions", 
                                         status='completed')
                            
                            # 5. Integration
                            self._log_step('integration', "Integrating solutions")
                            try:
                                integration_results = self._integrate_solutions(validated_solutions)
                                self.current_cycle['integration'] = integration_results
                                self._log_step('integration', 
                                             f"Integrated {integration_results.get('successful', 0)} solutions", 
                                             status='completed')
                                
                                # 6. Learning Update
                                self._log_step('learning_update', "Updating knowledge")
                                try:
                                    learning_results = self._update_learning(integration_results)
                                    self.current_cycle['learning'] = learning_results
                                    self._log_step('learning_update', "Knowledge updated", status='completed')
                                    
                                    # Update metrics and finalize
                                    self.evolution_metrics['successful_cycles'] += 1
                                    self.current_cycle['status'] = 'completed'
                                    self.current_cycle['end_time'] = time.time()
                                    self.current_cycle['duration'] = time.time() - start_time
                                    
                                    # Log successful completion
                                    logger.info("✅ Evolution cycle completed successfully in %.2f seconds", 
                                               self.current_cycle['duration'])
                                    self.console.print(
                                        f"\n[bold green]✓ Evolution completed in {self.current_cycle['duration']:.2f}s[/bold green]"
                                    )
                                    
                                    # Prepare success result
                                    result = {
                                        'status': 'success',
                                        'cycle_id': len(self.evolution_log) + 1,
                                        'duration': self.current_cycle['duration'],
                                        'modules_created': len([s for s in integration_results.get('integrated', []) 
                                                              if s.get('type') == 'new_module']),
                                        'metrics': self.current_cycle.get('metrics', {})
                                    }
                                    
                                    # Log and save before returning
                                    self._log_evolution(result)
                                    self._save_evolution_log()
                                    return result
                                    
                                except Exception as e:
                                    error_msg = f"Learning update failed: {str(e)}"
                                    logger.error(error_msg, exc_info=True)
                                    self._log_step('learning_update', error_msg, status='failed', error=str(e))
                                    # Continue even if learning update fails
                                    self.current_cycle['status'] = 'completed_with_warnings'
                                    self.current_cycle['end_time'] = time.time()
                                    self.current_cycle['duration'] = time.time() - start_time
                                    
                                    result = {
                                        'status': 'completed_with_warnings',
                                        'message': 'Evolution completed but learning update failed',
                                        'error': str(e),
                                        'cycle_id': len(self.evolution_log) + 1,
                                        'duration': self.current_cycle['duration']
                                    }
                                    
                                    self._log_evolution(result)
                                    self._save_evolution_log()
                                    return result
                                    
                            except Exception as e:
                                error_msg = f"Integration failed: {str(e)}"
                                logger.error(error_msg, exc_info=True)
                                self._log_step('integration', error_msg, status='failed', error=str(e))
                                raise RuntimeError(error_msg) from e
                                
                        except Exception as e:
                            error_msg = f"Solution testing failed: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            self._log_step('solution_testing', error_msg, status='failed', error=str(e))
                            raise RuntimeError(error_msg) from e
                            
                    except Exception as e:
                        error_msg = f"Solution generation failed: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        self._log_step('solution_generation', error_msg, status='failed', error=str(e))
                        raise RuntimeError(error_msg) from e
                        
                except Exception as e:
                    error_msg = f"Opportunity identification failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self._log_step('opportunity_identification', error_msg, status='failed', error=str(e))
                    raise RuntimeError(error_msg) from e
                    
            except Exception as e:
                error_msg = f"Analysis failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self._log_step('analysis', error_msg, status='failed', error=str(e))
                raise RuntimeError(error_msg) from e
                
        except Exception as e:
            # Handle any unexpected errors during the evolution process
            error_msg = f"Evolution process failed: {str(e)}"
            logger.critical(error_msg, exc_info=True)
            self.current_cycle['status'] = 'failed'
            self.current_cycle['error'] = str(e)
            
            # Update cycle status
            self.current_cycle['status'] = 'completed'
            self.current_cycle['end_time'] = time.time()
            
            # Update metrics
            self.evolution_metrics['total_cycles'] += 1
            self.evolution_metrics['successful_cycles'] += 1
            self.evolution_metrics['modules_created'] += integration_results.get('modules_created', 0)
            self.evolution_metrics['modules_removed'] += integration_results.get('modules_removed', 0)
            
            # Calculate performance improvement if possible
            if 'performance_improvement' in learning_results:
                self.evolution_metrics['performance_improvement'] = learning_results['performance_improvement']
            
            # Log completion
            duration = self.current_cycle['end_time'] - self.current_cycle['start_time']
            logger.info(f"✅ Evolution cycle completed successfully in {duration:.2f} seconds")
            
            # Save the updated evolution history
            self._save_evolution_history()
            
            return {
                'status': 'success',
                'cycle_id': len(self.evolution_log) + 1,
                'duration': duration,
                'steps_completed': [s['step'] for s in self.current_cycle['steps']],
                'modules_created': integration_results.get('modules_created', 0),
                'modules_removed': integration_results.get('modules_removed', 0),
                'performance_improvement': learning_results.get('performance_improvement', 0.0)
            }
            
        except Exception as e:
            error_msg = f"❌ Evolution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if hasattr(self, 'current_cycle') and self.current_cycle:
                self.current_cycle['status'] = 'failed'
                self.current_cycle['error'] = str(e)
                self.current_cycle['end_time'] = time.time()
                
                if not hasattr(self, 'evolution_log'):
                    self.evolution_log = []
                    
                self.evolution_log.append(self.current_cycle)
                
            # Initialize metrics if they don't exist
            if not hasattr(self, 'evolution_metrics'):
                self.evolution_metrics = {
                    'total_cycles': 0,
                    'successful_cycles': 0,
                    'failed_cycles': 0
                }
                
            # Update metrics
            self.evolution_metrics['total_cycles'] += 1
            self.evolution_metrics['failed_cycles'] += 1
            
            # Save the updated evolution history
            self._save_evolution_history()
            
            return {
                'status': 'error',
                'error': str(e),
                'cycle_id': len(self.evolution_log) if hasattr(self, 'evolution_log') else None
            }
            
        finally:
            self.is_evolving = False

    def _save_evolution_history(self):
        """Save the evolution history to disk"""
        try:
            history_file = self.evolution_dir / "evolution_history.json"
            with open(history_file, 'w') as f:
                json.dump({
                    'evolution_log': getattr(self, 'evolution_log', []),
                    'evolution_metrics': getattr(self, 'evolution_metrics', {})
                }, f, indent=2, default=str)
            logger.debug(f"Saved evolution history to {history_file}")
        except Exception as e:
            logger.error(f"Failed to save evolution history: {e}")
            log_error(e, {"context": "save_evolution_history"})

    def _analyze_system(self) -> Dict:
        """
        Analyze the current system state and identify improvement opportunities
        
        Returns:
            Dict containing analysis results and metrics
        """
        logger.info("🔍 Analyzing system state...")
        
        try:
            # Check if evolution is enabled
            if not getattr(self, 'enabled', False):
                msg = "[yellow]Evolution is disabled in configuration[/yellow]"
                self.console.print(msg)
                logger.warning("Evolution attempted but disabled in config")
                return {"status": "disabled", "message": msg}

            # Check if already evolving
            if getattr(self, 'is_evolving', False):
                msg = "[yellow]Evolution already in progress[/yellow]"
                self.console.print(msg)
                logger.warning("Evolution already in progress")
                return {"status": "busy", "message": msg}
                
            self.is_evolving = True
            self.current_cycle = {
                'start_time': time.time(),
                'status': 'started',
                'metrics': {},
                'changes': {}
            }

            # Check system resources
            if not self._check_system_resources():
                msg = "[yellow]Insufficient system resources for evolution[/yellow]"
                self.console.print(msg)
                return {"status": "resource_constrained", "message": msg}

            self.console.print(Panel(
                "[bold cyan]🧬 ELLMa Evolution Cycle Starting[/bold cyan]",
                title="Self-Improvement",
                subtitle=f"Cycle #{self.evolution_metrics.get('total_cycles', 0) + 1}",
                border_style="cyan"
            ))
            
            # Collect system metrics
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'modules_count': len(getattr(self.agent, 'modules', {})),
                'commands_count': len(getattr(self.agent, 'commands', {})),
                'capabilities': list(getattr(self, 'capabilities', set())),
                'errors': []
            }
            
            # Add any error logs from recent operations
            if hasattr(self, 'recent_errors') and self.recent_errors:
                metrics['recent_errors'] = self.recent_errors
                
            return {
                'status': 'success',
                'message': 'System analysis completed',
                'metrics': metrics,
                'suggestions': self._identify_improvements(metrics)
            }
            
        except Exception as e:
            error_msg = f"Failed to analyze system: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'error': str(e)
            }
        finally:
            self.is_evolving = False
            
    def _identify_improvements(self, metrics: Dict) -> List[Dict]:
        """
        Identify potential improvements based on system metrics
        
        Args:
            metrics: System metrics from _analyze_system
            
        Returns:
            List of suggested improvements with priorities
        """
        improvements = []
        
        # Check for missing core modules
        core_modules = ['error_handling', 'logging', 'configuration']
        existing_modules = set(metrics.get('capabilities', []))
        missing_modules = [m for m in core_modules if m not in existing_modules]
        
        for module in missing_modules:
            improvements.append({
                'type': 'add_module',
                'module': module,
                'priority': 'high',
                'reason': f'Core module {module} is missing'
            })
            
        # Check for recent errors
        if metrics.get('recent_errors'):
            error_count = len(metrics['recent_errors'])
            improvements.append({
                'type': 'fix_errors',
                'count': error_count,
                'priority': 'critical' if error_count > 5 else 'high',
                'reason': f'Found {error_count} recent errors in logs'
            })
            
        # Suggest performance improvements if command count is high
        if metrics.get('commands_count', 0) > 50:
            improvements.append({
                'type': 'optimize',
                'area': 'command_handling',
                'priority': 'medium',
                'reason': 'High number of commands may impact performance'
            })
            
        return improvements

    def _check_system_resources(self) -> bool:
        """
        Check if system has sufficient resources for evolution
        
        Returns:
            bool: True if system has sufficient resources, False otherwise
        """
        try:
            import psutil
            import shutil
            
            # Check available memory
            mem = psutil.virtual_memory()
            min_memory_mb = 512  # Reduced from 1GB to 512MB minimum
            available_mb = mem.available / (1024 * 1024)
            if available_mb < min_memory_mb:
                logger.warning(f"Insufficient memory: {available_mb:.1f}MB available, "
                             f"{min_memory_mb}MB required")
                return False
            
            # Check disk space
            min_disk_space = 1 * 1024 * 1024 * 1024  # Reduced from 2GB to 1GB
            _, _, free = shutil.disk_usage("/")
            free_mb = free / (1024 * 1024)
            min_disk_space_mb = min_disk_space / (1024 * 1024)
            if free < min_disk_space:
                logger.warning(f"Insufficient disk space: {free_mb:.1f}MB available, "
                             f"{min_disk_space_mb:.1f}MB required")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return False

    def _build_and_test_module(self, module_path: Path) -> bool:
        """
        Build and test a generated module.
        
        Args:
            module_path: Path to the module directory
            
        Returns:
            bool: True if build and tests pass, False otherwise
        """
        try:
            # Install the module in development mode
            result = subprocess.run(
                ["pip", "install", "-e", "."],
                cwd=module_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to install module: {result.stderr}")
                return False
                
            # Run tests
            test_result = subprocess.run(
                ["python", "-m", "pytest", "tests/"],
                cwd=module_path,
                capture_output=True,
                text=True
            )
            
            if test_result.returncode != 0:
                logger.error(f"Module tests failed: {test_result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error building/testing module: {e}", exc_info=True)
            return False
    
    def _import_module(self, module_name: str, module_path: str):
        """Dynamically import a module."""
        import importlib.util
        import sys
        
        # Add the parent directory to sys.path if needed
        parent_dir = str(Path(module_path).parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, str(Path(module_path) / "__init__.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return module
    
    def _integrate_solutions(self, solutions: List[Dict]) -> Dict:
        """
        Integrate validated solutions into the agent
        
        Args:
            solutions: List of validated solutions
            
        Returns:
            Integration results including module creation info
        """
        self.console.print(f"[yellow]Integrating {len(solutions)} solutions...[/yellow]")
        results = {
            'total': len(solutions),
            'successful': 0,
            'failed': 0,
            'modules_created': 0,
            'modules_removed': 0,
            'integrated': []
        }
        
        for solution in solutions:
            try:
                if solution.get('type') == 'new_module' and solution.get('test_status') == 'validated':
                    # Generate new module
                    module_spec = {
                        'name': solution.get('module_name', f'generated_module_{len(self.evolution_metrics["modules"])}'),
                        'description': solution.get('description', 'Auto-generated module'),
                        'purpose': solution.get('purpose', 'Automatically generated during evolution'),
                        'dependencies': solution.get('dependencies', [])
                    }
                    
                    # Generate the module
                    gen_result = self.module_generator.generate_module(module_spec)
                    
                    if gen_result['status'] == 'success':
                        module_name = gen_result['module_name']
                        module_path = gen_result['module_path']
                        
                        # Build and test the module
                        build_success = self._build_and_test_module(Path(module_path))
                        
                        if build_success:
                            # Add module to agent
                            try:
                                # Dynamically import the module
                                module = self._import_module(module_name, module_path)
                                if hasattr(module, module_spec['name'].title().replace(' ', '') + 'Module'):
                                    module_class = getattr(module, module_spec['name'].title().replace(' ', '') + 'Module')
                                    self.agent.add_module(module_name, module_class())
                                    
                                    # Update metrics
                                    results['modules_created'] += 1
                                    self.evolution_metrics['modules_created'] += 1
                                    self.evolution_metrics['modules'][module_name] = {
                                        'path': module_path,
                                        'created_at': datetime.now().isoformat(),
                                        'status': 'active'
                                    }
                                    
                                    results['successful'] += 1
                                    results['integrated'].append({
                                        'module': module_name,
                                        'path': module_path,
                                        'type': 'new_module',
                                        'timestamp': datetime.now().isoformat()
                                    })
                                else:
                                    raise ImportError(f"Module class not found in {module_name}")
                            except Exception as e:
                                logger.error(f"Failed to import module {module_name}: {e}")
                                results['failed'] += 1
                        else:
                            logger.error(f"Failed to build/test module {module_name}")
                            results['failed'] += 1
                    else:
                        logger.error(f"Failed to generate module: {gen_result.get('error', 'Unknown error')}")
                        results['failed'] += 1
                else:
                    # Handle other types of solutions (e.g., code patches)
                    # ... existing code ...
                    pass
                        
            except Exception as e:
                logger.error(f"Error integrating solution: {e}", exc_info=True)
                results['failed'] += 1
                log_error(e, {
                    'context': 'module_integration',
                    'solution': solution,
                    'error': str(e)
                })
        
        return results

    def _update_learning(self, integration_results: Dict) -> Dict:
        """
        Update the agent's learning based on integration results
        
        Args:
            integration_results: Results from solution integration
            
        Returns:
            Learning update results
        """
        self.console.print("[yellow]Updating agent's knowledge...[/yellow]")
        
        # Simple learning update - just log the results
        learning_update = {
            'timestamp': datetime.now().isoformat(),
            'integrated_modules': integration_results.get('successful', 0),
            'learning_rate': self.learning_rate
        }
        
        # Update agent's learning rate based on success
        if integration_results.get('successful', 0) > 0:
            self.learning_rate = min(1.0, self.learning_rate * 1.1)  # Increase learning rate
        
        return learning_update

    def _display_evolution_results(self, results: Dict) -> None:
        """
        Display evolution results in a user-friendly format
        
        Args:
            results: Evolution results dictionary
        """
        table = Table(title="Evolution Results", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Add basic metrics
        table.add_row("Evolution ID", results.get('evolution_id', 'N/A'))
        table.add_row("Status", results.get('status', 'unknown').upper())
        table.add_row("Duration", f"{results.get('duration', 0):.2f} seconds")
        
        # Add solution metrics
        if 'solutions_generated' in results:
            table.add_row("Solutions Generated", str(results['solutions_generated']))
            table.add_row("Solutions Validated", str(results.get('solutions_validated', 0)))
        
        # Add integration results
        if 'integrations' in results:
            table.add_row("Modules Integrated", str(results['integrations'].get('successful', 0)))
            table.add_row("Integration Failures", str(results['integrations'].get('failed', 0)))
        
        self.console.print(table)

    def _save_evolution_log(self) -> None:
        """
        Save the current evolution log to disk.
        
        This method saves the current evolution cycle and metrics to a JSON file.
        It handles serialization of the data and creates backups if needed.
        """
        try:
            if not hasattr(self, 'evolution_dir') or not self.evolution_dir:
                self.evolution_dir = Path.home() / ".ellma" / "evolution"
                self.evolution_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = self.evolution_dir / 'evolution_history.json'
            
            # Create a copy of the current cycle without any unpicklable objects
            cycle_copy = {}
            if hasattr(self, 'current_cycle') and self.current_cycle:
                for k, v in self.current_cycle.items():
                    try:
                        json.dumps(v)  # Test if serializable
                        cycle_copy[k] = v
                    except (TypeError, OverflowError):
                        cycle_copy[k] = str(v)
            
            # Add to evolution log if not already present
            if not hasattr(self, 'evolution_log'):
                self.evolution_log = []
                
            if cycle_copy and (not self.evolution_log or self.evolution_log[-1] != cycle_copy):
                self.evolution_log.append(cycle_copy)
            
            # Ensure metrics exist
            if not hasattr(self, 'evolution_metrics'):
                self.evolution_metrics = {
                    'total_cycles': 0,
                    'successful_cycles': 0,
                    'failed_cycles': 0,
                    'modules_created': 0,
                    'modules_removed': 0,
                    'performance_improvement': 0.0
                }
            
            # Save to file
            with open(log_file, 'w') as f:
                json.dump({
                    'version': '1.0',
                    'last_updated': datetime.now().isoformat(),
                    'cycles': self.evolution_log,
                    'metrics': self.evolution_metrics
                }, f, indent=2)
                
            logger.debug(f"Saved evolution log to {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save evolution log: {e}", exc_info=True)
            # Try to save a minimal log if full log fails
            try:
                log_file = self.evolution_dir / 'evolution_history_fallback.json'
                with open(log_file, 'w') as f:
                    json.dump({
                        'error': str(e),
                        'last_cycle_status': self.current_cycle.get('status', 'unknown') if hasattr(self, 'current_cycle') else 'unknown',
                        'timestamp': datetime.now().isoformat()
                    }, f)
            except Exception as inner_e:
                logger.critical(f"Completely failed to save evolution log: {inner_e}")
    
    def _log_evolution(self, results: Dict):
        """
        Log the results of an evolution cycle
        
        Args:
            results: Dictionary containing evolution results
        """
        self.evolution_log.append(results)
        
        # Save to file
        history_file = self.evolution_dir / "evolution_history.json"
        try:
            # Ensure directory exists
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file (pretty-printed JSON)
            with open(history_file, 'w') as f:
                json.dump(self.evolution_log, f, indent=2, default=str)
                
            logger.info(f"Logged evolution cycle {results.get('evolution_id', 'unknown')} to {history_file}")
            
        except Exception as e:
            logger.error(f"Failed to log evolution results: {e}")
            raise