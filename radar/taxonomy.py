"""分类体系：场景 → 圈子 → 细分类，外加地区识别与「是不是羊毛」的信号词。

规则都是按顺序匹配、先命中者为准，所以越具体的放越前面。改规则后跑 `python3 -m unittest` 回归。
"""

import re

# ASCII：让 \b 只按英文字母数字判断边界，否则「抽GPT」这种中英混排里 \bGPT 匹配不上
FLAGS = re.IGNORECASE | re.ASCII

SCENES = [
    {"id": "life", "name": "生活"},
    {"id": "work", "name": "工作"},
]

CIRCLES = [
    {"id": "ai", "name": "AI 玩家", "icon": "🤖", "scene": "work", "desc": "免费 API / Token 额度、AI 会员、AI 工具"},
    {"id": "dev", "name": "开发者", "icon": "👨‍💻", "scene": "work", "desc": "云服务器、代理网络、域名、软件授权"},
    {"id": "office", "name": "打工人", "icon": "💼", "scene": "work", "desc": "办公 / 网盘会员、课程证书"},
    {"id": "student", "name": "学生党", "icon": "🎓", "scene": "work", "desc": "学生认证、教育优惠"},
    {"id": "earn", "name": "副业党", "icon": "💰", "scene": "work", "desc": "问卷任务、拉新返佣、空投"},
    {"id": "money", "name": "卡友理财", "icon": "🏦", "scene": "life", "desc": "信用卡、开户、立减金、理财、积分里程"},
    {"id": "shop", "name": "网购党", "icon": "🛒", "scene": "life", "desc": "电商大促、数码家电、日用、免费样品"},
    {"id": "food", "name": "吃货", "icon": "🍜", "scene": "life", "desc": "外卖买菜、咖啡茶饮快餐、餐厅"},
    {"id": "travel", "name": "旅行常客", "icon": "✈️", "scene": "life", "desc": "机票、酒店会籍、门票签证"},
    {"id": "commute", "name": "通勤车主", "icon": "🚗", "scene": "life", "desc": "打车单车、加油充电停车"},
    {"id": "telecom", "name": "话费流量", "icon": "📱", "scene": "life", "desc": "话费、流量、宽带、eSIM"},
    {"id": "fun", "name": "游戏影音", "icon": "🎮", "scene": "life", "desc": "游戏喜加一、视频音乐会员、App 限免"},
    {"id": "kids", "name": "宝妈宝爸", "icon": "👶", "scene": "life", "desc": "母婴、儿童、玩具"},
    {"id": "pets", "name": "铲屎官", "icon": "🐱", "scene": "life", "desc": "猫粮狗粮、宠物用品"},
    {"id": "home", "name": "居家生活", "icon": "🏠", "scene": "life", "desc": "缴费、政府补贴、健康、本地服务"},
    {"id": "other", "name": "其他", "icon": "🐑", "scene": "life", "desc": "暂未归类的羊毛"},
]

