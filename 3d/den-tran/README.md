# Đền Trần Hưng Hà (Thiên Trường) — 3D Heritage Asset

Procedurally-built Blender model of the **Đền Trần temple complex** at Hưng Hà,
Thái Bình — red-brick enclosure with five arched openings, two-tier gate
pavilion, ornate corner pillars, ancient nghi môn, two-roofed đại điện, gravel
forecourt with the giant flagpole, and the historic **column-lined avenue**
running through rice fields between two grass mounds. Exported as a
web-ready GLB.

**Status: awaiting approval — the production website has NOT been modified.**

## Layout

```
3d/den-tran/
├── paste-*.png                    # reference images from the brief
├── blender/
│   ├── den-tran-model.blend       # ★ OPEN THIS in Blender 4.5+ (the master)
│   ├── scripts/
│   │   ├── build_den_tran.py      # full procedural rebuild (deterministic)
│   │   └── export_den_tran.py     # web pipeline: join, bake, rig flags, GLB
│   └── renders/
│       ├── preview_hero.png       # drone 3/4 over the avenue
│       ├── preview_front.png      # straight-on gate
│       ├── preview_temple.png     # courtyard → đại điện
│       ├── preview_avenue.png     # along the stone columns
│       └── preview_hall.png       # straight-on đại điện
├── exports/
│   ├── den-tran-model.glb         # ★ web-ready GLB (glTF 2.0 binary)
│   └── export_stats.json
└── preview/
    ├── index.html                 # standard preview (loads ../exports GLB)
    ├── preview_standalone.html    # self-contained (JS + GLB inlined)
    └── vendor/                    # three.js r128 + GLTFLoader + OrbitControls
```

## What the model encodes (from the references)

- **Enclosure wall** — 60 m red-brick wall, **5 real vaulted through-openings**
  (3 large + 2 small) with white-lime surrounds, dark tunnel reveals and
  open wooden door pairs, brick cornice + red tile coping, orange banner band.
- **Gate pavilion** — two stacked tiers (long hall + centre pavilion) with
  red-tile hip roofs, upswept đao corners, white colonnades, gold finial,
  white balustrades along the wall-top terrace.
- **Small side gate pavilions** left/right in the wall.
- **4 ornate corner pillars** (two pairs) — white shafts, stacked stone
  capitals, gold finials, hanging banners.
- **Nghi môn** — 4 weathered columns (2 tall + 2 short) with tile caps and
  connecting beams + side roofs, in the first courtyard.
- **Đại điện** — stone plinth, red-lacquer colonnade with stone bases, lattice
  screens + fanlights, framed gold plaque, **steep two-tier old-tile roof
  stack** with intermediate eave skirt (chồng diêm), corbel band, ridge bars
  with dragon-horn tips, gold finial + spire; flanked by two side halls.
- **Detail pass:** double arch rings, hanging red lanterns (animated), stone
  steles on turtle bases, bronze urns, lamp posts, yard paths + curbs, red
  fascia bands, ornate avenue columns (red band, ring, lotus caps).
- **Forecourt** — gravel with the **22 m giant flagpole** (animated red flag),
  steps, tree pairs.
- **Avenue** — raised paved strip lined with **2×9 stone columns** (pedestals,
  shafts, ball finials) running through **rice fields** (light/dark paddies +
  water strips), flanked by **two grass mounds** (historic earthworks).

Ambiguities resolved: interiors dark; brick reliefs suggested by material;
column statues simplified to discs+finials; trees/bushes low-poly.

## Blender master

- **File:** `3d/den-tran/blender/den-tran-model.blend` — opens in Material
  Preview with colors and the hero camera framed.
  Visitors: 28 figures — pilgrim families at the gate, monk procession,
  visitors along the column avenue and the courtyard.
- **Collections:** `Wall_Gate`, `Temple`, `Grounds`, `Fields`, `Trees`,
  `Flags`, `Lighting`, `Cameras`, `Environment` (633 objects).
- **Rebuild:** `blender --background --python scripts/build_den_tran.py`

## GLB export

- `den-tran-model.glb` — **26,960 triangles, 32 meshes, 25 materials**,
  1024px baked textures (brick, stone, lime, tiles), **8 sway animations**
  (giant flag, 2 pillar banners, 5 hanging lanterns), ~4.1 MB.
- Re-export: `blender --background --python scripts/export_den_tran.py`

## Web preview

`preview/index.html` (serve `3d/`) or `preview_standalone.html` (open from
disk — fully inlined). Responsive framing by aspect, orbit/zoom, auto-orbit,
flags toggle, reset, loading bar, error fallback, `prefers-reduced-motion`,
ACES tone mapping.

Verified: desktop + 390×844 mobile, giant-flag animation playing (rotation
sampled live), zero console errors, GLB re-imported into clean Blender.
