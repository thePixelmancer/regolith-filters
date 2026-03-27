from pathlib import Path
from PIL import Image

_cache: dict[Path, Image.Image] = {}


def get(path: Path) -> Image.Image:
    """
    Return a cached RGBA image for the given path, loading it on first access.

    The cache persists for the lifetime of the process. Since images are only
    ever read (never modified in-place), sharing the same object across threads
    is safe as long as callers do not mutate the returned image.
    """
    if path not in _cache:
        _cache[path] = Image.open(path).convert("RGBA")
    return _cache[path]


def clear() -> None:
    """Evict all cached images."""
    _cache.clear()
