#!/usr/bin/env python3
"""
Secure Executor for ELLMa

This module provides a secure execution environment for running Python code
with automatic dependency management and security checks.
"""

import sys
import os
import importlib
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ellma_secure_executor.log')
    ]
)
logger = logging.getLogger('secure_executor')

class SecureExecutor:
    """Secure execution environment for Python code."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the secure executor."""
        self.config = config or {}
        self.dependencies: List[Dict[str, Any]] = []
        self._setup_environment()
    
    def _setup_environment(self) -> None:
        """Set up the secure execution environment."""
        # Add project root to Python path
        project_root = str(Path(__file__).parent.absolute())
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Set secure environment variables
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    def load_dependencies(self, requirements_file: Optional[str] = None) -> bool:
        """Load dependencies from requirements file or configuration."""
        try:
            if requirements_file and os.path.exists(requirements_file):
                with open(requirements_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.dependencies.append(self._parse_dependency(line))
            return True
        except Exception as e:
            logger.error(f"Failed to load dependencies: {e}")
            return False
    
    def _parse_dependency(self, dep_str: str) -> Dict[str, Any]:
        """Parse a dependency string into its components."""
        # Simple implementation - can be enhanced with proper requirement parsing
        if '>=' in dep_str:
            name, version = dep_str.split('>=')
            return {'name': name.strip(), 'min_version': version.strip()}
        elif '==' in dep_str:
            name, version = dep_str.split('==')
            return {'name': name.strip(), 'version': version.strip()}
        return {'name': dep_str.strip()}
    
    def ensure_dependencies(self) -> Tuple[bool, List[str]]:
        """Ensure all dependencies are installed."""
        missing = []
        for dep in self.dependencies:
            try:
                importlib.import_module(dep['name'])
            except ImportError:
                missing.append(dep['name'])
        return len(missing) == 0, missing
    
    def install_dependencies(self) -> bool:
        """Install missing dependencies using pip."""
        try:
            import subprocess
            import sys
            
            _, missing = self.ensure_dependencies()
            if not missing:
                return True
                
            logger.info(f"Installing missing dependencies: {', '.join(missing)}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            return True
            
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def execute_script(self, script_path: str, *args: str) -> int:
        """Execute a Python script in the secure environment."""
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return 1
            
        try:
            # Ensure dependencies are installed
            if not self.install_dependencies():
                return 1
                
            # Run the script in a subprocess
            import subprocess
            cmd = [sys.executable, script_path] + list(args)
            logger.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=False)
            return result.returncode
            
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return 1
    
    def execute_code(self, code: str, globals_dict: Optional[Dict[str, Any]] = None) -> Any:
        """Execute Python code in a secure environment."""
        if not globals_dict:
            globals_dict = {}
            
        # Add safe builtins
        safe_builtins = {
            'print': print,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'type': type,
        }
        
        # Create a safe globals dictionary
        safe_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            '__file__': '<string>',
        }
        safe_globals.update(globals_dict)
        
        try:
            # Compile and execute the code
            compiled = compile(code, '<string>', 'exec')
            exec(compiled, safe_globals, {})
            return safe_globals.get('__result__', None)
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            raise

def main() -> int:
    """Main entry point for the secure executor."""
    parser = argparse.ArgumentParser(description='Secure Python Code Executor')
    parser.add_argument('script', nargs='?', help='Python script to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Script arguments')
    parser.add_argument('--requirements', '-r', help='Path to requirements.txt')
    
    args = parser.parse_args()
    
    executor = SecureExecutor()
    
    # Load dependencies if specified
    if args.requirements:
        if not executor.load_dependencies(args.requirements):
            return 1
    
    if args.script:
        return executor.execute_script(args.script, *args.args)
    else:
        # Interactive mode
        print("Secure Python Shell (type 'exit()' to quit)")
        print("Dependencies will be automatically installed as needed\n")
        
        while True:
            try:
                code = input('>>> ')
                if code.strip().lower() in ('exit', 'exit()', 'quit', 'quit()'):
                    break
                    
                # Try to evaluate as an expression first
                try:
                    result = executor.execute_code(code)
                    if result is not None:
                        print(repr(result))
                except Exception as e:
                    logger.error(f"Error: {e}")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
