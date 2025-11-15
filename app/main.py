"""Application entrypoint for the CoffeeZone Configurator backend."""

from __future__ import annotations

import argparse
import asyncio
import re
from typing import Iterable, List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .compat import patch_typing_only

patch_typing_only()

from .admin import setup_admin
from .admin_routes import router as admin_variations_router
from .config import settings
from .db import init_db
from .middleware import TrustedDomainMiddleware


def _split_origins(origins: Iterable[str]) -> Tuple[List[str], List[str]]:
    explicit: List[str] = []
    wildcard: List[str] = []
    for origin in origins:
        cleaned = origin.rstrip("/")
        if not cleaned:
            continue
        if "*" in cleaned:
            wildcard.append(cleaned)
        else:
            explicit.append(cleaned)
    return explicit, wildcard


def _build_regex(wildcard_origins: List[str]) -> str | None:
    if not wildcard_origins:
        return None
    escaped = [re.escape(origin).replace(r"\*", ".*") for origin in wildcard_origins]
    return rf"^({'|'.join(escaped)})$"


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(title="CoffeeZone Configurator Backend", version="0.1.0")

    explicit_origins, wildcard_origins = _split_origins(settings.allowed_origins)
    origin_regex = _build_regex(wildcard_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=explicit_origins,
        allow_origin_regex=origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedDomainMiddleware,
        allowed_origins=settings.allowed_origins,
        api_prefix="/api",
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

    settings.uploads_path.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.uploads_url_prefix_clean,
        StaticFiles(directory=settings.uploads_path, html=False),
        name="uploads",
    )

    from .api.meta import router as meta_router
    from .api.bundles import router as bundles_router

    app.include_router(meta_router, prefix="/api")
    app.include_router(bundles_router, prefix="/api")
    app.include_router(admin_variations_router)

    app.state.admin = setup_admin(app)

    @app.on_event("startup")
    async def _create_tables() -> None:
        await init_db()

    return app


app = create_app()


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CoffeeZone Configurator backend utilities.")
    parser.add_argument("--init-db", action="store_true", help="Create database tables and exit.")
    return parser.parse_args()


def main() -> None:
    args = _parse_arguments()
    if args.init_db:
        asyncio.run(init_db())


if __name__ == "__main__":
    main()
