// once frontend: talks to the same server's API (/auth, /posts).
const $ = id => document.getElementById(id);
const TOKEN_KEY = "once_token";
const PAGE_SIZE = 12; // the wheel shows the latest cards; a ring gets crowded past this
const MIN_SLOTS = 8;

/* ---------- pixel icons ---------- */
const PAL = { o: "#3b2a33", y: "#ffd35c", w: "#fffdf6", b: "#6ea9ea", g: "#fdf3df", p: "#f59ab5" };
const PX = {
  heart: [".pp.pp.", "ppppppp", "ppppppp", ".ppppp.", "..ppp..", "...p..."],
  folder: [".oooo.....", "oyyyyoooo.", "oyyyyyyyyo", "oyyyyyyyyo", "oyyyyyyyyo", "oyyyyyyyyo", "oyyyyyyyyo", ".oooooooo."],
  note: ["oooooo..", "owwwwoo.", "owwwwwwo", "owoooowo", "owwwwwwo", "owoooowo", "owwwwwwo", "owooowwo", "owwwwwwo", "oooooooo"],
  computer: [".oooooooo.", ".obbbbbbo.", ".obbwbbbo.", ".obbbbbbo.", ".oooooooo.", "...oooo...", "oooooooooo", "oggggggggo", "oooooooooo"],
  smile: [".oooooo.", "oyyyyyyo", "oyoyyoyo", "oyyyyyyo", "oyoyyoyo", "oyyooyyo", "oyyyyyyo", ".oooooo."],
  sun: ["o..o..o", ".ooooo.", ".ooooo.", "ooooooo", ".ooooo.", ".ooooo.", "o..o..o"]
};
function paint(svg) {
  const rows = PX[svg.dataset.px]; if (!rows) return;
  svg.setAttribute("viewBox", `0 0 ${rows[0].length} ${rows.length}`); svg.setAttribute("shape-rendering", "crispEdges");
  svg.innerHTML = rows.map((r, y) => [...r].map((c, x) => c === "." ? "" : `<rect x="${x}" y="${y}" width="1" height="1" fill="${PAL[c]}"/>`).join("")).join("");
}
document.querySelectorAll("svg[data-px]").forEach(paint);
const BARS = ["var(--pink)", "var(--blue)", "var(--mint)", "var(--sun)"], ART = ["heart", "smile", "note", "sun", "folder"];

