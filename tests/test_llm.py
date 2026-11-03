"""AI 审核模块的离线测试：不调用真实接口，用假的模型返回验证挑选、写回、导出和拒答拆分。"""

import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from radar import llm
from radar.build import export
from radar.sources import SOURCES

NOW = 1_800_000_000


def make_item(title, src="xb-zuanke", ts=NOW - 600, **extra):
    return {"title": title, "url": f"https://x/{title}", "src": src, "sub": "线报酷 · 赚客吧", "summary": "",
            "hint": None, "tags": [], "heat": 3, "value": None, "ts": ts, "seen": ts, **extra}


def verdict(id_, score, cat="money-pay", region="CN", title="改写后的标题", value="¥8", reason="低门槛"):
    return SimpleNamespace(id=id_, score=score, cat=cat, region=region, title=title, value=value, reason=reason)


class TestPendingAndApply(unittest.TestCase):
    def test_pending_skips_reviewed_old_and_exhausted(self):
        state = {"items": {
            "a": make_item("新条目"),
            "b": make_item("已审", ai={"v": llm.PROMPT_VERSION, "score": 4}),
            "c": make_item("旧版本审过", ai={"v": llm.PROMPT_VERSION - 1, "score": 4}),
            "d": make_item("过期", ts=NOW - 8 * 86400),
            "e": make_item("失败太多次", ai_tries=llm.MAX_TRIES),
        }}
        self.assertEqual(sorted(k for k, _ in llm.pending(state, NOW)), ["a", "c"])

    def test_apply_writes_verdict_and_counts_missing(self):
        batch = [("a", make_item("建行8元毛")), ("b", make_item("速度"))]
        done = llm.apply(batch, {"a": verdict("a", 4)}, NOW)
        self.assertEqual(done, 1)
        self.assertEqual(batch[0][1]["ai"]["score"], 4)
        self.assertEqual(batch[1][1]["ai_tries"], 1)

    def test_payload_contains_ids_and_source_region(self):
        rows = json.loads(llm.payload([("a", make_item("Synchrony 2% Card", src="doc"))], {s["id"]: s for s in SOURCES}))
        self.assertEqual(rows[0]["id"], "a")
        self.assertEqual(rows[0]["src_region"], "US")


class TestExport(unittest.TestCase):
    def test_ai_verdict_drives_display_and_low_scores_are_dropped(self):
        state = {"items": {
            "good": make_item("工行app搜消费季，速度", ai={"v": 1, "score": 4, "cat": "money-pay", "region": "CN",
                                                     "title": "工行 App 搜「消费季」领立减金", "value": None,
                                                     "reason": "低门槛立减金"}),
            "junk": make_item("闲鱼真神奇，二手衣服一大把人要", ai={"v": 1, "score": 0, "cat": "other", "region": "CN",
                                                          "title": "闲聊", "value": None, "reason": "闲聊"}),
            "todo": make_item("摇一摇有水 快"),
        }, "sources": {}, "runs": []}
        with tempfile.TemporaryDirectory() as tmp:
            export(state, SOURCES, Path(tmp), NOW)
            raw = (Path(tmp) / "data.js").read_text(encoding="utf-8")
        data = json.loads(raw[len("window.RADAR="):raw.rindex(";")])
        rows = {r["id"]: r for r in data["items"]}
        self.assertNotIn("junk", rows)
        self.assertEqual(rows["good"]["t"], "工行 App 搜「消费季」领立减金")
        self.assertEqual(rows["good"]["ot"], "工行app搜消费季，速度")
        self.assertEqual(rows["good"]["q"], 4)
        self.assertIsNone(rows["todo"]["q"])  # 待审条目按规则展示


@unittest.skipUnless(llm.anthropic, "需要 anthropic 包")
class TestCallRefusalSplit(unittest.TestCase):
    def test_refused_batch_is_split_until_single_item(self):
        class FakeMessages:
            def parse(self, **kw):
                ids = [r["id"] for r in json.loads(kw["messages"][0]["content"])]
                usage = SimpleNamespace(input_tokens=10, output_tokens=5)
                if "bad" in ids:
                    return SimpleNamespace(stop_reason="refusal", usage=usage, parsed_output=None)
                items = [verdict(i, 3) for i in ids]
                return SimpleNamespace(stop_reason="end_turn", usage=usage, parsed_output=SimpleNamespace(items=items))

        client = SimpleNamespace(messages=FakeMessages())
        batch = [(k, make_item(k)) for k in ("a", "bad", "c", "d")]
        verdicts, tin, tout, err = llm._call(client, batch, {}, threading.Event())
        self.assertEqual(sorted(verdicts), ["a", "c", "d"])
        self.assertEqual(err, "模型拒绝审核")
        self.assertGreater(tin, 10)


if __name__ == "__main__":
    unittest.main()
