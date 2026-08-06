# 宏观事件—期货预期分析

简体中文 | [English](README.en.md)

> QuantSkills 社区项目，由 GitHub 用户 `cikeqi` 维护。项目尚未经过独立审核，不代表 QuantSkills 官方认证，也不承诺收益或生产环境适用性。

独立交付版 PandaData Skill：先确认宏观事件和发布时间，再解析指定期货合约，结合价格、持仓、基差、期限结构及可用库存，输出条件化三情景。默认事件为美国 CPI `USA.004`，默认品种为 `AU CU SC`。

## 文件

- `SKILL.md`：触发说明、输入、硬规则和输出契约
- `scripts/macro_futures.py`：主 CLI 和报告编排
- `scripts/pandadata_source.py`：认证、调用、状态和溯源
- `scripts/validators.py`：日期、PIT、OHLC 和 surprise 校验
- `scripts/macro_events.py`：宏观日历和预期差
- `scripts/futures_data.py`：合约解析、行情和结构
- `scripts/transmission.py`：品种传导模板
- `scripts/scenarios.py`：基准/偏强/偏弱情景
- `scripts/report.py`：JSON/Markdown 输出
- `references/`：方法论、数据契约和合约规则
- `agents/`：Claude Code、便携运行时和 Cursor 适配器
- `tests/`：确定性单元测试

## 凭证

只从环境变量或 `~/.pandadata/pandadata.env` 读取：

```bash
export PANDA_USERNAME='你的账号'
export PANDA_PASSWORD='你的密码'
```

包内不包含账号、密码或 token。

## 快速运行

接口探测：

```bash
python3.11 scripts/macro_futures.py --probe-only --as-of 20260806
```

分析美国 CPI：

```bash
python3.11 scripts/macro_futures.py \
  --event USA.004 --symbols AU CU SC \
  --start-date 20260101 --end-date 20260806 --as-of 20260806
```

明确合约：

```bash
python3.11 scripts/macro_futures.py \
  --event USA.004 \
  --symbols AU2610.SHF CU2609.SHF SC2609.INE \
  --start-date 20260701 --end-date 20260806
```

默认输出：

```text
/tmp/macro_futures.json
/tmp/macro_futures.md
```

## 可以问什么（可直接复制）

这个 Skill 适合询问以下几类问题。为减少歧义，建议同时提供分析截止日期、观察区间和期货品种或明确合约；把示例中的方括号替换成自己的条件即可。

### 1. 宏观事件影响

```text
截至【YYYY-MM-DD】，分析最近一次美国 CPI 对沪金、沪铜和 SC 原油的影响。
分析美国非农低于预期对黄金、铜和原油期货的影响。
分析美联储降息或维持利率不变但表态偏鹰，对贵金属和工业品期货的影响。
分析中国 PMI、社融、M2、PPI 或固定资产投资对螺纹钢、铁矿石和铜的影响。
分析 OPEC+ 会议、EIA 库存、房地产政策或基建政策对相关期货的影响。
```

### 2. 事件公布前情景

```text
美国 CPI 尚未公布，请给出高于预期、符合预期和低于预期三种情景。
美联储议息会议前，请分析黄金、铜和原油期货的主要预期差与风险。
EIA 原油库存公布前，请分析库存增加、符合预期和下降三种情景。
```

### 3. 事件公布后的实际分析

```text
美国 CPI 已公布，请结合 actual、consensus 和 previous 分析沪金。
中国 PMI 已于【YYYY-MM-DD】公布，请结合实际值、预期值和前值分析黑色系期货。
数据公布后美元和黄金同时上涨，请分析这种背离可能由什么因素造成。
```

### 4. 期货供需分析

```text
分析螺纹钢的产量、高炉开工率、社会库存、铁矿石港口库存和基差。
分析沪铜的库存、进口、现货升贴水、美元、持仓量和需求预期。
分析原油的 WTI、Brent、EIA 原油库存、汽油库存、库欣库存和期限结构。
分析 PTA、甲醇、聚烯烃或豆粕的产量、进口、库存、开工率和下游需求。
```

### 5. 期货市场结构

```text
分析【品种或合约】在【日期区间】的上涨是否得到成交量和持仓量确认。
分析【品种或合约】在【日期区间】的基差扩大或收窄代表什么。
分析【品种】近月与远月价差，判断期限结构偏紧还是偏松。
请先解析 AU、CU、SC 的历史主力合约，再分析事件影响，不要猜月份。
```

### 6. 多品种比较

```text
比较沪金、沪银、沪铜和原油对美国利率变化的敏感度。
比较螺纹钢、铁矿石和焦煤对房地产与基建政策的敏感度。
比较铜、铝、锌的供需紧张程度和宏观敏感度。
在全球经济放缓情景下，比较黄金、铜、原油和螺纹钢的传导方向、确认条件与主要风险。
```

### 7. 指定日期与合约

```text
截至 2026-08-06，分析中国 PMI 对螺纹钢和铁矿石的影响。
分析 20260701—20260806 沪铜主力合约的价格、成交量、持仓量、基差和库存。
分析 CU2609.SHF 在指定日期区间受到美国宏观数据影响的情况。
以某日收盘为截止日，分析未来 1—5 个交易日的三种情景。
```

### 推荐的完整问法

```text
请使用 skill-macro-futures-scenario-analysis，分析【事件/指标/政策/供需变化】对【期货品种或合约】的影响。

分析区间：【YYYYMMDD—YYYYMMDD】
观察周期：【日内 / 未来1—5个交易日 / 数周 / 数月】
请结合：
1. 实际值、市场预期和前值；
2. surprise 与宏观传导链；
3. 产量、开工率、进口、库存和基差；
4. 价格、成交量、持仓量和期限结构；
5. 市场是否已经提前定价；
6. 基准、偏强和偏弱三种情景；
7. 每种情景的确认条件、失效条件和置信度。
```

### 不推荐与推荐

```text
原油会涨吗？
```

建议改成：

```text
请结合 EIA 库存、WTI/Brent、SC 原油、期限结构和持仓量，分析未来 1—5 个交易日原油期货的偏强、偏弱和震荡情景。
```

```text
分析螺纹钢。
```

建议改成：

```text
请先通过 PandaData 解析截至指定日期的螺纹钢主力合约，再结合产量、高炉开工、社会库存、基差和宏观需求分析未来数周情景。
```

## 测试

```bash
python3.11 -m unittest discover -s tests -v
```

## 限制

- SDK 或账号没有的接口会显示 `unsupported`，空数据显示 `empty`，不会静默补值；
- 事件报告期不等于发布日期；
- CPI surprise 需要 actual、consensus 和同口径单位；
- 库存、基差和期限结构缺失时，相应结论降级；
- 输出仅供研究与教育，不构成投资建议、收益承诺或自动交易指令。

## 许可

GPL-3.0-only。未声明 QuantSkills 官方认证。
