# Pluggable Taggers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make models, tagger kinds, prompts and complete tagging setups plug-and-play data or modules, so calibration work can add them without editing code in several places.

**Architecture:**
- `data/models.yaml` becomes the single source of model ids and prices. A validated `ModelId` string type replaces the closed enum.
- A tagger registry maps kind names to factories. The runner and CLI build taggers only through it.
- Prompts live in `data/prompts/<id>.yaml`. `v1` is today's text, unchanged.
- `data/taggers/<name>.yaml` names a full setup, and `semval tag --tagger NAME` runs it.
- The evaluation also separates configurations by prompt id and few-shot files.

**Tech Stack:** Python 3.11, pydantic 2, PyYAML, pytest, ruff (existing).

**Spec:** `docs/superpowers/specs/2026-11-24-pluggable-taggers-design.md` (parent: `docs/superpowers/specs/2026-11-19-tagging-method-design.md`).

## Global Constraints

- **No paid API calls.** Never run `semval tag` without `--dry-run`, `fewshot candidates`, `fewshot from-labels` or `touche23 build-proxy`, and never read or set API key variables. All tests use fake clients (owner rule: ask before any spend).
- **Commands:** run tests with `.venv/Scripts/python.exe -m pytest -q` and lint with `.venv/Scripts/python.exe -m ruff check .` and `ruff format --check .`. Never run `uv run` or `uv sync`.
- **Typing:** closed sets of reused strings are `StrEnum` or `Literal`:
  - `Provider`: `ANTHROPIC = "anthropic"`;
  - `Effort`, `Stance`, `UnitLevel`, `RunStatus`.
- **Open sets are validated against their registry file:** model ids, prompt ids, setup names and tagger kinds. An unknown id raises `ValueError` naming the known ones.
- **Compatibility:**
  - Every existing run manifest in `data/runs/` must still load, resume-check and score.
  - The `v1` prompt hash must equal today's `prompt_sha256` for the same targets and few-shot examples.
  - Never delete a model row: retire it with `requestable: false`.
