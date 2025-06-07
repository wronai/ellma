"""
ELLMa - Evolutionary Local LLM Agent
Self-evolving Python package for autonomous task execution
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ellma",
    version="0.1.6",
    description="Evolutionary Local LLM Agent - Self-improving AI assistant",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    author="ELLMa Team",
    author_email="contact@ellma.dev",
    url="https://github.com/ellma-ai/ellma",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.20.0',
            'black>=22.0.0',
            'flake8>=5.0.0',
            'mypy>=0.991',
        ],
        'web': [
            'fastapi>=0.100.0',
            'uvicorn>=0.23.0',
            'websockets>=11.0.0',
        ],
        'audio': [
            'sounddevice>=0.4.0',
            'scipy>=1.9.0',
            'librosa>=0.10.0',
        ]
    },
    entry_points={
        "console_scripts": [
            "ellma=ellma.cli.main:cli",
            "ellma-shell=ellma.cli.shell:interactive_shell",
            "ellma-evolve=ellma.core.evolution:evolve_cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators", 
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="llm ai agent automation evolution mistral local-ai",
    project_urls={
        "Bug Reports": "https://github.com/ellma-ai/ellma/issues",
        "Source": "https://github.com/ellma-ai/ellma",
        "Documentation": "https://ellma.readthedocs.io/",
    },
    zip_safe=False,
)