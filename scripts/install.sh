#!/bin/bash
#
# ELLMa Installation Script
# Automated installation and setup for ELLMa (Evolutionary Local LLM Agent)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ELLMA_VERSION="0.1.6"
PYTHON_MIN_VERSION="3.8"
INSTALL_DIR="${HOME}/.ellma"
MODELS_DIR="${INSTALL_DIR}/models"
VENV_DIR="${INSTALL_DIR}/venv"
CONFIG_FILE="${INSTALL_DIR}/config.yaml"
LOG_FILE="${INSTALL_DIR}/install.log"

# Global flags
FORCE_INSTALL=false
SKIP_MODEL_DOWNLOAD=false
VERBOSE=false
DEVELOPMENT_MODE=false

# Logging functions
log() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

log_debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $*" | tee -a "$LOG_FILE"
    fi
}

# Error handling
error_exit() {
    log_error "$1"
    exit "${2:-1}"
}

# Cleanup function
cleanup() {
    log_debug "Cleaning up temporary files..."
    # Add cleanup logic here if needed
}

# Trap for cleanup
trap cleanup EXIT

# Usage information
usage() {
    cat << EOF
ELLMa Installation Script v${ELLMA_VERSION}

Usage: $0 [options]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -f, --force             Force installation even if already installed
    -s, --skip-model        Skip model download
    -d, --dev               Install in development mode
    --install-dir DIR       Custom installation directory (default: ~/.ellma)
    --python-version VER    Minimum Python version (default: 3.8)

Examples:
    $0                      # Standard installation
    $0 --verbose --force    # Verbose forced installation
    $0 --dev                # Development installation
    $0 --skip-model         # Install without downloading model

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--force)
                FORCE_INSTALL=true
                shift
                ;;
            -s|--skip-model)
                SKIP_MODEL_DOWNLOAD=true
                shift
                ;;
            -d|--dev)
                DEVELOPMENT_MODE=true
                shift
                ;;
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --python-version)
                PYTHON_MIN_VERSION="$2"
                shift 2
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python_version() {
    log_info "Checking Python version..."

    if ! command_exists python3; then
        error_exit "Python 3 is not installed. Please install Python ${PYTHON_MIN_VERSION} or later."
    fi

    local python_version
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")

    # Version comparison
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int, '${PYTHON_MIN_VERSION}'.split('.'))) else 1)"; then
        error_exit "Python ${PYTHON_MIN_VERSION} or later is required. Found: ${python_version}"
    fi

    log_info "Python version: ${python_version} ✓"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check operating system
    local os_type
    os_type=$(uname -s)
    case "$os_type" in
        Linux*)     log_debug "Operating system: Linux" ;;
        Darwin*)    log_debug "Operating system: macOS" ;;
        CYGWIN*|MINGW*|MSYS*) log_debug "Operating system: Windows" ;;
        *)          log_warn "Unknown operating system: $os_type" ;;
    esac

    # Check available memory
    local mem_gb
    if command_exists free; then
        mem_gb=$(free -g | awk 'NR==2{printf "%.1f", $2}')
        log_debug "Available memory: ${mem_gb}GB"

        if (( $(echo "$mem_gb < 4" | bc -l) )); then
            log_warn "Low memory detected (${mem_gb}GB). ELLMa may perform slowly."
        fi
    fi

    # Check disk space
    local disk_space
    disk_space=$(df -h "$HOME" | awk 'NR==2 {print $4}')
    log_debug "Available disk space: $disk_space"

    # Check for required commands
    local required_commands=("curl" "wget" "git")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            log_warn "$cmd is not installed. Some features may not work properly."
        else
            log_debug "$cmd: available ✓"
        fi
    done
}

