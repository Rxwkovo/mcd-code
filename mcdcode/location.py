"""Use an explicitly supplied location to select the nearest open store.

The MCP search API accepts a city and a location keyword, not a device GPS
position. A saved location is only a user-supplied search anchor.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path


class LocationError(ValueError):
    """A location or a trustworthy nearest store could not be determined."""


@dataclass(frozen=True)
class UserLocation:
    city: str
    keyword: str
    source: str = "用户提供的位置"


def _validated_location(value: object) -> UserLocation | None:
    if not isinstance(value, dict):
        return None
    city, keyword = value.get("city"), value.get("keyword")
    source = value.get("source", "用户提供的位置")
    if not all(isinstance(part, str) and part.strip() for part in (city, keyword, source)):
        return None
    return UserLocation(city.strip(), keyword.strip(), source.strip())


def load_location(root: Path) -> UserLocation | None:
    """Read only our private user-provided location cache; never infer one."""
    try:
        value = json.loads((Path(root) / ".local" / "location.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return _validated_location(value)


def save_location(root: Path, location: UserLocation) -> Path:
    """Save the user's search anchor in the gitignored local cache."""
    checked = _validated_location({"city": location.city, "keyword": location.keyword,
                                   "source": location.source})
    if checked is None:
        raise LocationError("请提供城市和附近商圈、地标或门店名称。")
    path = Path(root) / ".local" / "location.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"city": checked.city, "keyword": checked.keyword,
                                "source": checked.source}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def nearest_store(stores: list[dict]) -> dict:
    """Select by the observed MCP ``distance`` field among confirmed open stores.

    Preserve the complete official record for subsequent service calls. An
    unknown distance or opening status cannot establish a nearest open store.
    """
    eligible = []
    for store in stores if isinstance(stores, list) else []:
        if not isinstance(store, dict) or store.get("businessStatus") is not True:
            continue
        distance = store.get("distance")
        if (isinstance(distance, bool) or not isinstance(distance, (int, float))
                or not math.isfinite(distance) or distance < 0 or not store.get("storeCode")):
            continue
        eligible.append(store)
    if not eligible:
        raise LocationError("没有可确认营业且带距离的门店，请换一个附近位置再试。")
    return min(eligible, key=lambda store: (store["distance"], str(store["storeCode"])))


def choose_nearest(service, location: UserLocation) -> dict:
    """Search for pickup stores once and choose the nearest valid open result."""
    checked = _validated_location({"city": location.city, "keyword": location.keyword,
                                   "source": location.source})
    if checked is None:
        raise LocationError("请先提供城市和所在位置。")
    store = nearest_store(service.search(checked.city, checked.keyword))
    service.choose_store(store, be_type=1)
    return store
