# semantic-values

> **Work in progress.** Research phase (v0 foundations) is done; no value data has been
> produced yet. No raw source text is stored in this repository.

Measuring how **societal values** (what ordinary people care about, not what governments
officially say) change **over time** and **between countries**, and how values **spread from
country to country**. Values are derived from newspaper and magazine text (opinion pieces,
columns, letters, editorials, and popular magazines), tagged with Schwartz's refined theory of
basic human values, and findings are published as blog posts.

## v0 scope

Countries: France, Netherlands, Belgium, Luxembourg, Germany, Austria, Switzerland, Italy,
Greece, Spain, Portugal and the United Kingdom. Focus period: recent (first target 2005 to now).

## Data policy

Raw text is never committed. The repository holds only references (source, URL/ID, date,
country, language) and extracted values; raw text is cached locally and git-ignored.

## Research so far

- [Literature review](docs/research/literature-review.md)
- [Framework decision](docs/research/framework-decision.md): Schwartz 19 values, validated
  against the European Social Survey
- [Source survey](docs/research/sources.md) and [coverage](docs/research/coverage.md): 137
  sources across 12 countries, each with access, terms and text-mining restrictions
- Source registry: `data/sources/sources.yaml`; value framework: `data/framework/`

## Development

```
python -m venv .venv
pip install -e .[dev]
pytest -q
ruff check .
```

## Design

See the [project design spec](docs/superpowers/specs/2026-11-18-semantic-values-design.md).

Code is MIT-licensed (see `LICENSE`); derived data is CC BY 4.0 (see `LICENSE-DATA.md`).
