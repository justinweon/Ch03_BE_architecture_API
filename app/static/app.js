// 게시판 화면. 같은 서버의 API(/auth, /posts)를 호출한다.
// 화면 주소: #list, #page-2, #post-12, #write, #edit-12, #login, #signup
const view = document.getElementById("view");
const nav = document.getElementById("nav");
const TOKEN_KEY = "board_token";
const PAGE_SIZE = 10;

/* ---------- 작은 도우미 ---------- */
// h("a", {href: "#list", class: "btn"}, "목록") 처럼 요소를 만든다. 글 내용은 항상 텍스트로 넣어 HTML 로 해석되지 않게 한다.
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) if (c != null && c !== false) el.append(c);
  return el;
}
const pad = n => String(n).padStart(2, "0");
function fmt(iso) { const d = new Date(iso); return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`; }
function show(...nodes) { view.replaceChildren(...nodes.filter(Boolean)); window.scrollTo(0, 0); }

/* ---------- API ---------- */
let token = null, user = null;
try { token = localStorage.getItem(TOKEN_KEY); } catch { /* 저장소를 못 쓰면 로그아웃 상태로 시작 */ }
function saveToken(value) {
  token = value;
  try { if (value) localStorage.setItem(TOKEN_KEY, value); else localStorage.removeItem(TOKEN_KEY); } catch { /* 무시 */ }
}
async function api(path, { method = "GET", json, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let body;
  if (json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;
  let res;
  try { res = await fetch(path, { method, headers, body }); }
  catch { throw new Error("서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."); }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(data?.error?.message || "요청을 처리하지 못했습니다.");
    err.status = res.status; err.details = data?.error?.details || [];
    throw err;
  }
  return data;
}
const FIELD_NAMES = { title: "제목", content: "내용", email: "이메일", username: "닉네임", password: "비밀번호" };
const errText = e => e.details && e.details.length ? e.details.map(d => `${FIELD_NAMES[d.field] || d.field}: ${d.message}`).join(" / ") : e.message;
// 로그인이 만료된 채로 보호된 요청을 보냈을 때: 로그아웃 처리하고 로그인 화면으로
function expired(e) { if (e.status !== 401) return false; signOut(false); location.hash = "#login"; return true; }

/* ---------- 계정 ---------- */
function paintNav() {
  nav.replaceChildren(...(user
    ? [h("span", { class: "who" }, `${user.username}님`), h("button", { class: "btn", type: "button", onclick: () => signOut(true) }, "로그아웃")]
    : [h("a", { class: "btn", href: "#login" }, "로그인"), h("a", { class: "btn primary", href: "#signup" }, "회원가입")]));
}
function signOut(rerender) { saveToken(null); user = null; paintNav(); if (rerender) route(); }
async function signIn(email, password) {
  const data = await api("/auth/login", { method: "POST", json: { email, password } });
  saveToken(data.access_token);
  user = await api("/auth/me");
  paintNav();
}
async function withBusy(formEl, work) {
  const btn = formEl.querySelector('button[type="submit"]'); btn.disabled = true;
  try { await work(); } finally { btn.disabled = false; }
}

/* ---------- 목록 ---------- */
async function listView(page) {
  let data;
  try { data = await api(`/posts?page=${page}&size=${PAGE_SIZE}`); }
  catch (e) { show(h("div", { class: "panel empty" }, e.message)); return; }
  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  if (page > pages) { location.hash = pages > 1 ? `#page-${pages}` : "#list"; return; }

  const head = h("div", { class: "head" },
    h("h1", {}, "전체 글", h("span", { class: "count" }, `${data.total}개`)),
    h("a", { class: "btn primary", href: "#write" }, "글쓰기"));

  let body;
  if (!data.items.length) {
    body = h("div", { class: "panel empty" }, "아직 글이 없습니다. 첫 글을 남겨 보세요.");
  } else {
    const rows = data.items.map(p => {
      const open = () => { location.hash = `#post-${p.id}`; };
      return h("tr", { tabindex: "0", onclick: open, onkeydown: e => { if (e.key === "Enter") open(); } },
        h("td", { class: "num" }, p.id),
        h("td", { class: "title" }, p.title, p.image_url ? h("span", { class: "tag" }, "사진") : null),
        h("td", {}, p.author.username),
        h("td", { class: "date" }, fmt(p.created_at)),
        h("td", { class: "num" }, p.like_count));
    });
    body = h("div", { class: "panel tablebox" }, h("table", {},
      h("thead", {}, h("tr", {}, h("th", { class: "num" }, "번호"), h("th", {}, "제목"), h("th", {}, "작성자"), h("th", { class: "date" }, "작성일"), h("th", { class: "num" }, "좋아요"))),
      h("tbody", {}, rows)));
  }

  const link = (n, label, current) => h("a", { class: `btn${current ? " on" : ""}`, href: n === 1 ? "#list" : `#page-${n}`, "aria-current": current ? "page" : null, "aria-label": typeof label === "string" && isNaN(label) ? label : `${n}쪽` }, label);
  const from = Math.max(1, Math.min(page - 2, pages - 4)), to = Math.min(pages, from + 4);
  const pager = pages > 1 ? h("nav", { class: "pager", "aria-label": "쪽 이동" },
    page > 1 ? link(page - 1, "이전") : null,
    Array.from({ length: to - from + 1 }, (_, i) => link(from + i, String(from + i), from + i === page)),
    page < pages ? link(page + 1, "다음") : null) : null;

  show(head, body, pager);
}

