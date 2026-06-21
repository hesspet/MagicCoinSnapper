from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "app":
        from mcs_trainer.cli.main import app

        return app
    raise AttributeError(name)

__all__ = ["app"]
