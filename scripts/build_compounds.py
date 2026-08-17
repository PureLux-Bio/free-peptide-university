#!/usr/bin/env python3
"""
Free Peptide University — deep compound page generator.

Authoring model: each compound is a Python dict with accurate, cited content
(sections are raw HTML so we can hedge precisely and add <sup> citations).
Run:  python3 scripts/build_compounds.py
Writes compounds/<slug>.html for each entry and keeps sitemap.xml in sync.

Compliance: every page carries an RUO/status banner + an evidence-tier badge and
cites primary literature. Nothing is dosing or medical advice.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = "https://freepeptideuniversity.com"

STYLE = """:root{--bg:#060912;--surface:#101829;--cream:#0A0F1C;--text:#EAF2FF;--soft:#AEBCD8;--muted:#6E7C99;--aqua:#7DEBDC;--aqua2:#34D6C2;--border:rgba(94,230,208,.20)}
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;line-height:1.75;letter-spacing:.2px;-webkit-font-smoothing:antialiased;background-image:linear-gradient(rgba(94,230,208,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(94,230,208,.03) 1px,transparent 1px);background-size:46px 46px}
    .wrap{max-width:840px;margin:0 auto;padding:56px 28px 90px}
    h1,h2,h3{font-family:'Sora',sans-serif;line-height:1.2;color:var(--text)}
    h1{font-size:clamp(2rem,5vw,3rem);margin:8px 0 4px}
    h2{font-size:1.45rem;margin:44px 0 12px}
    h3{font-size:1.1rem;margin:24px 0 6px}
    p,li{color:var(--soft);font-size:1.02rem}
    a{color:var(--aqua)}
    strong{color:var(--text)}
    sup a{font-size:.7em;text-decoration:none;padding:0 1px}
    .eyebrow{font-size:.72rem;letter-spacing:.3em;text-transform:uppercase;color:var(--aqua);font-weight:600}
    .sub{color:var(--muted);font-size:1rem;margin:0 0 18px}
    .topnav{display:flex;justify-content:space-between;align-items:center;margin-bottom:40px;font-size:.92rem}
    .topnav .brand{font-family:'Sora';font-weight:700;color:var(--text);text-decoration:none}
    .topnav .brand span{color:var(--aqua)}
    .badges{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 24px}
    .badge{font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;font-weight:700;padding:6px 12px;border-radius:999px}
    .b-class{color:#5FE0B0;background:rgba(52,214,194,.12);border:1px solid rgba(52,214,194,.3)}
    .b-evi{color:#C9A9F5;background:rgba(160,120,245,.12);border:1px solid rgba(160,120,245,.32)}
    .b-evi-trial{color:#7DC4FF;background:rgba(58,168,255,.12);border:1px solid rgba(58,168,255,.32)}
    .b-reg{color:#E7C56B;background:rgba(231,197,107,.1);border:1px solid rgba(231,197,107,.34)}
    .b-reg-ok{color:#5FE0B0;background:rgba(52,214,194,.1);border:1px solid rgba(52,214,194,.3)}
    .ruo{background:rgba(231,197,107,.06);border:1px solid rgba(231,197,107,.28);border-radius:12px;padding:16px 20px;margin:6px 0 8px;font-size:.9rem;color:var(--soft)}
    .ruo b{color:#E7C56B}
    .callout{background:linear-gradient(135deg,rgba(143,247,232,.14),rgba(94,230,208,.06));border-left:3px solid var(--aqua2);border-radius:10px;padding:16px 20px;margin:24px 0;font-size:.97rem}
    .callout b{color:var(--aqua)}
    .spec{width:100%;border-collapse:collapse;margin:18px 0;font-size:.94rem}
    .spec th,.spec td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--border);vertical-align:top}
    .spec th{font-family:'Sora';font-weight:600;color:var(--aqua);width:38%;background:var(--cream)}
    .tscroll{overflow-x:auto}
    ul{padding-left:20px}
    li{margin:7px 0}
    .refs{margin-top:14px;font-size:.9rem}
    .refs li{margin:9px 0;color:var(--muted)}
    .refs a{color:var(--aqua)}
    .disc{background:var(--cream);border-left:3px solid var(--aqua2);padding:14px 18px;border-radius:8px;font-size:.82rem;color:var(--muted);margin:34px 0 0}
    .sponsor{font-size:.85rem;color:var(--soft);margin:26px 0 0;padding:12px 18px;background:linear-gradient(135deg,rgba(143,247,232,.06),rgba(94,230,208,.03));border:1px solid var(--border);border-radius:10px}
    .sponsor a{color:var(--aqua);font-weight:600}
    .cta{display:inline-block;background:linear-gradient(135deg,#9BF7EA,#34D6C2 42%,#3AA8FF);color:#04140F;font-weight:600;padding:14px 30px;border-radius:999px;text-decoration:none;margin-top:14px}
    footer{border-top:1px solid var(--border);margin-top:52px;padding-top:26px;font-size:.8rem;color:var(--muted)}"""


def spec_table(rows):
    body = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    return f'<div class="tscroll"><table class="spec"><tbody>{body}</tbody></table></div>'


def render(c):
    url = f"{BASE}/compounds/{c['slug']}.html"
    title = f"{c['title']} | Free Peptide University"
    art = {"@context": "https://schema.org", "@type": "Article",
           "headline": c["title"], "description": c["desc"],
           "author": {"@type": "Organization", "name": "Free Peptide University"},
           "publisher": {"@type": "Organization", "name": "Free Peptide University"},
           "mainEntityOfPage": url, "image": f"{BASE}/og-image.jpg",
           "datePublished": "2026-08-17", "dateModified": "2026-08-17"}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList",
             "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Free Peptide University", "item": BASE + "/"},
                 {"@type": "ListItem", "position": 2, "name": "Compounds"},
                 {"@type": "ListItem", "position": 3, "name": c["name"], "item": url}]}
    b = c["badges"]
    badges = (f'<span class="badge b-class">{b["class"]}</span>'
              f'<span class="badge {b.get("eviCls","b-evi")}">{b["evidence"]}</span>'
              f'<span class="badge {b.get("regCls","b-reg")}">{b["reg"]}</span>')
    secs = "".join(f'<h2>{s["h"]}</h2>\n{s["html"]}' for s in c["sections"])
    refs = "".join(
        f'<li id="r{r["n"]}">{r["label"]} <a href="{r["url"]}" target="_blank" rel="noopener">{r["cite"]}</a></li>'
        for r in c["refs"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{c['desc']}" />
  <link rel="canonical" href="{url}" />
  <meta name="robots" content="index, follow" />
  <meta name="theme-color" content="#060912" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Free Peptide University" />
  <meta property="og:title" content="{c['title']}" />
  <meta property="og:description" content="{c['desc']}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{BASE}/og-image.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet" />
  <script type="application/ld+json">{json.dumps(art)}</script>
  <script type="application/ld+json">{json.dumps(crumb)}</script>
  <style>{STYLE}</style>
</head>
<body>
  <div class="wrap">
    <nav class="topnav">
      <a class="brand" href="../index.html"><span>◆</span> Free Peptide University</a>
      <a href="../index.html">Enter the library →</a>
    </nav>
    <div class="eyebrow">Compound Reference</div>
    <h1>{c['name']}</h1>
    <p class="sub">{c['sub']}</p>
    <div class="badges">{badges}</div>
    <div class="ruo">{c['ruo']}</div>
    {secs}
    <h2 id="refs">References</h2>
    <ol class="refs">{refs}</ol>
    <p class="sponsor">This free reference is made possible by our sponsor, <a href="https://pureluxbio.com/?utm_source=freepeptideuniversity&amp;utm_medium=sponsor&amp;utm_campaign=compound-{c['slug']}" target="_blank" rel="noopener sponsored">PureLux Bio</a> — U.S.-made research-grade peptides.</p>
    <p><a class="cta" href="../index.html">Explore the full library &amp; 75-compound reference →</a></p>
    <div class="disc">For educational and research purposes only. This content is not medical advice. {c.get('discExtra','Compounds referenced are research use only and not intended to diagnose, treat, cure, or prevent any disease.')} Free Peptide University does not sell compounds.</div>
    <footer>Free Peptide University is an independent educational resource, made free to the public through the sponsorship of Adonis TRT and <a href="https://pureluxbio.com/?utm_source=freepeptideuniversity&amp;utm_medium=sponsor&amp;utm_campaign=compound-footer" target="_blank" rel="noopener sponsored">PureLux Bio</a>. · <a href="../privacy.html">Privacy</a> · <a href="../terms.html">Terms</a></footer>
  </div>
</body>
</html>
"""


def sync_sitemap(slugs):
    sm_path = os.path.join(ROOT, "sitemap.xml")
    sm = open(sm_path).read()
    added = []
    for slug in slugs:
        loc = f"{BASE}/compounds/{slug}.html"
        if loc not in sm:
            entry = f'  <url><loc>{loc}</loc><lastmod>2026-08-17</lastmod></url>\n'
            sm = sm.replace("</urlset>", entry + "</urlset>")
            added.append(slug)
    if added:
        open(sm_path, "w").write(sm)
    return added


# Hand-authored pages (not generated here) that still belong in the index.
EXTRA_FOR_INDEX = [
    {"slug": "bpc-157", "name": "BPC-157",
     "badges": {"class": "Healing & tissue-repair research",
                "evidence": "Evidence: preclinical + early pilots",
                "reg": "RUO · not FDA-approved · WADA-prohibited"}},
    {"slug": "semaglutide", "name": "Semaglutide",
     "badges": {"class": "Metabolic · incretin (GLP-1)",
                "evidence": "Evidence: large Phase 3 RCTs", "eviCls": "b-evi-trial",
                "reg": "FDA-approved drug", "regCls": "b-reg-ok"}},
]


def index_page():
    cards = ""
    for c in sorted(COMPOUNDS + EXTRA_FOR_INDEX, key=lambda x: x["name"].lower()):
        b = c["badges"]
        cards += (f'<a class="cx" href="{c["slug"]}.html">'
                  f'<div class="cxtop"><span class="badge {b.get("regCls","b-reg")}">{b["reg"]}</span></div>'
                  f'<h3>{c["name"]}</h3><p class="cxcls">{b["class"]}</p>'
                  f'<p class="cxevi">{b["evidence"]}</p></a>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Compound Library — In-Depth Peptide Profiles | Free Peptide University</title>
  <meta name="description" content="In-depth, citations-first profiles of research peptides and related compounds — mechanism, pharmacokinetics, evidence tier, and regulatory status for each." />
  <link rel="canonical" href="{BASE}/compounds/" />
  <meta name="robots" content="index, follow" />
  <meta name="theme-color" content="#060912" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="Compound Library — In-Depth Peptide Profiles" />
  <meta property="og:description" content="Citations-first profiles: mechanism, PK, evidence tier, and regulatory status per compound." />
  <meta property="og:url" content="{BASE}/compounds/" />
  <meta property="og:image" content="{BASE}/og-image.jpg" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet" />
  <style>{STYLE}
    .cxgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;margin-top:30px}}
    .cx{{display:block;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px;text-decoration:none;transition:transform .4s var(--ease,ease),box-shadow .4s;box-shadow:0 12px 30px rgba(0,0,0,.42)}}
    .cx:hover{{transform:translateY(-4px);box-shadow:0 26px 60px rgba(0,0,0,.55);border-color:rgba(94,230,208,.4)}}
    .cxtop{{margin-bottom:12px}}
    .cx h3{{margin:0 0 4px;font-size:1.15rem;color:var(--text)}}
    .cxcls{{margin:0;font-size:.82rem;color:var(--aqua)}}
    .cxevi{{margin:6px 0 0;font-size:.78rem;color:var(--muted)}}
  </style>
</head>
<body>
  <div class="wrap">
    <nav class="topnav">
      <a class="brand" href="../index.html"><span>◆</span> Free Peptide University</a>
      <a href="../index.html">Enter the library →</a>
    </nav>
    <div class="eyebrow">Compound Library</div>
    <h1>In-depth compound profiles</h1>
    <p class="sub">Citations-first pages — mechanism, pharmacokinetics, the real evidence tier, and regulatory status for each compound. New profiles added regularly.</p>
    <div class="ruo"><b>Research framed.</b> Educational only — not medical advice, not dosing. Each page states whether a compound is FDA-approved, investigational, or research-use-only.</div>
    <div class="cxgrid">{cards}</div>
    <p class="sponsor" style="margin-top:34px">Made possible by our sponsor, <a href="https://pureluxbio.com/?utm_source=freepeptideuniversity&amp;utm_medium=sponsor&amp;utm_campaign=compounds-index" target="_blank" rel="noopener sponsored">PureLux Bio</a> — U.S.-made research-grade peptides.</p>
    <footer>Free Peptide University is an independent educational resource, made free to the public through the sponsorship of Adonis TRT and PureLux Bio. · <a href="../privacy.html">Privacy</a> · <a href="../terms.html">Terms</a></footer>
  </div>
</body>
</html>
"""


def main():
    os.makedirs(os.path.join(ROOT, "compounds"), exist_ok=True)
    for c in COMPOUNDS:
        out = os.path.join(ROOT, "compounds", f"{c['slug']}.html")
        open(out, "w").write(render(c))
        print("wrote", out)
    open(os.path.join(ROOT, "compounds", "index.html"), "w").write(index_page())
    print("wrote compounds/index.html")
    added = sync_sitemap([c["slug"] for c in COMPOUNDS])
    # ensure the index is in the sitemap too
    sm_path = os.path.join(ROOT, "sitemap.xml")
    sm = open(sm_path).read()
    if f"{BASE}/compounds/</loc>" not in sm:
        sm = sm.replace("</urlset>", f'  <url><loc>{BASE}/compounds/</loc><lastmod>2026-08-17</lastmod></url>\n</urlset>')
        open(sm_path, "w").write(sm)
    print("sitemap added:", added or "(all already present)")


# ── Compound content (accurate, hedged, cited) ──────────────────────────────
COMPOUNDS = [
  {
    "slug": "tirzepatide", "name": "Tirzepatide",
    "title": "Tirzepatide (GIP/GLP-1): Dual-Agonist Mechanism & Evidence",
    "sub": "Dual GIP + GLP-1 receptor agonist (\"twincretin\") · marketed as Mounjaro / Zepbound",
    "desc": "A cited profile of tirzepatide: the dual GIP/GLP-1 agonist mechanism, half-life engineering, the SURPASS/SURMOUNT trial base, and regulatory status.",
    "badges": {"class": "Metabolic · dual incretin", "evidence": "Evidence: large Phase 3 RCTs", "eviCls": "b-evi-trial", "reg": "FDA-approved drug", "regCls": "b-reg-ok"},
    "ruo": "<b>Important distinction.</b> Tirzepatide is an <b>FDA-approved prescription drug</b>, not a research chemical. This is educational science, not medical advice, and not an endorsement of sourcing it outside a licensed prescription.",
    "sections": [
      {"h": "What it is", "html": "<p>Tirzepatide is a single engineered peptide that activates <strong>two</strong> incretin receptors at once — <strong>GIP</strong> (glucose-dependent insulinotropic polypeptide) and <strong>GLP-1</strong> — earning the nickname \"twincretin.\" It builds on the <a href=\"semaglutide.html\">GLP-1 story</a> by adding a second, complementary pathway.</p>"},
      {"h": "Mechanism of action", "html": "<p>Both GIP-R and GLP-1R are <strong>class B GPCRs</strong>.<sup><a href=\"#r2\">2</a></sup> Agonizing both is thought to produce additive/synergistic effects on insulin secretion, glucagon, gastric emptying, and appetite — which is the leading explanation for why tirzepatide has shown <em>greater</em> weight and glycemic effects than GLP-1 alone in head-to-head trials.<sup><a href=\"#r1\">1</a></sup> The precise contribution of GIP-agonism is still an active research question.</p><div class=\"callout\"><b>Why it matters:</b> tirzepatide is the proof-of-concept that <b>multi-receptor peptides</b> can outperform single-target ones — the design logic now driving triple agonists like <a href=\"retatrutide.html\">retatrutide</a>.</div>"},
      {"h": "Pharmacokinetics", "html": spec_table([("Class", "Dual GIP/GLP-1 receptor agonist"), ("Modification", "C20 fatty-diacid acylation + albumin binding + DPP-4-resistant residues"), ("Half-life", "≈ 5 days (once-weekly)"), ("Receptors", "GIP-R and GLP-1R (class B GPCRs)")]) + "<p>Same half-life-engineering toolkit as semaglutide — a fatty-acid chain enabling albumin binding turns a short-lived peptide into a weekly drug.<sup><a href=\"#r3\">3</a></sup></p>"},
      {"h": "State of the evidence", "html": "<p>Large Phase 3 base: the <strong>SURPASS</strong> program (type 2 diabetes) and <strong>SURMOUNT</strong> program (obesity), with cardiovascular and other outcomes trials ongoing. This is a top-evidence-tier, FDA-approved drug — the opposite of an RUO peptide with no trials.</p>"},
      {"h": "Regulatory reality", "html": "<ul><li><strong>Approved:</strong> FDA-approved (Mounjaro/Zepbound), prescription-only.</li><li><strong>Compounded \"research\" tirzepatide:</strong> the FDA has moved to <strong>exclude tirzepatide from the 503B bulks list</strong>; the shortage-era compounding window has closed.<sup><a href=\"#r4\">4</a></sup> Powder sold as a chemical is not the approved medicine.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "Investigational GLP-1-based medicines & triple-targeting (Harvard HMS insight).", "cite": "learn.hms.harvard.edu", "url": "https://learn.hms.harvard.edu/insights/all-insights/investigational-glp-1-based-medicine-uses-triple-targeting-accelerate-weight-loss"},
      {"n": "2", "label": "Kobilka, GPCR structure (2012 Nobel lecture/review).", "cite": "Angew. Chem.", "url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/anie.201302116"},
      {"n": "3", "label": "Peptide half-life extension — lipidation/albumin binding (review).", "cite": "ACS Med. Chem. Lett.", "url": "https://pubs.acs.org/doi/10.1021/acsmedchemlett.8b00226"},
      {"n": "4", "label": "FDA: proposal to exclude semaglutide/tirzepatide/liraglutide from 503B bulks list.", "cite": "fda.gov", "url": "https://www.fda.gov/news-events/press-announcements/fda-proposes-exclude-semaglutide-tirzepatide-and-liraglutide-503b-bulks-list"},
    ],
    "discExtra": "Tirzepatide is a prescription drug; obtain and use medicines only under a licensed professional.",
  },
  {
    "slug": "retatrutide", "name": "Retatrutide",
    "title": "Retatrutide (GIP/GLP-1/Glucagon): Triple-Agonist Mechanism & Trial Status",
    "sub": "Investigational triple GIP + GLP-1 + glucagon receptor agonist",
    "desc": "A cited profile of retatrutide: the triple-agonist mechanism (adding glucagon-receptor agonism), the Phase 2 signal, and why 'not yet approved' is the key fact.",
    "badges": {"class": "Metabolic · triple incretin", "evidence": "Evidence: Phase 2 (Phase 3 ongoing)", "eviCls": "b-evi-trial", "reg": "Investigational · not approved", "regCls": "b-reg"},
    "ruo": "<b>Not an approved drug.</b> Retatrutide is <b>investigational</b> — still in clinical trials, not FDA-approved. Any \"retatrutide\" sold as a research chemical is not the trial medicine and has no approved use. Educational only; not medical advice.",
    "sections": [
      {"h": "What it is", "html": "<p>Retatrutide is a single peptide that agonizes <strong>three</strong> receptors: <strong>GIP, GLP-1, and glucagon</strong>. It extends the dual-agonist logic of <a href=\"tirzepatide.html\">tirzepatide</a> by adding glucagon-receptor activity.</p>"},
      {"h": "Mechanism — why add glucagon?", "html": "<p>Counter-intuitively, agonizing the <strong>glucagon receptor</strong> (alongside the incretin receptors) is thought to increase <strong>energy expenditure</strong> and hepatic fat handling, while the GLP-1 component offsets glucagon's tendency to raise blood sugar. The combined design aims for larger weight effects than dual agonists.<sup><a href=\"#r1\">1</a></sup> All three are <strong>class B GPCRs</strong>.<sup><a href=\"#r2\">2</a></sup></p><div class=\"callout\"><b>Evidence caveat:</b> the mechanism is well-reasoned and the early data striking, but this is a molecule <em>still being tested</em> — long-term efficacy and safety are not yet established.</div>"},
      {"h": "State of the evidence", "html": "<p><strong>Phase 2</strong> trials reported large weight reductions and generated significant attention; <strong>Phase 3</strong> trials are ongoing. It is <strong>not approved</strong> anywhere. Track current trial status on ClinicalTrials.gov.<sup><a href=\"#r3\">3</a></sup></p>"},
      {"h": "Regulatory reality", "html": "<ul><li><strong>Status:</strong> investigational; no approved product; not legally a medicine.</li><li><strong>Gray-market powder:</strong> unverified \"retatrutide\" is neither the trial drug nor quality-controlled — the COA and evidence-tier caveats matter enormously here.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "Triple-targeting to accelerate weight loss (Harvard HMS insight).", "cite": "learn.hms.harvard.edu", "url": "https://learn.hms.harvard.edu/insights/all-insights/investigational-glp-1-based-medicine-uses-triple-targeting-accelerate-weight-loss"},
      {"n": "2", "label": "Kobilka, GPCR structure (2012 Nobel lecture/review).", "cite": "Angew. Chem.", "url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/anie.201302116"},
      {"n": "3", "label": "Current retatrutide trial records.", "cite": "ClinicalTrials.gov", "url": "https://clinicaltrials.gov/search?term=retatrutide"},
    ],
  },
  {
    "slug": "tb-500", "name": "TB-500",
    "title": "TB-500 (Thymosin β4 fragment): Mechanism & Evidence Status",
    "sub": "A synthetic peptide related to Thymosin β4 · healing/regenerative research",
    "desc": "A cited profile of TB-500: its relationship to thymosin β4, the actin/angiogenesis mechanism proposed in preclinical work, the thin human evidence, and RUO/WADA status.",
    "badges": {"class": "Healing & tissue-repair research", "evidence": "Evidence: preclinical (minimal human)", "reg": "RUO · not FDA-approved · WADA-prohibited"},
    "ruo": "<b>Research Use Only.</b> TB-500 is not an approved medicine and not for human use. Nothing here is medical advice. Note also a common confusion: <b>TB-500 is a synthetic fragment marketed in reference to Thymosin β4 (Tβ4)</b> — they are related but not identical, and much cited data is actually on Tβ4.",
    "sections": [
      {"h": "What it is", "html": "<p>TB-500 refers to a synthetic peptide corresponding to an <strong>active region of Thymosin β4</strong>, a naturally occurring 43-amino-acid protein involved in cell repair. Research-grade \"TB-500\" is typically a shorter fragment sold RUO. It is discussed alongside <a href=\"bpc-157.html\">BPC-157</a> as a \"healing\" peptide.</p>"},
      {"h": "Proposed mechanism", "html": "<ul><li><strong>Actin regulation.</strong> Thymosin β4's core biology is binding/sequestering <strong>G-actin</strong>, regulating the cytoskeleton — which supports <strong>cell migration</strong> central to wound repair.<sup><a href=\"#r1\">1</a></sup></li><li><strong>Angiogenesis &amp; anti-inflammatory effects</strong> are reported in preclinical models.<sup><a href=\"#r2\">2</a></sup></li></ul><div class=\"callout\"><b>Read carefully:</b> most of this mechanism is established for the full Tβ4 protein in animal/cell studies — extrapolating it wholesale to injected \"TB-500\" fragment in humans is exactly the kind of leap Chapter 3 (Myth vs. Research) warns about.</div>"},
      {"h": "Pharmacology", "html": spec_table([("Parent", "Thymosin β4 (43 aa protein)"), ("Marketed form", "Synthetic active-region fragment (RUO)"), ("Half-life", "Not well characterized in humans"), ("Mechanism anchor", "G-actin binding → cell migration")])},
      {"h": "State of the evidence", "html": "<ul><li><strong>Preclinical:</strong> supportive animal/cell data for Tβ4.</li><li><strong>Human:</strong> minimal for TB-500 specifically; <strong>no Phase III RCTs</strong>.<sup><a href=\"#r2\">2</a></sup></li></ul>"},
      {"h": "Regulatory & sport status", "html": "<ul><li><strong>FDA/EMA:</strong> not approved; RUO only.</li><li><strong>WADA:</strong> prohibited (class <strong>S2</strong>, peptide hormones/growth factors &amp; mimetics) — relevant for tested athletes.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "Peptide Therapeutics 2.0 — open-access review of peptide mechanisms.", "cite": "PMC7287585", "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7287585/"},
      {"n": "2", "label": "Background, efficacy & safety of BPC-157 and TB-500 (2025).", "cite": "globalrph.com", "url": "https://globalrph.com/2025/11/bpc-157-and-tb-500-background-indications-efficacy-and-safety/"},
    ],
  },
  {
    "slug": "cjc-1295-ipamorelin", "name": "CJC-1295 + Ipamorelin",
    "title": "CJC-1295 + Ipamorelin: GH-Secretagogue Mechanism & Evidence",
    "sub": "A GHRH analog paired with a selective ghrelin-receptor (GHS-R) agonist",
    "desc": "A cited profile of the CJC-1295 + Ipamorelin combination: the two GH-release pathways, why they're stacked, the DAC half-life trick, and RUO/WADA status.",
    "badges": {"class": "Growth-hormone secretagogues", "evidence": "Evidence: early human PK / preclinical", "reg": "RUO · not FDA-approved · WADA-prohibited"},
    "ruo": "<b>Research Use Only.</b> Neither compound is an approved therapy, and the combination is not a medicine. Educational only — no dosing or medical advice.",
    "sections": [
      {"h": "What they are", "html": "<p>This is a <strong>two-pathway growth-hormone (GH) secretagogue stack</strong>. <strong>CJC-1295</strong> is a <strong>GHRH analog</strong> (mimics growth-hormone-releasing hormone). <strong>Ipamorelin</strong> is a selective <strong>ghrelin-receptor (GHS-R) agonist</strong>. They are combined because they push GH release through <em>different</em> receptors.</p>"},
      {"h": "Mechanism — two doors to the same room", "html": "<ul><li><strong>CJC-1295 → GHRH receptor:</strong> stimulates the pituitary to make/release GH, raising the baseline signal.</li><li><strong>Ipamorelin → GHS-R (ghrelin receptor):</strong> triggers a GH <em>pulse</em> and, being selective, is reported to do so with little effect on cortisol or prolactin.<sup><a href=\"#r2\">2</a></sup></li></ul><div class=\"callout\"><b>Why stack them:</b> a GHRH analog + a ghrelin mimetic act synergistically on the GH axis — the textbook rationale for combination research on secretagogues.<sup><a href=\"#r1\">1</a></sup></div>"},
      {"h": "Half-life & the DAC distinction", "html": spec_table([("CJC-1295 (no DAC)", "GHRH analog; short-acting"), ("CJC-1295 with DAC", "Adds a Drug-Affinity-Complex (albumin binding) → half-life of days"), ("Ipamorelin", "Selective GHS-R agonist; short pulse"), ("Combined effect", "Elevated baseline (CJC) + pulsatile release (Ipamorelin)")]) + "<p><strong>DAC</strong> is the same half-life-engineering idea seen in <a href=\"semaglutide.html\">semaglutide</a>: attach a group that binds albumin so the peptide isn't cleared for days. \"No-DAC\" vs \"DAC\" versions behave very differently for this reason.</p>"},
      {"h": "State of the evidence", "html": "<ul><li>CJC-1295 (with DAC) has early human <strong>pharmacokinetic</strong> data showing sustained GH/IGF-1 elevation; ipamorelin is largely preclinical/early.</li><li>The <strong>combination is not an approved therapy</strong> and lacks large outcome trials.</li></ul>"},
      {"h": "Regulatory & sport status", "html": "<ul><li><strong>FDA/EMA:</strong> not approved; RUO.</li><li><strong>WADA:</strong> GH secretagogues are prohibited (class <strong>S2</strong>) — relevant for tested athletes.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "Growth-hormone secretagogues — review.", "cite": "rco2.9 (Wiley)", "url": "https://onlinelibrary.wiley.com/doi/full/10.1002/rco2.9"},
      {"n": "2", "label": "The ghrelin / GHS-R pathway (review).", "cite": "PMC5412382", "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5412382/"},
    ],
  },
  {
    "slug": "ghk-cu", "name": "GHK-Cu",
    "title": "GHK-Cu (Copper Peptide): Mechanism & Evidence",
    "sub": "Copper-binding tripeptide (glycyl-histidyl-lysine + Cu²⁺) · skin & tissue-remodeling research",
    "desc": "A cited profile of GHK-Cu: the copper-tripeptide biology, its gene-expression and collagen effects, where the evidence is strong (topical) vs thin (injectable), and its status.",
    "badges": {"class": "Cosmetic · skin & tissue-repair", "evidence": "Evidence: cosmetic/preclinical", "reg": "Topical: cosmetic use · Injectable: RUO"},
    "ruo": "<b>Two very different uses.</b> GHK-Cu is widely used <b>topically in cosmetics</b> (better-supported), and separately sold as an <b>injectable research chemical</b> (RUO, far less human data). This page is educational; it is not medical advice and not a use instruction.",
    "sections": [
      {"h": "What it is", "html": "<p>GHK is a naturally occurring <strong>tripeptide</strong> (glycine-histidine-lysine) that avidly <strong>binds copper (Cu²⁺)</strong>; the complex is written GHK-Cu. Levels of GHK in the body decline with age, which framed early interest in it as a repair signal.<sup><a href=\"#r1\">1</a></sup></p>"},
      {"h": "Proposed mechanism", "html": "<ul><li><strong>Copper delivery &amp; enzyme cofactor support</strong> — copper is required by enzymes involved in connective-tissue crosslinking.</li><li><strong>Collagen / GAG stimulation</strong> — reported to promote synthesis of collagen, elastin, and glycosaminoglycans in skin models.<sup><a href=\"#r1\">1</a></sup></li><li><strong>Gene-expression modulation</strong> — in cell studies GHK-Cu is reported to shift the expression of a large number of genes toward a repair/anti-inflammatory profile.<sup><a href=\"#r2\">2</a></sup></li></ul><div class=\"callout\"><b>Read carefully:</b> most robust data are <em>topical / in-vitro</em>. Systemic (injected) human evidence is limited — the leap from \"resets genes in a dish\" to \"injected anti-aging\" is exactly what Chapter 3 cautions against.</div>"},
      {"h": "Evidence & status", "html": "<ul><li><strong>Topical:</strong> reasonable cosmetic-science support for skin appearance.</li><li><strong>Injectable/systemic:</strong> preclinical, minimal human; <strong>no Phase III</strong>.</li><li>Not an FDA-approved drug; the injectable form is sold RUO.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "GHK / copper-peptide biology in skin & tissue repair (literature).", "cite": "PubMed: GHK-Cu", "url": "https://pubmed.ncbi.nlm.nih.gov/?term=GHK-Cu+copper+peptide"},
      {"n": "2", "label": "Peptide Therapeutics 2.0 — review of peptide mechanisms.", "cite": "PMC7287585", "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7287585/"},
    ],
  },
  {
    "slug": "mots-c", "name": "MOTS-c",
    "title": "MOTS-c (Mitochondrial-Derived Peptide): Mechanism & Evidence",
    "sub": "A 16-amino-acid peptide encoded in mitochondrial 12S rRNA · metabolic research",
    "desc": "A cited profile of MOTS-c: what a mitochondrial-derived peptide is, its AMPK/metabolic mechanism, the exercise-mimetic preclinical data, and its RUO status.",
    "badges": {"class": "Metabolic · mitochondrial", "evidence": "Evidence: preclinical (early human interest)", "reg": "RUO · not FDA-approved"},
    "ruo": "<b>Research Use Only.</b> MOTS-c is not an approved medicine and not for human use. Educational only — no dosing or medical advice.",
    "sections": [
      {"h": "What it is", "html": "<p>MOTS-c is a <strong>mitochondrial-derived peptide (MDP)</strong> — a short peptide encoded within the mitochondrial <strong>12S rRNA</strong> gene rather than the nuclear genome. Its discovery helped establish that mitochondria themselves encode signaling peptides.<sup><a href=\"#r1\">1</a></sup></p>"},
      {"h": "Proposed mechanism", "html": "<ul><li><strong>Metabolic regulation via AMPK.</strong> MOTS-c is reported to activate the AMPK energy-sensing pathway, improving insulin sensitivity and glucose handling in animal models.<sup><a href=\"#r1\">1</a></sup></li><li><strong>Stress-responsive gene regulation.</strong> Under metabolic stress it is reported to translocate to the nucleus and influence adaptive gene expression — an \"exercise-mimetic\" theme in the literature.</li></ul>"},
      {"h": "Evidence & status", "html": "<ul><li><strong>Preclinical:</strong> notable mouse metabolic/exercise data.</li><li><strong>Human:</strong> early interest, limited controlled data; <strong>no Phase III</strong>.</li><li>RUO; not FDA-approved.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "MOTS-c / mitochondrial-derived peptides in metabolism (literature).", "cite": "PubMed: MOTS-c", "url": "https://pubmed.ncbi.nlm.nih.gov/?term=MOTS-c"},
    ],
  },
  {
    "slug": "tesamorelin", "name": "Tesamorelin",
    "title": "Tesamorelin (GHRH analog): Mechanism, Approval & Evidence",
    "sub": "A stabilized GHRH analog · FDA-approved (Egrifta) for HIV-associated lipodystrophy",
    "desc": "A cited profile of tesamorelin: the GHRH-analog mechanism, its FDA-approved indication, how it differs from RUO secretagogues, and evidence.",
    "badges": {"class": "GH secretagogue (GHRH analog)", "evidence": "Evidence: Phase 3 (approved indication)", "eviCls": "b-evi-trial", "reg": "FDA-approved (specific indication)", "regCls": "b-reg-ok"},
    "ruo": "<b>Approved — for a specific indication.</b> Tesamorelin is FDA-approved (Egrifta) to reduce excess visceral fat in HIV-associated lipodystrophy — a narrow, prescription indication. Use for other goals is off-label / not established. Educational only, not medical advice.",
    "sections": [
      {"h": "What it is", "html": "<p>Tesamorelin is a synthetic, stabilized analog of <strong>growth-hormone-releasing hormone (GHRH)</strong>. Like <a href=\"cjc-1295-ipamorelin.html\">CJC-1295</a> it works on the GHRH pathway — but unlike those RUO peptides, tesamorelin completed the trials to earn an FDA approval.</p>"},
      {"h": "Mechanism", "html": "<p>It binds the <strong>GHRH receptor</strong> on the pituitary, stimulating physiological growth-hormone release and raising IGF-1. In its approved indication this reduces visceral adipose tissue.<sup><a href=\"#r1\">1</a></sup></p>"},
      {"h": "Evidence & status", "html": "<ul><li><strong>Approved:</strong> FDA-approved (Egrifta) for HIV-associated lipodystrophy, backed by Phase 3 trials.<sup><a href=\"#r2\">2</a></sup></li><li><strong>Other uses:</strong> not established; a good example of \"approved for X does not mean proven for Y.\"</li><li><strong>WADA:</strong> GH secretagogues are prohibited (S2) for tested athletes.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "Growth-hormone secretagogues — review.", "cite": "rco2.9 (Wiley)", "url": "https://onlinelibrary.wiley.com/doi/full/10.1002/rco2.9"},
      {"n": "2", "label": "Tesamorelin clinical literature.", "cite": "PubMed: tesamorelin", "url": "https://pubmed.ncbi.nlm.nih.gov/?term=tesamorelin"},
    ],
    "discExtra": "Tesamorelin is a prescription drug; obtain and use medicines only under a licensed professional.",
  },
  {
    "slug": "pt-141", "name": "PT-141",
    "title": "PT-141 / Bremelanotide (Melanocortin agonist): Mechanism & Evidence",
    "sub": "A melanocortin-receptor agonist · FDA-approved as Vyleesi (bremelanotide)",
    "desc": "A cited profile of PT-141 (bremelanotide): the central melanocortin (MC4R) mechanism, its FDA approval for HSDD, and how it differs from vascular sexual-health drugs.",
    "badges": {"class": "Melanocortin · sexual-health research", "evidence": "Evidence: Phase 3 (approved indication)", "eviCls": "b-evi-trial", "reg": "FDA-approved (specific indication)", "regCls": "b-reg-ok"},
    "ruo": "<b>Approved — for a specific indication.</b> Bremelanotide (Vyleesi) is FDA-approved for hypoactive sexual desire disorder (HSDD) in premenopausal women — prescription-only. \"PT-141\" sold as a research chemical is not the approved product. Educational only, not medical advice.",
    "sections": [
      {"h": "What it is", "html": "<p>PT-141 (bremelanotide) is a <strong>melanocortin-receptor agonist</strong> derived from the melanotan lineage. Unlike PDE5 inhibitors (which act on blood flow), it works <strong>centrally in the brain</strong>.</p>"},
      {"h": "Mechanism", "html": "<p>It activates <strong>melanocortin-4 receptor (MC4R)</strong> — a GPCR involved in central pathways of sexual desire and arousal.<sup><a href=\"#r2\">2</a></sup> Acting on desire circuitry rather than vasculature is what distinguishes the melanocortin approach.<sup><a href=\"#r1\">1</a></sup></p>"},
      {"h": "Evidence & status", "html": "<ul><li><strong>Approved:</strong> FDA-approved (Vyleesi) for HSDD in premenopausal women, on Phase 3 evidence.<sup><a href=\"#r1\">1</a></sup></li><li>Common side effect: transient nausea; flushing.</li><li>The melanotan family also affects pigmentation — a reminder these receptors are pleiotropic.</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "Bremelanotide / PT-141 clinical literature.", "cite": "PubMed: bremelanotide", "url": "https://pubmed.ncbi.nlm.nih.gov/?term=bremelanotide"},
      {"n": "2", "label": "Kobilka, GPCR structure (MC4R is a GPCR) — Nobel review.", "cite": "Angew. Chem.", "url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/anie.201302116"},
    ],
    "discExtra": "Bremelanotide is a prescription drug; obtain and use medicines only under a licensed professional.",
  },
  {
    "slug": "nad", "name": "NAD+",
    "title": "NAD+ : What It Actually Is, Mechanism & Evidence",
    "sub": "Nicotinamide adenine dinucleotide — a coenzyme (not a peptide) · longevity research",
    "desc": "A cited profile of NAD+: why it's a coenzyme rather than a peptide, its role in energy metabolism and sirtuins, and the honest state of the human longevity evidence.",
    "badges": {"class": "Longevity · cellular coenzyme", "evidence": "Evidence: preclinical / emerging human", "reg": "Not a peptide · not an approved drug"},
    "ruo": "<b>First, a correction the space gets wrong:</b> NAD+ is a <b>coenzyme (a dinucleotide), not a peptide</b>. It's grouped with peptides in wellness marketing, but it's a different class of molecule. This is educational only, not medical advice.",
    "sections": [
      {"h": "What it is", "html": "<p><strong>NAD+ (nicotinamide adenine dinucleotide)</strong> is a coenzyme present in every cell, central to <strong>energy metabolism</strong> — it carries electrons in the reactions that make ATP. It is also a substrate consumed by repair and signaling enzymes.</p>"},
      {"h": "Mechanism / why the interest", "html": "<ul><li><strong>Redox metabolism:</strong> NAD+/NADH cycling powers the electron-transport chain.</li><li><strong>Sirtuins &amp; PARPs:</strong> NAD+ is the fuel for sirtuins (longevity-associated enzymes) and DNA-repair PARPs; cellular NAD+ declines with age, which drives the \"restore NAD+\" hypothesis.<sup><a href=\"#r1\">1</a></sup></li></ul><div class=\"callout\"><b>Honest framing:</b> the biology is real and important; whether <em>supplementing</em> NAD+ (or precursors like NR/NMN) meaningfully slows human aging is <b>not established</b> — human trials are early and mixed.</div>"},
      {"h": "Evidence & status", "html": "<ul><li><strong>Preclinical:</strong> extensive; NAD+ decline and repletion are heavily studied in animals.</li><li><strong>Human:</strong> early trials of precursors (NR, NMN); clinical benefit on aging outcomes remains unproven.</li><li>Not an FDA-approved drug; precursors are sold as supplements (regulatory status has shifted).</li></ul>"},
    ],
    "refs": [
      {"n": "1", "label": "NAD+ metabolism, sirtuins and aging (literature).", "cite": "PubMed: NAD+ aging", "url": "https://pubmed.ncbi.nlm.nih.gov/?term=NAD%2B+aging+sirtuin"},
    ],
  },
]

# ── Merge in the extended library (compounds_more.py) ───────────────────────
import sys as _sys
_sys.path.insert(0, HERE)
try:
    from compounds_more import MORE as _MORE
except Exception as _e:  # pragma: no cover
    print("compounds_more import failed:", _e)
    _MORE = []

_SEED = {}
try:
    for _s in json.load(open(os.path.join(HERE, "reference_seed.json"))):
        _SEED[_s["n"].replace("&amp;", "&")] = _s.get("recon", "")
except Exception:
    pass


def expand(m):
    recon = _SEED.get(m["name"], "") or _SEED.get(m["name"].replace("&", "&amp;"), "")
    sections = [
        {"h": "What it is", "html": f"<p>{m['what']}</p>"},
        {"h": "Proposed mechanism", "html": m["mech"]},
        {"h": "State of the evidence", "html": m["evidence"]},
        {"h": "Regulatory & status", "html": m["reg_html"]},
    ]
    if recon:
        sections.append({"h": "Reconstitution (reference only)",
                         "html": (f'<p>Lab-handling reference only — not a preparation or dosing '
                                  f'instruction: {recon}. See the <a href="../index.html">reconstitution '
                                  f'calculator</a> for the arithmetic. This page does not provide dosing guidance.</p>')})
    d = {"slug": m["slug"], "name": m["name"],
         "title": f"{m['name']}: Mechanism & Evidence",
         "sub": m["sub"],
         "desc": m.get("desc") or f"A cited, research-framed profile of {m['name']}: what it is, proposed mechanism, evidence tier, and regulatory status.",
         "badges": {"class": m["cls"], "evidence": m["evi"], "eviCls": m.get("evicls", "b-evi"),
                    "reg": m["reg"], "regCls": m.get("regcls", "b-reg")},
         "ruo": m["ruo"], "sections": sections, "refs": m["refs"]}
    if m.get("disc"):
        d["discExtra"] = m["disc"]
    return d


COMPOUNDS += [expand(m) for m in _MORE]

if __name__ == "__main__":
    main()
