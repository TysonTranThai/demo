#!/usr/bin/env python3
"""
Build index.html from the team's newest master, "new 9_10_2026.html".

That master is a superset of SMART_ART_HERITAGE_V3_11_RASOAT_HE_THONG.html: it
adds the sahed hotspot content editor, the #p321V312 worksheet section, the
AI 5A direct-content patch and the native <details> help blocks — and it
already carries two repairs this build used to apply itself (the truncated
sketch script, and the AI 5A call into a private refreshProjectHelp()).
Everything the master still gets wrong or loses is repaired below.

Transformations (everything else is byte-identical to the reference):
  1. The 155 inline data: base64 images -> the byte-identical real files in assets/extracted/
  2. Remove <section id="auditV311"> ... </section>          (user decision: leave it out)
  3. Restore what the master's scripts still lose, and prove on every build that
     the fixes it carries are actually present (see REPAIRS and CHECKS below)
  4. Append one new script that wires #journey39 to the real localStorage data
"""
import base64
import hashlib
import json
import os
import re
import sys

ROOT = "/Users/tysontran/Desktop/Smart Art Heritage"
# The team's 2026-10-09 master. Keep it in the tree under this exact name (or
# update REF here) — the build fails loudly if it is missing.
REF = os.path.join(ROOT, "new 9_10_2026.html")
OUT = os.path.join(ROOT, "index.html")

if not os.path.isfile(REF):
    sys.exit(
        "Missing the build source:\n  %s\n"
        "index.html is generated from it — restore the file (or point REF at the\n"
        "right master in tools/build_index.py) and run this again." % REF
    )

# --------------------------------------------------------------------------
# 1. base64 -> real asset paths
# --------------------------------------------------------------------------
src = open(REF, encoding="utf-8").read()

h2f = {}
ex = os.path.join(ROOT, "assets", "extracted")
for f in sorted(os.listdir(ex)):
    p = os.path.join(ex, f)
    if os.path.isfile(p):
        h2f.setdefault(hashlib.md5(open(p, "rb").read()).hexdigest(), set()).add(f)

meta = json.load(open(os.path.join(ROOT, "assets", "heritage_complete.json")))
expected = []
for k in meta:
    v = meta[k]
    expected += [v["cover"]] + [p["image"] for p in v["photos_list"]] + [h["image"] for h in v["hotspots"]]


def swap(m):
    h = hashlib.md5(base64.b64decode(m.group(1))).hexdigest()
    if h not in h2f:
        sys.exit("base64 blob has no matching file in assets/extracted/")
    return 'src="%s"' % m.group(2)


# verify the blob order equals the JSON order before substituting
blobs = re.findall(r'src="data:image/[a-z]+;base64,([A-Za-z0-9+/=]+)"', src)
assert len(blobs) == len(expected) == 155, (len(blobs), len(expected))
for i, (b, e) in enumerate(zip(blobs, expected)):
    assert os.path.basename(e) in h2f[hashlib.md5(base64.b64decode(b)).hexdigest()], (i, e)

it = iter(expected)
src = re.sub(
    r'src="data:image/([a-z]+);base64,([A-Za-z0-9+/=]+)"',
    lambda m: 'src="%s"' % next(it),
    src,
)
assert "base64," not in src, "leftover base64"

# --------------------------------------------------------------------------
# 2. remove #auditV311
# --------------------------------------------------------------------------
start = src.index('<section id="auditV311">')
end = src.index("</section>", start) + len("</section>")
removed = src[start:end]
assert removed.count("<section") == 1 and "au311-table" in removed
src = src[:start] + src[end:]

# 2b. the audit section's own <style> block (style13 is entirely its CSS)
m = [x for x in re.finditer(r'<style[^>]*>(.*?)</style>', src, re.S) if "au311" in x.group(1)]
assert len(m) == 1, "expected exactly one audit style block, got %d" % len(m)
assert all(k in m[0].group(1) for k in ("#auditV311", ".au311-table", ".au311-grid"))
aum = m[0]
src = src[: aum.start()] + src[aum.end() :]
assert "auditV311" not in src and "au311" not in src, "audit leftovers remain"
print("  removed #auditV311 section (%d B) and its style block (%d B)" % (len(removed), len(aum.group(0))))

# --------------------------------------------------------------------------
# 3. minimal repairs to the reference's own scripts
# --------------------------------------------------------------------------
REPAIRS = 0


def patch(old, new, why, count=1):
    """Replace `old` with `new`; fail loudly if the reference no longer matches."""
    global src, REPAIRS
    n = src.count(old)
    assert n == count, "expected %d occurrence(s) of %r, found %d" % (count, old[:70], n)
    src = src.replace(old, new)
    REPAIRS += 1
    print("  repair %d: %s" % (REPAIRS, why))


