"""大模型审核：判断是不是真羊毛、打 0–5 分、重新归类、把标题改写成一句看得懂的中文。

用 Claude Haiku 5.5（官方 anthropic SDK）。没装 anthropic 或没有 ANTHROPIC_API_KEY 时整体跳过，
网页退回关键词规则分类。结论存在条目的 ai 字段里；改了提示词就把 PROMPT_VERSION 加一，旧结论会重新审核。
"""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Literal, Optional

from .taxonomy import CATEGORY_INFO, CIRCLES, REGIONS

try:
    import anthropic
    from pydantic import BaseModel
except ImportError:  # 本地只用标准库跑时没有这两个包
    anthropic = None

MODEL = "claude-haiku-5-5"
PRICE_IN, PRICE_OUT = 0.10, 0.50  # 美元 / 百万 token（提示词 ≤100K 时）
PROMPT_VERSION = 1
BATCH_SIZE = 20
MAX_ITEMS_PER_RUN = 600   # 单轮上限，防止异常情况下一次花太多
MAX_TRIES = 3             # 同一条连续失败几次后放弃，按规则分类展示
WORKERS = 4
WINDOW = 7 * 86400

_circle_name = {c["id"]: c["name"] for c in CIRCLES}
_CATEGORIES = "\n".join(
    f"- {cid}：{_circle_name[info['circle']]} / {info['name']}" for cid, info in CATEGORY_INFO.items()
)

SYSTEM = f"""你是「羊毛雷达」的审核编辑。读者是生活在中国大陆、香港、美国、新加坡的华人，只想看到真正值得花时间去薅的羊毛。
你会收到一批从线报站、论坛、优惠博客抓来的条目（JSON 数组），对每一条给出审核结论，输入里的每个 id 都要有结论。

## 打分 score（0–5）
- 5 大毛：价值高且门槛低，大多数人能参与。例：开户 / 办卡奖励几百元以上、免费领实物或年度会员、大额立减金、明显的价格 bug、大额免费 API / 云额度。
- 4 好毛：明确的福利，值得专门花几分钟去做。例：几元到几十元的立减金 / 红包 / 话费、付费游戏或 App 限免、开卡礼、积分转换加成、免费试用付费服务。
- 3 小毛：有实际好处，但价值一般或有门槛。例：小额随机红包、要先消费才返的优惠、只限部分地区 / 人群 / 被选中账号（targeted）的活动。
- 2 普通优惠：常规打折、普通商品的“好价”，没有特别之处。
- 1 基本没价值：广告软文、商家自卖自夸的推广、价格并不低、门槛高回报低。
- 0 不是羊毛：讨论、提问、求助、吐槽、闲聊、新闻资讯、评测攻略（不含具体可参与的活动）、收 / 出二手、已失效，或者信息太少看不出能做什么（例如标题只有“速度”、详情也没有内容）。

判断要点：
- 只根据输入内容判断，不要臆测没写出来的金额或条件。
- 商品降价帖默认不超过 2 分；只有 0 元购、一分钱、半价以下、史低、价格 bug 这类才给 3–4 分。
- 商家推广帖：送的东西确实免费且有价值（免费额度、免费试用）给 2–3 分，纯广告给 1 分。
- 经验分享、活动汇总帖：信息完整、能直接参与的，按活动本身打分。
- 线报黑话：速度 / 冲 = 赶紧去；有水、放水、大水 = 中奖率高或补货了；毛 = 福利（大毛 / 小毛）；xyk = 信用卡；数币 = 数字人民币；立减金 = 支付时自动抵扣的券；果 = 成功截图；r = 元；tlj = 淘礼金；车 / 上车 = 下单链接或拼单；dd = 顶帖。

## 改写标题 title
用中文写一句话，30 字以内，说清楚「在哪 / 做什么 / 得到什么」，让人扫一眼就能决定要不要点开。
- 例：“工行 App 搜「消费季」领立减金”、“Chase 新卡开卡奖励 $200”、“Epic 本周免费领《Quiztopia》”。
- 保留品牌、产品名和数字；英文条目翻译成中文，专有名词可保留英文。不要编造输入里没有的信息。

## 分类 cat（只能从下面选一个 id）
{_CATEGORIES}
选「对谁最有用」的那个：银行、支付、信用卡相关的归卡友理财，即使发生在电商平台上（例：“京东支付用建行卡立减”归 money-pay）。实在归不了类用 other。

## 地区 region
CN（中国大陆）、HK（香港）、US（美国）、SG（新加坡）、GLOBAL（全球都能用的线上服务，如 API 额度、Steam / Epic 游戏、App 限免）。
看活动在哪里能参与，而不是帖子在哪里发；src_region 是来源的默认地区，可作参考。

## value 与 reason
- value：主要好处的金额或数量，例如 “¥16”、“$200”、“S$480”、“60,000 里程”、“免费”、“5 折”；没有就填 null。
- reason：10 字左右，说明打分理由，例如 “低门槛立减金”、“普通降价”、“纯提问”。"""

if anthropic is not None:
    class Verdict(BaseModel):
        id: str
        score: Literal[0, 1, 2, 3, 4, 5]
        cat: Literal[tuple(CATEGORY_INFO)]
        region: Literal[tuple(r["id"] for r in REGIONS)]
        title: str
        value: Optional[str]
        reason: str

    class Review(BaseModel):
        items: List[Verdict]


