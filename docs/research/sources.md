# Sources

Archive survey for the thin-slice countries, Greece (GR) and the United Kingdom (GB),
done on 2026-11-18. For each candidate we read the landing page, the terms of use or
API terms, and robots.txt. Where it helped, we also opened one or two sample article
pages to check the paywall flag (`isAccessibleForFree` in the page metadata) or a date
range. We read only documentation, terms and sample pages. We did not scrape, download
article text or store any of it. Every registry field rests on a page listed in that
entry's `evidence_urls` in `data/sources/sources.yaml`. If no visited page settled a
field, it is `unknown`. We did not infer permissions: `llm_api_allowed` is `no` only
when the terms explicitly ban AI/ML use or ban copying for any purpose. It is `unknown`
when the terms only carry generic "no reproduction" wording. In those cases the notes
quote what the terms do say. One limitation: `coverage.md` counts a source as "usable"
whenever access is free. It does not check the terms. Several free GB sources (Guardian,
BBC, Mumsnet) count as usable there but forbid our use, as set out below.

## GR

**2005–now.** Greek opinion text is plentiful and free. Ta Nea (`gr-tanea-website`),
To Vima (`gr-tovima-website`) and EfSyn (`gr-efsyn-website`) are free born-digital sites
with dedicated opinion/column sections. The opinion and print-edition articles we
checked are marked free (`isAccessibleForFree: true`). Their terms are standard Greek
"all rights reserved, one personal copy only" boilerplate. They contain no AI or
text-and-data-mining (TDM) clause, and robots.txt does not block AI crawlers. So LLM use
is `unknown`, not forbidden. These three, plus Rizospastis, are also editorially
diverse: centre-left (Ta Nea / To Vima), left (EfSyn) and communist (Rizospastis).
Kathimerini (centre-right) has a letters section (`/opinion/readers/`), but it is
metered (`isAccessibleForFree: "false"` on the opinion and letters pages we checked),
and robots.txt blocks AI crawlers. For forums, insomnia.gr's general-chat forum "Μπλα
Μπλα" (62k topics since 2000) is the main Greek-language forum found. Its robots.txt
signals `ai-train=no` and blocks AI crawlers, but does not address inference use.
r/greece is mixed Greek/English and depends on the Reddit API terms.

**1940–2005.** The National Library's efimeris collection (`gr-nlg-efimeris`) is free.
It covers Eleftheria 1944–67, Embros to 1969, Makedonia to 1981, Rizospastis to 1983,
Skrip to 1963 and Tachydromos 1958–77, with article-level search. That makes it the only
free full-text option for 1940–1983 we found. Its licence for text reuse is not stated.
The digitalcollections.nlg.gr default licence (attribution, non-commercial, no
derivatives, no distribution) may apply. Ta Nea's site reaches back to 1997 and
Rizospastis's to 1997. Kathimerini's Historical Archive (1919–2010) is subscription-only.

**Biggest gap (1940–2005):** **1984–1996** has no free full-text newspaper we could
verify: efimeris ends in 1983, and the newspapers' own online archives start in 1997.
(The .gr web archive has snapshots from 1996, but these are web pages, not newspaper
back-runs.) The one candidate is the To Vima / Ta Nea Historical Archive
(istorikoarxeio.gr, reportedly every issue since 6 Feb 1922). It was unreachable on
2026-11-18: HTTP 503/403 on the bare domain, and www resolved to a private IP that
refused connections. Its access terms are unknown. The 1940s–1960s are covered only by
a handful of titles, with OCR quality unchecked.

**Best for opinion / letters / forum genres:** opinion: Ta Nea, To Vima, EfSyn
(free); letters: Kathimerini `/opinion/readers/` (metered); forum: insomnia.gr Μπλα
Μπλα, r/greece.

### Recommended thin-slice sources (GR, 2005–now)

1. `gr-tanea-website`: free opinion and columns since 1997. Terms do not address LLM use.
2. `gr-tovima-website`: free opinion and columns since 2008. Terms do not address LLM use.
3. `gr-efsyn-website`: free left-leaning opinion columns, adds political balance.
4. `gr-insomnia-forum` (Μπλα Μπλα): Greek-language forum voice. Check the AI signals
   with the owner first.
5. `gr-gdelt-url-index` / `gr-common-crawl-news`: a URL-discovery layer only; the text
   remains under each publisher's terms.

Before any tagging, email Alter Ego Media and EfSyn to ask whether sending excerpts to a
commercial LLM API for research tagging is allowed. Until they answer, plan on
aggregates-only publication for these sources.

### Dead ends and leads (GR)

- **efimeries.nlg.gr** (the name in the brief) does not resolve. The live host is
  `efimeris.nlg.gr` (linked from nlg.gr).
