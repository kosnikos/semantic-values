# v0 Foundations & Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the public repo and complete design steps 1–3: repo setup, literature review + value-framework decision, and a machine-readable, per-country archive survey (Greece + UK first).

**Architecture:** A small Python package `semval` holds typed, validated registries (sources, values) loaded from YAML in `data/`. Research outputs are Markdown in `docs/research/`, backed by those registries so later pipeline stages (ingestion, tagging) consume them directly. Raw text never enters git.

**Tech Stack:** Python ≥3.11, pydantic v2, PyYAML, pytest, ruff. `gh` CLI for the GitHub repo.

**Spec:** `docs/superpowers/specs/2026-11-18-semantic-values-design.md`

## Global Constraints

- Region unit is **country**, by place of publication (ISO 3166-1 alpha-2, uppercase; UK = `GB`).
- v0 countries: FR, NL, BE, LU, DE, AT, CH, IT, GR, ES, PT, GB. Thin slice: **GR + GB**.
- Survey priority: 2005–now first, then 1940–2005. 1880–1940 is out of scope for this plan.
- Only free (non-paywalled) sources are usable; paywalled ones are still recorded, marked `paywall`.
- Prefer opinion pieces, letters to the editor, columns, forums over straight news; record genres per source.
- Online sources count only if attributable to one country (national domain, national forum/subreddit).
- Never commit raw text. `data/raw/` and `data/cache/` are git-ignored.
- Per source, record: free vs paywalled, years, languages, API/bulk, licence/ToS, TDM opt-out, whether sending text to commercial LLM/translation APIs is allowed (owner decides later how to act on this), whether per-text tags+URLs may be published.
- Every factual claim about a source or paper must come from a page actually visited, with URL; unverifiable items are marked `unknown`, never guessed.
- **Language: Python** (≥3.11) for everything unless a part genuinely needs something else.
- **Swappable components (owner requirement):** every basic component (source registry, value framework, and later ingestion, sampling, tagging, aggregation, models) sits behind a small typed interface (`typing.Protocol` or pydantic model) with config-driven selection, so an implementation or framework can be replaced without touching callers. No framework-specific or source-specific logic in shared code. Follow standard Python practice: type hints, `ruff` lint/format, pytest, small focused modules.
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A source whose coverage is ongoing (no end year) — expected to count as covering up to the current year. Test: `test_open_ended_source_counts_in_latest_period` (Task 2).
2. A source spanning only part of a period (e.g. 2010–2015 in 2005–now) — expected to count for that period. Test: `test_partial_overlap_counts` (Task 2).
3. Lowercase or legacy country codes (`gb`, `UK`) in YAML — expected: `gb` normalised to `GB`; `UK` rejected with a message pointing to `GB`. Test: `test_country_code_normalisation` (Task 2).
4. Duplicate source/value ids in a registry — expected: load fails naming the duplicate. Tests: `test_duplicate_ids_rejected` (Task 2), `test_duplicate_value_ids_rejected` (Task 6).
5. Paywalled sources inflating coverage — expected: coverage matrix counts only usable (`free`, `free_registration`) sources. Test: `test_paywalled_not_counted` (Task 2).

---

## File Structure

```
README.md                      project intent, status, how to run
LICENSE                        MIT (code)
LICENSE-DATA.md                CC BY 4.0 (docs/ and data/ except raw/cache)
.gitignore                     data/raw/, data/cache/, .env, venv, __pycache__
pyproject.toml                 package semval, deps, pytest config
src/semval/__init__.py
src/semval/sources.py          Source model, load_sources, coverage_matrix
src/semval/values.py           ValueDef model, load_values
src/semval/cli.py              `python -m semval coverage` -> docs/research/coverage.md
src/semval/__main__.py
data/sources/sources.yaml      the archive survey registry
data/framework/<framework_id>.yaml  one file per value framework (chosen one + any alternatives)
docs/research/literature-review.md
docs/research/framework-decision.md
docs/research/sources.md       narrative per country, links to registry
docs/research/coverage.md      generated
tests/test_sources.py
tests/test_values.py
tests/test_cli.py
```

---

### Task 1: Repo scaffold and public GitHub repo

**Files:**
- Create: `README.md`, `LICENSE`, `LICENSE-DATA.md`, `.gitignore`, `pyproject.toml`, `src/semval/__init__.py`, `tests/test_smoke.py`
- Already present: `docs/superpowers/specs/…`, `docs/superpowers/plans/…`

