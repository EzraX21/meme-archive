# -*- coding: utf-8 -*-
"""meme-archive：中文互联网梗库。"""

__version__ = "1.2.0"

from .core import Archive, Category, Meme, load  # noqa: E402

__all__ = ["Archive", "Category", "Meme", "load", "__version__"]
