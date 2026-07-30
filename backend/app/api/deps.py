"""Reusable FastAPI dependencies for authorization and Redis rate limiting."""
import logging
from collections.abc import Callable
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import verify_supabase_token
from app.db.session import get_db
from app.infrastructure.metrics import AUTH_FAILURES, RATE_LIMIT_REJECTIONS
from app.models import User
from app.services.auth import provision_or_get_user

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)
_INVALID_TOKEN = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})


def _resolve_user(credentials: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    """Verify a Supabase bearer token, then load (JIT-provisioning if needed) its local user row."""
    if not credentials:
        return None
    try:
        claims = verify_supabase_token(credentials.credentials)
    except jwt.PyJWTError:
        AUTH_FAILURES.inc()
        return None
    user = provision_or_get_user(db, claims)
    if not user:
        AUTH_FAILURES.inc()
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    """Require a valid, non-revoked bearer JWT and load its user."""
    if not credentials: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    user = _resolve_user(credentials, db)
    if not user: raise _INVALID_TOKEN
    return user


def get_current_user_optional(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    """Resolve the current user when a valid, non-revoked bearer token is present; anonymous otherwise, never raising."""
    return _resolve_user(credentials, db)


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Gate administrative endpoints with a server-side role, never a client claim alone."""
    if not user.is_admin: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


def rate_limit(limit: int, window_seconds: int) -> Callable:
    """Create a Redis fixed-window rate limiter dependency, failing closed in production."""
    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{request.url.path}:{client_ip}"
        try:
            client = Redis.from_url(get_settings().redis_url, decode_responses=True)
            count = client.incr(key)
            if count == 1: client.expire(key, window_seconds)
            if count > limit:
                logger.warning("rate_limit_exceeded path=%s ip=%s count=%s limit=%s", request.url.path, client_ip, count, limit)
                RATE_LIMIT_REJECTIONS.labels(path=_route_template(request)).inc()
                raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": str(window_seconds)})
        except HTTPException: raise
        except Exception:
            logger.exception("Rate limiter unavailable")
            if get_settings().app_env == "production": raise HTTPException(status_code=503, detail="Request protection temporarily unavailable")
    return dependency


def _route_template(request: Request) -> str:
    """The route's path template (e.g. /products/{id}), not the resolved URL - keeps metric label cardinality bounded."""
    route = request.scope.get("route")
    return route.path if route else "unmatched"