def pending(state, now):
    """还没审核（或提示词版本变了）的近 7 天条目，新的优先。"""
    out = []
    for key, v in state["items"].items():
        ai = v.get("ai")
        if ai and ai.get("v") == PROMPT_VERSION:
            continue
        if v.get("ai_tries", 0) >= MAX_TRIES or max(v["ts"], v["seen"]) < now - WINDOW:
            continue
        out.append((key, v))
    out.sort(key=lambda kv: kv[1]["seen"], reverse=True)
    return out[:MAX_ITEMS_PER_RUN]


def payload(batch, srcmap):
    rows = []
    for key, v in batch:
        src = srcmap.get(v["src"], {})
        row = {"id": key, "title": v["title"], "detail": (v.get("summary") or "")[:240],
               "src": v["sub"], "src_region": src.get("region", "")}
        if v.get("heat"):
            row["replies"] = v["heat"]
        rows.append(row)
    return json.dumps(rows, ensure_ascii=False)


class _Abort(Exception):
    """密钥无效、额度用完这类错误，后面的批次也不用再试了。"""


def _call(client, batch, srcmap, stop):
    """审核一批，返回 ({id: Verdict}, 输入 token, 输出 token, 错误)。被安全策略拒答时拆半重试。"""
    if stop.is_set():
        return {}, 0, 0, "已中止"
    try:
        resp = client.messages.parse(
            model=MODEL,
            max_tokens=16000,  # 思考也计入 max_tokens，给足空间
            system=SYSTEM,
            output_config={"effort": "low"},
            output_format=Review,
            messages=[{"role": "user", "content": payload(batch, srcmap)}],
        )
    except anthropic.AuthenticationError as exc:
        stop.set()
        raise _Abort(f"密钥无效：{exc.message}") from exc
    except anthropic.PermissionDeniedError as exc:
        stop.set()
        raise _Abort(f"没有权限：{exc.message}") from exc
    except anthropic.RateLimitError as exc:  # SDK 已自动重试过
        stop.set()
        return {}, 0, 0, f"限流：{exc.message}"[:160]
    except anthropic.APIStatusError as exc:
        return {}, 0, 0, f"HTTP {exc.status_code}：{exc.message}"[:160]
    except anthropic.APIConnectionError as exc:
        return {}, 0, 0, f"网络错误：{exc}"[:160]

    tin, tout = resp.usage.input_tokens, resp.usage.output_tokens
    if resp.stop_reason == "refusal":
        if len(batch) == 1:
            return {}, tin, tout, "模型拒绝审核"
        mid = len(batch) // 2
        a = _call(client, batch[:mid], srcmap, stop)
        b = _call(client, batch[mid:], srcmap, stop)
        return {**a[0], **b[0]}, tin + a[1] + b[1], tout + a[2] + b[2], a[3] or b[3]
    parsed = resp.parsed_output
    if parsed is None:
        return {}, tin, tout, f"没有拿到结构化结果（stop_reason={resp.stop_reason}）"
    return {vd.id: vd for vd in parsed.items}, tin, tout, None


def apply(batch, verdicts, now):
    done = 0
    for key, v in batch:
        vd = verdicts.get(key)
        if vd is None:
            v["ai_tries"] = v.get("ai_tries", 0) + 1
            continue
        v["ai"] = {
            "v": PROMPT_VERSION, "score": vd.score, "cat": vd.cat, "region": vd.region,
            "title": vd.title.strip()[:60], "value": (vd.value or "").strip()[:24] or None,
            "reason": vd.reason.strip()[:40], "at": now,
        }
        v.pop("ai_tries", None)
        done += 1
    return done


def review(state, sources, now, log=print):
    """审核待审条目，结果写回 state；返回本轮统计（也存到 state["llm"]）。"""
    info = {"model": MODEL, "checked": now, "enabled": False, "reviewed": 0, "failed": 0,
            "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
    if anthropic is None:
        info["error"] = "未安装 anthropic 包，使用关键词规则"
    elif not os.environ.get("ANTHROPIC_API_KEY"):
        info["error"] = "未配置 ANTHROPIC_API_KEY，使用关键词规则"
    if info.get("error"):
        state["llm"] = info
        return info

    info["enabled"] = True
    client = anthropic.Anthropic(max_retries=3, timeout=180)
    srcmap = {s["id"]: s for s in sources}
    todo = pending(state, now)
    batches = [todo[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    stop = threading.Event()
    errors = []

    def run(batch):
        try:
            return _call(client, batch, srcmap, stop)
        except _Abort as exc:
            return {}, 0, 0, str(exc)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for batch, (verdicts, tin, tout, err) in zip(batches, pool.map(run, batches)):
            done = apply(batch, verdicts, now)
            info["reviewed"] += done
            info["failed"] += len(batch) - done
            info["tokens_in"] += tin
            info["tokens_out"] += tout
            if err and err not in errors:
                errors.append(err)
    info["cost"] = round(info["tokens_in"] * PRICE_IN / 1e6 + info["tokens_out"] * PRICE_OUT / 1e6, 4)
    info["pending"] = len(pending(state, now))
    if errors:
        info["error"] = "；".join(errors)[:300]
    state["llm"] = info
    log(f"  🤖 AI 审核：{info['reviewed']} 条，失败 {info['failed']}，token {info['tokens_in']}/{info['tokens_out']}，"
        f"约 ${info['cost']}" + (f"，错误：{info['error']}" if errors else ""))
    return info
