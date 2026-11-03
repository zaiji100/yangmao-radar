"""抓取各类信息源，统一解析成 entry 字典。

entry 字段：title、url、published（aware datetime 或 None）、summary、heat（评论 / 回复 / 点数，可空）、
sub（来源下的子频道名，可空）、hint（规则没命中时的默认细分类，可空）、tags（来源自带分类，可空）。
"""

import html
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .taxonomy import XIANBAO_CHANNEL_HINT, XIANBAO_TAG_HINT

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
MAX_BYTES = 8 * 1024 * 1024


def curl_get(url, timeout, retries=1):
    """部分站点（Cloudflare）按 TLS 指纹拦截 Python，curl 可以正常访问。"""
    for attempt in range(retries + 1):
        proc = subprocess.run(
            ["curl", "-sSL", "--compressed", "-m", str(timeout), "-A", UA, "-w", "\n%{http_code}", url],
            capture_output=True, timeout=timeout + 5,
        )
        body, _, code = proc.stdout.rpartition(b"\n")
        if proc.returncode == 0 and code == b"200":
            return body[:MAX_BYTES]
        if code == b"429" and attempt < retries:  # 共享出口 IP（如 GitHub Actions）容易撞限流，等一下再试
            time.sleep(8)
            continue
        raise RuntimeError(f"curl 回退失败：HTTP {code.decode() or '?'} {proc.stderr.decode()[:80]}".strip())
    raise RuntimeError("unreachable")


