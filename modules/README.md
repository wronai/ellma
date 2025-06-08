# ELLMa Module System

This directory contains the modules that extend ELLMa's capabilities. Each module is a self-contained component that can be dynamically loaded and managed by the system.

## Module Structure

Each module follows this standard structure:

```
module_name/
├── Dockerfile           # Container configuration
├── pyproject.toml       # Dependencies and metadata
├── README.md            # Module documentation
├── module_name/         # Main module package
│   ├── __init__.py
│   └── main.py          # Main implementation
└── tests/               # Test files
    ├── __init__.py
    └── test_module_name.py
```

## Automatic Module Generation

ELLMa can automatically generate new modules during evolution. The system will:

1. Create a new directory with all necessary files
2. Generate tests and Docker configuration
3. Build and test the module
4. Integrate it into the system if tests pass

### Module Generation Process

1. **Analysis**: The system identifies opportunities for new capabilities
2. **Generation**: Creates a new module with all required files
3. **Testing**: Builds and tests the module in an isolated environment
4. **Integration**: If successful, adds the module to the running system
5. **Feedback**: Logs results and updates evolution metrics

## Creating a Module Manually

1. Create a new directory in `modules/`
2. Add the required files (use `example_module` as a template)
3. Implement your functionality in `module_name/main.py`
4. Add tests in `tests/test_module_name.py`
5. Update `pyproject.toml` with dependencies

## Module Requirements

- Must have a class that follows the naming convention `{ModuleName}Module`
- Must implement `get_commands()` that returns a dict of command names to methods
- Should include comprehensive tests
- Should document all public methods and classes
- Must not have side effects on import

## Testing Modules

Run tests for a specific module:

```bash
cd modules/module_name
pytest tests/ -v
```

Or use the Makefile:

```bash
cd modules/module_name
make test
```

## Building with Docker

Each module can be built and run in an isolated container:

```bash
cd modules/module_name
make docker-build
make docker-run
```

## Evolution Integration

During evolution, the system will:

1. Generate new modules based on identified needs
2. Test them in isolation
3. Integrate successful modules
4. Log all actions for analysis

## Best Practices

1. Keep modules focused on a single responsibility
2. Write comprehensive tests
3. Document all public interfaces
4. Handle errors gracefully
5. Include type hints for better IDE support
6. Follow Python naming conventions

## Example Module

See the `example_module` directory for a complete reference implementation.
