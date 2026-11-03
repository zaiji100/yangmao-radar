# 🐑 羊毛雷达

持续扫描中国、美国、新加坡的羊毛机会，按「场景 → 人群圈子 → 细分类」整理成网页，可以看今日和近 7 天的羊毛。

线上地址：**https://zaiji100.github.io/yangmao-radar/**（GitHub Actions 每小时更新）

- **AI 审核**：每条用 Claude Haiku 5.5 判断是不是真羊毛、打 0–5 分、重新归类，并把标题改写成一句看得懂的中文；0–1 分（讨论、提问、广告、普通新闻）直接不展示，网页默认只看 3 分以上
- 抓取只依赖 Python 3.9+ 标准库；AI 审核需要 `anthropic` 包和 `ANTHROPIC_API_KEY`，缺了就自动退回关键词规则
- 38 个信息源：线报酷（赚客吧 / 新赚吧 / 豆瓣 / 微博线报）、V2EX、Linux.do、NodeSeek、什么值得买海淘、Doctor of Credit、美卡论坛、Reddit、Hip2Save、DealNews、MileLion、Sethisfy、Great Deals SG、Eatbook、GamerPower、OpenRouter 免费模型等
- 网页是纯静态单页（`site/`），双击打开或放到任意静态托管都能用

## 快速开始

```bash
python3 run.py            # 抓一轮，生成 site/data.js
open site/index.html      # 直接打开网页

python3 run.py serve      # 常驻：每 30 分钟抓一轮，网页在 http://127.0.0.1:8000
python3 run.py serve --interval 15 --port 8080
```

其他命令：

```bash
python3 run.py --only doc,linuxdo-welfare   # 只抓指定来源，调试用
python3 run.py --rebuild                    # 不抓取，只按当前分类规则重新导出（改完规则用）
python3 run.py --review                     # 不抓取，只让 AI 审核待审条目并导出
python3 -m unittest                         # 分类规则回归测试
```

## 分类体系

| 场景 | 圈子 | 细分类 |
|---|---|---|
| 生活 | 🏦 卡友理财 | 信用卡 / 开卡奖励、理财 / 券商 / 高息、开户奖励、积分里程 / 礼品卡、立减金 / 支付 / 银行活动 |
| | 🛒 网购党 | 免费领 / 0 元购、数码家电、日用快消 / 服饰美妆、电商大促 / 优惠券 |
| | 🍜 吃货 | 外卖 / 买菜 / 超市、咖啡茶饮 / 快餐、餐厅 / 自助餐 |
| | ✈️ 旅行常客 | 机票 / 航司、酒店 / 会籍、旅游 / 门票 / 签证 |
| | 🚗 通勤车主 | 打车 / 单车 / 公交、加油 / 充电 / 停车 |
| | 📱 话费流量 | 话费 / 流量 / 宽带 / eSIM |
| | 🎮 游戏影音 | 游戏喜加一、视频音乐阅读会员、App 限免 |
| | 👶 宝妈宝爸 · 🐱 铲屎官 · 🏠 居家生活 | 母婴、宠物、缴费 / 政府补贴 / 健康 / 本地生活 |
| 工作 | 🤖 AI 玩家 | 免费 API / Token、AI 会员 / 账号、AI 工具 |
| | 👨‍💻 开发者 | 云服务器 / VPS、代理、域名 / CDN、软件授权 |
| | 💼 打工人 · 🎓 学生党 · 💰 副业党 | 办公网盘会员、课程证书、学生认证、问卷任务 |

地区：🇨🇳 中国（含 🇭🇰 香港）/ 🇺🇸 美国 / 🇸🇬 新加坡 / 🌐 全球通用（API、云、游戏、App 这类不分地区的）。

## 工作原理

```
radar/sources.py   信息源清单（地址、默认地区、筛选强度）
radar/fetchers.py  抓取与解析：RSS/Atom、V2EX、线报酷 API、GamerPower、OpenRouter、GitHub、HN
radar/taxonomy.py  分类规则、地区识别、羊毛信号词 ← 调分类主要改这里
radar/classify.py  关键词初筛：判断是不是羊毛 → 归圈子 / 细分类 / 地区 → 提取金额
radar/llm.py       AI 审核：Claude Haiku 5.5 打分、归类、改写标题（提示词在这里，改完把 PROMPT_VERSION 加一）
radar/store.py     data/state.json：去重（同 URL、3 天内同标题）、保留 10 天
radar/build.py     导出 site/data.js（近 7 天）
site/              网页：index.html + app.js + style.css
```

- **筛选强度**：专门的羊毛源（Doctor of Credit、Linux.do 福利羊毛…）全收；线报站、卡论坛用宽松口语词（「速度」「有水」「立减金」）；新闻站、综合论坛只收明确的优惠信号。求购、提问、已过期的帖子一律过滤。
- **分类在导出时现算**：改了 `taxonomy.py` 后跑 `python3 run.py --rebuild`，历史数据也按新规则重新归类。
- **加信息源**：在 `radar/sources.py` 里加一行；RSS 源 `kind` 填 `feed` 就行。
- Linux.do 等站点会按 TLS 指纹拦截 Python，抓取遇到 403 时会自动改用 `curl`。
- Reddit 对未登录请求限流很严，偶尔 429 属正常，下一轮会恢复。

## AI 审核

关键词规则先做一道便宜的初筛，通过的条目每 20 条一批交给 Claude Haiku 5.5 审核。打分标准：

| 分 | 含义 | 网页 |
|---|---|---|
| 5 大毛 | 价值高且门槛低：大额开户 / 办卡奖励、免费领实物或年度会员、价格 bug | 「好毛」里，带「大毛」标 |
| 4 好毛 | 明确福利：几元到几十元立减金、付费游戏 / App 限免、积分转换加成 | 「好毛」里 |
| 3 小毛 | 有好处但价值一般或有门槛：小额随机红包、targeted 活动 | 「值得薅」（默认） |
| 2 普通优惠 | 常规打折、普通商品好价 | 「全部」里 |
| 0–1 | 讨论、提问、新闻、广告、已失效 | 不展示 |

- 每条只审一次，结论存在 `data/state.json`；改了提示词把 `radar/llm.py` 里的 `PROMPT_VERSION` 加一，近 7 天的条目会全部重审。
- 单轮最多审 600 条；本地启用：`pip install -r requirements.txt` 后 `export ANTHROPIC_API_KEY=...`。
- 费用：按每天约 1000 条估算约 $3/月，网页状态栏显示近 24 小时的实际花费。

## 长期运行

**本机常驻**（Mac 开着就一直扫）：

```bash
nohup python3 run.py serve > radar.log 2>&1 &
```

**GitHub Actions + Pages**（不依赖本机）：仓库推到 GitHub 后，在 Settings → Pages 把 Source 设为「GitHub Actions」，在 Settings → Secrets and variables → Actions 添加 `ANTHROPIC_API_KEY`。`.github/workflows/scan.yml` 每小时抓一轮，把状态提交回仓库并发布网页。注意 GitHub 的机器在美国，个别国内站点、Reddit 可能拦截机房 IP，失败的源在网页底部「信息源与监听状态」里能看到。

## 注意

自动筛选和分类基于关键词，会有误判和漏判；活动真伪、参与条件和风险请以原帖和官方规则为准。
