# Framework decision memo: which value framework to tag with

Date: 2026-11-18 · Task 7 of the v0 foundations research · Builds on
[`literature-review.md`](literature-review.md) (Task 6)

This memo compares six candidate frameworks on the criteria the plan sets, answers two
questions the owner raised early (may values overlap? how does "endorse/reject" relate to
existing labels?), names a survey validation target, and describes how the value registry
(`src/semval/values.py`, `data/framework/*.yaml`) encodes the result. It ends with a
**recommendation**. The owner makes the decision at the next checkpoint.

**Citations.** `[Rn]` refers to the reference list of the literature review. Four sources
were opened for this memo and are listed at the end as `[Dn]`. Where I mark something
*interpretation*, it is my reading, not a finding of the cited work.

---

## 1. Comparison

Criteria from the plan. "v0 languages" are FR, NL, DE, LB, IT, EL, ES, PT and EN (spec,
"Multilingual"). Ratings (good / partial / poor) are my summary of the cited facts.

| Criterion | Schwartz 10 (1992) | Schwartz 19 (2012) | MFT (5/6 foundations) | Inglehart–Welzel | Hofstede | Rokeach (RVS) |
|---|---|---|---|---|---|---|
| **Detectable in short texts** | good: Schwartz-based dictionaries for text exist (PVD [R17]; newspaper value lexicon [R18]); ValueEval labels collapse to 10 (*interpretation*, [D2] p. 665: 19 values recombine into the 10) | good but hard: ValueEval'23/'24 use these labels; best macro-F1 0.56 per argument [R20], 0.39 per sentence [R22] | good: dictionaries (MFD, MFD 2.0, eMFD) [R4, R6, R7]; eMFD built on US news [R7] | poor: no text dataset or dictionary found [R14 / review §1.3]; several indicators are states or behaviours, not stances (*interpretation*) | poor: no text resources found; dimensions describe national cultures, not individuals' values [R15] | poor: no text resources found [review §1.5] |
| **Multiple values per text** | yes: theory says any attitude or action involves several values at once ([D1] p. 262, feature 6) | yes: ValueEval annotates many values per text [R20, R22] | yes: MFTC/MFRC are multi-label [R9, R10] | n/a: two continuous country-level axes | n/a | no: forced ranking of 18+18 values [R16, review §1.5] |
| **Endorse/reject stance** | partial: no stance labels at 10 | partial: ValueEval'24 has *attained/constrained*, not *endorsed/rejected* [R22; review §2.3]; see §3 | partial: virtue/vice poles, which mark the act discussed, not the author's stance (*interpretation*, review §1.2) | poor | poor | poor |
| **Readable to blog readers** | good | fair: some sub-values ("power: resources", "conformity: interpersonal") need a gloss (review §1.1) | good | good (two axes) | fair | fair |
| **Survey item mapping (ESS/EVS/WVS)** | good: ESS 21-item PVQ in every round 2002–2023/24 [R44, R45]; WVS w5–6 10-item version [R52, R53]; none found in WVS-7 (one data dictionary, not the master questionnaire) [R55] | good, via the 10: ESS items can be assigned to sub-values (§4), but the ESS scores only the 10 | none: no MFQ items in EVS/WVS/ESS (WVS-7 checked; EVS not itemised) [review §1.2] | perfect: defined by EVS/WVS items [R14] | none | none |
| **Works across v0 languages** | via LLM tagging (GPT effective in 12 languages [R25]) and ESS translations | ValueEval'24 has 6 of 9 v0 languages (DE, EL, EN, FR, IT, NL); none for ES, PT, LB [R22] | translated, validated MFD for FR, DE, IT, ES only; none found for EL, PT, NL [R11] | n/a (survey-only) | n/a | n/a |
| **Existing labelled data** | via collapsing the 19-value data (*interpretation*) | ValueEval'23: ≈9.3k EN arguments, CC BY 4.0 [R20, R21]; ValueEval'24: 2,648 news/manifesto texts, 9 languages, α = 0.546, redistribution forbidden [R22, R24] | MFTC 35k tweets [R9]; MFRC 16k Reddit comments [R10]; eMFD 1,010 US news articles [R7] — all English | none found | none found | none found |

