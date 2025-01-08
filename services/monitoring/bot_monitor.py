import logging
import time
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Deque
import threading
import psutil

logger = logging.getLogger(__name__)

@dataclass
class BotMetrics:
    """Data class to store bot monitoring metrics.

    Attributes:
        status: Current bot status ("running", "stopped", "error")
        uptime: Time elapsed since bot start in seconds
        message_count: Total number of messages processed
        error_count: Total number of errors encountered
        memory_usage: Current memory usage in MB
        cpu_usage: Current CPU usage percentage
        last_message_time: Timestamp of last processed message
        recent_errors: List of recent error messages
        response_times: List of recent message response times
    """
    status: str
    uptime: float
    message_count: int
    error_count: int
    memory_usage: float
    cpu_usage: float
    last_message_time: Optional[datetime]
    recent_errors: List[str]
    response_times: List[float]

class BotMonitor:
    """Class for monitoring bot performance and health metrics.

    Handles tracking of messages, errors, response times, and system resource usage.
    Thread-safe implementation using locks for concurrent access.
    """

    def __init__(self, max_errors: int = 100, max_response_times: int = 1000) -> None:
        """Initialize bot monitor with specified capacity for errors and response times.

        Args:
            max_errors: Maximum number of recent errors to store
            max_response_times: Maximum number of response times to store
        """
        self.start_time: float = time.time()
        self.message_count: int = 0
        self.error_count: int = 0
        self.recent_errors: Deque[str] = deque(maxlen=max_errors)
        self.response_times: Deque[float] = deque(maxlen=max_response_times)
        self.last_message_time: Optional[datetime] = None
        self.status: str = "stopped"
        self._lock: threading.Lock = threading.Lock()

    def record_message(self, response_time: float) -> None:
        """Record a processed message and its response time.

        Args:
            response_time: Time taken to process the message in seconds
        """
        try:
            with self._lock:
                self.message_count += 1
                self.last_message_time = datetime.now()
                self.response_times.append(response_time)
            logger.debug(f"Message recorded with response time: {response_time:.3f}s")
        except Exception as e:
            logger.error(f"Error recording message: {str(e)}")
            self.record_error(f"Failed to record message: {str(e)}")

    def record_error(self, error: str) -> None:
        """Record an error with timestamp.

        Args:
            error: Error message to record
        """
        try:
            with self._lock:
                self.error_count += 1
                self.recent_errors.append(f"{datetime.now().isoformat()}: {error}")
            logger.error(f"Error recorded: {error}")
        except Exception as e:
            logger.critical(f"Failed to record error: {str(e)}")

    def set_status(self, status: str) -> None:
        """Update bot status.

        Args:
            status: New status to set ("running", "stopped", "error")
        """
        try:
            with self._lock:
                self.status = status
            logger.info(f"Bot status changed to: {status}")
        except Exception as e:
            logger.error(f"Failed to update status: {str(e)}")
            self.record_error(f"Failed to update status: {str(e)}")

    def get_metrics(self) -> BotMetrics:
        """Get current bot metrics.

        Returns:
            BotMetrics object containing current monitoring data
        """
        try:
            with self._lock:
                process = psutil.Process()
                uptime = time.time() - self.start_time
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                cpu_usage = process.cpu_percent()
                recent_response_times = list(self.response_times)[-100:] if self.response_times else []

                return BotMetrics(
                    status=self.status,
                    uptime=uptime,
                    message_count=self.message_count,
                    error_count=self.error_count,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    last_message_time=self.last_message_time,
                    recent_errors=list(self.recent_errors),
                    response_times=recent_response_times
                )
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            self.record_error(f"Failed to get metrics: {str(e)}")
            return BotMetrics(
                status="error",
                uptime=0.0,
                message_count=0,
                error_count=0,
                memory_usage=0.0,
                cpu_usage=0.0,
                last_message_time=None,
                recent_errors=[],
                response_times=[]
            )

# Global instance
bot_monitor = BotMonitor()