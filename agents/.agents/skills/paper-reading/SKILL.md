---
name: paper-reading
description: Retrieve and read a scientific paper's real full text before describing it. Invoke whenever a task depends on what a specific paper says, or when a DOI, PMID, PMCID, bioRxiv link, or publisher URL appears.
---

# Reading a paper without hallucinating it

## The rule

Never describe a paper's contents from an abstract, a search snippet, or a
fetch tool's summary of a page you could not fully read. Either retrieve the
real full text, or say plainly that you could not and stop.

Every claim about a paper carries a label:

- **full text** — retrieved and read the article body.
- **abstract only** — say so in the same sentence as the claim.
- **not retrieved** — report the failure; do not fill the gap.

Quotes and paraphrase are different things. Mark direct quotes as quotes; do
not present your inference about a paper as the paper's own statement.

Why this exists: a first-pass fetch of a paywalled *Cell* paper's abstract
produced a confident, wrong mechanism claim (said the splicing effect was
cleavage-driven; the real full text says nuclease-dead steric blocking). The
gap between "what I read" and "what I said" is the failure mode this skill
closes.

## Retrieval

Start here for any identifier:

```bash
python3 <skill-dir>/scripts/get_fulltext.py <DOI | PMID | PMCID | title words> -o paper.txt
```

It resolves the identifier through Europe PMC and NCBI's ID converter, then
tries Europe PMC full-text XML → PMC HTML → bioRxiv/medRxiv, and prints a
provenance block naming the source and character count. Exit codes are the
contract:

| exit | meaning | required behaviour |
|---|---|---|
| 0 | full text retrieved | proceed; cite normally |
| 2 | only an abstract was reachable | label every claim "abstract only" |
| 3 | nothing reachable | say so and stop; ask for a PDF |

The script never fabricates; a failure is a real failure, not a prompt to guess.

## Figures and supplementary material

**Figure captions are not figure inspection.** Captions come with body text and
help locate the evidence, but they do not show axes, distributions, image
quality, lanes, annotations, or whether plotted data support the prose. When
the user asks to look at figures, actually open the figure images or rendered
PDF pages. State explicitly if only captions were available.

**Figure images** need `--figures DIR`. For PMC full text this pulls individual
images from PMC's CDN. For a publisher PDF, render the pages containing figures
to images, or use a browser's PDF screenshot facility, then open them. Do this
whenever the claim at stake lives in a panel rather than in prose (which
guide/lane/condition, what the axes say, which comparison was significant).

```bash
python3 <skill-dir>/scripts/get_fulltext.py <id> -o paper.txt --figures ./figs
```

**Supplementary files: fetch from Europe PMC.** Verified 2026-10-19 on 4 PMCIDs
(3 OA returned 0.6-1.25 MB zips; 1 non-OA returned an errorBean):

```bash
curl -sL -o suppl.zip "https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/supplementaryFiles"
file suppl.zip   # "Zip archive data" = got it; "XML" = an errorBean, not available
```

No browser, no auth, for OA-subset records. The zip also carries **figure and
table images**, which is the fix when a table does not come through
`fullTextXML` - journals that typeset tables as images (PLOS, some MDPI) ship
them as `*.t001.jpg` here. For a figure you intend to measure, take the
publisher's copy instead: PLOS serves ~3x the resolution of the PMC one at
`https://journals.plos.org/plosone/article/figure/image?size=large&id=<DOI>.g002`.

On an errorBean the record is outside the OA subset; fall back to an interactive
browser or ask the user, and until then say you did not read it.

**Elsevier supplementary files bypass the bot block.** `ars.els-cdn.com` serves
them to a plain request even when sciencedirect.com and the journal site return
`403` (verified 2026-10-21):

```bash
curl -sL -o mmc1.pdf "https://ars.els-cdn.com/content/image/1-s2.0-<PII>-mmc1.pdf"
```