# (细分类 id, 圈子 id, 名称, 规则)。顺序即优先级。
# 大小写不敏感；需要区分大小写的缩写用 (?-i:...) 包起来，例如 SUB（开卡奖励）不能误中 Subway 的 sub。
_RULES = [
    ("student-edu", "student", "学生 / 教育优惠",
     r"学生|大学生|校园|教育优惠|教育版|edu ?邮箱|\.edu\b|students?\b|GitHub Education|college|university"),

    ("ai-api", "ai", "免费 API / Token",
     r"\bAPI\b|api ?keys?|\btokens?\b|公益站|中转站?|硅基流动|SiliconFlow|OpenRouter|Groq|Cerebras|"
     r"免费模型|free (?:tier|credits?|models?)|API credits|大模型.{0,6}(?:额度|免费)|模型.{0,4}(?:免费|额度)"),
    ("ai-sub", "ai", "AI 会员 / 账号",
     r"ChatGPT|\bGPT|OpenAI|Claude|Anthropic|Gemini|Cursor|Copilot|Perplexity|Kimi|豆包|通义|千问|Qwen|文心|"
     r"元宝|DeepSeek|\bGrok\b|Midjourney|\bPoe\b|\bManus\b|\bCodex\b|Windsurf|\bTrae\b|NotebookLM|Google AI Pro|AI Ultra"),
    ("ai-tool", "ai", "AI 工具 / 应用",
     r"(?-i:\bAI\b)|人工智能|大模型|模型|\bLLMs?\b|\bAIGC\b|智能体|生图|绘图|文生|AI ?视频|\bSuno\b|\bRunway\b|\bSora\b|\bKling\b|可灵|即梦"),

    ("money-card", "money", "信用卡 / 开卡奖励",
     r"信用卡|XYK|办卡|开卡礼|刷卡金|附属卡|副卡|签账卡|玩卡|年费|credit cards?|"
     r"\bcards?\b.{0,40}(?:bonus|offer|cash ?back|miles|points|annual fee)|"
     r"\b(?:Amex|American Express|Chase|Citi|Capital One|Discover|Barclays|Bilt|Synchrony|Wells Fargo)\b.{0,30}(?:cards?|offers?|bonus)|"
     r"Mastercard|Visa (?:Signature|Infinite)|sign-?up bonus|(?-i:\bSUB\b)|welcome (?:bonus|offer|gift)|\bmpd\b|earn rates?"),
    ("money-wealth", "money", "理财 / 券商 / 高息",
     r"券商|证券|股票|炒股|基金|理财|黄金|存款|定期|大额存单|利率|高息|国债|逆回购|港股|美股|富途|moomoo|老虎证券|"
     r"Tiger Brokers|长桥|Longbridge|盈透|\bIBKR\b|Webull|Robinhood|Fidelity|Schwab|\bSyfe\b|Endowus|StashAway|"
     r"fixed deposits?|savings rates?|\binterest\b|p\.a\.|\bT-?bills?\b|(?-i:\bSSB\b)|\bHYSA\b|high[- ]yield|brokerage|"
     r"\bstocks?\b|\bETFs?\b|crypto|加密货币|比特币|\bBTC\b|币安|Binance|\bOKX\b|Coinbase|(?-i:\bCPF\b)|(?-i:\bSRS\b)"),
    ("money-account", "money", "开户奖励",
     r"开户|二类户|三类户|新户|checking|savings accounts?|bank accounts?|account (?:bonus|opening)|"
     r"(?:checking|savings|bank)\b.{0,30}bonus|众安|ZA ?Bank|天星银行|Airstar|\bMox\b|WeLab|汇丰|中银香港|"
     r"\bSoFi\b|\bChime\b|\bAlly\b|\bMarcus\b|Trust (?:Bank|App)|\bGXS\b|MariBank|Chocolate Finance"),
    ("money-points", "money", "积分里程 / 礼品卡 / 返利",
     r"里程|\bmiles\b|\bpoints\b|transfer bonus|Membership Rewards|Ultimate Rewards|ThankYou|HeyMax|Max Miles|"
     r"KrisFlyer|Asia Miles|Avios|返利|Rakuten|ShopBack|TopCashback|cash ?back portal|gift ?cards?|eGift|"
     r"礼品卡|E卡|超市卡|购物卡|ExtraBucks|(?-i:\bUR\b|\bMR\b|\bGC\b)"),
    ("money-pay", "money", "立减金 / 支付 / 银行活动",
     r"立减金|(?:微信|支付宝|云闪付|银联|数币|银行|卡)\S{0,6}立减|数币|数字人民币|微信支付|支付宝|云闪付|银联|转账|"
     r"摇一摇|还款|支付券|小金库|白条|Apple Pay|Google Pay|PayPal|Venmo|Zelle|Cash App|PayNow|PayLah|GrabPay|"
     r"ShopeePay|\bAtome\b|银行|銀絎|分行|工行|工商|建行|建融|农行|中行|招行|招商|交行|邮储|浦发|兴业|光大|中信|民生|"
     r"平安|广发|华夏|宁波银行|\bDBS\b|\bPOSB\b|\bOCBC\b|\bUOB\b|\bHSBC\b|Citibank|Standard Chartered|Maybank|Wells Fargo|"
     r"Bank of America|BofA|U\.S\. Bank|\bbank\b"),

    ("dev-cloud", "dev", "云服务器 / VPS",
     r"\bVPS\b|服务器|云主机|云服务|云计算|独服|\bECS\b|轻量|Lightsail|\bEC2\b|\bAWS\b|\bGCP\b|Google Cloud|Azure|"
     r"阿里云(?!盘)|腾讯云|华为云|火山引擎|天翼云|移动云|UCloud|Vultr|DigitalOcean|Linode|Akamai|Hetzner|\bOVH|"
     r"Contabo|搬瓦工|Bandwagon|DMIT|RackNerd|CloudCone|Kamatera|甲骨文|Oracle Cloud|Zenlayer|Cloudflare|"
     r"Vercel|Netlify|Railway|Fly\.io|Supabase|hosting|(?<!游戏)主机|\bIDC\b|带宽|算力|GPU ?(?:云|实例|cloud|instance|hours?|credits)|对象存储"),
    ("dev-proxy", "dev", "代理 / 网络加速",
     r"代理|prox(?:y|ies)|住宅 ?IP|静态 ?IP|动态 ?IP|IP ?池|\bVPNs?\b|梯子|加速器|节点|翻墙"),
    ("dev-domain", "dev", "域名 / CDN / 邮箱",
     r"域名|\bdomains?\b|\bCDN\b|\bSSL\b|\bDNS\b|企业邮箱|域名邮箱|email hosting"),
    ("office-soft", "office", "办公 / 网盘会员",
     r"(?-i:\bOffice\b)|Microsoft 365|\bWPS\b|Notion|Obsidian|网盘|云盘|夸克|迅雷|Adobe|Photoshop|Dropbox|iCloud|Google One|"
     r"OneDrive|Evernote|印象笔记|飞书|钉钉|\bZoom\b|Grammarly|\bCanva\b|Figma|1Password|Bitwarden|Setapp|\bPDF\b|扫描全能王|有道"),
    ("fun-app", "fun", "App 限免",
     r"App ?Store|限免|内购|Google Play|TestFlight|Play 商店"),
    ("dev-tool", "dev", "软件授权 / 开发工具",
     r"软件|正版|licen[cs]e|授权|激活码|序列号|JetBrains|IntelliJ|PyCharm|GitHub|GitLab|\bIDE\b|\bSDK\b|开发者|"
     r"\bdevelopers?\b|\bSaaS\b|(?-i:\bWindows\b)|macOS|Parallels|CleanMyMac|Docker|Typora|数码荔枝"),
    ("office-learn", "office", "课程 / 证书 / 学习",
     r"课程|网课|公开课|训练营|Coursera|Udemy|\bedX\b|Udacity|Skillshare|MasterClass|Duolingo|多邻国|证书|考证|考试|"
     r"英语|四六级|雅思|托福|IELTS|TOEFL|学习|知识付费|极客时间|courses?\b|bootcamp|certificat"),

    ("commute-ride", "commute", "打车 / 单车 / 公交",
     r"打车|滴滴|花小猪|高德|曹操出行|T3出行|单车|骑行|哈啰|青桔|电单车|骑车|Uber(?! ?Eats)|Lyft|"
     r"\bGrab\b(?!Food|Pay|Mart)|Gojek|\bTADA\b|\bRyde\b|ComfortDelGro|地铁|公交|乘车码|(?-i:\bMRT\b)|\btransit\b"),
    ("commute-car", "commute", "加油 / 充电 / 停车 / 养车",
     r"加油|油卡|油费|中石化|中石油|壳牌|充电桩|充电(?!宝|器|头|线)|特斯拉|Tesla|停车|(?-i:\bETC\b)|洗车|保养|车险|轮胎|驾照|"
     r"驾校|电动车|\bgas\b|\bfuel\b|petrol|(?-i:\bShell\b)|Caltex|\bEsso\b|(?-i:\bSPC\b)|EV charg|car wash|parking|car rentals?|"
     r"Hertz|\bAvis\b|租车"),
    ("telecom-phone", "telecom", "话费 / 流量 / 宽带",
     r"话费|流量(?!主|明星)|宽带|中国移动|移动(?:话费|流量|积分|口令|灵犀|权益|宽带|APP|营业厅|卡)|联通|电信(?!诈骗)|"
     r"广电|(?<![\dA-Za-z])5G\b|\beSIMs?\b|号卡|手机卡|上网卡|流量卡|\bSIM\b|灵犀|和包|携号转网|Singtel|StarHub|(?-i:\bM1\b)|Circles\.?Life|"
     r"\bSIMBA\b|\bGOMO\b|T-Mobile|Verizon|AT&T|Mint Mobile|Visible Wireless|US Mobile|Google Fi|Cricket Wireless|phone plans?|"
     r"mobile plans?|data plans?|roaming"),
    ("travel-flight", "travel", "机票 / 航司",
     r"机票|特价票|航司|航空|航班|里程票|升舱|flights?\b|airlines?|airfare|award (?:seat|space)|business class|"
     r"first class|(?-i:\bSIA\b)|Singapore Airlines|\bScoot\b|United Airlines|\bDelta\b|American Airlines|Southwest|"
     r"JetBlue|Alaska Airlines|Cathay|国泰|国航|东航|南航|海航|春秋航空|亚航|AirAsia|Emirates|Qatar"),
    ("travel-hotel", "travel", "酒店 / 会籍",
     r"酒店|万豪|希尔顿|洲际|凯悦|雅高|华住|亚朵|锦江|首旅|Marriott|Bonvoy|Hilton|\bIHG\b|Hyatt|\bAccor\b|Wyndham|"
     r"hotels?\b|resorts?\b|Airbnb|民宿|会籍|status match|房晚|free nights?"),
    ("travel-trip", "travel", "旅游 / 门票 / 签证",
     r"旅游|旅行|景区|门票|签证|邮轮|cruises?|Klook|KKday|Trip\.com|携程|飞猪|同程|去哪儿|途牛|Agoda|Booking\.com|"
     r"Expedia|travel insurance|旅行险|vacation|getaway|theme park|Universal Studios|迪士尼|Disneyland|环球影城"),

    ("fun-game", "fun", "游戏喜加一",
     r"\bSteam\b(?! ?(?:mop|cleaner|iron|oven|er\b))|\bEpic\b|\bGOG\b|喜加一|游戏|\bgames?\b|gaming|Xbox|PlayStation|PS ?Plus|\bPS5\b|Nintendo|(?-i:\bSwitch\b)|"
     r"Prime Gaming|Ubisoft|EA Play|\bDLC\b|手游|原神|王者荣耀|Battle\.net|暴雪|米哈游|Roblox|Fortnite|Minecraft|\bT?TRPGs?\b|桌游"),
    ("fun-video", "fun", "视频 / 音乐 / 阅读会员",
     r"爱奇艺|腾讯视频|优酷|芒果|B站|bilibili|哔哩哔哩|大会员|网易云|QQ音乐|酷狗|酷我|汽水音乐|Spotify|Netflix|"
     r"奈飞|YouTube|Disney\+|HBO|Hulu|Apple (?:TV|Music|One)|Peacock|Paramount|Prime Video|Audible|喜马拉雅|"
     r"懒人听书|微信读书|Kindle Unlimited|起点|番茄小说|有声书|视频会员|音乐会员|黑胶|\bSVIP\b|streaming"),
    ("fun-app", "fun", "App 限免",
     r"\biOS\b|iPadOS|Android|安卓|\bapps?\b|应用"),

    ("pets-supply", "pets", "宠物用品",
     r"宠物|猫粮|狗粮|猫砂|猫条|冻干|铲屎|驱虫|(?<![天熊黑])猫(?!超|眼|头鹰|爪)|(?<![热])狗(?!东)|\bpets?\b|\bcats?\b|"
     r"\bdogs?\b|kittens?|pupp(?:y|ies)|Chewy|Petco|PetSmart"),
    ("kids-baby", "kids", "母婴 / 儿童",
     r"母婴|宝宝|婴儿|婴幼儿|儿童|童装|童鞋|奶粉|尿不湿|纸尿裤|拉拉裤|奶瓶|辅食|玩具|亲子|早教|绘本|孕妇|孕期|文具|"
     r"bab(?:y|ies)|\bkids?\b|toddlers?|\btoys?\b|LEGO|乐高|diapers?|children|school supplies"),

    ("food-delivery", "food", "外卖 / 买菜 / 超市",
     r"外卖|淘宝闪购|美团(?!单车|骑)|饿了么|京东秒送|闪购|买菜|叮咚|朴朴|盒马|山姆|小象超市|GrabFood|foodpanda|"
     r"Deliveroo|DoorDash|Uber ?Eats|Instacart|Grubhub|FairPrice|(?-i:\bNTUC\b)|Sheng Siong|Cold Storage|RedMart|"
     r"grocer(?:y|ies)|supermarket|超市(?!卡)"),
    ("food-drink", "food", "咖啡茶饮 / 快餐 / 便利店",
     r"瑞幸|luckin|星巴克|Starbucks|库迪|Manner(?=咖啡| ?coffee)|茶百道|霸王茶姬|蜜雪|喜茶|奈雪|古茗|沪上阿姨|茉莉奶白|一点点|书亦|"
     r"麦当劳|McDonald|肯德基|(?-i:\bKFC\b)|疯狂星期四|汉堡王|Burger King|必胜客|Pizza Hut|达美乐|Domino|塔斯汀|"
     r"华莱士|德克士|Subway|赛百味|Chick-fil-A|Taco Bell|Wendy\'?s|Popeyes|Chipotle|Dunkin|Krispy Kreme|Panera|"
     r"Firehouse|Jollibee|Mr Bean|LiHO|Gong Cha|贡茶|Ya ?Kun|Toast Box|咖啡|奶茶|茶饮|饮品|coffee|bubble tea|"
     r"\bboba\b|1-for-1|1 for 1|BOGO|buy one,? get one|pizza|burgers?|donuts?|sandwich|sando|\bsubs?\b|fries|"
     r"chicken|7-?Eleven|7-11|全家|罗森|便利店|好想来|零食很忙"),
    ("food-dine", "food", "餐厅 / 自助餐",
     r"餐厅|餐饮|自助餐|buffets?|restaurants?|dining|\bdine\b|海底捞|火锅|烧烤|烤肉|brunch|omakase|hawker|"
     r"food court|大众点评|团购|堂食|饭店|eatery|\bcaf[eé]s?\b|\bmeals?\b"),

    ("home-bill", "home", "水电燃气缴费",
     r"电费|水费|燃气|煤气|缴费|物业费|utility|utilities|electricity|electric bill|SP Group|Geneco|water bill"),
    ("home-gov", "home", "政府补贴 / 消费券",
     r"政府(?:补贴|消费券)|(?:市|省|区|县)(?:级)?消费券|国补|以旧换新|惠民|(?-i:\bCDC\b)|SG60|GST Voucher|Climate Vouchers?|U-Save|"
     r"MediSave|ComCare|stimulus|tax credits?|tax refund|退税|个税|社保|医保|公积金|(?-i:\bIRS\b)|government|"
     r"grants?\b|subsid(?:y|ies)"),
    ("home-health", "home", "健康 / 医疗 / 保险",
     r"体检|药店|药品|医院|医疗|牙科|洗牙|眼镜|疫苗|挂号|问诊|健康|保健|维生素|鱼油|保险|血糖仪|血压计|insurance|"
     r"\bhealth|clinic|dental|pharmacy|Walgreens|(?-i:\bGuardian\b)|Watsons|屈臣氏|vitamins?|supplements?"),
    ("home-local", "home", "本地生活 / 电影演出 / 家居",
     r"电影|影票|观影|猫眼|淘票票|演唱会|演出|话剧|展览|博物馆|健身|游泳|瑜伽|美容|美甲|理发|洗衣(?!液|凝珠)|干洗|家政|"
     r"保洁|快递|寄件|顺丰|movies?\b|cinemas?|concerts?|museums?|exhibitions?|\bgyms?\b|fitness|yoga|haircuts?|"
     r"laundry|IKEA|宜家|家具|furniture|mattress"),

    ("earn-task", "earn", "问卷任务 / 拉新返佣",
     r"问卷|调查|surveys?|任务(?!栏)|赚钱|兼职|副业|搬砖|拉新|邀请(?:奖励|返现|码)|推荐(?:奖励|码)|referral|"
     r"refer a friend|beermoney|返佣|佣金|测试员|testers?|赏金|bount(?:y|ies)|airdrop|空投|撸毛"),

    ("shop-freebie", "shop", "免费领 / 0 元购",
     r"(?<![\d.])0\s*元|零元|一分钱|1分钱|免费领|免费送|免费拿|免费得|免单|试用装|小样|free samples?|freebies?|"
     r"free (?:gift|stuff|items?|t-?shirts?|tees?|stickers?)|giveaways?|sweepstakes|抽奖|drawing|\bfree\b(?! shipping| delivery| returns| w/| with)"),
    ("shop-digital", "shop", "数码家电",
     r"手机|iPhone|iPad|MacBook|Mac ?mini|iMac|AirPods|Apple Watch|\bPixel\b|\bGalaxy\b|电脑|笔记本|台式机|显示器|耳机|"
     r"音箱|音响|键盘|鼠标|\bSSDs?\b|固态|硬盘|内存|显卡|\bRTX\b|\bCPU\b|相机|镜头|手表|手环|平板|电视|投影|路由器|充电器|充电宝|"
     r"移动电源|数码|家电|洗衣机|冰箱|空调|热水器|扫地机|洗地机|吸尘器|吹风机|电动牙刷|净水器|厨师机|电钻|laptops?|"
     r"monitors?|headphones|earbuds|speakers?|keyboards?|\bmouse\b|hard drives?|\bTVs?\b|tablets?|smartphones?|"
     r"\bphones?\b|cameras?|smartwatch|routers?|chargers?|power banks?|Mini PC|\bPC\b|graphics card|consoles?|"
     r"Kindle|Dyson|戴森|drills?\b|vacuum"),
    ("shop-daily", "shop", "日用快消 / 服饰美妆",
     r"斐乐|FILA|耐克|Nike|阿迪|adidas|优衣库|Uniqlo|安踏|李宁|lululemon|露露|北面|始祖鸟|波司登|纸巾|抽纸|卷纸|湿巾|卫生巾|洗衣液|洗衣凝珠|柔顺剂|沐浴露|洗发水|护发|牙膏|牙刷|洗洁精|日用|零食|饮料|食品|粮油|"
     r"大米|食用油|水果|生鲜|牛奶|酸奶|坚果|服饰|衣服|外套|羽绒服|卫衣|裤|鞋|靴|袜|内衣|箱包|化妆品|护肤|面霜|面膜|"
     r"精华|口红|唇膏|香水|美妆|防晒|床品|四件套|snacks?|candy|chocolate|cookies?|cereal|clothing|apparel|"
     r"shoes|sneakers|boots|jackets?|hoodies?|socks|\bbags?\b|beauty|skincare|makeup|lipstick|perfume|fragrance|"
     r"shampoo|detergent|paper towels?|toilet paper|tissues?|pillowcases?|bedding|towels?|kitchen|cookware|"
     r"knife|blankets?|candles?|gift sets?|鸡排|牛排|鸭舌|云吞|饺子|鸡蛋|海鲜|月饼|调料|洁厕|清洁|垃圾袋|收纳|量杯|椅子?|"
     r"沙发|lamps?|lights?|chairs?"),
    ("shop-ecom", "shop", "电商大促 / 优惠券",
     r"京东|淘宝|天猫|拼多多|(?-i:\bPDD\b)|抖音商城|唯品会|闲鱼|苏宁|当当|得物|Amazon|亚马逊|(?-i:\bTarget\b)|Walmart|"
     r"Best Buy|Costco|\beBay\b|\bTemu\b|\bShein\b|AliExpress|速卖通|Shopee|Lazada|Qoo10|Zalora|双11|双十一|黑五|黑色星期五|"
     r"Black Friday|Cyber Monday|Prime Day|(?<!\d)618(?!\d)|百亿补贴|优惠券|券|coupons?|promo codes?|\bsale\b|% off|"
     r"\d+\s*折|折扣|discount|\bdeals?\b|clearance|price drop|海淘|直邮|包邮|shipped|free shipping"),
]

