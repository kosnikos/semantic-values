# Sources

Archive survey for the thin-slice countries, Greece (GR) and the United Kingdom (GB),
and for France (FR), Belgium (BE), Luxembourg (LU) and the Netherlands (NL), and
Germany (DE), Austria (AT) and Switzerland (CH), all done on 2026-11-18. For each candidate we read the landing page, the terms of use or
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

## FR

**2005–now.** The big French dailies are closed to us. lefigaro.fr's robots.txt says any
use "autre qu'un usage strictement individuel (incluant notamment l'entraînement des
grands modèles de langage (LLM) ...)" needs a licence. Its CGU also ban robot extraction
for AI. FigaroVox opinion pieces were paywalled (`isAccessibleForFree: false`). Le Monde
and Libération use the same robots.txt wording: only "partenaires" may use content beyond
"usage strictement individuel". Both block CCBot and ClaudeBot. lemonde.fr served a bot
challenge to our client, so its paywall status rests on a 2020 press report. The best
free option is **AgoraVox** (`fr-agoravox`). It is a citizen-media site founded in March
2005, where readers write the articles ("Tribune libre") and comment on them. That is
very close to the project's "ordinary people" target. The authors are self-selected and
often anti-establishment, so treat its bias as a known limitation. Its legal notice bans
reproduction without prior permission but has no AI clause, so LLM use is `unknown`. For
forums, **r/france** (since 2008, ~18M comments, French-language) is the largest one we
could verify. jeuxvideo.com's "Blabla 18-25 ans" forum and Doctissimo are obvious
candidates, but we could not read their terms (see dead ends).

**1940–2005.** **Gallica** (`fr-gallica-presse`) is free and has an SRU full-text API.
It holds more than 13,000 press titles published before 1954. Post-1954 issues are
viewable only inside the BnF (Gallica intra muros). So free French press coverage ends
in 1953. We could not read Gallica's own terms page (Cloudflare 403; the Wayback copy
returned 429). RetroNews (BnF-Partenariats) covers the same 1631–1954 span behind a
subscription. Its CGU explicitly forbid "utilisation dans des systèmes d'intelligence
artificielle". The BnF web archive (from the early 2000s) can only be consulted in BnF
reading rooms.

**Biggest gap (1940–2005):** **1954–2004**. We found no free full-text French newspaper
for this period. Le Monde's and Le Figaro's own archives are subscriber-only, and both
publishers require a licence for non-individual use.

**Best for opinion / letters / forum genres:** opinion: AgoraVox (free), FigaroVox and
Le Monde Débats (licence needed); letters: none free found; forum: r/france.

### Recommended sources (FR, 2005–now)

1. `fr-agoravox`: free reader-written opinion since 2005. Ask the Fondation AgoraVox
   about LLM tagging.
2. `fr-reddit-france`: the largest French-language forum. The Reddit permission caveats
   apply (as for GB).
3. `fr-common-crawl-news`: URL discovery only. The main dailies block CCBot.
4. Licensing route: Le Figaro (syndication-service@lefigaro.fr) or Le Monde
   (syndication@lemonde.fr), if a budget for licences appears.

For 1940–1953, use `fr-gallica-presse` via its API, after asking the BnF whether it
allows LLM tagging of public-domain issues (the `access=fayes` documents).

### Dead ends and leads (FR)

- **jeuxvideo.com forums** (Blabla 18-25 ans): pages and the CGU returned 403 to curl
  and WebFetch. Its robots.txt disallows `/forums/message/*` for all crawlers. Terms not
  read. It is a major youth forum; check it manually.
- **Doctissimo forums**: the landing page loaded, but we found no terms link and the guessed
  CGU URLs returned 404.
- **Le Club de Mediapart** (blogs.mediapart.fr): reader-written blogs. A strong lead, but
  WebFetch could not fetch the participation charter and robots.txt blocks CCBot,
  ClaudeBot and GPTBot. Check it manually.
- **Le Monde pre-2005 archive**: could not be reached (lemonde.fr served a bot challenge
  to curl and WebFetch). The only access evidence is next.ink (2020), which says the
  subscription includes "l'ensemble des contenus et des archives". Treat it as
  subscriber-only, unverified.
- **Libération**: robots.txt has the same "licence only" wording as Le Monde and blocks
  CCBot. No separate entry.
- **20 Minutes**: robots.txt disallows GPTBot, CCBot and ClaudeBot. Its access model
  and terms were not read. **Ouest-France** returned 403.
