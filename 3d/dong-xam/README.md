# Làng nghề chạm bạc Đồng Xâm — 3D Asset

Smart Art Heritage · the fifth heritage asset: the silver-carving village temple
complex at Hồng Thái, Kiến Xương, Thái Bình, on the **sông Vông**.

## Layout (from research + references)

- **Sông Vông** along the front, with the **nhà thủy tọa** — a two-tier pavilion
  standing IN the river on stone piles (six arched doors), reached by a white
  **footbridge**; multi-arch **brick bridge** crossing the river to the east;
  muddy water with **lotus** patches.
- **Tiền Tế** — grand 5-bay hall facing the river: stone terrace + stairs +
  balustrade, grey-white walls, **3 arched loggia portals** with white surrounds,
  round **gold medallion** row above, red columns, couplet panels, **two-tier
  steep red-tile roof** with upswept đao corners and a **gold-disc ridge line**.
- **Trung Tế + Hậu Cung** — connector block and the taller stacked two-tier
  Hậu Cung (the Khán Gian silver-carving hall) with gold finial; side wings.
- **Đền Thờ Tổ** (craft-founder shrine, "KHỔI TỔ 1428", from the user's photo) —
  Indochine **yellow facade**, white trim + quoins, tall arch portal with dark
  reveal + hanging lantern, side niches, couplet panels, **red/white roofline
  balustrade**, THREE circular character **medallions** on the roof slope,
  grey tile roof with corner pots, red blossom bushes, bronze urns.
- Grounds: flagpole with animated flag, **stone steles on turtle bases**,
  **carved altar with incense urn**, axial lamp posts, **planted urn rows**,
  axial walkway to the bridge, trees, dense village greenery, red-roofed
  village houses behind (aerial reference).
- The thủy tọa is fully detailed: **stone balustrade** around the platform,
  **white arch surrounds + red doors** on all four sides, corner lanterns
  (animated), and the footbridge now **spans the full river** to meet it
  (the first build's bridge stopped 6 m short — fixed).

Ambiguities resolved: interiors dark; medallion characters stylised as incised
discs; statues omitted; boat race not modeled.

## Blender master

- **File:** `3d/dong-xam/blender/dong-xam-model.blend` — opens in Material
  Preview with colors and the hero camera framed.
  Visitors: 30 figures — couples on the walkway/bridge, monk procession,
  families in the courtyard, kids in the village street.
- **Collections:** `Temple`, `ToShrine`, `WaterPavilion`, `River`, `Grounds`,
  `Trees`, `Flags`, `Lighting`, `Cameras`, `Environment` (449 objects).
- **Rebuild:** `blender --background --python scripts/build_dong_xam.py`
  then `blender --background --python scripts/export_dong_xam.py`, then
  regenerate `preview/preview_standalone.html` (inline vendor JS + base64 GLB).
- Renders in `blender/renders/` (hero / toshrine / hall / aerial), inspected
  across 5 iterations (fixed the corner-lift formula blowing up on long
  hip roofs — 41 m blades; river visibility; medallion mounting; arch ring
  intrusion; camera framing).

## GLB export

- `exports/dong-xam-model.glb` — **24,216 triangles, 33 meshes, baked
  materials**, 1024px textures, **7 sway animations** (lantern pivots + flag),
  ~4.1 MB. Re-import validated in clean Blender.

## Web preview

`preview/preview_standalone.html` (fully self-contained: inlined Three.js +
base64 GLB — open from anywhere) or `preview/index.html` (serve the project
root). Orbit/zoom, auto-orbit, lantern toggle, reset view, loading state,
error fallback, `prefers-reduced-motion`, ACES tone mapping, responsive
aspect-aware framing.

Verified: desktop + 390×844 mobile, zero console errors, 5 animations playing.

## Known limitations

- Statues/altars and silverwork interiors are omitted (interiors closed).
- Bridge arches are simplified vault rings; water is opaque matte (no refraction).
