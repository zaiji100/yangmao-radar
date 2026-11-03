#!/usr/bin/env python3
"""羊毛雷达：抓取 → 筛选 → AI 审核 → 生成网页。

抓取只依赖标准库；AI 审核需要 anthropic 包和 ANTHROPIC_API_KEY，缺了就退回关键词规则。

  python3 run.py                     抓一轮，更新 data/state.json 和 site/data.js
  python3 run.py --only doc,v2ex-free  只抓指定来源（调试用）
  python3 run.py --rebuild           不抓取，只按当前分类规则重新导出网页数据
  python3 run.py --review            不抓取，只让 AI 审核待审条目并导出（需要 ANTHROPIC_API_KEY）
  python3 run.py serve               本地常驻：每 30 分钟抓一轮，同时在 http://127.0.0.1:8000 提供网页
"""

import argparse
import functools
import http.server
import threading
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from radar.build import export
from radar.classify import is_deal
from radar.fetchers import fetch_source
from radar.llm import review
from radar.sources import SOURCES
from radar.store import ingest, load_state, prune, save_state

BASE = Path(__file__).resolve().parent
STATE_FILE = BASE / "data" / "state.json"
SITE_DIR = BASE / "site"
CST = timezone(timedelta(hours=8))
# 同一站点的请求串行并间隔，避免触发限流；Reddit 对未登录请求限得很紧
SAME_HOST_GAP = 1.5
HOST_GAP = {"www.reddit.com": 10}


def log(msg):
    print(f"{datetime.now(CST):%m-%d %H:%M:%S} {msg}", flush=True)


def fetch_group(group):
    results = {}
    for i, src in enumerate(group):
        if i:
            time.sleep(HOST_GAP.get(urlparse(src["url"]).hostname, SAME_HOST_GAP))
        try:
            results[src["id"]] = (fetch_source(src), None)
        except Exception as exc:  # 单个源失败不影响其他源
            results[src["id"]] = (None, f"{type(exc).__name__}: {exc}"[:200])
    return results


def scan(only=None):
    sources = [s for s in SOURCES if not only or s["id"] in only]
    groups = defaultdict(list)
    for s in sources:
        groups[urlparse(s["url"]).hostname].append(s)
    started = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for part in pool.map(fetch_group, groups.values()):
            results.update(part)

    state = load_state(STATE_FILE)
    now = int(time.time())
    total_new = 0
    for src in sources:
        entries, error = results[src["id"]]
        prev = state["sources"].get(src["id"], {})
        if error:
            state["sources"][src["id"]] = {**prev, "ok": False, "checked": now, "error": error}
            log(f"  ✗ {src['name']}: {error}")
            continue
        deals = [e for e in entries if is_deal(e, src)]
        new = ingest(state, src, deals, now)
        total_new += new
        state["sources"][src["id"]] = {
            "ok": True, "checked": now, "last_ok": now, "fetched": len(entries), "matched": len(deals), "new": new,
        }
        log(f"  ✓ {src['name']}: 抓到 {len(entries)}，羊毛 {len(deals)}，新增 {new}")
    prune(state, now)
    ai = review(state, SOURCES, now, log=log)
    run_info = {"at": now, "new": total_new, "secs": round(time.time() - started)}
    if ai.get("enabled"):
        run_info.update(ai_reviewed=ai["reviewed"], ai_cost=ai["cost"])
    state["runs"] = (state.get("runs", []) + [run_info])[-200:]
    save_state(STATE_FILE, state)
    shown = export(state, SOURCES, SITE_DIR, now)
    ok = sum(1 for s in SOURCES if state["sources"].get(s["id"], {}).get("ok"))
    log(f"完成：新增 {total_new} 条，网页展示近 7 天 {shown} 条，信息源 {ok}/{len(SOURCES)} 正常")


def rebuild(with_review=False):
    state = load_state(STATE_FILE)
    now = int(time.time())
    if with_review:
        review(state, SOURCES, now, log=log)
        save_state(STATE_FILE, state)
    shown = export(state, SOURCES, SITE_DIR, now)
    log(f"已重新导出：近 7 天 {shown} 条")


def serve(port, interval):
    def loop():
        while True:
            try:
                log("开始抓取")
                scan()
            except Exception:
                traceback.print_exc()
            time.sleep(interval * 60)

    threading.Thread(target=loop, daemon=True).start()
    handler = functools.partial(QuietHandler, directory=str(SITE_DIR))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        log(f"网页：http://127.0.0.1:{port}  （每 {interval} 分钟抓一轮，Ctrl+C 退出）")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            log("已退出")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description="羊毛雷达")
    ap.add_argument("command", nargs="?", default="scan", choices=["scan", "serve"])
    ap.add_argument("--only", help="只抓这些来源 id，逗号分隔")
    ap.add_argument("--rebuild", action="store_true", help="不抓取，只重新导出网页数据")
    ap.add_argument("--review", action="store_true", help="不抓取，只做 AI 审核并导出")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--interval", type=int, default=30, help="serve 模式的抓取间隔（分钟）")
    args = ap.parse_args()
    if args.rebuild or args.review:
        rebuild(with_review=args.review)
    elif args.command == "serve":
        serve(args.port, args.interval)
    else:
        scan(set(args.only.split(",")) if args.only else None)


if __name__ == "__main__":
    main()
