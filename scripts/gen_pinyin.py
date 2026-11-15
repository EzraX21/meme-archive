#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成拼音索引 memearchive/data/pinyin.json。

只跑在开发期：需要 pypinyin（见 requirements-dev.txt）。
运行时搜索不依赖 pypinyin，直接读生成的 JSON。

用法：
    python3 scripts/gen_pinyin.py
"""
import json
import os
import re
import sys

try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # pragma: no cover
    sys.exit("需要 pypinyin：pip install pypinyin")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMES = os.path.join(ROOT, "memearchive", "data", "memes.json")
OUT = os.path.join(ROOT, "memearchive", "data", "pinyin.json")

KEEP = re.compile(r"[^a-z0-9]")


def clean(text: str) -> str:
    return KEEP.sub("", text.lower())


def build(term: str):
    full = clean("".join(lazy_pinyin(term, style=Style.NORMAL, errors=lambda s: list(s))))
    initials = clean("".join(lazy_pinyin(term, style=Style.FIRST_LETTER, errors=lambda s: list(s))))
    return {"full": full, "initials": initials}


def main() -> None:
    with open(MEMES, encoding="utf-8") as f:
        doc = json.load(f)

    items = {m["id"]: build(m["term"]) for m in doc["items"]}
    payload = {"schema": 1, "items": items}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"已生成 {OUT}：{len(items)} 条")
    for sample in ("A01", "C01", "H01"):
        if sample in items:
            print(f"  {sample}: {items[sample]}")


if __name__ == "__main__":
    main()
