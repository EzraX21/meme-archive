# HTTP JSON 接口

只读接口，标准库实现，无第三方依赖。

```bash
meme serve --port 8000          # 默认只监听 127.0.0.1
meme serve --host 0.0.0.0 --port 8000
```

- 所有响应 `application/json; charset=utf-8`，`ensure_ascii=False`。
- 加 `?pretty=1` 输出缩进格式。
- 只支持 `GET` / `HEAD`，其余方法返回 `405`。
- 带 `Access-Control-Allow-Origin: *`，浏览器可直接取。
- 错误统一为 `{"error": {"code", "status", "message"}}`。

## 端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 服务信息与端点列表 |
| GET | `/health` | 健康检查 |
| GET | `/memes` | 词条列表，支持过滤与分页 |
| GET | `/memes/{id}` | 单条，支持编号、梗名或拼音 |
| GET | `/categories` | 分类及条数 |
| GET | `/sources` | 出处及条数 |
| GET | `/sources/{id}` | 单个出处及其全部词条 |
| GET | `/fortune` | 随机语录 |
| GET | `/stats` | 汇总统计 |
| GET | `/docs` | HTML 说明页 |

## GET /memes

| 参数 | 说明 | 示例 |
| --- | --- | --- |
| `q` | 关键词；支持中文、全拼前缀、首字母 | `q=pofang`、`q=破防` |
| `cat` | 分类 id，可逗号分隔 | `cat=J`、`cat=A,C` |
| `source` | 出处 id 或名称 | `source=zhenhuan` |
| `era` | 年代（子串匹配） | `era=2020` |
| `min_heat` | 最低热度 1–5 | `min_heat=5` |
| `limit` | 每页条数，默认 50，最大 500 | `limit=20` |
| `offset` | 偏移量，默认 0 | `offset=40` |

响应：

```json
{
  "total": 382,
  "limit": 50,
  "offset": 0,
  "count": 1,
  "items": [
    {
      "id": "A06",
      "cat": "A",
      "term": "破防",
      "meaning": "心理防线被击破，被戳中痛处或感动到绷不住。",
      "origin": "原是游戏术语“打破防御”，2021 年起在社交平台泛化。",
      "example": "看到那条留言我直接破防。",
      "era": "2020–2023",
      "heat": 5,
      "source": "web",
      "source_name": "网络",
      "category_name": "流行语·社会情绪"
    }
  ]
}
```

## 示例

```bash
curl 'http://127.0.0.1:8000/memes?source=zhenhuan'
curl 'http://127.0.0.1:8000/memes?q=pofang'
curl 'http://127.0.0.1:8000/memes?cat=J&min_heat=5&limit=5'
curl 'http://127.0.0.1:8000/memes/A01'
curl 'http://127.0.0.1:8000/sources?type=game'
curl 'http://127.0.0.1:8000/sources/zhenhuan'
curl 'http://127.0.0.1:8000/fortune?n=3&pretty=1'
curl 'http://127.0.0.1:8000/stats'
```

## GET /sources 响应

```json
{
  "total": 95,
  "limit": 500,
  "offset": 0,
  "count": 15,
  "items": [
    { "id": "wangzhe", "name": "王者荣耀", "type": "game", "year": 2015, "total": 2 }
  ]
}
```

## GET /sources/{id} 响应

```json
{
  "id": "zhenhuan",
  "name": "甄嬛传",
  "type": "tv",
  "year": 2011,
  "total": 4,
  "items": ["…同 /memes 的单条结构…"]
}
```

## 错误码

| 状态 | code | 场景 |
| --- | --- | --- |
| 400 | `invalid_param` | `limit` 非整数、超出范围 |
| 404 | `not_found` | 路径、词条或出处不存在 |
| 405 | `method_not_allowed` | 用了 POST / PUT 等 |
| 500 | `internal_error` | 兜底 |

## 说明

- 服务是无状态的，不写文件，也不依赖网络。
- 数据在启动时一次性载入内存，改 `memes.json` 后需重启。
- 未做鉴权与限流，只适合本机或内网；对外暴露请前面挂反向代理。
