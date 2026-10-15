"""Static, self-contained SVG day cards made from successful price quotes."""
from __future__ import annotations

import base64
from datetime import date
from html import escape
import os
from pathlib import Path
import tempfile
import unicodedata

from .service import DataError

ROOT = Path(__file__).resolve().parents[1]
CHARACTERS = (
    ("01-grape", "团子蛙", "今日圆度达标。\n甜品也得跟上我的体型！"),
    ("02-cherry", "招手蛙", "菜单我看过了。\n甜甜的，都给我打个招呼！"),
    ("03-orange", "鼠鼠蛙", "耳朵收到消息：\n今天的奶味浓度还可以！"),
    ("04-lemon", "咯咯蛙", "吃饱再叫醒我。\n我的快乐闹钟只认甜品！"),
    ("05-kiwi", "笑狗蛙", "笑得嘴都合不上了。\n这口奶味，值得再闻两下！"),
    ("06-tomato", "奔跑蛙", "四条腿都准备好了。\n奔向甜品区，启动！"),
    ("07-peach", "蹦跶蛙", "先蹦一下再吃。\n快乐没有热身就不能开机！"),
    ("08-pineapple", "抱手蛙", "我就抱着手等。\n谁也别动我的圆滚滚小食！"),
    ("09-coconut", "祈祷蛙", "愿今天的烦恼少一点。\n奶味和甜味，多一点！"),
    ("10-halfmelon", "捧腹蛙", "甜甜的先入栈，圆滚滚的不能丢。\n这顿快乐，编译通过！"),
    ("11-watermelon", "飞天蛙", "吃完这口我就起飞。\n先声明：不是价格飞了！"),
)


def character_for_day(day):
    """All eleven images appear once per eleven days; no host RNG needed."""
    return CHARACTERS[date.fromisoformat(day).toordinal() % len(CHARACTERS)]


def clean(value):
    value = str(value)
    token = os.environ.get("MCD_TOKEN")
    if token:
        value = value.replace(token, "[已隐藏]")
    return "".join(c for c in value if c == "\n" or not unicodedata.category(c).startswith("C"))


def wrap(value, width=44):
    rows, row, units = [], "", 0
    for char in clean(value):
        size = 2 if unicodedata.east_asian_width(char) in "WF" else 1
        if char == "\n" or units + size > width:
            rows.append(row)
            row, units = "", 0
        if char != "\n":
            row += char
            units += size
    if row:
        rows.append(row)
    return rows or [""]


def export_card(quote, service, output_dir):
    """No pricing rules and no network or write-tool calls live here."""
    if (isinstance(quote.cents, bool) or not isinstance(quote.cents, int)
            or quote.cents < 0 or quote.raw.get("price") != quote.cents):
        raise DataError("日卡需要一次成功的 calculate-price 报价。")
    lookup = {food.code: food.name for food in service.foods}
    if not quote.items or any(item.get("productCode") not in lookup for item in quote.items):
        raise DataError("日卡餐品必须来自当前门店菜单。")
    day = service.local_date()
    date.fromisoformat(day)
    character_id, character_name, quip = character_for_day(day)
    names = [f"{lookup[item['productCode']]} × {item['quantity']}" for item in quote.items]
    rows = [row for name in names for row in wrap(name)]
    if len(rows) > 10:
        raise DataError("餐品名称过长，无法完整放入日卡；未导出截断餐名的卡片。")
    price = f"{quote.cents // 100}.{quote.cents % 100:02d}"
    discount = quote.raw.get("discount")
    selected_coupon = any(item.get("couponId") or item.get("couponCode") for item in quote.items)
    label = ("券后价 · 官方试算" if selected_coupon and isinstance(discount, int)
             and not isinstance(discount, bool) and discount > 0 else
             "官方试算价 · 未用券" if not selected_coupon else "官方试算价 · 优惠以接口为准")
    marker = "官方试算 · 尚未下单"
    image = ""
    portrait = ROOT / "assets" / "characters" / (character_id + ".png")
    if not portrait.is_file():
        portrait = ROOT / "assets" / "nawa.png"
    if portrait.is_file():
        blob = portrait.read_bytes()
        if blob.startswith(b"\x89PNG\r\n\x1a\n") and len(blob) <= 512 * 1024:
            uri = base64.b64encode(blob).decode("ascii")
            image = f'<image x="683" y="222" width="330" height="330" href="data:image/png;base64,{uri}"/>'
    def text(x, y, content, size=30, fill="#30241e", extra=""):
        return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(clean(content))}</text>'
    font_size = 34 if len(rows) <= 6 else 27
    gap = 47 if len(rows) <= 6 else 33
    food_text = "".join(text(96, 840 + i * gap, row, font_size) for i, row in enumerate(rows))
    store = (service.store or {}).get("storeName", "门店未知")
    store_lines = wrap(store, 54)
    store_text = "".join(text(96, 1170 + i * 27, row, 22, "#78695e") for i, row in enumerate(store_lines[:2]))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">
<title>奶蛙今日想吃 · {escape(day)} · {escape(marker)}</title>
<desc>{escape(clean(' + '.join(names)))}；{escape(label)} {price} 元；{escape(marker)}</desc>
<rect width="1080" height="1440" fill="#fff4df"/>
<g font-family="Microsoft YaHei,PingFang SC,Noto Sans CJK SC,sans-serif">
<path d="M0 0H1080V294Q1080 360 1014 360H0Z" fill="#da291c"/>
{text(64, 72, 'MCD CODE   /   ' + day, 25, '#ffdc80')}
{text(60, 181, '奶蛙今日想吃', 76, '#ffbc0d', 'font-weight="800"')}
{text(65, 255, marker, 29, '#fff4df')}
<rect x="884" y="47" width="132" height="48" rx="24" fill="#ffbc0d"/>
{text(909, 81, '1024', 29, '#a31814', 'font-weight="800"')}
{image}
{text(65, 436, 'DAILY', 61, '#da291c', 'font-weight="800"')}
{text(68, 481, '今日份快乐 / 已入队', 24, '#78695e')}
{text(68, 522, '今日主角 · ' + character_name, 25, '#a42318')}
<rect x="56" y="564" width="968" height="668" rx="36" fill="#fffdf7" stroke="#f1dfbc" stroke-width="2"/>
{text(96, 626, label, 27, '#78695e')}
{text(90, 750, '¥ ' + price, 108, '#da291c', 'font-weight="800"')}
<path d="M96 784H984" stroke="#eddfc6" stroke-width="2"/>
{food_text}{store_text}
{text(66, 1302, '“' + quip.splitlines()[0], 31, '#a42318', 'font-weight="700"')}
{text(66, 1349, quip.splitlines()[1] + '”', 31, '#a42318', 'font-weight="700"')}
{text(66, 1402, '麦门 Code · 个人独立开发 · 非麦当劳官方产品', 21, '#8c7b69')}
</g></svg>'''
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"nawa-{day}.svg"
    # Only a complete file replaces today's prior card; failed writes leave no half SVG.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".tmp",
                                         dir=directory, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(svg)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"type": "svg", "path": str(target.resolve()), "date": day,
            "width": 1080, "height": 1440, "mode": "live", "price_cents": quote.cents,
            "character_id": character_id, "character_name": character_name}
