# -*- coding: utf-8 -*-
"""导出：Markdown / CSV / Excel。"""
from __future__ import annotations

import csv
import io
import math
import os
from collections import Counter
from typing import List

from .core import Archive

HEADERS = ["序号", "分类", "梗", "释义", "出处 / 来源", "出处实体", "用法示例", "年代", "热度"]
WIDTHS = [6, 17, 22, 50, 40, 20, 34, 13, 12]


def to_markdown(archive: Archive) -> str:
    out: List[str] = []
    add = out.append
    total = len(archive.items)

    add("# 互联网梗大全")
    add("")
    add(f"共收录 **{total}** 条，分 **{len(archive.categories)}** 大类。每条包含释义、出处、用法示例、年代与热度。")
    add("")
    if archive.updated:
        add(f"> 整理时间：{archive.updated} · 由 meme-archive 生成")
    add("")
    add("---")
    add("")
    add("## 目录")
    add("")
    by_cat = archive.by_cat()
    for c in archive.categories:
        add(f"- **{c.id}｜{c.name}**（{len(by_cat[c.id])} 条）")
    add("")
    add("---")
    add("")

    add("## 怎么用这份表")
    add("")
    add("1. **查梗**：先按分类找，再按“梗”的名字扫；Excel 版可以直接筛选、搜索。")
    add("2. **看语境**：释义只说明大意，真正决定分寸的是“出处”和“用法示例”。")
    add("3. **注意时效**：“热度”是整理时的体感，不是绝对排名；很多梗两三年后就变成“考古”。")
    add("4. **慎用场合**：梗的底色多是调侃与自嘲，正式文书、陌生场合、跨代沟通里容易翻车。")
    add("")
    add("---")
    add("")

    for c in archive.categories:
        items = by_cat[c.id]
        add(f"## {c.id}｜{c.name}")
        add("")
        for m in items:
            add(f"#### {m.id}　{m.term}")
            add("")
            add(f"- **释义**：{m.meaning}")
            add(f"- **出处**：{m.origin}")
            src = archive.source_of(m)
            if src and src.id != "web":
                add(f"- **相关作品**：{src.name}（{src.type}，{src.year}）")
            add(f"- **例句**：{m.example}")
            add(f"- **年代**：{m.era}　｜　**热度**：{m.stars}")
            add("")
        add("---")
        add("")

    add("## 附录：分类速查")
    add("")
    add("| 分类 | 条数 | 代表梗 |")
    add("| --- | ---: | --- |")
    for c in archive.categories:
        items = by_cat[c.id]
        rep = "、".join(m.term for m in items[:6])
        add(f"| {c.id}｜{c.name} | {len(items)} | {rep} … |")
    add("")
    add("---")
    add("")
    add("### 一点说明")
    add("")
    add("梗的生命周期很短，今天的“顶流”可能明年就没人接得住了。这份表更像一个切片：")
    add("把 2005 年至今仍在被使用、或被反复考古的表达挑出来，保留它们各自的语境。")
    add("如果要做内容创作，建议把“出处”当成二次创作的入口——很多梗的寿命，是靠不断被改写续上的。")
    add("")
    if archive.updated:
        add(f"数据版本：{archive.updated}。释义与例句为编写，非官方定义。")
        add("")
    return "\n".join(out)


def to_csv_text(archive: Archive) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)
    for idx, m in enumerate(archive.items, 1):
        w.writerow(
            [idx, archive.cat_name(m.cat), m.term, m.meaning, m.origin, archive.source_name(m), m.example, m.era, m.stars]
        )
    return buf.getvalue()


def write_csv(archive: Archive, path: str) -> str:
    # utf-8-sig：Excel 直接打开不乱码
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(to_csv_text(archive))
    return path


def write_markdown(archive: Archive, path: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_markdown(archive))
    return path


# ---------------- Excel ----------------

def _est_height(values, widths) -> int:
    lines = 1
    for v, w in zip(values, widths):
        if v is None:
            continue
        s = str(v)
        units = sum(2.4 if ord(ch) > 0x2E80 else 1.15 for ch in s)
        lines = max(lines, math.ceil(units / max(4.0, w * 0.92)))
    return min(180, max(24, lines * 14.5 + 8))


