class IntegrationError(RuntimeError):
    """Base error for algorithm infrastructure clients."""


class VectorStoreError(IntegrationError):
    """Raised when Milvus cannot complete an operation."""


class ObjectStorageError(IntegrationError):
    """Raised when MinIO cannot complete an operation."""


class CacheError(IntegrationError):
    """Raised when Redis cannot complete an operation."""


class ModelGatewayError(IntegrationError):
    """Raised when a model gateway call fails."""