**Interfaces:**
- Produces: installable package `semval` (`pip install -e .[dev]`), `semval.__version__ = "0.0.1"`.

- [ ] **Step 1:** `git init -b main` in the repository root (`Semantic_Values/`).
- [ ] **Step 2: Write the failing test** `tests/test_smoke.py::test_version` asserting `semval.__version__ == "0.0.1"`.
- [ ] **Step 3:** Run `pytest -q` → FAIL (module not found).
- [ ] **Step 4:** Create `pyproject.toml` (setuptools, `src/` layout, deps `pydantic>=2`, `pyyaml>=6`; extra `dev = ["pytest>=8", "ruff>=0.6"]`, `[tool.ruff]` line-length 100), `src/semval/__init__.py`, `.gitignore` (must include `data/raw/`, `data/cache/`, `.env`, `.venv/`, `__pycache__/`), `LICENSE` (MIT, copyright holder name confirmed with the owner in Step 8 before pushing), `LICENSE-DATA.md` (CC BY 4.0), `README.md` (intent from spec §1, v0 countries, "raw text is never committed", link to spec).
- [ ] **Step 5:** `python -m venv .venv`, `pip install -e .[dev]`, `pytest -q` and `ruff check .` → PASS.
- [ ] **Step 6:** Verify ignore: create `data/raw/x.txt`, `git status --porcelain` must not list it; delete it.
- [ ] **Step 7: Commit** all files: `chore: scaffold repo, licences, spec and plan`.
- [ ] **Step 8: Confirm with the owner** the LICENSE copyright-holder name (repo name `semantic-values` already approved). Then `gh repo create semantic-values --public --source . --push`. Expected: URL printed, `git remote -v` shows origin.

### Task 2: Source registry model and coverage matrix

**Files:**
- Create: `src/semval/sources.py`, `tests/test_sources.py`, `data/sources/sources.yaml` (empty list `[]`)

**Interfaces:**
- Produces:
  - `class Source(BaseModel)` with fields: `id: str` (slug), `name: str`, `country: str` (ISO alpha-2), `source_type: Literal["newspaper_archive","national_library","web_archive","news_api","forum","book_archive","other"]`, `url: HttpUrl`, `access: Literal["free","free_registration","partial_paywall","paywall"]`, `year_start: int`, `year_end: int | None` (None = ongoing), `languages: list[str]` (ISO 639-1), `genres: list[Literal["opinion","letters","columns","news","forum","books","other"]]`, `access_method: Literal["api","bulk","scrape","manual"]`, `licence: str`, `tdm_opt_out: Literal["yes","no","unknown"]`, `llm_api_allowed: Literal["yes","no","unknown"]`, `per_text_publish_allowed: Literal["yes","no","unknown"]`, `text_quality: Literal["born_digital","ocr_good","ocr_poor","unknown"]`, `volume_estimate: str`, `verified_on: date`, `evidence_urls: list[HttpUrl]` (min 1), `notes: str = ""`.
  - `USABLE_ACCESS = {"free", "free_registration"}`
  - `PERIODS: list[tuple[str, int, int | None]] = [("1940-1969",1940,1969), ("1970-1989",1970,1989), ("1990-2004",1990,2004), ("2005-now",2005,None)]`
  - `V0_COUNTRIES = ["FR","NL","BE","LU","DE","AT","CH","IT","GR","ES","PT","GB"]`
  - `load_sources(path: Path) -> list[Source]` — raises `ValueError` on duplicate ids.
  - `coverage_matrix(sources: list[Source], countries: list[str], current_year: int) -> dict[str, dict[str, list[str]]]` — country → period label → ids of usable sources overlapping that period.

- [ ] **Step 1: Write failing tests** in `tests/test_sources.py` (build sources via a `make_source(**overrides)` helper with valid defaults):
  - `test_valid_source_loads` — YAML with one valid entry → 1 `Source`, `country == "GR"`.
  - `test_country_code_normalisation` — `"gb"` → `"GB"`; `"UK"` → `ValidationError` whose message contains `"GB"`; `"XX"` → `ValidationError`.
  - `test_year_order` — `year_start=2010, year_end=2005` → `ValidationError`.
  - `test_unknown_enum_rejected` — `access="maybe"` → `ValidationError`.
  - `test_duplicate_ids_rejected` — two entries `id: guardian` → `ValueError` mentioning `"guardian"`.
  - `test_partial_overlap_counts` — free source 2010–2015 in GB → `matrix["GB"]["2005-now"] == [id]`, `matrix["GB"]["1990-2004"] == []`.
  - `test_open_ended_source_counts_in_latest_period` — free source 1999–None → appears in `1990-2004` and `2005-now`.
  - `test_paywalled_not_counted` — `access="paywall"` source → absent from every period.
  - `test_all_countries_present` — empty sources → every country in `V0_COUNTRIES` has all four period keys with `[]`.
