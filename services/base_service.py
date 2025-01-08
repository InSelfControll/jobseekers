from abc import ABC, abstractmethod

class BaseService(ABC):
    @abstractmethod
    async def initialize(self):
        """Initialize the service"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup the service"""
        pass

    @abstractmethod
    async def health_check(self):
        """Check service health"""
        pass
