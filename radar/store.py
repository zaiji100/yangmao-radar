"""状态文件：收录的条目、各信息源健康度、运行记录。

条目只存原始字段，圈子 / 细分类 / 地区在导出时现算，改了分类规则重新导出就能对历史数据生效。
"""

import hashlib
import json
import re
from pathlib import Path

KEEP_DAYS = 10          # 状态里保留多少天（页面只展示近 7 天）
DEDUP_WINDOW = 3 * 86400  # 不同来源标题相同、3 天内出现的算同一条
FUTURE_SLACK = 3600


def load_state(path: Path):
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("version") == 2:
            return state
    return {"version": 2, "items": {}, "sources": {}, "runs": []}


def save_state(path: Path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(path)


def norm_title(title):
    return re.sub(r"[\W_]+", "", title.lower())[:48]


def item_id(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def ingest(state, src, entries, now):
    """把一个来源本轮的 entries 并入状态，返回新增条数。entries 已经过羊毛筛选。"""
    items = state["items"]
    recent = {
        norm_title(v["title"]): k for k, v in items.items() if now - v["seen"] <= DEDUP_WINDOW
    }
    name = src["name"]
    new = 0
    for e in entries:
        key = item_id(e["url"])
        if key in items:
            if e.get("heat") is not None:
                items[key]["heat"] = e["heat"]
            continue
        ts = int(e["published"].timestamp()) if e.get("published") else now
        if ts > now + FUTURE_SLACK:
            ts = now
        if ts < now - KEEP_DAYS * 86400:
            continue
        sub = e.get("sub") or name
        dup = recent.get(norm_title(e["title"]))
        if dup:
            also = items[dup].setdefault("also", [])
            if sub != items[dup]["sub"] and sub not in also and len(also) < 5:
                also.append(sub)
            continue
        items[key] = {
            "title": e["title"],
            "url": e["url"],
            "src": src["id"],
            "sub": sub,
            "summary": e.get("summary", "")[:200],
            "hint": e.get("hint"),
            "tags": e.get("tags") or [],
            "heat": e.get("heat"),
            "value": e.get("value"),
            "ts": ts,
            "seen": now,
        }
        recent[norm_title(e["title"])] = key
        new += 1
    return new


def prune(state, now):
    cutoff = now - KEEP_DAYS * 86400
    items = state["items"]
    for key in [k for k, v in items.items() if max(v["ts"], v["seen"]) < cutoff]:
        del items[key]
