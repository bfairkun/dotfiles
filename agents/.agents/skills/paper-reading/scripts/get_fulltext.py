#!/usr/bin/env python3
"""Resolve a paper identifier to real full text, or fail loudly.

Usage:
    get_fulltext.py <DOI | PMID | PMCID | title words> [-o OUT.txt] [--quiet]

Prints a PROVENANCE block (what was actually retrieved, and how much of it),
then the text. Exit codes:
    0  full text retrieved
    2  only an abstract was reachable  -> caller must label it "abstract only"
    3  nothing reachable               -> caller must say so and stop

Never invents or paraphrases content it could not fetch.
"""
import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
TIMEOUT = 45
# Below this many characters a "full text" is really just an abstract landing page.
FULLTEXT_MIN_CHARS = 8000


def get(url, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def try_get(url, accept=None):
    try:
        return get(url, accept)
    except Exception:
        return None


def strip_html(raw):
    raw = re.sub(r"(?is)<(script|style|nav|footer|head)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)</(p|div|section|h[1-6]|li|tr)>", "\n", raw)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    text = re.sub(r"[ \t\xa0]+", " ", text)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()


def classify(ident):
    s = ident.strip()
    if re.fullmatch(r"(?i)pmc\d+", s):
        return "pmcid", s.upper()
    if re.fullmatch(r"\d{6,9}", s):
        return "pmid", s
    if s.lower().startswith("10.") or "doi.org/" in s.lower():
        return "doi", re.sub(r"(?i)^https?://(dx\.)?doi\.org/", "", s)
    return "title", s


def resolve_ids(kind, value):
    """Fill in doi / pmid / pmcid via Europe PMC (which also reports availability)."""
    ids = {"doi": None, "pmid": None, "pmcid": None, "title": None,
           "inEPMC": None, "isOpenAccess": None}
    if kind == "pmcid":
        ids["pmcid"] = value
    elif kind == "pmid":
        ids["pmid"] = value
    elif kind == "doi":
        ids["doi"] = value

    query = {"doi": f'DOI:"{value}"', "pmid": f"EXT_ID:{value}",
             "pmcid": f"PMCID:{value}", "title": f'TITLE:"{value}"'}[kind]
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
           + urllib.parse.quote(query) + "&format=json&resultType=core&pageSize=1")
    raw = try_get(url)
    if raw:
        try:
            res = json.loads(raw)["resultList"]["result"]
        except Exception:
            res = []
        if res:
            r = res[0]
            ids["doi"] = ids["doi"] or r.get("doi")
            ids["pmid"] = ids["pmid"] or r.get("pmid")
            ids["pmcid"] = ids["pmcid"] or r.get("pmcid")
            ids["title"] = r.get("title")
            ids["inEPMC"] = r.get("inEPMC")
            ids["isOpenAccess"] = r.get("isOpenAccess")
            ids["abstract"] = r.get("abstractText")

    # NCBI's converter is the authority for DOI/PMID -> PMCID; try it as a backstop.
    if not ids["pmcid"] and (ids["doi"] or ids["pmid"]):
        key = ids["doi"] or ids["pmid"]
        raw = try_get("https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
                      f"?ids={urllib.parse.quote(key)}&format=json")
        if raw:
            try:
                rec = json.loads(raw)["records"][0]
                ids["pmcid"] = rec.get("pmcid") or ids["pmcid"]
                ids["pmid"] = str(rec.get("pmid") or ids["pmid"] or "") or None
            except Exception:
                pass
    return ids


def from_europepmc_xml(pmcid):
    """OA subset only; returns None for non-OA records (that is expected)."""
    if not pmcid:
        return None
    raw = try_get("https://www.ebi.ac.uk/europepmc/webservices/rest/"
                  f"{pmcid}/fullTextXML", accept="application/xml")
    if raw and "<article" in raw:
        return strip_html(raw), f"Europe PMC fullTextXML ({pmcid})"
    return None


def from_pmc_html(pmcid):
    """Works for many non-OA PMC deposits too — the main workhorse."""
    if not pmcid:
        return None
    raw = try_get(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/")
    if raw:
        text = strip_html(raw)
        if len(text) > FULLTEXT_MIN_CHARS:
            return text, f"PMC HTML ({pmcid})"
    return None


def from_biorxiv(doi):
    if not doi:
        return None
    raw = try_get(f"https://api.biorxiv.org/details/biorxiv/{doi}")
    if not raw:
        return None
    try:
        coll = json.loads(raw).get("collection") or []
    except Exception:
        return None
    if not coll:
        return None
    server = coll[-1].get("server", "biorxiv").lower()
    page = try_get(f"https://www.{server}.org/content/{doi}v"
                   f"{coll[-1].get('version', '1')}.full")
    if page:
        text = strip_html(page)
        if len(text) > FULLTEXT_MIN_CHARS:
            return text, f"{server} preprint full text ({doi})"
    return None


def fetch_figures(pmcid, outdir):
    """Download figure images from PMC's CDN (no interstitial on these URLs).

    Returns list of saved paths. Figure *captions* are already in the body text;
    these are the images themselves, for visual inspection.
    """
    import os
    if not pmcid:
        return []
    raw = try_get(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/")
    if not raw:
        return []
    urls = sorted(set(re.findall(
        r'https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^"\']+?\.(?:jpg|png|gif)', raw)))
    os.makedirs(outdir, exist_ok=True)
    saved = []
    for u in urls:
        name = u.rsplit("/", 1)[-1]
        path = os.path.join(outdir, name)
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read()
            if len(data) > 5000:                       # skip icons/spacers
                with open(path, "wb") as fh:
                    fh.write(data)
                saved.append(path)
        except Exception:
            continue
    return saved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("identifier")
    ap.add_argument("-o", "--out")
    ap.add_argument("--figures", metavar="DIR",
                    help="also download figure images to DIR (PMC only)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    kind, value = classify(a.identifier)
    ids = resolve_ids(kind, value)

    result = (from_europepmc_xml(ids["pmcid"])
              or from_pmc_html(ids["pmcid"])
              or from_biorxiv(ids["doi"]))

    head = [f"identifier : {a.identifier} (parsed as {kind})",
            f"title      : {ids.get('title')}",
            f"doi        : {ids['doi']}",
            f"pmid       : {ids['pmid']}",
            f"pmcid      : {ids['pmcid']}",
            f"openAccess : {ids.get('isOpenAccess')}   inEPMC: {ids.get('inEPMC')}"]

    if result:
        text, source = result
        head += [f"source     : {source}", f"chars      : {len(text)}",
                 "status     : FULL TEXT"]
        body = text
        code = 0
    elif ids.get("abstract"):
        head += ["source     : Europe PMC abstract record",
                 f"chars      : {len(ids['abstract'])}",
                 "status     : ABSTRACT ONLY — do not describe this paper's "
                 "results as verified; say 'abstract only'."]
        body = ids["abstract"]
        code = 2
    else:
        head += ["source     : none",
                 "status     : NOT RETRIEVED — say the text was unreachable and stop. "
                 "Do not infer contents."]
        body = ""
        code = 3

    if a.figures:
        figs = fetch_figures(ids["pmcid"], a.figures)
        head.append(f"figures    : {len(figs)} saved to {a.figures}"
                    if figs else "figures    : none retrieved")

    block = "=== PROVENANCE ===\n" + "\n".join(head) + "\n=== END PROVENANCE ===\n"
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(block + "\n" + body)
        if not a.quiet:
            print(block + f"\nwrote {a.out}")
    else:
        print(block)
        if not a.quiet:
            print(body)
    return code


if __name__ == "__main__":
    sys.exit(main())