/* ---------- 글 보기 ---------- */
async function postView(id) {
  let p;
  try { p = await api(`/posts/${id}`); }
  catch (e) { show(h("div", { class: "panel empty" }, e.message, h("p", {}, h("a", { class: "btn", href: "#list" }, "목록으로")))); return; }
  const mine = user && user.id === p.author.id;
  const edited = p.updated_at !== p.created_at ? " (수정됨)" : "";

  const likeBtn = h("button", { class: "btn", type: "button" });
  const paintLike = () => { likeBtn.textContent = `좋아요 ${p.like_count}`; likeBtn.classList.toggle("on", p.liked_by_me); likeBtn.setAttribute("aria-pressed", String(p.liked_by_me)); };
  paintLike();
  likeBtn.addEventListener("click", async () => {
    if (!user) { location.hash = "#login"; return; }
    likeBtn.disabled = true;
    try { p = await api(`/posts/${p.id}/like`, { method: p.liked_by_me ? "DELETE" : "PUT" }); paintLike(); }
    catch (e) { if (!expired(e)) msg.textContent = e.message; }
    finally { likeBtn.disabled = false; }
  });

  const msg = h("p", { class: "error", role: "alert" });
  const delBtn = h("button", { class: "btn danger", type: "button" }, "삭제");
  delBtn.addEventListener("click", async () => {
    if (!delBtn.dataset.sure) { delBtn.dataset.sure = "1"; delBtn.textContent = "정말 삭제할까요?"; return; }
    delBtn.disabled = true;
    try { await api(`/posts/${p.id}`, { method: "DELETE" }); location.hash = "#list"; }
    catch (e) { delBtn.disabled = false; delBtn.textContent = "삭제"; delete delBtn.dataset.sure; if (!expired(e)) msg.textContent = e.message; }
  });

  show(h("article", { class: "panel post" },
    h("h1", {}, p.title),
    h("p", { class: "meta" }, `${p.author.username} · ${fmt(p.created_at)}${edited}`),
    p.image_url ? h("img", { src: p.image_url, alt: "첨부 사진" }) : null,
    h("div", { class: "content" }, p.content),
    msg,
    h("div", { class: "actions" },
      h("div", { class: "group" }, likeBtn, h("a", { class: "btn", href: "#list" }, "목록")),
      mine ? h("div", { class: "group" }, h("a", { class: "btn", href: `#edit-${p.id}` }, "수정"), delBtn) : null)));
}

/* ---------- 글쓰기 / 수정 ---------- */
async function writeView(id) {
  if (!user) { location.hash = "#login"; return; }
  let p = null;
  if (id) {
    try { p = await api(`/posts/${id}`); }
    catch (e) { show(h("div", { class: "panel empty" }, e.message)); return; }
    if (p.author.id !== user.id) { show(h("div", { class: "panel empty" }, "작성자만 수정할 수 있습니다.")); return; }
  }
  const title = h("input", { type: "text", id: "f-title", maxlength: "200", autocomplete: "off", value: p ? p.title : "" });
  const content = h("textarea", { id: "f-content", maxlength: "2000" }); content.value = p ? p.content : "";
  const file = h("input", { type: "file", id: "f-file", accept: "image/jpeg,image/png,image/gif,image/webp" });
  const msg = h("p", { class: "error", role: "alert" });
  const form = h("form", { class: "panel", novalidate: true },
    h("h1", {}, p ? "글 수정" : "글쓰기"),
    h("div", { class: "field" }, h("label", { for: "f-title" }, "제목"), title),
    h("div", { class: "field" }, h("label", { for: "f-content" }, "내용"), content),
    h("div", { class: "field" }, h("label", { for: "f-file" }, "사진 ", h("span", { class: "hint" }, p && p.image_url ? "(선택, 새로 고르면 기존 사진을 바꿉니다)" : "(선택, JPG·PNG·GIF·WEBP, 5MB 이하)")), file),
    msg,
    h("div", { class: "row" }, h("a", { class: "btn", href: p ? `#post-${p.id}` : "#list" }, "취소"), h("button", { class: "btn primary", type: "submit" }, p ? "저장" : "등록")));

  form.addEventListener("submit", e => {
    e.preventDefault();
    const t = title.value.trim(), c = content.value.trim(), f = file.files[0];
    if (!t) { msg.textContent = "제목을 입력해 주세요."; title.focus(); return; }
    if (!c) { msg.textContent = "내용을 입력해 주세요."; content.focus(); return; }
    if (f && f.size > 5 * 1024 * 1024) { msg.textContent = "사진은 5MB 이하만 올릴 수 있습니다."; return; }
    withBusy(form, async () => {
      let saved = null;
      try {
        saved = p ? await api(`/posts/${p.id}`, { method: "PATCH", json: { title: t, content: c } })
                  : await api("/posts", { method: "POST", json: { title: t, content: c } });
        if (f) { const fd = new FormData(); fd.append("file", f); await api(`/posts/${saved.id}/image`, { method: "PUT", form: fd }); }
        location.hash = `#post-${saved.id}`;
      } catch (err) {
        if (expired(err)) return;
        // 글은 저장됐는데 사진만 실패한 경우: 수정 화면에서 사진을 다시 올릴 수 있게 한다
        if (saved) { p = saved; msg.textContent = `글은 저장됐지만 사진은 올리지 못했습니다: ${errText(err)}`; form.querySelector("h1").textContent = "글 수정"; return; }
        msg.textContent = errText(err);
      }
    });
  });
  show(form); title.focus();
}

