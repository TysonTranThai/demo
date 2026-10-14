#!/usr/bin/env python3
"""
tools/build_index.py
Builds index.html matching the user's requirements:
  1. Trang chủ is an actual rich Landing Page.
  2. Quản trị / Teacher Dashboard is strictly hidden unless the user is a teacher.
  3. Presentation-like PowerPoint experience: each section (Bản đồ, 5 Di sản, Hồ sơ 15 ảnh,
     Phòng 3D, AI 5A, Xưởng sáng tạo, Triển lãm AR, Đánh giá & Phản tư) has its own page/slide
     with Back and Continue buttons, slide counter (Trang X / 9), and keyboard arrow navigation.
  4. Preserves 100% of all existing content, 155 images, scripts, forms, and styles.
"""
import os
import re
import sys
import json
import hashlib
import urllib.parse

ROOT = "/Users/tysontran/Desktop/Smart Art Heritage"
REF = os.path.join(ROOT, "new 9_10_2026.html")
OUT = os.path.join(ROOT, "index.html")

print("=== Building Smart Art Heritage Landing Page & PowerPoint Presentation ===")

if not os.path.isfile(REF):
    sys.exit("Error: Missing master source %s" % REF)

src = open(REF, encoding="utf-8").read()

# --------------------------------------------------------------------------
# 1. Base64 -> real extracted assets
# --------------------------------------------------------------------------
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

blobs = re.findall(r'src="data:image/[a-z]+;base64,([A-Za-z0-9+/=]+)"', src)
assert len(blobs) == len(expected) == 155, (len(blobs), len(expected))
it = iter(expected)
src = re.sub(
    r'src="data:image/([a-z]+);base64,([A-Za-z0-9+/=]+)"',
    lambda m: 'src="%s"' % next(it),
    src,
)
assert "base64," not in src, "leftover base64"
print("  ✓ Replaced 155 base64 images with extracted asset paths")

# --------------------------------------------------------------------------
# 2. Remove #auditV311
# --------------------------------------------------------------------------
start = src.index('<section id="auditV311">')
end = src.index("</section>", start) + len("</section>")
removed = src[start:end]
assert removed.count("<section") == 1 and "au311-table" in removed
src = src[:start] + src[end:]

m = [x for x in re.finditer(r'<style[^>]*>(.*?)</style>', src, re.S) if "au311" in x.group(1)]
assert len(m) == 1
src = src[: m[0].start()] + src[m[0].end() :]
print("  ✓ Removed auditV311 section and styles")

# --------------------------------------------------------------------------
# 3. Apply repairs to original scripts
# --------------------------------------------------------------------------
REPAIRS = 0
def patch(old, new, why, count=1):
    global src, REPAIRS
    n = src.count(old)
    assert n == count, "expected %d occurrence(s) of %r, found %d" % (count, old[:70], n)
    src = src.replace(old, new)
    REPAIRS += 1
    print("  ✓ Repair %d: %s" % (REPAIRS, why))

patch(
    'root.querySelectorAll("[data-f]").forEach(x=>x.addEventListener("input",save));\n'
    'confirm.addEventListener("change",save); P.addEventListener("change",()=>{load();refreshProjectHelp();});\n',
    'root.querySelectorAll("[data-f]").forEach(x=>x.addEventListener("input",save));\n'
    'confirm.addEventListener("change",save); P.addEventListener("change",()=>{load();refreshProjectHelp();});\n'
    'root.querySelectorAll(".skv-option").forEach(b=>b.addEventListener("click",()=>{'
    'root.querySelectorAll(".skv-option").forEach(x=>x.classList.remove("chosen"));'
    'b.closest(".skv-option").classList.add("chosen");save();}));\n',
    "sketchV25: restore the .skv-option 'chosen' selection",
)

patch(
    'P.addEventListener("change",load);\n'
    'b.textContent=h.classList.contains("open")?"Thu gọn gợi ý":"\U0001f4a1 Cần trợ giúp? Mở gợi ý";});\n',
    'P.addEventListener("change",load);\n',
    "artV33: drop orphan .av-help toggle tail",
)

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
    "pack context: read saved gói index as 0-based",
)

src = src.replace(
    '<div class="sah-actions">',
    '<div class="rmfb-box" id="teacherFeedbackBox" hidden></div>\n'
    '<div class="sah-actions">', 1)

src = src.replace('Đền Trần Hưng Hà', 'Đền Trần Long Hưng')

# Enhance Tab labels in Slide 3 with preview image data
src = src.replace('<label class="tablabel" for="h1">', '<label class="tablabel" for="h1" data-preview-img="assets/extracted/001_Pho_Hien_tong_quan.jpeg" data-preview-title="Hồ Sơ 01 • Quần Thể Phố Hiến" data-preview-sub="TP. Hưng Yên • Thương cảng cổ thế kỷ XVII" data-preview-badge="HỒ SƠ 01">')
src = src.replace('<label class="tablabel" for="h2">', '<label class="tablabel" for="h2" data-preview-img="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" data-preview-title="Hồ Sơ 02 • Tuyệt Tác Chùa Keo" data-preview-sub="xã Vũ Tiên, Hưng Yên (Vũ Thư cũ) • Gác chuông 1632" data-preview-badge="HỒ SƠ 02">')
src = src.replace('<label class="tablabel" for="h3">', '<label class="tablabel" for="h3" data-preview-img="assets/extracted/066_Nghi_mon_den_Tran.jpeg" data-preview-title="Hồ Sơ 03 • Đền Trần Long Hưng" data-preview-sub="xã Long Hưng, Hưng Yên (Hưng Hà cũ) • Phát tích triều Trần" data-preview-badge="HỒ SƠ 03">')
src = src.replace('<label class="tablabel" for="h4">', '<label class="tablabel" for="h4" data-preview-img="assets/extracted/094_Chan_dung_bac_hoc_Le_Quy_Don.jpeg" data-preview-title="Hồ Sơ 04 • Danh Nhân Lê Quý Đôn" data-preview-sub="xã Lê Quý Đôn, Hưng Yên (Hưng Hà cũ) • Danh nhân văn hóa" data-preview-badge="HỒ SƠ 04">')
src = src.replace('<label class="tablabel" for="h5">', '<label class="tablabel" for="h5" data-preview-img="assets/extracted/136_San_pham_mam_cham_trang_tri.jpeg" data-preview-title="Hồ Sơ 05 • Chạm Bạc Đồng Xâm" data-preview-sub="xã Trà Giang, Hưng Yên (Kiến Xương cũ) • Kim hoàn 500 năm" data-preview-badge="HỒ SƠ 05">')

# Enhance Switcher labels in Slide 4 with preview image data
src = src.replace('<label for="h1">01 Phố Hiến</label>', '<label for="h1" data-preview-img="assets/extracted/001_Pho_Hien_tong_quan.jpeg" data-preview-title="01 • Quần Thể Phố Hiến" data-preview-sub="TP. Hưng Yên • Thương cảng cổ thế kỷ XVII" data-preview-badge="HỒ SƠ 01">01 Phố Hiến</label>')
src = src.replace('<label for="h2">02 Chùa Keo</label>', '<label for="h2" data-preview-img="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" data-preview-title="02 • Tuyệt Tác Chùa Keo" data-preview-sub="xã Vũ Tiên, Hưng Yên (Vũ Thư cũ) • Gác chuông 1632" data-preview-badge="HỒ SƠ 02">02 Chùa Keo</label>')
src = src.replace('<label for="h3">03 Đền Trần Long Hưng</label>', '<label for="h3" data-preview-img="assets/extracted/066_Nghi_mon_den_Tran.jpeg" data-preview-title="03 • Đền Trần Long Hưng" data-preview-sub="xã Long Hưng, Hưng Yên (Hưng Hà cũ) • Phát tích triều Trần" data-preview-badge="HỒ SƠ 03">03 Đền Trần Long Hưng</label>')
src = src.replace('<label for="h4">04 Khu lưu niệm Lê Quý Đôn</label>', '<label for="h4" data-preview-img="assets/extracted/094_Chan_dung_bac_hoc_Le_Quy_Don.jpeg" data-preview-title="04 • Danh Nhân Lê Quý Đôn" data-preview-sub="xã Lê Quý Đôn, Hưng Yên (Hưng Hà cũ) • Danh nhân văn hóa" data-preview-badge="HỒ SƠ 04">04 Khu lưu niệm Lê Quý Đôn</label>')
src = src.replace('<label for="h5">05 Làng nghề chạm bạc Đồng Xâm</label>', '<label for="h5" data-preview-img="assets/extracted/136_San_pham_mam_cham_trang_tri.jpeg" data-preview-title="05 • Chạm Bạc Đồng Xâm" data-preview-sub="xã Trà Giang, Hưng Yên (Kiến Xương cũ) • Kim hoàn 500 năm" data-preview-badge="HỒ SƠ 05">05 Làng nghề chạm bạc Đồng Xâm</label>')

# --------------------------------------------------------------------------
# 4. Extract HTML Blocks
# --------------------------------------------------------------------------
p_radios_start = src.find('<input checked="" id="home0"')
p_tabs = src.find('<div class="tabs">')
RADIOS_HTML = src[p_radios_start:p_tabs]

p_panels = src.find('<div class="panels">')
TABS_HTML = src[p_tabs:p_panels]

p_switcher = src.find('<div class="switcher">')
PANELS_HTML = src[p_panels:p_switcher]
SWITCHER_HTML = src[p_switcher:src.find('</div>', p_switcher) + len('</div>')]

p_sah321 = src.find('<section id="sah321-integrated"')
p_ai5a = src.find('<section id="sah-ai5a-studio"')
SAH321_BLOCK = src[p_sah321:p_ai5a]

p_sketch = src.find('<section id="sketchV25"')
AI5A_BLOCK = src[p_ai5a:p_sketch]

p_art = src.find('<section id="artV33"')
SKETCH_BLOCK = src[p_sketch:p_art]

p_exhibit = src.find('<section id="exhibitV38"')
ART_BLOCK = src[p_art:p_exhibit]

p_j39 = src.find('<section id="journey39"')
EXHIBIT_BLOCK = src[p_exhibit:p_j39]

p_p321 = src.find('<section id="p321V312"')
p_p321_end = src.find('</script>', p_p321) + len('</script>')
JOURNEY39_BLOCK = src[p_j39:p_p321]
P321_BLOCK = src[p_p321:p_p321_end]

TRAILING_HTML = src[p_p321_end:src.find('</body>')]

p_header_end = src.find('</header>') + len('</header>')
HEADER_HTML = src[:p_header_end]
HEADER_HTML = HEADER_HTML.replace('<body>', '<body class="slide-mode">', 1)

# Read Map SVG
map_svg_path = os.path.join(ROOT, "assets", "heritage", "map_hung_yen.svg")
MAP_SVG = open(map_svg_path, encoding="utf-8").read() if os.path.isfile(map_svg_path) else "<!-- Map SVG -->"

# --------------------------------------------------------------------------
# 5. Modular Components: Navigation & Stepper
# --------------------------------------------------------------------------

# Top navigation: notice teacher-only class on admin link
NAV = """<!-- RM-NAV-START -->
<nav class="rm-topnav">
  <a class="rm-topnav-brand" href="#step1-trangchu" onclick="goToSlide(0); return false;">SMART ART HERITAGE</a>
  <a class="rm-topnav-link" href="#step2-bando" onclick="goToSlide(1); return false;">🗺️ Bản đồ</a>
  <a class="rm-topnav-link" href="#step4-hosodisan" onclick="goToSlide(3); return false;">🔍 15 Ảnh di sản</a>
  <a class="rm-topnav-link" href="#step5-phong3d" onclick="goToSlide(4); return false;">🧊 Phòng 3D</a>
  <a class="rm-topnav-link" href="#step6-ai5a" onclick="goToSlide(5); return false;">🤖 Trợ lý AI</a>
  <a class="rm-topnav-link" href="#step8-argallery" onclick="goToSlide(7); return false;">🖼️ Triển lãm AR</a>
  <a class="rm-topnav-link" href="#step9-danhgia" onclick="goToSlide(8); return false;">📝 Đánh giá và tự hoàn thiện</a>
  <a class="rm-topnav-link teacher-only" href="giao-vien.html" style="display:none;">👩‍🏫 Quản Trị ↗</a>
  <a class="rm-topnav-link" href="trien-lam.html">🗂️ Triển lãm đầy đủ ↗</a>
  <span class="rm-topnav-spacer"></span>
  <span class="rm-identity" id="rmIdentityChip"></span>
  <span class="rm-chip" id="rmRoleChip">— chưa chọn vai trò —</span>
  <button class="rm-btn sm" id="rmRoleSwitch" type="button">Đổi vai trò</button>
  <span class="rm-topnav-lock" id="rmLockStatus"></span>
</nav>
<!-- RM-NAV-END -->

<!-- RM-GATE-START -->
<div id="roleGate" class="rm-overlay" hidden>
  <div class="rm-card">
    <div class="rm-eyebrow">SMART ART HERITAGE • HÀNH TRÌNH 9 BƯỚC TUẦN TỰ</div>
    <h2>Trước tiên: em là ai?</h2>
    <p class="rm-sub">Chọn vai trò để bắt đầu hành trình. Học sinh khai báo họ tên, mã học sinh và lớp để lưu bài và nhận phản hồi từ giáo viên.</p>
    <div class="rm-choices" id="rgChoices">
      <button type="button" class="rm-choice" data-role="student"><span class="rm-ico">🎓</span><b>Học sinh</b><span>Nhập họ tên, mã học sinh, lớp rồi làm và nộp từng chặng</span></button>
      <button type="button" class="rm-choice" data-role="teacher"><span class="rm-ico">👩‍🏫</span><b>Giáo viên</b><span>Xem toàn bộ 9 bước & Truy cập Trang Quản Trị để chấm bài theo Rubric</span></button>
      <button type="button" class="rm-choice" data-role="guest"><span class="rm-ico">👀</span><b>Khách tham quan</b><span>Xem thử toàn bộ 9 bước hành trình mà không cần nộp bài</span></button>
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
    <p class="rm-note">Lựa chọn được lưu trên máy này. Muốn đổi vai trò, bấm “Đổi vai trò” trên thanh trên cùng.</p>
  </div>
</div>
<!-- RM-GATE-END -->
"""

# Stepper Bar with slide controls, jump pills, and view-mode toggle
GUIDELINE_STEPPER = """<!-- SAH-GUIDELINE-STEPPER-START -->
<nav id="sahGuidelineNav" class="sah-stepper-nav" aria-label="Hành trình PowerPoint 9 bước">
  <div class="sah-stepper-container">
    <div class="sah-stepper-left">
      <button type="button" class="sah-stepper-btn-quick" id="btnQuickPrev" onclick="prevSlide()" title="Trang trước (Phím ←)">❮</button>
      <div class="sah-stepper-cur-badge" id="stepperSlideBadge">Trang <b id="stepperCurNum">1</b>/<span id="stepperTotalNum">9</span></div>
      <button type="button" class="sah-stepper-btn-quick" id="btnQuickNext" onclick="nextSlide()" title="Trang tiếp (Phím →)">❯</button>
    </div>
    <div class="sah-stepper-track" id="sahStepperTrack">
      <a href="#step1-trangchu" class="sah-step-pill active" data-step="1" data-preview-img="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" data-preview-title="Bước 1 • Cổng Bảo Tàng Số" data-preview-sub="Không gian di sản nghệ thuật & 5 kiệt tác tiêu biểu" data-preview-badge="BƯỚC 1 / 9" onclick="goToSlide(0); return false;">
        <span class="sah-step-num">1</span>
        <span class="sah-step-txt">Trang chủ</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step2-bando" class="sah-step-pill" data-step="2" data-preview-img="assets/extracted/001_Pho_Hien_tong_quan.jpeg" data-preview-title="Bước 2 • Bản Đồ Văn Hóa Số" data-preview-sub="Định vị 5 di sản văn hóa trọng điểm vùng Sông Hồng" data-preview-badge="BƯỚC 2 / 9" onclick="goToSlide(1); return false;">
        <span class="sah-step-num">2</span>
        <span class="sah-step-txt">Bản đồ</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step3-5khudisan" class="sah-step-pill" data-step="3" data-preview-img="assets/extracted/066_Nghi_mon_den_Tran.jpeg" data-preview-title="Bước 3 • 5 Kiệt Tác Di Sản" data-preview-sub="Đền Trần Long Hưng, Chùa Keo, Phố Hiến..." data-preview-badge="BƯỚC 3 / 9" onclick="goToSlide(2); return false;">
        <span class="sah-step-num">3</span>
        <span class="sah-step-txt">5 Di sản</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step4-hosodisan" class="sah-step-pill" data-step="4" data-preview-img="assets/extracted/042_Chi_tiet_trang_tri_kien_truc.jpeg" data-preview-title="Bước 4 • Hồ Sơ 15 Ảnh & Hotspot" data-preview-sub="Quan sát tư liệu cấu trúc, kỹ thuật & biểu tượng" data-preview-badge="BƯỚC 4 / 9" onclick="goToSlide(3); return false;">
        <span class="sah-step-num">4</span>
        <span class="sah-step-txt">Hồ sơ 15 ảnh</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step5-phong3d" class="sah-step-pill" data-step="5" data-preview-img="assets/heritage/diagram_3d_keo.svg" data-preview-title="Bước 5 • Phòng Tương Tác 3D" data-preview-sub="Số hóa WebGL xoay 360° cảm thụ hình khối" data-preview-badge="BƯỚC 5 / 9" onclick="goToSlide(4); return false;">
        <span class="sah-step-num">5</span>
        <span class="sah-step-txt">Phòng 3D</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step6-ai5a" class="sah-step-pill" data-step="6" data-preview-img="assets/heritage/diagram_ai_5a.svg" data-preview-title="Bước 6 • Trợ Lý AI Art Assistant 5A" data-preview-sub="Đối thoại thông minh gợi ý hướng phát triển ý tưởng" data-preview-badge="BƯỚC 6 / 9" onclick="goToSlide(5); return false;">
        <span class="sah-step-num">6</span>
        <span class="sah-step-txt">AI 5A</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step7-xuongsangtao" class="sah-step-pill" data-step="7" data-preview-img="assets/extracted/126_Nghe_nhan_trong_xuong_cham_bac.jpeg" data-preview-title="Bước 7 • Xưởng Sáng Tạo & Phác Thảo" data-preview-sub="Biến đổi mô-đun hoa văn di sản thành tác phẩm độc bản" data-preview-badge="BƯỚC 7 / 9" onclick="goToSlide(6); return false;">
        <span class="sah-step-num">7</span>
        <span class="sah-step-txt">Xưởng sáng tạo</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step8-argallery" class="sah-step-pill" data-step="8" data-preview-img="assets/extracted/150_Chi_tiet_hoa_van_rong_cham_noi.jpeg" data-preview-title="Bước 8 • Triển Lãm Thực Tế Ảo (AR)" data-preview-sub="Trưng bày tác phẩm trong không gian thực qua camera" data-preview-badge="BƯỚC 8 / 9" onclick="goToSlide(7); return false;">
        <span class="sah-step-num">8</span>
        <span class="sah-step-txt">Triển lãm AR</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step9-danhgia" class="sah-step-pill" data-step="9" data-preview-img="assets/heritage/diagram_hotspot_321.svg" data-preview-title="Bước 9 • Đánh Giá Và Tự Hoàn Thiện" data-preview-sub="Phiếu tự đánh giá 3-2-1 & Rubric sư phạm" data-preview-badge="BƯỚC 9 / 9" onclick="goToSlide(8); return false;">
        <span class="sah-step-num">9</span>
        <span class="sah-step-txt">Đánh giá và tự hoàn thiện</span>
      </a>
      <span class="sah-step-sep teacher-only" style="display:none;">|</span>
      <a href="#step-dashboard" class="sah-step-pill sah-step-dash teacher-only" data-step="10" data-preview-img="assets/heritage/edu_avatar.svg" data-preview-title="Dashboard Giáo Viên" data-preview-sub="Quản trị hồ sơ bài làm học sinh & chấm điểm Rubric" data-preview-badge="QUẢN TRỊ" style="display:none;" onclick="goToSlide(9); return false;">
        <span class="sah-step-icon">👩‍🏫</span>
        <span class="sah-step-txt">Dashboard GV</span>
      </a>
    </div>
    <div class="sah-stepper-right">
      <button type="button" class="sah-view-toggle" id="btnViewToggle" onclick="toggleViewMode()" title="Chuyển đổi giữa chế độ Slide PowerPoint và Cuộn trang liên tục">
        <span id="viewToggleIco">📽️</span>
        <span id="viewToggleTxt">Chế độ Slide</span>
      </button>
    </div>
  </div>
</nav>

<!-- GLOBAL FLOATING HOVER PREVIEW MODAL -->
<div id="sahGlobalHoverPreview" class="sah-global-hover-preview" aria-hidden="true">
  <div class="sah-ghp-media">
    <img id="sahGhpImg" src="" alt="Xem trước di sản">
    <div class="sah-ghp-shine"></div>
  </div>
  <div class="sah-ghp-body">
    <div id="sahGhpBadge" class="sah-ghp-badge"></div>
    <div id="sahGhpTitle" class="sah-ghp-title"></div>
    <div id="sahGhpSub" class="sah-ghp-sub"></div>
    <div class="sah-ghp-hint">✦ Nhấp để mở trang này →</div>
  </div>
</div>
<!-- SAH-GUIDELINE-STEPPER-END -->
"""

