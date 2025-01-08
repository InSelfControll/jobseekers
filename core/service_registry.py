import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from threading import Lock

from services.logging_service import logging_service

logger = logging_service.get_structured_logger(__name__)

class ServiceStatus:
    def __init__(self):
        self.services_ready: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def register_service(self, service_name: str) -> None:
        with self._lock:
            if service_name not in self.services_ready:
                self.services_ready[service_name] = {
                    'ready': False,
                    'error': None,
                    'initialization_time': None
                }

    def set_service_ready(self, service_name: str, ready: bool, error: Optional[str] = None) -> None:
        with self._lock:
            if service_name in self.services_ready:
                self.services_ready[service_name].update({
                    'ready': ready,
                    'error': error,
                    'initialization_time': datetime.now() if ready else None
                })

    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        with self._lock:
            return self.services_ready.get(service_name, {
                'ready': False,
                'error': 'Service not registered',
                'initialization_time': None
            })

    def is_service_ready(self, service_name: str) -> bool:
        with self._lock:
            service_status = self.services_ready.get(service_name)
            return bool(service_status and service_status['ready'])

class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initializers: Dict[str, Callable] = {}
        self._cleanup_handlers: Dict[str, Callable] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._required_services: Dict[str, bool] = {}
        self.status = ServiceStatus()
        self._lock = Lock()

    def mark_service_ready(self, service_name: str) -> None:
        """Mark a service as ready."""
        with self._lock:
            if service_name in self._services:
                self.status.set_service_ready(service_name, True)
                logger.info(f"Service '{service_name}' marked as ready")

    def register_service(self, service_name: str, required: bool = False) -> None:
        """Register a service with the registry."""
        with self._lock:
            if service_name not in self._services:
                self._services[service_name] = None
                self._required_services[service_name] = required
                self.status.register_service(service_name)
                logger.info(f"Service '{service_name}' registered")

    def register_initializer(self, service_name: str, initializer: Callable) -> None:
        """Register an initialization function for a service."""
        with self._lock:
            self._initializers[service_name] = initializer
            logger.debug(f"Initializer registered for service '{service_name}'")

    def register_cleanup_handler(self, service_name: str, cleanup_handler: Callable) -> None:
        """Register a cleanup handler for a service."""
        with self._lock:
            self._cleanup_handlers[service_name] = cleanup_handler
            logger.debug(f"Cleanup handler registered for service '{service_name}'")

    def register_dependencies(self, service_name: str, dependencies: List[str]) -> None:
        """Register dependencies for a service."""
        with self._lock:
            self._dependencies[service_name] = dependencies
            logger.debug(f"Dependencies registered for service '{service_name}': {dependencies}")

    async def get_service(self, service_name: str) -> Any:
        """Get a service instance, initializing it if necessary."""
        with self._lock:
            if service_name not in self._services:
                raise KeyError(f"Service '{service_name}' not registered")

            if self._services[service_name] is None:
                await self._initialize_service(service_name)

            return self._services[service_name]

    async def _initialize_service(self, service_name: str) -> bool:
        """Initialize a service and its dependencies."""
        try:
            # Check if dependencies are satisfied
            if service_name in self._dependencies:
                for dep in self._dependencies[service_name]:
                    if not self.status.is_service_ready(dep):
                        await self._initialize_service(dep)

            # Initialize the service
            if service_name in self._initializers:
                self._services[service_name] = await self._initializers[service_name]()
                self.status.set_service_ready(service_name, True)
                logger.info(f"Service '{service_name}' initialized successfully")
                return True
            else:
                logger.warning(f"No initializer found for service '{service_name}'")
                return False

        except Exception as e:
            error_msg = f"Failed to initialize service '{service_name}': {str(e)}"
            logger.error(error_msg)
            self.status.set_service_ready(service_name, False, error_msg)
            return False

    async def cleanup_service(self, service_name: str) -> None:
        """Clean up a service."""
        try:
            if service_name in self._cleanup_handlers and self._services[service_name] is not None:
                await self._cleanup_handlers[service_name]()
                self._services[service_name] = None
                self.status.set_service_ready(service_name, False)
                logger.info(f"Service '{service_name}' cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up service '{service_name}': {str(e)}")

    async def cleanup_all_services(self) -> None:
        """Clean up all registered services."""
        for service_name in reversed(list(self._services.keys())):
            await self.cleanup_service(service_name)

    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services."""
        health_status = {
            'status': 'healthy',
            'services': {}
        }

        for service_name in self._services:
            service_status = self.status.get_service_status(service_name)
            health_status['services'][service_name] = {
                'status': 'healthy' if service_status['ready'] else 'unhealthy',
                'error': service_status['error'],
                'last_init_time': service_status['initialization_time'],
                'required': self._required_services.get(service_name, False)
            }

            if not service_status['ready'] and self._required_services.get(service_name, False):
                health_status['status'] = 'unhealthy'

        return health_status

# Create a global instance of the service registry
service_registry = ServiceRegistry()