/* ---------- API ---------- */
let token = null, user = null;
try { token = localStorage.getItem(TOKEN_KEY); } catch { /* storage unavailable: stay signed out */ }
function saveToken(value) {
  token = value;
  try { if (value) localStorage.setItem(TOKEN_KEY, value); else localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
}
async function api(path, { method = "GET", json, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let body;
  if (json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;
  let res;
  try { res = await fetch(path, { method, headers, body }); }
  catch { throw new Error("Can't reach the server. Try again in a moment."); }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(data?.error?.message || "Something went wrong.");
    err.status = res.status; err.details = data?.error?.details || [];
    throw err;
  }
  return data;
}
const errText = e => e.details && e.details.length ? e.details.map(d => `${d.field}: ${d.message}`).join(" / ") : e.message;

/* ---------- wheel ---------- */
const ring = $("ring");
let posts = [], cards = [], cur = 0, rot = 0, step = 0, radius = 0, editing = null;

const fmtDate = iso => { const d = new Date(iso), p = n => String(n).padStart(2, "0"); return `${d.getFullYear()}.${p(d.getMonth() + 1)}.${p(d.getDate())}`; };

async function loadPosts(keepId) {
  try {
    const data = await api(`/posts?page=1&size=${PAGE_SIZE}`);
    posts = data.items;
    $("empty-text").textContent = "No cards yet. Be the first to write one.";
  } catch (e) {
    posts = []; $("empty-text").textContent = e.message;
  }
  build();
  const i = keepId == null ? -1 : posts.findIndex(p => p.id === keepId);
  if (i > 0) { cur = i; rot = cur * step; applyRing(); sync(); }
}

function build() {
  ring.innerHTML = ""; cards = []; cur = 0; rot = 0;
  $("empty").hidden = posts.length > 0;
  posts.forEach((p, i) => {
    const mine = user && p.author.id === user.id;
    const card = document.createElement("div"); card.className = "card"; card.style.setProperty("--c", BARS[p.id % BARS.length]);
    card.setAttribute("role", "group"); card.setAttribute("aria-label", `Card from ${p.author.username}: ${p.title}`);
    card.innerHTML = `<div class="face spread">
        <div class="leaf-l"><svg data-px="${ART[p.id % ART.length]}" aria-hidden="true"></svg></div>
        <div class="leaf-r"><h2></h2><p class="txt"></p><p class="sign"></p>
          <div class="acts"><button type="button" class="b heart like"><svg data-px="heart" aria-hidden="true"></svg><span class="lk"></span></button>
          ${mine ? '<span><button type="button" class="b edit">Edit</button><button type="button" class="b del">Delete</button></span>' : ""}</div></div>
      </div><div class="face cover" aria-hidden="true">once</div>`;
    card.querySelector("h2").textContent = p.title;
    card.querySelector(".txt").textContent = p.content;
    card.querySelector(".sign").textContent = `from ${p.author.username}, ${fmtDate(p.created_at)}`;
    card.querySelectorAll("svg").forEach(paint);
    if (p.image_url) { const im = document.createElement("img"); im.alt = ""; im.src = p.image_url; card.querySelector(".leaf-l").appendChild(im); }
    paintLike(card, p);
    card.addEventListener("click", e => onCardClick(e, i, p, card));
    ring.appendChild(card); cards.push(card);
  });
  layout(); sync();
}
function paintLike(card, p) {
  const btn = card.querySelector(".like");
  btn.classList.toggle("liked", p.liked_by_me);
  btn.setAttribute("aria-pressed", String(p.liked_by_me));
  btn.setAttribute("aria-label", `${p.liked_by_me ? "Unlike" : "Like"}, ${p.like_count} likes`);
  card.querySelector(".lk").textContent = p.like_count;
}
async function onCardClick(e, i, p, card) {
  if (i !== cur) { goTo(i); return; }
  if (e.target.closest(".like")) {
    if (!user) { openLogin("Sign in first to like a card."); return; }
    try { Object.assign(p, await api(`/posts/${p.id}/like`, { method: p.liked_by_me ? "DELETE" : "PUT" })); paintLike(card, p); }
    catch (err) { if (err.status === 401) { signOut(); openLogin("Your session ended. Sign in again."); } }
    return;
  }
  const del = e.target.closest(".del");
  if (del) {
    if (!del.dataset.sure) { del.dataset.sure = "1"; del.textContent = "Sure?"; return; }
    del.disabled = true;
    try { await api(`/posts/${p.id}`, { method: "DELETE" }); const next = posts[i + 1] || posts[i - 1]; await loadPosts(next && next.id); }
    catch (err) { del.disabled = false; del.textContent = "Delete"; delete del.dataset.sure; if (err.status === 401) { signOut(); openLogin("Your session ended. Sign in again."); } }
    return;
  }
  const ed = e.target.closest(".edit");
  if (ed) {
    editing = p; $("form").reset();
    $("f-title").value = p.title; $("f-text").value = p.content;
    if (p.image_url) { $("thumb").style.backgroundImage = `url("${p.image_url}")`; }
    $("t-pad").textContent = "edit_post.txt - Notepad"; $("f-submit").textContent = "Save";
    openWin("w-pad", ed);
  }
}
function layout() {
  // The wheel always has at least MIN_SLOTS positions, so a few cards still sit close together
  // (45 degrees apart) instead of spreading out edge-on. With fewer cards the wheel is an open arc.
  const n = cards.length, h = ring.offsetHeight, slots = Math.max(n, MIN_SLOTS);
  step = 360 / slots;
  radius = n < 2 ? 0 : Math.round((h / 2) / Math.tan(Math.PI / slots)) + 34;
  cards.forEach((c, i) => { c.style.transform = `rotateX(${-i * step}deg) translateZ(${radius}px)`; });
  applyRing();
}
function applyRing() { ring.style.transform = `translateZ(${-radius}px) rotateX(${rot}deg)`; }
function sync() {
  cards.forEach((c, i) => {
    const on = i === cur; c.classList.toggle("on", on); c.tabIndex = on ? 0 : -1;
    c.querySelectorAll("button").forEach(b => { b.tabIndex = on ? 0 : -1; });
  });
  $("pos").textContent = cards.length ? `${cur + 1} / ${cards.length}` : "";
}
function goTo(i) {
  const n = cards.length; if (!n) return;
  let d;
  if (n < MIN_SLOTS) { i = Math.max(0, Math.min(n - 1, i)); d = i - cur; } // open arc: stop at the ends
  else { d = ((i - cur) % n + n) % n; if (d > n / 2) d -= n; i = ((i % n) + n) % n; } // full ring: wrap around
  rot += d * step; cur = i;
  applyRing(); sync();
}
let rollLock = 0, rollAcc = 0, touchY = null;
$("stage").addEventListener("wheel", e => {
  e.preventDefault();
  const now = Date.now(); if (now < rollLock) return;
  rollAcc += e.deltaY; if (Math.abs(rollAcc) < 30) return;
  goTo(cur + (rollAcc > 0 ? 1 : -1)); rollAcc = 0; rollLock = now + 420;
}, { passive: false });
$("stage").addEventListener("touchstart", e => { touchY = e.touches[0].clientY; }, { passive: true });
$("stage").addEventListener("touchend", e => {
  if (touchY === null) return;
  const dy = e.changedTouches[0].clientY - touchY; touchY = null;
  if (Math.abs(dy) > 40) goTo(cur + (dy < 0 ? 1 : -1));
});
$("stage").addEventListener("keydown", e => {
  if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
  if (e.target.closest("textarea, input")) return;
  e.preventDefault(); goTo(cur + (e.key === "ArrowUp" ? -1 : 1)); if (cards[cur]) cards[cur].focus();
});
window.addEventListener("resize", layout);

/* ---------- windows ---------- */
const layer = $("layer"), floats = [...layer.querySelectorAll(".float")];
let opener = null;
function openWin(id, from) {
  if (layer.hidden) opener = from || document.activeElement;
  floats.forEach(f => { f.hidden = f.id !== id; });
  layer.hidden = false; $("desk").inert = true;
  const first = $(id).querySelector("input:not([type=file]), textarea, button.go"); if (first) first.focus();
}
function closeWin() { layer.hidden = true; $("desk").inert = false; if (opener && opener.isConnected) opener.focus(); }
function openLogin(why) { $("l-why").textContent = why || ""; $("l-why").hidden = !why; $("l-err").textContent = ""; openWin("w-login"); }
document.addEventListener("click", e => {
  const o = e.target.closest("[data-open]");
  if (o) {
    const id = o.dataset.open;
    if (o.id === "tab-login" && user) { signOut(); return; }
    if (id === "w-pad") {
      if (!user) { openLogin("Sign in first to write a post."); return; }
      editing = null; $("form").reset(); $("err").textContent = "";
      $("t-pad").textContent = "new_post.txt - Notepad"; $("f-submit").textContent = "Post";
    }
    if (id === "w-login") { $("l-why").hidden = true; $("l-err").textContent = ""; }
    if (id === "w-join") $("j-err").textContent = "";
    openWin(id, o); return;
  }
  if (e.target.closest("[data-close]") || e.target === layer) closeWin();
});
document.addEventListener("keydown", e => { if (e.key === "Escape" && !layer.hidden) closeWin(); });

/* ---------- account ---------- */
function paintUser() {
  $("tab-login").querySelector("span").textContent = user ? `Sign out (${user.username})` : "Sign in";
  $("tab-login").setAttribute("aria-label", user ? "Sign out" : "Sign in");
  $("tab-join").hidden = !!user;
}
function signOut() { saveToken(null); user = null; paintUser(); loadPosts(posts[cur] && posts[cur].id); }
async function signIn(email, password) {
  const data = await api("/auth/login", { method: "POST", json: { email, password } });
  saveToken(data.access_token);
  user = await api("/auth/me");
  paintUser();
  await loadPosts(posts[cur] && posts[cur].id);
}
async function busy(formEl, work) {
  const btn = formEl.querySelector('button[type="submit"]'); btn.disabled = true;
  try { await work(); } finally { btn.disabled = false; }
}
$("login").addEventListener("submit", e => {
  e.preventDefault();
  const email = $("l-email").value.trim(), password = $("l-pass").value;
  if (!email || !password) { $("l-err").textContent = "Enter your email and password."; return; }
  busy($("login"), async () => {
    try { await signIn(email, password); $("login").reset(); closeWin(); }
    catch (err) { $("l-err").textContent = errText(err); }
  });
});
$("join").addEventListener("submit", e => {
  e.preventDefault();
  const username = $("j-name").value.trim(), email = $("j-email").value.trim(), password = $("j-pass").value;
  if (!username || !email || !password) { $("j-err").textContent = "Fill in all three fields."; return; }
  busy($("join"), async () => {
    try {
      await api("/auth/signup", { method: "POST", json: { username, email, password } });
      await signIn(email, password); $("join").reset(); closeWin();
    } catch (err) { $("j-err").textContent = errText(err); }
  });
});

/* ---------- write / edit ---------- */
let pickedFile = null, pickedUrl = null;
function clearPick() {
  pickedFile = null; if (pickedUrl) { URL.revokeObjectURL(pickedUrl); pickedUrl = null; }
  $("thumb").style.backgroundImage = "none"; $("unpick").hidden = true; $("f-photo").value = "";
}
$("f-photo").addEventListener("change", e => {
  const f = e.target.files && e.target.files[0]; if (!f) return;
  if (f.size > 5 * 1024 * 1024) { $("err").textContent = "That picture is over 5MB. Choose a smaller one."; e.target.value = ""; return; }
  if (pickedUrl) URL.revokeObjectURL(pickedUrl);
  pickedFile = f; pickedUrl = URL.createObjectURL(f);
  $("thumb").style.backgroundImage = `url("${pickedUrl}")`; $("unpick").hidden = false; $("err").textContent = "";
});
$("unpick").addEventListener("click", () => { clearPick(); if (editing && editing.image_url) $("thumb").style.backgroundImage = `url("${editing.image_url}")`; });
$("form").addEventListener("reset", clearPick);
$("f-title").addEventListener("input", () => { $("err").textContent = ""; });
$("f-text").addEventListener("input", () => { $("err").textContent = ""; });
$("form").addEventListener("submit", e => {
  e.preventDefault();
  const title = $("f-title").value.trim(), content = $("f-text").value.trim();
  if (!title) { $("err").textContent = "Give your post a title first."; $("f-title").focus(); return; }
  if (!content) { $("err").textContent = "Write a few words for the card."; $("f-text").focus(); return; }
  busy($("form"), async () => {
    let saved = null;
    try {
      saved = editing
        ? await api(`/posts/${editing.id}`, { method: "PATCH", json: { title, content } })
        : await api("/posts", { method: "POST", json: { title, content } });
      if (pickedFile) { const fd = new FormData(); fd.append("file", pickedFile); await api(`/posts/${saved.id}/image`, { method: "PUT", form: fd }); }
      editing = null; $("form").reset(); closeWin(); await loadPosts(saved.id);
    } catch (err) {
      if (err.status === 401) { signOut(); closeWin(); openLogin("Your session ended. Sign in again."); return; }
      // the text was saved but the picture failed: keep the window open on that post so the picture can be retried
      if (saved) { editing = saved; $("t-pad").textContent = "edit_post.txt - Notepad"; $("f-submit").textContent = "Save"; loadPosts(saved.id); $("err").textContent = `Your post is saved, but the picture wasn't: ${errText(err)}`; return; }
      $("err").textContent = errText(err);
    }
  });
});

/* ---------- start ---------- */
(async function start() {
  if (token) {
    try { user = await api("/auth/me"); } catch { saveToken(null); }
  }
  paintUser();
  await loadPosts();
})();
