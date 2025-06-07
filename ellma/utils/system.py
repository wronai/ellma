"""
System and resource management utilities for ELLMa.
"""
import os
import sys
import resource
import psutil
from typing import Dict, Optional

def set_system_limits() -> Dict[str, int]:
    """
    Set system resource limits to prevent resource exhaustion.
    
    Returns:
        Dict containing the applied limits
    """
    limits = {}
    
    try:
        # Set OpenMP threads (for llama-cpp-python)
        os.environ['OMP_NUM_THREADS'] = str(min(4, os.cpu_count() // 2) or 1)
        
        # Set MKL threads if using Intel MKL
        os.environ['MKL_NUM_THREADS'] = os.environ['OMP_NUM_THREADS']
        
        # Set process limits
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        new_soft = min(65536, max(soft, 8192))
        resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, hard))
        
        # Set stack size if needed
        # resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        
        limits = {
            'omp_threads': int(os.environ['OMP_NUM_THREADS']),
            'mkl_threads': int(os.environ['MKL_NUM_THREADS']),
            'file_descriptors': new_soft
        }
        
    except Exception as e:
        print(f"Warning: Could not set all system limits: {e}", file=sys.stderr)
    
    return limits

def get_system_status() -> Dict[str, Any]:
    """
    Get current system resource status.
    
    Returns:
        Dict containing system resource information
    """
    try:
        process = psutil.Process()
        mem = psutil.virtual_memory()
        
        return {
            'cpu': {
                'percent': psutil.cpu_percent(),
                'count': psutil.cpu_count(),
                'load': os.getloadavg()
            },
            'memory': {
                'total': mem.total,
                'available': mem.available,
                'percent': mem.percent,
                'used': mem.used,
                'free': mem.free
            },
            'process': {
                'pid': process.pid,
                'memory_info': process.memory_info()._asdict(),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            },
            'limits': {
                'open_files': resource.getrlimit(resource.RLIMIT_NOFILE),
                'max_processes': resource.getrlimit(resource.RLIMIT_NPROC)
            },
            'environment': {
                'OMP_NUM_THREADS': os.environ.get('OMP_NUM_THREADS'),
                'MKL_NUM_THREADS': os.environ.get('MKL_NUM_THREADS'),
                'PYTHONPATH': os.environ.get('PYTHONPATH')
            }
        }
    except Exception as e:
        return {'error': f"Could not get system status: {str(e)}"}
