"""Application error types allow services to stay independent from FastAPI."""
class DomainError(Exception):
    """Base expected business failure."""


class NotFoundError(DomainError):
    """Requested resource does not exist or is not visible to this caller."""


class ConflictError(DomainError):
    """Request conflicts with an existing invariant, such as a duplicate email."""


class AuthenticationError(DomainError):
    """Credentials are invalid or an authenticated principal is required."""


class ServiceUnavailableError(DomainError):
    """A required upstream dependency (LLM, embeddings) is unavailable, misconfigured, or declined the request."""