- [ ] **Step 2:** `pytest tests/test_sources.py -q` → FAIL (import error).
- [ ] **Step 3:** Implement per Interfaces. Country validation: accept any case, uppercase it, reject `UK` with "use GB", validate against a hard-coded set of ISO alpha-2 codes for Europe plus `US` (no new dependency).
- [ ] **Step 4:** `pytest -q` → all PASS.
- [ ] **Step 5: Commit** `feat: source registry model and coverage matrix`.

### Task 3: Coverage report CLI

**Files:**
- Create: `src/semval/cli.py`, `src/semval/__main__.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `load_sources`, `coverage_matrix`, `PERIODS`, `V0_COUNTRIES` (Task 2).
- Produces: `render_coverage_md(matrix: dict, sources: list[Source]) -> str`; CLI `python -m semval coverage [--sources data/sources/sources.yaml] [--out docs/research/coverage.md]`.

- [ ] **Step 1: Write failing tests:**
  - `test_render_has_table` — output contains header row `| Country | 1940-1969 | 1970-1989 | 1990-2004 | 2005-now |` and one row per country in `V0_COUNTRIES`, cells show the count of usable sources (`0` when empty).
  - `test_render_lists_open_questions` — a source with `llm_api_allowed="unknown"` appears under a `## Open questions` heading with its id.
  - `test_cli_writes_file` — run `main(["coverage","--sources",tmp_yaml,"--out",tmp_md])`; file exists and starts with `# Source coverage` and a line `Generated from data/sources/sources.yaml`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement with `argparse`; `current_year` from `date.today().year`.
- [ ] **Step 4:** `pytest -q` → PASS; `python -m semval coverage` on the empty registry writes a 12-row all-zero table.
- [ ] **Step 5: Commit** `feat: coverage report CLI`.

### Task 4: Archive survey — Greece and United Kingdom (thin slice)

Research task. Visit every source; record only what the pages show.

**Files:**
- Modify: `data/sources/sources.yaml`
- Create: `docs/research/sources.md` (sections `## GR`, `## GB`)
- Regenerate: `docs/research/coverage.md`

**Interfaces:**
- Consumes: `Source` schema (Task 2), CLI (Task 3).

- [ ] **Step 1:** Survey **GB** for 2005–now first, then 1940–2005. Must check at minimum: Guardian Open Platform API (full text, terms on LLM/storage use), BBC News, The Independent, national subreddits (r/unitedkingdom, r/AskUK — Reddit data terms), Mumsnet / other UK forums, UK Web Archive, Common Crawl News (`.uk` filter), GDELT (as URL index), British Newspaper Archive (record as paywall), any free letters-to-the-editor collections.
- [ ] **Step 2:** Survey **GR** likewise. Must check at minimum: National Library of Greece digital newspaper archive, Kathimerini / To Vima / Ta Nea / Efimerida ton Syntakton online archives, Rizospastis archive, Greek web archive (if any) and Internet Archive coverage of `.gr`, Common Crawl News (`.gr`), Greek forums (e.g. insomnia.gr), r/greece.
- [ ] **Step 3:** For each source add a registry entry with all fields; any field not established from a visited page is `unknown`; `evidence_urls` lists the pages used.
- [ ] **Step 4:** In `docs/research/sources.md`, per country: a short narrative (best 2005–now option for opinion/letters genres, best 1940–2005 option, gaps), and a "Recommended thin-slice sources" list.
- [ ] **Step 5:** `python -m semval coverage` → succeeds; `pytest -q` → PASS. Check: GB and GR each have ≥1 usable source in `2005-now`, or `sources.md` states explicitly that none was found and why.
- [ ] **Step 6: Commit** `research: archive survey for GR and GB`.

### Task 5: Archive survey — remaining v0 countries

Same method and checks as Task 4, for FR, NL, BE, LU, DE, AT, CH, IT, ES, PT. Can run in parallel with Tasks 4, 6.

**Files:** same as Task 4 (new `## <CC>` sections).

