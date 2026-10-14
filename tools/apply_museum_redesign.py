import re
import os

ROOT = "/Users/tysontran/Desktop/Smart Art Heritage"
BUILD_SCRIPT = os.path.join(ROOT, "tools", "build_index.py")

with open(BUILD_SCRIPT, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Google Fonts in build_index.py
old_font = '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">'
new_font = '<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;800;900&family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,700&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">'
if old_font in content:
    content = content.replace(old_font, new_font)

print("Font link updated:", new_font in content)

# 2. Write new STEP1_HTML
new_step1 = '''<!-- STEP 1: TRANG CHU - DEDICATED LUXURY MUSEUM LANDING PAGE -->
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
          <div class="sah-meta-item">🏛️ <b>Đơn vị nghiên cứu:</b> Trường THCS & THPT tỉnh Hưng Yên</div>
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
              <h4>Gác chuông Chùa Keo (Vũ Thư)</h4>
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
            <span class="sah-exhibit-loc">Kiến Xương, Thái Bình • Làng nghề truyền thống 500 năm</span>
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
</section>'''

# Replace STEP1_HTML in content
p1 = content.find("STEP1_HTML = f\"\"\"")
p2 = content.find("\n# --------------------------------------------------------------------------\n# 7. SLIDE 2:")
if p1 != -1 and p2 != -1:
    content = content[:p1] + "STEP1_HTML = f\"\"\"" + new_step1 + "\"\"\"\n" + content[p2:]
    print("STEP1_HTML replaced successfully!")
else:
    print("Failed to find STEP1_HTML boundaries:", p1, p2)

# Write to build_index.py
with open(BUILD_SCRIPT, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated build_index.py with new landing page!")
