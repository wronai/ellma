"""
ELLMa Python Code Generator

This module generates Python code using LLM for various programming tasks
including scripts, classes, functions, and complete applications.
"""

import ast
import re
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ellma.utils.logger import get_logger

logger = get_logger(__name__)


class PythonGenerator:
    """
    Python Code Generator

    Generates Python code using LLM with built-in templates,
    best practices, and code validation.
    """

    def __init__(self, agent):
        """Initialize Python Generator"""
        self.agent = agent
        self.templates = self._load_templates()
        self.code_patterns = self._load_code_patterns()
        self.style_guide = self._load_style_guide()

    def generate(self, task_description: str, **kwargs) -> str:
        """
        Generate Python code for given task

        Args:
            task_description: Description of what the code should do
            **kwargs: Additional parameters

        Returns:
            Generated Python code
        """
        # Extract parameters
        code_type = kwargs.get('type', 'script')  # script, class, function, module
        async_code = kwargs.get('async', False)
        include_tests = kwargs.get('tests', False)
        style = kwargs.get('style', 'pep8')
        add_typing = kwargs.get('typing', True)

        # Check if we have an LLM available
        if not self.agent.llm:
            return self._generate_fallback_code(task_description, **kwargs)

        # Create generation prompt
        prompt = self._create_generation_prompt(task_description, **kwargs)

        try:
            # Generate code using LLM
            generated_code = self.agent.generate(prompt, max_tokens=1500)

            # Post-process and enhance the code
            enhanced_code = self._enhance_code(generated_code, **kwargs)

            # Validate the code
            validation_result = self._validate_code(enhanced_code)

            if validation_result['valid']:
                # Add tests if requested
                if include_tests:
                    enhanced_code += "\n\n" + self._generate_tests(enhanced_code, task_description)

                return enhanced_code
            else:
                logger.warning(f"Generated code validation failed: {validation_result['errors']}")
                # Try to fix common issues
                fixed_code = self._fix_common_issues(enhanced_code)
                return fixed_code

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return self._generate_fallback_code(task_description, **kwargs)

    def _create_generation_prompt(self, task_description: str, **kwargs) -> str:
        """Create prompt for LLM code generation"""

        code_type = kwargs.get('type', 'script')
        async_code = kwargs.get('async', False)
        add_typing = kwargs.get('typing', True)

        prompt = f"""Generate Python code for the following task:
{task_description}

Requirements:
- Write clean, readable Python code following PEP 8 style guidelines
- Include proper error handling with try/except blocks
- Add docstrings for functions and classes
- Use meaningful variable and function names
- Include input validation where appropriate
"""

        if add_typing:
            prompt += "- Add type hints for function parameters and return values\n"

        if async_code:
            prompt += "- Use async/await patterns where appropriate\n"

        if code_type == 'class':
            prompt += "- Create a well-structured class with proper methods\n"
        elif code_type == 'function':
            prompt += "- Create a standalone function with clear purpose\n"
        elif code_type == 'module':
            prompt += "- Create a complete module with multiple functions/classes\n"

        prompt += f"""
Code type: {code_type}

Example structure for {code_type}:
"""

        if code_type == 'class':
            prompt += '''
```python
class ExampleClass:
    """Class description."""

    def __init__(self, param: str):
        """Initialize the class."""
        self.param = param

    def method(self, arg: int) -> str:
        """Method description."""
        try:
            # Implementation
            return result
        except Exception as e:
            raise ValueError(f"Error: {e}")
```
'''
        elif code_type == 'function':
            prompt += '''
```python
def example_function(param: str, optional: int = 0) -> dict:
    """
    Function description.

    Args:
        param: Parameter description
        optional: Optional parameter

    Returns:
        Description of return value

    Raises:
        ValueError: If param is invalid
    """
    if not param:
        raise ValueError("param cannot be empty")

    try:
        # Implementation
        result = {"param": param, "optional": optional}
        return result
    except Exception as e:
        raise RuntimeError(f"Function failed: {e}")
```
'''
        else:  # script
            prompt += '''
```python
#!/usr/bin/env python3
"""
Script description.
"""

import sys
from typing import Optional

def main() -> None:
    """Main function."""
    try:
        # Implementation
        print("Script completed successfully")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```
'''

        prompt += "\nGenerate ONLY the Python code, no explanations:"

        return prompt

    def _enhance_code(self, code: str, **kwargs) -> str:
        """Enhance generated code with additional features"""

        # Extract just the code if wrapped in markdown
        code = self._extract_code_from_markdown(code)

        # Add header comment if it's a script
        code_type = kwargs.get('type', 'script')
        if code_type == 'script' and not code.startswith('#!/usr/bin/env python'):
            header = self._generate_header(**kwargs)
            code = header + '\n\n' + code

        # Add imports if missing common ones
        code = self._add_missing_imports(code)

        # Format according to style guide
        code = self._apply_style_formatting(code)

        # Add type hints if missing and requested
        if kwargs.get('typing', True):
            code = self._add_type_hints(code)

        return code

    def _generate_header(self, **kwargs) -> str:
        """Generate script header"""
        task_description = kwargs.get('task_description', 'Generated script')

        return f'''#!/usr/bin/env python3
"""
{task_description}

Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""'''

    def _extract_code_from_markdown(self, text: str) -> str:
        """Extract Python code from markdown blocks"""
        # Look for code blocks
        python_pattern = r'```(?:python|py)?\n(.*?)\n```'
        match = re.search(python_pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        # If no code blocks, return as-is
        return text.strip()

    def _add_missing_imports(self, code: str) -> str:
        """Add commonly needed imports if they're used but not imported"""
        imports_to_add = []

        # Common patterns and their required imports
        import_patterns = {
            r'\bos\.': 'import os',
            r'\bsys\.': 'import sys',
            r'\bjson\.': 'import json',
            r'\bre\.': 'import re',
            r'\bdatetime\b': 'from datetime import datetime',
            r'\bPath\b': 'from pathlib import Path',
            r'\brequests\.': 'import requests',
            r'\btyping\.': 'from typing import ',
            r'\bOptional\b': 'from typing import Optional',
            r'\bList\b': 'from typing import List',
            r'\bDict\b': 'from typing import Dict',
        }

        existing_imports = self._extract_existing_imports(code)

        for pattern, import_stmt in import_patterns.items():
            if re.search(pattern, code) and not any(imp in import_stmt for imp in existing_imports):
                imports_to_add.append(import_stmt)

        if imports_to_add:
            # Find where to insert imports
            lines = code.split('\n')
            insert_index = 0

            # Skip shebang and docstrings
            for i, line in enumerate(lines):
                if line.startswith('#!') or line.startswith('"""') or line.startswith("'''"):
                    continue
                if line.strip() and not line.startswith('#'):
                    insert_index = i
                    break

            # Insert imports
            for import_stmt in sorted(set(imports_to_add)):
                lines.insert(insert_index, import_stmt)
                insert_index += 1

            code = '\n'.join(lines)

        return code

    def _extract_existing_imports(self, code: str) -> List[str]:
        """Extract existing import statements"""
        imports = []

        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)

        return imports

    def _apply_style_formatting(self, code: str) -> str:
        """Apply basic style formatting"""
        lines = code.split('\n')
        formatted_lines = []

        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()

            # Fix common spacing issues
            line = re.sub(r'([,;])\s*', r'\1 ', line)  # Space after commas
            line = re.sub(r'\s*([=!<>]+)\s*', r' \1 ', line)  # Space around operators
            line = re.sub(r'\s+', ' ', line)  # Multiple spaces to single

            formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def _add_type_hints(self, code: str) -> str:
        """Add basic type hints where missing"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated analysis

        lines = code.split('\n')

        for i, line in enumerate(lines):
            # Add type hints to function definitions
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*:', line):
                # Simple pattern matching for common cases
                if '-> ' not in line and 'return ' in code:
                    # Try to infer return type from return statements
                    if 'return None' in code or 'return' not in code:
                        line = line.replace(':', ' -> None:')
                    elif 'return ""' in code or 'return f"' in code:
                        line = line.replace(':', ' -> str:')
                    elif 'return []' in code or 'return [' in code:
                        line = line.replace(':', ' -> List:')
                    elif 'return {}' in code or 'return {' in code:
                        line = line.replace(':', ' -> Dict:')
                    else:
                        line = line.replace(':', ' -> Any:')

                lines[i] = line

        return '\n'.join(lines)

    def _validate_code(self, code: str) -> Dict[str, Any]:
        """Validate Python code syntax and structure"""
        errors = []
        warnings = []

        try:
            # Parse the AST to check syntax
            tree = ast.parse(code)

            # Basic structural checks
            has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            has_classes = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            has_main = 'if __name__ == "__main__"' in code

            # Check for common issues
            if not has_functions and not has_classes and len(code.strip().split('\n')) > 5:
                warnings.append("No functions or classes defined in multi-line code")

            # Check for proper main guard in scripts
            if not has_main and 'def main(' in code:
                warnings.append("Consider adding 'if __name__ == \"__main__\"' guard")

            # Check for docstrings
            if has_functions:
                function_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                for func in function_nodes:
                    if not ast.get_docstring(func):
                        warnings.append(f"Function '{func.name}' missing docstring")

        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
        except Exception as e:
            errors.append(f"Parse error: {e}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _fix_common_issues(self, code: str) -> str:
        """Fix common Python code issues"""
        lines = code.split('\n')
        fixed_lines = []

        for line in lines:
            # Fix indentation issues (basic)
            if line.strip() and not line.startswith(' ') and not line.startswith('#'):
                if any(keyword in line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:']):
                    # These should be at proper indentation
                    pass

            # Fix common syntax issues
            line = re.sub(r'print\s+([^(].*)', r'print(\1)', line)  # print statement to function

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _generate_tests(self, code: str, task_description: str) -> str:
        """Generate basic unit tests for the code"""

        if not self.agent.llm:
            return self._generate_basic_test_template(code)

        test_prompt = f"""Generate unit tests for this Python code:

