"""JSON and Markdown report rendering."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        try: return value.item()
        except Exception: pass
    if hasattr(value, "to_dict"):
        return value.to_dict(orient="records")
    if isinstance(value, dict): return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [json_safe(v) for v in value]
    return str(value)


def write_json(path: str, payload: dict) -> None:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(json_safe(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(path: str, payload: dict) -> None:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 宏观事件—期货预期分析报告", "", "## 1. 请求与分析范围"]
    request = payload.get("request", {})
    for key, value in request.items(): lines.append(f"- {key}：{value}")
    lines += ["", "## 2. 数据与来源状态", "| 用途 | 方法 | 状态 | 行数 | 最新日期 | 说明 |", "|---|---|---|---:|---|---|"]
    for item in payload.get("provenance", []):
        lines.append(f"| {item.get('purpose','')} | `{item.get('method','')}` | {item.get('status','')} | {item.get('rows',0)} | {item.get('latest_date') or '-'} | {item.get('error') or '-'} |")
    lines += ["", "## 3. 事件与预期差"]
    event = payload.get("event", {})
    latest = event.get("latest") or {}
    if latest:
        for key in ("event_name", "indicator", "pub_date_bj", "report_period", "actual", "consensus", "previous", "unit", "surprise", "surprise_reason"):
            lines.append(f"- {key}：{latest.get(key)}")
    else: lines.append("- 当前日期范围没有可用事件记录；以下仅输出机制与情景，不伪造实际值。")
    lines += ["", "## 4. 宏观传导链"]
    for item in payload.get("instruments", []):
        lines += [f"### {item.get('label')}（{item.get('contract')}）", f"- 主链：{item.get('main_chain')}", f"- 反向链：{item.get('counter_chain')}", f"- 观察变量：{', '.join(item.get('watch', []))}"]
    lines += ["", "## 5. 当前市场定价"]
    for item in payload.get("market", []):
        lines.append(f"- **{item.get('label')}**：收盘 {item.get('close')}；区间变化 {item.get('return_pct')}%；持仓 {item.get('open_interest')}；基差最新值 {item.get('basis')}")
    lines += ["", "## 6. 情景分析", "| 情景 | 触发条件 | 品种方向 | 时间窗口 | 确认条件 | 失效条件 | 置信度 |", "|---|---|---|---|---|---|---|"]
    for scenario in payload.get("scenarios", []):
        direction = "; ".join(f"{k}: {v}" for k, v in scenario.get("direction", {}).items())
        lines.append(f"| {scenario['name']} | {scenario['trigger']} | {direction} | {scenario['horizon']} | {scenario['confirmation']} | {scenario['invalidation']} | {scenario['confidence']} |")
    lines += ["", "## 7. 条件化观察"]
    for line in payload.get("observations", []): lines.append(f"1. {line}")
    lines += ["", "## 8. 风险边界与结论", "- 本报告为研究材料，不构成投资建议、收益承诺或直接下单指令。", "- 空结果、不可用接口和数据口径限制均已在数据状态表中保留。"]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