def expect(cond, why):
    """Prove something the reference must already carry; fail the build if not."""
    assert cond, "reference check failed: %s" % why
    print("  ok: %s" % why)


# 3a. script7 (Xương phác thảo, stage 4): the markup still has the three
#     <div class="skv-option"> cards and the CSS still styles .skv-option.chosen,
#     but this master's rewrite of the script dropped the handler that ever set
#     that class — so tapping "THỬ 1/2/3" no longer marks the chosen attempt.
#     Restore it right after the field listeners, where the previous reference had
#     (a truncated version of) it.
patch(
    'root.querySelectorAll("[data-f]").forEach(x=>x.addEventListener("input",save));\n'
    'confirm.addEventListener("change",save); P.addEventListener("change",()=>{load();refreshProjectHelp();});\n',
    'root.querySelectorAll("[data-f]").forEach(x=>x.addEventListener("input",save));\n'
    'confirm.addEventListener("change",save); P.addEventListener("change",()=>{load();refreshProjectHelp();});\n'
    'root.querySelectorAll(".skv-option").forEach(b=>b.addEventListener("click",()=>{'
    'root.querySelectorAll(".skv-option").forEach(x=>x.classList.remove("chosen"));'
    'b.closest(".skv-option").classList.add("chosen");save();}));\n',
    "sketchV25: restore the .skv-option 'chosen' selection the rewrite dropped",
)

# 3b. script8 (Bàn thực hành, stage 5): orphan tail of a help-toggle loop over
#     ".av-help", a class that no longer exists in the markup (the module now
#     uses native <details class="av-help-native">, which needs no JS).
patch(
    'P.addEventListener("change",load);\n'
    'b.textContent=h.classList.contains("open")?"Thu gọn gợi ý":"\U0001f4a1 Cần trợ giúp? Mở gợi ý";});\n',
    'P.addEventListener("change",load);\n',
    "artV33: drop the orphan .av-help toggle tail (its target class no longer exists)",
)

# 3c. script6 (AI 5A A1) used to call refreshProjectHelp() from outside script7's
#     closure, which threw before its own load(). This master already guards the
#     call, so only prove the guard survived.
expect(
    'if(typeof refreshProjectHelp === "function")' in src
    and 'setTimeout(load,30));refreshProjectHelp();\nload();' not in src,
    "ai5a A1: the help call is guarded, so load() still renders the A1 questions",
)

# 3d. the reference's own pack-context banner treated the saved gói index as
#     1-based ("if(n>=1&&n<=5)n=n-1"), but every writer in this page stores it
#     0-based: the "dùng gói" buttons save dataset.pack (0..4) verbatim. So a
#     student who worked in gói 2 was shown gói 1 and their answers looked lost.
#     Read the saved index as 0-based and prefer a gói that actually holds work.
patch(
    'function detect(p){\n'
    '   let idx=-1;\n'
    '   for(let i=0;i<5;i++){\n'
    '     for(let q=0;q<3;q++){\n'
    '       const candidates=[\n'
    '        "sah321-bank-answer-"+p+"-"+i+"-"+q,\n'
    '        "sah321-bank-answer-"+p+"-"+(i+1)+"-"+(q+1)\n'
    '       ];\n'
    '       if(candidates.some(k=>(localStorage.getItem(k)||"").trim())) idx=i;\n'
    '     }\n'
    '   }\n'
    '   let c=localStorage.getItem("sah321-integrated-pack-"+p);\n'
    '   if(c!==null && c!=="" && !isNaN(+c)){\n'
    '     let n=+c; if(n>=1&&n<=5)n=n-1;\n'
    '     idx=Math.max(0,Math.min(4,n));\n'
    '   }\n'
    '   return idx;\n'
    ' }',
    'function detect(p){\n'
    '   let idx=-1,found=false;\n'
    '   const work=k=>{for(let q=1;q<=3;q++){if((localStorage.getItem(k+"-"+q)||"").trim())return true;}return false;};\n'
    '   for(let i=0;i<5;i++){\n'
    '     if(work("sah321-integrated-"+p+"-"+i)||work("sah321-bank-answer-"+p+"-"+i)){idx=i;found=true;}\n'
    '   }\n'
    '   let c=localStorage.getItem("sah321-integrated-pack-"+p);\n'
    '   if(c!==null && c!=="" && !isNaN(+c)){\n'
    '     let n=Math.max(0,Math.min(4,+c));\n'
    '     if(work("sah321-integrated-"+p+"-"+n)||work("sah321-bank-answer-"+p+"-"+n)||!found) idx=n;\n'
    '   }\n'
    '   return idx;\n'
    ' }',
    "pack context: read the saved gói index as 0-based and prefer a gói that holds work",
)