- **GDELT**: no FR-specific facts gathered. See `gb-gdelt-url-index`.

## BE

**2005–now.** Belgian newspaper sites are mostly closed. De Standaard (Mediahuis) puts
an explicit Art. 4 CDSM reservation in robots.txt: no "text and data mining ... whether
for machine learning or artificial intelligence purposes or otherwise". Le Soir, HLN, De
Morgen, Het Nieuwsblad and 7sur7 returned 403 even to a browser-like client. The one
newspaper we could check is **La Libre Belgique** (`be-lalibre-website`). Its Débats
section carries outside op-eds and "ripostes", and two sampled 2026 opinions were
free (editorials were not). Its sales terms ban any reproduction "sous toute forme" (no AI
clause, but a total copying ban, so LLM use is `no`), and robots.txt blocks AI
crawlers. For forums, **forum.politics.be** (`be-politics-be-forum`) is a large Flemish
political forum with 11.2M posts since 2002.
r/belgium is mostly English, with expats in the mix. The language-specific subs are small.

**1940–2005.** **KBR BelgicaPress** (`be-kbr-belgicapress`) has 136 titles, 1814–1950,
with Le Soir to 1970 and Le Drapeau rouge to 1982, all with OCR. Issues up to 1918 are
open to everyone. Later issues need a free MyKBR login and a declaration that use falls
under the research or teaching exceptions of Belgian copyright law. That makes 1940–1950
(and Le Soir 1940–1970) usable for research, but whether the research exception covers
sending text to a commercial LLM API is unknown. KBR is digitising 1951–1989 dailies
(done by 2027).

**Biggest gap (1940–2005):** **1971–2004**. Only Le Drapeau rouge (to 1982) reaches past
1970, and nothing covers 1983–2004 until the KBR 1951–1989 project lands.
There is no public Belgian web archive: KBR's archive is "in development", per IIPC.

**Best for opinion / letters / forum genres:** opinion: La Libre Débats (partly free);
forum: forum.politics.be (Dutch), r/belgium (English).

### Recommended sources (BE, 2005–now)

1. `be-lalibre-website` (Débats/opinions): ask IPM about LLM tagging first.
2. `be-politics-be-forum`: Dutch-language Belgian forum voice. The terms are unknown, so
   contact the operator.
3. `be-reddit-belgium`: English, with the Reddit caveats.
4. `be-common-crawl-news`: URL discovery only.

Flanders (De Standaard and DPG titles) has no usable 2005–now newspaper source today.
Belgian coverage will be francophone-heavy unless Mediahuis or DPG grant a licence.

### Dead ends and leads (BE)

- **De Standaard**: robots.txt carries the TDM/AI reservation quoted above, and the site
  returned 403. No entry.
- **Le Soir, HLN, De Morgen, Het Nieuwsblad, 7sur7**: 403 on the landing pages (and for
  lesoir.be and hln.be, on robots.txt too). Access model and terms were not verified.
- **Belgian web archive** (KBR PROMISE/BelgicaWeb): IIPC lists "Access methods:
  currently in development" (https://netpreserve.org/about-us/members/kbr/). No entry.
- **RTBF / VRT NWS**: public broadcasters, reachable but mostly straight news. Not
  surveyed further.

## LU

**2005–now.** **RTL.lu** (`lu-rtl-lu`) is free and publishes readers' letters
(Lieserbréiwer) and guest op-eds (Carte blanche) in Luxembourgish. That makes it the most
direct "society's voice" source in this batch. Its comment threads, however, are visible
for only about two weeks, so they cannot be used as an archive. The terms ban reproducing
or commercially exploiting the service. They allow short extracts "à des fins
d'information ou de recherche", and they have no AI clause. tageblatt.lu (Meinung, Forum,
Leserbriefe) is metered. Its robots.txt reserves TDM and forbids automated mining
without permission. wort.lu (Mediahuis) carries the same CDSM TDM/AI reservation as De
Standaard and NRC, and returned 403. L'essentiel is free but mostly news, and it limits
use to personal use. r/Luxembourg is English and probably expat-dominated.