# Reusable PowerPoint Bottom Bar Generator
def make_ppt_footer(step_idx, prev_name, next_name, is_last=False):
    prev_click = f"goToSlide({step_idx - 2})" if step_idx > 1 else ""
    prev_style = "visibility:hidden;" if step_idx == 1 else ""
    
    if is_last:
        next_btn = f"""<button type="button" class="sah-ppt-btn sah-ppt-next sah-ppt-finish" onclick="goToSlide(0)">
          <span class="sah-ppt-lbl">Hoàn thành hành trình 🎉 (Về Trang chủ)</span> 
          <span class="sah-ppt-arr">↑</span>
        </button>"""
    else:
        next_click = f"goToSlide({step_idx})"
        next_btn = f"""<button type="button" class="sah-ppt-btn sah-ppt-next" onclick="{next_click}">
          <span class="sah-ppt-lbl">Tiếp tục: <b>{next_name}</b></span> 
          <span class="sah-ppt-arr">→</span>
        </button>"""
    
    return f"""
    <div class="sah-ppt-nav-bar">
      <button type="button" class="sah-ppt-btn sah-ppt-prev" style="{prev_style}" onclick="{prev_click}">
        <span class="sah-ppt-arr">←</span> 
        <span class="sah-ppt-lbl">Quay lại: <b>{prev_name}</b></span>
      </button>
      
      <div class="sah-ppt-indicator">
        <div class="sah-ppt-slide-num">Trang <b>{step_idx}</b> / <span class="sah-dyn-total">9</span></div>
        <div class="sah-ppt-key-hint">Dùng phím <kbd>←</kbd> <kbd>→</kbd> để chuyển trang</div>
      </div>

      {next_btn}
    </div>
    """

