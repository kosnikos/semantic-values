# Source coverage

Generated from data/sources/sources.yaml

## Usable (free access)

Cells show the number of usable (free or free-registration) sources per period. Source types out of scope for v0 (`forum`, setting `EXCLUDED_SOURCE_TYPES`) are left out of both tables; they stay in the registry.

| Country | 1940-1969 | 1970-1989 | 1990-2004 | 2005-now |
|---|---|---|---|---|
| FR | 1 | 0 | 0 | 4 |
| NL | 0 | 0 | 0 | 9 |
| BE | 1 | 1 | 0 | 5 |
| LU | 1 | 1 | 1 | 4 |
| DE | 4 | 4 | 7 | 8 |
| AT | 2 | 2 | 1 | 3 |
| CH | 2 | 2 | 2 | 2 |
| IT | 3 | 2 | 2 | 3 |
| GR | 1 | 1 | 3 | 7 |
| ES | 1 | 1 | 2 | 7 |
| PT | 1 | 1 | 3 | 2 |
| GB | 0 | 0 | 5 | 12 |

## Usable and not opted out

As above, minus sources whose restriction scope excludes them. Open scopes (setting `OPEN_SCOPES`): `none`, `ai_training_only`, `crawler_block_only`, `copyright_boilerplate`. `unknown` counts as open but is unverified; such sources are listed under open questions. Excluding scopes: `tdm_all`, `all_reuse`. Jurisdiction override (setting `JURISDICTION_OPEN_SCOPES`): in GB, `tdm_all`, `all_reuse` also count as open under CDPA s.29A. Overrides do not apply to sources accessed via `api` (setting `OVERRIDE_EXCLUDED_ACCESS_METHODS`). Source types out of scope for v0 (`forum`, setting `EXCLUDED_SOURCE_TYPES`) are left out of both tables; they stay in the registry.

| Country | 1940-1969 | 1970-1989 | 1990-2004 | 2005-now |
|---|---|---|---|---|
| FR | 1 | 0 | 0 | 4 |
| NL | 0 | 0 | 0 | 9 |
| BE | 1 | 1 | 0 | 5 |
| LU | 1 | 1 | 1 | 3 |
| DE | 2 | 2 | 4 | 5 |
| AT | 2 | 2 | 1 | 3 |
| CH | 2 | 2 | 2 | 2 |
| IT | 3 | 2 | 2 | 3 |
| GR | 1 | 1 | 3 | 7 |
| ES | 1 | 1 | 2 | 7 |
| PT | 0 | 0 | 2 | 2 |
| GB | 0 | 0 | 4 | 11 |

## Open questions

