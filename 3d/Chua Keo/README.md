# Gác Chuông Chùa Keo — 3D Heritage Asset

Procedurally-built Blender model of the **Gác Chuông (Bell Tower) of Chùa Keo**
(Thái Bình, Vietnam) with its surrounding courtyard compound — tam quan gate,
hành lang corridor galleries, side halls, boundary wall, trees and brick paving —
researched from reference photos of the real tower and exported as a web-ready GLB.

**Status: awaiting approval — the production website has NOT been modified.**

## Layout

```
3d/
├── reference_*.png                # reference images captured from the brief
├── blender/
│   ├── nlt-agent-model.blend      # ★ OPEN THIS in Blender 4.5+ (the master project)
│   ├── scripts/
│   │   ├── build_pagoda.py        # full procedural rebuild (deterministic)
│   │   └── export_glb.py          # web pipeline: bake materials, rig lanterns, GLB
│   └── renders/
│       ├── preview_hero.png
│       ├── preview_three_quarter.png
│       ├── preview_eaves.png
│       └── preview_courtyard.png
├── exports/
│   ├── nlt-agent-model.glb        # ★ web-ready GLB (glTF 2.0 binary)
│   └── export_stats.json          # machine-readable export stats
└── preview/
    ├── index.html                 # standard preview (loads ../exports GLB)
    ├── preview_standalone.html    # self-contained (JS + GLB inlined) for offline review
    └── vendor/                    # three.js r128 + GLTFLoader + OrbitControls (local)
```

## Blender master

- **File:** `3d/blender/nlt-agent-model.blend` — open in Blender 4.5 (LTS) or newer.
  Visitors: 26 stylised pilgrims/tourists (families, kids with balloons,
  photographer, monk procession) placed on the courtyard + walkway.
- **Collections:** `Architecture_Structure`, `Architecture_Roofs`, `Architecture_Details`,
  `Compound`, `Lanterns`, `Environment`, `Lighting`, `Cameras`.
- **Tower (per research on the real Gác Chuông):** stone platform + steps,
  timber colonnade, two galleries with slat balustrades, red doors,
  **intermediate eave bands (chồng diêm cổ các)** on every story, three upswept
  roof tiers (terracotta hip / hip + grey-green top gable, 12 roof planes),
  dragon-head corner ornaments, wind bells, **open top bell pavilion with a
  bronze bell**, ridge finials, 18 swinging lanterns, 4 named cameras,
  192-frame lantern swing animation + hero-camera orbit.
- **Compound:** tam quan entrance gate, two hành lang corridor galleries,
  side halls, stone boundary wall with caps, brick-paved courtyard, walkway,
  low-poly trees.
- **Materials:** rich procedural node graphs — brick-texture tile coursing with
  per-tile jitter and recessed mortar, wave-texture wood grain, ashlar stone
  blocks, roughness variation, weathering patches, bump mapping; flat PBR colors
  for gold, lantern silk and doors.
- **Rebuild:** `blender --background --factory-startup --python scripts/build_pagoda.py`
  (re-runs the entire scene from code and re-renders the previews).

## GLB export

- `nlt-agent-model.glb` — ~29.8k triangles, 27 meshes, 11 materials,
  1024px baked textures (baseColor + roughness for tile/wood/stone),
  18 lantern-swing animation tracks, ~2.6 MB.
- Export pipeline: bakes procedural materials to small textures (glTF cannot carry
  noise nodes), rigs each lantern on its own pivot with a pendulum action, joins
  geometry per material to minimize draw calls, strips Blender-only data.
- Re-export: `blender --background --factory-startup --python scripts/export_glb.py`

## Web preview

Serve the `3d/` folder (e.g. `python3 -m http.server`) and open
`preview/index.html`. Features: responsive canvas, orbit/zoom controls,
auto-orbit toggle, lantern animation toggle (with pause), double-click reset,
loading progress, WebGL/error fallback, `prefers-reduced-motion` respected
(auto-orbit and animation start paused).

`preview_standalone.html` inlines three.js and the GLB — open directly from disk.

## Design interpretation notes

- Real tower researched: ~8.5 m square plan, ~11 m tall, 3 tiers × 4 roof planes
  (12 roof surfaces, "stacked like a lotus bud"), mỗi tầng có its own eave line,
  iron-wood frame without nails, ngói nam tiles, bronze bell in the open top
  pavilion. Our model encodes these as documented geometry above.
- Ambiguities resolved: corridor roofs single-slope toward the courtyard,
  side halls and gate simplified hip roofs, dark unlit tower interior,
  carvings suggested by material variation, ridge finials simplified,
  trees are low-poly billboards-free blobs for web budget.
