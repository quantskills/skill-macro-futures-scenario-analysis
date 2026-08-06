"""Deterministic validation helpers for macro and futures data."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def valid_date(value: Any) -> bool:
    try:
        datetime.strptime(str(value), "%Y%m%d")
        return True
    except (TypeError, ValueError):
        return False


def validate_date_range(start: str, end: str) -> None:
    if not valid_date(start) or not valid_date(end):
        raise ValueError("日期必须为 YYYYMMDD")
    if start > end:
        raise ValueError("start_date 不能晚于 end_date")


def filter_pit(frame: pd.DataFrame, date_columns: tuple[str, ...], as_of: str) -> pd.DataFrame:
    result = frame.copy()
    for column in date_columns:
        if column in result.columns:
            result = result[result[column].astype(str) <= as_of]
            break
    return result


def validate_unique_dates(frame: pd.DataFrame, keys: tuple[str, ...] = ("date", "symbol")) -> list[str]:
    present = [key for key in keys if key in frame.columns]
    if not present:
        return []
    duplicates = frame.loc[frame.duplicated(present, keep=False), present]
    return ["|".join(str(row[key]) for key in present) for _, row in duplicates.iterrows()]


def validate_ohlc(frame: pd.DataFrame) -> dict[str, Any]:
    required = ["open", "high", "low", "close"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        return {"ok": False, "reason": f"缺少字段: {', '.join(missing)}"}
    numeric = frame[required].apply(pd.to_numeric, errors="coerce")
    finite = numeric.notna().all(axis=1)
    relation = (
        (numeric["high"] >= numeric[["open", "low", "close"]].max(axis=1))
        & (numeric["low"] <= numeric[["open", "high", "close"]].min(axis=1))
    )
    invalid = ~(finite & relation)
    return {"ok": not bool(invalid.any()), "invalid_rows": int(invalid.sum()), "reason": "OHLC关系或数值无效" if invalid.any() else None}


def validate_nonnegative(frame: pd.DataFrame, columns: tuple[str, ...]) -> dict[str, Any]:
    checked: dict[str, int] = {}
    for column in columns:
        if column in frame.columns:
            values = pd.to_numeric(frame[column], errors="coerce")
            checked[column] = int((values < 0).sum())
    bad = {key: value for key, value in checked.items() if value}
    return {"ok": not bad, "negative_rows": bad}


def calculate_surprise(actual: Any, consensus: Any, unit: Any = None, actual_unit: Any = None) -> dict[str, Any]:
    if actual is None or consensus is None or pd.isna(actual) or pd.isna(consensus):
        return {"value": None, "reason": "actual 或 consensus 缺失"}
    if unit is not None and actual_unit is not None and str(unit) != str(actual_unit):
        return {"value": None, "reason": "单位不一致"}
    try:
        value = float(actual) - float(consensus)
    except (TypeError, ValueError):
        return {"value": None, "reason": "数值不可计算"}
    return {"value": value, "reason": None}
