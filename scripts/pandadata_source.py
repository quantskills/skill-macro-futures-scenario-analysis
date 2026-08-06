"""PandaData source layer with provenance, redaction, and explicit statuses."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import pandas as pd

ENV_FILE = Path.home() / ".pandadata" / "pandadata.env"
SENSITIVE_PATTERN = re.compile(r"(?i)(password|passwd|token|username)\s*[=:]\s*[^\s,;]+")
DATE_COLUMNS = (
    "date", "trading_date", "pub_date_bj", "pub_date", "period_date",
    "report_period", "nature_date", "maturity_date",
)


def _read_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load_credentials() -> tuple[str, str]:
    file_values = _read_env_file()
    username = os.environ.get("PANDA_USERNAME") or file_values.get("PANDA_USERNAME", "")
    password = os.environ.get("PANDA_PASSWORD") or file_values.get("PANDA_PASSWORD", "")
    if not username or not password:
        raise RuntimeError(
            "缺少 PandaData 凭证。请设置 PANDA_USERNAME/PANDA_PASSWORD，"
            "或写入 ~/.pandadata/pandadata.env。"
        )
    return username, password


def sanitize_error(error: Exception | str) -> str:
    return SENSITIVE_PATTERN.sub(
        lambda match: f"{match.group(1)}=<redacted>", str(error)
    )[:500]


def compact_params(params: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in params.items():
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            result[f"{key}_count"] = len(value)
            result[f"{key}_sample"] = value[:5]
        else:
            result[key] = value
    return result


def latest_date(frame: pd.DataFrame) -> str | None:
    for column in DATE_COLUMNS:
        if column in frame.columns and frame[column].notna().any():
            return str(frame[column].dropna().astype(str).max())
    return None


@dataclass
class CallResult:
    method: str
    status: str
    purpose: str = ""
    data: pd.DataFrame = field(default_factory=pd.DataFrame, repr=False)
    rows: int = 0
    columns: list[str] = field(default_factory=list)
    latest_date: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    attempts: int = 1

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def provenance(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "purpose": self.purpose,
            "status": self.status,
            "rows": self.rows,
            "columns": self.columns,
            "latest_date": self.latest_date,
            "params": self.params,
            "error": self.error,
            "attempts": self.attempts,
        }


class PandaDataSource:
    """Authenticated wrapper around the installed panda_data SDK."""

    def __init__(self, retries: int = 2, retry_delay: float = 0.8):
        try:
            import panda_data
        except ImportError as exc:
            raise RuntimeError("未安装 panda_data，请安装与项目兼容的 SDK") from exc
        username, password = load_credentials()
        panda_data.init_token(username=username, password=password)
        self.api = panda_data
        self.retries = max(1, retries)
        self.retry_delay = max(0.0, retry_delay)
        self.calls: list[CallResult] = []

    def call(
        self,
        method: str,
        *,
        purpose: str = "",
        required_columns: tuple[str, ...] = (),
        unsupported_hint: bool = False,
        **params: Any,
    ) -> CallResult:
        fn: Callable[..., Any] | None = getattr(self.api, method, None)
        safe_params = compact_params(params)
        if fn is None:
            result = CallResult(
                method=method, purpose=purpose, status="unsupported",
                params=safe_params, error="当前 panda_data SDK 不包含该方法",
            )
            self.calls.append(result)
            return result

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                raw = fn(**params)
                if raw is None:
                    frame = pd.DataFrame()
                elif isinstance(raw, pd.DataFrame):
                    frame = raw.copy()
                else:
                    frame = pd.DataFrame(raw)
                missing = [column for column in required_columns if column not in frame.columns]
                if frame.empty:
                    status, error = "empty", "接口调用成功但未返回记录"
                elif missing:
                    status, error = "error", f"缺少必要字段: {', '.join(missing)}"
                else:
                    status, error = "ok", None
                result = CallResult(
                    method=method, purpose=purpose, status=status, data=frame,
                    rows=len(frame), columns=[str(c) for c in frame.columns],
                    latest_date=latest_date(frame), params=safe_params,
                    error=error, attempts=attempt,
                )
                self.calls.append(result)
                return result
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.retry_delay * attempt)

        error_text = sanitize_error(last_error or "未知错误")
        lower = error_text.lower()
        unsupported = unsupported_hint and any(
            marker in lower for marker in
            ("not support", "unsupported", "not found", "未上线", "废弃", "404")
        )
        result = CallResult(
            method=method, purpose=purpose,
            status="unsupported" if unsupported else "error",
            params=safe_params, error=error_text, attempts=self.retries,
        )
        self.calls.append(result)
        return result

    def provenance(self) -> list[dict[str, Any]]:
        return [call.provenance() for call in self.calls]


def date_window(as_of: str, calendar_days: int) -> tuple[str, str]:
    end = datetime.strptime(as_of, "%Y%m%d")
    start = end - timedelta(days=calendar_days)
    return start.strftime("%Y%m%d"), as_of


def resolve_as_of(source: PandaDataSource, requested: str | None = None) -> str:
    target = requested or datetime.now().strftime("%Y%m%d")
    datetime.strptime(target, "%Y%m%d")
    start, _ = date_window(target, 20)
    result = source.call(
        "get_trade_cal", purpose="解析最近完整交易日",
        start_date=start, end_date=target,
    )
    if result.ok:
        frame = result.data.copy()
        date_col = "nature_date" if "nature_date" in frame.columns else "date"
        if date_col in frame.columns:
            if "is_trade" in frame.columns:
                trade = pd.to_numeric(frame["is_trade"], errors="coerce").fillna(0).astype(bool)
                frame = frame.loc[trade]
            dates = frame[date_col].astype(str)
            dates = dates[dates <= target]
            if not dates.empty:
                return str(dates.max())
    return target


PROBE_METHODS = [
    "get_trade_cal", "get_macro_cal_config", "get_macro_cal",
    "get_macro_cal_info", "get_macro_detail", "get_macro_gb",
    "get_future_detail", "get_future_dominant", "get_future_daily",
    "get_future_daily_post", "get_future_basis", "get_future_term_structure",
    "get_future_inventory", "get_future_warehouse_receipt",
    "get_future_netposi_rank",
]


def probe_interfaces(source: PandaDataSource, as_of: str) -> list[dict[str, Any]]:
    start, _ = date_window(as_of, 10)
    probes = [
        ("get_trade_cal", dict(start_date=start, end_date=as_of)),
        ("get_macro_cal_config", dict(event_code=["USA.004"])),
        ("get_macro_cal", dict(event_code=["USA.004"], start_date="20260101", end_date=as_of)),
        ("get_macro_cal_info", dict(event_code=["USA.004"], start_date=start, end_date=as_of)),
        ("get_macro_detail", dict(symbol=["US0000010"], category="US")),
        ("get_macro_gb", dict(symbol=["US0000010"], start_date="20250101", end_date=as_of)),
        ("get_future_detail", dict(symbol=["AU2610.SHF"])),
        ("get_future_dominant", dict(underlying_symbol=["AU"], start_date=start, end_date=as_of)),
        ("get_future_daily", dict(symbol=["AU2610.SHF"], start_date=start, end_date=as_of)),
        ("get_future_daily_post", dict(underlying_symbol=["AU"], start_date=start, end_date=as_of)),
        ("get_future_basis", dict(underlying_symbol=["AU"], start_date=start, end_date=as_of)),
        ("get_future_term_structure", dict(symbol=["AU2610.SHF"], start_date=start, end_date=as_of)),
        ("get_future_inventory", dict(symbol=["AU2610.SHF"], start_date=start, end_date=as_of)),
        ("get_future_warehouse_receipt", dict(underlying_symbol=["AU"], start_date=start, end_date=as_of)),
        ("get_future_netposi_rank", dict(underlying_symbol=["AU"], start_date=start, end_date=as_of)),
    ]
    for method, params in probes:
        source.call(method, purpose="接口探测", unsupported_hint=True, **params)
    return source.provenance()