# --------------------------------------------------------------------------
# 6. SLIDE 1: DEDICATED RICH LANDING PAGE
# --------------------------------------------------------------------------
STEP1_HTML = f"""<!-- STEP 1: TRANG CHU - DEDICATED LUXURY MUSEUM LANDING PAGE -->
<section id="step1-trangchu" class="sah-step-sec sah-slide active-slide sah-landing-page">
  <!-- Monogram Heritage Watermark -->
  <div class="sah-museum-watermark" aria-hidden="true">S</div>

  <!-- HERO SECTION -->
  <div class="sah-landing-hero">
    <div class="sah-hero-grid">
      <div class="sah-hero-left">
        <div class="sah-landing-badge-bar">
          <span class="sah-badge-accent">✦ DỰ ÁN MĨ THUẬT SỐ DI SẢN VĂN HÓA ĐỊA PHƯƠNG</span>
          <span class="sah-badge-sub">TỈNH HƯNG YÊN & THÁI BÌNH • CHÂU THỔ SÔNG HỒNG</span>
        </div>
        
        <h1 class="sah-landing-title">
          <span class="sah-title-kicker">HÀNH TRÌNH KHÁM PHÁ & SÁNG TẠO</span>
          <span class="sah-title-main">SMART ART HERITAGE</span>
          <span class="sah-title-sub">Không Gian Nghệ Thuật Số Đương Đại Cho Di Sản Dân Tộc</span>
        </h1>

        <p class="sah-landing-lead">
          Chào mừng em đến với <b>Smart Art Heritage</b> — nền tảng học tập Mĩ thuật số chuyển hóa di sản văn hóa nghìn năm châu thổ Sông Hồng thành chất liệu sáng tạo đương đại. Trải nghiệm được thiết kế theo <b>bài giảng trình chiếu 9 bước tuần tự</b>: từ quan sát tư liệu, cảm thụ hình khối 3D 360°, đối thoại cùng trợ lý AI 5A đến trưng bày tác phẩm trong không gian thực qua thực tế tăng cường (AR).
        </p>

        <div class="sah-landing-meta-strip">
          <div class="sah-meta-item">🏛️ <b>Đơn vị nghiên cứu:</b> Trường Trung học cơ sở Lê Quý Đôn, xã Lê Quý Đôn, tỉnh Hưng Yên</div>
          <div class="sah-meta-item">🎓 <b>Đối tượng:</b> Học sinh THCS, THPT & Giáo viên mĩ thuật</div>
          <div class="sah-meta-item">📜 <b>Chuẩn đầu ra:</b> Phát triển năng lực mĩ thuật & cảm thụ di sản</div>
        </div>

        <div class="sah-landing-hero-actions">
          <button type="button" class="sah-btn-hero-primary" onclick="goToSlide(1)">
            🚀 BẮT ĐẦU HÀNH TRÌNH 9 BƯỚC (Trang 2: Bản đồ) →
          </button>
          <div class="sah-hero-quick-row">
            <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(1)">🗺️ Bản đồ số</button>
            <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(2)">🏛️ 5 Khu di sản</button>
            <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(3)">🔍 15 Ảnh tư liệu</button>
            <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(4)">🧊 Phòng 3D 360°</button>
            <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(5)">🤖 Trợ lý AI 5A</button>
            <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(7)">📱 Triển lãm AR</button>
          </div>
        </div>
      </div>

      <div class="sah-hero-right">
        <div class="sah-hero-pedestal">
          <div class="sah-pedestal-glow"></div>
          <div class="sah-pedestal-card">
            <div class="sah-pedestal-media-wrap">
              <img src="assets/extracted/053_Gac_chuong_ba_tang.jpeg" alt="Gác chuông Chùa Keo" class="sah-pedestal-img">
              <span class="sah-pedestal-badge">KIỆT TÁC TIÊU BIỂU</span>
            </div>
            <div class="sah-pedestal-caption">
              <h4>Gác chuông Chùa Keo</h4>
              <p>Đỉnh cao kết cấu gỗ cổ truyền 12 mái chồng diêm & hệ thống đấu củng tinh xảo thế kỷ XVII.</p>
              <div class="sah-pedestal-actions">
                <button type="button" class="sah-btn-pedestal" onclick="goToSlide(4)">Xoay 3D 360° →</button>
                <button type="button" class="sah-btn-pedestal-ghost" onclick="selectHeritageByCode('chuakeo')">Xem hồ sơ →</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 5 HERITAGE MASTERPIECES CURATORIAL EXHIBITION (MATCHING USER'S REFERENCE DESIGN) -->
  <div class="sah-landing-section sah-exhibits-section">
    <div class="sah-landing-sec-head">
      <span class="sah-tag-pill">BỘ SƯU TẬP HIỆN VẬT & KIẾN TRÚC</span>
      <h2>5 Kiệt Tác Di Sản Văn Hóa Trọng Điểm</h2>
      <p>Quan sát hiện vật, kiến trúc và hoa văn cổ truyền được số hóa độ nét cao phục vụ nghiên cứu mĩ thuật</p>
    </div>

    <div class="sah-exhibits-list">
      <!-- EXHIBIT 01: PHO HIEN -->
      <div class="sah-exhibit-card">
        <div class="sah-exhibit-num-col">
          <span class="sah-exhibit-num">01</span>
        </div>
        <div class="sah-exhibit-content-col">
          <div class="sah-exhibit-header">
            <h3>Quần Thể Di Tích Phố Hiến</h3>
            <span class="sah-exhibit-loc">TP. Hưng Yên • Thương cảng cổ thế kỷ XVII</span>
          </div>
          <div class="sah-exhibit-grid">
            <div class="sah-exhibit-text">
              <div class="sah-exhibit-quote">
                “Thứ nhất Kinh Kỳ, thứ nhì Phố Hiến” — thương cảng quốc tế hưng thịnh bậc nhất Đàng Ngoài, nơi hội tụ tinh hoa kiến trúc đình, đền, chùa truyền thống châu thổ Bắc Bộ cùng dấu ấn giao thương đa văn hóa.
              </div>
              <ul class="sah-exhibit-points">
                <li>✦ <b>Giá trị mĩ thuật:</b> Bố cục cổng tam quan uy nghiêm, mái đao cong thanh thoát, nghệ thuật chạm khắc vì kèo gỗ tinh xảo.</li>
                <li>✦ <b>Tư liệu học tập:</b> 15 bức ảnh số hóa chi tiết và hệ thống Hotspot phân tích 3 tầng ý nghĩa biểu tượng.</li>
              </ul>
              <div class="sah-exhibit-cta">
                <button type="button" class="sah-btn-exhibit-open" onclick="selectHeritageByCode('phohien')">
                  Khám phá Hồ sơ Phố Hiến (Bước 4) →
                </button>
              </div>
            </div>
            <div class="sah-exhibit-media">
              <div class="sah-exhibit-main-frame">
                <img id="exhibitImg01" src="assets/extracted/001_Pho_Hien_tong_quan.jpeg" alt="Phố Hiến" class="sah-exhibit-show-img">
              </div>
              <div class="sah-exhibit-filmstrip">
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('01', -1)" title="Ảnh trước">❮</button>
                <div class="sah-strip-track" id="thumbList01">
                  <img src="assets/extracted/001_Pho_Hien_tong_quan.jpeg" class="sah-exhibit-thumb active" onclick="switchExhibitImg('01', this.src, this)" alt="Toàn cảnh">
                  <img src="assets/extracted/003_Cong_tam_quan.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('01', this.src, this)" alt="Cổng tam quan">
                  <img src="assets/extracted/005_Kien_truc_co_Pho_Hien.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('01', this.src, this)" alt="Kiến trúc cổ">
                  <img src="assets/extracted/011_Kien_truc_go.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('01', this.src, this)" alt="Kiến trúc gỗ">
                </div>
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('01', 1)" title="Ảnh sau">❯</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- EXHIBIT 02: CHUA KEO -->
      <div class="sah-exhibit-card">
        <div class="sah-exhibit-num-col">
          <span class="sah-exhibit-num">02</span>
        </div>
        <div class="sah-exhibit-content-col">
          <div class="sah-exhibit-header">
            <h3>Chùa Keo — Tuyệt Tác Kiến Trúc Gỗ Cổ Truyền</h3>
            <span class="sah-exhibit-loc">xã Vũ Tiên, tỉnh Hưng Yên (Vũ Thư - Thái Bình cũ) • Khởi dựng năm 1632</span>
          </div>
          <div class="sah-exhibit-grid">
            <div class="sah-exhibit-text">
              <div class="sah-exhibit-quote">
                Đỉnh cao nghệ thuật kiến trúc gỗ cổ Việt Nam với Gác chuông 3 tầng 12 mái vút cao. Toàn bộ công trình dựng bằng gỗ lim theo kỹ thuật mộng truyền thống không dùng đinh kim loại, đạt độ cân xứng hình học hoàn mỹ.
              </div>
              <ul class="sah-exhibit-points">
                <li>✦ <b>Giá trị mĩ thuật:</b> Kết cấu đấu củng nhiều tầng độc nhất vô nhị, nhịp điệu tầng mái xếp lớp như những cánh hoa sen vươn tỏa.</li>
                <li>✦ <b>Mô hình 3D:</b> Đã được số hóa 3D WebGL cho phép xoay 360° cảm nhận tỉ lệ và khối tích không gian.</li>
              </ul>
              <div class="sah-exhibit-cta">
                <button type="button" class="sah-btn-exhibit-open" onclick="selectHeritageByCode('chuakeo')">
                  Khám phá Hồ sơ Chùa Keo (Bước 4) →
                </button>
              </div>
            </div>
            <div class="sah-exhibit-media">
              <div class="sah-exhibit-main-frame">
                <img id="exhibitImg02" src="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" alt="Chùa Keo" class="sah-exhibit-show-img">
              </div>
              <div class="sah-exhibit-filmstrip">
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('02', -1)" title="Ảnh trước">❮</button>
                <div class="sah-strip-track" id="thumbList02">
                  <img src="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" class="sah-exhibit-thumb active" onclick="switchExhibitImg('02', this.src, this)" alt="Toàn cảnh">
                  <img src="assets/extracted/042_Chi_tiet_trang_tri_kien_truc.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('02', this.src, this)" alt="Trang trí">
                  <img src="assets/extracted/053_Gac_chuong_ba_tang.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('02', this.src, this)" alt="Gác chuông">
                  <img src="assets/extracted/054_Gac_chuong_goc_nhin_khac.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('02', this.src, this)" alt="Chi tiết mái">
                </div>
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('02', 1)" title="Ảnh sau">❯</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- EXHIBIT 03: DEN TRAN -->
      <div class="sah-exhibit-card">
        <div class="sah-exhibit-num-col">
          <span class="sah-exhibit-num">03</span>
        </div>
        <div class="sah-exhibit-content-col">
          <div class="sah-exhibit-header">
            <h3>Đền Trần Long Hưng & Nghệ Thuật Điêu Khắc Thời Trần</h3>
            <span class="sah-exhibit-loc">xã Long Hưng, tỉnh Hưng Yên (Hưng Hà, tỉnh Thái Bình cũ) • Phát tích Vương triều Trần</span>
          </div>
          <div class="sah-exhibit-grid">
            <div class="sah-exhibit-text">
              <div class="sah-exhibit-quote">
                Nơi yên nghỉ của các vị vua khởi nghiệp nhà Trần, mang đậm hào khí Đông A. Không gian trang nghiêm với các công trình thờ tự bề thế và di sản điêu khắc đá, rồng chầu, mây lửa mang đặc trưng mĩ thuật thời Trần.
              </div>
              <ul class="sah-exhibit-points">
                <li>✦ <b>Giá trị mĩ thuật:</b> Hình tượng rồng thời Trần với thân mình mập mạp, uốn lượn dũng mãnh, móng vuốt sắc nhọn, biểu tượng cho sức mạnh quật cường.</li>
                <li>✦ <b>Tư liệu học tập:</b> Nghi môn, gian thờ các vua Trần và các mảng chạm khắc rồng phục vụ vẽ cách điệu.</li>
              </ul>
              <div class="sah-exhibit-cta">
                <button type="button" class="sah-btn-exhibit-open" onclick="selectHeritageByCode('dentran')">
                  Khám phá Hồ sơ Đền Trần (Bước 4) →
                </button>
              </div>
            </div>
            <div class="sah-exhibit-media">
              <div class="sah-exhibit-main-frame">
                <img id="exhibitImg03" src="assets/extracted/066_Nghi_mon_den_Tran.jpeg" alt="Đền Trần" class="sah-exhibit-show-img">
              </div>
              <div class="sah-exhibit-filmstrip">
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('03', -1)" title="Ảnh trước">❮</button>
                <div class="sah-strip-track" id="thumbList03">
                  <img src="assets/extracted/066_Nghi_mon_den_Tran.jpeg" class="sah-exhibit-thumb active" onclick="switchExhibitImg('03', this.src, this)" alt="Nghi môn">
                  <img src="assets/extracted/070_Gian_tho_vua_Tran_Thai_Tong.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('03', this.src, this)" alt="Gian thờ">
                  <img src="assets/extracted/081_Nghi_mon_den_Tran.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('03', this.src, this)" alt="Chi tiết nghi môn">
                  <img src="assets/extracted/085_Gian_tho_vua_Tran_Thai_Tong.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('03', this.src, this)" alt="Tượng thờ">
                </div>
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('03', 1)" title="Ảnh sau">❯</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- EXHIBIT 04: LE QUY DON -->
      <div class="sah-exhibit-card">
        <div class="sah-exhibit-num-col">
          <span class="sah-exhibit-num">04</span>
        </div>
        <div class="sah-exhibit-content-col">
          <div class="sah-exhibit-header">
            <h3>Khu Lưu Niệm Nhà Bác Học Lê Quý Đôn</h3>
            <span class="sah-exhibit-loc">xã Lê Quý Đôn, tỉnh Hưng Yên (Hưng Hà, tỉnh Thái Bình cũ) • Danh nhân văn hóa thế kỷ XVIII</span>
          </div>
          <div class="sah-exhibit-grid">
            <div class="sah-exhibit-text">
              <div class="sah-exhibit-quote">
                Tôn vinh trí tuệ lỗi lạc bậc nhất lịch sử phong kiến Việt Nam. Khu lưu niệm là bảo tàng sinh động về tinh thần hiếu học, sách cổ, hoành phi câu đối và các giá trị văn hóa tri thức trường tồn.
              </div>
              <ul class="sah-exhibit-points">
                <li>✦ <b>Giá trị mĩ thuật:</b> Bố cục từ đường truyền thống, hoành phi câu đối sơn son thếp vàng, hoa văn chữ triện và môtíp nho học.</li>
                <li>✦ <b>Cảm hứng sáng tạo:</b> Khơi gợi ý tưởng vẽ tranh chân dung, thiết kế bìa sách và biểu trưng học tập đương đại.</li>
              </ul>
              <div class="sah-exhibit-cta">
                <button type="button" class="sah-btn-exhibit-open" onclick="selectHeritageByCode('lequydon')">
                  Khám phá Hồ sơ Lê Quý Đôn (Bước 4) →
                </button>
              </div>
            </div>
            <div class="sah-exhibit-media">
              <div class="sah-exhibit-main-frame">
                <img id="exhibitImg04" src="assets/extracted/094_Chan_dung_bac_hoc_Le_Quy_Don.jpeg" alt="Lê Quý Đôn" class="sah-exhibit-show-img">
              </div>
              <div class="sah-exhibit-filmstrip">
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('04', -1)" title="Ảnh trước">❮</button>
                <div class="sah-strip-track" id="thumbList04">
                  <img src="assets/extracted/094_Chan_dung_bac_hoc_Le_Quy_Don.jpeg" class="sah-exhibit-thumb active" onclick="switchExhibitImg('04', this.src, this)" alt="Chân dung">
                  <img src="assets/extracted/096_Khu_luu_niem_nha_bac_hoc.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('04', this.src, this)" alt="Nhà lưu niệm">
                  <img src="assets/extracted/098_Khong_gian_tho_tu_noi_that.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('04', this.src, this)" alt="Nội thất">
                  <img src="assets/extracted/105_Hoi_thao_ky_niem_tai_khu_luu_n.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('04', this.src, this)" alt="Hoạt động lưu niệm">
                </div>
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('04', 1)" title="Ảnh sau">❯</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- EXHIBIT 05: DONG XAM -->
      <div class="sah-exhibit-card">
        <div class="sah-exhibit-num-col">
          <span class="sah-exhibit-num">05</span>
        </div>
        <div class="sah-exhibit-content-col">
          <div class="sah-exhibit-header">
            <h3>Làng Nghề Chạm Bạc Đồng Xâm — Tinh Hoa Kim Hoàn</h3>
            <span class="sah-exhibit-loc">xã Trà Giang, tỉnh Hưng Yên (Kiến Xương, tỉnh Thái Bình cũ) • Làng nghề truyền thống 500 năm</span>
          </div>
          <div class="sah-exhibit-grid">
            <div class="sah-exhibit-text">
              <div class="sah-exhibit-quote">
                Di sản phi vật thể và thủ công mĩ nghệ kim hoàn đỉnh cao. Các nghệ nhân Đồng Xâm nức danh với kỹ thuật chạm thúc bạc trổ thủng, tạo nên hoa văn rồng phượng, mây nước tinh xảo từng milimét trên mâm bạc, ống bạc.
              </div>
              <ul class="sah-exhibit-points">
                <li>✦ <b>Giá trị mĩ thuật:</b> Bố cục hoa văn tròn đồng tâm, kỹ thuật phân tầng độ nổi chìm, đường nét chạm trổ sắc sảo, mềm mại.</li>
                <li>✦ <b>Ứng dụng đồ họa:</b> Kho tư liệu hoa văn bạc quý giá để học sinh trích xuất họa tiết trang trí vào tác phẩm cá nhân.</li>
              </ul>
              <div class="sah-exhibit-cta">
                <button type="button" class="sah-btn-exhibit-open" onclick="selectHeritageByCode('dongxam')">
                  Khám phá Hồ sơ Đồng Xâm (Bước 4) →
                </button>
              </div>
            </div>
            <div class="sah-exhibit-media">
              <div class="sah-exhibit-main-frame">
                <img id="exhibitImg05" src="assets/extracted/136_San_pham_mam_cham_trang_tri.jpeg" alt="Chạm bạc Đồng Xâm" class="sah-exhibit-show-img">
              </div>
              <div class="sah-exhibit-filmstrip">
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('05', -1)" title="Ảnh trước">❮</button>
                <div class="sah-strip-track" id="thumbList05">
                  <img src="assets/extracted/136_San_pham_mam_cham_trang_tri.jpeg" class="sah-exhibit-thumb active" onclick="switchExhibitImg('05', this.src, this)" alt="Mâm bạc">
                  <img src="assets/extracted/125_Den_tho_To_nghe_kim_hoan_Dong_.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('05', this.src, this)" alt="Đền tổ nghề">
                  <img src="assets/extracted/126_Nghe_nhan_trong_xuong_cham_bac.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('05', this.src, this)" alt="Nghệ nhân chạm">
                  <img src="assets/extracted/150_Chi_tiet_hoa_van_rong_cham_noi.jpeg" class="sah-exhibit-thumb" onclick="switchExhibitImg('05', this.src, this)" alt="Rồng chạm nổi">
                </div>
                <button type="button" class="sah-strip-btn" onclick="rotateExhibitThumb('05', 1)" title="Ảnh sau">❯</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 4 TECH PILLARS SHOWCASE -->
  <div class="sah-landing-section">
    <div class="sah-landing-sec-head">
      <span class="sah-tag-pill">4 TRỤ CỘT CÔNG NGHỆ ĐỘT PHÁ</span>
      <h2>Nền Tảng Công Nghệ Đồng Hành Sáng Tạo</h2>
      <p>Sự kết hợp hài hòa giữa văn hóa truyền thống và công nghệ giáo dục hiện đại</p>
    </div>

    <div class="sah-pillars-grid">
      <div class="sah-pillar-card" onclick="goToSlide(5)" style="cursor:pointer;" title="Bấm để tới Trợ lý AI 5A">
        <div class="sah-pillar-top">
          <div class="sah-pillar-ico">🤖</div>
          <span class="sah-pillar-step-tag">BƯỚC 6</span>
        </div>
        <div class="sah-pillar-name">AI Art Assistant (5A)</div>
        <div class="sah-pillar-desc">
          Trợ lý AI khơi gợi tư duy mĩ thuật theo chu trình 5A: <b>Ask → Analyze → Advise → Adapt → Art</b>. AI không làm thay, chỉ đóng vai trò gợi mở để học sinh tự quyết định.
        </div>
        <div class="sah-pillar-rule">📌 Nguyên tắc: "Không quan sát = Không AI"</div>
      </div>

      <div class="sah-pillar-card" onclick="goToSlide(4)" style="cursor:pointer;" title="Bấm để tới Phòng 3D">
        <div class="sah-pillar-top">
          <div class="sah-pillar-ico">🧊</div>
          <span class="sah-pillar-step-tag">BƯỚC 5</span>
        </div>
        <div class="sah-pillar-name">Mô hình 3D tương tác WebGL</div>
        <div class="sah-pillar-desc">
          Số hóa không gian kiến trúc 3D xoay 360°, thu phóng đa góc nhìn. Giúp học sinh cảm nhận rõ hình khối, tỉ lệ và nhịp điệu kiến trúc trước khi vẽ phác thảo.
        </div>
        <div class="sah-pillar-rule">📌 Trải nghiệm xoay 360° trực quan trên trình duyệt</div>
      </div>

      <div class="sah-pillar-card" onclick="goToSlide(7)" style="cursor:pointer;" title="Bấm để tới Triển lãm AR">
        <div class="sah-pillar-top">
          <div class="sah-pillar-ico">📱</div>
          <span class="sah-pillar-step-tag">BƯỚC 8</span>
        </div>
        <div class="sah-pillar-name">Triển lãm Thực tế Tăng cường (AR)</div>
        <div class="sah-pillar-desc">
          Quét mã QR bằng điện thoại thông minh để đưa tranh vẽ của học sinh nổi 3D sống động trong không gian thực tại lớp học hoặc gia đình.
        </div>
        <div class="sah-pillar-rule">📌 Kết nối thực tế ảo tăng cường trên di động</div>
      </div>

      <div class="sah-pillar-card" onclick="goToSlide(1)" style="cursor:pointer;" title="Bấm để tới Bản đồ di sản">
        <div class="sah-pillar-top">
          <div class="sah-pillar-ico">🗺️</div>
          <span class="sah-pillar-step-tag">BƯỚC 2 & 4</span>
        </div>
        <div class="sah-pillar-name">Bản đồ số & 75 Hotspot 3 Tầng</div>
        <div class="sah-pillar-desc">
          Định vị 5 di sản văn hóa tiêu biểu, 75 tư liệu ảnh chất lượng cao và hệ thống Hotspot phân tích 3 tầng: <i>Cấu trúc bố cục → Hoa văn kỹ thuật → Biểu tượng ý nghĩa</i>.
        </div>
        <div class="sah-pillar-rule">📌 Cơ sở dữ liệu tư liệu chuẩn hóa</div>
      </div>
    </div>
  </div>

  <!-- INTERACTIVE ROADMAP FLOWCHART -->
  <div class="sah-landing-section">
    <div class="sah-landing-sec-head">
      <span class="sah-tag-pill">QUY TRÌNH SƯ PHẠM</span>
      <h2>Hành Trình Trải Nghiệm 9 Bước Tuần Tự</h2>
      <p>Học sinh đi qua từng trang theo thứ tự khoa học để hình thành tác phẩm độc bản</p>
    </div>

    <div class="sah-roadmap-track">
      <div class="sah-roadmap-step" onclick="goToSlide(0)" data-preview-img="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" data-preview-title="Bước 1 • Cổng Bảo Tàng Số" data-preview-sub="Khởi động & Khám phá trụ cột di sản" data-preview-badge="BƯỚC 1 / 9">
        <span class="sah-rm-num">1</span>
        <b>Trang chủ</b>
        <small>Khởi động & Trụ cột</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(1)" data-preview-img="assets/extracted/001_Pho_Hien_tong_quan.jpeg" data-preview-title="Bước 2 • Bản Đồ Văn Hóa Số" data-preview-sub="Định vị 5 di sản văn hóa trọng điểm Hưng Yên" data-preview-badge="BƯỚC 2 / 9">
        <span class="sah-rm-num">2</span>
        <b>Bản đồ số</b>
        <small>Định vị di sản</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(2)" data-preview-img="assets/extracted/066_Nghi_mon_den_Tran.jpeg" data-preview-title="Bước 3 • 5 Kiệt Tác Di Sản • Đền Trần Long Hưng" data-preview-sub="xã Long Hưng • Lăng mộ các vua Trần & Điêu khắc đá" data-preview-badge="BƯỚC 3 / 9">
        <span class="sah-rm-num">3</span>
        <b>5 Khu di sản</b>
        <small>Chọn hồ sơ nghiên cứu</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(3)" data-preview-img="assets/extracted/042_Chi_tiet_trang_tri_kien_truc.jpeg" data-preview-title="Bước 4 • Hồ Sơ 15 Ảnh & Hotspot" data-preview-sub="Quan sát tư liệu cấu trúc, kỹ thuật & biểu tượng" data-preview-badge="BƯỚC 4 / 9">
        <span class="sah-rm-num">4</span>
        <b>Hồ sơ 15 ảnh</b>
        <small>Hotspot 3 tầng</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(4)" data-preview-img="assets/heritage/diagram_3d_keo.svg" data-preview-title="Bước 5 • Phòng Tương Tác 3D" data-preview-sub="Số hóa WebGL xoay 360° cảm thụ hình khối" data-preview-badge="BƯỚC 5 / 9">
        <span class="sah-rm-num">5</span>
        <b>Phòng 3D</b>
        <small>Xoay 360° đa chiều</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(5)" data-preview-img="assets/heritage/diagram_ai_5a.svg" data-preview-title="Bước 6 • Trợ Lý AI Art Assistant 5A" data-preview-sub="Hỏi & Gợi mở ý tưởng sáng tạo mĩ thuật" data-preview-badge="BƯỚC 6 / 9">
        <span class="sah-rm-num">6</span>
        <b>AI 5A Studio</b>
        <small>Hỏi & Gợi mở ý tưởng</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(6)" data-preview-img="assets/extracted/126_Nghe_nhan_trong_xuong_cham_bac.jpeg" data-preview-title="Bước 7 • Xưởng Sáng Tạo & Phác Thảo" data-preview-sub="Biến đổi mô-đun hoa văn thành tác phẩm độc bản" data-preview-badge="BƯỚC 7 / 9">
        <span class="sah-rm-num">7</span>
        <b>Xưởng sáng tạo</b>
        <small>Phác thảo → Tác phẩm</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(7)" data-preview-img="assets/extracted/150_Chi_tiet_hoa_van_rong_cham_noi.jpeg" data-preview-title="Bước 8 • Triển Lãm Thực Tế Ảo (AR)" data-preview-sub="Trưng bày thực tế tăng cường trong không gian thực" data-preview-badge="BƯỚC 8 / 9">
        <span class="sah-rm-num">8</span>
        <b>Triển lãm AR</b>
        <small>Trưng bày thực tế ảo</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(8)" data-preview-img="assets/heritage/diagram_hotspot_321.svg" data-preview-title="Bước 9 • Đánh Giá Và Tự Hoàn Thiện" data-preview-sub="Phiếu tự đánh giá 3-2-1 & Rubric chấm điểm sư phạm" data-preview-badge="BƯỚC 9 / 9">
        <span class="sah-rm-num">9</span>
        <b>Đánh giá và tự hoàn thiện</b>
        <small>Phiếu 3-2-1 & Rubric</small>
      </div>
    </div>
  </div>

  <!-- DOCUMENTARY VIDEO SHOWCASE -->
  <div class="sah-landing-section">
    <div class="sah-landing-sec-head">
      <span class="sah-tag-pill">NGUỒN TƯ LIỆU SỐ HÓA</span>
      <h2>Phim Tài Liệu & Video Khám Phá Di Sản</h2>
      <p>Theo dõi các đoạn phim tư liệu chân thực về di tích lịch sử và danh nhân văn hóa</p>
    </div>

    <div class="sah-video-showcase">
      <div class="sah-video-player-wrap">
        <video id="landingVideoPlayer" controls playsinline style="width: 100%; border-radius: 12px; background: #000; aspect-ratio: 16/9;">
          <source id="videoSource" src="video%20v%E1%BB%81%20qu%E1%BA%A7n%20th%E1%BB%83%20ph%E1%BB%91%20hi%E1%BA%BFn.mp4" type="video/mp4">
          Trình duyệt của em không hỗ trợ phát video HTML5.
        </video>
        <div class="sah-video-caption" id="videoCaption">
          <b>Phim tài liệu:</b> Giới thiệu quần thể di tích quốc gia đặc biệt Phố Hiến
        </div>
      </div>

      <div class="sah-video-playlist">
        <div class="sah-video-item active" onclick="switchLandingVideo('video%20v%E1%BB%81%20qu%E1%BA%A7n%20th%E1%BB%83%20ph%E1%BB%91%20hi%E1%BA%BFn.mp4', 'Quần thể di tích lịch sử và văn hóa Phố Hiến – Hưng Yên', this)">
          <span class="sah-v-ico">▶</span>
          <div>
            <b>Quần thể di tích Phố Hiến</b>
            <small>Thương cảng cổ truyền & đô thị hưng thịnh thế kỷ XVII</small>
          </div>
        </div>
        <div class="sah-video-item" onclick="switchLandingVideo('Da%CC%81u%20a%CC%81n%20nha%CC%80%20Tra%CC%80n%20tre%CC%82n%20vu%CC%80ng%20%C4%91a%CC%81t%20Tha%CC%81i%20Bi%CC%80nh%20xWeb%20HYTV.mp4', 'Phim tài liệu 02: Dấu ấn vương triều Trần trên vùng đất Thái Bình xưa', this)">
          <span class="sah-v-ico">▶</span>
          <div>
            <b>Dấu ấn vương triều Trần</b>
            <small>Đền Trần Long Hưng & khu lăng mộ các vua Trần</small>
          </div>
        </div>
        <div class="sah-video-item" onclick="switchLandingVideo('Le%CC%82%20Quy%CC%81%20%C4%90o%CC%82n%20%E2%80%93%20Nha%CC%80%20Ba%CC%81c%20Ho%CC%A3c%20Vi%CC%83%20%C4%90a%CC%A3i%20Nha%CC%82%CC%81t%20Li%CC%A3ch%20Su%CC%9B%CC%89%20Phong%20Kie%CC%82%CC%81n%20Vie%CC%A3%CC%82t%20Nam.mp4', 'Phim tài liệu 03: Nhà bác học Lê Quý Đôn – Cuộc đời và trước tác vĩ đại', this)">
          <span class="sah-v-ico">▶</span>
          <div>
            <b>Nhà bác học Lê Quý Đôn</b>
            <small>Khu lưu niệm danh nhân văn hóa & truyền thống hiếu học</small>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- EDUCATIONAL STATS -->
  <div class="sah-landing-stats-grid">
    <div class="sah-lstat-card">
      <div class="sah-lstat-num">05</div>
      <div class="sah-lstat-lbl">Di sản văn hóa trọng điểm</div>
      <small>Số hóa 3D & Bản đồ tương tác</small>
    </div>
    <div class="sah-lstat-card">
      <div class="sah-lstat-num">75</div>
      <div class="sah-lstat-lbl">Tư liệu ảnh & Điểm chạm Hotspot</div>
      <small>Phân tích 3 tầng bố cục - hoa văn - ý nghĩa</small>
    </div>
    <div class="sah-lstat-card">
      <div class="sah-lstat-num">128</div>
      <div class="sah-lstat-lbl">Học sinh thực nghiệm sư phạm</div>
      <small>Đạt kết quả vượt trội so với lớp đối chứng</small>
    </div>
    <div class="sah-lstat-card">
      <div class="sah-lstat-num">+54%</div>
      <div class="sah-lstat-lbl">Tăng trưởng năng lực mĩ thuật</div>
      <small>Đo lường bằng Rubric chuẩn 4 mức độ</small>
    </div>
  </div>

  <!-- CALL TO ACTION BANNER -->
  <div class="sah-landing-cta-banner">
    <h3>Sẵn sàng bước vào hành trình sáng tạo Mĩ thuật di sản?</h3>
    <p>Chạm vào nút bên dưới để chuyển sang Trang 2 và định vị 5 di tích trên Bản đồ văn hóa số.</p>
    <button type="button" class="sah-btn-hero-primary" onclick="goToSlide(1)">
      Khám phá Trang 2: Bản đồ di sản Hưng Yên →
    </button>
  </div>

  {make_ppt_footer(1, "", "Bản đồ di sản Hưng Yên")}
</section>"""