# 3e. sketchV25 (Xương phác thảo, stage 4): the project help box under "Nhìn lại
#     3 lần thử" was a bare empty <div> that only refreshProjectHelp() filled, and
#     only when the project dropdown changed — so "Cần trợ giúp? Mở gợi ý" opened
#     a blank box on first paint. This master already fixes it three ways (native
#     <details>, default copy inside the body, refresh at init); prove all three,
#     because this is exactly the regression the team reported.
expect('<details class="skv-native-help">' in src and 'id="skvProjectHelp">' in src,
       "sketchV25: the project help is a native <details> with seeded content")
expect('projectHelp[P.value]||h.innerHTML' in src,
       "sketchV25: an unknown project keeps the existing help instead of blanking it")
expect('\nload();\nrefreshProjectHelp();\n' in src,
       "sketchV25: the project help is filled at init, not only on project change")

# 3f. prove the content the team added on 2026-10-09 is actually in this build:
#     the sahed hotspot content editor, the #p321V312 worksheet section, the AI 5A
#     direct-content patch and the native help styling.
for _needle, _why in (
    ('<style id="sahed-css">', "the sahed hotspot editor stylesheet is present"),
    ('<script id="sahed-js">', "the sahed hotspot editor script is present"),
    ('class="sahed-tools"', "the sahed edit/restore toolbars are on the hotspot cards"),
    ('<section id="p321V312">', "the p321V312 worksheet section is present"),
    ('<script id="p321-v312-js">', "the p321V312 tab + save script is present"),
    ('<script id="ai5a-direct-content-patch-v314">', "the AI 5A direct-content patch is present"),
    ('<style id="skv-native-help-fix">', "the native help styling is present"),
):
    expect(_needle in src, _why)

