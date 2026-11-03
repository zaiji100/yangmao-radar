"""判断一条信息是不是羊毛，并归到 圈子 / 细分类 / 地区，顺便提取金额。"""

from .taxonomy import (
    CATEGORY_INFO, GLOBAL_CATS, GLOBAL_CATS_FROM_LOCAL, NOISE, REGION_BRANDS, REGION_CN, REGION_EXPLICIT, RULES,
    SIGNAL, VALUE_PATTERNS,
)


def is_deal(e, src):
    title = e["title"]
    if not title or not e["url"]:
        return False
    drop = set(src.get("drop_tags") or [])
    if drop and drop.intersection(e.get("tags") or []):
        return False
    if src["kind"] in ("openrouter", "github", "gamerpower"):
        return True
    if NOISE.search(title):
        return False
    mode = src.get("mode", "strict")
    if mode == "pass":
        return True
    return bool(SIGNAL[mode].search(title))


def match_category(text):
    for cid, _circle, _name, pat in RULES:
        if pat.search(text):
            return cid
    return None


def detect_region(text, cat, src):
    origin = src.get("region", "CN")
    for code in ("HK", "SG", "US"):
        if REGION_EXPLICIT[code].search(text):
            return code
    if origin in ("US", "SG"):
        return "GLOBAL" if cat in GLOBAL_CATS_FROM_LOCAL else origin
    for code in ("HK", "SG", "US"):
        if REGION_BRANDS[code].search(text):
            return code
    if cat in GLOBAL_CATS:
        return "GLOBAL"
    if REGION_CN.search(text):
        return "CN"
    return origin


def extract_value(text):
    best = None
    for pat in VALUE_PATTERNS:
        m = pat.search(text)
        if m and (best is None or m.start() < best.start()):
            best = m
    if not best:
        return None
    value = best.group(0).strip()
    return value[:-1] + "元" if value.endswith("r") else value


def classify(e, src):
    # 只看标题：摘要（尤其论坛正文）噪音太大，拿来匹配反而误判，没命中就用来源提示兜底
    title = e["title"]
    cat = match_category(title) or e.get("hint") or src.get("hint") or "other"
    return {
        "cat": cat,
        "circle": CATEGORY_INFO[cat]["circle"],
        "region": detect_region(title, cat, src),
        "value": e.get("value") or extract_value(title),
    }
