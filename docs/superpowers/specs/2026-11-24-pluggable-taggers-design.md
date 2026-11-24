# Pluggable Taggers — Design (short)

Date: 2026-11-24
Status: approved 2026-11-24. The owner agreed to the proposal in chat ("yes") and asked to continue after PR #1 merged.
Parent: `docs/superpowers/specs/2026-11-19-tagging-method-design.md` (decision: Sonnet 5.5 high).

## Intent

The tagger needs calibration later (backlog: "Calibrate tagging quality"). That work will try other models, other example sets, other prompts and perhaps a fine-tuned or non-Claude model.

The owner wants each of those to be **plug and play**: adding one means adding a file or one module, not editing code in several places.

**Owner rule:** no paid API run without the owner's explicit go-ahead. This plan needs none: everything is tested offline with fake clients.

## Goals

1. **Models are data.** `data/models.yaml` lists every model:
   - its provider;
   - its prices per 1M tokens (input, output, cache write, cache read);
   - whether it can be requested or is only priced (fallback models);
   - whether it supports server-side fallbacks.

   Adding a model means adding a row. Nothing in `src/` names a model id except as a default that a setup file can override.
2. **Tagger kinds are pluggable.** A small registry maps a kind name to a factory that builds a `Tagger` from a spec. `claude` and `lexicon` register themselves. A new kind (another provider, a fine-tuned model, a local classifier) is one module that calls `register_tagger`. The CLI and runner contain no `if kind == …` branches.
3. **Saved setups.** `data/taggers/<name>.yaml` names a complete configuration:
   - kind, model, effort;
   - framework, level, unit;
   - few-shot files (an empty list means zero-shot);
   - batch;
   - prompt id.

   `semval tag --tagger NAME --sample S` runs it, and individual flags still override single fields. `data/taggers/sonnet-high.yaml` records the decided method and is the default.
4. **Prompts are versioned files.** `data/prompts/<id>.yaml` holds the instructions and the user-message template. `v1` is today's text byte for byte, so the prompt hash of existing runs is unchanged and they still resume. A new prompt is a new file. The run records the prompt id.
5. **Old runs still load and score.** Manifests written before this change (no prompt id, model as a plain string) load unchanged. `semval evaluate` separates configurations that differ only in prompt id or few-shot files.

## Non-goals

- Implementing a second provider or a fine-tuned model. Only the plug-in point and a test double are built.
- Changing the decided method or re-running anything paid.
- Changing review, sampling or evaluation metrics beyond the grouping key.

## Approaches considered

- **(a) Keep the enums and add values per model.** This keeps the enum rigour, but every model means a code change in config, CLI and prices. Rejected: it is not plug and play.
- **(b) Registry files plus validated string ids (chosen).** Model ids, prompt ids and setup names live in data files and are validated against them when loaded. An unknown id is an error that names the known ones. The owner's "Enum/Literal for reused strings" rule still holds for closed sets (stance, unit, effort, run status, provider). Model ids become *data*, checked against the registry, because the set is meant to be open.
- **(c) Entry-point plugins (Python packaging).** Too heavy for one repo. An import-and-register module gives the same plug-in point.

## Decided how

- `Provider` is a `StrEnum` (`anthropic` today). `Effort` stays a `StrEnum`.
- `ModelId` becomes a validated string type backed by the registry. Code defaults (`PROXY_MODEL`, `DRAFT_MODEL`) read the registry.
- Pricing (`cost_of`, `priced_model`), `SERVER_FALLBACK_MODELS` and the CLI `--model` choices all come from the registry. An unknown reported model is still charged at the dearest known price (fail safe).
- Tagger registry: `register_tagger(kind: str, factory)` and `build_tagger(spec, *, client=None, few_shot=()) -> Tagger`. `TaggerSpec.kind` is validated against the registry. `TaggerKind` constants are kept for the two built-in kinds.
- `TaggerSpec` gains `prompt_id: str = "v1"`. Existing manifests default to `v1`.
- Evaluation `ConfigKey` gains the prompt id and the few-shot file list, both from the manifest.

## Left to the builder

The YAML field names, the module layout (e.g. `semval/registry.py` and `semval/tagging/registry.py`), the error-message wording, and how overrides merge in the CLI.
