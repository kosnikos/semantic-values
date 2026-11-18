# semantic-values

Measuring how **societal values** (what ordinary people care about, not what governments
officially say) change **over time** and **between countries**, and how values **spread from
country to country**. Values are derived from large collections of everyday text
(newspapers, books, online posts), and findings are published as blog posts.

## v0 scope

Countries: France, Netherlands, Belgium, Luxembourg, Germany, Austria, Switzerland, Italy,
Greece, Spain, Portugal and the United Kingdom. Focus period: recent (first target 2005 to now).

## Data policy

Raw text is never committed. The repository holds only references (source, URL/ID, date,
country, language) and extracted values; raw text is cached locally and git-ignored.

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
