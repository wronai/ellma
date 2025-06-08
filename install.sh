#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect package manager
detect_package_manager() {
    if command_exists apt-get; then
        echo "apt"
    elif command_exists dnf; then
        echo "dnf"
    elif command_exists yum; then
        echo "yum"
    elif command_exists pacman; then
        echo "pacman"
    elif command_exists zypper; then
        echo "zypper"
    else
        echo "unsupported"
    fi
}

# Function to install dependencies
install_dependencies() {
    local pm="$1"
    echo -e "${YELLOW}Installing dependencies using $pm...${NC}"
    
    case "$pm" in
        apt)
            sudo apt-get update
            sudo apt-get install -y python3-dev portaudio19-dev libasound2-dev \
                                 python3-pip python3-venv build-essential \
                                 libssl-dev zlib1g-dev libbz2-dev \
                                 libreadline-dev libsqlite3-dev wget curl \
                                 llvm libncurses5-dev libncursesw5-dev \
                                 xz-utils tk-dev libffi-dev liblzma-dev \
                                 python3-openssl git
            ;;
        dnf)
            sudo dnf install -y python3-devel portaudio-devel alsa-lib-devel \
                             python3-pip python3-virtualenv make gcc \
                             openssl-devel bzip2-devel libffi-devel \
                             xz-devel wget curl git
            ;;
        yum)
            sudo yum install -y python3-devel portaudio-devel alsa-lib-devel \
                             python3-pip python3-virtualenv make gcc \
                             openssl-devel bzip2-devel libffi-devel \
                             xz-devel wget curl git
            ;;
        pacman)
            sudo pacman -Syu --noconfirm python python-pip python-virtualenv \
                                      base-devel portaudio alsa-lib \
                                      openssl bzip2 libffi xz wget curl git
            ;;
        zypper)
            sudo zypper install -y python3-devel portaudio-devel alsa-devel \
                                 python3-pip python3-virtualenv make gcc \
                                 libopenssl-devel libbz2-devel libffi-devel \
                                 xz-devel wget curl git
            ;;
        *)
            echo -e "${RED}Unsupported package manager. Please install dependencies manually.${NC}"
            echo "Required packages: python3-dev portaudio-devel alsa-lib-devel python3-pip python3-venv"
            exit 1
            ;;
    esac
}

# Function to create virtual environment and install Python packages
setup_python_env() {
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip and setuptools
    pip install --upgrade pip setuptools wheel
    
    # Install Poetry if not installed
    if ! command_exists poetry; then
        echo -e "${YELLOW}Installing Poetry...${NC}"
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Install project dependencies
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    poetry install --with audio
    
    # Verify installation
    if poetry run python -c "import audioop" 2>/dev/null; then
        echo -e "${GREEN}Audio support verified!${NC}"
    else
        echo -e "${YELLOW}Warning: Audio support might not be fully functional.${NC}"
        echo "You may need to install additional system packages or reinstall Python with audio support."
    fi
}

# Main execution
main() {
    echo -e "${GREEN}Starting ELLMa installation...${NC}"
    
    # Detect package manager
    PM=$(detect_package_manager)
    if [ "$PM" = "unsupported" ]; then
        echo -e "${RED}Unsupported Linux distribution. Please install dependencies manually.${NC}"
        exit 1
    fi
    
    echo -e "Detected package manager: ${YELLOW}$PM${NC}"
    
    # Install system dependencies
    install_dependencies "$PM"
    
    # Setup Python environment
    setup_python_env
    
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo -e "To activate the virtual environment, run: ${YELLOW}source venv/bin/activate${NC}"
    echo -e "To start ELLMa, run: ${YELLOW}poetry run ellma${NC}"
}

# Run main function
main "$@"
