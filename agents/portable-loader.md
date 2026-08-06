# Portable Runtime Loader

This file is the portable entry point for Hermes, OpenClaw, and other Markdown-capable runtimes.

## Load

1. Read `../SKILL.md` in full.
2. Follow its PandaData-only boundary, event-release PIT rules, contract-resolution rules, statuses, provenance, and scenario requirements.
3. Load only relevant files under `../references/`.
4. Prefer programs under `../scripts/` to duplicated calculations.

## Safety

- Use PandaData only for quantitative facts.
- Credentials may come only from documented environment variables or the local credential file and must never enter output.
- Never guess a contract, backfill missing data, promise a direction or return, or generate an automatic trade.
- Separate facts, derived metrics, and judgments; expose empty/error/unsupported data.
- State that output is research material and is not officially certified by QuantSkills.

## Default Task

Resolve the event and historical futures contracts first, retrieve point-in-time macro and futures evidence, then produce base, bullish, and bearish scenarios with a horizon, confirmation, invalidation, confidence, missing-data statement, and provenance.