# --------------------------------------------------------------------------
# 4. journey39 wiring
# --------------------------------------------------------------------------
J39 = r"""
<!-- J39-WIRING-START -->
<script>
document.addEventListener("DOMContentLoaded",function(){
var R=document.getElementById("journey39"), P=document.getElementById("j39p");
if(!R||!P)return;

/* #j39p has no value= attributes, so its options are the five projects in order. */
var KEYS=["phohien","chuakeo","dentran","lequydon","dongxam"];
/* mirrors js5.js so the dossier label matches the gói the student actually opened */
var PACKNAME={phohien:["Dấu ấn Phố Hiến","Kiến trúc & không gian","Màu sắc & cảm xúc","Xưa & nay","Biểu tượng cá nhân"],
 chuakeo:["Nhịp điệu mái chùa","Hình khối kiến trúc","Hoa văn & chi tiết gỗ","Không gian & góc nhìn","Chùa Keo hiện đại"],
 dentran:["Dấu ấn lịch sử","Kiến trúc trang nghiêm","Biểu tượng & hoa văn","Không gian tưởng niệm","Di sản với thế hệ trẻ"],
 lequydon:["Chân dung nhà bác học","Không gian lưu niệm","Sách & tri thức","Kể chuyện bằng hình ảnh","Tri thức hôm nay"],
 dongxam:["Hoa văn chạm bạc","Ánh sáng & bề mặt","Nhịp điệu trang trí","Truyền thống → hiện đại","Bảo tồn bằng Mĩ thuật"]};
var HINT="Sẽ lấy từ phần Khám phá.";

function g(k){var v=localStorage.getItem(k);return v==null?"":String(v);}
/* the reference's own AI 5A writes this literal placeholder into storage when A1 is
   empty, so it must never be mistaken for a student answer */
var NOPLACE=["Em chưa nhập nội dung A1."];
function t(v){var s=String(v==null?"":v).trim();return NOPLACE.indexOf(s)>=0?"":s;}
function json(k){try{return JSON.parse(localStorage.getItem(k)||"{}")||{};}catch(e){return {};}}
function join(){var a=[].slice.call(arguments).map(t).filter(Boolean);return a.join("  •  ");}

/* the gói the student is on, resolved the same way js0/js5 do. The sheet and the
   Kho both store the index 0-based, so a saved index is 0-based too: reading
   1..4 as "1-based" shifted gói 2..5 onto gói 1..4 and hid the answers the
   student had just written. Prefer a gói that holds work, so a stale index can
   never hide it. */
function packIdx(p){
  var i=-1,j,found=false,
      work=function(k){for(var q=1;q<=3;q++){if(t(g(k+"-"+q)))return true;}return false;},
      any=function(k){return work("sah321-integrated-"+k)||work("sah321-bank-answer-"+k);};
  for(j=0;j<5;j++){if(any(p+"-"+j)){i=j;found=true;}}
  var c=g("sah321-integrated-pack-"+p);
  if(c!==""&&!isNaN(+c)){
    var n=Math.max(0,Math.min(4,+c));
    if(any(p+"-"+n)||!found)i=n;
  }
  return i<0?0:i;
}
/* one 3-2-1 answer, preferring the integrated sheet then the bank then the per-project sheet */
function ans(p,i,q){
  var v=t(g("sah321-integrated-"+p+"-"+packIdx(p)+"-"+q));
  if(!v) v=t(g("sah321-bank-answer-"+p+"-"+packIdx(p)+"-"+q));
  if(!v) v=t(g("direct321-"+p+"-"+q));
  return v;
}
/* every gói the student has filled, so stage 1 shows all their discoveries */
function ansAll(p,q){
  var a=[],j;
  for(j=0;j<5;j++){var v=t(g("sah321-bank-answer-"+p+"-"+j+"-"+q)); if(v) a.push(v);}
  a.push(ans(p,null,q));
  return a.filter(Boolean).join("  •  ");
}
function ai(p,x){return t(g("sah-ai5a-studio-"+p+"-"+x));}
function pass(p,x){return t(g("sah-ai5a-studio-"+p+"-pass-"+x));}
function sketch(p){return json("sah-sketch-v25-"+p);}
function art(p){return json("sah-art-v33-"+p);}
function ex(p){return json("sah-ex38-"+p);}

/* the 26 fields, in document order, each with the real storage it reads */
function fields(p){
  var a1=ai(p,"a1"), sk=sketch(p), ar=art(p), exd=ex(p);
  if(!a1){var parts=[["a1part-main","hình ảnh chính"],["a1part-heritage","nét di sản"],["a1part-feeling","cảm xúc / thông điệp"]];
    var z=[];parts.forEach(function(q){var v=ai(p,q[0]);if(v)z.push(q[1]+": "+v);});if(z.length)a1=z.join("  •  ");}
  var idea=t(g("sah-ai5a-seed-"+p))||ans(p,null,1);
  var feedback=join(exd.peer1,exd.peer2,exd.peer3);
  var talk=join(exd.talk1,exd.talk2,exd.talk3);
  var obs=ans(p,null,3);
  return [
    /* 1 */ ansAll(p,3), ansAll(p,2)||ai(p,"a1part-main"),
    /* 2 */ obs?("Gói "+(packIdx(p)+1)+" • "+PACKNAME[p][packIdx(p)]+" — "+obs):"",
             ans(p,null,2), idea, ai(p,"ask-0"),
    /* 3 */ a1, join(ai(p,"a3"),ai(p,"a4")), pass(p,"signature"), pass(p,"decision"),
    /* 4 */ sk.carryForward, sk.heritage, sk.change, sk.why,
    /* 5 */ ar.title, join(ar.tech,ar.form,ar.size), ar.core, ar.message,
    /* 6 */ talk, join(exd.peer1,exd.peer2),
             exd.peer3, feedback?("Tiếp thu từ phản hồi: "+feedback):"",
    /* 7 */ exd.self1, exd.self2, exd.self4, exd.self3
  ];
}

function render(){
  var p=KEYS[P.selectedIndex]||KEYS[0];
  var vals=fields(p);
  /* must match ANY span: spans are re-classed between renders, so selecting
     ".j39miss" here would return an empty list on every render after the first */
  var spans=R.querySelectorAll(".j39field > span"), i;
  for(i=0;i<spans.length;i++){
    var v=t(vals[i]);
    if(v){
      spans[i].className="j39real";
      spans[i].textContent=v;
    }else{
      spans[i].className="j39miss";
      spans[i].textContent=HINT;
    }
  }
}
P.addEventListener("change",render);
render();
});
</script>
<style>
.j39real{color:#1f3d31}
.j39field:has(.j39real){background:#f2f8f3;border-left:3px solid #285b46}
.j39field:has(.j39miss){border-left:3px solid #d7e0da}
</style>
<!-- J39-WIRING-END -->
"""

# --------------------------------------------------------------------------
# 5. restored modules (role gate, step lock, 3D room, teacher bridge,
#    Trien lam gallery, live AI chat, worksheet export, navigation)
# --------------------------------------------------------------------------
anchor = "</body>"

