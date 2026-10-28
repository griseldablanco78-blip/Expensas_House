"""Compatibility alias; persistence lives in backend.app.infrastructure."""
import sys
from backend.app.infrastructure import json_store
sys.modules[__name__] = json_store
