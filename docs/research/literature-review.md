# Literature review: measuring societal values in European news text

Date: 2026-11-18 · Task 6 of the v0 foundations research · Feeds Task 7 (framework decision)

This review covers six areas: value frameworks, value detection in text, values over time from text,
cross-country diffusion, survey ground truth, and the gaps this project fills. Citations are numbered
[R1]…[R68]. The reference list at the end gives author(s), year, title and the DOI or URL that was opened.
Where only a DOI/catalogue record was opened (not the paper's text or abstract), the reference is marked
*(metadata only)*, and no claim beyond that record depends on it unless flagged.

**Convention.** "Found" means a paper's reported result. "Interpretation" or "for us" means my reading
for this project.

---

## 1. Value frameworks

### 1.1 Schwartz: 10 basic values (1992) and the refined 19-value theory (2012)

**What it is.** Schwartz's theory defines ten basic personal values (self-direction, stimulation,
hedonism, achievement, power, security, conformity, tradition, benevolence, universalism). They sit on a
circle ordered by compatible and conflicting motivations. The original tests covered 20 countries [R1].
The 2012 overview reports support from samples in 82 countries. It says that individuals differ a lot in
their value priorities, but most societal groups show a similar average ordering. The two main instruments
are the Schwartz Value Survey (SVS) and the Portrait Values Questionnaire (PVQ) [R2].

**Refined theory.** Schwartz et al. (2012) split the circle into **19 values**, for example
self-direction-thought vs -action, power-dominance vs -resources, security-personal vs -societal, and
benevolence-caring vs -dependability. They tested it with a new instrument (PVQ-R) in 15 samples from
10 countries (N = 6,059). Confirmatory factor analysis and multidimensional scaling separated the 19
values, and each value correlated uniquely with external variables [R3].

**Facts for Task 7's criteria.**
- *Detectable in short texts / existing labelled data:* the strongest of all frameworks. The Touché
  ValueEval datasets use the 19 values (+1, see §2) [R19, R20, R22]. A Schwartz-based dictionary exists
  (Personal Values Dictionary) [R17], and so does a Schwartz-based newspaper lexicon validated on US
  newspapers 1900–2000 [R18].
- *Multi-label:* yes by design. ValueEval annotates many values per argument or sentence [R20, R22].
- *Stance:* the ValueEval'24 data label each value reference as **attained or constrained** [R22, R23]
  (details and caveat in §2.3).
- *Survey mapping:* the ESS has carried a 21-item PVQ in every round since 2002 [R44, R45], and WVS
  waves 5–6 carry a 10-item version [R52, R53]. I found none in wave 7, based on one national data
  dictionary [R55] and not checked against the master questionnaire (§5.3).
- *Multilingual:* ValueEval'24 covers 9 languages, 6 of them v0 languages (DE, EL, EN, FR, IT, NL) [R22].
- *Readability:* the 10 values read well. Some of the 19 sub-values ("power: resources",
  "conformity: interpersonal") need a gloss for blog readers (interpretation).

### 1.2 Moral Foundations Theory (MFT) and its dictionaries

**What it is.** MFT measures moral intuitions, originally five: Harm/care, Fairness/reciprocity,
Ingroup/loyalty, Authority/respect and Purity/sanctity. Graham, Haidt & Nosek (2009) found across four
studies that liberals relied more on care and fairness, while conservatives used all five more equally.
One study used foundation words in sermons [R4]. A review chapter is [R5] *(metadata only)*. Atari et al.
(2023) revised the theory with the MFQ-2 across 25 populations. Fairness split into **equality** and
**proportionality**, giving six foundations, and the paper found that the foundations' nomological
network varies across cultures [R8].

