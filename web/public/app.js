// AutoPostInsta front end: write copy, make or upload an image, compose the poster on a canvas,
// run checks, then upload the JPEG and publish through the worker.

const $ = (id) => document.getElementById(id);
const SIZE = 1080;
const BAND = 270;
const CTA = "START A BRIEF · AWSAVYA.IN";
const GROUNDS = {
  paper: { bg: "#F5F4F8", text: "#15131C", muted: "#57536A", rule: "#C9C6D2", logo: "/brand/awsavya-logo.png" },
  ink: { bg: "#15131C", text: "#F5F4F8", muted: "#A19DAD", rule: "#36323F", logo: "/brand/awsavya-logo-light.png" },
};
const CLAIM_WORDS = /\b(clients?|customers? love|testimonials?|reviews?|guarantee[ds]?|award|best|#1|number one|world-class|revolutionary|game-changing|cutting-edge|years of experience)\b/i;

const state = { scene: null, sceneIsAI: false, logos: {}, ready: false };

// ---------------- API ----------------

async function api(path, { method = "GET", body, headers = {}, raw = false } = {}) {
  const resp = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: { "x-requested-with": "autopostinsta", ...(body && !raw ? { "content-type": "application/json" } : {}), ...headers },
    body: body ? (raw ? body : JSON.stringify(body)) : undefined,
  });
  if (resp.status === 401 && path !== "/api/login") {
    showLogin();
    throw new Error("Please log in again.");
  }
  return resp;
}

async function apiJson(path, opts) {
  const resp = await api(path, opts);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || data.errors?.[0]?.message || `Request failed (${resp.status})`);
  return data;
}

function setStatus(el, text, kind = "") {
  el.textContent = text;
  el.className = `status ${kind}`;
}

async function busy(button, statusEl, label, fn) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  try {
    return await fn();
  } catch (err) {
    setStatus(statusEl, err.message, "bad");
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

// ---------------- login ----------------

function showLogin() {
  $("app-view").hidden = true;
  $("login-view").hidden = false;
  $("password").focus();
}

async function showApp() {
  $("login-view").hidden = true;
  $("app-view").hidden = false;
  if (!state.ready) await setupApp();
}

$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("login-error").textContent = "";
  const resp = await api("/api/login", { method: "POST", body: { password: $("password").value } });
  if (resp.ok) {
    $("password").value = "";
    await showApp();
  } else {
    const data = await resp.json().catch(() => ({}));
    $("login-error").textContent = data.error || "Couldn't log in.";
  }
});

$("logout").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  showLogin();
});

// ---------------- poster ----------------

const loadImage = (src) => new Promise((resolve, reject) => {
  const img = new Image();
  img.onload = () => resolve(img);
  img.onerror = () => reject(new Error(`Couldn't load ${src}`));
  img.src = src;
});

function ground() {
  return document.querySelector("input[name=ground]:checked").value;
}

function wrapLines(ctx, text, maxWidth) {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function draw() {
  const g = GROUNDS[ground()];
  const canvas = $("poster");
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = g.bg;
  ctx.fillRect(0, 0, SIZE, SIZE + BAND);

  if (state.scene) {
    const s = state.scene;
    const scale = Math.max(SIZE / s.width, SIZE / s.height); // cover-crop to a square
    const w = s.width * scale, h = s.height * scale;
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, SIZE, SIZE); // keep tall or wide photos out of the copy band
    ctx.clip();
    ctx.drawImage(s, (SIZE - w) / 2, (SIZE - h) / 2, w, h);
    ctx.restore();
  } else {
    ctx.fillStyle = g.rule;
    ctx.fillRect(0, 0, SIZE, SIZE);
    ctx.fillStyle = g.muted;
    ctx.font = '500 26px "Martian Mono"';
    ctx.textAlign = "center";
    ctx.fillText("NO IMAGE YET", SIZE / 2, SIZE / 2);
    ctx.textAlign = "left";
  }

  ctx.fillStyle = g.rule;
  ctx.fillRect(0, SIZE - 1, SIZE, 2);

  const pad = 64;
  ctx.fillStyle = g.text;
  ctx.font = '420 31px "Archivo"';
  ctx.textBaseline = "top";
  const lines = wrapLines(ctx, $("sub").value, SIZE - pad * 2);
  lines.slice(0, 2).forEach((line, i) => ctx.fillText(line, pad, SIZE + 38 + i * 42));
  state.subLines = lines.length;

  const logo = state.logos[ground()];
  if (logo) {
    const lh = 44, lw = (logo.width / logo.height) * lh;
    const baseY = SIZE + BAND - 44 - lh;
    ctx.drawImage(logo, pad, baseY, lw, lh);
    ctx.fillStyle = g.muted;
    ctx.font = '500 20px "Martian Mono"';
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    ctx.fillText(CTA, SIZE - pad, baseY + lh / 2);
    ctx.textAlign = "left";
  }
  ctx.textBaseline = "alphabetic";
  runChecks();
}

// ---------------- checks ----------------

