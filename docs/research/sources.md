# Sources

Archive survey for the thin-slice countries, Greece (GR) and the United Kingdom (GB),
and for France (FR), Belgium (BE), Luxembourg (LU) and the Netherlands (NL), and
Germany (DE), Austria (AT) and Switzerland (CH), and Italy (IT), Spain (ES) and Portugal (PT), all done on 2026-11-18. For each candidate we read the landing page, the terms of use or
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

- **Spectator Archive**: see above (lead, unverified). Task 5e read spectator.com/terms:
  any use "for any purpose" needs prior written consent (`all_reuse`), so it is closed
  in GB too unless licensed.
- **British Newspaper Archive** pages (.co.uk redirects to .com) and the
  **UK Web Archive** site (webarchive.org.uk) returned 403. Facts for both come from
  British Library pages instead.
- **Other UK forums** (Digital Spy, MoneySavingExpert, PistonHeads) were not surveyed.
  Mumsnet was the one required.
- **Free letters-to-the-editor collections**: none found. Letters pages exist at the
  Guardian (restricted terms) and the Independent (Member exclusive). Historical letters
  are in the paid BNA and, if it proves accessible, the Spectator Archive.

### Wider sweep (Task 5e)

**Title list.** National dailies and Sundays, and the main regional dailies, come from
Wikipedia's [List of newspapers in the United Kingdom by circulation](https://en.wikipedia.org/wiki/List_of_newspapers_in_the_United_Kingdom_by_circulation)
(ABC figures). Circulation below is the latest figure that page gives (Jan 2025 unless
noted). Magazines come from the owner's lists. We cross-checked them against Wikipedia's
[List of magazines in the United Kingdom](https://en.wikipedia.org/wiki/List_of_magazines_in_the_United_Kingdom),
which names every title below except UnHerd, Good Housekeeping and Reader's Digest. We found
no cited magazine circulation figures (n/a).
Guardian, Observer, BBC and Independent are covered above. We checked 30 titles, all of
them listed in the two tables below: 11 newspapers and 19 magazines. 13 of the 30 are
registered (rows marked **Registry**) and 17 are not. For each,
robots.txt, the terms page, and one to three sample article pages (paywall flag and
whether the body is in the HTML). "Open" uses the GB rule: `tdm_all` and (per the later
controller ruling) `all_reuse` are both open under CDPA s.29A(5).

One judgement call matters for GB. DMG Media (Daily Mail, i), Future plc (Woman & Home,
The Week) and Prospect use near-identical TDM clauses. Each one bans TDM and scraping but
says it "shall not apply insofar as ... we are unable to exclude or limit text/data mining
or web scraping activity by contract under the laws which are applicable to us". We class
these as `tdm_all`, so they are open in GB. Reach plc (Mirror, MEN, OK!) instead bans
"any automated means, including bots, scrapers, crawlers, spiders, AI agents" outright, and
bans "Any other use ... (including without limitation reproduction for a purpose ...)"
without written permission. We class Reach as `all_reuse`. Controller ruling (after the sweep): under s.29A(5) GB
`all_reuse` also counts as open, so Reach, the Times, FT, Scotsman, Spectator, New Statesman
and Radio Times are not excluded by their terms. A follow-up access check registered the
three Reach titles (Mirror, MEN, OK!); the others stay unregistered for the access reasons
in the tables (paywall, crawler block or no free part).

#### Newspapers

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| Daily Mail / MailOnline | tdm_all | 687,063 | **Registry** `gb-daily-mail`. Open (s.29A). Debate columns served without login; Mail+ items are paywalled; sitemap from 1994. | `evidence_urls` of registry entry `gb-daily-mail` |
| The i Paper | tdm_all | 122,487 | **Registry** `gb-inews`. Open (s.29A). 3/3 opinion pieces served; there is a subscriber tier; sitemap from 2016. | `evidence_urls` of registry entry `gb-inews` |
| Evening Standard | copyright_boilerplate | 314,285 (2023) | **Registry** `gb-evening-standard`. Free (2/2 `isAccessibleForFree` true); archive from 1998. | `evidence_urls` of registry entry `gb-evening-standard` |
| The Times / Sunday Times | all_reuse | 368,929 (2020) | robots.txt: "The Times does not permit the unlicensed use of our content for large language models", and `User-agent: *` `Disallow: /`, so our crawler is blocked. Subscription. The terms page served a device-verification challenge. | https://www.thetimes.com/robots.txt ("does not permit the unlicensed use of our content for large language models"); https://www.thetimes.com/static/terms-and-conditions (challenge page) |
| Financial Times | all_reuse | 109,995 | Terms "expressly prohibit any use of our content or data ... in any manner for any machine learning and/or artificial intelligence purposes, including ... to generate any data or content". Subscription. | https://help.ft.com/legal-privacy/terms-and-conditions/ ("expressly prohibit any use of our content or data ... for any machine learning and/or artificial intelligence purposes"); https://www.ft.com/robots.txt |
| Daily Telegraph | unknown | 360,345 (2020) | Blocked: terms pages returned HTTP 429 to curl and WebFetch. robots.txt blocks CCBot, ClaudeBot, GPTBot and others. | https://www.telegraph.co.uk/terms-and-conditions/ and https://www.telegraph.co.uk/customer-service/terms-conditions/ (both HTTP 429); https://www.telegraph.co.uk/robots.txt |
| Daily Mirror | all_reuse | 205,332 | **Registry** `gb-mirror`. Open (s.29A(5)). Reach terms ban "any automated means, including bots, scrapers, crawlers, spiders, AI agents" and any other use without permission. 2 of 3 Opinion pieces free (one Premium); oldest page seen 2013. | `evidence_urls` of registry entry `gb-mirror` |
| Manchester Evening News | all_reuse | 20,993 (2020) | **Registry** `gb-manchester-evening-news`. Open (s.29A(5)); same Reach terms. 4/4 news pages free; no opinion section found; oldest page seen 2019. | `evidence_urls` of registry entry `gb-manchester-evening-news` |
| The Scotsman | all_reuse | n/a | robots.txt: AI training, dataset creation or bulk extraction "NOT permitted without written agreement and payment of £650 per page viewed". The linked Iconic Media contract allows free access only for "reading by individuals for their own personal use" and search, and says "You must not make any AI Use", which includes "any use of Content to generate, ground or inform the output of an AI Model". | https://www.scotsman.com/robots.txt ("payment of £650 per page viewed"); https://www.mediaconcierge.co.uk/ai-usage-contract-v1/ ("You must not make any AI Use of the Content without a written licence") |
| Yorkshire Post | all_reuse | 13,284 (2020) | Identical robots.txt and contract to the Scotsman (same publisher). | https://www.yorkshirepost.co.uk/robots.txt (byte-identical to the Scotsman's); https://www.mediaconcierge.co.uk/ai-usage-contract-v1/ ("You must not make any AI Use") |
| The Herald (Glasgow) | copyright_boilerplate | 28,872 (2020) | Newsquest terms: "you will not otherwise copy, store, distribute ... create a database ... without our written permission". Open, but two sampled opinion pages served only ~80 words of body in the HTML, so we found no free part. Not registered. | https://www.newsquest.co.uk/legal/terms-conditions/ (reached from the heraldscotland.com footer via https://www.newsquest.co.uk/legal/); samples https://www.heraldscotland.com/opinion/26738773.named-person-law-wouldnt-helped-family-c-scandal/, https://www.heraldscotland.com/opinion/26738516.scottish-government-owned-prestwick-airport-delivers-style/ |

#### Magazines

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| The Conversation UK | ai_training_only | n/a | **Registry** `gb-conversation-uk`. CC BY-ND; only AI training banned. Free, from 2013. Written by academics. | `evidence_urls` of registry entry `gb-conversation-uk` |
| openDemocracy | none | n/a | **Registry** `gb-opendemocracy`. CC BY-NC 4.0 on article pages. Free, from 2004 or earlier. | `evidence_urls` of registry entry `gb-opendemocracy` |
| Prospect | tdm_all | n/a | **Registry** `gb-prospect`. Open (s.29A). Piano subscription; sampled pages served their body. Sitemap from 1995. | `evidence_urls` of registry entry `gb-prospect` |
| UnHerd | copyright_boilerplate | n/a | **Registry** `gb-unherd`. Personal-use terms, no TDM/AI clause; 1 of 2 essays was free. From 2018. | `evidence_urls` of registry entry `gb-unherd` |
| HELLO! | copyright_boilerplate | n/a | **Registry** `gb-hello`. Celebrity weekly; 1 of 2 pages free. From 2001. | `evidence_urls` of registry entry `gb-hello` |
| Good Housekeeping UK | copyright_boilerplate | n/a | **Registry** `gb-good-housekeeping-uk`. Hearst "solely for personal use"; sampled page free. | `evidence_urls` of registry entry `gb-good-housekeeping-uk` |
| Woman & Home | tdm_all | n/a | **Registry** `gb-woman-and-home`. Future terms (open, s.29A); 2/2 pages free. Sitemap from 2005. | `evidence_urls` of registry entry `gb-woman-and-home` |
| The Spectator | all_reuse | n/a | Terms: Content "may not be used, reproduced, duplicated, copied, sold, resold, accessed, modified, or otherwise exploited, in full or in part, for any purpose without our prior written consent". | https://spectator.com/terms/ ("for any purpose without our prior written consent") |
| New Statesman | all_reuse | n/a | Terms (read via WebFetch; curl got 403): "you are not allowed to copy or use anything on our site for any other purpose, unless authorised by the New Statesman. This includes not only business and commercial but also educational purposes." | https://www.newstatesman.com/terms-and-conditions (WebFetch; "not allowed to copy or use anything on our site for any other purpose") |
| The Economist | unknown | n/a | Blocked: 403 to curl, WebFetch refused. robots.txt blocks GPTBot, CCBot, Claude-* and others. | https://www.economist.com/ (403); https://www.economist.com/legal/terms-of-use (WebFetch refused); https://www.economist.com/robots.txt |
| London Review of Books | copyright_boilerplate | n/a | Terms: "you may not download, store, disseminate, republish, post, reproduce ... in any form without the prior written permission". Both sampled current-issue pieces had `isAccessibleForFree` false. We found no free part, so not registered. | https://www.lrb.co.uk/terms; samples https://www.lrb.co.uk/the-paper/v48/n21/alex-de-waal/an-atrocity-foretold, https://www.lrb.co.uk/the-paper/v48/n21/alexander-zevin/peace-and-goodwill; https://www.lrb.co.uk/robots.txt |
| The Critic | copyright_boilerplate | n/a | "Content accessed by users is for their personal use only." Two sampled articles served ~250 words (truncated), so no free part was found. | https://thecritic.co.uk/terms-and-conditions/; samples https://thecritic.co.uk/against-the-porn-ban/, https://thecritic.co.uk/britains-china-problem/ |
| The Week (UK) | tdm_all | n/a | Future terms (open in GB), but the sampled article had `isAccessibleForFree` "False". theweek.com now mixes the US and UK editions. Not registered. | https://futureplc.com/terms-and-conditions-uk/ ("You shall not conduct, facilitate, authorise or permit any text or data mining"); sample https://theweek.com/defence/china-f35-parts-hong-kong-us |
| Private Eye | unknown | n/a | The website "showcases a few selected highlights from the current issue". Too little web text; we found no terms page. | https://www.private-eye.co.uk/about; https://www.private-eye.co.uk/robots.txt (404) |
| Radio Times | all_reuse | n/a | robots.txt: "Content-signal: search=yes, ai-input = no, ai-train=no", with "As a condition of accessing this website, you agree to abide by the following content signals". `ai-input` covers feeding content to AI models, i.e. our LLM tagging. Immediate Media terms allow access only "for your own personal and non-commercial use and not for any commercial or other purposes". | https://www.radiotimes.com/robots.txt ("ai-input = no, ai-train=no"); https://www.immediate.co.uk/terms-and-conditions/ ("not for any commercial or other purposes") |
| OK! | all_reuse | n/a | **Registry** `gb-ok-magazine`. Open (s.29A(5)); same Reach terms. 4/4 pages free; oldest page seen 2017. | `evidence_urls` of registry entry `gb-ok-magazine` |
| Woman's Weekly | tdm_all | n/a | womansweekly.com redirects (301) to goodto.com (GoodtoKnow, Future plc). The magazine has no separate web text, so not registered. | https://www.womansweekly.com/ (301 to https://www.goodto.com/); https://futureplc.com/terms-and-conditions-uk/ ("You shall not conduct, facilitate, authorise or permit any text or data mining") |
| Reader's Digest UK | unknown | n/a | readersdigest.co.uk: the connection failed (no HTTP response). | https://www.readersdigest.co.uk/ and /robots.txt (no response) |
| The People's Friend | unknown | n/a | 403 to curl (homepage and robots.txt). | https://www.thepeoplesfriend.co.uk/ and /robots.txt (403) |

#### Open titles shortlist (GB), ranked by fit

Newspapers:

1. `gb-daily-mail`: the largest daily (687k). Named opinion columnists, sitemap back to
   1994, mostly free. Open only via s.29A (the terms ban TDM). Its right-of-centre tabloid
   slant needs a counterweight.
2. `gb-mirror`: left-of-centre tabloid (205k) with Opinion pieces and "leaders"
   editorials; mostly free, some Premium. Oldest page seen 2013. Balances the Mail's slant.
3. `gb-inews`: centrist opinion desk, free opinion pieces, from 2016. Also open via s.29A.
4. `gb-evening-standard`: free Comment section, archive from 1998, boilerplate terms only.
   London-centred.
5. `gb-manchester-evening-news`: free regional news; no opinion section found, so low fit.

Magazines:

1. `gb-prospect`: monthly essays and politics from 1995; open via s.29A. The paywall's
   effect on bulk access has not been tested.
2. `gb-opendemocracy`: CC BY-NC, free, from 2004. Left-leaning and international, so
   filter to UK sections.
3. `gb-unherd`: heterodox opinion from 2018; partly paywalled.
4. `gb-conversation-uk`: CC BY-ND academic commentary from 2013; low "ordinary voice" fit.
5. Popular-magazine stream: `gb-hello`, `gb-ok-magazine`, `gb-woman-and-home`,
   `gb-good-housekeeping-uk`.
   They are open and largely free, but mostly celebrity and lifestyle copy.

Letters pages were not checked title by title in this sweep. The s.29A conditions in spec
§3 apply to everything above.

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
- **Le Club de Mediapart** (blogs.mediapart.fr): now registered as `fr-mediapart-club`
  (Task 5e). Earlier note: reader-written blogs. A strong lead, but
  WebFetch could not fetch the participation charter and robots.txt blocks CCBot,
  ClaudeBot and GPTBot. Check it manually.
- **Le Monde pre-2005 archive**: could not be reached (lemonde.fr served a bot challenge
  to curl and WebFetch). The only access evidence is next.ink (2020), which says the
  subscription includes "l'ensemble des contenus et des archives". Treat it as
  subscriber-only, unverified.
- **Libération**: robots.txt has the same "licence only" wording as Le Monde and blocks
  CCBot. No separate entry.
- **20 Minutes**: robots.txt disallows GPTBot, CCBot and ClaudeBot. Its access model
  and terms were not read. **Ouest-France** returned 403. (Task 5e read both: 20 Minutes
  is `tdm_all`; Ouest-France's robots.txt blocks all agents. See Wider sweep.)
- **GDELT**: no FR-specific facts gathered. See `gb-gdelt-url-index`.

### Wider sweep (Task 5e)

**Title list.** Newspapers come from French Wikipedia's
[Liste de journaux en France](https://fr.wikipedia.org/wiki/Liste_de_journaux_en_France),
which names all eleven dailies below. Magazines come from the owner's lists.
Circulation (DFP, copies per issue, 2025) is from the ACPM 2025 results as reported by
[CB News, 28 April 2026](https://www.cbnews.fr/node/100535). That page gives no figure
for the titles marked n/a. Le Monde, Le Figaro, RetroNews, Gallica and AgoraVox are
covered above. We checked 33 titles, all listed below: 11 newspapers and 22 magazines.
5 are registered and 28 are not. We read robots.txt, the CGU or mentions légales, and one or
two sample pages each.

Under the EU rule, French titles fall into two groups. Bayard (La Croix, Notre Temps,
Pèlerin), Prisma (Femme Actuelle; probably Télé-Loisirs, unverified), Elle and 20 Minutes make an express
L.122-5-3 / Art. 4(3) TDM opt-out (`tdm_all`). Most of the others use the same clause
Le Monde uses: "seule ... l'utilisation pour un usage privé ... toute autre utilisation
est constitutive de contrefaçon", or "de quelque nature que ce soit ... dans quelque but
que ce soit". We class that as `all_reuse`, following the Le Monde and La Libre entries.
Only redistribution-only boilerplate (Slate.fr, Mediapart, VSD) and titles whose terms we
could not read stay open. The line (controller ruling): clauses that restrict *use* ("toute autre
utilisation", "dans quelque but que ce soit", "for any purpose") are `all_reuse`; clauses
that restrict only reproduction, representation or redistribution are
`copyright_boilerplate`.

#### Newspapers

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| L'Humanité | unknown | n/a | **Registry** `fr-humanite`. The legal notice could not be read (script shell; WebFetch refused). Partly free; sitemap from 1997. | `evidence_urls` of registry entry `fr-humanite` |
| Libération | all_reuse | n/a | robots.txt: "Seuls les partenaires sont habilités à utiliser nos contenus pour un usage autre que strictement individuel" (same wording as Le Monde). | https://www.liberation.fr/robots.txt ("Seuls les partenaires sont habilités à utiliser nos contenus pour un usage autre que strictement individuel") |
| La Croix | tdm_all | n/a | CGU (PDF): "BAYARD SERVICE s'oppose à toutes opérations de moissonnage et de fouille de textes et de données". | https://img.aws.la-croix.com/2011/02/15/10639/CGU-LaCroix.pdf, linked from https://www.la-croix.com/ ("s'oppose à toutes opérations de moissonnage et de fouille de textes et de données") |
| 20 Minutes | tdm_all | n/a | CGU: "20 Minutes s'oppose à la fouille de textes et de données sur l'ensemble du Site", "quel que soit le but poursuivi". | https://www.20minutes.fr/cgu ("20 Minutes s'oppose à la fouille de textes et de données sur l'ensemble du Site") |
| La Dépêche du Midi | all_reuse | n/a | CGU: "Toute reproduction, représentation, modification, diffusion ou utilisation commerciale ou non commerciale ... sans l'autorisation écrite de l'EDITEUR est strictement interdite", and no access "par des moyens automatisés". | https://www.ladepeche.fr/page/conditions-generales-d-utilisation ("utilisation commerciale ou non commerciale ... est strictement interdite") |
| Le Télégramme | all_reuse | n/a | robots.txt: "Tout usage de nos contenus en dehors du cadre privé, requiert une licence ... Sont inclus notamment l'entraînement et l'ancrage des grands modèles de langage (LLM) ..., la veille web ou le media monitoring"; also `User-agent: *` `Disallow: /`. | https://www.letelegramme.fr/robots.txt ("Tout usage de nos contenus en dehors du cadre privé, requiert une licence d'utilisation") |
| Ouest-France | unknown | 581,505 | robots.txt (WebFetch): `User-agent: *` `Disallow: /`, so our crawler is blocked. The site returned 403 to curl. | https://www.ouest-france.fr/robots.txt (WebFetch); https://www.ouest-france.fr/ (403) |
| Le Parisien | unknown | 192,505 | Blocked: 403 to curl and WebFetch. robots.txt (curl) blocks GPTBot, CCBot, anthropic-ai and others. | https://www.leparisien.fr/ (403); https://www.leparisien.fr/robots.txt (curl; WebFetch refused) |
| Les Échos | unknown | n/a | Blocked: homepage 403. Terms not read. | https://www.lesechos.fr/ (403); https://www.lesechos.fr/robots.txt |
| La Voix du Nord | unknown | n/a | Blocked: 403 on homepage and robots.txt. | https://www.lavoixdunord.fr/ and /robots.txt (403) |
| Sud Ouest | unknown | n/a | Blocked: 302 redirect loop on homepage and robots.txt. | https://www.sudouest.fr/ and /robots.txt (302 loop) |

#### Magazines

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| The Conversation France | none | n/a | **Registry** `fr-conversation-france`. CC BY-ND; the French guidelines have no AI clause. Free, from 2015. | `evidence_urls` of registry entry `fr-conversation-france` |
| Slate.fr | copyright_boilerplate | n/a | **Registry** `fr-slate`. Personal-use and no-redistribution wording only; 2/2 pages free. | `evidence_urls` of registry entry `fr-slate` |
| Le Club de Mediapart | copyright_boilerplate | n/a | **Registry** `fr-mediapart-club`. Free reader blogs; Mediapart mentions légales (no TDM/AI clause). The Club charter is unread. | `evidence_urls` of registry entry `fr-mediapart-club` |
| Valeurs actuelles | unknown | n/a | **Registry** `fr-valeurs-actuelles`. No reuse clause found; partly free; sitemap from 2003. | `evidence_urls` of registry entry `fr-valeurs-actuelles` |
| Mediapart (journal) | copyright_boilerplate | n/a | Same mentions légales; the journal is subscriber-only. The free part is Le Club (above). | https://www.mediapart.fr/mentions-legales |
| Le Point | unknown | 268,788 | Blocked: 403 to curl (homepage, robots.txt), WebFetch refused. | https://www.lepoint.fr/ and https://www.lepoint.fr/robots.txt (403; WebFetch refused) |
| L'Express | all_reuse | 124,452 | CGU: "seule est permise l'utilisation pour un usage privé"; "toute autre utilisation est constitutive de contrefaçon ... sauf autorisation préalable". robots.txt has a "Blocages et autorisation Bots et LLM" section. | https://www.lexpress.fr/outils/conditions-generales-utilisation.html ("toute autre utilisation est constitutive de contrefaçon"); https://www.lexpress.fr/robots.txt |
| L'Obs | all_reuse | 166,054 | CGV: no crawling or mass collection "par quelque moyen et dans quelque but que ce soit", and "toute reproduction ... de quelque nature que ce soit ... est strictement interdite". | https://www.nouvelobs.com/cgv ("par quelque moyen et dans quelque but que ce soit") |
| Marianne | all_reuse | 106,990 | CGV (CMI France): "seule leur utilisation pour un usage privé est autorisée ... Toute autre utilisation est constitutive de contrefaçon". | https://www.marianne.net/cgu-cgv ("Toute autre utilisation est constitutive de contrefaçon"); https://www.marianne.net/robots.txt |
| Télérama | all_reuse | n/a | Mentions légales: "Tout autre usage est soumis à autorisation préalable et expresse". | https://www.telerama.fr/mentionslegales.php ("Tout autre usage est soumis à autorisation préalable et expresse") |
| Courrier international | all_reuse | 161,466 | CGVU: "toute reproduction, représentation, diffusion, traduction ou exploitation totale ou partielle, de quelque nature que ce soit et par quelque moyen que ce soit ... est strictement interdite". | https://www.courrierinternational.com/page/cgvu ("de quelque nature que ce soit et par quelque moyen que ce soit") |
| Le Monde diplomatique | all_reuse | n/a | CGVU: same template as L'Obs ("dans quelque but que ce soit"; "de quelque nature que ce soit"). | https://www.monde-diplomatique.fr/diplo/cgvu/ ("dans quelque but que ce soit") |
| Paris Match | all_reuse | n/a | CGU: no automatic or manual mass copying "pour quelque motif que ce soit et en particulier afin de développer ou d'entraîner tout programme logiciel (notamment les programmes basés sur l'intelligence artificielle)". | https://www.parismatch.com/cgu ("pour quelque motif que ce soit et en particulier afin de développer ou d'entraîner") |
| Elle | tdm_all | n/a | Mentions légales 10.3: bans "toute action ou processus de crawler, moissonnage et/ou fouille de textes et de données ... pour toute finalité". | https://www.elle.fr/pages/Mentions-Legales ("fouille de textes et de données ... pour toute finalité") |
| Femme Actuelle | tdm_all | 284,633 | Prisma Media: opposes "toute extraction (notamment moissonnage et/ou fouille de textes et de données)" without authorisation "et selon une grille tarifaire". | https://www.prismamedia.com/mentions-legales/, linked from the femmeactuelle.fr footer ("toute extraction (notamment moissonnage et/ou fouille de textes et de données)") |
| Télé-Loisirs | unknown | n/a | Its footer links a title-specific Prisma page that served only a script shell. The group-wide Prisma notice (`tdm_all`, see Femme Actuelle) probably applies, but programme-tv.net does not link to it, so the scope is unverified. Access was not sampled; not registered. | https://www.prismamedia.com/mentions-legales-tel/ (the footer link; served an empty script-rendered shell); the group-wide https://www.prismamedia.com/mentions-legales/ is not linked from programme-tv.net |
| Télé 7 Jours | copyright_boilerplate | n/a | programme-television.org (Bauer): content "exclusivement destinés à l'information et à l'usage personnel"; no TDM/AI clause found. The site is TV listings and soap recaps, and the sampled news page served ~70 words in paragraph tags. No free full text verified, so not registered. | https://www.programme-television.org/mentions-legales-et-conditions-generales-dutilisation; sample https://www.programme-television.org/news/series/series-quotidiennes/demain-nous-appartient-le-reve-de-jordan-vire-au-cauchemar-que-va-t-il-se-passer-dans-les-episodes-de-cette-semaine-sur-tf1-142941 |
| Notre Temps | tdm_all | 407,081 | Bayard CGU: "BAYARD s'oppose à toutes opérations de moissonnage et de fouille de textes et de données". | https://www.notretemps.com/conditions-generales-dutilisation ("BAYARD s'oppose à toutes opérations de moissonnage et de fouille de textes et de données") |
| Le Pèlerin | tdm_all | n/a | Same Bayard CGU. | https://www.lepelerin.com/cgu ("BAYARD s'oppose à toutes opérations de moissonnage et de fouille") |
| Psychologies | all_reuse | n/a | CGU: "L'Utilisateur n'est pas autorisé à copier, utiliser, reproduire, distribuer tout ou partie desdits Contenus sur un quelconque support, à titre onéreux ou gratuit, sans l'autorisation préalable écrite". | https://www.psychologies.com/Conditions-Generales-d-Utilisation ("pas autorisé à copier, utiliser, reproduire, distribuer") |
| Marie Claire | all_reuse | n/a | "Sauf autorisation, toute utilisation des œuvres autres que la reproduction et la consultation individuelles et privées sont interdites." | https://www.marieclaire.fr/,mentions-legales,20214,1711.asp ("toute utilisation des œuvres autres que la reproduction et la consultation individuelles et privées sont interdites") |
| VSD | copyright_boilerplate | n/a | CGU: "Vous ne devez pas copier, modifier, distribuer ... sans l'autorisation écrite préalable". Open, but two sampled pages served only ~130-150 words alongside "abonnés" markers. No free full text verified, so not registered. | https://vsd.fr/cgu/; samples https://vsd.fr/94610-lionel-jospin-est-mort/, https://vsd.fr/90285-exclu-vsd-tina-arena-50-ans-de-carriere-la-tele-ma-rendue-forte-mais-pas-toujours-heureuse/ |

#### Open titles shortlist (FR), ranked by fit

Newspapers:

1. `fr-humanite`: the only open national daily we found. It has debate pages and a
   sitemap from 1997, but it is partly paywalled and its terms are unread (read them in a
   browser first). Communist; one-sided.

Magazines:

1. `fr-mediapart-club`: free reader-written opinion blogs (an "ordinary people" fit
   similar to `fr-agoravox`). Left-leaning self-selected authors. Archive depth not
   verified.
2. `fr-valeurs-actuelles`: right-wing opinion weekly, partly free, from 2003. Terms
   unread. Pair it with the Club to balance the slant.
3. `fr-slate`: free commentary and features with boilerplate terms only. Archive depth not
   verified.
4. `fr-conversation-france`: CC BY-ND academic commentary from 2015; low "ordinary voice"
   fit.

No open popular magazine with free full text was found. Every major women's, family and
TV title we could read has an express TDM opt-out or an any-use clause. VSD and Télé 7
Jours are open but thin online. Télé-Loisirs is `unknown` (terms page unreadable) and its
access was not sampled. French popular-magazine coverage therefore needs a licence, e.g.
Prisma's "grille tarifaire" or Bayard's "accord spécifique".

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
  (Task 5e: nieuwsblad.be's robots.txt is now readable and carries the Mediahuis Art. 4
  reservation, so `tdm_all`; the DPG titles still return 403. See Wider sweep.)
- **Belgian web archive** (KBR PROMISE/BelgicaWeb): IIPC lists "Access methods:
  currently in development" (https://netpreserve.org/about-us/members/kbr/). No entry.
- **RTBF / VRT NWS**: public broadcasters, reachable but mostly straight news. (Task 5e
  surveyed both: RTBF is registered as `be-rtbf-info`; VRT's terms reserve TDM, so
  `tdm_all`. See Wider sweep.)

### Wider sweep (Task 5e)

**Title list.** Newspapers come from Wikipedia's
[List of newspapers in Belgium](https://en.wikipedia.org/wiki/List_of_newspapers_in_Belgium),
whose daily-newspaper table names every daily below with its average distribution in 2011
(CIM). Circulation below is that 2011 figure; the page gives none for the Brussels Times
(NA) or the broadcasters (n/a). Public-broadcaster and other news sites (VRT NWS, RTBF, RTL
info, 7sur7, BRUZZ) were added from the owner's brief. Magazines come from the owner's lists,
cross-checked against Wikipedia's
[List of magazines in Belgium](https://en.wikipedia.org/wiki/List_of_magazines_in_Belgium),
which names Knack, Le Vif/L'Express, HUMO, Dag Allemaal, Story, Libelle, Flair, Femmes
d'Aujourd'hui, Moustique, Ciné-Télé-Revue, Paris Match Belgique, Plus Magazine, Joepie,
Mondiaal Nieuws (MO*), Médor and Kerk en Leven. Apache, DeWereldMorgen, Doorbraak and
Télépro are not on that page; they were added as Belgian opinion and TV-guide titles. We
found no cited magazine circulation figures (n/a). De Standaard, La Libre, Le Soir,
BelgicaPress and forum.politics.be are covered above. We checked 38 titles, all listed in
the two tables below: 18 newspapers and 20 magazines. 5 are registered (rows marked
**Registry**) and 33 are not. For each we read robots.txt, the terms page, and one to
three sample pages (paywall flag and whether the body is in the HTML).

Belgium splits into three groups. (1) Blocked: DPG Media (HLN, De Morgen, 7sur7, Humo, Dag
Allemaal, Story, Joepie) returned its "Web Application Firewall" 403 to every request;
Rossel (Sudinfo, Grenz-Echo, Metro, Ciné-Télé-Revue) returned an Akamai 403; Mediafin (De
Tijd, L'Echo) served the homepage but returned a "Bot detection" 403 for robots.txt and the
terms; Roularta (Knack, Le Vif, Libelle, Flair, Femmes d'Aujourd'hui, Télépro) and Plus
Magazine served an AWS "Human Verification" page (HTTP 405). We did not try to get past any of these, so
their scope is `unknown`. Such titles are open under the rule but unusable until the terms
and access are checked in a browser. (2) Closed: Mediahuis (Het Nieuwsblad, GVA, HBVL) and
VRT reserve TDM (`tdm_all`); IPM (DH, Paris Match Belgique) uses the La Libre "sous toute
forme" clause, and Moustique, BRUZZ, Apache and Kerknet restrict use (`all_reuse`). (3)
Open and usable: RTBF, L'Avenir, RTL info, MO* and DeWereldMorgen.

#### Newspapers

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| RTBF (Actus, Opinions / Carte blanche) | copyright_boilerplate | n/a | **Registry** `be-rtbf-info`. Public broadcaster. The CGU ban copying except "utilisation à des fins strictement privées", with no AI clause. 2/2 opinion pages free. | `evidence_urls` of registry entry `be-rtbf-info` |
| L'Avenir | copyright_boilerplate | 94,118 | **Registry** `be-lavenir-website`. EDA Presse terms grant rights "à titre personnel", with no use ban and no AI clause. 1 of 3 opinion pieces free. | `evidence_urls` of registry entry `be-lavenir-website` |
| RTL info | unknown | n/a | **Registry** `be-rtl-info`. Terms page is a script shell; robots.txt blocks AI bots. 2/2 news pages free; no opinion section. | `evidence_urls` of registry entry `be-rtl-info` |
| Het Laatste Nieuws | unknown | 288,898 | Blocked: DPG WAF 403 on homepage and robots.txt; WebFetch could not fetch robots.txt. | https://www.hln.be/ and https://www.hln.be/robots.txt (403, "blocked by DPG Media's Web Application Firewall") |
| Het Nieuwsblad | tdm_all | 264,961 (incl. De Gentenaar) | robots.txt: "In accordance with Article 4 of the Directive on Copyright in the Digital Single Market (CDSM) ... all content of this website ... is not to be used for the purposes of text and data mining, extraction, scraping ... whether for machine learning or artificial intelligence purposes or otherwise". Homepage 403. | https://www.nieuwsblad.be/robots.txt ("is not to be used for the purposes of text and data mining"); https://www.nieuwsblad.be/ (403) |
| Gazet van Antwerpen | tdm_all | 101,559 | Same Mediahuis Art. 4 reservation in robots.txt. Homepage 403. | https://www.gva.be/robots.txt ("is not to be used for the purposes of text and data mining") |
| Het Belang van Limburg | tdm_all | 100,113 | Same Mediahuis Art. 4 reservation in robots.txt. Homepage 403. | https://www.hbvl.be/robots.txt ("is not to be used for the purposes of text and data mining") |
| De Morgen | unknown | 55,870 | Blocked: DPG WAF 403 on homepage and robots.txt. | https://www.demorgen.be/ and /robots.txt (403) |
| De Tijd | unknown | 37,720 | Homepage served (200), but robots.txt and the terms page returned 403 "Bot detection"; WebFetch could not fetch the terms. | https://www.tijd.be/robots.txt and https://www.tijd.be/service/algemene-voorwaarden.html (403) |
| L'Echo | unknown | 17,170 | Same Mediafin bot detection: 403 on robots.txt and the terms page. | https://www.lecho.be/robots.txt and https://www.lecho.be/service/conditions-generales.html (403) |
| La Dernière Heure / Les Sports+ | all_reuse | 62,427 | IPM conditions générales (same as La Libre): "Toute reproduction totale ou partielle et sous toute forme des contenus ... est strictement interdite". The sampled editorial had `isAccessibleForFree` false. | https://www.dhnet.be/page/conditions-generales/ ("Toute reproduction totale ou partielle et sous toute forme"); https://www.dhnet.be/robots.txt; sample https://www.dhnet.be/actu/edito/2026/11/18/appel-au-boycott-du-nouveau-james-bond-ou-quand-le-cinema-se-footballise-5KLUYFUMJ5CERADQPOPASDSNQI/ |
| Sudinfo (SudPresse: La Meuse, La Capitale, La Nouvelle Gazette, La Province, Nord Éclair) | unknown | 115,853 | Blocked: Akamai 403 on homepage and robots.txt. | https://www.sudinfo.be/ and /robots.txt (403) |
| Grenz-Echo | unknown | 12,079 | Blocked: Akamai 403 on homepage and robots.txt. | https://www.grenzecho.net/ and /robots.txt (403) |
| Metro (BE) | unknown | 130,968 (nl) / 116,022 (fr) | metrotime.be redirects to lesoir.be, which returned 403. | https://www.metrotime.be/ (redirect to https://www.lesoir.be/, 403) |
| The Brussels Times | unknown | NA | The site is a script-rendered app: the homepage and /terms-and-conditions served the same shell with no terms text. robots.txt has no AI block. English-language and expat-oriented; access not verified, so not registered. | https://www.brusselstimes.com/terms-and-conditions (script shell); https://www.brusselstimes.com/robots.txt |
| VRT NWS | tdm_all | n/a | VRT terms: "VRT maakt een uitdrukkelijk voorbehoud dat de reproductie, opvraging en elk ander gebruik van rechtmatig toegankelijke VRT-content met het oog op tekst- en datamining enkel kan met de voorafgaande, specifieke schriftelijke toestemming van VRT"; automated use "(vb. voor het trainen van artificiële intelligentie (AI))" is also banned. | https://www.vrt.be/nl/info/gebruiksvoorwaarden ("uitdrukkelijk voorbehoud ... met het oog op tekst- en datamining"); https://www.vrt.be/robots.txt |
| 7sur7 | unknown | n/a | Blocked: DPG WAF 403 on homepage and robots.txt. | https://www.7sur7.be/ and /robots.txt (403) |
| BRUZZ | all_reuse | n/a | Disclaimer: articles "mogen op geen enkele wijze worden verspreid, gebruikt of overgenomen". | https://www.bruzz.be/disclaimer-copyright-op-bruzzbe ("op geen enkele wijze worden verspreid, gebruikt of overgenomen") |

#### Magazines

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| MO* (Mondiaal Nieuws) | copyright_boilerplate | n/a | **Registry** `be-mo-magazine`. Personal download and copying allowed, reproduction needs permission; no AI clause. 3/3 column/opinion pages free. | `evidence_urls` of registry entry `be-mo-magazine` |
| DeWereldMorgen | unknown | n/a | **Registry** `be-dewereldmorgen`. No terms found. 2/2 opinion pages free; sitemap from 2008; has reader "Community" posts. | `evidence_urls` of registry entry `be-dewereldmorgen` |
| Knack | unknown | n/a | Blocked: AWS "Human Verification" page (HTTP 405) on homepage and /algemene-voorwaarden/; WebFetch got 403. robots.txt (readable) has no AI block. roularta.com's own disclaimer covers only the corporate site. | https://www.knack.be/ and https://www.knack.be/algemene-voorwaarden/ (405 challenge); https://www.knack.be/robots.txt |
| Le Vif | unknown | n/a | Same Roularta AWS challenge (405). robots.txt has no AI block. | https://www.levif.be/ (405); https://www.levif.be/robots.txt |
| Libelle (BE) | unknown | n/a | Same Roularta AWS challenge (405); robots.txt is the same Roularta template (`rmg_dologin`). | https://www.libelle.be/ (405); https://www.libelle.be/robots.txt |
| Flair | unknown | n/a | Same Roularta AWS challenge (405). | https://www.flair.be/ (405); https://www.flair.be/robots.txt |
| Femmes d'Aujourd'hui | unknown | n/a | Same Roularta AWS challenge (405). | https://www.femmesdaujourdhui.be/ (405); https://www.femmesdaujourdhui.be/robots.txt |
| Plus Magazine | unknown | n/a | Same AWS challenge (405). | https://www.plusmagazine.be/ (405); https://www.plusmagazine.be/robots.txt |
| Télépro | unknown | n/a | Same Roularta AWS challenge (405). | https://www.telepro.be/ (405); https://www.telepro.be/robots.txt |
| HUMO | unknown | n/a | Blocked: DPG WAF 403 on homepage and robots.txt. | https://www.humo.be/ and /robots.txt (403) |
| Dag Allemaal | unknown | n/a | Blocked: DPG WAF 403. | https://www.dagallemaal.be/ and /robots.txt (403) |
| Story (BE) | unknown | n/a | Blocked: DPG WAF 403. | https://www.story.be/ and /robots.txt (403) |
| Joepie | unknown | n/a | joepie.be redirects to hln.be/joepie (DPG WAF 403). | https://www.joepie.be/ (redirect to https://www.hln.be/joepie, 403) |
| Moustique | all_reuse | n/a | L'Avenir Hebdo CGUV: the user agrees to "n'utiliser ces pages que pour ses besoins strictement personnels" and to download only "pour un usage personnel et limité dans le temps". robots.txt blocks CCBot, GPTBot and others. | https://www.moustique.be/page/conditions-generales/ ("n'utiliser ces pages que pour ses besoins strictement personnels"); https://www.moustique.be/robots.txt |
| Paris Match Belgique | all_reuse | n/a | IPM conditions générales: "Toute reproduction totale ou partielle et sous toute forme ... est strictement interdite". | https://www.parismatch.be/page/conditions-generales/ ("sous toute forme"); https://www.parismatch.be/robots.txt |
| Ciné-Télé-Revue | unknown | n/a | cinetelerevue.be redirects to sudinfo.be/cine-tele-revue (Akamai 403). | https://www.cinetelerevue.be/ (redirect, 403) |
| Apache | all_reuse | n/a | Terms: "Je mag de inhoud van Apache ook niet automatisch opnemen in een database". robots.txt blocks GPTBot, CCBot, anthropic-ai and Claude-Web. | https://apache.be/algemene-voorwaarden ("niet automatisch opnemen in een database"); https://apache.be/robots.txt |
| Doorbraak | copyright_boilerplate | n/a | Terms: "Het verder verspreiden van deze inhoud ... zonder de uitdrukkelijke schriftelijke toestemming van Perruptio BV, is verboden". Open, but all four sampled pieces (one interview, one column, two Forum pieces) carried the "Plus" paywall block ("Dit artikel is er eentje voor onze abo[nnees]"), and three served only ~3,000 characters of page text. No free full text verified, so not registered. Flemish-nationalist opinion. | https://doorbraak.be/algemene-voorwaarden ("Het verder verspreiden van deze inhoud ... is verboden"); samples https://doorbraak.be/barbara-pas-vlaams-belang-wat-de-nva-doet-is-niet-compromissen-maken-maar-kruipen, https://doorbraak.be/de-discriminatiemythe-ontkracht, https://doorbraak.be/de-vragen-die-kasparov-niet-kreeg, https://doorbraak.be/een-parlementaire-gebedslunch-is-de-scheiding-van-kerk-en-staat-nu-bedreigd |
| Médor | none | n/a | Conditions générales: Médor encourages authors to publish "sous des licences Creative Commons, qui sont renseignées dans les articles"; sampled pieces are "Texte (CC BY-NC-ND)". Quarterly, mostly for subscribers. Two "libre accès" pieces served ~400 words with a trial overlay ("Je lis d'abord la suite"), so we could not verify full free text. Not registered. | https://medor.coop/medor-cest-quoi-cest-qui/conditions-generales/ ("sous des licences Creative Commons"); samples https://medor.coop/magazines/medor-n44-automne-2026/edito-a-quoi-bon-impact-journalisme-changement-democratie-environnement-sante-social/, https://medor.coop/magazines/medor-n44-automne-2026/chomage-le-debut-de-la-fin-reforme-aide-sociale-allocations-politique-mobilisation-archive-photo-guyaux-histoire-onem-cpas/ |
| Kerknet (Kerk & Leven) | all_reuse | n/a | Terms: "Zonder toestemming mag je informatie op deze website op geen enkele manier gebruiken, kopiëren, opslaan, publiceren ...". | https://www.kerknet.be/gebruiksvoorwaarden ("op geen enkele manier gebruiken, kopiëren, opslaan") |

#### Open titles shortlist (BE), ranked by fit

Newspapers:

1. `be-rtbf-info`: free francophone public broadcaster with an Opinions / Carte blanche
   section (outside op-eds by associations and citizens). Boilerplate terms only. Archive
   depth of opinions not verified.
2. `be-lavenir-website`: regional francophone daily with Opinions and Espace débat; partly
   free, boilerplate terms. Pair with `be-rtbf-info`.
3. `be-rtl-info`: free commercial TV news; terms unread and no opinion section, so low
   fit.

No usable Flemish daily was found. Mediahuis and VRT reserve TDM; DPG and Mediafin block
our client.

Magazines:

1. `be-dewereldmorgen`: free Flemish opinion and reader "Community" posts, with sitemap
   URLs from 2008. Left-leaning; terms unknown, so ask the publisher.
2. `be-mo-magazine`: free Flemish columns and opinion on global affairs; boilerplate
   terms. NGO slant.

No open popular magazine with free text was reachable. Roularta's (Knack, Le Vif,
Libelle, Flair, Femmes d'Aujourd'hui, Télépro), Plus Magazine and DPG's (HUMO, Dag Allemaal,
Story) are all behind bot walls, so a browser check of the Roularta terms is the next
step. Knack and Le Vif would be the best-fit opinion weeklies if their terms are open.

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
- **NOS**: public broadcaster, reachable, but straight news. (Task 5e: NOS terms ban
  "Bots of AI-systemen gebruiken om automatisch data te verzamelen", so `all_reuse`. De
  Telegraaf's robots.txt is now readable and carries the Mediahuis Art. 4 reservation.
  See Wider sweep.)
- **r/Netherlands**: English and expat-heavy. Recorded in the notes of
  `nl-reddit-thenetherlands`.

### Wider sweep (Task 5e)

**Title list.** Newspapers come from Wikipedia's
[List of newspapers in the Netherlands](https://en.wikipedia.org/wiki/List_of_newspapers_in_the_Netherlands),
which lists the national and regional dailies with 2017 circulation (Mediamonitor, "the
last year precise numbers were published"). Circulation below is that 2017 figure.
Broadcaster news sites (NOS, RTL Nieuws, NH Nieuws, Omroep Brabant) and Metro were added
from the owner's brief. Magazines come from the owner's lists, cross-checked against
Wikipedia's [List of magazines in the Netherlands](https://en.wikipedia.org/wiki/List_of_magazines_in_the_Netherlands),
which names Elsevier, De Groene Amsterdammer, HP/De Tijd, Vrij Nederland, Nieuwe Revu,
Panorama, Libelle, Margriet, Opzij, Privé, Story, Viva and Televizier. De Correspondent,
Follow the Money, LINDA., TPO, Wynia's Week, De Dagelijkse Standaard and Joop are not on
that page; they were added as major online opinion or popular titles. We found no cited
magazine circulation figures (n/a). NRC, Delpher, the KB, GeenStijl, FOK! and Reddit are
covered above. De Telegraaf, de Volkskrant, Trouw and NU.nl were dead ends in the first
survey; the first three are re-checked below, and NU.nl still returned 403. We checked 48
titles in 40 table rows: 20 newspaper rows (two of them group seven DPG and three
Mediahuis regionals, so 28 newspapers) and 20 magazines. 9 are
registered (rows marked **Registry**) and 39 are not. For each we read robots.txt, the
terms page, and one to three sample pages.

The Dutch national and regional press is closed or blocked. Every Mediahuis NL daily we
could read (De Telegraaf and eight regionals) carries the Art. 4 CDSM reservation in
robots.txt. FD and RD print their own TDM/AI ban in robots.txt, and ND reserves TDM in its
terms (`tdm_all`). All DPG Media titles (AD, de Volkskrant, Trouw, Het Parool, the DPG
regionals, Libelle, Margriet, LINDA., Story) returned DPG's "Web Application Firewall" 403,
so they are `unknown` and unusable for now. NOS bans bots and AI collection
(`all_reuse`). The open, usable titles are regional public broadcasters (NH Nieuws, Omroep
Brabant), Metro, and a set of online opinion and popular magazines.

#### Newspapers

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| NH Nieuws | ai_training_only | n/a | **Registry** `nl-nh-nieuws`. robots.txt content signals: `ai-train=no, search=yes, ai-input=yes`. Free regional public broadcaster. | `evidence_urls` of registry entry `nl-nh-nieuws` |
| Omroep Brabant | unknown | n/a | **Registry** `nl-omroep-brabant`. No terms page found; llms.txt invites AI use. Free. | `evidence_urls` of registry entry `nl-omroep-brabant` |
| Metro | unknown | n/a | **Registry** `nl-metro`. The linked Mediahuis NL terms returned 403; robots.txt has no reservation or AI block. Free; sitemaps from 2020. | `evidence_urls` of registry entry `nl-metro` |
| De Telegraaf | tdm_all | 385,501 | robots.txt (now readable): "In accordance with Article 4 of the Directive on Copyright in the Digital Single Market (CDSM) ... all content of this website ... is not to be used for the purposes of text and data mining ...". Homepage 403. | https://www.telegraaf.nl/robots.txt ("is not to be used for the purposes of text and data mining"); https://www.telegraaf.nl/ (403) |
| Algemeen Dagblad | unknown | 340,758 | Blocked: DPG WAF 403 on homepage and robots.txt. | https://www.ad.nl/ and /robots.txt (403, "blocked by DPG Media's Web Application Firewall") |
| de Volkskrant | unknown | 239,219 | Re-check: still DPG WAF 403 on homepage and robots.txt. | https://www.volkskrant.nl/ and /robots.txt (403) |
| Trouw | unknown | 98,882 | Re-check: still DPG WAF 403. | https://www.trouw.nl/ and /robots.txt (403) |
| Het Financieele Dagblad | tdm_all | 47,363 | robots.txt "AI & TDM OPT-OUT": "Scraping, harvesting, or any other form of data or text mining, machine learning, or artificial intelligence purposes ... using FD content — is expressly prohibited." | https://fd.nl/robots.txt ("any other form of data or text mining ... is expressly prohibited") |
| Reformatorisch Dagblad | tdm_all | 42,967 | robots.txt: the same wording ("... using RD content — is expressly prohibited"), plus `User-agent: *` `Disallow: /`. | https://www.rd.nl/robots.txt ("any other form of data or text mining ... is expressly prohibited") |
| Nederlands Dagblad | tdm_all | 19,593 | Terms 7.3, an express Art. 15o reservation: "ND behoudt zich met betrekking tot ... tekst- en datamining van content van ND, als bedoeld in artikel 15 c.q. 15o van de Auteurswet, daaronder begrepen, maar niet uitsluitend het gebruik van content van ND voor het trainen van generatieve ...". robots.txt: "Nederlands Dagblad allows search indexing, but no real-time retrieval, no AI training." | https://www.nd.nl/service/algemene-voorwaarden ("met betrekking tot tekst- en datamining van content van ND, als bedoeld in artikel 15 c.q. 15o van de Auteurswet"); https://www.nd.nl/robots.txt |
| Het Parool | unknown | 49,483 | Blocked: DPG WAF 403. | https://www.parool.nl/ and /robots.txt (403) |
| De Gelderlander and the other DPG regionals (Brabants Dagblad, De Stentor, Tubantia, Eindhovens Dagblad, BN DeStem, PZC) | unknown | 111,311 (Gelderlander); 41,111-96,008 (others) | Blocked: all seven returned DPG WAF 403 on homepage and robots.txt. | https://www.gelderlander.nl/, https://www.bd.nl/, https://www.destentor.nl/, https://www.tubantia.nl/, https://www.ed.nl/, https://www.bndestem.nl/, https://www.pzc.nl/ (each plus /robots.txt, 403) |
| Dagblad van het Noorden | tdm_all | 95,202 | Mediahuis Art. 4 reservation in robots.txt. Homepage 403. | https://www.dvhn.nl/robots.txt ("is not to be used for the purposes of text and data mining") |
| Leeuwarder Courant | tdm_all | 64,639 | Same Mediahuis reservation. Homepage 403. | https://www.lc.nl/robots.txt ("is not to be used for the purposes of text and data mining") |
| De Limburger | tdm_all | 122,269 | Same Mediahuis reservation; the homepage redirected to a Mediahuis login. | https://www.limburger.nl/robots.txt ("is not to be used for the purposes of text and data mining") |
| Noordhollands Dagblad | tdm_all | 95,767 | Same Mediahuis reservation. Homepage 403. | https://www.noordhollandsdagblad.nl/robots.txt ("is not to be used for the purposes of text and data mining") |
| Friesch Dagblad | tdm_all | 12,112 | Same Mediahuis reservation. Homepage 403. | https://www.frieschdagblad.nl/robots.txt ("is not to be used for the purposes of text and data mining") |
| Haarlems Dagblad, Leidsch Dagblad, De Gooi- en Eemlander | tdm_all | 25,464 / 21,318 / 17,020 | Same Mediahuis reservation in all three robots.txt files. Homepages 403. | https://www.haarlemsdagblad.nl/robots.txt, https://www.leidschdagblad.nl/robots.txt, https://www.gooieneemlander.nl/robots.txt ("is not to be used for the purposes of text and data mining") |
| NOS | all_reuse | n/a | Terms: you may not "Bots of AI-systemen gebruiken om automatisch data te verzamelen, tenzij NOS dit expliciet toestaat"; content may be viewed and shared "voor persoonlijk en niet-commercieel gebruik". robots.txt blocks CCBot, GPTBot and others. | https://over.nos.nl/organisatie/algemene-voorwaarden-nos/ ("Bots of AI-systemen gebruiken om automatisch data te verzamelen"); https://nos.nl/robots.txt |
| RTL Nieuws | unknown | n/a | rtl.nl redirected to the DPG privacy gate (403); terms not read. robots.txt: "Blocked are AI training, AI search and AI agents, SEO scrapers, archives". | https://www.rtl.nl/ (redirect to myprivacy.dpgmedia.nl, 403); https://www.rtl.nl/robots.txt |

#### Magazines

| Title | Scope | Circ. | Reason | Evidence |
|---|---|---|---|---|
| De Correspondent | copyright_boilerplate | n/a | **Registry** `nl-de-correspondent`. No publishing, copying, scanning "of anderszins te exploiteren" without permission; no AI clause. 2/2 pages free. | `evidence_urls` of registry entry `nl-de-correspondent` |
| Wynia's Week | unknown | n/a | **Registry** `nl-wynias-week`. Only shop terms found. Free opinion columns; sitemaps from 2019. | `evidence_urls` of registry entry `nl-wynias-week` |
| TPO (ThePostOnline) | copyright_boilerplate | n/a | **Registry** `nl-tpo`. Same terms template as De Correspondent. Has a Premium tier; 3 sampled pages served their body. | `evidence_urls` of registry entry `nl-tpo` |
| De Dagelijkse Standaard | crawler_block_only | n/a | **Registry** `nl-dagelijkse-standaard`. No terms found; robots.txt blocks AI bots on /nieuws/ only. 2/2 Opinie pages free. | `evidence_urls` of registry entry `nl-dagelijkse-standaard` |
| VIVA | unknown | n/a | **Registry** `nl-viva`. Terms put no reuse restriction on visitors. 2/2 pages free. | `evidence_urls` of registry entry `nl-viva` |
| Opzij | unknown | n/a | **Registry** `nl-opzij`. No terms found. 2/2 pages free; sitemaps from 2017. | `evidence_urls` of registry entry `nl-opzij` |
| EW (Elsevier Weekblad) | unknown | n/a | Blocked: AWS "Human Verification" page (HTTP 405), as on the Roularta BE sites; robots.txt uses the Roularta template (`rmg_dologin`). Terms unread. | https://www.ewmagazine.nl/ (405 challenge); https://www.ewmagazine.nl/robots.txt |
| De Groene Amsterdammer | all_reuse | n/a | Terms: "Voor het overnemen, opslaan en verspreiden van (delen van) de inhoud en gebruik van de vormgeving, op welke wijze dan ook, dient u vooraf schriftelijke toestemming te hebben verkregen". robots.txt blocks AI training, search and RAG agents. | https://www.groene.nl/over/pagina/gebruiksvoorwaarden ("overnemen, opslaan en verspreiden ... op welke wijze dan ook"); https://www.groene.nl/robots.txt |
| Vrij Nederland | unknown | n/a | The disclaimer has no reuse clause; the algemene voorwaarden PDF was not read. Two sampled articles served only ~110-120 words (paywalled), so no free part was found. Not registered. | https://www.vn.nl/service/disclaimer/; samples https://www.vn.nl/dag-verzorgingsstaat-hallo-vermogensstaat/, https://www.vn.nl/econoom-eelco-heinen-moet-op-bijles/ |
| HP/De Tijd | all_reuse | n/a | Terms: "Gebruik van (de aangeboden informatie op) de Website is alleen toegestaan voor persoonlijke, niet commerciële doeleinden", and copying by any means "(bijv. geautomatiseerde software)" is banned. The sampled page had `isAccessibleForFree` False. | https://www.hpdetijd.nl/gebruikersvoorwaarden ("alleen toegestaan voor persoonlijke, niet commerciële doeleinden"); sample https://www.hpdetijd.nl/boezemvrienden/boezemvrienden/48508/rinus-gerritsen-en-nico-dijkshoorn-in-het-begin-was-ik-starstruck |
| Follow the Money | copyright_boilerplate | n/a | Same terms template as De Correspondent ("openbaar te maken, te verveelvoudigen, scannen of anderszins te exploiteren"). robots.txt: "Training en dataverzameling: geblokkeerd". Member-funded; the sampled articles served ~500 and ~1,400 words with no free flag, so the free share is not established. Investigative, low opinion fit. Not registered. | https://www.ftm.nl/over-ftm/voorwaarden; https://www.ftm.nl/robots.txt; samples https://www.ftm.nl/artikelen/ai-bedrijf-wil-geld-verdienen-met-dubieuze-duurzaamheids-claim, https://www.ftm.nl/artikelen/gevangen-in-de-franse-morvan-1-weggestopt-en-uitgebuit |
| Joop (BNNVARA) | all_reuse | n/a | BNNVARA terms: "Het is niet toegestaan de Diensten op geautomatiseerde wijze te (laten) raadplegen en/of te analyseren, zoals onder meer via scripts, spiders en of bots." joop.nl redirects to bnnvara.nl/joop. | https://www.bnnvara.nl/algemene-voorwaarden ("op geautomatiseerde wijze te (laten) raadplegen en/of te analyseren") |
| Panorama | all_reuse | n/a | Pijper Media robots.txt: the content is "uitsluitend voor persoonlijk, niet-commercieel gebruik en het is niet toegestaan om gegevens ... door middel van screen scraping (of een andere geautomatiseerde werkwijze) te vergaren". | https://panorama.nl/robots.txt ("uitsluitend voor persoonlijk, niet-commercieel gebruik") |
| Nieuwe Revu | all_reuse | n/a | Same Pijper Media robots.txt clause. | https://revu.nl/robots.txt ("uitsluitend voor persoonlijk, niet-commercieel gebruik") |
| Privé | tdm_all | n/a | prive.nl redirects to telegraaf.nl/entertainment, so it falls under De Telegraaf's Art. 4 reservation (prive.nl/robots.txt served a Cloudflare challenge). | https://www.prive.nl/ (redirect to https://www.telegraaf.nl/entertainment, 403); https://www.telegraaf.nl/robots.txt ("is not to be used for the purposes of text and data mining") |
| Libelle (NL) | unknown | n/a | Blocked: DPG WAF 403 on homepage and robots.txt. | https://www.libelle.nl/ and /robots.txt (403) |
| Margriet | unknown | n/a | Blocked: DPG WAF 403. | https://www.margriet.nl/ and /robots.txt (403) |
| LINDA. | unknown | n/a | Blocked: DPG WAF 403. | https://www.linda.nl/ and /robots.txt (403) |
| Story (NL) | unknown | n/a | Blocked: DPG WAF 403. | https://www.story.nl/ and /robots.txt (403) |
| Televizier | all_reuse | n/a | Terms: the services "zijn alleen bedoeld voor eigen persoonlijke raadpleging en/of via normaal browserbezoek". | https://www.televizier.nl/algemene-voorwaarden/ ("alleen bedoeld voor eigen persoonlijke raadpleging en/of via normaal browserbezoek") |

#### Open titles shortlist (NL), ranked by fit

Newspapers:

1. `nl-nh-nieuws`: free regional public broadcaster that explicitly allows `ai-input`
   (only AI training is refused). The clearest terms in this batch, but mostly news.
2. `nl-omroep-brabant`: free regional public broadcaster with no terms found and an
   AI-friendly llms.txt. News only.
3. `nl-metro`: free daily with a daily reader poll ("Stelling van de dag"). Its Mediahuis
   terms are unread, so check them before use.

No national daily is usable: Mediahuis, FD, RD and ND reserve TDM, and DPG blocks our
client.

Magazines:

1. `nl-de-correspondent`: free long-form opinion and explanatory pieces, with boilerplate
   terms (our reading of "anderszins te exploiteren"). Progressive.
2. `nl-wynias-week`: free right-of-centre opinion columns from 2019; terms unknown. Pairs
   with De Correspondent for balance.
3. `nl-tpo`: right-leaning opinion and news, partly Premium; boilerplate terms.
4. `nl-dagelijkse-standaard`: right-wing opinion blog with comments; one-sided.
5. Popular-magazine stream: `nl-viva` (women's, free, terms silent on reuse) and
   `nl-opzij` (feminist monthly, free, from 2017).

The big popular titles (Libelle, Margriet, LINDA., Story) are DPG and blocked; Privé is
under the Telegraaf reservation; Panorama, Nieuwe Revu and Televizier restrict use.
Letters pages were not checked title by title.

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

## IT

Scope note for IT, ES and PT: as for DE/AT/CH, newspapers are the core v0 source and
forums/comments were not surveyed. The type of restriction is marked (a) bans any
TDM/automated analysis, (b) bans any reuse without licence, (c) bans only AI training,
(d) only blocks AI crawlers in robots.txt.

**2005–now.** *What exists:* Corriere della Sera, la Repubblica and La Stampa, each with
opinion and letters sections ("Lettere al direttore", "Lo dico al Corriere", Repubblica
"lettere" and "Commenti"). *What is free:* little that we could confirm. **Corriere**
(`it-corriere-archive`) opinion was 5/5 paywalled, and its archive is account-based.
**la Repubblica** (`it-repubblica-archive`) is the interesting case. Its 1984–now archive
pages on ricerca.repubblica.it served text without login for 1995 and 2005 samples, and a
2016 page also loaded without login. But the search results for 2005–2021 point to the paid
"edicola", so the free cut-off is unknown. All three GEDI/RCS sites block AI crawlers in
robots.txt (type d: GPTBot, CCBot, anthropic-ai, Google-Extended; Corriere adds
"__usage_ai-training"). We did not find GEDI's or RCS's written terms, so we do not know
whether they also have type (a) or (b) clauses. **CC-NEWS** (`it-common-crawl-news`)
is thin for Italy because all three big dailies disallow CCBot.

**1940–2005.** **Archivio storico La Stampa** (`it-archivio-lastampa`) is the standout. It
is free, with no login, and holds the full run 1867–2005 plus Stampa Sera 1931–1992 (1.76M
pages). Articles are segmented from 1910, and article text files are downloadable from 1910
on. The site posts no reuse, TDM or AI terms at all; OCR is admittedly uneven. **l'Unità
1946–2014** (`it-unita-archive`) is free online with full-text search. It is the PCI/PDS
party paper, the site looks like a volunteer mirror, and its rights status is unclear.
**Internet Culturale** (`it-internet-culturale-emeroteca`) is CC BY-NC-SA, but it has
almost nothing after 1945 (a handful of Liberation-era titles to 1951).

**Biggest gap:** a licensable 2005–now source. La Stampa's free archive stops in 2005, and
the free share of Repubblica after 2005 is unknown. There is also no free centre or right
counterweight to l'Unità for 1946–1990 apart from La Stampa.

**Best for opinion / letters genres:** 2005–now: Repubblica archive pages (free share
unknown; type d block); historical: La Stampa 1945–2005 (free, terms silent), l'Unità
1946–2014 (party paper).

### Recommended sources (IT)

1. `it-archivio-lastampa`: 1945–2005, free, no stated terms. Ask the archive (Contatti
   page) and La Stampa/GEDI about research tagging and per-text URLs.
2. `it-repubblica-archive`: measure the free cut-off in a browser, then ask GEDI for a
   research licence covering 1984–now (letters and Commenti).
3. `it-unita-archive`: 1946–2014 left voice, only after the rights holder is identified.
4. `it-corriere-archive`: paywalled. Ask RCS only if 1 and 2 fail.

### Dead ends and leads (IT)

- **GEDI / RCS terms pages**: three GEDI URL guesses returned 404. archivio.corriere.it
  is refused by WebFetch, and its pricing and FAQ were not reached.
- **Corpus la Repubblica** (SSLMIT/dipintra, 1985–2000 research corpus): the query
  interface returned 401 (login), and the info page did not resolve. A lead for KWIC-style
  research access, like DWDS.
- **Italian national web archive**: no public archive found. Search results mention a
  single BNCF harvest of .it in 2006 and an Archive-It collection, but we could not
  verify either. No entry.
- **il manifesto** (ilmanifesto.it): publishes a TDMRep `tdm-reservation: 1` file pointing
  to a "tdm-disclaimer" page. Not surveyed further.
- **Avvenire, Il Fatto Quotidiano, Il Post**: not surveyed. ilpost.it returned 403.
- **Forums / comments** (out of v0 scope): not surveyed.

## ES

**2005–now.** *What exists:* El País, ABC, La Vanguardia, El Mundo and elDiario.es, all
with opinion and letters ("Cartas al director") sections. *What is free:* almost nothing
that we can use. The legacy dailies state explicit art. 67.3 RDL 24/2021 / Art. 4(3) DSM
reservations of type (a)+(b). **El País** (`es-elpais-website`): 4/4 sampled archive and
opinion pages were not free. Its terms reserve TDM "así como frente a cualquier
utilización de sus contenidos por tecnologías de inteligencia artificial, sea cual sea su
naturaleza y finalidad". **ABC** (`es-abc-hemeroteca`) forbids use "para fines de minería
de datos o textos ni para cualquier otro fin". **La Vanguardia**
(`es-lavanguardia-hemeroteca`) explicitly extends its ban to inference and RAG. Under the
owner's source-use rule all three are excluded. The one possible exception is
**elDiario.es** (`es-eldiario-website`, 2012–now, member-funded). It says readers "No
pagan para leer la información", and its robots.txt blocks no AI crawler. But 5/5
sampled opinion pages carried `isAccessibleForFree: false`, and its legal page did not
render, so it stays partial_paywall/unknown until checked in a browser.

**1940–2005.** *What exists:* a lot. The **BNE Hemeroteca Digital**
(`es-bne-hemeroteca-digital`) holds full runs of ABC, El País, Diario 16 and La Nueva
España, Cuadernos para el diálogo and Cambio 16, the 1999–2009 current press, and about
200 dailies deposited since 2014. *What is free:* none of that. In BNE's own words, "solo
pueden consultarse desde las propias instalaciones de la BNE" (since 2021 also in
regional conservation centres). The open part stops in the 1930s. **ABC** 1891–now and
**La Vanguardia** 1881–now have page archives with free viewing (ABC: previews and
watermarked weekly PDFs; La Vanguardia: free per a dated XTEC guide, captcha-blocked
for us). Both terms forbid TDM. **BVPH** (`es-bvph-prensa-historica`) is free, mostly CC
BY 4.0, with an OAI-PMH endpoint and issues dated up to 2026. Its post-1940 share is
unmeasured and probably mostly local titles.

**Biggest gap:** everything after 1939 that we could legally tag. The Franco-era and
Transition press (1940–1982) is either in BNE reading rooms or in publisher archives
with type (a)/(b) reservations. 2005–now has no confirmed free, unreserved opinion source.

**Best for opinion / letters genres:** 2005–now: elDiario.es (to verify); historical:
ABC and La Vanguardia page archives (licence needed), BNE on-site (agreement needed).

### Recommended sources (ES)

1. `es-bvph-prensa-historica`: list post-1940 titles with CC BY 4.0 records (OAI-PMH
   metadata), since it is the only licence-clean route.
2. `es-eldiario-website`: check the paywall and aviso legal in a browser. If it is open
   and unreserved, it is the 2012–now opinion source.
3. `es-bne-hemeroteca-digital`: ask BNE about an on-site research agreement (the
   1940–2009 national press is all there).
4. `es-abc-hemeroteca` / `es-lavanguardia-hemeroteca`: licence requests only
   (profesionales.archivo@abc.es; La Vanguardia via aviso legal contact).

### Dead ends and leads (ES)

- **hemerotecadigital.bne.es**: bot-check 403 (curl and WebFetch). robots.txt allows only
  Googlebot and bingbot. We used BNE's PDF guide instead.
- **hemeroteca.lavanguardia.com**: AWS WAF captcha. We did not try to get around it.
- **ARCA** (arca.bnc.cat, Catalan historical magazines): connection refused or timed out 3 times.
- **Galiciana** (Biblioteca de Galicia): DNS failure and timeouts.
- **Liburuklik** (Basque digital library): TLS protocol error and 503.
- **Archivo de la Web Española** (BNE): bulk .es crawls since 2009, but per search
  snippets and the BNE collection policy PDF, consultation is in-room only, by URL. No
  entry.
- **El Mundo, 20minutos, Público.es**: not surveyed.
- **MyNews Hemeroteca**: a commercial press database licensed by university libraries
  (seen in search results only). A research-access lead.
- **Forums / comments** (out of v0 scope): not surveyed.

## PT

**2005–now.** *What exists:* Público, Diário de Notícias, Expresso and Observador, with
opinion columns and letters ("Cartas ao director", "Cartas dos Leitores"). *What is
free:* more than elsewhere in southern Europe. **Público** (`pt-publico-website`) had
5 of 8 sampled opinion pages free, including the daily "Cartas ao director". Its terms
carry generic all-rights-reserved wording with no TDM/AI clause, and robots.txt blocks
AI crawlers (type d only). **Diário de Notícias** (`pt-dn-website`) has a letters
section, is partly subscriber-only, and blocks no AI crawler. Its terms bar copying or
commercial use "sem autorização prévia" (ambiguous wording, possibly type b).
**Arquivo.pt** (`pt-arquivo-pt`) is the key infrastructure. It is a national web archive
with daily crawls of selected publications, a public JSON full-text search API with
extracted text, a one-year embargo, and terms that make access free "to support for work
of an educational, scientific or research nature" with "Use for commercial purposes ...
strictly forbidden". A test query found ~13,750 publico.pt "cartas ao director" captures
for 2012–2015.

**1940–2005.** **Casa Comum** (`pt-casa-comum-diario-de-lisboa`) has the near-complete
**Diário de Lisboa 1921–1990**, free to browse: 200–1,100 issues per year, the
"jornal dos intelectuais" of the "oposição possível". Using its images "requer
autorização prévia", and OCR availability is unknown. Pre-1974 issues are censored
press. **CETEMPúblico** (`pt-cetempublico`) covers Público 1991–1998: ~180M words, free
with registration for research, with an `opi` (opinion) section tag per extract. But
articles are cut into shuffled ~2-paragraph extracts that, by protocol, cannot be
reconstituted, so it allows paragraph-level analysis by half-year without per-text URLs.

**Biggest gap:** **1990–2005 full articles** (CETEMPúblico gives extracts only; Arquivo.pt
captures start ~2000 and are sparse early) and any free daily other than Diário de Lisboa
for 1940–1990.

**Best for opinion / letters genres:** 2005–now: Público opinion and "Cartas ao director"
(free share high, type d only), via the site or Arquivo.pt; 1991–1998: CETEMPúblico `opi`
extracts; 1940–1990: Diário de Lisboa (permission needed).

### Recommended sources (PT)

1. `pt-arquivo-pt`: the bulk route for 2005–now Portuguese press (API, research terms).
   Ask FCT|FCCN whether LLM tagging and publishing per-text Arquivo.pt URLs plus tags fits
   "educational, scientific or research" use and the "not forwarded" clause.
2. `pt-publico-website`: best single title (letters plus free opinion). Ask Público about
   research tagging, since its terms defer to "condições de uso livre permitidas por lei".
3. `pt-cetempublico`: 1991–1998 opinion at paragraph level, immediately usable for
   research.
4. `pt-casa-comum-diario-de-lisboa`: 1940–1990. Ask the Fundação about OCR and research
   use.

### Dead ends and leads (PT)

- **Hemeroteca Digital de Lisboa** (hemerotecadigital.cm-lisboa.pt): Cloudflare challenge
  (403 to curl and WebFetch). robots.txt carries `Content-Signal: search=yes,
  ai-train=no, use=reference` and blocks CCBot, ClaudeBot and GPTBot. Search snippets say
  it targets public-domain periodicals only, so it is likely nothing post-1940. No entry.
- **Expresso** (expresso.pt): opinion page 403 to curl, and WebFetch refused. robots.txt
  disallows CCBot, ClaudeBot and GPTBot. Paywall status unknown. No entry.
- **Diário de Notícias historical archive**: no online archive found.
- **Observador, Correio da Manhã**: not surveyed.
- **Forums / comments** (out of v0 scope): not surveyed.