def write_xlsx(archive: Archive, path: str) -> str:
    try:
        from openpyxl import Workbook
        from openpyxl.chart import BarChart, Reference
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.properties import PageSetupProperties
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("导出 Excel 需要 openpyxl：pip install 'meme-archive[xlsx]'") from exc

    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    head_fill = PatternFill("solid", fgColor="1F3864")
    band_fill = PatternFill("solid", fgColor="F2F5FA")
    head_font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
    body_font = Font(name="微软雅黑", size=10)

    def style(ws, headers, widths, rows, with_cat=True):
        ws.append(headers)
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        for cell in ws[1]:
            cell.font = head_font
            cell.fill = head_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        ws.row_dimensions[1].height = 30

        for r, row in enumerate(rows, start=2):
            ws.append(row)
            for c, cell in enumerate(ws[r], start=1):
                cell.font = body_font
                cell.border = border
                center = c == 1 or (with_cat and c == len(headers))
                cell.alignment = Alignment(vertical="top", wrap_text=True, horizontal="center" if center else "left")
            if r % 2 == 0:
                for cell in ws[r]:
                    cell.fill = band_fill
            ws.row_dimensions[r].height = _est_height(row, widths)

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.print_title_rows = "1:1"
        ws.print_options.horizontalCentered = True

    wb = Workbook()
    ws = wb.active
    ws.title = "总表"
    table = [
        [i, archive.cat_name(m.cat), m.term, m.meaning, m.origin, archive.source_name(m), m.example, m.era, m.stars]
        for i, m in enumerate(archive.items, 1)
    ]
    style(ws, HEADERS, WIDTHS, table)

    by_cat = archive.by_cat()
    for c in archive.categories:
        sheet = wb.create_sheet(title=f"{c.id}·{c.name}"[:31])
        rows = [
            [i, m.term, m.meaning, m.origin, archive.source_name(m), m.example, m.era, m.stars]
            for i, m in enumerate(by_cat[c.id], 1)
        ]
        style(
            sheet,
            ["序号", "梗", "释义", "出处 / 来源", "出处实体", "用法示例", "年代", "热度"],
            [6, 22, 50, 40, 20, 34, 13, 12],
            rows,
            with_cat=False,
        )

    src_sheet = wb.create_sheet("出处表")
    src_rows = [
        [i, s.id, s.name, s.type, s.year or "", n]
        for i, (s, n) in enumerate(archive.source_counts(), 1)
        if n > 0
    ]
    style(
        src_sheet,
        ["序号", "ID", "出处", "类型", "年份", "条数"],
        [6, 18, 26, 12, 8, 8],
        src_rows,
        with_cat=False,
    )
    for row in src_sheet.iter_rows(min_row=2, min_col=6, max_col=6):
        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="top")

    st = wb.create_sheet("统计")
    st.column_dimensions["A"].width = 26
    st.column_dimensions["B"].width = 12
    st["A1"] = "分类"
    st["B1"] = "条数"
    row = 2
    for c in archive.categories:
        st.cell(row=row, column=1, value=c.name)
        st.cell(row=row, column=2, value=len(by_cat[c.id]))
        row += 1
    total = row
    st.cell(row=total, column=1, value="合计")
    st.cell(row=total, column=2, value=len(archive.items))

    for r in range(1, total + 1):
        for col in (1, 2):
            cell = st.cell(row=r, column=col)
            cell.border = border
            if r == 1:
                cell.font = head_font
                cell.fill = head_fill
            else:
                cell.font = Font(name="微软雅黑", size=10, bold=(r == total))
            cell.alignment = Alignment(vertical="center", horizontal="center" if col == 2 else "left")
        if r % 2 == 0 and r != total:
            st.cell(row=r, column=1).fill = band_fill
            st.cell(row=r, column=2).fill = band_fill

    chart = BarChart()
    chart.type = "bar"
    chart.title = "各类梗数量分布"
    chart.y_axis.title = "条数"
    chart.add_data(Reference(st, min_col=2, min_row=1, max_row=total - 1), titles_from_data=True)
    chart.set_categories(Reference(st, min_col=1, min_row=2, max_row=total - 1))
    chart.height, chart.width, chart.legend = 10, 20, None
    st.add_chart(chart, "E2")

    era_counts = Counter(m.era for m in archive.items)
    er = total + 3
    st.cell(row=er, column=1, value="年代分布").font = Font(bold=True, color="1F3864")
    for era, cnt in sorted(era_counts.items()):
        er += 1
        st.cell(row=er, column=1, value=era)
        st.cell(row=er, column=2, value=cnt)

    st.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    st.page_setup.orientation = "portrait"
    st.page_setup.paperSize = st.PAPERSIZE_A4
    st.page_setup.fitToWidth = 1
    st.page_setup.fitToHeight = 1

    wb.save(path)
    return path


def export(archive: Archive, fmt: str, out: str) -> List[str]:
    """按格式导出，返回生成的文件路径列表。"""
    fmt = fmt.lower()
    written = []
    base, ext = os.path.splitext(out)
    if fmt == "md":
        written.append(write_markdown(archive, out if ext else out + ".md"))
    elif fmt == "csv":
        written.append(write_csv(archive, out if ext else out + ".csv"))
    elif fmt == "xlsx":
        written.append(write_xlsx(archive, out if ext else out + ".xlsx"))
    elif fmt == "all":
        stem = base if ext else out
        written.append(write_markdown(archive, stem + ".md"))
        written.append(write_csv(archive, stem + ".csv"))
        written.append(write_xlsx(archive, stem + ".xlsx"))
    else:
        raise ValueError(f"未知格式：{fmt}（可选 md / csv / xlsx / all）")
    return written