**1940–2005.** Luxembourg is the best-covered country in this batch. **eluxemburgensia.lu**
(`lu-eluxemburgensia`) has the Luxemburger Wort free online for 1848–1980 (1951–1980
added in 2021 under an agreement with the publisher; PDF download only inside the BnL).
Since 26 May 2026 it also has Tageblatt for 1951–2014. Tageblatt is "rooted in the labour and
trade union movement" (BnL), so it gives a second editorial line next to the Wort. The
Lëtzebuerger Journal 1948–2020 is being digitised. We could not read the
portal's own copyright page (JavaScript-only). BnL's FAQ only says that all use "must comply
with copyright law". BnL runs its own newspaper chatbot on OpenAI models. That gives us
no right, but it suggests BnL may be open to an LLM-tagging request.

**Biggest gap (1940–2005):** the 1981–2004 Wort (microfilm only) is missing. Tageblatt
covers that period, but as a single title. No free source covers
Luxembourgish-language forum voice before RTL's recent letters.

**Best for opinion / letters / forum genres:** letters/opinion: RTL.lu Lieserbréiwer
and Carte blanche (free), Tageblatt Forum/Leserbriefe (metered, TDM reserved);
historical letters/opinion: Wort and Tageblatt via eluxemburgensia; forum: r/Luxembourg
(weak).

### Recommended sources (LU)

1. `lu-eluxemburgensia`: Wort 1940–1980 and Tageblatt 1951–2014. The best long series
   in the batch. Ask BnL about LLM tagging and per-text publication.
2. `lu-rtl-lu`: Luxembourgish letters and op-eds, 2024 onwards (archive depth unverified).
   Ask RTL.
3. `lu-tageblatt-website`: only with permission (syndication@tageblatt.lu), to extend
   Tageblatt past 2014.
4. `lu-reddit-luxembourg`: low priority (English, expats).

### Dead ends and leads (LU)

- **Luxemburger Wort website** (wort.lu): 403. Its robots.txt carries the Mediahuis
  CDSM TDM/AI reservation. No entry; see `lu-common-crawl-news`.
- **Reporter.lu, Le Quotidien**: reachable, but not surveyed further. BnL offers free
  access to journal.lu "only ... on library premises" and partners with Reporter Media
  and other publishers for on-site access (2023 release).
- **Luxembourg Web Archive** (`lu-web-archive`): on-site only, but it does preserve the
  news-media sites (and so RTL comments) since June 2020.

## NL

**2005–now.** The Dutch quality press is closed to us. NRC (`nl-nrc-website`) carries
the Mediahuis Art. 4 CDSM TDM/AI reservation in robots.txt, and all sampled opinion and
letters pages were paywalled. de Volkskrant, Trouw, NU.nl (DPG) and De Telegraaf returned
403. The free options are forums. **r/thenetherlands** (Dutch-language, since 2014,
6.4M comments) and **FOK!forum** (since at least 2002) are the main ones. FOK!'s terms
ban copying beyond personal use, with no AI clause. **GeenStijl** (since 2003) is free
and has very active reader comments, but it is a one-sided provocative blog, and we found
no reuse terms.

**1940–2005.** **Delpher** (`nl-delpher-kranten`) is the largest archive in this batch,
but only part of it is free. *What exists:* almost 2 million newspaper issues 1618–1995,
including all years of the main national dailies (De Telegraaf, de Volkskrant 1920–1995,
Trouw 1945–1995, Het Parool 1941–1995), with OCR. *What is free:* the KB says only that
the files are "voor een deel vrij toegankelijk". Newspapers older than 140 years are
public domain, and newer ones are "vaak nog wel auteursrechtelijk ... beschermd". A 2017
press report says the post-war Volkskrant, Trouw and Parool runs were put online with
publisher consent. No page we could open gives the free/restricted split by title or
year: delpher.nl, including its help pages, returned 403 again on re-try. Both Delpher
routes are therefore recorded as `partial_paywall`, and the post-1940 free share must be
checked in a browser before we rely on it. For machine access, the KB
(`nl-kb-delpher-data`) offers SRU and OAI-PMH APIs on request. Only its 1618–1879 bulk
set is open. It supports TDM/AI research but restricts in-copyright data to
"niet-commercieel wetenschappelijk onderzoek", sometimes only in its secure environments
(KB_Datalab, SANE). Sending post-1940 text to a commercial LLM API is not addressed. The
KB's AI statement says it has blocked commercial crawling of Delpher but will not hinder
academic reuse.

**Biggest gap (1940–2005):** **1996–2004**. Delpher stops at 1995, the KB web archive
starts in 2007 (reading room only), and Reddit starts in 2014. FOK! and GeenStijl
(2002/2003 onwards) partly fill it. Until the free share of Delpher is verified,
**1940–1995** is also only conditionally covered: the content exists, but free access
is unconfirmed.

