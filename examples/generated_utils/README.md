# Generated Utilities Examples

This directory contains examples demonstrating how to use the generated utilities in the ELLMa framework.

## Examples

### 1. Error Handling

[`error_handling_example.py`](error_handling_example.py)

Demonstrates how to use the `@enhanced_error_handler` decorator to automatically retry failed operations with exponential backoff.

**Run it with:**
```bash
python -m examples.generated_utils.error_handling_example
```

### 2. Performance Caching

[`cache_example.py`](cache_example.py)

Shows how to use the `PerformanceCache` class to cache expensive operations with time-based expiration.

**Run it with:**
```bash
python -m examples.generated_utils.cache_example
```

### 3. Parallel Processing

[`parallel_processing_example.py`](parallel_processing_example.py)

Demonstrates how to use `parallel_map` to process items in parallel using multiple worker processes.

**Run it with:**
```bash
python -m examples.generated_utils.parallel_processing_example
```

### 4. Combined Example

[`combined_example.py`](combined_example.py)

A comprehensive example that combines all three utilities to build a robust and efficient data processing pipeline.

**Run it with:**
```bash
python -m examples.generated_utils.combined_example
```

## Key Features Demonstrated

- **Error Resilience**: Automatic retries with exponential backoff
- **Performance Optimization**: Caching to avoid redundant computations
- **Concurrency**: Parallel processing for improved performance
- **Composability**: Utilities work together seamlessly

## Running Examples

All examples can be run from the project root using the `-m` flag:

```bash
# From the project root directory
python -m examples.generated_utils.example_name
```

Or by running the files directly:

```bash
cd examples/generated_utils/
python example_name.py
```

## Dependencies

All examples use only the standard library and the ELLMa framework. No additional dependencies are required.
