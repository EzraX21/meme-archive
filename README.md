# meme-archive · 互联网梗大全

382 条中文互联网梗 · 95 个出处实体 · 60 条 fortune 语录 · 查询、抽取、导出。

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![tests](https://img.shields.io/badge/tests-46%20passed-brightgreen)
![data](https://img.shields.io/badge/data-382%20entries-orange)
![license](https://img.shields.io/badge/license-MIT%20%2B%20CC%20BY--SA%204.0-lightgrey)

## 这是什么

一个把“网上那些梗”整理成可用数据的小项目：

- **382 条词条**，分 10 大类：流行语、缩写谐音、影视名场面、表情包人物、游戏电竞、弹幕二次元、方言、海外梗、早期考古、2025–2026 新梗。
- 每条字段：`梗 / 释义 / 出处 / 例句 / 年代 / 热度`，并**外键关联到一个出处实体**（作品、人物、平台或事件）。
- **拼音搜索**：`neijuan`、`nj`、`pofang` 都能查到，索引随仓库走，运行时不依赖拼音库。
- 自带 **CLI**：随机抽梗、搜索、按分类/年代/出处筛选、统计。
- 自带 **fortune 语录**：60 条能单独成立的句子，可直接接 `fortune`。
- 一键导出 **Markdown / CSV / Excel**（Excel 含分类表、出处表、统计图）。
- 自带 **只读 JSON 接口**：`meme serve`，零依赖，按分类/出处/关键词查询。

## 快速开始

不需要安装，仓库根目录直接跑：

```bash
python3 -m memearchive random          # 随机一条
python3 -m memearchive search 破防      # 搜索（也支持 pofang）
python3 -m memearchive sources         # 看所有出处
python3 -m memearchive stats           # 统计
```

想装成命令 `meme`：

```bash
pip install -e ".[xlsx]"   # xlsx 导出需要 openpyxl，其余功能零依赖
meme random -n 3
```

## 命令

| 命令 | 说明 | 示例 |
| --- | --- | --- |
| `random` | 随机抽梗，可按分类/年代/热度/出处过滤 | `meme random -n 3 --cat J --min-heat 4` |
| `search` | 全文搜索 + 拼音（全拼前缀、首字母） | `meme search pofang` |
| `show` | 查看单条（编号、名称或拼音） | `meme show A01` / `meme show neijuan` |
| `list` | 条件列出，支持 `--json` | `meme list --source zhenhuan` |
| `sources` | 列出处及条数，可按类型过滤 | `meme sources --type film` |
| `stats` | 分类 / 年代 / 热度 / 出处分布 | `meme stats` |
| `serve` | 启动只读 JSON 接口 | `meme serve --port 8000` |
| `fortune` | 随机语录 | `meme fortune -n 3` |
| `export` | 导出 md / csv / xlsx | `meme export -f all -o dist/互联网梗大全` |

输出示例：

```
$ meme show C04
C04  臣妾做不到  ★★★★★  2010–2015
  释义  表示实在做不到、无能为力。
  出处  《甄嬛传》皇后宜修台词。
  出自  甄嬛传（tv，2011）
  例句  让我六点起床？臣妾做不到。
```

## 数据

三个数据文件，都在 `memearchive/data/`：

| 文件 | 内容 |
| --- | --- |
| `memes.json` | 382 条梗，`source` 字段外键指向出处 |
| `sources.json` | 95 个出处实体（作品/人物/平台/事件），带类型与年份 |
| `pinyin.json` | 382 条拼音索引（全拼 + 首字母），由 `scripts/gen_pinyin.py` 生成 |

| 类 | 内容 | 条数 |
| --- | --- | ---: |
| A | 流行语·社会情绪 | 60 |
| B | 缩写与谐音 | 45 |
| C | 影视综艺名场面 | 40 |
| D | 表情包与网红人物 | 35 |
| E | 游戏与电竞 | 30 |
| F | 弹幕·二次元·饭圈 | 35 |
| G | 地域与方言 | 25 |
| H | 海外与英文梗 | 45 |
| I | 考古·早期经典 | 35 |
| J | 2025–2026 新梗 | 32 |

字段定义、出处类型与校验规则见 [docs/data-schema.md](docs/data-schema.md)。

**来源**：2025 年度十大网络流行语参考国家语言资源监测与研究中心发布、[商务印书馆刊载](https://www.cp.com.cn/Content/2025/12-11/1519412222.html)的名单；2026 年初新梗参考[人民日报](https://www.peopleapp.com/column/30051748153-500007415266)等媒体报道与网络盘点。释义与例句为编写，非官方定义。

## 导出

```bash
meme export -f all -o dist/互联网梗大全
```

- `互联网梗大全.md` — 可读全文，非“网络”出处的条目会附相关作品
- `互联网梗大全.csv` — UTF-8 BOM，Excel 直接打开不乱码
- `互联网梗大全.xlsx` — 总表 + 10 个分类表 + 出处表 + 统计页（带图表）

## HTTP 接口

```bash
meme serve --port 8000
```

```bash
curl 'http://127.0.0.1:8000/memes?source=zhenhuan'
curl 'http://127.0.0.1:8000/memes?q=pofang&pretty=1'
curl 'http://127.0.0.1:8000/sources?type=game'
```

端点、参数与响应结构见 [docs/api.md](docs/api.md)。服务只读、无鉴权，适合本机或内网。

## fortune 语录

`memearchive/data/fortunes.txt` 是标准 fortune 格式（条目间用单独一行 `%` 分隔）：

```bash
strfile memearchive/data/fortunes.txt
fortune memearchive/data/fortunes.txt
```

或者用自带的：`meme fortune -n 3`。

## 项目结构

```
meme-archive/
├── memearchive/
│   ├── cli.py          # 命令行
│   ├── core.py         # 数据模型、拼音匹配、查询
│   ├── export.py       # md / csv / xlsx 导出
│   ├── fortune.py      # 语录
│   ├── server.py       # 只读 HTTP 接口
│   └── data/
│       ├── memes.json
│       ├── sources.json
│       ├── pinyin.json
│       └── fortunes.txt
├── scripts/
│   ├── gen_pinyin.py       # 生成拼音索引（需要 pypinyin）
│   └── assign_sources.py   # 给词条挂出处（规则 + 兜底）
├── tests/              # 46 个测试
├── docs/
├── dist/               # 导出产物（git 忽略）
├── pyproject.toml
└── Makefile
```

## 加一条梗

1. 在 `memearchive/data/memes.json` 的 `items` 里追加：

```json
{
  "id": "J33",
  "cat": "J",
  "term": "新梗",
  "meaning": "一句话解释",
  "origin": "出处",
  "example": "例句",
  "era": "2024–2026",
  "heat": 4,
  "source": "web"
}
```

2. 如果出处不在 `sources.json` 里，先在 `scripts/assign_sources.py` 的 `SOURCE_LIST` 加实体，再跑：

```bash
python3 scripts/assign_sources.py   # 重新分配出处
python3 scripts/gen_pinyin.py       # 补拼音（需要 pypinyin）
make test
```

`assign_sources.py` 按“作品 > 人物 > 平台 > 网络”的顺序匹配，没命中的落到 `web`。规则集中在 `RULES` 里，改动可 review。

## 开发

```bash
pip install -r requirements-dev.txt   # pypinyin + openpyxl
make test     # 46 个 unittest
make export   # 重新生成 dist/
make pinyin   # 重新生成拼音索引
make sources  # 重新分配出处
```

## 许可

- 代码：[MIT](LICENSE)
- 数据（`memes.json`、`sources.json`、`pinyin.json`、`fortunes.txt`）：[CC BY-SA 4.0](LICENSE-DATA)

## 已知限制

- **出处是一对多简化**：一个梗只挂一个主要出处，多个来源时取最先命中的；完整语境看 `origin` 文本。
- **热度是主观值**，用于排序参考，不是精确排名。
- **释义非官方**，梗的含义随语境漂移，以“出处 + 例句”为准。
- 拼音按字面生成，**多音字可能不准**（如“重”“长”），生成后建议抽查。
- 数据覆盖面偏中文互联网，海外梗仅收录 45 条主流款。
