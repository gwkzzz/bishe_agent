class IntegrationError(RuntimeError):
    """Base error for infrastructure clients."""


class AlgorithmClientError(IntegrationError):
    """Raised when the algorithm service returns an error or cannot be reached."""


class QueuePublishError(IntegrationError):
    """Raised when a RabbitMQ publish operation fails."""


class ObjectStorageError(IntegrationError):
    """Raised when MinIO cannot complete an operation."""


class CacheError(IntegrationError):
    """Raised when Redis cannot complete an operation."""
