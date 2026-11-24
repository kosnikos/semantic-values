# Tagging Method — Design (v0, step 4)

Date: 2026-11-19
Status: approved 2026-11-19
Parent spec: `docs/superpowers/specs/2026-11-18-semantic-values-design.md` (step 4 of §5)

## 1. Intent

Pick the method that turns a text into **value tags**: for each value in the framework, whether
the text *endorses*, *rejects*, or merely *mentions* it, with the evidence span. The choice is
made by measurement on real Greek and UK opinion texts and on public labelled data, within the
$300 thin-slice budget. Everything built here is reused at scale in step 5, so it must be
general: swappable in **method**, **targets** (framework/level) and **text unit**.

## 2. Goals, non-goals, anti-goals

**Goals**
- A small, polite **sampler** that collects a few dozen opinion/letters/editorial pieces per
  thin-slice country (GR, GB) from sources open under the source-use rule.
- A **tagger interface** with interchangeable implementations: Claude models (first), a
  word-list baseline (reference only).
- **Targets from data**: the tagger reads the value list from a framework file at a chosen
  level (e.g. Schwartz 19 leaves, Schwartz 10 basic values, 4 groups, or another framework).
- **Generic text units** (article / paragraph / sentence) with a **merge** step that rolls tags
  up from a lower unit to a higher one.
- A local **review web page** where the owner corrects 10–20 tagged articles.
- An **evaluation** that compares configurations and reports quality and cost; a written
  **method decision**.
- Housekeeping carried over from the v0-foundations final review (§6.1) and a **backlog
  document**.

**Non-goals**
- Tagging at scale (step 5), survey validation, spread models, blog posts.
- A trained classifier and the translated-dictionary track (deferred to the backlog — owner
  chose comparison (a), 2026-11-19).
- Translation of Greek texts for the owner (owner reads Greek).

**Anti-goals**
- Framework- or source-specific logic in shared code (e.g. the tagger naming Schwartz values).
- Bare reused strings — every reused string value is an `Enum` or `Literal`.
- Raw article text committed to the repo (Touché23 few-shot examples are CC BY and may be
  committed with attribution).
- Spending past the budget cap because a loop ran away.

## 3. Decisions made

