# 数据结构

三个数据文件都在 `memearchive/data/`，UTF-8、2 空格缩进。这是唯一数据源，CLI 与导出都读它们。

```
memes.json ──source──> sources.json
     │
     └──id──> pinyin.json（派生，可重新生成）
```

## memes.json

```json
{
  "schema": 1,
  "updated": "2026-11-15",
  "categories": [{ "id": "A", "name": "流行语·社会情绪" }],
  "items": [
    {
      "id": "A01",
      "cat": "A",
      "term": "内卷",
      "meaning": "在资源有限的条件下……",
      "origin": "源自人类学“农业内卷化”……",
      "example": "公司要求每天写日报……",
      "era": "2020–2023",
      "heat": 5,
      "source": "web"
    }
  ]
}
```

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `id` | string | `分类字母 + 两位序号`，全局唯一 |
| `cat` | string | 必须是 `categories` 中存在的 id |
| `term` | string | 全局唯一，非空 |
| `meaning` | string | 非空，一句话释义 |
| `origin` | string | 非空，出处或流行背景（自由文本） |
| `example` | string | 非空，可直接使用的例句 |
| `era` | string | 形如 `2020–2023`（en dash `–`） |
| `heat` | int | 1–5，5 为最热 |
| `source` | string | 外键，必须存在于 `sources.json` |

`source` 是**主要出处**，`origin` 保留完整表述。两者不重复：前者可索引、可聚合，后者可读。

## sources.json

```json
{
  "schema": 1,
  "items": [
    { "id": "zhenhuan", "name": "甄嬛传", "type": "tv", "year": 2011 },
    { "id": "web", "name": "网络", "type": "web", "year": 1990 }
  ]
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 小写英文/数字，全局唯一 |
| `name` | string | 展示名 |
| `type` | string | 见下表 |
| `year` | int / null | 作品首播/发行年；平台为上线年；`web` 为占位 |

### type 取值

| type | 含义 | 例子 |
| --- | --- | --- |
| `film` | 电影 | 让子弹飞、功夫 |
| `tv` | 电视剧/综艺 | 甄嬛传、变形计 |
| `game` | 游戏 | 原神、黑神话：悟空 |
| `anime` | 动画/番剧 | 新世纪福音战士、Skibidi Toilet |
| `person` | 人物 | 马保国、大司马 |
| `platform` | 平台/渠道 | 百度贴吧、B站、短视频平台 |
| `event` | 事件/赛事 | 春晚、NBA、国足 |
| `web` | 泛指网络 | 兜底，无更具体出处时使用 |

## pinyin.json

派生文件，由 `scripts/gen_pinyin.py` 生成：

```json
{
  "schema": 1,
  "items": {
    "A01": { "full": "neijuan", "initials": "nj" }
  }
}
```

- `full`：全拼，去声调、只保留 `a-z0-9`
- `initials`：首字母

搜索规则：全拼**前缀匹配**或首字母**全等**才命中，且查询至少 2 个字符。改动 `term` 后需要重跑生成脚本。

## 校验

`tests/` 会检查：

- 总数为 382，分类为 A–J
- `id`、`term` 全局唯一
- 必需字段非空，`heat` 在 1–5，`cat` 合法
- 每条 `source` 都能在 `sources.json` 里找到
- 每条都有拼音索引

## 约定

- **年代**是“大致流行区间”，不是首次出现年份。
- **热度**是整理时的体感值，用于排序与筛选。
- 例句尽量写成**能直接发出去的一句话**。
- 新增出处时，`id` 用作品/人物的通行英文名，避免拼音歧义。