# --------------------------------------------------------------------------
# 7. SLIDE 2: BẢN ĐỒ DI SẢN HƯNG YÊN (DEDICATED PAGE)
# --------------------------------------------------------------------------
STEP2_HTML = f"""<!-- STEP 2: BAN DO DI SAN HUNG YEN -->
<section id="step2-bando" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 2 / 9 • BẢN ĐỒ VĂN HÓA SỐ</div>
  <div class="sah-sec-header">
    <h2>🗺️ BẢN ĐỒ DI SẢN VĂN HÓA HƯNG YÊN</h2>
    <p class="sah-sec-sub">Bản đồ văn hóa số tương tác định vị 5 di sản văn hóa trọng điểm vùng châu thổ Sông Hồng. Chạm vào điểm ghim trên bản đồ hoặc thẻ di sản bên phải để chọn di sản và chuyển ngay sang hồ sơ khám phá 15 ảnh.</p>
  </div>
  
  <div class="sah-map-layout">
    <div class="sah-map-visual">
      {MAP_SVG}
    </div>
    <div class="sah-map-sidebar">
      <div class="sah-map-card-head">
        <b>CHỌN DI SẢN ĐỊNH VỊ:</b>
        <small>Nhấp để xem tư liệu chi tiết</small>
      </div>
      <div class="sah-map-list">
        <div class="sah-map-item" onclick="selectHeritageByCode('phohien')" data-preview-img="assets/extracted/001_Pho_Hien_tong_quan.jpeg" data-preview-title="01 • Quần Thể Di Tích Phố Hiến" data-preview-sub="TP. Hưng Yên • Thương cảng cổ thế kỷ XVII" data-preview-badge="ĐỊNH VỊ 01">
          <span class="sah-site-pill" style="background:#B3261E;">01</span>
          <div class="sah-map-thumb">
            <img src="assets/extracted/001_Pho_Hien_tong_quan.jpeg" alt="Phố Hiến" loading="lazy">
          </div>
          <div class="sah-item-info">
            <b>Phố Hiến</b>
            <p>TP. Hưng Yên • Quần thể di tích thương cảng cổ "Thứ nhất Kinh Kỳ, thứ nhì Phố Hiến".</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('chuakeo')" data-preview-img="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" data-preview-title="02 • Chùa Keo (Vũ Tiên)" data-preview-sub="xã Vũ Tiên, Hưng Yên (Vũ Thư cũ) • Khởi dựng năm 1632" data-preview-badge="ĐỊNH VỊ 02">
          <span class="sah-site-pill" style="background:#C89547;">02</span>
          <div class="sah-map-thumb">
            <img src="assets/extracted/032_Toan_canh_quan_the_Chua_Keo_tu.jpeg" alt="Chùa Keo" loading="lazy">
          </div>
          <div class="sah-item-info">
            <b>Chùa Keo</b>
            <p>xã Vũ Tiên (Vũ Thư cũ) • Đỉnh cao kiến trúc gỗ cổ truyền, gác chuông 3 tầng mái thanh thoát.</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('dentran')" data-preview-img="assets/extracted/066_Nghi_mon_den_Tran.jpeg" data-preview-title="03 • Đền Trần Long Hưng" data-preview-sub="xã Long Hưng, Hưng Yên (Hưng Hà cũ) • Nơi phát tích triều Trần" data-preview-badge="ĐỊNH VỊ 03">
          <span class="sah-site-pill" style="background:#285B46;">03</span>
          <div class="sah-map-thumb">
            <img src="assets/extracted/066_Nghi_mon_den_Tran.jpeg" alt="Đền Trần Long Hưng" loading="lazy">
          </div>
          <div class="sah-item-info">
            <b>Đền Trần Long Hưng</b>
            <p>xã Long Hưng (Hưng Hà cũ) • Nơi phát tích vương triều Trần, không gian trang nghiêm và khu lăng mộ vua.</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('lequydon')" data-preview-img="assets/extracted/094_Chan_dung_bac_hoc_Le_Quy_Don.jpeg" data-preview-title="04 • Khu Lưu Niệm Lê Quý Đôn" data-preview-sub="xã Lê Quý Đôn, Hưng Yên (Hưng Hà cũ) • Danh nhân văn hóa" data-preview-badge="ĐỊNH VỊ 04">
          <span class="sah-site-pill" style="background:#1B4965;">04</span>
          <div class="sah-map-thumb">
            <img src="assets/extracted/094_Chan_dung_bac_hoc_Le_Quy_Don.jpeg" alt="Lê Quý Đôn" loading="lazy">
          </div>
          <div class="sah-item-info">
            <b>Khu lưu niệm Lê Quý Đôn</b>
            <p>xã Lê Quý Đôn (Hưng Hà cũ) • Không gian tưởng niệm Nhà bác học uyên bác nhất lịch sử phong kiến Việt Nam.</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('dongxam')" data-preview-img="assets/extracted/136_San_pham_mam_cham_trang_tri.jpeg" data-preview-title="05 • Làng Chạm Bạc Đồng Xâm" data-preview-sub="xã Trà Giang, Hưng Yên (Kiến Xương cũ) • Kim hoàn 500 năm" data-preview-badge="ĐỊNH VỊ 05">
          <span class="sah-site-pill" style="background:#6B4226;">05</span>
          <div class="sah-map-thumb">
            <img src="assets/extracted/136_San_pham_mam_cham_trang_tri.jpeg" alt="Đồng Xâm" loading="lazy">
          </div>
          <div class="sah-item-info">
            <b>Làng chạm bạc Đồng Xâm</b>
            <p>xã Trà Giang (Kiến Xương cũ) • Nghệ thuật kim hoàn truyền thống, hoa văn chạm khắc tinh xảo.</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
      </div>
    </div>
  </div>

  {make_ppt_footer(2, "Trang chủ", "5 Khu di sản")}
</section>
"""

# --------------------------------------------------------------------------
# 8. SLIDE 3: 5 KHU DI SẢN (DEDICATED PAGE)
# --------------------------------------------------------------------------
STEP3_HTML = f"""<!-- STEP 3: 5 KHU DI SAN -->
<section id="step3-5khudisan" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 3 / 9 • LỰA CHỌN KHU DI SẢN</div>
  <div class="sah-sec-header">
    <h2>🏛️ 5 KHU DI SẢN VĂN HÓA TRỌNG ĐIỂM</h2>
    <p class="sah-sec-sub">Chạm vào một trong 5 thẻ di sản bên dưới để kích hoạt hồ sơ học tập. Khi chọn một hồ sơ, chỉ hồ sơ đó và 15 ảnh tư liệu tương ứng sẽ mở ra ở Bước 4, các hồ sơ khác được ẩn gọn gàng.</p>
  </div>
  
  {RADIOS_HTML}
  {TABS_HTML}

  {make_ppt_footer(3, "Bản đồ di sản", "Hồ sơ 15 ảnh & Hotspot")}
</section>
"""

# --------------------------------------------------------------------------
# 9. SLIDE 4: HỒ SƠ KHÁM PHÁ DI SẢN (15 PHOTOS & HOTSPOTS)
# --------------------------------------------------------------------------
STEP4_HTML = f"""<!-- STEP 4: HO SO KHAM PHA DI SAN -->
<section id="step4-hosodisan" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 4 / 9 • QUAN SÁT TƯ LIỆU SỐ</div>
  <div class="sah-sec-header">
    <h2>🔍 HỒ SƠ KHÁM PHÁ DI SẢN • 15 ẢNH & HOTSPOT 3 TẦNG</h2>
    <p class="sah-sec-sub">Mỗi di sản gồm 15 ảnh tư liệu độ phân giải cao và hệ thống Hotspot phân tích 3 tầng: <b>Tầng 1: Cấu trúc & bố cục</b> → <b>Tầng 2: Hoa văn & kỹ thuật</b> → <b>Tầng 3: Biểu tượng & ý nghĩa văn hóa</b>.</p>
  </div>

  <div class="sah-rule-banner">
    <span class="sah-rule-ico">⚠️</span>
    <div class="sah-rule-body">
      <b>NGUYÊN TẮC CỐT LÕI: KHÔNG QUAN SÁT = KHÔNG AI</b>
      <p>Học sinh cần quan sát kỹ tư liệu ảnh thực tế và mô hình 3D trước khi kích hoạt trợ lý AI 5A. AI chỉ đồng hành gợi ý, không sáng tạo thay con người.</p>
    </div>
  </div>

  {PANELS_HTML}
  {SWITCHER_HTML}

  {make_ppt_footer(4, "5 Khu di sản", "Phòng 3D tương tác")}
</section>
"""

# --------------------------------------------------------------------------
# 10. SLIDE 5: PHÒNG 3D TƯƠNG TÁC (WEBGL 360)
# --------------------------------------------------------------------------
RM_ROOM3D_SEC = """<section id="rmRoom3d" class="rm-sec">
  <h2>🧊 PHÒNG 3D • XOAY 360° TỪNG DI SẢN</h2>
  <p class="rm-sub">Mô hình 3D của 5 di sản, xoay và phóng to bằng chuột hoặc ngón tay (WebGL). Học sinh cảm nhận không gian và tỉ lệ kiến trúc trước khi sáng tạo.</p>
  <div class="rm-frame" id="rm3dWrap">
    <iframe id="rm3dFrame" title="Phòng 3D di sản" loading="lazy" allowfullscreen></iframe>
    <button type="button" class="rm-frame-cta" id="rm3dCta">▶ Mở phòng 3D</button>
  </div>
  <p class="rm-note">Muốn xem toàn màn hình: <a href="models.html">mở models.html ↗</a></p>
</section>"""

STEP5_HTML = f"""<!-- STEP 5: PHONG 3D TUONG TAC -->
<section id="step5-phong3d" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 5 / 9 • KHÔNG GIAN 3 CHIỀU</div>

  {RM_ROOM3D_SEC}

  {make_ppt_footer(5, "Hồ sơ 15 ảnh", "AI Art Assistant 5A")}
</section>
"""

# --------------------------------------------------------------------------
# 11. SLIDE 6: AI ART ASSISTANT 5A & CHAT
# --------------------------------------------------------------------------
RM_CHAT_SEC = """<section id="rmChat" class="rm-sec">
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
</section>"""

STEP6_HTML = f"""<!-- STEP 6: AI ART ASSISTANT 5A -->
<section id="step6-ai5a" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 6 / 9 • TRỢ LÝ AI ĐỒNG HÀNH</div>
  <div class="sah-sec-header">
    <h2>🤖 AI ART ASSISTANT – 5A • TỪ QUAN SÁT ĐẾN DẤU ẤN CÁ NHÂN</h2>
    <p class="sah-sec-sub">Quy trình sáng tạo 5A: <b>Ask (Hỏi & Khơi gợi)</b> → <b>Analyze (Phân tích nét di sản)</b> → <b>Advise (Gợi ý chất liệu/hình thức)</b> → <b>Adapt (Chuyển hóa phong cách cá nhân)</b> → <b>Art (Định hình tác phẩm)</b>. AI không làm thay học sinh, AI đặt câu hỏi gợi mở để em tự quyết định.</p>
  </div>

  <div class="sah-5a-process-bar">
    <div class="sah-5a-step"><b>1. ASK</b><span>Khơi gợi ý tưởng</span></div>
    <div class="sah-5a-arrow">→</div>
    <div class="sah-5a-step"><b>2. ANALYZE</b><span>Phân tích tư liệu</span></div>
    <div class="sah-5a-arrow">→</div>
    <div class="sah-5a-step"><b>3. ADVISE</b><span>Gợi ý phương án</span></div>
    <div class="sah-5a-arrow">→</div>
    <div class="sah-5a-step"><b>4. ADAPT</b><span>Chuyển hóa cá nhân</span></div>
    <div class="sah-5a-arrow">→</div>
    <div class="sah-5a-step"><b>5. ART</b><span>Định hình tác phẩm</span></div>
  </div>

  {AI5A_BLOCK}
  {RM_CHAT_SEC}

  {make_ppt_footer(6, "Phòng 3D", "Xưởng sáng tạo")}
</section>
"""

# --------------------------------------------------------------------------
# 12. SLIDE 7: XƯỞNG SÁNG TẠO (SKETCH & ART COMPLETION)
# --------------------------------------------------------------------------
STEP7_HTML = f"""<!-- STEP 7: XUONG SANG TAO -->
<section id="step7-xuongsangtao" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 7 / 9 • THỰC HÀNH SÁNG TẠO</div>
  <div class="sah-sec-header">
    <h2>✏️ XƯỞNG SÁNG TẠO • TỪ PHÁC THẢO ĐẾN TÁC PHẨM HOÀN THIỆN</h2>
    <p class="sah-sec-sub">Hành trình 4 giai đoạn sáng tạo Mĩ thuật: <b>1. Ý tưởng cốt lõi</b> → <b>2. Thử nghiệm 3 phương án phác thảo</b> → <b>3. Phương án chọn</b> → <b>4. Bàn thực hành tác phẩm hoàn thiện</b>.</p>
  </div>

  <div class="sah-studio-flow">
    <div class="sah-flow-badge">Giai đoạn 1: Ý tưởng cốt lõi</div>
    <div class="sah-flow-sep">➔</div>
    <div class="sah-flow-badge">Giai đoạn 2: Phác thảo 1, 2, 3</div>
    <div class="sah-flow-sep">➔</div>
    <div class="sah-flow-badge">Giai đoạn 3: Phương án chọn</div>
    <div class="sah-flow-sep">➔</div>
    <div class="sah-flow-badge">Giai đoạn 4: Tác phẩm hoàn thiện</div>
  </div>

  {SKETCH_BLOCK}
  {ART_BLOCK}

  {make_ppt_footer(7, "AI Art Assistant 5A", "Triển lãm AR Gallery")}
</section>
"""

# --------------------------------------------------------------------------
# 13. SLIDE 8: AR GALLERY (EXHIBITION & MOBILE AR QR)
# --------------------------------------------------------------------------
RM_EXHIBIT_SEC = """<section id="rmExhibit" class="rm-sec">
  <h2>🖼️ TRIỂN LÃM TÁC PHẨM • HỒ SƠ LỚP</h2>
  <p class="rm-sub">Tác phẩm em lưu sẽ xuất hiện ở đây và trong Trang Quản Trị của giáo viên.</p>
  <div class="rm-stats" id="rmStats"></div>
  <div class="rm-tools">
    <input id="rmSearch" type="search" placeholder="Tìm theo tên tác phẩm, mã học sinh, lớp...">
    <select id="rmFilter">
      <option value="">Tất cả di sản</option>
      <option value="phohien">Phố Hiến</option><option value="chuakeo">Chùa Keo</option>
      <option value="dentran">Đền Trần</option><option value="lequydon">Lê Quý Đôn</option>
      <option value="dongxam">Làng nghề chạm bạc Đồng Xâm</option>
    </select>
    <button type="button" class="rm-btn" id="rmSaveWork">💾 Lưu tác phẩm của em vào triển lãm</button>
    <button type="button" class="rm-btn ghost" id="rmExport321">⬇ Xuất phiếu 3–2–1</button>
    <span class="rm-note" id="rmWorkMsg"></span>
    <span class="rm-note" id="rmExportMsg"></span>
  </div>
  <div class="rm-grid" id="rmGallery"></div>
  <p class="rm-note" id="rmGalleryEmpty"></p>
</section>"""

STEP8_HTML = f"""<!-- STEP 8: AR GALLERY -->
<section id="step8-argallery" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 8 / 9 • TRIỂN LÃM & CÔNG NGHỆ AR</div>
  <div class="sah-sec-header">
    <h2>🖼️ AR GALLERY • TRIỂN LÃM THỰC TẾ TĂNG CƯỜNG (AR)</h2>
    <p class="sah-sec-sub">Không gian trưng bày tác phẩm số của học sinh kết hợp công nghệ Thực tế Tăng cường (AR). Quét mã QR bằng điện thoại để xem tranh nổi trong không gian thực qua camera di động.</p>
  </div>

  <div class="sah-ar-card">
    <div class="sah-ar-info">
      <span class="sah-ar-tag">📱 CÔNG NGHỆ THỰC TẾ TĂNG CƯỜNG (AR)</span>
      <h3>Xem tranh nổi 3D trong không gian thực qua camera điện thoại</h3>
      <p>Học sinh, giáo viên và phụ huynh có thể dùng camera điện thoại quét mã QR bên cạnh để trình chiếu tác phẩm mĩ thuật nổi 3D ngay trong phòng học, không gian triển lãm hoặc tại nhà.</p>
      <div class="sah-ar-actions">
        <button type="button" class="rm-btn" onclick="openArDemoModal()">📱 Mở chế độ xem thử AR trên Web</button>
        <a href="trien-lam.html" class="rm-btn ghost">🗂️ Mở trang Triển lãm độc lập ↗</a>
      </div>
    </div>
    <div class="sah-ar-qr">
      <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
        <rect width="120" height="120" rx="12" fill="#FFFFFF"/>
        <rect x="12" y="12" width="30" height="30" rx="4" fill="#172119"/>
        <rect x="18" y="18" width="18" height="18" rx="2" fill="#FFFFFF"/>
        <rect x="22" y="22" width="10" height="10" rx="1" fill="#172119"/>
        <rect x="78" y="12" width="30" height="30" rx="4" fill="#172119"/>
        <rect x="84" y="18" width="18" height="18" rx="2" fill="#FFFFFF"/>
        <rect x="88" y="22" width="10" height="10" rx="1" fill="#172119"/>
        <rect x="12" y="78" width="30" height="30" rx="4" fill="#172119"/>
        <rect x="18" y="84" width="18" height="18" rx="2" fill="#FFFFFF"/>
        <rect x="22" y="88" width="10" height="10" rx="1" fill="#172119"/>
        <rect x="52" y="16" width="16" height="8" rx="2" fill="#172119"/>
        <rect x="52" y="32" width="8" height="16" rx="2" fill="#172119"/>
        <rect x="68" y="44" width="16" height="8" rx="2" fill="#172119"/>
        <rect x="52" y="60" width="16" height="16" rx="2" fill="#172119"/>
        <rect x="76" y="76" width="16" height="8" rx="2" fill="#172119"/>
        <rect x="96" y="60" width="12" height="12" rx="2" fill="#172119"/>
        <rect x="76" y="96" width="20" height="12" rx="2" fill="#172119"/>
        <circle cx="60" cy="60" r="6" fill="#C89547"/>
      </svg>
      <small>Quét mã QR để mở AR trên di động</small>
    </div>
  </div>

  {EXHIBIT_BLOCK}
  {RM_EXHIBIT_SEC}

  {make_ppt_footer(8, "Xưởng sáng tạo", "Đánh giá và tự hoàn thiện")}
</section>
"""

# --------------------------------------------------------------------------
# 14. SLIDE 9: ĐÁNH GIÁ & PHẢN TƯ (3-2-1, RUBRIC, PRE-POST CHART, JOURNEY)
# --------------------------------------------------------------------------
RUBRIC_PREPOST_HTML = """
<div class="sah-eval-container">
  <!-- Rubric standard table -->
  <div class="sah-rubric-card">
    <div class="sah-eval-head">
      <h3>📊 RUBRIC ĐÁNH GIÁ MĨ THUẬT THEO TIÊU CHÍ CHUẨN</h3>
      <span class="sah-eval-badge">Thang điểm 4 mức độ</span>
    </div>
    <p class="sah-eval-sub">Khung đánh giá năng lực Mĩ thuật di sản và tính sáng tạo cá nhân (theo hồ sơ nghiên cứu Smart Art Heritage):</p>
    <div class="sah-rubric-table-wrap">
      <table class="sah-rubric-tbl">
        <thead>
          <tr>
            <th>Tiêu chí đánh giá</th>
            <th>Mức 1: Cần cố gắng (&lt;5đ)</th>
            <th>Mức 2: Đạt (5–6.9đ)</th>
            <th>Mức 3: Tốt (7–8.9đ)</th>
            <th>Mức 4: Xuất sắc (9–10đ)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><b>1. Nhận thức di sản (25%)</b><br><small>Quan sát & phát hiện giá trị tạo hình</small></td>
            <td>Nhận biết sơ sài, chưa liên hệ tư liệu ảnh quan sát</td>
            <td>Chỉ ra được 1–2 nét di sản cơ bản</td>
            <td>Nhận diện rõ đặc điểm kiến trúc, hoa văn, chất liệu</td>
            <td>Phát hiện sâu sắc cấu trúc, tỷ lệ và hồn cốt văn hóa di sản</td>
          </tr>
          <tr>
            <td><b>2. Ý tưởng sáng tạo (25%)</b><br><small>Biến đổi & tạo dấu ấn cá nhân</small></td>
            <td>Sao chép nguyên bản, thiếu tính đổi mới</td>
            <td>Có ý tưởng mới nhưng chưa thật sự rõ nét</td>
            <td>Có 3 phương án phác thảo, chọn lọc hợp lý</td>
            <td>Độc bản, đột phá về ngôn ngữ tạo hình và thông điệp sâu sắc</td>
          </tr>
          <tr>
            <td><b>3. Kỹ thuật tạo hình (25%)</b><br><small>Bố cục, nét, màu sắc, chất liệu</small></td>
            <td>Kỹ thuật yếu, bố cục rời rạc</td>
            <td>Kỹ thuật đạt yêu cầu cơ bản</td>
            <td>Bố cục cân đối, hòa sắc hài hòa, nét vững vàng</td>
            <td>Làm chủ kỹ thuật và chất liệu, tính thẩm mĩ và biểu cảm cao</td>
          </tr>
          <tr>
            <td><b>4. Ứng dụng AI & Phản tư (25%)</b><br><small>Sử dụng AI có trách nhiệm, phiếu 3-2-1</small></td>
            <td>Phụ thuộc AI hoàn toàn hoặc bỏ qua phản tư</td>
            <td>Hoàn thành phiếu 3-2-1 ở mức cơ bản</td>
            <td>Làm chủ AI 5A, giải thích được quyết định sáng tạo của mình</td>
            <td>Phản tư sâu sắc, sử dụng AI thông minh, làm rõ bản quyền tác giả</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Pre-test vs Post-test Comparison Chart -->
  <div class="sah-prepost-card">
    <div class="sah-eval-head">
      <h3>📈 ĐỐI SÁNH KẾT QUẢ THỰC NGHIỆM SƯ PHẠM</h3>
      <span class="sah-eval-badge gold">Pre-test vs Post-test</span>
    </div>
    <p class="sah-eval-sub">Dữ liệu thực nghiệm trên 128 học sinh trước và sau khi ứng dụng hệ sinh thái Smart Art Heritage:</p>
    
    <div class="sah-chart-grid">
      <div class="sah-chart-item">
        <div class="sah-chart-label">
          <span>Hiểu biết di sản địa phương</span>
          <b>38% ➔ 92% (+54%)</b>
        </div>
        <div class="sah-chart-bars">
          <div class="sah-bar-pre" style="width:38%" title="Pre-test: 38%"><span>38%</span></div>
          <div class="sah-bar-post" style="width:92%" title="Post-test: 92%"><span>92%</span></div>
        </div>
      </div>

      <div class="sah-chart-item">
        <div class="sah-chart-label">
          <span>Năng lực phát triển ý tưởng mĩ thuật</span>
          <b>42% ➔ 89% (+47%)</b>
        </div>
        <div class="sah-chart-bars">
          <div class="sah-bar-pre" style="width:42%" title="Pre-test: 42%"><span>42%</span></div>
          <div class="sah-bar-post" style="width:89%" title="Post-test: 89%"><span>89%</span></div>
        </div>
      </div>

      <div class="sah-chart-item">
        <div class="sah-chart-label">
          <span>Ứng dụng AI có trách nhiệm (AI 5A)</span>
          <b>15% ➔ 95% (+80%)</b>
        </div>
        <div class="sah-chart-bars">
          <div class="sah-bar-pre" style="width:15%" title="Pre-test: 15%"><span>15%</span></div>
          <div class="sah-bar-post" style="width:95%" title="Post-test: 95%"><span>95%</span></div>
        </div>
      </div>

      <div class="sah-chart-item">
        <div class="sah-chart-label">
          <span>Hứng thú học tập Mĩ thuật di sản</span>
          <b>45% ➔ 96% (+51%)</b>
        </div>
        <div class="sah-chart-bars">
          <div class="sah-bar-pre" style="width:45%" title="Pre-test: 45%"><span>45%</span></div>
          <div class="sah-bar-post" style="width:96%" title="Post-test: 96%"><span>96%</span></div>
        </div>
      </div>

      <div class="sah-chart-item">
        <div class="sah-chart-label">
          <span>Tỷ lệ hoàn thành tác phẩm chất lượng cao</span>
          <b>52% ➔ 98% (+46%)</b>
        </div>
        <div class="sah-chart-bars">
          <div class="sah-bar-pre" style="width:52%" title="Pre-test: 52%"><span>52%</span></div>
          <div class="sah-bar-post" style="width:98%" title="Post-test: 98%"><span>98%</span></div>
        </div>
      </div>
    </div>

    <div class="sah-chart-legend">
      <span><i class="sah-dot-pre"></i> Trước thực nghiệm (Pre-test)</span>
      <span><i class="sah-dot-post"></i> Sau thực nghiệm với Smart Art Heritage (Post-test)</span>
    </div>
  </div>
</div>
"""

