import logging
import psutil
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    A utility class for collecting system metrics like CPU and memory usage.
    
    This class provides methods to safely collect various system metrics using psutil,
    with proper error handling and logging.
    """
    
    @staticmethod
    def get_memory_usage(pid: Optional[int] = None) -> float:
        """
        Get memory usage for a specific process or current process.
        
        Args:
            pid: Process ID to get memory for. If None, uses current process.
            
        Returns:
            Memory usage in megabytes.
            
        Raises:
            RuntimeError: If process information cannot be retrieved.
        """
        try:
            process = psutil.Process(pid) if pid else psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except psutil.NoSuchProcess:
            logger.error(f"Process with PID {pid} not found")
            raise RuntimeError(f"Process with PID {pid} not found")
        except psutil.AccessDenied:
            logger.error("Access denied when trying to get memory usage")
            raise RuntimeError("Access denied when trying to get memory usage")
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            raise RuntimeError(f"Error getting memory usage: {str(e)}")

    @staticmethod
    def get_cpu_usage(pid: Optional[int] = None) -> float:
        """
        Get CPU usage for a specific process or current process.
        
        Args:
            pid: Process ID to get CPU usage for. If None, uses current process.
            
        Returns:
            CPU usage percentage.
            
        Raises:
            RuntimeError: If process information cannot be retrieved.
        """
        try:
            process = psutil.Process(pid) if pid else psutil.Process()
            return process.cpu_percent()
        except psutil.NoSuchProcess:
            logger.error(f"Process with PID {pid} not found")
            raise RuntimeError(f"Process with PID {pid} not found")
        except psutil.AccessDenied:
            logger.error("Access denied when trying to get CPU usage")
            raise RuntimeError("Access denied when trying to get CPU usage")
        except Exception as e:
            logger.error(f"Error getting CPU usage: {str(e)}")
            raise RuntimeError(f"Error getting CPU usage: {str(e)}")

    @staticmethod
    def get_system_metrics() -> Dict[str, float]:
        """
        Get overall system metrics including CPU and memory usage.
        
        Returns:
            Dictionary containing system metrics:
            - system_cpu_percent: Overall CPU usage percentage
            - system_memory_percent: Overall memory usage percentage
            
        Raises:
            RuntimeError: If system metrics cannot be retrieved.
        """
        try:
            return {
                'system_cpu_percent': psutil.cpu_percent(interval=0.1),
                'system_memory_percent': psutil.virtual_memory().percent
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            raise RuntimeError(f"Error getting system metrics: {str(e)}")

    @staticmethod
    def get_process_metrics(pid: Optional[int] = None) -> Dict[str, float]:
        """
        Get comprehensive metrics for a specific process.
        
        Args:
            pid: Process ID to get metrics for. If None, uses current process.
            
        Returns:
            Dictionary containing process metrics:
            - memory_mb: Memory usage in megabytes
            - cpu_percent: CPU usage percentage
            - threads: Number of threads
            - fds: Number of file descriptors
            
        Raises:
            RuntimeError: If process metrics cannot be retrieved.
        """
        try:
            process = psutil.Process(pid) if pid else psutil.Process()
            return {
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'fds': process.num_fds() if hasattr(process, 'num_fds') else 0
            }
        except Exception as e:
            logger.error(f"Error getting process metrics: {str(e)}")
            raise RuntimeError(f"Error getting process metrics: {str(e)}")

    @staticmethod
    def get_timestamp() -> datetime:
        """
        Get current timestamp.
        
        Returns:
            Current datetime object.
        """
        return datetime.now()