- [ ] **Step 1:** Per country, check at minimum: national library newspaper portal (Gallica/Retronews, Delpher, KBR BelgicaPress, eluxemburgensia, Deutsches Zeitungsportal, ANNO, e-newspaperarchives.ch, Emeroteca/La Stampa archive, Hemeroteca Digital BNE, Arquivo.pt), free archives of major national newspapers (e.g. Der Spiegel, Die Zeit, El País, Le Monde — record paywall if so), national web archive, Common Crawl News by ccTLD, national forums/subreddits.
- [ ] **Step 2:** Registry entries + `sources.md` sections as in Task 4 Steps 3–4.
- [ ] **Step 3:** `python -m semval coverage` and `pytest -q` → PASS.
- [ ] **Step 4: Commit** `research: archive survey for remaining v0 countries`.

### Task 5d: Restriction scope field

**Files:**
- Modify: `src/semval/sources.py`, `tests/test_sources.py`, `src/semval/cli.py`, `tests/test_cli.py`, `data/sources/sources.yaml`
- Regenerate: `docs/research/coverage.md`

**Interfaces:**
- Produces: `Source.restriction_scope: Literal["none","ai_training_only","crawler_block_only","tdm_all","all_reuse","unknown"]` (required). Meaning: `tdm_all` = terms or a valid Art. 4(3) reservation forbid any automated analysis (covers dictionary methods too); `all_reuse` = any copying/reproduction forbidden without licence; `ai_training_only` = only AI training/development is forbidden; `crawler_block_only` = no clause in terms, only robots.txt blocks of AI crawlers; `none` = terms explicitly allow or impose nothing relevant.
- Produces: `OPEN_SCOPES = {"none","ai_training_only","crawler_block_only","unknown"}`; `JURISDICTION_OPEN_SCOPES: dict[str, set[str]] = {"GB": {"tdm_all"}}` (UK CDPA s.29A: contract bans on non-commercial research TDM are unenforceable; `all_reuse` stays closed). `is_open(source) -> bool` = scope in `OPEN_SCOPES | JURISDICTION_OPEN_SCOPES.get(country, set())`. `coverage_matrix(..., open_only: bool = False)` — when True, also excludes sources where `is_open` is False. CLI renders two tables: "Usable (free access)" and "Usable and not opted out".
- Amended during execution: `copyright_boilerplate` was added to the scopes and to `OPEN_SCOPES`; GB = `{"tdm_all", "all_reuse"}` per spec §3; jurisdiction overrides do not apply to the `api` access route (`OVERRIDE_EXCLUDED_ACCESS_METHODS`); `magazine` was added to `source_type`.

