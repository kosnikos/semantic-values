# Tagging Method Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a swappable value-tagging pipeline (sampler → tagger → review page → evaluation), and use it to choose the tagging method for v0 on Greek and UK opinion texts.

**Architecture:** The framework file defines named levels and roll-ups (`leaf19`, `basic10`, `group4`, …), and a `TargetSet` built from one level is all a tagger sees. `Segment`s are generic text units with parents, so tags merge upward. A `Tagger` protocol has Claude and lexicon implementations, and every run writes a manifest and a cost ledger entry. A stdlib-only local review server reads run files and writes the owner's verdicts as offsets-only JSONL. An evaluation module scores runs against Touché23-ValueEval and the owner labels.

**Tech Stack:** Python ≥3.11, pydantic v2, PyYAML, `anthropic` (Python SDK), `httpx` only if the SDK already pulls it, stdlib `http.server` + plain JS for review, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-11-19-tagging-method-design.md` (its `leaf19` level is the framework's `leaf` level here; parent: `docs/superpowers/specs/2026-11-18-semantic-values-design.md`)

## Global Constraints

- **Reused string values are `StrEnum` or `Literal`.** This covers stances, verdicts, unit levels, model ids, effort levels, run status, access values and basis values. No bare repeated strings (owner requirement).
- **Shared code has no framework-, source- or model-specific logic.** Value ids come from framework files. Source parsing lives in per-source adapter modules. Model ids and prices live in one config module.
- **Raw article text is never committed.** Cache it under `data/raw/` (git-ignored). Committed references and labels hold ids, URLs and character offsets only.
- **Touché23-ValueEval** (CC BY 4.0): download the raw files directly into `data/external/touche23/` (git-ignored). Never run its loading script (`trust_remote_code`). Few-shot examples may be committed with attribution.
- **Crawling:** obey robots.txt for our own user-agent (`semval-research/0.1 (+https://github.com/kosnikos/semantic-values)`) and `Crawl-delay`, default 5 s between requests per host. Skip pages whose JSON-LD has `"isAccessibleForFree": false`. Never get around bot challenges.
- **API:** use the Anthropic Python SDK. Read the `claude-api` skill before writing API code.
  - Model ids are exactly `claude-haiku-5-5`, `claude-sonnet-5-5` and `claude-opus-5-5`.
  - Effort goes in `output_config.effort`. Do not send `thinking` or sampling parameters.
  - Use structured outputs, and prompt caching on the system prompt.
  - Use Message Batches for bulk runs. Use server-side refusal fallbacks on non-batch calls.
- **Budget:** a hard cap of **$50** for this plan's API spend, in config (`semval.config.BUDGET_USD`). The ledger refuses calls that would exceed it.
- **Prices (USD per 1M tokens, input/output):** Haiku 5.5 0.10/0.50, Sonnet 5.5 2/10, Opus 5.5 4/20. Cache reads cost the model's cache-read price; batch is ×0.5. Keep these in one table.
- **Licence of definitions:** verbatim official definitions go in the public repo only if their source's licence allows it. Otherwise they go in `data/framework/local/` (git-ignored), and the repo keeps the citation and page.
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Owner stop points (do not proceed past them without the owner):** Task 9 (checkpoint review), Task 11 Step 2 (few-shot confirmation), Task 13 Step 3 (blind pass), Task 13 Step 5 (method decision).

## Review Focus

1. **An article in which the model finds no values** is a valid result (an empty tag list). It is not an error and is not retried. Test: `test_empty_tag_list_is_valid` (Task 7).
2. **A model quote that doesn't occur in the text.** The model returns quote strings and code finds their offsets. If a quote isn't found, the tag is kept, flagged `evidence_unresolved`, and its evidence is dropped. Test: `test_unresolved_quote_keeps_tag_flagged` (Task 7).
3. **The budget runs out mid-run.** The run stops before the call that would exceed the cap, records `status=stopped_budget`, and resumes later without re-tagging finished segments. Tests: `test_ledger_refuses_over_cap`, `test_run_resumes_without_retagging` (Task 7).
4. **Paywalled or robots-disallowed pages** are skipped and logged, never cached. Test: `test_skips_not_free_and_disallowed` (Task 5).
5. **Rapid clicks, re-clicks or a page reload in the review page.** Saving is idempotent, and the last verdict per (labeller, document, value) wins. Test: `test_verdict_upsert_last_write_wins` (Task 8).

---

## File Structure

```
src/semval/
  config.py            ModelId, Effort enums; PRICES; BUDGET_USD; paths
  sources.py           (modify) access 'restricted', year bases, slug/ISO-639 checks
  values.py            (modify) LevelDef, TargetDef, OfficialDefinition, Framework.levels,
                       target_set(), rollup_map(); duplicate-opposes check
  targets.py           TargetSet model (what a tagger sees)
  units.py             UnitLevel, Document, Segment, segmenters (article/paragraph/sentence)
  tags.py              Stance, ValueTag, EvidenceSpan, merge(), rollup_tags()
  sampling/
    fetch.py           PoliteFetcher (robots, crawl-delay, UA, cache, free-check)
    adapters/base.py   SourceAdapter protocol; registry by source id
    adapters/<id>.py   one module per source (GR x3, GB x3)
    sample.py          collect_sample(); CLI hook
  tagging/
    base.py            Tagger protocol, TaggerSpec, RunManifest, RunStatus
    ledger.py          CostLedger
    prompt.py          prompt + output-schema builder from TargetSet (+ few-shot)
    claude.py          ClaudeTagger (sync + batch)
    lexicon.py         LexiconTagger
    runner.py          run_tagging(): manifests, resume, quote->offset resolution
  datasets/touche23.py loader, objectivity mapping, Greek proxy builder, few-shot pool
  review/
    labels.py          Verdict enum, LabelRecord, upsert store, pooling (blind)
    server.py          stdlib HTTP server + JSON API
    static/index.html, static/review.js, static/review.css
  evaluation/
    metrics.py         presence P/R/F1 (macro, per value), stance agreement, EN-EL gap
    report.py          tagging-evaluation.md writer
  cli.py               (modify) subcommands: sample, tag, review, evaluate, touche23
data/framework/schwartz19.yaml   (modify) levels + official definition refs
data/framework/local/            (git-ignored) verbatim definitions if licence requires
data/samples/<run>.yaml          committed sample references (no text)
data/runs/<run_id>/              manifest.json + tags.jsonl (offsets only)
data/labels/<labeller>/*.jsonl   owner verdicts (offsets only)
data/fewshot/touche23.yaml       committed few-shot examples (CC BY, attributed)
docs/backlog.md
docs/research/tagging-evaluation.md
```

---

### Task 1: Source schema housekeeping + backlog document

**Files:**
- Modify: `src/semval/sources.py`, `tests/test_sources.py`, `tests/conftest.py`, `data/sources/sources.yaml`, `src/semval/cli.py` (only if it lists access values)
- Create: `docs/backlog.md`
- Regenerate: `docs/research/coverage.md` (`--year 2026`)

**Interfaces:**
- Produces:
  - `AccessLevel = Literal["free","free_registration","partial_paywall","paywall","restricted"]`, with `USABLE_ACCESS` unchanged ("restricted" is not usable).
  - `YearBasis = Literal["verified","window","observed","unknown"]`, and the fields `Source.year_start_basis: YearBasis` and `Source.year_end_basis: YearBasis` (required).
  - Slug check on `Source.id` (`^[a-z][a-z0-9-]*$`).
  - `ISO_639_1: frozenset[str]`, with `Source.languages` validated against it.

- [ ] **Step 1: Write failing tests:**
  - `test_restricted_access_not_usable`
  - `test_year_basis_required`
  - `test_source_id_slug_enforced` (`"Bad ID"` → error)
  - `test_language_must_be_iso639_1` (`"gre"` → error, `"el"` ok)
  - `test_restricted_counts_in_neither_table`

  Update `make_source` defaults to include both basis fields as `"verified"`.
- [ ] **Step 2:** `pytest -q` → FAIL.
- [ ] **Step 3:** Implement. Then back-fill `sources.yaml` from each row's existing notes, with no new research:
  - reading-room or on-site-only rows (UKWA, BnF/LU/KB/DNB web archives, Delpher ×2, BNE) → `restricted`;
  - `year_start_basis`: `window` when the notes say "our window", `observed` when they say "oldest page seen" / "earliest seen", `verified` when a page states the start, otherwise `unknown`;
  - `year_end_basis`: `verified` for documented ends, `observed` for `null` ongoing, `unknown` where the notes say unverified.
- [ ] **Step 4:** Create `docs/backlog.md` with sections Methods / Sources / Data schema / Legal / Analysis / Extensions, seeded with every item in spec §6.2. Each item is one line: what, why deferred, link.
- [ ] **Step 5:** `pytest -q`, `ruff check .`, `ruff format --check .`, `python -m semval coverage --year 2026` → PASS, and the freshness test passes after regeneration.
- [ ] **Step 6: Commit** `feat: restricted access, year bases, id/language checks; backlog`.

### Task 2: Framework levels, roll-ups and target sets

**Files:**
- Modify: `src/semval/values.py`, `data/framework/schwartz19.yaml`, `tests/test_values.py`
- Create: `src/semval/targets.py`, `tests/test_targets.py`

**Interfaces:**
- Produces:
  - `OfficialDefinition(BaseModel)`: `citation: str`, `page: str`, `text: str | None` (None when the text lives in the local file), `local_only: bool`.
  - `TargetDef(BaseModel)`: `id`, `name`, `definition` (our plain-English), `official: OfficialDefinition | None`, `examples_endorse: list[str]`, `examples_reject: list[str]`.
  - `LevelDef(BaseModel)`: `id: str` (slug), `targets_from: str | None` (reuse another level's targets), `targets: list[TargetDef]`, `map: dict[str, str]` (leaf id → target id).
  - The special level id `LEAF_LEVEL = "leaf"` means the framework's leaves (no map).
  - `Framework.levels: list[LevelDef]` (default `[]`).
  - `Framework.level_ids() -> list[str]`, `Framework.target_set(level_id: str) -> TargetSet`, `Framework.rollup_map(level_id: str) -> dict[str, str]` (leaf → target).
  - In `targets.py`: `TargetSet(BaseModel)`: `framework_id`, `level_id`, `targets: list[TargetDef]`, `def ids(self) -> list[str]`.
  - `load_framework(path, local_dir: Path | None = FRAMEWORK_DIR / "local")` merges verbatim official texts from `local_dir/<framework_id>.official.yaml` when that file exists.

- [ ] **Step 1: Write failing tests:**
  - `test_level_map_covers_every_leaf_exactly_once`
  - `test_level_map_targets_exist`
  - `test_targets_from_reuses_targets`
  - `test_target_set_leaf_equals_leaves`
  - `test_validation_rollup_humility_to_tradition` (in the real file: `basic10_validation` maps `humility → tradition`, and `basic10` maps `humility → conformity`)
  - `test_duplicate_opposes_rejected`
  - `test_childless_group_is_leaf_documented` (asserts current behaviour, and the docstring states it)
  - `test_schwartz19_shape` (19 leaves, 4 groups, levels `leaf`, `basic10`, `basic10_validation`, `group4` present)
  - `test_local_official_text_merged` (tmp local file)
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement. Add `levels` to `schwartz19.yaml`:
  - `basic10`: the 10 basic values as targets, each with our own plain-English definition. The official definitions are filled in Task 3.
  - `basic10_validation`: `targets_from: basic10`, with the humility→tradition map.
  - `group4`: targets are the 4 groups, mapped through `parent`.
  - The leaf→basic map follows the value ids (e.g. `power_dominance → power`), face → security, and humility → conformity in `basic10`.

  Validation: every map key must be a leaf, and every map value a target of that level.
- [ ] **Step 4:** Run the suite + ruff → PASS. Update `framework-decision.md` §4/§5 to say the 19→10 roll-up is now encoded in `levels`.
- [ ] **Step 5: Commit** `feat: framework levels, roll-ups and target sets`.

### Task 3: Official definitions (research + data)

**Files:**
- Modify: `data/framework/schwartz19.yaml`, `docs/research/framework-decision.md` (new §"Official definitions")
- Create (only if needed): `data/framework/local/schwartz19.official.yaml` (git-ignored), and add `data/framework/local/` to `.gitignore`

- [ ] **Step 1:** Open and record the licence or copyright terms of:
  - Schwartz et al. 2012, JPSP 103(4), the definitions table for the 19 values;
  - Schwartz 2012, *An Overview of the Schwartz Theory of Basic Values*, Online Readings in Psychology and Culture 2(1), doi:10.9707/2307-0919.1116, for the 10 values;
  - Kiesel et al. 2022, ACL, value descriptions.

  Every claim needs a URL that was opened.
- [ ] **Step 2:** For each leaf and each `basic10` target, fill in `official` with citation and page. Where the licence permits public verbatim text, put `text` inline. Otherwise set `local_only: true` and write the text to the local file.
- [ ] **Step 3:** `pytest -q` → PASS, including `test_schwartz19_shape`. Add `test_every_target_has_official_citation`.
- [ ] **Step 4: Commit** `research: official Schwartz definitions with sources`.

### Task 4: Units, tags and merge

**Files:**
- Create: `src/semval/units.py`, `src/semval/tags.py`, `tests/test_units.py`, `tests/test_tags.py`

**Interfaces:**
- Produces:
  - `UnitLevel(StrEnum)`: `ARTICLE="article"`, `PARAGRAPH="paragraph"`, `SENTENCE="sentence"`, with `.rank` (0, 1, 2).
  - `Document(BaseModel)`: `id`, `source_id`, `country`, `language`, `date: date | None`, `genre`, `url: str | None`, `title: str | None`, `text_sha256: str`.
  - `Segment(BaseModel)`: `id`, `document_id`, `level: UnitLevel`, `parent_id: str | None`, `start: int`, `end: int` (char offsets in the document text).
  - `segment(doc_id: str, text: str, level: UnitLevel) -> list[Segment]`. Paragraphs split on blank lines. Sentences are a simple regex split per paragraph; finer levels' parents point to the level above.
  - `Stance(StrEnum)`: `ENDORSE`, `REJECT`, `MENTION`, `CONTESTED` (CONTESTED only from merge).
  - `EvidenceSpan(BaseModel)`: `start`, `end`.
  - `ValueTag(BaseModel)`: `segment_id`, `value_id`, `stance: Stance`, `evidence: list[EvidenceSpan]`, `evidence_unresolved: bool = False`, `confidence: float | None`, `run_id`.
  - `merge(tags, segments, to_level: UnitLevel) -> list[ValueTag]` uses the spec §5.2 rule.
  - `rollup_tags(tags, rollup_map: dict[str,str]) -> list[ValueTag]` combines tags that map to the same target, with the same combination rule as merge.

- [ ] **Step 1: Write failing tests:**
  - segment offsets reconstruct the text;
  - parent links are correct;
  - merge branches: endorse+reject→contested, endorse+mention→endorse, reject only→reject, mention only→mention;
  - evidence spans are unioned;
  - roll-up of `self_direction_thought`=endorse with `self_direction_action`=reject gives `self_direction`=contested;
  - merging to a finer level raises `ValueError`.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS + ruff.
- [ ] **Step 5: Commit** `feat: generic text units, value tags, merge and roll-up`.

### Task 5: Polite fetcher and sampler

**Files:**
- Create: `src/semval/sampling/fetch.py`, `src/semval/sampling/adapters/base.py`, adapter modules, `src/semval/sampling/sample.py`, `tests/test_fetch.py`, `tests/test_sample.py`, and `tests/fixtures/sampling/*.html` (**synthetic** HTML written for tests, never real articles)
- Modify: `src/semval/cli.py` (`sample` subcommand), `.gitignore` (`data/raw/`, already ignored; verify)

**Interfaces:**
- Produces:
  - `FetchOutcome(StrEnum)`: `OK`, `NOT_FREE`, `ROBOTS_DISALLOWED`, `HTTP_ERROR`, `CHALLENGE`.
  - `PoliteFetcher(user_agent, min_delay_s=5.0, cache_dir=Path("data/raw/http"))` with `.get(url) -> FetchResult(outcome, status, html | None)`. It honours robots.txt and Crawl-delay per host. A `NOT_FREE` result comes from JSON-LD `isAccessibleForFree` false. `CHALLENGE` means the response looks like a bot challenge (status 403/429/503 with challenge markers); it is logged and never retried.
  - `SourceAdapter` protocol: `source_id: str`, `list_candidates(fetcher, since: date, until: date) -> Iterable[str]` (URLs), `parse(url, html) -> ParsedArticle(title, date, genre, text)`.
  - `ADAPTERS: dict[str, SourceAdapter]`.
  - `collect_sample(source_ids, per_country: int, since, until) -> SampleManifest`. This writes texts to `data/raw/docs/<doc_id>.txt` and committed references to `data/samples/<name>.yaml` (Document fields only). It rejects any source where `is_open()` is False or access is not usable.

- [ ] **Step 1: Write failing tests** with a fake transport (no network):
  - `test_skips_not_free_and_disallowed`
  - `test_respects_crawl_delay` (fake clock)
  - `test_challenge_not_retried`
  - `test_cache_hit_no_second_request`
  - `test_collect_rejects_closed_source`
  - `test_sample_yaml_has_no_text`
  - one parse test per adapter, against its synthetic fixture
- [ ] **Step 2:** FAIL → **Step 3:** implement the fetcher and the six adapters. Choose from `gr-tovima-website`, `gr-tanea-website`, `gr-efsyn-website`, `gb-guardian-website`, `gb-evening-standard`, `gb-opendemocracy`. If one parses badly, swap in another open GR/GB source and note it. → **Step 4:** PASS + ruff.
- [ ] **Step 5: Live collection.** Run `python -m semval sample --countries GR GB --per-country 40 --since 2024-01-01 --until 2026-11-19 --name thin-slice-v0`. Report the counts per source and outcome. Commit `data/samples/thin-slice-v0.yaml` only.
- [ ] **Step 6: Commit** `feat: polite fetcher, source adapters and thin-slice sample`.

### Task 6: Tagger interface, cost ledger and lexicon baseline

**Files:**
- Create: `src/semval/config.py`, `src/semval/tagging/base.py`, `src/semval/tagging/ledger.py`, `src/semval/tagging/lexicon.py`, `tests/test_ledger.py`, `tests/test_lexicon.py`
- Add dependency: `anthropic` in `pyproject.toml`

**Interfaces:**
- Produces:
  - `ModelId(StrEnum)`: `HAIKU_5_5="claude-haiku-5-5"`, `SONNET_5_5="claude-sonnet-5-5"`, `OPUS_5_5="claude-opus-5-5"`.
  - `Effort(StrEnum)`: `LOW`, `MEDIUM`, `HIGH`.
  - `PRICES: dict[ModelId, Price]`, where `Price` has `input`, `output` and `cache_read` (USD/M). `BUDGET_USD = 50.0`.
  - `TaggerKind(StrEnum)`: `CLAUDE`, `LEXICON`.
  - `TaggerSpec(BaseModel)`: `kind`, `model: ModelId | None`, `effort: Effort | None`, `framework_id`, `level_id`, `unit: UnitLevel`, `few_shot: bool`, `batch: bool`.
  - `Tagger` protocol: `spec: TaggerSpec`, `tag(segments: list[Segment], texts: dict[str,str], targets: TargetSet) -> TagBatchResult(tags_by_segment: dict[str, list[RawTag]], usage: Usage)`. `RawTag` = value_id, stance, quotes: list[str], confidence.
  - `RunStatus(StrEnum)`: `RUNNING`, `DONE`, `STOPPED_BUDGET`, `FAILED`.
  - `RunManifest(BaseModel)`: `run_id`, `spec`, `input_sample`, `prompt_sha256`, `status`, `segments_done: list[str]`, `usage_totals`, `cost_usd`, `started`, `finished`.
  - `CostLedger(path=Path("data/runs/ledger.jsonl"), cap=BUDGET_USD)` with:
    - `.estimate(model, in_tokens, out_tokens, batch) -> float`
    - `.can_spend(usd) -> bool`
    - `.record(run_id, usage, model, batch) -> float`
    - `.total() -> float`
  - `LexiconTagger`: English only; emits `MENTION`; its word list comes from a data file `data/lexicon/<name>.yaml` keyed by target id at its level.

- [ ] **Step 1: Write failing tests:**
  - `test_ledger_refuses_over_cap`
  - `test_ledger_batch_halves_cost`
  - `test_ledger_persists_across_instances`
  - `test_lexicon_emits_mention_only`
  - `test_lexicon_ignores_non_english`
  - `test_prices_cover_all_models`
- [ ] **Step 2:** FAIL → **Step 3:** implement. For the lexicon, use a licensed English values word list, e.g. Ponizovskiy et al. 2020 Personal Values Dictionary, if its licence allows. Record the licence in the yaml header. If it doesn't, write a small seed list per `basic10` target and say so. → **Step 4:** PASS + ruff.
- [ ] **Step 5: Commit** `feat: tagger protocol, cost ledger, lexicon baseline`.

### Task 7: Claude tagger and run orchestration

**Files:**
- Create: `src/semval/tagging/prompt.py`, `src/semval/tagging/claude.py`, `src/semval/tagging/runner.py`, `tests/test_prompt.py`, `tests/test_claude_tagger.py`, `tests/test_runner.py`
- Modify: `src/semval/cli.py` (`tag` subcommand)

**Interfaces:**
- Consumes: `TargetSet` (Task 2), units/tags (Task 4), the Task 6 interfaces.
- Produces:
  - `build_prompt(targets: TargetSet, few_shot: list[FewShotExample]) -> PromptParts(system: str, schema: dict)`. The system prompt lists each target's id, name, official definition (falling back to ours), and endorse/reject examples. It defines endorse / reject / mention, and asks for verbatim quotes. The schema constrains `value_id` to `targets.ids()` and `stance` to {endorse, reject, mention}, and allows an empty list.
  - `FewShotExample(BaseModel)`: `id`, `text`, `language`, `tags: list[RawTag]`, `source: str` (attribution).
  - `ClaudeTagger(spec, client)` is the sync path. It uses `client.beta.messages.create` or `.parse` per the claude-api skill, with:
    - structured output `output_config.format`;
    - `output_config.effort`;
    - `cache_control` on the system prompt;
    - server-side refusal fallback (`fallbacks: "default"`, beta `server-side-fallback-2026-07-01`) for Sonnet and Opus.

    The batch path uses Message Batches, keyed by `custom_id = segment_id`. A refusal (`stop_reason=="refusal"`) is recorded as `refused` and retried once on the sync path.
  - `resolve_quotes(text, segment, quotes) -> tuple[list[EvidenceSpan], bool]` searches exact first, then whitespace-normalised. It returns `unresolved=True` if any quote is missing.
  - `run_tagging(spec, sample_name, run_id=None, limit=None) -> RunManifest`. It creates or resumes `data/runs/<run_id>/`, checks `ledger.can_spend` before each call or batch (estimating with `count_tokens` or a char-based estimate), appends `tags.jsonl` (`ValueTag`s, no text), and updates the manifest.

- [ ] **Step 1: Write failing tests** with a fake client object (no network):
  - `test_schema_restricts_value_ids`
  - `test_prompt_uses_official_definition_when_present`
  - `test_prompt_includes_few_shot_with_attribution`
  - `test_request_has_effort_cache_and_no_thinking_params`
  - `test_fallbacks_only_on_sync_sonnet_opus`
  - `test_empty_tag_list_is_valid`
  - `test_unresolved_quote_keeps_tag_flagged`
  - `test_refusal_recorded_and_retried_once`
  - `test_ledger_refuses_over_cap` (runner level: stops with `STOPPED_BUDGET`)
  - `test_run_resumes_without_retagging`
  - `test_tags_jsonl_has_no_text`
- [ ] **Step 2:** FAIL → **Step 3:** implement. Read the `claude-api` skill (Python README, structured outputs, batches, prompt caching) before writing SDK calls. → **Step 4:** PASS + ruff.
- [ ] **Step 5: Live smoke run.** Tag 3 sample articles with Haiku 5.5, low effort, sync. Check the cache read tokens on the 2nd/3rd call, the ledger cost and the manifest. Report the cost.
- [ ] **Step 6: Commit** `feat: Claude tagger, quote resolution, resumable runs`.

### Task 8: Review page

**Files:**
- Create: `src/semval/review/labels.py`, `src/semval/review/server.py`, `src/semval/review/static/{index.html,review.js,review.css}`, `tests/test_labels.py`, `tests/test_review_server.py`
- Modify: `src/semval/cli.py` (`review` subcommand)

**Interfaces:**
- Produces:
  - `Verdict(StrEnum)`: `CORRECT`, `NOT_PRESENT`, `WRONG_CALL`, `ADDED`.
  - `LabelRecord(BaseModel)`: `labeller`, `document_id`, `value_id`, `level_id`, `model_stance: Stance | None` (None for ADDED), `verdict`, `corrected_stance: Stance | None` (required when verdict ∈ {WRONG_CALL, ADDED}), `note: str = ""`, `source_runs: list[str]`, `updated: datetime`.
  - `LabelStore(path)` with `.upsert(rec)` (key = labeller, document_id, value_id, level_id) and `.all()`.
  - `pool_unjudged(runs: list[RunManifest], store, labeller) -> list[ReviewItem]`. It gives the union of tags across runs that have no verdict yet, with the run identity hidden (blind).
  - CLI:
    - `python -m semval review --run <id> [--run <id> ...] [--blind] --labeller owner [--port 8765]`
    - `--source touche23-fewshot` to review few-shot candidates.
  - `TextProvider` protocol: `text(document_id) -> str`. Implementations: raw sample documents (`data/raw/docs`) and Touché23 items (Task 10, used by `--source touche23-fewshot`). The server takes a provider and never reads files directly.
  - JSON API:
    - `GET /api/items`
    - `GET /api/doc/<id>` (text via the `TextProvider`)
    - `POST /api/verdict`
  - Static UI as approved in the spec:
    - layout A: article left, tag table right;
    - header with country, source, genre, date, run settings (hidden when `--blind`), "Article n/N" and "Saved ✓";
    - **underline** highlights, a stable colour per value id (a hash into a fixed palette), and a matching chip in the table;
    - clicking a row scrolls to and focuses its spans;
    - ✓ / ✗ / ⟲ (⟲ opens endorse/reject/mention);
    - "+ add missed value" from the `TargetSet`;
    - a notes field;
    - autosave on every action.
  - Bind to 127.0.0.1 only.

- [ ] **Step 1: Write failing tests:**
  - `test_verdict_upsert_last_write_wins`
  - `test_wrong_call_requires_corrected_stance`
  - `test_label_file_has_no_text`
  - `test_pool_unjudged_excludes_judged_and_hides_run`
  - `test_server_serves_items_and_saves` (start the server on port 0 in a thread, then use stdlib `urllib`)
  - `test_server_binds_localhost_only`
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS + ruff. Open the page once with a 2-article fixture run and screenshot-check the layout against the spec (underline highlights readable in dark mode).
- [ ] **Step 5: Commit** `feat: local review page with blind pooling`.

### Task 9: Owner checkpoint: first tagging and unit decision (STOP)

- [ ] **Step 1:** Run `python -m semval tag --sample thin-slice-v0 --model claude-sonnet-5-5 --effort medium --level leaf --unit article --limit-per-country 10 --few-shot off`. Few-shot is off because the examples don't exist yet. Report the cost.
- [ ] **Step 2: STOP.** Ask the owner to review the 20 articles in the review page.
- [ ] **Step 3:** With the owner, decide the unit (article / paragraph / sentence) from the corrections: look at missed values, wrong calls and contested cases. Record the decision in the spec §3 and in the ledger. If the unit changes, Task 13's grid runs at the new unit, merged to article for owner-set scoring, within the $50 cap.

### Task 10: Touché23 loader and Greek proxy

**Files:**
- Create: `src/semval/datasets/touche23.py`, `tests/test_touche23.py`, `tests/fixtures/touche23/*.tsv` (synthetic rows)
- Modify: `src/semval/cli.py` (`touche23` subcommand: `download`, `build-proxy`)

**Interfaces:**
- Produces:
  - `TOUCHE23_CATEGORIES` maps each of the 20 category names to a framework leaf id, or `None` for "Universalism: objectivity".
  - `OBJECTIVITY_TARGET = {"basic10": "universalism"}`.
  - `load_split(split: Literal["train","validation","test"]) -> list[ToucheItem]`, where `ToucheItem` has id, text (conclusion + stance + premise), and `labels: set[str]` (leaf ids, plus the objectivity flag).
  - `gold_at_level(item, framework, level_id) -> set[str]`.
  - `build_greek_proxy(n=100, seed=1) -> path`. It translates test items with Claude (Sonnet 5.5, low effort, through the ledger) into `data/external/touche23/proxy_el.jsonl` (git-ignored), with parallel ids.
  - `download()` fetches the raw data files from the Hugging Face repo by direct file URL into `data/external/touche23/`. It never runs the loading script.

- [ ] **Step 1: Write failing tests:**
  - `test_category_map_covers_20`
  - `test_objectivity_maps_to_universalism_at_basic10_and_dropped_at_leaf`
  - `test_parse_fixture_rows`
  - `test_gold_at_level_rolls_up`
  - `test_proxy_keeps_ids_and_labels` (fake translator)
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS + ruff. Run `download` live and `build-proxy` live, and report the counts and cost.
- [ ] **Step 5: Commit** `feat: Touché23 loader, level mapping, Greek proxy`.

### Task 11: Few-shot examples (owner confirmation STOP)

**Files:**
- Create: `data/fewshot/touche23.yaml` (committed; CC BY attribution header), `src/semval/tagging/fewshot.py`, `tests/test_fewshot.py`

**Interfaces:**
- Produces: `select_candidates(n=20, seed=1)` from train+validation only. It balances by value and draws stance from Claude: Opus 5.5, medium effort, given the gold presence labels as hints. `load_fewshot(path) -> list[FewShotExample]`.

- [ ] **Step 1:** Write tests (`test_candidates_never_from_test_split`, `test_fewshot_yaml_has_attribution`), then implement and run them. Generate 20 candidates.
- [ ] **Step 2: STOP.** The owner confirms or corrects the stance of each candidate in the review page (`--source touche23-fewshot`). Keep 10–20 of them, balanced endorse/reject/mention.
- [ ] **Step 3:** Write the confirmed set to `data/fewshot/touche23.yaml`. Commit `data: confirmed Touché23 few-shot examples`.

### Task 12: Evaluation metrics and report

**Files:**
- Create: `src/semval/evaluation/metrics.py`, `src/semval/evaluation/report.py`, `tests/test_metrics.py`, `tests/test_report.py`
- Modify: `src/semval/cli.py` (`evaluate` subcommand)

**Interfaces:**
- Produces:
  - `presence_scores(pred: dict[str,set[str]], gold: dict[str,set[str]], labels: list[str]) -> Scores` (per-label P/R/F1, macro-F1, support).
  - `stance_agreement(run_tags, labels: LabelStore, level_id) -> StanceScores` (agreement on co-present values, missed, spurious, with counts).
  - `language_gap(scores_en, scores_el) -> float`.
  - `write_report(results: list[ConfigResult], path=Path("docs/research/tagging-evaluation.md"))`. The report has a table of configuration × (macro-F1 EN, macro-F1 EL-proxy, gap, stance agreement, cost/1k, latency), the decision rule from spec §5.6, the caveats (arguments ≠ news; EL is a proxy; small owner n), and a recommendation.

- [ ] **Step 1: Write failing tests:**
  - hand-computed P/R/F1 on a 3-item example;
  - macro-F1 ignores labels with zero support only when declared;
  - `test_stance_agreement_counts`;
  - `test_report_contains_caveats_and_rule`
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** PASS + ruff.
- [ ] **Step 5: Commit** `feat: evaluation metrics and report`.

### Task 13: Evaluation grid, blind pass and decision (STOP)

- [ ] **Step 1: Grid.** Run with batches, all within the ledger cap.
  - Configurations: Haiku 5.5 {low, medium}; Sonnet 5.5 {low, medium, high}; Opus 5.5 {low, medium, high}. Level `leaf` is scored at `basic10`; few-shot is on.
  - Extra configurations on Sonnet medium and Opus medium: level `basic10` directly, and few-shot off.
  - Lexicon baseline: once.
  - Inputs: Touché23 test (EN; sample size chosen to fit the budget, at least 300 items), the EL proxy, and the 20 owner articles.

  Report the cost after each configuration. If the cap would be hit, drop the lowest-value cells (Haiku medium, then Sonnet high) and say so.
- [ ] **Step 2:** Compute metrics, then `python -m semval evaluate` writes the draft report.
- [ ] **Step 3: STOP: blind pass.** The owner runs `python -m semval review --run <all grid runs on owner articles> --blind --labeller owner` and judges only the unjudged pooled tags.
- [ ] **Step 4:** Re-compute stance agreement with the complete owner labels, then finalise `docs/research/tagging-evaluation.md` with a recommendation.
- [ ] **Step 5: STOP: decision.** The owner picks the method. Record it in the spec §3 (`## Decision` in tagging-evaluation.md). Add the follow-ups to `docs/backlog.md`. Commit `docs: tagging method decision`.
