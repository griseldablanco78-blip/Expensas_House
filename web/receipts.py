"""Compatibility alias; implementation moved to backend services."""
import sys
from backend.app.services import receipt_scanning
sys.modules[__name__] = receipt_scanning