**Best for opinion / letters / forum genres:** opinion/letters: NRC (paywall, TDM
reserved), Delpher dailies' letters columns (1940–1995); forum: r/thenetherlands, FOK!,
GeenStijl comments.

### Recommended sources (NL)

1. `nl-kb-delpher-data` / `nl-delpher-kranten`: 1940–1995. Ask the KB whether LLM-API
   tagging (or an on-premise or open-weights alternative in SANE) is possible.
2. `nl-reddit-thenetherlands`: Dutch-language forum, with the Reddit caveats.
3. `nl-fok-forum`: long-running general forum. Ask FOK! (blanket copying ban).
4. `nl-geenstijl`: only alongside other sources, because of its one-sided readership.
5. `nl-common-crawl-news`: URL discovery only.

### Dead ends and leads (NL)

- **de Volkskrant, Trouw, NU.nl (NUjij comments), De Telegraaf**: 403 on the landing
  pages (and for volkskrant.nl and nu.nl, on robots.txt too). Access model and terms were
  not verified. NUjij is a strong lead for reader comments.
- **NOS**: public broadcaster, reachable, but straight news. Not surveyed.
- **r/Netherlands**: English and expat-heavy. Recorded in the notes of
  `nl-reddit-thenetherlands`.

## DE

Scope note for DE, AT and CH: the owner made newspapers the core v0 source (opinion,
columns, letters, editorials first, then news). Forums, subreddits and comment sections
are out of scope for v0 and were not surveyed. The effort went into newspaper routes and
into research-access programmes instead.

**2005–now.** *What exists:* every major title has a large online archive with opinion
and letters sections. *What is free:* very little that we can use. **taz.de**
(`de-taz-website`) is the exception. Articles from 1991, 2015 and 2023 were all flagged
free, and taz relies on voluntary "taz zahl ich" payments. But its Impressum reserves
commercial TDM (§ 44b UrhG) and allows copying into databases only "für den privaten
Gebrauch". **DER SPIEGEL** is free up to about the end of 2009 (`de-spiegel-print-archive`,
with readers' letters ("Briefe") in every issue). From 2010 it is mostly SPIEGEL+
(`de-spiegel-website`). Spiegel's terms reserve TDM, ban AI use, and ban "die automatisierte
Analyse, Auswertung oder Aufbereitung" and "Ablage in fremden Speichersystemen ('Cloud')",
so LLM use is `no`. **DIE ZEIT** (`de-zeit-website`, archive from 1946) blocks all
non-allow-listed bots with a 403 and a § 44b notice. We could not measure its free/Z+
split, and its 2012 public API is gone (404). For research access, **DWDS**
(`de-dwds-zeitungskorpora`; Zeit 1946–2025, Spiegel, FAZ, Tagesspiegel, Berliner Zeitung)
and **IDS DeReKo** (`de-ids-dereko`, 63.8 billion words) let you search these papers. Both
are concordance-only. Results are limited to citation-length quotes, and automated
evaluation needs permission. Neither delivers full text for LLM tagging.

**1940–2005.** The **Spiegel print archive 1947–2009** is the best free national run.
It is a weekly magazine with letters and commentary, but it is one title with one
editorial line. The free cut-off was observed from `isAccessibleForFree` flags on sampled
issues (all true up to 2009, all false from 2010); it is not documented. The **Deutsches
Zeitungsportal** (`de-zeitungsportal`, 1609–1994, 37M pages, free, with API) covers
1940–1950 well, but post-war titles depend on what partner libraries add, and the
post-1950 share was not measured. **ZEFYS DDR-Presse** (`de-zefys-ddr-presse`) has
Neues Deutschland, Berliner Zeitung and Neue Zeit, 1945–1990/94, free with login. These
are state/party papers, so they give official voice for the GDR, not society's voice.
taz covers 1991 onward (1986 according to unverified search snippets).

**Biggest gap:** a free, licensable West German daily for **1950–1990**. FAZ, SZ and
Welt archives were not found free (not surveyed in depth). The Zeitungsportal's post-war
holdings are patchy. From 2010 onward, the free option is taz alone (one left-leaning
title, TDM reserved).

**Legal lead (not a permission):** § 60d UrhG allows reproductions for text and data
mining for non-commercial scientific research. It covers research organisations,
heritage institutions and "individual researchers who pursue no commercial aim"
(gesetze-im-internet.de/urhg/__60d.html, read via WebFetch summary). DWDS explicitly
carves out "sofern nicht über § 60d UrhG zulässig". Whether § 60d covers sending text to
a commercial LLM API, or publishing per-text tags in a blog, is a legal question we have
not settled. It needs legal advice before we rely on it.

