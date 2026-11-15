# -*- coding: utf-8 -*-
"""fortune 语录：读取、随机抽取。"""
from __future__ import annotations

import random
from importlib import resources
from typing import List

RESOURCE = "memearchive.data"


def load(path: str | None = None) -> List[str]:
    if path:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = resources.files(RESOURCE).joinpath("fortunes.txt").read_text(encoding="utf-8")

    entries = []
    for block in raw.split("\n%\n"):
        text = block.strip()
        if text:
            entries.append(text)
    return entries


def draw(n: int = 1, path: str | None = None) -> List[str]:
    pool = load(path)
    if not pool:
        return []
    n = max(1, min(n, len(pool)))
    return random.sample(pool, n)
