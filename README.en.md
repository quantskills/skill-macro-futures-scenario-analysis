# Macro Event—Futures Scenario Analysis

[简体中文](README.md) | English

> This is a QuantSkills community project maintained by GitHub user `cikeqi`. It has not been independently reviewed, is not officially endorsed by QuantSkills, and makes no promise of returns or production suitability.

A standalone PandaData skill for researching how macro events and surprise data may transmit into futures. It resolves contracts point-in-time, retrieves available market structure evidence, and reports base, bullish, and bearish scenarios with confirmation and invalidation conditions. It does not promise direction, returns, or automated trades.

## Quick start

```bash
python3.11 scripts/macro_futures.py --probe-only --as-of 20260806
python3.11 scripts/macro_futures.py \
  --event USA.004 --symbols AU CU SC \
  --start-date 20260101 --end-date 20260806 --as-of 20260806
```

Credentials are read only from `PANDA_USERNAME`/`PANDA_PASSWORD` or `~/.pandadata/pandadata.env`. No credentials are shipped.

## What can I ask?

- Analyze the latest US CPI, payrolls, Fed decision, China PMI, credit, PPI, property policy, OPEC+ or EIA inventory event.
- Before an event, compare above-consensus, in-line, and below-consensus scenarios.
- After an event, compare actual, consensus, previous, surprise, dollar, rates, price, volume, and open interest.
- Analyze futures basis, inventories, warehouse receipts, term structure, roll, and contract selection.
- Compare gold, copper, crude, ferrous, chemical, and agricultural futures.
- Request a date range, explicit contract, or historical point-in-time analysis.

Example:

```text
As of [YYYY-MM-DD], analyze the latest released US CPI impact on SHFE gold, copper, and SC crude oil.
Before the next CPI release, provide above-consensus, in-line, and below-consensus scenarios.
Resolve the historical main contracts for AU, CU, and SC first; do not guess contract months.
```

The package contains a CLI, PandaData source wrapper, validators, event extraction, futures contract resolution, transmission templates, scenario generation, JSON/Markdown reporting, references, adapters, and tests. See `README.md` and `SKILL.md` for the full contract.

Interfaces that are absent or unavailable are reported as `unsupported`; successful empty calls are `empty`. Report dates and publication dates are kept separate, and actual event values cannot be used before publication.
