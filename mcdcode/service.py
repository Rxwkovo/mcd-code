"""Business adapters for the captured official MCP schemas.

Never infer a price from a menu label or a coupon rule. Every Quote below is
created from calculate-price.data.price, expressed in integer cents.
"""
from __future__ import annotations

import copy
import csv
import io
import re
from datetime import datetime, timezone, timedelta
from typing import Any

from .selection import Food, Quote


class DataError(ValueError):
    pass


def data_of(envelope: dict) -> Any:
    if not isinstance(envelope, dict) or "data" not in envelope:
        raise DataError("接口未返回 data；不能用猜测值继续。")
    return envelope["data"]


def name_key(value: str) -> str:
    # No fuzzy matching: preserve sizes, counts and flavor differences.
    return re.sub(r"\s+", "", str(value)).translate(str.maketrans("（）", "()"))


def parse_nutrition(value: Any) -> dict[str, int]:
    """Parse the observed TOON-style CSV table; unknown layouts stay unknown."""
    rows = value if isinstance(value, list) else []
    if isinstance(value, str):
        lines = value.strip().splitlines()
        if lines and re.fullmatch(r"\[\d+\]\{[^}]+\}:", lines[0].strip()):
            header = lines[0].split("{", 1)[1].rsplit("}", 1)[0].split(",")
            rows = [dict(zip(header, r)) for r in csv.reader(
                io.StringIO("\n".join(s.strip() for s in lines[1:])))]
    observed: dict[str, set[int]] = {}
    for row in rows:
        try:
            name, energy = row["productName"], float(row["energyKcal"])
            if energy < 0 or not energy.is_integer():
                continue
            observed.setdefault(name_key(name), set()).add(int(energy))
        except (KeyError, ValueError, TypeError):
            continue
    # Conflicting records for one exact name are deliberately excluded.
    return {key: next(iter(values)) for key, values in observed.items() if len(values) == 1}


def parse_menu(data: dict, nutrition: dict | None = None) -> list[Food]:
    if not isinstance(data, dict) or not isinstance(data.get("meals"), dict):
        raise DataError("菜单结构与已核对的 meals 映射不一致，请更新工具快照。")
    categories = {}
    for group in data.get("categories", []):
        for item in group.get("meals", []):
            categories.setdefault(str(item.get("code")), str(group.get("name", "")))
    result = []
    for code, raw in data["meals"].items():
        if not isinstance(raw, dict) or not raw.get("name"):
            continue
        result.append(Food(str(code), str(raw["name"]), categories.get(str(code), ""),
                           (nutrition or {}).get(name_key(raw["name"])), raw))
    return sorted(result, key=lambda food: (food.name, food.code))


def default_modification(detail: dict) -> dict:
    values = []
    for group in detail.get("modification", {}).get("items", []):
        for option in group.get("values", []):
            quantity = option.get("selectedQuantity", 0)
            key = option.get("selectedKey") if quantity else option.get("unselectedKey")
            if key:
                values.append({"code": str(option["code"]), "key": str(key), "quantity": quantity})
    return {"values": values} if values else {}


def default_item(code: str, detail: dict, quantity: int = 1) -> dict:
    item: dict = {"productCode": code, "quantity": quantity}
    rounds = []
    for group in detail.get("rounds", []):
        choices = []
        for choice in group.get("choices", []):
            if choice.get("isDefault") == 1:
                q = choice.get("quantity")
                if not isinstance(q, int) or q < 1:
                    raise DataError("套餐默认数量未知，请查看详情并明确选择。")
                selected = {"code": str(choice["code"]), "quantity": q}
                modification = default_modification(choice)
                if modification:
                    selected["modification"] = modification
                choices.append(selected)
        if not choices and group.get("minQuantity", 0) > 0:
            raise DataError("套餐需要选择子项；无法自动补造默认选项。")
        if choices:
            rounds.append({"round": str(group["id"]), "comboItemList": choices})
    if rounds:
        item["roundList"] = rounds
    modification = default_modification(detail)
    if modification:
        item["modification"] = modification
    return item


