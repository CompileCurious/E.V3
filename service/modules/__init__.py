raise ImportError(
	"service.modules is removed — import from service.Modules instead:\n"
	"from service.Modules import EV3Service"
)
"""Modules service package (renamed from core)."""
from .service import EV3Service

__all__ = ['EV3Service']
