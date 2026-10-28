"""Compatibility alias; implementation moved to backend services."""
import sys
from backend.app.services import snapshot_merge
sys.modules[__name__] = snapshot_merge