RULES = [(cid, circle, name, re.compile(pat, FLAGS)) for cid, circle, name, pat in _RULES]
CATEGORY_INFO = {cid: {"id": cid, "circle": circle, "name": name} for cid, circle, name, _ in _RULES}
CATEGORY_INFO["other"] = {"id": "other", "circle": "other", "name": "其他羊毛"}

# 线报酷「好单线报-宠物-淘宝」这类子标签，规则没命中时作为兜底
XIANBAO_TAG_HINT = {
    "宠物": "pets-supply", "母婴": "kids-baby", "数码": "shop-digital", "家电": "shop-digital",
    "日用": "shop-daily", "美妆": "shop-daily", "服饰": "shop-daily", "粮油": "shop-daily",
    "零食": "shop-daily", "食品": "shop-daily", "蛋肉": "shop-daily", "健康": "home-health",
}

# 线报酷的购物类频道（豆瓣买组、微博线报等），规则没命中也按「电商」兜底；赚客吧这类综合频道不兜底
XIANBAO_CHANNEL_HINT = {
    "豆瓣线报": "shop-ecom", "微博线报": "shop-ecom", "微博超话": "shop-ecom", "好单线报": "shop-ecom",
    "值得买": "shop-ecom", "慢慢买": "shop-ecom",
}