# In Step 9, footer adapts dynamically via JS whether teacher or student
STEP9_HTML = f"""<!-- STEP 9: DANH GIA & TU HOAN THIEN -->
<section id="step9-danhgia" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 9 / 9 • ĐÁNH GIÁ VÀ TỰ HOÀN THIỆN</div>
  <div class="sah-sec-header">
    <h2>📝 ĐÁNH GIÁ VÀ TỰ HOÀN THIỆN • PHIẾU 3-2-1 & HỒ SƠ HÀNH TRÌNH</h2>
    <p class="sah-sec-sub">Phiếu tổng kết 3-2-1, Tự đánh giá của học sinh & Đánh giá của giáo viên theo Rubric chuẩn. Đối sánh năng lực sư phạm và lưu trữ Hồ sơ hành trình sáng tạo cá nhân.</p>
  </div>

  {SAH321_BLOCK}
  {P321_BLOCK}
  {RUBRIC_PREPOST_HTML}
  {JOURNEY39_BLOCK}

  <!-- Footer with dynamic Next/Finish handling -->
  <div class="sah-ppt-nav-bar" id="step9NavBar">
    <button type="button" class="sah-ppt-btn sah-ppt-prev" onclick="goToSlide(7)">
      <span class="sah-ppt-arr">←</span> 
      <span class="sah-ppt-lbl">Quay lại: <b>Triển lãm AR Gallery</b></span>
    </button>
    
    <div class="sah-ppt-indicator">
      <div class="sah-ppt-slide-num">Trang <b>9</b> / <span class="sah-dyn-total">9</span></div>
      <div class="sah-ppt-key-hint">Dùng phím <kbd>←</kbd> <kbd>→</kbd> để chuyển trang</div>
    </div>

    <button type="button" class="sah-ppt-btn sah-ppt-next sah-ppt-finish student-or-guest-action" onclick="goToSlide(0)">
      <span class="sah-ppt-lbl">Hoàn thành hành trình 🎉 (Về Trang chủ)</span> 
      <span class="sah-ppt-arr">↑</span>
    </button>
    
    <button type="button" class="sah-ppt-btn sah-ppt-next teacher-only" style="display:none;" onclick="goToSlide(9)">
      <span class="sah-ppt-lbl">Tiếp tục: <b>Dashboard Quản trị GV</b></span> 
      <span class="sah-ppt-arr">→</span>
    </button>
  </div>
</section>
"""

# --------------------------------------------------------------------------
# 15. SLIDE 10: TEACHER DASHBOARD (TEACHER ONLY)
# --------------------------------------------------------------------------
STEP_DASHBOARD_HTML = f"""<!-- STEP 10: TEACHER DASHBOARD (TEACHER ONLY) -->
<section id="step-dashboard" class="sah-step-sec sah-dashboard-sec sah-slide teacher-only" style="display:none;">
  <div class="sah-step-badge">DÀNH CHO GIÁO VIÊN • TRANG QUẢN TRỊ</div>
  <div class="sah-sec-header">
    <h2>👩‍🏫 DASHBOARD GIÁO VIÊN & THỐNG KÊ KẾT QUẢ</h2>
    <p class="sah-sec-sub">Theo dõi tiến độ toàn lớp theo thời gian thực, chấm bài theo Rubric chuẩn, xuất báo cáo tổng kết và quản lý ngân hàng câu hỏi phục vụ giảng dạy.</p>
  </div>

  <div class="sah-dash-grid">
    <div class="sah-dash-card">
      <div class="sah-dash-num">128</div>
      <div class="sah-dash-lbl">Học sinh tích cực tham gia</div>
      <small>Độ phủ đầy đủ cả 5 di sản văn hóa</small>
    </div>
    <div class="sah-dash-card">
      <div class="sah-dash-num">86%</div>
      <div class="sah-dash-lbl">Tỷ lệ hoàn thành trọn vẹn 9 bước</div>
      <small>Tăng 34% so với lớp đối chứng</small>
    </div>
    <div class="sah-dash-card">
      <div class="sah-dash-num">245</div>
      <div class="sah-dash-lbl">Tác phẩm đã nộp vào triển lãm</div>
      <small>Kèm đủ phác thảo và thuyết minh</small>
    </div>
    <div class="sah-dash-card">
      <div class="sah-dash-num">100%</div>
      <div class="sah-dash-lbl">Học sinh nhận phản hồi sư phạm</div>
      <small>Từ trợ lý AI 5A và giáo viên bộ môn</small>
    </div>
  </div>

  <div class="sah-dash-actions">
    <a href="giao-vien.html" class="rm-btn" style="padding:14px 28px;font-size:15px;display:inline-block;text-decoration:none;">👩‍🏫 Truy cập Trang Quản Trị Giáo Viên (giao-vien.html) ↗</a>
  </div>

  {make_ppt_footer(10, "Đánh giá và tự hoàn thiện", "Trang chủ", is_last=True)}
</section>
"""

# --------------------------------------------------------------------------
# 16. Modals
# --------------------------------------------------------------------------
MODALS_HTML = """<!-- RESTORED MODALS -->
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

<!-- Simulated AR Demo Modal -->
<div class="rm-modal" id="arDemoModal" hidden>
  <div class="rm-modal-card" style="max-width:580px;text-align:center;">
    <button class="rm-modal-x" type="button" onclick="closeArDemoModal()">✕</button>
    <h3>📱 Trải nghiệm Thực tế Tăng cường (AR)</h3>
    <p class="rm-sub">Mô phỏng tác phẩm mĩ thuật chiếu trong không gian thực qua camera di động:</p>
    <div style="background:#172119;border-radius:16px;padding:20px;position:relative;overflow:hidden;min-height:300px;display:flex;align-items:center;justify-content:center;">
      <div style="position:absolute;inset:0;opacity:0.25;background:repeating-linear-gradient(45deg, #285b46 0, #285b46 10px, #12281f 10px, #12281f 20px);"></div>
      <div style="position:relative;background:#fff;border-radius:12px;padding:12px;box-shadow:0 20px 40px rgba(0,0,0,0.6);transform:perspective(600px) rotateY(-10deg) rotateX(8deg);max-width:280px;">
        <img src="assets/extracted/000_Ph__Hi_n.jpeg" alt="Tác phẩm mẫu" style="width:100%;height:180px;object-fit:cover;border-radius:8px;">
        <div style="padding:8px 4px;text-align:left;">
          <b style="color:#172119;font-size:13px;display:block;">Dấu ấn Phố Hiến xưa và nay</b>
          <small style="color:#667069;font-size:11px;">Mô phỏng 3D AR • Tỉ lệ 1:1 trong phòng</small>
        </div>
      </div>
    </div>
    <p class="rm-note" style="margin-top:12px;">Trên điện thoại, camera sẽ tự động nhận diện mặt phẳng bàn hoặc tường để đặt tranh.</p>
    <button type="button" class="rm-btn" onclick="closeArDemoModal()">Đóng cửa sổ AR</button>
  </div>
</div>
"""

