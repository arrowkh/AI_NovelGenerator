# ui/__init__.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

__all__ = ["NovelGeneratorGUI"]


def __getattr__(name: str) -> Any:
    if name == "NovelGeneratorGUI":
        from .main_window import NovelGeneratorGUI

        return NovelGeneratorGUI
    raise AttributeError(f"module 'ui' has no attribute {name!r}")