NAV = """<!-- RM-NAV-START -->
<nav class="rm-topnav">
  <a class="rm-topnav-brand" href="#p0">SMART ART HERITAGE</a>
  <a class="rm-topnav-link" href="#rmRoom3d">🧊 Phòng 3D</a>
  <a class="rm-topnav-link" href="#rmExhibit">🖼️ Triển lãm</a>
  <a class="rm-topnav-link" href="#rmChat">🤖 Trợ lý AI</a>
  <a class="rm-topnav-link" href="giao-vien.html">👩‍🏫 Trang Quản Trị ↗</a>
  <a class="rm-topnav-link" href="trien-lam.html">🗂️ Triển lãm đầy đủ ↗</a>
  <span class="rm-topnav-spacer"></span>
  <span class="rm-identity" id="rmIdentityChip"></span>
  <span class="rm-chip" id="rmRoleChip">— chưa chọn vai trò —</span>
  <button class="rm-btn sm" id="rmRoleSwitch" type="button">Đổi</button>
  <span class="rm-topnav-lock" id="rmLockStatus"></span>
</nav>
<!-- RM-NAV-END -->

<!-- RM-GATE-START -->
<div id="roleGate" class="rm-overlay" hidden>
  <div class="rm-card">
    <div class="rm-eyebrow">SMART ART HERITAGE • HÀNH TRÌNH 1 → 5</div>
    <h2>Trước tiên: em là ai?</h2>
    <p class="rm-sub">Chọn vai trò để bắt đầu. Học sinh khai báo họ tên, mã học sinh và lớp một lần duy nhất, rồi làm và nộp từng chặng. Khách xem thử toàn bộ mà không nộp bài.</p>
    <div class="rm-choices" id="rgChoices">
      <button type="button" class="rm-choice" data-role="student"><span class="rm-ico">🎓</span><b>Học sinh</b><span>Nhập họ tên, mã học sinh, lớp rồi làm và nộp từng chặng</span></button>
      <button type="button" class="rm-choice" data-role="teacher"><span class="rm-ico">👩‍🏫</span><b>Giáo viên</b><span>Về Trang Quản Trị để chấm bài, phản hồi và kết nối AI</span></button>
      <button type="button" class="rm-choice" data-role="guest"><span class="rm-ico">👀</span><b>Khách</b><span>Xem thử toàn bộ hành trình, không cần tên</span></button>
    </div>
    <div class="rm-form" id="rgStudentForm" hidden>
      <label for="rmName">Họ tên đầy đủ của em</label>
      <input id="rmName" type="text" placeholder="VD: Nguyễn Minh An" autocomplete="name">
      <label for="rmStudentId">Mã học sinh</label>
      <input id="rmStudentId" type="text" placeholder="VD: HS-6A1-024" autocomplete="off">
      <label for="rmClass">Lớp</label>
      <input id="rmClass" type="text" placeholder="VD: 6A1" autocomplete="off">
      <div class="rm-err" id="rmErr"></div>
      <div class="rm-form-actions">
        <button type="button" class="rm-btn" id="rmStudentStart">Bắt đầu hành trình →</button>
        <button type="button" class="rm-btn ghost" id="rmStudentBack">← Chọn lại vai trò</button>
      </div>
    </div>
    <p class="rm-note">Lựa chọn được lưu trên máy này. Muốn đổi vai trò, bấm “Đổi” trên thanh trên cùng.</p>
  </div>
</div>
<!-- RM-GATE-END -->
"""

SECTIONS = """<!-- RM-SECTIONS-START -->
<section id="rmRoom3d" class="rm-sec">
  <h2>🧊 PHÒNG 3D • XOAY 360° TỪNG DI SẢN</h2>
  <p class="rm-sub">Mô hình 3D của 5 di sản, xoay và phóng to bằng chuột hoặc ngón tay. Mô hình tải khi em mở để trang không bị nặng ngay từ đầu.</p>
  <div class="rm-frame" id="rm3dWrap">
    <iframe id="rm3dFrame" title="Phòng 3D di sản" loading="lazy" allowfullscreen></iframe>
    <button type="button" class="rm-frame-cta" id="rm3dCta">▶ Mở phòng 3D</button>
  </div>
  <p class="rm-note">Muốn xem toàn màn hình: <a href="models.html">mở models.html ↗</a></p>
</section>

<section id="rmExhibit" class="rm-sec">
  <h2>🖼️ TRIỂN LÃM TÁC PHẨM • HỒ SƠ LỚP</h2>
  <p class="rm-sub">Tác phẩm em lưu sẽ xuất hiện ở đây và trong Trang Quản Trị của giáo viên.</p>
  <div class="rm-stats" id="rmStats"></div>
  <div class="rm-tools">
    <input id="rmSearch" type="search" placeholder="Tìm theo tên tác phẩm, mã học sinh, lớp...">
    <select id="rmFilter">
      <option value="">Tất cả di sản</option>
      <option value="phohien">Phố Hiến</option><option value="chuakeo">Chùa Keo</option>
      <option value="dentran">Đền Trần</option><option value="lequydon">Lê Quý Đôn</option>
      <option value="dongxam">Đồng Xâm</option>
    </select>
    <button type="button" class="rm-btn" id="rmSaveWork">💾 Lưu tác phẩm của em vào triển lãm</button>
    <button type="button" class="rm-btn ghost" id="rmExport321">⬇ Xuất phiếu 3–2–1</button>
    <span class="rm-note" id="rmWorkMsg"></span>
    <span class="rm-note" id="rmExportMsg"></span>
  </div>
  <div class="rm-grid" id="rmGallery"></div>
  <p class="rm-note" id="rmGalleryEmpty"></p>
</section>

<section id="rmChat" class="rm-sec">
  <h2>🤖 TRỢ LÝ AI • GỢI Ý ĐỒNG HÀNH</h2>
  <p class="rm-sub">AI không làm thay em. AI đặt câu hỏi và gợi mở để em tự quyết định.</p>
  <div class="rm-chat-wrap">
    <div class="rm-chat" id="rmChatHistory"></div>
    <div class="rm-chatbar">
      <input id="rmChatInput" type="text" placeholder="Nhập câu hỏi hoặc suy nghĩ của em để AI gợi ý tiếp...">
      <button type="button" class="rm-btn" id="rmSend">Gửi</button>
      <button type="button" class="rm-btn ghost" id="rmCfgBtn">⚙ Cấu hình AI</button>
    </div>
    <p class="rm-note" id="rmCfgStatus"></p>
  </div>
</section>

<div class="rm-modal" id="rmCfgModal" hidden>
  <div class="rm-modal-card">
    <button class="rm-modal-x" id="rmCfgClose" type="button">✕</button>
    <h3>Cấu hình AI</h3>
    <label>Đường dẫn API<input id="rmCfgBase" type="text" placeholder="https://api.openai.com/v1"></label>
    <label>Khoá API<input id="rmCfgKey" type="password" placeholder="sk-..."></label>
    <label>Tên mô hình<input id="rmCfgModel" type="text" placeholder="gpt-4o-mini"></label>
    <p class="rm-note" id="rmCfgNote"></p>
    <button type="button" class="rm-btn" id="rmCfgSave">Lưu cấu hình</button>
  </div>
</div>

<div class="rm-modal" id="rmLightbox" hidden>
  <div class="rm-modal-card wide">
    <button class="rm-modal-x" id="rmLbClose" type="button">✕</button>
    <h3 id="rmLbTitle"></h3>
    <img id="rmLbImg" alt="">
    <p class="rm-note" id="rmLbMeta"></p>
    <p id="rmLbNote"></p>
    <div class="rm-lb-grade" id="rmLbGrade" hidden></div>
  </div>
</div>
<!-- RM-SECTIONS-END -->
"""

