#!/usr/bin/env python3
"""Print the Skill's required opening banner without calling any MCP tools."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcdcode.ui import banner, initialize_terminal  # noqa: E402


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", help="已查到的真实积分；未知时不要传")
    parser.add_argument("--coupons", help="已查到的真实可用券数量；未知时不要传")
    args = parser.parse_args()
    initialize_terminal()
    print(banner(points=args.points, coupons=args.coupons))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