# Create installation directories
create_directories() {
    log_info "Creating installation directories..."

    local directories=(
        "$INSTALL_DIR"
        "$MODELS_DIR"
        "${INSTALL_DIR}/modules"
        "${INSTALL_DIR}/logs"
        "${INSTALL_DIR}/config"
        "${INSTALL_DIR}/evolution"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_debug "Created directory: $dir"
        else
            log_debug "Directory exists: $dir"
        fi
    done
}

# Create Python virtual environment
create_virtual_environment() {
    log_info "Creating Python virtual environment..."

    if [ -d "$VENV_DIR" ] && [ "$FORCE_INSTALL" = false ]; then
        log_info "Virtual environment already exists. Use --force to recreate."
        return 0
    fi

    if [ -d "$VENV_DIR" ] && [ "$FORCE_INSTALL" = true ]; then
        log_info "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    fi

    python3 -m venv "$VENV_DIR"

    # Activate virtual environment
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"

    # Upgrade pip
    pip install --upgrade pip wheel setuptools

    log_info "Virtual environment created: $VENV_DIR ✓"
}

# Install ELLMa package
install_ellma() {
    log_info "Installing ELLMa package..."

    # Activate virtual environment
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"

    if [ "$DEVELOPMENT_MODE" = true ]; then
        # Development installation
        if [ -f "setup.py" ]; then
            log_info "Installing ELLMa in development mode..."
            pip install -e ".[dev]"
        else
            error_exit "setup.py not found. Are you in the ELLMa project directory?"
        fi
    else
        # Production installation
        log_info "Installing ELLMa from PyPI..."
        pip install ellma=="$ELLMA_VERSION"
    fi

    log_info "ELLMa package installed ✓"
}

# Download language model
download_model() {
    if [ "$SKIP_MODEL_DOWNLOAD" = true ]; then
        log_info "Skipping model download (--skip-model flag)"
        return 0
    fi

    log_info "Downloading Mistral 7B model..."

    local model_file="${MODELS_DIR}/mistral-7b.gguf"
    local model_url="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

    if [ -f "$model_file" ] && [ "$FORCE_INSTALL" = false ]; then
        log_info "Model already exists: $model_file"
        return 0
    fi

    # Check available download tools
    if command_exists curl; then
        log_info "Downloading model with curl..."
        curl -L -o "$model_file" "$model_url" --progress-bar
    elif command_exists wget; then
        log_info "Downloading model with wget..."
        wget -O "$model_file" "$model_url" --progress=bar:force
    else
        log_error "Neither curl nor wget is available for downloading."
        log_info "Please download the model manually:"
        log_info "URL: $model_url"
        log_info "Save to: $model_file"
        return 1
    fi

    # Verify download
    if [ -f "$model_file" ] && [ -s "$model_file" ]; then
        local file_size
        file_size=$(du -h "$model_file" | cut -f1)
        log_info "Model downloaded successfully: $file_size ✓"
    else
        error_exit "Model download failed or file is empty"
    fi
}

# Create configuration file
create_config() {
    log_info "Creating configuration file..."

    if [ -f "$CONFIG_FILE" ] && [ "$FORCE_INSTALL" = false ]; then
        log_info "Configuration file already exists: $CONFIG_FILE"
        return 0
    fi

    cat > "$CONFIG_FILE" << EOF
# ELLMa Configuration File
# Generated by installation script on $(date)

# Model Configuration
model:
  path: ${MODELS_DIR}/mistral-7b.gguf
  context_length: 4096
  temperature: 0.7
  threads: $(nproc 2>/dev/null || echo 4)
  gpu_layers: 0

# Evolution Configuration
evolution:
  enabled: true
  auto_improve: true
  learning_rate: 0.1
  evolution_interval: 50
  max_modules: 100
  backup_before_evolution: true

# Modules Configuration
modules:
  auto_load: true
  custom_path: ${INSTALL_DIR}/modules
  builtin_modules: true
  allow_remote: false

# Logging Configuration
logging:
  level: INFO
  file: ${INSTALL_DIR}/logs/ellma.log
  console: true
  max_size: 10MB
  backup_count: 5

# Security Configuration
security:
  sandbox_mode: false
  allowed_commands: null
  blocked_commands: null
  max_execution_time: 300
  require_confirmation: false
EOF

    log_info "Configuration file created: $CONFIG_FILE ✓"
}

# Create shell activation script
create_activation_script() {
    log_info "Creating activation script..."

    local activation_script="${INSTALL_DIR}/activate.sh"

    cat > "$activation_script" << EOF
#!/bin/bash
#
# ELLMa Environment Activation Script
#

# Activate Python virtual environment
source "${VENV_DIR}/bin/activate"

# Set environment variables
export ELLMA_HOME="${INSTALL_DIR}"
export ELLMA_CONFIG="${CONFIG_FILE}"
export PATH="${VENV_DIR}/bin:\$PATH"

echo "ELLMa environment activated!"
echo "Home: \$ELLMA_HOME"
echo "Config: \$ELLMA_CONFIG"
echo ""
echo "Quick start:"
echo "  ellma --help          # Show help"
echo "  ellma init            # Initialize ELLMa"
echo "  ellma shell           # Start interactive shell"
echo "  ellma evolve          # Trigger evolution"
echo ""
EOF

    chmod +x "$activation_script"
    log_info "Activation script created: $activation_script ✓"
}

# Add to shell profile
add_to_shell_profile() {
    log_info "Adding ELLMa to shell profile..."

    local shell_profiles=(
        "$HOME/.bashrc"
        "$HOME/.zshrc"
        "$HOME/.profile"
    )

    local ellma_block="
# ELLMa (Evolutionary Local LLM Agent)
export ELLMA_HOME=\"${INSTALL_DIR}\"
export PATH=\"${VENV_DIR}/bin:\$PATH\"
alias ellma-activate=\"source ${INSTALL_DIR}/activate.sh\"
"

    for profile in "${shell_profiles[@]}"; do
        if [ -f "$profile" ]; then
            # Check if already added
            if ! grep -q "ELLMA_HOME" "$profile"; then
                echo "$ellma_block" >> "$profile"
                log_debug "Added ELLMa to $profile"
            else
                log_debug "ELLMa already in $profile"
            fi
        fi
    done

    log_info "Shell profile updated ✓"
}

# Test installation
test_installation() {
    log_info "Testing installation..."

    # Activate virtual environment
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"

    # Test ELLMa command
    if ellma --version >/dev/null 2>&1; then
        local version
        version=$(ellma --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "unknown")
        log_info "ELLMa command available: v$version ✓"
    else
        error_exit "ELLMa command not working properly"
    fi

    # Test Python import
    if python3 -c "import ellma; print('ELLMa import test: OK')" 2>/dev/null; then
        log_info "ELLMa Python package import ✓"
    else
        error_exit "Cannot import ELLMa Python package"
    fi

    # Test configuration
    if [ -f "$CONFIG_FILE" ]; then
        log_info "Configuration file exists ✓"
    else
        log_warn "Configuration file missing"
    fi

    # Test model file
    local model_file="${MODELS_DIR}/mistral-7b.gguf"
    if [ -f "$model_file" ]; then
        log_info "Model file exists ✓"
    else
        log_warn "Model file missing (can be downloaded later)"
    fi

    log_info "Installation test completed ✓"
}

# Display post-installation instructions
show_post_install_info() {
    cat << EOF

${GREEN}🎉 ELLMa Installation Completed Successfully! 🎉${NC}

${CYAN}Installation Details:${NC}
  Location: ${INSTALL_DIR}
  Config:   ${CONFIG_FILE}
  Logs:     ${INSTALL_DIR}/logs/
  Models:   ${MODELS_DIR}/

${CYAN}Quick Start:${NC}
  1. Activate ELLMa environment:
     ${YELLOW}source ${INSTALL_DIR}/activate.sh${NC}

  2. Initialize ELLMa:
     ${YELLOW}ellma init${NC}

  3. Start interactive shell:
     ${YELLOW}ellma shell${NC}

  4. Try some commands:
     ${YELLOW}ellma exec "system.scan"${NC}
     ${YELLOW}ellma generate python --task="web scraper"${NC}
     ${YELLOW}ellma evolve${NC}

${CYAN}Useful Commands:${NC}
  ellma --help                 # Show all commands
  ellma status                 # Check agent status
  ellma setup --download-model # Download additional models
  ellma-activate              # Quick activation alias

${CYAN}Documentation:${NC}
  GitHub: https://github.com/ellma-ai/ellma
  Docs:   https://ellma.readthedocs.io/

${CYAN}Next Steps:${NC}
  • Start a new terminal or run: source ~/.bashrc
  • Try the quick start commands above
  • Explore the interactive shell: ellma shell
  • Let ELLMa evolve: ellma evolve

${GREEN}Happy coding with ELLMa! 🚀${NC}

EOF
}

# Main installation function
main() {
    log "Starting ELLMa installation v${ELLMA_VERSION}"

    # Setup log file
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"

    # Display banner
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🧬 ELLMa - Evolutionary Local LLM Agent                        ║
║                                                                  ║
║   Self-improving AI assistant that evolves with your needs       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF

    log_info "Installation started at $(date)"

    # Pre-installation checks
    check_python_version
    check_requirements

    # Installation steps
    create_directories
    create_virtual_environment
    install_ellma

    if [ "$SKIP_MODEL_DOWNLOAD" = false ]; then
        download_model
    fi

    create_config
    create_activation_script
    add_to_shell_profile

    # Post-installation
    test_installation
    show_post_install_info

    log_info "Installation completed successfully at $(date)"
}

# Initialize log file path early
if [ ! -d "${HOME}/.ellma" ]; then
    mkdir -p "${HOME}/.ellma"
fi
LOG_FILE="${HOME}/.ellma/install.log"

# Parse arguments and run main function
parse_args "$@"
main

exit 0