RM_CSS = """<!-- RM-CSS-START -->
<style>
/* The author display rules below outrank the UA [hidden]{display:none} rule, so
   every hidden overlay would stay on screen. Make hidden authoritative. */
[hidden]{display:none !important}
/* an empty identity or lock chip should not render as a blank pill */
.rm-identity:empty,.rm-topnav-lock:empty{display:none}
.rm-topnav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:9px 16px;background:#12281f;color:#eaf3ee;font-size:13px;position:sticky;top:0;z-index:60}
.rm-topnav a{color:#cfe3d8;text-decoration:none;padding:5px 9px;border-radius:8px}
.rm-topnav a:hover{background:#1d4033}
.rm-topnav-brand{font-weight:800;letter-spacing:.05em;color:#fff!important}
.rm-topnav-spacer{flex:1}
.rm-chip{background:#1d4033;padding:5px 10px;border-radius:999px;font-size:12px}
.rm-identity{background:#c89547;color:#12281f;font-weight:700;padding:5px 10px;border-radius:999px;font-size:12px}
.rm-topnav-lock{background:#fff8e5;color:#6b5316;padding:5px 10px;border-radius:999px;font-size:12px}
.rm-btn{background:#285b46;color:#fff;border:0;border-radius:10px;padding:9px 13px;font:inherit;font-weight:600;cursor:pointer}
.rm-btn:hover{background:#1d4033}.rm-btn.ghost{background:#eef3f0;color:#285b46}.rm-btn.sm{padding:5px 10px;font-size:12px}
.rm-overlay{position:fixed;inset:0;background:rgba(12,26,20,.72);display:flex;align-items:center;justify-content:center;z-index:200;padding:18px}
.rm-card{background:#fff;border-radius:20px;padding:26px;max-width:620px;width:100%;max-height:92vh;overflow:auto}
.rm-eyebrow{font-size:11px;letter-spacing:.2em;color:#5d6b63;font-weight:700}
.rm-sub{color:#53645b;line-height:1.6}
.rm-note{color:#6b7a72;font-size:13px;margin:6px 0}
.rm-choices{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0}
.rm-choice{background:#f4f7f4;border:2px solid #d7e0da;border-radius:14px;padding:14px;text-align:left;cursor:pointer;font:inherit;display:grid;gap:5px}
.rm-choice:hover{border-color:#285b46;background:#f0f8f3}
.rm-choice .rm-ico{font-size:24px}
.rm-choice span:last-child{font-size:12px;color:#5d6b63;line-height:1.5}
.rm-form{display:grid;gap:6px;margin-top:12px}
.rm-form label{font-size:12px;font-weight:700;color:#53645b}
.rm-form input{padding:10px;border:1px solid #c9d5cd;border-radius:10px;font:inherit}
.rm-err{color:#b3261e;font-size:13px;min-height:18px}
.rm-form-actions{display:flex;gap:8px;margin-top:8px}
@media(max-width:760px){.rm-choices{grid-template-columns:1fr}}
.rm-sec{max-width:1160px;margin:28px auto;padding:20px;background:#fff;border:1px solid #d7e0da;border-radius:20px}
.rm-sec h2{margin:0 0 6px}
/* the nav below is sticky, so a plain #hash jump parks the target heading
   underneath it. --rm-navh is kept in sync with the real nav height in JS. */
html{scroll-behavior:smooth}
:root{--rm-navh:79px}
section[id],.rm-sec,:target{scroll-margin-top:calc(var(--rm-navh) + 26px)}
.rm-lockbadge{display:flex;gap:11px;align-items:flex-start;background:#fff8e5;border:1px solid #e8d8ab;border-left:5px solid #8b6d1f;border-radius:12px;padding:12px 14px;margin:0 0 16px;font-size:14px;line-height:1.55;color:#4a3c12}
.rm-lockbadge .rm-lockico{font-size:19px;line-height:1.35}
.rm-lockbadge .rm-lockbody{flex:1;display:grid;gap:6px;justify-items:start}
.rm-lockbadge b{font-size:14px}
.rm-lockbadge .rm-lockgo{text-decoration:none}
/* a locked step is muted, never blurred: the banner above it stays sharp */
.rm-locked{position:relative;background:#fffdf6;border-color:#e8d8ab}
.rm-locked>*:not(.rm-lockbadge){opacity:.4;pointer-events:none;user-select:none}
.rm-frame{position:relative;aspect-ratio:16/9;background:#0e1c17;border-radius:16px;overflow:hidden}
.rm-frame iframe{width:100%;height:100%;border:0;display:block}
.rm-frame-cta{position:absolute;inset:0;margin:auto;width:max-content;height:max-content;background:#c89547;color:#12281f;border:0;border-radius:999px;padding:14px 26px;font:inherit;font-weight:800;cursor:pointer}
.rm-stats{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.rm-stats span{background:#f4f7f4;border:1px solid #d7e0da;border-radius:10px;padding:7px 12px;font-size:13px}
.rm-stats b{font-size:16px}
.rm-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}
.rm-tools input,.rm-tools select{padding:9px;border:1px solid #c9d5cd;border-radius:10px;font:inherit}
.rm-tools input{min-width:240px;flex:1}
.rm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-top:10px}
.rm-card{margin:0;background:#f8faf8;border:1px solid #d7e0da;border-radius:14px;overflow:hidden;cursor:pointer}
.rm-card img{width:100%;height:150px;object-fit:cover;display:block}
.rm-card figcaption{padding:9px;display:grid;gap:3px}
.rm-card figcaption b{font-size:13px}
.rm-card figcaption small{color:#6b7a72;font-size:11px}
.rm-chip{display:inline-block}
.rm-card .rm-chip{background:#e4f0e8;color:#285b46;font-size:11px;padding:2px 8px;border-radius:999px;align-self:start}
.rm-chat{display:flex;flex-direction:column;gap:8px;max-height:340px;overflow:auto;background:#f8faf8;border:1px solid #d7e0da;border-radius:14px;padding:12px}
.rm-bubble{max-width:82%;padding:9px 12px;border-radius:14px;font-size:14px;line-height:1.55;white-space:pre-wrap}
.rm-me{align-self:flex-end;background:#285b46;color:#fff;border-bottom-right-radius:4px}
.rm-ai{align-self:flex-start;background:#fff;border:1px solid #d7e0da;border-bottom-left-radius:4px}
.rm-chatbar{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.rm-chatbar input{flex:1;min-width:220px;padding:10px;border:1px solid #c9d5cd;border-radius:10px;font:inherit}
.rm-modal{position:fixed;inset:0;background:rgba(12,26,20,.74);display:flex;align-items:center;justify-content:center;z-index:210;padding:18px}
.rm-modal-card{background:#fff;border-radius:18px;padding:22px;max-width:560px;width:100%;max-height:92vh;overflow:auto;position:relative;display:grid;gap:8px}
.rm-modal-card.wide{max-width:860px}
.rm-modal-card label{font-size:12px;font-weight:700;color:#53645b;display:grid;gap:4px}
.rm-modal-card input{padding:10px;border:1px solid #c9d5cd;border-radius:10px;font:inherit}
.rm-modal-x{position:absolute;top:10px;right:12px;border:0;background:transparent;font-size:18px;cursor:pointer}
.rm-modal-card img{width:100%;border-radius:12px}
.rm-lb-grade{background:#f0f8f3;border-left:4px solid #285b46;padding:11px;border-radius:8px;line-height:1.6}
.rmfb-box{background:#f0f8f3;border:1px solid #cfe0d6;border-left:4px solid #285b46;border-radius:10px;padding:12px;margin:12px 0;line-height:1.6}
.rmfb-head{font-weight:800;font-size:13px;margin-bottom:4px}
.rmfb-head small{font-weight:400;color:#6b7a72}
</style>
<!-- RM-CSS-END -->
"""

