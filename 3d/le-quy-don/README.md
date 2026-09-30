# Khu lưu niệm Lê Quý Đôn — 3D Heritage Asset

Procedurally-built Blender model of the **Lê Quý Đôn memorial site** (Độc Lập,
Hưng Hà, Thái Bình) — the wide memorial hall with its white dragon-ridge roof
and stone colonnade, the old timber house with white lime gable-ends flanked
by two arched gate pavilions, stone lantern pedestals + carved altar, and the
red-brick plaza with benches, lamps and trimmed bushes. Exported as a
web-ready GLB.

**Status: awaiting approval — the production website has NOT been modified.**

## Layout

```
3d/le-quy-don/
├── paste-*.png                    # reference images from the brief
├── blender/
│   ├── le-quy-don-model.blend     # ★ OPEN THIS in Blender 4.5+ (the master)
│   ├── scripts/
│   │   ├── build_le_quy_don.py    # full procedural rebuild (deterministic)
│   │   └── export_le_quy_don.py   # web pipeline: join, bake, rig lanterns, GLB
│   └── renders/
│       ├── preview_hero.png       # reference-angle view from the plaza
│       ├── preview_house.png      # old house + gate pavilions
│       ├── preview_hall.png       # memorial hall colonnade
│       └── preview_plaza.png      # plaza overview
├── exports/
│   ├── le-quy-don-model.glb       # ★ web-ready GLB (glTF 2.0 binary)
│   └── export_stats.json
└── preview/
    ├── index.html                 # standard preview (loads ../exports GLB)
    ├── preview_standalone.html    # self-contained (JS + GLB inlined)
    └── vendor/                    # three.js r128 + GLTFLoader + OrbitControls
```

## What the model encodes (from the references)

- **Memorial hall** — stone terrace with **3 stair flights** (centre wide +
  cheek walls), grey **stone colonnade** (9 columns + bases), dark timber
  body with red door band and red banner, aged-terracotta **saddle-hip roof
  with a true ridge line** carrying the **white dragon crest** (bar + flame
  ball + horn pairs + head boards seated ON the ridge), **4 hanging
  lanterns (animated)**.
- **Old timber house** — dark weathered wood, **recessed front wall forming a
  real open loggia** (posts + bases + beam + porch floor), framed doorway,
  red door + lattice door, full **gable roof** (ridge E-W), white lime
  gable-end walls tucked under the roofline + white ridge bar with horns.
- **Two gate pavilions** — grey plaster blocks with real arched openings,
  red-tile saddled roofs, mini white ridge crests with horns.
- **Forecourt** — carved **stone altar** + 4 **stone lantern pedestals**.
- **Plaza** — red-brick paving with worn patches, green benches, garden lamps,
  trimmed bushes, hedge row, 8 trees (incl. two palms).

Ambiguities resolved: interiors dark, dragon ridge stylised to crest geometry,
statues omitted, benches simplified.

## Blender master

- **File:** `3d/le-quy-don/blender/le-quy-don-model.blend` — opens in Material
  Preview with colors and the hero camera framed.
  Visitors: 24 figures — families on the plaza, school group on the hall
  stairs, kids with balloons, monk at the altar.
- **Collections:** `Hall`, `OldHouse`, `Grounds`, `Plaza`, `Trees`, `Flags`,
  `Lighting`, `Cameras`, `Environment` (249 objects).
- **Bug fixes in v2/v3:** roofs rebuilt as true saddle-hips with ridge lines
  (old version had pyramid roofs, leaving ridge ornaments floating); house
  changed to full gable roof; gable walls re-profiled + repositioned (old
  version pierced the roof AND sat detached from the house at y=0 instead of
  y=−6 — the floating "white sails"); dao-tip ornaments re-derived from the
  new roof height formula (old ones floated ~1 m); ridge bars clamped to the
  true ridge segment length; front wall recessed into a loggia.
- **Bug fixes in v4 (viewport screenshot pass):** smooth shading now marks
  edges sharper than 32° as sharp — the big roofs previously smeared normals
  across ridge/hip edges and rendered as large misplaced grey facet patches;
  gable-end walls now track the roof underside pointwise (no dark open
  triangle at the gable ends); standalone preview re-inlines vendor scripts
  (rebuild had 404'd them).
- **Rebuild:** `blender --background --python scripts/build_le_quy_don.py`
  then `blender --background --python scripts/export_le_quy_don.py`, then
  regenerate `preview/preview_standalone.html` (inline vendor JS + base64 GLB).

## GLB export

- `le-quy-don-model.glb` — **10,500 triangles, 22 meshes, 19 materials**,
  1024px baked textures, **4 lantern-sway animations** (per-lantern pivots),
  ~2.7 MB.
- Re-export: `blender --background --python scripts/export_le_quy_don.py`

## Web preview

`preview/index.html` (serve `3d/`) or `preview_standalone.html` (open from
disk). Responsive aspect-aware framing, orbit/zoom, auto-orbit, lantern
toggle, reset, loading bar, error fallback, `prefers-reduced-motion`, ACES
tone mapping.

Verified: desktop + 390×844 mobile, lantern animation playing (rotation
sampled live), zero console errors, GLB re-imported into clean Blender.
