"""Interactive, read-first terminal command router; no LLM API needed."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import shlex
import sys
from itertools import combinations
from datetime import datetime, timezone, timedelta

from .mcp import MCPClient, MCPError, AuthError, RateLimitError
from .safety import ConfirmationGateway, SafetyError
from .selection import (Candidate, amount_to_cents, candidate_baskets, best_under_budget,
                        nearest_quote, calorie_candidates, nearest_points, is_drink, is_mascot_main)
from .service import OrderingService, DataError
from .location import UserLocation, load_location, save_location, choose_nearest, LocationError
from .ui import banner, laugh, render_card, safe_text, theme_text, initialize_terminal
from .structured import envelope, dumps, error_code
from .day_card import export_card
from .preferences import PreferenceMemory

ROOT = Path(__file__).resolve().parents[1]
HELP = [
    "/coupons [可领|已有|领取|门店]    查询或确认领券",
    "/order 搜店 城市 附近地标       搜索到店门店",
    "/order 门店 1 · /order 菜单     选择门店与菜单",
    "/order 详情 CODE · /order 加 CODE [数量]",
    "/order 算价 · /order 下单 取餐方式code",
    "/order 地址 · /order 选地址 1 · /order 外送店",
    "/order 查单 ID · /order 取消 ID 原因code",
    "/budget 30                     官方核价后找预算方案",
    "/1024 [热量|24|102.4|积分]      搜索最接近目标",
    "/奶蛙 [预算30] [--card]         大笑、推荐、可选导出 SVG 日卡",
    "/pick 1                        选推荐并重新算价",
    "/points [兑换 SPU_ID SKU_ID]    查询积分商城/预览兑换",
    "/confirm 确认码 · /abort        确认一次写操作/放弃",
    "/status · /events · /tools · /help · /quit",
    "/achievements · /成就          本机成就与解锁进度",
    "/偏好 [记住 内容|忘掉 关键词|暂停|恢复|清空]",
    "/location 城市 附近地标        更新位置，自动选最近营业门店",
]


def money(cents):
    return f"{cents // 100}.{cents % 100:02d} 元"


class App:
    def __init__(self, *, client=None, state_dir=None, json_output=False, card_dir=None):
        if getattr(client, "is_demo", False):
            raise DataError("正式入口仅连接真实接口。")
        self.client = client
        self.service = None
        self.gateway = None
        self.pending = None
        self.state_dir = state_dir or (ROOT / ".local" / "state")
        self.stores = []
        self.store_mode = 1
        self.addresses = []
        self.recommendations = []
        self.points_products = []
        self.cart = []
        self.running = True
        self.json_output = json_output
        self.card_dir = Path(card_dir) if card_dir is not None else ROOT / "outputs"
        self.result_data = {}
        self.messages = []
        self.artifacts = []

    def set_data(self, **values):
        self.result_data.update(copy.deepcopy(values))

    def items_data(self, items):
        lookup = {food.code: food for food in self.service.foods} if self.service else {}
        return [{**copy.deepcopy(item), "name": lookup[item["productCode"]].name
                 if item["productCode"] in lookup else None} for item in items]

    def quote_data(self, quote):
        return {"items": self.items_data(quote.items), "price_cents": quote.cents,
                "price_source": "calculate-price",
                "raw": copy.deepcopy(quote.raw)}

    def emit(self, text):
        if self.json_output:
            self.messages.append(self.redact(str(text)))
            return
        for line in str(text).splitlines() or [""]:
            print(theme_text(self.redact(line), "body"))

    def redact(self, value):
        token = os.environ.get("MCD_TOKEN")
        return str(value).replace(token, "[已隐藏]") if token else str(value)

    def card(self, title, lines):
        if self.json_output:
            self.messages.extend([self.redact(title)] + [self.redact(line) for line in lines])
            return
        print(render_card(self.redact(title), [self.redact(line) for line in lines]))

    def connect(self):
        if self.service:
            return self.service
        self.client = self.client or MCPClient.from_env()
        self.client.initialize()
        self.client.list_tools()
        self.service = OrderingService(self.client)
        self.gateway = ConfirmationGateway(self.client, self.state_dir)
        return self.service

    def show_achievements(self):
        path = ROOT / ".local" / "player-state.json"
        if not path.exists():
            self.set_data(achievements=None)
            return self.card("麦门玩家档案", ["还没有玩家记录。使用 Skill 时，模型会帮你记录次数和起趣味称号。",
                             "可以统计点餐次数、常点餐品、挑战达成和奶蛙大笑次数；玩法由模型自由发挥。"])
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise DataError("玩家记录暂时无法读取，可让 Skill 模型检查本机记录。") from None
        self.set_data(achievements=state)
        self.card("麦门玩家档案 · 称号由 Skill 模型创作", [json.dumps(state, ensure_ascii=False, indent=2),
                  "本机趣味记录，不是麦当劳积分或会员权益。"])

    def preferences_command(self, args):
        memory = PreferenceMemory(ROOT)
        state = memory.update(args[0], " ".join(args[1:])) if args else memory.load()
        self.set_data(preferences=state)
        lines = ["奶蛙会记住你的口味，越点越懂你。",
                 "记忆已启用。" if state["enabled"] else "记忆已暂停；不用于推荐，也不自动记录新订单。"]
        lines.extend("你告诉奶蛙：" + note for note in state["notes"])
        for choice in state["order_choices"]:
            names = " + ".join(f"{item['name']} ×{item['quantity']}" for item in choice.get("items", []))
            lines.append("曾确认选择：" + names + "（支付未核实，不等于常吃）")
        if not state["notes"] and not state["order_choices"]:
            lines.append("还没有口味记录；奶蛙先听你说，不猜。")
        lines.append("Skill 会参考记录选餐；当前要求优先。可记住、忘掉、暂停、恢复或清空。")
        return self.card("奶蛙的口味小本本 · 仅本机保存", lines)

    def abort(self):
        if self.pending and self.gateway:
            self.gateway.cancel(self.pending)
        self.pending = None

    def preview(self, tool, args, summary):
        self.abort()
        self.pending = self.gateway.preview(tool, args, summary)
        self.set_data(operation=tool)
        if tool == "create-order" and self.service.quote:
            self.set_data(quote=self.quote_data(self.service.quote))
        self.card("待确认 · 尚未执行", [summary, "五分钟内输入：/confirm " + self.pending.code,
                                            "不确认不会执行；/abort 放弃。"])

    def status(self):
        service = self.connect()
        values = []
        account, coupon_result, count = None, None, None
        try:
            account = service.read("query-my-account")
            point = account.get("availablePoint")
            if point is not None:
                values.append("积分 " + str(point))
        except MCPError as exc:
            if self.json_output and isinstance(exc, (AuthError, RateLimitError)):
                raise
            pass
        try:
            coupons = service.read("query-my-coupons", {"page": "1", "pageSize": "200"})
            coupon_result = coupons
            # enable is an asset-level flag, not a promise for a particular order.
            total_pages = coupons.get("totalPages")
            owned = coupons.get("coupons", [])
            if total_pages == 1:
                count = sum(c.get("enable") == 1 for c in owned)
                values.append(f"卡包可用券 {count}（以门店核验为准）")
            elif isinstance(total_pages, int) and total_pages > 1:
                values.append(f"卡包券总数 {coupons.get('totalCount', '未知')}（可用数未知）")
        except MCPError as exc:
            if self.json_output and isinstance(exc, (AuthError, RateLimitError)):
                raise
            pass
        self.set_data(account=account, coupons=coupon_result, available_coupon_count=count)
        return values

    def ensure_menu(self):
        service = self.connect()
        if not service.store:
            location = load_location(ROOT)
            if location is None:
                raise DataError("告诉我城市和附近地标，就能自动选最近营业门店。可输入 /location 城市 地标。")
            store = choose_nearest(service, location)
            self.emit(f"按{location.source}「{location.city}·{location.keyword}」自动选择最近营业门店："
                      f"{store['storeName']} · {store.get('address', '地址未知')} · 距离 {store['distance']} 米")
        service.require_store()
        if not service.foods:
            service.load_menu()
        return service

    def coupons_command(self, args):
        service = self.connect()
        action = args[0] if args else "可领"
        if action in ("可领", "available"):
            rows = service.read("available-coupons")
            self.set_data(coupons=rows, kind="available")
            self.card("可领取优惠券", [str(c.get("couponName", "未知")) + " · " + str(c.get("label", "")) for c in rows]
                      + ["领取需 /coupons 领取，再明确确认。"])
        elif action in ("已有", "mine"):
            lines = []
            owned = []
            for page in range(1, 6):
                result = service.read("query-my-coupons", {"page": str(page), "pageSize": "200"})
                owned.extend(result.get("coupons", []))
                lines.extend(str(c.get("title", "未知")) + " · " + str(c.get("datetimeText", "有效期未知"))
                             for c in result.get("coupons", []))
                if page >= result.get("totalPages", 1):
                    break
            self.set_data(coupons=owned, kind="owned", pages_read=page,
                          total_pages=result.get("totalPages"), total_count=result.get("totalCount"))
            self.card("我的券 · 当前订单需另行核验", lines or ["未返回优惠券。"])
        elif action in ("领取", "claim"):
            rows = service.read("available-coupons")
            self.preview("auto-bind-coupons", {}, "领取麦麦省当前全部可领券：" + "、".join(str(c.get("couponName", "未知")) for c in rows))
        elif action in ("门店", "store"):
            rows = self.ensure_menu().load_store_coupons()
            self.set_data(coupons=rows, kind="store")
            self.card("当前门店可用券", [f"{i}. {c.get('title', '未知')} · 适用 " +
                      "、".join(p.get("productName", "未知") for p in c.get("products", []))
                      for i, c in enumerate(rows, 1)] or ["未返回可用券。"])
        else:
            raise DataError("用法：/coupons 可领|已有|领取|门店")

    def order_command(self, args):
        if not args:
            return self.order_command(["菜单"])
        service = self.connect()
        action, rest = args[0], args[1:]
        if action in ("搜店", "find", "得来速"):
            if len(rest) < 2:
                raise DataError("用法：/order 搜店 城市 位置关键词")
            self.store_mode = 5 if action == "得来速" else 1
            self.stores = service.search(rest[0], " ".join(rest[1:]), self.store_mode == 5)
            self.show_stores()
        elif action in ("门店", "store"):
            index = int(rest[0]) - 1
            if not 0 <= index < len(self.stores):
                raise DataError("请从本次搜索结果选择门店序号。")
            self.abort()
            service.choose_store(self.stores[index], self.store_mode)
            self.cart, self.recommendations = [], []
            lines = [service.store["storeName"], service.store.get("address", "地址未知"),
                     "门店 code: " + service.context["storeCode"], "/order 菜单 查看在售餐品。"]
            if service.context.get("beCode"):
                lines.append("业务 beCode: " + service.context["beCode"])
            # Upstream requires all advertised reservation windows to be shown.
            for option in service.store.get("reservationTimeOptions", []):
                lines.append(str(option.get("date", "未知")) + (" (今天) " if option.get("today") else " ")
                             + str(option.get("reservationOptionText", "未知")))
            self.card("已选择门店", lines)
        elif action in ("菜单", "menu"):
            service = self.ensure_menu()
            service.load_menu()
            self.set_data(menu=[{"product_code": f.code, "name": f.name, "category": f.category,
                                 "kcal": f.kcal} for f in service.foods])
            self.card("当前门店菜单", [f"{f.code}  {f.name} · {f.category or '分类未知'} · 热量 " +
                      (f"{f.kcal} kcal" if f.kcal is not None else "未知") for f in service.foods]
                      + ["价格请选餐后 /order 算价；菜单标价不作为应付金额。"])
        elif action in ("详情", "detail"):
            service = self.ensure_menu()
            detail = service.detail(rest[0])
            self.set_data(detail=detail)
            lines = [str(detail.get("name", "未知")) + ("【可特调】" if detail.get("supportModify") else "")]
            for group in detail.get("rounds", []):
                lines.append(str(group.get("name", "未知")) + ": " + " / ".join(
                    str(c.get("name", "未知")) + (" [默认]" if c.get("isDefault") == 1 else "")
                    + ("【可特调】" if c.get("supportModify") else "") for c in group.get("choices", [])))
            lines.append("第一版按接口默认组合下单；不自动替换套餐子项。")
            self.card("餐品详情", lines)
        elif action in ("加", "add"):
            service = self.ensure_menu()
            code, qty = rest[0], int(rest[1]) if len(rest) > 1 else 1
            item = service.prepare_items([{"productCode": code, "quantity": qty}])[0]
            self.abort()
            self.cart.append(item)
            service.invalidate_quote()
            self.set_data(cart=self.items_data(self.cart))
            self.card("购物车 · 尚未下单", service.item_labels(self.cart))
        elif action in ("清空", "clear"):
            self.abort()
            self.cart = []
            service.invalidate_quote()
            self.set_data(cart=[])
            self.emit("购物车已清空。")
        elif action in ("用券", "coupon"):
            service = self.ensure_menu()
            if len(rest) != 2:
                raise DataError("用法：/order 用券 购物车序号 门店券序号（先 /coupons 门店）")
            item_idx, coupon_idx = int(rest[0])-1, int(rest[1])-1
            if not (0 <= item_idx < len(self.cart) and 0 <= coupon_idx < len(service.coupons)):
                raise DataError("请选择有效序号。")
            changed = copy.deepcopy(self.cart)
            changed[item_idx]["couponId"] = str(service.coupons[coupon_idx]["couponId"])
            changed = service.prepare_items(changed)
            self.abort()
            self.cart = changed
            service.invalidate_quote()
            self.set_data(cart=self.items_data(self.cart))
            self.emit("已选择券；优惠是否成立由下一次官方算价决定。")
        elif action in ("算价", "price"):
            self.abort()
            quote = service.calculate(self.cart, remember=True)
            self.show_quote(quote, "官方试算")
        elif action in ("下单", "checkout"):
            args = service.checkout_args(rest[0] if rest else None)
            self.preview("create-order", args, f"{service.store['storeName']} · " +
                         "、".join(service.item_labels(service.quote.items)) + f" · 试算 {money(service.quote.cents)} · "
                         + ("取餐方式 " + args["takeWayCode"] if args["orderType"] == 1 else "配送到已选择地址")
                         + "。确认后仅创建订单，支付由你完成。")
        elif action in ("地址", "addresses"):
            result = service.read("delivery-query-addresses")
            self.addresses = result.get("addresses", [])
            self.set_data(addresses=self.addresses)
            self.card("已保存配送地址", [f"{i}. {a.get('address', '地址未知')} {a.get('addressDetail', '')}"
                                          for i, a in enumerate(self.addresses, 1)] or ["没有地址；请先在官方 App 添加。"])
        elif action in ("选地址", "address"):
            index = int(rest[0])-1
            if not 0 <= index < len(self.addresses):
                raise DataError("请从已查询的地址列表选择。")
            self.abort()
            service.address = copy.deepcopy(self.addresses[index])
            self.set_data(selected_address=service.address)
            # A different address requires a new delivery-store query and choice.
            if service.context.get("orderType") == 2:
                service.store = None
                service.context = {"orderType": 1, "beType": 1}
                service.foods, service.details, service.coupons = [], {}, []
                service.cart = []
                self.cart, self.recommendations = [], []
            self.stores = []
            service.invalidate_quote()
            self.emit("地址已选择，下一步 /order 外送店。")
        elif action in ("外送店", "delivery"):
            if not service.address or not service.address.get("addressId"):
                raise DataError("先 /order 地址，再 /order 选地址 序号。")
            self.store_mode = 2
            self.stores = service.read("delivery-query-stores", {"addressId": str(service.address["addressId"]), "beType": 2})
            self.show_stores()
        elif action in ("查单", "query"):
            result = service.read("query-order", {"orderId": rest[0]})
            self.set_data(order=result)
            self.card("订单查询", [f"{key}: {result[key]}" for key in
                      ("orderId", "orderStatus", "status", "storeName", "pickupCode") if key in result])
        elif action in ("历史", "history"):
            result = service.read("order-list")
            self.set_data(orders=result)
            self.card("历史点餐订单", [json.dumps(result, ensure_ascii=False)])
        elif action in ("取消", "cancel"):
            if len(rest) != 2 or rest[1] not in {"1", "2", "3", "4", "5", "-1"}:
                raise DataError("用法：/order 取消 订单ID 原因code（1改主意/2重复/3餐品有误/4地址有误/5时间有误/-1其他）")
            detail = service.read("query-order", {"orderId": rest[0]})
            self.preview("cancel-order", {"orderId": rest[0], "cancelReasonCode": rest[1]},
                         f"取消订单 {rest[0]} · {detail.get('storeName', '门店未知')} · 原因 {rest[1]}")
        else:
            raise DataError("未知点餐子命令，/order 查看帮助。")

    def show_stores(self):
        self.set_data(stores=self.stores)
        self.card("门店搜索 · 请选择", [f"{i}. {s.get('storeName', '未知')} · {s.get('address', '地址未知')}"
                  + f" · code {s.get('storeCode', '未知')}" for i, s in enumerate(self.stores, 1)]
                  + ["/order 门店 序号"])

    def show_quote(self, quote, title):
        self.set_data(quote=self.quote_data(quote))
        lines = self.service.item_labels(quote.items) + ["合计 " + money(quote.cents), "热量：未知（未核对的规格不猜测）"]
        for option in quote.raw.get("takeWayList", []):
            lines.append(f"取餐 {option.get('code', '未知')} = {option.get('title', '未知')}")
        lines.append("尚未下单。先 /order 下单 取餐code，再 /confirm 确认码。")
        self.card(title, lines)

    def recommend(self, amount=None, mascot=False, target=None):
        service = self.ensure_menu()
        service.load_store_coupons()
        candidates = candidate_baskets(service.foods, limit=16, seed=service.local_date(), mascot=mascot)
        self.emit(f"正在试算 {len(candidates)} 个候选；最多 24 次官方价格请求。")
        quotes, failures = service.quote_candidates(candidates, max_calls=20)
        # Use already observed single quotes only to prioritize new trials.
        # Their sum is NEVER displayed as a combination's final price.
        if amount is not None or target is not None:
            singles = [q for q in quotes if len(q.items) == 1 and not q.items[0].get("couponId")]
            foods = {food.code: food for food in service.foods}
            existing = {tuple(sorted(item["productCode"] for item in c.items)) for c in candidates}
            adaptive = []
            for a, b in combinations(singles, 2):
                first, second = a.items[0]["productCode"], b.items[0]["productCode"]
                key = tuple(sorted((first, second)))
                if first == second or key in existing:
                    continue
                if mascot and not ((is_mascot_main(foods[first]) and is_drink(foods[second])) or
                                    (is_mascot_main(foods[second]) and is_drink(foods[first]))):
                    continue
                estimate = a.cents + b.cents
                priority = (abs(estimate-target) if target is not None else
                            (estimate > amount, estimate))
                adaptive.append((priority, key, Candidate(a.items+b.items, "自适应官方试算", 100 if mascot else 20)))
            adaptive.sort(key=lambda row: (row[0], row[1]))
            remaining = 24-len(quotes)-len(failures)
            extra, failed = service.quote_candidates([row[2] for row in adaptive[:min(4, remaining)]],
                                                      max_calls=min(4, remaining))
            quotes.extend(extra)
            failures.extend(failed)
        chosen = ([nearest_quote(quotes, target)] if target is not None else
                  best_under_budget(quotes, amount)[:3] if amount is not None else quotes[:1])
        chosen = [q for q in chosen if q is not None]
        self.recommendations = chosen
        self.set_data(recommendations=[self.quote_data(q) for q in chosen], budget_cents=amount,
                      target_cents=target, quote_count=len(quotes), failure_count=len(failures),
                      delta_cents=(chosen[0].cents-target if chosen and target is not None else None))
        lines = []
        for index, quote in enumerate(chosen, 1):
            lines.append(f"方案 {index} · {money(quote.cents)}")
            lines.extend(service.item_labels(quote.items))
            if target is not None:
                delta = quote.cents-target
                lines.append("恰好命中！" if delta == 0 else f"差 {money(abs(delta))}（{'超出' if delta > 0 else '还差'}）")
        if not chosen:
            lines.append("本次已核价候选里没有符合条件的方案。可调整预算或门店。")
        if mascot:
            lines.append("奶蛙：甜甜的先入栈，圆滚滚的不能丢！嘿嘿嘿～")
        if target is not None:
            lines.append("DEBUG: 目标没崩，餐价没有按我的断点运行。")
        lines.extend([f"已核价 {len(quotes)} 次；失败/未知 {len(failures)} 次。仅比较本次有限候选。",
                      "同日相同菜单与条件结果稳定；门店、优惠和库存会改变结果。",
                      "/pick 序号 选方案并重新算价；之后仍需预览和明确确认。"])
        self.card("奶蛙今天最想吃的套餐" if mascot else "目标试算" if target else "预算方案", lines)

    def points_command(self, args):
        service = self.connect()
        if not args:
            products = service.read("mall-points-products", {"catRuleIds": "1>4"})
            self.points_products = products
            self.set_data(products=products)
            self.card("积分商城 · 列表不代表最终可兑换", [f"SPU {p.get('spuId', '未知')} · {p.get('spuName', '未知')} · "
                       f"{p.get('point', '未知')} 积分 · 金额 {p.get('price', '未知')} · 截止 {p.get('downTime', '未知')}"
                       for p in products])
        elif args[0] == "兑换" and len(args) == 3:
            spu, sku_id = int(args[1]), int(args[2])
            detail = service.read("mall-product-detail", {"spuId": spu})
            if detail.get("shopId") != 2 or str(detail.get("spuCategory")) != "1":
                raise DataError("第一版仅支持不依赖地址的商城虚拟券兑换。")
            sku = next((s for s in detail.get("skuList", []) if s.get("skuId") == sku_id), None)
            if not sku:
                raise DataError("SKU 未在官方详情中找到。")
            self.preview("mall-create-order", {"skuId": sku_id, "spuCategory": "1", "count": 1},
                         f"兑换 {detail.get('spuName', '未知')} · SKU {sku_id} · {sku.get('points', '未知')} 积分 · "
                         f"额外金额 {sku.get('price', '未知')} · 券核销另付 {sku.get('extTradePrice', '未知')}")
            self.set_data(product=detail, sku=sku)
        elif args[0] == "详情" and len(args) == 2:
            detail = service.read("mall-product-detail", {"spuId": int(args[1])})
            self.set_data(detail=detail)
            self.card("商城商品详情", [str(detail.get("spuName", "未知")), str(detail.get("note", "")),
                      json.dumps(detail.get("skuList", []), ensure_ascii=False)])
        else:
            raise DataError("/points 或 /points 详情 SPU_ID 或 /points 兑换 SPU_ID SKU_ID")

    def challenge(self, mode):
        if mode in ("24", "24.00", "102.4", "102.40"):
            return self.recommend(target=amount_to_cents(mode))
        service = self.ensure_menu() if mode in ("热量", "kcal") else self.connect()
        if mode in ("热量", "kcal"):
            service.load_nutrition()
            candidates = calorie_candidates(service.foods)
            lines, choices = [], []
            normalized = []
            for foods, kcal in candidates:
                try:
                    quote = service.calculate([{"productCode": f.code, "quantity": 1} for f in foods])
                except (MCPError, DataError):
                    continue
                choices.append(quote)
                delta = abs(kcal-1024)
                normalized.append({**self.quote_data(quote), "kcal": kcal,
                                   "delta_kcal": kcal-1024, "achieved": delta <= 50})
                achieved = "约 1024 kcal · 挑战达成" if delta <= 50 else "当前搜索范围最接近"
                lines.extend([" + ".join(f.name for f in foods),
                              f"{achieved} · {kcal} kcal · 差 {delta} kcal · {money(quote.cents)}"])
            self.recommendations = choices
            self.set_data(recommendations=normalized, target_kcal=1024, tolerance_kcal=50)
            self.card("约 1024 kcal 挑战 · 允许 ±50 kcal", lines + ["目标允许 ±50 kcal（约 5%）；差值仅供参考。",
                      "使用可核对的官方营养数据；未匹配的热量为未知。",
                      "最多 48 个已知餐品，每组合最多 3 个不同餐品；最接近仅指该搜索范围。",
                      "DEBUG: 近似就能通过断言，不拿一两卡为难午餐。/pick 序号 选择。"])
        elif mode in ("积分", "points"):
            from decimal import Decimal, InvalidOperation
            products = service.read("mall-points-products", {"catRuleIds": "1>4"})
            normalized = []
            zone = timezone(timedelta(hours=8))
            now = datetime.now(zone)
            def product_time(value):
                parsed = datetime.fromisoformat(value)
                return parsed.replace(tzinfo=zone) if parsed.tzinfo is None else parsed.astimezone(zone)
            for p in products[:16]:
                try:
                    if p.get("status") != 2 or p.get("shopId") != 2:
                        continue
                    if p.get("downTime") and product_time(p["downTime"]) < now:
                        continue
                    if p.get("upTime") and product_time(p["upTime"]) > now:
                        continue
                    detail = service.read("mall-product-detail", {"spuId": p["spuId"]})
                    for sku in detail.get("skuList", []):
                        point = Decimal(str(sku.get("points")))
                        cash = Decimal(str(sku.get("price")))
                        if point >= 0 and point == point.to_integral_value() and cash == 0:
                            normalized.append({"code": str(p["spuId"]), "name": p.get("spuName", "未知"),
                                               "sku": sku["skuId"], "points": int(point), "cash_cents": 0,
                                               "redeem_extra": sku.get("extTradePrice", "未知")})
                except (MCPError, ValueError, InvalidOperation, KeyError):
                    continue
            choice = nearest_points(normalized)
            self.set_data(products=choice.products if choice else [], points=choice.points if choice else None,
                          target_points=1024, delta_points=choice.points-1024 if choice else None)
            lines = ([f"{p['name']} · SKU {p['sku']} · {p['points']} 积分 · 核销另付 {p['redeem_extra']}" for p in choice.products]
                     + [f"合计 {choice.points} 积分 · 差 {abs(choice.points-1024)} 积分"] if choice else
                     ["当前未得到可核对的积分兑换候选；不编造兑换方案。"])
            self.card("1024 积分挑战", lines + ["最多查询前 16 个列表商品的 SKU，组合最多 2 个。未验证最终兑换资格。",
                      "仅推荐，不自动兑换。DEBUG: 积分还没凑齐，先别提交事务。"])
        else:
            self.set_data(modes=["热量", "24", "102.4", "积分"])
            self.card("1024 目标模式", ["/1024 热量 · /1024 24 · /1024 102.4 · /1024 积分",
                      "金额均调用官方试算；不承诺恰好命中。"])

    def dispatch(self, line):
        line = line.strip()
        if not line:
            return
        args = shlex.split(line)
        command, rest = args[0], args[1:]
        if command == "/奶蛙":
            make_card = "--card" in rest
            rest = [arg for arg in rest if arg != "--card"]
            # Critical ordering: local animation before connect/search/quote.
            if self.json_output:
                pass  # Host mode must never send media, ANSI or prompts to stdout.
            elif "全身" in rest:
                full_path = ROOT / "assets" / "laugh-full.json"
                if not full_path.is_file():
                    full_path = ROOT / ".local" / "laugh-hq-full.json"
                laugh(frames_path=full_path)
            else:
                laugh()
            amount = None
            budget_args = " ".join(rest)
            if "预算" in budget_args:
                budget_text = budget_args.split("预算", 1)[1].strip()
                amount = amount_to_cents(budget_text)
            self.recommend(amount, mascot=True)
            if make_card:
                if not self.recommendations:
                    raise DataError("没有成功核价且符合条件的套餐，未导出日卡。")
                artifact = export_card(self.recommendations[0], self.service, self.card_dir)
                self.artifacts.append(artifact)
                self.emit("日卡已导出：" + artifact["path"])
            return
        if command in ("/help", "帮助"):
            self.set_data(commands=HELP)
            return self.card("命令提示", HELP)
        if command in ("/quit", "/exit"):
            self.abort()
            self.running = False
            return
        if command == "/abort":
            self.abort()
            return self.emit("已放弃待确认操作。")
        if command == "/confirm":
            if not self.pending or len(rest) != 1:
                raise SafetyError("没有待确认操作。")
            pending = self.pending
            if pending.tool == "create-order":
                current = self.service.checkout_args(pending.args.get("takeWayCode"))
                if current != pending.args:
                    self.abort()
                    raise SafetyError("门店或餐品已变化，请重新预览。")
            result = self.gateway.execute(pending, "确认 " + rest[0])
            self.pending = None
            self.set_data(operation=pending.tool, result=result.get("data", result))
            lines = [json.dumps(result.get("data", result), ensure_ascii=False)]
            order = result.get("data", result)
            if pending.tool == "create-order" and isinstance(order, dict) and order.get("orderId"):
                hint = {"app": "麦当劳 App", "entry": "我的订单",
                        "message": "可以在麦当劳 App「我的订单」查看；待支付订单可点进去完成支付。请使用同一会员账号。"}
                self.set_data(app_hint=hint, preference_recorded=False)
                lines.extend([hint["message"], "创建订单不等于已付款；支付后可再 /order 查单 订单ID 核实。"])
                try:
                    recorded = PreferenceMemory(ROOT).record_order(order["orderId"], self.items_data(self.service.quote.items))
                    self.set_data(preference_recorded=recorded)
                    if recorded:
                        lines.append("奶蛙记下了这次点餐选择；支付未核实，不会直接当成你最爱的口味。")
                except (OSError, DataError):
                    self.set_data(preference_warning="订单已返回，偏好未能保存；不要因此重新下单。")
                    lines.append("订单已返回，偏好未能保存；不要因此重新下单。")
            self.card("操作已返回 · 请核对实际结果", lines)
            return
        if command == "/coupons":
            return self.coupons_command(rest)
        if command == "/order":
            return self.order_command(rest)
        if command == "/budget":
            return self.recommend(amount_to_cents(rest[0]))
        if command == "/1024":
            return self.challenge(rest[0] if rest else "")
        if command == "/pick":
            index = int(rest[0])-1
            if not 0 <= index < len(self.recommendations):
                raise DataError("请从当前推荐方案选择。")
            self.abort()
            quote = self.service.choose_quote(self.recommendations[index])
            self.cart = copy.deepcopy(quote.items)
            return self.show_quote(quote, "已选方案 · 尚未下单")
        if command in ("/achievements", "/成就"):
            return self.show_achievements()
        if command in ("/偏好", "/preferences"):
            return self.preferences_command(rest)
        if command in ("/location", "/位置"):
            if not rest:
                location = load_location(ROOT)
                self.set_data(location={"city": location.city, "keyword": location.keyword,
                                        "source": location.source} if location else None)
                return self.card("附近位置", [f"{location.city}·{location.keyword}（{location.source}）"] if location else
                                 ["告诉我城市和附近地标，就能自动选最近营业门店。"])
            if len(rest) < 2:
                raise DataError("用法：/location 城市 附近地标")
            location = UserLocation(rest[0], " ".join(rest[1:]))
            save_location(ROOT, location)
            self.set_data(location={"city": location.city, "keyword": location.keyword, "source": location.source})
            self.abort()
            self.cart, self.stores, self.recommendations = [], [], []
            if self.service:
                self.service.store = None
                self.service.context = {"orderType":1, "beType":1}
                self.service.foods, self.service.details, self.service.coupons = [], {}, []
                self.service.invalidate_quote()
            return self.emit("位置已更新，下次点餐或推荐会自动选择最近营业门店。")
        if command == "/points":
            return self.points_command(rest)
        if command == "/status":
            return self.card("会员状态", self.status() or ["积分和可用券数量暂不可用。"])
        if command == "/events":
            result = self.connect().read("campaign-calendar")
            self.set_data(events=result)
            return self.card("活动日历", [json.dumps(result, ensure_ascii=False)])
        if command == "/tools":
            tools = self.connect().client.list_tools()
            self.set_data(tools=tools)
            return self.card("服务端工具清单", [t["name"] for t in tools]
                             + ["可用工具不代表 CLI 全部实现，参见 docs/tools.md。"])
        raise DataError("未知命令，输入 /help 查看。")

    def run_line(self, line):
        self.result_data, self.messages, self.artifacts = {}, [], []
        error = None
        try:
            self.dispatch(line)
        except (MCPError, ValueError, IndexError, KeyError, TypeError, OSError) as exc:
            message = str(exc) if isinstance(exc, (MCPError, DataError, LocationError)) else "参数格式或返回字段不符合要求，请查看 /help；缺失字段不猜测。"
            token = os.environ.get("MCD_TOKEN")
            if token:
                message = message.replace(token, "[已隐藏]")
            self.emit("提示：" + message)
            error = {"code": error_code(exc), "message": message}
        if self.json_output:
            data = copy.deepcopy(self.result_data)
            if self.service and self.service.store:
                data["store"] = copy.deepcopy(self.service.store)
                data["context"] = copy.deepcopy(self.service.context)
            print(dumps(envelope(line, data=data, messages=self.messages,
                                 artifacts=self.artifacts, pending=self.pending,
                                 error=error, running=self.running)), flush=True)
        return error is None


def main(argv=None):
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    argv = list(sys.argv[1:] if argv is None else argv)
    want_json = "--json" in argv

    class Parser(argparse.ArgumentParser):
        def error(self, message):
            if want_json:
                raise DataError(message)
            super().error(message)

        def print_help(self, file=None):
            if want_json:
                print(dumps(envelope("/help", data={"usage": self.format_help(), "commands": HELP})))
            else:
                super().print_help(file)

    parser = Parser(description="麦门 Code · 终端里的麦当劳点餐 Skill")
    parser.add_argument("--json", action="store_true", help="Agent JSON/JSONL 模式，stdout 仅输出结构化结果")
    parser.add_argument("--command", help="运行单条命令；写操作只能生成预览")
    parser.add_argument("command_text", nargs="?", help="单条命令，也可用 --command 指定")
    parser.add_argument("--commands-file", type=Path, help="逐行运行命令；仍要求确切的一次性确认码")
    parser.add_argument("--no-animation", action="store_true")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto", help="终端配色；默认自动识别")
    try:
        options = parser.parse_args(argv)
        if sum(value is not None for value in (options.command, options.command_text, options.commands_file)) > 1:
            parser.error("单条命令和命令文件不能同时指定。")
        options.command = options.command if options.command is not None else options.command_text
    except DataError as exc:
        print(dumps(envelope("", error={"code": "INVALID_ARGUMENTS", "message": str(exc)})))
        return 2
    if options.no_animation:
        os.environ["MCD_NO_ANIMATION"] = "1"
    if options.color != "auto":
        os.environ["MCD_COLOR"] = options.color
        if options.color == "always":
            os.environ.pop("NO_COLOR", None)
    initialize_terminal()
    app = App(json_output=options.json)
    if not options.json:
        print(banner())
    if options.command is not None:
        return 0 if app.run_line(options.command) else 1
    if options.commands_file:
        ok = True
        try:
            lines = options.commands_file.read_text(encoding="utf-8-sig").splitlines()
        except (OSError, UnicodeError):
            if options.json:
                print(dumps(envelope("", error={"code": "IO_ERROR", "message": "无法读取命令文件。"})))
            else:
                app.emit("无法读取命令文件。")
            return 1
        for line in lines:
            if line.strip() and not line.lstrip().startswith("#") and app.running:
                if not options.json:
                    app.emit("> " + line)
                ok = app.run_line(line) and ok
        return 0 if ok else 1
    if options.json:
        try:
            for line in sys.stdin:
                app.run_line(line.rstrip("\r\n"))
                if not app.running:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            app.abort()
        return 0
    try:
        values = app.status()
        if values:
            app.card("状态", values)
    except MCPError as exc:
        app.emit(str(exc))
    try:
        while app.running:
            line = input(theme_text("mcd > ", "prompt"))
            app.run_line(line)
    except (EOFError, KeyboardInterrupt):
        app.abort()
        app.emit("已退出。待确认操作未执行。")
    return 0
