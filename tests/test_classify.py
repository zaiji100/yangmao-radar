"""分类规则回归：样本都取自真实抓到的标题。改 radar/taxonomy.py 后跑 `python3 -m unittest`。"""

import unittest

from radar.classify import classify, extract_value, is_deal
from radar.sources import SOURCES

SRC = {s["id"]: s for s in SOURCES}


def run(title, source):
    e = {"title": title, "url": "https://example.com/x", "summary": "", "tags": []}
    return classify(e, SRC[source])


# (标题, 来源, 期望细分类, 期望地区)
CASES = [
    ("北京建行16大毛", "linuxdo-welfare", "money-pay", "CN"),
    ("建设银行搜索惠省钱微信立减金", "linuxdo-welfare", "money-pay", "CN"),
    ("支付宝中国银行转账立减金3元，冲。", "xb-zuanke", "money-pay", "CN"),
    ("农行XYK，15元刷卡金，领到加果", "xb-zuanke", "money-card", "CN"),
    ("十一月香港众安银行奖励依旧丰富！开户反 550HKD 平台薅 1500+HKD", "v2ex-promo", "money-account", "HK"),
    ("AmEx Offers: Avis Car Rental, Spend $200/$400 & Get $40/$80 Statement Credit", "doc", "money-card", "US"),
    ("Amex Offer: Spend $1,000+ on Etihad, get $200 back (targeted, enrollment required)", "frequentmiler",
     "money-card", "US"),
    ("Synchrony 2% Card: $100 Signup Bonus", "doc", "money-card", "US"),
    ("Giftcards.com: $10 Bonus Giftcard With $100+ Virtual Visa eGiftcard Purchase", "doc", "money-points", "US"),
    ("Chase UR 兑换GC Sale", "uscardforum", "money-points", "US"),
    ("AMEX KrisFlyer Credit Card increases earn rates to 1.3 mpd", "milelion", "money-card", "SG"),
    ("HeyMax offering 50% transfer bonus to IHG One Rewards", "milelion", "money-points", "SG"),
    ("Buffed: UOB Stash Increases Rates to 1.92% p.a. From November 2026", "sethisfy", "money-wealth", "SG"),
    ("【LV中转】11 月了，给新朋友的 10 元体验额度还在，这帖也能领", "linuxdo-welfare", "ai-api", "GLOBAL"),
    ("抽GPT PLUS 试用号 * 2，未接码", "linuxdo-welfare", "ai-sub", "GLOBAL"),
    ("Bilibili的免费翻译模型来了", "linuxdo-welfare", "ai-tool", "GLOBAL"),
    ("帮忙免费验证几个Google One 学生认证 [请暂时不要私发]", "linuxdo-welfare", "student-edu", "CN"),
    ("Zenlayer 黑五活动:新老用户充 >=100 到账 150,新号首单再返 25", "v2ex-promo", "dev-cloud", "GLOBAL"),
    ("数据采集必备：动态住宅代理 IP 入门指南（IPFLY 注册就送 500M 流量）", "v2ex-promo", "dev-proxy", "GLOBAL"),
    ("[数码荔枝 x 双十一] 超 150 款正版软件 6 折起", "v2ex-promo", "dev-tool", "GLOBAL"),
    ("App Store本体限免：Mossca — Lossless music Player [macOS]", "smzdm-haitao", "fun-app", "GLOBAL"),
    ("[Steam 喜加一] 《Colleccct》即将转为付费，还可以免费领取", "linuxdo-welfare", "fun-game", "GLOBAL"),
    ("Bissell Steam Mop Only $49.99 Shipped on Amazon", "hip2save", "shop-ecom", "US"),
    ("Ten Free TTRPGs, Zines, and Supplements to Fight Your Frights", "reddit-efreebies", "fun-game", "GLOBAL"),
    ("「网易云音乐」11 月领免费会员，随机 7 天 左右 ，共 128 天", "v2ex-free", "fun-video", "CN"),
    ("中国移动有个美团单车的权益，大家有需要的可以去美团-骑车里面找下领取", "v2ex-free", "commute-ride", "CN"),
    ("20261103移动领1-9元话费", "linuxdo-welfare", "telecom-phone", "CN"),
    ("10点移动灵犀口令", "xb-zuanke", "telecom-phone", "CN"),
    ("一分钱喝茶百道", "xb-zuanke", "food-drink", "CN"),
    ("美团外卖红包", "xb-today", "food-delivery", "CN"),
    ("KFC Singapore Is Serving Up a $6.50 2-Piece Chicken Meal for One Day Only", "greatdeals-sg", "food-drink", "SG"),
    ("IKEA Singapore Brings Back Its Christmas Buffet at 3 Outlets", "greatdeals-sg", "food-dine", "SG"),
    ("Firehouse Subs Medium Sub: Free w/ $15 purchase", "dealnews", "food-drink", "US"),
    ("Free K-Town Chicken Salad sando at 7-11 (US only)", "reddit-freebies", "food-drink", "US"),
    ("sc猫粮rb不到 200 需弹限时红包", "xb-today", "pets-supply", "CN"),
    ("斐乐猫爪7好价238", "xb-today", "shop-daily", "CN"),
    ("贝亲玻璃奶瓶0-6月+新生宝宝防胀气防呛奶嘴 137.4元", "xb-haodan", "kids-baby", "CN"),
    ("速度，京东家政bug大礼包", "xb-zuanke", "home-local", "CN"),
    ("论坛里那个电钻车失效了 还有另一个商品也能用200-25消费券凑单", "xb-kuan", "shop-digital", "CN"),
    ("HOKA Women's Rincon 4 Running Shoes for $62 + free shipping", "dealnews", "shop-daily", "US"),
    ("Magnetic Under Hood LED Work Light Bar 2-Pack for $36 + free shipping", "dealnews", "shop-daily", "US"),
    ("联想 WL300 蓝牙静音鼠标 5键 1600DPI $12.36", "smzdm-haitao", "shop-digital", "US"),
    ("小厨鼠旗舰店客服发送免单活动", "xb-kuan", "shop-freebie", "CN"),
    ("大聪明卡有$200 off $900机票 如何套现", "uscardforum", "travel-flight", "US"),
    ("SAFRA Members Enjoy 1-FOR-1 Universal Studios Singapore Tickets", "greatdeals-sg", "travel-trip", "SG"),
    ("住8晚，送29个月万豪白金：这届双11，会籍才值得算账", "xb-today", "travel-hotel", "CN"),
    ("松兔电站：每天赚1元以上，挂着就行！", "xb-mianfei", "earn-task", "CN"),
]


