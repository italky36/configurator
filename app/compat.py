"""Compatibility helpers for different Python / dependency versions."""

from __future__ import annotations

import typing


def patch_typing_only() -> None:
    """Relax typing.TypingOnly checks on Python 3.14+ for SQLAlchemy."""

    typing_only = getattr(typing, "TypingOnly", None)
    if typing_only is None:
        return

    # Replace TypingOnly.__init_subclass__ with a permissive stub so runtime
    # helpers (SQLAlchemy) can subclass it even if they define extra attrs.
    def _patched_init_subclass(cls, *args, **kwargs):  # type: ignore[override]
        return None

    setattr(_patched_init_subclass, "__coffeezone_patch__", True)
    typing_only.__init_subclass__ = _patched_init_subclass  # type: ignore[assignment]
