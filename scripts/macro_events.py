"""Macro calendar and surprise extraction."""
from __future__ import annotations

from typing import Any

import pandas as pd

from validators import calculate_surprise, filter_pit


def resolve_event(source, event_code: str, start_date: str, end_date: str, as_of: str | None = None) -> dict[str, Any]:
    config = source.call("get_macro_cal_config", purpose="解析宏观事件代码", event_code=[event_code])
    calendar = source.call(
        "get_macro_cal", purpose="读取宏观事件实际值与预期值",
        event_code=[event_code], start_date=start_date, end_date=end_date,
    )
    info = source.call(
        "get_macro_cal_info", purpose="读取宏观事件发布时间",
        event_code=[event_code], start_date=start_date, end_date=end_date,
    )
    frame = calendar.data.copy()
    if as_of and not frame.empty:
        frame = filter_pit(frame, ("pub_date_bj", "pub_date"), as_of)
    records = []
    for _, row in frame.iterrows():
        actual = row.get("actual_value")
        consensus = row.get("consensus_value")
        unit = row.get("unit_cn")
        surprise = calculate_surprise(actual, consensus, unit)
        records.append({
            "event_code": row.get("event_code", event_code),
            "event_name": row.get("event_name_cn", ""),
            "indicator": row.get("indicator_name_cn", ""),
            "country": row.get("country_name_cn", row.get("country_code", "")),
            "pub_date_bj": row.get("pub_date_bj", row.get("pub_date")),
            "pub_time_bj": row.get("pub_time_bj"),
            "report_period": row.get("report_period"),
            "actual": actual,
            "consensus": consensus,
            "previous": row.get("previous_value"),
            "unit": unit,
            "surprise": surprise["value"],
            "surprise_reason": surprise["reason"],
            "source": row.get("source_cn"),
        })
    return {
        "event_code": event_code,
        "config": config.data.to_dict(orient="records") if not config.data.empty else [],
        "records": records,
        "calendar_status": calendar.status,
        "info_status": info.status,
    }


def choose_latest(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    ordered = sorted(records, key=lambda row: str(row.get("pub_date_bj") or ""))
    return ordered[-1]
