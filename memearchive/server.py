# -*- coding: utf-8 -*-
"""只读 HTTP JSON 接口，标准库实现，无第三方依赖。

    meme serve --port 8000

端点见 docs/api.md，或启动后访问 http://127.0.0.1:8000/
"""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__, fortune as fortune_mod
from .core import Archive, Meme

DEFAULT_LIMIT = 50
MAX_LIMIT = 500


class HttpError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _json_bytes(payload: Any, pretty: bool = False) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None).encode("utf-8")


def meme_payload(archive: Archive, m: Meme) -> Dict[str, Any]:
    data = m.as_dict()
    src = archive.source_of(m)
    data["source_name"] = src.name if src else ""
    data["category_name"] = archive.cat_name(m.cat)
    return data


def _int_param(params: Dict[str, List[str]], name: str, default: int, lo: int, hi: int) -> int:
    raw = params.get(name, [None])[0]
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise HttpError(400, "invalid_param", f"{name} 必须是整数")
    if value < lo or value > hi:
        raise HttpError(400, "invalid_param", f"{name} 需在 {lo}–{hi} 之间")
    return value


def _str_param(params: Dict[str, List[str]], name: str) -> Optional[str]:
    raw = params.get(name, [None])[0]
    return raw.strip() if raw and raw.strip() else None


def _page(items: List[Meme], archive: Archive, params: Dict[str, List[str]]) -> Dict[str, Any]:
    limit = _int_param(params, "limit", DEFAULT_LIMIT, 1, MAX_LIMIT)
    offset = _int_param(params, "offset", 0, 0, 10**9)
    window = items[offset : offset + limit]
    return {
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "count": len(window),
        "items": [meme_payload(archive, m) for m in window],
    }


def route(archive: Archive, path: str, params: Dict[str, List[str]]) -> Tuple[int, Any]:
    parts = [unquote(p) for p in path.strip("/").split("/") if p]
    resource = parts[0] if parts else ""

    if resource == "":
        return 200, {
            "name": "meme-archive",
            "version": __version__,
            "total": len(archive.items),
            "endpoints": {
                "GET /memes": "列表；q, cat, source, era, min_heat, limit, offset",
                "GET /memes/{id}": "单条，支持编号或梗名",
                "GET /categories": "分类及条数",
                "GET /sources": "出处及条数；type, limit, offset",
                "GET /sources/{id}": "单个出处及其词条",
                "GET /fortune": "语录；n",
                "GET /stats": "汇总统计",
                "GET /health": "健康检查",
                "GET /docs": "HTML 说明页",
            },
        }

    if resource == "health":
        return 200, {"status": "ok", "version": __version__, "total": len(archive.items)}

    if resource == "docs":
        return 200, {"_html": _docs_html()}

    if resource == "categories":
        counts = {c.id: 0 for c in archive.categories}
        for m in archive.items:
            counts[m.cat] += 1
        return 200, {
            "items": [
                {"id": c.id, "name": c.name, "total": counts.get(c.id, 0)} for c in archive.categories
            ]
        }

    if resource == "sources":
        if len(parts) == 2:
            key = parts[1]
            src = next((s for s in archive.sources if key in (s.id, s.name)), None)
            if not src:
                raise HttpError(404, "not_found", f"没有找到出处“{key}”")
            memes = [m for m in archive.items if m.source == src.id]
            return 200, {
                "id": src.id,
                "name": src.name,
                "type": src.type,
                "year": src.year,
                "total": len(memes),
                "items": [meme_payload(archive, m) for m in memes],
            }

        rows = [(s, n) for s, n in archive.source_counts() if n > 0]
        type_filter = _str_param(params, "type")
        if type_filter:
            rows = [(s, n) for s, n in rows if s.type == type_filter]
        limit = _int_param(params, "limit", MAX_LIMIT, 1, MAX_LIMIT)
        offset = _int_param(params, "offset", 0, 0, 10**9)
        window = rows[offset : offset + limit]
        return 200, {
            "total": len(rows),
            "limit": limit,
            "offset": offset,
            "count": len(window),
            "items": [
                {"id": s.id, "name": s.name, "type": s.type, "year": s.year, "total": n}
                for s, n in window
            ],
        }

    if resource == "fortune":
        n = _int_param(params, "n", 1, 1, 50)
        return 200, {"items": fortune_mod.draw(n)}

    if resource == "stats":
        s = archive.stats()
        return 200, {
            "total": s["total"],
            "by_category": s["categories"],
            "by_era": s["eras"],
            "by_heat": {str(k): v for k, v in s["heat"].items()},
            "by_source": s["sources"],
            "source_count": s["source_count"],
            "updated": archive.updated,
        }

    if resource == "memes":
        if len(parts) == 2:
            key = parts[1]
            m = archive.get(key)
            if not m:
                raise HttpError(404, "not_found", f"没有找到“{key}”")
            return 200, meme_payload(archive, m)

        q = _str_param(params, "q")
        items = archive.query(
            q=q,
            cat=_str_param(params, "cat"),
            era=_str_param(params, "era"),
            min_heat=_int_param(params, "min_heat", 0, 0, 5),
            source=_str_param(params, "source"),
        )
        return 200, _page(items, archive, params)

    raise HttpError(404, "not_found", f"未知路径：{path}")


