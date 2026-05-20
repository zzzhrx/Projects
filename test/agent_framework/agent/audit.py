from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuditRecord:
    tool_name: str
    args: dict[str, Any]
    result: Any | None = None
    error: str | None = None
    user_id: str = "unknown"
    thread_id: str = "unknown"
    approved: bool = False
    dry_run: bool = False
    timestamp: float = field(default_factory=time.time)
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditLogger:
    """Logs tool invocations for compliance, debugging, and billing.

    Default implementation writes JSON lines to stderr via the logging module.
    Replace with database-backed implementation for production use.
    """

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    def log(self, record: AuditRecord) -> None:
        if not self._enabled:
            return
        entry = json.dumps(record.to_dict(), ensure_ascii=False, default=str)
        logger.info("audit: %s", entry)


class ApprovalGate:
    """Decides whether a tool call requires explicit user approval.

    Phase 1: all tools are read-only (no side effects), so no approval needed.
    Phase 2: tools marked has_side_effects=True require approval before execution.
    """

    def __init__(self, interactive_prompt: bool = False) -> None:
        self._interactive = interactive_prompt

    def requires_approval(self, tool_name: str, tool_meta: dict[str, Any] | None = None) -> bool:
        if not tool_meta:
            return False
        return bool(tool_meta.get("has_side_effects", False))

    def request_approval(self, tool_name: str, args: dict[str, Any]) -> bool:
        """Present the tool call to the user for confirmation.

        Returns True if approved, False otherwise.
        """
        if not self._interactive:
            return False

        print(f"\n[审批] 工具 {tool_name!r} 需要您的确认才能执行:")
        print(f"  参数: {json.dumps(args, ensure_ascii=False)}")
        response = input("  确认执行? (y/n): ").strip().lower()
        return response in ("y", "yes", "是")


class DryRunMode:
    """Wraps a tool to support dry_run=True, returning simulated results.

    When dry_run is True, the tool is NOT actually invoked. Instead a placeholder
    result is returned so the agent can preview what would happen.
    """

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def wrap_result(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "source": "dry_run",
            "tool": tool_name,
            "args": args,
            "note": "This is a simulated result. The tool was not actually executed.",
        }
