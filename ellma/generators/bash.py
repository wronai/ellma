"""
ELLMa Bash Script Generator

This module generates bash scripts using LLM for various system administration
and automation tasks with proper error handling and best practices.
"""

import re
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from ellma.utils.logger import get_logger

logger = get_logger(__name__)


class BashGenerator:
    """
    Bash Script Generator

    Generates bash scripts using LLM with built-in templates,
    best practices, and error handling patterns.
    """

    def __init__(self, agent):
        """Initialize Bash Generator"""
        self.agent = agent
        self.templates = self._load_templates()
        self.common_patterns = self._load_common_patterns()

    def generate(self, task_description: str, **kwargs) -> str:
        """
        Generate bash script for given task

        Args:
            task_description: Description of what the script should do
            **kwargs: Additional parameters

        Returns:
            Generated bash script
        """
        # Extract parameters
        interactive = kwargs.get('interactive', False)
        error_handling = kwargs.get('error_handling', True)
        logging = kwargs.get('logging', True)
        dry_run = kwargs.get('dry_run', False)

        # Check if we have an LLM available
        if not self.agent.llm:
            return self._generate_fallback_script(task_description, **kwargs)

        # Create generation prompt
        prompt = self._create_generation_prompt(task_description, **kwargs)

        try:
            # Generate script using LLM
            generated_script = self.agent.generate(prompt, max_tokens=1000)

            # Post-process and enhance the script
            enhanced_script = self._enhance_script(generated_script, **kwargs)

            # Validate the script
            validation_result = self._validate_script(enhanced_script)

            if validation_result['valid']:
                return enhanced_script
            else:
                logger.warning(f"Generated script validation failed: {validation_result['errors']}")
                # Try to fix common issues
                fixed_script = self._fix_common_issues(enhanced_script)
                return fixed_script

        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return self._generate_fallback_script(task_description, **kwargs)

    def _create_generation_prompt(self, task_description: str, **kwargs) -> str:
        """Create prompt for LLM script generation"""

        prompt = f"""Generate a bash script for the following task:
{task_description}

Requirements:
- Use proper bash syntax and best practices
- Include error handling with 'set -euo pipefail'
- Add helpful comments explaining each step
- Use meaningful variable names
- Include input validation where appropriate
"""

        if kwargs.get('interactive', False):
            prompt += "- Make the script interactive with user prompts\n"

        if kwargs.get('logging', True):
            prompt += "- Include logging statements for important operations\n"

        if kwargs.get('dry_run', False):
            prompt += "- Include a --dry-run option to show what would be done\n"

        if kwargs.get('functions', True):
            prompt += "- Use functions for reusable code blocks\n"

        prompt += """
Example structure:
```bash
#!/bin/bash
set -euo pipefail

# Script description and usage
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
function usage() {
    echo "Usage: $SCRIPT_NAME [options]"
    exit 1
}

function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

# Main script logic
main() {
    # Your code here
}

# Parse arguments and run main
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

Generate ONLY the bash script code, no explanations:
"""

        return prompt

    def _enhance_script(self, script: str, **kwargs) -> str:
        """Enhance generated script with additional features"""

        # Extract just the script code if wrapped in markdown
        script = self._extract_script_code(script)

        # Add shebang if missing
        if not script.startswith('#!/bin/bash'):
            script = '#!/bin/bash\n\n' + script

        # Add error handling if missing
        if 'set -' not in script:
            lines = script.split('\n')
            shebang_line = lines[0] if lines[0].startswith('#!') else ''
            other_lines = lines[1:] if shebang_line else lines

            enhanced_lines = [shebang_line] if shebang_line else []
            enhanced_lines.extend([
                '',
                '# Error handling',
                'set -euo pipefail',
                ''
            ])
            enhanced_lines.extend(other_lines)
            script = '\n'.join(enhanced_lines)

        # Add header comment
        header = self._generate_header(**kwargs)
        script = self._insert_header(script, header)

        # Add common functions if not present
        script = self._add_common_functions(script, **kwargs)

        return script

    def _generate_header(self, **kwargs) -> str:
        """Generate script header with metadata"""
        return f"""#
# Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Task: {kwargs.get('task_description', 'Automated task')}
#"""

    def _insert_header(self, script: str, header: str) -> str:
        """Insert header after shebang"""
        lines = script.split('\n')
        if lines and lines[0].startswith('#!'):
            return lines[0] + '\n' + header + '\n' + '\n'.join(lines[1:])
        else:
            return header + '\n' + script

    def _add_common_functions(self, script: str, **kwargs) -> str:
        """Add common utility functions if not present"""

        functions_to_add = []

        # Add logging function if logging is enabled and not present
        if kwargs.get('logging', True) and 'function log(' not in script and 'log()' not in script:
            functions_to_add.append('''
# Logging function
function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

function log_info() {
    log "INFO: $*"
}

function log_error() {
    log "ERROR: $*" >&2
}

function log_warn() {
    log "WARN: $*" >&2
}
''')

        # Add error handling function
        if 'function error_exit(' not in script and 'error_exit()' not in script:
            functions_to_add.append('''
# Error handling function
function error_exit() {
    log_error "$1"
    exit "${2:-1}"
}
''')

        # Add check command function
        if 'function check_command(' not in script and 'check_command()' not in script:
            functions_to_add.append('''
# Check if command exists
function check_command() {
    if ! command -v "$1" &> /dev/null; then
        error_exit "Required command '$1' not found"
    fi
}
''')

        # Insert functions after set -euo pipefail
        if functions_to_add:
            lines = script.split('\n')
            insert_index = 0

            for i, line in enumerate(lines):
                if 'set -euo pipefail' in line:
                    insert_index = i + 1
                    break

            if insert_index > 0:
                lines.insert(insert_index, ''.join(functions_to_add))
                script = '\n'.join(lines)

        return script

    def _extract_script_code(self, text: str) -> str:
        """Extract bash script code from markdown or plain text"""
        # Look for code blocks
        bash_pattern = r'```(?:bash|sh)?\n(.*?)\n```'
        match = re.search(bash_pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()

        # If no code blocks, look for lines starting with # or commands
        lines = text.split('\n')
        script_lines = []
        in_script = False

        for line in lines:
            # Start collecting when we see shebang or set command
            if line.startswith('#!/bin/bash') or line.startswith('set -'):
                in_script = True

            if in_script:
                script_lines.append(line)

        if script_lines:
            return '\n'.join(script_lines)

        # Fallback: return as-is
        return text.strip()

    def _validate_script(self, script: str) -> Dict[str, Any]:
        """Validate bash script syntax and structure"""
        errors = []
        warnings = []

        # Check for shebang
        if not script.startswith('#!/bin/bash'):
            warnings.append("Missing shebang (#!/bin/bash)")

        # Check for error handling
        if 'set -e' not in script and 'set -euo pipefail' not in script:
            warnings.append("Missing error handling (set -e or set -euo pipefail)")

        # Check for basic syntax issues
        lines = script.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Check for unmatched quotes
            if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                warnings.append(f"Line {i}: Possible unmatched quotes")

            # Check for unsafe variable usage
            if '$' in line and '${' not in line and '"$' not in line:
                # Simple check for unquoted variables
                if re.search(r'\$\w+(?!\w)', line):
                    warnings.append(f"Line {i}: Consider quoting variables")

        # Try basic syntax check if bash is available
        try:
            import subprocess
            result = subprocess.run(
                ['bash', '-n'],
                input=script,
                text=True,
                capture_output=True,
                timeout=5
            )

            if result.returncode != 0:
                errors.append(f"Syntax error: {result.stderr.strip()}")

        except (subprocess.SubprocessError, FileNotFoundError):
            # bash not available for syntax checking
            pass
        except Exception as e:
            warnings.append(f"Could not validate syntax: {e}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _fix_common_issues(self, script: str) -> str:
        """Fix common bash script issues"""
        lines = script.split('\n')
        fixed_lines = []

        for line in lines:
            # Fix common variable quoting issues
            # This is a simplified fix - in practice, you'd want more sophisticated parsing
            fixed_line = re.sub(r'=\$(\w+)(?!\w)', r'="${\1}"', line)
            fixed_line = re.sub(r'\[\s*\$(\w+)', r'[ "${\1}"', fixed_line)

            fixed_lines.append(fixed_line)

        return '\n'.join(fixed_lines)

    def _generate_fallback_script(self, task_description: str, **kwargs) -> str:
        """Generate fallback script when LLM is not available"""

        # Try to match task description to templates
        for template_name, template in self.templates.items():
            if any(keyword in task_description.lower() for keyword in template['keywords']):
                return self._apply_template(template, task_description, **kwargs)

        # Generate basic script structure
        script = f'''#!/bin/bash
set -euo pipefail

#
# Generated by ELLMa - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Task: {task_description}
#

# Logging function
function log() {{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}}

function log_info() {{
    log "INFO: $*"
}}

function log_error() {{
    log "ERROR: $*" >&2
}}

# Error handling function
function error_exit() {{
    log_error "$1"
    exit "${{2:-1}}"
}}

# Main function
function main() {{
    log_info "Starting: {task_description}"

    # TODO: Implement task logic here
    echo "Task: {task_description}"
    echo "Please implement the specific logic for this task."

    log_info "Task completed successfully"
}}

# Run main function
if [[ "${{BASH_SOURCE[0]}}" == "${{0}}" ]]; then
    main "$@"
fi
'''

        return script

    def _load_templates(self) -> Dict[str, Dict]:
        """Load script templates for common tasks"""
        return {
            'backup': {
                'keywords': ['backup', 'archive', 'copy', 'save'],
                'template': '''#!/bin/bash
set -euo pipefail

# Backup script
BACKUP_SOURCE="${1:-}"
BACKUP_DEST="${2:-/tmp/backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

function usage() {
    echo "Usage: $0 <source> [destination]"
    exit 1
}

function main() {
    [[ -z "$BACKUP_SOURCE" ]] && usage
    [[ ! -e "$BACKUP_SOURCE" ]] && { log "Source not found: $BACKUP_SOURCE"; exit 1; }

    BACKUP_FILE="${BACKUP_DEST}/backup_${TIMESTAMP}.tar.gz"
    mkdir -p "$(dirname "$BACKUP_FILE")"

    log "Creating backup: $BACKUP_SOURCE -> $BACKUP_FILE"
    tar -czf "$BACKUP_FILE" -C "$(dirname "$BACKUP_SOURCE")" "$(basename "$BACKUP_SOURCE")"

    log "Backup completed: $BACKUP_FILE"
}

main "$@"
'''
            },

            'monitoring': {
                'keywords': ['monitor', 'watch', 'check', 'status', 'health'],
                'template': '''#!/bin/bash
set -euo pipefail

# System monitoring script
INTERVAL="${1:-60}"
LOG_FILE="${2:-/tmp/monitor.log}"

function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

function check_system() {
    local cpu_usage memory_usage disk_usage

    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)

    log "CPU: ${cpu_usage}% | Memory: ${memory_usage}% | Disk: ${disk_usage}%"

    # Alert if usage is high
    (( $(echo "$cpu_usage > 80" | bc -l) )) && log "WARNING: High CPU usage!"
    (( $(echo "$memory_usage > 80" | bc -l) )) && log "WARNING: High memory usage!"
    (( disk_usage > 85 )) && log "WARNING: High disk usage!"
}

function main() {
    log "Starting system monitoring (interval: ${INTERVAL}s)"

    while true; do
        check_system
        sleep "$INTERVAL"
    done
}

main "$@"
'''
            },

            'cleanup': {
                'keywords': ['cleanup', 'clean', 'remove', 'delete', 'temp'],
                'template': '''#!/bin/bash
set -euo pipefail

# Cleanup script
TARGET_DIR="${1:-/tmp}"
DAYS_OLD="${2:-7}"
DRY_RUN="${3:-false}"

function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

function cleanup_old_files() {
    local dir="$1"
    local days="$2"

    log "Cleaning files older than $days days in $dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN - Files that would be deleted:"
        find "$dir" -type f -mtime +"$days" -print
    else
        local count
        count=$(find "$dir" -type f -mtime +"$days" -delete -print | wc -l)
        log "Deleted $count files"
    fi
}

function main() {
    [[ ! -d "$TARGET_DIR" ]] && { log "Directory not found: $TARGET_DIR"; exit 1; }

    log "Starting cleanup in $TARGET_DIR"
    cleanup_old_files "$TARGET_DIR" "$DAYS_OLD"
    log "Cleanup completed"
}

main "$@"
'''
            },

            'deployment': {
                'keywords': ['deploy', 'install', 'setup', 'configure'],
                'template': '''#!/bin/bash
set -euo pipefail

# Deployment script
APP_NAME="${1:-myapp}"
TARGET_DIR="${2:-/opt/$APP_NAME}"
SERVICE_USER="${3:-$APP_NAME}"

function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

function check_requirements() {
    command -v systemctl &> /dev/null || { log "systemctl not found"; exit 1; }
    [[ $EUID -eq 0 ]] || { log "This script must be run as root"; exit 1; }
}

function create_user() {
    if ! id "$SERVICE_USER" &> /dev/null; then
        log "Creating user: $SERVICE_USER"
        useradd --system --shell /bin/false --home-dir "$TARGET_DIR" "$SERVICE_USER"
    fi
}

function setup_directories() {
    log "Setting up directories"
    mkdir -p "$TARGET_DIR"/{bin,config,logs,data}
    chown -R "$SERVICE_USER:$SERVICE_USER" "$TARGET_DIR"
    chmod 755 "$TARGET_DIR"
}

function main() {
    log "Starting deployment of $APP_NAME"

    check_requirements
    create_user
    setup_directories

    log "Deployment completed successfully"
}

main "$@"
'''
            },

            'network': {
                'keywords': ['network', 'ping', 'port', 'connection', 'firewall'],
                'template': '''#!/bin/bash
set -euo pipefail

# Network diagnostic script
TARGET="${1:-google.com}"
PORT="${2:-80}"

function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

function check_connectivity() {
    local target="$1"

    log "Checking connectivity to $target"

    if ping -c 3 "$target" &> /dev/null; then
        log "✓ Ping to $target successful"
    else
        log "✗ Ping to $target failed"
        return 1
    fi
}

function check_port() {
    local target="$1"
    local port="$2"

    log "Checking port $port on $target"

    if timeout 5 bash -c "</dev/tcp/$target/$port" &> /dev/null; then
        log "✓ Port $port on $target is open"
    else
        log "✗ Port $port on $target is closed or filtered"
        return 1
    fi
}

function main() {
    log "Starting network diagnostics"

    check_connectivity "$TARGET"
    check_port "$TARGET" "$PORT"

    log "Network diagnostics completed"
}

main "$@"
'''
            }
        }

    def _load_common_patterns(self) -> Dict[str, str]:
        """Load common bash patterns and snippets"""
        return {
            'error_handling': 'set -euo pipefail',
            'logging': '''
function log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}
''',
            'usage_function': '''
function usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help    Show this help message"
    exit 1
}
''',
            'argument_parsing': '''
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done
''',
            'check_root': '''
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi
''',
            'check_command': '''
function check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Required command '$1' not found"
        exit 1
    fi
}
'''
        }

    def _apply_template(self, template: Dict, task_description: str, **kwargs) -> str:
        """Apply template with customizations"""
        script = template['template']

        # Replace placeholders if any
        script = script.replace('{{TASK_DESCRIPTION}}', task_description)
        script = script.replace('{{TIMESTAMP}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Add additional features based on kwargs
        if kwargs.get('dry_run', False):
            script = script.replace('DRY_RUN="${3:-false}"', 'DRY_RUN="${3:-true}"')

        return script

    def get_available_templates(self) -> List[str]:
        """Get list of available script templates"""
        return list(self.templates.keys())

    def get_template(self, template_name: str) -> Optional[str]:
        """Get specific template by name"""
        template = self.templates.get(template_name)
        return template['template'] if template else None

    def generate_from_template(self, template_name: str, **kwargs) -> str:
        """Generate script from specific template"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        return self._apply_template(template, kwargs.get('task_description', ''), **kwargs)


if __name__ == "__main__":
    # Test the generator
    class MockAgent:
        def __init__(self):
            self.llm = None

        def generate(self, prompt, **kwargs):
            return '''#!/bin/bash
set -euo pipefail

# Simple test script
echo "Hello, World!"
echo "Task: $1"
'''


    agent = MockAgent()
    generator = BashGenerator(agent)

    # Test script generation
    script = generator.generate("Create a backup script")
    print("Generated script:")
    print(script)

    # Test templates
    print("\nAvailable templates:")
    for template in generator.get_available_templates():
        print(f"- {template}")

    # Test template usage
    backup_script = generator.generate_from_template('backup')
    print(f"\nBackup template:\n{backup_script[:200]}...")