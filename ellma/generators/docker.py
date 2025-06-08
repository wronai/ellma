"""
ELLMa Docker Configuration Generator

This module generates Docker configurations including Dockerfiles,
docker-compose.yml files, and deployment configurations.
"""

import re
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from ellma.utils.logger import get_logger

logger = get_logger(__name__)

class DockerGenerator:
    """
    Docker Configuration Generator

    Generates Docker configurations using LLM with built-in templates
    and best practices for containerization.
    """

    def __init__(self, agent):
        """Initialize Docker Generator"""
        self.agent = agent
        self.templates = self._load_templates()
        self.base_images = self._load_base_images()

    def generate(self, task_description: str, **kwargs) -> Dict[str, str]:
        """
        Generate Docker configuration for given task

        Args:
            task_description: Description of what to containerize
            **kwargs: Additional parameters

        Returns:
            Dictionary with generated Docker files
        """
        # Extract parameters
        app_type = kwargs.get('type', 'web')  # web, api, worker, database
        language = kwargs.get('language', 'python')
        base_image = kwargs.get('base_image', None)
        multi_stage = kwargs.get('multi_stage', True)
        compose = kwargs.get('compose', True)

        # Check if we have an LLM available
        if not self.agent.llm:
            return self._generate_fallback_config(task_description, **kwargs)

        try:
            # Generate Dockerfile
            dockerfile = self._generate_dockerfile(task_description, **kwargs)

            result = {'dockerfile': dockerfile}

            # Generate docker-compose.yml if requested
            if compose:
                result['docker_compose'] = self._generate_compose(task_description, **kwargs)

            # Generate additional files
            result.update(self._generate_supporting_files(**kwargs))

            return result

        except Exception as e:
            logger.error(f"Docker configuration generation failed: {e}")
            return self._generate_fallback_config(task_description, **kwargs)

    def _generate_dockerfile(self, task_description: str, **kwargs) -> str:
        """Generate Dockerfile using LLM"""

        language = kwargs.get('language', 'python')
        app_type = kwargs.get('type', 'web')
        multi_stage = kwargs.get('multi_stage', True)

        prompt = f"""Generate a Dockerfile for the following application:
{task_description}

Requirements:
- Application type: {app_type}
- Programming language: {language}
- Use multi-stage build: {multi_stage}
- Follow Docker best practices
- Minimize image size
- Include security considerations
- Add proper labels and metadata
- Use non-root user when possible
- Implement health checks

Best practices to follow:
- Use specific version tags, not 'latest'
- Combine RUN commands to reduce layers
- Use .dockerignore to exclude unnecessary files
- Set appropriate working directory
- Use COPY instead of ADD when possible
- Clean up package manager caches

Generate ONLY the Dockerfile content:
"""

        if self.agent.llm:
            dockerfile = self.agent.generate(prompt, max_tokens=800)
            dockerfile = self._extract_dockerfile_content(dockerfile)
        else:
            dockerfile = self._get_template_dockerfile(language, app_type)

        # Enhance with best practices
        dockerfile = self._enhance_dockerfile(dockerfile, **kwargs)

        return dockerfile

    def _generate_compose(self, task_description: str, **kwargs) -> str:
        """Generate docker-compose.yml"""

        services = kwargs.get('services', ['app'])
        database = kwargs.get('database', None)
        redis = kwargs.get('redis', False)
        nginx = kwargs.get('nginx', False)

        prompt = f"""Generate a docker-compose.yml file for:
{task_description}

Requirements:
- Main application service
- Include database: {database if database else 'none'}
- Include Redis: {redis}
- Include Nginx: {nginx}
- Use environment variables for configuration
- Include proper networking
- Add volumes for persistent data
- Include health checks
- Use restart policies

Generate ONLY the docker-compose.yml content:
"""

        if self.agent.llm:
            compose = self.agent.generate(prompt, max_tokens=600)
            compose = self._extract_compose_content(compose)
        else:
            compose = self._get_template_compose(**kwargs)

        return compose

    def _generate_supporting_files(self, **kwargs) -> Dict[str, str]:
        """Generate supporting files like .dockerignore, entrypoint.sh"""

        files = {}

        # Generate .dockerignore
        files['dockerignore'] = self._generate_dockerignore(**kwargs)

        # Generate entrypoint script if needed
        if kwargs.get('entrypoint', False):
            files['entrypoint.sh'] = self._generate_entrypoint(**kwargs)

        # Generate environment file template
        files['env.example'] = self._generate_env_template(**kwargs)

        return files

    def _extract_dockerfile_content(self, text: str) -> str:
        """Extract Dockerfile content from LLM response"""
        # Look for Dockerfile in code blocks
        dockerfile_pattern = r'```(?:dockerfile|docker)?\n(.*?)\n```'
        match = re.search(dockerfile_pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # If no code blocks, look for lines starting with Docker commands
        lines = text.split('\n')
        dockerfile_lines = []
        in_dockerfile = False

        for line in lines:
            if line.strip().upper().startswith(('FROM', 'RUN', 'COPY', 'ADD', 'WORKDIR', 'ENV', 'EXPOSE')):
                in_dockerfile = True

            if in_dockerfile:
                dockerfile_lines.append(line)

        if dockerfile_lines:
            return '\n'.join(dockerfile_lines)

        return text.strip()

    def _extract_compose_content(self, text: str) -> str:
        """Extract docker-compose content from LLM response"""
        # Look for YAML in code blocks
        yaml_pattern = r'```(?:yaml|yml)?\n(.*?)\n```'
        match = re.search(yaml_pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        return text.strip()

    def _enhance_dockerfile(self, dockerfile: str, **kwargs) -> str:
        """Enhance Dockerfile with additional best practices"""

        lines = dockerfile.split('\n')
        enhanced_lines = []

        # Add header comment
        header = f"""# Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Task: {kwargs.get('task_description', 'Docker configuration')}
"""
        enhanced_lines.extend(header.split('\n'))

        # Process each line
        for line in lines:
            line = line.strip()
            if not line:
                enhanced_lines.append('')
                continue

            # Add security enhancements
            if line.upper().startswith('FROM'):
                enhanced_lines.append(line)
                # Add security labels
                enhanced_lines.append('')
                enhanced_lines.append('# Security and metadata labels')
                enhanced_lines.append('LABEL maintainer="ELLMa Generated"')
                enhanced_lines.append('LABEL security.updates="auto"')

            elif line.upper().startswith('RUN'):
                # Enhance RUN commands with cleanup
                if 'apt-get' in line and 'clean' not in line:
                    line += ' && apt-get clean && rm -rf /var/lib/apt/lists/*'
                elif 'yum' in line and 'clean' not in line:
                    line += ' && yum clean all'
                enhanced_lines.append(line)

            else:
                enhanced_lines.append(line)

        # Add health check if not present
        dockerfile_content = '\n'.join(enhanced_lines)
        if 'HEALTHCHECK' not in dockerfile_content.upper():
            enhanced_lines.append('')
            enhanced_lines.append('# Health check')
            enhanced_lines.append('HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\')
            enhanced_lines.append('  CMD curl -f http://localhost:8000/health || exit 1')

        return '\n'.join(enhanced_lines)

    def _generate_dockerignore(self, **kwargs) -> str:
        """Generate .dockerignore file"""

        language = kwargs.get('language', 'python')

        base_ignore = """# Git
.git
.gitignore
README.md
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Runtime
*.pid
*.seed
*.pid.lock
"""

        language_specific = {
            'python': """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
""",
            'node': """
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache
""",
            'java': """
# Java
target/
*.jar
*.war
*.ear
*.class
.mvn/
""",
            'go': """
# Go
vendor/
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
"""
        }

        return base_ignore + language_specific.get(language, '')

    def _generate_entrypoint(self, **kwargs) -> str:
        """Generate entrypoint.sh script"""

        return """#!/bin/bash
set -e

# Wait for database if needed
if [ "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    while ! nc -z $DB_HOST $DB_PORT; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is up - executing command"
fi

# Run migrations or setup if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    # Add migration command here
fi

# Execute the main command
exec "$@"
"""

    def _generate_env_template(self, **kwargs) -> str:
        """Generate .env.example file"""

        return """# Application Configuration
APP_NAME=myapp
APP_ENV=production
APP_DEBUG=false
APP_PORT=8000

# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/dbname
DB_HOST=db
DB_PORT=5432
DB_NAME=myapp
DB_USER=myapp
DB_PASSWORD=secretpassword

# Redis Configuration (if using Redis)
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# External Services
# API_KEY=your-api-key
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=user@example.com
# SMTP_PASSWORD=password
"""

    def _get_template_dockerfile(self, language: str, app_type: str) -> str:
        """Get template Dockerfile for language/app type"""

        templates = self.templates.get(language, {})
        return templates.get(app_type, templates.get('default', self._get_generic_dockerfile()))

    def _get_template_compose(self, **kwargs) -> str:
        """Get template docker-compose.yml"""

        database = kwargs.get('database')
        redis = kwargs.get('redis', False)

        compose = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
    depends_on:
      - db
    restart: unless-stopped
"""

        if database == 'postgresql':
            compose += """
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: secretpassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
"""

        if redis:
            compose += """
  redis:
    image: redis:7-alpine
    restart: unless-stopped
"""

        if database == 'postgresql':
            compose += """
volumes:
  postgres_data:
"""

        return compose

    def _get_generic_dockerfile(self) -> str:
        """Get generic Dockerfile template"""

        return """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "app.py"]
"""

    def _generate_fallback_config(self, task_description: str, **kwargs) -> Dict[str, str]:
        """Generate fallback configuration when LLM is not available"""

        language = kwargs.get('language', 'python')

        return {
            'dockerfile': self._get_template_dockerfile(language, kwargs.get('type', 'web')),
            'docker_compose': self._get_template_compose(**kwargs),
            'dockerignore': self._generate_dockerignore(**kwargs),
            'env.example': self._generate_env_template(**kwargs)
        }

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load Dockerfile templates for different languages and app types"""

        return {
            'python': {
                'web': """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    curl \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

COPY --chown=appuser:appuser . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
""",

                'api': """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

COPY --chown=appuser:appuser . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
            },

            'node': {
                'web': """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

COPY --chown=nextjs:nodejs . .
USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["npm", "start"]
"""
            }
        }

    def _load_base_images(self) -> Dict[str, List[str]]:
        """Load recommended base images for different languages"""

        return {
            'python': ['python:3.11-slim', 'python:3.10-alpine', 'python:3.11'],
            'node': ['node:18-alpine', 'node:16-alpine', 'node:18-slim'],
            'java': ['openjdk:17-jre-slim', 'openjdk:11-jre-slim'],
            'go': ['golang:1.20-alpine', 'scratch'],
            'nginx': ['nginx:alpine', 'nginx:stable-alpine']
        }

if __name__ == "__main__":
    # Test the generator
    class MockAgent:
        def __init__(self):
            self.llm = None

        def generate(self, prompt, **kwargs):
            return '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]'''

    agent = MockAgent()
    generator = DockerGenerator(agent)

    # Test Docker configuration generation
    config = generator.generate("Web application with PostgreSQL database")
    print("Generated Dockerfile:")
    print(config['dockerfile'])

    if 'docker_compose' in config:
        print("\nGenerated docker-compose.yml:")
        print(config['docker_compose'])