**Caveats carried forward from the review.**
- The WVS-7 "no Schwartz battery" finding rests on one national data dictionary (Czechia
  2022) and was not checked against the master questionnaire [R55].
- The ESS country × round table in review §5.1 comes partly from Wikipedia [R64]; only
  Rounds 7 and 8 were cross-checked against ESS documents [R65, R66]. Task 8 should confirm
  it in the ESS Data Portal.
- The ESS Human Values Scale changes from Round 12 (2025–26): new 20-item version, new
  time series [R62]. The usable PVQ-21 series is Rounds 1–11.
- ValueEval'24 agreement varies by language, from α = 0.367 (DE) to 0.696 (EL) [R22].

**A note on Hofstede, Rokeach and Inglehart.** When designing the ESS values module,
Schwartz judged all three unsuitable or less than optimal as survey instruments: Hofstede's dimensions discriminate
nations, not persons, and mostly concern work values; Rokeach's ranking leaves out
tradition and power values and is long; Inglehart's materialism items are sensitive to
current economic conditions ([D1] pp. 264–265). These are the same weaknesses for our
purpose (per-text, per-year, stance). The source is the author of the rival theory, so
read it as a reasoned argument, not an independent test.

## 2. Do values overlap, or are they mutually exclusive?

**They overlap, and the tagging must be multi-label.** The literature is consistent on this:

- **Theory.** Schwartz states that any attitude or behaviour typically has implications for
  several values at once; action follows from the *trade-off* among them ([D1] p. 262).
  Values sit on a circle: the closer two values are, the more compatible their motivations;
  the more distant, the more they conflict ([D1] pp. 268–269; [D4] PDF p. 4).
- **The circle is a continuum, not a set of boxes.** The refined theory is explicitly built
  on the idea that values form "a circular motivational continuum", which the 19 values
  partition more finely than the 10; boundaries are fuzzy, and items often express parts of
  adjacent values ([D2] pp. 663–664, 668). Adjacent values can be recombined into the 10,
  the four higher-order values, or two halves ([D2] p. 665).
- **Practice.** All labelled corpora annotate several values per text: ValueEval [R20, R22]
  and MFTC/MFRC [R9, R10].

So there is no "vertical" (one value per text) constraint. A single op-ed can endorse
`universalism_concern` and `security_societal` at once, and often will, because opinion
writing is about trade-offs.

**What the opposition structure means — and does not mean.** Schwartz names two bipolar
dimensions: self-enhancement (power, achievement) vs self-transcendence (universalism,
benevolence), and openness to change (self-direction, stimulation) vs conservation
(security, conformity, tradition). Hedonism shares elements of openness and
self-enhancement ([D1] p. 269; [D2] p. 669). Two cautions:
- Visually opposite values are "likely to be antagonistic" but not necessarily the most
  strongly in conflict, because distances around the circle may be unequal ([D2] p. 669,
  footnote 9).
- Conflict in the theory need not show up as a negative correlation. In ESS, WVS and SVS
  data, openness correlated *positively* with self-enhancement and conservation with
  self-transcendence on average, and the pattern varied by country (Rudnev, Magun &
  Schwartz 2018, as summarised in [D4] PDF p. 15).

**How the registry encodes this.**
- `opposes` records the theory's oppositions as data. It is a description, not a
  constraint: the tagger may mark opposing values in the same text, and analysis may use
  `opposes` to check expected trade-offs (e.g. does endorsement of one rise as the other
  falls?), treating it as a hypothesis to test, not an assumption.
- `parent` records the higher-order group, so results can be reported at 19, or rolled up
  to 4 groups for blog readers.
- `load_framework` checks that every reference resolves, that `opposes` is symmetric and
  never self-referential, and that `parent` has no cycles. It places no limit on how many
  values one text may carry.

## 3. Endorse/reject versus ValueEval's attained/constrained

**The gap.** ValueEval'24 asks whether a sentence describes something that *attains* or
*constrains* a value [R22, R23]. Our spec asks whether the *author endorses or rejects* the
value. These differ (review §2.3): "the new law tramples press freedom" *constrains*
self-direction while the author *endorses* it. The ValueEval polarity F1 of 0.83 [R22] is
therefore not an estimate of our stance accuracy.

