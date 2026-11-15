# -*- coding: utf-8 -*-
"""数据模型与查询。"""
from __future__ import annotations

import json
import os
import random as _random
import unicodedata
from dataclasses import dataclass, field
from importlib import resources
from typing import Dict, List, Optional, Tuple

__all__ = ["Meme", "Category", "Source", "Archive", "load", "display_width", "pad"]

RESOURCE = "memearchive.data"


def display_width(text: str) -> int:
    """按终端显示宽度计算：全角字符算 2 列。"""
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad(text: str, width: int, align: str = "left") -> str:
    gap = max(0, width - display_width(text))
    if align == "right":
        return " " * gap + text
    return text + " " * gap


def _normalize(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _resource_json(name: str) -> Optional[dict]:
    try:
        raw = resources.files(RESOURCE).joinpath(name).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        return None
    return json.loads(raw)


def _file_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class Category:
    id: str
    name: str


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    type: str = ""
    year: Optional[int] = None

    @property
    def label(self) -> str:
        if self.year:
            return f"{self.name}（{self.type}{self.year}）"
        return f"{self.name}（{self.type}）" if self.type else self.name


@dataclass(frozen=True)
class Meme:
    id: str
    cat: str
    term: str
    meaning: str
    origin: str
    example: str
    era: str
    heat: int
    source: str = ""

    @property
    def stars(self) -> str:
        heat = max(0, min(5, int(self.heat)))
        return "★" * heat + "☆" * (5 - heat)

    def as_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "cat": self.cat,
            "term": self.term,
            "meaning": self.meaning,
            "origin": self.origin,
            "example": self.example,
            "era": self.era,
            "heat": self.heat,
            "source": self.source,
        }


