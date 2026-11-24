# Backlog

Deferred work, by area. One line per item: what, why deferred, link. Every later deferral is added here.
Spec: [tagging-method design](superpowers/specs/2026-11-19-tagging-method-design.md) (section 6.2).

## Methods

- Three-way method comparison (b): deferred until the first two methods have run on the sample. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- ValueEval'24 (Greek + news test set): Zenodo access request drafted 2026-11-19, awaiting access. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- Greek few-shot examples from owner-corrected articles: needs the owner's review pass first. [spec 7](superpowers/specs/2026-11-19-tagging-method-design.md)
- **Calibrate tagging quality** (owner, 2026-11-24): the chosen method (Sonnet 5.5 high) scores only ~0.55 macro-F1 on Touché23 and agrees with the owner's stance on ~64% of shared values. Options to try: better and more in-domain few-shot examples (ValueEval'24 news, more owner-corrected Greek/UK paragraphs), paragraph context (headline, neighbouring paragraphs), per-value thresholds on confidence, a fine-tuned or other model. Every experiment that spends money needs the owner's go-ahead first. [evaluation](research/tagging-evaluation.md)
- Paragraph context for the tagger: the model sees one paragraph without the headline or the rest of the article, so stance in rebuttals and irony can go wrong. [spec 3](superpowers/specs/2026-11-19-tagging-method-design.md)
- Kiesel et al. 2022 54-value taxonomy as a source of value definitions: after the base framework is fixed. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- Moral Foundations Theory (MFT) lens: a second reading of the same tags, not needed for v0. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- Translation toggle in the review page: nice for non-Greek reviewers, not on the critical path. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)

## Sources

- Browser checks for blocked publishers (DPG, Rossel, Mediafin, Roularta, Le Monde, Telegraph ...): automated fetches were refused, so terms need a manual look. [sources.yaml](../data/sources/sources.yaml)
- Tele-Loisirs: not yet assessed. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- Forum classification of AgoraVox and GeenStijl: forums are out of v0 scope until classified. [sources.yaml](../data/sources/sources.yaml)
- GR 1984-1996: coverage gap; no usable source found yet. [coverage](research/coverage.md)
- NL 1940-1989 Delpher free part: which titles and years are free is unverified. [sources.yaml](../data/sources/sources.yaml)
- EU Art. 3 TDM route via a university partner: needs an institutional partner. [sources research](research/sources.md)
- Eastern Europe: outside the v0 country list. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- Balkans: outside the v0 country list. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- 1880-1940: outside the v0 period list. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)

## Data schema

- Hawkes analysis needs article timestamps, which the current schema does not store. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)

## Legal

- EU Art. 3 via a university partner (see Sources): the legal basis for research TDM on restricted archives. [sources research](research/sources.md)

## Analysis

- ESS Round-12 series break: values scores before and after are not directly comparable. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)
- ESS scoring key to verify (`ipbhprp`): the item mapping was not confirmed against the codebook. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)

## Extensions

- Eastern Europe, Balkans and 1880-1940 (see Sources): widen country and period coverage after v0. [spec 6.2](superpowers/specs/2026-11-19-tagging-method-design.md)

## Engineering follow-ups

From the final review of the tagging branch (2026-11-24). Small code and docs fixes, none blocking; most are deferred because they cannot occur with one owner, one process and the current prompt.

### Cost accounting

- Ledger lock timeout loses a paid cost: a `TimeoutError` while recording a sync call stops the run before the row is written, and the resume calls that segment again. Reconcile it (write a side file `<ledger>.unrecorded` that `total()` counts, or wait for the lock without limit, since the money is spent). Deferred: needs a second process holding the lock for 30 s or more, and costs at most one call per incident. [ledger.py](../src/semval/tagging/ledger.py)
- Refused batch items are sent again on the sync path when a pending batch is fetched again on resume (real, small spend). Persist "sync retry done" per segment. Deferred: refused items are rare and only an interrupted batch triggers it. [claude.py](../src/semval/tagging/claude.py)
- Mid-file ledger fragment repair: `repair()` only moves a damaged *final* line; damage earlier in the file still stops every run until fixed by hand. Deferred: only the final line can be torn by a crash. [ledger.py](../src/semval/tagging/ledger.py)
- `_try_lock` treats every `OSError` as contention; the ledger is read twice and locked twice per record. Deferred: correct, just slower. [fsutil.py](../src/semval/fsutil.py)
- A batch is all-or-nothing against the budget, and a resumed batch loses raised `max_tokens` caps. Deferred: the pre-call estimate is about 8x conservative (measured), so the cap is not reached in practice. [runner.py](../src/semval/tagging/runner.py)
- Pre-call estimates are rough (600 output tokens per segment, character-count fallback, `AttributeError` catch in `count_tokens`); fallback-model cache prices are inferred. Verify the prices before production-scale runs. [config.py](../src/semval/config.py)
- Move `billed()` and `CHARS_PER_TOKEN` into one shared helper in `tagging` (they are duplicated in the Touché proxy and few-shot scripts). Deferred: refactor only. [touche23.py](../src/semval/datasets/touche23.py)
- The cost ledger's default path is relative to the working directory. Deferred: the CLI always runs from the repo root. [ledger.py](../src/semval/tagging/ledger.py)

