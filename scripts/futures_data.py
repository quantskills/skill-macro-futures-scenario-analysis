"""Futures contract resolution and market-data validation."""
from __future__ import annotations

from typing import Any

import pandas as pd

from validators import filter_pit, validate_ohlc, validate_unique_dates


def resolve_contracts(source, symbols: list[str], start_date: str, end_date: str) -> dict[str, Any]:
    resolved: dict[str, str] = {}
    evidence: list[dict[str, Any]] = []
    roots = [symbol for symbol in symbols if "." not in symbol and symbol.isalpha()]
    explicit = [symbol for symbol in symbols if symbol not in roots]
    for symbol in explicit:
        resolved[symbol] = symbol
        evidence.append({"requested": symbol, "resolved": symbol, "method": "explicit", "status": "ok"})
    if roots:
        result = source.call(
            "get_future_dominant", purpose="解析品种主力合约",
            underlying_symbol=roots, start_date=start_date, end_date=end_date,
        )
        if result.ok:
            frame = result.data.copy()
            if {"underlying_symbol", "symbol", "date"}.issubset(frame.columns):
                frame["date"] = frame["date"].astype(str)
                for root in roots:
                    rows = frame[(frame["underlying_symbol"].astype(str).str.upper() == root.upper()) & (frame["date"] <= end_date)]
                    if not rows.empty:
                        row = rows.sort_values("date").iloc[-1]
                        resolved[root] = str(row["symbol"])
                        evidence.append({"requested": root, "resolved": str(row["symbol"]), "resolution_date": str(row["date"]), "method": "get_future_dominant", "status": "ok"})
                    else:
                        evidence.append({"requested": root, "method": "get_future_dominant", "status": "empty", "reason": "没有不晚于结束日期的主力映射"})
        else:
            evidence.extend({"requested": root, "method": "get_future_dominant", "status": result.status, "reason": result.error} for root in roots)
    return {"resolved": resolved, "evidence": evidence}


def fetch_contract_data(source, contracts: list[str], start_date: str, end_date: str, as_of: str | None = None) -> dict[str, Any]:
    result = source.call(
        "get_future_daily", purpose="读取期货日线与持仓",
        symbol=contracts, start_date=start_date, end_date=end_date,
        fields=["date", "symbol", "underlying_symbol", "open", "high", "low", "close", "volume", "open_interest", "settlement", "pre_settlement"],
    )
    frame = result.data.copy()
    if as_of and not frame.empty:
        frame = filter_pit(frame, ("date",), as_of)
    validation = validate_ohlc(frame)
    duplicates = validate_unique_dates(frame)
    return {"result": result, "data": frame, "validation": validation, "duplicates": duplicates}


def fetch_structure(source, underlyings: list[str], contracts: list[str], start_date: str, end_date: str) -> dict[str, Any]:
    basis = source.call("get_future_basis", purpose="读取期货基差", underlying_symbol=underlyings, start_date=start_date, end_date=end_date)
    term = source.call("get_future_term_structure", purpose="读取期货期限结构", symbol=contracts, start_date=start_date, end_date=end_date)
    inventory = source.call("get_future_inventory", purpose="读取期货库存", symbol=contracts, start_date=start_date, end_date=end_date)
    receipt = source.call("get_future_warehouse_receipt", purpose="读取期货仓单", underlying_symbol=underlyings, start_date=start_date, end_date=end_date)
    return {"basis": basis, "term": term, "inventory": inventory, "receipt": receipt}


def fetch_details(source, contracts: list[str]) -> Any:
    return source.call("get_future_detail", purpose="读取合约基本信息", symbol=contracts, fields=["symbol", "name", "exchange", "underlying_symbol", "maturity_date", "contract_multiplier", "trading_hours"])