# ---------------- 地区 ----------------

REGIONS = [
    {"id": "CN", "name": "中国", "flag": "🇨🇳"},
    {"id": "HK", "name": "香港", "flag": "🇭🇰"},
    {"id": "US", "name": "美国", "flag": "🇺🇸"},
    {"id": "SG", "name": "新加坡", "flag": "🇸🇬"},
    {"id": "GLOBAL", "name": "全球", "flag": "🌐"},
]

# 明确写出地名 / 币种的，任何来源都认
REGION_EXPLICIT = {
    "HK": re.compile(r"香港|港卡|港币|港元|HKD|HK\$|Hong Kong", FLAGS),
    "SG": re.compile(r"Singapore|新加坡|狮城|S\$|SGD|(?-i:\bSG\b)", FLAGS),
    "US": re.compile(r"(?-i:\bUSA?\b)|U\.S\.|美国|北美|美区|US only", FLAGS),
}
# 当地特有的品牌，只在来源地区不明确（国内 / 全球来源）时用来判断
REGION_BRANDS = {
    "HK": re.compile(r"众安|ZA ?Bank|天星银行|Airstar|\bMox\b|WeLab|中银香港|八达通|Octopus|PayMe", FLAGS),
    "SG": re.compile(
        r"\bDBS\b|\bPOSB\b|\bOCBC\b|\bUOB\b|Singtel|StarHub|(?-i:\bM1\b)|Circles\.?Life|(?-i:\bNTUC\b)|FairPrice|Sheng Siong|"
        r"(?-i:\bCDC\b)|SG60|(?-i:\bHDB\b)|(?-i:\bCPF\b)|Changi|KrisFlyer|\bScoot\b|Trust Bank|\bGXS\b|MariBank|"
        r"Chocolate Finance|HeyMax|PayNow|PayLah|Deepavali|Sentosa", FLAGS),
    "US": re.compile(
        r"\bChase\b|\bAmex\b|American Express|Capital One|Discover (?:it|card|bank)|Wells Fargo|Bank of America|BofA|"
        r"U\.S\. Bank|Synchrony|Barclays|\bBilt\b|\bSoFi\b|\bChime\b|Robinhood|Webull|Schwab|Fidelity|Venmo|Zelle|"
        r"Cash App|Walmart|(?-i:\bTarget\b)|Best Buy|\bCVS\b|Walgreens|Kroger|Safeway|Whole Foods|Trader Joe|DoorDash|"
        r"Instacart|T-Mobile|Verizon|AT&T|Mint Mobile|Google Fi|Southwest|JetBlue|Chick-fil-A|Taco Bell|"
        r"Chipotle|Dunkin|Krispy Kreme|(?-i:\bIRS\b)|401k|HYSA|美卡", FLAGS),
}
REGION_CN = re.compile(
    r"国内|大陆|人民币|\d\s*元|[¥￥]|京东|淘宝|天猫|拼多多|支付宝|微信|云闪付|美团|饿了么|滴滴|高德|工行|建行|农行|中行|"
    r"招行|交行|邮储|浦发|兴业|光大|中信|民生|广发|中国移动|联通|电信|数币|数字人民币|B站|爱奇艺|腾讯|网易|抖音|快手|"
    r"小红书|瑞幸|蜜雪|山姆|双十一|双11|国补|四六级")

