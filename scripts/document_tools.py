#!/usr/bin/env python3
"""Document a saved tools/list response and optional private probe shapes.

This script makes no network requests.  Observation values are never emitted:
only schema-safe field names, their paths, and their JSON types are retained.
Private .local probe files must remain outside version control.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit


SCHEMA_ROW_LIMIT = 240
OBSERVATION_ROW_LIMIT = 240
MAX_DEPTH = 12
MAX_ARRAY_SAMPLES = 64
_TOON_HEADER = re.compile(r"^\s*\[\d+\]\{([^{}]+)\}:\s*$")
_FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def cell(value: object) -> str:
    text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.replace("|", "\\|").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def summary(text: object, limit: int = 600) -> str:
    compact = " ".join(str(text).split())
    if len(compact) > limit:
        compact = compact[:limit] + "…（完整说明见原始 Schema）"
    return cell(compact)


def schema_type(schema: object) -> str:
    if not isinstance(schema, dict):
        return "未声明"
    value = schema.get("type")
    if isinstance(value, list):
        return " / ".join(str(item) for item in value)
    if isinstance(value, str):
        return value
    if "$ref" in schema:
        return f"$ref {schema['$ref']}"
    for union in ("anyOf", "oneOf", "allOf"):
        if isinstance(schema.get(union), list):
            return " / ".join(dict.fromkeys(schema_type(item) for item in schema[union]))
    if "properties" in schema or "additionalProperties" in schema:
        return "object（隐式）"
    if "items" in schema:
        return "array（隐式）"
    return "未声明"


def schema_rows(schema: object) -> tuple[list[tuple[str, str, str, str]], bool]:
    """Walk properties, arrays, additionalProperties and union branches."""
    rows: list[tuple[str, str, str, str]] = []
    clipped = False

    def visit(node: object, path: str, required: str, depth: int) -> None:
        nonlocal clipped
        if not isinstance(node, dict):
            return
        if len(rows) >= SCHEMA_ROW_LIMIT or depth > MAX_DEPTH:
            clipped = True
            return
        description = node.get("description", "")
        if "enum" in node:
            # Enum values belong to the public schema, not to private probes.
            enum = json.dumps(node["enum"], ensure_ascii=False, separators=(",", ":"))
            description = f"{description}；枚举 {enum}".lstrip("；")
        rows.append((path, schema_type(node), required, str(description)))
        properties = node.get("properties", {})
        required_names = node.get("required", [])
        if isinstance(properties, dict):
            for name, child in properties.items():
                visit(child, f"{path}.{name}", "是" if name in required_names else "否", depth + 1)
        items = node.get("items")
        if isinstance(items, dict):
            visit(items, path + "[]", "—", depth + 1)
        elif isinstance(items, list):
            for index, child in enumerate(items):
                visit(child, f"{path}[{index}]", "—", depth + 1)
        if isinstance(node.get("additionalProperties"), dict):
            visit(node["additionalProperties"], path + ".{key}", "—", depth + 1)
        for union in ("oneOf", "anyOf", "allOf"):
            if isinstance(node.get(union), list):
                for index, child in enumerate(node[union]):
                    visit(child, f"{path}<{union}:{index + 1}>", "—", depth + 1)

    visit(schema, "$", "—", 0)
    return rows, clipped


def declared_names(tools: list[dict]) -> set[str]:
    names = {"success", "datetime", "content", "text", "type", "structuredContent", "isError", "result"}

    def visit(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                names.update(str(key) for key in properties)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    for tool in tools:
        visit(tool.get("outputSchema", {}))
    return names


def json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "未知"


def observed_rows(value: object, allowed_names: set[str]) -> tuple[list[tuple[str, str]], bool, bool]:
    """Extract structure without retaining or formatting any response value.

    Unrecognized mapping keys become {key}, because dynamic keys can themselves
    contain account identifiers.  Large arrays are sampled only for shape.
    """
    observed: dict[str, set[str]] = {}
    clipped = False
    toon = False

    def add(path: str, kind: str) -> None:
        nonlocal clipped
        if path not in observed and len(observed) >= OBSERVATION_ROW_LIMIT:
            clipped = True
            return
        observed.setdefault(path, set()).add(kind)

    def visit(node: object, path: str, depth: int) -> None:
        nonlocal clipped, toon
        if depth > MAX_DEPTH:
            clipped = True
            return
        add(path, json_type(node))
        if isinstance(node, dict):
            for key, child in node.items():
                field = str(key) if key in allowed_names else "{key}"
                visit(child, f"{path}.{field}", depth + 1)
        elif isinstance(node, list):
            if len(node) > MAX_ARRAY_SAMPLES:
                clipped = True
            for child in node[:MAX_ARRAY_SAMPLES]:
                visit(child, path + "[]", depth + 1)
        elif isinstance(node, str):
            # A TOON header declares column *names*.  Data rows are deliberately
            # never parsed, copied, displayed, or used as examples in this file.
            first_line = node.split("\n", 1)[0].rstrip("\r")
            match = _TOON_HEADER.fullmatch(first_line)
            if match:
                toon = True
                try:
                    headers = next(csv.reader([match.group(1)]))
                except (csv.Error, StopIteration):
                    return
                for header in headers:
                    name = header.strip()
                    field = name if _FIELD_NAME.fullmatch(name) else "{column}"
                    add(f"{path}~toon[].{field}", "CSV text（不是 JSON 字段）")

    visit(value, "$", 0)
    return [(path, " / ".join(sorted(types))) for path, types in observed.items()], clipped, toon


def read_observations(directory: Path | None, tools: list[dict]) -> dict[str, dict]:
    if directory is None or not directory.is_dir():
        return {}
    allowed = declared_names(tools)
    output = {}
    for tool in tools:
        path = directory / f"probe-{tool['name']}.json"
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            output[tool["name"]] = {"unreadable": True}
            continue
        rows, clipped, toon = observed_rows(payload, allowed)
        success = isinstance(payload, dict) and payload.get("success") is True
        output[tool["name"]] = {"rows": rows, "clipped": clipped, "toon": toon, "success": success}
    return output


def schema_table(schema: object) -> list[str]:
    rows, clipped = schema_rows(schema)
    if not rows:
        return ["服务端未声明该 Schema；不能推断字段。", ""]
    lines = ["| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |", "|---|---|---|---|"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    lines.append("")
    if clipped:
        lines.extend([f"字段展示达到 {SCHEMA_ROW_LIMIT} 行或 {MAX_DEPTH} 层上限；所有字段仍可在原始 Schema 中查看。", ""])
    return lines


def public_endpoint(value: object) -> str:
    parts = urlsplit(str(value))
    # Never retain a URL credential, query string or fragment from capture metadata.
    host = parts.hostname or ""
    if parts.port:
        host += f":{parts.port}"
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


def generate(capture: dict, observations: dict[str, dict], schema_link: str) -> str:
    tools = capture.get("tools")
    if not isinstance(tools, list):
        raise ValueError("工具捕获文件须包含 tools 数组。")
    tools = sorted(tools, key=lambda tool: tool["name"])
    observed_count = sum(not entry.get("unreadable") for entry in observations.values())
    server = capture.get("server") or {}
    lines = [
        "# MCP 真实工具目录", "",
        f"- tools/list 捕获时间：`{cell(capture.get('capturedAt', '未记录'))}`。",
        f"- 实际连接端点：`{cell(public_endpoint(capture.get('endpoint', '')))}`。",
        f"- 服务端：`{cell(server.get('name', '未记录'))}`，版本 `{cell(server.get('version', '未记录'))}`。",
        f"- 实际返回 **{len(tools)} 个工具**；本文件读取到 **{observed_count} 个工具的本地响应结构**。",
        f"- 完整工具描述、输入及输出 Schema：[原始 tools/list 捕获]({schema_link})。",
        "",
        "本文件的工具列表表示服务器可用能力，不表示 CLI 已实现或已真实执行每个工具。实际命令接入情况见 [MCP_INTEGRATION.md](../MCP_INTEGRATION.md)。",
        "",
        "**证据区分：**输入及输出声明表来自 tools/list 的 Schema；“实际观察字段”只来自另行保存的本地探测响应。声明字段不等于调用成功，未探测工具不冒充已验证。观察仅记录路径与类型，不包含 Token、用户标识值、地址、手机号、订单、支付链接或响应示例值。",
        "",
        "**结构展示限制：**单个 Schema 最多展示 240 行、12 层，完整字段以原始捕获为准；响应观察每个数组最多抽样 64 个元素、共 240 条字段路径。空数组或 null 只能证明此次响应形态；未出现的字段不能推定不存在。动态映射键及未知字段名统一写成 `{key}`，避免把标识值误写为字段名。",
        "",
        "## 与旧资料的差异", "",
        "- 活动门店日期、场次的真实名称为 `query-party-store-date`、`query-party-store-session`，使用实际清单名称。",
        "- 当前清单还包含 `query-meal-assistance`、`query-promotions`、`query-survey-coupon`；不根据旧文章推断工具是否存在。",
        "- 响应中实际观察到 `success`、`datetime` 等封装字段；部分工具的 outputSchema 未完整声明这些公共封装字段。",
        "- `list-nutrition-foods` 的 `data` 声明为 string，实测也是字符串，内部采用 `[n]{字段名,...}:` 加 CSV 行的 TOON 形式。不能直接当作 JSON 餐品数组。热量等字段缺失或无法精确对应餐品规格时显示“未知”。",
        "- 工具的描述文字可能列出业务必需条件，而 inputSchema.required 较少；执行时必须同时遵守业务条件，不能只看 required 表。",
        "",
        "## 实际工具名", "",
    ]
    lines.extend(f"{index}. [`{tool['name']}`](#{tool['name']})" for index, tool in enumerate(tools, 1))
    lines.append("")
    for tool in tools:
        name = tool["name"]
        lines.extend([f"## {name}", "", summary(tool.get("description", "服务端未提供描述。")), "", "### 输入：Schema 声明", ""])
        lines.extend(schema_table(tool.get("inputSchema")))
        lines.extend(["### 返回：Schema 声明", ""])
        lines.extend(schema_table(tool.get("outputSchema")))
        lines.extend(["### 实际观察字段", ""])
        observation = observations.get(name)
        if not observation:
            lines.extend(["未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。", ""])
        elif observation.get("unreadable"):
            lines.extend(["存在本地探测文件，但未能读取其 JSON 结构；不作已验证结论。", ""])
        else:
            status = "已观察到成功响应的字段结构" if observation["success"] else "已观察到响应字段结构，但该结构本身不能证明业务成功"
            lines.extend([status + "；未复制任何响应值。", "", "| 字段路径 | 实测类型 |", "|---|---|"])
            lines.extend(f"| {cell(path)} | {cell(kind)} |" for path, kind in observation["rows"])
            lines.append("")
            if observation["toon"]:
                lines.extend(["`~toon[]` 是字符串内容中的列名，CSV 单元格在传输中为文本；这不表示服务端返回了嵌套 JSON 数组。文档仅保存列名，不保存原始数据行。", ""])
            if observation["clipped"]:
                lines.extend(["本次结构观察触及抽样或层级上限，展示不保证穷尽每个响应元素。", ""])
    lines.extend([
        "## 更新本文件", "",
        "从项目根目录运行（只读已有捕获和本地探测文件；不连接网络）：", "",
        "```sh", "python scripts/document_tools.py --schemas docs/tool-schemas.json --output docs/tools.md --observations .local", "```", "",
        "不传 `--observations` 时只生成 Schema 声明，不读取本地私有探测。请勿提交 `.local` 文件夹。", "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schemas", type=Path, default=Path("docs/tool-schemas.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/tools.md"))
    parser.add_argument("--observations", type=Path, default=None)
    args = parser.parse_args()
    try:
        capture = json.loads(args.schemas.read_text(encoding="utf-8-sig"))
        tools = capture.get("tools")
        if not isinstance(tools, list):
            raise ValueError("工具捕获文件须包含 tools 数组。")
        observations = read_observations(args.observations, tools)
        # A relative link makes the public capture usable after GitHub publication.
        import os
        schema_link = Path(os.path.relpath(args.schemas.resolve(), args.output.parent.resolve())).as_posix()
        document = generate(capture, observations, schema_link)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError, KeyError):
        parser.exit(1, "无法生成工具文档：请检查捕获文件格式及文件读写权限。\n")
    print(f"Documented {len(tools)} tools; observations for {len(observations)} tools.")


if __name__ == "__main__":
    main()
