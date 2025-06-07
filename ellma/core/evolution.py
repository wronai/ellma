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
import importlib.util
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from ellma import EvolutionError
from ellma.utils.logger import get_logger

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

    def __init__(self, agent):
        """
        Initialize Evolution Engine with enhanced configuration

        Args:
            agent: ELLMa agent instance
        """
        self.agent = agent
        self.console = Console()
        self.evolution_log = []
        self.capabilities = set()
        self.improvement_suggestions = []
        self.last_evolution_time = None
        self.evolution_metrics = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'modules_created': 0,
            'modules_removed': 0,
            'performance_improvement': 0.0
        }

        # Load and validate evolution configuration
        self._load_configuration()

        # Setup evolution environment
        self._setup_directories()
        self._setup_resource_limits()
        self._load_evolution_history()
        
        # Initialize evolution state
        self.current_cycle = None
        self.is_evolving = False

    def _load_configuration(self):
        """Load and validate evolution configuration"""
        self.evolution_config = self.agent.config.get("evolution", {})
        
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

    def _setup_resource_limits(self):
        """Configure system resource limits for evolution"""
        try:
            import resource
            # Convert MB to bytes
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            new_soft = min(soft if soft != resource.RLIM_INFINITY else float('inf'), 
                         self.max_memory_mb * 1024 * 1024)
            resource.setrlimit(resource.RLIMIT_AS, (new_soft, hard))
            logger.debug(f"Set memory limit to {self.max_memory_mb}MB")
        except Exception as e:
            logger.warning(f"Could not set resource limits: {e}")

    def _setup_directories(self):
        """Create and validate evolution directories"""
        # Base directories
        self.evolution_dir = self.agent.home_dir / "evolution"
        self.generated_modules_dir = self.evolution_dir / "generated"
        self.analysis_dir = self.evolution_dir / "analysis"
        self.backup_dir = self.evolution_dir / "backups"
        self.temp_dir = self.evolution_dir / "temp"
        
        # Create all required directories
        for directory in [self.evolution_dir, self.generated_modules_dir, 
                         self.analysis_dir, self.backup_dir, self.temp_dir]:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # Ensure directories are writable
                if not os.access(str(directory), os.W_OK):
                    raise PermissionError(f"Directory not writable: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise

    def _load_evolution_history(self):
        """Load and validate previous evolution cycles"""
        history_file = self.evolution_dir / "evolution_history.json"
        backup_file = self.backup_dir / f"evolution_history_{int(time.time())}.json"
        
        if not history_file.exists():
            logger.info("No evolution history found, starting fresh")
            self.evolution_log = []
            return
            
        try:
            # Create backup before loading
            if history_file.exists():
                import shutil
                shutil.copy2(str(history_file), str(backup_file))
                logger.debug(f"Created backup of evolution history at {backup_file}")
            
            # Load history
            with open(history_file, 'r') as f:
                history = json.load(f)
                
            # Validate history structure
            if not isinstance(history, list):
                raise ValueError("Invalid history format: expected list")
                
            # Update metrics from history
            self.evolution_metrics['total_cycles'] = len(history)
            self.evolution_metrics['successful_cycles'] = sum(
                1 for cycle in history if cycle.get('status') == 'success'
            )
            self.evolution_metrics['failed_cycles'] = self.evolution_metrics['total_cycles'] - self.evolution_metrics['successful_cycles']
            
            self.evolution_log = history
            logger.info(f"Loaded {len(self.evolution_log)} evolution cycles ({self.evolution_metrics['successful_cycles']} successful)")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evolution history: {e}")
            self.evolution_log = []
        except Exception as e:
            logger.error(f"Failed to load evolution history: {e}")
            self.evolution_log = []

    def evolve(self, force: bool = False) -> Dict:
        """
        Main evolution process with enhanced capabilities

        Args:
            force: If True, force evolution even if conditions aren't optimal

        Returns:
            Evolution results dictionary with detailed metrics
        """
        if not self.enabled and not force:
            msg = "[yellow]Evolution is disabled in configuration[/yellow]"
            self.console.print(msg)
            logger.warning("Evolution attempted but disabled in config")
            return {"status": "disabled", "message": msg}

        if self.is_evolving:
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

        try:
            # Check system resources
            if not self._check_system_resources() and not force:
                msg = "[yellow]Insufficient system resources for evolution[/yellow]"
                self.console.print(msg)
                return {"status": "resource_constrained", "message": msg}

            self.console.print(Panel(
                "[bold cyan]🧬 ELLMa Evolution Cycle Starting[/bold cyan]",
                title="Self-Improvement",
                subtitle=f"Cycle #{self.evolution_metrics['total_cycles'] + 1}",
                border_style="cyan"
            ))

        except Exception as e:
            error_msg = f"Failed to start evolution cycle: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.is_evolving = False
            return {"status": "error", "message": error_msg}

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
            min_memory_mb = 1024  # 1GB minimum
            if mem.available < (min_memory_mb * 1024 * 1024):
                logger.warning(f"Insufficient memory: {mem.available/(1024*1024):.1f}MB available, "
                             f"{min_memory_mb}MB required")
                return False
            
            # Check disk space
            min_disk_space = 2 * 1024 * 1024 * 1024  # 2GB
            _, _, free = shutil.disk_usage("/")
            if free < min_disk_space:
                logger.warning(f"Insufficient disk space: {free/(1024*1024):.1f}MB available, "
                             f"{min_disk_space/(1024*1024):.1f}MB required")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return False

        evolution_start = time.time()
        evolution_id = f"evolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Phase 1: Analysis
            self.console.print("[yellow]📊 Phase 1: Analyzing current state...[/yellow]")
            analysis_results = self._analyze_current_state()

            # Phase 2: Opportunity Identification
            self.console.print("[yellow]🎯 Phase 2: Identifying opportunities...[/yellow]")
            opportunities = self._identify_opportunities(analysis_results)

            # Phase 3: Solution Generation
            self.console.print("[yellow]🛠️  Phase 3: Generating solutions...[/yellow]")
            solutions = self._generate_solutions(opportunities)

            # Phase 4: Testing & Validation
            self.console.print("[yellow]🧪 Phase 4: Testing solutions...[/yellow]")
            validated_solutions = self._test_solutions(solutions)

            # Phase 5: Integration
            self.console.print("[yellow]⚡ Phase 5: Integrating improvements...[/yellow]")
            integration_results = self._integrate_solutions(validated_solutions)

            # Phase 6: Learning Update
            self.console.print("[yellow]🧠 Phase 6: Updating knowledge...[/yellow]")
            learning_results = self._update_learning(integration_results)

            # Compile results
            evolution_time = time.time() - evolution_start
            results = {
                "evolution_id": evolution_id,
                "timestamp": datetime.now().isoformat(),
                "duration": evolution_time,
                "analysis": analysis_results,
                "opportunities": opportunities,
                "solutions_generated": len(solutions),
                "solutions_validated": len(validated_solutions),
                "integrations": integration_results,
                "learning": learning_results,
                "status": "success"
            }

            # Update metrics
            self.agent.performance_metrics['evolution_cycles'] += 1

            # Log evolution
            self._log_evolution(results)

            # Display results
            self._display_evolution_results(results)

            return results

        except Exception as e:
            error_results = {
                "evolution_id": evolution_id,
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - evolution_start,
                "error": str(e),
                "status": "failed"
            }
            self._log_evolution(error_results)
            raise EvolutionError(f"Evolution cycle failed: {e}")

    def _analyze_current_state(self) -> Dict:
        """Analyze current agent capabilities and performance"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "agent_status": self.agent.get_status(),
            "performance_analysis": self._analyze_performance(),
            "capability_assessment": self._assess_capabilities(),
            "resource_usage": self._analyze_resource_usage(),
            "failure_patterns": self._analyze_failures()
        }

        # Save analysis
        analysis_file = self.analysis_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)

        return analysis

    def _analyze_performance(self) -> Dict:
        """
        Analyze performance metrics with enhanced statistics
        
        Returns:
            Dict containing comprehensive performance analysis
        """
        metrics = self.agent.performance_metrics
        
        # Basic metrics
        total_executions = metrics.get('successful_executions', 0) + metrics.get('failed_executions', 0)
        success_rate = metrics.get('successful_executions', 0) / max(total_executions, 1)
        avg_execution_time = metrics.get('total_execution_time', 0) / max(total_executions, 1)
        
        # Command success rates
        command_stats = {}
        for cmd, stats in metrics.get('command_stats', {}).items():
            cmd_total = stats.get('success', 0) + stats.get('fail', 0)
            if cmd_total > 0:
                command_stats[cmd] = {
                    'success_rate': stats.get('success', 0) / cmd_total,
                    'avg_time': stats.get('total_time', 0) / cmd_total,
                    'total': cmd_total
                }
        
        # Identify problematic commands
        problematic_commands = [
            cmd for cmd, stats in command_stats.items()
            if stats['success_rate'] < 0.8 or stats['avg_time'] > 5.0
        ]
        
        # Resource usage
        resource_usage = {
            'memory_mb': metrics.get('peak_memory_usage_mb', 0),
            'cpu_percent': metrics.get('peak_cpu_percent', 0),
            'io_operations': metrics.get('io_operations', 0)
        }
        
        # Performance score (0-1, higher is better)
        perf_score = min(1.0, success_rate * (1 / max(avg_execution_time, 0.01)))
        
        return {
            # Basic metrics
            'total_commands': metrics.get('commands_executed', 0),
            'success_rate': success_rate,
            'failure_rate': 1 - success_rate,
            'average_execution_time': avg_execution_time,
            'total_execution_time': metrics.get('total_execution_time', 0),
            'performance_score': perf_score,
            
            # Detailed statistics
            'command_stats': command_stats,
            'problematic_commands': problematic_commands,
            'resource_usage': resource_usage,
            'timestamps': {
                'first_command': metrics.get('first_command_time'),
                'last_command': metrics.get('last_command_time'),
                'uptime_seconds': time.time() - (metrics.get('start_time', time.time()))
            }
        }

    def _assess_capabilities(self) -> Dict:
        """Assess current capabilities"""
        return {
            "modules_count": len(self.agent.modules),
            "commands_count": len(self.agent.commands),
            "available_modules": list(self.agent.commands.keys()),
            "model_loaded": self.agent.llm is not None,
            "custom_modules": self._count_custom_modules()
        }

    def _analyze_resource_usage(self) -> Dict:
        """Analyze system resource usage"""
        import psutil

        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids())
        }

    def _analyze_failures(self) -> List[Dict]:
        """Analyze recent failures to identify patterns"""
        recent_failures = [
            task for task in self.agent.task_history[-100:]  # Last 100 tasks
            if not task['success']
        ]

        failure_patterns = {}
        for failure in recent_failures:
            command = failure['command']
            error = failure['result']

            # Group by command type
            if command not in failure_patterns:
                failure_patterns[command] = {
                    'count': 0,
                    'errors': [],
                    'avg_execution_time': 0
                }

            failure_patterns[command]['count'] += 1
            failure_patterns[command]['errors'].append(error)

        return list(failure_patterns.items())

    def _count_custom_modules(self) -> int:
        """Count custom/generated modules"""
        custom_count = 0
        if self.generated_modules_dir.exists():
            custom_count = len(list(self.generated_modules_dir.glob("*.py")))
        return custom_count

    def _identify_opportunities(self, analysis: Dict) -> List[Dict]:
        """
        Identify improvement opportunities with enhanced analysis
        
        Args:
            analysis: Performance analysis results
            
        Returns:
            List of improvement opportunities with priority and context
        """
        opportunities = []
        now = time.time()
        
        # 1. Performance-based opportunities
        perf = analysis.get('performance_analysis', {})
        
        # High failure rate
        if perf.get('failure_rate', 0) > 0.1:
            opportunities.append({
                'id': f"perf_failure_{int(now)}",
                'type': 'performance',
                'category': 'reliability',
                'priority': 'high',
                'description': f'High command failure rate ({perf["failure_rate"]*100:.1f}%)',
                'metrics': {'failure_rate': perf['failure_rate']},
                'suggested_actions': [
                    'improve_error_handling',
                    'add_retry_mechanism',
                    'enhance_validation'
                ],
                'impact': 'high',
                'effort': 'medium',
                'created_at': now
            })
        
        # 2. Capability gaps
        for cmd in perf.get('problematic_commands', []):
            if cmd not in getattr(self.agent, 'command_registry', {}):
                opportunities.append({
                    'id': f"cap_missing_{cmd}_{int(now)}",
                    'type': 'capability',
                    'category': 'missing_feature',
                    'priority': 'high',
                    'description': f'Missing command: {cmd}',
                    'suggested_actions': [f'add_{cmd}_command'],
                    'impact': 'high',
                    'effort': 'medium',
                    'created_at': now
                })
        
        # 3. Resource optimization
        res = analysis.get('resource_usage', {})
        if res.get('memory_usage', 0) > 80:  # If memory usage > 80%
            opportunities.append({
                'id': f"res_memory_{int(now)}",
                'type': 'resource',
                'category': 'memory',
                'priority': 'high',
                'description': f'High memory usage: {res["memory_usage"]:.1f}%',
                'metrics': {'memory_percent': res['memory_usage']},
                'suggested_actions': [
                    'optimize_memory_usage',
                    'add_memory_limits',
                    'implement_garbage_collection'
                ],
                'impact': 'high',
                'effort': 'high',
                'created_at': now
            })
        
        # 4. LLM-based opportunity identification
        if hasattr(self.agent, 'llm') and self.agent.llm is not None:
            try:
                llm_opportunities = self._llm_identify_opportunities(analysis)
                opportunities.extend(llm_opportunities)
            except Exception as e:
                logger.error(f"LLM opportunity identification failed: {e}")
        
        # Sort opportunities by priority (high to low) and creation time (newest first)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        opportunities.sort(key=lambda x: (priority_order.get(x.get('priority', 'low'), 2), 
                                        -x.get('created_at', 0)))
        
        return opportunities
        
    def _llm_identify_opportunities(self, analysis: Dict) -> List[Dict]:
        """Use LLM to identify additional improvement opportunities"""
        if not hasattr(self.agent, 'generate'):
            return []
            
        prompt = f"""
        Analyze this ELLMa agent performance data and suggest improvement opportunities:
        
        Performance Metrics:
        - Success Rate: {analysis['performance_analysis']['success_rate']:.2%}
        - Average Execution Time: {analysis['performance_analysis']['average_execution_time']:.2f}s
        - Available Modules: {analysis['capability_assessment']['available_modules']}
        
        Focus on:
        1. Missing essential functionality
        2. Performance bottlenecks
        3. New capabilities that would make the agent more useful
        
        Return a JSON array of opportunities with this structure:
        [
          {{
            "type": "capability|performance|reliability",
            "priority": "high|medium|low",
            "description": "Clear description",
            "suggested_actions": ["action1", "action2"]
          }}
        ]
        """
        
        try:
            response = self.agent.generate(prompt, max_tokens=500)
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"LLM opportunity identification failed: {e}")
            
        return []

        return []

    def _generate_solutions(self, opportunities: List[Dict]) -> List[Dict]:
        """Generate solutions for identified opportunities"""
        solutions = []
        total_ops = len(opportunities)
        
        if total_ops == 0:
            self.console.print("[yellow]No opportunities found to generate solutions for[/yellow]")
            return solutions

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                "•",
                TextColumn("({task.completed}/{task.total})"),
                "•",
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
        ) as progress:
            task = progress.add_task(
                "[cyan]Generating solutions...",
                total=total_ops
            )

            for i, opportunity in enumerate(opportunities, 1):
                try:
                    # Log which opportunity is being processed
                    desc = opportunity.get('description', 'No description')
                    progress.console.print(
                        f"[dim]Processing opportunity {i}/{total_ops}: {desc[:100]}{'...' if len(desc) > 100 else ''}"
                    )
                    
                    # Generate the solution
                    solution = self._generate_single_solution(opportunity)
                    
                    if solution:
                        solutions.append(solution)
                        progress.console.print(
                            f"[green]✓ Generated solution for: {desc[:80]}{'...' if len(desc) > 80 else ''}"
                        )
                    else:
                        progress.console.print(
                            f"[yellow]⚠️  No solution generated for: {desc[:80]}{'...' if len(desc) > 80 else ''}"
                        )
                        
                    progress.advance(task)
                    
                except Exception as e:
                    error_msg = f"Failed to generate solution for {opportunity.get('description', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    progress.console.print(f"[red]✗ {error_msg}")
                    progress.advance(task)
                    continue

        return solutions

    def _generate_single_solution(self, opportunity: Dict) -> Optional[Dict]:
        """Generate a single solution for an opportunity"""
        if not self.agent.llm:
            return None

        action = opportunity['suggested_action']

        # Generate solution based on action type
        if action.startswith('create_new_modules'):
            return self._generate_new_module_solution(opportunity)
        elif action.startswith('improve_error_handling'):
            return self._generate_error_handling_solution(opportunity)
        elif action.startswith('optimize_execution'):
            return self._generate_optimization_solution(opportunity)
        elif action.startswith('fix_') and action.endswith('_command'):
            return self._generate_command_fix_solution(opportunity)
        else:
            return self._generate_generic_solution(opportunity)

    def _generate_new_module_solution(self, opportunity: Dict) -> Dict:
        """Generate a new module solution"""
        prompt = f"""
        Create a new Python module for ELLMa agent to address this opportunity:
        {opportunity['description']}

        The module should:
        1. Follow ELLMa module pattern
        2. Include error handling
        3. Be useful for system administration or automation
        4. Have clear documentation

        Generate complete Python code:

        ```python
        class NewModule:
            def __init__(self, agent):
                self.agent = agent
                self.name = "module_name"

            def get_commands(self):
                return {{
                    'newmodule': self
                }}

            def action_name(self, *args, **kwargs):
                '''Action description'''
                # Implementation
                return result
        ```

        Make it practical and immediately useful.
        """

        try:
            code = self.agent.generate(prompt, max_tokens=800)

            # Extract Python code
            import re
            code_match = re.search(r'```python\n(.*?)\n```', code, re.DOTALL)
            if code_match:
                module_code = code_match.group(1)

                return {
                    'type': 'new_module',
                    'opportunity_id': id(opportunity),
                    'description': opportunity['description'],
                    'code': module_code,
                    'module_name': 'generated_module_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'priority': opportunity['priority']
                }
        except Exception as e:
            logger.error(f"Failed to generate new module: {e}")

        return None

    def _generate_error_handling_solution(self, opportunity: Dict) -> Dict:
        """Generate error handling improvement"""
        return {
            'type': 'error_handling',
            'opportunity_id': id(opportunity),
            'description': 'Improve error handling and retry logic',
            'code': '''
def enhanced_error_handler(func):
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        return wrapper
            ''',
            'module_name': 'error_handling_enhancement',
            'priority': opportunity['priority']
        }

    def _generate_optimization_solution(self, opportunity: Dict) -> Dict:
        """Generate performance optimization solution"""
        return {
            'type': 'optimization',
            'opportunity_id': id(opportunity),
            'description': 'Cache frequently used operations',
            'code': '''
import time
from functools import lru_cache

class PerformanceCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.ttl = 300  # 5 minutes

    def get(self, key):
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key, value):
        self.cache[key] = value
        self.timestamps[key] = time.time()
            ''',
            'module_name': 'performance_cache',
            'priority': opportunity['priority']
        }

    def _generate_command_fix_solution(self, opportunity: Dict) -> Dict:
        """Generate command fix solution"""
        command_name = opportunity['suggested_action'].replace('fix_', '').replace('_command', '')

        return {
            'type': 'command_fix',
            'opportunity_id': id(opportunity),
            'description': f'Fix issues in {command_name} command',
            'code': f'''
# Enhanced {command_name} command with better error handling
def enhanced_{command_name}(self, *args, **kwargs):
    try:
        # Add validation
        if not args:
            raise ValueError("Arguments required")

        # Original logic with improvements
        result = self.original_{command_name}(*args, **kwargs)
        return result

    except Exception as e:
        self.agent.console.print(f"[red]Error in {command_name}: {{e}}[/red]")
        return {{"error": str(e), "status": "failed"}}
            ''',
            'module_name': f'{command_name}_fix',
            'priority': opportunity['priority']
        }

    def _generate_generic_solution(self, opportunity: Dict) -> Optional[Dict]:
        """Generate generic solution"""
        prompt = f"""
        Create a Python solution for this improvement opportunity:
        {opportunity['description']}

        Generate practical code that can be integrated into ELLMa agent.
        Focus on the specific problem described.

        Return only Python code without explanations.
        """

        try:
            code = self.agent.generate(prompt, max_tokens=400)
            return {
                'type': 'generic',
                'opportunity_id': id(opportunity),
                'description': opportunity['description'],
                'code': code,
                'module_name': 'generic_solution',
                'priority': opportunity['priority']
            }
        except Exception as e:
            logger.error(f"Failed to generate generic solution: {e}")
            return None

    def _test_solutions(self, solutions: List[Dict]) -> List[Dict]:
        """
        Test and validate generated solutions
        
        Args:
            solutions: List of solution dictionaries to test
            
        Returns:
            List of validated solutions
        """
        self.console.print(f"[yellow]Testing {len(solutions)} solutions...[/yellow]")
        validated_solutions = []
        
        for solution in solutions:
            try:
                # Simple validation - check required fields
                if all(k in solution for k in ['type', 'description', 'code']):
                    solution['test_status'] = 'validated'
                    solution['test_timestamp'] = datetime.now().isoformat()
                    validated_solutions.append(solution)
                else:
                    solution['test_status'] = 'invalid'
                    solution['error'] = 'Missing required fields'
            except Exception as e:
                solution['test_status'] = 'error'
                solution['error'] = str(e)
                logger.error(f"Error testing solution: {e}")
        
        return validated_solutions

    def _integrate_solutions(self, solutions: List[Dict]) -> Dict:
        """
        Integrate validated solutions into the agent
        
        Args:
            solutions: List of validated solutions
            
        Returns:
            Integration results
        """
        self.console.print(f"[yellow]Integrating {len(solutions)} solutions...[/yellow]")
        results = {
            'total': len(solutions),
            'successful': 0,
            'failed': 0,
            'integrated': []
        }
        
        for solution in solutions:
            try:
                if solution.get('test_status') == 'validated':
                    module_name = f"generated_{len(os.listdir(self.generated_modules_dir)) + 1}"
                    module_path = self.generated_modules_dir / f"{module_name}.py"
                    
                    with open(module_path, 'w') as f:
                        f.write(solution.get('code', ''))
                    
                    solution['module_path'] = str(module_path)
                    results['successful'] += 1
                    results['integrated'].append({
                        'module': module_name,
                        'path': str(module_path),
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Error integrating solution: {e}")
                results['failed'] += 1
        
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

    def _log_evolution(self, results: Dict) -> None:
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