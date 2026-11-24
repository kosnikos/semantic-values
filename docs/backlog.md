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
