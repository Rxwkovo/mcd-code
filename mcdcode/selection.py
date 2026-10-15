"""Bounded recommendation searches, with no local pricing or coupon rules.

Prices must be supplied as official ``calculate-price`` quotes.  Nutrition and
points must be explicitly present in normalized live data; missing values
are never inferred from a product name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
from itertools import combinations
import re
from typing import Callable, TypeVar


MAX_BASKET_LIMIT = 64
MAX_MENU_POOL = 32
MAX_CALORIE_FOODS = 48
MAX_CALORIE_ITEMS = 3
MAX_POINTS_PRODUCTS = 48
MAX_POINTS_ITEMS = 2


@dataclass
class Food:
    code: str
    name: str
    category: str = ""
    kcal: int | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class Candidate:
    items: list[dict]
    label: str
    score: int = 0


@dataclass
class Quote:
    items: list[dict]
    cents: int
    raw: dict = field(default_factory=dict)
    score: int = 0


@dataclass
class PointsChoice:
    products: list[dict]
    points: int


T = TypeVar("T")


def closest(
    values: list[T], target: int, value_fn: Callable[[T], int] = lambda value: value
) -> T | None:
    """Return the nearest observed value; a tie favours the lower value.

    Equal values preserve input order.  This only searches the supplied list.
    """
    if not values:
        return None
    return min(values, key=lambda value: (abs(value_fn(value) - target), value_fn(value)))


def amount_to_cents(amount: str) -> int:
    """Parse a positive decimal yuan amount, at most 10,000 yuan.

    Accept one or two decimal digits and surrounding whitespace.  Reject
    exponents, signs, currency marks, non-ASCII digits, and fractional cents.
    """
    if not isinstance(amount, str):
        raise ValueError("金额请输入十进制数字，例如 24.00。")
    text = amount.strip()
    if re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", text) is None:
        raise ValueError("金额最多保留两位小数，例如 24.00。")
    # Check length before Decimal construction so untrusted CLI input is bounded.
    normalized = text.lstrip("0") or "0"
    if len(normalized.split(".")[0]) > 5:
        raise ValueError("金额须大于 0，且不超过 10000.00 元。")
    cents = int(Decimal(text) * 100)
    if cents <= 0 or cents > 1_000_000:
        raise ValueError("金额须大于 0，且不超过 10000.00 元。")
    return cents


_FAVOURITE_WORDS = (
    "冰淇淋", "冰激凌", "麦旋风", "奶昔", "甜筒", "新地", "圣代",
    "派", "麦乐鸡", "鸡块", "牛奶", "奶茶", "奶味", "奶香",
    "ice cream", "icecream", "mcflurry", "milkshake", "sundae", "pie", "nugget",
)
_DRINK_WORDS = (
    "饮料", "饮品", "可乐", "雪碧", "芬达", "咖啡", "拿铁", "美式",
    "茶", "牛奶", "奶昔", "果汁", "豆浆", "纯净水", "矿泉水",
    "drink", "beverage", "cola", "sprite", "fanta", "coffee", "latte",
    "milk", "juice", "tea", "water", "shake",
)
_DESSERT_DRINK_EXCEPTIONS = (
    "奶昔", "麦旋风", "冰淇淋", "冰激凌", "甜筒", "新地", "圣代",
    "milkshake", "milk shake", "mcflurry", "ice cream", "icecream", "sundae",
)


def _food_text(food: Food) -> str:
    # Category can be absent or unusable; names remain a documented fallback.
    return f"{food.category or ''} {food.name}".casefold()


def is_mascot_favourite(food: Food) -> bool:
    """Name/category keyword preference only; this is not nutrition inference."""
    return any(word in _food_text(food) for word in _FAVOURITE_WORDS)


def is_drink(food: Food) -> bool:
    return any(word in _food_text(food) for word in _DRINK_WORDS)


def is_mascot_main(food: Food) -> bool:
    """Prefer a dessert/snack main over a pair made entirely of beverages.

    Milkshakes and ice creams remain valid dessert mains even if the menu
    groups them under drinks.  Plain milk is a fallback only when no preferred
    dessert/snack can be found.
    """
    text = _food_text(food)
    return is_mascot_favourite(food) and (
        not is_drink(food) or any(word in text for word in _DESSERT_DRINK_EXCEPTIONS)
    )


def _interleave(groups: list[list[Food]]) -> list[Food]:
    """Preserve seeded order inside groups while showing different families."""
    result = []
    for offset in range(max((len(group) for group in groups), default=0)):
        result.extend(group[offset] for group in groups if offset < len(group))
    return result


def _diverse_mains(foods: list[Food]) -> list[Food]:
    families = (
        ("圆筒", "甜筒", "冰淇淋", "冰激凌", "新地", "圣代", "ice cream", "icecream", "sundae"),
        ("派", "pie"), ("麦乐鸡", "鸡块", "nugget"),
        ("麦旋风", "mcflurry"), ("奶昔", "milkshake", "milk shake"),
    )
    groups: list[list[Food]] = [[] for _ in range(len(families) + 1)]
    family_order: list[int] = []
    for food in foods:
        text = _food_text(food)
        family = next((index for index, words in enumerate(families) if any(word in text for word in words)), len(families))
        if not groups[family]:
            family_order.append(family)
        groups[family].append(food)
    # The incoming order has already been seeded.  Preserve its family order
    # so daily randomness still affects the first recommended main, while the
    # first cycle contains one representative from each available family.
    return _interleave([groups[family] for family in family_order])


def _diverse_drinks(foods: list[Food]) -> list[Food]:
    families = (
        ("牛奶", "纯奶"), ("可乐", "雪碧", "芬达", "cola", "sprite", "fanta"),
        ("茶", "tea"), ("咖啡", "拿铁", "coffee", "latte"),
        ("纯净水", "矿泉水", "water"), ("果汁", "juice"),
    )
    groups: list[list[Food]] = [[] for _ in range(len(families) + 1)]
    for food in foods:
        text = _food_text(food)
        family = next((index for index, words in enumerate(families) if any(word in text for word in words)), len(families))
        groups[family].append(food)
    return _interleave(groups)


def _ordered_foods(foods: list[Food], seed: str | None = None) -> list[Food]:
    ordered = sorted(
        (food for food in foods if isinstance(food.code, str) and food.code),
        key=lambda food: (food.code, food.name, food.category or ""),
    )
    unique: dict[str, Food] = {}
    for food in ordered:
        unique.setdefault(food.code, food)
    ordered = list(unique.values())
    if seed is not None:
        ordered.sort(
            key=lambda food: (
                sha256(f"{seed}\0{food.code}\0{food.name}".encode("utf-8")).digest(),
                food.code,
            )
        )
    return ordered


def _candidate(foods: list[Food], score: int) -> Candidate:
    return Candidate(
        items=[{"productCode": food.code, "quantity": 1} for food in foods],
        label=" + ".join(food.name for food in foods),
        score=score,
    )


def candidate_baskets(
    foods: list[Food], limit: int = 16, seed: str | None = None, mascot: bool = False
) -> list[Candidate]:
    """Build bounded baskets to be quoted by the official pricing tool.

    Singles are deliberately retained for tight budgets: the default eight
    single-item slots include up to five mains and three drinks.  Mascot mains
    are diversified across ice cream, pie, nuggets, flurry and shake families;
    this is a name preference, never an assumption about their price.  Mascot
    favourites paired with a drink have the highest score. No item price, discount rule,
    availability, or budget fit is inferred here.  Each basket has at most two
    different products, quantity one each.  Search is capped at 64 baskets,
    using at most 32 menu products plus up to 32 favourites and 32 drinks.

    A seed such as ``2026-10-15`` gives stable results for the same menu and
    parameters, independent of incoming menu order and process hash seed.
    """
    limit = min(max(0, limit), MAX_BASKET_LIMIT)
    if not limit:
        return []
    ordered = _ordered_foods(foods, seed)
    if not ordered:
        return []

    favourites = [food for food in ordered if is_mascot_favourite(food)]
    mains = [food for food in favourites if is_mascot_main(food)]
    # Sweet/milky beverages can be a fallback, but must not displace an
    # available ice cream, pie or nuggets as the main part of the mascot meal.
    if mascot and mains:
        favourites = _diverse_mains(mains)
    drinks = _diverse_drinks([food for food in ordered if is_drink(food)])
    if mascot and favourites:
        favourite_codes = {food.code for food in favourites}
        main_pool = favourites + [food for food in ordered if food.code not in favourite_codes and not is_drink(food)]
    else:
        main_pool = [food for food in ordered if not is_drink(food) or is_mascot_main(food)]
    main_pool = main_pool[:MAX_MENU_POOL]
    main_codes = {food.code for food in main_pool}
    single_drinks = [food for food in drinks if food.code not in main_codes][:MAX_MENU_POOL]
    # Reserve observable drink singles for later budget searches.  Putting
    # several main families first also prevents one large family monopolising
    # the bounded recommendation pool.
    early_singles = _interleave([main_pool[:5], single_drinks[:3]])
    early_codes = {food.code for food in early_singles}
    single_pool = (early_singles + [food for food in main_pool + single_drinks if food.code not in early_codes])[:MAX_MENU_POOL]

    pairs: list[Candidate] = []
    seen: set[tuple[str, ...]] = set()

    def add_pair(first: Food, second: Food, score: int) -> None:
        if first.code == second.code:
            return
        key = tuple(sorted((first.code, second.code)))
        if key not in seen:
            seen.add(key)
            pairs.append(_candidate([first, second], score))

    if mascot:
        # Explore different main foods before cycling through another drink.
        for drink in drinks[:MAX_MENU_POOL]:
            for favourite in favourites[:MAX_MENU_POOL]:
                add_pair(favourite, drink, 100)
        for first, second in combinations(favourites[:MAX_MENU_POOL], 2):
            add_pair(first, second, 80)
    # Preserve useful multi-item options even when no mascot keyword matches.
    for first, second in combinations(single_pool, 2):
        add_pair(first, second, 20)

    singles = [
        _candidate([food], 60 if mascot and is_mascot_favourite(food) else 10)
        for food in single_pool
    ]
    if limit == 1:
        return pairs[:1] or singles[:1]
    single_count = min(len(singles), max(1, limit // 2))
    pair_count = min(len(pairs), limit - single_count)
    # Use spare slots for singles if the menu cannot form enough unique pairs.
    single_count = min(len(singles), limit - pair_count)
    return pairs[:pair_count] + singles[:single_count]


def _valid_quote(quote: Quote) -> bool:
    return isinstance(quote.cents, int) and not isinstance(quote.cents, bool) and quote.cents >= 0


def best_under_budget(quotes: list[Quote], budget: int) -> list[Quote]:
    """Rank observed quotes within budget; equal preference stays input-stable."""
    valid = [quote for quote in quotes if _valid_quote(quote) and quote.cents <= budget]
    return sorted(valid, key=lambda quote: -quote.score)


def nearest_quote(quotes: list[Quote], target: int) -> Quote | None:
    return closest([quote for quote in quotes if _valid_quote(quote)], target, lambda quote: quote.cents)


def calorie_candidates(
    foods: list[Food], target: int = 1024, limit: int = 3
) -> list[tuple[list[Food], int]]:
    """Nearest known calorie totals within a finite, explicitly bounded search.

    Evaluate one to three distinct products from the first 48 known-nutrition
    products in code/name order.  At most 18,472 baskets are evaluated.  Missing
    calories are excluded, zero calories remain valid, and ties favour a lower
    total then fewer products.  The returned total does not cover menu extras
    or a changed portion unless the upstream nutrition mapping covers them.
    """
    if limit <= 0:
        return []
    known = [
        food for food in _ordered_foods(foods)
        if isinstance(food.kcal, int) and not isinstance(food.kcal, bool) and food.kcal >= 0
    ][:MAX_CALORIE_FOODS]
    choices: list[tuple[list[Food], int]] = []
    for count in range(1, min(MAX_CALORIE_ITEMS, len(known)) + 1):
        for group in combinations(known, count):
            total = sum(food.kcal for food in group)
            choices.append((list(group), total))
    choices.sort(key=lambda choice: (
        abs(choice[1] - target), choice[1], len(choice[0]), tuple(food.code for food in choice[0])
    ))
    return choices[:limit]


def nearest_points(products: list[dict], target: int = 1024) -> PointsChoice | None:
    """Nearest single/pair of explicit points-only, normalized product SKUs.

    Upstream adapters must provide ``points`` and ``cash_cents`` as integers.
    A missing cash amount is unknown, not zero.  Only cash_cents == 0 is
    eligible.  The original product dictionaries (including SKU metadata) are
    preserved.  Search uses at most 48 distinct normalized code/SKU products
    and evaluates at most 1,176 single/pair choices.  This never redeems them.
    """
    eligible = []
    seen: set[tuple[str, str]] = set()
    for product in sorted(products, key=lambda item: (str(item.get("code", "")), str(item.get("sku", "")))):
        points, cash = product.get("points"), product.get("cash_cents")
        if not isinstance(points, int) or isinstance(points, bool) or points <= 0:
            continue
        if not isinstance(cash, int) or isinstance(cash, bool) or cash != 0:
            continue
        code = product.get("code")
        if not isinstance(code, str) or not code:
            continue
        key = (code, str(product.get("sku", "")))
        if key in seen:
            continue
        seen.add(key)
        eligible.append(product)
    eligible = eligible[:MAX_POINTS_PRODUCTS]
    choices = [PointsChoice([product], product["points"]) for product in eligible]
    choices.extend(
        PointsChoice(list(group), sum(product["points"] for product in group))
        for group in combinations(eligible, MAX_POINTS_ITEMS)
    )
    return closest(choices, target, lambda choice: choice.points)
