"""
Agentic AI Demo Application Package
"""

__version__ = "1.0.0"
__author__ = "Agentic AI Team"

# Package initialization
from app.config import settings

# Expose key components
__all__ = [
    "settings",
    "__version__",
    "__author__"
]