# --------------------------------------------------------------------------
# 17. CSS for Landing Page & PowerPoint Presentation Mode
# --------------------------------------------------------------------------
GUIDELINE_CSS = """<!-- SAH-GUIDELINE-CSS-START -->
<style>
/* ==========================================================================
   SMART ART HERITAGE — LUXURY MUSEUM EXHIBITION DESIGN SYSTEM
   Inspired by Classical Cultural Heritage & Curatorial Architecture
   ========================================================================== */

:root {
  --sah-bg-obsidian: #090807;
  --sah-bg-surface: #12100e;
  --sah-bg-card: rgba(22, 19, 16, 0.92);
  --sah-bg-card-hover: rgba(30, 26, 22, 0.98);
  --sah-gold-primary: #d4af37;
  --sah-gold-bright: #f5d475;
  --sah-gold-deep: #b38b22;
  --sah-gold-glow: rgba(212, 175, 55, 0.18);
  --sah-gold-border: rgba(212, 175, 55, 0.24);
  --sah-gold-subtle: rgba(212, 175, 55, 0.1);
  --sah-text-heading: #fcfaf6;
  --sah-text-body: #e2dacf;
  --sah-text-muted: #a39988;
  --sah-font-display: 'Cinzel', serif;
  --sah-font-serif: 'Playfair Display', Georgia, serif;
  --sah-font-sans: 'Plus Jakarta Sans', system-ui, sans-serif;
}

html {
  overflow-x: hidden;
  max-width: 100vw;
}
body {
  overflow-x: hidden;
  max-width: 100vw;
}

/* Base Body in Slide Mode with Dynamic Thematic Backgrounds */
body.slide-mode {
  background-color: var(--sah-bg-obsidian);
  color: var(--sah-text-body);
  font-family: var(--sah-font-sans);
  min-height: 100vh;
  overflow-x: hidden;
  max-width: 100vw;
  position: relative;
  transition: background-color 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Atmospheric Viewport Site Background Layer */
body.slide-mode::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 1;
  transition: opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1), background 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  background-attachment: fixed;
}

/* Default / Slide 1: Trang Chu - Royal Museum Atrium & Golden Sunburst */
body.slide-mode::before,
body.slide-mode[data-active-slide="step1-trangchu"]::before {
  background:
    radial-gradient(ellipse 95% 65% at 50% -12%, rgba(212, 175, 55, 0.22) 0%, rgba(180, 130, 30, 0.08) 45%, transparent 70%),
    radial-gradient(circle at 12% 40%, rgba(184, 115, 51, 0.12) 0%, transparent 45%),
    radial-gradient(circle at 88% 60%, rgba(212, 175, 55, 0.10) 0%, transparent 45%);
}

/* Slide 2: Ban Do - Red River Delta Topography & Silt-Emerald Cartography */
body.slide-mode[data-active-slide="step2-bando"]::before {
  background:
    radial-gradient(ellipse 85% 55% at 20% 30%, rgba(37, 99, 235, 0.18) 0%, transparent 60%),
    radial-gradient(ellipse 75% 65% at 85% 65%, rgba(40, 91, 70, 0.22) 0%, transparent 60%),
    radial-gradient(circle at 50% -10%, rgba(212, 175, 55, 0.12) 0%, transparent 55%),
    repeating-linear-gradient(45deg, rgba(37, 99, 235, 0.012) 0px, rgba(37, 99, 235, 0.012) 1px, transparent 1px, transparent 14px);
}
body.slide-mode[data-active-slide="step2-bando"] {
  background-color: #060b09;
}

/* Slide 3: 5 Khu Di San - Royal Temple Sanctuary & Lacquered Vermilion-Amber */
body.slide-mode[data-active-slide="step3-5khudisan"]::before {
  background:
    radial-gradient(ellipse 85% 55% at 50% 0%, rgba(185, 28, 28, 0.22) 0%, rgba(120, 20, 20, 0.08) 45%, transparent 75%),
    radial-gradient(circle at 15% 45%, rgba(212, 175, 55, 0.14) 0%, transparent 50%),
    radial-gradient(circle at 85% 55%, rgba(180, 83, 9, 0.14) 0%, transparent 50%);
}
body.slide-mode[data-active-slide="step3-5khudisan"] {
  background-color: #0e0706;
}

/* Slide 4: Ho So Di San - Curatorial Library & Archival Indigo */
body.slide-mode[data-active-slide="step4-hosodisan"]::before {
  background:
    radial-gradient(ellipse 80% 55% at 30% 10%, rgba(30, 58, 138, 0.22) 0%, transparent 65%),
    radial-gradient(ellipse 75% 50% at 80% 30%, rgba(212, 175, 55, 0.12) 0%, transparent 60%),
    radial-gradient(circle at 50% 80%, rgba(15, 23, 42, 0.30) 0%, transparent 60%);
}
body.slide-mode[data-active-slide="step4-hosodisan"] {
  background-color: #070912;
}

/* Slide 5: Phong 3D - Cybernetic Cobalt & Hologram Virtual Studio */
body.slide-mode[data-active-slide="step5-phong3d"]::before {
  background:
    radial-gradient(ellipse 80% 55% at 50% 15%, rgba(37, 99, 235, 0.24) 0%, rgba(6, 182, 212, 0.10) 45%, transparent 75%),
    radial-gradient(circle at 15% 75%, rgba(59, 130, 246, 0.14) 0%, transparent 50%),
    radial-gradient(circle at 85% 75%, rgba(14, 165, 233, 0.12) 0%, transparent 50%);
}
body.slide-mode[data-active-slide="step5-phong3d"] {
  background-color: #050812;
}

/* Slide 6: AI 5A - Neural Intelligence Studio & Amethyst Constellations */
body.slide-mode[data-active-slide="step6-ai5a"]::before {
  background:
    radial-gradient(ellipse 85% 55% at 50% 15%, rgba(147, 51, 234, 0.22) 0%, rgba(168, 85, 247, 0.08) 45%, transparent 75%),
    radial-gradient(circle at 20% 50%, rgba(212, 175, 55, 0.12) 0%, transparent 50%),
    radial-gradient(circle at 80% 60%, rgba(99, 102, 241, 0.16) 0%, transparent 50%);
}
body.slide-mode[data-active-slide="step6-ai5a"] {
  background-color: #0a0614;
}

/* Slide 7: Xuong Sang Tao - Artist Atelier & Fine-Art Ochre Canvas */
body.slide-mode[data-active-slide="step7-xuongsangtao"]::before {
  background:
    radial-gradient(ellipse 80% 55% at 40% 15%, rgba(217, 119, 6, 0.20) 0%, transparent 65%),
    radial-gradient(circle at 80% 40%, rgba(180, 83, 9, 0.16) 0%, transparent 55%),
    radial-gradient(circle at 20% 75%, rgba(212, 175, 55, 0.12) 0%, transparent 50%);
}
body.slide-mode[data-active-slide="step7-xuongsangtao"] {
  background-color: #0f0b07;
}

/* Slide 8: Trien Lam AR - Spatial Teal Gallery & Augmented Reality Lighting */
body.slide-mode[data-active-slide="step8-argallery"]::before {
  background:
    radial-gradient(ellipse 80% 50% at 50% 5%, rgba(16, 185, 129, 0.20) 0%, rgba(6, 182, 212, 0.10) 45%, transparent 75%),
    radial-gradient(circle at 15% 60%, rgba(20, 184, 166, 0.14) 0%, transparent 50%),
    radial-gradient(circle at 85% 60%, rgba(52, 211, 153, 0.12) 0%, transparent 50%);
}
body.slide-mode[data-active-slide="step8-argallery"] {
  background-color: #050d0b;
}

/* Slide 9: Danh Gia & Tu Hoan Thien - Serene Zen Gold & Reflection Pavilion */
body.slide-mode[data-active-slide="step9-danhgia"]::before {
  background:
    radial-gradient(ellipse 85% 55% at 50% 15%, rgba(212, 175, 55, 0.24) 0%, rgba(202, 138, 4, 0.10) 45%, transparent 75%),
    radial-gradient(circle at 20% 50%, rgba(180, 83, 9, 0.12) 0%, transparent 50%),
    radial-gradient(circle at 80% 50%, rgba(212, 175, 55, 0.12) 0%, transparent 50%);
}
body.slide-mode[data-active-slide="step9-danhgia"] {
  background-color: #0d0a07;
}

/* Slide 10: Teacher Dashboard - Scholastic Command Observatory & Navy-Gold */
body.slide-mode[data-active-slide="step-dashboard"]::before {
  background:
    radial-gradient(ellipse 85% 50% at 50% 0%, rgba(59, 130, 246, 0.22) 0%, rgba(29, 78, 216, 0.10) 45%, transparent 75%),
    radial-gradient(circle at 15% 45%, rgba(212, 175, 55, 0.14) 0%, transparent 50%),
    radial-gradient(circle at 85% 55%, rgba(37, 99, 235, 0.16) 0%, transparent 50%);
}
body.slide-mode[data-active-slide="step-dashboard"] {
  background-color: #060914;
}

/* Distinctive Slide Container Backgrounds */
#step1-trangchu {
  background: linear-gradient(180deg, #161310 0%, #100e0c 100%) !important;
  border-color: rgba(212, 175, 55, 0.35) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(212, 175, 55, 0.08) !important;
}
#step2-bando {
  background: linear-gradient(180deg, #0e1512 0%, #0a0f0d 100%) !important;
  border-color: rgba(40, 91, 70, 0.45) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(37, 99, 235, 0.08) !important;
}
#step3-5khudisan {
  background: linear-gradient(180deg, #180f0c 0%, #110b08 100%) !important;
  border-color: rgba(185, 28, 28, 0.35) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(185, 28, 28, 0.08) !important;
}
#step4-hosodisan {
  background: linear-gradient(180deg, #0f121b 0%, #0b0c13 100%) !important;
  border-color: rgba(59, 130, 246, 0.35) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(59, 130, 246, 0.08) !important;
}
#step5-phong3d {
  background: linear-gradient(180deg, #0c121d 0%, #080d15 100%) !important;
  border-color: rgba(6, 182, 212, 0.4) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(6, 182, 212, 0.1) !important;
}
#step6-ai5a {
  background: linear-gradient(180deg, #130d1d 0%, #0c0813 100%) !important;
  border-color: rgba(147, 51, 234, 0.35) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(147, 51, 234, 0.08) !important;
}
#step7-xuongsangtao {
  background: linear-gradient(180deg, #18130e 0%, #110d0a 100%) !important;
  border-color: rgba(217, 119, 6, 0.35) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(217, 119, 6, 0.08) !important;
}
#step8-argallery {
  background: linear-gradient(180deg, #0d1715 0%, #09100e 100%) !important;
  border-color: rgba(16, 185, 129, 0.35) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(16, 185, 129, 0.08) !important;
}
#step9-danhgia {
  background: linear-gradient(180deg, #181510 0%, #110f0c 100%) !important;
  border-color: rgba(212, 175, 55, 0.35) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(212, 175, 55, 0.08) !important;
}
#step-dashboard {
  background: linear-gradient(180deg, #0e121e 0%, #0a0d16 100%) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.8), 0 0 36px rgba(59, 130, 246, 0.1) !important;
}

/* Classical Monogram Watermark */
.sah-museum-watermark {
  position: fixed;
  top: 14%;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--sah-font-display);
  font-size: 42vw;
  font-weight: 900;
  color: rgba(212, 175, 55, 0.022);
  pointer-events: none;
  user-select: none;
  z-index: 0;
  line-height: 1;
}

/* Teacher Only Guard */
.teacher-only {
  display: none !important;
}
body.role-teacher .teacher-only.rm-topnav-link {
  display: inline-flex !important;
}
body.role-teacher .teacher-only.sah-step-pill {
  display: inline-flex !important;
}
body.role-teacher .teacher-only.sah-step-sep {
  display: inline !important;
}
body.role-teacher .teacher-only.sah-ppt-next {
  display: inline-flex !important;
}
body.role-teacher section.teacher-only.active-slide {
  display: block !important;
}
body.role-teacher:not(.slide-mode) section.teacher-only {
  display: block !important;
}

/* Slide Mode vs Scroll Mode */
body.slide-mode .sah-slide {
  display: none !important;
}
body.slide-mode .sah-slide.active-slide {
  display: block !important;
  animation: slideFadeIn 0.32s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes slideFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

body:not(.slide-mode) .sah-slide {
  display: block !important;
  margin-bottom: 40px;
}

/* Top Navigation Bar */
.rm-topnav {
  background: rgba(10, 9, 8, 0.94) !important;
  backdrop-filter: blur(18px) !important;
  -webkit-backdrop-filter: blur(18px) !important;
  border-bottom: 1px solid var(--sah-gold-border) !important;
  box-shadow: 0 4px 28px rgba(0, 0, 0, 0.75) !important;
  font-family: var(--sah-font-sans) !important;
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  flex-wrap: nowrap !important;
  padding: 8px 18px !important;
  box-sizing: border-box !important;
}
@media (min-width: 861px) {
  .rm-topnav {
    position: sticky !important;
    top: 0 !important;
    z-index: 60 !important;
  }
  .sah-stepper-nav {
    position: sticky !important;
    top: 48px !important;
    z-index: 55 !important;
  }
}
@media (max-width: 860px) {
  .rm-topnav {
    position: relative !important;
    top: auto !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    white-space: nowrap !important;
    padding: 8px 12px !important;
    scrollbar-width: none !important;
    -webkit-overflow-scrolling: touch !important;
  }
  .rm-topnav::-webkit-scrollbar {
    display: none !important;
  }
  .rm-topnav-brand {
    font-size: 13px !important;
    flex-shrink: 0 !important;
  }
  .rm-topnav-link {
    font-size: 12px !important;
    padding: 4px 8px !important;
    flex-shrink: 0 !important;
  }
  .rm-chip, .rm-btn {
    font-size: 11px !important;
    padding: 4px 8px !important;
    flex-shrink: 0 !important;
  }
  .sah-stepper-nav {
    position: sticky !important;
    top: 0 !important;
    z-index: 70 !important;
    background: rgba(17, 15, 13, 0.96) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
  }
  .sah-stepper-container {
    padding: 6px 8px !important;
    gap: 6px !important;
  }
  .sah-step-pill {
    padding: 5px 10px !important;
    font-size: 11px !important;
  }
  .sah-view-toggle {
    padding: 4px 8px !important;
    font-size: 10px !important;
  }
  .sah-step-sec {
    margin: 14px 6px 28px !important;
    padding: 18px 12px !important;
    scroll-margin-top: 56px !important;
    border-radius: 18px !important;
  }
  .sah-landing-page {
    padding: 18px 12px !important;
  }
  .sah-hero-grid {
    grid-template-columns: 1fr !important;
    gap: 20px !important;
  }
  .sah-exhibit-card {
    grid-template-columns: 1fr !important;
    padding: 16px 12px !important;
    gap: 12px !important;
  }
  .sah-exhibit-num {
    font-size: 32px !important;
  }
}
.rm-topnav-brand {
  font-family: var(--sah-font-display) !important;
  letter-spacing: 0.16em !important;
  font-weight: 800 !important;
  font-size: 15px !important;
  background: linear-gradient(180deg, #ffffff 0%, #f7e6b0 45%, #d4af37 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  text-shadow: 0 0 20px rgba(212, 175, 55, 0.3) !important;
}
.rm-topnav-link {
  color: #c8c0b2 !important;
  font-size: 13px !important;
  transition: all 0.2s ease !important;
}
.rm-topnav-link:hover {
  color: #ffffff !important;
  text-shadow: 0 0 10px rgba(212, 175, 55, 0.5) !important;
}
.rm-chip {
  background: rgba(212, 175, 55, 0.1) !important;
  border: 1px solid var(--sah-gold-border) !important;
  color: var(--sah-gold-bright) !important;
}
.rm-btn {
  background: rgba(212, 175, 55, 0.15) !important;
  border: 1px solid var(--sah-gold-border) !important;
  color: var(--sah-text-heading) !important;
  transition: all 0.2s ease !important;
}
.rm-btn:hover {
  background: var(--sah-gold-primary) !important;
  color: #0c0b0a !important;
}

/* Stepper Bar */
.sah-stepper-nav {
  position: sticky;
  top: 48px;
  z-index: 55;
  background: #110f0d;
  border-bottom: 1px solid var(--sah-gold-border);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.65);
  font-family: var(--sah-font-sans);
}
.sah-stepper-container {
  max-width: 1340px;
  margin: 0 auto;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.sah-stepper-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sah-stepper-btn-quick {
  background: rgba(212, 175, 55, 0.08);
  color: var(--sah-gold-bright);
  border: 1px solid var(--sah-gold-border);
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-stepper-btn-quick:hover:not(:disabled) {
  background: var(--sah-gold-primary);
  color: #0b0a09;
  box-shadow: 0 0 12px rgba(212, 175, 55, 0.4);
}
.sah-stepper-btn-quick:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.sah-stepper-cur-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--sah-gold-bright);
  white-space: nowrap;
  padding: 0 4px;
}
.sah-stepper-track {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: thin;
  padding-bottom: 2px;
  flex: 1;
}
.sah-step-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(212, 175, 55, 0.16);
  color: #c9c0b1;
  text-decoration: none;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s ease;
  cursor: pointer;
}
.sah-step-pill:hover {
  background: rgba(212, 175, 55, 0.16);
  color: #ffffff;
  border-color: rgba(212, 175, 55, 0.4);
}
.sah-step-pill.active {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.3) 0%, rgba(179, 143, 40, 0.45) 100%);
  border-color: var(--sah-gold-primary);
  color: #ffffff;
  box-shadow: 0 0 16px rgba(212, 175, 55, 0.35);
}
.sah-step-pill .sah-step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  font-size: 10px;
  font-weight: 800;
}
.sah-step-pill.active .sah-step-num {
  background: var(--sah-gold-primary);
  color: #0b0a09;
}
.sah-step-arrow {
  color: rgba(212, 175, 55, 0.25);
  font-size: 11px;
}
.sah-step-sep {
  color: rgba(212, 175, 55, 0.3);
  margin: 0 4px;
}
.sah-step-dash {
  background: rgba(212, 175, 55, 0.12);
  border-color: var(--sah-gold-primary);
  color: var(--sah-gold-bright);
}
.sah-view-toggle {
  background: rgba(212, 175, 55, 0.08);
  color: #e2dacf;
  border: 1px solid var(--sah-gold-border);
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}
.sah-view-toggle:hover {
  background: rgba(212, 175, 55, 0.22);
  border-color: var(--sah-gold-primary);
  color: #ffffff;
}

/* PowerPoint Slide Navigation Bar (Footer of every slide) */
.sah-ppt-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 42px;
  padding: 20px 26px;
  background: #181512;
  border: 1px solid var(--sah-gold-border);
  border-radius: 20px;
  flex-wrap: wrap;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
}
.sah-ppt-btn {
  background: linear-gradient(135deg, #d4af37 0%, #b38b22 100%);
  color: #0c0b0a !important;
  border: 0;
  border-radius: 12px;
  padding: 13px 24px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  transition: all 0.25s ease;
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.35);
  text-decoration: none;
}
.sah-ppt-btn:hover {
  background: linear-gradient(135deg, #f5d475 0%, #c59b27 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(212, 175, 55, 0.55);
}
.sah-ppt-prev {
  background: rgba(255, 255, 255, 0.06);
  color: #e2dacf !important;
  border: 1px solid var(--sah-gold-border);
  box-shadow: none;
}
.sah-ppt-prev:hover {
  background: rgba(212, 175, 55, 0.16);
  border-color: var(--sah-gold-primary);
  color: #ffffff !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}
.sah-ppt-finish {
  background: linear-gradient(135deg, #e5c158 0%, #a87d18 100%);
  color: #0c0b0a !important;
}
.sah-ppt-finish:hover {
  background: linear-gradient(135deg, #ffe082 0%, #c59b27 100%);
}
.sah-ppt-indicator {
  text-align: center;
  font-size: 13px;
  color: var(--sah-gold-bright);
}
.sah-ppt-slide-num b {
  color: #ffffff;
  font-size: 16px;
}
.sah-ppt-key-hint {
  font-size: 11px;
  color: #9c9180;
  margin-top: 4px;
}
.sah-ppt-key-hint kbd {
  background: rgba(212, 175, 55, 0.12);
  border: 1px solid var(--sah-gold-border);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 10px;
  font-family: monospace;
  color: #f7f3ea;
}

/* Step Section Layout (Slide Container) */
.sah-step-sec {
  max-width: 1240px;
  margin: 28px auto 40px;
  padding: 34px;
  background: var(--sah-bg-surface);
  border: 1px solid var(--sah-gold-border);
  border-radius: 26px;
  box-shadow: 0 16px 54px rgba(0, 0, 0, 0.75);
  color: var(--sah-text-body);
  position: relative;
  z-index: 1;
  scroll-margin-top: calc(var(--rm-navh) + 60px);
}
.sah-step-sec .rm-sec {
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: inherit !important;
}
.sah-step-badge {
  display: inline-block;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid var(--sah-gold-border);
  color: var(--sah-gold-bright);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  padding: 6px 14px;
  border-radius: 999px;
  margin-bottom: 14px;
}
.sah-sec-header {
  margin-bottom: 24px;
}
.sah-sec-header h2 {
  font-family: var(--sah-font-serif);
  font-size: 28px;
  font-weight: 800;
  color: var(--sah-text-heading);
  margin: 0 0 8px;
  line-height: 1.28;
  letter-spacing: -0.01em;
}
.sah-sec-sub {
  color: var(--sah-text-muted);
  font-size: 15px;
  line-height: 1.65;
  margin: 0;
}

/* ==========================================================================
   LANDING PAGE (STEP 1) — MUSEUM SHOWCASE STYLES
   ========================================================================== */
.sah-landing-page {
  padding: 38px;
}
.sah-landing-hero {
  border-bottom: 1px solid var(--sah-gold-border);
  padding-bottom: 38px;
  margin-bottom: 40px;
}
.sah-hero-grid {
  display: grid;
  grid-template-columns: 1.25fr 0.95fr;
  gap: 36px;
  align-items: center;
}
@media (max-width: 980px) {
  .sah-hero-grid { grid-template-columns: 1fr; }
}

.sah-landing-badge-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.sah-badge-accent {
  background: rgba(212, 175, 55, 0.12);
  border: 1px solid var(--sah-gold-border);
  color: var(--sah-gold-bright);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  padding: 6px 14px;
  border-radius: 999px;
}
.sah-badge-sub {
  color: #9e9383;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.sah-landing-title {
  margin: 0 0 18px;
  line-height: 1.15;
}
.sah-title-kicker {
  display: block;
  font-family: var(--sah-font-display);
  font-size: 13px;
  letter-spacing: 0.22em;
  color: var(--sah-gold-primary);
  font-weight: 700;
  margin-bottom: 8px;
}
.sah-title-main {
  display: block;
  font-family: var(--sah-font-display);
  font-size: clamp(34px, 4.4vw, 52px);
  font-weight: 900;
  letter-spacing: 0.06em;
  background: linear-gradient(180deg, #ffffff 0%, #f7e6b0 45%, #d4af37 85%, #b38b22 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 40px rgba(212, 175, 55, 0.25);
}
.sah-title-sub {
  display: block;
  font-family: var(--sah-font-serif);
  font-style: italic;
  font-size: clamp(16px, 1.8vw, 21px);
  font-weight: 400;
  color: #d6ccbe;
  margin-top: 10px;
  line-height: 1.4;
}

.sah-landing-lead {
  font-size: 15.5px;
  line-height: 1.75;
  color: #cdc3b3;
  margin-bottom: 24px;
}

.sah-landing-meta-strip {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 14px 18px;
  background: #181512;
  border-radius: 16px;
  border: 1px solid var(--sah-gold-border);
  font-size: 13px;
  color: #beb4a4;
  margin-bottom: 26px;
}
.sah-landing-meta-strip b {
  color: var(--sah-gold-bright);
}

.sah-landing-hero-actions {
  display: grid;
  gap: 16px;
}
.sah-btn-hero-primary {
  background: linear-gradient(135deg, #d4af37 0%, #b38b22 100%);
  color: #0c0b0a !important;
  border: 0;
  border-radius: 999px;
  padding: 16px 32px;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 6px 26px rgba(212, 175, 55, 0.45);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: fit-content;
}
.sah-btn-hero-primary:hover {
  background: linear-gradient(135deg, #f5d475 0%, #c59b27 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 34px rgba(212, 175, 55, 0.65);
}

.sah-hero-quick-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.sah-btn-hero-ghost {
  background: rgba(255, 255, 255, 0.05);
  color: #d8cebe;
  border: 1px solid var(--sah-gold-border);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-btn-hero-ghost:hover {
  background: rgba(212, 175, 55, 0.18);
  border-color: var(--sah-gold-primary);
  color: #ffffff;
}

/* Featured Artifact Pedestal */
.sah-hero-pedestal {
  position: relative;
}
.sah-pedestal-glow {
  position: absolute;
  inset: -20px;
  background: radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.2) 0%, transparent 70%);
  filter: blur(20px);
  pointer-events: none;
  z-index: 0;
}
.sah-pedestal-card {
  position: relative;
  z-index: 1;
  background: #181512;
  border: 1px solid var(--sah-gold-border);
  border-radius: 22px;
  padding: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.85);
}
.sah-pedestal-media-wrap {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  aspect-ratio: 4/3;
  border: 1px solid rgba(212, 175, 55, 0.3);
}
.sah-pedestal-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.sah-pedestal-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(12, 11, 10, 0.88);
  backdrop-filter: blur(8px);
  border: 1px solid var(--sah-gold-border);
  color: var(--sah-gold-bright);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.14em;
  padding: 4px 10px;
  border-radius: 999px;
}
.sah-pedestal-caption {
  padding: 16px 8px 6px;
}
.sah-pedestal-caption h4 {
  font-family: var(--sah-font-serif);
  font-size: 18px;
  margin: 0 0 6px;
  color: var(--sah-text-heading);
}
.sah-pedestal-caption p {
  font-size: 13px;
  color: var(--sah-text-muted);
  line-height: 1.55;
  margin: 0 0 14px;
}
.sah-pedestal-actions {
  display: flex;
  gap: 10px;
}
.sah-btn-pedestal {
  background: var(--sah-gold-primary);
  color: #0c0b0a;
  border: 0;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-btn-pedestal:hover {
  background: var(--sah-gold-bright);
}
.sah-btn-pedestal-ghost {
  background: transparent;
  color: #d8cebe;
  border: 1px solid var(--sah-gold-border);
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-btn-pedestal-ghost:hover {
  background: rgba(212, 175, 55, 0.12);
  color: #ffffff;
}

/* ==========================================================================
   CURATORIAL EXHIBITS LIST (MATCHING USER REFERENCE LAYOUT)
   ========================================================================== */
.sah-exhibits-section {
  margin: 48px 0;
}
.sah-exhibits-list {
  display: grid;
  gap: 28px;
}
.sah-exhibit-card {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 20px;
  background: #151310;
  border: 1px solid var(--sah-gold-border);
  border-radius: 22px;
  padding: 30px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65);
  transition: all 0.25s ease;
}
.sah-exhibit-card:hover {
  border-color: rgba(212, 175, 55, 0.45);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.85);
  transform: translateY(-2px);
}
@media (max-width: 820px) {
  .sah-exhibit-card { grid-template-columns: 1fr; gap: 14px; padding: 22px; }
}

.sah-exhibit-num-col {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.sah-exhibit-num {
  font-family: var(--sah-font-display);
  font-size: 44px;
  font-weight: 900;
  color: var(--sah-gold-primary);
  line-height: 1;
  text-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
}

.sah-exhibit-content-col {
  display: grid;
  gap: 16px;
}
.sah-exhibit-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 10px;
  border-bottom: 1px solid rgba(212, 175, 55, 0.15);
  padding-bottom: 12px;
}
.sah-exhibit-header h3 {
  font-family: var(--sah-font-serif);
  font-size: 24px;
  font-weight: 800;
  color: var(--sah-text-heading);
  margin: 0;
  letter-spacing: -0.01em;
}
.sah-exhibit-loc {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--sah-gold-bright);
}

.sah-exhibit-grid {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 28px;
  align-items: start;
}
@media (max-width: 860px) {
  .sah-exhibit-grid { grid-template-columns: 1fr; }
}

.sah-exhibit-text {
  display: grid;
  gap: 14px;
}
.sah-exhibit-quote {
  border-left: 3px solid var(--sah-gold-primary);
  padding: 4px 0 4px 14px;
  font-style: italic;
  font-size: 14px;
  line-height: 1.65;
  color: #dfd6c8;
}
.sah-exhibit-points {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #b5aba0;
}
.sah-exhibit-points b {
  color: var(--sah-text-heading);
}
.sah-btn-exhibit-open {
  background: rgba(212, 175, 55, 0.12);
  border: 1px solid var(--sah-gold-border);
  color: var(--sah-gold-bright);
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  width: fit-content;
}
.sah-btn-exhibit-open:hover {
  background: var(--sah-gold-primary);
  color: #0b0a09;
  border-color: var(--sah-gold-primary);
}

/* Exhibit Media & Thumbnail Filmstrip */
.sah-exhibit-media {
  display: grid;
  gap: 10px;
}
.sah-exhibit-main-frame {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  aspect-ratio: 16/10;
  border: 1px solid var(--sah-gold-border);
  box-shadow: 0 8px 26px rgba(0, 0, 0, 0.7);
  background: #0b0a09;
}
.sah-exhibit-show-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: opacity 0.25s ease;
}
.sah-exhibit-filmstrip {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sah-strip-btn {
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid var(--sah-gold-border);
  color: var(--sah-gold-bright);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}
.sah-strip-btn:hover {
  background: var(--sah-gold-primary);
  color: #0c0b0a;
}
.sah-strip-track {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  flex: 1;
  padding: 2px 0;
}
.sah-exhibit-thumb {
  width: 60px;
  height: 42px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.25);
  cursor: pointer;
  opacity: 0.65;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.sah-exhibit-thumb:hover {
  opacity: 1;
  border-color: var(--sah-gold-bright);
}
.sah-exhibit-thumb.active {
  opacity: 1;
  border-color: var(--sah-gold-primary);
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.6);
}

/* ==========================================================================
   4 TECH PILLARS
   ========================================================================== */
.sah-landing-section {
  margin: 44px 0;
}
.sah-landing-sec-head {
  text-align: center;
  max-width: 780px;
  margin: 0 auto 28px;
}
.sah-tag-pill {
  background: rgba(212, 175, 55, 0.1);
  color: var(--sah-gold-bright);
  border: 1px solid var(--sah-gold-border);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  padding: 5px 14px;
  border-radius: 999px;
  display: inline-block;
  margin-bottom: 8px;
}
.sah-landing-sec-head h2 {
  font-family: var(--sah-font-serif);
  font-size: 30px;
  font-weight: 800;
  color: var(--sah-text-heading);
  margin: 6px 0 8px;
  letter-spacing: -0.01em;
}
.sah-landing-sec-head p {
  color: var(--sah-text-muted);
  font-size: 14.5px;
  margin: 0;
}

.sah-pillars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}
.sah-pillar-card {
  background: #171411;
  border: 1px solid var(--sah-gold-border);
  border-radius: 20px;
  padding: 24px;
  display: grid;
  gap: 12px;
  transition: all 0.25s ease;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.55);
}
.sah-pillar-card:hover {
  border-color: var(--sah-gold-primary);
  box-shadow: 0 14px 40px rgba(212, 175, 55, 0.16);
  transform: translateY(-3px);
  background: #1c1814;
}
.sah-pillar-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sah-pillar-ico { font-size: 34px; }
.sah-pillar-step-tag {
  background: rgba(212, 175, 55, 0.12);
  color: var(--sah-gold-bright);
  border: 1px solid var(--sah-gold-border);
  font-size: 10px;
  font-weight: 800;
  padding: 3px 9px;
  border-radius: 6px;
  letter-spacing: 0.08em;
}
.sah-pillar-name {
  font-family: var(--sah-font-serif);
  font-size: 18px;
  font-weight: 800;
  color: var(--sah-text-heading);
}
.sah-pillar-desc {
  font-size: 13.5px;
  line-height: 1.65;
  color: #beb3a3;
}
.sah-pillar-rule {
  font-size: 11.5px;
  font-weight: 700;
  color: var(--sah-gold-bright);
  background: rgba(212, 175, 55, 0.08);
  border: 1px solid var(--sah-gold-border);
  padding: 6px 12px;
  border-radius: 8px;
}

/* Roadmap Flowchart */
.sah-roadmap-track {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  padding: 18px 12px;
  background: #15120f;
  border-radius: 22px;
  border: 1px solid var(--sah-gold-border);
  box-shadow: 0 8px 30px rgba(0,0,0,0.5);
}
.sah-roadmap-step {
  background: #1c1915;
  border: 1px solid var(--sah-gold-border);
  border-radius: 14px;
  padding: 12px 10px;
  min-width: 120px;
  max-width: 150px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1 0 auto;
  box-sizing: border-box;
}
.sah-roadmap-step:hover {
  border-color: var(--sah-gold-primary);
  background: rgba(212, 175, 55, 0.14);
  transform: translateY(-2px);
}
.sah-rm-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--sah-gold-primary);
  color: #0c0b0a;
  font-size: 11px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}
.sah-roadmap-step b {
  display: block;
  font-size: 12px;
  color: var(--sah-text-heading);
  white-space: normal;
  word-wrap: break-word;
  line-height: 1.35;
  margin-bottom: 3px;
}
.sah-roadmap-step small {
  display: block;
  font-size: 10px;
  color: var(--sah-text-muted);
  white-space: normal;
  line-height: 1.3;
}
.sah-rm-arr {
  color: var(--sah-gold-primary);
  font-weight: 800;
  font-size: 14px;
  opacity: 0.6;
}

/* Video Showcase in Landing */
.sah-video-showcase {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 22px;
  align-items: start;
}
@media (max-width: 860px) {
  .sah-video-showcase { grid-template-columns: 1fr; }
}
.sah-video-player-wrap {
  background: #0c0b0a;
  border-radius: 18px;
  padding: 12px;
  border: 1px solid var(--sah-gold-border);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.8);
}
.sah-video-caption {
  color: #cfc5b4;
  font-size: 12.5px;
  padding: 10px 4px 4px;
}
.sah-video-caption b {
  color: var(--sah-gold-bright);
}
.sah-video-playlist {
  display: grid;
  gap: 12px;
}
.sah-video-item {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  background: #171411;
  border: 1px solid var(--sah-gold-border);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-video-item:hover, .sah-video-item.active {
  background: rgba(212, 175, 55, 0.12);
  border-color: var(--sah-gold-primary);
}
.sah-v-ico {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--sah-gold-primary);
  color: #0c0b0a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}
.sah-video-item b {
  font-size: 13.5px;
  color: var(--sah-text-heading);
  display: block;
}
.sah-video-item small {
  font-size: 11.5px;
  color: var(--sah-text-muted);
}

/* Landing Stats Grid */
.sah-landing-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 18px;
  margin: 40px 0;
}
.sah-lstat-card {
  background: #161310;
  border: 1px solid var(--sah-gold-border);
  border-radius: 20px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}
.sah-lstat-num {
  font-family: var(--sah-font-display);
  font-size: 42px;
  font-weight: 800;
  color: var(--sah-gold-primary);
  line-height: 1;
  margin-bottom: 6px;
  text-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
}
.sah-lstat-lbl {
  font-family: var(--sah-font-serif);
  font-size: 14px;
  font-weight: 700;
  color: var(--sah-text-heading);
  margin-bottom: 4px;
}
.sah-lstat-card small {
  font-size: 11.5px;
  color: var(--sah-text-muted);
}

/* Landing CTA Banner */
.sah-landing-cta-banner {
  background: linear-gradient(135deg, #1b1713 0%, #28211a 100%);
  color: #fff;
  border: 1px solid var(--sah-gold-border);
  border-radius: 22px;
  padding: 36px 24px;
  text-align: center;
  margin: 32px 0;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.7);
}
.sah-landing-cta-banner h3 {
  font-family: var(--sah-font-serif);
  font-size: 26px;
  margin: 0 0 10px;
  color: var(--sah-text-heading);
}
.sah-landing-cta-banner p {
  color: #cec4b4;
  font-size: 14.5px;
  margin: 0 0 22px;
}

/* ==========================================================================
   SUB-SLIDES MUSEUM DARK STYLING OVERRIDES (STEP 2 TO STEP 10)
   ========================================================================== */

/* Map Layout in Step 2 */
.sah-map-layout {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 24px;
  align-items: start;
}
@media (max-width: 860px) {
  .sah-map-layout { grid-template-columns: 1fr; }
}
.sah-map-visual {
  background: #171411;
  border-radius: 20px;
  border: 1px solid var(--sah-gold-border);
  padding: 14px;
  display: flex;
  justify-content: center;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
}
.sah-map-visual svg {
  width: 100%;
  height: auto;
  max-width: 560px;
  display: block;
}
.sah-map-sidebar {
  display: grid;
  gap: 12px;
}
.sah-map-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--sah-text-muted);
}
.sah-map-card-head b { color: var(--sah-gold-bright); }
.sah-map-list {
  display: grid;
  gap: 10px;
}
.sah-map-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  background: #171411;
  border: 1px solid var(--sah-gold-border);
  border-radius: 16px;
  cursor: pointer;
  position: relative;
  transition: border-color 0.25s ease, background 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
}
.sah-map-item:hover {
  border-color: var(--sah-gold-primary);
  background: rgba(212, 175, 55, 0.14);
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.7), 0 0 18px rgba(212, 175, 55, 0.24);
}
.sah-map-thumb {
  width: 46px;
  height: 46px;
  border-radius: 11px;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid var(--sah-gold-border);
  background: #090807;
  position: relative;
  transition: border-color 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
}
.sah-map-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.sah-map-item:hover .sah-map-thumb {
  border-color: var(--sah-gold-bright);
  box-shadow: 0 0 14px rgba(212, 175, 55, 0.45);
  transform: scale(1.06);
}
.sah-map-item:hover .sah-map-thumb img {
  transform: scale(1.22);
}

/* SVG Map Pin Hover Animations */
.map-pin-group {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.map-pin-group:hover {
  filter: drop-shadow(0 0 12px rgba(212, 175, 55, 0.85));
}
.map-pin-group:hover circle:nth-of-type(2) {
  stroke: var(--sah-gold-bright) !important;
  stroke-width: 3.5px !important;
}

/* Global Floating Hover Preview Card */
.sah-global-hover-preview {
  position: fixed;
  z-index: 999999;
  width: 260px;
  background: #14110e;
  border: 1.5px solid var(--sah-gold-primary);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.96), 0 0 30px rgba(212, 175, 55, 0.35);
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transform: translateY(8px) scale(0.96);
  transition: opacity 0.22s cubic-bezier(0.16, 1, 0.3, 1), transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.22s;
}
.sah-global-hover-preview.visible {
  opacity: 1;
  visibility: visible;
  transform: translateY(0) scale(1);
}
.sah-ghp-media {
  position: relative;
  width: 100%;
  height: 130px;
  overflow: hidden;
  background: #000;
}
.sah-ghp-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.sah-global-hover-preview.visible .sah-ghp-media img {
  transform: scale(1.08);
}
.sah-ghp-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 55%, rgba(20, 17, 14, 0.95) 100%);
  pointer-events: none;
}
.sah-ghp-badge {
  position: absolute;
  top: 9px;
  left: 9px;
  font-size: 9.5px;
  font-weight: 800;
  letter-spacing: 0.08em;
  padding: 3px 8px;
  border-radius: 20px;
  background: rgba(10, 9, 8, 0.92);
  color: var(--sah-gold-bright);
  border: 1px solid rgba(212, 175, 55, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.sah-ghp-body {
  padding: 11px 14px 14px;
  background: #14110e;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sah-ghp-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.35;
}
.sah-ghp-sub {
  font-size: 11.5px;
  color: var(--sah-gold-muted);
  line-height: 1.35;
}
.sah-ghp-hint {
  font-size: 10px;
  color: var(--sah-gold-primary);
  margin-top: 4px;
  font-weight: 700;
}
.sah-site-pill {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: #0c0b0a;
  background: var(--sah-gold-primary);
  font-size: 12px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sah-item-info { flex: 1; }
.sah-item-info b {
  font-size: 14px;
  color: var(--sah-text-heading);
  display: block;
}
.sah-item-info p {
  font-size: 12px;
  color: var(--sah-text-muted);
  margin: 2px 0 0;
  line-height: 1.4;
}
.sah-item-go {
  background: var(--sah-gold-primary);
  color: #0c0b0a;
  border: 0;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

/* Rule Banner */
.sah-rule-banner {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  background: #191511;
  border: 1px solid var(--sah-gold-border);
  border-left: 4px solid var(--sah-gold-primary);
  border-radius: 14px;
  padding: 14px 18px;
  margin-bottom: 22px;
}
.sah-rule-ico { font-size: 22px; line-height: 1.2; }
.sah-rule-body b { font-size: 14px; color: var(--sah-gold-bright); display: block; margin-bottom: 4px; }
.sah-rule-body p { font-size: 13px; color: #cfc4b4; line-height: 1.5; margin: 0; }

/* 5A Process Bar */
.sah-5a-process-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #161310;
  border: 1px solid var(--sah-gold-border);
  border-radius: 16px;
  padding: 14px 18px;
  margin-bottom: 24px;
  overflow-x: auto;
}
.sah-5a-step {
  display: grid;
  gap: 2px;
  text-align: center;
  flex: 1;
  min-width: 100px;
}
.sah-5a-step b { font-size: 13px; color: var(--sah-gold-bright); letter-spacing: 0.05em; }
.sah-5a-step span { font-size: 11px; color: var(--sah-text-muted); }
.sah-5a-arrow { color: var(--sah-gold-primary); font-weight: 800; font-size: 14px; opacity: 0.6; }

/* Studio Flow Bar in Step 7 */
.sah-studio-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #161310;
  border: 1px solid var(--sah-gold-border);
  border-radius: 14px;
  padding: 12px 18px;
  margin-bottom: 20px;
  overflow-x: auto;
}
.sah-flow-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--sah-gold-bright);
  background: #1f1b16;
  border: 1px solid var(--sah-gold-border);
  padding: 6px 14px;
  border-radius: 999px;
  white-space: nowrap;
}
.sah-flow-sep { color: var(--sah-gold-primary); font-size: 12px; opacity: 0.6; }

/* AR Card in Step 8 */
.sah-ar-card {
  display: flex;
  gap: 24px;
  align-items: center;
  background: linear-gradient(135deg, #181512 0%, #26201a 100%);
  color: #fff;
  border: 1px solid var(--sah-gold-border);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7);
}
@media (max-width: 760px) {
  .sah-ar-card { flex-direction: column; text-align: center; }
}
.sah-ar-info { flex: 1; display: grid; gap: 8px; }
.sah-ar-tag {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.15em;
  color: var(--sah-gold-bright);
}
.sah-ar-info h3 { font-size: 20px; margin: 0; color: #fff; font-family: var(--sah-font-serif); }
.sah-ar-info p { color: #cfc4b4; font-size: 14px; line-height: 1.55; margin: 0; }
.sah-ar-actions { display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap; }
.sah-ar-qr {
  display: grid;
  justify-items: center;
  gap: 6px;
  background: #110f0d;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--sah-gold-border);
  flex-shrink: 0;
}
.sah-ar-qr small { font-size: 11px; color: var(--sah-gold-bright); text-align: center; max-width: 120px; }

/* Rubric & Pre-Post Evaluation in Step 9 */
.sah-eval-container {
  display: grid;
  gap: 24px;
  margin: 28px 0;
}
.sah-rubric-card, .sah-prepost-card {
  background: #161310;
  border: 1px solid var(--sah-gold-border);
  border-radius: 18px;
  padding: 22px;
}
.sah-eval-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}
.sah-eval-head h3 { font-size: 19px; margin: 0; color: var(--sah-text-heading); font-family: var(--sah-font-serif); }
.sah-eval-badge {
  background: rgba(212, 175, 55, 0.12);
  color: var(--sah-gold-bright);
  border: 1px solid var(--sah-gold-border);
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
}
.sah-eval-sub { color: var(--sah-text-muted); font-size: 13px; margin: 0 0 16px; line-height: 1.5; }
.sah-rubric-table-wrap { overflow-x: auto; }
.sah-rubric-tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  line-height: 1.5;
}
.sah-rubric-tbl th, .sah-rubric-tbl td {
  border: 1px solid var(--sah-gold-border);
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}
.sah-rubric-tbl th {
  background: #1f1b16;
  color: var(--sah-gold-bright);
  font-weight: 700;
  font-size: 12px;
}
.sah-rubric-tbl td:first-child { background: #1a1713; width: 22%; color: #fff; }
.sah-rubric-tbl td:first-child small { color: var(--sah-text-muted); }

/* Dashboard Section (Step 10) */
.sah-dashboard-sec { background: #13110f; border-color: var(--sah-gold-border); }
.sah-dash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 20px 0;
}
.sah-dash-card {
  background: #171411;
  border: 1px solid var(--sah-gold-border);
  border-radius: 16px;
  padding: 22px;
  text-align: center;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
}
.sah-dash-num {
  font-family: var(--sah-font-display);
  font-size: 38px;
  font-weight: 800;
  color: var(--sah-gold-primary);
  line-height: 1;
  margin-bottom: 6px;
}
.sah-dash-lbl {
  font-size: 13px;
  font-weight: 700;
  color: var(--sah-text-heading);
  margin-bottom: 4px;
}
.sah-dash-card small { font-size: 11px; color: var(--sah-text-muted); }

/* Dark Theme Overrides for Core Inputs, Forms & Modals */
input[type="text"], input[type="password"], textarea, select {
  background: #1a1714 !important;
  color: #f7f3ea !important;
  border: 1px solid var(--sah-gold-border) !important;
  border-radius: 8px !important;
}
input[type="text"]:focus, input[type="password"]:focus, textarea:focus, select:focus {
  border-color: var(--sah-gold-primary) !important;
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.35) !important;
  outline: none !important;
}
.rm-overlay {
  background: rgba(8, 7, 6, 0.88) !important;
  backdrop-filter: blur(12px) !important;
}
.rm-card {
  background: #181512 !important;
  border: 1px solid var(--sah-gold-border) !important;
  color: var(--sah-text-body) !important;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.85) !important;
}
.rm-card h2 {
  font-family: var(--sah-font-serif) !important;
  color: var(--sah-text-heading) !important;
}
.rm-choice {
  background: #201c18 !important;
  border: 1px solid var(--sah-gold-border) !important;
  color: var(--sah-text-body) !important;
}
.rm-choice:hover {
  background: rgba(212, 175, 55, 0.15) !important;
  border-color: var(--sah-gold-primary) !important;
}
.rm-choice b {
  color: var(--sah-gold-bright) !important;
}

/* Radio button tab panel visibility sync */
#h1:checked ~ #step3-5khudisan .tabs label[for="h1"],
#h1:checked ~ * .tabs label[for="h1"] { background: var(--sah-gold-primary); color: #0c0b0a; border-color: var(--sah-gold-primary); font-weight: 800; }
#h1:checked ~ #step4-hosodisan .panels #p1,
#h1:checked ~ * .panels #p1 { display: block !important; }
#h2:checked ~ #step3-5khudisan .tabs label[for="h2"],
#h2:checked ~ * .tabs label[for="h2"] { background: var(--sah-gold-primary); color: #0c0b0a; border-color: var(--sah-gold-primary); font-weight: 800; }
#h2:checked ~ #step4-hosodisan .panels #p2,
#h2:checked ~ * .panels #p2 { display: block !important; }
#h3:checked ~ #step3-5khudisan .tabs label[for="h3"],
#h3:checked ~ * .tabs label[for="h3"] { background: var(--sah-gold-primary); color: #0c0b0a; border-color: var(--sah-gold-primary); font-weight: 800; }
#h3:checked ~ #step4-hosodisan .panels #p3,
#h3:checked ~ * .panels #p3 { display: block !important; }
#h4:checked ~ #step3-5khudisan .tabs label[for="h4"],
#h4:checked ~ * .tabs label[for="h4"] { background: var(--sah-gold-primary); color: #0c0b0a; border-color: var(--sah-gold-primary); font-weight: 800; }
#h4:checked ~ #step4-hosodisan .panels #p4,
#h4:checked ~ * .panels #p4 { display: block !important; }
#h5:checked ~ #step3-5khudisan .tabs label[for="h5"],
#h5:checked ~ * .tabs label[for="h5"] { background: var(--sah-gold-primary); color: #0c0b0a; border-color: var(--sah-gold-primary); font-weight: 800; }
#h5:checked ~ #step4-hosodisan .panels #p5,
#h5:checked ~ * .panels #p5 { display: block !important; }
#home0:checked ~ #step4-hosodisan .panels #p0,
#home0:checked ~ * .panels #p0 { display: block !important; }
#h1:checked ~ * .switcher label[for="h1"],
#h2:checked ~ * .switcher label[for="h2"],
#h3:checked ~ * .switcher label[for="h3"],
#h4:checked ~ * .switcher label[for="h4"],
#h5:checked ~ * .switcher label[for="h5"] { background: var(--sah-gold-primary); color: #0c0b0a; font-weight: 800; }
#home0:checked ~ * .switcher label[for="home0"] { background: var(--sah-gold-primary); color: #0c0b0a; font-weight: 800; }
</style>
<!-- SAH-GUIDELINE-CSS-END -->"""

