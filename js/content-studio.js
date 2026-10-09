/* ==========================================================================
   content-studio.js — Bộ sửa nội dung & thiết kế cho giáo viên
   --------------------------------------------------------------------------
   Giáo viên sửa thẳng câu hỏi / nhiệm vụ / gợi ý trên trang học sinh, lưu nháp,
   rồi "Xuất bản" để cả lớp nhìn thấy. Kèm thư viện thiết kế + xuất/nhập tệp.

   Cách hoạt động (và vì sao như vậy):
   * Đơn vị sửa là MỘT TEXT NODE, không phải cả phần tử. Nhiều câu hỏi nằm lẫn
     với <b>/<textarea>/<details> trong cùng một khối; thay textContent sẽ xoá
     mất các phần tử đó. Đổi đúng text node thì cấu trúc trang giữ nguyên.
   * Một "ô nội dung" được nhận diện bằng (đường dẫn phần tử + vị trí text node
     + bản băm của NỘI DUNG GỐC). Nội dung gốc nằm trong khoá, nên bản sửa chỉ
     áp dụng khi nội dung gốc vẫn còn nguyên ở đúng chỗ — đổi nguồn xây dựng sẽ
     làm bản sửa "trượt" (báo rõ số lượng) chứ không dán nhầm vào câu khác.
   * Nhiều câu hỏi do JS sinh ra (BANK, DATA, Q...) và bị vẽ lại khi học sinh đổi
     dự án/gói. Vì vậy có MutationObserver: phần tử nào bị vẽ lại về nguyên bản
     thì bản sửa được đắp lại ngay.
   * Bản đã xuất bản được nhớ trong localStorage và đắp NGAY khi DOM sẵn sàng,
     nên không thấy "nháy" nội dung cũ; sau đó tải lại từ máy chủ để luôn mới.
   ========================================================================== */
