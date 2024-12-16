import logging
import time
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional
import threading
import psutil

@dataclass
class BotMetrics:
    status: str  # "running", "stopped", "error"
    uptime: float
    message_count: int
    error_count: int
    memory_usage: float
    cpu_usage: float
    last_message_time: Optional[datetime]
    recent_errors: List[str]
    response_times: List[float]

class BotMonitor:
    def __init__(self, max_errors=100, max_response_times=1000):
        self.start_time = time.time()
        self.message_count = 0
        self.error_count = 0
        self.recent_errors = deque(maxlen=max_errors)
        self.response_times = deque(maxlen=max_response_times)
        self.last_message_time = None
        self.status = "stopped"
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def record_message(self, response_time: float):
        with self._lock:
            self.message_count += 1
            self.last_message_time = datetime.now()
            self.response_times.append(response_time)

    def record_error(self, error: str):
        with self._lock:
            self.error_count += 1
            self.recent_errors.append(f"{datetime.now().isoformat()}: {error}")

    def set_status(self, status: str):
        with self._lock:
            self.status = status
            self.logger.info(f"Bot status changed to: {status}")

    def get_metrics(self) -> BotMetrics:
        with self._lock:
            process = psutil.Process()
            
            # Calculate metrics
            uptime = time.time() - self.start_time
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent()

            # Calculate average response time
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

# Global instance
bot_monitor = BotMonitor()
