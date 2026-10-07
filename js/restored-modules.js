/* ============================================================================
   RESTORED MODULES for the V3.11 clone
   Brings back everything the reference layout dropped, and — critically —
   bridges the clone's own storage into the keys the teacher admin page reads,
   so giao-vien.html can finally see real student work.

   Bridge contracts (verified against giao-vien.html / trien-lam.html):
     sah_student_works : Array<{id,kind,title,studentId,studentClass,heritage,
                               note,dataUrl,fileName,bytes,createdAt,dataset}>
     sah_work_grades   : { [workId]: {...} }
     sah_321_draft     : {project,q1,q2,q3,studentId,studentClass,updatedAt}
     sah_321_feedback  : { "321": text, "321_at": iso }
   ========================================================================== */
(function () {
  'use strict';

  var K = {
    role: 'sah_role', cfg: 'sah_chatgpt_cfg', fb: 'sah_321_feedback',
    works: 'sah_student_works', grades: 'sah_work_grades',
    draft: 'sah_321_draft', prog: 'sah_task_progress', session: 'sah_teacher_session',
    sessionSS: 'sah_teacher_session', chatHist: 'rm_chat_history'
  };

  var ORDER = ['phohien', 'chuakeo', 'dentran', 'lequydon', 'dongxam'];
  var DEFAULT_KEY = ORDER[0];
  var NAMES = {
    phohien: 'Phố Hiến', chuakeo: 'Chùa Keo', dentran: 'Đền Trần',
    lequydon: 'Khu lưu niệm Lê Quý Đôn', dongxam: 'Làng nghề chạm bạc Đồng Xâm'
  };

  function $(id) { return document.getElementById(id); }
  function qsa(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function jget(k, fb) { try { return JSON.parse(get(k)) || fb; } catch (e) { return fb; } }
  function jset(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function txt(el, s) { if (el) el.textContent = s == null ? '' : s; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function today() { return new Date().toLocaleDateString('vi-VN'); }

  /* the dossier the student is working on right now */
  function curKey() {
    var s = $('sahProjectSelect');
    return (s && s.value && ORDER.indexOf(s.value) >= 0) ? s.value : DEFAULT_KEY;
  }
  /* a gói holds work once any of its three answers is filled, in the sheet or
     in the Kho */
  function packWork(h, i) {
    for (var q = 1; q <= 3; q++) {
      if ((get('sah321-integrated-' + h + '-' + i + '-' + q) || '').trim()) return true;
      if ((get('sah321-bank-answer-' + h + '-' + i + '-' + q) || '').trim()) return true;
    }
    return false;
  }
  /* The sheet and the Kho both store the gói index 0-based, so a saved index is
     0-based too: reading 1..4 as "1-based" shifted gói 2..5 onto gói 1..4 and
     hid the answers the student had just written. Prefer a gói that holds work
     so a stale index can never hide it. */
  function curPack() {
    var h = curKey(), i = 0, found = false, j;
    for (j = 0; j < 5; j++) if (packWork(h, j)) { i = j; found = true; }
    var n = parseInt(get('sah321-integrated-pack-' + h), 10);
    if (!isNaN(n)) {
      n = Math.max(0, Math.min(4, n));
      if (packWork(h, n) || !found) i = n;
    }
    return i;
  }
  /* one 3-2-1 answer, wherever the student wrote it: the sheet, the Kho, or the
     per-project phiếu */
  function integrated(q) {
    var h = curKey(), p = curPack();
    return (get('sah321-integrated-' + h + '-' + p + '-' + q) || '').trim()
      || (get('sah321-bank-answer-' + h + '-' + p + '-' + q) || '').trim()
      || (get('sah321-integrated-' + h + '-0-' + q) || '').trim()
      || (get('direct321-' + h + '-' + q) || '').trim();
  }
  function artwork() { return jget('sah-art-v33-' + curKey(), {}) || {}; }

  /* ======================================================== role + identity */
  function role() { return get(K.role) || ''; }
  function profile() {
    var p = (jget(K.prog, {}) || {})._profile;
    return (p && p.name) ? p : { name: '', id: '', cls: '' };
  }

  /* The nav is sticky and wraps to a different number of rows per width and
     role, so anchor targets read their offset from its measured height. */
  function syncNavHeight() {
    var n = document.querySelector('.rm-topnav'); if (!n) return;
    document.documentElement.style.setProperty('--rm-navh',
      Math.round(n.getBoundingClientRect().height) + 'px');
  }

  function renderRole() {
    var r = role(), p = profile();
    txt($('rmRoleChip'), r === 'student' ? ('🎓 ' + (p.name || 'Học sinh'))
      : r === 'teacher' ? '👩‍🏫 Giáo viên'
      : r === 'guest' ? '👀 Khách' : '— chưa chọn vai trò —');
    txt($('rmIdentityChip'), p.name ? (p.name + ' • ' + p.id + ' • ' + p.cls) : '');
    document.body.classList.toggle('role-student', r === 'student');
    document.body.classList.toggle('role-teacher', r === 'teacher');
    document.body.classList.toggle('role-guest', r === 'guest');
    var student = r === 'student';
    ['sahSave321', 'sahToAI5A', 'skvSave', 'avSave', 'ex38Save', 'rmSaveWork'].forEach(function (id) {
      var el = $(id); if (el) el.style.display = student ? '' : 'none';
    });
    syncNavHeight();
  }

  function openGate() {
    var g = $('roleGate'); if (!g) return;
    g.hidden = false; $('rgChoices').hidden = false; $('rgStudentForm').hidden = true;
  }
  function closeGate() { var g = $('roleGate'); if (g) g.hidden = true; }

  function setStudent(name, id, cls) {
    var p = jget(K.prog, {}); p._profile = { name: name, id: id, cls: cls };
    jset(K.prog, p); set(K.role, 'student');
    closeGate(); renderRole(); syncDraft(); refreshLocks();
  }

  /* ================================================== 3-2-1 -> teacher page */
  /* The teacher worksheet view reads sah_321_draft. Mirror the clone's own
     per-pack answers into it so the admin page sees the live sheet. */
  function syncDraft() {
    var p = profile();
    jset(K.draft, {
      project: curKey(), q1: integrated(1), q2: integrated(2), q3: integrated(3),
      studentId: p.id || '', studentClass: p.cls || '', updatedAt: new Date().toISOString()
    });
  }

  /* ================================================ artwork -> gallery/admin */
  function currentArtworkImage() {
    // the clone never stores the file itself, so re-read the blob the student
    // picked in the art table / exhibit step if it is still in sessionStorage
    try {
      var raw = sessionStorage.getItem('rm_artwork_image');
      if (raw) return raw;
    } catch (e) {}
    return null;
  }

  function saveWork() {
    var p = profile(), ar = artwork(), ex = jget('sah-ex38-' + curKey(), {}) || {};
    if (!ar.title && !ar.message && !ar.core) { alert('Em điền thêm thông tin tác phẩm trước nhé.'); return; }
    var img = currentArtworkImage();
    if (!img) {
      alert('Chưa có ảnh tác phẩm. Em tải ảnh ở Bàn thực hành hoặc Trưng bày trước khi lưu vào triển lãm.');
      return;
    }
    var list = jget(K.works, []); if (!Array.isArray(list)) list = [];
    var id = 'w-' + Date.now();
    list.push({
      id: id, kind: 'image',
      title: ar.title || ex.title || 'Tác phẩm chưa đặt tên',
      studentId: p.id || '', studentClass: p.cls || '',
      heritage: curKey(), note: ar.message || ex.message || '',
      dataUrl: img, fileName: '', bytes: Math.round(img.length * 0.75),
      createdAt: today(), dataset: 'sah-art-v33-' + curKey()
    });
    jset(K.works, list);
    renderGallery();
    txt($('rmWorkMsg'), '✓ Đã lưu vào Triển lãm. Giáo viên đã thấy tác phẩm này.');
  }

  /* ==================================================== teacher -> student */
  function renderFeedback() {
    var box = $('teacherFeedbackBox'); if (!box) return;
    var map = jget(K.fb, {}) || {};
    var t = (map['321'] || '').trim();
    box.hidden = !t;
    if (t) {
      box.innerHTML = '<div class="rmfb-head">📮 Nhận xét của giáo viên'
        + (map['321_at'] ? ' <small>' + esc(new Date(map['321_at']).toLocaleString('vi-VN')) + '</small>' : '')
        + '</div><div class="rmfb-text">' + esc(t) + '</div>';
    }
  }

  /* ============================================================== gallery */
  function works() { var w = jget(K.works, []); return Array.isArray(w) ? w : []; }
  function gradeOf(w) { return (jget(K.grades, {}) || {})[w.id] || null; }

  function renderGallery() {
    var grid = $('rmGallery'); if (!grid) return;
    var q = (($('rmSearch') || {}).value || '').trim().toLowerCase();
    var hf = ($('rmFilter') || {}).value || '';
    var all = works().slice().reverse();
    var list = all.filter(function (w) {
      if (hf && w.heritage !== hf) return false;
      if (!q) return true;
      return ((w.title || '') + ' ' + (w.studentId || '') + ' ' + (w.studentClass || '') + ' ' + (w.note || ''))
        .toLowerCase().indexOf(q) >= 0;
    });

    txt($('rmGalleryEmpty'), list.length ? '' : 'Chưa có tác phẩm nào. Em làm xong tác phẩm rồi bấm “Lưu vào Triển lãm”.');
    grid.innerHTML = list.map(function (w) {
      var g = gradeOf(w);
      return '<figure class="rm-card" data-id="' + esc(w.id) + '">'
        + '<img loading="lazy" src="' + esc(w.dataUrl) + '" alt="' + esc(w.title) + '">'
        + '<figcaption><b>' + esc(w.title) + '</b>'
        + '<small>' + esc(NAMES[w.heritage] || w.heritage || '') + ' • ' + esc(w.studentId || '') + ' • ' + esc(w.createdAt || '') + '</small>'
        + (g ? '<em class="rm-chip">Đã chấm: ' + esc(g.score != null ? g.score : 'xem nhận xét') + '</em>' : '')
        + '</figcaption></figure>';
    }).join('');

    var st = $('rmStats');
    if (st) {
      var n = all.length;
      var students = {}; all.forEach(function (w) { if (w.studentId) students[w.studentId] = 1; });
      var graded = all.filter(function (w) { return !!gradeOf(w); }).length;
      st.innerHTML = '<span><b>' + n + '</b> tác phẩm</span>'
        + '<span><b>' + Object.keys(students).length + '</b> học sinh</span>'
        + '<span><b>' + graded + '</b> đã chấm</span>';
    }
  }

  function openLightbox(w) {
    var lb = $('rmLightbox'); if (!lb) return;
    txt($('rmLbTitle'), w.title || '');
    txt($('rmLbMeta'), [NAMES[w.heritage] || '', w.studentId || '', w.studentClass || '', w.createdAt || '']
      .filter(Boolean).join(' • '));
    txt($('rmLbNote'), w.note || '');
    var g = gradeOf(w);
    var fb = $('rmLbGrade');
    if (g) { fb.hidden = false; fb.innerHTML = '<b>Điểm: ' + esc(g.score != null ? g.score : '—') + '</b><br>' + esc(g.feedback || ''); }
    else fb.hidden = true;
    var img = $('rmLbImg'); img.src = w.dataUrl || ''; img.alt = w.title || '';
    lb.hidden = false;
  }

  /* ============================================================ AI chat */
  function cfg() { return jget(K.cfg, {}) || {}; }
  function cfgReady() { var c = cfg(); return !!(c.baseUrl && c.apiKey && c.model); }

  function bubble(who, content) {
    var h = $('rmChatHistory'); if (!h) return;
    var d = document.createElement('div');
    d.className = 'rm-bubble rm-' + who; d.textContent = content;
    h.appendChild(d); h.scrollTop = h.scrollHeight;
  }

  function sheetContext() {
    var p = profile();
    return 'Di sản: ' + NAMES[curKey()]
      + '\nHọc sinh: ' + (p.name || 'ẩn danh') + (p.cls ? ' • lớp ' + p.cls : '')
      + '\nGói 3-2-1 đang mở: ' + (curPack() + 1) + '/5'
      + '\n3 – Khám phá: ' + integrated(3)
      + '\n2 – Lựa chọn: ' + integrated(2)
      + '\n1 – Ý tưởng: ' + (integrated(1) || get('sah-ai5a-seed-' + curKey()) || '');
  }

  function sendChat() {
    var input = $('rmChatInput'); if (!input) return;
    var q = (input.value || '').trim(); if (!q) return;
    input.value = ''; bubble('me', q);
    if (!cfgReady()) { openCfg('Chưa cấu hình AI trên máy này.'); return; }
    var c = cfg();
    var hist = jget(K.chatHist, []); if (!Array.isArray(hist)) hist = [];
    hist.push({ role: 'user', content: q }); hist = hist.slice(-12);
    bubble('ai', '…');

    fetch(String(c.baseUrl).replace(/\/+$/, '') + '/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + c.apiKey },
      body: JSON.stringify({
        model: c.model, temperature: 0.7,
        messages: [
          { role: 'system', content: 'Em là trợ lý gợi mở Mĩ thuật cho học sinh THCS. '
            + 'Hãy đặt câu hỏi và gợi mở, KHÔNG làm thay học sinh. Trả lời tiếng Việt, ngắn gọn.\n'
            + sheetContext() },
          { role: 'user', content: q }
        ]
      })
    }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (r) {
        var last = $('rmChatHistory').lastElementChild;
        if (last && last.classList.contains('rm-ai')) last.remove();
        if (!r.ok) { bubble('ai', '⚠️ ' + ((r.j && r.j.error && r.j.error.message) || 'Không gọi được AI.')); return; }
        var m = (r.j.choices && r.j.choices[0] && r.j.choices[0].message && r.j.choices[0].message.content) || '';
        hist.push({ role: 'assistant', content: m }); jset(K.chatHist, hist.slice(-12));
        bubble('ai', m);
      }).catch(function (e) {
        var last = $('rmChatHistory').lastElementChild;
        if (last && last.classList.contains('rm-ai')) last.remove();
        bubble('ai', '⚠️ Lỗi mạng: ' + e.message);
      });
  }

  function openCfg(note) {
    var m = $('rmCfgModal'); if (!m) return;
    var c = cfg();
    $('rmCfgBase').value = c.baseUrl || 'https://api.openai.com/v1';
    $('rmCfgKey').value = c.apiKey || '';
    $('rmCfgModel').value = c.model || 'gpt-4o-mini';
    txt($('rmCfgNote'), note || 'Khóa lưu ngay trên máy này, không gửi đi đâu khác.');
    m.hidden = false;
  }

  /* ======================================================== 3-2-1 export */
  function export321() {
    var p = profile();
    var lines = [
      'SMART ART HERITAGE – PHIẾU 3–2–1',
      'Học sinh: ' + (p.name || '') + ' | Mã: ' + (p.id || '') + ' | Lớp: ' + (p.cls || ''),
      'Di sản: ' + NAMES[curKey()] + ' | Gói ' + (curPack() + 1) + '/5 | ' + today(),
      '', '3 – KHÁM PHÁ', integrated(3),
      '', '2 – LỰA CHỌN & SUY NGHĨ', integrated(2),
      '', '1 – Ý TƯỞNG SÁNG TẠO CÁ NHÂN', integrated(1)
    ];
    var fb = (jget(K.fb, {}) || {})['321'];
    if (fb) lines.push('', '--- NHẬN XÉT CỦA GIÁO VIÊN ---', fb);
    var blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'phieu-3-2-1-' + curKey() + '-' + today() + '.txt';
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
    txt($('rmExportMsg'), '✓ Đã tải phiếu.');
  }

  /* The reference ships five independent project selects that can disagree.
     Driving them all from the dossier choice keeps the bridged work filed
     under the heritage the student is actually looking at. */
  var PROJECT_SELECTS = ['sahProjectSelect', 'studioProject', 'skvProject', 'avProject', 'ex38Project', 'j39p'];
  function selectHeritage(key) {
    PROJECT_SELECTS.forEach(function (id) {
      var sel = $(id); if (!sel) return;
      if (id === 'j39p') { if (sel.selectedIndex !== ORDER.indexOf(key)) sel.selectedIndex = ORDER.indexOf(key); }
      else if (ORDER.indexOf(sel.value) !== ORDER.indexOf(key)) { sel.value = key; }
      else return;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }

  /* ============================================================ step lock */
  var STEPS = [
    ['sah321-integrated', 'Phiếu 3–2–1'], ['sah-ai5a-studio', 'AI 5A'],
    ['sketchV25', 'Xưởng phác thảo'], ['artV33', 'Tác phẩm'],
    ['exhibitV38', 'Trưng bày'], ['journey39', 'Hồ sơ hành trình']
  ];

  function unlockedThrough() {
    var k = curKey(), open = 0;
    var prog = jget(K.prog, {}); if (prog[k] && prog[k].dossier) open = 1;
    if (open >= 1 && integrated(1).trim()) open = 2;
    if (open >= 2 && get('sah-ai5a-studio-' + k + '-confirm') === '1') open = 3;
    if (open >= 3 && (jget('sah-sketch-v25-' + k, {}) || {}).confirm) open = 4;
    if (open >= 4 && (jget('sah-art-v33-' + k, {}) || {}).confirm) open = 5;
    if (open >= 5 && (jget('sah-ex38-' + k, {}) || {}).confirm) open = 6;
    return open;
  }

  function markDossier() {
    var p = jget(K.prog, {}), k = curKey();
    if (!p[k]) p[k] = {};
    p[k].dossier = true; jset(K.prog, p); refreshLocks();
  }

  /* A locked section must say why it is locked and how to get there, otherwise
     a dimmed page just reads as broken. The badge lives inside the section so
     the explanation travels with the content it explains. */
  function ensureLockBadge(sec) {
    var badge = sec.querySelector('.rm-lockbadge');
    if (badge) return badge;
    badge = document.createElement('div');
    badge.className = 'rm-lockbadge';
    badge.setAttribute('role', 'note');
    badge.innerHTML =
      '<span class="rm-lockico" aria-hidden="true">🔒</span>' +
      '<span class="rm-lockbody">' +
        '<b>Chặng này chưa mở</b>' +
        '<span class="rm-lockmsg"></span>' +
        '<a class="rm-btn sm ghost rm-lockgo" href="#' + STEPS[0][0] + '"></a>' +
      '</span>';
    sec.insertBefore(badge, sec.firstChild);
    return badge;
  }

  function refreshLocks() {
    var isStudent = role() === 'student';        // only students get the lock
    var open = isStudent ? unlockedThrough() : STEPS.length;
    var here = Math.min(open, STEPS.length - 1);
    STEPS.forEach(function (s, i) {
      var sec = $(s[0]); if (!sec) return;
      var unlocked = !isStudent || (i + 1) <= open + 1;
      sec.classList.toggle('rm-locked', !unlocked);
      var badge = ensureLockBadge(sec);
      badge.hidden = unlocked;
      if (!unlocked) {
        var prev = STEPS[i - 1];
        txt(badge.querySelector('.rm-lockmsg'),
          'Mở khoá sau khi em hoàn thành chặng trước: ' + (prev ? prev[1] : STEPS[0][1]) + '.');
        var go = badge.querySelector('.rm-lockgo');
        go.href = '#' + STEPS[here][0];
        txt(go, '→ Về chặng đang làm: ' + STEPS[here][1]);
      }
      // CSS mutes a locked section for the mouse; inert also takes it out of the
      // tab order so a student cannot type into a step that is not open yet.
      Array.prototype.forEach.call(sec.children, function (child) {
        var tag = child.tagName;
        if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'TEMPLATE') return;
        if (child.classList.contains('rm-lockbadge')) return;
        if (unlocked) child.removeAttribute('inert');
        else child.setAttribute('inert', '');
      });
    });
    var bar = $('rmLockStatus');
    if (bar) {
      // The student must finish the first stage they have not completed; that
      // is what opens the next one. `open` counts finished stages, so the stage
      // to complete is the one at open-1 (open+1 announced a step two ahead).
      var todo = STEPS[Math.max(0, open - 1)];
      txt(bar, !isStudent ? '' : (open >= STEPS.length
        ? '✓ Em đã mở hết các chặng của hồ sơ này.'
        : 'Chặng kế tiếp mở khi em hoàn thành: ' + todo[1]));
    }
  }

  /* ================================================== artwork image capture */
  function wireImageCapture() {
    // the clone previews files via object URLs and never persists them, so grab
    // the bytes once at save time to hand the gallery a real dataUrl
    [['#avFinalFile', 'rm_artwork_image'], ['#skvFinalFile', 'rm_artwork_image']]
      .forEach(function (pair) {
        var inp = $(pair[0][1]); if (!inp) return;
        inp.addEventListener('change', function () {
          var f = inp.files && inp.files[0]; if (!f) return;
          var r = new FileReader();
          r.onload = function () { try { sessionStorage.setItem(pair[1], r.result); } catch (e) {} };
          r.readAsDataURL(f);
        });
      });
  }

  /* ================================================================ init */
  function init() {
    var choices = $('rgChoices');
    if (choices) choices.addEventListener('click', function (e) {
      var b = e.target.closest('.rm-choice'); if (!b) return;
      var r = b.dataset.role;
      if (r === 'student') {
        choices.hidden = true; $('rgStudentForm').hidden = false;
        var p = profile();
        $('rmName').value = p.name || ''; $('rmStudentId').value = p.id || ''; $('rmClass').value = p.cls || '';
        $('rmName').focus(); return;
      }
      set(K.role, r);
      closeGate(); renderRole(); refreshLocks();
      // the admin page owns its own auth gate; do not fabricate a session
      if (r === 'teacher') window.location.href = 'giao-vien.html';
    });

    var back = $('rmStudentBack');
    if (back) back.onclick = function () { $('rgStudentForm').hidden = true; choices.hidden = false; };

    var start = $('rmStudentStart');
    if (start) start.onclick = function () {
      var n = ($('rmName').value || '').trim(), i = ($('rmStudentId').value || '').trim(), c = ($('rmClass').value || '').trim();
      if (!n || !i || !c) { txt($('rmErr'), 'Hãy điền đủ họ tên, mã học sinh và lớp nhé!'); return; }
      setStudent(n, i, c);
    };
    ['rmName', 'rmStudentId', 'rmClass'].forEach(function (id) {
      var el = $(id); if (!el) return;
      el.addEventListener('keydown', function (e) { if (e.key === 'Enter' && start) start.click(); });
    });

    var sw = $('rmRoleSwitch'); if (sw) sw.onclick = openGate;

    // gallery
    var search = $('rmSearch'); if (search) search.addEventListener('input', renderGallery);
    var filter = $('rmFilter'); if (filter) filter.addEventListener('change', renderGallery);
    var grid = $('rmGallery');
    if (grid) grid.addEventListener('click', function (e) {
      var f = e.target.closest('.rm-card'); if (!f) return;
      var w = works().filter(function (x) { return x.id === f.dataset.id; })[0];
      if (w) openLightbox(w);
    });
    var lbClose = $('rmLbClose'); if (lbClose) lbClose.onclick = function () { $('rmLightbox').hidden = true; };

    var sw2 = $('rmSaveWork'); if (sw2) sw2.onclick = saveWork;
    var exp = $('rmExport321'); if (exp) exp.onclick = export321;

    // chat
    var send = $('rmSend'); if (send) send.onclick = sendChat;
    var ci = $('rmChatInput');
    if (ci) ci.addEventListener('keydown', function (e) { if (e.key === 'Enter') sendChat(); });
    var cb = $('rmCfgBtn'); if (cb) cb.onclick = function () { openCfg(''); };
    var cc = $('rmCfgClose'); if (cc) cc.onclick = function () { $('rmCfgModal').hidden = true; };
    var cs = $('rmCfgSave');
    if (cs) cs.onclick = function () {
      jset(K.cfg, {
        baseUrl: ($('rmCfgBase').value || '').trim(), apiKey: ($('rmCfgKey').value || '').trim(),
        model: ($('rmCfgModel').value || '').trim()
      });
      $('rmCfgModal').hidden = true;
      txt($('rmCfgStatus'), cfgReady() ? '✓ Đã lưu cấu hình AI trên máy này' : 'Thiếu: cần đường dẫn, khóa và mô hình.');
    };
    var hist = jget(K.chatHist, []);
    if (Array.isArray(hist)) hist.forEach(function (m) { bubble(m.role === 'user' ? 'me' : 'ai', m.content); });
    txt($('rmCfgStatus'), cfgReady() ? '✓ Đã có cấu hình AI' : 'Chưa cấu hình AI trên máy này');

    // 3D room: boot three.js (600 KB) only when opened. The CTA overlays the
    // iframe, so listen on both.
    var frame = $('rm3dFrame'), cta = $('rm3dCta');
    var bootRoom = function () {
      if (!frame || frame.dataset.loaded) return;
      frame.dataset.loaded = '1';
      frame.src = 'models.html';
      if (cta) cta.hidden = true;
    };
    if (frame) frame.addEventListener('click', bootRoom, { once: true });
    if (cta) cta.addEventListener('click', bootRoom, { once: true });

    // keep the teacher worksheet in sync
    var save321 = $('sahSave321'); if (save321) save321.addEventListener('click', function () { syncDraft(); markDossier(); });
    // opening a dossier counts as finishing the discovery step
    ['h1', 'h2', 'h3', 'h4', 'h5'].forEach(function (id, i) {
      var r = $(id); if (!r) return;
      r.addEventListener('change', function () {
        markDossier();
        selectHeritage(ORDER[i]);
        syncDraft(); renderGallery();
      });
    });
    var ps = $('sahProjectSelect'); if (ps) ps.addEventListener('change', function () { syncDraft(); refreshLocks(); });

    wireImageCapture();

    window.addEventListener('storage', function (e) {
      if (e.key === K.fb) renderFeedback();
      if (e.key === K.works || e.key === K.grades) renderGallery();
    });

    // A stage must open the moment the student finishes the one before it.
    // The stages save themselves on change/click, so re-read on the same events
    // (debounced, capture phase, so the section's own handler has already run)
    // instead of making the student wait for the next poll.
    var lockTick = null;
    function soonLocks() {
      if (lockTick) return;
      lockTick = setTimeout(function () { lockTick = null; refreshLocks(); }, 80);
    }
    document.addEventListener('change', soonLocks, true);
    document.addEventListener('click', soonLocks, true);

    renderRole(); renderFeedback(); renderGallery(); refreshLocks();
    if (!role()) openGate(); else closeGate();
    // backstop: the lock must also clear when another tab switches the role
    setInterval(refreshLocks, 4000);
    syncNavHeight();
    window.addEventListener('resize', syncNavHeight);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  window.rmRestored = {
    role: role, profile: profile, works: works, syncDraft: syncDraft, saveWork: saveWork,
    renderGallery: renderGallery, renderFeedback: renderFeedback,
    unlockedThrough: unlockedThrough, refreshLocks: refreshLocks,
    selectHeritage: function (k) { if (ORDER.indexOf(k) < 0) return; selectHeritage(k); }
  };
})();