- [ ] **Step 1: Failing tests:** `test_restriction_scope_required`, `test_open_only_excludes_tdm_all` (free FR source with `tdm_all` absent from `open_only=True` matrix, present in default), `test_gb_tdm_all_open_under_s29a` (free GB `tdm_all` source present with `open_only=True`; GB `all_reuse` absent), `test_render_has_two_tables`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Back-fill `restriction_scope` for every existing entry from its `notes` (no new web research; if the notes don't establish it → `unknown`). A licence requirement for any use beyond strictly personal/individual use (e.g. Le Figaro) is `all_reuse`. `pytest -q`, `ruff check .`, `python -m semval coverage` → PASS.
- [ ] **Step 5: Commit** `feat: restriction scope and open-only coverage`.

### Task 5e: Wider newspaper/magazine sweep for restriction-heavy countries

Research task, same method and evidence rules as Task 4. Countries: GB, FR, BE, NL, plus any of DE/AT/CH where batch 5b found most major titles opted out.

- [ ] **Step 1:** Per country, list general-interest national and major regional newspapers and news/opinion/culture magazines (weekly and monthly), and popular general-audience magazines (family, women's, men's, TV-guide, people, general-interest; record circulation where a cited page gives it); exclude pure sport, pure fashion/beauty, trade. Magazines use `source_type: magazine` (added in batch 5e-i). Cite the list's source (e.g. press-council, circulation-audit or Wikipedia list page).
- [ ] **Step 2:** For each title, check: online archive depth, access, ToS/robots.txt text on TDM/AI, `restriction_scope`, and whether a research/academic licence route exists. Add registry entries only for titles with `access` usable or a research-licence route; list the rest in a per-country table in `sources.md` (title, scope, one-line reason).
- [ ] **Step 3:** In `sources.md`, per country: "open titles" shortlist ranked by fit (opinion/letters/editorials, archive depth).
- [ ] **Step 4:** `python -m semval coverage`, `pytest -q` → PASS. **Commit** `research: wider newspaper sweep for restriction-heavy countries`.

### Task 6: Literature review

Research task; can run in parallel with Tasks 4–5.

**Files:**
- Create: `docs/research/literature-review.md`

- [ ] **Step 1:** Write sections, each with verified citations (author, year, title, URL/DOI):
  1. Value frameworks: Schwartz (1992; refined 19-value theory 2012), Moral Foundations Theory (Haidt & Graham; MFD, MFD 2.0, eMFD), Inglehart–Welzel cultural map, Hofstede, Rokeach Value Survey.
  2. Value detection in text: Touché ValueEval 2022–23 (Kiesel et al.) and successors, LLM-based value/stance detection (2023–2026).
  3. Values over time from text: culturomics (Michel et al. 2011), Greenfield 2013, Kesebir & Kesebir 2012, historical psychology (Atari & Henrich 2023), moral-foundation trends in news.
  4. Cross-country diffusion of values/attitudes: diffusion and contagion models, Hawkes / Granger applications to cultural or opinion spread.
  5. Survey ground truth: EVS/WVS waves, country coverage for the 12 v0 countries, item availability.
  6. Gaps this project fills (country-level, multilingual, stance-based, diffusion).
- [ ] **Step 2:** Check: every citation has a URL or DOI that was opened; no section is empty.
- [ ] **Step 3: Commit** `research: literature review`.

### Task 7: Framework comparison, decision memo, and value registry

Depends on Task 6.

**Files:**
- Create: `docs/research/framework-decision.md`, `src/semval/values.py`, `tests/test_values.py`, `data/framework/<framework_id>.yaml` (e.g. `schwartz19.yaml`)

**Interfaces:**
- Produces: `class ValueDef(BaseModel)`: `id: str` (slug), `name: str`, `definition: str` (≥1 sentence), `framework: str`, `parent: str | None` (higher-order group id, e.g. Schwartz "openness_to_change"), `opposes: list[str]` (value ids), `survey_items: list[str]` (EVS/WVS item codes, may be empty), `examples_endorse: list[str]`, `examples_reject: list[str]`; `class Framework(BaseModel)`: `id: str`, `name: str`, `citation: str`, `values: list[ValueDef]`; `load_framework(path: Path) -> Framework` — raises `ValueError` on duplicate ids or on an `opposes`/`parent` reference to an unknown id.

- [ ] **Step 1:** In `framework-decision.md`, compare Schwartz (10 and 19), MFT, Inglehart–Welzel, Hofstede, Rokeach in a table on these criteria: detectable in short texts; supports multiple values per text; supports endorse/reject stance; readable to blog readers; EVS/WVS item mapping exists; works across the v0 languages; existing labelled data (e.g. ValueEval). End with a recommendation and its reasons, and how overlap is handled (multi-label, with opposing pairs recorded).
- [ ] **Step 2: Write failing tests** `tests/test_values.py`:
  - `test_values_yaml_loads` — every `data/framework/*.yaml` loads via `load_framework`, ≥10 values, every value has a non-empty `definition`.
  - `test_duplicate_value_ids_rejected`.
  - `test_unknown_reference_rejected` — `opposes: ["nope"]` → `ValueError` naming `nope`.
  - `test_two_frameworks_coexist` — two tmp framework files with different ids both load independently.
- [ ] **Step 3:** Run → FAIL. Implement `values.py`; write `data/framework/<framework_id>.yaml` for the recommended framework; nothing in `values.py` may reference a specific framework.
- [ ] **Step 4:** `pytest -q` → PASS.
- [ ] **Step 5: Commit** `research: framework decision and value registry`.

### Task 8: Owner decision checkpoint

- [ ] **Step 1:** Write a summary for the owner: (a) the recommended framework and why; (a2) legal routes worth checking: EU DSM Art. 3 (research organisations) and UK CDPA s.29A (non-commercial research; contract override void) — flagged as leads, not legal advice; (b) GR/GB thin-slice sources and their coverage; (c) how many usable sources have `llm_api_allowed` = `no`/`unknown` (spec §3 open item); (d) proposed next plan (step 4 of the design: tagging-method comparison under the $300 cap).
- [ ] **Step 2:** The owner approves or amends the framework and the API decision. Record the outcome in `framework-decision.md` (`## Decision`) and the spec's §3 table. Commit `docs: record owner decisions`.