- **No raw text committed:** keep `data/raw`, `data/labels`, `data/runs`, `data/external` and `data/fewshot/local` out of git.
- **Commit trailer:** `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Existing runs after the refactor:** old manifests have no `prompt_id` or `options`, and their model is a plain string. They load, resume without "prompt changed" errors, and group in `evaluate` exactly as before. Tests: `test_old_manifest_loads_and_defaults` (Task 3), `test_v1_prompt_hash_unchanged` (Task 2), and `test_existing_configs_group_as_before` (Task 5).
2. **A model the API reports that is not in the registry:** it is still charged at the dearest known price. Test: `test_unknown_reported_model_priced_dearest` (Task 1).
3. **A typo in a setup file, or an unknown model, prompt or kind name:** the error names the file and the known ids, rather than a `KeyError` traceback. Tests: `test_unknown_setup_name_lists_known`, `test_setup_rejects_unknown_field` (Task 4), and `test_unknown_kind_lists_registered` (Task 3).
4. **Overrides that do not fit the kind** (e.g. `--model` with the lexicon setup): a clear error, not a silently ignored flag. Test: `test_override_not_valid_for_kind` (Task 4).
5. **A broken registry file** (duplicate model id, missing price field): it fails at load, naming the row. Test: `test_registry_rejects_duplicate_and_missing_fields` (Task 1).

---

### Task 1: Model registry

**Files:**
- Create: `data/models.yaml`, `src/semval/models.py`, `tests/test_models.py`
- Modify: `src/semval/config.py`, `src/semval/tagging/ledger.py`, `src/semval/tagging/claude.py`, `src/semval/datasets/touche23.py`, `src/semval/tagging/fewshot_candidates.py`, `src/semval/cli.py` (`--model` choices), tests that import `ModelId` / `PRICES` / `FallbackModelId`

**Interfaces:**
- **`data/models.yaml`:** a `models:` list.
  - Each row has `id`, `provider` (`Provider`), `prices: {input, output, cache_write, cache_read}` (USD per 1M tokens), `requestable: bool` and `server_fallbacks: bool`.
  - The rows and prices are today's `PRICES`, unchanged: the three 5.5 models are requestable, and the three fallback models are `requestable: false`.
  - `batch_factor: 0.5` is a top-level key.
- **`semval.models`:**
  - `class Provider(StrEnum)` and `class ModelInfo(BaseModel)`, frozen, `extra="forbid"`.
  - `class ModelRegistry` with:
    - `get(id) -> ModelInfo`;
    - `requestable() -> list[str]`;
    - `price(id) -> Price`;
    - `priced(name: str) -> str` (an unknown name gives the dearest id);
    - `batch_factor: float`.
  - `load_registry(path=MODELS_PATH) -> ModelRegistry` and `registry() -> ModelRegistry`, a cached default.
  - `ModelId = Annotated[str, AfterValidator(check_model)]`: `check_model` accepts any registry id and otherwise raises `ValueError` listing the ids.
- **`semval.config`:**
  - Keeps `BUDGET_USD`, `Effort`, the max-token settings and `API_KEY_ENV_VARS`.
  - Re-exports `ModelId` and `Price` from `semval.models`.
  - `PRICES`, `FallbackModelId`, `PricedModel`, `SERVER_FALLBACK_MODELS`, `BATCH_FACTOR` and `priced_model` are removed. Their callers use `registry()`.
  - Named constants `SONNET_5_5 = "claude-sonnet-5-5"`, `OPUS_5_5 = "claude-opus-5-5"` and `HAIKU_5_5 = "claude-haiku-5-5"` stay as defaults only, for `PROXY_MODEL`, `DRAFT_MODEL` and tests.
- **`cost_of(usage, model: str, batch)`** prices through the registry.

- [ ] **Step 1: Write the failing tests** in `tests/test_models.py`:
  - `test_registry_matches_previous_prices`: the six ids and their four prices equal the old table, and `batch_factor == 0.5`.
  - `test_requestable_and_fallback_flags`: `requestable()` gives the three 5.5 ids; `server_fallbacks` is True for Sonnet and Opus 5.5 only.
  - `test_unknown_reported_model_priced_dearest`: `priced("claude-future-9")` returns the id with the highest (output, input) price; `cost_of` with that name is > 0.
  - `test_model_id_validation_lists_known`: a pydantic model with a `ModelId` field rejects `"gpt-x"` with a message that contains `claude-sonnet-5-5`.
  - `test_registry_rejects_duplicate_and_missing_fields`: temp YAML files with a duplicate id, or a row missing `prices.output`, raise `ValueError` naming the id.
  - `test_new_row_needs_no_code_change`: with a temp registry plus one extra requestable row, that id validates, prices and appears in `requestable()`.
- [ ] **Step 2:** run them and confirm they FAIL (module missing).
- [ ] **Step 3:** implement `models.py` and the YAML, switch all callers, and update the existing tests' imports. CLI `--model` uses `choices=registry().requestable()` and `type=str`.
- [ ] **Step 4:** run the full suite and ruff, and confirm PASS (357 + new).
- [ ] **Step 5: Commit** `feat: model registry file replaces the model enum and price table`.

### Task 2: Prompt files

**Files:**
- Create: `data/prompts/v1.yaml`, `tests/test_prompt_files.py`
- Modify: `src/semval/tagging/prompt.py`, `src/semval/tagging/claude.py`, `src/semval/tagging/base.py` (`TaggerSpec.prompt_id`)

**Interfaces:**
- **`data/prompts/v1.yaml`:** keys `id: v1`, `instructions` (today's `INSTRUCTIONS`, with `{max_quotes}` where it has `MAX_QUOTES`), `user_template` (today's `USER_TEMPLATE`) and `notes`.
- **`semval.tagging.prompt`:**
  - `PromptTemplate` (pydantic).
  - `load_prompt(prompt_id: str, prompts_dir=PROMPTS_DIR) -> PromptTemplate`. An unknown id raises `ValueError` listing the known ids.
  - `build_prompt(targets, few_shot, template: PromptTemplate)`.
  - `user_message(text, meta, template)`.
  - `prompt_sha256(parts, template)` hashes exactly what it hashes today: system, user template and schema.
- **`TaggerSpec.prompt_id: str = "v1"`.** `ClaudeTagger` loads `load_prompt(spec.prompt_id)`.

- [ ] **Step 1: Write the failing tests:**
  - `test_v1_prompt_hash_unchanged`: first, on the unchanged code, compute `prompt_sha256` for the real framework's `leaf` and `basic10` targets, with and without `data/fewshot/touche23.yaml`. Paste the four hex values into the test as constants. Then assert that the new code gives the same four.
  - `test_v1_text_equals_previous_constants`: the rendered instructions equal the old `INSTRUCTIONS` string (kept in the test as a literal).
  - `test_unknown_prompt_id_lists_known`.
  - `test_new_prompt_file_changes_hash_and_is_used`: a temp `v2.yaml` with different instructions gives a different hash, and `ClaudeTagger` with `prompt_id="v2"` sends the v2 text (fake client).
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** full suite and ruff PASS.
- [ ] **Step 5: Commit** `feat: versioned prompt files`.

### Task 3: Tagger registry

**Files:**
- Create: `src/semval/tagging/registry.py`, `tests/test_tagger_registry.py`
- Modify: `src/semval/tagging/base.py`, `src/semval/tagging/claude.py`, `src/semval/tagging/lexicon.py`, `src/semval/tagging/runner.py`, `src/semval/evaluation/metrics.py` (kind checks)

**Interfaces:**
- **`TaggerFactory = Callable[[TaggerSpec, TaggerContext], Tagger]`.** `TaggerContext` is a frozen dataclass with `client: Any = None` and `few_shot: Sequence[FewShotExample] = ()`.
- **`register_tagger(kind: str, factory: TaggerFactory, *, needs: frozenset[str] = frozenset(), allows: frozenset[str])`:**
  - `needs` and `allows` name the `TaggerSpec` fields the kind requires or accepts, out of `model`, `effort`, `unit`, `few_shot`, `batch` and `options`.
  - Registering an existing kind raises `ValueError`.
- **`build_tagger(spec, ctx=TaggerContext()) -> Tagger`**, `registered_kinds() -> list[str]` and `check_spec(spec)` (missing needs or extra fields give a `ValueError` naming them).
- **`TaggerSpec`:**
  - `kind: str`, validated by `registered_kinds()` at model validation.
  - `options: dict[str, str | int | float | bool] = {}`.
  - `TaggerKind(StrEnum)` stays as the names of the two built-in kinds.
  - The old `_claude_needs_settings` validator is replaced by `check_spec`.
- **Built-in registration:**
  - The claude kind registers in `semval.tagging.claude` (needs model, effort and unit).
  - The lexicon kind registers in `semval.tagging.lexicon` (needs `options["lexicon_file"]`, which defaults to `DEFAULT_LEXICON_PATH` when absent).
  - `semval.tagging.registry` imports both built-ins lazily, so the registry is complete after `import semval.tagging.registry`.
- **Runner:** `run_tagging(spec, …, tagger=None)` builds through `build_tagger`. `make_tagger` is removed.
- **Evaluation:** "is the baseline" checks use a new `TaggerSpec.is_baseline` property (True for lexicon) instead of comparing kinds.

- [ ] **Step 1: Write the failing tests:**
  - `test_unknown_kind_lists_registered`.
  - `test_fake_kind_runs_end_to_end`: the test registers kind `"echo"`, whose factory returns a tagger that tags every segment with one fixed value. `run_tagging` on a tiny sample fixture writes a DONE manifest, with no change to the runner or CLI.
  - `test_claude_spec_missing_effort_rejected` and `test_lexicon_rejects_model`.
  - `test_double_registration_rejected`.
  - `test_old_manifest_loads_and_defaults`: every `data/runs/*/manifest.json` present on disk loads with `prompt_id == "v1"` and `options == {}`. Skip when `data/runs` is absent. Also load a checked-in minimal old-format manifest fixture.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** full suite and ruff PASS.
- [ ] **Step 5: Commit** `feat: tagger registry; runner builds taggers by kind`.

### Task 4: Saved setups and the `tag` command

**Files:**
- Create: `data/taggers/sonnet-high.yaml`, `data/taggers/lexicon.yaml`, `src/semval/tagging/setups.py`, `tests/test_setups.py`
- Modify: `src/semval/cli.py` (`tag` parser and `_tag`, `_tag_lexicon` removed)

**Interfaces:**
- **`data/taggers/sonnet-high.yaml`:** `kind: claude`, `model: claude-sonnet-5-5`, `effort: high`, `level: leaf`, `unit: paragraph`, `framework: schwartz19`, `prompt: v1`, `batch: true` and `few_shot_files: [data/fewshot/touche23.yaml, data/fewshot/local/articles.yaml]`, plus a `description:` line naming the decision (2026-11-24).
  - A missing local file is skipped with a logged warning, and the manifest records only the files used. The owner's local examples are not in git.
- **`data/taggers/lexicon.yaml`:** `kind: lexicon`, `level: basic10`, `framework: schwartz19`, `options: {lexicon_file: data/lexicon/basic10_seed.yaml}`.
- **`semval.tagging.setups`:**
  - `TaggerSetup` (pydantic, `extra="forbid"`): `description`, `kind`, `model`, `effort`, `framework`, `level`, `unit`, `prompt`, `few_shot_files: list[Path] = []`, `batch: bool = False` and `options`.
  - `load_setup(name, dir=SETUPS_DIR) -> TaggerSetup`. An unknown name raises `ValueError` listing the known setups.
  - `apply_overrides(setup, **overrides) -> TaggerSetup`: only non-None values apply; `few_shot_files=[]` means zero-shot.
  - `to_spec(setup) -> TaggerSpec`: `few_shot = bool(few_shot_files)`, then `check_spec`.
- **CLI:** `semval tag --sample S [--tagger NAME (default sonnet-high)]`.
  - Override flags: `--model`, `--effort`, `--level`, `--unit`, `--framework`, `--prompt`, `--few-shot-file` (repeatable; replaces the list), `--no-few-shot`, `--batch/--no-batch` and `--option KEY=VALUE` (repeatable).
  - Kept as they are: `--limit`, `--limit-per-country` and `--run-id`.
  - `--dry-run` prints the resolved setup, spec and few-shot files, then exits 0 without building a client. It is the only way tests exercise the CLI.
  - The run manifest also records the setup name. Add `setup_name: str | None = None` to `RunManifest`.
  - `--kind` and `--lexicon-file` are removed; use `--tagger lexicon` and `--option lexicon_file=…`. The README or docs line on the old flags is updated.

- [ ] **Step 1: Write the failing tests:**
  - `test_sonnet_high_setup_matches_decision`.
  - `test_unknown_setup_name_lists_known`.
  - `test_setup_rejects_unknown_field`: the temp file has a typo `efort:`, and the message names the file.
  - `test_overrides_replace_single_fields`.
  - `test_no_few_shot_gives_zero_shot_spec`.
  - `test_override_not_valid_for_kind`: `--tagger lexicon --model claude-opus-5-5` gives a non-zero exit with a message.
  - `test_missing_local_fewshot_file_skipped_and_recorded`.
  - `test_cli_dry_run_prints_resolved_spec`: run `main(["tag", "--sample", "x", "--dry-run"])` and check the output names the model, effort and files. It makes no client.
- [ ] **Step 2:** FAIL → **Step 3:** implement → **Step 4:** full suite and ruff PASS.
- [ ] **Step 5: Commit** `feat: saved tagger setups; semval tag --tagger NAME`.

### Task 5: Evaluation grouping and the how-to doc

**Files:**
- Create: `docs/plugging-in.md`
- Modify: `src/semval/evaluation/metrics.py` (`ConfigKey`), `src/semval/evaluation/report.py` (label), `docs/backlog.md`, `tests/test_metrics.py`

**Interfaces:**
- **`ConfigKey`** gains `prompt_id: str` and `few_shot_files: tuple[str, ...]`, both from the manifest. Old manifests give `"v1"` and their recorded list.
- **The label** appends ` prompt <id>` only when the id is not `v1`, and ` examples <short names>` only when the files differ from the most common set in the report. Today's report labels therefore stay identical.

- [ ] **Step 1: Write the failing tests:**
  - `test_runs_differing_only_in_fewshot_files_are_two_configs`.
  - `test_runs_differing_only_in_prompt_are_two_configs`.
  - `test_existing_configs_group_as_before`: over the real `data/runs/grid-*` manifests (skip if absent), the grouping gives 13 configurations with the same labels as today's `docs/research/tagging-evaluation.md` table.
- [ ] **Step 2:** FAIL → **Step 3:** implement.
- [ ] **Step 4:** write `docs/plugging-in.md`, about one page with one short section each on how to add:
  - a model (one row; retire, never delete);
  - a prompt (a new file and a new id; hashes);
  - an example set;
  - a setup;
  - a new tagger kind (a module calling `register_tagger`, with the echo test as the template).

  Remove the backlog items this plan closes, if any; add none unless something is deferred.
- [ ] **Step 5:** full suite and ruff PASS → **Commit** `feat: evaluation separates prompt and example sets; plugging-in guide`.
