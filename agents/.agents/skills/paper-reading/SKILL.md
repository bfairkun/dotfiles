---
name: paper-reading
description: Retrieve and read the real full text of a scientific paper before describing its contents. Invoke whenever a task depends on what a specific paper says — summarizing it, checking a claim or mechanism against it, extracting methods/reagents/coordinates, or writing a wiki/source note about it — and whenever a DOI, PMID, PMCID, bioRxiv link, or publisher URL appears in the request.
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

## When the script returns 2 or 3

Work down this list. Stop at the first one that yields real text.

1. **Check for a preprint.** Search the exact title plus `biorxiv OR medrxiv
   OR arxiv`. Preprints are unpaywalled and usually contain the same methods.
   Note in your answer that you read the preprint, not the version of record.
2. **Try the publisher page directly.** Some publishers serve full text to a
   plain request; see the access notes below for which ones do not.
3. **Use an interactive browser session** if browser-automation tools are
   available. This is the best fallback for subscription content: it reuses
   the user's own logged-in session, and a real browser is not treated as a
   bot. Open the article and read the rendered page.
4. **Ask the user for the PDF.** Cheap, reliable, and always correct. Prefer
   this over any elaborate workaround.

Do not present the paper's findings until one of these succeeds.

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