/* ---------- 로그인 / 회원가입 ---------- */
function loginView() {
  if (user) { location.hash = "#list"; return; }
  const email = h("input", { type: "email", id: "l-email", autocomplete: "username" });
  const pass = h("input", { type: "password", id: "l-pass", autocomplete: "current-password" });
  const msg = h("p", { class: "error", role: "alert" });
  const form = h("form", { class: "panel narrow", novalidate: true },
    h("h1", {}, "로그인"),
    h("div", { class: "field" }, h("label", { for: "l-email" }, "이메일"), email),
    h("div", { class: "field" }, h("label", { for: "l-pass" }, "비밀번호"), pass),
    msg,
    h("button", { class: "btn primary", type: "submit" }, "로그인"),
    h("p", { class: "alt" }, "계정이 없나요? ", h("a", { href: "#signup" }, "회원가입")));
  form.addEventListener("submit", e => {
    e.preventDefault();
    if (!email.value.trim() || !pass.value) { msg.textContent = "이메일과 비밀번호를 입력해 주세요."; return; }
    withBusy(form, async () => {
      try { await signIn(email.value.trim(), pass.value); location.hash = "#list"; }
      catch (err) { msg.textContent = errText(err); }
    });
  });
  show(form); email.focus();
}
function signupView() {
  if (user) { location.hash = "#list"; return; }
  const name = h("input", { type: "text", id: "s-name", maxlength: "50", autocomplete: "nickname" });
  const email = h("input", { type: "email", id: "s-email", autocomplete: "username" });
  const pass = h("input", { type: "password", id: "s-pass", autocomplete: "new-password" });
  const msg = h("p", { class: "error", role: "alert" });
  const form = h("form", { class: "panel narrow", novalidate: true },
    h("h1", {}, "회원가입"),
    h("div", { class: "field" }, h("label", { for: "s-name" }, "닉네임 ", h("span", { class: "hint" }, "(2자 이상)")), name),
    h("div", { class: "field" }, h("label", { for: "s-email" }, "이메일"), email),
    h("div", { class: "field" }, h("label", { for: "s-pass" }, "비밀번호 ", h("span", { class: "hint" }, "(8자 이상)")), pass),
    msg,
    h("button", { class: "btn primary", type: "submit" }, "가입하기"),
    h("p", { class: "alt" }, "이미 계정이 있나요? ", h("a", { href: "#login" }, "로그인")));
  form.addEventListener("submit", e => {
    e.preventDefault();
    const n = name.value.trim(), m = email.value.trim(), pw = pass.value;
    if (!n || !m || !pw) { msg.textContent = "닉네임, 이메일, 비밀번호를 모두 입력해 주세요."; return; }
    withBusy(form, async () => {
      try { await api("/auth/signup", { method: "POST", json: { username: n, email: m, password: pw } }); await signIn(m, pw); location.hash = "#list"; }
      catch (err) { msg.textContent = errText(err); }
    });
  });
  show(form); name.focus();
}

/* ---------- 주소에 따라 화면 고르기 ---------- */
function route() {
  const name = location.hash.slice(1) || "list";
  let m;
  if (name === "list") return listView(1);
  if ((m = name.match(/^page-(\d+)$/))) return listView(Math.max(1, Number(m[1])));
  if ((m = name.match(/^post-(\d+)$/))) return postView(Number(m[1]));
  if (name === "write") return writeView(null);
  if ((m = name.match(/^edit-(\d+)$/))) return writeView(Number(m[1]));
  if (name === "login") return loginView();
  if (name === "signup") return signupView();
  return listView(1);
}
window.addEventListener("hashchange", route);

(async function start() {
  if (token) {
    try { user = await api("/auth/me"); } catch { saveToken(null); }
  }
  paintNav();
  route();
})();
