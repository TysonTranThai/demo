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
  <a class="rm-topnav-link" href="#step9-danhgia" onclick="goToSlide(8); return false;">📝 Đánh giá & Phản tư</a>
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
      <a href="#step1-trangchu" class="sah-step-pill active" data-step="1" onclick="goToSlide(0); return false;">
        <span class="sah-step-num">1</span>
        <span class="sah-step-txt">Trang chủ</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step2-bando" class="sah-step-pill" data-step="2" onclick="goToSlide(1); return false;">
        <span class="sah-step-num">2</span>
        <span class="sah-step-txt">Bản đồ</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step3-5khudisan" class="sah-step-pill" data-step="3" onclick="goToSlide(2); return false;">
        <span class="sah-step-num">3</span>
        <span class="sah-step-txt">5 Di sản</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step4-hosodisan" class="sah-step-pill" data-step="4" onclick="goToSlide(3); return false;">
        <span class="sah-step-num">4</span>
        <span class="sah-step-txt">Hồ sơ 15 ảnh</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step5-phong3d" class="sah-step-pill" data-step="5" onclick="goToSlide(4); return false;">
        <span class="sah-step-num">5</span>
        <span class="sah-step-txt">Phòng 3D</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step6-ai5a" class="sah-step-pill" data-step="6" onclick="goToSlide(5); return false;">
        <span class="sah-step-num">6</span>
        <span class="sah-step-txt">AI 5A</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step7-xuongsangtao" class="sah-step-pill" data-step="7" onclick="goToSlide(6); return false;">
        <span class="sah-step-num">7</span>
        <span class="sah-step-txt">Xưởng sáng tạo</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step8-argallery" class="sah-step-pill" data-step="8" onclick="goToSlide(7); return false;">
        <span class="sah-step-num">8</span>
        <span class="sah-step-txt">Triển lãm AR</span>
      </a>
      <span class="sah-step-arrow">→</span>
      <a href="#step9-danhgia" class="sah-step-pill" data-step="9" onclick="goToSlide(8); return false;">
        <span class="sah-step-num">9</span>
        <span class="sah-step-txt">Đánh giá & Phản tư</span>
      </a>
      <span class="sah-step-sep teacher-only" style="display:none;">|</span>
      <a href="#step-dashboard" class="sah-step-pill sah-step-dash teacher-only" data-step="10" style="display:none;" onclick="goToSlide(9); return false;">
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
STEP1_HTML = f"""<!-- STEP 1: TRANG CHU - DEDICATED LANDING PAGE -->
<section id="step1-trangchu" class="sah-step-sec sah-slide active-slide sah-landing-page">
  <div class="sah-landing-hero">
    <div class="sah-landing-badge-bar">
      <span class="sah-badge-accent">⭐ DỰ ÁN MĨ THUẬT SỐ DI SẢN VĂN HÓA ĐỊA PHƯƠNG</span>
      <span class="sah-badge-sub">TỈNH HƯNG YÊN • CHÂU THỔ SÔNG HỒNG</span>
    </div>
    
    <h1 class="sah-landing-title">
      SMART ART HERITAGE
      <span class="sah-landing-sub">Hệ Sinh Thái Giáo Dục Mĩ Thuật Tích Hợp AI 5A, 3D WebGL & Thực Tế Tăng Cường (AR)</span>
    </h1>

    <div class="sah-landing-meta-strip">
      <div class="sah-meta-item">🏛️ <b>Đơn vị nghiên cứu:</b> Trường THCS & THPT tỉnh Hưng Yên</div>
      <div class="sah-meta-item">🎓 <b>Đối tượng:</b> Học sinh THCS, THPT & Giáo viên toàn quốc</div>
      <div class="sah-meta-item">📜 <b>Chuẩn đầu ra:</b> Phát triển năng lực mĩ thuật & cảm thụ di sản</div>
    </div>

    <p class="sah-landing-lead">
      Chào mừng em đến với <b>Smart Art Heritage</b> — giải pháp học tập Mĩ thuật số đột phá, biến di sản văn hóa địa phương thành chất liệu sáng tạo đương đại. Được thiết kế theo <b>hành trình 9 bước tuần tự như một bài giảng trình chiếu sống động</b>, hệ thống dẫn dắt em từ quan sát tư liệu, xoay mô hình 3D 360°, đối thoại cùng trợ lý AI 5A, thử nghiệm phác thảo cho đến triển lãm AR trong không gian thực.
    </p>

    <div class="sah-landing-hero-actions">
      <button type="button" class="sah-btn-hero-primary" onclick="goToSlide(1)">
        🚀 BẮT ĐẦU HÀNH TRÌNH 9 BƯỚC (Trang 2: Bản đồ) →
      </button>
      <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(1)">
        🗺️ Khám phá Bản đồ số
      </button>
      <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(4)">
        🧊 Phòng 3D 360°
      </button>
      <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(5)">
        🤖 Trợ lý AI 5A
      </button>
      <button type="button" class="sah-btn-hero-ghost" onclick="goToSlide(7)">
        📱 Triển lãm AR
      </button>
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
      <div class="sah-roadmap-step" onclick="goToSlide(0)">
        <span class="sah-rm-num">1</span>
        <b>Trang chủ</b>
        <small>Khởi động & Trụ cột</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(1)">
        <span class="sah-rm-num">2</span>
        <b>Bản đồ số</b>
        <small>Định vị di sản</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(2)">
        <span class="sah-rm-num">3</span>
        <b>5 Khu di sản</b>
        <small>Chọn hồ sơ nghiên cứu</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(3)">
        <span class="sah-rm-num">4</span>
        <b>Hồ sơ 15 ảnh</b>
        <small>Hotspot 3 tầng</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(4)">
        <span class="sah-rm-num">5</span>
        <b>Phòng 3D</b>
        <small>Xoay 360° đa chiều</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(5)">
        <span class="sah-rm-num">6</span>
        <b>AI 5A Studio</b>
        <small>Hỏi & Gợi mở ý tưởng</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(6)">
        <span class="sah-rm-num">7</span>
        <b>Xưởng sáng tạo</b>
        <small>Phác thảo → Tác phẩm</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(7)">
        <span class="sah-rm-num">8</span>
        <b>Triển lãm AR</b>
        <small>Trưng bày thực tế ảo</small>
      </div>
      <div class="sah-rm-arr">→</div>
      <div class="sah-roadmap-step" onclick="goToSlide(8)">
        <span class="sah-rm-num">9</span>
        <b>Đánh giá & Phản tư</b>
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
        <video id="landingVideoPlayer" controls preload="none" poster="assets/extracted/000_Ph__Hi_n.jpeg" style="width:100%;border-radius:16px;background:#000;">
          <source id="videoSource" src="video%20v%E1%BB%81%20qu%E1%BA%A7n%20th%E1%BB%83%20ph%E1%BB%91%20hi%E1%BA%BFn.mp4" type="video/mp4">
          Trình duyệt của em không hỗ trợ phát video HTML5.
        </video>
        <div class="sah-video-caption" id="videoCaption">
          <b>Phim tài liệu 01:</b> Quần thể di tích lịch sử và thương cảng cổ Phố Hiến (Hưng Yên)
        </div>
      </div>
      <div class="sah-video-playlist">
        <div class="sah-video-item active" onclick="switchLandingVideo('video%20v%E1%BB%81%20qu%E1%BA%A7n%20th%E1%BB%83%20ph%E1%BB%91%20hi%E1%BA%BFn.mp4', 'Phim tài liệu 01: Quần thể di tích lịch sử và thương cảng cổ Phố Hiến (Hưng Yên)', this)">
          <span class="sah-v-ico">▶</span>
          <div>
            <b>Phố Hiến — Đô thị cổ</b>
            <small>Quần thể di tích "Thứ nhất Kinh Kỳ, thứ nhì Phố Hiến"</small>
          </div>
        </div>
        <div class="sah-video-item" onclick="switchLandingVideo('Da%CC%82%CC%81u%20a%CC%82%CC%81n%20nha%CC%80%20Tra%CC%82%CC%80n%20tre%CC%82n%20vu%CC%80ng%20%C4%91a%CC%82%CC%81t%20Tha%CC%81i%20Bi%CC%80nh%20xu%CC%9Ba%20%20HYTV.mp4', 'Phim tài liệu 02: Dấu ấn nhà Trần trên vùng đất Thái Bình xưa (Đền Trần Hưng Hà) - HYTV', this)">
          <span class="sah-v-ico">▶</span>
          <div>
            <b>Dấu ấn vương triều Trần</b>
            <small>Đền Trần Hưng Hà & khu lăng mộ các vua Trần</small>
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
</section>
"""

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
        <div class="sah-map-item" onclick="selectHeritageByCode('phohien')">
          <span class="sah-site-pill" style="background:#B3261E;">01</span>
          <div class="sah-item-info">
            <b>Phố Hiến</b>
            <p>TP. Hưng Yên • Quần thể di tích thương cảng cổ "Thứ nhất Kinh Kỳ, thứ nhì Phố Hiến".</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('chuakeo')">
          <span class="sah-site-pill" style="background:#C89547;">02</span>
          <div class="sah-item-info">
            <b>Chùa Keo</b>
            <p>Vũ Thư • Đỉnh cao kiến trúc gỗ cổ truyền, gác chuông 3 tầng mái thanh thoát.</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('dentran')">
          <span class="sah-site-pill" style="background:#285B46;">03</span>
          <div class="sah-item-info">
            <b>Đền Trần Hưng Hà</b>
            <p>Hưng Hà • Nơi phát tích vương triều Trần, không gian trang nghiêm và khu lăng mộ vua.</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('lequydon')">
          <span class="sah-site-pill" style="background:#1B4965;">04</span>
          <div class="sah-item-info">
            <b>Khu lưu niệm Lê Quý Đôn</b>
            <p>Hưng Hà • Không gian tưởng niệm Nhà bác học uyên bác nhất lịch sử phong kiến Việt Nam.</p>
          </div>
          <button type="button" class="sah-item-go">Khám phá →</button>
        </div>
        <div class="sah-map-item" onclick="selectHeritageByCode('dongxam')">
          <span class="sah-site-pill" style="background:#6B4226;">05</span>
          <div class="sah-item-info">
            <b>Làng chạm bạc Đồng Xâm</b>
            <p>Kiến Xương • Nghệ thuật kim hoàn truyền thống, hoa văn chạm khắc tinh xảo.</p>
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

  {make_ppt_footer(8, "Xưởng sáng tạo", "Đánh giá & Phản tư")}
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
STEP9_HTML = f"""<!-- STEP 9: DANH GIA & PHAN TU -->
<section id="step9-danhgia" class="sah-step-sec sah-slide">
  <div class="sah-step-badge">BƯỚC 9 / 9 • ĐÁNH GIÁ & PHẢN TƯ</div>
  <div class="sah-sec-header">
    <h2>📝 ĐÁNH GIÁ & PHẢN TƯ • PHIẾU 3-2-1 & HỒ SƠ HÀNH TRÌNH</h2>
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

  {make_ppt_footer(10, "Đánh giá & Phản tư", "Trang chủ", is_last=True)}
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
  animation: slideFadeIn 0.28s ease-out;
}
@keyframes slideFadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

body:not(.slide-mode) .sah-slide {
  display: block !important;
}

/* Stepper Bar */
.sah-stepper-nav {
  position: sticky;
  top: 48px;
  z-index: 55;
  background: #0e2017;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  font-family: 'Plus Jakarta Sans', sans-serif;
}
.sah-stepper-container {
  max-width: 1320px;
  margin: 0 auto;
  padding: 6px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.sah-stepper-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sah-stepper-btn-quick {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.18);
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-stepper-btn-quick:hover {
  background: #285b46;
  border-color: #4ade80;
}
.sah-stepper-cur-badge {
  font-size: 12px;
  font-weight: 700;
  color: #f1d084;
  white-space: nowrap;
  padding: 0 4px;
}
.sah-stepper-track {
  display: flex;
  align-items: center;
  gap: 5px;
  overflow-x: auto;
  scrollbar-width: thin;
  padding-bottom: 2px;
  flex: 1;
}
.sah-step-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: #d1ded6;
  text-decoration: none;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s ease;
  cursor: pointer;
}
.sah-step-pill:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #ffffff;
}
.sah-step-pill.active {
  background: #285b46;
  border-color: #4ade80;
  color: #ffffff;
  box-shadow: 0 0 10px rgba(74, 222, 128, 0.35);
}
.sah-step-pill .sah-step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  font-size: 10px;
  font-weight: 800;
}
.sah-step-pill.active .sah-step-num {
  background: #4ade80;
  color: #0e2017;
}
.sah-step-arrow {
  color: rgba(255, 255, 255, 0.3);
  font-size: 11px;
}
.sah-step-sep {
  color: rgba(255, 255, 255, 0.3);
  margin: 0 3px;
}
.sah-step-dash {
  background: rgba(200, 149, 71, 0.2);
  border-color: rgba(200, 149, 71, 0.4);
  color: #f1d084;
}
.sah-view-toggle {
  background: rgba(255, 255, 255, 0.1);
  color: #d7ded9;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 5px 11px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s ease;
}
.sah-view-toggle:hover {
  background: #285b46;
  color: #fff;
  border-color: #4ade80;
}

/* PowerPoint Slide Navigation Bar (Footer of every slide) */
.sah-ppt-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 36px;
  padding: 18px 22px;
  background: #f7faf8;
  border: 1px solid #cfe0d6;
  border-radius: 18px;
  flex-wrap: wrap;
}
.sah-ppt-btn {
  background: #285b46;
  color: #ffffff !important;
  border: 0;
  border-radius: 12px;
  padding: 12px 22px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(40, 91, 70, 0.2);
  text-decoration: none;
}
.sah-ppt-btn:hover {
  background: #1d4033;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(40, 91, 70, 0.28);
}
.sah-ppt-prev {
  background: #eef3f0;
  color: #285b46 !important;
  box-shadow: none;
  border: 1px solid #c9d8d0;
}
.sah-ppt-prev:hover {
  background: #dce7e1;
}
.sah-ppt-finish {
  background: #c89547;
  color: #12281f !important;
}
.sah-ppt-finish:hover {
  background: #b58338;
}
.sah-ppt-indicator {
  text-align: center;
  font-size: 13px;
  color: #5d6b63;
}
.sah-ppt-slide-num b {
  color: #172119;
  font-size: 15px;
}
.sah-ppt-key-hint {
  font-size: 11px;
  color: #7b8b82;
  margin-top: 2px;
}
.sah-ppt-key-hint kbd {
  background: #e6eee9;
  border: 1px solid #c9d8d0;
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 10px;
  font-family: monospace;
}

/* Step Section Layout */
.sah-step-sec {
  max-width: 1200px;
  margin: 28px auto 40px;
  padding: 28px;
  background: #ffffff;
  border: 1px solid #d7e0da;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(18, 40, 31, 0.04);
  scroll-margin-top: calc(var(--rm-navh) + 60px);
}
.sah-step-sec .rm-sec {
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
#step6-ai5a #rmChat {
  margin-top: 28px !important;
  border-top: 1px solid #d7e0da !important;
  padding-top: 24px !important;
}
#step8-argallery #rmExhibit {
  margin-top: 28px !important;
  border-top: 1px solid #d7e0da !important;
  padding-top: 24px !important;
}
.sah-step-badge {
  display: inline-block;
  background: #eaf3ee;
  border: 1px solid #c3ded0;
  color: #285b46;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  padding: 5px 12px;
  border-radius: 999px;
  margin-bottom: 12px;
}
.sah-sec-header {
  margin-bottom: 22px;
}
.sah-sec-header h2 {
  font-size: 26px;
  font-weight: 800;
  color: #172119;
  margin: 0 0 6px;
  line-height: 1.25;
}
.sah-sec-sub {
  color: #53645b;
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

/* Landing Page Styles */
.sah-landing-page {
  padding: 34px;
}
.sah-landing-hero {
  border-bottom: 1px solid #e0eae3;
  padding-bottom: 32px;
  margin-bottom: 34px;
}
.sah-landing-badge-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.sah-badge-accent {
  background: #fdf6e9;
  border: 1px solid #ebd9ab;
  color: #8b6d1f;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  padding: 5px 12px;
  border-radius: 999px;
}
.sah-badge-sub {
  color: #6b7a72;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
}
.sah-landing-title {
  font-size: 38px;
  font-weight: 800;
  line-height: 1.18;
  color: #172119;
  margin: 0 0 16px;
  letter-spacing: -0.01em;
}
.sah-landing-sub {
  display: block;
  font-size: 22px;
  font-weight: 600;
  color: #285b46;
  margin-top: 6px;
  line-height: 1.35;
}
.sah-landing-meta-strip {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background: #f8faf8;
  border-radius: 14px;
  border: 1px solid #d7e0da;
  font-size: 13px;
  color: #4b5d52;
  margin-bottom: 18px;
}
.sah-landing-lead {
  font-size: 16px;
  line-height: 1.7;
  color: #3f5146;
  margin-bottom: 26px;
  max-width: 1040px;
}
.sah-landing-hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.sah-btn-hero-primary {
  background: #285b46;
  color: #fff;
  border: 0;
  border-radius: 14px;
  padding: 14px 28px;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 6px 20px rgba(40, 91, 70, 0.25);
}
.sah-btn-hero-primary:hover {
  background: #1d4033;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(40, 91, 70, 0.35);
}
.sah-btn-hero-ghost {
  background: #f0f6f2;
  color: #285b46;
  border: 1px solid #c9d8d0;
  border-radius: 14px;
  padding: 13px 20px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-btn-hero-ghost:hover {
  background: #e2ece6;
  border-color: #285b46;
}
.sah-landing-section {
  margin: 36px 0;
}
.sah-landing-sec-head {
  text-align: center;
  max-width: 720px;
  margin: 0 auto 24px;
}
.sah-tag-pill {
  background: #eaf3ee;
  color: #285b46;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  padding: 4px 12px;
  border-radius: 999px;
  display: inline-block;
  margin-bottom: 6px;
}
.sah-landing-sec-head h2 {
  font-size: 26px;
  font-weight: 800;
  color: #172119;
  margin: 4px 0 6px;
}
.sah-landing-sec-head p {
  color: #617369;
  font-size: 14px;
  margin: 0;
}

/* 4 Pillars Grid */
.sah-pillars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 18px;
}
.sah-pillar-card {
  background: #fdfefd;
  border: 1px solid #d7e0da;
  border-radius: 18px;
  padding: 22px;
  display: grid;
  gap: 10px;
  transition: all 0.2s ease;
}
.sah-pillar-card:hover {
  border-color: #285b46;
  box-shadow: 0 10px 28px rgba(40, 91, 70, 0.1);
  transform: translateY(-3px);
}
.sah-pillar-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sah-pillar-ico { font-size: 32px; }
.sah-pillar-step-tag {
  background: #f0f6f2;
  color: #285b46;
  font-size: 10px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 6px;
}
.sah-pillar-name {
  font-size: 17px;
  font-weight: 800;
  color: #172119;
}
.sah-pillar-desc {
  font-size: 13px;
  line-height: 1.6;
  color: #55675c;
}
.sah-pillar-rule {
  font-size: 11px;
  font-weight: 700;
  color: #8b6d1f;
  background: #fff8e8;
  padding: 6px 10px;
  border-radius: 8px;
}

/* Roadmap Flowchart */
.sah-roadmap-track {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  padding: 16px 8px;
  background: #f8faf8;
  border-radius: 20px;
  border: 1px solid #d7e0da;
}
.sah-roadmap-step {
  background: #fff;
  border: 1px solid #d7e0da;
  border-radius: 14px;
  padding: 12px 14px;
  min-width: 110px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1;
}
.sah-roadmap-step:hover {
  border-color: #285b46;
  background: #f0f8f3;
  transform: translateY(-2px);
}
.sah-rm-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #285b46;
  color: #fff;
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
  color: #172119;
  white-space: nowrap;
}
.sah-roadmap-step small {
  display: block;
  font-size: 10px;
  color: #7b8b82;
  white-space: nowrap;
}
.sah-rm-arr {
  color: #a4b5ab;
  font-weight: 800;
  font-size: 14px;
}

/* Video Showcase in Landing */
.sah-video-showcase {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 860px) {
  .sah-video-showcase { grid-template-columns: 1fr; }
}
.sah-video-player-wrap {
  background: #0e1c17;
  border-radius: 18px;
  padding: 12px;
  border: 1px solid #d7e0da;
}
.sah-video-caption {
  color: #cfe0d6;
  font-size: 12px;
  padding: 8px 4px 2px;
}
.sah-video-playlist {
  display: grid;
  gap: 10px;
}
.sah-video-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  background: #f8faf8;
  border: 1px solid #d7e0da;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-video-item:hover, .sah-video-item.active {
  background: #f0f8f3;
  border-color: #285b46;
}
.sah-v-ico {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #285b46;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}
.sah-video-item b {
  font-size: 13px;
  color: #172119;
  display: block;
}
.sah-video-item small {
  font-size: 11px;
  color: #617369;
}

/* Landing Stats Grid */
.sah-landing-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 36px 0;
}
.sah-lstat-card {
  background: #f9fbf9;
  border: 1px solid #d7e0da;
  border-radius: 18px;
  padding: 22px;
  text-align: center;
}
.sah-lstat-num {
  font-size: 38px;
  font-weight: 800;
  color: #285b46;
  line-height: 1;
  margin-bottom: 6px;
}
.sah-lstat-lbl {
  font-size: 14px;
  font-weight: 700;
  color: #172119;
  margin-bottom: 4px;
}
.sah-lstat-card small {
  font-size: 11px;
  color: #7b8b82;
}

/* Landing CTA Banner */
.sah-landing-cta-banner {
  background: linear-gradient(135deg, #12281f 0%, #1e4435 100%);
  color: #fff;
  border-radius: 20px;
  padding: 30px;
  text-align: center;
  margin: 28px 0;
  box-shadow: 0 10px 28px rgba(18, 40, 31, 0.2);
}
.sah-landing-cta-banner h3 {
  font-size: 24px;
  margin: 0 0 8px;
}
.sah-landing-cta-banner p {
  color: #d1ded6;
  font-size: 14px;
  margin: 0 0 20px;
}

/* Map Layout in Step 2 */
.sah-map-layout {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 860px) {
  .sah-map-layout { grid-template-columns: 1fr; }
}
.sah-map-visual {
  background: #fffdf9;
  border-radius: 20px;
  border: 1px solid #e5dfc8;
  padding: 10px;
  display: flex;
  justify-content: center;
}
.sah-map-visual svg {
  width: 100%;
  height: auto;
  max-width: 560px;
  display: block;
}
.sah-map-sidebar {
  display: grid;
  gap: 10px;
}
.sah-map-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #6b7a72;
}
.sah-map-card-head b { color: #172119; }
.sah-map-list {
  display: grid;
  gap: 8px;
}
.sah-map-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: #f8faf8;
  border: 1px solid #d7e0da;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-map-item:hover {
  border-color: #285b46;
  background: #f0f8f3;
  transform: translateX(3px);
}
.sah-site-pill {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sah-item-info { flex: 1; }
.sah-item-info b {
  font-size: 14px;
  color: #172119;
  display: block;
}
.sah-item-info p {
  font-size: 12px;
  color: #6b7a72;
  margin: 2px 0 0;
  line-height: 1.4;
}
.sah-item-go {
  background: #285b46;
  color: #fff;
  border: 0;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

/* Rule Banner */
.sah-rule-banner {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  background: #fff8e5;
  border: 1px solid #ebd9ab;
  border-left: 5px solid #c89547;
  border-radius: 14px;
  padding: 14px 18px;
  margin-bottom: 20px;
}
.sah-rule-ico { font-size: 22px; line-height: 1.2; }
.sah-rule-body b { font-size: 14px; color: #6b5316; display: block; margin-bottom: 4px; }
.sah-rule-body p { font-size: 13px; color: #574413; line-height: 1.5; margin: 0; }

/* 5A Process Bar */
.sah-5a-process-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f4f8f5;
  border: 1px solid #cde0d5;
  border-radius: 16px;
  padding: 12px 18px;
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
.sah-5a-step b { font-size: 13px; color: #285b46; letter-spacing: 0.05em; }
.sah-5a-step span { font-size: 11px; color: #6b7a72; }
.sah-5a-arrow { color: #8fa79a; font-weight: 800; font-size: 14px; }

/* Studio Flow Bar in Step 7 */
.sah-studio-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fdfaf4;
  border: 1px solid #edd9b9;
  border-radius: 14px;
  padding: 10px 16px;
  margin-bottom: 20px;
  overflow-x: auto;
}
.sah-flow-badge {
  font-size: 12px;
  font-weight: 700;
  color: #7a501e;
  background: #fff;
  border: 1px solid #dec39b;
  padding: 6px 12px;
  border-radius: 999px;
  white-space: nowrap;
}
.sah-flow-sep { color: #caa471; font-size: 12px; }

/* AR Card in Step 8 */
.sah-ar-card {
  display: flex;
  gap: 24px;
  align-items: center;
  background: linear-gradient(135deg, #10241b 0%, #1a382b 100%);
  color: #fff;
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(16, 36, 27, 0.2);
}
@media (max-width: 760px) {
  .sah-ar-card { flex-direction: column; text-align: center; }
}
.sah-ar-info { flex: 1; display: grid; gap: 8px; }
.sah-ar-tag {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.15em;
  color: #f1d084;
}
.sah-ar-info h3 { font-size: 20px; margin: 0; color: #fff; }
.sah-ar-info p { color: #cfe0d6; font-size: 14px; line-height: 1.55; margin: 0; }
.sah-ar-actions { display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap; }
.sah-ar-qr {
  display: grid;
  justify-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.1);
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}
.sah-ar-qr small { font-size: 11px; color: #f1d084; text-align: center; max-width: 120px; }

/* Rubric & Pre-Post Evaluation in Step 9 */
.sah-eval-container {
  display: grid;
  gap: 24px;
  margin: 28px 0;
}
.sah-rubric-card, .sah-prepost-card {
  background: #fbfdfc;
  border: 1px solid #d7e0da;
  border-radius: 18px;
  padding: 22px;
}
.sah-eval-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}
.sah-eval-head h3 { font-size: 18px; margin: 0; color: #172119; }
.sah-eval-badge {
  background: #e4f0e8;
  color: #285b46;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
}
.sah-eval-badge.gold { background: #fff4d9; color: #8b6d1f; }
.sah-eval-sub { color: #617369; font-size: 13px; margin: 0 0 16px; line-height: 1.5; }
.sah-rubric-table-wrap { overflow-x: auto; }
.sah-rubric-tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  line-height: 1.5;
}
.sah-rubric-tbl th, .sah-rubric-tbl td {
  border: 1px solid #d7e0da;
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}
.sah-rubric-tbl th {
  background: #f0f6f2;
  color: #172119;
  font-weight: 700;
  font-size: 12px;
}
.sah-rubric-tbl td:first-child { background: #f7faf8; width: 22%; }
.sah-rubric-tbl td:first-child small { color: #6b7a72; }

/* Pre-Post Chart */
.sah-chart-grid { display: grid; gap: 14px; }
.sah-chart-item { display: grid; gap: 6px; }
.sah-chart-label { display: flex; justify-content: space-between; font-size: 13px; color: #34443b; }
.sah-chart-label b { color: #285b46; }
.sah-chart-bars {
  position: relative;
  height: 26px;
  background: #e8f0eb;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
}
.sah-bar-pre {
  height: 100%;
  background: #9ab4a7;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 1;
}
.sah-bar-post {
  height: 100%;
  background: linear-gradient(90deg, #285b46 0%, #3e8869 100%);
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 2;
  opacity: 0.92;
}
.sah-chart-legend {
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #5d6b63;
  margin-top: 14px;
  flex-wrap: wrap;
}
.sah-chart-legend span { display: flex; align-items: center; gap: 6px; }
.sah-dot-pre {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  background: #9ab4a7;
}
.sah-dot-post {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  background: #285b46;
}

/* Dashboard Section */
.sah-dashboard-sec { background: #f7faf8; border-color: #c9dbd1; }
.sah-dash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 20px 0;
}
.sah-dash-card {
  background: #ffffff;
  border: 1px solid #d7e0da;
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(18, 40, 31, 0.04);
}
.sah-dash-num {
  font-size: 36px;
  font-weight: 800;
  color: #285b46;
  line-height: 1;
  margin-bottom: 6px;
}
.sah-dash-lbl {
  font-size: 13px;
  font-weight: 700;
  color: #172119;
  margin-bottom: 4px;
}
.sah-dash-card small { font-size: 11px; color: #6b7a72; }
.sah-dash-actions { text-align: center; margin: 20px 0; }

/* Radio button tab panel visibility sync */
#h1:checked ~ #step3-5khudisan .tabs label[for="h1"],
#h1:checked ~ * .tabs label[for="h1"] { background: var(--ink); color: #fff; border-color: var(--ink); }
#h1:checked ~ #step4-hosodisan .panels #p1,
#h1:checked ~ * .panels #p1 { display: block !important; }
#h2:checked ~ #step3-5khudisan .tabs label[for="h2"],
#h2:checked ~ * .tabs label[for="h2"] { background: var(--ink); color: #fff; border-color: var(--ink); }
#h2:checked ~ #step4-hosodisan .panels #p2,
#h2:checked ~ * .panels #p2 { display: block !important; }
#h3:checked ~ #step3-5khudisan .tabs label[for="h3"],
#h3:checked ~ * .tabs label[for="h3"] { background: var(--ink); color: #fff; border-color: var(--ink); }
#h3:checked ~ #step4-hosodisan .panels #p3,
#h3:checked ~ * .panels #p3 { display: block !important; }
#h4:checked ~ #step3-5khudisan .tabs label[for="h4"],
#h4:checked ~ * .tabs label[for="h4"] { background: var(--ink); color: #fff; border-color: var(--ink); }
#h4:checked ~ #step4-hosodisan .panels #p4,
#h4:checked ~ * .panels #p4 { display: block !important; }
#h5:checked ~ #step3-5khudisan .tabs label[for="h5"],
#h5:checked ~ * .tabs label[for="h5"] { background: var(--ink); color: #fff; border-color: var(--ink); }
#h5:checked ~ #step4-hosodisan .panels #p5,
#h5:checked ~ * .panels #p5 { display: block !important; }
#home0:checked ~ #step4-hosodisan .panels #p0,
#home0:checked ~ * .panels #p0 { display: block !important; }
#h1:checked ~ * .switcher label[for="h1"],
#h2:checked ~ * .switcher label[for="h2"],
#h3:checked ~ * .switcher label[for="h3"],
#h4:checked ~ * .switcher label[for="h4"],
#h5:checked ~ * .switcher label[for="h5"] { background: #fff; color: #172119; }
#home0:checked ~ * .switcher label[for="home0"] { background: #fff; color: #172119; }
</style>
<!-- SAH-GUIDELINE-CSS-END -->
"""

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
  'Đánh giá & Phản tư',
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
  window.toggleSlideMode = toggleSlideMode;
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
    '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">\n'
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
