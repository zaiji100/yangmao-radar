"""把状态导出成网页读取的 site/data.js（近 7 天、已分类）。

有 AI 审核结论的条目用 AI 的分类 / 标题 / 分数，低于 MIN_SCORE 的（不是羊毛、没价值）不导出；
还没审核到的退回关键词规则，网页上标为「待审」。
"""

import json
from pathlib import Path

from .classify import classify, extract_value, is_deal
from .taxonomy import CATEGORY_INFO, CIRCLES, REGIONS, SCENES

WINDOW = 7 * 86400
MIN_SCORE = 2
REGION_IDS = {r["id"] for r in REGIONS}


def export(state, sources, out_dir: Path, now):
    srcmap = {s["id"]: s for s in sources}
    items = []
    for key, v in state["items"].items():
        src = srcmap.get(v["src"])
        if src is None or v["ts"] < now - WINDOW:
            continue
        ai = v.get("ai")
        if ai and ai.get("cat") in CATEGORY_INFO and ai.get("region") in REGION_IDS:
            if ai["score"] < MIN_SCORE:
                continue
            c = {"cat": ai["cat"], "circle": CATEGORY_INFO[ai["cat"]]["circle"], "region": ai["region"],
                 "value": ai.get("value") or v.get("value") or extract_value(v["title"])}
            title, score, why = ai["title"] or v["title"], ai["score"], ai.get("reason")
        else:
            e = {k: v.get(k) for k in ("title", "url", "summary", "hint", "tags", "value")}
            if not is_deal(e, src):  # 规则收紧后，历史条目也按新规则过滤
                continue
            c = classify(e, src)
            title, score, why = v["title"], None, None
        row = {
            "id": key,
            "t": title,
            "u": v["url"],
            "s": v["src"],
            "sn": v["sub"],
            "ts": v["ts"],
            "seen": v["seen"],
            "c": c["circle"],
            "k": c["cat"],
            "r": c["region"],
            "v": c["value"],
            "q": score,
            "h": v.get("heat"),
            "a": v.get("also") or [],
            "d": (v.get("summary") or "")[:140],
        }
        if title != v["title"]:
            row["ot"] = v["title"]
        if why:
            row["why"] = why
        items.append(row)
    items.sort(key=lambda x: (x["ts"], x["seen"]), reverse=True)

    runs = state.get("runs", [])
    status = state.get("sources", {})
    llm = dict(state.get("llm") or {})
    llm["cost_24h"] = round(sum(r.get("ai_cost", 0) for r in runs if r["at"] >= now - 86400), 4)
    payload = {
        "generated": now,
        "scenes": SCENES,
        "circles": CIRCLES,
        "categories": list(CATEGORY_INFO.values()),
        "regions": REGIONS,
        "llm": llm,
        "sources": [
            {
                "id": s["id"], "name": s["name"], "region": s["region"], "url": s["url"],
                "circles": s.get("circles", []), **status.get(s["id"], {}),
            }
            for s in sources
        ],
        "runs": runs[-48:],
        "items": items,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    tmp = out_dir / "data.js.tmp"
    tmp.write_text(f"window.RADAR={body};\n", encoding="utf-8")
    tmp.replace(out_dir / "data.js")
    return len(items)