| Topic | Decision |
|---|---|
| Comparison scope | **(a)**: Claude configurations + a word-list baseline. The three-way comparison (b) goes to the backlog. |
| Unit | Start at **whole article**; code supports paragraph/sentence and merging. **Revisit after the first owner-corrected batch, on the actual data** (explicit checkpoint, §7 step 6). **Decided 2026-11-19 at the checkpoint: tag per paragraph, report per article via merge.** On the same 20 articles (Sonnet 5.5, medium, leaf) the owner judged both runs: article level found 65 of the 103 values the owner confirmed (recall 0.63, precision 0.92, $0.17); paragraph level found 94 (recall 0.91, precision 0.89, $0.44). Paragraph level also fixed two stance calls the owner flagged. Sentence level was not tried: about 10× the calls and less context. |
| Targets | Framework file + level chosen per run; recorded in every run. |
| Owner corrections | **Review web page, layout A** (article left, tag table right), **underline highlights** (one colour per value, matching chip in the table), ✓ correct / ✗ not present / ⟲ wrong call (pick endorse/reject/mention), "+ add missed value", per-article notes, autosave. Local Python server, e.g. `python -m semval review`. No translation toggle. |
| Correction storage | Article id, value id, model call, owner verdict, notes, evidence as **character offsets only** — no text. **Kept in git-ignored `data/labels/`, not committed** (amended 2026-11-24): owner notes are free text and can quote article text. |
| Typing rigour | Reused string values are `Enum`/`Literal` (stances, verdicts, unit levels, model ids, run status, access values …). Owner, 2026-11-19. |
| API use for tagging | Allowed per parent spec §3 (owner, 2026-11-19). |
| Target level | **Report and score at the 10 basic values.** Test both tagging at 19 then rolling up, and tagging directly at 10, on two configurations; the better one at 10 becomes the default (owner, 2026-11-19). |
| Definitions given to the model | **Official definitions**: 19 values from Schwartz et al. 2012 (JPSP, Table 1), 10 values from Schwartz 2012 (Online Readings in Psychology and Culture), stored with citation and page. Licence checked first; if verbatim text cannot be public, it lives in a git-ignored local file and the repo keeps the citation. Our plain-English paraphrases stay for the review page and the blog (owner, 2026-11-19). |
| Labelled data (v0) | **Touché23-ValueEval** (`webis/Touche23-ValueEval`, CC BY 4.0, open; the raw files are downloaded from Zenodo record 7879430, which the Hugging Face card points to): ~9,300 English arguments, 20 value categories (Schwartz 19 + "Universalism: objectivity"), presence per argument. Used for the English test set and few-shot examples. **ValueEval'24 (Greek, news) is a follow-up** in the backlog (owner, 2026-11-19). Mapping: "Universalism: objectivity" → universalism at `basic10`; excluded at `leaf19`. |
| Greek quality (v0) | Owner's 10 Greek corrected articles, plus a **proxy**: ~100 Touché23 test arguments machine-translated to Greek by Claude, labels carried over; per-language F1 on parallel texts gives the EN–EL gap. Reported as a proxy (translations read cleaner than native Greek). |
| Few-shot examples | **10–20 Touché23 examples from train/validation** (never test), balanced across endorse/reject/mention. **Stance assigned by reading**, not mechanically: Claude drafts stance (Touché23 has presence only), owner confirms in the review page. CC BY 4.0 — may be sent via the API and committed with attribution. **Few-shot is on by default** (owner, 2026-11-19); the grid still runs few-shot off on two configurations to report its effect. Greek few-shot from owner-corrected articles is a backlog item (owner, 2026-11-19). |
| **Tagging method (decided 2026-11-24, owner)** | **Claude Sonnet 5.5, high effort, tagging the 19 leaf values per paragraph, few-shot on (Touché23 + local article examples), merged to the article and reported at the 10 basic values.** By the §5.6 rule: ranking score 0.554 (mean of EN 0.573 / EL-proxy 0.535) against the best 0.566 (Opus low); within 0.02 and cheapest of the three in tolerance (≈ $20 per 1,000 articles vs $36–39 for Opus); stance agreement 67/105 on the owner set, inside the gate. Haiku dropped by the stance gate; tagging directly at 10 values gave mixed results (Sonnet +0.03, Opus −0.02), so leaf tagging stays the default. Absolute quality is modest; **calibration of tagging is a follow-up** (backlog). Full table: `docs/research/tagging-evaluation.md`. |
| Blind second pass | After the grid, the review page shows the owner **only tags not yet judged**, from any configuration, **without saying which configuration proposed them** (pooled, blind). Removes the bias toward the checkpoint model; ~20–40 minutes (owner, 2026-11-19). |

## 4. Approaches considered

- **Comparison scope.** (a) Claude configurations + simple baseline — fast, cheap, what the
  evidence points to (no Greek Schwartz dictionary exists; best ValueEval-trained system scores
  0.39 F1 and needs a GPU). (b) full three-way comparison — stronger blog story, ~2× the work.
  **Chosen: (a)**; (b) to backlog.
- **Unit of tagging.** Whole article (one call per article, matches the country × year
  charting unit, evidence quotes make review fast) vs paragraph/sentence (finer, matches
  ValueEval sentence labels, 10–30× calls). **Chosen: article first, generic units in code,
  revisit on data.**
- **Correction tool.** Spreadsheet (simplest) vs review page (reading in context).
  **Chosen: review page**; layout A over a one-tag-at-a-time card flow; underline over tint or
  marker highlights (dark-theme readability).

## 5. The design

### 5.1 Core types (`src/semval/`)
- `UnitLevel` Enum: `article`, `paragraph`, `sentence` (ordered, coarse → fine).
- `Stance` Enum: `endorse`, `reject`, `mention`, plus `contested` which **only** arises from
  merging (a unit containing both endorse and reject for the same value). "Absent" = no tag.
- `Segment`: id, document id, level, parent segment id (null at article level), character
  span within the document, language, country, source id, date, genre.
- `ValueTag`: segment id, value id (from the framework file), stance, evidence spans
  (character offsets), optional confidence, tagger run id.
- `TargetSet`: framework id + level → the list of target values with definitions and
  examples, derived from the framework file. The tagger only ever sees a `TargetSet`.
- **Framework roll-ups as data** (housekeeping, §6.1): the framework file declares named
  levels (e.g. `leaf19`, `basic10`, `group4`) and a mapping per level, including the
  validation-only variant (humility → tradition) as its own named roll-up. A generic function
  maps tags from one level to another.

