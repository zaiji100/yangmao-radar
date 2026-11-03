# 🐑 羊毛雷达

持续扫描中国、美国、新加坡的羊毛机会，按「场景 → 人群圈子 → 细分类」整理成网页，可以看今日和近 7 天的羊毛。

线上地址：**https://zaiji100.github.io/yangmao-radar/**（GitHub Actions 每小时更新）

- 只依赖 Python 3.9+ 标准库，不用装任何包
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
radar/classify.py  判断是不是羊毛 → 归圈子 / 细分类 / 地区 → 提取金额
radar/store.py     data/state.json：去重（同 URL、3 天内同标题）、保留 10 天
radar/build.py     导出 site/data.js（近 7 天）
site/              网页：index.html + app.js + style.css
```

- **筛选强度**：专门的羊毛源（Doctor of Credit、Linux.do 福利羊毛…）全收；线报站、卡论坛用宽松口语词（「速度」「有水」「立减金」）；新闻站、综合论坛只收明确的优惠信号。求购、提问、已过期的帖子一律过滤。
- **分类在导出时现算**：改了 `taxonomy.py` 后跑 `python3 run.py --rebuild`，历史数据也按新规则重新归类。
- **加信息源**：在 `radar/sources.py` 里加一行；RSS 源 `kind` 填 `feed` 就行。
- Linux.do 等站点会按 TLS 指纹拦截 Python，抓取遇到 403 时会自动改用 `curl`。
- Reddit 对未登录请求限流很严，偶尔 429 属正常，下一轮会恢复。

## 长期运行

**本机常驻**（Mac 开着就一直扫）：

```bash
nohup python3 run.py serve > radar.log 2>&1 &
```

**GitHub Actions + Pages**（不依赖本机，免费）：仓库推到 GitHub 后，在 Settings → Pages 把 Source 设为「GitHub Actions」。`.github/workflows/scan.yml` 每小时抓一轮，把状态提交回仓库并发布网页。注意 GitHub 的机器在美国，个别国内站点、Reddit 可能拦截机房 IP，失败的源在网页底部「信息源与监听状态」里能看到。

## 注意

自动筛选和分类基于关键词，会有误判和漏判；活动真伪、参与条件和风险请以原帖和官方规则为准。
