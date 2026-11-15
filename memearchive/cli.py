# -*- coding: utf-8 -*-
"""命令行入口。"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__, export as export_mod, fortune as fortune_mod
from .core import Archive, Meme, display_width, pad

# ---------- 终端样式 ----------

_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None and os.environ.get("TERM") != "dumb"


def _wrap(code: str):
    def apply(text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if _COLOR else text

    return apply


bold = _wrap("1")
dim = _wrap("2")
cyan = _wrap("36")
yellow = _wrap("33")
green = _wrap("32")


# ---------- 输出 ----------

def print_meme(m: Meme, archive: Archive, index: bool = True) -> None:
    head = f"{bold(m.term)}  {yellow(m.stars)}  {dim(m.era)}"
    if index:
        head = f"{dim(m.id)}  {head}"
    print(head)
    print(f"  {dim('释义')}  {m.meaning}")
    if m.origin:
        print(f"  {dim('出处')}  {m.origin}")
    src = archive.source_of(m)
    if src and src.id != "web":
        print(f"  {dim('出自')}  {src.name}（{src.type}，{src.year}）")
    if m.example:
        print(f"  {dim('例句')}  {m.example}")
    print()


def print_brief(m: Meme, term_width: int = 18) -> None:
    print(f"{dim(m.id)}  {pad(m.term, term_width)}{dim(pad(m.era, 12))}{yellow(m.stars)}")



def _bar(n: int, max_n: int, width: int = 40) -> str:
    if n <= 0 or max_n <= 0:
        return ""
    return "▇" * max(1, round(n / max_n * width))


def cmd_random(archive: Archive, args) -> int:
    picked = archive.random(args.n, cat=args.cat, era=args.era, min_heat=args.min_heat, source=args.source)
    if not picked:
        print("没有符合条件的梗。", file=sys.stderr)
        return 1
    for m in picked:
        print_meme(m, archive)
    return 0


def cmd_search(archive: Archive, args) -> int:
    hits = archive.search(args.query)
    if args.limit:
        hits = hits[: args.limit]
    if not hits:
        print(f"没有找到与“{args.query}”相关的内容。", file=sys.stderr)
        return 1
    if args.json:
        import json

        print(json.dumps([m.as_dict() for m in hits], ensure_ascii=False, indent=2))
        return 0
    py_ids = {m.id for m in archive.match_pinyin(args.query)}
    note = "，含拼音匹配" if any(m.id in py_ids for m in hits) else ""
    print(dim(f"找到 {len(hits)} 条（关键词：{args.query}{note}）"))
    print()
    for m in hits:
        print_meme(m, archive)
    return 0


def cmd_show(archive: Archive, args) -> int:
    m = archive.get(args.term)
    if args.json and m:
        import json

        print(json.dumps(m.as_dict(), ensure_ascii=False, indent=2))
        return 0
    if not m:
        hits = archive.find(args.term)
        if len(hits) == 1:
            m = hits[0]
        elif hits:
            print(dim(f"“{args.term}”有 {len(hits)} 个匹配："))
            for h in hits:
                print_brief(h)
            return 0
        else:
            print(f"没有找到“{args.term}”。", file=sys.stderr)
            return 1
    print_meme(m, archive)
    return 0


def cmd_list(archive: Archive, args) -> int:
    items = archive.select(cat=args.cat, era=args.era, min_heat=args.min_heat, source=args.source)
    if args.limit:
        items = items[: args.limit]
    if not items:
        print("没有符合条件的梗。", file=sys.stderr)
        return 1

    if args.json:
        import json

        print(json.dumps([m.as_dict() for m in items], ensure_ascii=False, indent=2))
        return 0

    term_width = min(30, max(display_width(m.term) for m in items) + 2)
    last_cat = None
    for m in items:
        if m.cat != last_cat:
            if last_cat is not None:
                print()
            print(bold(f"{m.cat}｜{archive.cat_name(m.cat)}"))
            last_cat = m.cat
        print_brief(m, term_width)
    print()
    print(dim(f"共 {len(items)} 条"))
    return 0


def cmd_sources(archive: Archive, args) -> int:
    rows = [(s, n) for s, n in archive.source_counts() if n > 0]
    if args.type:
        rows = [(s, n) for s, n in rows if s.type == args.type]
    if not rows:
        print("没有匹配的出处。", file=sys.stderr)
        return 1

    if args.json:
        import json

        print(
            json.dumps(
                [{"id": s.id, "name": s.name, "type": s.type, "year": s.year, "memes": n} for s, n in rows],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    width = max(display_width(s.name) for s, _ in rows) + 2
    print(bold(f"出处 {len(rows)} 个，共 {sum(n for _, n in rows)} 条"))
    print()
    shown = rows[: args.limit] if args.limit else rows
    top = rows[0][1] if rows else 0
    for s, n in shown:
        year = str(s.year) if s.year else "----"
        print(
            f"  {pad(s.name, width)}{dim(pad(s.type, 12))}{dim(pad(year, 8))}"
            f"{str(n):>4}  {cyan(_bar(n, top))}"
        )
    return 0


def cmd_stats(archive: Archive, args) -> int:
    s = archive.stats()
    print(bold(f"共 {s['total']} 条，{len(archive.categories)} 类，{s['source_count']} 个出处"))
    if archive.updated:
        print(dim(f"数据版本：{archive.updated}"))
    print()

    width = max(display_width(c.name) for c in archive.categories) + 2
    cat_max = max(s["categories"].values()) if s["categories"] else 0
    print(bold("分类"))
    for c in archive.categories:
        n = s["categories"].get(c.id, 0)
        print(f"  {dim(c.id)}  {pad(c.name, width)}{str(n):>4}  {cyan(_bar(n, cat_max))}")
    print()

    print(bold("年代"))
    era_max = max(s["eras"].values()) if s["eras"] else 0
    for era, n in s["eras"].items():
        print(f"  {pad(era, 14)}{str(n):>4}  {cyan(_bar(n, era_max))}")
    print()

    print(bold("热度"))
    for h in range(5, 0, -1):
        n = s["heat"].get(h, 0)
        bar = "▇" * round(n / 8)
        print(f"  {yellow('★' * h + '☆' * (5 - h))}  {str(n):>4}  {cyan(bar)}")
    print()

    print(bold("出处 Top 10"))
    counts = archive.source_counts()
    top_max = counts[0][1] if counts else 0
    for src, n in counts[:10]:
        print(f"  {pad(src.name, 16)}{dim(pad(src.type, 12))}{str(n):>4}  {cyan(_bar(n, top_max))}")
    return 0


def cmd_fortune(archive: Archive, args) -> int:
    entries = fortune_mod.load(args.file)
    if not entries:
        print("语录库是空的。", file=sys.stderr)
        return 1
    if args.all:
        for e in entries:
            print(e)
        return 0
    for e in fortune_mod.draw(args.n, args.file):
        print(e)
        if args.n > 1:
            print()
    return 0


def cmd_serve(archive: Archive, args) -> int:
    from .server import serve

    serve(archive, host=args.host, port=args.port, quiet=args.quiet)
    return 0


def cmd_export(archive: Archive, args) -> int:
    out = args.out or "dist/互联网梗大全"
    parent = os.path.dirname(os.path.abspath(out))
    os.makedirs(parent, exist_ok=True)
    try:
        files = export_mod.export(archive, args.format, out)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for f in files:
        print(f"{green('✓')} {f}  {dim(str(os.path.getsize(f)) + ' bytes')}")
    return 0


# ---------- 参数 ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="meme",
        description="互联网梗库：查询、随机抽梗、fortune 语录与导出。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  meme random -n 3 --cat J\n"
            "  meme search 破防 / meme search pofang\n"
            "  meme show A01\n"
            "  meme sources --type film\n"
            "  meme serve --port 8000\n"
            "  meme fortune -n 3\n"
            "  meme export -f all -o dist/互联网梗大全"
        ),
    )
    p.add_argument("--version", action="version", version=f"meme-archive {__version__}")
    p.add_argument("--data", help="自定义 memes.json 路径（默认用内置数据）")
    sub = p.add_subparsers(dest="command")

    sp = sub.add_parser("random", help="随机抽梗")
    sp.add_argument("-n", type=int, default=1, help="抽几条（默认 1）")
    sp.add_argument("--cat", help="限定分类，如 A 或 A,C")
    sp.add_argument("--era", help="限定年代，如 2020–2023")
    sp.add_argument("--min-heat", type=int, default=0, help="最低热度 1–5")
    sp.add_argument("--source", help="限定出处 id 或名称")
    sp.set_defaults(func=cmd_random)

    sp = sub.add_parser("search", help="全文搜索（支持拼音）")
    sp.add_argument("query", help="关键词，或全拼/首字母，如 neijuan / nj")
    sp.add_argument("-n", "--limit", type=int, default=0, help="最多显示几条")
    sp.add_argument("--json", action="store_true", help="输出 JSON")
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("show", help="查看单条")
    sp.add_argument("term", help="梗名、编号或拼音，如 内卷 / A01 / neijuan")
    sp.add_argument("--json", action="store_true", help="输出 JSON")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("list", help="按条件列出")
    sp.add_argument("--cat", help="分类")
    sp.add_argument("--era", help="年代")
    sp.add_argument("--min-heat", type=int, default=0)
    sp.add_argument("--source", help="出处 id 或名称")
    sp.add_argument("-n", "--limit", type=int, default=0, help="最多显示几条")
    sp.add_argument("--json", action="store_true", help="输出 JSON")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("sources", help="列出出处")
    sp.add_argument("--type", help="限定类型：film / tv / game / anime / platform / person / event / web")
    sp.add_argument("-n", "--limit", type=int, default=0, help="最多显示几个")
    sp.add_argument("--json", action="store_true", help="输出 JSON")
    sp.set_defaults(func=cmd_sources)

    sp = sub.add_parser("stats", help="统计")
    sp.set_defaults(func=cmd_stats)

    sp = sub.add_parser("fortune", help="随机语录")
    sp.add_argument("-n", type=int, default=1, help="抽几条（默认 1）")
    sp.add_argument("--all", action="store_true", help="全部输出")
    sp.add_argument("-f", "--file", help="自定义 fortunes 文件")
    sp.set_defaults(func=cmd_fortune)

    sp = sub.add_parser("serve", help="启动只读 JSON 接口")
    sp.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    sp.add_argument("--port", type=int, default=8000, help="端口（默认 8000）")
    sp.add_argument("--quiet", action="store_true", help="不打印访问日志")
    sp.set_defaults(func=cmd_serve)

    sp = sub.add_parser("export", help="导出 md / csv / xlsx")
    sp.add_argument("-f", "--format", default="md", choices=["md", "csv", "xlsx", "all"])
    sp.add_argument("-o", "--out", help="输出路径（默认 dist/互联网梗大全）")
    sp.set_defaults(func=cmd_export)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    archive = Archive.load(getattr(args, "data", None))
    return args.func(archive, args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