@dataclass
class Archive:
    categories: List[Category]
    items: List[Meme]
    updated: str = ""
    schema: int = 1
    sources: List[Source] = field(default_factory=list)
    pinyin: Dict[str, Dict[str, str]] = field(default_factory=dict, repr=False)
    _by_cat: Dict[str, Category] = field(default_factory=dict, repr=False)
    _by_source: Dict[str, Source] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._by_cat = {c.id: c for c in self.categories}
        self._by_source = {s.id: s for s in self.sources}

    # ---------- 载入 ----------

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Archive":
        if path:
            doc = _file_json(path)
            if doc is None:
                raise FileNotFoundError(path)
            base = os.path.dirname(os.path.abspath(path))
            sources_doc = _file_json(os.path.join(base, "sources.json"))
            pinyin_doc = _file_json(os.path.join(base, "pinyin.json"))
        else:
            doc = _resource_json("memes.json")
            if doc is None:
                raise FileNotFoundError("内置数据缺失：memes.json")
            sources_doc = _resource_json("sources.json")
            pinyin_doc = _resource_json("pinyin.json")
        return cls.from_doc(doc, sources_doc, pinyin_doc)

    @classmethod
    def from_doc(
        cls,
        doc: dict,
        sources_doc: Optional[dict] = None,
        pinyin_doc: Optional[dict] = None,
    ) -> "Archive":
        if doc.get("schema", 1) != 1:
            raise ValueError(f"不支持的数据版本：{doc.get('schema')}")
        cats = [Category(id=c["id"], name=c["name"]) for c in doc["categories"]]
        items = [
            Meme(
                id=m["id"],
                cat=m["cat"],
                term=m["term"],
                meaning=m["meaning"],
                origin=m.get("origin", ""),
                example=m.get("example", ""),
                era=m.get("era", ""),
                heat=int(m.get("heat", 3)),
                source=m.get("source", ""),
            )
            for m in doc["items"]
        ]
        sources = []
        if sources_doc:
            sources = [
                Source(id=s["id"], name=s["name"], type=s.get("type", ""), year=s.get("year"))
                for s in sources_doc["items"]
            ]
        pinyin = (pinyin_doc or {}).get("items", {})
        return cls(
            categories=cats,
            items=items,
            updated=doc.get("updated", ""),
            schema=doc.get("schema", 1),
            sources=sources,
            pinyin=pinyin,
        )

    # ---------- 查询 ----------

    @property
    def eras(self) -> List[str]:
        return sorted({m.era for m in self.items if m.era})

    def cat_name(self, cat_id: str) -> str:
        c = self._by_cat.get(cat_id)
        return c.name if c else cat_id

    def source_of(self, m: Meme) -> Optional[Source]:
        return self._by_source.get(m.source)

    def source_name(self, m: Meme) -> str:
        s = self.source_of(m)
        return s.name if s else ""

    def by_cat(self) -> "Dict[str, List[Meme]]":
        out: Dict[str, List[Meme]] = {c.id: [] for c in self.categories}
        for m in self.items:
            out.setdefault(m.cat, []).append(m)
        return out

    def by_source(self) -> "Dict[str, List[Meme]]":
        out: Dict[str, List[Meme]] = {s.id: [] for s in self.sources}
        for m in self.items:
            if m.source:
                out.setdefault(m.source, []).append(m)
        return out

    def source_counts(self) -> List[Tuple[Source, int]]:
        counts = {s.id: 0 for s in self.sources}
        for m in self.items:
            if m.source in counts:
                counts[m.source] += 1
        return sorted(
            [(self._by_source[sid], n) for sid, n in counts.items()],
            key=lambda pair: (-pair[1], pair[0].name),
        )

    def get(self, key: str) -> Optional[Meme]:
        """先按 id、名称精确匹配，最后尝试拼音。"""
        k = key.strip()
        for m in self.items:
            if m.id.lower() == k.lower():
                return m
        for m in self.items:
            if m.term.lower() == k.lower():
                return m
        py = self.match_pinyin(k)
        return py[0] if len(py) == 1 else None

    def find(self, key: str) -> List[Meme]:
        k = key.strip().lower()
        exact = self.get(key)
        if exact:
            return [exact]
        hits = [m for m in self.items if k in m.term.lower()]
        if hits:
            return hits
        return self.match_pinyin(key)

    def match_pinyin(self, query: str) -> List[Meme]:
        """全拼前缀、或首字母全等。少于两个字符不匹配，避免误伤。"""
        q = _normalize(query)
        if len(q) < 2 or not self.pinyin:
            return []
        out = []
        for m in self.items:
            py = self.pinyin.get(m.id)
            if not py:
                continue
            if q == py.get("initials") or py.get("full", "").startswith(q):
                out.append(m)
        return out

    def search(self, query: str) -> List[Meme]:
        q = query.strip().lower()
        if not q:
            return []
        scored = []
        for m in self.items:
            haystack = " ".join([m.term, m.meaning, m.origin, m.example, m.era, m.id]).lower()
            if q not in haystack:
                continue
            score = 0 if q in m.term.lower() else 1
            scored.append((score, m))
        scored.sort(key=lambda pair: (pair[0], pair[1].id))
        hits = [m for _, m in scored]
        seen = {m.id for m in hits}
        for m in self.match_pinyin(query):
            if m.id not in seen:
                hits.append(m)
                seen.add(m.id)
        return hits

    def _match(
        self,
        m: Meme,
        cats: Optional[set],
        era: Optional[str],
        min_heat: int,
        source: Optional[str],
    ) -> bool:
        if cats and m.cat.upper() not in cats and self.cat_name(m.cat) not in cats:
            return False
        if era and era not in m.era:
            return False
        if m.heat < min_heat:
            return False
        if source:
            src = self.source_of(m)
            if not src or source not in (src.id, src.name):
                return False
        return True

    def select(
        self,
        cat: Optional[str] = None,
        era: Optional[str] = None,
        min_heat: int = 0,
        source: Optional[str] = None,
    ) -> List[Meme]:
        cats = None
        if cat:
            cats = {c.strip().upper() for c in cat.replace("，", ",").split(",") if c.strip()}
        return [m for m in self.items if self._match(m, cats, era, min_heat, source)]

    def query(
        self,
        q: Optional[str] = None,
        cat: Optional[str] = None,
        era: Optional[str] = None,
        min_heat: int = 0,
        source: Optional[str] = None,
    ) -> List[Meme]:
        """搜索 + 过滤的组合，供 CLI 与 HTTP 接口共用。"""
        cats = None
        if cat:
            cats = {c.strip().upper() for c in cat.replace("，", ",").split(",") if c.strip()}
        pool = self.search(q) if q else self.items
        return [m for m in pool if self._match(m, cats, era, min_heat, source)]

    def random(self, n: int = 1, **filters) -> List[Meme]:
        pool = self.select(**filters) if filters else list(self.items)
        if not pool:
            return []
        n = max(1, min(n, len(pool)))
        return _random.sample(pool, n)

    # ---------- 统计 ----------

    def stats(self) -> Dict[str, object]:
        by_cat = {c.id: 0 for c in self.categories}
        by_era: Dict[str, int] = {}
        by_heat: Dict[int, int] = {i: 0 for i in range(1, 6)}
        by_source: Dict[str, int] = {}
        for m in self.items:
            by_cat[m.cat] = by_cat.get(m.cat, 0) + 1
            by_era[m.era] = by_era.get(m.era, 0) + 1
            by_heat[m.heat] = by_heat.get(m.heat, 0) + 1
            by_source[m.source] = by_source.get(m.source, 0) + 1
        return {
            "total": len(self.items),
            "categories": by_cat,
            "eras": dict(sorted(by_era.items())),
            "heat": by_heat,
            "sources": by_source,
            "source_count": len(by_source),
        }


def load(path: Optional[str] = None) -> Archive:
    return Archive.load(path)
