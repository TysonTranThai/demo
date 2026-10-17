/* ==========================================================================
   teacher-theme.js — Hệ thống Quản trị Font chữ & Giao diện Triển lãm
   Smart Art Heritage • Dedicated Teacher Typography & Customization Engine
   ========================================================================== */
(function() {
  'use strict';

  var STORAGE_KEY = 'sah_custom_theme_v1';

  var FONT_PRESETS = {
    'preset-heritage': {
      id: 'preset-heritage',
      name: '🏛️ Bảo tàng Hoàng gia (Mặc định)',
      desc: 'Sang trọng, uy nghi, tôn vinh kiến trúc & hoa văn cổ truyền.',
      displayFont: "'Cinzel', serif",
      serifFont: "'Playfair Display', Georgia, serif",
      sansFont: "'Plus Jakarta Sans', system-ui, sans-serif"
    },
    'preset-classical': {
      id: 'preset-classical',
      name: '📜 Chữ Khắc Cổ Điển / Văn Miếu',
      desc: 'Nét chữ khắc bia tiến sĩ thanh thoát, cổ kính, trang nhã.',
      displayFont: "'Cormorant Garamond', serif",
      serifFont: "'Playfair Display', Georgia, serif",
      sansFont: "'Plus Jakarta Sans', system-ui, sans-serif"
    },
    'preset-modern': {
      id: 'preset-modern',
      name: '🎨 Mĩ Thuật Đương Đại (Modern Art)',
      desc: 'Hình khối kỷ hà dứt khoát, phong cách đồ họa đương đại tối giản.',
      displayFont: "'Montserrat', sans-serif",
      serifFont: "'Playfair Display', serif",
      sansFont: "'Inter', system-ui, sans-serif"
    },
    'preset-vietnam': {
      id: 'preset-vietnam',
      name: '🏮 Đông Phương & Bản Sắc Việt',
      desc: 'Tối ưu dấu thanh tiếng Việt tròn đầy, mang hồn cốt Á Đông.',
      displayFont: "'Be Vietnam Pro', sans-serif",
      serifFont: "'Playfair Display', Georgia, serif",
      sansFont: "'Be Vietnam Pro', system-ui, sans-serif"
    },
    'preset-pedagogy': {
      id: 'preset-pedagogy',
      name: '📖 Thân Thiện Học Đường (Dễ Đọc)',
      desc: 'Cấu trúc chữ Lexend thông thoáng, chống mỏi mắt cho học sinh.',
      displayFont: "'Lexend', sans-serif",
      serifFont: "'Playfair Display', serif",
      sansFont: "'Lexend', 'Plus Jakarta Sans', sans-serif"
    }
  };

  var THEME_PALETTES = {
    'theme-gold': {
      id: 'theme-gold',
      name: '🌟 Hoàng Kim Bảo Tàng',
      desc: 'Nền mun huyền bí, thếp vàng kim hoàng gia & ngọc lục bảo.',
      bgObsidian: '#090807',
      bgSurface: '#12100e',
      bgCard: 'rgba(22, 19, 16, 0.92)',
      goldPrimary: '#d4af37',
      goldBright: '#f5d475',
      goldBorder: 'rgba(212, 175, 55, 0.28)',
      textHeading: '#fcfaf6',
      textBody: '#e2dacf',
      textMuted: '#a39988',
      accentColor: '#34d399',
      isLight: false
    },
    'theme-cinnabar': {
      id: 'theme-cinnabar',
      name: '🏯 Cung Đình Chu Sa',
      desc: 'Màu gỗ lim trầm ấm, sắc đỏ chu sa đình đền & đồng thau cổ.',
      bgObsidian: '#120807',
      bgSurface: '#1c0f0d',
      bgCard: 'rgba(28, 15, 13, 0.94)',
      goldPrimary: '#d97736',
      goldBright: '#f39c12',
      goldBorder: 'rgba(217, 119, 54, 0.32)',
      textHeading: '#fff5f2',
      textBody: '#ead5cf',
      textMuted: '#ab958f',
      accentColor: '#e74c3c',
      isLight: false
    },
    'theme-indigo': {
      id: 'theme-indigo',
      name: '🌕 Đêm Trăng Phố Hiến',
      desc: 'Xanh chàm tĩnh lặng, ánh bạc trăng soi bóng sông Châu & lam ngọc.',
      bgObsidian: '#060913',
      bgSurface: '#0c1222',
      bgCard: 'rgba(14, 20, 36, 0.94)',
      goldPrimary: '#38bdf8',
      goldBright: '#7dd3fc',
      goldBorder: 'rgba(56, 189, 248, 0.3)',
      textHeading: '#f0f9ff',
      textBody: '#d1e3f0',
      textMuted: '#8da6be',
      accentColor: '#818cf8',
      isLight: false
    },
    'theme-emerald': {
      id: 'theme-emerald',
      name: '🌿 Châu Thổ Sông Hồng',
      desc: 'Rêu phong cổ kính, đồng lúa phù sa châu thổ & ngọc bích.',
      bgObsidian: '#06120b',
      bgSurface: '#0c1f14',
      bgCard: 'rgba(14, 34, 23, 0.94)',
      goldPrimary: '#10b981',
      goldBright: '#34d399',
      goldBorder: 'rgba(16, 185, 129, 0.3)',
      textHeading: '#f0fdf4',
      textBody: '#d1fae5',
      textMuted: '#86a896',
      accentColor: '#eab308',
      isLight: false
    },
    'theme-daylight': {
      id: 'theme-daylight',
      name: '🏛️ Bảo Tàng Ban Ngày (Phòng Sáng)',
      desc: 'Nền ngà sáng thanh thoát, mực đen mun & vàng sâm panh cho lớp học nhiều ánh sáng.',
      bgObsidian: '#f7f4ed',
      bgSurface: '#ede8dc',
      bgCard: 'rgba(255, 255, 255, 0.96)',
      goldPrimary: '#996515',
      goldBright: '#b87c1e',
      goldBorder: 'rgba(153, 101, 21, 0.28)',
      textHeading: '#1a1612',
      textBody: '#2d261e',
      textMuted: '#6e6456',
      accentColor: '#059669',
      isLight: true
    }
  };

  var DEFAULT_CONFIG = {
    fontPreset: 'preset-heritage',
    displayFont: "'Cinzel', serif",
    serifFont: "'Playfair Display', Georgia, serif",
    sansFont: "'Plus Jakarta Sans', system-ui, sans-serif",
    fontScale: 1.0,          // 0.9, 1.0, 1.1, 1.2
    lineHeight: 1.6,         // 1.4, 1.6, 1.8
    themePalette: 'theme-gold',
    cardRadius: '20px',      // 8px, 18px, 26px
    glassBlur: '16px',       // 0px, 10px, 18px
    watermarkOpacity: 0.022, // 0, 0.022, 0.06
    projectorContrast: false,// true / false
    animationSpeed: 'normal' // normal, fast, none
  };

  function getConfig() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') {
          return Object.assign({}, DEFAULT_CONFIG, parsed);
        }
      }
    } catch(e) {
      console.warn('Read theme config error:', e);
    }
    return Object.assign({}, DEFAULT_CONFIG);
  }

  function saveConfig(cfg) {
    try {
      var merged = Object.assign({}, getConfig(), cfg);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      applyConfig(merged);
      
      // Also sync to content-studio published cache if available
      try {
        var rawDraft = localStorage.getItem('sah_content_draft_v1');
        if (rawDraft) {
          var draftObj = JSON.parse(rawDraft);
          if (draftObj) {
            draftObj.theme = merged;
            localStorage.setItem('sah_content_draft_v1', JSON.stringify(draftObj));
          }
        }
      } catch(e) {}
      
      return true;
    } catch(e) {
      console.error('Save theme config error:', e);
      return false;
    }
  }

  function resetConfig() {
    try {
      localStorage.removeItem(STORAGE_KEY);
      applyConfig(DEFAULT_CONFIG);
      return true;
    } catch(e) {
      return false;
    }
  }

  function applyConfig(cfg) {
    if (!cfg) cfg = getConfig();
    var root = document.documentElement;
    var body = document.body;
    if (!root || !body) return;

    // 1. Resolve Fonts
    var display = cfg.displayFont || DEFAULT_CONFIG.displayFont;
    var serif = cfg.serifFont || DEFAULT_CONFIG.serifFont;
    var sans = cfg.sansFont || DEFAULT_CONFIG.sansFont;

    root.style.setProperty('--sah-font-display', display);
    root.style.setProperty('--sah-font-serif', serif);
    root.style.setProperty('--sah-font-sans', sans);

    // 2. Font scale & Line height
    var scale = parseFloat(cfg.fontScale || 1.0);
    root.style.setProperty('--sah-font-scale', String(scale));
    root.style.fontSize = Math.round(16 * scale) + 'px';

    var lh = parseFloat(cfg.lineHeight || 1.6);
    root.style.setProperty('--sah-line-height', String(lh));

    // 3. Theme Palette
    var paletteId = cfg.themePalette || 'theme-gold';
    var p = THEME_PALETTES[paletteId] || THEME_PALETTES['theme-gold'];

    root.style.setProperty('--sah-bg-obsidian', p.bgObsidian);
    root.style.setProperty('--sah-bg-surface', p.bgSurface);
    root.style.setProperty('--sah-bg-card', p.bgCard);
    root.style.setProperty('--sah-gold-primary', p.goldPrimary);
    root.style.setProperty('--sah-gold-bright', p.goldBright);
    root.style.setProperty('--sah-gold-border', p.goldBorder);
    root.style.setProperty('--sah-text-heading', p.textHeading);
    root.style.setProperty('--sah-text-body', p.textBody);
    root.style.setProperty('--sah-text-muted', p.textMuted);

    // Update body theme class
    Object.keys(THEME_PALETTES).forEach(function(k) {
      body.classList.remove(k);
    });
    body.classList.add(paletteId);
    if (p.isLight) {
      body.classList.add('theme-light-mode');
    } else {
      body.classList.remove('theme-light-mode');
    }

    // 4. Card Radius & Glass Blur
    var rad = cfg.cardRadius || '20px';
    root.style.setProperty('--sah-radius-card', rad);
    var blurVal = cfg.glassBlur || '16px';
    root.style.setProperty('--sah-blur-glass', blurVal);

    // 5. Watermark opacity
    var wmOp = parseFloat(cfg.watermarkOpacity != null ? cfg.watermarkOpacity : 0.022);
    var wm = document.querySelector('.sah-museum-watermark');
    if (wm) {
      wm.style.opacity = String(wmOp);
    }

    // 6. Projector High Contrast
    if (cfg.projectorContrast) {
      body.classList.add('projector-contrast');
    } else {
      body.classList.remove('projector-contrast');
    }

    // 7. Dispatch custom event for listener components
    try {
      window.dispatchEvent(new CustomEvent('sah-theme-changed', { detail: cfg }));
    } catch(e) {}
  }

  // Inject Dedicated Theme & Font Utility Styles
  function injectThemeStyles() {
    if (document.getElementById('sah-theme-engine-css')) return;
    var css = [
      "/* Smart Art Heritage • Dynamic Theme & Font System */",
      ":root {",
      "  --sah-font-scale: 1.0;",
      "  --sah-radius-card: 20px;",
      "  --sah-blur-glass: 16px;",
      "}",
      "body.theme-light-mode {",
      "  background-color: var(--sah-bg-obsidian) !important;",
      "  color: var(--sah-text-body) !important;",
      "}",
      "body.theme-light-mode .sah-step-sec {",
      "  background: rgba(255, 255, 255, 0.95) !important;",
      "  border-color: rgba(153, 101, 21, 0.28) !important;",
      "  box-shadow: 0 16px 40px rgba(100, 80, 50, 0.12) !important;",
      "}",
      "body.theme-light-mode .rm-topnav {",
      "  background: rgba(247, 244, 237, 0.96) !important;",
      "  border-bottom-color: rgba(153, 101, 21, 0.25) !important;",
      "}",
      "body.theme-light-mode .sah-lstat-card,",
      "body.theme-light-mode .sah-dash-card,",
      "body.theme-light-mode .sah-comment-card {",
      "  background: #ffffff !important;",
      "  border-color: rgba(153, 101, 21, 0.22) !important;",
      "  box-shadow: 0 6px 18px rgba(0,0,0,0.06) !important;",
      "}",
      "body.projector-contrast {",
      "  filter: contrast(114%) brightness(105%);",
      "}",
      "body.projector-contrast .sah-step-sec {",
      "  border-width: 2px !important;",
      "  box-shadow: 0 0 0 1px var(--sah-gold-primary), 0 20px 60px rgba(0,0,0,0.9) !important;",
      "}",
      "body.projector-contrast .sah-sec-header h2,",
      "body.projector-contrast .sah-landing-title {",
      "  text-shadow: 0 2px 8px rgba(0,0,0,0.8), 0 0 16px var(--sah-gold-primary);",
      "}",
      ".sah-theme-badge {",
      "  display: inline-flex;",
      "  align-items: center;",
      "  gap: 6px;",
      "  padding: 4px 10px;",
      "  border-radius: 999px;",
      "  font-size: 11px;",
      "  font-weight: 700;",
      "  background: rgba(212, 175, 55, 0.15);",
      "  color: var(--sah-gold-primary);",
      "  border: 1px solid var(--sah-gold-border);",
      "}"
    ].join('\n');

    var styleEl = document.createElement('style');
    styleEl.id = 'sah-theme-engine-css';
    styleEl.textContent = css;
    (document.head || document.documentElement).appendChild(styleEl);
  }

  // Auto init
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      injectThemeStyles();
      applyConfig();
    });
  } else {
    injectThemeStyles();
    applyConfig();
  }

  // Export to Global window.SahTheme API
  window.SahTheme = {
    FONT_PRESETS: FONT_PRESETS,
    THEME_PALETTES: THEME_PALETTES,
    DEFAULT_CONFIG: DEFAULT_CONFIG,
    getConfig: getConfig,
    saveConfig: saveConfig,
    resetConfig: resetConfig,
    applyConfig: applyConfig
  };

})();