**How the chosen definitions support stance tagging.**
- Each Schwartz value is defined as a *motivational goal* ([D2] Table 2). A goal can be
  wanted or disowned, so "does the author treat this goal as worth pursuing?" is a
  well-posed question for every value. (*Interpretation.*)
- Each tag-able value carries `examples_endorse` and `examples_reject`: short
  opinion-style sentences written for this project. Several endorse examples deliberately
  describe a value being *constrained* while the author defends it (e.g. under
  `self_direction_thought`: "The ministry's plan to vet university syllabuses is an attack
  on free inquiry"), so prompts and annotators see the difference from attained/constrained
  directly.
- Mapping ValueEval'24 data onto our stance needs an extra step or a re-annotation layer
  (review §2.3). Task 4 will define that step; this memo only notes that ValueEval'24 labels the
  same 19 Schwartz values [R22], so the value dimension needs no mapping, only the stance
  dimension does.

## 4. Validation target and survey items

**Target: the ESS Human Values Scale (21-item PVQ), Rounds 1–11 (2002–2023/24).** It is
the only per-round, cross-national Schwartz measure [R44, R45, R61]. Compare within-country
change and rank order, not levels, because only partial scalar invariance holds [R61].
WVS waves 5–6 add a few points for six v0 countries [R52]. Inglehart–Welzel remains the
natural frame for EVS/WVS, possibly via a post-hoc mapping from Schwartz scores (review
§1.6; untested).

**What `survey_items` contains.**
- **ESS codes only**, with an `ESS:` prefix. The 21 variable names (`ipcrtiv`, `imprich`,
  …, `impfun`) and their labels were read from the ESS Round 4 data dictionary [D3]. Their
  order matches the final 21-item questionnaire printed in [D1] (pp. 313–314), and [D1]
  Table 6 gives each item's basic value (pp. 284–286).
- **Assignment to the 19 sub-values** follows Schwartz et al. (2012), which classifies the
  corresponding PVQ items: new ideas/creative → thought; own decisions → action; rich →
  resources; secure surroundings → personal security; country safe from threats → societal
  security; follow rules and behave properly → conformity: rules; humble/don't draw
  attention → humility; customs/religion → tradition; help people → caring; equal
  opportunity → concern; listen to different people → tolerance; care for environment →
  nature ([D2] pp. 665–668). The ESS wordings differ slightly from the PVQ-40 items the paper
  discusses; matching them is my reading.
- **Three items need care:**
  - `iprspot` ("get respect from others … wants people to do what he says") is filed under
    `power_dominance`, but its first half is closer to `face`.
  - `iplylfr` (loyal to friends, devoted to close people) is listed under both benevolence
    values, because the paper says this item mixes caring and dependability ([D2] p. 667).
  - `ipmodst` fills item slot 9, a *tradition* item in the ESS's 10-value design ([D1]
    Table 6; the final wording, "humble and modest", replaced the proposed one, pp. 285,
    313), but it is *humility* in the refined theory ([D2] p. 667).
- **Empty lists, on purpose.** `face` and `conformity_interpersonal` have no ESS item ([D2]
  p. 666: "No PVQ items tapped face"; the PVQ politeness items are not in the ESS-21). The
  four higher-order groups carry none, because they are scored from their members.
- **No WVS codes.** The review gives V70–V79 as the WVS-6 battery [R53] but not the
  item-to-value assignment, and I did not open a source that gives it. I left WVS codes out
  rather than guess. **No EVS codes**: no Schwartz battery was found in EVS (review §5.3).
- **Validation scores at the 10-value level.** The ESS measures the 10 basic values, so
  validation rolls our 19 up to 10 and compares against ESS 10-value scores. The exact
  rule follows.

### Validation roll-up

- **Survey side: unchanged.** ESS 10-value scores are computed with the official ESS
  scoring key, which assigns each item to one basic value as in [D1] Table 6. So
  `ipmodst` + `imptrad` = tradition, and `ipfrule` + `ipbhprp` = conformity.
