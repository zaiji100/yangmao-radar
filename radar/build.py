"""把状态导出成网页读取的 site/data.js（近 7 天、已分类）。"""

import json
from pathlib import Path

from .classify import classify, is_deal
from .taxonomy import CATEGORY_INFO, CIRCLES, REGIONS, SCENES

WINDOW = 7 * 86400


def export(state, sources, out_dir: Path, now):
    srcmap = {s["id"]: s for s in sources}
    items = []
    for key, v in state["items"].items():
        src = srcmap.get(v["src"])
        if src is None or v["ts"] < now - WINDOW:
            continue
        e = {k: v.get(k) for k in ("title", "url", "summary", "hint", "tags", "value")}
        if not is_deal(e, src):  # 规则收紧后，历史条目也按新规则过滤
            continue
        c = classify(e, src)
        items.append({
            "id": key,
            "t": v["title"],
            "u": v["url"],
            "s": v["src"],
            "sn": v["sub"],
            "ts": v["ts"],
            "seen": v["seen"],
            "c": c["circle"],
            "k": c["cat"],
            "r": c["region"],
            "v": c["value"],
            "h": v.get("heat"),
            "a": v.get("also") or [],
            "d": (v.get("summary") or "")[:140],
        })
    items.sort(key=lambda x: (x["ts"], x["seen"]), reverse=True)

    status = state.get("sources", {})
    payload = {
        "generated": now,
        "scenes": SCENES,
        "circles": CIRCLES,
        "categories": list(CATEGORY_INFO.values()),
        "regions": REGIONS,
        "sources": [
            {
                "id": s["id"], "name": s["name"], "region": s["region"], "url": s["url"],
                "circles": s.get("circles", []), **status.get(s["id"], {}),
            }
            for s in sources
        ],
        "runs": state.get("runs", [])[-48:],
        "items": items,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    tmp = out_dir / "data.js.tmp"
    tmp.write_text(f"window.RADAR={body};\n", encoding="utf-8")
    tmp.replace(out_dir / "data.js")
    return len(items)
