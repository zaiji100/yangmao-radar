(() => {
  "use strict";
  const D = window.RADAR;
  const $ = (id) => document.getElementById(id);
  if (!D) {
    $("content").innerHTML = '<div class="list empty">还没有数据：先在项目目录运行 <code>python3 run.py</code></div>';
    return;
  }

  // ---------- 基础数据 ----------
  const OFFSET = 8 * 3600 * 1000; // 「今日」按北京时间 / 新加坡时间（UTC+8）切日
  const dayKey = (ts) => new Date(ts * 1000 + OFFSET).toISOString().slice(0, 10);
  const HUE = { ai: 262, dev: 218, office: 198, student: 180, earn: 42, money: 26, shop: 338, food: 8, travel: 192,
    commute: 158, telecom: 286, fun: 305, kids: 322, pets: 92, home: 138, other: 215 };
  const circleMap = Object.fromEntries(D.circles.map((c) => [c.id, c]));
  const catMap = Object.fromEntries(D.categories.map((c) => [c.id, c]));
  const regionMap = Object.fromEntries(D.regions.map((r) => [r.id, r]));
  const srcMap = Object.fromEntries(D.sources.map((s) => [s.id, s]));
  const REGION_FILTERS = [
    { id: "", name: "全部" },
    { id: "CN", name: "🇨🇳 中国", match: ["CN", "HK"] },
    { id: "US", name: "🇺🇸 美国", match: ["US"] },
    { id: "SG", name: "🇸🇬 新加坡", match: ["SG"] },
    { id: "GLOBAL", name: "🌐 全球通用", match: ["GLOBAL"] },
  ];
  const items = D.items.map((it) => ({
    ...it,
    day: dayKey(it.ts),
    scene: (circleMap[it.c] || {}).scene || "life",
    text: `${it.t} ${it.sn} ${(catMap[it.k] || {}).name || ""} ${(circleMap[it.c] || {}).name || ""}`.toLowerCase(),
    score: (it.h || 0) + (it.a ? it.a.length * 15 : 0),
  }));

  // ---------- 状态（同步到地址栏，方便收藏 / 分享） ----------
  const DEFAULT = { t: "today", sc: "", r: "", c: "", k: "", q: "", s: "new" };
  const S = { ...DEFAULT };
  let limit = 150;
  function readHash() {
    const p = new URLSearchParams(location.hash.slice(1));
    for (const key of Object.keys(DEFAULT)) S[key] = p.get(key) ?? DEFAULT[key];
    $("q").value = S.q;
  }
  function writeHash() {
    const p = new URLSearchParams();
    for (const [key, val] of Object.entries(S)) if (val && val !== DEFAULT[key]) p.set(key, val);
    const h = p.toString();
    history.replaceState(null, "", h ? `#${h}` : location.pathname + location.search);
  }
  function set(patch) {
    Object.assign(S, patch);
    limit = 150;
    writeHash();
    render();
  }

  // ---------- 筛选 ----------
  const today = () => dayKey(Date.now() / 1000);
  const inTime = (it, t) => t === "7d" || it.day === today();
  const inRegion = (it, r) => !r || REGION_FILTERS.find((f) => f.id === r).match.includes(it.r);
  const inQuery = (it, q) => !q || q.toLowerCase().split(/\s+/).filter(Boolean).every((w) => it.text.includes(w));
  const base = (o = {}) => {
    const f = { ...S, ...o };
    return items.filter((it) => inTime(it, f.t) && (!f.sc || it.scene === f.sc) && inRegion(it, f.r) && inQuery(it, f.q));
  };
  const countBy = (list, key) => list.reduce((m, it) => ((m[it[key]] = (m[it[key]] || 0) + 1), m), {});
  const sorted = (list) =>
    S.s === "hot" ? [...list].sort((a, b) => b.score - a.score || b.ts - a.ts) : list; // 原始数据已按时间倒序

  // ---------- 渲染工具 ----------
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const pad = (n) => String(n).padStart(2, "0");
  const cst = (ts) => new Date(ts * 1000 + OFFSET);
  const hm = (ts) => { const d = cst(ts); return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`; };
  const md = (ts) => { const d = cst(ts); return `${d.getUTCMonth() + 1}月${d.getUTCDate()}日`; };
  function ago(ts) {
    const s = Date.now() / 1000 - ts;
    if (s < 60) return "刚刚";
    if (s < 3600) return `${Math.floor(s / 60)} 分钟前`;
    if (s < 86400) return `${Math.floor(s / 3600)} 小时前`;
    return `${md(ts)} ${hm(ts)}`;
  }
  const WEEK = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  function dayLabel(day) {
    const t = today();
    const y = dayKey(Date.now() / 1000 - 86400);
    const d = new Date(`${day}T00:00:00Z`);
    const base = `${d.getUTCMonth() + 1}月${d.getUTCDate()}日 ${WEEK[d.getUTCDay()]}`;
    return day === t ? `今天 · ${base}` : day === y ? `昨天 · ${base}` : base;
  }

  function itemHTML(it, compact) {
    const cat = catMap[it.k] || catMap.other;
    const reg = regionMap[it.r] || { flag: "🌐", name: "全球" };
    const fresh = Date.now() / 1000 - it.seen < 2 * 3600;
    const meta = [
      `<button class="tag" style="--h:${HUE[it.c] ?? 215}" data-c="${esc(it.c)}" data-k="${esc(it.k)}">${esc(cat.name)}</button>`,
      `<span>${esc(it.sn)}</span>`,
      `<span title="${esc(md(it.ts) + " " + hm(it.ts))}">${compact || S.t === "today" ? ago(it.ts) : hm(it.ts)}</span>`,
      it.h ? `<span title="评论 / 回复 / 热度">💬 ${it.h}</span>` : "",
      fresh ? '<span class="new">新</span>' : "",
      it.a && it.a.length ? `<span class="also">也见于 ${esc(it.a.join("、"))}</span>` : "",
    ].join("");
    return `<div class="item">
      <span class="flag" title="${esc(reg.name)}">${reg.flag}</span>
      <a class="t" href="${esc(it.u)}" target="_blank" rel="noopener noreferrer" title="${esc(it.d || it.t)}">${esc(it.t)}</a>
      ${it.v ? `<span class="val">${esc(it.v)}</span>` : "<span></span>"}
      <div class="meta">${meta}</div>
    </div>`;
  }

  // ---------- 各区块 ----------
  function renderTime() {
    const n = { today: base({ t: "today" }).length, "7d": base({ t: "7d" }).length };
    $("timeSeg").innerHTML = [["today", "今日"], ["7d", "近 7 天"]]
      .map(([id, name]) => `<button class="${S.t === id ? "on" : ""}" data-t="${id}" role="tab">${name}<b>${n[id]}</b></button>`)
      .join("");
  }

  function renderStatus() {
    const ok = D.sources.filter((s) => s.ok).length;
    const age = Date.now() / 1000 - D.generated;
    const todayNew = items.filter((it) => it.day === today()).length;
    const stale = age > 3 * 3600;
    $("statusLine").innerHTML = [
      `<span><i class="dot ${stale ? "bad" : ""}"></i>更新于 ${md(D.generated)} ${hm(D.generated)}（${ago(D.generated)}）</span>`,
      stale ? `<span class="stale">数据已 ${Math.floor(age / 3600)} 小时未更新，检查抓取任务是否在运行</span>` : "",
      `<span>信息源 ${ok}/${D.sources.length} 正常</span>`,
      `<span>今日 ${todayNew} 条 · 近 7 天 ${items.length} 条</span>`,
    ].join("");
  }

  function renderChips() {
    const scenes = [{ id: "", name: "全部" }, ...D.scenes];
    const byScene = countBy(base({ sc: "" }), "scene");
    $("sceneChips").innerHTML = scenes
      .map((s) => `<button class="chip ${S.sc === s.id ? "on" : ""}" data-sc="${s.id}">${s.name}${s.id ? `<span class="n">${byScene[s.id] || 0}</span>` : ""}</button>`)
      .join("");
    const pool = base({ r: "" });
    $("regionChips").innerHTML = REGION_FILTERS
      .map((f) => {
        const n = f.id ? pool.filter((it) => f.match.includes(it.r)).length : pool.length;
        return `<button class="chip ${S.r === f.id ? "on" : ""}" data-r="${f.id}">${f.name}<span class="n">${n}</span></button>`;
      })
      .join("");
    $("sortChips").innerHTML = [["new", "最新"], ["hot", "最热"]]
      .map(([id, name]) => `<button class="chip ${S.s === id ? "on" : ""}" data-s="${id}">${name}</button>`)
      .join("");
  }

  function renderCircles(counts) {
    const scenes = S.sc ? D.scenes.filter((s) => s.id === S.sc) : D.scenes;
    $("circleGrid").innerHTML = scenes
      .map((sc) => {
        const cards = D.circles
          .filter((c) => c.scene === sc.id && (c.id !== "other" || counts.other))
          .map((c) => {
            const n = counts[c.id] || 0;
            return `<button class="circle ${S.c === c.id ? "on" : ""} ${n ? "" : "zero"}" style="--h:${HUE[c.id]}" data-c="${c.id}" title="${esc(c.desc)}">
              <span class="ic">${c.icon}</span><span class="nm">${esc(c.name)}</span><span class="ct">${n}</span>
              <span class="ds">${esc(c.desc)}</span></button>`;
          })
          .join("");
        return `<div class="scene-row"><div class="scene-name">${sc.name}</div><div class="circles">${cards}</div></div>`;
      })
      .join("");
  }

  function renderCatBar(pool) {
    const bar = $("catBar");
    if (!S.c) { bar.hidden = true; return; }
    const c = circleMap[S.c] || circleMap.other;
    const counts = countBy(pool, "k");
    const cats = D.categories.filter((k) => k.circle === S.c && counts[k.id]);
    bar.hidden = false;
    bar.innerHTML = `<span class="title">${c.icon} ${esc(c.name)}</span>
      <button class="chip ${!S.k ? "on" : ""}" data-k="">全部<span class="n">${pool.length}</span></button>
      ${cats.map((k) => `<button class="chip ${S.k === k.id ? "on" : ""}" data-k="${k.id}">${esc(k.name)}<span class="n">${counts[k.id]}</span></button>`)
        .join("")}
      <button class="clear" data-c="">✕ 返回全部圈子</button>`;
  }

  function renderBoard(pool) {
    const counts = countBy(pool, "c");
    const scenes = S.sc ? D.scenes.filter((s) => s.id === S.sc) : D.scenes;
    const html = scenes
      .map((sc) => {
        const blocks = D.circles
          .filter((c) => c.scene === sc.id && counts[c.id])
          .sort((a, b) => (a.id === "other") - (b.id === "other") || counts[b.id] - counts[a.id])
          .map((c) => {
            const top = sorted(pool.filter((it) => it.c === c.id)).slice(0, 6);
            return `<article class="block" style="--h:${HUE[c.id]}">
              <div class="block-head"><h2>${c.icon} ${esc(c.name)}</h2><span class="cnt">${counts[c.id]}</span>
                <span class="ds">${esc(c.desc)}</span>
                <button class="more" data-c="${c.id}">查看全部 →</button></div>
              <div class="items">${top.map((it) => itemHTML(it, true)).join("")}</div></article>`;
          })
          .join("");
        return blocks ? `<div class="day">${sc.name}场景</div><div class="board">${blocks}</div>` : "";
      })
      .join("");
    $("content").innerHTML = html || emptyHTML();
  }

  function renderList(list) {
    if (!list.length) { $("content").innerHTML = emptyHTML(); return; }
    const shown = sorted(list).slice(0, limit);
    let html = "";
    if (S.s === "hot") {
      html = `<div class="list">${shown.map((it) => itemHTML(it, true)).join("")}</div>`;
    } else {
      const groups = [];
      for (const it of shown) {
        if (!groups.length || groups[groups.length - 1].day !== it.day) groups.push({ day: it.day, list: [] });
        groups[groups.length - 1].list.push(it);
      }
      html = groups
        .map((g) => `<div class="day">${dayLabel(g.day)}<small>${list.filter((it) => it.day === g.day).length} 条</small></div>
          <div class="list">${g.list.map((it) => itemHTML(it, false)).join("")}</div>`)
        .join("");
    }
    if (list.length > shown.length) html += `<button class="load-more" id="loadMore">再显示 ${Math.min(150, list.length - shown.length)} 条（共 ${list.length}）</button>`;
    $("content").innerHTML = html;
  }

  function emptyHTML() {
    const hint = S.t === "today" ? '今天这个筛选下还没有收录，<button class="chip" data-t="7d">看看近 7 天</button>' : "换个筛选条件试试";
    return `<div class="list empty">没有找到羊毛。${hint}</div>`;
  }

  function renderSources() {
    const ago2 = (ts) => (ts ? ago(ts) : "—");
    const rows = D.sources
      .map((s) => {
        const reg = regionMap[s.region] || {};
        const circles = (s.circles || []).map((c) => (circleMap[c] || {}).icon || "").join(" ");
        const st = s.ok
          ? '<span class="ok">● 正常</span>'
          : `<span class="bad">● ${s.checked ? "失败" : "未运行"}</span>${s.error ? `<div class="err">${esc(s.error)}</div>` : ""}`;
        const stats = s.ok ? `${s.fetched} / ${s.matched} / ${s.new}` : "—";
        return `<tr><td>${esc(s.name)}</td><td>${reg.flag || ""} ${esc(reg.name || "")}</td><td title="监听的圈子">${circles}</td>
          <td>${st}</td><td class="hide-sm">${stats}</td><td class="hide-sm">${ago2(s.last_ok)}</td></tr>`;
      })
      .join("");
    $("sources").innerHTML = `<div class="src-wrap"><table class="src-table"><thead><tr><th>来源</th><th>地区</th><th>圈子</th>
      <th>状态</th><th class="hide-sm">本轮 抓到 / 羊毛 / 新增</th><th class="hide-sm">最近成功</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  // ---------- 主渲染 ----------
  function render() {
    renderTime();
    renderStatus();
    renderChips();
    const pool = base();
    renderCircles(countBy(pool, "c"));
    const inCircle = S.c ? pool.filter((it) => it.c === S.c) : pool;
    renderCatBar(inCircle);
    const list = S.k ? inCircle.filter((it) => it.k === S.k) : inCircle;
    if (!S.c && !S.q) renderBoard(pool);
    else renderList(list);
  }

  // ---------- 交互 ----------
  document.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const d = b.dataset;
    if (b.id === "loadMore") { limit += 150; render(); return; }
    if (b.id === "themeBtn") return;
    if ("t" in d) set({ t: d.t });
    else if ("sc" in d) set({ sc: d.sc, c: "", k: "" });
    else if ("r" in d) set({ r: d.r });
    else if ("s" in d) set({ s: d.s });
    else if (b.classList.contains("tag")) { set({ c: d.c, k: d.k }); window.scrollTo({ top: 0, behavior: "smooth" }); }
    else if ("c" in d) {
      set({ c: S.c === d.c && b.classList.contains("circle") ? "" : d.c, k: "" });
      if (b.classList.contains("more")) window.scrollTo({ top: 0, behavior: "smooth" });
    } else if ("k" in d) set({ k: d.k });
  });
  let timer;
  $("q").addEventListener("input", (e) => { clearTimeout(timer); timer = setTimeout(() => set({ q: e.target.value.trim() }), 150); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== $("q")) { e.preventDefault(); $("q").focus(); }
    if (e.key === "Escape" && document.activeElement === $("q")) { $("q").value = ""; set({ q: "" }); $("q").blur(); }
  });
  $("themeBtn").addEventListener("click", () => {
    const cur = document.documentElement.dataset.theme
      || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("radar-theme", next); } catch (err) { /* 隐私模式下忽略 */ }
  });
  window.addEventListener("hashchange", () => { readHash(); render(); });

  readHash();
  renderSources();
  render();
  setInterval(() => { renderStatus(); }, 60 * 1000);
})();
