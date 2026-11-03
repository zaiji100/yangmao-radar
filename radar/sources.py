"""信息源清单。

字段：
  kind     解析器：feed（RSS/Atom）/ v2ex / xianbao / gamerpower / openrouter / github / hn
  region   来源默认地区：CN / US / SG / GLOBAL（标题里有明确地区信号时会被覆盖）
  mode     筛选强度：pass 全收（专门的羊毛源）/ loose 羊毛社区口语词也收 / strict 只收明确的羊毛信号
  limit    每轮最多看多少条（大流量的购物源压一下，避免刷屏）
  hint     规则没命中时的默认细分类
  circles  这个源主要覆盖哪些圈子（只用于页面展示「谁在监听」）
"""

XIANBAO = "https://new.xianbao.fun/api/v1"

SOURCES = [
    # ---------------- 中国 ----------------
    {"id": "xb-hot24", "name": "线报酷 · 24 小时热榜", "kind": "xianbao", "region": "CN", "mode": "loose",
     "url": f"{XIANBAO}/rank?act=ershisixiaoshi&limit=100", "circles": ["money", "shop", "food", "telecom"]},
    {"id": "xb-today", "name": "线报酷 · 今日榜", "kind": "xianbao", "region": "CN", "mode": "loose",
     "url": f"{XIANBAO}/rank?act=jintian&limit=300", "circles": ["money", "shop", "food", "telecom"]},
    {"id": "xb-zuanke", "name": "线报酷 · 赚客吧", "kind": "xianbao", "region": "CN", "mode": "loose",
     "url": f"{XIANBAO}/feed?cate=16&limit=50", "circles": ["money", "telecom"]},
    {"id": "xb-xinzuan", "name": "线报酷 · 新赚吧", "kind": "xianbao", "region": "CN", "mode": "loose",
     "url": f"{XIANBAO}/feed?cate=18&limit=50", "circles": ["money"]},
    {"id": "xb-xiaodigu", "name": "线报酷 · 小嘀咕", "kind": "xianbao", "region": "CN", "mode": "loose",
     "url": f"{XIANBAO}/feed?cate=11&limit=50", "circles": ["money"]},
    {"id": "xb-kuan", "name": "线报酷 · 酷安", "kind": "xianbao", "region": "CN", "mode": "loose",
     "url": f"{XIANBAO}/feed?cate=17&limit=50", "circles": ["fun", "shop"]},
    {"id": "xb-mianfei", "name": "线报酷 · 免费赚钱中心", "kind": "xianbao", "region": "CN", "mode": "loose",
     "url": f"{XIANBAO}/feed?cate=9&limit=50", "hint": "earn-task", "circles": ["earn"]},
    {"id": "xb-haodan", "name": "线报酷 · 好单（宠物 / 母婴）", "kind": "xianbao", "region": "CN", "mode": "pass",
     "url": f"{XIANBAO}/feed?cate=30&limit=50", "xb_tags": ["宠物", "母婴"], "circles": ["pets", "kids"]},
    {"id": "v2ex-free", "name": "V2EX · 免费赠送", "kind": "v2ex", "region": "CN", "mode": "pass",
     "url": "https://www.v2ex.com/api/topics/show.json?node_name=free", "circles": ["fun", "ai"]},
    {"id": "v2ex-promo", "name": "V2EX · 推广", "kind": "v2ex", "region": "CN", "mode": "strict",
     "url": "https://www.v2ex.com/api/topics/show.json?node_name=promotions", "circles": ["dev", "ai"]},
    {"id": "v2ex-latest", "name": "V2EX · 最新", "kind": "v2ex", "region": "CN", "mode": "strict",
     "url": "https://www.v2ex.com/api/topics/latest.json", "circles": ["ai", "dev"]},
    {"id": "linuxdo-welfare", "name": "Linux.do · 福利羊毛", "kind": "feed", "region": "CN", "mode": "pass",
     "url": "https://linux.do/c/welfare/36.rss", "circles": ["ai", "money", "fun"]},
    {"id": "nodeseek", "name": "NodeSeek", "kind": "feed", "region": "CN", "mode": "strict",
     "url": "https://rss.nodeseek.com/", "circles": ["dev"]},
    {"id": "smzdm-haitao", "name": "什么值得买 · 海淘", "kind": "feed", "region": "US", "mode": "pass",
     "url": "http://haitao.smzdm.com/feed", "circles": ["shop", "fun"]},
    {"id": "ithome", "name": "IT之家", "kind": "feed", "region": "CN", "mode": "strict",
     "url": "https://www.ithome.com/rss/", "circles": ["fun", "shop"]},
    {"id": "sspai", "name": "少数派", "kind": "feed", "region": "CN", "mode": "strict",
     "url": "https://sspai.com/feed", "circles": ["fun", "office"]},

    # ---------------- 美国 ----------------
    {"id": "doc", "name": "Doctor of Credit", "kind": "feed", "region": "US", "mode": "pass",
     "url": "https://www.doctorofcredit.com/feed/", "hint": "money-pay", "circles": ["money"]},
    {"id": "uscardforum", "name": "美卡论坛", "kind": "feed", "region": "US", "mode": "loose",
     "url": "https://www.uscardforum.com/latest.rss",
     "drop_tags": ["闲聊", "签证与身份（美国）", "签证与身份（美国以外）", "学术", "健康", "股市投资", "加密货币", "影音娱乐"],
     "circles": ["money", "travel"]},
    {"id": "reddit-freebies", "name": "Reddit · r/freebies", "kind": "feed", "region": "US", "mode": "pass",
     "url": "https://www.reddit.com/r/freebies/new/.rss", "hint": "shop-freebie", "circles": ["shop", "food"]},
    {"id": "reddit-efreebies", "name": "Reddit · r/eFreebies", "kind": "feed", "region": "GLOBAL", "mode": "pass",
     "url": "https://www.reddit.com/r/eFreebies/new/.rss", "hint": "shop-freebie", "circles": ["office", "fun"]},
    {"id": "hip2save", "name": "Hip2Save", "kind": "feed", "region": "US", "mode": "pass", "limit": 25,
     "url": "https://hip2save.com/feed/", "hint": "shop-ecom", "circles": ["shop", "food"]},
    {"id": "dealnews", "name": "DealNews", "kind": "feed", "region": "US", "mode": "pass", "limit": 25,
     "url": "https://www.dealnews.com/?rss=1", "hint": "shop-ecom", "circles": ["shop"]},
    {"id": "frequentmiler", "name": "Frequent Miler", "kind": "feed", "region": "US", "mode": "strict",
     "url": "https://frequentmiler.com/feed/", "hint": "money-points", "circles": ["money", "travel"]},
    {"id": "omaat", "name": "One Mile at a Time", "kind": "feed", "region": "US", "mode": "strict",
     "url": "https://onemileatatime.com/feed/", "hint": "travel-flight", "circles": ["travel"]},

    # ---------------- 新加坡 ----------------
    {"id": "milelion", "name": "The MileLion", "kind": "feed", "region": "SG", "mode": "loose",
     "url": "https://milelion.com/feed/", "hint": "money-points", "circles": ["money", "travel"]},
    {"id": "sethisfy", "name": "Sethisfy", "kind": "feed", "region": "SG", "mode": "pass",
     "url": "https://sethisfy.com/feed/", "hint": "money-pay", "circles": ["money"]},
    {"id": "greatdeals-sg", "name": "Great Deals Singapore", "kind": "feed", "region": "SG", "mode": "pass",
     "url": "https://www.greatdeals.com.sg/feed", "hint": "shop-ecom", "circles": ["food", "shop"]},
    {"id": "moneysmart", "name": "MoneySmart", "kind": "feed", "region": "SG", "mode": "strict",
     "url": "https://blog.moneysmart.sg/feed/", "hint": "money-pay", "circles": ["money"]},
    {"id": "mothership", "name": "Mothership", "kind": "feed", "region": "SG", "mode": "strict",
     "url": "https://mothership.sg/feed/", "circles": ["food", "home"]},
    {"id": "eatbook", "name": "Eatbook", "kind": "feed", "region": "SG", "mode": "strict",
     "url": "https://eatbook.sg/feed/", "hint": "food-dine", "circles": ["food"]},
    {"id": "thesmartlocal", "name": "TheSmartLocal", "kind": "feed", "region": "SG", "mode": "strict",
     "url": "https://thesmartlocal.com/feed/", "circles": ["food", "home", "travel"]},
    {"id": "goodyfeed", "name": "Goody Feed", "kind": "feed", "region": "SG", "mode": "strict",
     "url": "https://www.goodyfeed.com/feed/", "circles": ["food", "home"]},
    {"id": "reddit-sgfi", "name": "Reddit · r/singaporefi", "kind": "feed", "region": "SG", "mode": "strict",
     "url": "https://www.reddit.com/r/singaporefi/new/.rss", "hint": "money-wealth", "circles": ["money"]},

    # ---------------- 全球 · AI / 开发 / 游戏 ----------------
    {"id": "openrouter-free", "name": "OpenRouter 免费模型", "kind": "openrouter", "region": "GLOBAL", "mode": "pass",
     "url": "https://openrouter.ai/api/v1/models", "hint": "ai-api", "circles": ["ai"]},
    {"id": "gh-free-llm", "name": "GitHub · awesome-free-llm-apis", "kind": "github", "region": "GLOBAL",
     "mode": "pass", "url": "https://api.github.com/repos/mnfst/awesome-free-llm-apis/commits?per_page=30",
     "hint": "ai-api", "circles": ["ai"]},
    {"id": "hn-free-tier", "name": "Hacker News · free tier", "kind": "hn", "region": "GLOBAL", "mode": "strict",
     "url": "https://hn.algolia.com/api/v1/search_by_date?query=%22free%20tier%22&tags=story&hitsPerPage=30"
            "&numericFilters=points%3E%3D3",
     "hint": "dev-cloud", "circles": ["ai", "dev"]},
    {"id": "hn-free-credits", "name": "Hacker News · free credits", "kind": "hn", "region": "GLOBAL",
     "mode": "strict",
     "url": "https://hn.algolia.com/api/v1/search_by_date?query=%22free%20credits%22&tags=story&hitsPerPage=30",
     "hint": "ai-api", "circles": ["ai", "dev"]},
    {"id": "gamerpower", "name": "GamerPower 游戏赠送", "kind": "gamerpower", "region": "GLOBAL", "mode": "pass",
     "url": "https://www.gamerpower.com/api/giveaways?type=game", "hint": "fun-game", "circles": ["fun"]},
]
