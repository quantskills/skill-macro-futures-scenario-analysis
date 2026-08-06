"""Scenario generation without unsupported probabilities."""
from __future__ import annotations


def build_scenarios(latest_event: dict | None, instruments: list[dict]) -> list[dict]:
    event = latest_event or {}
    return [
        {
            "name": "偏冷/降息预期升温",
            "trigger": "CPI及核心CPI低于预期，且美元与实际利率回落",
            "direction": {item["label"]: "偏强" if item["underlying"] in ("AU", "CU") else "方向分化" for item in instruments},
            "horizon": "日内至1—5个交易日",
            "confirmation": "美元指数和实际利率同步走弱，价格上涨得到成交量/持仓或现货验证",
            "invalidation": "实际利率不降、美元转强，或低通胀被解读为衰退冲击",
            "confidence": "中",
        },
        {
            "name": "符合预期/震荡消化",
            "trigger": "CPI与核心CPI大体符合预期，利率和美元反应有限",
            "direction": {item["label"]: "震荡" for item in instruments},
            "horizon": "1—5个交易日",
            "confirmation": "价格在事件前区间内运行，成交量和持仓未出现单边确认",
            "invalidation": "美元/实际利率出现持续单边变化，或品种供需数据发生重大偏离",
            "confidence": "中",
        },
        {
            "name": "偏热/实际利率上行",
            "trigger": "CPI尤其核心CPI高于预期，美元与实际利率上升",
            "direction": {item["label"]: "偏弱" if item["underlying"] in ("AU", "CU") else "方向不明" for item in instruments},
            "horizon": "日内至1—5个交易日",
            "confirmation": "实际利率和美元同步走强，贵金属/工业品价格跌破事件前结构位",
            "invalidation": "避险需求、供应冲击或现货紧张抵消利率压力",
            "confidence": "中",
        },
    ]