- gb-bbc-news: per_text_publish_allowed
- gb-independent: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gb-reddit-unitedkingdom: llm_api_allowed, per_text_publish_allowed, restriction_scope
- gb-reddit-askuk: llm_api_allowed, per_text_publish_allowed, restriction_scope
- gb-mumsnet: per_text_publish_allowed
- gb-uk-web-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- gb-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- gb-gdelt-url-index: llm_api_allowed, per_text_publish_allowed
- gb-british-newspaper-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- gb-daily-mail: per_text_publish_allowed
- gb-inews: per_text_publish_allowed
- gb-evening-standard: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gb-conversation-uk: llm_api_allowed, tdm_opt_out
- gb-opendemocracy: llm_api_allowed
- gb-prospect: per_text_publish_allowed
- gb-unherd: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gb-hello: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gb-good-housekeeping-uk: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gb-woman-and-home: per_text_publish_allowed
- gb-mirror: per_text_publish_allowed
- gb-manchester-evening-news: per_text_publish_allowed
- gb-ok-magazine: per_text_publish_allowed
- gr-nlg-efimeris: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- gr-kathimerini-historical-archive: llm_api_allowed, per_text_publish_allowed, restriction_scope
- gr-kathimerini-website: llm_api_allowed, per_text_publish_allowed
- gr-tovima-website: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gr-tanea-website: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gr-efsyn-website: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- gr-rizospastis-website: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- gr-insomnia-forum: llm_api_allowed, per_text_publish_allowed
- gr-reddit-greece: llm_api_allowed, per_text_publish_allowed, restriction_scope
- gr-greek-web-archive-portal: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- gr-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- gr-gdelt-url-index: llm_api_allowed, per_text_publish_allowed
- fr-gallica-presse: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- fr-retronews: per_text_publish_allowed
- fr-lemonde-website: llm_api_allowed, per_text_publish_allowed
- fr-agoravox: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- fr-reddit-france: llm_api_allowed, per_text_publish_allowed, restriction_scope
- fr-bnf-web-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- fr-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- fr-conversation-france: llm_api_allowed, tdm_opt_out
- fr-slate: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- fr-mediapart-club: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- fr-humanite: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- fr-valeurs-actuelles: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- be-kbr-belgicapress: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- be-lalibre-website: per_text_publish_allowed
- be-politics-be-forum: llm_api_allowed, per_text_publish_allowed, restriction_scope
- be-reddit-belgium: llm_api_allowed, per_text_publish_allowed, restriction_scope
- be-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- be-lavenir-website: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- be-rtbf-info: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- be-rtl-info: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- be-mo-magazine: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- be-dewereldmorgen: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- lu-eluxemburgensia: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- lu-rtl-lu: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- lu-tageblatt-website: per_text_publish_allowed
- lu-lessentiel: llm_api_allowed, per_text_publish_allowed
- lu-reddit-luxembourg: llm_api_allowed, per_text_publish_allowed, restriction_scope
- lu-web-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- lu-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-delpher-kranten: llm_api_allowed, per_text_publish_allowed, restriction_scope
- nl-kb-delpher-data: llm_api_allowed, per_text_publish_allowed
- nl-nrc-website: per_text_publish_allowed
- nl-geenstijl: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-fok-forum: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- nl-reddit-thenetherlands: llm_api_allowed, per_text_publish_allowed, restriction_scope
- nl-kb-web-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-nh-nieuws: llm_api_allowed, per_text_publish_allowed
- nl-omroep-brabant: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-metro: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-de-correspondent: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- nl-tpo: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- nl-wynias-week: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-dagelijkse-standaard: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- nl-viva: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- nl-opzij: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- de-zeitungsportal: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- de-zefys-ddr-presse: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- de-spiegel-print-archive: per_text_publish_allowed
- de-spiegel-website: per_text_publish_allowed
- de-zeit-website: llm_api_allowed, per_text_publish_allowed
- de-taz-website: llm_api_allowed, per_text_publish_allowed
- de-ids-dereko: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- de-dnb-web-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- de-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- de-berliner-zeitung: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- de-nd-aktuell: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- de-junge-welt: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- de-handelsblatt: llm_api_allowed, per_text_publish_allowed
- de-junge-freiheit: llm_api_allowed, per_text_publish_allowed
- de-brigitte: llm_api_allowed, per_text_publish_allowed
- de-gala: llm_api_allowed, per_text_publish_allowed
- de-eltern: llm_api_allowed, per_text_publish_allowed
- at-anno: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- at-arbeiterzeitung-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- at-derstandard-website: llm_api_allowed, per_text_publish_allowed
- at-diepresse-website: llm_api_allowed, per_text_publish_allowed
- at-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- ch-e-newspaperarchives: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- ch-letempsarchives: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- ch-letemps-website: llm_api_allowed, per_text_publish_allowed
- ch-nzz-website: per_text_publish_allowed
- ch-swissdox-liri: llm_api_allowed
- ch-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- it-archivio-lastampa: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- it-unita-archive: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- it-repubblica-archive: llm_api_allowed, per_text_publish_allowed
- it-corriere-archive: llm_api_allowed, per_text_publish_allowed
- it-internet-culturale-emeroteca: llm_api_allowed, per_text_publish_allowed
- it-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- es-bne-hemeroteca-digital: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- es-bvph-prensa-historica: llm_api_allowed, per_text_publish_allowed
- es-eldiario-website: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- es-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- es-larazon: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- es-rtve-noticias: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- es-hola: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- es-ctxt: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- es-elsalto: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- es-lamarea: llm_api_allowed, per_text_publish_allowed
- pt-arquivo-pt: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- pt-publico-website: llm_api_allowed, per_text_publish_allowed
- pt-dn-website: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
- pt-cetempublico: llm_api_allowed
- pt-casa-comum-diario-de-lisboa: llm_api_allowed, per_text_publish_allowed, tdm_opt_out
- pt-common-crawl-news: llm_api_allowed, per_text_publish_allowed, tdm_opt_out, restriction_scope
