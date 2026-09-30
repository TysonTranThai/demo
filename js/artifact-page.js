/* ==========================================================================
   ARTIFACT JOURNEY — full-page immersive 3D viewer for the five
   Blender heritage models. Serves models.html.
   ========================================================================== */
(function () {
  'use strict';

  var MODELS = [
    {
      id: 'chuakeo', name: 'Chùa Keo', loc: 'Gác chuông · Thái Bình',
      poem: 'Tháp chuông ba tầng vươn giữa đồng lúa, mái cong nhuộm màu bốn thế kỷ.',
      file: '3d/Chua%20Keo/exports/nlt-agent-model.glb',
      cam: [17, 9.5, 19], target: [0, 5.0, 0],
      color: '#7c4c28',
      chips: ['Kiến trúc gỗ 1632', '26 khách tham quan', 'Mái ngói 12 đao cong'],
      stats: '26 visitors · 41.8k tris · GLB 3.4 MB'
    },
    {
      id: 'denmau', name: 'Đền Mẫu', loc: 'Phố Hiến · Hưng Yên',
      poem: 'Nghi môn mở lối vào hồ bán nguyệt, cờ đỏ rướn mình giữa trời năm tháng.',
      file: '3d/den-mau/exports/den-mau-model.glb',
      cam: [27, 15, 31], target: [0, 3.4, 0],
      zoom: [[0.8, 1.55], [1.2, 1.25]],
      color: '#c46238',
      chips: ['Hồ Bán Nguyệt', '18 hoạt cảnh', '25 khách tham quan'],
      stats: '18 animations · 25 visitors · 37.3k tris · GLB 4.1 MB'
    },
    {
      id: 'dentran', name: 'Đền Trần', loc: 'Lộc Vượng · Nam Định',
      poem: 'Quần thể đá đỏ trầm mặc, nền gạch ô vuông in dấu hội mùa xuân.',
      file: '3d/den-tran/exports/den-tran-model.glb',
      cam: [40, 22, 46], target: [0, 3.0, -4],
      zoom: [[0.8, 1.55], [1.2, 1.25]],
      color: '#435c4b',
      chips: ['Khu đền đá cổ', '8 hoạt cảnh', '28 khách tham quan'],
      stats: '8 animations · 28 visitors · 42.9k tris · GLB 5.0 MB'
    },
    {
      id: 'lequydon', name: 'Lê Quý Đôn', loc: 'Khu lưu niệm · Thái Bình',
      poem: 'Nhà gỗ lam tim soi bóng sân gạch, mái ngói trầm như nét mực cũ.',
      file: '3d/le-quy-don/exports/le-quy-don-model.glb',
      cam: [24, 20, 17], target: [0, 2.5, 3],
      zoom: [[0.8, 1.55], [1.2, 1.25]],
      color: '#a39e93',
      chips: ['Nhà gỗ truyền thống', '4 hoạt cảnh', '24 khách tham quan'],
      stats: '4 animations · 24 visitors · 22.2k tris · GLB 3.3 MB'
    },
    {
      id: 'dongxam', name: 'Đồng Xâm', loc: 'Đền Thờ Tổ Nghề · Thái Bình',
      poem: 'Đền vàng bên dòng sông, nơi nghề kim hoàn thắp lửa từ năm 1428.',
      file: '3d/dong-xam/exports/dong-xam-model.glb',
      cam: [-26, 22, 46], target: [2, 2, 4],
      zoom: [[0.8, 1.5], [1.2, 1.2]],
      color: '#c89547',
      chips: ['Khởi tổ 1428', '7 hoạt cảnh', '30 khách tham quan'],
      stats: '7 animations · 30 visitors · 42.1k tris · GLB 5.1 MB'
    }
  ];

  function $(id) { return document.getElementById(id); }

  var stage = $('jrStage'), host = $('jrCanvasHost'), veil = $('jrVeil');
  var info = $('jrInfo'), dockStops = $('jrDockStops'), statline = $('jrStatline');
  var loaderEl = $('jrLoader'), loaderLabel = $('jrLoaderLabel');
  var veilTitle = $('jrVeilTitle'), veilSub = $('jrVeilSub');
  var barTop = $('jrBarTop'), barBottom = $('jrBarBottom');
  var zenBtn = $('jrZenBtn'), zenExit = $('jrZenExit');

  var renderer, scene, camera, controls, mixer, clock;
  var currentRoot = null, currentId = null, loadingId = null;
  var entered = false, ready = false, zen = false, prefetching = false;
  var loadedIds = {};
  var camStart = new THREE.Vector3(), camEnd = new THREE.Vector3();
  var targetStart = new THREE.Vector3(), targetEnd = new THREE.Vector3();
  var dolly = { active: false, t: 0, dur: 2.6 };

  function getModel(id) {
    for (var i = 0; i < MODELS.length; i++) if (MODELS[i].id === id) return MODELS[i];
    return null;
  }
  function getIndex(id) {
    for (var i = 0; i < MODELS.length; i++) if (MODELS[i].id === id) return i;
    return -1;
  }

  /* ---------- boot ---------- */

  function init() {
    if (typeof THREE === 'undefined') {
      loaderLabel.textContent = 'Không tải được thư viện 3D (THREE).';
      return;
    }
    buildDock();
    bindChrome();
    setupRenderer();

    var hash = (location.hash || '').replace('#', '');
    var startId = getModel(hash) ? hash : MODELS[0].id;
    showVeil(startId);
    select(startId);
  }

  function setupRenderer() {
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch (err) {
      loaderLabel.textContent = 'Trình duyệt không hỗ trợ WebGL.';
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.12;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    host.appendChild(renderer.domElement);

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xaecbe6);

    camera = new THREE.PerspectiveCamera(42, 1, 0.1, 400);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.autoRotateSpeed = 0.55;
    controls.minDistance = 6;
    controls.maxDistance = 120;

    scene.add(new THREE.HemisphereLight(0xbfd8f0, 0x8a7a5c, 0.75));
    var sun = new THREE.DirectionalLight(0xfff0dc, 1.5);
    sun.position.set(-18, 22, -14);
    scene.add(sun);
    var fill = new THREE.DirectionalLight(0xcfe0ff, 0.35);
    fill.position.set(14, 10, 16);
    scene.add(fill);

    clock = new THREE.Clock();
    window.addEventListener('resize', syncSize);
    renderer.domElement.addEventListener('dblclick', resetView);
    veil.addEventListener('click', enterStage);

    ready = true;
    syncSize();
    animate();
  }

  function buildDock() {
    dockStops.innerHTML = '';
    MODELS.forEach(function (m, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'jr-stop';
      b.dataset.model = m.id;
      b.title = m.name;
      b.innerHTML =
        '<span class="jr-stop-dot" style="background:' + m.color + '"></span>' +
        '<span class="jr-stop-num">0' + (i + 1) + '</span>' +
        '<span class="jr-stop-name">' + m.name + '</span>';
      b.addEventListener('click', function () { go(m.id); });
      dockStops.appendChild(b);
    });
  }

  function bindChrome() {
    $('jrPrev').addEventListener('click', function () { step(-1); });
    $('jrNext').addEventListener('click', function () { step(1); });
    zenBtn.addEventListener('click', toggleZen);
    zenExit.addEventListener('click', toggleZen);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') step(1);
      else if (e.key === 'ArrowLeft') step(-1);
      else if (e.key === 'z' || e.key === 'Z') toggleZen();
      else if (e.key === 'Escape' && zen) toggleZen();
    });
    window.addEventListener('hashchange', function () {
      var id = (location.hash || '').replace('#', '');
      if (getModel(id) && id !== currentId) go(id);
    });
  }

  /* ---------- veil + enter ---------- */

  function showVeil(id) {
    var m = getModel(id);
    var i = getIndex(id);
    veilTitle.textContent = m.name;
    veilSub.textContent = m.loc;
    veil.style.setProperty('--accent', m.color);
    $('jrInfoEyebrow').textContent = 'DI SẢN 0' + (i + 1) + ' / 05';
  }

  function enterStage() {
    if (entered) return;
    entered = true;
    document.body.classList.add('jr-entered');
    veil.classList.add('jr-veil-out');
    setTimeout(function () { veil.classList.add('hidden'); }, 1400);

    // Cinematic dolly-in as the visitor steps through the veil
    if (currentId) {
      var m0 = getModel(currentId);
      if (m0) applyFraming(m0, false);
    }
  }

  /* ---------- model switching ---------- */

  function select(id) {
    if (!ready) return;
    if (id === currentId && !loadingId) return;
    if (loadingId && loadingId !== id) { /* queue latest intent */ }
    if (loadingId === id) return;

    loadingId = id;
    var m = getModel(id);

    loaderEl.classList.remove('hidden');
    loaderLabel.textContent = 'Đang tải ' + m.name + '…';
    statline.textContent = '';

    new THREE.GLTFLoader().load(m.file, function (gltf) {
      if (loadingId !== id) return;
      loadingId = null;
      loadedIds[id] = true;

      clearModel();
      currentRoot = gltf.scene;
      scene.add(currentRoot);
      currentId = id;

      applyFraming(m, !entered);

      controls.autoRotate = true; // slow contemplative drift

      mixer = null;
      if (gltf.animations && gltf.animations.length) {
        mixer = new THREE.AnimationMixer(currentRoot);
        gltf.animations.forEach(function (clip) {
          var act = mixer.clipAction(clip);
          act.play();
        });
      }

      updateChrome(m, gltf.animations ? gltf.animations.length : 0);
      loaderEl.classList.add('hidden');
      syncSize();
      prefetchRest();
    }, undefined, function () {
      if (loadingId !== id) return;
      loadingId = null;
      loaderEl.classList.add('hidden');
      loaderLabel.textContent = 'Không tải được mô hình — thử lại sau.';
      console.error('[artifact] failed to load', m.file);
    });
  }

  function go(id) {
    if (id === currentId) { enterStage(); return; }
    history.replaceState(null, '', '#' + id);
    showVeil(id);
    enterStage();
    select(id);
  }

  function step(delta) {
    var i = getIndex(currentId);
    if (i < 0) i = 0;
    var n = (i + delta + MODELS.length) % MODELS.length;
    go(MODELS[n].id);
  }

  function updateChrome(m, animCount) {
    $('jrInfoEyebrow').textContent = 'DI SẢN 0' + (getIndex(m.id) + 1) + ' / 05';
    $('jrInfoTitle').textContent = m.name;
    $('jrInfoPoem').textContent = m.poem;

    var chips = $('jrInfoChips');
    chips.innerHTML = '';
    m.chips.forEach(function (c) {
      var s = document.createElement('span');
      s.className = 'jr-chip';
      s.textContent = c;
      chips.appendChild(s);
    });

    Array.prototype.forEach.call(dockStops.children, function (b, i) {
      b.classList.toggle('is-active', b.dataset.model === m.id);
      b.classList.toggle('is-visited', !!loadedIds[b.dataset.model] && b.dataset.model !== m.id);
    });

    document.title = m.name + ' — Bộ Sưu Tập 3D Di Sản';
    statline.textContent = m.stats;
  }

  function clearModel() {
    if (mixer) { mixer.stopAllAction(); mixer = null; }
    if (currentRoot) {
      scene.remove(currentRoot);
      disposeDeep(currentRoot);
      currentRoot = null;
    }
    currentId = null;
  }

  function disposeDeep(root) {
    root.traverse(function (node) {
      if (node.geometry) node.geometry.dispose();
      if (node.material) {
        var mats = Array.isArray(node.material) ? node.material : [node.material];
        mats.forEach(function (mat) {
          for (var key in mat) {
            var v = mat[key];
            if (v && v.isTexture) v.dispose();
          }
          mat.dispose();
        });
      }
    });
  }

  /* ---------- camera ---------- */

  function applyFraming(m, instant) {
    var dist = 1;
    var aspect = stage.clientWidth / Math.max(1, stage.clientHeight);
    if (m.zoom) {
      if (aspect < m.zoom[0][0]) dist = m.zoom[0][1];
      else if (aspect < m.zoom[1][0]) dist = m.zoom[1][1];
    }

    camEnd.set(m.cam[0] * dist, m.cam[1] * dist, m.cam[2] * dist);
    targetEnd.set(m.target[0], m.target[1], m.target[2]);

    if (instant || !entered) {
      camera.position.copy(camEnd);
      controls.target.copy(targetEnd);
      controls.update();
      return;
    }

    // Cinematic dolly: pull back+up, then glide to the framed position
    var dir = camEnd.clone().normalize();
    camStart.copy(camEnd).addScaledVector(dir, 14).add(new THREE.Vector3(0, 7, 0));
    targetStart.copy(targetEnd).add(new THREE.Vector3(0, 2.5, 0));
    dolly.active = true;
    dolly.t = 0;
  }

  function resetView() {
    var m = getModel(currentId);
    if (m) applyFraming(m, true);
  }

  /* ---------- zen mode ---------- */

  function toggleZen() {
    zen = !zen;
    document.body.classList.toggle('jr-zen', zen);
    zenExit.classList.toggle('hidden', !zen);
  }

  /* ---------- prefetch ---------- */

  function prefetchRest() {
    if (prefetching) return;
    prefetching = true;
    var files = MODELS
      .filter(function (m) { return !loadedIds[m.id]; })
      .map(function (m) { return m.file; });
    files.forEach(function (f) {
      fetch(f, { mode: 'same-origin' }).catch(function () {});
    });
  }

  /* ---------- size + loop ---------- */

  function syncSize() {
    if (!ready || !stage) return;
    var w = stage.clientWidth, h = stage.clientHeight;
    if (!w || !h) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
  }

  function animate() {
    requestAnimationFrame(animate);

    var dt = Math.min(clock.getDelta(), 0.05);

    if (dolly.active) {
      dolly.t += dt;
      var raw = Math.min(1, dolly.t / dolly.dur);
      var e = 1 - Math.pow(1 - raw, 3); // easeOutCubic
      camera.position.lerpVectors(camStart, camEnd, e);
      controls.target.lerpVectors(targetStart, targetEnd, e);
      if (raw >= 1) dolly.active = false;
      controls.update();
    } else {
      controls.update();
    }

    if (mixer) mixer.update(dt);
    renderer.render(scene, camera);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
