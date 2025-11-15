"""Custom middleware for the FastAPI application."""

from __future__ import annotations

import re
from typing import Iterable, List, Pattern
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def compile_origin_patterns(origins: Iterable[str] | None) -> List[Pattern[str]]:
    """Compile allowed origin patterns with wildcard support."""

    if not origins:
        return []

    patterns: List[Pattern[str]] = []
    for origin in origins:
        if not origin:
            continue
        normalized = origin.rstrip("/")
        if not normalized:
            continue
        escaped = re.escape(normalized).replace(r"\*", ".*")
        regex = re.compile(rf"^{escaped}$", re.IGNORECASE)
        patterns.append(regex)
    return patterns


class TrustedDomainMiddleware(BaseHTTPMiddleware):
    """Middleware that restricts API usage by Origin/Referer."""

    def __init__(
        self,
        app,
        allowed_origins: Iterable[str] | None = None,
        api_prefix: str = "/api",
    ):
        super().__init__(app)
        self.api_prefix = api_prefix
        self.allowed_patterns = compile_origin_patterns(allowed_origins)

    def _normalize_origin(self, header_value: str | None) -> str | None:
        if not header_value:
            return None

        parsed = urlparse(header_value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        return header_value.rstrip("/")

    def _is_same_host(self, origin: str, request: Request) -> bool:
        parsed = urlparse(origin)
        origin_host = parsed.hostname or parsed.netloc
        if not origin_host:
            return False

        request_host = request.url.hostname or request.url.netloc
        if not request_host:
            return False

        def canonical(host: str) -> str:
            host = host.lower()
            if host in {"localhost", "127.0.0.1"}:
                return "local"
            return host

        return canonical(origin_host) == canonical(request_host)

    def _is_allowed(self, origin: str) -> bool:
        if not self.allowed_patterns:
            return True
        return any(pattern.match(origin) for pattern in self.allowed_patterns)

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(self.api_prefix):
            return await call_next(request)

        origin = self._normalize_origin(request.headers.get("origin"))
        referer = self._normalize_origin(request.headers.get("referer"))
        candidate = origin or referer

        if candidate is None:
            return await call_next(request)

        if self._is_same_host(candidate, request):
            return await call_next(request)

        if not self._is_allowed(candidate):
            return Response(status_code=403, content="Forbidden")

        return await call_next(request)
