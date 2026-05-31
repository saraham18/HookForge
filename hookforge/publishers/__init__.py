"""Publisher backends. Each returns a dict with at least an 'id' and 'url'."""
from .x import publish_to_x
from .instagram import publish_to_instagram

__all__ = ["publish_to_x", "publish_to_instagram"]