def _docs_html() -> str:
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>meme-archive API</title>
<style>
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;max-width:760px;margin:40px auto;padding:0 20px;line-height:1.7;color:#222}
code{background:#f4f4f6;padding:2px 6px;border-radius:4px}
table{border-collapse:collapse;width:100%;margin:16px 0}
td,th{border:1px solid #ddd;padding:8px 10px;text-align:left;font-size:14px}
th{background:#1f3864;color:#fff}
h1{font-size:24px}
a{color:#1f3864}
</style></head><body>
<h1>meme-archive API</h1>
<p>只读 JSON 接口，所有响应 <code>application/json; charset=utf-8</code>，支持 <code>?pretty=1</code> 格式化。</p>
<table>
<tr><th>端点</th><th>说明</th></tr>
<tr><td><code>GET /memes</code></td><td>列表，参数 <code>q, cat, source, era, min_heat, limit, offset</code></td></tr>
<tr><td><code>GET /memes/{id}</code></td><td>单条，支持编号或梗名</td></tr>
<tr><td><code>GET /categories</code></td><td>分类及条数</td></tr>
<tr><td><code>GET /sources</code></td><td>出处及条数，参数 <code>type</code></td></tr>
<tr><td><code>GET /sources/{id}</code></td><td>单个出处及其所有词条</td></tr>
<tr><td><code>GET /fortune?n=3</code></td><td>随机语录</td></tr>
<tr><td><code>GET /stats</code></td><td>汇总统计</td></tr>
<tr><td><code>GET /health</code></td><td>健康检查</td></tr>
</table>
<p>示例：<code>/memes?source=zhenhuan</code>、<code>/memes?q=pofang</code>、<code>/memes?cat=J&amp;min_heat=5</code></p>
</body></html>"""


def make_handler(archive: Archive, quiet: bool = False):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"meme-archive/{__version__}"
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:  # noqa: A003
            if not quiet:
                sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_HEAD(self) -> None:  # noqa: N802
            self._handle(head_only=True)

        def do_GET(self) -> None:  # noqa: N802
            self._handle()

        def _not_allowed(self) -> None:
            body = _json_bytes(
                {"error": {"code": "method_not_allowed", "status": 405, "message": "只支持 GET / HEAD"}}
            )
            self.send_response(405)
            self.send_header("Allow", "GET, HEAD, OPTIONS")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            self._not_allowed()

        def do_PUT(self) -> None:  # noqa: N802
            self._not_allowed()

        def do_DELETE(self) -> None:  # noqa: N802
            self._not_allowed()

        def do_PATCH(self) -> None:  # noqa: N802
            self._not_allowed()

        def _error(self, status: int, code: str, message: str, head_only: bool = False) -> None:
            self._send(
                status,
                {"error": {"code": code, "status": status, "message": message}},
                head_only,
            )

        def _send(self, status: int, payload: Any, head_only: bool = False, ctype: Optional[str] = None) -> None:
            if isinstance(payload, dict) and "_html" in payload:
                body = payload["_html"].encode("utf-8")
                ctype = "text/html; charset=utf-8"
            else:
                pretty = self._pretty
                body = _json_bytes(payload, pretty)
                ctype = ctype or "application/json; charset=utf-8"
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if not head_only:
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        def _handle(self, head_only: bool = False) -> None:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            self._pretty = params.get("pretty", ["0"])[0].lower() in ("1", "true", "yes")
            try:
                status, payload = route(archive, parsed.path, params)
            except HttpError as exc:
                self._error(exc.status, exc.code, exc.message, head_only)
                return
            except Exception as exc:  # pragma: no cover - 兜底
                self._error(500, "internal_error", str(exc), head_only)
                return
            self._send(status, payload, head_only)

    return Handler


def create_server(archive: Archive, host: str = "127.0.0.1", port: int = 8000, quiet: bool = True) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(archive, quiet=quiet))


def serve(archive: Archive, host: str = "127.0.0.1", port: int = 8000, quiet: bool = False) -> None:
    httpd = create_server(archive, host, port, quiet=quiet)
    url = f"http://{host}:{httpd.server_port}"
    print(f"meme-archive {__version__} · {url}")
    print("  GET /memes   /memes/{id}   /sources   /stats   /fortune?n=3")
    print("  Ctrl+C 停止")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()