### 5.2 Merge
`merge(tags, from_level, to_level)` — generic, framework-agnostic. Rule: per (parent, value):
any endorse and any reject → `contested`; else endorse if any endorse; else reject if any
reject; else `mention`. Evidence spans are unioned. Unit tests cover each branch.

### 5.3 Tagger interface
`Tagger` protocol: `tag(segments, targets) -> list[ValueTag]` plus metadata (id, version,
parameters). Implementations selected by config:
- `ClaudeTagger`: Anthropic Python SDK; structured output (schema generated from the
  `TargetSet`, so value ids are constrained to the target list); framework definitions in a
  cached system prompt; Message Batches for bulk runs (50% cost); server-side refusal
  fallbacks enabled; model and effort are parameters. Models: `claude-haiku-5-5`,
  `claude-sonnet-5-5`, `claude-opus-5-5`; effort levels per the evaluation grid.
- `LexiconTagger`: word-list baseline. English only unless a licensed list exists for Greek;
  emits `mention` only (a word list cannot judge stance). Reference point, not a candidate.
- Every run writes a **run manifest**: run id, tagger id + parameters, framework id + level,
  unit level, input set, prompt hash, token usage, cost, timestamps.

### 5.4 Cost control
A cost ledger accumulates `usage` per call priced from a model-price table in config. A run
has a hard cap (config); exceeding it stops the run cleanly with a resumable state. The whole
plan's experiments target **≤ $50** of the $300 thin-slice cap; the ledger reports cumulative
spend.

### 5.5 Sampler
- Inputs: source ids from the registry (must be `is_open`, usable access, GR or GB, opinion/
  letters/editorial/column genre). Initial candidates: GR — To Vima, Ta Nea, EfSyn opinion
  pages; GB — Guardian website comment, Evening Standard comment, openDemocracy.
- Collects ~40 articles per country from 2024–2026 (recent, to keep the slice simple).
- Rules (from the parent spec and the source survey): obey robots.txt for our own user-agent
  and `Crawl-delay`; honest user-agent; polite rate; skip pages whose JSON-LD says
  `isAccessibleForFree: false` even if the HTML contains the text; no circumvention of bot
  challenges; text cached under `data/raw/` (git-ignored); only references (URL, date,
  source, title hash) are committed.
- Source-specific parsing lives in per-source adapter modules behind a `SourceAdapter`
  protocol; shared code has no source ids.

### 5.6 Evaluation
- **Value-presence quality** (scored at `basic10`, with `leaf19` reported where tagging was at
  19) on the Touché23-ValueEval `main` test split (English arguments; CC BY 4.0), plus the
  machine-translated Greek proxy subset. Report macro-F1 and per-value F1. **Caveat in the
  report:** arguments are short and not news, so absolute scores flatter every model; use them
  to rank configurations, not as "accuracy on newspapers".
- **Stance quality** on the owner's 10–20 corrected articles: agreement on stance among
  values both agree are present, plus missed and spurious values. Small-n; reported with
  counts, not just rates.
- **Cross-language consistency** (parent spec step 4): macro-F1 on the parallel English and
  Greek-proxy texts and the gap between them, per configuration.
