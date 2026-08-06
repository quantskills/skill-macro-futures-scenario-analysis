"""Transparent macro-to-futures transmission templates."""
from __future__ import annotations

TEMPLATES = {
    "AU": {
        "label": "沪金",
        "main_chain": "CPI surprise → 美联储路径 → 美元/实际利率 → 黄金估值",
        "counter_chain": "避险需求、央行购金或地缘风险可能抵消实际利率压力",
        "watch": ["美元指数", "美国10年期TIPS收益率", "沪金价格", "持仓量", "基差"],
    },
    "CU": {
        "label": "沪铜",
        "main_chain": "CPI surprise → 利率/美元与全球增长预期 → 制造业需求 → 铜价",
        "counter_chain": "矿端/冶炼约束、低库存或现货升水可能抵消宏观压力",
        "watch": ["美元指数", "美国收益率", "铜库存", "进口/现货基差", "持仓量"],
    },
    "SC": {
        "label": "SC原油",
        "main_chain": "CPI surprise → 利率与美国需求预期 → 原油需求/风险偏好 → SC价格",
        "counter_chain": "OPEC、地缘供应和库存变化可能压过CPI的利率传导",
        "watch": ["美元指数", "EIA库存", "WTI/Brent", "SC基差", "期限结构", "持仓量"],
    },
}


def infer_template(underlying: str) -> dict:
    return TEMPLATES.get(str(underlying).upper(), {
        "label": underlying, "main_chain": "宏观事件 → 利率/汇率/增长预期 → 品种供需 → 期货定价",
        "counter_chain": "品种自身供给、库存、基差和资金因素可能抵消宏观方向",
        "watch": ["价格", "成交量", "持仓量", "库存", "基差", "期限结构"],
    })
