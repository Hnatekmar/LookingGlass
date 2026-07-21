from .config import Settings
from .v1.__main__ import app

# Import providers so they are registered in the registry at import time
import app.providers  # noqa: F401

__all__ = ["Settings", "app"]