function runChecks() {
  const caption = $("caption").value;
  const hashtags = (caption.match(/(?<!\w)#\w+/g) || []).length;
  const words = `${$("headline").value} ${$("sub").value} ${caption.replace(/#\w+/g, "")}`;
  const checks = [
    [state.scene ? "ok" : "bad", state.scene ? "Image ready" : "No image yet"],
    [$("headline").value.trim() ? "ok" : "bad", $("headline").value.trim() ? "Headline set" : "Headline is empty"],
    [state.subLines <= 2 ? "ok" : "bad", state.subLines <= 2 ? "Copy line fits" : "Copy line is longer than 2 lines: shorten it"],
    [caption.trim() ? (caption.length <= 2200 ? "ok" : "bad") : "bad",
      caption.trim() ? `Caption ${caption.length}/2200 characters` : "Caption is empty"],
    [hashtags <= 5 ? "ok" : "bad", `${hashtags}/5 hashtags (Buffer's Instagram limit)`],
    [/\d/.test(words) || /[%₹$]/.test(words) ? "warn" : "ok",
      /\d/.test(words) || /[%₹$]/.test(words) ? "Contains numbers or prices: make sure every one is true" : "No numbers or prices"],
    [CLAIM_WORDS.test(words) ? "warn" : "ok",
      CLAIM_WORDS.test(words) ? `Check the claim "${words.match(CLAIM_WORDS)[0]}": no invented clients, reviews or superlatives` : "No risky claims found"],
  ];
  $("checks").innerHTML = checks.map(([kind, text]) => `<li class="${kind}">${text.replace(/</g, "&lt;")}</li>`).join("");
  $("caption-count").textContent = `${caption.length}/2200 · ${hashtags}/5 #`;
  state.blocked = checks.some(([kind]) => kind === "bad");
  return state.blocked;
}

// ---------------- copy and image ----------------

$("write-copy").addEventListener("click", () =>
  busy($("write-copy"), $("copy-status"), "Writing…", async () => {
    setStatus($("copy-status"), "");
    const copy = await apiJson("/api/copy", { method: "POST", body: { idea: $("idea").value, ground: ground() } });
    $("headline").value = copy.headline || "";
    $("sub").value = copy.sub || "";
    $("caption").value = copy.caption || "";
    $("scene").value = copy.scene || "";
    $("alt").value = copy.alt || "";
    draw();
    setStatus($("copy-status"), `Done (${copy.account}). Read it through and edit anything that isn't right.`, "ok");
    $("scene-why").textContent = copy.why ? `Why this picture: ${copy.why}` : "";
  }));

$("suggest-idea").addEventListener("click", () =>
  busy($("suggest-idea"), $("copy-status"), "Thinking…", async () => {
    setStatus($("copy-status"), "");
    const { options = [] } = await apiJson("/api/idea", { method: "POST", body: {} });
    const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
    $("idea-options").innerHTML = options.map((o) =>
      `<button type="button" class="idea-chip" data-idea="${esc(o.idea)}">` +
      (o.label ? `<span class="idea-label mono">${esc(o.label)}</span>` : "") +
      `<span>${esc(o.idea)}</span></button>`).join("");
    setStatus($("copy-status"), "Pick one (it goes into the box), edit it if you like, then click Write it with AI.", "ok");
  }));

$("idea-options").addEventListener("click", (e) => {
  const chip = e.target.closest(".idea-chip");
  if (!chip) return;
  $("idea").value = chip.dataset.idea;
  document.querySelectorAll(".idea-chip").forEach((c) => c.classList.toggle("picked", c === chip));
});

$("make-image").addEventListener("click", () =>
  busy($("make-image"), $("image-status"), "Making image… (about 20 s)", async () => {
    setStatus($("image-status"), "");
    const resp = await api("/api/image", {
      method: "POST",
      body: { scene: $("scene").value, headline: $("headline").value, ground: ground() },
    });
    const type = resp.headers.get("content-type") || "";
    if (resp.ok && type.startsWith("image/")) {
      state.scene = await createImageBitmap(await resp.blob()); // backup services send the image itself
    } else {
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || !data.result?.image) throw new Error(data.error || "The image didn't come back. Try again.");
      state.scene = await loadImage(`data:image/jpeg;base64,${data.result.image}`);
    }
    state.sceneIsAI = true;
    $("ai-label").checked = true;
    draw();
    setStatus($("image-status"), `Image made (${resp.headers.get("x-ai-account") || "AI"}). Check the headline spelling in the preview.`, "ok");
  }));

$("own-photo").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    state.scene = await createImageBitmap(file);
    state.sceneIsAI = false;
    $("ai-label").checked = false; // a real photo isn't AI-generated
    draw();
    setStatus($("image-status"), "Your photo is in. It's cropped to a square; the headline isn't drawn on real photos.", "ok");
  } catch {
    setStatus($("image-status"), "Couldn't read that file. Try a JPEG or PNG.", "bad");
  }
  e.target.value = "";
});

// ---------------- publish ----------------

function mode() {
  return document.querySelector("input[name=mode]:checked").value;
}

