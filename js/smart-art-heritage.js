/**
 * SMART ART HERITAGE V1.0 - CORE INTERACTIVE ENGINE
 * Three.js 3D Viewer, Hotspots, 3-2-1 Form, AI 5A Studio, Canvas, & Dashboard
 */

// Global State
const SAH_STATE = {
  currentHeritage: 'chuakeo',
  studentId: localStorage.getItem('sah_student_id') || 'HS-6A1-024',
  studentClass: localStorage.getItem('sah_student_class') || '6A1',
  studentName: localStorage.getItem('sah_student_name') || 'Nguyễn Minh An',
  active3dMode: 'textured',
  activeLighting: 'day',
  activeHotspot3D: null,
  heritageData: null,
  currentAiStep: 0,
  chatHistory: []
};

// Default Built-in Heritage Data
const BUILTIN_HERITAGES = {
  phohien: {
    name: "Phố Hiến",
    tagline: "Đô thị & Thương cảng cổ thế kỷ XVII",
    year: "Thế kỷ XVII",
    location: "Thành phố Hưng Yên",
    cover: "assets/extracted/cover_phohien.jpeg",
    description: "Từng được mệnh danh là 'Thứ nhất Kinh Kỳ, thứ nhì Phố Hiến', đây là thương cảng quốc tế sầm uất bậc nhất Đàng Ngoài với quần thể di tích đình, đền, chùa và hồ Bán Nguyệt thơ mộng.",
    tags: ["Thương Cảng Cổ", "Đền Mẫu", "Hồ Bán Nguyệt", "Kiến Trúc Gỗ"],
    hotspotsCount: 15,
    photosCount: 15
  },
  chuakeo: {
    name: "Chùa Keo",
    tagline: "Kiệt tác kiến trúc gỗ & Gác chuông 3 tầng 12 mái",
    year: "Khởi dựng 1632",
    location: "Hưng Yên cổ / Thái Bình",
    cover: "assets/extracted/cover_chuakeo.jpeg",
    description: "Đỉnh cao của kiến trúc gỗ cổ truyền Việt Nam. Gác chuông Chùa Keo cao 11.04m với 3 tầng 12 mái cong hình đầu đao, liên kết bằng hệ thống con sơn đấu củng chịu lực tinh xảo hoàn toàn không dùng đinh sắt.",
    tags: ["Gác Chuông 3 Tầng", "12 Mái Cong", "Đấu Củng", "Gỗ Lim"],
    hotspotsCount: 15,
    photosCount: 15
  },
  dentran: {
    name: "Đền Trần Hưng Hà",
    tagline: "Vùng đất phát tích & Lăng mộ các vua triều Trần",
    year: "Hào khí Đông A",
    location: "Hưng Hà",
    cover: "assets/extracted/cover_dentran.jpeg",
    description: "Nơi an nghỉ của các vị vua khởi nghiệp nhà Trần, mang đậm hào khí Đông A với kiến trúc trục thần đạo trang nghiêm, bậc tam cấp chạm rồng đá và các lễ hội rước nước, kéo chữ truyền thống.",
    tags: ["Lăng Mộ Triều Trần", "Hào Khí Đông A", "Rồng Đá", "Trục Thần Đạo"],
    hotspotsCount: 15,
    photosCount: 15
  },
  lequydon: {
    name: "Khu lưu niệm Lê Quý Đôn",
    tagline: "Không gian tưởng niệm Nhà bác học bách khoa thế kỷ XVIII",
    year: "Thế kỷ XVIII",
    location: "Diên Hà",
    cover: "assets/extracted/cover_lequydon.jpeg",
    description: "Khu lưu niệm tôn vinh danh nhân văn hóa, nhà bác học lỗi lạc Lê Quý Đôn. Không gian kết hợp giữa đền thờ truyền thống, tượng danh nhân, thư tịch cổ và các hoạt động giáo dục địa phương.",
    tags: ["Nhà Bác Học", "Tượng Đồng Danh Nhân", "Thư Tịch Cổ", "Giáo Dục Địa Phương"],
    hotspotsCount: 15,
    photosCount: 15
  },
  dongxam: {
    name: "Làng nghề chạm bạc Đồng Xâm",
    tagline: "Nghệ thuật chạm khắc kim hoàn thủ công tinh xảo 500 năm",
    year: "Truyền thống 500 năm",
    location: "Kiến Xương",
    cover: "assets/extracted/cover_dongxam.jpeg",
    description: "Cái nôi của nghề chạm bạc truyền thống Việt Nam. Với kỹ thuật 'thúc, ve, trổ, chạm' điêu luyện, nghệ nhân Đồng Xâm thổi hồn vào các tấm kim loại bạc, đồng thành những tác phẩm hoa văn rồng phượng sống động.",
    tags: ["Chạm Bạc", "Nghệ Nhân Kim Hoàn", "Hoa Văn Rồng Phượng", "Thủ Công Mỹ Nghệ"],
    hotspotsCount: 15,
    photosCount: 15
  }
};

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
  renderHeritageProjectsGrid();
  initHeritageModals();
  init3DViewer();
  initForm321();
  loadSavedData();
  checkAi5aHandoff();
  setupSmoothScroll();
});