# navigation goes right after the page header; sections before #journey39
src = src.replace("</header>", "</header>\n" + NAV, 1)
src = src.replace('<section id="journey39">', SECTIONS + '<section id="journey39">', 1)
# teacher feedback inside the 3-2-1 card, just above its action row
src = src.replace(
    '<div class="sah-actions">',
    '<div class="rmfb-box" id="teacherFeedbackBox" hidden></div>\n'
    '<div class="sah-actions">', 1)
# styles + loader at the end, with the journey39 wiring
# Cache-bust the module on its own contents so an edit can never go stale in a
# browser that already cached the previous deploy.
rm_js_hash = hashlib.md5(
    open(os.path.join(ROOT, "js", "restored-modules.js"), "rb").read()
).hexdigest()[:10]
src = src.replace(anchor, RM_CSS + '<script src="js/restored-modules.js?v=' + rm_js_hash + '"></script>\n' + J39 + "\n" + anchor, 1)

# Google Fonts, as the old page had it
src = src.replace(
    "<title>",
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">\n'
    "<title>", 1)

# --------------------------------------------------------------------------
# 6. the teacher content studio (sửa câu hỏi → xuất bản cho học sinh)
# --------------------------------------------------------------------------
# It must load from <head>, not the end of <body>: only then can it hide the
# blocks that carry a teacher edit before the browser paints them, so students
# never see the old wording flash on top of the new one.
studio_js = os.path.join(ROOT, "js", "content-studio.js")
if not os.path.isfile(studio_js):
    sys.exit(
        "Missing js/content-studio.js — index.html would load a studio that is not there.\n"
        "Restore the file and run this again."
    )
