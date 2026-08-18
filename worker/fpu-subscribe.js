// Free Peptide University — email capture Worker
// On a NEW signup: (1) store in KV, (2) add to the Resend audience, (3) send a
// branded welcome email. Existing signups are ignored (idempotent, no re-welcome).
//
// Bindings/vars required:
//   FPU_EMAILS         KV namespace (fpu_emails)
//   RESEND_API_KEY     secret  (Resend account API key)
//   RESEND_AUDIENCE_ID var     (Free Peptide University audience id)
//
// POST {email, source} -> 200 ; GET ?export=<SECRET> -> newline list.

const ALLOW_ORIGINS = [
  "https://freepeptideuniversity.com",
  "https://www.freepeptideuniversity.com",
  "https://purelux-bio.github.io",
];
const EXPORT_SECRET = "plb-fpu-export-2026"; // read-only list export
const FROM = "Free Peptide University <news@send.freepeptideuniversity.com>";
const REPLY_TO = "donny@pureluxbio.com";
const WELCOME_URL = "https://freepeptideuniversity.com/newsletter/welcome.html";
const WELCOME_SUBJECT = "Welcome to Free Peptide University — start here";

function cors(origin) {
  const allow = ALLOW_ORIGINS.includes(origin) ? origin : ALLOW_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

// Add the contact to the Resend audience (auto-sync). Best-effort.
async function resendAddContact(env, email) {
  if (!env.RESEND_API_KEY || !env.RESEND_AUDIENCE_ID) return;
  try {
    await fetch(
      `https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.RESEND_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, unsubscribed: false }),
      }
    );
  } catch (_) {}
}

// Send the branded welcome email. Fetches the template from the live site so the
// design can be edited without redeploying the Worker. Best-effort.
async function resendWelcome(env, email) {
  if (!env.RESEND_API_KEY) return;
  try {
    let html = "";
    try {
      const r = await fetch(WELCOME_URL, { cf: { cacheTtl: 300 } });
      if (r.ok) html = await r.text();
    } catch (_) {}
    const unsub =
      "mailto:unsubscribe@send.freepeptideuniversity.com?subject=unsubscribe";
    if (html) {
      html = html.split("{{unsubscribe_url}}").join(unsub);
    } else {
      // Fallback if the template can't be fetched — plain but on-brand.
      html =
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1a2233">' +
        "<h1>Welcome to Free Peptide University.</h1>" +
        "<p>You're in. Real peptide science — cited, jargon-free, and free forever.</p>" +
        '<p><a href="https://freepeptideuniversity.com/?utm_source=welcome">Explore the library →</a></p>' +
        "<p>— The Free Peptide University Team</p></div>";
    }
    await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: FROM,
        to: [email],
        reply_to: REPLY_TO,
        subject: WELCOME_SUBJECT,
        html,
        headers: {
          "List-Unsubscribe":
            "<mailto:unsubscribe@send.freepeptideuniversity.com>",
        },
      }),
    });
  } catch (_) {}
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }

    // Owner export: GET /?export=SECRET -> "email\tISO\tsource" per line
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
      return new Response(`# ${out.length} subscribers\n` + out.join("\n") + "\n", {
        status: 200,
        headers: { "Content-Type": "text/plain" },
      });
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

      // First-seen only: keep original signup date; welcome + sync exactly once.
      const existing = await env.FPU_EMAILS.get(email);
      if (!existing) {
        const stamp = `${new Date().toISOString()}\t${source}`;
        await env.FPU_EMAILS.put(email, stamp);
        // Run Resend work after the response so signups stay instant.
        ctx.waitUntil(
          Promise.all([resendAddContact(env, email), resendWelcome(env, email)])
        );
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