function renderHeritageProjectsGrid() {
  const grid = document.getElementById('projectsGridContainer');
  if (!grid) return;

  const cards = [
    { key: "phohien", no: "01", name: "PHỐ HIẾN", year: "THẾ KỶ XVII", tags: ["THƯƠNG CẢNG CỔ", "ĐỀN MẪU", "HỒ BÁN NGUYỆT"], desc: "Quần thể di tích thương cảng cổ kính sầm uất với đền Mẫu và chùa Chuông.", photo: "assets/extracted/cover_phohien.jpeg" },
    { key: "chuakeo", no: "02", name: "CHÙA KEO", year: "KIẾN TRÚC GỖ", tags: ["GÁC CHUÔNG 3 TẦNG", "12 MÁI CONG", "GỖ LIM"], desc: "Gác chuông ba tầng 12 mái cong kiệt tác đấu củng gỗ không dùng đinh sắt.", photo: "assets/extracted/cover_chuakeo.jpeg" },
    { key: "dentran", no: "03", name: "ĐỀN TRẦN HƯNG HÀ", year: "HÀO KHÍ ĐÔNG A", tags: ["LĂNG MỘ VUA TRẦN", "RỒNG ĐÁ", "TRỤC THẦN ĐẠO"], desc: "Vùng đất phát tích vương triều Trần với không gian tưởng niệm và lễ hội trang nghiêm.", photo: "assets/extracted/cover_dentran.jpeg" },
    { key: "lequydon", no: "04", name: "KHU LƯU NIỆM LÊ QUÝ ĐÔN", year: "DANH NHÂN VĂN HÓA", tags: ["NHÀ BÁC HỌC", "TƯỢNG ĐỒNG", "THƯ TỊCH CỔ"], desc: "Không gian tưởng niệm Nhà bác học Lê Quý Đôn kết nối học liệu mĩ thuật số.", photo: "assets/extracted/cover_lequydon.jpeg" },
    { key: "dongxam", no: "05", name: "LÀNG NGHỀ CHẠM BẠC ĐỒNG XÂM", year: "LÀNG NGHỀ 500 NĂM", tags: ["CHẠM BẠC KIM HOÀN", "HOA VĂN TINH XẢO", "NGHỆ NHÂN"], desc: "Nghệ thuật chạm khắc kim hoàn thủ công truyền thống tinh hoa đất Bắc.", photo: "assets/extracted/cover_dongxam.jpeg" },
    { key: "studio", no: "06", name: "XƯỞNG SÁNG TẠO & AR GALLERY", year: "TRIỂN LÃM MĨ THUẬT", tags: ["CANVAS DRAWING", "AI 5A ASSISTANT", "VIRTUAL AR"], desc: "Không gian phác thảo, hoàn thiện tác phẩm mĩ thuật và triển lãm AR trên di động.", photo: "assets/extracted/002_Cong_di_tich_kien_truc_co.jpeg" }
  ];

  grid.innerHTML = cards.map(c => `
    <div class="project-card" onclick="handleProjectCardClick('${c.key}')">
      <div class="project-meta-row">
        <span class="project-code-title">${c.no} — ${c.name}</span>
        <span class="project-year">${c.year}</span>
      </div>
      <div class="project-photo-wrapper">
        <img class="project-photo" src="${c.photo}" alt="${c.name}" loading="lazy" />
        <div class="project-hover-curtain"></div>
        <div class="project-floating-tags">
          ${c.tags.map(t => `<span class="tag-mini">${t}</span>`).join('')}
        </div>
      </div>
      <div class="project-card-footer">
        <span class="project-subtitle-text">${c.desc}</span>
        <button class="project-explore-btn" type="button">
          Khám phá chi tiết <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M7 17L17 7M17 7H7M17 7V17"/></svg>
        </button>
      </div>
    </div>
  `).join('');
}

