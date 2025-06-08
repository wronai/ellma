#!/usr/bin/env python3
"""
Script to automatically add dependency checking to Python files.

This script will scan all Python files in the project and add the necessary
imports and decorators for dependency checking.
"""

import ast
import astor
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# Template for the secure import
SECURE_IMPORT = """from ellma.core.decorators import secure, validate_input, SecureContext
from ellma.core.security import Dependency, secure_import, SecurityError, ensure_dependencies

"""

# Common dependencies for different modules
MODULE_DEPENDENCIES = {
    # Core dependencies
    'core': [
        ('typing', 'typing', None, None, True),
        ('logging', 'logging', None, None, True),
        ('pathlib', 'pathlib', None, None, True),
    ],
    # CLI dependencies
    'cli': [
        ('click', 'click', '8.0.0', None, True),
        ('rich', 'rich', '10.0.0', None, True),
    ],
    # ML dependencies
    'ml': [
        ('numpy', 'numpy', '1.20.0', None, True),
        ('torch', 'torch', '1.9.0', None, False),
        ('transformers', 'transformers', '4.0.0', None, False),
    ],
    # Web dependencies
    'web': [
        ('requests', 'requests', '2.25.0', None, True),
        ('fastapi', 'fastapi', '0.68.0', None, False),
        ('uvicorn', 'uvicorn', '0.15.0', None, False),
    ]
}

def get_module_category(file_path: str) -> str:
    """Determine the module category based on file path."""
    path_parts = Path(file_path).parts
    if 'core' in path_parts:
        return 'core'
    elif 'cli' in path_parts:
        return 'cli'
    elif any(m in path_parts for m in ['ml', 'models', 'training']):
        return 'ml'
    elif any(m in path_parts for m in ['web', 'api', 'server']):
        return 'web'
    return 'core'  # default

def generate_dependencies(module_category: str) -> str:
    """Generate the dependencies code for a module category."""
    if module_category not in MODULE_DEPENDENCIES:
        return ''
    
    deps = MODULE_DEPENDENCIES[module_category]
    dep_code = []
    
    for name, pkg, min_ver, max_ver, required in deps:
        dep = f"    Dependency(name='{name}', package_name='{pkg}'"
        if min_ver:
            dep += f", min_version='{min_ver}'"
        if max_ver:
            dep += f", max_version='{max_ver}'"
        dep += f", required={required}),"
        dep_code.append(dep)
    
    if not dep_code:
        return ''
        
    return f"\n# Dependencies for {module_category} module\nDEPENDENCIES = [\n" + "\n".join(dep_code) + "\n]\n\n"

def add_dependency_checking(file_path: str) -> bool:
    """Add dependency checking to a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip files that already have security imports
        if 'from ellma.core.decorators import' in content:
            return False
            
        # Parse the AST
        tree = ast.parse(content)
        
        # Find the first import or docstring
        insert_pos = 0
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)) or \
               (isinstance(node, ast.Expr) and isinstance(node.value, ast.Str)):
                insert_pos = i + 1
            else:
                break
        
        # Generate the new imports and dependencies
        module_category = get_module_category(file_path)
        new_content = SECURE_IMPORT
        
        # Add dependencies specific to the module category
        deps_code = generate_dependencies(module_category)
        if deps_code:
            new_content += deps_code
            
            # Add the secure decorator to all functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Skip if already has a decorator
                    if not any(isinstance(dec, ast.Name) and dec.id == 'secure' 
                             for dec in node.decorator_list):
                        # Add @secure() decorator
                        node.decorator_list.insert(0, ast.Call(
                            func=ast.Name(id='secure', ctx=ast.Load()),
                            args=[],
                            keywords=[ast.keyword(
                                arg='dependencies',
                                value=ast.Name(id='DEPENDENCIES' if deps_code else 'None', ctx=ast.Load())
                            )]
                        ))
        
        # Convert AST back to code
        modified_content = astor.to_source(tree)
        
        # Combine the new content with the original content
        lines = content.splitlines(keepends=True)
        if lines and lines[0].startswith('#!'):
            # Keep the shebang line at the top
            shebang = lines[0]
            lines = [shebang, '\n'] + [new_content] + lines[1:]
        else:
            lines = [new_content] + lines
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(''.join(lines))
            
        print(f"Updated {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_directory(directory: str) -> None:
    """Process all Python files in a directory recursively."""
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                if add_dependency_checking(file_path):
                    count += 1
    print(f"\nUpdated {count} files with dependency checking.")

if __name__ == "__main__":
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Process the entire project
    process_directory(project_root)