- **To Vima / Ta Nea Historical Archive** (istorikoarxeio.gr): unreachable on
  2026-11-18. Coverage from 1922 is reported in
  https://www.tovima.gr/2023/04/26/media/istoriko-arxeio-to-vima-kai-ta-nea-diathesimes-online-oi-omilies-tou-diethnous-epistimonikou-synedriou-gia-ti-glossa-kai-ti-logotexnia/amp/.
  Access model unknown. Re-check: if it is free, it closes the 1984–1996 gap.
- **Rizospastis party archive** (arxeio.kke.gr): a KKE party archive of documents and
  posters, not newspaper text. It is out of scope (party voice).
- **Separate Greek national web archive:** none apart from the NLG/Internet Archive
  portal (`gr-greek-web-archive-portal`), which covers .gr snapshots from 1996.

## GB

**2005–now.** The UK has the most text but the strictest terms. The Guardian's free Open
Platform API serves full text from 1999, including Opinion, Columnists and Letters. Its
terms, however, explicitly forbid any ML/AI use and any text/data "analysis or mining"
that generates patterns or trends. They also limit storage to 24 hours and reserve
rights under Art. 4(3) of the EU Digital Single Market (DSM) Directive. The website ToS
repeat this. So the Guardian is out unless licensed (Commercial key, which the access
page says covers "sentiment analysis"). The BBC forbids RAG, summarising, dataset
building and TDM. Mumsnet forbids copying "for any purpose" without a licence. The
Independent has a date archive from 1995, but its letters are "Member exclusive"
(paywalled) and its terms ban copying or storing without permission (no explicit AI
clause). That leaves Reddit (r/unitedkingdom since 2008, r/AskUK since 2011) as the
largest free, country-attributable source. The Reddit terms ban model training and
"shar[ing] Reddit Services and Data with any third party". Sending text to a commercial
LLM API is not explicitly addressed, but probably requires permission. Reddit's
research programme (r/reddit4researchers, linked from robots.txt) is the route to ask.

**1940–2005.** We found no free full-text source we could verify for 1940–1994. The
British Newspaper Archive is a paid subscription. Its free-to-view set ends in 1880.
The Independent's online archive starts in 1995 and the Guardian's in 1999 (both with
the restrictions above). The UK Web Archive starts in 2004, and most of it is viewable
only in reading rooms (searchable only to Dec 2022).

**Biggest gap (1940–2005):** all of **1940–1994**. A lead is the Spectator Archive
(archive.spectator.co.uk), reported as every issue July 1828 – December 2008 with OCR
(https://thenextweb.com/news/uk-magazine-the-spectator-finally-launches-its-180-year-online-archive).
That would include letters and opinion. The site served a bot-challenge page to our
client, so we could not verify its access model or terms, and it is not in the registry.
Verify it manually in a browser. Note that it is a single right-of-centre weekly, not a
national cross-section.

**Best for opinion / letters / forum genres:** opinion and letters: Guardian
(licence needed), Independent letters (paywalled); forum: r/unitedkingdom, r/AskUK,
Mumsnet (licence needed).

### Recommended thin-slice sources (GB, 2005–now)

1. `gb-reddit-unitedkingdom` + `gb-reddit-askuk`: free via the API, but first get
   written confirmation from Reddit (research access) that LLM-API tagging is allowed.
2. `gb-guardian-open-platform`: ask licensing@theguardian.com for a research or
   commercial licence covering tagging. It is the best opinion/letters source if granted.
3. `gb-gdelt-url-index` / `gb-common-crawl-news`: URL discovery only.
4. Fallback if neither Reddit nor the Guardian agrees: `gb-independent` opinion. Its
   editorials were marked free, but one comment piece and the letters were not. Ask the
   Independent first, because its terms ban copying without permission.

Plainly: under current terms **no GB source is cleared for LLM-API tagging today**.
The free sources either explicitly forbid it (Guardian, BBC, Mumsnet) or need
permission (Reddit, Independent). The GB thin slice cannot start until one permission
request succeeds. That request should be sent now.

### Dead ends and leads (GB)

- **Spectator Archive**: see above (lead, unverified).
- **British Newspaper Archive** pages (.co.uk redirects to .com) and the
  **UK Web Archive** site (webarchive.org.uk) returned 403. Facts for both come from
  British Library pages instead.
- **Other UK forums** (Digital Spy, MoneySavingExpert, PistonHeads) were not surveyed.
  Mumsnet was the one required.
- **Free letters-to-the-editor collections**: none found. Letters pages exist at the
  Guardian (restricted terms) and the Independent (Member exclusive). Historical letters
  are in the paid BNA and, if it proves accessible, the Spectator Archive.
