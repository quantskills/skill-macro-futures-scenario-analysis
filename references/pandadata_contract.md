# PandaData 数据契约

> SDK 中存在的方法不等于当前账号服务端可用；以 `--probe-only` 实测结果为准。

## 认证

只读取：

- `PANDA_USERNAME`
- `PANDA_PASSWORD`
- `~/.pandadata/pandadata.env`

凭证不得进入 JSON、Markdown、日志、异常或版本控制。

## 主要接口

| 模块 | 方法 | 关键字段/用途 |
|---|---|---|
| 交易日 | `get_trade_cal` | 完整交易日与 `is_trade` |
| 事件配置 | `get_macro_cal_config` | 事件代码、指标名称、地区 |
| 事件数据 | `get_macro_cal` | 发布时间、报告期、actual、consensus、previous |
| 事件时间 | `get_macro_cal_info` | 北京发布日期/时间与指标期数 |
| 指标元数据 | `get_macro_detail` | 频率、单位、来源、API 名称 |
| 国际宏观 | `get_macro_gb` | `symbol/period_date/data_value` |
| 期货详情 | `get_future_detail` | 合约、交易所、乘数、到期、交易时间 |
| 主力映射 | `get_future_dominant` | 品种、日期、实际主力合约 |
| 期货日线 | `get_future_daily` | OHLC、成交量、持仓量、结算价 |
| 复权连续 | `get_future_daily_post` | 复权方法必须明确，不等同现货价格 |
| 基差 | `get_future_basis` | underlying、date、basis、spot_price |
| 期限结构 | `get_future_term_structure` | 合约、日期、收盘价 |
| 库存 | `get_future_inventory` | 日期、库存量、品种 |
| 仓单 | `get_future_warehouse_receipt` | 仓单数量和变化 |
| 净持仓 | `get_future_netposi_rank` | 席位、方向、净持仓 |

## 状态

- `ok`：返回记录且满足必要字段；
- `empty`：调用成功但没有记录；
- `error`：认证、权限、参数、服务或字段问题；
- `unsupported`：SDK 或服务端没有该方法，或当前能力未批准。

每项溯源必须包含：方法、用途、参数摘要、行数、列名、最新日期、状态和无敏感错误摘要。

## 时间边界

- `as_of` 之后的事件、行情和指标不得进入报告；
- actual 只能在 `pub_date_bj/pub_date` 不晚于 `as_of` 时使用；
- report_period 是统计期，不是市场获知时间；
- 主力合约按请求区间逐日解析，不能用当前主力替代历史主力；
- 空库存或空基差必须显示 `empty`，不能用价格推断并填充。

## 口径

- surprise 只在 actual 和 consensus 同时存在、单位一致时计算；
- OHLC 满足 `high >= max(open, low, close)` 与 `low <= min(open, high, close)`；
- 结算价与收盘价不能混写；
- 单位、币种、乘数、交易所和到期日必须保留；
- 相关性、持仓变化和库存变化都不能单独构成因果或交易结论。
