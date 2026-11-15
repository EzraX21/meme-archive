#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 memes.json 的每一条挂到 sources.json 的出处实体上。

用法：
    python3 scripts/assign_sources.py --dry-run   # 只看分配结果
    python3 scripts/assign_sources.py             # 写回 sources.json + memes.json

规则按“先具体、后泛化”排序：作品 > 人物 > 平台 > 网络。
新增词条后重跑一次即可补上 source 字段。
"""
import argparse
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMES = os.path.join(ROOT, "memearchive", "data", "memes.json")
SOURCES = os.path.join(ROOT, "memearchive", "data", "sources.json")

# (id, 名称, 类型, 年份)
SOURCE_LIST = [
    # ---- 影视 ----
    ("rangzidanfei", "让子弹飞", "film", 2010),
    ("zhenhuan", "甄嬛传", "tv", 2011),
    ("sanguo94", "三国演义（1994）", "tv", 1994),
    ("sanguo2010", "三国（2010）", "tv", 2010),
    ("liangjian", "亮剑", "tv", 2005),
    ("kuangbiao", "狂飙", "tv", 2023),
    ("yinmidejiao", "隐秘的角落", "tv", 2020),
    ("renmindemingyi", "人民的名义", "tv", 2017),
    ("shenchuandirenjie", "神探狄仁杰", "tv", 2004),
    ("yanshuangying", "燕双鹰系列", "tv", 2001),
    ("xiyouji", "西游记（1986）", "tv", 1986),
    ("shuihuzhuan", "水浒传（1998）", "tv", 1998),
    ("dahuaxiyou", "大话西游", "film", 1995),
    ("gongfu", "功夫", "film", 2004),
    ("xialuotefannao", "夏洛特烦恼", "film", 2015),
    ("xihongshishoufu", "西虹市首富", "film", 2018),
    ("liulangdiqiu", "流浪地球", "film", 2019),
    ("nezha1", "哪吒之魔童降世", "film", 2019),
    ("nezha2", "哪吒之魔童闹海", "film", 2025),
    ("shibingtuji", "士兵突击", "tv", 2006),
    ("wulinwaizhuan", "武林外传", "tv", 2006),
    ("aiqinggongyu", "爱情公寓", "tv", 2009),
    ("jiayounver", "家有儿女", "tv", 2005),
    ("huanzhugege", "还珠格格", "tv", 1998),
    ("xiangcunaiqing", "乡村爱情", "tv", 2006),
    ("doutinghao", "都挺好", "tv", 2019),
    ("manchangjijie", "漫长的季节", "tv", 2023),
    ("zhanlang", "战狼", "film", 2015),
    ("wobushiyaoshen", "我不是药神", "film", 2018),
    ("wujiandao", "无间道", "film", 2002),
    ("xijuzhiwang", "喜剧之王", "film", 1999),
    ("tianxiawuzhei", "天下无贼", "film", 2004),
    ("jiupinzhimaguan", "九品芝麻官", "film", 1994),
    ("qingshenshen", "情深深雨濛濛", "tv", 2001),
    ("wangjiaokamen", "旺角卡门", "film", 1988),
    ("bianxingji", "变形计", "tv", 2006),
    ("woaiwojia", "我爱我家", "tv", 1993),
    ("langlangshan", "浪浪山小妖怪", "film", 2025),
    ("balala", "巴啦啦小魔仙", "tv", 2008),
    # ---- 游戏 ----
    ("yuanshen", "原神", "game", 2020),
    ("heishenhua", "黑神话：悟空", "game", 2024),
    ("aierdeng", "艾尔登法环", "game", 2022),
    ("saibopengke", "赛博朋克 2077", "game", 2020),
    ("pvz", "植物大战僵尸", "game", 2009),
    ("wangzhe", "王者荣耀", "game", 2015),
    ("lol", "英雄联盟", "game", 2009),
    ("csgo", "CS:GO", "game", 2012),
    ("amongus", "Among Us", "game", 2018),
    ("yangle", "羊了个羊", "game", 2022),
    ("hechengxigua", "合成大西瓜", "game", 2021),
    ("lvxingqingwa", "旅行青蛙", "game", 2017),
    ("tanwanlanyue", "贪玩蓝月", "game", 2017),
    ("xiaoyouxi4399", "4399 小游戏", "game", 2002),
    ("shimingzhaohuan", "使命召唤", "game", 2003),
    # ---- ACG / 网络形象 ----
    ("eva", "新世纪福音战士", "anime", 1995),
    ("skibidi", "Skibidi Toilet", "anime", 2023),
    ("pepe", "Pepe 蛙", "web", 2005),
    ("doge", "Doge 柴犬", "web", 2010),
    ("cheems", "Cheems 柴犬", "web", 2019),
    ("niconico", "niconico 动画", "platform", 2006),
    # ---- 人物 ----
    ("mabaoguo", "马保国", "person", 2020),
    ("dongyongge", "冬泳怪鸽", "person", 2019),
    ("guolaoshi", "迷人的郭老师", "person", 2019),
    ("dasima", "大司马", "person", 2016),
    ("sunxiaochuan", "孙笑川", "person", 2015),
    ("wangjingze", "王境泽", "person", 2018),
    ("fuyuanhui", "傅园慧", "person", 2016),
    ("wulantuya", "乌兰图雅", "person", 2025),
    ("jipai", "鸡排主理人李俊永", "person", 2025),
    ("fengjie", "凤姐", "person", 2009),
    ("furong", "芙蓉姐姐", "person", 2005),
    ("xilige", "犀利哥", "person", 2010),
    ("naicha", "奶茶妹妹", "person", 2009),
    # ---- 平台 ----
    ("tieba", "百度贴吧", "platform", 2003),
    ("weibo", "微博", "platform", 2009),
    ("douyin", "抖音", "platform", 2016),
    ("kuaishou", "快手", "platform", 2011),
    ("bilibili", "哔哩哔哩", "platform", 2009),
    ("xiaohongshu", "小红书", "platform", 2013),
    ("zhihu", "知乎", "platform", 2011),
    ("douban", "豆瓣", "platform", 2005),
    ("wechat", "微信", "platform", 2011),
    ("qq", "QQ", "platform", 1999),
    ("tianya", "天涯社区", "platform", 1999),
    ("maopu", "猫扑", "platform", 1997),
    ("renren", "人人网", "platform", 2005),
    ("twitter", "X（推特）", "platform", 2006),
    ("reddit", "Reddit", "platform", 2005),
    ("fourchan", "4chan", "platform", 2003),
    ("tiktok", "TikTok", "platform", 2016),
    ("twitch", "Twitch", "platform", 2011),
    ("taobao", "淘宝", "platform", 2003),
    ("duanshipin", "短视频平台", "platform", 2016),
    ("zhibo", "直播平台", "platform", 2014),
    # ---- 事件 ----
    ("chunwan", "央视春晚", "event", 1983),
    ("aoyunhui", "奥运会", "event", 1896),
    ("nba", "NBA", "event", 1946),
    ("shijiebei", "世界杯", "event", 1930),
    ("guozu", "国足", "event", 1924),
    # ---- 兜底 ----
    ("web", "网络", "web", 1990),
]

# 关键词 → 出处 id，按顺序匹配（先具体后泛化）
RULES = [
    ("rangzidanfei", ["让子弹飞"]),
    ("zhenhuan", ["甄嬛传"]),
    ("sanguo94", ["三国演义"]),
    ("sanguo2010", ["《三国》（2010）", "电视剧《三国》"]),
    ("liangjian", ["亮剑"]),
    ("kuangbiao", ["狂飙"]),
    ("yinmidejiao", ["隐秘的角落"]),
    ("renmindemingyi", ["人民的名义"]),
    ("shenchuandirenjie", ["神探狄仁杰"]),
    ("yanshuangying", ["燕双鹰"]),
    ("xiyouji", ["西游记"]),
    ("shuihuzhuan", ["水浒传"]),
    ("dahuaxiyou", ["大话西游"]),
    ("gongfu", ["《功夫》"]),
    ("xialuotefannao", ["夏洛特烦恼"]),
    ("xihongshishoufu", ["西虹市首富"]),
    ("liulangdiqiu", ["流浪地球"]),
    ("nezha2", ["哪吒之魔童闹海"]),
    ("nezha1", ["哪吒之魔童降世", "《哪吒之魔童降世》"]),
    ("shibingtuji", ["士兵突击"]),
    ("wulinwaizhuan", ["武林外传"]),
    ("aiqinggongyu", ["爱情公寓"]),
    ("jiayounver", ["家有儿女"]),
    ("huanzhugege", ["还珠格格"]),
    ("xiangcunaiqing", ["乡村爱情"]),
    ("doutinghao", ["都挺好"]),
    ("manchangjijie", ["漫长的季节"]),
    ("zhanlang", ["战狼"]),
    ("wobushiyaoshen", ["我不是药神"]),
    ("wujiandao", ["无间道"]),
    ("xijuzhiwang", ["喜剧之王"]),
    ("tianxiawuzhei", ["天下无贼"]),
    ("jiupinzhimaguan", ["九品芝麻官"]),
    ("qingshenshen", ["情深深雨濛濛"]),
    ("wangjiaokamen", ["旺角卡门"]),
    ("bianxingji", ["变形计"]),
    ("woaiwojia", ["我爱我家"]),
    ("langlangshan", ["浪浪山小妖怪"]),
    ("balala", ["巴啦啦小魔仙"]),
    ("yuanshen", ["原神"]),
    ("heishenhua", ["黑神话"]),
    ("aierdeng", ["艾尔登法环", "老头环"]),
    ("saibopengke", ["赛博朋克"]),
    ("pvz", ["植物大战僵尸"]),
    ("wangzhe", ["王者荣耀"]),
    ("lol", ["英雄联盟"]),
    ("csgo", ["CS:GO", "反恐精英"]),
    ("amongus", ["Among Us"]),
    ("yangle", ["羊了个羊"]),
    ("hechengxigua", ["合成大西瓜"]),
    ("lvxingqingwa", ["旅行青蛙"]),
    ("tanwanlanyue", ["贪玩蓝月"]),
    ("xiaoyouxi4399", ["4399"]),
    ("shimingzhaohuan", ["使命召唤"]),
    ("eva", ["新世纪福音战士", "EVA"]),
    ("skibidi", ["Skibidi"]),
    ("pepe", ["Pepe"]),
    ("doge", ["Doge"]),
    ("cheems", ["Cheems"]),
    ("niconico", ["NICONICO", "niconico"]),
    ("mabaoguo", ["马保国"]),
    ("dongyongge", ["冬泳怪鸽"]),
    ("guolaoshi", ["郭老师"]),
    ("dasima", ["大司马"]),
    ("sunxiaochuan", ["孙笑川", "抽象工作室"]),
    ("wangjingze", ["王境泽"]),
    ("fuyuanhui", ["傅园慧"]),
    ("wulantuya", ["乌兰图雅"]),
    ("jipai", ["鸡排主理人"]),
    ("fengjie", ["凤姐"]),
    ("furong", ["芙蓉姐姐"]),
    ("xilige", ["犀利哥"]),
    ("naicha", ["奶茶妹妹"]),
    ("tieba", ["贴吧"]),
    ("weibo", ["微博"]),
    ("douyin", ["抖音"]),
    ("kuaishou", ["快手"]),
    ("bilibili", ["B站", "B 站"]),
    ("xiaohongshu", ["小红书"]),
    ("zhihu", ["知乎"]),
    ("douban", ["豆瓣"]),
    ("wechat", ["微信"]),
    ("qq", ["QQ"]),
    ("tianya", ["天涯"]),
    ("maopu", ["猫扑"]),
    ("renren", ["人人网", "校内网"]),
    ("twitter", ["Twitter", "推特"]),
    ("reddit", ["Reddit"]),
    ("fourchan", ["4chan"]),
    ("tiktok", ["TikTok"]),
    ("twitch", ["Twitch"]),
    ("taobao", ["淘宝"]),
    ("duanshipin", ["短视频"]),
    ("zhibo", ["直播"]),
    ("chunwan", ["春晚"]),
    ("aoyunhui", ["奥运会"]),
    ("nba", ["NBA"]),
    ("shijiebei", ["世界杯"]),
    ("guozu", ["国足"]),
]


def pick(term: str, origin: str, meaning: str = "") -> str:
    text = f"{term} {meaning} {origin}".lower()
    for sid, keywords in RULES:
        for kw in keywords:
            if kw.lower() in text:
                return sid
    return "web"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(MEMES, encoding="utf-8") as f:
        doc = json.load(f)

    counts = Counter()
    for m in doc["items"]:
        m["source"] = pick(m["term"], m.get("origin", ""), m.get("meaning", ""))
        counts[m["source"]] += 1

    names = {s[0]: s[1] for s in SOURCE_LIST}
    print(f"共 {len(doc['items'])} 条，覆盖 {len(counts)} 个出处\n")
    for sid, n in counts.most_common():
        print(f"  {n:>3}  {names.get(sid, sid)}（{sid}）")
    missing = [s for s, _ in counts.items() if s not in names]
    if missing:
        sys.exit(f"未知出处 id：{missing}")

    if args.dry_run:
        print("\n[dry-run] 未写文件")
        return

    # 只保留被引用到的出处，未命中的实体仍留在 SOURCE_LIST 里备查
    sources = [
        {"id": i, "name": n, "type": t, "year": y}
        for i, n, t, y in SOURCE_LIST
        if counts.get(i)
    ]
    with open(SOURCES, "w", encoding="utf-8") as f:
        json.dump({"schema": 1, "items": sources}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(MEMES, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n已写入 {SOURCES} 与 {MEMES}")


if __name__ == "__main__":
    main()