**Best for opinion / letters genres:** letters: Spiegel "Briefe" 1947–2009 (free, terms
forbid automated analysis); opinion/columns: taz (free, TDM reserved), Spiegel/Zeit
(paywall/blocked); research search: DWDS, DeReKo (KWIC only).

### Recommended sources (DE)

1. `de-taz-website`: the only free daily with 1991–now opinion. Ask lizenzen@taz.de
   whether research LLM tagging and per-text URL/tag publication is acceptable.
2. `de-spiegel-print-archive`: 1947–2009 with letters. Ask syndication@spiegel.de for a
   research licence. The terms as written forbid our use.
3. `de-zeitungsportal`: 1940–1950 and whatever post-war regional titles partners have
   added. Check rights statements per title (API with a free DDB key).
4. `de-zeit-website`: ask crawl-request@zeit.de. Zeit would be the best opinion source
   1946–now if it could be licensed.
5. `de-dwds-zeitungskorpora` / `de-ids-dereko`: for vocabulary validation only, not as a
   text source.

### Dead ends and leads (DE)

- **DIE ZEIT Content API** (developer.zeit.de): 404, discontinued.
- **zeit.de pages**: 403 to curl and WebFetch. We used one Internet Archive snapshot of
  the 2005 year index to confirm the archive structure, and stopped there.
- **FAZ, Süddeutsche Zeitung, Welt, Bild**: not surveyed. They are known to be paywalled
  (FAZ is in DWDS for KWIC only).
- **DNB Webarchiv** (`de-dnb-web-archive`): selective, reading rooms in Leipzig and
  Frankfurt only.
- **Forums / comments** (out of v0 scope): not surveyed.

## AT

**2005–now.** *What exists:* Der Standard, Die Presse, Kurier and Krone, each
with an opinion section. *What is free:* **DER STANDARD**
(`at-derstandard-website`) is free to read. Its AGB say the service is provided
"unentgeltlich" and financed by advertising, with an ad-free PUR subscription as the
alternative. We could not see article pages (consent wall), so archive depth and genre
labels are unverified. The AGB reserve commercial TDM under § 42h (6) UrhG and Art. 4(3)
DSM, and limit use to "den privaten Eigenbedarf". **Die Presse** (`at-diepresse-website`)
is partly paywalled (2 of 3 sampled columns locked). Its robots.txt bans TDM "for the
training of AI", which leaves inference use unaddressed. **Krone** (krone.at) robots.txt
prohibits TDM under § 42h (6) and "the development of any ... large language models
(LLMs)"; no entry. Kurier was not surveyed beyond robots.txt.

**1940–2005.** **ANNO** (`at-anno`, ÖNB: 28M pages, 1,600+ titles, free) is the main
route. *What exists:* its title list includes the main post-war dailies (Die Presse to
2023, Arbeiter-Zeitung to 1985, Kurier from 1954/1959, Oberösterreichische Nachrichten
1945–2019, Tiroler Tageszeitung 1945–1993, Vorarlberger Nachrichten 1945–1989, KPÖ
Volkswille). *What is free:* the home page links 1953–57 issues of several dailies
directly, so at least the 1950s are open. We could not check which later years are
online per title, because the title calendars sit behind a Cloudflare challenge. ÖNB
claims no own rights in its scans but leaves third-party (publisher) rights to the user.
**Arbeiter-Zeitung 1945–1989** (`at-arbeiterzeitung-archive`) is free with a free
account. It has full text, 200,000+ pages, and is run as a non-commercial R&D project.
It is the social-democratic party paper.

**Biggest gap:** **1990–2005**, with no free route at all. Before 1990 coverage depends on
ANNO's per-title online years, which are unverified. Also, no free source carries an
open licence for post-war text.

**Research access lead:** the **Austrian Media Corpus (amc)**, an ÖAW ACDH-CH / APA
cooperation with Austrian press from 1986, is the obvious research route. All its pages
(oeaw.ac.at, arche.acdh.oeaw.ac.at) returned 403 three times, so it gets no entry. Search
snippets say it is searchable on-site via Sketch Engine. Its AT part also feeds the DWDS
ZDL-Regionalkorpus, whose terms exclude "jede kommerzielle, journalistische bzw.
publizistische Nutzung" (see `de-dwds-zeitungskorpora`). Contact ACDH-CH directly.