- **Text side, for validation only:** our 19 values roll up to the 10 so that each text
  value lands where its ESS item lands:
  - `humility` → **tradition**, matching the ESS's scoring of `ipmodst`;
  - `face` → security (it has no ESS item, so this choice cannot cause a mismatch);
  - every other sub-value → the basic value named in its id (e.g. `power_dominance` →
    power, `universalism_nature` → universalism). Hedonism, stimulation, achievement and
    tradition map to themselves.
- **Blog charts and other roll-ups** keep humility → conformity, following Schwartz et al.
  ([D2] p. 675), which is also why `humility` has `parent: conservation` in the registry.
  Both tradition and conformity belong to conservation, so the 4-group view is the same
  under either rule.
- **Both roll-ups are encoded as data** in the `levels` of `schwartz19.yaml` (see §5):
  `basic10` (humility → conformity) and `basic10_validation` (same 10 targets, humility →
  tradition). The values themselves (definitions, `parent`) are unchanged by the choice;
  validation code picks the `basic10_validation` level by name. Validation charts and posts
  should state which roll-up they use.

## 5. How the registry represents the framework

- **One file per framework**, `data/framework/<id>.yaml`, holding `id`, `name`, `citation`,
  `values` and, optionally, `levels`. `values.py` contains no framework names. A second framework (e.g. MFT as a
  robustness lens) is a second YAML file, and both load side by side
  (`test_two_frameworks_coexist`).
- **Higher-order groups are values too.** `openness_to_change`, `self_enhancement`,
  `conservation` and `self_transcendence` are `ValueDef`s with `parent: null`, a
  definition, `opposes` (each other, pairwise), and no examples or survey items. This keeps
  "`parent` must resolve to an id in the same file" a single uniform rule.
  `Framework.groups()` returns values that some other value names as parent;
  `Framework.leaves()` returns the 19 tag-able values. Examples are required (by test) for
  leaves only.
- **Border values get one parent.** The source places three values on a border:
  hedonism (openness / self-enhancement), face (power / security) and humility
  (conservation / self-transcendence) ([D2] pp. 669–670). `parent` holds one id, so:
  hedonism → `openness_to_change` (the paper puts it in the growth sector with openness, and
  it is closer to openness in about two thirds of samples, [D2] p. 669); face and humility →
  `conservation` (the paper finds it best to treat face as security and humility as
  conformity when recombining into the 10, [D2] p. 675). Each definition says that the value
  is a border value.
- **Value-level `opposes`** is the two dimensions as Schwartz states them for the 10
  ([D1] p. 269), carried down to the sub-values: self-direction (both) and stimulation
  oppose security (both), tradition and conformity (both); achievement and power (both)
  oppose universalism (all three) and benevolence (both). Lists put the strongest stated
  conflict first where the paper names one (thought ↔ tradition; action ↔ conformity: rules,
  [D2] p. 669). The three border values have no value-level opposite: the source names
  none, and their opposition is carried by their group.
- **Definitions** are short paraphrases of [D2] Table 2, written for blog readers; the
  framework `citation` attributes them.
- **Levels and roll-ups are data.** Besides the built-in level `leaf` (the 19 leaves), the
  file declares named `levels`, each with its targets and a `map` that sends every leaf to
  exactly one target (checked on load):
  - `basic10`: the 10 basic values, with their own plain-English definitions and examples.
    Sub-values map to the basic value named in their id (e.g. `power_dominance` → power);
    face → security and humility → conformity ([D2] p. 675).
  - `basic10_validation`: reuses the `basic10` targets (`targets_from`); humility →
    tradition, the validation roll-up of §4.
  - `group4`: the 4 higher-order groups, using their own `ValueDef`s as targets
    (`value_targets`); each leaf maps to its `parent`.

  A tagger only sees a `TargetSet` built from one level (`Framework.target_set`), and
  `Framework.rollup_map` gives the leaf → target map. A new level or another framework's
  levels need only YAML.

## 6. Open points for the owner