def http_get(url, timeout=20, retries=1):
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(MAX_BYTES)
        except urllib.error.HTTPError as exc:
            if exc.code == 403 and shutil.which("curl"):
                return curl_get(url, timeout)
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(4 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            # python.org 安装的 Python 在 Mac 上常缺根证书，交给用系统证书的 curl
            if "CERTIFICATE_VERIFY_FAILED" in str(exc) and shutil.which("curl"):
                return curl_get(url, timeout)
            if attempt < retries:
                time.sleep(2)
                continue
            raise
    raise RuntimeError("unreachable")


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def parse_time(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    text = str(value).strip()
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def entry(title, url, published=None, summary="", heat=None, sub=None, hint=None, tags=None):
    return {
        "title": clean(title),
        "url": (url or "").strip(),
        "published": published,
        "summary": clean(summary)[:400],
        "heat": heat,
        "sub": sub,
        "hint": hint,
        "tags": tags or [],
    }


# ---------------- RSS / Atom ----------------

_BAD_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _feed_xml(raw):
    text = raw.decode("utf-8", "replace")
    root = ET.fromstring(_BAD_XML_CHARS.sub("", text))
    out = []
    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        rec, tags = {}, []
        for child in node:
            name = _local(child.tag)
            if name == "link":
                href = child.get("href")
                if href and child.get("rel", "alternate") != "alternate":
                    continue
                rec.setdefault("link", href or (child.text or "").strip())
            elif name in ("title", "summary", "description", "content", "encoded"):
                rec.setdefault(name, child.text or "")
            elif name in ("pubDate", "published", "updated", "date"):
                rec.setdefault("time", child.text)
            elif name == "category":
                tags.append((child.text or child.get("term") or "").strip())
        out.append((rec, tags))
    return out


_ITEM_RE = re.compile(r"<(item|entry)\b.*?</\1>", re.S)


def _field(block, *names):
    for name in names:
        m = re.search(rf"<{name}\b[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{name}>", block, re.S)
        if m:
            return m.group(1)
    return ""


def _feed_regex(raw):
    """XML 不合规（未定义实体等）时的兜底解析。"""
    text = raw.decode("utf-8", "replace")
    out = []
    for m in _ITEM_RE.finditer(text):
        block = m.group(0)
        link = _field(block, "link")
        if not link:
            href = re.search(r'<link[^>]+href="([^"]+)"', block)
            link = href.group(1) if href else ""
        rec = {
            "title": _field(block, "title"),
            "link": html.unescape(link),
            "summary": _field(block, "description", "summary", "content"),
            "time": _field(block, "pubDate", "published", "updated", "dc:date"),
        }
        tags = [clean(t) for t in re.findall(r"<category[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</category>", block, re.S)]
        out.append((rec, tags))
    return out


def parse_feed(raw, src):
    try:
        records = _feed_xml(raw)
    except ET.ParseError:
        records = _feed_regex(raw)
    out = []
    for rec, tags in records:
        summary = rec.get("summary") or rec.get("description") or rec.get("content") or rec.get("encoded")
        out.append(entry(rec.get("title"), rec.get("link"), parse_time(rec.get("time")), summary, tags=tags))
    return out


# ---------------- JSON API ----------------

def parse_v2ex(raw, src):
    return [
        entry(t.get("title"), t.get("url"), parse_time(t.get("created")), t.get("content", ""), heat=t.get("replies"))
        for t in json.loads(raw)
    ]


def parse_xianbao(raw, src):
    data = json.loads(raw).get("data") or {}
    allow = set(src.get("xb_tags") or [])
    out = []
    for it in data.get("items", []):
        parts = ((it.get("category") or {}).get("name") or "").split("-")
        channel, tag = parts[0], (parts[1] if len(parts) > 1 else "")
        if allow and tag not in allow:
            continue
        out.append(entry(
            it.get("title"), it.get("url"), parse_time(it.get("published_at")), it.get("content", ""),
            heat=it.get("comments"), sub=f"线报酷 · {channel}" if channel else None,
            hint=XIANBAO_TAG_HINT.get(tag) or XIANBAO_CHANNEL_HINT.get(channel),
        ))
    return out


def parse_gamerpower(raw, src):
    out = []
    for g in json.loads(raw):
        if g.get("status") and g["status"] != "Active":
            continue
        worth = g.get("worth") if g.get("worth") not in (None, "", "N/A") else None
        end = g.get("end_date") if g.get("end_date") not in (None, "", "N/A") else None
        summary = f"平台：{g.get('platforms', '')}" + (f"；截止 {end}" if end else "")
        e = entry(g.get("title"), g.get("gamerpower_url") or g.get("open_giveaway_url"),
                  parse_time(g.get("published_date")), summary, heat=g.get("users"))
        e["value"] = f"原价 {worth}" if worth else None
        out.append(e)
    return out


def parse_openrouter(raw, src):
    out = []
    for m in json.loads(raw).get("data", []):
        mid = m.get("id", "")
        pricing = m.get("pricing") or {}
        free = mid.endswith(":free") or (pricing.get("prompt") == "0" and pricing.get("completion") == "0")
        if not free or mid.startswith("openrouter/"):
            continue
        ctx = m.get("context_length")
        summary = (f"上下文 {ctx // 1000}K；" if ctx else "") + (m.get("description") or "")
        e = entry(f"OpenRouter 新增免费模型：{m.get('name') or mid}", f"https://openrouter.ai/{mid}",
                  parse_time(m.get("created")), summary)
        e["value"] = "免费"
        out.append(e)
    return out


# 只关心目录内容的变化（新增 / 下架 / 数据同步），文档、测试、重构类提交跳过
_USEFUL_COMMIT = re.compile(
    r"^(?:data sync|add(?:ed)? (?!the |a |missing)|remov(?:e|ed) |deprecat|new (?:provider|model))", re.I)


def parse_github(raw, src):
    repo = re.search(r"repos/([^/]+/[^/]+)/", src["url"]).group(1)
    out = []
    for c in json.loads(raw):
        lines = [ln.strip() for ln in (c.get("commit", {}).get("message") or "").splitlines() if ln.strip()]
        if not lines:
            continue
        msg = lines[0]
        if msg.lower().startswith("merge pull request") and len(lines) > 1:
            msg = lines[1]
        if not _USEFUL_COMMIT.search(msg):
            continue
        date = (c.get("commit", {}).get("committer") or {}).get("date")
        out.append(entry(f"免费 LLM API 目录更新：{msg}", c.get("html_url") or f"https://github.com/{repo}",
                         parse_time(date), f"来自 {repo}"))
    return out


def parse_hn(raw, src):
    out = []
    for h in json.loads(raw).get("hits", []):
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        out.append(entry(h.get("title"), url, parse_time(h.get("created_at_i")),
                         f"HN {h.get('points', 0)} 分 · {h.get('num_comments') or 0} 评论", heat=h.get("points")))
    return out


PARSERS = {
    "feed": parse_feed,
    "v2ex": parse_v2ex,
    "xianbao": parse_xianbao,
    "gamerpower": parse_gamerpower,
    "openrouter": parse_openrouter,
    "github": parse_github,
    "hn": parse_hn,
}


def fetch_source(src):
    raw = http_get(src["url"])
    entries = PARSERS[src["kind"]](raw, src)
    if src["kind"] == "feed" and not entries and not re.search(rb"<(?:rss|feed|rdf:RDF)\b", raw[:2000]):
        raise RuntimeError("返回的不是 RSS/Atom，可能被反爬拦截")
    return entries[: src.get("limit", 300)]
