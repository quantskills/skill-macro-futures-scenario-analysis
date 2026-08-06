#!/usr/bin/env python3
"""CLI for PandaData macro-event to futures scenario analysis."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from futures_data import fetch_contract_data, fetch_details, fetch_structure, resolve_contracts
from macro_events import choose_latest, resolve_event
from pandadata_source import PandaDataSource, probe_interfaces, resolve_as_of
from report import write_json, write_markdown
from scenarios import build_scenarios
from transmission import infer_template
from validators import validate_date_range


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="宏观事件—期货预期分析")
    parser.add_argument("--event", default="USA.004", help="宏观日历事件代码，默认美国CPI USA.004")
    parser.add_argument("--symbols", nargs="+", default=["AU", "CU", "SC"], help="品种根代码或明确合约")
    parser.add_argument("--start-date", help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", help="结束日期 YYYYMMDD")
    parser.add_argument("--as-of", help="硬截止日期 YYYYMMDD")
    parser.add_argument("--horizon", default="1—5个交易日", help="分析观察窗口")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--out-json", default="/tmp/macro_futures.json")
    parser.add_argument("--out-md", default="/tmp/macro_futures.md")
    return parser.parse_args()


def summarize_market(frame: pd.DataFrame, basis_frame: pd.DataFrame, instruments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for item in instruments:
        contract = item["contract"]
        rows = frame[frame["symbol"].astype(str) == contract].sort_values("date") if not frame.empty and "symbol" in frame.columns else pd.DataFrame()
        market = {"label": item["label"], "contract": contract, "close": None, "return_pct": None, "open_interest": None, "basis": None}
        if not rows.empty:
            first = pd.to_numeric(rows.iloc[0].get("close"), errors="coerce")
            last = pd.to_numeric(rows.iloc[-1].get("close"), errors="coerce")
            market["close"] = None if pd.isna(last) else float(last)
            if not pd.isna(first) and not pd.isna(last) and first != 0:
                market["return_pct"] = round((float(last) / float(first) - 1) * 100, 2)
            oi = pd.to_numeric(rows.iloc[-1].get("open_interest"), errors="coerce")
            market["open_interest"] = None if pd.isna(oi) else float(oi)
        if not basis_frame.empty and "underlying_symbol" in basis_frame.columns:
            subset = basis_frame[basis_frame["underlying_symbol"].astype(str).str.upper() == item["underlying"]].copy()
            if not subset.empty:
                subset = subset.sort_values("date") if "date" in subset.columns else subset
                value = pd.to_numeric(subset.iloc[-1].get("basis"), errors="coerce")
                market["basis"] = None if pd.isna(value) else float(value)
        output.append(market)
    return output


def main() -> int:
    args = parse_args()
    source = PandaDataSource()
    as_of = resolve_as_of(source, args.as_of or args.end_date)
    if args.probe_only:
        probes = probe_interfaces(source, as_of)
        payload = {"request": {"模式": "接口探测", "截止日": as_of}, "provenance": probes, "event": {}, "instruments": [], "market": [], "scenarios": [], "observations": ["接口静态存在不等于当前账号可用，以本探测状态为准。"]}
        write_json(args.out_json, payload); write_markdown(args.out_md, payload)
        print(f"probe complete: {args.out_json} {args.out_md}")
        return 0

    end_date = args.end_date or as_of
    start_date = args.start_date or (str(int(end_date[:4]) - 1) + end_date[4:])
    validate_date_range(start_date, end_date)

    contracts = resolve_contracts(source, [s.upper() for s in args.symbols], start_date, end_date)
    resolved = list(dict.fromkeys(contracts["resolved"].values()))
    if not resolved:
        raise RuntimeError("没有解析出任何期货合约；请提供明确合约或可识别品种根代码")
    details = fetch_details(source, resolved)
    daily = fetch_contract_data(source, resolved, start_date, end_date, as_of)
    roots = []
    if details.ok and "underlying_symbol" in details.data.columns:
        roots = sorted(set(details.data["underlying_symbol"].dropna().astype(str).str.upper()))
    if not roots:
        roots = [key.upper() for key in contracts["resolved"] if key.isalpha()]
    structure = fetch_structure(source, roots, resolved, start_date, end_date)
    event_start = str(int(end_date[:4]) - 1) + "0101"
    event = resolve_event(source, args.event, event_start, end_date, as_of)
    latest = choose_latest(event["records"])

    instruments = []
    detail_rows = details.data.to_dict(orient="records") if details.ok else []
    for requested, contract in contracts["resolved"].items():
        detail = next((row for row in detail_rows if str(row.get("symbol")) == contract), {})
        underlying = str(detail.get("underlying_symbol") or (requested if requested.isalpha() else "")).upper()
        template = infer_template(underlying)
        instruments.append({"requested": requested, "contract": contract, "underlying": underlying, **template, "detail": detail})

    basis_frame = structure["basis"].data if structure["basis"].ok else pd.DataFrame()
    market = summarize_market(daily["data"], basis_frame, instruments)
    payload = {
        "request": {"事件": args.event, "品种/合约": ", ".join(args.symbols), "开始日期": start_date, "结束日期": end_date, "截止日": as_of, "观察窗口": args.horizon},
        "event": {**event, "latest": latest},
        "contracts": contracts,
        "instruments": instruments,
        "market": market,
        "validation": {"ohlc": daily["validation"], "duplicates": daily["duplicates"]},
        "scenarios": build_scenarios(latest, instruments),
        "observations": [
            "actual 只在事件发布日期不晚于 as_of 时使用；报告期不等于发布日期。",
            "品种根代码通过 get_future_dominant 解析，不自行拼接合约月份。",
            "库存、基差或期限结构为空时保持 N/A，不据此补造供需结论。",
        ],
        "provenance": source.provenance(),
    }
    write_json(args.out_json, payload); write_markdown(args.out_md, payload)
    print(f"analysis complete: {args.out_json} {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
