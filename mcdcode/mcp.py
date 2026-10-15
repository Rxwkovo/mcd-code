"""Small, standard-library-only Streamable HTTP MCP client.

The token has one source: MCD_TOKEN in the process environment.  Exceptions
deliberately contain no server response bodies, headers, URLs or arguments.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

ENDPOINTS = ("https://mcp.mcd.cn", "https://mcp.mcd.cn/mcp-servers/mcd-mcp")
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
WRITE_TOOLS = frozenset({
    "auto-bind-coupons", "create-order", "cancel-order", "mall-create-order",
    "delivery-create-address", "party-order-create", "draw-lottery",
})
READ_TOOLS = frozenset({
    "now-time-info", "campaign-calendar", "available-coupons", "query-my-coupons",
    "query-store-coupons", "query-survey-coupon", "query-my-account",
    "query-nearby-stores", "delivery-query-stores", "query-meals",
    "query-meal-detail", "calculate-price", "list-nutrition-foods",
    "delivery-query-addresses", "query-order", "order-list",
    "mall-points-products", "mall-product-detail", "mall-order-list",
    "mall-order-detail", "query-party-city", "query-party-store",
    "query-party-store-date", "query-party-store-session", "query-lottery-info",
    "query-my-prizes", "query-meal-assistance", "query-promotions",
})


class MCPError(Exception):
    """A safe-to-display error, containing no remote response body."""


class AuthError(MCPError):
    pass


class ProtocolError(MCPError):
    pass


class TransportError(MCPError):
    """A transport failure. A write may already have reached the server."""


class _ReadTimeout(TransportError):
    """Only timeouts, not redirects or arbitrary transport failures, retry."""


class RateLimitError(MCPError):
    pass


class BusinessError(MCPError):
    def __init__(self, message: str, code: Any = None):
        super().__init__(message)
        value = str(code) if code is not None else ""
        self.code = value if re.fullmatch(r"[A-Za-z0-9_-]{1,40}", value) else None


class _HTTPStatus(MCPError):
    def __init__(self, status: int, retry_after: float = 0.0):
        self.status = status
        self.retry_after = retry_after
        super().__init__("MCP HTTP 请求未完成。")


def _canonical(arguments: dict[str, Any]) -> str:
    if not isinstance(arguments, dict):
        raise ValueError("工具参数必须是对象。")
    return json.dumps(arguments, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _origin(url: str) -> tuple[str, str | None, int | None]:
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme.lower(), parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if _origin(req.full_url) != _origin(newurl):
            raise TransportError("已拒绝跨域重定向，认证信息未发送至其他站点。")
        # No hidden POST repetition, even for same-origin redirects.
        if req.get_method() == "POST":
            raise TransportError("MCP 地址发生重定向，请检查官方服务地址。")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _json_text(text: str) -> Any:
    """Parse a whole JSON block, never the first brace inside prose/examples."""
    text = text.strip().lstrip("\ufeff")
    heading = re.search(r"(?m)^## Original Response[ \t]*\r?$", text)
    if heading:
        text = text[heading.end():].strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) < 3 or lines[0].strip().lower() not in {"```", "```json"} or lines[-1].strip() != "```":
            raise ValueError("Not a whole JSON fence")
        text = "\n".join(lines[1:-1])
    return json.loads(text)


def _check_business(data: dict[str, Any]) -> dict[str, Any]:
    code = data.get("code")
    if code in (401, 403, "401", "403"):
        raise AuthError("MCD_TOKEN 无效、过期或无权访问，请更新环境变量后重试。")
    if data.get("success") is False or data.get("status") in ("error", "failed"):
        raise BusinessError("麦当劳接口未完成请求，请检查输入和门店状态。", code)
    # Observed official envelopes have success, code, message and data.
    # Only apply the observed code convention to an identified envelope.
    if "code" in data and "data" in data and "message" in data and code not in (0, 200, "0", "200", "0000", "000000"):
        raise BusinessError("麦当劳接口返回业务错误，请检查输入或稍后重试。", code)
    return data


def unwrap_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return official tool payload, preferring structuredContent over text.

    Some tools use Markdown followed by an exact ``## Original Response``
    section. Plain explanatory prose is retained as text, never treated as
    invented fields. Explicit MCP/business failures raise sanitized errors.
    """
    if not isinstance(result, dict):
        raise ProtocolError("工具返回格式无法识别。")
    if result.get("isError"):
        raise BusinessError("工具执行失败，请检查输入、Token 和服务状态。")
    if "structuredContent" in result:
        data = result["structuredContent"]
        if isinstance(data, dict):
            return _check_business(data)
        return {"data": data}
    content = result.get("content")
    if content is None:
        return _check_business(result)
    if not isinstance(content, list):
        raise ProtocolError("工具内容格式无法识别。")
    texts = [block["text"] for block in content
             if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)]
    # The explicitly marked original response takes priority over examples.
    ordered = sorted(texts, key=lambda text: not bool(re.search(r"(?m)^## Original Response[ \t]*\r?$", text)))
    for text in ordered:
        try:
            data = _json_text(text)
        except (ValueError, TypeError):
            continue
        return _check_business(data) if isinstance(data, dict) else {"data": data}
    return {"text": "\n".join(texts)}