studio_hash = hashlib.md5(open(studio_js, "rb").read()).hexdigest()[:10]
studio_tag = '<script src="js/content-studio.js?v=%s"></script>\n' % studio_hash
assert src.count("<head>") == 1, "expected exactly one <head>"
_head_end = src.index("<head>") + len("<head>")
src = src[: _head_end] + "\n" + studio_tag + src[_head_end :]
print("  injected js/content-studio.js?v=%s into <head>" % studio_hash)

assert src.index(studio_tag) < src.index("</head>"), \
    "the studio loader must be inside <head>"

# trien-lam.html is hand-maintained, so keep its loader version in step here
# rather than leaving a hand-typed hash to go stale after the next edit to
# js/content-studio.js.
for _page in ("trien-lam.html",):
    _path = os.path.join(ROOT, _page)
    if not os.path.isfile(_path):
        continue
    _html = open(_path, encoding="utf-8").read()
    _synced, _n = re.subn(r"js/content-studio\.js\?v=[0-9a-f]+",
                          "js/content-studio.js?v=" + studio_hash, _html)
    assert _n == 1, "expected exactly one studio loader in %s, found %d" % (_page, _n)
    if _synced != _html:
        open(_path, "w", encoding="utf-8").write(_synced)
    print("  %s studio loader is on the same hash (%s)" % (_page, studio_hash))
expect('js/content-studio.js?v=%s' % studio_hash in src,
       "the teacher content studio loader is in <head>, cache-busted by its own hash")
# The studio is useless if the file it reads and the file the server writes are
# not the same path, so prove they agree instead of trusting the naming.
_studio_src = open(studio_js, encoding="utf-8").read()
assert "CONTENT_URL = 'content/published.json'" in _studio_src, \
    "content-studio.js no longer reads content/published.json"
assert "'/api/content'" in _studio_src, "content-studio.js no longer posts to /api/content"
_api_src = open(os.path.join(ROOT, "tools", "content_api.py"), encoding="utf-8").read()
assert 'PUBLISHED = os.path.join(DATA_DIR, "published.json")' in _api_src, \
    "content_api.py no longer writes content/published.json"
expect(True, "the studio reads and the API writes the same content/published.json")

# --------------------------------------------------------------------------
assert src.count(anchor) == 1, "expected exactly one </body>, found %d" % src.count(anchor)

# --------------------------------------------------------------------------
open(OUT, "w", encoding="utf-8").write(src)

# --------------------------------------------------------------------------
print("  wrote index.html: %.1f KB (reference was %.1f KB)" % (len(src) / 1024, len(open(REF, encoding='utf-8').read()) / 1024))
print("  repairs applied: %d" % REPAIRS)