class OrderingService:
    def __init__(self, client):
        self.client = client
        self.context: dict = {"orderType": 1, "beType": 1}
        self.store: dict | None = None
        self.address: dict | None = None
        self.foods: list[Food] = []
        self.details: dict[str, dict] = {}
        self.nutrition: dict[str, int] = {}
        self.coupons: list[dict] = []
        self.cart: list[dict] = []
        self.quote: Quote | None = None
        self.quote_context: dict | None = None
        self.quoted_at: datetime | None = None
        self.calls: dict[str, int] = {}

    def read(self, name: str, args: dict | None = None):
        self.calls[name] = self.calls.get(name, 0) + 1
        return data_of(self.client.call_read(name, args or {}))

    def search(self, city: str, keyword: str, drive=False) -> list[dict]:
        return self.read("query-nearby-stores", {
            "city": city, "keyword": keyword, "searchType": 2, "beType": 5 if drive else 1})

    def choose_store(self, store: dict, be_type=1):
        if not store.get("storeCode"):
            raise DataError("门店编码未知。")
        self.store = copy.deepcopy(store)
        self.context = {"storeCode": str(store["storeCode"]),
                        "orderType": 1 if be_type in (1, 5) else 2, "beType": be_type}
        if be_type != 1:
            if not store.get("beCode"):
                raise DataError("该点餐方式缺少官方 beCode。")
            self.context["beCode"] = str(store["beCode"])
        self.foods, self.details, self.cart, self.coupons = [], {}, [], []
        self.invalidate_quote()

    def invalidate_quote(self):
        self.quote = self.quote_context = self.quoted_at = None

    def load_menu(self) -> list[Food]:
        self.require_store()
        self.foods = parse_menu(self.read("query-meals", self.context), self.nutrition)
        return self.foods

    def load_nutrition(self):
        self.nutrition = parse_nutrition(self.read("list-nutrition-foods"))
        for food in self.foods:
            food.kcal = self.nutrition.get(name_key(food.name))

    def require_store(self):
        if not self.store:
            raise DataError("请先 /order 搜店 城市 关键词，然后选择门店。")

    def detail(self, code: str) -> dict:
        self.require_store()
        if code not in self.details:
            self.details[code] = self.read("query-meal-detail", {**self.context, "code": code})
        return self.details[code]

    def prepare_items(self, items: list[dict]) -> list[dict]:
        if not items:
            raise DataError("购物车为空。")
        menu_codes = {food.code for food in self.foods}
        result = []
        for entry in items:
            code, quantity = str(entry.get("productCode", "")), entry.get("quantity")
            if code not in menu_codes:
                raise DataError("商品必须来自当前门店真实菜单。")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 20:
                raise DataError("每项数量必须为 1～20。")
            prepared = default_item(code, self.detail(code), quantity)
            # Explicit selection from current official coupon-product mapping only.
            if entry.get("couponId"):
                valid = next((c for c in self.coupons if str(c.get("couponId")) == str(entry["couponId"])
                              and any(str(p.get("productCode")) == code for p in c.get("products", []))), None)
                if not valid:
                    raise DataError("优惠券未通过当前门店适用商品映射核对。")
                prepared.update(couponId=str(valid["couponId"]), couponCode=str(valid["couponCode"]))
            result.append(prepared)
        return result

    def load_store_coupons(self):
        self.require_store()
        self.coupons = self.read("query-store-coupons", self.context)
        if not isinstance(self.coupons, list):
            raise DataError("门店券结构未知。")
        return self.coupons

    def calculate(self, items: list[dict], *, remember=False, score=0) -> Quote:
        self.require_store()
        prepared = self.prepare_items(items)
        args = {**self.context, "items": prepared, "needTableware": False}
        if self.context["beType"] == 6:
            raise DataError("第一版暂不执行企业团餐；助餐服务需另行选择。")
        raw = self.read("calculate-price", args)
        cents = raw.get("price") if isinstance(raw, dict) else None
        if isinstance(cents, bool) or not isinstance(cents, int) or cents < 0:
            raise DataError("官方试算价格未知，不展示推测金额。")
        quote = Quote(prepared, cents, raw, score=score)
        if remember:
            self.cart = copy.deepcopy(prepared)
            self.quote = quote
            self.quote_context = copy.deepcopy(self.context)
            self.quoted_at = datetime.now(timezone.utc)
        return quote

    def quote_candidates(self, candidates, max_calls=24) -> tuple[list[Quote], list[str]]:
        """Quote baseline + one eligible coupon per basket. No local stacking rules."""
        quoted, failures = [], []
        pending = [(candidate.items, candidate.score) for candidate in candidates]
        # Baselines first: coupon variants must not crowd out budget singles.
        for candidate in candidates:
            for index, entry in enumerate(candidate.items):
                coupon = next((c for c in self.coupons if c.get("couponCode") and any(
                    str(p.get("productCode")) == entry["productCode"] for p in c.get("products", []))), None)
                if coupon:
                    with_coupon = copy.deepcopy(candidate.items)
                    with_coupon[index]["couponId"] = str(coupon["couponId"])
                    pending.append((with_coupon, candidate.score))
                    break  # finite, transparent search; no guessed coupon stacking
        for items, score in pending:
            if len(quoted) + len(failures) >= max_calls:
                return quoted, failures
            try:
                quoted.append(self.calculate(items, score=score))
            except Exception as exc:
                from .mcp import AuthError, RateLimitError
                if isinstance(exc, (AuthError, RateLimitError)):
                    raise
                failures.append(type(exc).__name__)
        return quoted, failures

    def choose_quote(self, quote: Quote):
        # Refresh to avoid using an old recommendation or stale total for checkout.
        return self.calculate(quote.items, remember=True, score=quote.score)

    def checkout_args(self, take_way: str | None = None) -> dict:
        if not self.quote or self.quote_context != self.context or not self.quoted_at:
            raise DataError("请先官方算价。")
        if datetime.now(timezone.utc) - self.quoted_at > timedelta(minutes=3):
            raise DataError("试算已超过三分钟，请重新算价后预览订单。")
        args = {**self.context, "items": copy.deepcopy(self.quote.items), "needTableware": False}
        if self.context["orderType"] == 1:
            options = self.quote.raw.get("takeWayList", [])
            if not take_way or not any(str(o.get("code")) == take_way for o in options):
                raise DataError("请选择官方算价返回的取餐方式 code。")
            args["takeWayCode"] = take_way
        else:
            if not self.address or not self.address.get("addressId"):
                raise DataError("请先选择外送地址。")
            args["addressId"] = str(self.address["addressId"])
        return args

    def local_date(self):
        # Beijing and the client's requested timezone both use UTC+08:00.
        return datetime.now(timezone(timedelta(hours=8))).date().isoformat()

    def item_labels(self, items: list[dict]) -> list[str]:
        lookup = {f.code: f.name for f in self.foods}
        return [f"{lookup.get(item['productCode'], '未知餐品')} × {item['quantity']}"
                + (" [使用门店券]" if item.get("couponId") else "") for item in items]