def _matching_result(messages: list[Any], request_id: int) -> dict[str, Any] | None:
    """Distinguish an unmatched event (None) from a valid empty result ({})."""
    for message in messages:
        if isinstance(message, dict) and type(message.get("id")) is int and message.get("id") == request_id:
            if message.get("jsonrpc") != "2.0":
                raise ProtocolError("MCP JSON-RPC 版本无法识别。")
            if "error" in message:
                raise ProtocolError("MCP 拒绝了请求，请检查工具参数和协议版本。")
            if "result" not in message or not isinstance(message["result"], dict):
                raise ProtocolError("MCP 响应缺少有效 result。")
            return message["result"]
    return None


def _event_result(chunks: list[str], request_id: int) -> dict[str, Any] | None:
    if not chunks:
        return None
    payload = "\n".join(chunks)
    if payload == "[DONE]":
        return None
    try:
        value = json.loads(payload)
    except ValueError:
        return None
    return _matching_result(value if isinstance(value, list) else [value], request_id)


def _decode_response(raw: bytes, request_id: int | None) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8-sig").strip()
    except UnicodeDecodeError:
        raise ProtocolError("MCP 响应不是有效的 UTF-8。") from None
    if not text:
        if request_id is None:
            return {}
        raise ProtocolError("MCP 返回空响应。")
    messages: list[Any] = []
    try:
        body = json.loads(text)
        messages.extend(body if isinstance(body, list) else [body])
    except ValueError:
        # SSE dispatches an event at each blank line. Multiple data fields are
        # joined with a newline as required by the event-stream format.
        chunks: list[str] = []
        for line in text.splitlines() + [""]:
            if not line:
                if chunks:
                    payload = "\n".join(chunks)
                    chunks = []
                    if payload == "[DONE]":
                        continue
                    try:
                        value = json.loads(payload)
                    except ValueError:
                        continue
                    messages.extend(value if isinstance(value, list) else [value])
            elif line.startswith("data:"):
                value = line[5:]
                chunks.append(value[1:] if value.startswith(" ") else value)
    if request_id is None:
        return {}
    result = _matching_result(messages, request_id)
    if result is not None:
        return result
    raise ProtocolError("MCP 响应缺少匹配的请求 ID。")


@dataclass
class _WritePermit:
    key: object
    tool: str
    arguments: str
    used: bool = False


