"""PromptCraft: refine rough prompts into standard, robust prompts.

The refiner library lands in Phase 2 of ADR-001. This package currently
exposes only its version.
"""

from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("promptcraft")
except PackageNotFoundError:  # pragma: no cover - only hit when running from an uninstalled tree
    __version__ = "0.0.0"

__all__ = ["__version__"]