1. **Granularity: 19 or 10?** Tagging at 19 matches the ValueEval'24 benchmark and keeps
   distinctions that matter in news (e.g. societal vs personal security, which predicted
   attitudes to immigration differently in [D2] p. 665). But agreement and accuracy fall
   as label sets grow (54 values: α = 0.49 [R19]; 19 values per sentence: F1 0.39 [R22]).
   `parent` maps the 19 directly to the 4 groups, so nothing is lost by tagging at 19 and
   reporting at 4; the cost is tagging difficulty. The 19 → 10 roll-up is encoded as data in
   the `levels` of `schwartz19.yaml` (§5).
2. **Benevolence: dependability is the weakest value.** The paper itself notes little
   prior evidence for it ([D2] p. 670). Watch its agreement in Task 4.
3. **ES, PT and LB have no ValueEval'24 data** [R22]. Cross-language consistency for these
   must come from Task 4's own checks.
4. **MFT as a second lens** would be a second YAML file. It is cheap to add later but has no
   survey target.

## Recommendation

**Adopt Schwartz's refined theory (19 values, `data/framework/schwartz19.yaml`) as the
v0 framework, with results rolled up to the 10 basic values and the 4 higher-order groups
for validation and for blog readers.**

Reasons, in order of weight:
1. It is the only framework with all three things this project needs: multilingual,
   news-text labels covering six v0 languages including Greek [R22]; a stance-like label
   to build on [R22]; and a per-round, cross-national survey target, the ESS Human Values
   Scale, 2002–2023/24 [R44, R45] (review §1.6).
2. It is multi-label by design, and its circle gives a principled, testable account of
   which values conflict, encoded as `opposes` (§2).
3. Its values are motivational goals, so endorse/reject is well posed for every value; the
   examples in the registry make the difference from attained/constrained explicit (§3).
4. It nests: 19 → 10 → 4, which serves blog readability and ESS validation without
   re-tagging (§4, §5). In the registry, the 19 → 10 and 19 → 4 roll-ups (and the
   validation variant) are encoded as data in `levels` (§5).

**Runner-up: Moral Foundations Theory**, as a secondary lens or robustness check. It has the
best dictionary resources, including translated MFDs for FR, DE, IT and ES [R11], and good
readability, but no survey validation target and only English labelled data [R7, R9, R10].
**Inglehart–Welzel** is the validation *frame* for EVS/WVS rather than a tagging scheme.
**Hofstede and Rokeach** are set aside (§1).

**Overlap rule:** values are multi-label. Each text gets endorse / reject / neutral per
value, any number of values per text, including opposing ones; opposing pairs are recorded
in `opposes` for analysis, not enforced at tagging time.

---

## Sources opened for this memo

- [D1] Schwartz, S. H. (n.d., c. 2001–2002). Chapter 7: A proposal for measuring value
  orientations across nations. In *ESS Core Questionnaire Development* (pp. 259–319).
  European Social Survey. https://www.europeansocialsurvey.org/sites/default/files/2023-06/ESS_core_questionnaire_human_values.pdf
  (full text; page numbers are the printed ones)
- [D2] Schwartz, S. H., Cieciuch, J., Vecchione, M., Davidov, E., Fischer, R., Beierlein,
  C., et al. (2012). Refining the theory of basic individual values. *JPSP* 103(4), 663–688.
  https://doi.org/10.1037/a0029393 (= [R3]; full text read from the institutional copy at
  https://avesis.tedu.edu.tr/yayin/5030e84d-d374-42d4-a46c-b6f7b2d08457/refining-the-theory-of-basic-individual-values/document.pdf)
- [D3] IHSN Data Catalog. European Social Survey 2008, Round 4 (ECA_2008_ESS-R4_v01_M),
  data dictionary, file ESS4e04_5, human values variables `ipcrtiv` … `impfun`.
  https://datacatalog.ihsn.org/catalog/8935/data-dictionary/F1/?offset=600
- [D4] European Social Survey (n.d., c. 2021). *The Human Values Scale: Findings from the
  European Social Survey* (booklet; = [R45]). Schwartz's introduction (PDF p. 4) and the
  summary of Rudnev, Magun & Schwartz (2018) (PDF p. 15).
  https://www.europeansocialsurvey.org/sites/default/files/2023-06/ESS_Findings_HVS.pdf
  (full text; the booklet prints two pages per PDF page, so PDF page numbers are given)