function handleProjectCardClick(key) {
  if (key === 'studio') {
    // Creative studio now lives on its own page (student work portfolio)
    location.href = 'trien-lam.html';
  } else {
    // Heritage explorer now lives on its own immersive page
    location.href = 'di-san.html#' + key;
  }
}

/* ==========================================================================
   MODAL CONTROLLER
   ========================================================================== */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.add('is-active');
  document.body.style.overflow = 'hidden';

  // If opening 3D viewer, trigger resize
  if (modalId === 'viewer3dModal' && window.sah3dResize) {
    setTimeout(window.sah3dResize, 150);
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.remove('is-active');
  document.body.style.overflow = '';
}

// Close on backdrop click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('is-active');
    document.body.style.overflow = '';
  }
});

// Close on ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.is-active').forEach(m => {
      m.classList.remove('is-active');
    });
    document.body.style.overflow = '';
  }
});

/* ==========================================================================
   HERITAGE EXPLORER & 15-HOTSPOT DRAWER
   ========================================================================== */
let allHeritageDataCache = null;

async function loadHeritageDatabase() {
  if (allHeritageDataCache) return allHeritageDataCache;
  try {
    const res = await fetch('assets/heritage_complete.json');
    if (res.ok) {
      allHeritageDataCache = await res.json();
      return allHeritageDataCache;
    }
  } catch (err) {
    console.warn('Could not load heritage_complete.json, using fallback');
  }
  return null;
}

async function openHeritageDrawer(key) {
  SAH_STATE.currentHeritage = key;
  const modal = document.getElementById('heritageExplorerModal');
  if (!modal) return;

  const data = await loadHeritageDatabase();
  const info = BUILTIN_HERITAGES[key] || BUILTIN_HERITAGES.chuakeo;

  document.getElementById('explorerModalTitle').textContent = `${info.name} — ${info.tagline}`;
  document.getElementById('explorerModalDesc').textContent = info.description;

  // Active tab pills
  document.querySelectorAll('.heritage-tab-pill').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.heritage === key);
  });

  // Render 15 Hotspots
  renderHotspotsGrid(key, data);
  openModal('heritageExplorerModal');
}