class MCPClient:
    """Streamable HTTP client; public tool calls are read-only by default."""

    is_demo = False

    def __init__(self, *, timeout: float = 20.0, min_interval: float = 0.25,
                 max_read_retries: int = 2, opener=None,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep):
        token = os.environ.get("MCD_TOKEN", "").strip()
        if not token:
            raise AuthError("尚未设置 MCD_TOKEN；请在当前进程环境中配置后重试。")
        if any(char in token for char in "\r\n"):
            raise AuthError("MCD_TOKEN 格式无效，请重新设置环境变量。")
        self._token = token
        self.account_scope = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.endpoint = ENDPOINTS[0]
        self.timeout = max(0.1, float(timeout))
        self.min_interval = max(0.2, float(min_interval))
        self.max_read_retries = min(3, max(0, int(max_read_retries)))
        self._opener = opener or urllib.request.build_opener(_SafeRedirect())
        self._clock, self._sleep = clock, sleep
        self._last_request: float | None = None
        self._lock = threading.Lock()
        self._request_id = 0
        self._session_id: str | None = None
        self._protocol_version = "2025-03-26"
        self._initialized = False
        self._server_info: dict[str, Any] = {}
        self._permit_key = object()

    @classmethod
    def from_env(cls, **kwargs) -> "MCPClient":
        return cls(**kwargs)

    def _throttle(self):
        with self._lock:
            now = self._clock()
            if self._last_request is not None:
                delay = self.min_interval - (now - self._last_request)
                if delay > 0:
                    self._sleep(delay)
            self._last_request = self._clock()

    def _request_once(self, payload: dict[str, Any], request_id: int | None) -> dict[str, Any]:
        if self.endpoint not in ENDPOINTS:
            raise TransportError("已拒绝向非官方 MCP 地址发送认证请求。")
        self._throttle()
        headers = {"Authorization": "Bearer " + self._token,
                   "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        headers["MCP-Protocol-Version"] = self._protocol_version
        request = urllib.request.Request(self.endpoint,
            data=json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8"), headers=headers, method="POST")
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                status = getattr(response, "status", 200)
                if status >= 400:
                    raise _HTTPStatus(status)
                session = response.headers.get("Mcp-Session-Id")
                if session:
                    if "\r" in session or "\n" in session:
                        raise ProtocolError("MCP 会话标识无效。")
                    self._session_id = session
                # Notifications have no response ID to wait for. In particular,
                # an initialized notification may answer HTTP 202 with no body.
                if request_id is None:
                    return {}
                media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if media_type == "text/event-stream" and callable(getattr(response, "readline", None)):
                    return self._read_event_stream(response, request_id)
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ProtocolError("MCP 响应超过大小限制。")
                return _decode_response(body, request_id)
        except urllib.error.HTTPError as error:
            retry_after = 0.0
            try:
                retry_after = min(5.0, max(0.0, float(error.headers.get("Retry-After", "0"))))
            except (ValueError, TypeError, AttributeError):
                pass
            status = error.code
            error.close()
            raise _HTTPStatus(status, retry_after) from None
        except (TimeoutError, socket.timeout):
            raise _ReadTimeout("网络请求超时；写操作不会自动重试，请先核实结果。") from None
        except urllib.error.URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise _ReadTimeout("网络请求超时；写操作不会自动重试，请先核实结果。") from None
            raise TransportError("网络请求未完成，请检查连接；写操作不会自动重试。") from None
        except (ConnectionError, OSError):
            raise TransportError("网络请求未完成，请检查连接；写操作不会自动重试。") from None

    def _read_event_stream(self, response, request_id: int) -> dict[str, Any]:
        """Return the matching SSE result without waiting for connection EOF.

        urllib's socket timeout bounds each read. The deadline additionally
        prevents an endless stream of unrelated events/keepalives from extending
        the request indefinitely. All event bytes count towards the same cap.
        """
        total = 0
        chunks: list[str] = []
        first_line = True
        deadline = self._clock() + self.timeout
        while True:
            if self._clock() >= deadline:
                raise _ReadTimeout("MCP 事件流等待超时；写操作不会自动重试。")
            raw = response.readline(MAX_RESPONSE_BYTES - total + 1)
            total += len(raw)
            if total > MAX_RESPONSE_BYTES:
                raise ProtocolError("MCP 响应超过大小限制。")
            if self._clock() >= deadline:
                raise _ReadTimeout("MCP 事件流等待超时；写操作不会自动重试。")
            if not raw:
                result = _event_result(chunks, request_id)
                if result is not None:
                    return result
                raise ProtocolError("MCP 事件流结束，未收到匹配的请求 ID。")
            try:
                line = raw.decode("utf-8-sig" if first_line else "utf-8").rstrip("\r\n")
            except UnicodeDecodeError:
                raise ProtocolError("MCP 响应不是有效的 UTF-8。") from None
            first_line = False
            if not line:
                result = _event_result(chunks, request_id)
                chunks = []
                if result is not None:
                    return result
            elif line.startswith("data:"):
                value = line[5:]
                chunks.append(value[1:] if value.startswith(" ") else value)

    def _send(self, payload: dict[str, Any], request_id: int | None, *, retryable: bool) -> dict[str, Any]:
        attempts = 1 + (self.max_read_retries if retryable else 0)
        for attempt in range(attempts):
            try:
                return self._request_once(payload, request_id)
            except _HTTPStatus as error:
                if error.status in (401, 403):
                    raise AuthError("MCD_TOKEN 无效、过期或无权访问，请更新环境变量后重试。") from None
                if error.status in (404, 405):
                    raise
                if retryable and error.status in (429, 502, 503) and attempt + 1 < attempts:
                    self._sleep(max(error.retry_after, min(2.0, 0.5 * (2 ** attempt))))
                    continue
                if error.status == 429:
                    raise RateLimitError("请求过于频繁，请稍后重试；写操作不会自动重发。") from None
                raise TransportError("麦当劳 MCP 服务暂时不可用，请稍后重试。") from None
            except _ReadTimeout:
                if retryable and attempt + 1 < attempts:
                    self._sleep(min(2.0, 0.5 * (2 ** attempt)))
                    continue
                raise
        raise TransportError("MCP 请求未完成。")

    def _rpc(self, method: str, params: dict[str, Any], *, retryable: bool = False) -> dict[str, Any]:
        self._request_id += 1
        return self._send({"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params},
                          self._request_id, retryable=retryable)

    def initialize(self) -> dict[str, Any]:
        if self._initialized:
            return self._server_info
        params = {"protocolVersion": self._protocol_version, "capabilities": {},
                  "clientInfo": {"name": "mcd-code", "version": "0.1.0"}}
        for index, endpoint in enumerate(ENDPOINTS):
            self.endpoint = endpoint
            self._session_id = None
            try:
                result = self._rpc("initialize", params, retryable=True)
            except _HTTPStatus as error:
                if error.status in (404, 405) and index + 1 < len(ENDPOINTS):
                    continue
                raise TransportError("官方 MCP 地址暂不支持连接，请稍后重试。") from None
            version = result.get("protocolVersion")
            if not isinstance(version, str) or not version:
                raise ProtocolError("MCP 握手缺少协议版本。")
            self._protocol_version = version
            # The server may answer an initialized notification with HTTP 202
            # and no body. Notifications intentionally have no JSON-RPC id.
            self._send({"jsonrpc": "2.0", "method": "notifications/initialized"}, None, retryable=False)
            self._server_info, self._initialized = result, True
            return result
        raise TransportError("无法连接官方 MCP 地址。")

    def list_tools(self) -> list[dict[str, Any]]:
        self.initialize()
        tools: list[dict[str, Any]] = []
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(100):
            result = self._rpc("tools/list", {"cursor": cursor} if cursor else {}, retryable=True)
            batch = result.get("tools")
            if not isinstance(batch, list) or any(not isinstance(tool, dict) for tool in batch):
                raise ProtocolError("tools/list 未返回有效工具清单。")
            tools.extend(batch)
            cursor = result.get("nextCursor")
            if not cursor:
                return tools
            if not isinstance(cursor, str) or cursor in seen:
                raise ProtocolError("tools/list 分页游标无效。")
            seen.add(cursor)
        raise ProtocolError("工具清单分页超过安全限制。")

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.call_read(name, arguments)

    def call_read(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in READ_TOOLS:
            raise MCPError("此工具不在只读白名单；写操作必须经过预览与明确确认。")
        args = {} if arguments is None else json.loads(_canonical(arguments))
        self.initialize()
        try:
            result = self._rpc("tools/call", {"name": name, "arguments": args}, retryable=True)
        except _HTTPStatus:
            raise TransportError("MCP 工具地址不可用，请重新连接服务。") from None
        return unwrap_result(result)

    def _issue_write_permit(self, name: str, arguments: dict[str, Any]) -> _WritePermit:
        """Private capability entry point used only by ConfirmationGateway."""
        return _WritePermit(self._permit_key, name, _canonical(arguments))

    def execute_write(self, name: str, arguments: dict[str, Any], permit: _WritePermit) -> dict[str, Any]:
        canonical = _canonical(arguments)
        if (name not in WRITE_TOOLS or not isinstance(permit, _WritePermit)
                or permit.key is not self._permit_key or permit.tool != name
                or permit.arguments != canonical or permit.used):
            raise MCPError("写操作缺少有效的单次确认许可。")
        permit.used = True
        # Establishing a session is read-only. The actual tools/call below is
        # submitted exactly once, irrespective of HTTP/network failures.
        self.initialize()
        try:
            result = self._rpc("tools/call", {"name": name, "arguments": json.loads(canonical)}, retryable=False)
        except _HTTPStatus:
            raise TransportError("写操作结果待核实，请查询订单后再决定下一步。") from None
        return unwrap_result(result)
