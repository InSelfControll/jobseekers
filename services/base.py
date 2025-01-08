import logging
import asyncio
import threading
from typing import Dict, Any, Optional
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceStatus:
    """Consolidated service status tracking"""
    
    def __init__(self):
        self.services_ready: Dict[str, bool] = {}
        self.cleanup_status: Dict[str, bool] = {}
        self.error_details: Dict[str, Optional[str]] = {}
        self.initialization_time: Dict[str, float] = {}
        
    def register_service(self, service_name: str):
        """Register a new service for status tracking"""
        self.services_ready[service_name] = False
        self.cleanup_status[service_name] = False
        self.error_details[service_name] = None
        self.initialization_time[service_name] = 0.0
        
    def set_service_ready(self, service_name: str, status: bool, error: Optional[str] = None):
        """Update service ready status"""
        self.services_ready[service_name] = status
        if error:
            self.error_details[service_name] = error
            
    def set_cleanup_status(self, service_name: str, status: bool, error: Optional[str] = None):
        """Update service cleanup status"""
        self.cleanup_status[service_name] = status
        if error:
            self.error_details[service_name] = error
            
    def all_services_ready(self) -> bool:
        """Check if all services are ready"""
        return all(self.services_ready.values())
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive status for a specific service"""
        return {
            'ready': self.services_ready.get(service_name, False),
            'cleanup_complete': self.cleanup_status.get(service_name, False),
            'error': self.error_details.get(service_name),
            'initialization_time': self.initialization_time.get(service_name, 0.0)
        }

class BaseServiceManager:
    """Base class for service management with common initialization patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status = ServiceStatus()
        self._running = False
        self.startup_complete = threading.Event()
        self.error_queue = Queue()
        self.required_services: Dict[str, bool] = {}
        
    def register_required_service(self, service_name: str, required: bool = True):
        """Register a service and whether it's required for operation"""
        self.required_services[service_name] = required
        self.status.register_service(service_name)
        
    async def initialize_service(self, service_name: str, init_func, *args, **kwargs) -> bool:
        """Initialize a service with proper error handling"""
        try:
            self.logger.info(f"Initializing service: {service_name}")
            import time
            start_time = time.time()
            
            result = await init_func(*args, **kwargs) if asyncio.iscoroutinefunction(init_func) else init_func(*args, **kwargs)
            
            self.status.initialization_time[service_name] = time.time() - start_time
            self.status.set_service_ready(service_name, bool(result))
            
            if not result and self.required_services.get(service_name, False):
                error_msg = f"Required service {service_name} failed to initialize"
                self.logger.error(error_msg)
                self.status.set_service_ready(service_name, False, error_msg)
                return False
                
            return bool(result)
            
        except Exception as e:
            error_msg = f"Error initializing {service_name}: {str(e)}"
            self.logger.error(error_msg)
            self.status.set_service_ready(service_name, False, error_msg)
            if self.required_services.get(service_name, False):
                raise
            return False
            
    async def cleanup_service(self, service_name: str, cleanup_func, *args, **kwargs) -> bool:
        """Clean up a service with proper error handling"""
        try:
            self.logger.info(f"Cleaning up service: {service_name}")
            
            result = await cleanup_func(*args, **kwargs) if asyncio.iscoroutinefunction(cleanup_func) else cleanup_func(*args, **kwargs)
            
            self.status.set_cleanup_status(service_name, bool(result))
            self.status.set_service_ready(service_name, False)
            
            return bool(result)
            
        except Exception as e:
            error_msg = f"Error cleaning up {service_name}: {str(e)}"
            self.logger.error(error_msg)
            self.status.set_cleanup_status(service_name, False, error_msg)
            return False
            
    async def cleanup_all(self, cleanup_only: bool = False):
        """Clean up all registered services"""
        self.logger.info(f"Starting {'cleanup' if cleanup_only else 'shutdown'} process...")
        self._running = False
        
        cleanup_results = []
        for service_name in self.status.services_ready.keys():
            if hasattr(self, f"cleanup_{service_name}"):
                cleanup_func = getattr(self, f"cleanup_{service_name}")
                result = await self.cleanup_service(service_name, cleanup_func, cleanup_only=cleanup_only)
                cleanup_results.append(result)
                
        cleanup_success = all(cleanup_results)
        if cleanup_success:
            self.logger.info(f"{'Cleanup' if cleanup_only else 'Shutdown'} completed successfully")
        else:
            failed_services = [
                service for service, status in self.status.cleanup_status.items()
                if not status
            ]
            self.logger.warning(
                f"{'Cleanup' if cleanup_only else 'Shutdown'} partially failed for services: "
                f"{', '.join(failed_services)}"
            )
            
    def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report for all services"""
        return {
            'services': {
                name: self.status.get_service_status(name)
                for name in self.status.services_ready.keys()
            },
            'all_services_ready': self.status.all_services_ready(),
            'running': self._running
        }