function renderHotspotsGrid(key, fullData) {
  const container = document.getElementById('hotspotsMasonryGrid');
  if (!container) return;

  const siteData = fullData ? fullData[key] : null;
  const hotspots = siteData && siteData.hotspots ? siteData.hotspots : [];

  if (hotspots.length === 0) {
    // Generate fallback cards if json not loaded
    container.innerHTML = Array.from({ length: 15 }).map((_, i) => `
      <div class="hotspot-detail-card">
        <img class="hotspot-card-photo" src="assets/extracted/${String(i+1).padStart(3, '0')}_Pho_Hien_tong_quan.jpeg" onerror="this.src='assets/extracted/cover_chuakeo.jpeg'" alt="Hotspot ${i+1}" />
        <div class="hotspot-card-body">
          <div class="hotspot-card-meta">
            <span class="hotspot-card-no">HOTSPOT #${i+1}</span>
            <span class="badge-pill-outline">QUAN SÁT</span>
          </div>
          <h4 class="hotspot-card-h4">Điểm chạm quan sát nghệ thuật ${i+1}</h4>
          <div class="hotspot-accordion">
            <details open>
              <summary>① Nhìn ảnh – trả lời</summary>
              <div class="hotspot-drawer-content">Hãy quan sát đường nét mái cong, tỉ lệ hình khối và sự đối xứng của công trình.</div>
            </details>
            <details>
              <summary>② Em có biết?</summary>
              <div class="hotspot-drawer-content">Công trình thể hiện triết lý âm dương trong kiến trúc truyền thống vùng châu thổ sông Hồng.</div>
            </details>
            <details>
              <summary>③ Gợi ý mĩ thuật</summary>
              <div class="hotspot-drawer-content">Em có thể chọn chi tiết con sơn hoặc hoa văn đầu đao làm điểm nhấn cho bức tranh mĩ thuật cá nhân.</div>
            </details>
          </div>
        </div>
      </div>
    `).join('');
    return;
  }

  container.innerHTML = hotspots.map((h, idx) => `
    <div class="hotspot-detail-card">
      <img class="hotspot-card-photo" src="${h.image}" alt="${h.title}" loading="lazy" onerror="this.src='assets/extracted/cover_chuakeo.jpeg'" />
      <div class="hotspot-card-body">
        <div class="hotspot-card-meta">
          <span class="hotspot-card-no">${h.code || `HOTSPOT #${idx+1}`}</span>
          <span class="badge-pill-outline">MĨ THUẬT</span>
        </div>
        <h4 class="hotspot-card-h4">${h.title}</h4>
        <div class="hotspot-accordion">
          <details open>
            <summary>${h.q1 && h.q1.title ? h.q1.title : '① Nhìn ảnh – trả lời'}</summary>
            <div class="hotspot-drawer-content">${h.q1 && h.q1.content ? h.q1.content : 'Quan sát cấu trúc và sự phân bổ ánh sáng của chi tiết.'}</div>
          </details>
          <details>
            <summary>${h.q2 && h.q2.title ? h.q2.title : '② Em có biết?'}</summary>
            <div class="hotspot-drawer-content">${h.q2 && h.q2.content ? h.q2.content : 'Chi tiết mang giá trị lịch sử và bản sắc nghệ thuật độc đáo.'}</div>
          </details>
          <details>
            <summary>${h.q3 && h.q3.title ? h.q3.title : '③ Gợi ý mĩ thuật'}</summary>
            <div class="hotspot-drawer-content">${h.q3 && h.q3.content ? h.q3.content : 'Áp dụng độ tương phản sáng tối để làm nổi bật khối gỗ.'}</div>
          </details>
        </div>
        <button class="btn-outline-pill" style="margin-top:auto; font-size:0.75rem; justify-content:center;" onclick="useHotspotFor321('${key}', '${h.title.replace(/'/g, "\\'")}')">
          Đưa vào Phiếu 3–2–1 ↗
        </button>
      </div>
    </div>
  `).join('');
}

function initHeritageModals() {
  // Heritage explorer tabs moved to di-san.html; nothing to wire here.
}

function useHotspotFor321(key, title) {
  closeModal('heritageExplorerModal');
  openModal('modal321');
  const sel = document.getElementById('form321Project');
  if (sel) sel.value = key;
  const q3 = document.getElementById('field321_3');
  if (q3 && !q3.value.includes(title)) {
    q3.value = (q3.value ? q3.value + "\n- " : "- ") + `Ấn tượng với chi tiết: ${title}`;
  }
}

/* ==========================================================================
   THREE.JS 3D PAGODA ARCHITECTURAL VIEWER — RETIRED
   Superseded by the immersive artifact page (models.html +
   js/artifact-page.js). This legacy init is inert:
   its #threeCanvasContainer no longer exists in the DOM.
   ========================================================================== */
function init3DViewer() {
  const container = document.getElementById('threeCanvasContainer');
  if (!container || typeof THREE === 'undefined') return;

  // Scene, Camera, Renderer
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x191918);
  scene.fog = new THREE.FogExp2(0x191918, 0.035);

  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(12, 10, 16);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xfff5e6, 0.9);
  scene.add(ambientLight);

  const sunLight = new THREE.DirectionalLight(0xffe2b3, 1.8);
  sunLight.position.set(15, 25, 12);
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.width = 1024;
  sunLight.shadow.mapSize.height = 1024;
  scene.add(sunLight);

  const fillLight = new THREE.DirectionalLight(0x738b9c, 0.6);
  fillLight.position.set(-15, 10, -10);
  scene.add(fillLight);

  // Floor Grid Plinth
  const groundGeo = new THREE.CylinderGeometry(8, 8.5, 0.6, 32);
  const groundMat = new THREE.MeshStandardMaterial({ color: 0x2d2b27, roughness: 0.9, metalness: 0.1 });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.position.y = -0.3;
  ground.receiveShadow = true;
  scene.add(ground);

  // Materials for Modes
  const woodMaterial = new THREE.MeshStandardMaterial({ color: 0x5a341e, roughness: 0.7, metalness: 0.1 });
  const tileMaterial = new THREE.MeshStandardMaterial({ color: 0x933d26, roughness: 0.8, metalness: 0.05 });
  const bellMaterial = new THREE.MeshStandardMaterial({ color: 0xb58c3a, roughness: 0.35, metalness: 0.8 });
  const wireMaterial = new THREE.MeshBasicMaterial({ color: 0x55ffaa, wireframe: true });
  const clayMaterial = new THREE.MeshStandardMaterial({ color: 0xded8ce, roughness: 0.9, metalness: 0 });

  const pagodaGroup = new THREE.Group();
  scene.add(pagodaGroup);

  // Procedural 3-Tier Chùa Keo Pagoda
  function buildPagoda(matWood, matRoof, matBell) {
    while(pagodaGroup.children.length > 0){ 
      pagodaGroup.remove(pagodaGroup.children[0]); 
    }

    // --- TẦNG 1 (Ground Tier) ---
    // Stone Plinth Base
    const baseGeo = new THREE.BoxGeometry(7, 0.5, 7);
    const base = new THREE.Mesh(baseGeo, matWood);
    base.position.y = 0.25;
    base.castShadow = true;
    pagodaGroup.add(base);

    // 16 Columns (Cột lim)
    const colGeo = new THREE.CylinderGeometry(0.16, 0.18, 3.2, 16);
    const colCoords = [-2.8, -1, 1, 2.8];
    colCoords.forEach(x => {
      colCoords.forEach(z => {
        const col = new THREE.Mesh(colGeo, matWood);
        col.position.set(x, 1.85, z);
        col.castShadow = true;
        pagodaGroup.add(col);
      });
    });

    // Tier 1 Roof (4 curved eaves)
    const roof1Geo = new THREE.ConeGeometry(5.8, 1.4, 4);
    const roof1 = new THREE.Mesh(roof1Geo, matRoof);
    roof1.position.y = 3.8;
    roof1.rotation.y = Math.PI / 4;
    roof1.castShadow = true;
    pagodaGroup.add(roof1);

    // --- TẦNG 2 (Middle Tier - Bracket sets & balcony) ---
    const tier2Base = new THREE.BoxGeometry(4.4, 0.3, 4.4);
    const t2b = new THREE.Mesh(tier2Base, matWood);
    t2b.position.y = 4.2;
    t2b.castShadow = true;
    pagodaGroup.add(t2b);

    // 8 Tier 2 Columns
    const col2Geo = new THREE.CylinderGeometry(0.14, 0.15, 2.4, 16);
    [-1.6, 1.6].forEach(x => {
      [-1.6, 1.6].forEach(z => {
        const col = new THREE.Mesh(col2Geo, matWood);
        col.position.set(x, 5.4, z);
        pagodaGroup.add(col);
      });
    });

    // Tier 2 Roof
    const roof2Geo = new THREE.ConeGeometry(4.2, 1.2, 4);
    const roof2 = new THREE.Mesh(roof2Geo, matRoof);
    roof2.position.y = 6.8;
    roof2.rotation.y = Math.PI / 4;
    roof2.castShadow = true;
    pagodaGroup.add(roof2);

    // --- TẦNG 3 (Top Tier - Bronze Bell & High Flared Roof) ---
    const tier3Base = new THREE.BoxGeometry(2.6, 0.25, 2.6);
    const t3b = new THREE.Mesh(tier3Base, matWood);
    t3b.position.y = 7.1;
    pagodaGroup.add(t3b);

    // Bronze Bell (Quả chuông đồng)
    const bellGeo = new THREE.CylinderGeometry(0.35, 0.55, 1.1, 16);
    const bell = new THREE.Mesh(bellGeo, matBell);
    bell.position.y = 7.8;
    bell.castShadow = true;
    pagodaGroup.add(bell);

    // Top Roof
    const roof3Geo = new THREE.ConeGeometry(3.0, 1.4, 4);
    const roof3 = new THREE.Mesh(roof3Geo, matRoof);
    roof3.position.y = 9.2;
    roof3.rotation.y = Math.PI / 4;
    roof3.castShadow = true;
    pagodaGroup.add(roof3);

    // Finial (Kìm nóc hồ lô)
    const finialGeo = new THREE.SphereGeometry(0.25, 16, 16);
    const finial = new THREE.Mesh(finialGeo, matBell);
    finial.position.y = 10.1;
    pagodaGroup.add(finial);
  }

  buildPagoda(woodMaterial, tileMaterial, bellMaterial);

  // Mouse Orbiting Logic (Zero dependency fallback for OrbitControls)
  let isDragging = false;
  let prevMouseX = 0;
  let prevMouseY = 0;
  let spherical = { radius: 20, theta: 0.8, phi: 1.1 };

  function updateCamera() {
    spherical.phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, spherical.phi));
    camera.position.x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
    camera.position.y = spherical.radius * Math.cos(spherical.phi) + 3;
    camera.position.z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
    camera.lookAt(0, 4.5, 0);
  }
  updateCamera();

  container.addEventListener('mousedown', (e) => {
    isDragging = true;
    prevMouseX = e.clientX;
    prevMouseY = e.clientY;
  });

  window.addEventListener('mouseup', () => { isDragging = false; });

  container.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const deltaX = e.clientX - prevMouseX;
    const deltaY = e.clientY - prevMouseY;
    prevMouseX = e.clientX;
    prevMouseY = e.clientY;

    spherical.theta -= deltaX * 0.008;
    spherical.phi -= deltaY * 0.008;
    updateCamera();
  });

  // Touch Support
  container.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      isDragging = true;
      prevMouseX = e.touches[0].clientX;
      prevMouseY = e.touches[0].clientY;
    }
  }, { passive: true });

  container.addEventListener('touchmove', (e) => {
    if (!isDragging || e.touches.length !== 1) return;
    const deltaX = e.touches[0].clientX - prevMouseX;
    const deltaY = e.touches[0].clientY - prevMouseY;
    prevMouseX = e.touches[0].clientX;
    prevMouseY = e.touches[0].clientY;

    spherical.theta -= deltaX * 0.01;
    spherical.phi -= deltaY * 0.01;
    updateCamera();
  }, { passive: true });

  // Zoom
  container.addEventListener('wheel', (e) => {
    e.preventDefault();
    spherical.radius = Math.max(8, Math.min(32, spherical.radius + e.deltaY * 0.02));
    updateCamera();
  }, { passive: false });

  // Auto slow rotation
  let autoRotate = true;
  container.addEventListener('mouseenter', () => { autoRotate = false; });
  container.addEventListener('mouseleave', () => { autoRotate = true; });

  // Render loop
  function animate() {
    requestAnimationFrame(animate);
    if (autoRotate && !isDragging) {
      spherical.theta += 0.0025;
      updateCamera();
    }
    renderer.render(scene, camera);
  }
  animate();

  // Resize handler
  window.sah3dResize = function() {
    if (!container) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  };
  window.addEventListener('resize', window.sah3dResize);

  // Toolbar Actions (Texture, Wireframe, Clay)
  document.getElementById('toolTextured')?.addEventListener('click', (e) => {
    setToolbarActive(e.target);
    buildPagoda(woodMaterial, tileMaterial, bellMaterial);
  });

  document.getElementById('toolWireframe')?.addEventListener('click', (e) => {
    setToolbarActive(e.target);
    buildPagoda(wireMaterial, wireMaterial, wireMaterial);
  });

  document.getElementById('toolClay')?.addEventListener('click', (e) => {
    setToolbarActive(e.target);
    buildPagoda(clayMaterial, clayMaterial, clayMaterial);
  });

  function setToolbarActive(btn) {
    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
    btn?.classList.add('active');
  }

  // Hotspot Buttons to Focus Camera
  window.focusHotspot3D = function(index) {
    document.querySelectorAll('.hotspot-chip-btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`hotspotChip${index}`);
    if (btn) btn.classList.add('active');

    const indicator = document.getElementById('hotspotIndicatorText');

    if (index === 1) {
      spherical = { radius: 11, theta: 0.5, phi: 1.3 };
      if (indicator) indicator.textContent = "Đang xem: TẦNG 1 — Hệ thống 16 cột gỗ lim đỡ toàn bộ tải trọng công trình.";
    } else if (index === 2) {
      spherical = { radius: 10, theta: 1.2, phi: 1.0 };
      if (indicator) indicator.textContent = "Đang xem: TẦNG 2 — Khung vì kèo con sơn ngàm mộng chịu lực độc nhất vô nhị.";
    } else if (index === 3) {
      spherical = { radius: 9, theta: 2.1, phi: 0.7 };
      if (indicator) indicator.textContent = "Đang xem: TẦNG 3 — Quả chuông đồng đúc năm 1730 & 12 đầu đao mái cong.";
    }
    updateCamera();
  };
}

/* ==========================================================================
   3-2-1 REFLECTION WORKSHEET (AUTO-SAVE & EXPORT)
   ========================================================================== */
function initForm321() {
  const form = document.getElementById('worksheetForm321');
  if (!form) return;

  const f3 = document.getElementById('field321_3');
  const f2 = document.getElementById('field321_2');
  const f1 = document.getElementById('field321_1');
  const saveStatus = document.getElementById('save321Status');

  function autoSave() {
    const data = {
      project: document.getElementById('form321Project')?.value || 'chuakeo',
      studentId: document.getElementById('form321StudentId')?.value || SAH_STATE.studentId,
      studentClass: document.getElementById('form321Class')?.value || SAH_STATE.studentClass,
      q3: f3?.value || '',
      q2: f2?.value || '',
      q1: f1?.value || '',
      updatedAt: new Date().toISOString()
    };
    localStorage.setItem('sah_321_draft', JSON.stringify(data));
    if (saveStatus) {
      saveStatus.textContent = "✓ Đã tự động lưu nháp";
      setTimeout(() => { saveStatus.textContent = ""; }, 2500);
    }
  }

  [f3, f2, f1].forEach(input => {
    input?.addEventListener('input', debounce(autoSave, 500));
  });

  // Export / Print button
  document.getElementById('btnExport321')?.addEventListener('click', () => {
    window.print();
  });
}

function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/* ==========================================================================
   RESTORE SAVED LOCALSTORAGE DATA
   ========================================================================== */
function loadSavedData() {
  try {
    const draft321 = JSON.parse(localStorage.getItem('sah_321_draft') || '{}');
    if (draft321.q3) document.getElementById('field321_3').value = draft321.q3;
    if (draft321.q2) document.getElementById('field321_2').value = draft321.q2;
    if (draft321.q1) document.getElementById('field321_1').value = draft321.q1;
    if (draft321.project) document.getElementById('form321Project').value = draft321.project;
  } catch(e) {}
}

/* ==========================================================================
   AI 5A HANDOFF — receive worksheet context from phieu-3-2-1.html
   ========================================================================== */
function checkAi5aHandoff() {
  let payload = null;
  try {
    payload = JSON.parse(sessionStorage.getItem('sah_321_to_ai5a') || 'null');
  } catch (e) {}
  if (!payload) return;

  sessionStorage.removeItem('sah_321_to_ai5a');

  // Stale handoffs (> 1h) are ignored
  if (!payload.ts || Date.now() - payload.ts > 3600000) return;

  // The AI 5A studio now lives on its own page; forward the handoff there.
  if (location.hash.startsWith('#ai5a')) {
    history.replaceState(null, '', location.pathname);
    location.href = 'tro-ly-ai.html';
  }
}

/* ==========================================================================
   SMOOTH SCROLLING
   ========================================================================== */
function setupSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}
