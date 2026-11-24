# Plugging in: models, prompts, examples, setups, tagger kinds

Every piece of the tagging pipeline that you might want to swap lives in a file or one module. Nothing needs editing in several places. Two rules apply to all of it.

- **Ask before any paid run.** Always look first with `semval tag --sample SAMPLE --tagger NAME --dry-run`. It builds the tagger, prints what would be sent and the cost estimate, and spends nothing. Only run without `--dry-run` after the owner has said yes to that spend.
- **Old runs must keep working.** Every run records which model, prompt and example files it used, and `semval evaluate` groups runs by those. So never delete or rewrite something an old run names; add a new thing next to it.

## A model

Add one row to `data/models.yaml`: the id, the provider (`anthropic`), the four prices per million tokens (input, output, cache write, cache read), `requestable: true`, and `server_fallbacks`. Check the prices against the provider's list first. To retire a model, set `requestable: false`. Never delete the row: old run manifests name it, and they would stop loading. The model then appears in `--model` and is accepted in setups.

## A prompt

Copy `data/prompts/v1.yaml` to a new file whose name is the new id, say `data/prompts/v2.yaml`, set `id: v2` inside it, and edit the instructions, the user template, or the way targets and examples are worded. Use it with `--prompt v2`, or `prompt: v2` in a setup. Leave `v1` alone: its hash must stay the same. Each run stores a SHA-256 hash (a fingerprint) of the full prompt, targets and examples together, so two runs with the same fingerprint really saw the same text, and any edit gives a different one. In the evaluation report a configuration with another prompt is listed separately, with ` prompt v2` added to its label.

## An example set

Few-shot examples are a YAML file in the same shape as `data/fewshot/touche23.yaml`: an `attribution` block and a list of `examples`, each with text, language and tags (value, stance, verbatim quotes, confidence). Your own articles go under `data/fewshot/local/`, which is git-ignored. Pass files with `--few-shot-file PATH` (repeat for several, in order), or list them in a setup under `few_shot_files`. The run records the files actually used. In the report, a configuration whose files differ from the most common set gets ` examples NAME+NAME` in its label (ties for "most common" go to the first set in sorted order).

## A setup

A setup is a saved choice of everything above: a file `data/taggers/NAME.yaml` with `description`, `kind`, `model`, `effort`, `level`, `unit`, `framework`, `prompt`, `batch`, `few_shot_files` (and `options` for kinds that take them). See `sonnet-high.yaml` (the default) and `lexicon.yaml`. Use it with `semval tag --sample S --tagger NAME`. Any flag (`--model`, `--effort`, `--prompt`, `--few-shot-file`, `--no-few-shot`, `--batch`) overrides one field for that run only. The run manifest records the setup name.

## A new tagger kind

A kind is a way of producing tags (a model, a word list, something else). Write one module that defines a class with `prompt_info(targets)` and `tag(segments, texts, targets, documents)`, and ends by calling `register_tagger("mykind", factory, needs=..., allows=..., baseline=...)`. `needs` and `allows` name the spec fields the kind requires or accepts (for example `options`, `unit`); `baseline=True` marks a comparison that is never recommended. Then add the module's name to `_BUILTIN_MODULES` in `src/semval/tagging/registry.py` so it loads. The template is the `EchoTagger` and `test_fake_kind_runs_end_to_end` in `tests/test_tagger_registry.py`: copy it, change the tagging rule, and the test shows the kind running end to end with no paid call. Then add a setup file for it (above). The CLI and the runner need no changes.
