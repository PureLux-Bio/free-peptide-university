#!/usr/bin/env python3
"""
Free Peptide University — "This Week in Peptides" news fetcher.

Pulls recent, factual peptide news from three public sources, evidence-tags each
item, and writes data/news.json. Stdlib only (no pip deps) so it runs clean in CI.

Sources:
  - PubMed (NCBI E-utilities): new papers by term, last N days
  - ClinicalTrials.gov API v2: recently-updated trials by term
  - FDA press-release RSS: approvals / compounding-policy items mentioning peptides

Compliance: we store only factual metadata (title, source, date, link, evidence
tier) and link out to the primary source. We never reproduce abstracts, and we
never render anything as dosing/medical advice. Every item carries an evidence
tier so readers see "preclinical vs trial vs approved" at a glance.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "news.json")

UA = "FreePeptideUniversity-news/1.0 (+https://freepeptideuniversity.com)"
NCBI_KEY = os.environ.get("NCBI_API_KEY", "").strip()

# Curated peptide terms — what FPU teaches + the hot molecules.
TERMS = [
    "tirzepatide", "semaglutide", "retatrutide", "cagrilintide", "survodutide",
    "GLP-1 receptor agonist", "BPC-157", "TB-500", "GHK-Cu", "CJC-1295",
    "ipamorelin", "sermorelin", "MOTS-c", "tesamorelin", "melanotan",
    "growth hormone secretagogue", "peptide therapeutics",
]
# Tighter subset for the (heavier) trials query so we don't hammer the API.
TRIAL_TERMS = ["tirzepatide", "retatrutide", "semaglutide", "BPC-157", "cagrilintide"]

DAYS = 21          # look-back window
MAX_PER_SOURCE = 20
TIMEOUT = 25


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def _get_json(url):
    return json.loads(_get(url).decode("utf-8", "replace"))


def _norm_date(s):
    """Best-effort YYYY-MM-DD from assorted formats."""
    if not s:
        return ""
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y %b %d", "%Y %b", "%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    m = re.search(r"(\d{4})[-/ ](\d{1,2})[-/ ](\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"\d{4}", s)
    return m.group(0) if m else ""


def _matched_terms(text):
    t = (text or "").lower()
    return [term for term in TERMS if term.lower() in t]


# ── PubMed ──────────────────────────────────────────────────────────────────
def pubmed_tier(title, pubtypes):
    pts = " ".join(pubtypes).lower()
    title_l = (title or "").lower()
    if "meta-analysis" in pts:
        return "Meta-analysis"
    if "systematic review" in pts:
        return "Systematic review"
    if re.search(r"phase\s*(iii|3)", pts) or re.search(r"phase\s*(iii|3)", title_l):
        return "Phase 3"
    if "randomized controlled trial" in pts:
        return "RCT"
    if "clinical trial" in pts:
        return "Clinical trial"
    if any(w in title_l for w in ("mouse", "mice", "rat", "rodent", "murine",
                                  "in vitro", "in vivo", "cell", "preclinical")):
        return "Preclinical"
    if "review" in pts:
        return "Review"
    return "Study"


def fetch_pubmed():
    items = []
    term = "(" + " OR ".join(f'"{t}"' for t in TERMS) + ")"
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    key = f"&api_key={NCBI_KEY}" if NCBI_KEY else ""
    es = (base + "esearch.fcgi?db=pubmed&retmode=json&sort=date&retmax=40"
          f"&datetype=edat&reldate={DAYS}&term={urllib.parse.quote(term)}{key}")
    try:
        ids = _get_json(es).get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[pubmed] esearch failed: {e}", file=sys.stderr)
        return items
    if not ids:
        return items
    time.sleep(0.34)
    su = (base + "esummary.fcgi?db=pubmed&retmode=json&id="
          + ",".join(ids[:40]) + key)
    try:
        res = _get_json(su).get("result", {})
    except Exception as e:
        print(f"[pubmed] esummary failed: {e}", file=sys.stderr)
        return items
    for pmid in res.get("uids", []):
        r = res.get(pmid, {})
        title = (r.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        journal = r.get("fulljournalname") or r.get("source") or ""
        date = _norm_date(r.get("pubdate") or r.get("epubdate") or "")
        pubtypes = r.get("pubtype") or []
        items.append({
            "id": f"pubmed:{pmid}",
            "source": "PubMed",
            "type": "study",
            "title": title,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "date": date,
            "meta": " · ".join(x for x in (journal, (date[:4] if date else "")) if x),
            "tier": pubmed_tier(title, pubtypes),
            "terms": _matched_terms(title),
        })
    return items[:MAX_PER_SOURCE]


# ── ClinicalTrials.gov v2 ───────────────────────────────────────────────────
def fetch_trials():
    items = []
    seen = set()
    for term in TRIAL_TERMS:
        url = ("https://clinicaltrials.gov/api/v2/studies?"
               + urllib.parse.urlencode({
                   "query.term": term,
                   "pageSize": 8,
                   "sort": "LastUpdatePostDate:desc",
               }))
        try:
            data = _get_json(url)
        except Exception as e:
            print(f"[trials] {term} failed: {e}", file=sys.stderr)
            continue
        for st in data.get("studies", []):
            ps = st.get("protocolSection", {})
            nct = ps.get("identificationModule", {}).get("nctId")
            if not nct or nct in seen:
                continue
            seen.add(nct)
            title = (ps.get("identificationModule", {}).get("briefTitle") or "").strip()
            status = ps.get("statusModule", {}).get("overallStatus") or ""
            phases = ps.get("designModule", {}).get("phases") or []
            upd = (ps.get("statusModule", {})
                     .get("lastUpdatePostDateStruct", {}).get("date") or "")
            phase = (phases[0].replace("PHASE", "Phase ").replace("NA", "Trial")
                     if phases else "Trial")
            items.append({
                "id": f"nct:{nct}",
                "source": "ClinicalTrials.gov",
                "type": "trial",
                "title": title,
                "url": f"https://clinicaltrials.gov/study/{nct}",
                "date": _norm_date(upd),
                "meta": " · ".join(x for x in (status.title().replace("_", " "),
                                               nct) if x),
                "tier": phase,
                "terms": _matched_terms(term + " " + title),
            })
        time.sleep(0.2)
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:MAX_PER_SOURCE]


# ── FDA press-release RSS ───────────────────────────────────────────────────
FDA_FEEDS = [
    "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
    "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/drugs/rss.xml",
]
FDA_MATCH = re.compile(
    r"semaglutide|tirzepatide|liraglutide|glp-1|peptide|compound(ing|ed)|"
    r"retatrutide|weight[- ]loss drug", re.I)


def fetch_fda():
    items = []
    seen = set()
    for feed in FDA_FEEDS:
        try:
            xml = _get(feed)
            root = ET.fromstring(xml)
        except Exception as e:
            print(f"[fda] {feed} failed: {e}", file=sys.stderr)
            continue
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            desc = it.findtext("description") or ""
            if not title or not link or link in seen:
                continue
            if not FDA_MATCH.search(title + " " + desc):
                continue
            seen.add(link)
            items.append({
                "id": "fda:" + link,
                "source": "FDA",
                "type": "regulatory",
                "title": title,
                "url": link,
                "date": _norm_date(it.findtext("pubDate") or ""),
                "meta": "U.S. FDA",
                "tier": "Regulatory",
                "terms": _matched_terms(title + " " + desc) or ["regulatory"],
            })
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:10]


def main():
    all_items = []
    for fn in (fetch_pubmed, fetch_trials, fetch_fda):
        try:
            got = fn()
            print(f"{fn.__name__}: {len(got)} items", file=sys.stderr)
            all_items.extend(got)
        except Exception as e:
            print(f"{fn.__name__} crashed: {e}", file=sys.stderr)

    # Dedupe by id, sort newest first, cap.
    uniq = {}
    for it in all_items:
        uniq.setdefault(it["id"], it)
    items = sorted(uniq.values(), key=lambda x: (x.get("date") or ""), reverse=True)[:40]

    payload = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "count": len(items),
        "items": items,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"wrote {OUT} with {len(items)} items")


if __name__ == "__main__":
    main()
