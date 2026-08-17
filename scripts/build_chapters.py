#!/usr/bin/env python3
"""
Free Peptide University — Advanced Track chapter generator.
Cited, academic-grade teaching chapters -> /chapters/advanced-<slug>.html + sitemap.
Run: python3 scripts/build_chapters.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = "https://freepeptideuniversity.com"

STYLE = """:root{--bg:#060912;--surface:#101829;--cream:#0A0F1C;--text:#EAF2FF;--soft:#AEBCD8;--muted:#6E7C99;--aqua:#7DEBDC;--aqua2:#34D6C2;--border:rgba(94,230,208,.20)}
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;line-height:1.75;letter-spacing:.2px;-webkit-font-smoothing:antialiased;background-image:linear-gradient(rgba(94,230,208,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(94,230,208,.03) 1px,transparent 1px);background-size:46px 46px}
    .wrap{max-width:840px;margin:0 auto;padding:56px 28px 90px}
    h1,h2,h3{font-family:'Sora',sans-serif;line-height:1.2;color:var(--text)}
    h1{font-size:clamp(2rem,5vw,3rem);margin:8px 0 6px}
    h2{font-size:1.5rem;margin:44px 0 12px}
    h3{font-size:1.12rem;margin:24px 0 6px}
    p,li{color:var(--soft);font-size:1.03rem}
    a{color:var(--aqua)}
    strong{color:var(--text)}
    sup a{font-size:.7em;text-decoration:none;padding:0 1px}
    .eyebrow{font-size:.72rem;letter-spacing:.3em;text-transform:uppercase;color:var(--aqua);font-weight:600}
    .sub{color:var(--muted);font-size:1.05rem;margin:0 0 8px}
    .meta{color:var(--muted);font-size:.85rem;margin:0 0 22px}
    .topnav{display:flex;justify-content:space-between;align-items:center;margin-bottom:40px;font-size:.92rem}
    .topnav .brand{font-family:'Sora';font-weight:700;color:var(--text);text-decoration:none}
    .topnav .brand span{color:var(--aqua)}
    .callout{background:linear-gradient(135deg,rgba(143,247,232,.14),rgba(94,230,208,.06));border-left:3px solid var(--aqua2);border-radius:10px;padding:16px 20px;margin:24px 0;font-size:.98rem}
    .callout b{color:var(--aqua)}
    .diagram{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:24px;margin:28px 0}
    .diagram figcaption{text-align:center;color:var(--muted);font-size:.82rem;margin-top:12px}
    .spec{width:100%;border-collapse:collapse;margin:18px 0;font-size:.94rem}
    .spec th,.spec td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--border);vertical-align:top}
    .spec th{font-family:'Sora';font-weight:600;color:var(--aqua);background:var(--cream)}
    .tscroll{overflow-x:auto}
    ul,ol{padding-left:22px}
    li{margin:8px 0}
    .refs{margin-top:14px;font-size:.9rem}
    .refs li{margin:9px 0;color:var(--muted)}
    .refs a{color:var(--aqua)}
    .disc{background:var(--cream);border-left:3px solid var(--aqua2);padding:14px 18px;border-radius:8px;font-size:.82rem;color:var(--muted);margin:34px 0 0}
    .sponsor{font-size:.85rem;color:var(--soft);margin:26px 0 0;padding:12px 18px;background:linear-gradient(135deg,rgba(143,247,232,.06),rgba(94,230,208,.03));border:1px solid var(--border);border-radius:10px}
    .sponsor a{color:var(--aqua);font-weight:600}
    .cta{display:inline-block;background:linear-gradient(135deg,#9BF7EA,#34D6C2 42%,#3AA8FF);color:#04140F;font-weight:600;padding:14px 30px;border-radius:999px;text-decoration:none;margin-top:14px}
    .nextprev{display:flex;justify-content:space-between;gap:12px;margin-top:40px;font-size:.9rem}
    footer{border-top:1px solid var(--border);margin-top:52px;padding-top:26px;font-size:.8rem;color:var(--muted)}"""


def render(ch, idx, total):
    slug = f"advanced-{ch['slug']}"
    url = f"{BASE}/chapters/{slug}.html"
    art = {"@context": "https://schema.org", "@type": "Article", "headline": ch["title"],
           "description": ch["desc"], "author": {"@type": "Organization", "name": "Free Peptide University"},
           "publisher": {"@type": "Organization", "name": "Free Peptide University"},
           "mainEntityOfPage": url, "image": f"{BASE}/og-image.jpg",
           "datePublished": "2026-08-17", "dateModified": "2026-08-17"}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Free Peptide University", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Advanced Track"},
        {"@type": "ListItem", "position": 3, "name": ch["name"], "item": url}]}
    secs = "".join(f'<h2>{s["h"]}</h2>\n{s["html"]}' for s in ch["sections"])
    refs = "".join(f'<li>{r["label"]} <a href="{r["url"]}" target="_blank" rel="noopener">{r["cite"]}</a></li>'
                   for r in ch["refs"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{ch['title']} | Free Peptide University</title>
  <meta name="description" content="{ch['desc']}" />
  <link rel="canonical" href="{url}" />
  <meta name="robots" content="index, follow" />
  <meta name="theme-color" content="#060912" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="Free Peptide University" />
  <meta property="og:title" content="{ch['title']}" />
  <meta property="og:description" content="{ch['desc']}" />
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
    <div class="eyebrow">Advanced Track · {idx} of {total}</div>
    <h1>{ch['name']}</h1>
    <p class="sub">{ch['sub']}</p>
    {secs}
    <h2>Further reading — primary sources</h2>
    <ol class="refs">{refs}</ol>
    <p class="sponsor">This free curriculum is made possible by our sponsor, <a href="https://pureluxbio.com/?utm_source=freepeptideuniversity&amp;utm_medium=sponsor&amp;utm_campaign=chapter-{ch['slug']}" target="_blank" rel="noopener sponsored">PureLux Bio</a> — U.S.-made research-grade peptides.</p>
    <p><a class="cta" href="../compounds/index.html">Apply it → browse the 75-compound library</a></p>
    <div class="disc">For educational and research purposes only. This content is not medical advice. Compounds referenced are research use only unless noted as approved drugs, and nothing here is an instruction to use, prepare, or administer anything. Free Peptide University does not sell compounds.</div>
    <footer>Free Peptide University is an independent educational resource, made free to the public through the sponsorship of Adonis TRT and <a href="https://pureluxbio.com/?utm_source=freepeptideuniversity&amp;utm_medium=sponsor&amp;utm_campaign=chapter-footer" target="_blank" rel="noopener sponsored">PureLux Bio</a>. · <a href="../privacy.html">Privacy</a> · <a href="../terms.html">Terms</a></footer>
  </div>
</body>
</html>
"""


SVG_SPPS = ('<figure class="diagram"><svg viewBox="0 0 560 150" width="100%" role="img" aria-label="Solid-phase peptide synthesis cycle">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9BF7EA"/><stop offset="1" stop-color="#34D6C2"/></linearGradient></defs>'
            '<circle cx="70" cy="75" r="26" fill="#0B1322" stroke="#34D6C2" stroke-width="2"/><text x="70" y="79" text-anchor="middle" font-size="11" fill="#AEBCD8" font-family="Inter">resin</text>'
            '<path d="M104 75 H175" stroke="#34D6C2" stroke-width="2" marker-end="url(#a)"/>'
            '<circle cx="205" cy="75" r="18" fill="url(#g)"/><text x="205" y="112" text-anchor="middle" font-size="10" fill="#8FA0BD" font-family="Inter">couple aa</text>'
            '<path d="M228 75 H300" stroke="#34D6C2" stroke-width="2"/>'
            '<circle cx="330" cy="75" r="18" fill="url(#g)"/><circle cx="368" cy="75" r="18" fill="url(#g)"/><text x="349" y="112" text-anchor="middle" font-size="10" fill="#8FA0BD" font-family="Inter">deprotect · repeat</text>'
            '<path d="M392 75 H460" stroke="#34D6C2" stroke-width="2" stroke-dasharray="5 6"/>'
            '<circle cx="490" cy="75" r="18" fill="url(#g)"/><circle cx="510" cy="60" r="14" fill="url(#g)" opacity=".7"/><circle cx="510" cy="90" r="14" fill="url(#g)" opacity=".7"/><text x="500" y="120" text-anchor="middle" font-size="10" fill="#8FA0BD" font-family="Inter">cleave → peptide</text>'
            '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="#34D6C2"/></marker></defs>'
            '</svg><figcaption>Solid-phase peptide synthesis: build the chain one amino acid at a time on an anchored resin — couple, deprotect, repeat — then cleave the finished peptide off.</figcaption></figure>')

SVG_HALF = ('<figure class="diagram"><svg viewBox="0 0 560 170" width="100%" role="img" aria-label="Half-life extension by albumin binding">'
            '<text x="20" y="30" font-size="12" fill="#8FA0BD" font-family="Inter">native peptide (t½ ≈ 2 min)</text>'
            '<circle cx="60" cy="70" r="16" fill="#34D6C2"/><path d="M84 70 H180" stroke="#6E7C99" stroke-width="2" stroke-dasharray="3 5"/><text x="200" y="74" font-size="11" fill="#D08770" font-family="Inter">cleared fast (DPP-4)</text>'
            '<text x="20" y="120" font-size="12" fill="#8FA0BD" font-family="Inter">+ fatty-acid chain → binds albumin (t½ days)</text>'
            '<circle cx="60" cy="150" r="16" fill="#34D6C2"/><path d="M76 150 q18 -14 34 0" stroke="#E7C56B" stroke-width="3" fill="none"/><circle cx="140" cy="150" r="26" fill="none" stroke="#7DC4FF" stroke-width="2"/><text x="140" y="154" text-anchor="middle" font-size="10" fill="#7DC4FF" font-family="Inter">albumin</text>'
            '<path d="M172 150 H300" stroke="#5FE0B0" stroke-width="2"/><text x="320" y="154" font-size="11" fill="#5FE0B0" font-family="Inter">protected → weekly dosing</text>'
            '</svg><figcaption>A fatty-acid chain lets a peptide hitch onto albumin, hiding it from clearance — the trick that turns a 2-minute molecule into a once-weekly drug.</figcaption></figure>')


CHAPTERS = [
  {
    "slug": "how-peptides-are-made", "name": "How Peptides Are Made",
    "title": "How Peptides Are Made: Solid-Phase Synthesis, Explained",
    "sub": "Merrifield's resin, coupling and deprotection cycles — and why it shapes the whole market",
    "desc": "How peptides are actually manufactured: solid-phase peptide synthesis (SPPS), Boc vs Fmoc chemistry, purification, and why short natural sequences are hard to patent.",
    "sections": [
      {"h": "The problem SPPS solved", "html": "<p>A peptide is a precise, ordered chain of amino acids. Building one by classic solution chemistry — making and purifying after every single bond — is brutally slow. In 1963 <strong>Bruce Merrifield</strong> introduced <strong>solid-phase peptide synthesis (SPPS)</strong>, which won him the 1984 Nobel Prize in Chemistry and made modern peptide drugs possible.<sup><a href='#r1'>1</a></sup></p>"},
      {"h": "The cycle", "html": "<p>The trick is to anchor the growing chain to an insoluble <strong>resin bead</strong>, so excess reagents and byproducts can simply be washed away between steps. Each amino acid is added by repeating a cycle:</p>" + SVG_SPPS + "<ol><li><strong>Couple</strong> the next (protected) amino acid to the chain's free end.</li><li><strong>Deprotect</strong> — remove the temporary protecting group to expose the next reaction site.</li><li><strong>Wash &amp; repeat</strong> — until the full sequence is built.</li><li><strong>Cleave</strong> the finished peptide off the resin and remove side-chain protections.</li></ol>"},
      {"h": "Boc vs Fmoc", "html": "<p>Two protecting-group strategies dominate: <strong>Boc</strong> (older, uses strong acid) and <strong>Fmoc</strong> (milder base-removable chemistry, now the workhorse). The choice affects which sequences and modifications are practical.<sup><a href='#r1'>1</a></sup></p><div class='callout'><b>Why purity is everything:</b> because the chain is built stepwise, any missed coupling creates a slightly-wrong \"deletion\" peptide. That's exactly why the <a href='../chapters/myth-vs-research.html'>Certificate of Analysis</a> (HPLC purity + mass spec) matters so much for research material.</div>"},
      {"h": "Why this shapes the whole market", "html": "<p>A short, naturally-occurring sequence is <strong>hard to patent</strong>. No patent means no company will fund the expensive human trials — which is precisely why compounds like <a href='../compounds/bpc-157.html'>BPC-157</a> have striking animal data but almost no human trials, and end up sold \"research use only.\" The chemistry that makes peptides cheap to make is the same reason many never become approved drugs.</p>"},
    ],
    "refs": [
      {"label": "Mitchell — Bruce Merrifield and solid-phase peptide synthesis: a historical assessment.", "cite": "Peptide Science (Wiley)", "url": "https://onlinelibrary.wiley.com/doi/10.1002/bip.20925"},
      {"label": "Peptide Therapeutics 2.0 — review.", "cite": "PMC7287585", "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7287585/"},
    ],
  },
  {
    "slug": "how-peptides-signal", "name": "How Peptides Signal",
    "title": "How Peptides Signal: GPCRs & Receptor Pharmacology",
    "sub": "The receptor family Kobilka won a Nobel for — and why ~1 in 3 drugs targets it",
    "desc": "How peptides act on cells: G-protein-coupled receptors (GPCRs), agonists vs antagonists, and why the incretin, ghrelin and melanocortin receptors matter.",
    "sections": [
      {"h": "Peptides mostly talk to receptors", "html": "<p>Most signaling peptides work by fitting a specific <strong>receptor</strong> — like a key cut for one lock. The single most important receptor family for peptide drugs is the <strong>G-protein-coupled receptor (GPCR)</strong>. GPCRs are the target of an estimated one-third of all approved drugs.<sup><a href='#r1'>1</a></sup></p>"},
      {"h": "Why Kobilka's Nobel matters", "html": "<p>For decades GPCRs were understood only indirectly. <strong>Brian Kobilka</strong> (Stanford) captured the first high-resolution structures of a GPCR — including the receptor caught in the act of signaling — earning the 2012 Nobel Prize in Chemistry.<sup><a href='#r1'>1</a></sup> Seeing the actual shape is what lets chemists design molecules that fit.</p>"},
      {"h": "Agonist vs antagonist", "html": "<ul><li>An <strong>agonist</strong> binds and <em>activates</em> the receptor (semaglutide is a GLP-1 receptor agonist).</li><li>An <strong>antagonist</strong> binds and <em>blocks</em> it.</li></ul><p>\"Partial\" and \"biased\" agonists activate only some of a receptor's downstream signals — an active frontier in making drugs with fewer side effects.</p>"},
      {"h": "The receptors behind this whole field", "html": "<div class='tscroll'><table class='spec'><thead><tr><th>Receptor</th><th>Peptides that act on it</th></tr></thead><tbody>" +
        "<tr><td><strong>GLP-1R / GIP-R</strong> (class B GPCRs)</td><td>Incretins — <a href='../compounds/semaglutide.html'>semaglutide</a>, <a href='../compounds/tirzepatide.html'>tirzepatide</a>, <a href='../compounds/retatrutide.html'>retatrutide</a></td></tr>" +
        "<tr><td><strong>GHRH-R</strong></td><td>GHRH analogs — <a href='../compounds/sermorelin.html'>sermorelin</a>, <a href='../compounds/tesamorelin.html'>tesamorelin</a>, CJC-1295</td></tr>" +
        "<tr><td><strong>GHS-R</strong> (ghrelin receptor)</td><td>Secretagogues — <a href='../compounds/ipamorelin.html'>ipamorelin</a>, GHRP-2/6, <a href='../compounds/mk-677.html'>MK-677</a></td></tr>" +
        "<tr><td><strong>MC4R</strong> (melanocortin-4)</td><td><a href='../compounds/pt-141.html'>PT-141</a>, melanotan</td></tr>" +
        "</tbody></table></div><div class='callout'><b>The payoff:</b> once you know a peptide's receptor, you can predict a lot — what it does, what it interacts with, and why two peptides on the same receptor behave alike.</div>"},
    ],
    "refs": [
      {"label": "Kobilka — GPCR structure (2012 Nobel lecture / review).", "cite": "Angew. Chem. Int. Ed.", "url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/anie.201302116"},
      {"label": "GPCRs & drug discovery — Stanford news.", "cite": "news.stanford.edu", "url": "https://news.stanford.edu/stories/2012/10/nobel-prize-work-g-protein-coupled-receptors-paves-way-drug-discoveries"},
    ],
  },
  {
    "slug": "half-life-engineering", "name": "Half-Life Engineering",
    "title": "Half-Life Engineering: Why 2 Minutes Becomes a Week",
    "sub": "Lipidation, albumin-hitchhiking, PEGylation and DAC — the real magic behind weekly drugs",
    "desc": "How chemists extend a peptide's half-life: fatty-acid acylation, albumin binding, PEGylation and DAC linkers — the reason native GLP-1 lasts 2 minutes but semaglutide lasts a week.",
    "sections": [
      {"h": "The core problem", "html": "<p>Natural peptides are usually cleared from the body in <strong>minutes</strong>. Native GLP-1's half-life is roughly <strong>2 minutes</strong> — the enzyme DPP-4 chops it up almost immediately.<sup><a href='#r1'>1</a></sup> A drug you'd have to inject every few minutes is useless. The entire modern peptide-drug industry is, in a sense, the science of making short-lived peptides last.</p>"},
      {"h": "The toolkit", "html": SVG_HALF + "<ul><li><strong>Lipidation (acylation):</strong> attach a fatty-acid chain so the molecule reversibly <strong>binds albumin</strong> — the blood's most abundant protein — hiding from clearance. Semaglutide's C18 diacid chain pushes its half-life to ~165 hours (weekly).<sup><a href='#r1'>1</a></sup></li><li><strong>Amino-acid substitutions</strong> that make the peptide resist DPP-4.</li><li><strong>PEGylation:</strong> attach polyethylene-glycol to increase size and slow clearance.</li><li><strong>DAC (Drug-Affinity Complex):</strong> a group that binds albumin — the reason <a href='../compounds/cjc-1295-no-dac.html'>CJC-1295 with vs without DAC</a> behaves so differently (days vs minutes).</li></ul>"},
      {"h": "Why 'No-DAC' vs 'DAC' matters", "html": "<div class='callout'><b>Read the suffix:</b> the same core peptide with an albumin-binding group can go from short-acting to multi-day. \"No-DAC\" isn't a weaker version — it's a <em>different kinetics profile</em>. Recognizing modifications (DAC, acylation, PEG) tells you how often something is meant to act and how long it lingers.</div>"},
      {"h": "The lesson", "html": "<p>When you see a peptide marketed as \"long-acting\" or \"weekly,\" ask <em>what modification</em> makes it so. The mechanism (the receptor) tells you <em>what</em> it does; the half-life engineering tells you <em>how long and how often</em>.</p>"},
    ],
    "refs": [
      {"label": "Peptide half-life extension — lipidation, albumin binding, PEGylation (review).", "cite": "ACS Med. Chem. Lett.", "url": "https://pubs.acs.org/doi/10.1021/acsmedchemlett.8b00226"},
      {"label": "Peptide Therapeutics 2.0 — review.", "cite": "PMC7287585", "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7287585/"},
    ],
  },
  {
    "slug": "the-incretin-story", "name": "The Incretin Story",
    "title": "The Incretin Story: From Mojsov's GLP-1 to Triple Agonists",
    "sub": "How one peptide fragment became the biggest drug class of the decade",
    "desc": "The incretin discovery: Svetlana Mojsov's identification of bioactive GLP-1(7-37), the incretin effect, and the lineage from GLP-1 to dual and triple agonists.",
    "sections": [
      {"h": "A discovery that took decades to credit", "html": "<p>In the 1980s, <strong>Svetlana Mojsov</strong> — working in the peptide-synthesis tradition Merrifield founded — synthesized glucagon-family peptides and pinned down the truly bioactive incretin sequence, <strong>GLP-1(7-37)</strong>, the 31-amino-acid fragment that actually stimulates insulin.<sup><a href='#r1'>1</a></sup> That identification is the seed of the entire GLP-1 drug class; she received a 2024 Lasker~DeBakey Award.<sup><a href='#r2'>2</a></sup></p>"},
      {"h": "What the 'incretin effect' is", "html": "<p>Incretins are gut hormones released when you eat. They produce <strong>glucose-dependent</strong> insulin release (insulin only when sugar is high — hence low hypoglycemia risk), suppress glucagon, slow gastric emptying, and signal satiety to the brain. Turning that biology into a durable drug required <a href='../chapters/advanced-half-life-engineering.html'>half-life engineering</a>.</p>"},
      {"h": "The lineage", "html": "<div class='tscroll'><table class='spec'><thead><tr><th>Generation</th><th>Targets</th><th>Examples</th></tr></thead><tbody>" +
        "<tr><td>Single agonist</td><td>GLP-1</td><td><a href='../compounds/semaglutide.html'>Semaglutide</a></td></tr>" +
        "<tr><td>Dual (\"twincretin\")</td><td>GLP-1 + GIP</td><td><a href='../compounds/tirzepatide.html'>Tirzepatide</a></td></tr>" +
        "<tr><td>Triple</td><td>GLP-1 + GIP + glucagon</td><td><a href='../compounds/retatrutide.html'>Retatrutide</a> (investigational)</td></tr>" +
        "<tr><td>Oral small-molecule</td><td>GLP-1</td><td><a href='../compounds/orforglipron.html'>Orforglipron</a> (investigational)</td></tr>" +
        "</tbody></table></div><div class='callout'><b>The pattern:</b> each generation adds a complementary pathway. It's the clearest real-world example of rational, receptor-by-receptor drug design — and why the science in the <a href='../chapters/advanced-how-peptides-signal.html'>GPCR chapter</a> pays off.</div>"},
    ],
    "refs": [
      {"label": "The discovery of GLP-1 and its therapeutic legacy.", "cite": "PNAS", "url": "https://www.pnas.org/doi/10.1073/pnas.2415550121"},
      {"label": "GLP-1-based therapy for obesity — Lasker citation.", "cite": "laskerfoundation.org", "url": "https://laskerfoundation.org/winners/glp-1-based-therapy-for-obesity/"},
      {"label": "GLP-1 mechanisms & development — Harvard HMS CME.", "cite": "learn.hms.harvard.edu", "url": "https://learn.hms.harvard.edu/programs/glp-1-based-therapies-mechanisms-action-development-and-clinical-impact"},
    ],
  },
  {
    "slug": "evidence-and-regulation", "name": "Evidence & Regulation",
    "title": "Evidence & Regulation: How to Grade a Peptide Claim",
    "sub": "Preclinical vs pilot vs RCT vs approved — and FDA vs compounded vs research-use-only",
    "desc": "How to grade peptide evidence (preclinical to approved) and read the regulatory reality: FDA approval vs 503A/503B compounding vs research-use-only, plus WADA.",
    "sections": [
      {"h": "The evidence ladder", "html": "<p>Not all \"studies\" are equal. Grade any claim by where it sits on this ladder:</p><div class='tscroll'><table class='spec'><thead><tr><th>Tier</th><th>What it means</th></tr></thead><tbody>" +
        "<tr><td><strong>Preclinical</strong></td><td>Cells / animals only. Hypothesis-generating, not proof in people.</td></tr>" +
        "<tr><td><strong>Pilot / early human</strong></td><td>Small, often uncontrolled human studies. Signal, not proof.</td></tr>" +
        "<tr><td><strong>RCT (Phase 2/3)</strong></td><td>Randomized, controlled, powered trials. This is real evidence.</td></tr>" +
        "<tr><td><strong>Approved</strong></td><td>Regulator reviewed the full trial package.</td></tr>" +
        "</tbody></table></div><p>This is exactly why every profile in our <a href='../compounds/index.html'>compound library</a> shows an evidence tier — so <a href='../compounds/bpc-157.html'>BPC-157</a> (\"0 Phase III\") reads very differently from <a href='../compounds/semaglutide.html'>semaglutide</a> (\"large Phase 3 RCTs\").</p>"},
      {"h": "Three legal categories people confuse", "html": "<ul><li><strong>FDA-approved drug</strong> — reviewed and approved; prescription-only (e.g., semaglutide, tesamorelin, PT-141).</li><li><strong>Compounded drug (503A/503B)</strong> — made by a pharmacy for specific needs; NOT the same as FDA approval. The FDA is moving to <strong>exclude</strong> compounded semaglutide/tirzepatide as supply stabilizes.<sup><a href='#r1'>1</a></sup></li><li><strong>Research Use Only (RUO)</strong> — a research chemical, not a medicine, not for human use. Most \"peptides\" sold online are here.</li></ul>"},
      {"h": "WADA — for anyone tested", "html": "<p>Many performance-adjacent peptides (GH secretagogues, BPC-157, TB-500, IGF-1) are <strong>prohibited by WADA</strong> — often at all times. If you're a tested athlete, \"research use only\" doesn't make it allowed.</p>"},
      {"h": "How to use the News feed", "html": "<div class='callout'><b>Put it together:</b> our <a href='../index.html'>This Week in Peptides</a> feed tags every new paper and trial by tier and links the primary source. Read the tier first, the headline second — that habit alone puts you ahead of most of the internet.</div>"},
    ],
    "refs": [
      {"label": "FDA — proposal to exclude semaglutide/tirzepatide/liraglutide from the 503B bulks list.", "cite": "fda.gov", "url": "https://www.fda.gov/news-events/press-announcements/fda-proposes-exclude-semaglutide-tirzepatide-and-liraglutide-503b-bulks-list"},
      {"label": "FDA — policies for compounders as GLP-1 supply stabilizes.", "cite": "fda.gov", "url": "https://www.fda.gov/drugs/drug-alerts-and-statements/fda-clarifies-policies-compounders-national-glp-1-supply-begins-stabilize"},
    ],
  },
]


def main():
    os.makedirs(os.path.join(ROOT, "chapters"), exist_ok=True)
    slugs = []
    for i, ch in enumerate(CHAPTERS, 1):
        slug = f"advanced-{ch['slug']}"
        open(os.path.join(ROOT, "chapters", f"{slug}.html"), "w").write(render(ch, i, len(CHAPTERS)))
        slugs.append(slug)
        print("wrote chapters/" + slug + ".html")
    # sitemap sync
    sm_path = os.path.join(ROOT, "sitemap.xml")
    sm = open(sm_path).read()
    added = []
    for slug in slugs:
        loc = f"{BASE}/chapters/{slug}.html"
        if loc not in sm:
            sm = sm.replace("</urlset>", f'  <url><loc>{loc}</loc><lastmod>2026-08-17</lastmod></url>\n</urlset>')
            added.append(slug)
    if added:
        open(sm_path, "w").write(sm)
    print("sitemap added:", added or "(all present)")


if __name__ == "__main__":
    main()