function defaultWhen() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(10, 0, 0, 0);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T10:00`;
}

document.querySelectorAll("input[name=mode]").forEach((r) => r.addEventListener("change", () => {
  $("schedule-row").hidden = mode() !== "at";
  $("publish").textContent = { at: "Schedule", now: "Post now", queue: "Add to queue", draft: "Save as Buffer draft" }[mode()];
}));

$("publish").addEventListener("click", () =>
  busy($("publish"), $("publish-status"), "Publishing…", async () => {
    setStatus($("publish-status"), "");
    if (runChecks()) throw new Error("Fix the items marked ✕ first.");
    if (location.protocol !== "https:") throw new Error("Publishing only works on the live site (Buffer can't fetch images from this computer).");
    const m = mode();
    let at;
    if (m === "at") {
      if (!$("when").value) throw new Error("Pick a date and time.");
      at = new Date($("when").value).toISOString();
    }
    if (m === "now" && !confirm("Post this to Instagram right now?")) return;

    setStatus($("publish-status"), "Uploading image…");
    const blob = await new Promise((resolve) => $("poster").toBlob(resolve, "image/jpeg", 0.92));
    const upload = await apiJson("/api/upload", { method: "POST", body: blob, raw: true, headers: { "content-type": "image/jpeg" } });

    setStatus($("publish-status"), "Sending to Buffer…");
    const post = await apiJson("/api/publish", {
      method: "POST",
      body: {
        imageUrl: upload.url, caption: $("caption").value, alt: $("alt").value, mode: m, at,
        aiLabel: $("ai-label").checked, headline: $("headline").value, ground: ground(),
      },
    });
    const when = post.dueAt ? new Date(post.dueAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "";
    const text = {
      now: "Sent. It should be on Instagram within a minute.",
      at: `Scheduled for ${when}.`,
      queue: `Added to Buffer's queue${when ? ` for ${when}` : ""}.`,
      draft: "Saved as a draft in Buffer. Nothing was published.",
    }[m];
    setStatus($("publish-status"), text, "ok");
    loadHistory();
  }));

// ---------------- history ----------------

async function loadHistory() {
  try {
    const { items, queued } = await apiJson("/api/history");
    $("queue-pill").textContent = `Queue ${queued}/10`;
    const last = items[0];
    $("grid-hint").textContent = last
      ? `Last post was ${last.ground === "ink" ? "dark" : "light"}. ${last.ground === "ink" ? "Light" : "Dark"} keeps the grid alternating.`
      : "";
    if (!items.length) return;
    $("history").innerHTML = items.map((r) => {
      const when = r.dueAt ? new Date(r.dueAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "";
      const status = { sent: "Posted", scheduled: `Scheduled · ${when}`, draft: "Buffer draft", error: "Failed in Buffer", sending: "Sending" }[r.status] || r.status;
      const link = r.link ? ` · <a href="${r.link}" target="_blank" rel="noopener">View on Instagram</a>` : "";
      const title = (r.headline || "Untitled").replace(/</g, "&lt;");
      const canDelete = r.status === "draft" || r.status === "scheduled";
      const del = canDelete
        ? `<button class="btn btn-ghost btn-small" data-delete="${r.id}" aria-label="Delete ${title}">Delete</button>`
        : "";
      return `<li><img src="${r.imageUrl}" alt="" loading="lazy"><div><div>${title}</div><div class="meta">${status}${link}</div></div>${del}</li>`;
    }).join("");
  } catch { /* history is optional */ }
}

$("history").addEventListener("click", async (e) => {
  const button = e.target.closest("button[data-delete]");
  if (!button) return;
  const row = button.closest("li");
  const title = row.querySelector("div > div")?.textContent || "this post";
  if (!confirm(`Delete "${title}" from Buffer? It won't be posted.`)) return;
  button.disabled = true;
  button.textContent = "Deleting…";
  try {
    await apiJson("/api/delete", { method: "POST", body: { id: button.dataset.delete } });
    row.remove();
    loadHistory();
  } catch (err) {
    button.disabled = false;
    button.textContent = "Delete";
    alert(err.message);
  }
});

// ---------------- setup ----------------

async function setupApp() {
  state.ready = true;
  await Promise.all([
    document.fonts.load('420 31px "Archivo"'),
    document.fonts.load('500 20px "Martian Mono"'),
    loadImage(GROUNDS.paper.logo).then((img) => (state.logos.paper = img)),
    loadImage(GROUNDS.ink.logo).then((img) => (state.logos.ink = img)),
  ]).catch(() => {});
  $("when").value = defaultWhen();
  ["headline", "sub", "caption"].forEach((id) => $(id).addEventListener("input", draw));
  document.querySelectorAll("input[name=ground]").forEach((r) => r.addEventListener("change", draw));
  draw();
  loadHistory();
}

(async () => {
  try {
    const resp = await fetch("/api/me", { credentials: "same-origin" });
    if (resp.ok) await showApp();
    else showLogin();
  } catch {
    showLogin();
  }
})();