# 这些细分类天然跨地区（API、云、游戏、App），没有明确地区信号时记为「全球」
GLOBAL_CATS = {
    "ai-api", "ai-sub", "ai-tool", "dev-cloud", "dev-proxy", "dev-domain", "dev-tool", "fun-game", "fun-app",
}
# 美国 / 新加坡来源里，这几类也按全球算（App 限免、游戏、AI 不分地区）
GLOBAL_CATS_FROM_LOCAL = {"ai-api", "ai-sub", "ai-tool", "fun-game", "fun-app"}

# ---------------- 羊毛信号 ----------------

# strict：新闻站、综合论坛的标题，必须命中这里才收
_STRICT = (
    r"羊毛|薅|白嫖|返现|反现|返利|返佣|立减|立省|满减|限免|限时免费|"
    r"免费(?:领|送|拿|试用|赠|兑换|得|试玩|用|额度|会员|骑|看|喝|吃|体验|下载|升级|领取)|免单|(?<![\d.])0\s*元|零元|一分钱|1分钱|"
    r"\d+(?:\.\d+)?\s*折|史低|白菜价|好价|神价|红包|福利|抽奖|优惠|特价|低价|降价|大促|秒杀|半价|买一送一|第二件|"
    r"兑换码|激活码|CDK|折扣码|开户(?:礼|送|奖励|返|反)|办卡(?:礼|送|返)|刷卡金|立减金|数币|喜加一|"
    r"新人(?:礼|券|专享)|首单|(?<![推运发传输递])送\s*\d+|(?<![推运发传输递])送\S{0,4}(?:券|金|币|流量|积分|会员|红包|礼|月|天|年|GB|元)|"
    r"赠送|体验金|免费额度|公益站|大毛|小毛|有水|放水|bug价|黑五|双十一|双11|消费券|补贴|"
    r"\bfree\b|freebies?|giveaways?|\d+%\s*off|\bBOGO\b|1[- ]for[- ]1|buy one,? get one|promo ?codes?|coupons?|"
    r"cash ?back|\bbonus\b|sign-?up bonus|welcome (?:bonus|offer)|free trial|free credits?|free tier|"
    r"\$\d[\d,]*\s*(?:off|back|credit|bonus|statement credit|gift ?card)|price drop|\bdeals?\b|discount|"
    r"limited[- ]time|on sale|\bsale\b|half price|waived?|rebates?|\boffers?\b|promo(?:tion)?s?\b|"
    r"transfer bonus|\bvouchers?\b|targeted|\bspend \$|\bget \$|S\$\d|up to \d+%|"
    r"\d+(?:,\d{3})*\s*(?:bonus )?(?:miles|points)"
)
# loose：羊毛社区（线报站、卡论坛）里大部分帖子本身就是羊毛，放宽到这些口语词
_LOOSE = _STRICT + (
    r"|速度|毛|抢|口令|任务|活动|补货|有货|上新|积分|E卡|\d+(?:\.\d+)?\s*元|\$\d|mpd|earn rate|\binterest\b|"
    r"p\.a\.|nerf|buff|抽(?:奖|黄金|红包|免单|\S{0,3}金)|领(?:取|券|红包|会员)?"
)
SIGNAL = {
    "strict": re.compile(_STRICT, FLAGS),
    "loose": re.compile(_LOOSE, FLAGS),
}

