# Sources

Archive survey for the thin-slice countries, Greece (GR) and the United Kingdom (GB),
and for France (FR), Belgium (BE), Luxembourg (LU) and the Netherlands (NL), all
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

**1940–2005.** **Delpher** (`nl-delpher-kranten`) is the strongest single archive in this
batch. It holds almost 2 million newspaper issues 1618–1995, including all years of the
main national dailies (De Telegraaf, de Volkskrant 1920–1995, Trouw 1945–1995, Het Parool
1941–1995), with OCR. Post-war in-copyright runs are online under publisher agreements.
delpher.nl returned 403 to us, so we could not check per-title online access. For
machine access, the KB (`nl-kb-delpher-data`) offers SRU and OAI-PMH APIs on request. It
supports TDM/AI research but restricts in-copyright data to "niet-commercieel
wetenschappelijk onderzoek", sometimes only in its secure environments (KB_Datalab,
SANE). Sending post-1940 text to a commercial LLM API is not addressed.

**Biggest gap (1940–2005):** **1996–2004**. Delpher stops at 1995, the KB web archive
starts in 2007 (reading room only), and Reddit starts in 2014. FOK! and GeenStijl
(2002/2003 onwards) partly fill it.

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