(function () {
  'use strict';

  var D = document;
  var PAGE = (function () {
    var f = location.pathname.split('/').pop() || 'index.html';
    f = f.replace(/\.html?$/i, '');
    return f || 'index';
  })();

  var K = {
    draft: 'sah_content_draft_v1',
    cache: 'sah_content_cache_v1',
    lib: 'sah_content_library_v1',
    cfg: 'sah_content_cfg_v1',
    seeded: 'sah_content_seed_v1'
  };
  var MIN_LEN = 12;
  var GUARD_MS = 1500;
  var CONTENT_URL = 'content/published.json';
  var LIBRARY_URL = 'content/library/designs.json';

  var SKIP_TAGS = {
    SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEMPLATE: 1, SVG: 1, PATH: 1, MATH: 1,
    CANVAS: 1, IFRAME: 1, OBJECT: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1,
    OPTION: 1, OPTGROUP: 1, CODE: 1, PRE: 1, VIDEO: 1, AUDIO: 1
  };

  /* ---------------------------------------------------------------- tiện ích */
  function norm(s) { return String(s == null ? '' : s).replace(/\s+/g, ' ').trim(); }

  function fnv(s) {
    var h = 0x811c9dc5, i;
    for (i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = (h * 0x01000193) >>> 0; }
    return ('0000000' + h.toString(16)).slice(-8);
  }

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
  function readJSON(k, dflt) {
    var raw = lsGet(k);
    if (!raw) return dflt;
    try { var v = JSON.parse(raw); return (v && typeof v === 'object') ? v : dflt; } catch (e) { return dflt; }
  }
  function writeJSON(k, v) { return lsSet(k, JSON.stringify(v)); }
  function nowISO() { return new Date().toISOString(); }
  function uid() { return Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4); }

  function el(tag, attrs, kids) {
    var n = D.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      /* Hàm phải gán thành thuộc tính, KHÔNG được setAttribute: đặt onclick
         bằng setAttribute sẽ biến mã nguồn của hàm thành thân HTML, và trình
         duyệt báo "SyntaxError: Function statements require a function name" —
         đúng lỗi đã gặp làm nút "Lưu cài đặt" không chạy. */
      else if (typeof attrs[k] === 'function') n[k] = attrs[k];
      else if (attrs[k] === true) n.setAttribute(k, '');
      else if (attrs[k] != null && attrs[k] !== false) n.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }

  /* ------------------------------------------------------- mô hình "ô" nội dung */

  function pathOf(node) {
    var parts = [], n = node;
    while (n && n.nodeType === 1 && n !== D.body) {
      var p = n.tagName.toLowerCase();
      var par = n.parentElement;
      if (par) {
        var same = [], c = par.children, i;
        for (i = 0; i < c.length; i++) if (c[i].tagName === n.tagName) same.push(c[i]);
        if (same.length > 1) p += ':nth-of-type(' + (same.indexOf(n) + 1) + ')';
      }
      parts.unshift(p);
      n = n.parentElement;
    }
    return parts.join('>');
  }

  function resolvePath(path) {
    if (!path) return null;
    var parts = String(path).split('>'), cur = D.body, i, j;
    for (i = 0; i < parts.length; i++) {
      var m = /^([a-z0-9]+)(?::nth-of-type\((\d+)\))?$/i.exec(parts[i]);
      if (!m) return null;
      var tag = m[1].toUpperCase(), want = m[2] ? parseInt(m[2], 10) : 0, hit = null, seen = 0;
      for (j = 0; j < cur.children.length; j++) {
        if (cur.children[j].tagName === tag) {
          seen++;
          if (want ? seen === want : seen === 1) { hit = cur.children[j]; break; }
        }
      }
      if (!hit) return null;
      cur = hit;
    }
    return cur;
  }

  function textIdx(t) {
    var i = 0, n = t.parentNode ? t.parentNode.firstChild : null;
    while (n && n !== t) { if (n.nodeType === 3) i++; n = n.nextSibling; }
    return n === t ? i : -1;
  }

  function textAt(parent, i) {
    var c = parent.childNodes, seen = 0, j;
    for (j = 0; j < c.length; j++) {
      if (c[j].nodeType === 3) { if (seen === i) return c[j]; seen++; }
    }
    return null;
  }

  function skipped(node) {
    var x = node;
    while (x && x.nodeType === 1) {
      if (SKIP_TAGS[x.tagName]) return true;
      if (x.hasAttribute && x.hasAttribute('data-sah-ui')) return true;
      x = x.parentElement;
    }
    return false;
  }

  function editableTextNode(t) {
    return !!t && t.nodeType === 3 && !skipped(t.parentNode) && norm(t.data).length >= MIN_LEN;
  }

  function groupRoot(node) {
    var x = node;
    while (x.parentElement && x.parentElement !== D.body &&
           x.parentElement.tagName !== 'MAIN' && x.parentElement.tagName !== 'BODY') {
      x = x.parentElement;
    }
    return x;
  }

  function secId(node) {
    var s = node.closest ? node.closest('section[id]') : null;
    if (s) return s.id;
    var g = node.closest ? node.closest('[id]') : null;
    return g ? g.id : '';
  }

  /* Tập "ô nội dung" hiện có trên trang. */
  /* Một ô luôn được nhận diện bằng NỘI DUNG GỐC của trang, không bao giờ bằng
     chữ đang hiển thị. Nếu lấy chữ đang hiển thị, sửa lại một ô đã sửa sẽ tạo
     ra ô mới lấy "gốc" là bản sửa cũ, và nút Về bản gốc chẳng xoá được gì —
     đúng lỗi đã gặp. pending chính là các bản sửa đang áp dụng, nên tra ngược
     được từ chữ đang hiện về chữ gốc. */
  function pristineOf(path, i, cur) {
    for (var j = 0; j < pending.length; j++) {
      var e = pending[j];
      if (e.path === path && e.i === i && e.v === cur) return e.p;
    }
    return cur;
  }

  function collect() {
    var out = [], w, t;
    try { w = D.createTreeWalker(D.body, NodeFilter.SHOW_TEXT); } catch (e) { return out; }
    while ((t = w.nextNode())) {
      if (!editableTextNode(t)) continue;
      var cur = norm(t.data), parent = t.parentNode, i = textIdx(t);
      if (i < 0) continue;
      var path = pathOf(parent);
      var v = pristineOf(path, i, cur);
      out.push({
        k: path + '#' + i + '#' + fnv(v),
        path: path, i: i, p: v,
        sec: secId(parent),
        grp: pathOf(groupRoot(parent)),
        node: t
      });
    }
    return out;
  }

  var FIELDS = [];                 // tập ô nội dung của lần quét gần nhất
  var FIELD_BY_KEY = {};

  function refreshFields() {
    FIELDS = collect();
    FIELD_BY_KEY = {};
    FIELDS.forEach(function (f) { FIELD_BY_KEY[f.k] = f; });
    return FIELDS;
  }

  function setText(t, value) {
    var raw = t.data || '';
    var lead = (raw.match(/^\s*/) || [''])[0];
    var trail = (raw.match(/\s*$/) || [''])[0];
    t.data = lead + value + trail;
  }

  /* Tìm lại text node của một bản sửa. `quick` = chỉ dò theo đường dẫn (dùng
     trong vòng lặp MutationObserver cho rẻ). */
  function findNode(e, quick) {
    var parent = resolvePath(e.path);
    if (parent) {
      var t = textAt(parent, e.i);
      if (t && (norm(t.data) === e.p || norm(t.data) === e.v)) return t;
      var c = parent.childNodes, j;
      for (j = 0; j < c.length; j++) {
        if (c[j].nodeType === 3) {
          var s = norm(c[j].data);
          if (s === e.p || s === e.v) return c[j];
        }
      }
    }
    if (quick) return null;
    var root = (e.sec && D.getElementById(e.sec)) || resolvePath(e.grp) || D.body;
    var w, n;
    try { w = D.createTreeWalker(root, NodeFilter.SHOW_TEXT); } catch (err) { return null; }
    while ((n = w.nextNode())) {
      var s2 = norm(n.data);
      if ((s2 === e.p || s2 === e.v) && !skipped(n.parentNode)) return n;
    }
    return null;
  }

  /* ------------------------------------------------------------------ kho lưu */
  /* Khoá: pages.<page>.text["<path>#<i>#<hash nội dung gốc>"] = {v,p,path,i,sec,grp}
     Còn: pages.<page>.hidden = [id khối bị ẩn theo thiết kế]                        */

  function emptyStore() { return { v: 1, at: null, by: '', pages: {} }; }

  function pageOf(store) {
    if (!store.pages) store.pages = {};
    if (!store.pages[PAGE]) store.pages[PAGE] = { text: {}, hidden: [] };
    var p = store.pages[PAGE];
    if (!p.text) p.text = {};
    if (!p.hidden) p.hidden = [];
    return p;
  }

  function countText(store) {
    var p = store && store.pages && store.pages[PAGE];
    if (!p || !p.text) return 0;
    return Object.keys(p.text).length;
  }

  function mergeInto(dest, src) {
    var sp = src && src.pages && src.pages[PAGE];
    if (!sp) return dest;
    var dp = pageOf(dest);
    for (var k in (sp.text || {})) dp.text[k] = sp.text[k];
    (sp.hidden || []).forEach(function (id) { if (dp.hidden.indexOf(id) < 0) dp.hidden.push(id); });
    return dest;
  }

  function published() { var s = readJSON(K.cache, emptyStore()); if (!s.pages) s.pages = {}; return s; }
  function draft() { var s = readJSON(K.draft, emptyStore()); if (!s.pages) s.pages = {}; return s; }
  /* Trả về kết quả ghi: nơi gọi dựa vào đó để báo thành công hay thất bại. */
  function saveDraft(s) { s.at = nowISO(); return writeJSON(K.draft, s); }

  /* ------------------------------------------------------------ áp dụng lên trang */

  var pending = [];          // các bản sửa đang áp dụng: {k,v,p,path,i,sec,grp}
  var stats = { applied: 0, ok: 0, unmatched: 0 };

  function entriesOf(store) {
    var p = store && store.pages && store.pages[PAGE];
    if (!p || !p.text) return [];
    var out = [];
    for (var k in p.text) {
      var e = p.text[k];
      if (!e || typeof e.v !== 'string') continue;
      out.push({ k: k, v: e.v, p: e.p, path: e.path, i: e.i, sec: e.sec, grp: e.grp });
    }
    return out;
  }

  function applyAll(store, quick) {
    pending = entriesOf(store);
    stats = { applied: 0, ok: 0, unmatched: 0 };
    pending.forEach(function (e) { applyOne(e, quick); });
    applyHidden(store);
    return stats;
  }

  function applyOne(e, quick) {
    var t = findNode(e, quick);
    if (!t) { stats.unmatched++; return false; }
    if (norm(t.data) === e.v) { stats.ok++; return true; }
    setText(t, e.v);
    stats.applied++;
    return true;
  }

  function applyHidden(store) {
    var p = store && store.pages && store.pages[PAGE];
    var ids = (p && p.hidden) || [];
    var all = D.querySelectorAll('[data-sah-hidden]');
    var i;
    for (i = 0; i < all.length; i++) all[i].removeAttribute('data-sah-hidden');
    for (i = 0; i < ids.length; i++) {
      var n = D.getElementById(ids[i]);
      if (n) n.setAttribute('data-sah-hidden', '1');
    }
  }

  /* Vẽ lại của trang (đổi dự án/gói, chuyển chặng...) làm mất bản sửa. Đắp lại
     bằng MutationObserver — nhờ vậy nội dung do JS sinh ra cũng giữ được bản sửa. */
  var applying = false;
  var observer = null;

  /* Đắp lại NGAY, không hẹn qua requestAnimationFrame: ở thẻ chạy nền trình duyệt
     hạ nhịp rAF xuống rất thấp, đo được độ trễ 172 ms–1,2 giây, nên câu hỏi vừa
     bị vẽ lại cứ hiện nguyên bản một lúc rồi mới đổi. Đắp đồng bộ thì hễ nội dung
     bị vẽ lại, bản sửa về đúng ngay trong cùng nhịp. Vòng lặp không thể chạy mãi
     vì chỉ ghi khi nội dung khác bản sửa — ghi xong thì lần sau không còn gì để
     ghi. */
  function scheduleReapply() {
    if (applying || !pending.length) return;
    applying = true;
    try {
      for (var i = 0; i < pending.length; i++) {
        var e = pending[i];
        var t = findNode(e, true);
        if (t && norm(t.data) !== e.v) setText(t, e.v);
      }
    } finally {
      applying = false;
    }
  }

  function startObserver() {
    if (observer || !window.MutationObserver) return;
    observer = new MutationObserver(function (records) {
      var i, r, ours = true;
      for (i = 0; i < records.length; i++) {
        r = records[i];
        var n = r.target && r.target.nodeType === 1 ? r.target : (r.target && r.target.parentNode);
        if (!n || !n.closest || !n.closest('[data-sah-ui]')) { ours = false; break; }
      }
      if (!ours) scheduleReapply();
    });
    try {
      observer.observe(D.body, { childList: true, subtree: true, characterData: true });
    } catch (e) { observer = null; }
  }

  /* Chống "nháy" nội dung cũ: ẩn trước các khối có bản sửa, gỡ ra ngay sau khi
     đắp xong; kèm khoá an toàn theo thời gian để trang không thể kẹt trắng. */
  function guardOn(store) {
    var sel = [], seen = {}, p = store && store.pages && store.pages[PAGE];
    if (!p) return;
    var needTop = false;
    /* Đoạn này chạy trong <head>, khi phần thân trang chưa được đọc — nên KHÔNG
       được kiểm tra phần tử có tồn tại hay không, chỉ dựng bộ chọn theo id. */
    Object.keys(p.text || {}).forEach(function (k) {
      var e = p.text[k];
      if (e && e.sec) { if (!seen[e.sec]) { seen[e.sec] = 1; sel.push('#' + e.sec); } }
      else needTop = true;
    });
    var hid = p.hidden || [];
    hid.forEach(function (id) { if (!seen[id]) { seen[id] = 1; sel.push('#' + id); } });
    if (needTop && !seen.__top) { sel.push('header'); sel.push('.rm-topnav'); }
    if (!sel.length) return;
    var style = el('style', { 'data-sah-ui': '1' });
    style.textContent = 'html.sah-pre ' + sel.join(',html.sah-pre ') + '{visibility:hidden !important}';
    try { D.head.appendChild(style); D.documentElement.classList.add('sah-pre'); } catch (e) {}
    setTimeout(guardOff, GUARD_MS);
  }

  function guardOff() { try { D.documentElement.classList.remove('sah-pre'); } catch (e) {} }

  /* ---------------------------------------------------------------- cấu hình */
  function cfg() {
    var c = readJSON(K.cfg, {});
    if (typeof c.api !== 'string') c.api = '';
    if (typeof c.token !== 'string') c.token = '';
    return c;
  }
  function saveCfg(c) { writeJSON(K.cfg, c); }
  function apiUrl(path) { return String(cfg().api || '').replace(/\/+$/, '') + path; }

  /* ------------------------------------------------------------ studio: dựng UI */

  var UI = {};
  var STUDIO_ON = false;
  var previewPublished = false;
  var highlighted = null;

  /* Khối bị ẩn theo thiết kế của giáo viên phải biến mất với HỌC SINH — nên quy
     tắc này phải có mặt trên mọi lượt mở trang, không chỉ khi bật chế độ sửa.
     Trước đây nó nằm trong bảng kiểu của bộ sửa, nên học sinh vẫn thấy đủ khối. */
  function addBaseStyles() {
    if (D.getElementById('sah-base-css')) return;
    var st = el('style', { 'data-sah-ui': '1', id: 'sah-base-css' });
    st.textContent = '[data-sah-hidden]{display:none !important}';
    D.head.appendChild(st);
  }

  function addStyles() {
    if (D.getElementById('sah-studio-css')) return;
    var css = [
      /* Chỉ tô ô đang được trỏ tới. Tô cả 1700 ô cùng lúc thì trang không còn\n         đọc được nữa — chính vì vậy data-sah-hit không có kiểu dáng. */
      /* Lớp sah-studio do mã này gắn lên <body> (xem toggleStudio/boot), KHÔNG
         phải <html>. Bản cũ viết html.sah-studio nên không bao giờ khớp: đo
         bằng getComputedStyle thấy outline:none, cursor:auto — tức là giáo
         viên không hề thấy ô nào sửa được, dù bấm vào vẫn mở hộp sửa. */
      "body.sah-studio [data-sah-hover]{outline:2px dashed #c89547 !important;outline-offset:2px;border-radius:3px;cursor:text}",
      "body.sah-studio:not(.sah-noedit) [data-sah-hover]{background:rgba(200,149,71,.07)}",
      "[data-sah-hidden]{display:none !important}",
      "[data-sah-ui]{box-sizing:border-box}",
      "[data-sah-ui] button{font:inherit;cursor:pointer}",
      "#sahBar{position:fixed;left:14px;bottom:14px;z-index:9000;display:flex;gap:6px;align-items:center;flex-wrap:wrap;max-width:calc(100vw - 28px);background:#12281f;color:#eaf3ee;border-radius:14px;padding:8px 10px;box-shadow:0 8px 26px rgba(0,0,0,.32);font:13px/1.35 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}",
      "#sahBar .sah-b{border:0;border-radius:9px;padding:7px 11px;background:#1d4033;color:#eaf3ee;font-weight:600}",
      "#sahBar .sah-b:hover{background:#285b46}",
      "#sahBar .sah-b.pri{background:#c89547;color:#12281f}",
      "#sahBar .sah-b.on{background:#2e7d55;color:#fff}",
      "#sahBar .sah-b[disabled]{opacity:.45;cursor:not-allowed}",
      "#sahBar .sah-meta{font-size:12px;color:#bcd3c6;padding:2px 6px;border-radius:8px;max-width:46vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
      "#sahBar .sah-meta.act{cursor:pointer;text-decoration:underline dotted}",
      "#sahBar .sah-meta.act:hover{background:#1d4033}",
      "#sahBar .sah-meta.warn{color:#ffd479}",
      "#sahBar .sah-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#c89547;margin-right:5px;vertical-align:1px}",
      "#sahBar .sah-dot.clean{background:#3f9d6a}",
      "#sahPanel{position:fixed;right:0;top:0;bottom:0;width:390px;max-width:96vw;z-index:9001;background:#fff;border-left:1px solid #d7e0da;display:flex;flex-direction:column;font:13px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#1d2a24;box-shadow:-8px 0 30px rgba(0,0,0,.14)}",
      "#sahPanel header{padding:12px 14px;border-bottom:1px solid #e6ece8;display:flex;align-items:center;gap:8px}",
      "#sahPanel header b{flex:1;font-size:14px}",
      "#sahPanel .sah-x{border:0;background:#eef3f0;border-radius:8px;padding:5px 9px}",
      "#sahPanel .sah-search{padding:10px 14px;border-bottom:1px solid #e6ece8;display:grid;gap:6px}",
      "#sahPanel .sah-search input{padding:8px 10px;border:1px solid #c9d5cd;border-radius:9px;font:inherit}",
      "#sahPanel .sah-tabs{display:flex;gap:6px;flex-wrap:wrap}",
      "#sahPanel .sah-tabs button{border:1px solid #d7e0da;background:#f7faf8;border-radius:999px;padding:5px 10px;font-size:12px}",
      "#sahPanel .sah-tabs button.on{background:#285b46;color:#fff;border-color:#285b46}",
      "#sahPanel .sah-list{overflow:auto;padding:8px 10px 22px;flex:1}",
      "#sahPanel .sah-grp{margin:10px 0 4px;font-weight:800;font-size:12px;letter-spacing:.03em;text-transform:uppercase;color:#5d6b63}",
      "#sahPanel .sah-item{display:block;width:100%;text-align:left;border:1px solid #e3eae6;background:#fbfdfc;border-radius:10px;padding:8px 10px;margin:5px 0;line-height:1.4}",
      "#sahPanel .sah-item:hover{border-color:#285b46;background:#f2f8f4}",
      "#sahPanel .sah-item.chg{border-left:4px solid #c89547}",
      "#sahPanel .sah-item small{display:block;color:#6b7a72;font-size:11px;margin-top:3px}",
      "#sahPanel .sah-empty{color:#6b7a72;padding:18px 6px}",
      "#sahPanel .sah-block{border:1px solid #e3eae6;border-radius:10px;padding:8px 10px;margin:5px 0;display:flex;gap:8px;align-items:flex-start}",
      "#sahPanel .sah-block b{flex:1;font-weight:600}",
      "#sahEdit{position:fixed;z-index:9002;width:420px;max-width:96vw;background:#fff;border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,.26);border:1px solid #d7e0da;padding:12px;font:13px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#1d2a24}",
      "#sahEdit textarea{width:100%;min-height:92px;padding:9px;border:1px solid #c9d5cd;border-radius:9px;font:inherit;resize:vertical}",
      "#sahEdit .sah-row{display:flex;gap:7px;align-items:center;margin-top:9px;flex-wrap:wrap}",
      "#sahEdit .sah-row button{border:0;border-radius:9px;padding:8px 12px;font-weight:700}",
      "#sahEdit .sah-save{background:#285b46;color:#fff}",
      "#sahEdit .sah-cancel{background:#eef3f0;color:#285b46}",
      "#sahEdit .sah-reset{background:#fff3e0;color:#8a5a12}",
      "#sahEdit .sah-where{font-size:11px;color:#6b7a72;word-break:break-all}",
      "#sahEdit .sah-same{margin-top:8px;font-size:12px;background:#f7faf8;border:1px dashed #cfdcd5;border-radius:9px;padding:7px 9px}",
      "#sahModal{position:fixed;inset:0;z-index:9003;background:rgba(12,26,20,.6);display:flex;align-items:center;justify-content:center;padding:18px}",
      "#sahModal .sah-mcard{background:#fff;border-radius:18px;max-width:720px;width:100%;max-height:88vh;overflow:auto;padding:20px;font:13px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#1d2a24}",
      "#sahModal h3{margin:0 0 10px}",
      "#sahModal h4{margin:16px 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#5d6b63}",
      "#sahModal .sah-more-item{display:block;width:100%;text-align:left;border:1px solid #e3eae6;background:#fbfdfc;border-radius:11px;padding:12px 14px;margin:7px 0;font-weight:700;font-size:14px}",
      "#sahModal .sah-more-item:hover{border-color:#285b46;background:#f2f8f4}",
      "#sahModal .sah-lib{border:1px solid #e3eae6;border-radius:11px;padding:10px;margin:7px 0;display:flex;gap:10px;align-items:flex-start}",
      "#sahModal .sah-lib b{flex:1}",
      "#sahModal .sah-lib small{color:#6b7a72;display:block}",
      "#sahModal .sah-lib button{border:0;border-radius:8px;padding:6px 10px;background:#eef3f0;font-weight:600}",
      "#sahModal .sah-fields{display:grid;gap:7px;margin-top:10px}",
      "#sahModal .sah-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}",
      "#sahModal .sah-row button{border:0;border-radius:9px;padding:9px 13px;font-weight:700}",
      "#sahModal .sah-save{background:#285b46;color:#fff}",
      "#sahModal .sah-cancel{background:#eef3f0;color:#285b46}",
      "#sahModal label{display:grid;gap:4px;margin-top:9px}",
      "#sahModal label span{font-size:12px;color:#5d6b63}",
      "#sahModal details{margin-top:10px;border-top:1px solid #e6ece8;padding-top:8px}",
      "#sahModal summary{cursor:pointer;color:#5d6b63;font-weight:700}",
      "#sahModal input[type=text],#sahModal input[type=password]{width:100%;padding:9px;border:1px solid #c9d5cd;border-radius:9px;font:inherit}",
      "#sahToast{position:fixed;left:50%;bottom:82px;transform:translateX(-50%);z-index:9004;background:#12281f;color:#fff;padding:11px 16px;border-radius:11px;font:13px/1.4 system-ui,sans-serif;max-width:88vw;box-shadow:0 10px 30px rgba(0,0,0,.3)}",
      "#sahToast.err{background:#8c2f21}",
      "@media(max-width:700px){#sahBar{left:8px;right:8px;bottom:8px}#sahPanel{width:100vw}#sahEdit{width:94vw}}"
    ].join('\n');
    var st = el('style', { 'data-sah-ui': '1', id: 'sah-studio-css' });
    st.textContent = css;
    D.head.appendChild(st);
  }

  /* Mỗi thông báo tự hẹn giờ cho CHÍNH NÓ. Bản cũ hẹn giờ rồi xoá UI.toast —
     tức là xoá thông báo mới nhất, không phải thông báo của mình. Hệ quả thật
     đã gặp: thông báo "Đang mở chế độ sửa" lúc mở trang hẹn giờ xong ở giây
     thứ 5,7 và xoá luôn thông báo "Đã quay lại bản lưu" vừa hiện, nên giáo viên
     không đọc được lời xác nhận. */
  function toast(msg, isErr) {
    if (UI.toast) UI.toast.remove();
    var node = el('div', { 'data-sah-ui': '1', id: 'sahToast', class: isErr ? 'err' : '', text: msg });
    UI.toast = node;
    D.body.appendChild(node);
    setTimeout(function () {
      node.remove();
      if (UI.toast === node) UI.toast = null;
    }, 4200);
  }

  /* ------------------------------------------------------------- khối thiết kế */

  function designBlocks() {
    var ids = ['p321V312', 'sah321-integrated', 'direct321-module', 'sah-ai5a-studio',
      'sketchV25', 'artV33', 'exhibitV38', 'journey39', 'rmExhibit', 'rmRoom3d', 'rmChat'];
    var out = [];
    ids.forEach(function (id) {
      var n = D.getElementById(id);
      if (!n) return;
      var h = n.querySelector('h1,h2,h3');
      out.push({ id: id, name: norm(h ? h.textContent : id) || id });
    });
    return out;
  }

  /* ----------------------------------------------------- sửa một câu trên trang */
  /* Trước đây chỗ này còn hàm changedKeys() để đếm "N thay đổi chưa xuất bản"
     trên thanh lệnh. Thanh lệnh mới không còn con số đó nữa (giáo viên không
     cần đếm), và việc quyết định có gửi lên hay không nay do cờ DIRTY quyết
     định — xem phần "tự lưu & tự đưa lên" bên dưới. */
  function editField(f, value) {
    var d = draft();
    var p = pageOf(d);
    var had = p.text[f.k];
    lastUndo = { k: f.k, before: had ? had.v : null };   // null = trước đó là chữ gốc của trang
    if (value == null || norm(value) === '' || norm(value) === f.p) delete p.text[f.k];
    else p.text[f.k] = { v: value, p: f.p, path: f.path, i: f.i, sec: f.sec, grp: f.grp, at: nowISO() };
    DIRTY = true;
    saveDraft(d);
    return d;
  }

  /* ------------------------------------------------- tự lưu & tự đưa lên cho học sinh */
  /* Giáo viên không phải "lưu" rồi "xuất bản": sửa xong một câu là việc lưu và
     việc đưa lên xảy ra cùng lúc, không hỏi gì. Không có chữ nào về tệp, mã hay
     "bản nháp" trong giao diện — chỉ có một câu trạng thái và nút Hoàn tác.

     DIRTY là "giáo viên đã sửa gì trong phiên này", không phải "tệp khác bản đã
     đưa lên" — nhờ vậy việc tự đưa lên khi vừa đăng nhập không bao giờ ghi đè
     bài của máy khác bằng một bản nháp rỗng. */
  var SAVE_STATE = 'idle';       // idle | saving | saved | offline | failed
  var SAVE_HINT = '';
  var DIRTY = false;             // có thay đổi thật chưa gửi lên được
  var lastUndo = null;           // { k, before } — để dựng lại thao tác vừa rồi

  function setSaveState(state, hint) {
    SAVE_STATE = state;
    SAVE_HINT = hint || '';
    updateBar();
  }

  /* Sau khi biết máy này đã đăng nhập hay chưa: có việc đang chờ thì gửi, không
     thì chỉ nói cho giáo viên biết trạng thái thật. */
  function afterSession(ok) {
    if (!ok) { if (STUDIO_ON) setSaveState('offline'); return; }
    if (DIRTY) commitAll();
    else setSaveState('saved');
  }

  function saveLabel() {
    if (SAVE_STATE === 'saving') return 'Đang lưu…';
    if (SAVE_STATE === 'saved') return '✓ Học sinh đang thấy bản này';
    if (SAVE_STATE === 'offline') return '⚠ Chưa đăng nhập — bấm để đăng nhập';
    if (SAVE_STATE === 'failed') return '⚠ Chưa lưu được — bấm để thử lại';
    return DIRTY ? '… Chưa gửi lên' : '✓ Đã lưu';
  }

  /* Lưu tại chỗ rồi đẩy lên. Gọi ở ba chỗ: khi đóng hộp sửa, khi bật/tắt khối,
     và khi trang sắp bị đóng (để chữ đang gõ dở không mất nếu giáo viên đóng
     tab ngay giữa câu). */
  function commitAll() {
    saveDraft(draft());
    if (!DIRTY) { if (canWrite()) setSaveState('saved'); return; }
    if (!canWrite()) { setSaveState('offline'); return; }
    publishQuietly();
  }

  /* Không hỏi gì, không báo "đang xuất bản…": ghi xong thì báo đã lưu, lỗi thì
     để giáo viên bấm thử lại. */
  function publishQuietly() {
    var pg = pageOf(draft());
    var payload = { page: PAGE, text: pg.text || {}, hidden: pg.hidden || [],
                    at: nowISO(), by: 'teacher' };
    setSaveState('saving');
    fetch(apiUrl('/api/content'), {
      method: 'POST',
      credentials: 'same-origin',
      keepalive: true,             // sống sót khi trang vừa bị đóng
      headers: apiHeaders(true),
      body: JSON.stringify(payload)
    }).then(function (r) {
      return r.text().then(function (t) { return { ok: r.ok, status: r.status, body: t }; });
    }).then(function (r) {
      if (!r.ok) throw new Error(r.status + ' ' + r.body.slice(0, 160));
      var saved = null;
      try { saved = JSON.parse(r.body); } catch (e) {}
      var store = published();
      store.at = (saved && saved.at) || payload.at;
      store.pages = store.pages || {};
      store.pages[PAGE] = { text: payload.text, hidden: payload.hidden };
      writeJSON(K.cache, store);
      var dd = draft();
      dd.sid = store.at;
      saveDraft(dd);
      DIRTY = false;
      setSaveState('saved');
    }).catch(function (err) {
      var m = String(err.message || '');
      if (m.indexOf('401') === 0) { SIGNED_IN = false; setSaveState('offline'); return; }
      setSaveState('failed', m.slice(0, 80));
    });
  }

  function undoLast() {
    if (!lastUndo) return;
    var k = lastUndo.k, before = lastUndo.before;
    var d = draft(), p = pageOf(d);
    if (before == null) delete p.text[k];
    else {
      var f = FIELD_BY_KEY[k];
      p.text[k] = f
        ? { v: before, p: f.p, path: f.path, i: f.i, sec: f.sec, grp: f.grp, at: nowISO() }
        : Object.assign({}, p.text[k] || {}, { v: before });
    }
    saveDraft(d);
    lastUndo = null;
    DIRTY = true;
    repaint(true);
    commitAll();
    toast('Đã trả lại như trước.');
  }

  /* Áp dụng cùng nội dung cho mọi ô đang có ĐÚNG nội dung gốc này. */
  function similarFields(f) {
    return FIELDS.filter(function (x) { return x.p === f.p && x.k !== f.k; });
  }

  function editSimilar(f, value) {
    var d = draft(), p = pageOf(d), n = 0;
    if (!value || value === f.p) return 0;
    similarFields(f).forEach(function (x) {
      p.text[x.k] = { v: value, p: x.p, path: x.path, i: x.i, sec: x.sec, grp: x.grp, at: nowISO() };
      n++;
    });
    if (n) { DIRTY = true; saveDraft(d); }
    return n;
  }

  /* --------------------------------------------------------- chế độ xem trước */
  function activeStore() {
    if (!STUDIO_ON || previewPublished) return published();
    return draft();
  }

  /* Trả những ô đang mang bản sửa về nội dung gốc trước khi đắp bộ khác — nếu
     không, một ô đã xuất bản rồi bỏ khỏi bản nháp sẽ mãi giữ nội dung cũ. */
  function resetApplied() {
    pending.forEach(function (e) {
      var t = findNode(e, false);
      if (t && norm(t.data) === e.v) setText(t, e.p);
    });
    pending = [];
  }

  function repaint(quiet) {
    resetApplied();
    var s = applyAll(activeStore());
    if (STUDIO_ON) decorate();
    updateBar();
    return s;
  }

  /* Bản nháp là BỨC TRANH ĐẦY ĐỦ giáo viên muốn thấy, nên khi mở chế độ sửa lần
     đầu (hoặc sau khi có người khác xuất bản) nó được trộn thêm phần đã xuất
     bản. Nhờ vậy "Về bản gốc" xoá khỏi nháp là trang hiện lại nguyên bản. */
  function ensureDraftSeeded() {
    var d = draft(), pub = published();
    var sid = pub.at || 'none';
    if (d.sid === sid) return d;
    mergeInto(d, pub);
    d.sid = sid;
    saveDraft(d);
    return d;
  }

  /* ------------------------------------------------------------ tô viền ô sửa */
  /* Quét lại danh sách ô. Không gắn thuộc tính lên từng ô: hơn 1700 lần ghi DOM
     mỗi lần lưu là vô ích, vì phần tô sáng chỉ dùng cho ô đang được trỏ tới. */
  function decorate() {
    if (!STUDIO_ON) return;
    refreshFields();
  }

  function pickAt(x, y) {
    var n = null;
    try {
      if (D.caretRangeFromPoint) {
        var r = D.caretRangeFromPoint(x, y);
        n = r && r.startContainer;
      } else if (D.caretPositionFromPoint) {
        var c = D.caretPositionFromPoint(x, y);
        n = c && c.offsetNode;
      }
    } catch (e) { n = null; }
    if (n && n.nodeType === 3) {
      if (editableTextNode(n)) return n;
      /* Bấm trúng nhãn ngắn nằm cạnh câu hỏi ("1.", "3 – KHÁM PHÁ"...) vẫn phải
         mở được ô chứa nó — nhưng chỉ dò lên tối đa 3 tầng để không vơ phải
         một ô không liên quan ở tận khối cha. */
      var p = n.parentElement;
      for (var hop = 0; hop < 3 && p && p !== D.body; hop++) {
        var hit = firstEditable(p);
        if (hit) return hit;
        p = p.parentElement;
      }
      return null;
    }
    if (n && n.nodeType === 1) return firstEditable(n);
    return null;
  }

  function firstEditable(root) {
    var w, t;
    try { w = D.createTreeWalker(root, NodeFilter.SHOW_TEXT); } catch (e) { return null; }
    while ((t = w.nextNode())) if (editableTextNode(t)) return t;
    return null;
  }

  function fieldFor(node) {
    var parent = node.parentNode, i = textIdx(node);
    if (i < 0) return null;
    var path = pathOf(parent);
    var v = pristineOf(path, i, norm(node.data));
    return {
      k: path + '#' + i + '#' + fnv(v),
      path: path, i: i, p: v,
      sec: secId(parent), grp: pathOf(groupRoot(parent)), node: node
    };
  }

  /* Những chỗ bấm vào là để LÀM VIỆC, không phải để sửa chữ. Bộ sửa tuyệt đối
     không được nuốt cú bấm của trang: trước đây nó gọi stopPropagation cho mọi
     cú bấm ở pha capture, làm cổng chọn vai trò, các thẻ và nút lưu đều chết. */
  var WORK_TAGS = { A: 1, BUTTON: 1, INPUT: 1, SELECT: 1, TEXTAREA: 1, LABEL: 1, SUMMARY: 1, VIDEO: 1, AUDIO: 1, IFRAME: 1, OPTION: 1 };

  function isControl(el) {
    var x = el;
    while (x && x.nodeType === 1 && x !== D.body) {
      if (WORK_TAGS[x.tagName]) return true;
      if (x.hasAttribute('onclick') || x.hasAttribute('href') || x.hasAttribute('contenteditable')) return true;
      if (x.getAttribute && x.getAttribute('role') === 'button') return true;
      /* Con trỏ bàn tay là dấu hiệu chắc chắn nhất của "chỗ này bấm được", kể cả
         khi trang gắn sự kiện bằng JS (thẻ tác phẩm, thẻ hướng đi...). */
      try { if (getComputedStyle(x).cursor === 'pointer') return true; } catch (e) {}
      x = x.parentElement;
    }
    return false;
  }

  function onClickDoc(ev) {
    if (!STUDIO_ON) return;
    var t = ev.target;
    if (!t || !t.closest) return;
    if (t.closest('[data-sah-ui]')) return;
    /* Cú bấm do mã tạo ra (btn.click(), thẻ <label>...) phải giữ nguyên ý nghĩa
       của trang — chỉ cú bấm thật của người dùng mới mở hộp sửa. */
    if (ev.isTrusted === false) return;
    if (isControl(t)) return;
    var node = pickAt(ev.clientX, ev.clientY);
    if (!node) return;
    ev.preventDefault();
    ev.stopPropagation();
    openEditor(fieldFor(node), node);
  }

  var hoverTarget = null;

  function onHoverDoc(ev) {
    if (!STUDIO_ON || UI.edit) return;
    var t = ev.target;
    if (!t || !t.closest || t.closest('[data-sah-ui]')) return;
    /* mousemove bắn rất nhiều; chỉ tính lại khi con trỏ sang phần tử khác, nếu
       không mỗi lần di chuột lại phải getComputedStyle cả chuỗi cha. */
    if (t === hoverTarget) return;
    hoverTarget = t;
    var host = null;
    if (!isControl(t)) {
      var node = pickAt(ev.clientX, ev.clientY);
      host = node ? node.parentNode : null;
    }
    if (host === highlighted) return;
    highlighted = host;
    var all = D.querySelectorAll('[data-sah-hover]'), i;
    for (i = 0; i < all.length; i++) all[i].removeAttribute('data-sah-hover');
    if (host) host.setAttribute('data-sah-hover', '1');
  }

  /* ------------------------------------------------------------- hộp sửa một ô */
  function openEditor(f, node) {
    if (!f) return;
    closeEditor();
    var d = draft();
    var p = pageOf(d);
    var stored = p.text[f.k];
    var before = stored ? stored.v : f.p;

    var ta = el('textarea', { 'data-role': 'value' });
    ta.value = before;

    var same = similarFields(f);
    var sameBox = null, sameChk = null;
    if (same.length) {
      sameChk = el('input', { type: 'checkbox' });
      sameBox = el('label', { class: 'sah-same', 'data-sah-ui': '1' }, [
        sameChk,
        el('span', { text: ' Áp dụng cho ' + same.length + ' vị trí khác đang có đúng nội dung gốc này' })
      ]);
    }

    /* Gõ tới đâu trang hiện tới đó, và chữ đã gõ không bao giờ mất: đóng hộp
       bằng cách nào (bấm Xong, bấm sang câu khác, gõ Esc) cũng đều tự lưu và
       tự đưa lên cho học sinh. Không còn nút "lưu nháp" hay "xuất bản". */
    var dirty = false;
    var live = function () { if (node && node.parentNode) setText(node, ta.value); };
    ta.addEventListener('input', function () {
      dirty = true;
      /* Gõ là thanh lệnh đổi ngay thành "chưa gửi lên", để giáo viên không bao
         giờ tưởng nhầm là học sinh đã thấy chữ mình đang gõ. */
      if (!DIRTY) { DIRTY = true; setSaveState('idle'); }
      live();
    });

    function saveNow() {
      if (!dirty) return 0;
      editField(f, ta.value);
      var extra = 0;
      if (sameChk && sameChk.checked) extra = editSimilar(f, ta.value);
      dirty = false;
      repaint(true);
      commitAll();                 // tự lưu + tự đưa lên, không hỏi gì
      return extra;
    }

    var box = el('div', { 'data-sah-ui': '1', id: 'sahEdit' }, [
      el('div', { class: 'sah-where', text: (f.sec ? '#' + f.sec + ' › ' : '') + f.path.split('>').slice(-2).join(' › ') }),
      ta,
      sameBox,
      el('div', { class: 'sah-row' }, [
        el('button', { class: 'sah-save', 'data-act': 'save', text: '✅ Xong' }),
        el('button', { class: 'sah-reset', 'data-act': 'reset', text: '↩️ Trả lại như cũ' }),
        el('button', { class: 'sah-cancel', 'data-act': 'cancel', text: 'Đóng' })
      ]),
      el('div', { class: 'sah-where', text: canWrite()
        ? 'Sửa xong là học sinh thấy ngay. Lỡ tay thì bấm ↩️ Hoàn tác trên thanh dưới.'
        : 'Máy này chưa đăng nhập, nên sửa xong cần bấm Thêm › Đăng nhập một lần.' })
    ]);

    box.addEventListener('click', function (ev) {
      var a = ev.target.getAttribute && ev.target.getAttribute('data-act');
      if (!a) return;
      if (a === 'cancel') { closeEditor(); return; }
      if (a === 'reset') {
        lastUndo = null;
        editField(f, f.p);
        if (sameChk && sameChk.checked) {
          var d2 = draft(), p2 = pageOf(d2);
          similarFields(f).forEach(function (x) { delete p2.text[x.k]; });
          saveDraft(d2);
        }
        dirty = false;
        repaint(true); closeEditor(); commitAll();
        toast('Đã trả lại như trước.');
        return;
      }
      if (a === 'save') {
        var extra = saveNow();
        closeEditor();
        if (extra) toast('Đã sửa cả ' + extra + ' chỗ có cùng câu chữ.');
      }
    });

    /* Đóng hộp vì bất cứ lý do gì (bấm câu khác, gõ Esc…) cũng lưu trước. */
    UI.editCommit = saveNow;

    D.body.appendChild(box);
    UI.edit = box;
    var r = node && node.parentNode ? node.parentNode.getBoundingClientRect() : null;
    var top = r ? Math.min(Math.max(r.bottom + 8, 12), window.innerHeight - 260) : 90;
    var left = r ? Math.min(Math.max(r.left, 12), window.innerWidth - 440) : 40;
    box.style.top = Math.max(12, top) + 'px';
    box.style.left = Math.max(12, left) + 'px';
    ta.focus();
  }

  function closeEditor() {
    if (!UI.edit) return;
    var commit = UI.editCommit;
    UI.editCommit = null;
    UI.edit.remove();
    UI.edit = null;
    if (commit) { try { commit(); } catch (e) {} }
  }

  /* ------------------------------------------------------------------ thanh lệnh */
  /* Thanh này cố tình ngắn và không có một chữ kỹ thuật nào: bốn việc giáo
     viên thật sự làm, một câu trạng thái cho biết học sinh đã thấy bài mới hay
     chưa, và một nút "Thêm" giấu hết những thứ phức tạp ở trong. */
  function updateBar() {
    if (!UI.bar) return;
    UI.meta.textContent = '';
    UI.meta.appendChild(el('span', { class: 'sah-dot' + (SAVE_STATE === 'saved' || SAVE_STATE === 'idle' ? ' clean' : '') }));
    UI.meta.appendChild(D.createTextNode(STUDIO_ON ? saveLabel() : 'Chế độ sửa đang tắt'));
    if (SAVE_STATE === 'failed' && SAVE_HINT) UI.meta.title = SAVE_HINT;
    else UI.meta.removeAttribute('title');
    /* Chip chỉ trông bấm được khi bấm vào có việc để làm — "đã lưu" thì đừng
       mời người ta bấm (kiểm tra trên máy chủ thật phát hiện chỗ này). */
    var actionable = SAVE_STATE === 'offline' || SAVE_STATE === 'failed' || DIRTY;
    UI.meta.classList.toggle('warn', SAVE_STATE === 'offline' || SAVE_STATE === 'failed');
    UI.meta.classList.toggle('act', actionable);

    UI.btnStudio.textContent = STUDIO_ON ? '✏️ Đang sửa' : '✏️ Sửa nội dung';
    UI.btnStudio.classList.toggle('on', STUDIO_ON);
    UI.btnPreview.textContent = previewPublished ? '👁 Đang xem như học sinh' : '👁 Xem như học sinh';
    UI.btnPreview.classList.toggle('on', previewPublished);
    UI.btnUndo.disabled = !lastUndo;
    UI.btnMore.textContent = (STUDIO_ON && !canWrite()) ? '🔐 Thêm' : '➕ Thêm';
  }

  function buildBar() {
    if (UI.bar) return;
    UI.meta = el('span', { class: 'sah-meta', 'data-sah-ui': '1' });
    UI.btnStudio = el('button', { class: 'sah-b', 'data-sah-ui': '1' });
    UI.btnPreview = el('button', { class: 'sah-b', 'data-sah-ui': '1' });
    UI.btnUndo = el('button', { class: 'sah-b', 'data-sah-ui': '1', text: '↩️ Hoàn tác',
                                title: 'Trả lại nội dung vừa sửa' });
    UI.btnMore = el('button', { class: 'sah-b', 'data-sah-ui': '1', text: '➕ Thêm',
                                title: 'Danh sách câu chữ, ẩn/hiện khối, quay lại bản trước' });

    UI.bar = el('div', { 'data-sah-ui': '1', id: 'sahBar' },
      [UI.btnStudio, UI.btnPreview, UI.btnUndo, UI.meta, UI.btnMore]);
    D.body.appendChild(UI.bar);

    UI.btnStudio.onclick = function () { toggleStudio(!STUDIO_ON); };
    UI.btnPreview.onclick = function () { previewPublished = !previewPublished; repaint(true); };
    UI.btnUndo.onclick = function () { undoLast(); };
    UI.btnMore.onclick = function () { openMore(); };
    /* Bấm vào câu trạng thái: chưa đưa lên được thì đăng nhập, lỗi thì thử lại. */
    UI.meta.onclick = function () {
      if (!STUDIO_ON) return;
      if (SAVE_STATE === 'offline') { openSettings(); return; }
      if (SAVE_STATE === 'failed') { commitAll(); return; }
      /* Chỉ gửi khi giáo viên thật sự vừa sửa (DIRTY). So bản nháp với bản nhớ
         trong máy là sai đường: máy mới mở lần đầu có bản nhớ rỗng, "khác" là
         giả, gửi đi sẽ xoá mất bài mà máy khác đã đưa lên. */
      if (DIRTY) commitAll(); else setSaveState('saved');
    };
    updateBar();
  }

  /* Nút "Thêm" — mọi thứ khác gom vào một chỗ, gọi tên bằng việc chứ không
     bằng cơ chế ("Quay lại bản trước", không phải "Bản lưu đã xuất bản"). */
  function openMore() {
    if (!STUDIO_ON) toggleStudio(true);
    var signed = canWrite();
    var items = [];
    if (!signed) items.push(['🔐 Đăng nhập để học sinh thấy bài mới', openSettings]);
    items = items.concat([
      ['🔎 Tìm câu chữ cần sửa', openPanel],
      ['🙈 Ẩn / hiện từng phần', openDesign],
      ['📚 Thư viện thiết kế', openLibrary],
      ['🕘 Quay lại bản trước', openHistory]
    ]);
    if (signed) items.push(['🔐 Đăng nhập / đăng xuất', openSettings]);
    var list = el('div', { class: 'sah-mcard', 'data-sah-ui': '1' }, [el('h3', { text: '➕ Thêm' })]);
    if (!signed) {
      list.appendChild(el('p', { class: 'sah-where', text: 'Máy này chưa đăng nhập nên bài sửa chưa đến tay học sinh.' }));
    }
    items.forEach(function (it) {
      var b = el('button', { class: 'sah-more-item', text: it[0] });
      b.onclick = function () { closeModal(); it[1](); };
      list.appendChild(b);
    });
    list.appendChild(el('div', { class: 'sah-row' }, [el('button', { class: 'sah-cancel', text: 'Đóng' })]));
    showModal(list);
  }

  /* Mở trang với ?studio=1 mà chưa chọn vai trò thì cổng hỏi "em là ai?" sẽ
     chặn ngay trên trang. Giáo viên vào đây để sửa nội dung, nên dùng đúng
     đường của trang: chọn "Khách" (xem trọn hành trình, không nộp bài). Lựa
     chọn này vẫn đổi lại được bằng nút "Đổi" trên thanh trên cùng. */
  var viewableDone = false;

  function ensureViewable(tries) {
    tries = tries || 0;
    if (lsGet('sah_role')) return;
    var gate = D.getElementById('roleGate');
    var btn = D.querySelector('#rgChoices .rm-choice[data-role="guest"]');
    /* Bộ sửa chạy ở DOMContentLoaded, còn js/restored-modules.js gắn sự kiện
       cho cổng chọn vai trò trong một DOMContentLoaded đăng ký sau — nên lần
       bấm đầu tiên có thể rơi vào lúc chưa có ai lắng nghe. Thử lại vài nhịp. */
    if (btn && gate && !gate.hidden) {
      try { btn.click(); } catch (e) { lsSet('sah_role', 'guest'); }
    }
    if (lsGet('sah_role')) {
      if (!viewableDone) {
        viewableDone = true;
        toast('Đang xem trang như học sinh (không nộp bài).');
      }
      return;
    }
    if (tries < 8) setTimeout(function () { ensureViewable(tries + 1); }, 120);
  }

  function toggleStudio(on) {
    STUDIO_ON = !!on;
    if (STUDIO_ON) {
      buildBar();
      ensureViewable();
      addStyles();
      if (D.body) D.body.classList.add('sah-studio');
      ensureDraftSeeded();
      decorate();
    } else {
      if (D.body) D.body.classList.remove('sah-studio');
      closeEditor();
      if (UI.panel) { UI.panel.remove(); UI.panel = null; }
      previewPublished = false;
    }
    repaint(true);
    if (STUDIO_ON) toast('Bấm vào câu chữ trên trang để sửa. Sửa xong là học sinh thấy ngay.');
  }

  /* --------------------------------------------------------------- bảng danh sách */
  function openPanel() {
    if (UI.panel) { UI.panel.remove(); UI.panel = null; return; }
    if (!STUDIO_ON) toggleStudio(true);
    var list = el('div', { class: 'sah-list', 'data-sah-ui': '1' });
    var q = el('input', { type: 'search', placeholder: 'Tìm câu chữ cần sửa…', 'data-sah-ui': '1' });
    var only = { mode: 'all' };
    var tabs = el('div', { class: 'sah-tabs', 'data-sah-ui': '1' });

    function renderList() {
      var d = draft(), p = pageOf(d);
      var term = norm(q.value).toLowerCase();
      list.textContent = '';
      refreshFields();
      var groups = {};
      FIELDS.forEach(function (f) {
        var edited = !!p.text[f.k];
        if (only.mode === 'edited' && !edited) return;
        if (term) {
          var hay = (f.p + ' ' + (edited ? p.text[f.k].v : '')).toLowerCase();
          if (hay.indexOf(term) < 0) return;
        }
        (groups[f.grp] = groups[f.grp] || []).push(f);
      });
      var keys = Object.keys(groups);
      if (!keys.length) { list.appendChild(el('div', { class: 'sah-empty', text: 'Không tìm thấy câu nào khớp.' })); return; }
      keys.forEach(function (gk) {
        var arr = groups[gk];
        var root = null;
        try { root = resolvePath(gk); } catch (e) { root = null; }
        var h = root ? root.querySelector('h1,h2,h3') : null;
        var name = (h ? norm(h.textContent) : '') || (root && root.id ? '#' + root.id : gk.split('>').slice(-1)[0]);
        list.appendChild(el('div', { class: 'sah-grp', text: name + ' • ' + arr.length + ' câu' }));
        arr.slice(0, 400).forEach(function (f) {
          var edited = !!p.text[f.k];
          var shown = edited ? p.text[f.k].v : f.p;
          var item = el('button', { class: 'sah-item' + (edited ? ' chg' : ''), 'data-k': f.k },
            [el('span', { text: shown.slice(0, 120) }),
             el('small', { text: (edited ? 'ĐÃ SỬA › ' : '') + f.p.slice(0, 70) })]);
          item.onclick = function () {
            var node = findNode({ path: f.path, i: f.i, p: f.p, v: edited ? p.text[f.k].v : f.p, sec: f.sec, grp: f.grp }) || f.node;
            if (!node) { toast('Câu này không còn trên trang.', true); return; }
            try { node.parentNode.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) {}
            openEditor(fieldFor(node) || f, node);
          };
          list.appendChild(item);
        });
      });
    }

    [['all', 'Tất cả'], ['edited', 'Đã sửa']].forEach(function (t) {
      var b = el('button', { text: t[1] });
      b.onclick = function () {
        only.mode = t[0];
        [].forEach.call(tabs.children, function (x) { x.classList.remove('on'); });
        b.classList.add('on');
        renderList();
      };
      if (t[0] === 'all') b.classList.add('on');
      tabs.appendChild(b);
    });
    q.addEventListener('input', renderList);

    UI.panel = el('div', { 'data-sah-ui': '1', id: 'sahPanel' }, [
      el('header', {}, [el('b', { text: 'Tìm câu chữ cần sửa' }),
        el('button', { class: 'sah-x', text: '✕' })]),
      el('div', { class: 'sah-search' }, [q, tabs]),
      list
    ]);
    UI.panel.querySelector('.sah-x').onclick = function () { UI.panel.remove(); UI.panel = null; };
    D.body.appendChild(UI.panel);
    renderList();
  }

  /* ------------------------------------------------------------- khối thiết kế */
  function openDesign() {
    if (!STUDIO_ON) toggleStudio(true);
    var d = draft(), p = pageOf(d);
    var blocks = designBlocks();
    var fields = el('div', { class: 'sah-fields', 'data-sah-ui': '1' });
    blocks.forEach(function (b) {
      var chk = el('input', { type: 'checkbox' });
      chk.checked = p.hidden.indexOf(b.id) < 0;
      chk.onchange = function () {
        var dd = draft(), pp = pageOf(dd);
        pp.hidden = pp.hidden.filter(function (x) { return x !== b.id; });
        if (!chk.checked) pp.hidden.push(b.id);
        DIRTY = true;
        saveDraft(dd);
        repaint(true);
        commitAll();               // ẩn/hiện cũng tự lưu, không cần bấm gì thêm
      };
      fields.appendChild(el('label', { class: 'sah-lib', 'data-sah-ui': '1' }, [
        chk, el('b', {}, [
          el('span', { text: b.name.slice(0, 90) }),
          el('small', { text: '#' + b.id + (p.hidden.indexOf(b.id) < 0 ? ' • đang mở' : ' • sẽ ẩn với học sinh') })
        ])
      ]));
    });
    var m = el('div', { class: 'sah-mcard', 'data-sah-ui': '1' }, [
      el('h3', { text: '🙈 Ẩn / hiện từng phần' }),
      el('p', { text: 'Bỏ chọn phần nào thì học sinh không thấy phần đó nữa. Chữ vẫn còn nguyên, muốn cho hiện lại thì tích vào.' }),
      fields,
      el('div', { class: 'sah-row' }, [el('button', { class: 'sah-cancel', text: 'Đóng' })])
    ]);
    showModal(m);
  }

  /* ------------------------------------------------------------------ thư viện */
  function library() { var l = readJSON(K.lib, {}); return l && typeof l === 'object' ? l : {}; }
  function saveLibrary(l) { return writeJSON(K.lib, l); }

  function openLibrary() {
    if (!STUDIO_ON) toggleStudio(true);
    var m = el('div', { class: 'sah-mcard', 'data-sah-ui': '1' });
    m.appendChild(el('h3', { text: '📚 Thư viện thiết kế' }));
    m.appendChild(el('p', { text: 'Cách bài đang sửa thành một "thiết kế" để dùng lại cho lớp khác, hoặc chọn lại một thiết kế đã lưu.' }));

    /* lưu bản hiện tại */
    var nameIn = el('input', { type: 'text', placeholder: 'Tên thiết kế, VD: Tiết 2 – 6A1' });
    m.appendChild(el('h4', { text: 'Cất cách bài đang sửa' }));
    m.appendChild(el('div', { class: 'sah-row' }, [
      nameIn,
      el('button', { class: 'sah-save', text: '💾 Lưu vào thư viện', onclick: function () {
        var nm = norm(nameIn.value);
        if (!nm) { toast('Hãy đặt tên cho thiết kế.', true); return; }
        var l = library();
        l[nm] = { at: nowISO(), pages: JSON.parse(JSON.stringify(draft().pages)) };
        if (!saveLibrary(l)) { toast('Trình duyệt không cho lưu thư viện.', true); return; }
        nameIn.value = '';
        renderLibs();
        toast('Đã cất thiết kế “' + nm + '”.');
      } })
    ]));

    m.appendChild(el('h4', { text: 'Thiết kế có sẵn' }));
    var libBox = el('div', { 'data-sah-ui': '1' });
    m.appendChild(libBox);
    function renderLibs() {
      var l = library(), keys = Object.keys(l);
      libBox.textContent = '';
      if (!keys.length) libBox.appendChild(el('div', { class: 'sah-empty', text: 'Thư viện trống. Hãy cất thiết kế đầu tiên ở trên.' }));
      keys.forEach(function (nm) {
        var n = countText(l[nm]);
        libBox.appendChild(el('div', { class: 'sah-lib', 'data-sah-ui': '1' }, [

          el('b', {}, [el('span', { text: nm }),
            el('small', { text: n + ' chỗ sửa • ' + dateText(l[nm].at) })]),
          el('button', { text: 'Dùng cách này', onclick: function () {
            var d = draft();
            mergeInto(d, l[nm]);
            DIRTY = true;
            saveDraft(d);
            repaint(true);
            closeModal();
            commitAll();
            toast('Đã đổi sang thiết kế “' + nm + '”.');
          } }),
          el('button', { text: 'Xoá', onclick: function () {
            var ll = library(); delete ll[nm]; saveLibrary(ll); renderLibs();
          } })
        ]));
      });
    }
    renderLibs();

    m.appendChild(el('div', { class: 'sah-row' }, [el('button', { class: 'sah-cancel', text: 'Đóng' })]));
    showModal(m);

    /* thiết kế mẫu đóng gói kèm trang */
    fetch(LIBRARY_URL + '?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.designs || !j.designs.length) return;
        var box = el('div', { 'data-sah-ui': '1' });
        m.insertBefore(box, m.querySelector('h4'));
        var h = el('h4', { text: 'Thiết kế có sẵn của bộ công cụ' });
        m.insertBefore(h, box);
        j.designs.forEach(function (dz) {
          box.appendChild(el('div', { class: 'sah-lib', 'data-sah-ui': '1' }, [
            el('b', {}, [el('span', { text: dz.name }), el('small', { text: dz.desc || '' })]),
            el('button', { text: 'Dùng cách này', onclick: function () {
              var d = draft(), p = pageOf(d);
              d.pages[PAGE] = d.pages[PAGE] || { text: {}, hidden: [] };
              d.pages[PAGE].hidden = (dz.hidden || []).slice();
              DIRTY = true;
              saveDraft(d);
              repaint(true);
              closeModal();
              commitAll();
              toast('Đã đổi sang thiết kế “' + dz.name + '”.');
            } })
          ]));
        });
      })
      .catch(function () {});
  }

  /* ------------------------------------------------------ đăng nhập giáo viên */
  /* Giáo viên đăng nhập một lần; máy chủ trả cookie HttpOnly nên TRÌNH DUYỆT
     giữ phiên, không phải trang này — bí mật không nằm trong localStorage và
     không ai phải dán mã xuất bản nữa. Mã Bearer vẫn dùng được cho script,
     đặt trong mục “Nâng cao” của hộp thoại. */
  var SIGNED_IN = false;
  var SESSION_UNTIL = '';

  function apiHeaders(withBody) {
    var c = cfg(), h = {};
    if (withBody) h['Content-Type'] = 'application/json';
    if (!SIGNED_IN && c.token) h['Authorization'] = 'Bearer ' + c.token;
    return h;
  }

  function canWrite() { return SIGNED_IN || !!cfg().token; }

  function checkSession() {
    return fetch(apiUrl('/api/session') + '?_=' + Date.now(),
                 { cache: 'no-store', credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        SIGNED_IN = !!(j && j.signedIn);
        SESSION_UNTIL = (j && j.until) || '';
        updateBar();
        return SIGNED_IN;
      })
      .catch(function () { return false; });
  }

  /* ------------------------------------------------------------------ đăng nhập */
  /* Một ô duy nhất. Giáo viên không cần biết cookie, mã hay phiên là gì — chỉ
     cần biết "máy này đã đăng nhập hay chưa". Những thứ kỹ thuật (đổi máy chủ,
     mã cho script) vẫn còn nhưng giấu trong mục Nâng cao, dành cho người viết
     script chứ không dành cho giáo viên. */
  function openSettings() {
    var c = cfg();
    var pw = el('input', { type: 'password', autocomplete: 'current-password',
                           placeholder: 'Mật khẩu do tổ chuyên môn đặt' });
    var api = el('input', { type: 'text', value: c.api || '',
                            placeholder: 'Để trống nếu dùng máy chủ của trường' });
    var tok = el('input', { type: 'password', value: c.token || '',
                            placeholder: 'Mã xuất bản (chỉ cần cho script)' });
    var state = el('p', { class: 'sah-where' });
    var btnIn = el('button', { class: 'sah-save', text: '🔓 Đăng nhập' });
    var btnOut = el('button', { class: 'sah-cancel', text: 'Đăng xuất máy này' });

    function paint() {
      state.textContent = SIGNED_IN
        ? 'Máy này đã đăng nhập. Mọi thay đổi tự động đến tay học sinh.'
        : 'Máy này chưa đăng nhập. Học sinh chưa thấy thay đổi nào cho tới khi đăng nhập.';
      btnIn.style.display = SIGNED_IN ? 'none' : '';
      btnOut.style.display = SIGNED_IN ? '' : 'none';
    }

    btnIn.onclick = function () {
      var v = pw.value;
      if (!v) { toast('Hãy nhập mật khẩu.', true); return; }
      btnIn.disabled = true;
      btnIn.textContent = 'Đang đăng nhập…';
      fetch(apiUrl('/api/login'), {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: v })
      }).then(function (r) {
        return r.text().then(function (t) { return { ok: r.ok, status: r.status, body: t }; });
      }).then(function (r) {
        if (!r.ok) {
          var msg = '';
          try { msg = JSON.parse(r.body).error || ''; } catch (e) {}
          throw new Error(msg || ('máy chủ trả về ' + r.status));
        }
        pw.value = '';
        return checkSession();
      }).then(function (ok) {
        if (!ok) throw new Error('máy chủ nhận mật khẩu nhưng không lưu được phiên');
        paint();
        toast('Đã đăng nhập. Từ giờ máy này không phải nhập lại.');
        /* Đăng nhập xong thì đưa ngay những gì đang chờ lên — giáo viên sửa
           bài trước rồi mới đăng nhập là chuyện thường. */
        commitAll();
      }).catch(function (err) {
        toast('Không đăng nhập được: ' + err.message, true);
      }).then(function () {
        btnIn.disabled = false;
        btnIn.textContent = '🔓 Đăng nhập';
      });
    };

    btnOut.onclick = function () {
      fetch(apiUrl('/api/logout'), {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' }, body: '{}'
      }).catch(function () {}).then(function () {
        SIGNED_IN = false;
        SESSION_UNTIL = '';
        paint();
        setSaveState('offline');   // máy này không gửi được gì cho tới khi đăng nhập lại
        toast('Đã đăng xuất khỏi máy này.');
      });
    };

    var m = el('div', { class: 'sah-mcard', 'data-sah-ui': '1' }, [
      el('h3', { text: '🔐 Đăng nhập giáo viên' }),
      el('p', { text: 'Nhập mật khẩu của tổ chuyên môn một lần. Máy này sẽ nhớ, lần sau không phải nhập lại — và mọi thay đổi tự động đến tay học sinh.' }),
      state,
      el('label', {}, [el('span', { text: 'Mật khẩu' }), pw]),
      el('details', {}, [
        el('summary', { text: 'Nâng cao (không cần cho giáo viên)' }),
        el('label', {}, [el('span', { text: 'Địa chỉ máy chủ khác (bỏ trống = máy chủ này)' }), api]),
        el('label', {}, [el('span', { text: 'Mã xuất bản cho script' }), tok])
      ]),
      el('div', { class: 'sah-row' }, [
        btnIn, btnOut,
        el('button', { class: 'sah-save', text: 'Lưu cài đặt', onclick: function () {
          saveCfg({ api: norm(api.value), token: tok.value });
          toast('Đã lưu cài đặt.');
          checkSession().then(function (ok) { paint(); if (ok) commitAll(); });
        } }),
        el('button', { class: 'sah-cancel', text: 'Đóng' })
      ])
    ]);
    showModal(m);
    paint();
    checkSession().then(paint);
  }

  function showModal(card) {
    closeModal();
    var wrap = el('div', { 'data-sah-ui': '1', id: 'sahModal' }, [card]);
    wrap.addEventListener('click', function (ev) {
      if (ev.target === wrap) return closeModal();
      if (ev.target.classList && ev.target.classList.contains('sah-cancel')) closeModal();
    });
    D.body.appendChild(wrap);
    UI.modal = wrap;
  }
  function closeModal() { if (UI.modal) { UI.modal.remove(); UI.modal = null; } }

  /* ------------------------------------------------------- quay lại bản trước */

  /* --------------------------------------------------- bản lưu & quay lại */
  /* Xuất bản sai thì phải lùi được. Máy chủ đã giữ sẵn bản cũ trước mỗi lần
     ghi (xem write_store trong tools/content_api.py), nhưng trước đây bộ công
     cụ không có đường nào tới đó — giáo viên xuất bản nhầm là hết cách. Nút
     này mở đúng hai đường dẫn đã có: GET /api/content/history và
     POST /api/content/restore. */
  /* Ngày tháng theo kiểu người Việt đọc, không phải ISO. */
  function dateText(iso) {
    if (!iso) return 'không rõ ngày';
    var s = String(iso).slice(0, 10).split('-');
    return s.length === 3 ? s[2] + '/' + s[1] + '/' + s[0] : String(iso);
  }

  function whenText(iso) {
    if (!iso) return '(không rõ thời điểm)';
    var d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    try {
      return d.toLocaleString('vi-VN', { hour12: false }) + ' (giờ máy em)';
    } catch (e) { return iso; }
  }

  function openHistory() {
    if (!canWrite()) {
      toast('Cần đăng nhập giáo viên mới quay lại được bản trước.', true);
      openSettings();
      return;
    }
    var box = el('div', { 'data-sah-ui': '1' });
    box.appendChild(el('p', { class: 'sah-where', text: 'Đang tải…' }));
    var m = el('div', { class: 'sah-mcard', 'data-sah-ui': '1' }, [
      el('h3', { text: '🕘 Quay lại bản trước' }),
      el('p', { text: 'Chọn thời điểm muốn quay lại. Học sinh sẽ thấy đúng bài ở thời điểm đó, còn những gì đang sửa trên máy này sẽ được thay bằng bản đó.' }),
      box,
      el('div', { class: 'sah-row' }, [
        el('button', { class: 'sah-cancel', text: 'Đóng' })
      ])
    ]);
    showModal(m);

    fetch(apiUrl('/api/content/history') + '?_=' + Date.now(),
          { cache: 'no-store', credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        box.innerHTML = '';
        var items = (j && j.revisions) || [];
        if (!items.length) {
          box.appendChild(el('p', { class: 'sah-where', text: 'Chưa có bản nào để quay lại. Bản đầu tiên sẽ có sau lần sửa thứ hai.' }));
          return;
        }
        items.forEach(function (it) {
          var pages = (it.pages || []).length;
          var btn = el('button', { text: '↩️ Quay lại' });
          btn.onclick = function () { doRestore(it, btn); };
          box.appendChild(el('div', { class: 'sah-lib', 'data-sah-ui': '1' }, [
            el('b', {}, [
              el('span', { text: whenText(it.at) }),
              el('small', { text: pages > 1 ? 'gồm cả ' + pages + ' trang của bài' : 'bản trước của trang này' })
            ]),
            btn
          ]));
        });
      })
      .catch(function (err) {
        box.innerHTML = '';
        box.appendChild(el('p', { class: 'sah-where', text: 'Không tải được danh sách: ' + err.message }));
      });
  }

  function doRestore(rev, btn) {
    if (!canWrite()) { toast('Cần đăng nhập giáo viên.', true); openSettings(); return; }
    if (btn) { btn.disabled = true; btn.textContent = 'Đang quay lại…'; }
    lastUndo = null;
    fetch(apiUrl('/api/content/restore'), {
      method: 'POST',
      credentials: 'same-origin',
      headers: apiHeaders(true),
      body: JSON.stringify({ rev: rev.rev })
    }).then(function (r) {
      return r.text().then(function (t) { return { ok: r.ok, status: r.status, body: t }; });
    }).then(function (r) {
      if (!r.ok) throw new Error(r.status + ' ' + r.body.slice(0, 200));
      /* Đọc lại bản vừa khôi phục rồi coi đó là điểm xuất phát mới, để trang
         giáo viên thấy đúng những gì học sinh sẽ thấy. */
      return fetch(apiUrl('/api/content') + '?_=' + Date.now(),
                   { cache: 'no-store', credentials: 'same-origin' })
        .then(function (r2) { return r2.ok ? r2.json() : null; })
        .then(function (j) {
          if (j && j.pages) {
            writeJSON(K.cache, j);
            saveDraft({ v: 1, at: j.at || null, by: 'teacher', pages: j.pages });
          }
          repaint(true);
          closeModal();
          setSaveState('saved');
          toast('Đã quay lại bản trước. Học sinh mở trang là thấy bản này.');
        });
    }).catch(function (err) {
      if (btn) { btn.disabled = false; btn.textContent = '↩️ Quay lại'; }
      toast('Không quay lại được: ' + err.message, true);
    });
  }

  /* -------------------------------------------------- nhập bản sửa sahed cũ */
  /* Trước đây giáo viên đã sửa câu hỏi hotspot bằng công cụ `sahed` và những
     bản sửa đó nằm riêng trong máy. Chuyển chúng vào bản nháp của bộ công cụ
     mới để không mất công sức, và để lần này xuất bản được cho cả lớp. */
  function migrateSahed() {
    if (lsGet(K.seeded)) return 0;
    var old = readJSON('smart_art_heritage_hotspot_edits_v1', null);
    lsSet(K.seeded, '1');
    if (!old) return 0;
    var cards = [].slice.call(D.querySelectorAll('article.hot-card')).filter(function (c) {
      return c.querySelector('.sahed-tools');
    });
    var d = draft(), p = pageOf(d), moved = 0;
    cards.forEach(function (card, i) {
      var noEl = card.querySelector('.hot-no');
      var id = (noEl ? norm(noEl.textContent) : 'card') + '::' + i;
      var vals = old[id];
      if (!Array.isArray(vals)) return;
      var nodes = [].slice.call(card.querySelectorAll(
        'details .hot-content .logic,details .hot-content .know,details .hot-content .question'));
      nodes.forEach(function (elm, k) {
        if (typeof vals[k] !== 'string') return;
        var v = norm(vals[k]);
        if (!v) return;
        var t = null, c2 = elm.childNodes, j;
        for (j = 0; j < c2.length; j++) if (c2[j].nodeType === 3 && norm(c2[j].data)) { t = c2[j]; break; }
        if (!t) return;
        var f = fieldFor(t);
        if (!f || v === f.p) return;
        p.text[f.k] = { v: v, p: f.p, path: f.path, i: f.i, sec: f.sec, grp: f.grp, at: nowISO(), from: 'sahed' };
        moved++;
      });
    });
    if (moved) saveDraft(d);
    return moved;
  }

  /* --------------------------------------------------------------------- khởi động */

  function inStudio() {
    try {
      if (/[?&]studio=1/.test(location.search)) return true;
      if (location.hash === '#sah-studio') return true;
      if (lsGet('sah_role') === 'teacher' && lsGet('sah_content_studio_always') === '1') return true;
    } catch (e) {}
    return false;
  }

  var UNRESOLVED = [];

  function resolveReport() {
    var list = [];
    pending.forEach(function (e) { if (!findNode(e)) list.push(e.k); });
    UNRESOLVED = list;
    return list;
  }

  function boot() {
    addBaseStyles();
    /* 1. đắp ngay bản đã xuất bản đang nhớ trong máy (không nháy) */
    var cached = published();
    var first = applyAll(cached, false);
    guardOff();
    resolveReport();
    var moved = 0;
    try { moved = migrateSahed(); } catch (e) {}
    if (moved) DIRTY = true;    // bản sửa cũ vừa được mang sang: còn phải gửi đi

    if (inStudio()) {
      buildBar();
      ensureViewable();
      addStyles();
      D.body.classList.add('sah-studio');
      STUDIO_ON = true;
      ensureDraftSeeded();
      repaint(true);
      /* Máy nào đã đăng nhập thì nhớ luôn, không hỏi lại — và nếu còn thay đổi
         chưa đến tay học sinh (sửa lúc chưa đăng nhập, hoặc bản sửa cũ vừa
         được chuyển sang) thì đưa lên luôn, không bắt giáo viên bấm gì. */
      checkSession().then(afterSession);
    }

    /* 2. tải bản mới nhất từ máy chủ rồi đắp lại

       Phải đi qua repaint(): nó trả các ô đang mang bản CŨ về nội dung gốc rồi
       mới đắp bản mới. Nếu chỉ applyAll(bản mới) thì ô đang hiển thị giá trị đã
       xuất bản lần trước không khớp với "gốc" lẫn "giá trị mới", nên bị coi là
       không tìm thấy và trang giữ nguyên nội dung cũ mặc dù giáo viên đã xuất
       bản lần hai. */
    fetch(CONTENT_URL + '?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.pages) return;
        writeJSON(K.cache, j);
        if (STUDIO_ON) ensureDraftSeeded();
        repaint(true);
        resolveReport();
      })
      .catch(function () {});

    startObserver();
    repaint(true);

    if (moved && inStudio()) toast('Đã mang ' + moved + ' chỗ sửa cũ sang bộ công cụ này.');

    /* Đóng tab / chuyển trang khi hộp sửa đang mở: lưu ngay, đừng để mất chữ. */
    window.addEventListener('pagehide', function () {
      if (UI.editCommit) { try { UI.editCommit(); } catch (e) {} }
    });

    D.addEventListener('click', onClickDoc, true);
    D.addEventListener('mousemove', onHoverDoc, true);
    D.addEventListener('keydown', function (ev) {
      if (ev.shiftKey && (ev.metaKey || ev.ctrlKey) && (ev.key === 'E' || ev.key === 'e')) {
        ev.preventDefault(); toggleStudio(!STUDIO_ON);
      }
      if (ev.key === 'Escape') { closeEditor(); closeModal(); }
    });
  }

  /* API nhỏ để kiểm tra / dùng từ ngoài */
  window.SAHContent = {
    page: PAGE,
    fields: function () { return refreshFields(); },
    draft: draft,
    published: published,
    saveDraft: saveDraft,
    store: function () { return activeStore(); },
    ensureDraftSeeded: ensureDraftSeeded,
    resetApplied: resetApplied,
    applyAll: applyAll,
    repaint: repaint,
    unresolved: function () { return resolveReport(); },
    studio: function (on) { toggleStudio(on); },
    bar: function () { return UI.bar; },
    history: openHistory,
    restore: doRestore,
    settings: openSettings,
    checkSession: checkSession,
    signedIn: function () { return SIGNED_IN; },
    editField: editField,
    /* Dùng cho kiểm tra tự động: lưu + đưa lên ngay, không cần bấm nút nào. */
    save: commitAll,
    undo: undoLast,
    more: openMore,
    saveState: function () { return SAVE_STATE; },
    setStudioAlways: function (on) {
      if (on) lsSet('sah_content_studio_always', '1'); else lsSet('sah_content_studio_always', '0');
    },
    migrateSahed: migrateSahed
  };

  /* Chạy sớm nhất có thể: nếu đã có bản nhớ trong máy thì ẩn trước các khối có
     bản sửa để không nháy nội dung cũ. */
  try {
    var early = PAGE === 'index' || PAGE === 'trien-lam' ? published() : null;
    if (early) guardOn(early);
  } catch (e) {}

  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
