# Đền Mẫu Phố Hiến + hồ Bán Nguyệt — 3D Heritage Asset

Procedurally-built Blender model of the **Đền Mẫu (Hoa Dương Linh Từ)** at
Phố Hiến, Hưng Yên — the nghi môn gate ("chồng diêm hai tầng tám mái"),
the temple with its arched loggias and flag terrace, and **hồ Bán Nguyệt**
(the crescent lake) with its stone walkway — exported as a web-ready GLB.

**Status: awaiting approval — the production website has NOT been modified.**

## Layout

```
3d/den-mau/
├── paste-*.png                    # reference images from the brief
├── blender/
│   ├── den-mau-model.blend        # ★ OPEN THIS in Blender 4.5+ (the master)
│   ├── scripts/
│   │   ├── build_den_mau.py       # full procedural rebuild (deterministic)
│   │   └── export_den_mau.py      # web pipeline: join, bake, rig flags, GLB
│   └── renders/
│       ├── preview_hero.png       # 3/4 view from the lake
│       ├── preview_front.png      # frontal gate + lake
│       ├── preview_temple.png     # temple terrace + flags
│       └── preview_throughgate.png# through the vaults
├── exports/
│   ├── den-mau-model.glb          # ★ web-ready GLB (glTF 2.0 binary)
│   └── export_stats.json          # machine-readable export stats
└── preview/
    ├── index.html                 # standard preview (loads ../exports GLB)
    ├── preview_standalone.html    # self-contained (JS + GLB inlined)
    └── vendor/                    # three.js r128 + GLTFLoader + OrbitControls
```

## What the model encodes (researched from the real site)

- **Nghi môn gate** — masonry wall with **3 vaulted through-openings** (1 main +
  2 side), stepped massing (tall centre bay, lower side bays), two stacked
  pavilions ("chồng diêm hai tầng tám mái" — 8 roof planes total), **circular
  moon window** on the upper story, đao flame tips, inscription tablets, gold
  finial. Aged grey masonry with dark rain-streak weathering.
- **Temple** — plinth + steps, 3 vaulted loggia arches + 2 red side doors,
  open upper **terrace with stone balustrade and 4 red flags**, central
  belvedere + two side wings with tile roofs.
- **Hồ Bán Nguyệt** — true crescent water body (annulus sector) with stone
  coping, outer balustrade, lotus pads, and a **stone walkway** crossing the
  crescent opening to the gate.
- Grounds — brick-paved courtyard, perimeter walls, 8 mature trees + shrubs,
  4 tall flagpoles (red/yellow) with waving flags, 2 lantern pillars.
- **Detail pass:** white-lime arch surrounds (gate + temple loggias), white
  eave fascia bands with apex finials on every roof, framed windows with dark
  reveals on both gate stories, cross-mullioned moon window with stone sill,
  framed inscription tablets with gold character bars, ridge bars, 10 hanging
  red lanterns (animated sway), bronze incense urns, dense balustrades and
  parapet posts, walkway parapets with posts.

Ambiguities resolved: interiors dark (doors closed), relief carvings suggested
by tablets/insets, trees low-poly, flags rigid-sway (no cloth sim).

## Blender master

- **File:** `3d/den-mau/blender/den-mau-model.blend` — opens in **Material
  Preview** shading with the hero camera framed (colors visible immediately).
  Visitors: 25 figures — sightseers crossing the walkway, kids at the
  lakeside, worshippers + monk on the temple terrace.
- **Collections:** `Gate`, `Temple`, `Lake`, `Grounds`, `Trees`, `Flags`,
  `Lighting`, `Cameras`, `Environment` (585 objects total).
- **Materials:** procedural — brick-pattern masonry with vertical rain-streak
  weathering, ashlar stone, tile coursing, wood grain, water, gold, red silk.
- **Rebuild:** `blender --background --python scripts/build_den_mau.py`
  (rebuilds the whole scene + re-renders previews).

## GLB export

- `den-mau-model.glb` — **25,012 triangles, 32 meshes, 16 materials**,
  1024px baked textures (color + roughness for masonry/stone/tile),
  **18 sway animations** (8 flags + 10 hanging lanterns, per-object pivots,
  phase-alternated), ~3.4 MB.
- Re-export: `blender --background --python scripts/export_den_mau.py`

## Web preview

Open `preview/index.html` (serve the `3d/` folder) or `preview_standalone.html`
(directly from disk — everything inlined). Features: responsive canvas with
aspect-aware initial framing, orbit/zoom, auto-orbit toggle, flags toggle,
double-click reset, loading bar, error fallback, `prefers-reduced-motion`
respected, ACES tone mapping.

Verified: desktop + 390×844 mobile viewports, flag animation playing
(rotation deltas sampled live), zero console errors.
