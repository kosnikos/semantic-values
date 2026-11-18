# Semantic Values — Project Design (v0)

Date: 2026-11-18
Status: approved 2026-11-18

## 1. Intent

Measure how **societal values** (what ordinary people care about, not what governments
officially say) change **over time** and **between countries**, and how values **spread from
country to country**. Derive values from large collections of everyday text (newspapers,
books, online posts), and publish the findings as **blog posts**: rigorous enough to survive a
sceptical reader, not aimed at peer review.

The owner is mathematically trained; the spreading analysis is where advanced modelling
(Hawkes processes, hidden Markov models, VAR/Granger, change-point detection) is expected and
welcome.

## 2. Goals, non-goals, anti-goals

**Goals**
- Country-level value time series for the v0 countries, from full text.
- Charts that each make one clear point (trend, country comparison, lead/lag between countries).
- A credibility check: text-derived trends compared with European Values Study / World Values
  Survey results for at least a few countries.
- Spread models across neighbouring countries.
- A public, reproducible repo: readers can see how every number was made.

**Non-goals**
- Peer-review-grade statistics.
- Causal claims ("X caused Y"). Statistical lead/lag and diffusion models are in scope;
  causal language is not.
- Language-area or continent-level analysis as the primary unit.

**Anti-goals (would make it a failure even if it "works")**
- Measuring official/government voice (speeches, manifestos, state press) and presenting it
  as society's values.
- A home-made value list with no grounding in the literature.
- Publishing copyrighted text in the public repo.
- Charts whose differences come from changes in sources, OCR quality or sampling rather than
  from values, without saying so.

## 3. Decisions made so far