class TestClassify(unittest.TestCase):
    def test_cases(self):
        for title, source, cat, region in CASES:
            with self.subTest(title=title):
                got = run(title, source)
                self.assertEqual((got["cat"], got["region"]), (cat, region))

    def test_value(self):
        self.assertEqual(extract_value("大希地鸡排好价 3.8r一片 160g"), "3.8元")
        self.assertEqual(extract_value("新用户评论送 ¥3"), "¥3")
        self.assertEqual(extract_value("艾维诺婴儿身体乳好价，两瓶354ml40块"), "40块")
        self.assertEqual(extract_value("HSBC Rewards+ Offers up to 6% P.A. Bonus Interest on S$100,000"), "6% P.A.")
        self.assertEqual(extract_value("Huge Offer: Get S$480 Cash or 28,000 Max Miles"), "S$480")
        self.assertIsNone(extract_value("工行app搜消费季，速度"))

    def test_signal(self):
        def deal(title, source):
            return is_deal({"title": title, "url": "https://x", "tags": []}, SRC[source])

        self.assertTrue(deal("工行app搜消费季，速度", "xb-zuanke"))
        self.assertTrue(deal("摇一摇有水 快", "xb-zuanke"))
        self.assertFalse(deal("闲鱼真神奇，二手衣服一大把人要", "xb-zuanke"))
        self.assertFalse(deal("抖音招行还款优惠没了吗", "xb-zuanke"))
        self.assertFalse(deal("内存条啥时候能降价啊", "nodeseek"))
        self.assertFalse(deal("社区速递 164 | 1500 元圆梦昔日卡皇与派友们做的 AI 平替", "sspai"))
        self.assertFalse(deal("Any update on IBKR Margin Update?", "reddit-sgfi"))
        self.assertTrue(deal("Pizza Hut Offers 1-FOR-1 Melts at S$9.95", "mothership"))


if __name__ == "__main__":
    unittest.main()
