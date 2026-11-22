// AutoPostInsta worker: password login, AI copy and images (Cloudflare Workers AI), image hosting (KV),
// and posting through Buffer. Static files in ./public are served by the assets binding.

const SESSION_DAYS = 30;
const IMAGE_TTL_SECONDS = 120 * 24 * 3600; // keep images long enough for far-off scheduled posts
const MAX_UPLOAD_BYTES = 8 * 1024 * 1024; // Instagram's limit
const BUFFER_API = "https://api.buffer.com";

const IMAGE_STYLE =
  "Black-and-white palette of white, silver, grey and near-black only, premium editorial advertising photography, " +
  "close-up at eye level, objects large and sharp in the lower two thirds, shallow depth of field. " +
  "Any phone or tablet screen shows a simple clean app interface of cards, icons and check marks with no readable words. " +
  "The headline is the only readable text in the image: no other words, no logos, no brand marks, no people, no hands.";

const COPY_SYSTEM_PROMPT = `You write Instagram ads for AWSAVYA, a two-person software studio in India run by Vivek and Yash.
Facts you may use (nothing else):
- AWSAVYA designs and builds mobile apps (Android, offline-first), websites and web platforms, custom software shaped around how an operation runs, and applied AI and automation whose output can be checked.
- Clients talk directly to Vivek and Yash, who scope, design and build the work. No account managers.
- Work is scoped in milestones; each milestone ends with working software the client can open and try. At the end, a documented handover of the code.
- Four products the founders built themselves (never call them client work): TripSplit (offline-first Android app for group expenses), Build2Buzz (AI pipeline that drafts release posts from evidence for a person to review), Har Apparels (Android shop-floor app for a denim plant), QuicklyCart (local commerce web platform).
- To start: send a brief at awsavya.in.
Hard rules:
- Never invent clients, numbers, percentages, prices, timelines, results, awards, reviews or testimonials.
- No hype words: revolutionary, game-changing, world-class, cutting-edge, best, #1, guaranteed.
- Plain, specific, calm voice. Short sentences. Talk to the reader ("you", "your team").
Return JSON only with these keys:
The one-second rule: someone scrolling must understand the ad from the headline and the image alone, in one second, with no decoding. Clear beats clever.
- "headline": 2 to 6 words, ends with a full stop, drawn inside the image. It states the positive outcome for the owner plainly (for example "Orders in. Phone quiet.", "Every fee, tracked.", "Less paperwork. More baking."). It must never read like a rule or refusal aimed at customers ("No phone orders." sounds like the shop refuses orders), and it must match the image.
- "sub": ONE full sentence of 60 to 110 characters, shown under the image. It adds a concrete benefit the headline doesn't say.
- "hook": the caption's first line, under 100 characters. A question or a pointed statement about the reader's real problem that makes them stop scrolling. Never start with "Custom software" or the product name.
- "paragraphs": 2 or 3 short paragraphs (1 to 3 sentences each) that follow the hook: the problem, then how AWSAVYA solves it using only the facts above.
- "hashtags": exactly 5 hashtags without the # sign, all specific to this post's topic (not generic tech tags that don't fit).
- "scene": two or three sentences describing a photograph that tells the ad's story on its own, so someone who can't read the caption still gets 80% of the message. It must include:
  1. WHERE: two or three props that make the business type obvious at a glance (bakery: trays of croissants, a flour-dusted counter, a bread display; clinic: a stethoscope, an appointment book, a treatment chair; coaching centre: a whiteboard, stacked notebooks; hardware shop: shelves of tools and bolts).
  2. THE PROBLEM, visible: the messy "before" (a desk phone off its hook, a spike of handwritten order slips, sticky notes everywhere, a thick ledger, a crumpled printout).
  3. THE FIX, visible: one phone or tablet whose screen shows a simple, clean app layout made of rows of cards, icons and check marks with NO readable words or numbers, clearly organised compared with the mess.
  Frame it as a close-up at eye level with the objects large, filling the lower two thirds of the frame; keep the upper third calm and uncluttered for the headline.
  No abstract metaphors (no keys, locks, puzzles, mazes, gears, light bulbs, paths). Objects only: no people, faces or hands (the image model draws them badly), no logos. Monochrome palette only: white, silver, chrome, steel, glass, black and grey, and food or goods rendered in black-and-white tones; never coloured objects.
- "alt": alt text for the finished image, under 150 characters, describing the scene and quoting the headline.
- "why": one sentence explaining how the image shows the business, the problem and the fix to someone who sees it for one second. If any of the three is missing, change the scene before answering.`;