The PII is the `S…` identifier in the article URL, without punctuation. Numbering
runs `mmc1`, `mmc2`, … in the order the article lists them, and the extension is
the file's own (`.pdf`, `.xlsx`, `.docx`). Wiley supplementary tables have no
equivalent and still `403`; ask the user for those.

The old `oa.fcgi` endpoint 404s - recipes referencing it are stale.

## When the script returns 2 or 3

Work down this list. Stop at the first one that yields real text.

1. **Follow version links in both directions.** A PMC page may be only a
   metadata shell when the preprint license forbids PMC archiving. Read its
   `Updated version available` / `Preprint of` link and try the published
   DOI. Conversely, search a published title for an accessible preprint.
2. **Check for a preprint.** Search the exact title plus `biorxiv OR medrxiv
   OR arxiv`. Preprints are unpaywalled and usually contain the same methods.
   Note in your answer that you read the preprint, not the version of record.
3. **Check OpenAlex `locations` for a green-OA copy.** It lists every known
   location, including institutional repositories that Unpaywall misses — which
   is how a paywalled *Genetics in Medicine* paper was read as the accepted
   manuscript in UCL Discovery (verified 2026-10-21). Say you read the accepted
   manuscript, not the version of record, and expect supplementary files to be
   deposited alongside it or not at all.

   ```bash
   curl -sL "https://api.openalex.org/works/doi:<DOI>" |
     python3 -c 'import json,sys; [print(l["landing_page_url"], l.get("pdf_url")) for l in json.load(sys.stdin)["locations"] if l.get("is_oa")]'
   ```
4. **Try the publisher page and PDF directly.** Some publishers serve full
   text to a plain request; see the access notes below for which ones do not.
   For a Nature accelerated/article-in-press page whose ordinary `.pdf` URL
   returns HTML, try `<article-url>_reference.pdf`. Validate the response:
   `Content-Type: application/pdf` and `%PDF` magic bytes.
5. **Use an interactive browser session** if browser-automation tools are
   available. Open the article or direct PDF and read its extracted text.
   When figures were requested, screenshot every page containing a main
   figure and inspect those screenshots.
6. **Ask the user for the PDF.** Cheap, reliable, and always correct. Prefer
   this over any elaborate workaround.

Do not present the paper's findings until one of these succeeds. Do not
synthesize a panel-by-panel narrative from search snippets, captions, or a
related paper. If the image pixels were not opened, say `figures not visually
inspected` rather than implying otherwise.

## Access notes (UChicago / RCC Midway)

Verified 2026-07-22 from `midway3-login4`:

- **The HPC is already on the institutional network.** Login-node external IP
  is in `128.135.0.0/16` (University of Chicago), so IP-authenticated
  subscription content resolves without a VPN or proxy login.
- **The real barrier is bot detection, not authentication.** ScienceDirect /
  Elsevier returns `403` with a captcha challenge to command-line clients
  regardless of entitlement. Credentials cannot fix this — the block is on the
  automated client, not the identity. Use an interactive browser instead.
- **PMC serves many non-open-access articles.** A record with
  `isOpenAccess: N` can still have a readable PMC deposit; the incident paper
  is exactly this case (`PMC12798835`, ~105k characters including Methods).
  Always try PMC before concluding a paper is unreachable.
- **Europe PMC `fullTextXML` is open-access-subset only** and 404s for non-OA
  records. That 404 is not evidence the paper is unavailable — fall through to
  PMC HTML.
- **Do not store library credentials for scraping.** Automated retrieval
  through the library proxy generally breaches publisher terms and risks the
  account. The tiers above cover the same ground without a secret at rest.

## Writing it up

When the result becomes a note or a summary, record what was actually read —
source (PMC / preprint / publisher / PDF) and whether it was full text. A note
that does not say what it was based on cannot be audited later.

For a claim that matters and that you could not source to primary full text,
flag it explicitly as needing the user's own eyes rather than burying the
uncertainty.