# --------------------------------------------------------------------------
# 18. JavaScript for PowerPoint Slides, Keyboard Navigation, and Videos
# --------------------------------------------------------------------------
GUIDELINE_JS = """<!-- SAH-GUIDELINE-JS-START -->
<script>
// Slide IDs definition
var SLIDE_IDS = [
  'step1-trangchu',
  'step2-bando',
  'step3-5khudisan',
  'step4-hosodisan',
  'step5-phong3d',
  'step6-ai5a',
  'step7-xuongsangtao',
  'step8-argallery',
  'step9-danhgia',
  'step-dashboard'
];

var SLIDE_NAMES = [
  'Trang chủ',
  'Bản đồ di sản',
  '5 Khu di sản',
  'Hồ sơ 15 ảnh & Hotspot',
  'Phòng 3D tương tác',
  'AI Art Assistant 5A',
  'Xưởng sáng tạo',
  'Triển lãm AR Gallery',
  'Đánh giá và tự hoàn thiện',
  'Dashboard Quản trị GV'
];

var currentSlideIndex = 0;
var isSlideMode = true; // Default: PowerPoint Slide Mode!

function isTeacherRole() {
  return document.body.classList.contains('role-teacher') || (localStorage.getItem('rm_role') || '') === 'teacher';
}

function getAvailableSlides() {
  return isTeacherRole() ? SLIDE_IDS : SLIDE_IDS.slice(0, 9);
}

function updateTeacherVisibility() {
  var isTeacher = isTeacherRole();
  document.body.classList.toggle('role-teacher', isTeacher);
  
  // Guard topnav & stepper links
  document.querySelectorAll('.teacher-only').forEach(function(el) {
    if (el.tagName === 'SECTION') {
      if (isTeacher) {
        if (!isSlideMode || el.classList.contains('active-slide')) el.style.display = 'block';
        else el.style.display = 'none';
      } else {
        el.style.display = 'none';
      }
    } else {
      el.style.display = isTeacher ? '' : 'none';
    }
  });

  // Guard step9 finish button vs continue to teacher dashboard
  var studentAction = document.querySelector('.student-or-guest-action');
  if (studentAction) {
    studentAction.style.display = isTeacher ? 'none' : 'inline-flex';
  }

  // Update total slide indicator text
  var total = getAvailableSlides().length;
  document.querySelectorAll('.sah-dyn-total').forEach(function(el) { el.textContent = total; });
  var stepperTotal = document.getElementById('stepperTotalNum');
  if (stepperTotal) stepperTotal.textContent = total;
}

function goToSlide(index) {
  var slides = getAvailableSlides();
  if (index < 0) index = 0;
  if (index >= slides.length) index = slides.length - 1;
  currentSlideIndex = index;
  localStorage.setItem('sah_current_slide', index);

  if (isSlideMode) {
    document.body.classList.add('slide-mode');
    SLIDE_IDS.forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.classList.remove('active-slide');
    });
    var curEl = document.getElementById(slides[currentSlideIndex]);
    if (curEl) {
      curEl.classList.add('active-slide');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  } else {
    document.body.classList.remove('slide-mode');
    var curEl = document.getElementById(slides[currentSlideIndex]);
    if (curEl) {
      curEl.scrollIntoView({ behavior: 'smooth' });
    }
  }

  updateSlideUI();
}

function nextSlide() {
  var slides = getAvailableSlides();
  if (currentSlideIndex < slides.length - 1) {
    goToSlide(currentSlideIndex + 1);
  }
}

function prevSlide() {
  if (currentSlideIndex > 0) {
    goToSlide(currentSlideIndex - 1);
  }
}

function toggleViewMode() {
  isSlideMode = !isSlideMode;
  var btnIco = document.getElementById('viewToggleIco');
  var btnTxt = document.getElementById('viewToggleTxt');
  if (isSlideMode) {
    if (btnIco) btnIco.textContent = '📽️';
    if (btnTxt) btnTxt.textContent = 'Chế độ Slide';
    goToSlide(currentSlideIndex);
  } else {
    if (btnIco) btnIco.textContent = '📜';
    if (btnTxt) btnTxt.textContent = 'Xem toàn trang';
    document.body.classList.remove('slide-mode');
    var curEl = document.getElementById(SLIDE_IDS[currentSlideIndex]);
    if (curEl) curEl.scrollIntoView({ behavior: 'smooth' });
  }
}

function updateSlideUI() {
  var slides = getAvailableSlides();
  var total = slides.length;
  
  // Update data-active-slide for dynamic background styling
  var activeSlideId = slides[currentSlideIndex];
  if (activeSlideId) {
    document.body.setAttribute('data-active-slide', activeSlideId);
  }

  // Update stepper pills
  var pills = document.querySelectorAll('.sah-stepper-track .sah-step-pill');
  pills.forEach(function(pill, idx) {
    if (idx === currentSlideIndex) {
      pill.classList.add('active');
      pill.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
    } else {
      pill.classList.remove('active');
    }
  });

  // Update stepper indicator
  var stepperCur = document.getElementById('stepperCurNum');
  if (stepperCur) stepperCur.textContent = (currentSlideIndex + 1);

  // Update quick prev/next buttons
  var btnP = document.getElementById('btnQuickPrev');
  var btnN = document.getElementById('btnQuickNext');
  if (btnP) btnP.disabled = (currentSlideIndex === 0);
  if (btnN) btnN.disabled = (currentSlideIndex === total - 1);

  updateTeacherVisibility();
}

// Global Hover Preview Modal with location previews
function initHoverPreview() {
  if (window.matchMedia && window.matchMedia('(hover: none)').matches) return;
  var modal = document.getElementById('sahGlobalHoverPreview');
  var imgEl = document.getElementById('sahGhpImg');
  var badgeEl = document.getElementById('sahGhpBadge');
  var titleEl = document.getElementById('sahGhpTitle');
  var subEl = document.getElementById('sahGhpSub');
  if (!modal || !imgEl) return;

  var curTarget = null;
  var hideTimeout = null;

  function showPreview(target) {
    var imgSrc = target.getAttribute('data-preview-img');
    if (!imgSrc) return;
    
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }

    imgEl.src = imgSrc;
    imgEl.alt = target.getAttribute('data-preview-title') || 'Xem trước di sản';
    if (badgeEl) badgeEl.textContent = target.getAttribute('data-preview-badge') || 'XEM TRƯỚC';
    if (titleEl) titleEl.textContent = target.getAttribute('data-preview-title') || '';
    if (subEl) subEl.textContent = target.getAttribute('data-preview-sub') || '';

    positionPreview(target);
    modal.classList.add('visible');
    modal.setAttribute('aria-hidden', 'false');
  }

  function hidePreview() {
    if (hideTimeout) clearTimeout(hideTimeout);
    hideTimeout = setTimeout(function() {
      modal.classList.remove('visible');
      modal.setAttribute('aria-hidden', 'true');
      curTarget = null;
    }, 80);
  }

  function positionPreview(target) {
    var rect = target.getBoundingClientRect();
    var modalWidth = 260;
    var modalHeight = 220;
    
    var left = rect.left + (rect.width / 2) - (modalWidth / 2);
    var top = rect.bottom + 12;

    if (top + modalHeight > window.innerHeight - 10) {
      top = rect.top - modalHeight - 12;
    }
    
    if (left < 12) left = 12;
    if (left + modalWidth > window.innerWidth - 12) {
      left = window.innerWidth - modalWidth - 12;
    }
    if (top < 12) top = 12;

    modal.style.left = Math.round(left) + 'px';
    modal.style.top = Math.round(top) + 'px';
  }

  document.addEventListener('mouseover', function(e) {
    var target = e.target && e.target.closest ? e.target.closest('[data-preview-img]') : null;
    if (!target) return;
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }
    if (target === curTarget) return;
    curTarget = target;
    showPreview(target);
  }, true);

  document.addEventListener('mouseout', function(e) {
    var target = e.target && e.target.closest ? e.target.closest('[data-preview-img]') : null;
    if (!target) return;
    if (e.relatedTarget && (target === e.relatedTarget || target.contains(e.relatedTarget))) return;
    hidePreview();
  }, true);

  window.addEventListener('scroll', function() {
    if (curTarget) hidePreview();
  }, { passive: true });

  document.addEventListener('click', function() {
    if (curTarget) hidePreview();
  });
}
window.initHoverPreview = initHoverPreview;

// Heritage selector helper used by Map and Quick Cards
function selectHeritageByCode(code) {
  var codeToId = {
    'phohien': 'h1',
    'chuakeo': 'h2',
    'dentran': 'h3',
    'lequydon': 'h4',
    'dongxam': 'h5'
  };
  var rId = codeToId[code];
  if (rId) {
    var r = document.getElementById(rId);
    if (r) {
      r.checked = true;
      r.dispatchEvent(new Event('change'));
    }
  }
  syncHeritagePanels();
  // Automatically navigate to Step 4 (Hồ sơ khám phá di sản 15 ảnh)
  goToSlide(3);
}

// Sync panel display when radio buttons change
function syncHeritagePanels() {
  var radios = ['home0', 'h1', 'h2', 'h3', 'h4', 'h5'];
  var checkedRadio = null;
  for (var i = 0; i < radios.length; i++) {
    var el = document.getElementById(radios[i]);
    if (el && el.checked) {
      checkedRadio = radios[i];
      break;
    }
  }
  var targetId = 'p0';
  if (checkedRadio && checkedRadio !== 'home0') {
    targetId = checkedRadio.replace('h', 'p');
  }
  document.querySelectorAll('.panels .panel').forEach(function(p) {
    if (p.id === targetId) {
      p.style.display = 'block';
    } else {
      p.style.display = 'none';
    }
  });
}

// Video switcher on Landing Page
function switchLandingVideo(srcUrl, caption, element) {
  var player = document.getElementById('landingVideoPlayer');
  var source = document.getElementById('videoSource');
  var cap = document.getElementById('videoCaption');
  if (player && source) {
    source.src = srcUrl;
    player.load();
    if (cap) cap.innerHTML = '<b>Phim tài liệu:</b> ' + caption;
  }
  document.querySelectorAll('.sah-video-item').forEach(function(item) {
    item.classList.remove('active');
  });
  if (element) element.classList.add('active');
}

// AR Demo Modal handlers
function openArDemoModal() {
  var m = document.getElementById('arDemoModal');
  if (m) m.hidden = false;
}
function closeArDemoModal() {
  var m = document.getElementById('arDemoModal');
  if (m) m.hidden = true;
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
  // Wire radio change listeners
  ['home0', 'h1', 'h2', 'h3', 'h4', 'h5'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('change', syncHeritagePanels);
  });
  syncHeritagePanels();

  // Wire Map Pin click listeners
  var pins = {
    'pin-phohien': 'phohien',
    'pin-chuakeo': 'chuakeo',
    'pin-dentran': 'dentran',
    'pin-lequydon': 'lequydon',
    'pin-dongxam': 'dongxam'
  };
  Object.keys(pins).forEach(function(pinId) {
    var el = document.getElementById(pinId);
    if (el) {
      el.style.cursor = 'pointer';
      el.addEventListener('click', function() {
        selectHeritageByCode(pins[pinId]);
      });
    }
  });

  // Keyboard navigation like PowerPoint (Left / Right arrows, PageUp / PageDown)
  window.addEventListener('keydown', function(e) {
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown') {
      e.preventDefault();
      nextSlide();
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault();
      prevSlide();
    }
  });

  // Export to window for global access
  window.goToSlide = goToSlide;
  window.nextSlide = nextSlide;
  window.prevSlide = prevSlide;
  window.toggleViewMode = toggleViewMode;

// Museum Exhibit Thumbnail Switcher and Rotator
function switchExhibitImg(id, src, element) {
  var img = document.getElementById('exhibitImg' + id);
  if (img) img.src = src;
  var track = document.getElementById('thumbList' + id);
  if (track) {
    track.querySelectorAll('.sah-exhibit-thumb').forEach(function(t) { t.classList.remove('active'); });
  }
  if (element) element.classList.add('active');
}

function rotateExhibitThumb(id, direction) {
  var track = document.getElementById('thumbList' + id);
  if (!track) return;
  var thumbs = Array.from(track.querySelectorAll('.sah-exhibit-thumb'));
  if (!thumbs.length) return;
  var curIdx = thumbs.findIndex(function(t) { return t.classList.contains('active'); });
  if (curIdx < 0) curIdx = 0;
  var nextIdx = (curIdx + direction + thumbs.length) % thumbs.length;
  thumbs[nextIdx].click();
}
window.switchExhibitImg = switchExhibitImg;
window.rotateExhibitThumb = rotateExhibitThumb;

  window.toggleSlideMode = toggleViewMode;
  window.updateTeacherVisibility = updateTeacherVisibility;

  // Observe body class changes to automatically sync teacher visibility
  if (window.MutationObserver) {
    var roleObserver = new MutationObserver(function() {
      updateTeacherVisibility();
    });
    roleObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  }

  // Watch storage events to sync role
  window.addEventListener('storage', function(e) {
    if (e.key === 'rm_role') updateTeacherVisibility();
  });

  // Check URL hash or saved slide
  var savedSlide = parseInt(localStorage.getItem('sah_current_slide') || '0', 10);
  if (isNaN(savedSlide) || savedSlide < 0) savedSlide = 0;
  
  var hash = window.location.hash.replace('#', '');
  if (hash) {
    var hIdx = SLIDE_IDS.indexOf(hash);
    if (hIdx >= 0) savedSlide = hIdx;
  }

  // Activate default slide mode
  goToSlide(savedSlide);
  updateTeacherVisibility();
  initHoverPreview();
});
</script>
<!-- SAH-GUIDELINE-JS-END -->
"""

