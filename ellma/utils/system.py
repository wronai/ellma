"""
System and resource management utilities for ELLMa.
"""
import os
import sys
import resource
import psutil
from typing import Any, Dict, Optional
from ellma.utils.logger import get_logger

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
    status = {
        'cpu': {},
        'memory': {},
        'disk': {},
        'process': {}
    }
    
    try:
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        status['cpu'].update({
            'percent': cpu_percent,
            'cores': cpu_count,
            'current_freq': cpu_freq.current if cpu_freq else None,
            'max_freq': cpu_freq.max if cpu_freq else None
        })
        
        # Memory information
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        status['memory'].update({
            'total': mem.total,
            'available': mem.available,
            'percent': mem.percent,
            'used': mem.used,
            'free': mem.free,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_free': swap.free,
            'swap_percent': swap.percent
        })
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        status['disk'].update({
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent,
            'read_count': disk_io.read_count if disk_io else 0,
            'write_count': disk_io.write_count if disk_io else 0,
            'read_bytes': disk_io.read_bytes if disk_io else 0,
            'write_bytes': disk_io.write_bytes if disk_io else 0
        })
        
        # Process information
        process = psutil.Process()
        with process.oneshot():
            status['process'].update({
                'pid': process.pid,
                'name': process.name(),
                'status': process.status(),
                'create_time': process.create_time(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'connections': len(process.connections())
            })
            
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error getting system status: {e}", exc_info=True)
        status['error'] = str(e)
    
    return status
