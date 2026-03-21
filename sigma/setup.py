"""Setup entry point and metadata (used by `sigma-setup` console script)."""

from __future__ import annotations

from .setup_agent import run_setup

__version__ = "3.7.0"

__all__ = ["__version__", "run_setup"]
