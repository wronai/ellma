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
        Initialize Evolution Engine

        Args:
            agent: ELLMa agent instance
        """
        self.agent = agent
        self.console = Console()
        self.evolution_log = []
        self.capabilities = set()
        self.improvement_suggestions = []

        # Evolution configuration
        self.evolution_config = self.agent.config.get("evolution", {})
        self.enabled = self.evolution_config.get("enabled", True)
        self.auto_improve = self.evolution_config.get("auto_improve", True)
        self.learning_rate = self.evolution_config.get("learning_rate", 0.1)

        # Directories
        self.evolution_dir = self.agent.home_dir / "evolution"
        self.generated_modules_dir = self.evolution_dir / "generated"
        self.analysis_dir = self.evolution_dir / "analysis"

        # Create directories
        self._setup_directories()

        # Load evolution history
        self._load_evolution_history()

    def _setup_directories(self):
        """Create evolution directories"""
        for directory in [self.evolution_dir, self.generated_modules_dir, self.analysis_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_evolution_history(self):
        """Load previous evolution cycles"""
        history_file = self.evolution_dir / "evolution_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.evolution_log = json.load(f)
                logger.info(f"Loaded {len(self.evolution_log)} evolution cycles")
            except Exception as e:
                logger.warning(f"Failed to load evolution history: {e}")

    def evolve(self) -> Dict:
        """
        Main evolution process

        Returns:
            Evolution results dictionary
        """
        if not self.enabled:
            self.console.print("[yellow]Evolution is disabled in configuration[/yellow]")
            return {"status": "disabled"}

        self.console.print(Panel(
            "[bold cyan]🧬 ELLMa Evolution Cycle Starting[/bold cyan]",
            title="Self-Improvement",
            border_style="cyan"
        ))

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
        """Analyze performance metrics"""
        metrics = self.agent.performance_metrics

        total_executions = metrics['successful_executions'] + metrics['failed_executions']
        success_rate = metrics['successful_executions'] / max(total_executions, 1)
        avg_execution_time = metrics['total_execution_time'] / max(total_executions, 1)

        return {
            "total_commands": metrics['commands_executed'],
            "success_rate": success_rate,
            "failure_rate": 1 - success_rate,
            "average_execution_time": avg_execution_time,
            "total_execution_time": metrics['total_execution_time'],
            "performance_score": success_rate * (1 / max(avg_execution_time, 0.01))
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
        """Identify improvement opportunities based on analysis"""
        opportunities = []

        # Performance-based opportunities
        performance = analysis['performance_analysis']
        if performance['failure_rate'] > 0.1:
            opportunities.append({
                'type': 'performance',
                'priority': 'high',
                'description': 'High failure rate detected - need error handling improvements',
                'metrics': {'failure_rate': performance['failure_rate']},
                'suggested_action': 'improve_error_handling'
            })

        if performance['average_execution_time'] > 5.0:
            opportunities.append({
                'type': 'performance',
                'priority': 'medium',
                'description': 'Slow execution times - need optimization',
                'metrics': {'avg_time': performance['average_execution_time']},
                'suggested_action': 'optimize_execution'
            })

        # Capability-based opportunities
        capabilities = analysis['capability_assessment']
        if capabilities['modules_count'] < 5:
            opportunities.append({
                'type': 'capability',
                'priority': 'medium',
                'description': 'Limited modules available - expand functionality',
                'metrics': {'modules_count': capabilities['modules_count']},
                'suggested_action': 'create_new_modules'
            })

        # Failure pattern opportunities
        failures = analysis['failure_patterns']
        for command, pattern in failures:
            if pattern['count'] > 3:
                opportunities.append({
                    'type': 'reliability',
                    'priority': 'high',
                    'description': f'Frequent failures in {command} command',
                    'metrics': {'failure_count': pattern['count']},
                    'suggested_action': f'fix_{command}_command'
                })

        # LLM-based opportunity identification
        if self.agent.llm:
            llm_opportunities = self._llm_identify_opportunities(analysis)
            opportunities.extend(llm_opportunities)

        return opportunities

    def _llm_identify_opportunities(self, analysis: Dict) -> List[Dict]:
        """Use LLM to identify additional opportunities"""
        prompt = f"""
        Analyze this ELLMa agent performance data and identify 3 specific improvement opportunities:

        Performance Metrics:
        - Success Rate: {analysis['performance_analysis']['success_rate']:.2%}
        - Average Execution Time: {analysis['performance_analysis']['average_execution_time']:.2f}s
        - Available Modules: {analysis['capability_assessment']['available_modules']}

        Recent Task History: {len(self.agent.task_history)} tasks

        Focus on:
        1. Missing essential functionality that users might need
        2. Performance bottlenecks that could be optimized
        3. New capabilities that would make the agent more useful

        Return JSON array of opportunities:
        [
          {{
            "type": "capability|performance|reliability",
            "priority": "high|medium|low", 
            "description": "Clear description of the opportunity",
            "suggested_action": "specific_action_to_take"
          }}
        ]
        """

        try:
            response = self.agent.generate(prompt, max_tokens=500)
            # Try to parse JSON response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                opportunities = json.loads(json_match.group())
                return opportunities
        except Exception as e:
            logger.warning(f"LLM opportunity identification failed: {e}")

        return []

    def _generate_solutions(self, opportunities: List[Dict]) -> List[Dict]:
        """Generate solutions for identified opportunities"""
        solutions = []

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=self.console
        ) as progress:

            task = progress.add_task("Generating solutions...", total=len(opportunities))

            for opportunity in opportunities:
                try:
                    solution = self._generate_single_solution(opportunity)
                    if solution:
                        solutions.append(solution)
                        progress.advance(task)
                except Exception as e:
                    logger.error(f"Failed to generate solution for {opportunity}: {e}")
                    progress.advance(task)

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

    def _generate_generic_solution(self, opportunity: Dict) -> Dict:
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
        
    def _log_evolution(self, results: Dict) -> None:
        """
        Log the results of an evolution cycle
        
        Args:
            results: Dictionary containing evolution results
        """
        try:
            # Add to in-memory log
            self.evolution_log.append(results)
            
            # Save to file
            history_file = self.evolution_dir / "evolution_history.json"
            
            # Ensure directory exists
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file (pretty-printed JSON)
            with open(history_file, 'w') as f:
                json.dump(self.evolution_log, f, indent=2, default=str)
                
            logger.info(f"Logged evolution cycle {results.get('evolution_id', 'unknown')} to {history_file}")
            
        except Exception as e:
            logger.error(f"Failed to log evolution results: {e}")
            raise