## Decision

Owner, 2026-11-19: **approved**. Schwartz refined theory (19 values, `data/framework/schwartz19.yaml`), rolled up to 10 basic values and 4 higher-order groups for reporting. Values overlap, so tagging is multi-label. Validation is against ESS PVQ-21 using the validation roll-up in §4. Moral Foundations Theory stays an optional secondary lens for later.

---

## Official definitions

Added 2026-11-19 (tagging-method plan, Task 3). The tagger should judge texts against the
sources' own definitions, not our paraphrases. Our `definition` fields stay as they are,
for the review page and the blog. Each `official` block records where the source's
definition is (`citation`, `page`) and, where the licence allows, the verbatim `text`.

### What each source says, and what its licence allows

| Source | What it defines | Licence or copyright, as found | Decision |
|---|---|---|---|
| Schwartz et al. (2012), JPSP [D2] | **Table 2, p. 669**: the 19 values, "each defined in terms of its motivational goal". **Table 1, p. 664**, column 2: the 10 basic values; the table note says they are "adapted from" Schwartz (1994), *Journal of Social Issues* 50, p. 22, © 1994 John Wiley & Sons | © 2012 American Psychological Association (printed on p. 663 of the copy opened, [D2]). APA's policy [D5] lists "tables, figures" among uses that **require permission**, and exempts only "single text extracts of 400 words or fewer" with attribution | **`local_only`** for all 29 texts (19 leaves from Table 2, 10 `basic10` targets from Table 1) |
| Schwartz (2012), ORPC 2(1) [D6] | The 10 basic values (overview paper) | **CC BY-NC-ND 3.0**, stated on the ScholarWorks@GVSU article page [D6]. The site footer also says "Copyright © 2011 International Association for Cross-Cultural Psychology. All Rights Reserved"; I read that as the journal's copyright notice, with the article-level CC licence granting reuse | **Not used**: the full text could not be opened (see below) |
| Kiesel et al. (2022), ACL [D7] | No definitions in the paper itself: Table 1 (p. 4462) lists the 54 Level-1 values (e.g. "Be broadminded") under their Schwartz categories; the "taxonomy description" is published with the dataset [D8] | Paper: **CC BY 4.0** ("Materials published in or after 2016 are licensed on a Creative Commons Attribution 4.0 International License", ACL Anthology page [D7]). Dataset Webis-ArgValues-22: **CC BY-NC 4.0** (Zenodo metadata [D8]) | **Documented alternative only**; nothing added to the framework file |

**Why the JPSP texts are local, not public.** The texts are short (29 noun phrases, 247
words in all), so APA's exemption for text extracts of up to 400 words might cover them.
But they are the whole content of two tables, and APA lists tables separately as needing
permission. Table 1's definitions are also third-party material (adapted from a Wiley
article), which APA says the reuser must clear. That is not explicit permission. Under
this task's rule, the verbatim texts stay out of the public repository. If the owner
wants them public, the route is a CCC Marketplace request for "Website" use [D5]. It
would need to cover both tables, and Wiley's rights for Table 1.

**Why ORPC is not used.** The ORPC article page opened and shows the CC licence. But the
PDF (`https://scholarworks.gvsu.edu/cgi/viewcontent.cgi?article=1116&context=orpc`, the
only open-access copy Semantic Scholar lists [D9]) returned HTTP 403 to automated
requests. I did not use unofficial uploads (Scribd, SlideShare), and I wrote nothing from
memory. For the 10 basic values I used Table 1 of [D2] instead: Schwartz's own conceptual
definitions of the 10, from a paper I could open. (`text: null` with `local_only: false`,
the fallback for an unopened source, is not a valid `OfficialDefinition`. Table 1 avoids
the need for it.)

**Owner action, optional:** open the ORPC PDF in a browser. If its definitions are
preferred, they can be **inline and public**. CC BY-NC-ND permits copying the work
verbatim with attribution for non-commercial purposes. A definition quoted word for word,
with citation and page, is an unmodified, attributed, non-commercial redistribution. This
holds only while the project stays non-commercial.