**Best for opinion / letters genres:** opinion: Der Standard (free, TDM reserved), Die
Presse (partly paywalled); historical letters/opinion: ANNO dailies, Arbeiter-Zeitung.

### Recommended sources (AT)

1. `at-anno`: verify per-title online years in a browser, then ask ÖNB and publishers
   (Die Presse, Kurier) about research tagging.
2. `at-derstandard-website`: ask legal@derstandard.at about a research licence for
   2005–now opinion.
3. `at-arbeiterzeitung-archive`: 1945–1989, with an editorial-line caveat. Ask
   Medienhaus Wien.
4. amc (ACDH-CH): ask about research access covering 1986–now.

### Dead ends and leads (AT)

- **ANNO title calendars**: Cloudflare Turnstile. We did not try to get around it.
- **Austrian Media Corpus**: 403 (see above).
- **ÖNB Webarchiv Österreich**: the landing page shows only a title, so access terms
  were not verified. No entry.
- **Kurier, Salzburger Nachrichten, Kleine Zeitung**: not surveyed.
- **Forums / Der Standard postings** (out of v0 scope): not surveyed.

## CH

**2005–now.** *What exists:* NZZ, Tages-Anzeiger, Le Temps and the other big Swiss
titles. *What is free:* nothing that we found. **NZZ** (`ch-nzz-website`) opinion is
paywalled (3/3 locked), and per the FHNW library the NZZ prohibits AI/ML use "outside of
special agreements". **Le Temps** (`ch-letemps-website`) marks opinion "Réservé aux
abonnés" and signals `ai-train=no, use=reference` as an Art. 4 DSM reservation.
tagesanzeiger.ch loops on redirects and disallows CCBot. The real route is research
access: **Swissdox@LiRI** (`ch-swissdox-liri`, University of Zurich and SMD). It holds
about 24M articles from 260 Swiss sources (CH Media, NZZ, Ringier, TX/Tamedia, SRG, Le
Temps, Weltwoche, WOZ), in German and French, through an API "for project related
academic use only". Costs run from CHF 1,000 per 30-day single-user project. Data must
stay on academic IT and may not go to third parties, so a commercial LLM API is doubtful.
Derived data ("derivates") need not be deleted.

**1940–2005.** French-speaking Switzerland is well served. **letempsarchives.ch**
(`ch-letempsarchives`) is free, article-segmented, and has Journal de Genève 1826–1998,
Gazette de Lausanne 1798–1998 and Le Nouveau Quotidien 1991–1998: about 3.9M articles,
liberal titles. For German, Italian and Romansh, **e-newspaperarchives.ch**
(`ch-e-newspaperarchives`, Swiss National Library) is free, with 15M pages from 200+
titles from 1692 "bis heute". The site returned 403 to us, so which post-1940 years are
online per title is unknown, and so are the terms.

**Biggest gap:** German-speaking Switzerland 1940–2005 (unverified until e-npa can be
checked in a browser), and any free 2005–now opinion source. Swissdox is the only
licensable 2005–now route, and it requires an academic affiliation.

**Best for opinion / letters genres:** historical: Journal de Genève / Gazette de
Lausanne (free); 2005–now: Swissdox (academic fee), NZZ/Le Temps (paywall).

### Recommended sources (CH)

1. `ch-letempsarchives`: French-Swiss 1940–1998, free. Ask Le Temps about LLM tagging
   and per-text publication.
2. `ch-swissdox-liri`: the 2005–now route, if an academic partner can hold the
   subscription. Ask LiRI whether sending text to a commercial LLM API counts as
   "sharing with third parties".
3. `ch-e-newspaperarchives`: check post-1940 German-Swiss titles in a browser, then ask
   the National Library.

### Dead ends and leads (CH)

- **e-newspaperarchives.ch**: 403 (curl and WebFetch, including robots.txt).
- **impresso** (impresso-project.ch): a research platform over Swiss and Luxembourg
  newspapers including Le Temps and NZZ collections (per a directory entry). The app and
  terms pages are JavaScript-only. A lead for research access.
- **Webarchiv Schweiz**: selective, "on the premises of the National Library and those
  of its partner institutions" only, and reproduction is not permitted (NL FAQ). No entry.
- **Tages-Anzeiger** (tagesanzeiger.ch): redirect loop; robots.txt disallows CCBot.
- **Forums / comments** (out of v0 scope): not surveyed.