const LIGHTING = {
  paper: "Bright, airy, high-key lighting: mostly white and pale silver grey tones",
  ink: "Dark, low-key lighting: mostly deep black tones with silver highlights",
};

// ---------------- helpers ----------------

const json = (data, status = 200, headers = {}) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json", ...headers } });

const fail = (message, status = 400) => json({ error: message }, status);

async function hmac(secret, text) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(text));
  return btoa(String.fromCharCode(...new Uint8Array(sig))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function safeEqual(a, b) {
  const x = new TextEncoder().encode(a);
  const y = new TextEncoder().encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

async function makeSession(env) {
  const expires = Date.now() + SESSION_DAYS * 86400 * 1000;
  return `${expires}.${await hmac(env.SESSION_SECRET, String(expires))}`;
}

async function isLoggedIn(request, env) {
  const cookie = request.headers.get("cookie") || "";
  const match = cookie.match(/(?:^|;\s*)aps=([^;]+)/);
  if (!match) return false;
  const [expires, sig] = match[1].split(".");
  if (!expires || !sig || Number(expires) < Date.now()) return false;
  return safeEqual(sig, await hmac(env.SESSION_SECRET, expires));
}

function sessionCookie(value, maxAge, secure) {
  return `aps=${value}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${maxAge}${secure ? "; Secure" : ""}`;
}

// Accounts in order: CF_ACCOUNT_ID / CF_API_TOKEN first, then _2, _3 … up to _20. Gaps are skipped.
function cfAccounts(env) {
  const accounts = [];
  for (let n = 1; n <= 20; n++) {
    const suffix = n === 1 ? "" : `_${n}`;
    const id = env[`CF_ACCOUNT_ID${suffix}`], token = env[`CF_API_TOKEN${suffix}`];
    if (id && token) accounts.push({ label: `account ${n}`, id, token });
  }
  return accounts;
}

// Calls a Workers AI model, trying each account in turn when one has used its daily free allowance.
async function runModel(env, model, makeRequest) {
  const accounts = cfAccounts(env);
  if (!accounts.length) throw new Error("No Cloudflare account is configured on the server.");
  let lastError = "";
  for (const acc of accounts) {
    for (let attempt = 0; attempt < 2; attempt++) {
      const req = makeRequest(); // fresh body each try: a request body can only be sent once
      const resp = await fetch(`https://api.cloudflare.com/client/v4/accounts/${acc.id}/ai/run/${model}`, {
        method: "POST",
        body: req.body,
        headers: { Authorization: `Bearer ${acc.token}`, ...req.headers },
      });
      if (resp.ok) return { resp, account: acc.label };
      const detail = (await resp.text()).slice(0, 300);
      lastError = `${acc.label}: HTTP ${resp.status} ${detail}`;
      if (resp.status === 429) break; // allowance used up: next account
      if (resp.status < 500) throw new Error(lastError); // bad request: retrying won't help
    }
  }
  if (lastError.includes("429")) {
    throw new Error("Every Cloudflare account has used its free AI allowance for now (it frees up within 24 hours). You can still write the words yourself and upload your own photo.");
  }
  throw new Error(`Cloudflare AI failed. ${lastError}`);
}

// Text (ideas, ad copy) goes through free text providers first, so Cloudflare's daily allowance is left for images.
// Order: Groq → Gemini → OpenRouter → Cloudflare Workers AI. A provider is used only when its key is set.
function textProviders(env) {
  const list = [];
  if (env.GROQ_API_KEY) list.push({
    name: "Groq", url: "https://api.groq.com/openai/v1/chat/completions", key: env.GROQ_API_KEY,
    model: env.GROQ_MODEL || "openai/gpt-oss-120b", extra: { reasoning_effort: "low" },
  });
  if (env.GEMINI_API_KEY) list.push({
    name: "Gemini", url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", key: env.GEMINI_API_KEY,
    model: env.GEMINI_MODEL || "gemini-flash-latest", extra: {},
  });
  if (env.OPENROUTER_API_KEY) list.push({
    name: "OpenRouter", url: "https://openrouter.ai/api/v1/chat/completions", key: env.OPENROUTER_API_KEY,
    model: env.OPENROUTER_MODEL || "google/gemma-4-31b-it:free", extra: {},
  });
  return list;
}

async function completeText(env, system, user, { maxTokens = 2000, temperature = 0.7 } = {}) {
  const errors = [];
  for (const p of textProviders(env)) {
    try {
      const resp = await fetch(p.url, {
        method: "POST",
        headers: { Authorization: `Bearer ${p.key}`, "content-type": "application/json" },
        body: JSON.stringify({
          model: p.model, temperature, max_tokens: maxTokens, ...p.extra,
          messages: [{ role: "system", content: system }, { role: "user", content: user }],
        }),
      });
      if (!resp.ok) { errors.push(`${p.name}: HTTP ${resp.status}`); continue; }
      const text = (await resp.json()).choices?.[0]?.message?.content;
      if (text?.trim()) return { text, provider: p.name };
      errors.push(`${p.name}: empty answer`);
    } catch (err) {
      errors.push(`${p.name}: ${err.message}`);
    }
  }
  // Last resort: Cloudflare Workers AI (shares the image allowance).
  const body = env.TEXT_MODEL.includes("gpt-oss")
    ? { instructions: system, input: user, reasoning: { effort: "low" } }
    : { messages: [{ role: "system", content: system }, { role: "user", content: user }], max_tokens: 4000, temperature };
  try {
    const { resp, account } = await runModel(env, env.TEXT_MODEL, () => ({ headers: { "content-type": "application/json" }, body: JSON.stringify(body) }));
    const r = (await resp.json()).result || {};
    const text = r.response ?? r.choices?.[0]?.message?.content
      ?? r.output?.flatMap((o) => o.content || []).find((c) => c.type === "output_text")?.text;
    if (typeof text === "string" && text.trim()) return { text, provider: `Cloudflare ${account}` };
    if (text && typeof text === "object") return { text: JSON.stringify(text), provider: `Cloudflare ${account}` };
    errors.push("Cloudflare: empty answer");
  } catch (err) {
    errors.push(`Cloudflare: ${err.message}`);
  }
  throw new Error(`No AI could write text right now. ${errors.join(" · ")}`);
}

// ---------------- Buffer ----------------

async function buffer(env, query, variables = {}) {
  const resp = await fetch(BUFFER_API, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.BUFFER_API_KEY}`, "content-type": "application/json", "user-agent": "AutoPostInsta/1.0" },
    body: JSON.stringify({ query, variables }),
  });
  if (resp.status === 401) throw new Error("Buffer rejected the API key. Regenerate it in Buffer and update the server secret.");
  if (resp.status === 429) throw new Error(`Buffer rate limit reached. Try again in ${resp.headers.get("retry-after") || "a few"} seconds.`);
  const data = await resp.json();
  if (data.errors?.length) throw new Error(`Buffer: ${data.errors[0].extensions?.code || ""} ${data.errors[0].message}`.trim());
  return data.data;
}

async function bufferOrgId(env) {
  const cached = await env.STORE.get("buffer:org");
  if (cached) return cached;
  const data = await buffer(env, "query { account { organizations { id } } }");
  const orgId = data.account.organizations[0]?.id;
  if (orgId) await env.STORE.put("buffer:org", orgId);
  return orgId;
}

// ---------------- routes ----------------

async function login(request, env) {
  if (!env.APP_PASSWORD || !env.SESSION_SECRET) return fail("The server has no password set yet.", 500);
  const { password = "" } = await request.json().catch(() => ({}));
  if (!safeEqual(String(password), env.APP_PASSWORD)) {
    await new Promise((r) => setTimeout(r, 600)); // slow down guessing
    return fail("Wrong password.", 401);
  }
  const secure = new URL(request.url).protocol === "https:";
  return json({ ok: true }, 200, { "set-cookie": sessionCookie(await makeSession(env), SESSION_DAYS * 86400, secure) });
}

async function writeCopy(request, env) {
  const { idea = "", ground = "paper" } = await request.json().catch(() => ({}));
  if (String(idea).trim().length < 3) return fail("Write a few words about the post first.");
  const schema = {
    type: "object",
    properties: {
      headline: { type: "string" }, sub: { type: "string" }, hook: { type: "string" },
      paragraphs: { type: "array", items: { type: "string" } },
      hashtags: { type: "array", items: { type: "string" } },
      scene: { type: "string" }, alt: { type: "string" }, why: { type: "string" },
    },
    required: ["headline", "sub", "hook", "paragraphs", "hashtags", "scene", "alt", "why"],
  };
  const mood = ground === "ink" ? "dark, low-key" : "bright, high-key";
  const userText = `Ad idea: ${String(idea).slice(0, 800)}\nThe photo will be ${mood}; describe a scene that suits that lighting.\n` +
    `Return only the JSON object with the keys: ${schema.required.join(", ")}.`;
  const { text, provider } = await completeText(env, COPY_SYSTEM_PROMPT, userText, { maxTokens: 3000 });
  let copy = null;
  const match = text.match(/\{[\s\S]*\}/);
  try { copy = match ? JSON.parse(match[0]) : null; } catch { copy = null; }
  if (!copy?.headline) return fail(`The AI (${provider}) didn't return usable copy. Try again.`, 502);
  const account = provider;

  // Build the caption ourselves so the layout is always right: hook, paragraphs, CTA, then 5 clean hashtags.
  const tags = [...new Set((copy.hashtags || [])
    .map((t) => String(t).replace(/^#/, "").replace(/[^\p{L}\p{N}_]/gu, "").toLowerCase())
    .filter(Boolean))].slice(0, 5);
  const paragraphs = (Array.isArray(copy.paragraphs) ? copy.paragraphs : [String(copy.paragraphs || "")])
    .map((p) => String(p).trim())
    .filter((p) => p && !/awsavya\.in/i.test(p)); // the CTA is added once below
  const caption = [String(copy.hook || "").trim(), ...paragraphs, "Start a brief at awsavya.in.", tags.map((t) => `#${t}`).join(" ")]
    .filter(Boolean)
    .join("\n\n");
  return json({ headline: copy.headline, sub: copy.sub, caption, scene: copy.scene, alt: copy.alt, why: copy.why || "", account });
}

const IDEA_PROMPT = `You suggest Instagram ad ideas for AWSAVYA, a two-person software studio in India (Vivek and Yash).
They build: Android apps that work offline, websites and web platforms, custom software shaped around how a business runs,
and applied AI and automation whose output can be checked. Clients talk directly to the two founders; work comes in
milestones with working software each time, and ends with a documented handover.
You'll get three numbered pairs of a business type and a thing AWSAVYA could build for it. Write one ad idea per pair.
Each idea is ONE short sentence, at most 22 words, in plain everyday English, the way you'd explain it to the owner
over chai: what the thing does in their day, and what they get from it. A shop owner must understand it on first read.
No jargon or buzzwords (no "real time", "sync", "seamless", "streamline", "leverage", "digital transformation", "boutique").
Never invent clients, numbers, prices or results.
Good examples (different businesses, different things):
- "A booking page where salon customers pick their own slot, so the phone stops ringing all day."
- "Fee reminders go out to parents by themselves, so nobody at the coaching centre has to chase payments."
- "Every morning a new Instagram post about today's bakes goes up on its own, while you're busy baking."
Return only JSON: {"ideas": ["idea for pair 1", "idea for pair 2", "idea for pair 3"]}`;

// Picked in code so every request explores different ground instead of the model's favourite ("a boutique café").
const IDEA_BUSINESSES = [
  "neighbourhood bakery", "dental clinic", "coaching centre", "hardware shop", "garment manufacturing unit",
  "pharmacy", "cloud kitchen", "salon", "gym", "real estate agent", "school", "printing press", "furniture showroom",
  "diagnostic lab", "travel agency", "wholesale distributor", "car service centre", "event caterer", "pet clinic",
  "dairy supplier", "mobile repair shop", "architect's office", "packers and movers", "tuition teacher", "florist",
  "electrical contractor", "organic farm", "jewellery shop", "physiotherapy clinic", "courier franchise",
];
// Concrete things AWSAVYA builds (all within its four services). Each idea gets a different one.
// `label` is shown on the idea button; `brief` is what the AI is told.
const IDEA_SERVICES = [
  { label: "Instagram auto-posting", brief: "an automation that makes and posts an Instagram ad every day by itself (like the one AWSAVYA built for itself)" },
  { label: "Auto reminders", brief: "automatic payment or appointment reminders sent to customers without anyone typing them" },
  { label: "Auto invoices", brief: "invoices and receipts that are made and sent automatically after each sale or job" },
  { label: "Booking website", brief: "a website where customers book a slot or appointment themselves" },
  { label: "Business website", brief: "a simple website that says plainly what the business does and brings in enquiries" },
  { label: "Online catalogue", brief: "a website catalogue where customers browse products and place orders" },
  { label: "Order system", brief: "custom software where every order is recorded in one place and moves step by step until delivered" },
  { label: "Stock & billing", brief: "custom software for stock and billing that replaces the register or spreadsheet" },
  { label: "Staff app", brief: "an Android app for staff on the move or on the floor that keeps working without internet" },
  { label: "Customer portal", brief: "a login page where customers check their order, report or status themselves" },
  { label: "AI assistant", brief: "an AI assistant that answers customers' common questions using the business's own information, checked by a person" },
  { label: "Daily summary", brief: "an automatic summary of the day's sales, orders or bookings sent to the owner every evening" },
];
const pick = (list, n) => [...list].sort(() => Math.random() - 0.5).slice(0, n);

async function suggestIdea(env) {
  const list = await env.STORE.list({ prefix: "post:", limit: 10 });
  const recent = (await Promise.all(list.keys.map((k) => env.STORE.get(k.name, "json"))))
    .filter(Boolean).map((r) => r.headline).filter(Boolean);
  const businesses = pick(IDEA_BUSINESSES, 3);
  const services = pick(IDEA_SERVICES, 3);
  const pairs = businesses.map((b, i) => ({ business: b, service: services[i] }));
  const input = pairs.map((p, i) => `${i + 1}. Business: ${p.business}. Build: ${p.service.brief}.`).join("\n") +
    (recent.length ? `\nAvoid repeating these recent posts: ${recent.join(" | ")}` : "");
  const { text, provider } = await completeText(env, IDEA_PROMPT, input, { maxTokens: 1200, temperature: 0.9 });
  let ideas = [];
  try { ideas = JSON.parse(text.match(/\{[\s\S]*\}/)?.[0] || "{}").ideas || []; } catch { /* fall back below */ }
  if (!ideas.length) ideas = text.split("\n").map((l) => l.replace(/^[\s\-\d.)"“]+|["”]$/g, "").trim()).filter((l) => l.length > 20);
  const options = ideas.slice(0, 3).map((idea, i) => ({
    idea: String(idea).trim(),
    label: pairs[i] ? `${pairs[i].business.replace(/^\w/, (c) => c.toUpperCase())} · ${pairs[i].service.label}` : "",
  })).filter((o) => o.idea);
  if (!options.length) return fail("The AI didn't come up with ideas. Try again.", 502);
  return json({ options, ideas: options.map((o) => o.idea), provider });
}

async function makeImage(request, env) {
  const { scene = "", headline = "", ground = "paper" } = await request.json().catch(() => ({}));
  if (!scene.trim() || !headline.trim()) return fail("Scene and headline are both needed for the image.");
  const g = ground === "ink" ? "ink" : "paper";
  const type = g === "ink"
    ? "a large clean white sans-serif headline"
    : "a large elegant black serif headline";
  // One-piece composition: the headline sits in the photo's own empty space, not on a separate banner.
  const prompt =
    `${scene.trim().replace(/\.?$/, ".")} A single full-bleed photograph that fills the entire frame edge to edge, ` +
    `with a calm, uncluttered upper third. In that space, ${type} is set directly onto the photo ` +
    `as part of the image (no box, no banner, no border, no separate panel), reading "${headline.trim()}". ` +
    `${LIGHTING[g]}. ${IMAGE_STYLE}`;
  let cloudflareError;
  try {
    const { resp, account } = await runModel(env, env.IMAGE_MODEL, () => {
      const form = new FormData();
      form.append("prompt", prompt);
      form.append("width", "1024");
      form.append("height", "1024");
      return { body: form, headers: {} };
    });
    // Pass Cloudflare's JSON ({"result":{"image":"<base64>"}}) straight through: parsing ~1.5 MB here
    // would eat the free plan's CPU budget, so the browser decodes it instead.
    return new Response(resp.body, { headers: { "content-type": "application/json", "x-ai-account": `Cloudflare ${account}` } });
  } catch (err) {
    cloudflareError = err.message;
  }
  // Backup: Z-Image Turbo on Hugging Face (free daily GPU quota tied to HF_TOKEN).
  if (env.HF_TOKEN) {
    for (const space of HF_SPACES) {
      try {
        const image = await hfGenerate(env, space, prompt);
        return new Response(image.body, { headers: { "content-type": image.type, "x-ai-account": `Hugging Face (${space.label})` } });
      } catch (err) {
        cloudflareError += ` · ${space.label}: ${err.message}`;
      }
    }
  }
  return fail(`No image service is available right now. ${cloudflareError}`, 503);
}

// Public Z-Image Turbo demos on Hugging Face, called through Gradio's HTTP API. The official one first.
const HF_SPACES = [
  { label: "Z-Image", host: "tongyi-mai-z-image-turbo.hf.space", api: "generate",
    data: (prompt) => [prompt, "1024x1024 ( 1:1 )", 42, 8, 3.0, true, []],
    pick: (out) => out?.[0]?.[0]?.image?.url },
  { label: "Z-Image mirror", host: "mrfakename-z-image-turbo.hf.space", api: "generate_image",
    data: (prompt) => [prompt, 1024, 1024, 9, 42, true],
    pick: (out) => out?.[0]?.url },
];

async function hfGenerate(env, space, prompt) {
  const auth = { Authorization: `Bearer ${env.HF_TOKEN}`, "user-agent": "AutoPostInsta/1.0" };
  const base = `https://${space.host}/gradio_api/call/${space.api}`;
  const start = await fetch(base, {
    method: "POST",
    headers: { ...auth, "content-type": "application/json" },
    body: JSON.stringify({ data: space.data(prompt) }),
  });
  if (!start.ok) throw new Error(`HTTP ${start.status}`);
  const { event_id: eventId } = await start.json();
  const stream = await (await fetch(`${base}/${eventId}`, { headers: auth })).text();
  const blocks = stream.split("\n\n");
  const error = blocks.find((b) => b.includes("event: error"));
  if (error) {
    const msg = error.split("data:")[1]?.trim() || "error";
    throw new Error(/quota|exceeded/i.test(msg) ? "free daily GPU quota used up" : msg.slice(0, 120));
  }
  const done = blocks.find((b) => b.includes("event: complete"));
  if (!done) throw new Error("no result");
  const url = space.pick(JSON.parse(done.split("data:")[1].trim()));
  if (!url) throw new Error("no image in result");
  const img = await fetch(url, { headers: auth });
  if (!img.ok) throw new Error(`image download HTTP ${img.status}`);
  return { body: img.body, type: img.headers.get("content-type") || "image/png" };
}

async function uploadImage(request, env) {
  const type = request.headers.get("content-type") || "";
  if (!type.startsWith("image/jpeg")) return fail("Upload a JPEG.");
  const bytes = await request.arrayBuffer();
  if (bytes.byteLength > MAX_UPLOAD_BYTES) return fail("Image is over 8 MB.");
  if (bytes.byteLength < 1000) return fail("Image is empty.");
  const id = crypto.randomUUID().replace(/-/g, "");
  await env.STORE.put(`img:${id}`, bytes, { expirationTtl: IMAGE_TTL_SECONDS, metadata: { size: bytes.byteLength } });
  const url = `${new URL(request.url).origin}/img/${id}.jpg`;
  return json({ id, url });
}

async function serveImage(id, env) {
  if (!/^[a-f0-9]{32}$/.test(id)) return new Response("Not found", { status: 404 });
  const bytes = await env.STORE.get(`img:${id}`, "arrayBuffer");
  if (!bytes) return new Response("Not found", { status: 404 });
  return new Response(bytes, { headers: { "content-type": "image/jpeg", "cache-control": "public, max-age=31536000, immutable" } });
}

async function publish(request, env) {
  const body = await request.json().catch(() => ({}));
  const { imageUrl, caption, alt, mode, at, aiLabel = true, headline = "", ground = "paper" } = body;
  if (!imageUrl?.startsWith("https://")) return fail("The image needs a public https link. Publishing only works on the live site.");
  if (!caption?.trim()) return fail("The caption is empty.");
  const hashtags = (caption.match(/(?<!\w)#\w+/g) || []).length;
  if (hashtags > 5) return fail(`Buffer allows 5 hashtags on Instagram; this caption has ${hashtags}.`);
  if (caption.length > 2200) return fail("The caption is over 2,200 characters.");
  const modes = { now: "shareNow", at: "customScheduled", queue: "addToQueue", draft: "addToQueue" };
  if (!modes[mode]) return fail("Pick how to publish.");

  const image = { url: imageUrl };
  if (alt?.trim()) image.metadata = { altText: alt.trim().slice(0, 1000) };
  const input = {
    channelId: env.BUFFER_CHANNEL_ID,
    text: caption,
    schedulingType: "automatic",
    mode: modes[mode],
    assets: [{ image }],
    aiAssisted: true,
    metadata: { instagram: { type: "post", shouldShareToFeed: true, isAiGenerated: Boolean(aiLabel) } },
  };
  if (mode === "draft") input.saveToDraft = true;
  if (mode === "at") {
    const due = new Date(at);
    if (Number.isNaN(due.getTime())) return fail("Pick a date and time to schedule.");
    if (due.getTime() - Date.now() < 5 * 60 * 1000) return fail("Schedule at least 5 minutes ahead.");
    input.dueAt = due.toISOString();
  }

  const q = `mutation ($input: CreatePostInput!) {
    createPost(input: $input) {
      __typename
      ... on PostActionSuccess { post { id status dueAt externalLink } }
      ... on MutationError { message }
    }
  }`;
  const result = (await buffer(env, q, { input })).createPost;
  if (result.__typename !== "PostActionSuccess") return fail(`Buffer refused it: ${result.message || result.__typename}`, 502);

  const post = result.post;
  const key = `post:${String(9999999999999 - Date.now()).padStart(13, "0")}`;
  const record = {
    key, id: post.id, status: post.status, dueAt: post.dueAt, link: post.externalLink || null, mode,
    headline: String(headline).slice(0, 120), ground: ground === "ink" ? "ink" : "paper", imageUrl,
    createdAt: new Date().toISOString(),
  };
  await env.STORE.put(key, JSON.stringify(record));
  return json(record);
}

// Deletes a draft or scheduled post in Buffer (sent posts are already on Instagram and are left alone),
// then removes it and its image from the site.
async function deletePost(request, env) {
  const { id = "" } = await request.json().catch(() => ({}));
  if (!/^[a-f0-9]{24}$/.test(id)) return fail("Unknown post.");
  const list = await env.STORE.list({ prefix: "post:", limit: 100 });
  let record = null, key = null;
  for (const k of list.keys) {
    const r = await env.STORE.get(k.name, "json");
    if (r?.id === id) { record = r; key = k.name; break; }
  }
  if (!record) return fail("That post isn't in this site's history.", 404);
  if (record.status === "sent") return fail("This one is already on Instagram. Delete it in the Instagram app instead.");

  const q = `mutation ($input: DeletePostInput!) {
    deletePost(input: $input) { __typename ... on VoidMutationError { message } }
  }`;
  const result = (await buffer(env, q, { input: { id } })).deletePost;
  if (result.__typename !== "DeletePostSuccess") {
    // Already gone from Buffer (deleted there, or it failed): still tidy up the site's copy.
    if (!/not.?found/i.test(result.message || "")) return fail(`Buffer refused: ${result.message || result.__typename}`, 502);
  }
  await env.STORE.delete(key);
  const imageId = (record.imageUrl || "").match(/\/img\/([a-f0-9]{32})\.jpg$/)?.[1];
  if (imageId) await env.STORE.delete(`img:${imageId}`);
  return json({ ok: true, id });
}

async function history(env) {
  const list = await env.STORE.list({ prefix: "post:", limit: 30 });
  const records = await Promise.all(list.keys.map((k) => env.STORE.get(k.name, "json")));
  const items = records.filter(Boolean);
  // Refresh status and Instagram links from Buffer for anything not final yet.
  const pending = items.filter((r) => r.status !== "sent" && r.status !== "error");
  if (pending.length && env.BUFFER_API_KEY) {
    try {
      const orgId = await bufferOrgId(env);
      const q = `query ($input: PostsInput!) { posts(first: 50, input: $input) { edges { node { id status dueAt externalLink } } } }`;
      const data = await buffer(env, q, { input: { organizationId: orgId, filter: { channelIds: [env.BUFFER_CHANNEL_ID] } } });
      const byId = Object.fromEntries((data.posts.edges || []).map((e) => [e.node.id, e.node]));
      for (const r of items) {
        const live = byId[r.id];
        if (live) Object.assign(r, { status: live.status, dueAt: live.dueAt, link: live.externalLink || r.link });
      }
    } catch { /* show stored data if Buffer is unreachable */ }
  }
  const queued = items.filter((r) => r.status === "scheduled").length;
  return json({ items, queued });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path.startsWith("/img/") && request.method === "GET") return serveImage(path.slice(5).replace(/\.jpg$/, ""), env);
    if (!path.startsWith("/api/")) return env.ASSETS.fetch(request);

    try {
      if (path === "/api/login" && request.method === "POST") return await login(request, env);
      if (path === "/api/logout" && request.method === "POST") {
        return json({ ok: true }, 200, { "set-cookie": sessionCookie("", 0, url.protocol === "https:") });
      }
      if (!(await isLoggedIn(request, env))) return fail("Log in first.", 401);
      if (request.method === "POST" && request.headers.get("x-requested-with") !== "autopostinsta") {
        return fail("Bad request origin.", 403); // blocks cross-site form posts
      }
      if (path === "/api/me") return json({ ok: true, bufferReady: Boolean(env.BUFFER_API_KEY && env.BUFFER_CHANNEL_ID) });
      if (path === "/api/copy" && request.method === "POST") return await writeCopy(request, env);
      if (path === "/api/idea" && request.method === "POST") return await suggestIdea(env);
      if (path === "/api/image" && request.method === "POST") return await makeImage(request, env);
      if (path === "/api/upload" && request.method === "POST") return await uploadImage(request, env);
      if (path === "/api/publish" && request.method === "POST") return await publish(request, env);
      if (path === "/api/history" && request.method === "GET") return await history(env);
      if (path === "/api/delete" && request.method === "POST") return await deletePost(request, env);
      return fail("Not found.", 404);
    } catch (err) {
      return fail(err.message || "Something went wrong.", 502);
    }
  },
};
