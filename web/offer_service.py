"""Compatibility alias; implementation moved to backend services."""
import sys
from backend.app.services import offers
sys.modules[__name__] = offers