# Original J39 wiring
J39 = r"""
<!-- J39-WIRING-START -->
<script>
document.addEventListener("DOMContentLoaded",function(){
var R=document.getElementById("journey39"), P=document.getElementById("j39p");
if(!R||!P)return;

var KEYS=["phohien","chuakeo","dentran","lequydon","dongxam"];
var PACKNAME={phohien:["Dấu ấn Phố Hiến","Kiến trúc & không gian","Màu sắc & cảm xúc","Xưa & nay","Biểu tượng cá nhân"],
 chuakeo:["Nhịp điệu mái chùa","Hình khối kiến trúc","Hoa văn & chi tiết gỗ","Không gian & góc nhìn","Chùa Keo hiện đại"],
 dentran:["Dấu ấn lịch sử","Kiến trúc trang nghiêm","Biểu tượng & hoa văn","Không gian tưởng niệm","Di sản với thế hệ trẻ"],
 lequydon:["Chân dung nhà bác học","Không gian lưu niệm","Sách & tri thức","Kể chuyện bằng hình ảnh","Tri thức hôm nay"],
 dongxam:["Hoa văn chạm bạc","Ánh sáng & bề mặt","Nhịp điệu trang trí","Truyền thống → hiện đại","Bảo tồn bằng Mĩ thuật"]};
var HINT="Sẽ lấy từ phần Khám phá.";

function g(k){var v=localStorage.getItem(k);return v==null?"":String(v);}
var NOPLACE=["Em chưa nhập nội dung A1."];
function t(v){var s=String(v==null?"":v).trim();return NOPLACE.indexOf(s)>=0?"":s;}
function json(k){try{return JSON.parse(localStorage.getItem(k)||"{}")||{};}catch(e){return {};}}
function join(){var a=[].slice.call(arguments).map(t).filter(Boolean);return a.join("  •  ");}

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

function ans(p,i,q){
  var v=t(g("sah321-integrated-"+p+"-"+packIdx(p)+"-"+q));
  if(!v) v=t(g("sah321-bank-answer-"+p+"-"+packIdx(p)+"-"+q));
  if(!v) v=t(g("direct321-"+p+"-"+q));
  return v;
}

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

# RM CSS
RM_CSS = """<!-- RM-CSS-START -->
<style>
[hidden]{display:none !important}
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
html{scroll-behavior:smooth}
:root{--rm-navh:79px}
section[id],.rm-sec,:target{scroll-margin-top:calc(var(--rm-navh) + 26px)}
.rm-lockbadge{display:flex;gap:11px;align-items:flex-start;background:#fff8e5;border:1px solid #e8d8ab;border-left:5px solid #8b6d1f;border-radius:12px;padding:12px 14px;margin:0 0 16px;font-size:14px;line-height:1.55;color:#4a3c12}
.rm-lockbadge .rm-lockico{font-size:19px;line-height:1.35}
.rm-lockbadge .rm-lockbody{flex:1;display:grid;gap:6px;justify-items:start}
.rm-lockbadge b{font-size:14px}
.rm-lockbadge .rm-lockgo{text-decoration:none}
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

# Restored modules hash
rm_js_hash = hashlib.md5(
    open(os.path.join(ROOT, "js", "restored-modules.js"), "rb").read()
).hexdigest()[:10]
RESTORED_MODULES_TAG = f'<script src="js/restored-modules.js?v={rm_js_hash}"></script>\n'

# Assemble the whole sequential body
body_parts = [
    NAV,
    GUIDELINE_STEPPER,
    '<main class="sah-main-guideline">',
    STEP1_HTML,
    STEP2_HTML,
    STEP3_HTML,
    STEP4_HTML,
    STEP5_HTML,
    STEP6_HTML,
    STEP7_HTML,
    STEP8_HTML,
    STEP9_HTML,
    STEP_DASHBOARD_HTML,
    '</main>',
    MODALS_HTML,
    TRAILING_HTML,
    RM_CSS,
    GUIDELINE_CSS,
    RESTORED_MODULES_TAG,
    J39,
    GUIDELINE_JS
]

assembled_body = "\n".join(body_parts)

final_html = HEADER_HTML + "\n" + assembled_body + "\n</body>\n</html>"

# Inject Google Fonts
final_html = final_html.replace(
    "<title>",
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;800;900&family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,700&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">\n'
    "<title>", 1)

# Inject content-studio.js into <head>
studio_js = os.path.join(ROOT, "js", "content-studio.js")
studio_hash = hashlib.md5(open(studio_js, "rb").read()).hexdigest()[:10]
studio_tag = f'<script src="js/content-studio.js?v={studio_hash}"></script>\n'
head_end = final_html.index("<head>") + len("<head>")
final_html = final_html[:head_end] + "\n" + studio_tag + final_html[head_end:]

# Sync trien-lam.html
trien_lam_path = os.path.join(ROOT, "trien-lam.html")
if os.path.isfile(trien_lam_path):
    tl_html = open(trien_lam_path, encoding="utf-8").read()
    tl_synced, n = re.subn(r"js/content-studio\.js\?v=[0-9a-f]+", "js/content-studio.js?v=" + studio_hash, tl_html)
    if n == 1 and tl_synced != tl_html:
        open(trien_lam_path, "w", encoding="utf-8").write(tl_synced)

# Write output file
open(OUT, "w", encoding="utf-8").write(final_html)

print(f"  ✓ Successfully wrote index.html: {len(final_html)/1024:.1f} KB")
print(f"  ✓ Applied {REPAIRS} repairs")
print("=== PowerPoint Slide Mode & Landing Page Build Complete ===")
