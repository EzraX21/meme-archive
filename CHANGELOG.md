# Changelog

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

## [1.2.0] - 2026-11-15

### 新增

- **只读 HTTP 接口** `meme serve`：标准库实现，零依赖；提供 `/memes`、`/memes/{id}`、`/categories`、`/sources`、`/sources/{id}`、`/fortune`、`/stats`、`/health`、`/docs`。
- 接口支持 `q / cat / source / era / min_heat / limit / offset` 过滤与分页，`?pretty=1` 格式化，CORS 开放，错误统一 JSON。
- `search` / `show` 增加 `--json` 输出，便于脚本与接口对齐。
- `docs/api.md`：端点、参数、响应示例与错误码。

### 变更

- 查询逻辑统一到 `Archive.query()`，CLI 与 HTTP 复用。
- 测试从 32 个增加到 46 个（新增接口测试）。

## [1.1.0] - 2026-11-15

### 新增

- **出处实体表** `sources.json`：93 个出处（作品/人物/平台/事件），带类型与年份；`memes.json` 每条通过 `source` 外键关联。
- **拼音搜索**：全拼前缀与首字母匹配（`neijuan`、`nj`、`pofang`），索引 `pinyin.json` 随仓库分发，运行时不依赖拼音库。
- CLI 新命令 `sources`（按类型过滤、`--json`），`list` / `random` 支持 `--source`。
- 导出：CSV 与 Excel 增加“出处实体”列，Excel 新增“出处表”工作表。
- `scripts/assign_sources.py`（规则分配，可 review）与 `scripts/gen_pinyin.py`。
- 测试从 27 个增加到 32 个。

### 变更

- `show` 在非“网络”出处时多显示一行“出自”。
- 统计页增加“出处 Top 10”，柱状条改为相对最大值缩放。

## [1.0.0] - 2026-11-15

### 新增

- 382 条互联网梗数据，分 10 大类（A–J），字段含释义、出处、例句、年代、热度。
- CLI：`random` / `search` / `show` / `list` / `stats` / `fortune` / `export`。
- 导出 Markdown、CSV、Excel（总表 + 分类表 + 统计图表）。
- 60 条 fortune 语录，标准 `%` 分隔格式，可直接接 `fortune`。
- 27 个单元测试，覆盖数据校验、查询、导出与 CLI。
- GitHub Actions CI（Python 3.9 / 3.12）。