### Runner, units and tags

- Merge tiny paragraphs (one-line paragraphs cost a full call and carry little context). Deferred to the calibration follow-up. [units.py](../src/semval/units.py)
- Over-tagging of `benevolence_dependability`: the model marks it present more often than the owner does. Deferred to the calibration follow-up. [evaluation](research/tagging-evaluation.md)
- `_combine` trusts single-run groups; the sampler's seed handling is redundant. Deferred: entry points guard it. [tags.py](../src/semval/tags.py)
- Old run manifests and some report wording predate later fields. Deferred: old runs still load. [runner.py](../src/semval/tagging/runner.py)
- The lexicon tagger's word stems overmatch; its Greek test is indirect. Deferred: the lexicon is a reference point only. [lexicon.py](../src/semval/tagging/lexicon.py)

### Review page and labels

- Notes save on every keystroke: debounce the autosave. Deferred: it works, just chatty. [review.js](../src/semval/review/static/review.js)
- Owner-selected spans for values added with "+ add missed value": today such a value has no evidence span. Deferred to the calibration follow-up. [session.py](../src/semval/review/session.py)
- Two label writers in different processes are not locked; `updated` is stamped before the lock; normal mode hides other runs' stances; torn label lines are skipped anywhere in the file, not only at the end (unlike the ledger). Deferred: one owner, one server. [labels.py](../src/semval/review/labels.py)
- The few-shot candidate session hard-codes the framework id `schwartz19`. Deferred: Touché23 gold is defined over Schwartz 19, so the coupling is real; take it from a flag if another framework gets candidates. [fewshot_session.py](../src/semval/review/fewshot_session.py)

### Framework

- ORPC inline definitions: the 10 basic values cite JPSP Table 1 because the ORPC PDF (Schwartz 2012, CC BY-NC-ND) could not be opened; if the owner opens it in a browser, its definitions could go inline and public. Deferred: needs a manual browser check. [framework decision](research/framework-decision.md)
- Framework file checks: `KeyError` (not `ValueError`) when `targets_from` names an unknown id; no nested duplicate-key test; one long line in the framework memo; a brittle docstring test. Deferred: cosmetic. [values.py](../src/semval/values.py)

### Evaluation report

- `semval evaluate` overwrites the hand-written "Cost notes" and "Decision" sections of the evaluation report. Keep them in a separate file, or have the renderer preserve a hand-written trailer, before the next re-run. [evaluation](research/tagging-evaluation.md)
- Cost per 1,000 articles uses whole-run spend; latency mixes units; the "paragraph" caption is hard-coded; the framework comes from the first run; `SCORING_LEVEL` is a default constant; per-value names are English only; leaf/basic10 F1 paths are thinly tested; no partial-document test; `_load` segments every document. Deferred: the published table is correct for the current runs. [report.py](../src/semval/evaluation/report.py)
- The two `basic10` configurations show 0 spurious tags because a leaf-level owner verdict cannot prove absence at 10 values. Deferred: stated in the report's cost notes. [evaluation](research/tagging-evaluation.md)

### Datasets and few-shot scripts

- Touché23: the download is untested (no HTTP check); the Greek proxy append is not atomic; `total()` is read twice; eager import; redundant leaf check; a `type: ignore`; the proxy ignores `split`; `derive` allows duplicate ids; stats reset; a bare id in `touche_gold`. Deferred: one-off scripts, already run. [touche23.py](../src/semval/datasets/touche23.py)
- Few-shot candidates: the CLI exits 0 when drafts failed; bare `KeyError` in finalize; an unused `_quotes` parameter; mid-function imports; private `_Candidate`; no tie-break test; a resume keeps the first `few_shot_files` silently. Deferred: one-off script, already run. [fewshot_candidates.py](../src/semval/tagging/fewshot_candidates.py)
- Test hygiene: an unused `noqa` import in `fewshot.py`, an unused `capsys`, a translator test and some few-shot tests that were never seen failing first. Deferred: cosmetic. [tests](../tests)

### Sampling and fetching

- Uneven date coverage in the samples: some sources contribute only a few days of the window. Deferred: enough for the method comparison; fix before trend analysis. [sample.py](../src/semval/sampling/sample.py)
- Challenged / not-free markers are kept in memory only; a 200 response with a challenge page is cached (not article text, not committed); parse tests are post hoc; redirects to non-http schemes are not refused explicitly; no not-free-after-redirect or cross-host delay tests. Deferred: no observed failure. [sampling](../src/semval/sampling)
- Source registry: backlog reasons and duplicates to tidy; the year basis of `ch-e` and `es-abc` to confirm. Deferred: outside the thin slice. [sources.yaml](../data/sources/sources.yaml)
