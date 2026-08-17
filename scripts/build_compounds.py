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


def main():
    os.makedirs(os.path.join(ROOT, "compounds"), exist_ok=True)
    for c in COMPOUNDS:
        out = os.path.join(ROOT, "compounds", f"{c['slug']}.html")
        open(out, "w").write(render(c))
        print("wrote", out)
    added = sync_sitemap([c["slug"] for c in COMPOUNDS])
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
]

if __name__ == "__main__":
    main()