**Dictionaries.**
- **MFD** (Graham et al. 2009) [R4].
- **MFD 2.0**: Frimer and colleagues, distributed as `mfd2.0.dic` on OSF [R6].
- **eMFD** (Hopp et al. 2021): 854 crowd annotators (557 finished) highlighted foundation content in
  1,010 US news articles from 2016–17. It gives 3,270 words, each with a probability weight and a
  VADER-based valence per foundation. A 689-word virtue/vice version also exists. Found: the eMFD
  separated partisan outlets better than MFD/MFD 2.0 and predicted share counts better. The authors
  caution that it may transfer less well to text far from news [R7]. These numbers were re-checked in
  the published PDF: annotator counts and the 1,010 annotated articles are on p. 236 ("Annotators,
  training, and highlight procedure"; "Text material"), the 3,270 words are in the Fig. 1 caption on
  p. 237, and the 689-word version is on p. 238.
- **Multilingual MFD:** Husson & Palma (2024) translated and validated the MFD into **French, German,
  Italian and Spanish** (abstract, p. 487; introduction, p. 488; validation section, p. 494). They
  validated against formally translated documents (not multilingual surveys or coders) and applied it
  to party manifestos: 329,004 statements from 31 elections in nine European multiparty systems
  (pp. 487, 494) [R11].
  Simonsen & Widmann (2025) built multilingual moral dictionaries for parliamentary immigration speeches
  in eight Western democracies over six decades [R12]. I found **no validated Greek, Portuguese or
  Dutch MFD** in this search. That is a gap, not proof of absence.

**Labelled data and agreement.**
- **MFTC:** 35,108 tweets, at least 3 trained annotators, 10 virtue/vice categories [R9].
- **MFRC:** 16,123 Reddit comments under the six-foundation MFT. It reports Fleiss' κ and
  prevalence-adjusted PABAK. Found: "most reported kappa's are low" because of low base rates, with
  medium-to-high PABAK. Fine-tuned BERT beat Llama-3-8B/Ministral-8B zero- and few-shot [R10].
- All of these are English and social-media or US-news data.

**Facts for Task 7.**
- *Stance:* virtue/vice poles are built in, so stance is partly encoded. Note that "vice" words mark the
  *violation* being discussed, not the author rejecting the foundation (interpretation).
- *Survey mapping:* no MFQ items exist in EVS/WVS/ESS (I checked the WVS-7 variable list [R55] and found
  none; EVS not itemised here).
- *Multi-label:* yes (MFTC/MFRC are multi-label [R9, R10]).
- *Readability:* good ("care", "fairness", "loyalty", "authority", "purity").

### 1.3 Inglehart–Welzel cultural map

**What it is.** There are two country-level dimensions, each built from five indicators. The first runs
from **traditional to secular-rational** (religion, parent–child ties, deference to authority,
rejection of divorce/abortion/euthanasia, national pride). The second runs from **survival to
self-expression** (materialist vs post-materialist priorities, subjective well-being, interpersonal
trust, political activism, tolerance of outgroups measured by acceptance of homosexuality). The
indicators were chosen because they appear in all waves. The current map is "WVS 7 (2023)" [R14].
Inglehart & Baker (2000) found, across 65 societies, both large value change linked to development and
path-dependent persistence of religious and historical heritage [R13].

**Facts for Task 7.**
- *Survey mapping:* perfect, because the dimensions are *defined* by EVS/WVS items.
- *Text detection:* I found no labelled text dataset or dictionary.
- *Granularity:* two dimensions are coarse. Several indicators (trust, happiness, petition signing) are
  behaviours or states rather than values a text "endorses" (interpretation).
- *Unit:* designed as a country-level construct.

### 1.4 Hofstede

Hofstede's model has six dimensions of **national** culture: power distance, uncertainty avoidance,
individualism/collectivism, masculinity/femininity, long/short-term orientation and indulgence/restraint.
Hofstede explicitly warns against confusing these country-level dimensions with value differences among
individuals [R15].

*Facts for Task 7:* no text datasets found, no EVS/WVS item mapping, and the scores are essentially
static country scores. Interpretation: this is a poor fit for a time-series, per-text, stance-based
design.

### 1.5 Rokeach Value Survey

Rokeach (1973), *The Nature of Human Values* [R16] *(catalogue record opened; contents not opened)*. As
commonly described, the RVS asks respondents to **rank** 18 terminal and 18 instrumental values. The
ranking format makes it single-ordering rather than multi-label, and I found no text datasets or
survey-panel mapping. Interpretation: historically important, but it is a weak candidate on most Task 7
criteria.

### 1.6 Summary table for Task 7

| Criterion | Schwartz 10/19 | MFT (5/6) | Inglehart–Welzel | Hofstede | Rokeach |
|---|---|---|---|---|---|
| Labelled text data | ValueEval'23 (≈9.3k EN arguments) [R20]; ValueEval'24 (2,648 news+manifesto texts, 9 langs) [R22] | MFTC 35k tweets [R9], MFRC 16k Reddit [R10], eMFD news [R7] | none found | none found | none found |
| Inter-annotator agreement | α = 0.49 (2022, crowd, 54 values) [R19]; α = 0.546 overall, 0.37–0.70 by language (2024) [R22] | κ mostly low, PABAK medium–high (MFRC) [R10] | n/a | n/a | n/a |
| Best reported detection | macro-F1 0.56 (2023, argument level) [R20]; 0.39 (2024, sentence level, 19 values) [R22] | per-foundation F1 in [R10] (BERT > small LLMs) | n/a | n/a | n/a |
| Stance support | attained/constrained (2024); polarity F1 0.83 given the value [R22] | virtue/vice poles [R6, R7] | n/a | n/a | n/a |
| Multi-label | yes | yes | n/a (2 dims) | n/a | no (ranking) |
| Multilingual resources | 9-lang ValueEval'24 incl. DE/EL/EN/FR/IT/NL [R22] | MFD in FR/DE/IT/ES [R11]; others [R12] | – | – | – |
| Survey mapping | ESS PVQ-21 every round 2002–2023/24 [R44, R45]; WVS w5–6 10 items [R52, R53]; none found in w7 (one data dictionary checked, not the master questionnaire) [R55] | none in EVS/WVS/ESS | defined by EVS/WVS items [R14] | none | none |
| Blog readability | good (10), fair (19) | good | good (2 axes) | fair | fair |

**Implications for this project**
- Schwartz (19 values, collapsible to 10) is the only framework that has *all* of the following:
  multilingual news-text labels in v0 languages, a stance-like label, and a per-round survey target (ESS).
  This is the strongest default for Task 7.
- MFT is the best-resourced *dictionary* framework, and translated MFDs exist for four v0 languages. It
  is a candidate secondary lens or robustness check, but it has no survey validation target.
- Inglehart–Welzel is the natural *validation* frame for EVS/WVS. Text could be mapped onto its two axes
  post hoc (e.g. from Schwartz scores) rather than tagged directly. That mapping is my suggestion and is
  untested.
- Hofstede and Rokeach should be cited and set aside.

---

## 2. Value detection in text

### 2.1 Touché/ValueEval 2022–2023 (Kiesel et al.)

- **2022 (ACL):** Kiesel et al. built a multi-level taxonomy of **54 values** aligned with the
  psychology literature, and 5,270 arguments from four cultures. Crowdworkers reached an average
  value-wise **Krippendorff's α = 0.49**. Most disagreement came from handling 54 values at once.
  Baseline classifiers reached F1 up to 0.81 on some values but only 0.25 on average [R19].
- **SemEval-2023 Task 4:** 20 value categories, the 19 Schwartz values plus "universalism:
  objectivity". There were 8,865 arguments in the main set: IBM-ArgQ, the Conference on the Future of
  Europe, and Group Discussion Ideas. Supplementary test sets came from Zhihu, Nahj al-Balagha and
  **The New York Times (80 arguments from 12 articles)**. 39 teams took part. Found: the best macro-F1 on
  the main test set was **0.56** (team "Adam Smith", an ensemble of DeBERTa/RoBERTa models), against
  0.42 for the BERT baseline. On the NYT set the best was **0.34**, and 0.47 for a hypothetical
  best-per-category oracle. The best per-category F1 was 0.87 (universalism: nature) [R20]. Each argument
  had 3 crowdworkers [R20]. The English data are CC BY 4.0 on Zenodo [R21].

### 2.2 ValueEval'24: multilingual, news, attainment

The Touché 2024 Human Value Detection task is the most relevant precedent for this project [R22, R23].
- **Data:** 2,648 texts of 400–800 words from **news articles and political manifestos** published
  2019–2023, in 9 languages: Bulgarian, Dutch, English, French, German, **Greek**, Hebrew, Italian and
  Turkish. More than 70 value scholars annotated them in the JRC-led **ValuesML** project. The data are
  split into sentences (74,231 in total) and come with DeepL English translations (Google Translate for
  Hebrew) [R22].
- **Labels:** 19 Schwartz values × {attained, constrained} at sentence level [R22, R23].
- **Agreement** (Krippendorff's α, before curation): EL 0.696, FR 0.685, IT 0.610, BG 0.495,
  TR 0.463, NL 0.411, EN 0.409, DE 0.367; **overall 0.546**. Teams then curated a single ground truth
  [R22].
- **Results:** 9 teams. The best subtask-1 macro-F1 (which values) was **0.39**, from team "Hierocles of
  Alexandria" with XLM-RoBERTa-xl and previous-sentence context; the random baseline was 0.06. The best
  subtask-2 F1 (attained vs constrained, given a gold value reference) was **0.83**, against a random
  0.52. Multilingual models did best. Rare values were detected worst, except by one zero-shot GPT-4o
  run [R22, R23].
- **Licence:** a Data Usage Agreement restricts use to scientific human-value-detection research and
  forbids redistribution [R24].
- **Later work:** Yeste & Rosso (2026) re-ran the ValuesML/ValueEval format under matched conditions.
  Found: full-document context improved DeBERTa-v3 encoders by 2.5–3.8 macro-F1 points but did not
  consistently help zero-shot LLMs of 12B–123B. Retrieved moral knowledge helped every model family, and
  larger models did not guarantee gains [R28].

### 2.3 Attained/constrained is not endorsed/rejected

Interpretation, important for Tasks 7 and 4. ValueEval'24 asks whether the sentence describes something
that *attains* or *constrains* a value [R22]. Our spec asks whether the *author endorses or rejects* the
value. These differ. "The new law tramples press freedom" *constrains* self-direction, but the author
*endorses* it. So the 0.83 polarity F1 is not an estimate of our stance accuracy, and the labels need an
extra mapping step or a re-annotation layer.

### 2.4 LLM-based value and stance detection (2023–2026)

- **Gilardi et al. (2023):** on 6,183 tweets and news articles, zero-shot ChatGPT beat crowd workers by
  about 25 points on average across relevance, **stance**, topic and frame tasks. Its intercoder
  agreement was higher than that of crowds and of trained annotators [R26].
- **Rathje et al. (2024):** GPT detected psychological constructs, as judged by human annotators, across
  **12 languages** with simple prompts and no training data, including lesser-spoken languages [R25].
- **Ziems et al. (2024):** across 25 English CSS benchmarks, zero-shot LLMs did *not* beat the best
  fine-tuned models on classification but reached "fair" agreement with humans [R27].
- **Milkova & Rudnev (2026):** different LLMs produced different Schwartz value interpretations of
  social-media posts. Calibrating the prompt through error analysis improved alignment with experts.
  Found: annotation-regime differences propagated into predicted *levels* of value expression, whereas
  *standardised temporal dynamics* and event responses were more robust [R29].
- **MFRC (2022/2026):** fine-tuned BERT still beat 8B LLMs on moral-foundation labels [R10].

**Implications for this project**
- Expect modest per-text accuracy. The best sentence-level 19-value F1 is 0.39 [R22]; even
  argument-level detection reaches only 0.56 [R20]. Aggregate trends can still be informative if errors
  are stable over time and country. [R29] gives early evidence that dynamics are more robust than levels.
- Use the ValueEval'24 data (which includes Greek) as Task 4's quantitative benchmark, within the DUA
  terms: no redistribution, so the public repo cannot hold it.
- Define our stance label explicitly against attained/constrained (§2.3), and measure it on the owner's
  corrected examples.
- Report results as relative changes (z-scored per source) rather than absolute value shares. That is
  where [R29] found robustness.

---

## 3. Values over time from text

### 3.1 Culturomics and its limits

- **Michel et al. (2011):** built a corpus of about 4% of all books ever printed and showed trend
  analyses of 1800–2000 English on topics such as censorship, fame and collective memory [R30].
- **Pechenick et al. (2015):** found that the Google Books corpus is "a library, containing one of each
  book". Single prolific authors can move frequencies, and a rising share of scientific text distorts
  20th-century trends. Only the English Fiction subset of the second version was not heavily affected
  [R31].
- Interpretation: this is the canonical warning that *source mix drives artefacts*, as the spec's
  anti-goals already say.

### 3.2 Value and morality trends in books

- **Greenfield (2013):** in American English books 1800–2000, word frequencies moved from rural-adaptive
  values (duty, obligation, religion) to urban, individualistic and materialistic ones (choice, getting,
  child-centred words), in step with urbanisation. UK books replicated the pattern [R32].
- **Kesebir & Kesebir (2012):** general moral terms (virtue, decency, conscience) declined in 20th-century
  American books, and 74% of 50 virtue words declined significantly [R33].
- **Wheeler, McGrath & Haslam (2019):** tracked 304 moral terms in six sets (general plus five MFT
  foundations), 1900–2007, in English Google Books. Found non-linear paths. General and purity language
  fell until about 1980 and then rebounded. Loyalty rose steadily. Harm rose sharply after 1980.
  Authority peaked in the late 1960s. There was no consistent shift towards individualist morality [R34].
  Interpretation: this partly contradicts [R33], and the difference is a methods lesson about word-list
  choice.
- **Scheffer et al. (2021):** across languages, rationality-related words rose from 1850 and
  sentiment-laden words fell. The pattern reversed in the 1980s and accelerated around 2007, alongside a
  collectivist-to-individualist pronoun shift [R35].
- **Atari & Henrich (2023):** frame "historical psychology" around three text-analytic tool classes:
  dictionaries, distributed representations and human annotation. They urge going beyond English [R36].
- **Xie et al. (2019):** used diachronic embeddings to infer moral sentiment change for concepts such as
  slavery, including polarity flips [R37].

### 3.3 Newspapers specifically

- **Bardi et al. (2008):** built a Schwartz-based *value lexicon* and validated it on **American
  newspapers 1900–2000**. It converged with self-reports and predicted value-expressive behaviours, and
  value levels fluctuated with major historical events [R18].
- **Ponizovskiy et al. (2020):** Personal Values Dictionary. Found: small to moderate correlations
  (r = .1–.4) with self-reported values for 7 of 10 values [R17]. Interpretation: this is a realistic
  ceiling for dictionary-to-survey agreement.
- **Mokhberian et al. (2020):** characterised MFT moral framing across partisan US news outlets [R38].
- **Hopp et al. (2021):** eMFD scores separated Breitbart, NYT and HuffPost by foundation emphasis [R7].
- **Rozado, al-Gharbi & Halberstadt (2021):** analysed 27 million news and opinion articles from
  47 US outlets, 1970–2019. Prejudice-denoting words rose sharply in the 2010s. Found: some outlets'
  yearly prevalence **predicted others' usage the following year**, and **Granger tests** suggested the
  term prevalence might predict shifts in public opinion [R39]. Interpretation: this is the closest
  published precedent to our "news text → survey" and "lead/lag between sources" design, at the
  outlet-within-country level.

**Implications for this project**
- Almost all prior longitudinal work is **English, mostly US, mostly books, and mention-based**. None
  measures stance per value across several European countries (see §6).
- Book corpora are not our source, but Pechenick's lesson carries over: normalise per source, and keep
  source mixes constant across years.
- Expect weak absolute links to surveys (r ≈ .1–.4 at the individual level [R17]). Validate on
  *trends and rank orders*, not levels.
- Rozado-style yearly lead/lag analysis on news is feasible and publishable as a blog result, provided
  the common-shock caveats in §4 are stated.

---

## 4. Cross-country diffusion of values and attitudes

### 4.1 What we know substantively

- **Jackson & Medvedev (2024):** used WVS/EVS data 1981–2022 (n = 406,185, 76 national cultures). Found
  global **value divergence**, especially on tolerance and self-expression. GDP similarity tracks value
  similarity, and **geographic proximity has become an increasingly strong correlate of value
  similarity**: values "diverged globally but converged regionally" [R40]. Interpretation: this gives a
  prior that neighbouring-country spillover is plausible in our European sample.
- **Coppedge et al. (2021, V-Dem):** on democratisation, "Galton's problem" means international
  influence can be mistaken for domestic causes, or the reverse. They handle it with domestic controls
  and network-correlated errors. Found: short-run contagion was small but long-run effects were large
  [R41].
- **Inglehart & Baker (2000):** the persistence of cultural heritage zones implies shared, slow-moving
  common factors [R13]. These are a confound for any "spread" claim.

### 4.2 Methods suited to about 20 annual points × 12 countries

The usable panel is about **12 countries × ~20 years ≈ 240 country-years per value**. Methods, ordered
roughly by fit:

**(a) Spatial econometrics (spatial-lag panel).** Model y_it = ρ Σ_j w_ij y_jt(−1) + x_it β + α_i + τ_t + ε_it,
with a fixed neighbour matrix W (contiguity or distance).
- Franzese & Hays (2007) show that non-spatial OLS has omitted-variable bias. Spatial OLS performs
  acceptably under low-to-moderate interdependence and reasonable sample sizes. Spatial 2SLS or ML is
  better otherwise. They illustrate with European governments' panel data [R42].
- Interpretation: W fixes the network a priori, so we estimate one ρ, not 144 pairwise effects. This is
  the most parameter-efficient option for our size. Year effects τ_t absorb Europe-wide common shocks
  (2008, 2015, 2020).

**(b) Panel VAR.**
- Holtz-Eakin, Newey & Rosen (1988) introduced panel VAR estimated by IV on quasi-differenced equations
  [R43]. Abrigo & Love (2016) give GMM estimation and inference tools [R46].
- *Caveat:* with fixed effects and short T, dynamic panel estimators carry Nickell bias of order 1/T
  [R47] *(metadata only; result stated from the standard literature)*. At T ≈ 20 that is material
  (roughly −(1+ρ)/(T−1) ≈ −0.1 for ρ = 0.8). Interpretation: use GMM or bias-corrected estimators, and
  treat persistence estimates cautiously.
- *Caveat:* a panel VAR pools dynamics across countries, so it answers "do values move together", not
  "does France lead Belgium".

**(c) Pairwise and heterogeneous-panel Granger tests.**
- Dumitrescu & Hurlin (2012) average individual Wald statistics across units. They derive a fixed-T
  standardised statistic, and their Monte Carlo found good small-sample properties even with
  cross-sectional dependence [R48].
- Rozado et al. (2021) used this style of test on yearly news series [R39].
- *Caveat:* an unrestricted 12-country VAR with p = 1 has 13 coefficients per equation from about 19
  usable observations. That is infeasible. Bivariate tests on 66 country pairs per value need
  multiple-testing control (e.g. FDR), and the power per pair with T ≈ 20 is low. Interpretation: report
  effect sizes and the fraction of significant pairs against a permutation null, not single "France
  Granger-causes Spain" headlines.

**(d) Change-point detection, then diffusion-network inference.**
- PELT finds multiple change points at linear cost by penalised cost minimisation [R50]. Hamilton's
  Markov-switching model infers discrete unobserved regime shifts [R51]. This is the HMM "value regimes"
  idea.
- Turning change-point dates into adoption events allows **NetInf**. Gomez-Rodriguez, Leskovec & Krause
  (2010) infer the latent network that best explains observed infection times [R49].
- Desmarais, Harden & Boehmke (2015) applied network inference to **187 policies** diffusing among US
  states, a yearly-adoption setting like ours, to recover a persistent diffusion network [R54].
- *Caveat:* their identification comes from many cascades. With 19 values × 12 countries we have at most
  19 cascades of length ≤ 12 per period, and change points dated at yearly resolution produce ties. The
  inferred network will be fragile. Report edge stability under bootstrap.

**(e) Hawkes processes.**
- Hawkes (1971) defined self- and mutually-exciting point processes [R56]. Linderman & Adams (2014)
  combine them with random-graph priors to infer latent networks from event data [R57]. Rizoiu et al.
  (2017) give a practical tutorial [R58].
- Zannettou et al. (2017) used Hawkes processes to estimate how news URLs spread between web communities
  (Reddit, 4chan, Twitter) [R59]. This is an application of mutually-exciting models to cross-community
  information spread.
- *Caveat:* Hawkes needs **events in continuous or fine time**. Annual country aggregates give too few
  events: a 12×12 excitation matrix has 144 parameters plus kernels. Binned or aggregated data bias naive
  estimators. Shlomovich et al. (2021) found alternative approaches "can be heavily biased" and proposed
  MC-EM for multivariate aggregated Hawkes processes [R60].
- Interpretation: apply Hawkes at the **article level** (dated articles strongly endorsing value v,
  country c, at daily or monthly resolution, 2005+), not on annual series. Use low-rank or pooled
  kernels.

**Implications for this project**
- Lead with **spatial-lag panels with year fixed effects** and per-country trends. They are the most
  defensible on about 240 country-years, and the parameters are few and readable.
- Treat Granger/VAR and NetInf results as *descriptive lead/lag*, with permutation nulls and FDR control.
  State the T ≈ 20 power limits on the page (the spec already forbids causal language).
- Reserve Hawkes for article-level timestamps in the 2005+ web era. This makes monthly series a
  first-class by-product, not "secondary", for that model only.
- Always control for common European shocks (year effects or a common factor) before claiming that
  something spread. Otherwise Galton's problem [R41] and shared heritage [R13] will masquerade as
  diffusion.

---

## 5. Survey ground truth: EVS, WVS and the ESS human-values module

### 5.1 European Social Survey (ESS): the best Schwartz target

- **Instrument:** the Human Values Scale, a 21-item PVQ measuring the 10 basic values, has been in
  **every ESS round since Round 1 (2002/03)** [R44, R45].
- **Measurement invariance:** Davidov, Schmidt & Schwartz (2008) found configural and metric invariance
  across 20 countries in Round 1. Mean comparisons across countries are valid **only for subsets where
  scalar invariance holds** [R61].
- **Series break:** from **Round 12 (2025–26)** the ESS uses a **new 20-item HVS** with shorter,
  gender-neutral items for self-completion modes. The developers say the revised items "represent new
  items in the ESS time series" [R62]. The ESS site lists the initial Round 12 data release for early 2027
  [R63]. So the PVQ-21 series is **2002–2023/24 (Rounds 1–11)**, which is about 11 biennial points per
  country, and the ESS's move from face-to-face to self-completion is a further mode caveat [R62].

**Country × round coverage, Rounds 1–11.** R1 2002/03, R2 2004/05, R3 2006/07, R4 2008/09, R5 2010/11,
R6 2012/13, R7 2014/15, R8 2016/17, R9 2018/19, R10 2020/22, R11 2023/24.

| Country | Rounds with data | n |
|---|---|---|
| BE, FR, DE, NL, PT, CH, GB | 1–11 | 11 |
| ES | 1–11 | 11 |
| AT | 1–5, 7–11 (no R6) | 10 |
| IT | 1, 2, 6, 8–11 | 7 |
| GR | 1, 2, 4, 5, 10, 11 | 6 |
| LU | 1, 2 | 2 |

Source and verification: the table comes from the participation matrix on Wikipedia's ESS page [R64],
cross-checked against official ESS round documents for Round 7 [R65] and Round 8 [R66]. The Round 8 check
showed **Spain did participate in R8** (23 countries), which Wikipedia omits, so the table above is
corrected. The R7 document confirms Italy's absence. The other cells are not yet confirmed against the
ESS Data Portal, which needs an interactive query. Task 7/8 should confirm them there.

### 5.2 European Values Study (EVS)

Waves: 1981, 1990, 1999, 2008, 2017; a 2026 wave is listed [R67].

| Wave | v0 countries present (official EVS country pages) |
|---|---|
| 1981 | BE, FR, DE, IT, NL, ES, GB |
| 1990 | AT, BE, FR, DE, IT, NL, PT, ES, GB |
| 1999 | AT, BE, FR, DE, GR, IT, LU, NL, PT, ES, GB |
| 2008 | all 12 (incl. CH, LU) |
| 2017 | AT, FR, DE, IT, NL, PT (fieldwork 2020), ES, CH, GB; GR as a separate national CAWI dataset (ZA7546); **no BE, no LU** |

Sources: [R67] (country pages for each wave). The EVS 2017 page also shows mixed modes (CAPI plus
CAWI/mail) in DE, NL and CH, which is a comparability caveat [R67].

### 5.3 World Values Survey (WVS)

- **Wave 7 (2017–2022, v5.0.0):** among v0 countries it covers DE, GR, NL and GB (Great Britain plus
  Northern Ireland) [R68]. It is jointly harmonised with EVS 2017 to build the cultural map [R14].
- **Schwartz items in WVS:** waves 5 and 6 contain a 10-item portrait battery ("Now I will briefly
  describe some people…", six-point "very much like me" to "not at all like me"; V70–V79 in wave 6)
  [R52, R53]. v0 countries with WVS-5 files: ES 2007, NL 2006, FR 2006, DE 2006, GB 2005, IT 2005.
  WVS-6: DE 2013, NL 2012, ES 2011 [R52]. Switzerland is not checked.
- **No Schwartz battery in wave 7:** I found no portrait-value items in a full WVS-7 data dictionary
  (Czechia 2022, 398 variables) [R55]. I have not verified this against the master questionnaire.
- **EVS and Schwartz:** I found no evidence that EVS carries a Schwartz battery. Not verified item by
  item.

### 5.4 What maps to what

- **Schwartz:** ESS HVS (21 items, every round to R11) [R44, R61]; WVS-5/6 10 items [R52, R53]. None found in WVS-7,
  from one national data dictionary [R55]; not checked against the master questionnaire.
- **Inglehart–Welzel:** EVS and WVS by construction [R14].
- **MFT:** no direct items. Proxies such as EVS/WVS "justifiability" items (abortion, divorce,
  homosexuality) relate to purity/care, but that is my interpretation, not a validated mapping.

**Implications for this project**
- For Schwartz, validate on **ESS Rounds 1–11**. Seven v0 countries have all 11 rounds, and AT has 10.
  **LU (2 rounds) and GR (6) are weak**, which matters for the Greece thin slice: GR has ESS 2002, 2004,
  2008, 2010, 2020/22 and 2023/24, plus EVS 1999, 2008 and 2017 and WVS 2017.
- Do not splice ESS Round 12+ onto Rounds 1–11 without a bridging analysis [R62].
- Compare **within-country change and cross-country rank order**, given only partial scalar invariance
  [R61].
- EVS/WVS give 3–5 points per country since 1981. They are useful for the 1940–2005 extension's later
  end and for Inglehart–Welzel framing, not for annual validation.

---

## 6. Gaps this project fills

Based on §§2–5 (interpretation, grounded in the cited work):

1. **Country-level, multi-country, longitudinal.** Prior trend studies are overwhelmingly US/English and
   book-based [R30–R35], or US newspapers [R18, R39]. ValueEval'24 is multilingual but cross-sectional,
   covering 2019–2023 [R22]. No study found here builds **annual value series for 12 European
   countries** from national press.
2. **Stance, not mention.** Dictionary and culturomics work measures salience [R17, R18, R33, R34].
   ValueEval'24's attained/constrained is closest, but it is not author endorsement (§2.3). An
   endorse/reject/neutral layer per value is new.
3. **Multilingual consistency.** Agreement varies across languages, with α from 0.37 (DE) to 0.70 (EL)
   in [R22]. Translated MFDs exist for only four v0 languages [R11]. Measuring cross-language consistency
   explicitly, as Task 4 plans, addresses a known weakness.
4. **Validation against a per-round values survey.** Bardi et al. validated against self-reports in one
   country [R18]. Using the ESS HVS across countries and rounds [R44, R61] as an external check on
   text-derived Schwartz series appears new.
5. **Diffusion between countries from text.** Diffusion-network inference has been used for policies
   [R54] and Hawkes processes for online communities [R59]. The geographic convergence of values is
   documented in surveys [R40]. Combining these on **text-derived national value series** with spatial
   panels, Granger tests, change points and NetInf is new, provided the small-T caveats in §4 are shown.

**Implications for this project**
- The blog's novelty claims should be the five above, each stated with its caveat. Avoid "first ever"
  wording, because the search was not exhaustive.
- The strongest single contribution is likely (2) plus (4): stance-based Schwartz series checked against
  the ESS.
- The weakest is (5) on annual data. Frame it as exploratory lead/lag with explicit power limits.

---

## References

Notes: "(metadata only)" means only the DOI or catalogue record was opened. Abstract-level claims were
read from publisher abstracts via Crossref, OpenAlex or Semantic Scholar records, or publisher pages.
"(full text)" means the PDF or HTML was read.

- [R1] Schwartz, S. H. (1992). Universals in the content and structure of values: Theoretical advances and empirical tests in 20 countries. *Advances in Experimental Social Psychology*. https://doi.org/10.1016/S0065-2601(08)60281-6 *(metadata only)*
- [R2] Schwartz, S. H. (2012). An overview of the Schwartz theory of basic values. *Online Readings in Psychology and Culture* 2(1). https://doi.org/10.9707/2307-0919.1116 (landing page https://scholarworks.gvsu.edu/orpc/vol2/iss1/11/)
- [R3] Schwartz, S. H., Cieciuch, J., Vecchione, M., Davidov, E., Fischer, R., Beierlein, C., et al. (2012). Refining the theory of basic individual values. *JPSP* 103(4). https://doi.org/10.1037/a0029393
- [R4] Graham, J., Haidt, J., & Nosek, B. A. (2009). Liberals and conservatives rely on different sets of moral foundations. *JPSP* 96(5). https://doi.org/10.1037/a0015141
- [R5] Graham, J., Haidt, J., Koleva, S., Motyl, M., Iyer, R., Wojcik, S., & Ditto, P. (2013). Moral Foundations Theory: The pragmatic validity of moral pluralism. *Advances in Experimental Social Psychology* 47. https://doi.org/10.1016/B978-0-12-407236-7.00002-4 *(metadata only)*
- [R6] Frimer, J., et al. (2019). Moral Foundations Dictionary 2.0 (OSF project, `mfd2.0.dic`). https://osf.io/ezn37/
- [R7] Hopp, F. R., Fisher, J. T., Cornell, D., Huskey, R., & Weber, R. (2021). The extended Moral Foundations Dictionary (eMFD). *Behavior Research Methods* 53. https://doi.org/10.3758/s13428-020-01433-0 (full text)
- [R8] Atari, M., Haidt, J., Graham, J., Koleva, S., Stevens, S. T., & Dehghani, M. (2023). Morality beyond the WEIRD: How the nomological network of morality varies across cultures. *JPSP*. https://doi.org/10.1037/pspp0000470
- [R9] Hoover, J., Portillo-Wightman, G., Yeh, L., et al. (2020). Moral Foundations Twitter Corpus: A collection of 35k tweets annotated for moral sentiment. *SPPS* 11(8). https://doi.org/10.1177/1948550619876629
- [R10] Trager, J., Ziabari, A. S., et al. (2022; v4 2026). The Moral Foundations Reddit Corpus. arXiv:2208.05545. https://arxiv.org/abs/2208.05545 (full text)
- [R11] Husson, C., & Palma, N. (2024; issue 2025). Broadening the study of morality in multiparty settings through a novel dictionary translation and validation methodology. *Political Psychology* 46(3). https://doi.org/10.1111/pops.13019 (full text via https://madoc.bib.uni-mannheim.de/70023/)
- [R12] Simonsen, K. B., & Widmann, T. (2025). When do political parties moralize? A cross-national study of the use of moral language in political communication on immigration. *British Journal of Political Science*. https://doi.org/10.1017/S0007123425000122
- [R13] Inglehart, R., & Baker, W. E. (2000). Modernization, cultural change, and the persistence of traditional values. *American Sociological Review* 65(1). https://doi.org/10.2307/2657288
- [R14] World Values Survey Association. Findings and Insights / The Inglehart–Welzel World Cultural Map – WVS 7 (2023). https://www.worldvaluessurvey.org/WVSContents.jsp?CMSID=Findings
- [R15] Hofstede, G. (2011). Dimensionalizing cultures: The Hofstede model in context. *Online Readings in Psychology and Culture* 2(1). https://doi.org/10.9707/2307-0919.1014 (https://scholarworks.gvsu.edu/orpc/vol2/iss1/8/)
- [R16] Rokeach, M. (1973). *The Nature of Human Values*. New York: Free Press. https://archive.org/details/natureofhumanval00roke *(catalogue record only)*
- [R17] Ponizovskiy, V., Ardag, M., Grigoryan, L., Boyd, R., Dobewall, H., & Holtz, P. (2020). Development and validation of the Personal Values Dictionary. *European Journal of Personality* 34(5). https://doi.org/10.1002/per.2294
- [R18] Bardi, A., Calogero, R. M., & Mullen, B. (2008). A new archival approach to the study of values and value–behavior relations: Validation of the value lexicon. *Journal of Applied Psychology* 93(3). https://doi.org/10.1037/0021-9010.93.3.483
- [R19] Kiesel, J., Alshomary, M., Handke, N., Cai, X., Wachsmuth, H., & Stein, B. (2022). Identifying the human values behind arguments. *ACL 2022*. https://doi.org/10.18653/v1/2022.acl-long.306 (full text)
- [R20] Kiesel, J., Alshomary, M., Mirzakhmedova, N., Heinrich, M., Handke, N., Wachsmuth, H., & Stein, B. (2023). SemEval-2023 Task 4: ValueEval: Identification of human values behind arguments. *SemEval-2023*. https://doi.org/10.18653/v1/2023.semeval-1.313 (full text)
- [R21] Kiesel, J., Mirzakhmedova, N., Alshomary, M., et al. (2022). Touché23-ValueEval / Human-Value-Detection dataset (Zenodo, CC BY 4.0). https://zenodo.org/records/6814564
- [R22] Kiesel, J., Çöltekin, Ç., Heinrich, M., Fröbe, M., Alshomary, M., De Longueville, B., et al. (2024). Overview of Touché 2024: Argumentation Systems (extended version). *CLEF 2024 Working Notes*, CEUR-WS Vol-3740, pp. 3341–3366. https://ceur-ws.org/Vol-3740/paper-322.pdf (full text)
- [R23] Touché @ CLEF 2024. Human Value Detection 2024 (task page and leaderboard). https://touche.webis.de/clef24/touche24-web/human-value-detection.html
- [R24] The ValuesML Team (2023). Touché24-ValueEval (Zenodo; ValueEval'24 Data Usage Agreement). https://doi.org/10.5281/zenodo.10396293 (record https://zenodo.org/records/10396294)
- [R25] Rathje, S., Mirea, D.-M., Sucholutsky, I., Marjieh, R., Robertson, C. E., & Van Bavel, J. J. (2024). GPT is an effective tool for multilingual psychological text analysis. *PNAS* 121(34). https://doi.org/10.1073/pnas.2308950121
- [R26] Gilardi, F., Alizadeh, M., & Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. *PNAS* 120(30). https://doi.org/10.1073/pnas.2305016120
- [R27] Ziems, C., Held, W., Shaikh, O., Chen, J., Zhang, Z., & Yang, D. (2024). Can large language models transform computational social science? *Computational Linguistics* 50(1). https://doi.org/10.1162/coli_a_00502 (arXiv:2305.03514)
- [R28] Yeste, V., & Rosso, P. (2026). More context, larger models, or moral knowledge? A systematic study of Schwartz value detection in political texts. *Findings of EMNLP 2026*. https://aclanthology.org/2026.findings-emnlp.1910/
- [R29] Milkova, M., & Rudnev, M. (2026). Measuring human value expression in social media texts: Calibrated LLM annotation and encoder transfer. arXiv:2606.11018. https://arxiv.org/abs/2606.11018
- [R30] Michel, J.-B., Shen, Y. K., Aiden, A. P., Veres, A., Gray, M. K., et al. (2011). Quantitative analysis of culture using millions of digitized books. *Science* 331(6014). https://doi.org/10.1126/science.1199644
- [R31] Pechenick, E. A., Danforth, C. M., & Dodds, P. S. (2015). Characterizing the Google Books corpus: Strong limits to inferences of socio-cultural and linguistic evolution. *PLOS ONE* 10(10). https://doi.org/10.1371/journal.pone.0137041
- [R32] Greenfield, P. M. (2013). The changing psychology of culture from 1800 through 2000. *Psychological Science* 24(9). https://doi.org/10.1177/0956797613479387
- [R33] Kesebir, P., & Kesebir, S. (2012). The cultural salience of moral character and virtue declined in twentieth century America. *Journal of Positive Psychology* 7(6). https://doi.org/10.1080/17439760.2012.715182
- [R34] Wheeler, M. A., McGrath, M. J., & Haslam, N. (2019). Twentieth century morality: The rise and fall of moral concepts from 1900 to 2007. *PLOS ONE* 14(2). https://doi.org/10.1371/journal.pone.0212267
- [R35] Scheffer, M., van de Leemput, I., Weinans, E., & Bollen, J. (2021). The rise and fall of rationality in language. *PNAS* 118(51). https://doi.org/10.1073/pnas.2107848118
- [R36] Atari, M., & Henrich, J. (2023). Historical psychology. *Current Directions in Psychological Science* 32(2). https://doi.org/10.1177/09637214221149737
- [R37] Xie, J. Y., Ferreira Pinto Junior, R., Hirst, G., & Xu, Y. (2019). Text-based inference of moral sentiment change. *EMNLP-IJCNLP 2019*. https://doi.org/10.18653/v1/D19-1472
- [R38] Mokhberian, N., Abeliuk, A., Cummings, P., & Lerman, K. (2020). Moral framing and ideological bias of news. arXiv:2009.12979. https://arxiv.org/abs/2009.12979
- [R39] Rozado, D., al-Gharbi, M., & Halberstadt, J. (2021). Prevalence of prejudice-denoting words in news media discourse: A chronological analysis. *Social Science Computer Review*. https://doi.org/10.1177/08944393211031452
- [R40] Jackson, J. C., & Medvedev, D. (2024). Worldwide divergence of values. *Nature Communications* 15. https://doi.org/10.1038/s41467-024-46581-5 (full text)
- [R41] Coppedge, M., Denison, B., Friesen, P., Tiscornia, L., & Xu, Y. (2021). International influence: The hidden dimension. V-Dem Working Paper 2021:119. https://www.v-dem.net/media/publications/wp_119_final.pdf (full text)
- [R42] Franzese, R. J., & Hays, J. C. (2007). Spatial econometric models of cross-sectional interdependence in political science panel and time-series-cross-section data. *Political Analysis* 15(2). https://doi.org/10.1093/pan/mpm005
- [R43] Holtz-Eakin, D., Newey, W., & Rosen, H. S. (1988). Estimating vector autoregressions with panel data. *Econometrica* 56(6). https://doi.org/10.2307/1913103
- [R44] European Social Survey. Findings from the Human Values Scale (news article). https://www.europeansocialsurvey.org/news/article/findings-human-values-scale
- [R45] European Social Survey (n.d., c. 2021). *The Human Values Scale: Findings from the European Social Survey* (booklet). https://www.europeansocialsurvey.org/sites/default/files/2023-06/ESS_Findings_HVS.pdf
- [R46] Abrigo, M. R. M., & Love, I. (2016). Estimation of panel vector autoregression in Stata. *Stata Journal* 16(3). https://doi.org/10.1177/1536867X1601600314
- [R47] Nickell, S. (1981). Biases in dynamic models with fixed effects. *Econometrica* 49(6). https://doi.org/10.2307/1911408 *(metadata only)*
- [R48] Dumitrescu, E.-I., & Hurlin, C. (2012). Testing for Granger non-causality in heterogeneous panels. *Economic Modelling* 29(4). https://doi.org/10.1016/j.econmod.2012.02.014 (abstract via https://ideas.repec.org/a/eee/ecmode/v29y2012i4p1450-1460.html)
- [R49] Gomez-Rodriguez, M., Leskovec, J., & Krause, A. (2010). Inferring networks of diffusion and influence. *KDD 2010*. https://doi.org/10.1145/1835804.1835933
- [R50] Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection of changepoints with a linear computational cost. *JASA* 107(500). https://doi.org/10.1080/01621459.2012.737745
- [R51] Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle. *Econometrica* 57(2). https://doi.org/10.2307/1912559
- [R52] IHSN Survey Catalog. World Values Survey Wave 5 and Wave 6 national files (catalogue search API; e.g. ESP_2007_WVS-W5, DEU_2013_WVS-W6). https://catalog.ihsn.org/index.php/api/catalog/search?sk=World%20Values%20Survey%20Wave%205
- [R53] IHSN Survey Catalog. World Values Survey 2015–2016, Wave 6 (Haiti), variable V70 (Schwartz portrait item, Show Card L). https://catalog.ihsn.org/catalog/9008/variable/F1/V74?name=V70
- [R54] Desmarais, B. A., Harden, J. J., & Boehmke, F. J. (2015). Persistent policy pathways: Inferring diffusion networks in the American states. *APSR* 109(2). https://doi.org/10.1017/S0003055415000040
- [R55] IHSN Survey Catalog. Czechia – World Values Survey – Wave 7, 2022, data dictionary (398 variables). https://catalog.ihsn.org/catalog/11564/data-dictionary/F1?file_name=F1
- [R56] Hawkes, A. G. (1971). Spectra of some self-exciting and mutually exciting point processes. *Biometrika* 58(1). https://doi.org/10.1093/biomet/58.1.83
- [R57] Linderman, S. W., & Adams, R. P. (2014). Discovering latent network structure in point process data. *ICML 2014*. arXiv:1402.0914. https://arxiv.org/abs/1402.0914
- [R58] Rizoiu, M.-A., Lee, Y., Mishra, S., & Xie, L. (2017). A tutorial on Hawkes processes for events in social media. arXiv:1708.06401. https://arxiv.org/abs/1708.06401
- [R59] Zannettou, S., Caulfield, T., De Cristofaro, E., Kourtellis, N., Leontiadis, I., et al. (2017). The web centipede: Understanding how web communities influence each other through the lens of mainstream and alternative news sources. *IMC 2017*. arXiv:1705.06947. https://arxiv.org/abs/1705.06947
- [R60] Shlomovich, L., Cohen, E. A. K., & Adams, N. (2021). A parameter estimation method for multivariate aggregated Hawkes processes. arXiv:2108.12357 (published in *Statistics and Computing* 32, 2022). https://arxiv.org/abs/2108.12357
- [R61] Davidov, E., Schmidt, P., & Schwartz, S. H. (2008). Bringing values back in: The adequacy of the European Social Survey to measure values in 20 countries. *Public Opinion Quarterly* 72(3). https://doi.org/10.1093/poq/nfn035
- [R62] Sommer, E., Dorer, B., Efu Nkong, U., Hanson, T., Zinn, S., & Schwartz, S. H. (2025). Revision and cross-cultural adaptation of the Human Values Scale for self-completion modes. *Survey Practice* 18. https://doi.org/10.29115/SP-2025-0017 (full text via https://openaccess.city.ac.uk/id/eprint/36306/)
- [R63] European Social Survey. Participating Countries page (news list includes "Initial Round 12 data release scheduled for early 2027"). https://www.europeansocialsurvey.org/about/participating-countries
- [R64] Wikipedia contributors. European Social Survey (participating-countries table, rounds 1–11). https://en.wikipedia.org/wiki/European_Social_Survey (secondary source; one error found and corrected, see §5.1)
- [R65] European Social Survey. ESS7 quality matrix. https://www.europeansocialsurvey.org/sites/default/files/2023-06/ESS7_quality_matrix.pdf
- [R66] European Social Survey. ESS8 weighting strategy (Table 1: 23 participating countries). https://www.europeansocialsurvey.org/sites/default/files/2023-06/ESS8_weighting_strategy.pdf
- [R67] European Values Study. Participating countries and country information, surveys 1981, 1990, 1999, 2008, 2017. https://europeanvaluesstudy.eu/surveys/surveys-evs/evs-2017/participating-countries-and-country-information-survey-2017/ (and the analogous `survey-1981/…`, `survey-1990/…`, `survey-1999/…`, `survey-2008/…` pages)
- [R68] World Values Survey Association (2024). World Values Survey Wave 7 (2017–2022) Cross-National Data-Set v5.0.0 (B2FIND record, spatial coverage). https://doi.org/10.14281/18241.20 (record https://b2find.eudat.eu/dataset/ca564f45-3091-5430-aced-d69dd8bd4941)