# 求购、转让、提问类帖子不算羊毛
NOISE = re.compile(
    r"^\s*(?:求|收|出|转让|问|请教|请问|有没有|有无|关于|吐槽)|招聘|求职|内推|租房|出租|【(?:收|出)】|\[(?:收|出)\]|"
    r"^(?:WTB|WTS)\b|已失效|已结束|已过期|\[?expired\]?|megathread|weekly (?:thread|discussion)|daily discussion|monthly meeting|"
    r"吗(?:[？?，,。!！\s]|$)|[？?]\s*$|怎么(?:办|弄|样|选)|是不是|能不能|有人知道|啥时候|什么时候|为什么|求推荐",
    FLAGS,
)

# ---------------- 价值提取 ----------------

VALUE_PATTERNS = [
    re.compile(r"(?:S\$|HK\$|US\$|A\$|C\$|\$|[¥￥])\s?\d(?:[\d,]*\d)?(?:\.\d+)?(?:\s?[kK]\b)?"),
    re.compile(r"\d(?:[\d,]*\d)?(?:\.\d+)?\s?(?:元|块钱|块|HKD|港币|港元|SGD|USD|美元|美金|刀)"),
    re.compile(r"(?<![A-Za-z\d.])\d+(?:\.\d+)?r(?![A-Za-z])"),  # 线报黑话：24.3r = 24.3 元
    re.compile(r"\d{1,3}(?:,\d{3})+\s?(?:bonus\s)?(?:miles|points|积分|里程)|\d+[kK]\s?(?:miles|points|积分|里程)",
               FLAGS),
    re.compile(r"\d+(?:\.\d+)?\s?折"),
    re.compile(r"\d+(?:\.\d+)?%\s?(?:off|back|cash ?back|返现|p\.a\.)", FLAGS),
]
