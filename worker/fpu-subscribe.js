// Free Peptide University — email capture Worker
// Stores signups in KV namespace bound as FPU_EMAILS.
// POST {email, source} -> 200; GET ?export=<SECRET> -> newline list.

const ALLOW_ORIGINS = [
  "https://freepeptideuniversity.com",
  "https://www.freepeptideuniversity.com",
  "https://purelux-bio.github.io",
];
const EXPORT_SECRET = "plb-fpu-export-2026"; // change anytime; used only to read the list

function cors(origin) {
  const allow = ALLOW_ORIGINS.includes(origin) ? origin : ALLOW_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }

    // Owner export: GET /?export=SECRET  -> plain-text list of "email\tISO\tsource"
    if (request.method === "GET" && url.searchParams.get("export") === EXPORT_SECRET) {
      const out = [];
      let cursor;
      do {
        const list = await env.FPU_EMAILS.list({ cursor });
        for (const k of list.keys) {
          const v = await env.FPU_EMAILS.get(k.name);
          out.push(`${k.name}\t${v || ""}`);
        }
        cursor = list.list_complete ? undefined : list.cursor;
      } while (cursor);
      return new Response(
        `# ${out.length} subscribers\n` + out.join("\n") + "\n",
        { status: 200, headers: { "Content-Type": "text/plain" } }
      );
    }

    if (request.method === "POST") {
      let email = "";
      let source = "site";
      try {
        const body = await request.json();
        email = String(body.email || "").trim().toLowerCase();
        source = String(body.source || "site").slice(0, 40);
      } catch (_) {}

      const valid = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email);
      if (!valid) {
        return new Response(JSON.stringify({ ok: false, error: "invalid email" }), {
          status: 400,
          headers: { ...cors(origin), "Content-Type": "application/json" },
        });
      }

      // Only write first-seen record; keep original signup date if already present.
      const existing = await env.FPU_EMAILS.get(email);
      if (!existing) {
        const stamp = `${new Date().toISOString()}\t${source}`;
        await env.FPU_EMAILS.put(email, stamp);
      }

      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { ...cors(origin), "Content-Type": "application/json" },
      });
    }

    return new Response("Free Peptide University subscribe endpoint", {
      status: 200,
      headers: { "Content-Type": "text/plain" },
    });
  },
};
