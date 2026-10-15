"""Explicit-confirmation gate and conservative local duplicate protection.

Only a hash, status and timestamps reach SQLite. Orders, addresses, tokens,
summaries and tool arguments are never stored in the operation journal.
"""
from __future__ import annotations

import copy
import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .mcp import MCPError, WRITE_TOOLS, _canonical


class SafetyError(MCPError):
    pass


@dataclass(frozen=True)
class Pending:
    id: str
    code: str
    tool: str
    args: dict[str, Any]
    summary: str
    fingerprint: str
    expires_at: float

    @property
    def confirmation(self) -> str:
        return "确认 " + self.code


@dataclass(frozen=True)
class _Snapshot:
    code: str
    tool: str
    arguments: str
    summary: str
    fingerprint: str
    expires_at: float


class ConfirmationGateway:
    """Preview -> exact confirmation -> one attempted execution.

    The in-memory preview is bound to this gateway. The persistent hash is
    bound to the environment-token scope and exact tool arguments. Identical
    operations remain blocked after success or an uncertain result, including
    after process restarts. This is local duplicate protection, not a claim of
    server-side idempotency.
    """

    def __init__(self, client, state_dir: str | Path | None = None, *,
                 ttl: float = 300.0, clock: Callable[[], float] = time.time):
        self.client = client
        self._clock = clock
        self.ttl = min(300.0, max(1.0, float(ttl)))
        self._pending: dict[str, _Snapshot] = {}
        scope = getattr(client, "account_scope", None)
        if not isinstance(scope, str) or not scope:
            raise SafetyError("客户端缺少身份范围，不能启用真实写操作。")
        self._scope = scope
        self.state_dir = Path(state_dir) if state_dir is not None else Path.home() / ".mcd-code"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.state_dir / "operations.sqlite3"
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS operations (fingerprint TEXT PRIMARY KEY, status TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL)")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            with db:
                yield db
        finally:
            # sqlite3.Connection.__exit__ commits/rolls back but does not
            # close its Windows file handle.
            db.close()

    def preview(self, tool: str, args: dict[str, Any], summary: str) -> Pending:
        if tool not in WRITE_TOOLS:
            raise SafetyError("该操作不在已审核的写操作白名单。")
        if not isinstance(summary, str) or not summary.strip():
            raise SafetyError("执行前必须展示具体操作预览。")
        canonical = _canonical(args)
        fingerprint = hashlib.sha256((self._scope + "\0" + tool + "\0" + canonical).encode("utf-8")).hexdigest()
        operation_id = secrets.token_hex(16)
        code = secrets.token_hex(3).upper()
        expires = self._clock() + self.ttl
        snapshot = _Snapshot(code, tool, canonical, summary, fingerprint, expires)
        self._pending[operation_id] = snapshot
        return Pending(operation_id, code, tool, json.loads(canonical), summary, fingerprint, expires)

    def cancel(self, pending: Pending) -> None:
        self._pending.pop(pending.id, None)

    def _reserve(self, fingerprint: str) -> None:
        now = self._clock()
        try:
            with self._connect() as db:
                db.execute("INSERT INTO operations VALUES (?, ?, ?, ?)", (fingerprint, "inflight", now, now))
        except sqlite3.IntegrityError:
            raise SafetyError("相同操作已有执行记录，已阻止重复提交；请先查询实际结果。") from None
        except sqlite3.Error:
            raise SafetyError("无法写入防重复记录，本次操作未执行。") from None

    def _mark(self, fingerprint: str, status: str) -> None:
        with self._connect() as db:
            db.execute("UPDATE operations SET status = ?, updated_at = ? WHERE fingerprint = ?", (status, self._clock(), fingerprint))

    def execute(self, pending: Pending, confirmation: str) -> dict[str, Any]:
        if not isinstance(pending, Pending):
            raise SafetyError("操作预览无效，请重新预览。")
        snapshot = self._pending.get(pending.id)
        if snapshot is None:
            raise SafetyError("该确认已使用或不属于本次会话，请重新预览。")
        try:
            same_arguments = _canonical(pending.args) == snapshot.arguments
        except (TypeError, ValueError):
            same_arguments = False
        if (not same_arguments or pending.code != snapshot.code or pending.tool != snapshot.tool
                or pending.summary != snapshot.summary or pending.fingerprint != snapshot.fingerprint
                or pending.expires_at != snapshot.expires_at):
            self._pending.pop(pending.id, None)
            raise SafetyError("操作参数发生变化，原确认已失效，请重新预览。")
        if self._clock() >= snapshot.expires_at:
            self._pending.pop(pending.id, None)
            raise SafetyError("操作预览已过期，请重新查看金额和内容后确认。")
        if confirmation != "确认 " + snapshot.code:
            raise SafetyError("未收到与本次预览匹配的明确确认，本次操作未执行。")
        # Reserve before minting a capability or contacting the remote server.
        self._reserve(snapshot.fingerprint)
        self._pending.pop(pending.id, None)
        args = json.loads(snapshot.arguments)
        try:
            permit = self.client._issue_write_permit(snapshot.tool, args)
            result = self.client.execute_write(snapshot.tool, copy.deepcopy(args), permit)
        except BaseException:
            # Includes interruption: the server may have received the request.
            # A failed mark still leaves the original inflight row, which also
            # blocks duplicate attempts after a restart.
            try:
                self._mark(snapshot.fingerprint, "unknown")
            except sqlite3.Error:
                pass
            raise
        try:
            self._mark(snapshot.fingerprint, "succeeded")
        except sqlite3.Error:
            raise SafetyError("操作已返回结果，但本地记录未更新；请查询结果，勿重复提交。") from None
        return result


# Short alias for callers embedding the skill.
Gateway = ConfirmationGateway