### What the framework file holds

- **Leaves (19):** `official: {citation: "Schwartz et al. (2012), JPSP 103(4), Table 2",
  page: "p. 669", local_only: true}`.
- **`basic10` targets (10):** citation "Schwartz et al. (2012), JPSP 103(4), Table 1,
  column 2; adapted there from Schwartz (1994), Journal of Social Issues 50, p. 22",
  page "p. 664", `local_only: true`. `basic10_validation` reuses these targets
  (`targets_from`).
- **Groups (`group4`):** no `official` (it is optional). [D2] p. 669 defines the four
  higher-order values in running text ("Openness to change values emphasize readiness
  for new ideas, actions, and experiences", and so on), so they could be added the same
  way later.
- **Local file:** `data/framework/local/schwartz19.official.yaml` (git-ignored) holds the
  29 verbatim texts, copied from [D2]. A script checked them against the PDF's extracted
  text, both as strings and as table rows (value name followed by its definition). They
  are kept exactly as printed: curly apostrophes, the em dash in self-direction, and the
  final period that Table 1 prints after hedonism only. They are noun phrases, not
  sentences.

Counts: **0 inline, 29 local-only, 0 missing.**

### How the tagger uses them (prompt-use note)

- For each target, the prompt shows the **official text when present**, with its citation
  and page, and **falls back to our `definition`** when `official.text` is `None`. In a
  fresh clone, every `local_only` block has no text, so all of them fall back.
- **Reproducibility.** All 29 texts are local-only, so a fresh clone tags with our
  paraphrases and the owner's machine tags with the official texts: the prompts differ. A
  run should record which wording each target used (official or fallback), for example
  through the prompt hash in the run manifest, so that results from the two setups are not
  pooled by mistake.
- `test_every_target_has_official_citation` loads the public file alone (`local_dir=None`)
  and checks that every leaf, `basic10` and `basic10_validation` target has an `official`
  block with a citation and page. `test_local_official_file_covers_every_local_only_target`
  checks that every one of them gets its text when the local file exists, and skips
  otherwise.

### Sources opened for this section

- [D2] as above: Table 1 p. 664, © notice p. 663, Table 2 p. 669.
- [D5] American Psychological Association. *APA copyright and permissions for scholarly
  journals and books* (page metadata: last updated 2025-05-21).
  https://www.apa.org/about/contact/copyright/. The live page served a bot-protection
  page, so I read the Internet Archive snapshot of 2026-11-11:
  https://web.archive.org/web/20261111223418/https://www.apa.org/about/contact/copyright/
- [D6] Schwartz, S. H. (2012). An overview of the Schwartz theory of basic values.
  *Online Readings in Psychology and Culture*, 2(1). https://doi.org/10.9707/2307-0919.1116,
  which resolves to the article page https://scholarworks.gvsu.edu/orpc/vol2/iss1/11/.
  The licence was read there; the PDF was not retrievable (HTTP 403).
- [D7] Kiesel, J., Alshomary, M., Handke, N., Cai, X., Wachsmuth, H., & Stein, B. (2022).
  Identifying the human values behind arguments. *Proceedings of the 60th Annual Meeting
  of the ACL (Vol. 1)*, 4459–4471. https://doi.org/10.18653/v1/2022.acl-long.306.
  Anthology page https://aclanthology.org/2022.acl-long.306/ (licence); PDF
  https://aclanthology.org/2022.acl-long.306.pdf (Table 1 and data pointer, p. 4462).
- [D8] Webis-ArgValues-22, Zenodo record 5657249 (https://doi.org/10.5281/zenodo.5657249).
  Metadata read through https://zenodo.org/api/records/5657249: licence `cc-by-nc-4.0`,
  version 2022-07-18.
- [D9] Semantic Scholar API record for doi:10.9707/2307-0919.1116,
  https://api.semanticscholar.org/graph/v1/paper/DOI:10.9707/2307-0919.1116?fields=title,openAccessPdf,externalIds.
  The only open-access PDF it lists is the GVSU one.
