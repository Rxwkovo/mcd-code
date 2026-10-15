#!/usr/bin/env python3
"""Opt-in, read-only integration check. Credentials only come from MCD_TOKEN."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mcdcode.mcp import MCPClient, MCPError
from mcdcode.service import OrderingService


def shape(value, depth=0):
    if depth > 8:
        return type(value).__name__
    if isinstance(value, dict):
        # Arbitrary menu codes are keys; do not publish account identifiers.
        return {str(k): shape(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [shape(value[0], depth + 1)] if value else []
    return type(value).__name__


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", required=True)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--private-snapshots", action="store_true")
    args = parser.parse_args()
    client = MCPClient.from_env()
    client.initialize()
    tools = client.list_tools()  # Always discover before first business call.
    service = OrderingService(client)
    report = {"checkedAt": datetime.now(timezone(timedelta(hours=8))).isoformat(),
              "endpoint": client.endpoint, "toolCount": len(tools), "writesExecuted": 0,
              "storeCode": args.store, "checks": {}}
    private = ROOT / ".local"
    private.mkdir(exist_ok=True)

    def probe(name, arguments=None):
        result = client.call_read(name, arguments or {})
        report["checks"][name] = {"status": "passed", "shape": shape(result)}
        if args.private_snapshots:
            (private / f"probe-{name}.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PASS {name}", flush=True)
        return result.get("data")

    for tool in ("now-time-info", "campaign-calendar", "query-my-account", "available-coupons", "query-my-coupons"):
        try:
            probe(tool)
        except MCPError as exc:
            report["checks"][tool] = {"status": "failed", "errorType": type(exc).__name__}
            print(f"FAIL {tool}: {type(exc).__name__}", flush=True)
    stores = probe("query-nearby-stores", {"city": args.city, "keyword": args.keyword, "searchType": 2, "beType": 1})
    store = next((s for s in stores if str(s.get("storeCode")) == args.store), None)
    if not store:
        raise ValueError("Requested store not returned by search; no replacement selected.")
    service.choose_store(store)
    menu = probe("query-meals", service.context)
    from mcdcode.service import parse_menu
    service.foods = parse_menu(menu)
    coupons = probe("query-store-coupons", service.context)
    service.coupons = coupons if isinstance(coupons, list) else []
    nutrition = probe("list-nutrition-foods")
    from mcdcode.service import parse_nutrition
    service.nutrition = parse_nutrition(nutrition)
    public_sample = []
    for food in service.foods[:3]:
        detail = probe("query-meal-detail", {**service.context, "code": food.code})
        service.details[food.code] = detail
        try:
            quote = service.calculate([{"productCode": food.code, "quantity": 1}])
            report["checks"]["calculate-price"] = {"status": "passed", "shape": shape({"data": quote.raw})}
            if args.private_snapshots:
                (private / "probe-calculate-price.json").write_text(
                    json.dumps({"data": quote.raw}, ensure_ascii=False, indent=2), encoding="utf-8")
            public_sample.append({"name": food.name, "cents": quote.cents})
        except (MCPError, ValueError) as exc:
            print(f"SKIP price: {type(exc).__name__}", flush=True)
    products = probe("mall-points-products", {"catRuleIds": "1>4"})
    for product in products[:8]:
        if product.get("downTime", "9999") < service.local_date():
            continue
        try:
            probe("mall-product-detail", {"spuId": product["spuId"]})
            break
        except MCPError as exc:
            report["checks"]["mall-product-detail"] = {"status": "failed", "errorType": type(exc).__name__}
    else:
        report["checks"].setdefault("mall-product-detail", {"status": "unverified", "reason": "No usable product detail in bounded list"})
    print(json.dumps({"storeName": store["storeName"], "menuCount": len(service.foods),
                      "nutritionNameCount": len(service.nutrition), "priceSamples": public_sample}, ensure_ascii=False), flush=True)
    # Shapes only, never values of profile, coupons, addresses, or order data.
    (ROOT / "docs" / "live-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