- **Stance vs ValueEval labels** (builder's call): Touché23 labels presence only, so it
  measures value detection; stance is measured on the owner set. This closes the
  open item framework-decision §3 left for this task.
- **Decision rule** (builder's call): Touché23 macro-F1 (English and Greek proxy) ranks the
  configurations; the owner set is a gate — a configuration whose stance agreement on the
  owner set is clearly worse than the best is dropped; among the rest, prefer the cheapest
  within 0.02 macro-F1 of the best. 20 articles cannot rank 8 configurations on stance alone.
- **Cost** per 1,000 articles and latency per configuration.
- **Grid**: Haiku 5.5 (low, medium), Sonnet 5.5 (low, medium, high), Opus 5.5 (low, medium,
  high), at article level, tagging at `leaf19`, scored at `basic10`. Extra dimensions on two
  configurations (Sonnet medium, Opus medium): tag directly at `basic10`; few-shot on vs off.
  The baseline runs once. All within the $50 cap.
- Output: `docs/research/tagging-evaluation.md` — table of configurations × metrics, and a
  recommendation. **The owner decides.**

### 5.7 Review page
Local server (`python -m semval review --run <run id>`), serving one page per article from
run files + the raw cache. Layout A; underline highlights with a stable colour per value id;
tag table rows link to their spans; verdict buttons; "+ add missed value" lists the
`TargetSet`; notes; autosave per action to `data/labels/<labeller>/<run id>.jsonl` (git-ignored, never
committed: notes can quote article text).
Framework-agnostic: value names and definitions come from the `TargetSet`.

## 6. Constraints

- Python ≥ 3.11, pydantic v2, ruff, pytest, type hints; `Enum`/`Literal` for reused strings;
  small focused modules; config-driven selection; no framework- or source-specific logic in
  shared code.
- Source-use rule and ingestion rules of the parent spec §3; raw text never committed.
- Touché23-ValueEval's Hugging Face repo uses a loading script (arbitrary code). Download the
  raw data files directly into their own git-ignored folder and parse them with our own code;
  never run the dataset's script (`trust_remote_code`).
- Touché23-ValueEval: CC BY 4.0 — attribute in docs and any committed examples. Texts cached
  locally; only examples and ids committed.
- Budget: ≤ $50 for this plan's experiments (hard cap in config), inside the $300 slice cap.
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

### 6.1 Housekeeping carried in (first task)
From the v0-foundations final whole-branch review (findings recorded in the parent spec's commits and this list; the review itself was a session artefact): framework roll-ups as data (19→10, validation
variant); source schema — `restricted` access value (usable: no), `year_start_basis` and
`year_end_basis` (`verified` / `window` / `observed` / `unknown`), slug-id and ISO 639-1
language checks; duplicate `opposes` entries rejected; schwartz19 shape test; childless-group
leaf rule documented (`Framework.leaves()` currently treats a group with no children as a leaf; make that explicit and tested). Re-classify affected registry rows (reading-room archives →
`restricted`; year bases from existing notes, no new research).

### 6.2 Backlog document
Create `docs/backlog.md`, organised by area (Methods, Sources, Data schema, Legal, Analysis,
Extensions). Seed it with: three-way method comparison (b); ValueEval'24 (Greek + news test set; Zenodo access request drafted 2026-11-19); Greek few-shot from owner-corrected articles; Kiesel et al. 2022 54-value taxonomy as a definitions source; MFT lens; translation toggle in
review; browser checks for blocked publishers (DPG, Rossel, Mediafin, Roularta, Le Monde,
Telegraph …); Télé-Loisirs; forum classification of AgoraVox/GeenStijl; GR 1984–1996; NL
1940–1989 Delpher free part; EU Art. 3 via university partner; Hawkes needs article
timestamps; ESS Round-12 series break; ESS scoring key to verify (`ipbhprp`); Eastern
Europe; Balkans; 1880–1940. Every later deferral is added here.

## 7. Order of work

1. Housekeeping (§6.1) + backlog doc (§6.2).
2. Core types, framework levels/roll-ups, merge.
3. Sampler + GR/GB adapters; collect the sample.
4. Tagger interface, `ClaudeTagger`, `LexiconTagger`, run manifests, cost ledger.
5. Review page.
6. **Checkpoint with owner:** tag ~20 sample articles (builder's call: 10 GR + 10 GB) with one
   mid configuration (Sonnet 5.5, medium); owner corrects them in the review page; **revisit
   the unit decision on this data.** If the unit changes (builder's call): the grid runs at
   the new unit and merges to article level for the owner-set comparison; Touché23 is always
   compared at argument level; the $50 cap holds, so the grid shrinks (drop low-value cells)
   rather than the cap growing.
7. Load Touché23; build the Greek proxy subset; select few-shot examples from train/validation;
   owner confirms their stance in the review page.
8. Evaluation grid on Touché23 (+ Greek proxy) + owner set; **blind second pass** by the owner on the pooled
   new tags; `tagging-evaluation.md`; owner picks the method.

## 8. Left to the builder

- Exact prompt wording and output schema details (within §5.3).
- Storage formats (JSONL vs Parquet) for runs and labels.
- Web stack for the review page (stdlib/FastAPI + plain JS), as long as it stays local.
- Which three sources per country the sampler uses first, given what parses cleanly.
- Sample sizes within the stated ranges.