```python
{code}
```

Task: {task_description}

Requirements:
- Use unittest framework
- Test main functions and methods
- Include both positive and negative test cases
- Add docstrings for test methods
- Test edge cases and error handling

Generate complete test code:
"""

        try:
            test_code = self.agent.generate(test_prompt, max_tokens=800)
            test_code = self._extract_code_from_markdown(test_code)

            # Ensure test code has proper structure
            if 'import unittest' not in test_code:
                test_code = 'import unittest\n\n' + test_code

            return test_code

        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return self._generate_basic_test_template(code)

    def _generate_basic_test_template(self, code: str) -> str:
        """Generate basic test template"""
        return f'''import unittest

class TestGeneratedCode(unittest.TestCase):
    """Test cases for generated code."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # TODO: Add specific tests for the generated code
        self.assertTrue(True)

    def test_error_handling(self):
        """Test error handling."""
        # TODO: Add tests for error conditions
        pass

if __name__ == '__main__':
    unittest.main()
'''

    def _generate_fallback_code(self, task_description: str, **kwargs) -> str:
        """Generate fallback code when LLM is not available"""

        code_type = kwargs.get('type', 'script')

        if code_type == 'class':
            return self._generate_class_template(task_description)
        elif code_type == 'function':
            return self._generate_function_template(task_description)
        else:
            return self._generate_script_template(task_description)

    def _generate_script_template(self, task_description: str) -> str:
        """Generate basic script template"""
        return f'''#!/usr/bin/env python3