| Topic | Decision |
|---|---|
| Unit of region | **Country**, assigned by place of publication, not language. |
| Whose values | Society's: newspapers, books, online posts. Not speeches/manifestos. |
| v0 countries | France, Netherlands, Belgium, Luxembourg, Germany, Austria, Switzerland, Italy, Greece, Spain, Portugal, **United Kingdom** (added as thin-slice country). |
| Extensions | 1st: Eastern Europe (key story: the post-1990 shift). 2nd: Balkans. |
| Time | Full text as far back as possible over time, but **v0 focus is recent**: 1940–now, with 2005–now as the first target period. 1880–1940 legacy archives are later work. |
| Sources | Use free (non-paywalled) archives, including national libraries and individual newspapers' own archives. |
| Value framework | Not fixed. Chosen by an internal comparison (step 2) of Schwartz, Moral Foundations Theory, Inglehart–Welzel, Hofstede/Rokeach. Overlapping (multi-label) values are expected to be allowed; the comparison confirms. |
| Output | Blog posts with charts. |
| Repo | Public GitHub repo (GitHub Free allows unlimited private repos, so public is a choice, not a constraint). |
| v0 storage | Commit **references** (source, URL/ID, date, country, language) and **extracted values**. Raw text is cached locally and git-ignored. No database in v0. |
| Work order | Approach C (hybrid), below. |
| What a value score means | **Stance, not just mention.** Each text is tagged per value as endorsed / rejected / neutral-mention. Salience (mentioned at all) is recorded too, at no extra cost, but the headline measure is endorsement, which is what EVS/WVS also measure. |
| Text genres | **Newspapers (and similar edited publications) are the core source.** Within them prefer opinion pieces, columns, letters to the editor, editorials; news reports are second tier, tagged by genre and analysed separately. **Forums/comments/Reddit are out of scope for v0** (owner, 2026-11-18: "random opinions", not what we need). |
| Timescale | **Years are the primary unit** (values move slowly). Thin slice uses 2005–now; **1940–2005 sources come immediately after** the thin slice, since yearly spread models need longer series. Monthly series may be computed but are secondary. |
| Budget | **$300 cap for the thin slice** (tagging + translation API costs). Measure actual cost per 1k texts and revisit before scaling. |
| Hand labelling | Owner reads **English and Greek**. The model tags first; the owner corrects **10–20 examples** (Greek originals, other languages via English translation). |
| v0 "done" (builder's call) | Steps 1–5 complete (repo, literature + framework, archive survey, tagging method, thin slice incl. early survey check) **and the first blog post published**. Steps 6+ are v1. |
| Online posts (builder's call) | Only sources attributable to one country: national-domain sites, national forums, national subreddits. Global platforms without a country signal are out of scope (they would create artificial cross-country links). |
| Publishing tags (builder's call) | Public repo holds per-text reference + URL + tags, unless a source's terms forbid it; then only aggregates for that source. Why: outside readers can audit any data point and re-run aggregation/models without paying to re-tag. Owner may switch to aggregates-only. |
| Source-use rule (owner, 2026-11-18) | **EU:** a source is usable unless its terms or a valid Art. 4(3) reservation forbid *any* automated analysis/TDM, or forbid any reuse without licence (e.g. Le Figaro). AI-training-only bans and robots.txt AI-crawler blocks do not exclude a source. **UK:** CDPA s.29A (non-commercial research TDM; contract terms restricting it are unenforceable) makes UK sources with lawful (free) access usable, on conditions: blog stays non-commercial; use free public websites, not contract-bound APIs; never transfer copies to others (whether sending text to a third-party LLM API counts is decided in the tagging plan — options: local model or zero-retention API); acknowledge sources. **Everywhere:** obey robots.txt rules that apply to our own crawler, polite rate limits, honest user-agent, no circumvention of anti-bot or access controls. |
| Third-party APIs | **Open.** Step 3 records, per source, whether terms allow sending text to commercial LLM/translation APIs. Owner decides once the survey shows how much this constrains us. |

## 4. Approaches considered (work order)

- **A. Research first.** Finish all literature and archive research before any code.
  Trade-off: no wasted building, but weeks before any chart, and some questions (OCR quality,
  whether LLM tagging works on a given language/era) are only answered by trying.
- **B. Thin slice first.** One end-to-end pipeline immediately. Trade-off: fast feedback, but
  the value framework would be chosen before it's debated, risking re-tagging.
- **C. Hybrid. Chosen.** Run the framework comparison and the archive survey in parallel
  (desk research), then build one thin slice on recent data, then widen. Gets the
  framework right before tagging at scale, and real feedback soon after.

## 5. Work order

1. **Repo setup.** Public repo, README, licence, git-ignored text cache, `docs/research/`.
2. **Literature review and framework decision.** Prior work (Schwartz and refined 19-value
   theory, Moral Foundations / MFD / eMFD, Inglehart–Welzel, Hofstede, Rokeach, Touché
   ValueEval 2022–23, culturomics/Ngram studies, "historical psychology"). Compare frameworks
   on: detectable in text, multi-label support, readability for blog readers, availability of
   survey data for validation (EVS/WVS item mapping), cross-language applicability.
   **Output:** `docs/research/literature-review.md` and a framework decision memo with the
   final value list and definitions.
3. **Archive survey (per country).** For each v0 country (then Eastern Europe), list national
   library portals, individual newspapers' own archives, web archives and forum/online
   sources. Record: free vs paywalled, years covered, languages, API/bulk download, licence and
   terms of use, text-and-data-mining opt-outs, OCR/text quality, rough volume.
   Prioritise 2005–now, then 1940–2005. Candidates to verify (hypotheses, not facts):
   Arquivo.pt (Portuguese web archive, has an API), Common Crawl News, Internet Archive,
   GDELT (as a URL index), Der Spiegel and Die Zeit free archives, La Stampa archive, Delpher,
   Gallica, ANNO, national Greek newspaper archives, Reddit/forum dumps.
   **Output:** `docs/research/sources.md` with one table per country plus a coverage matrix
   (country × period × source type).
4. **Value-tagging method.** Using the chosen framework, compare (a) LLM tagging,
   (b) translated value dictionaries, (c) a classifier trained on ValueEval data.
   Quantitative comparison uses the public ValueEval labelled data (builder's call: 10–20
   owner corrections are too few to rank methods on their own). The owner's 10–20 corrected
   examples (Greek and English originals) are the sanity check for stance tagging
   and for the target languages. Measure agreement, cost per 1k texts, and cross-language
   consistency. **Output:** method decision, stance-tagging prompt/spec, cost estimate.
5. **Thin slice.** **Greece + United Kingdom**, 2005–now, yearly resolution, opinion-type
   genres preferred. Chosen so the owner can correct tags on originals (Greek, English).
   Not neighbours, so the slice tests the pipeline and survey check, not spreading.
   UK candidates to verify: Guardian Open Platform API (full text since ~1999), national
   subreddits/forums; British Newspaper Archive is paywalled. Ingest → sample N texts per country-year → tag →
   aggregate → time series → one chart. Stay under the $300 cap; record actual costs.
   **Early survey check (builder's call):** compare against EVS/WVS for both countries
   before scaling. On mismatch: investigate (genre mix, tagging, source bias) before
   step 6; if the mismatch is understood, it can become a blog finding.
   Learn about OCR/noise, de-duplication, source mix and cost.
6. **Extend back to 1940–2005** for the thin-slice countries, then **scale to all v0
   countries**.
7. **Full survey check.** Compare text-derived trends with EVS/WVS waves (1981+) for all
   countries where both exist.
8. **Spread models.** Change-point detection, VAR/Granger, Hawkes processes across countries,
   hidden Markov "value regimes".
9. **Blog posts.**
10. **Extensions.** Eastern Europe, then Balkans.

Steps 2 and 3 run in parallel. Step 4 depends on 2. Step 5 depends on 3 and 4.

## 6. Constraints and known risks

- **Copyright and terms of use.** Post-1940 text is mostly in copyright. Use only sources
  that are free to read; respect ToS, robots.txt and EU text-and-data-mining opt-outs
  (DSM Directive Art. 4). Never commit raw text to the public repo.
- **Coverage gaps.** Free full text is expected to be thin for ~1950–1990 and richer after
  ~2005 (web). Different periods will likely use different source types; any join across
  source types must be flagged in charts and handled (e.g. per-source normalisation,
  overlap periods).
- **Source mix drives artefacts.** Value shares must be normalised per source and compared
  within consistent source mixes, otherwise a change in archive looks like a change in values.
- **Multilingual.** v0 spans ~9 languages (FR, NL, DE, LB, IT, EL, ES, PT, plus EN online).
  Tagging must be consistent across languages; step 4 measures this.
- **Eastern Europe 1945–1989.** State-controlled press is the "official voice" this project
  avoids. The extension needs a dedicated source strategy (post-1990 press and web,
  literature, letters, émigré press) and careful before/after comparison.
- **Sampling.** We sample texts per country-period rather than tagging whole archives, to
  control cost. Sample sizes must give stable estimates; the builder sizes this in step 5.

## 7. Left to the builder

- Language and tooling (Python is the presumed default), file formats for references and
  tags (e.g. Parquet/CSV), project layout.
- Sampling scheme and sample sizes.
- Which LLM and prompts (if LLM tagging wins in step 4).
- Chart tooling and blog platform.
- Exact choice of the thin-slice country pair, given the step-3 results.
