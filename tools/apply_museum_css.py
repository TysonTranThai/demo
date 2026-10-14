import re
import os

ROOT = "/Users/tysontran/Desktop/Smart Art Heritage"
BUILD_SCRIPT = os.path.join(ROOT, "tools", "build_index.py")

with open(BUILD_SCRIPT, "r", encoding="utf-8") as f:
    content = f.read()

MUSEUM_CSS = """<!-- SAH-GUIDELINE-CSS-START -->
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

/* Base Body in Slide Mode */
body.slide-mode {
  background: var(--sah-bg-obsidian);
  background-image: 
    radial-gradient(ellipse at 50% -12%, rgba(212, 175, 55, 0.14) 0%, transparent 60%),
    radial-gradient(circle at 85% 30%, rgba(139, 90, 43, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 15% 70%, rgba(179, 139, 34, 0.06) 0%, transparent 50%);
  background-attachment: fixed;
  color: var(--sah-text-body);
  font-family: var(--sah-font-sans);
  min-height: 100vh;
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
  padding: 13px 16px;
  background: #171411;
  border: 1px solid var(--sah-gold-border);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sah-map-item:hover {
  border-color: var(--sah-gold-primary);
  background: rgba(212, 175, 55, 0.12);
  transform: translateX(3px);
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

# Replace GUIDELINE_CSS
p_css_start = content.find("GUIDELINE_CSS = \"\"\"")
p_css_end = content.find('"""\n\n# -------------------------------------------', p_css_start)
if p_css_start != -1 and p_css_end != -1:
    content = content[:p_css_start] + "GUIDELINE_CSS = \"\"\"" + MUSEUM_CSS + "\"\"\"" + content[p_css_end + 3:]
    print("GUIDELINE_CSS replaced successfully!")
else:
    print("Failed to find GUIDELINE_CSS:", p_css_start, p_css_end)

# Also add the image switcher helpers into GUIDELINE_JS
gallery_helper = """
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
"""

if "window.switchExhibitImg = switchExhibitImg;" not in content:
    content = content.replace("window.toggleViewMode = toggleViewMode;", "window.toggleViewMode = toggleViewMode;\n" + gallery_helper)
    print("Added gallery helpers to GUIDELINE_JS!")

with open(BUILD_SCRIPT, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated build_index.py with Museum CSS & Gallery Helpers!")
