# Changelog

All notable changes to the ELLMa project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Security**: New security validation module with file permission checks, network access controls, and system command validations
- **Evolution**: Refactored evolution engine into modular components with improved extensibility
  - Added multiple selection strategies (tournament, rank-based, elitism, etc.)
  - Implemented various crossover operators (single-point, uniform, subtree, arithmetic)
  - Added mutation operators (Gaussian, bit-flip, subtree, swap)
  - Created comprehensive configuration system
  - Added population management with history tracking

### Changed
- **Code Organization**: Split large files into smaller, focused modules
  - Refactored `evolution.py` (1032 lines) into a well-organized package
  - Improved module structure for better maintainability
  - Enhanced type hints and documentation throughout the codebase

### Fixed
- **Security**: Fixed file permission validation to properly detect insecure permissions
- **Tests**: Improved test coverage and reliability

### Removed
- **Deprecated**: Removed legacy code that was marked for removal

## [0.1.0] - 2025-06-07

### Added
- Initial project structure
- Core functionality for secure code execution
- Basic module system
- Command-line interface
- Documentation setup

### Changed
- Project setup and configuration
- Dependencies management

[Unreleased]: https://github.com/wronai/ellma/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/wronai/ellma/releases/tag/v0.1.0