"""
{task_description}

Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
from typing import Optional

def main() -> None:
    """Main function."""
    try:
        # TODO: Implement {task_description.lower()}
        print("Task: {task_description}")
        print("Please implement the specific logic for this task.")

    except Exception as e:
        print(f"Error: {{e}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    def _generate_class_template(self, task_description: str) -> str:
        """Generate basic class template"""
        class_name = self._extract_class_name(task_description)

        return f'''"""
{task_description}

Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

from typing import Any, Optional

class {class_name}:
    """
    {task_description}
    """

    def __init__(self):
        """Initialize {class_name}."""
        # TODO: Add initialization logic
        pass

    def process(self, data: Any) -> Any:
        """
        Process data according to task requirements.

        Args:
            data: Input data to process

        Returns:
            Processed data

        Raises:
            ValueError: If data is invalid
        """
        if data is None:
            raise ValueError("Data cannot be None")

        # TODO: Implement processing logic
        return data
'''

    def _generate_function_template(self, task_description: str) -> str:
        """Generate basic function template"""
        function_name = self._extract_function_name(task_description)

        return f'''"""
{task_description}

Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

from typing import Any, Optional

def {function_name}(data: Any) -> Any:
    """
    {task_description}

    Args:
        data: Input data to process

    Returns:
        Processed data

    Raises:
        ValueError: If data is invalid
    """
    if data is None:
        raise ValueError("Data cannot be None")

    try:
        # TODO: Implement function logic
        result = data  # Placeholder
        return result

    except Exception as e:
        raise RuntimeError(f"Function failed: {{e}}")
'''

    def _extract_class_name(self, description: str) -> str:
        """Extract class name from description"""
        # Simple heuristic to create class name
        words = re.findall(r'\b[A-Za-z]+\b', description)
        if words:
            return ''.join(word.capitalize() for word in words[:3]) + 'Class'
        return 'GeneratedClass'

    def _extract_function_name(self, description: str) -> str:
        """Extract function name from description"""
        # Simple heuristic to create function name
        words = re.findall(r'\b[a-zA-Z]+\b', description.lower())
        if words:
            name = '_'.join(words[:4])
            return re.sub(r'[^a-z_]', '', name)
        return 'generated_function'

    def _load_templates(self) -> Dict[str, str]:
        """Load code templates"""
        return {
            'web_scraper': '''
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

class WebScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def scrape(self, path: str) -> Dict[str, str]:
        response = self.session.get(f"{self.base_url}/{path}")
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        return {"title": soup.title.string if soup.title else ""}
''',

            'data_processor': '''
import pandas as pd
from typing import Any, Dict

class DataProcessor:
    def __init__(self):
        self.data = None

    def load_data(self, file_path: str) -> None:
        self.data = pd.read_csv(file_path)

    def process(self) -> Dict[str, Any]:
        if self.data is None:
            raise ValueError("No data loaded")

        return {
            "shape": self.data.shape,
            "columns": list(self.data.columns),
            "summary": self.data.describe().to_dict()
        }
''',

            'file_handler': '''
import os
from pathlib import Path
from typing import List, Optional

class FileHandler:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def list_files(self, pattern: str = "*") -> List[str]:
        return [str(f) for f in self.base_path.glob(pattern)]

    def read_file(self, filename: str) -> str:
        file_path = self.base_path / filename
        with open(file_path, 'r') as f:
            return f.read()
'''
        }

    def _load_code_patterns(self) -> Dict[str, str]:
        """Load common code patterns"""
        return {
            'error_handling': '''
try:
    # operation
    pass
except SpecificError as e:
    # handle specific error
    pass
except Exception as e:
    # handle general error
    pass
''',

            'logging_setup': '''
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
''',

            'argument_parsing': '''
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('input', help='Input file')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--verbose', action='store_true')
    return parser.parse_args()
'''
        }

    def _load_style_guide(self) -> Dict[str, Any]:
        """Load style guide rules"""
        return {
            'max_line_length': 88,
            'indentation': 4,
            'use_type_hints': True,
            'require_docstrings': True,
            'naming_convention': 'snake_case'
        }


if __name__ == "__main__":
    # Test the generator
    class MockAgent:
        def __init__(self):
            self.llm = None

        def generate(self, prompt, **kwargs):
            return '''
def example_function(data):
    """Process data and return result."""
    if not data:
        raise ValueError("Data cannot be empty")

    result = data.upper()
    return result
'''


    agent = MockAgent()
    generator = PythonGenerator(agent)

    # Test code generation
    code = generator.generate("Create a function to process text data")
    print("Generated code:")
    print(code)

    # Test validation
    validation = generator._validate_code(code)
    print(f"\nValidation: {validation}")