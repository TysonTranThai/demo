# -*- coding: utf-8 -*-
"""
SMART ART HERITAGE — Gác Chuông (Bell Tower), Chùa Keo (Thái Bình).  V3
Procedural Blender 4.5 build. V3 upgrade based on research of the real tower:

Real-tower facts encoded (researched):
- 3 tiers x 4 roof planes = 12 roof surfaces, "stacked like a lotus bud"
- "Chồng diêm cổ các": each story has its own intermediate eave band between
  the main roof tiers (3 roof lines per story)
- Square plan ~8.5 m side, ~11 m tall, iron-wood frame, ngói nam clay tiles
- Open top pavilion with a hanging bronze bell
- Dragon-head eave-corner ornaments + flame (lưỡi mác) ridge finials
- Surrounding complex: tam quan gate, hành lang corridor galleries flanking a
  courtyard, side halls, brick paving, stone boundary wall, trees

V2 changelog (visual iterations vs reference) retained below.
- Much larger roof tiers with strong upswept corners; dark-wood underside fascia
- Taller overall proportions; dark interior core; ground-floor railings
- Lanterns hung on visible cords under each eave
- Aged-wood / terracotta / grey-gable materials with baked detail
"""

import bpy, bmesh, os, math, sys
from math import radians, sin, cos, pi
from mathutils import Vector, Euler

V = Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(SCRIPT_DIR, "..", "nlt-agent-model.blend")
RENDER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "renders"))
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "_shared")))
from visitors_module import add_visitors

# ---------------------------------------------------------------- helpers
def build_mesh(name, bm, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.scene.collection.objects.link(obj)
    return obj

def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=V(size), verts=bm.verts)
    return build_mesh(name, bm, loc, rot)

def cylinder(name, r, h, loc=(0, 0, 0), verts=14, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=r, radius2=r, depth=h)
    return build_mesh(name, bm, loc, rot)

def sphere(name, r, loc=(0, 0, 0), segs=14, rings=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    return build_mesh(name, bm, loc)

def shade_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

# ---------------------------------------------------------------- materials
def pbr(name, color, rough=0.8, metal=0.0, emit=None, emit_strength=0.0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat

def noise_mat(name, base, spot, rough=0.85, scale=6.0, detail=8.0, dist=0.0, lo=0.35, hi=0.65):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = detail
    if "Roughness" in tex.inputs:
        tex.inputs["Roughness"].default_value = 0.55
    if dist:
        tex.inputs["Distortion"].default_value = dist
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = lo
    ramp.color_ramp.elements[0].color = (*base, 1.0)
    ramp.color_ramp.elements[1].position = hi
    ramp.color_ramp.elements[1].color = (*spot, 1.0)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat

MAT = {}
def _obj_uv(nt):
    """Object-space texture coordinates (stable under joins/bakes)."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs["Object"]

def _weathering(nt, strength=0.35, lo=0.72, hi=1.18):
    """Large-scale brightness variation (weathering patches). Returns Color output."""
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.9
    noise.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    return ramp.outputs["Color"], strength

def tile_mat(name, c1, c2, mortar_col, rough=0.45, bump=0.14):
    """Curved-tile roof: running-bond tile rows, per-tile color jitter,
    recessed dark mortar, roughness variation, weathering patches."""
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    uv = _obj_uv(nt)

    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 0.40
    brick.inputs["Row Height"].default_value = 0.125
    brick.inputs["Mortar Size"].default_value = 0.012
    brick.inputs["Mortar Smooth"].default_value = 0.45
    brick.inputs["Bias"].default_value = 0.0
    brick.inputs["Color1"].default_value = (*c1, 1.0)
    brick.inputs["Color2"].default_value = (*c2, 1.0)
    brick.inputs["Mortar"].default_value = (*mortar_col, 1.0)
    nt.links.new(uv, brick.inputs["Vector"])

    wcol, wf = _weathering(nt)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = wf
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(wcol, mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = bump
    bumpn.inputs["Distance"].default_value = 0.02
    nt.links.new(brick.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])

    rn = nt.nodes.new("ShaderNodeTexNoise")
    rn.inputs["Scale"].default_value = 7.0
    rn.inputs["Detail"].default_value = 6.0
    rmap = nt.nodes.new("ShaderNodeMapRange")
    rmap.inputs["From Min"].default_value = 0.0
    rmap.inputs["From Max"].default_value = 1.0
    rmap.inputs["To Min"].default_value = rough - 0.12
    rmap.inputs["To Max"].default_value = rough + 0.18
    nt.links.new(uv, rn.inputs["Vector"])
    nt.links.new(rn.outputs["Fac"], rmap.inputs["Value"])
    nt.links.new(rmap.outputs["Result"], bsdf.inputs["Roughness"])
    return mat

def wood_mat(name, base, streak, rough=0.75):
    """Aged timber: vertical grain bands with distortion, darker recesses,
    weathering patches, subtle bump."""
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    uv = _obj_uv(nt)

    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'X'
    wave.wave_profile = 'SIN'
    wave.inputs["Scale"].default_value = 6.0
    wave.inputs["Distortion"].default_value = 5.5
    wave.inputs["Detail"].default_value = 2.5
    wave.inputs["Detail Scale"].default_value = 1.4
    nt.links.new(uv, wave.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (*base, 1.0)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*streak, 1.0)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])

    wcol, wf = _weathering(nt, strength=0.45, lo=0.65, hi=1.25)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = wf
    nt.links.new(ramp.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(wcol, mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = 0.06
    bumpn.inputs["Distance"].default_value = 0.01
    nt.links.new(wave.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])

    rn = nt.nodes.new("ShaderNodeTexNoise")
    rn.inputs["Scale"].default_value = 9.0
    rmap = nt.nodes.new("ShaderNodeMapRange")
    rmap.inputs["To Min"].default_value = rough - 0.08
    rmap.inputs["To Max"].default_value = rough + 0.12
    nt.links.new(uv, rn.inputs["Vector"])
    nt.links.new(rn.outputs["Fac"], rmap.inputs["Value"])
    nt.links.new(rmap.outputs["Result"], bsdf.inputs["Roughness"])
    return mat

def stone_mat(name, c1, c2, mortar_col, rough=0.88):
    """Ashlar stone blocks with per-block value jitter and recessed joints."""
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    uv = _obj_uv(nt)

    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 0.62
    brick.inputs["Row Height"].default_value = 0.30
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Mortar Smooth"].default_value = 0.3
    brick.inputs["Color1"].default_value = (*c1, 1.0)
    brick.inputs["Color2"].default_value = (*c2, 1.0)
    brick.inputs["Mortar"].default_value = (*mortar_col, 1.0)
    nt.links.new(uv, brick.inputs["Vector"])

    wcol, wf = _weathering(nt, strength=0.5, lo=0.78, hi=1.12)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = wf
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(wcol, mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = 0.10
    bumpn.inputs["Distance"].default_value = 0.015
    nt.links.new(brick.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Roughness"].default_value = rough
    return mat

def build_materials():
    MAT["wood"]    = wood_mat("Pagoda_Wood_Dark",   (0.052, 0.035, 0.022), (0.135, 0.088, 0.052), rough=0.75)
    MAT["wood_ul"] = pbr("Pagoda_Wood_UltraDark",    (0.075, 0.060, 0.050), rough=0.9)
    MAT["tile"]    = tile_mat("Pagoda_Tile_Terra",  (0.485, 0.185, 0.072), (0.365, 0.140, 0.056), (0.125, 0.052, 0.032), rough=0.42)
    MAT["tile_g"]  = tile_mat("Pagoda_Tile_Grey",   (0.165, 0.175, 0.150), (0.225, 0.235, 0.200), (0.10, 0.105, 0.09), rough=0.58, bump=0.10)
    MAT["stone"]   = stone_mat("Pagoda_Stone_Grey", (0.26, 0.26, 0.25), (0.35, 0.35, 0.34), (0.20, 0.20, 0.19), rough=0.88)
    MAT["gold"]    = pbr("Pagoda_Gold_Trim",         (0.80, 0.60, 0.22), rough=0.35, metal=1.0)
    MAT["bronze"]  = pbr("Pagoda_Bronze",           (0.26, 0.20, 0.11), rough=0.42, metal=0.9)
    MAT["leaf"]    = pbr("Pagoda_Foliage",           (0.085, 0.160, 0.052), rough=0.85)
    MAT["lat_red"] = pbr("Pagoda_Lantern_Red",       (0.50, 0.045, 0.035), rough=0.6, emit=(1.0, 0.22, 0.1), emit_strength=0.5)
    MAT["lat_tas"] = pbr("Pagoda_Lantern_Tassel",    (0.80, 0.68, 0.25), rough=0.7, emit=(0.85, 0.65, 0.2), emit_strength=0.25)

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
build_materials()

COL = {}
for cname in ["Architecture_Structure", "Architecture_Roofs", "Architecture_Details",
              "Compound", "Lanterns", "Environment", "Lighting", "Cameras"]:
    COL[cname] = bpy.data.collections.new(cname)
    scene.collection.children.link(COL[cname])

def place(obj, cname):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    COL[cname].objects.link(obj)
    return obj

# ================================================================ DIMENSIONS
# Real tower: ~8.5 m square plan, ~11 m tall. Our plan: 9 bays x 0.885 m.
COL_N = 9
BAY = 0.885
H_COL  = 2.70
S = (COL_N - 1) * BAY          # 7.08 plan width

Z0 = 0.0
PLATFORM_H = 0.75
PLATFORM_W = S + 3.4

Z_BALC1  = H_COL               # 2.70
Z_FLOOR1 = Z_BALC1 + 0.22      # 2.92
H_GAL1   = 2.10
Z_BALC2  = Z_FLOOR1 + H_GAL1   # 5.02
Z_FLOOR2 = Z_BALC2 + 0.22      # 5.24
H_GAL2   = 1.85
Z_ROOF1  = Z_FLOOR2 + H_GAL2   # 7.09  underside of roof tier 1

R1_W, R1_H = S / 2 + 1.35, 1.30
R2_W, R2_H = S / 2 + 0.35, 1.15
R3_W, R3_H = R2_W - 0.35, 2.20           # top gable NARROWER than tier-2 roof (tapered silhouette)
R3_D = 2.70                              # gable depth: eaves overhang the top pavilion
T2_BASE = Z_ROOF1 + R1_H * 0.80
# open bell pavilion rises through the tier-2 roof, gable sits on top of it
Z_PAV_BASE  = T2_BASE + R2_H * 0.30
Z_PAV_TOP   = T2_BASE + R2_H + 1.00
Z_ROOF2_TOP = Z_PAV_TOP - 0.08

# ================================================================ 1. PLATFORM
place(box("Stone_Platform", (PLATFORM_W, PLATFORM_W, PLATFORM_H), (0, 0, -PLATFORM_H / 2)), "Architecture_Structure")
# three ascending stone steps on the +Y (front) side
for k in range(3):
    w = PLATFORM_W - 0.0 + k * 0.0
    d = 0.55 - k * 0.12
    h = 0.16 * (k + 1)
    place(box(f"Stone_Step_{k}", (w - 1.6 + k * 0.8, d, h), (0, PLATFORM_W / 2 + 0.28 - k * 0.28, -h / 2)), "Architecture_Structure")

# ================================================================ 2. COLUMNS
col_xs = [-(COL_N - 1) / 2 * BAY + i * BAY for i in range(COL_N)]
for i, x in enumerate(col_xs):
    for j, y in enumerate(col_xs):
        if i == 0 or j == 0 or i == COL_N - 1 or j == COL_N - 1:
            place(cylinder(f"Column_Ground_{i}_{j}", 0.13, H_COL, (x, y, Z0 + H_COL / 2), verts=10), "Architecture_Structure")

def lintel_ring(z, tag, w=S, t=0.15, hgt=0.18, mat_col="Architecture_Structure"):
    place(box(f"Lintel_{tag}_N", (w, t, hgt), (0, S / 2, z)), mat_col)
    place(box(f"Lintel_{tag}_S", (w, t, hgt), (0, -S / 2, z)), mat_col)
    place(box(f"Lintel_{tag}_E", (t, w, hgt), (S / 2, 0, z)), mat_col)
    place(box(f"Lintel_{tag}_W", (t, w, hgt), (-S / 2, 0, z)), mat_col)

lintel_ring(Z_BALC1 - 0.09, "G")

# ================================================================ 3. INTERIOR CORE (dark mass)
core_w = S - 1.1
place(box("Interior_Core", (core_w, core_w, Z_ROOF1 - 0.15), (0, 0, (Z_ROOF1 - 0.15) / 2)), "Architecture_Structure")
# front doorway suggestion (dark recessed panel)
place(box("Door_Front", (1.5, 0.1, 1.9), (0, core_w / 2 + 0.03, 0.95)), "Architecture_Details")

# ground-floor perimeter railing between columns (dark wood)
def ground_rail(y, tag):
    zt = 0.95
    place(box(f"GroundRail_{tag}_Top", (S - 0.3, 0.08, 0.08), (0, y, zt)), "Architecture_Details")
    place(box(f"GroundRail_{tag}_Mid", (S - 0.3, 0.05, 0.05), (0, y, 0.52)), "Architecture_Details")
    n = int((S - 0.3) / 0.13)
    for k in range(n):
        x = -(S - 0.3) / 2 + 0.065 + k * 0.13
        place(box(f"GroundRail_{tag}_Slat_{k}", (0.035, 0.035, 0.40), (x, y, 0.50)), "Architecture_Details")
ground_rail(S / 2 - 0.31, "F")
ground_rail(-(S / 2 - 0.31), "B")

# ================================================================ 4. GALLERIES
place(box("Gallery1_Floor_Slab", (S + 1.0, S + 1.0, 0.2), (0, 0, Z_BALC1 + 0.11)), "Architecture_Structure")
place(box("Gallery2_Floor_Slab", (S + 0.7, S + 0.7, 0.2), (0, 0, Z_BALC2 + 0.11)), "Architecture_Structure")

for i, x in enumerate(col_xs):
    for j, y in enumerate(col_xs):
        if i == 0 or j == 0 or i == COL_N - 1 or j == COL_N - 1:
            place(cylinder(f"Column_Gal1_{i}_{j}", 0.10, H_GAL1, (x, y, Z_FLOOR1 + H_GAL1 / 2), verts=8), "Architecture_Structure")
            place(cylinder(f"Column_Gal2_{i}_{j}", 0.09, H_GAL2, (x, y, Z_FLOOR2 + H_GAL2 / 2), verts=8), "Architecture_Structure")

lintel_ring(Z_BALC2 - 0.09, "L2", w=S + 0.7)
lintel_ring(Z_ROOF1 - 0.09, "L3", w=S + 0.4)

def balustrade(z_floor_top, tag, run_w, y):
    zt = z_floor_top + 0.62
    place(box(f"{tag}_RailTop", (run_w, 0.09, 0.09), (0, y, zt)), "Architecture_Details")
    place(box(f"{tag}_RailMid", (run_w, 0.06, 0.06), (0, y, z_floor_top + 0.33)), "Architecture_Details")
    n = int(run_w / 0.13)
    for k in range(n):
        x = -run_w / 2 + 0.065 + k * 0.13
        place(box(f"{tag}_Slat_{k}", (0.04, 0.04, 0.52), (x, y, z_floor_top + 0.30)), "Architecture_Details")

def balustrade_x(z_floor_top, tag, run_w, x):
    zt = z_floor_top + 0.62
    place(box(f"{tag}_RailTop", (0.09, run_w, 0.09), (x, 0, zt)), "Architecture_Details")
    place(box(f"{tag}_RailMid", (0.06, run_w, 0.06), (x, 0, z_floor_top + 0.33)), "Architecture_Details")
    n = int(run_w / 0.13)
    for k in range(n):
        y = -run_w / 2 + 0.065 + k * 0.13
        place(box(f"{tag}_Slat_{k}", (0.04, 0.04, 0.52), (x, y, z_floor_top + 0.30)), "Architecture_Details")

for z_f, tag in ((Z_FLOOR1, "Balcony1"), (Z_FLOOR2, "Balcony2")):
    off = 0.45
    balustrade(z_f, f"{tag}_Front", S + 0.9 - off, S / 2 + off / 2 + 0.05)
    balustrade(z_f, f"{tag}_Back", S + 0.9 - off, -(S / 2 + off / 2 + 0.05))
    balustrade_x(z_f, f"{tag}_East", S + 0.9 - off, S / 2 + off / 2 + 0.05)
    balustrade_x(z_f, f"{tag}_West", S + 0.9 - off, -(S / 2 + off / 2 + 0.05))

# ================================================================ 5. ROOFS
def roof_shell(name, grid_fn, half_w, half_d, z_base, seg_x=10, seg_y=10, thick=0.22, tile_mat="tile"):
    """grid_fn(x,y)->height. Builds displaced grid, solidifies, assigns tile
    material to the TOP skin and dark wood to the UNDERSIDE by comparing each
    face's centre height against the profile function (robust to normal flips)."""
    bm = bmesh.new()
    Nx, Ny = seg_x + 1, seg_y + 1
    verts = []
    for iy in range(Ny):
        row = []
        for ix in range(Nx):
            xn = ix / seg_x
            yn = iy / seg_y
            x = (-half_w + 2 * half_w * xn)
            y = (-half_d + 2 * half_d * yn)
            h = grid_fn(x, y)
            row.append(bm.verts.new((x, y, h)))
        verts.append(row)
    for iy in range(Ny - 1):
        for ix in range(Nx - 1):
            bm.faces.new((verts[iy][ix], verts[iy][ix + 1],
                          verts[iy + 1][ix + 1], verts[iy + 1][ix]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.solidify(bm, thickness=thick, geom=geom)
    # Face is TILE if it sits at/above the mid-shell plane of the profile;
    # the lower skin (underside) gets dark wood. Tolerance covers solidify's
    # normal-direction offset of the original skin.
    for f in bm.faces:
        cx = sum(v.co.x for v in f.verts) / len(f.verts)
        cy = sum(v.co.y for v in f.verts) / len(f.verts)
        fz = sum(v.co.z for v in f.verts) / len(f.verts)
        f.material_index = 0 if fz >= grid_fn(cx, cy) - thick * 0.55 else 1
    obj = build_mesh(name, bm, (0, 0, z_base))
    me = obj.data
    me.materials.append(MAT[tile_mat])
    me.materials.append(MAT["wood_ul"])
    shade_smooth(obj)
    place(obj, "Architecture_Roofs")
    return obj

def hip_profile(half_w, rise, curve):
    def fn(x, y):
        u = max(abs(x), abs(y)) / half_w
        h = rise * (1 - u)
        h -= curve * rise * 0.20 * u * (1 - u) * 2          # gentle concave slope
        corner = (abs(x) / half_w) * (abs(y) / half_w)
        h += curve * rise * 0.85 * corner ** 4                # upswept corners
        return h
    return fn

def gable_profile(half_w, half_d, rise, curve):
    def fn(x, y):
        u = abs(y) / half_d
        h = rise * (1 - u)
        corner = (abs(x) / half_w) ** 3 * (u ** 2)
        h += curve * rise * 0.38 * corner                     # flying gable eaves
        return h
    return fn

roof_shell("Roof_Tier1", hip_profile(R1_W, R1_H, 0.75), R1_W, R1_W, Z_ROOF1 - 0.10)
roof_shell("Roof_Tier2", hip_profile(R2_W, R2_H, 0.75), R2_W, R2_W, T2_BASE - 0.08)

# open top pavilion (3rd story): posts rise through the tier-2 roof, bronze bell inside
PAV_HW = R2_W * 0.55
post_pos = [(sx * PAV_HW, sy * PAV_HW) for sx in (-1, 1) for sy in (-1, 1)] + \
           [(0, sy * PAV_HW) for sy in (-1, 1)] + [(sx * PAV_HW, 0) for sx in (-1, 1)]
for k, (px, py) in enumerate(post_pos):
    place(cylinder(f"Pavilion_Post_{k}", 0.085, Z_PAV_TOP - Z_PAV_BASE,
                   (px, py, Z_PAV_BASE + (Z_PAV_TOP - Z_PAV_BASE) / 2), verts=8), "Architecture_Structure")

# pavilion railings between posts (so the story reads as a pavilion, not a gazehole)
def pav_rail_y(y, tag):
    zt = Z_PAV_BASE + 0.52
    w = PAV_HW * 2
    place(box(f"{tag}_Top", (w, 0.07, 0.07), (0, y, zt)), "Architecture_Details")
    place(box(f"{tag}_Mid", (w, 0.05, 0.05), (0, y, Z_PAV_BASE + 0.26)), "Architecture_Details")
    n = int(w / 0.14)
    for k in range(n):
        x = -w / 2 + 0.07 + k * 0.14
        place(box(f"{tag}_Slat_{k}", (0.035, 0.035, 0.42), (x, y, Z_PAV_BASE + 0.24)), "Architecture_Details")

def pav_rail_x(x, tag):
    zt = Z_PAV_BASE + 0.52
    w = PAV_HW * 2
    place(box(f"{tag}_Top", (0.07, w, 0.07), (x, 0, zt)), "Architecture_Details")
    place(box(f"{tag}_Mid", (0.05, w, 0.05), (x, 0, Z_PAV_BASE + 0.26)), "Architecture_Details")
    n = int(w / 0.14)
    for k in range(n):
        y = -w / 2 + 0.07 + k * 0.14
        place(box(f"{tag}_Slat_{k}", (0.035, 0.035, 0.42), (x, y, Z_PAV_BASE + 0.24)), "Architecture_Details")

for sy in (-1, 1):
    pav_rail_y(sy * PAV_HW, f"PavRail_F{sy}")
for sx in (-1, 1):
    pav_rail_x(sx * PAV_HW, f"PavRail_E{sx}")

# perimeter header beams at pavilion top — the gable visibly rests on this ring
HB = Z_PAV_TOP - 0.10
place(box("PavBeam_N", (PAV_HW * 2 + 0.2, 0.16, 0.18), (0,  PAV_HW, HB)), "Architecture_Structure")
place(box("PavBeam_S", (PAV_HW * 2 + 0.2, 0.16, 0.18), (0, -PAV_HW, HB)), "Architecture_Structure")
place(box("PavBeam_E", (0.16, PAV_HW * 2 + 0.2, 0.18), ( PAV_HW, 0, HB)), "Architecture_Structure")
place(box("PavBeam_W", (0.16, PAV_HW * 2 + 0.2, 0.18), (-PAV_HW, 0, HB)), "Architecture_Structure")

# bronze bell in the open top pavilion (the tower is the BELL TOWER)
YOKE_Z = Z_PAV_TOP - 0.22
BELL_Z = YOKE_Z - 0.10
bell = bpy.data.objects.new("Bronze_Bell", bpy.data.meshes.new("Bronze_Bell"))
bbm = bmesh.new()
bmesh.ops.create_cone(bbm, cap_ends=True, cap_tris=False, segments=16,
                      radius1=0.40, radius2=0.27, depth=0.74)
bmesh.ops.translate(bbm, vec=V((0, 0, -0.31)), verts=bbm.verts)
bbm.to_mesh(bell.data)
bbm.free()
bpy.context.scene.collection.objects.link(bell)
bell.data.materials.append(MAT["bronze"])
bell.location = (0, 0, BELL_Z)
place(bell, "Architecture_Details")
bell_yoke = box("Bell_Yoke", (0.12, PAV_HW * 2 + 0.5, 0.09), (0, 0, YOKE_Z))
place(bell_yoke, "Architecture_Details")
bell_yoke.data.materials.append(MAT["wood_ul"])
bell_top = cylinder("Bell_Top_Knob", 0.05, 0.12, (0, 0, YOKE_Z - 0.02), verts=8)
place(bell_top, "Architecture_Details")
bell_top.data.materials.append(MAT["bronze"])

gable_fn = gable_profile(R3_W, R3_D, R3_H, 0.9)
roof_shell("Roof_Tier3_Gable", gable_fn, R3_W, R3_D, Z_ROOF2_TOP - 0.06, tile_mat="tile_g")

# red door panels on the upper-gallery level (front + back), echo of reference doors
for sy in (-1, 1):
    for k in range(4):
        dx = -1.35 + k * 0.9
        place(box(f"Door_Upper_{sy}_{k}", (0.72, 0.06, 1.45),
                  (dx, sy * (S / 2 + 0.12), Z_FLOOR2 + 0.85)), "Architecture_Details")

# gable-end tympanum walls (close the triangular ends of the top roof)
def tympanum(name, x_end, half_d, rise, z_base, fn):
    bm = bmesh.new()
    v1 = bm.verts.new((0, -half_d + 0.02, fn(x_end, -half_d + 0.02) - 0.02))
    v2 = bm.verts.new((0, half_d - 0.02, fn(x_end, half_d - 0.02) - 0.02))
    v3 = bm.verts.new((0, 0, fn(x_end, 0) - 0.06))  # stay just under the tile surface
    f = bm.faces.new((v1, v2, v3))
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    moved = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(-0.10 * (1 if x_end > 0 else -1), 0, 0), verts=moved)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = build_mesh(name, bm, (x_end, 0, z_base))
    obj.data.materials.append(MAT["wood"])
    place(obj, "Architecture_Roofs")
    return obj

tympanum("Gable_Tympanum_E", R3_W - 0.16, R3_D, R3_H, Z_ROOF2_TOP - 0.06, gable_fn)
tympanum("Gable_Tympanum_W", -(R3_W - 0.16), R3_D, R3_H, Z_ROOF2_TOP - 0.06, gable_fn)

# ridge + finial decorations
place(box("Ridge_T3_Main", (R3_W * 2 - 1.4, 0.26, 0.20), (0, 0, Z_ROOF2_TOP + R3_H + 0.04)), "Architecture_Details")
for sx in (-1, 1):
    place(box(f"Ridge_T3_End_{sx}", (1.1, 0.18, 0.14), (sx * (R3_W - 0.6), 0, Z_ROOF2_TOP + R3_H - 0.10),
              rot=(0, radians(30), 0)), "Architecture_Details")
    place(cone_fin := cylinder(f"Finial_T3_{sx}", 0.03, 0.5, (sx * (R3_W - 0.08), 0, Z_ROOF2_TOP + R3_H + 0.30),
          verts=8, rot=(0, radians(28), 0)), "Architecture_Details")
    place(sphere(f"Finial_T3_Ball_{sx}", 0.09, (sx * (R3_W - 0.28), 0, Z_ROOF2_TOP + R3_H + 0.28)), "Architecture_Details")
# center stupa ornament on the ridge
place(sphere("Finial_T3_Center", 0.13, (0, 0, Z_ROOF2_TOP + R3_H + 0.22)), "Architecture_Details")
place(cylinder("Finial_T3_Spire", 0.03, 0.55, (0, 0, Z_ROOF2_TOP + R3_H + 0.55), verts=8), "Architecture_Details")

# hip ridge caps for tier1/2 (small gold finial at each apex)
for tag, hw, z in (("T1", R1_W * 0.16, Z_ROOF1 + R1_H - 0.02), ("T2", R2_W * 0.16, T2_BASE + R2_H - 0.02)):
    place(box(f"Ridge_{tag}_Cap", (hw * 2, 0.2, 0.14), (0, 0, z)), "Architecture_Details")
    place(sphere(f"Finial_{tag}", 0.10, (0, 0, z + 0.14)), "Architecture_Details")

# intermediate eave bands — the real tower is "chồng diêm cổ các": every story
# shows its own small eave line between the main tiers (3 roof lines per story).
def eave_band(name, half_out, z, depth=0.85, thick=0.10, slope=0.55, tile_mat="tile"):
    """Four sloped perimeter skirts forming a stepped eave line (no hip cap)."""
    parts = []
    for sy in (-1, 1):   # north / south faces
        bm = bmesh.new()
        vts = [bm.verts.new(p) for p in (
            (-half_out,          sy * half_out,          0.0),
            ( half_out,          sy * half_out,          0.0),
            ( half_out + depth,  sy * (half_out + depth), -depth * slope),
            (-half_out - depth,  sy * (half_out + depth), -depth * slope))]
        bm.faces.new((vts[3], vts[2], vts[1], vts[0]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.solidify(bm, thickness=thick, geom=geom)
        o = build_mesh(f"{name}_{sy}", bm, (0, 0, z))
        o.data.materials.append(MAT[tile_mat])
        o.data.materials.append(MAT["wood_ul"])
        shade_smooth(o)
        place(o, "Architecture_Roofs")
        parts.append(o)
    for sx in (-1, 1):   # east / west faces
        bm = bmesh.new()
        vts = [bm.verts.new(p) for p in (
            (sx * half_out,          -half_out,          0.0),
            (sx * half_out,           half_out,          0.0),
            (sx * (half_out + depth), half_out + depth,  -depth * slope),
            (sx * (half_out + depth), -half_out - depth, -depth * slope))]
        bm.faces.new((vts[3], vts[2], vts[1], vts[0]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.solidify(bm, thickness=thick, geom=geom)
        o = build_mesh(f"{name}_{sx}", bm, (0, 0, z))
        o.data.materials.append(MAT[tile_mat])
        o.data.materials.append(MAT["wood_ul"])
        shade_smooth(o)
        place(o, "Architecture_Roofs")
        parts.append(o)
    return parts

eave_band("EaveBand_L2", S / 2,       Z_FLOOR2 + H_GAL2 - 0.14)                 # above upper gallery, tucks into column line
eave_band("EaveBand_T1", R2_W - 0.55, T2_BASE - 0.02, depth=0.55, slope=0.75)  # tier-2 story eave line under its roof

t1_fn = hip_profile(R1_W, R1_H, 0.75)
t2_fn = hip_profile(R2_W, R2_H, 0.75)

# wind bells (chuông gió) — small bronze bells under each tier-1 eave corner
def wind_bell(name, loc):
    body = cylinder(f"{name}_Body", 0.055, 0.14, (loc[0], loc[1], loc[2] - 0.07), verts=8)
    body.data.materials.append(MAT["bronze"])
    clap = sphere(f"{name}_Clapper", 0.018, (loc[0], loc[1], loc[2] - 0.17), segs=8, rings=5)
    clap.data.materials.append(MAT["gold"])
    strp = cylinder(f"{name}_String", 0.008, 0.08, (loc[0], loc[1], loc[2] - 0.01), verts=5)
    strp.data.materials.append(MAT["wood_ul"])

for sx in (-1, 1):
    for sy in (-1, 1):
        wind_bell(f"WindBell_T1_{sx}_{sy}",
                  (sx * (R1_W - 0.35), sy * (R1_W - 0.35),
                   Z_ROOF1 - 0.10 + t1_fn(sx * (R1_W - 0.35), sy * (R1_W - 0.35))))

# bronze bell in the open top pavilion (the tower is the BELL TOWER)
bell_z = Z_FLOOR2 + H_GAL2 * 0.55
bell = bpy.data.objects.new("Bronze_Bell", bpy.data.meshes.new("Bronze_Bell"))
bbm = bmesh.new()
bmesh.ops.create_cone(bbm, cap_ends=True, cap_tris=False, segments=16,
                      radius1=0.34, radius2=0.24, depth=0.62)
bmesh.ops.translate(bbm, vec=V((0, 0, -0.31)), verts=bbm.verts)
bbm.to_mesh(bell.data)
bbm.free()
bpy.context.scene.collection.objects.link(bell)
bell.data.materials.append(MAT["bronze"])
bell.location = (0, 0, bell_z)
bell.scale = (1, 1, 1.0)
place(bell, "Architecture_Details")
bell_yoke = box("Bell_Yoke", (0.55, 0.09, 0.07), (0, 0, bell_z + 0.36))
place(bell_yoke, "Architecture_Details")
bell_yoke.data.materials.append(MAT["wood_ul"])
bell_top = cylinder("Bell_Top_Knob", 0.05, 0.10, (0, 0, bell_z + 0.36), verts=8)
place(bell_top, "Architecture_Details")
bell_top.data.materials.append(MAT["bronze"])

# corner ornaments — dragon-head style (scaled head + upswept horn) seated on eave tips
for tag, hw, zb, fn in (("T1", R1_W, Z_ROOF1 - 0.10, t1_fn), ("T2", R2_W, T2_BASE - 0.08, t2_fn)):
    for sx in (-1, 1):
        for sy in (-1, 1):
            tip_z = zb + fn(sx * (hw - 0.02), sy * (hw - 0.02))
            head = sphere(f"CornerOrn_{tag}_{sx}_{sy}", 0.10, (sx * (hw - 0.02), sy * (hw - 0.02), tip_z + 0.04))
            head.scale = (1.0, 1.0, 0.70)
            place(head, "Architecture_Details")
            horn = cone_horn = cylinder(f"CornerHorn_{tag}_{sx}_{sy}", 0.035, 0.42,
                                        (sx * (hw - 0.14), sy * (hw - 0.14), tip_z + 0.22), verts=7,
                                        rot=(radians(-38) * sx, radians(38) * sy, 0))
            place(horn, "Architecture_Details")
            horn.data.materials.append(MAT["tile"])
            head.data.materials.append(MAT["tile"])

# ================================================================ 6. LANTERNS
lantern_parent = bpy.data.objects.new("Lanterns_Root", None)
scene.collection.objects.link(lantern_parent)
place(lantern_parent, "Lanterns")

def lantern(name, loc, scale=1.0, parent=lantern_parent):
    root = bpy.data.objects.new(name, None)
    root.location = (loc[0], loc[1], loc[2] - 0.04)
    root.parent = parent
    COL["Lanterns"].objects.link(root)
    # cord hangs DOWN from the eave
    cord = cylinder(f"{name}_Cord", 0.012, 0.42, (0, 0, -0.21), verts=6)
    cord.parent = root
    cord.data.materials.append(MAT["wood_ul"])
    body = sphere(f"{name}_Body", 0.17 * scale, loc=(0, 0, -0.56 * scale))
    body.scale = (1.0, 1.0, 0.85)
    body.parent = root
    body.data.materials.append(MAT["lat_red"])
    cap_t = cylinder(f"{name}_CapT", 0.06 * scale, 0.05 * scale, (0, 0, -0.36 * scale), verts=10)
    cap_t.parent = root
    cap_t.data.materials.append(MAT["gold"])
    cap_b = cylinder(f"{name}_CapB", 0.06 * scale, 0.05 * scale, (0, 0, -0.76 * scale), verts=10)
    cap_b.parent = root
    cap_b.data.materials.append(MAT["gold"])
    tas = cylinder(f"{name}_Tassel", 0.025 * scale, 0.18 * scale, (0, 0, -0.90 * scale), verts=6)
    tas.parent = root
    tas.data.materials.append(MAT["lat_tas"])
    return root

hang = []  # (x, y, eave_surface_z) — roots sit just BELOW the tile surface, cords hang down
for sx in (-1, 1):
    for sy in (-1, 1):
        hang.append((sx * (R1_W - 0.55), sy * (R1_W - 0.55),
                     Z_ROOF1 - 0.10 + t1_fn(sx * (R1_W - 0.55), sy * (R1_W - 0.55))))
        hang.append((sx * (R2_W - 0.45), sy * (R2_W - 0.45),
                     T2_BASE - 0.08 + t2_fn(sx * (R2_W - 0.45), sy * (R2_W - 0.45))))
for sy in (-1, 1):                                                                 # tier1 mids front/back
    for kx in (-2, 0, 2):
        hang.append((kx * S / 4.4, sy * (R1_W - 0.55),
                     Z_ROOF1 - 0.10 + t1_fn(kx * S / 4.4, sy * (R1_W - 0.55))))
for sy in (-1, 1):                                                                 # pavilion corner lanterns
    for sx in (-1, 1):
        hang.append((sx * (PAV_HW - 0.05), sy * (PAV_HW - 0.05), YOKE_Z - 0.04))

for idx, hp in enumerate(hang):
    lantern(f"Lantern_{idx + 1:02d}", hp, scale=1.15 if idx % 2 == 0 else 1.0)

# ================================================================ 6. COMPOUND
# Researched layout of Chùa Keo: a walled courtyard; the bell tower stands in a
# courtyard flanked by two long wooden corridor galleries (hành lang) with tile
# roofs, a tam quan gate at the entrance, side halls behind the corridors, and
# brick paving with a stone walkway to the tower steps.

# --- paving
place(box("Courtyard_Paving", (52, 46, 0.10), (0, 0, -PLATFORM_H - 0.05)), "Compound")
place(box("Walkway", (3.2, 24.0, 0.06), (0, PLATFORM_W / 2 + 12.4, -PLATFORM_H - 0.012)), "Compound")

def corridor(cy, tag):
    """hành lang — long open wooden gallery with roof, along X at y=cy."""
    ln, dep, h = 21.0, 2.6, 2.35
    zpl = -PLATFORM_H  # ground level
    place(box(f"{tag}_Base", (ln, dep, 0.30), (0, cy, zpl + 0.15)), "Compound")
    zfl = zpl + 0.30
    n = 12
    for k in range(n):
        x = -ln / 2 + 0.8 + k * ((ln - 1.6) / (n - 1))
        place(cylinder(f"{tag}_Col_{k}_i", 0.10, h, (x, cy + dep / 2 - 0.25, zfl + h / 2), verts=8), "Compound")
        place(cylinder(f"{tag}_Col_{k}_o", 0.10, h, (x, cy - dep / 2 + 0.25, zfl + h / 2), verts=8), "Compound")
    zt = zfl + h
    place(box(f"{tag}_Beam_i", (ln, 0.16, 0.16), (0, cy + dep / 2 - 0.25, zt + 0.08)), "Compound")
    place(box(f"{tag}_Beam_o", (ln, 0.16, 0.16), (0, cy - dep / 2 + 0.25, zt + 0.08)), "Compound")
    # lean-to roof sloping DOWN toward the outside, ridge high on the courtyard side
    s = 1 if cy > 0 else -1
    off = dep / 2 + 0.55
    bm = bmesh.new()
    hi_z, lo_z = zt + 1.05, zt - 0.28
    vts = [bm.verts.new(p) for p in (
        (-ln / 2 - 0.4, cy - s * off, lo_z), (ln / 2 + 0.4, cy - s * off, lo_z),
        (ln / 2 + 0.4, cy + s * off, hi_z), (-ln / 2 - 0.4, cy + s * off, hi_z))]
    bm.faces.new((vts[3], vts[2], vts[1], vts[0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.solidify(bm, thickness=0.12, geom=geom)
    roof = build_mesh(f"{tag}_Roof", bm, (0, 0, 0))
    roof.data.materials.append(MAT["tile"])
    roof.data.materials.append(MAT["wood_ul"])
    shade_smooth(roof)
    place(roof, "Compound")
    # railing slats (simplified: two rails + posts)
    place(box(f"{tag}_Rail_o", (ln - 0.6, 0.08, 0.08), (0, cy - dep / 2 + 0.25, zfl + 0.85)), "Compound")

# corridors flank the tower: inner edges ~10.5 m from centre (tower platform half=5.24)
corridor(-11.6, "Corridor_West")
corridor( 11.6, "Corridor_East")

# --- side halls behind each corridor (đại điện suggestion / nhà tả hữu)
def side_hall(cx, tag, rot=0):
    w, d, h = 9.5, 5.5, 2.6
    zfl = -PLATFORM_H
    place(box(f"{tag}_Base", (w + 0.8, d + 0.8, 0.30), (cx, 0, zfl + 0.15)), "Compound")
    place(box(f"{tag}_Body", (w, d, h), (cx, 0, zfl + 0.30 + h / 2)), "Compound")
    hip = hip_profile(w / 2 + 1.0, 1.25, 0.7)
    roof_shell(f"{tag}_Roof", hip, w / 2 + 1.0, d / 2 + 1.0, zfl + 0.30 + h - 0.06,
               seg_x=8, seg_y=6, thick=0.18)
    obj = bpy.data.objects[f"{tag}_Roof"]
    obj.rotation_euler = (0, 0, radians(rot))

side_hall(-17.5, "SideHall_West")
side_hall( 17.5, "SideHall_East")

# --- tam quan gate at the south end of the walkway
def tam_quan(cy):
    zfl = -PLATFORM_H
    base_w = 7.6
    place(box("Gate_Base", (base_w, 1.6, 0.35), (0, cy, zfl + 0.175)), "Compound")
    # three arched openings suggested by four piers + lintel band
    for k, px in enumerate((-2.7, -0.9, 0.9, 2.7)):
        place(box(f"Gate_Pier_{k}", (0.85, 1.2, 2.5), (px, cy, zfl + 0.35 + 1.25)), "Compound")
    place(box("Gate_Lintel", (base_w, 1.5, 0.55), (0, cy, zfl + 0.35 + 2.5 + 0.275)), "Compound")
    hip = hip_profile(base_w / 2 + 0.75, 1.0, 0.8)
    roof_shell("Gate_Roof", hip, base_w / 2 + 0.75, 1.55, zfl + 0.35 + 2.5 + 0.55 - 0.04,
               seg_x=8, seg_y=4, thick=0.16)
    place(box("Gate_Ridge", (base_w + 0.6, 0.18, 0.12), (0, cy, zfl + 0.35 + 2.5 + 0.55 + 1.0)), "Compound")

tam_quan(23.5)

# --- stone boundary wall (weathered, capstones) around the compound
WALL_X, WALL_Y = 26.0, 23.0
wall_h = 1.15
for sgn in (-1, 1):
    place(box(f"Boundary_Wall_N{sgn}", (WALL_X * 2, 0.42, wall_h), (0, sgn * WALL_Y, -PLATFORM_H + wall_h / 2)), "Compound")
    place(box(f"Boundary_Wall_E{sgn}", (0.42, WALL_Y * 2, wall_h), (sgn * WALL_X, 0, -PLATFORM_H + wall_h / 2)), "Compound")
    place(box(f"Wall_Cap_N{sgn}", (WALL_X * 2, 0.60, 0.12), (0, sgn * WALL_Y, -PLATFORM_H + wall_h + 0.06)), "Compound")
    place(box(f"Wall_Cap_E{sgn}", (0.60, WALL_Y * 2, 0.12), (sgn * WALL_X, 0, -PLATFORM_H + wall_h + 0.06)), "Compound")
# leave a gap in the south wall where the walkway exits: overlay caps still read fine; simple gap:
for o in list(bpy.data.objects):
    if o.name == "Boundary_Wall_N1":
        # split south wall into two segments around walkway (x ±1.9)
        o.name = "Boundary_Wall_S_tmp"
        w0, h0 = o.dimensions.x, o.dimensions.z
        bpy.data.objects.remove(o, do_unlink=True)
        for seg, sgn2 in ((-1, -1), (1, 1)):
            seg_len = (WALL_X - 2.2)
            cx = sgn2 * (2.2 + seg_len / 2)
            place(box(f"Boundary_Wall_S_{sgn2}", (seg_len, 0.42, wall_h), (cx, WALL_Y, -PLATFORM_H + wall_h / 2)), "Compound")
            place(box(f"Wall_Cap_S_{sgn2}", (seg_len, 0.60, 0.12), (cx, WALL_Y, -PLATFORM_H + wall_h + 0.06)), "Compound")

# --- trees (simplified low-poly: trunk + foliage blobs), placed outside corridors
import random
def tree(name, x, y, h=3.2, r=1.4, seed=1):
    rnd = random.Random(seed)
    trunk = cylinder(f"{name}_Trunk", 0.14, h, (x, y, -PLATFORM_H + h / 2), verts=7)
    trunk.data.materials.append(MAT["wood_ul"])
    trunk.rotation_euler = (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 0)
    for k, (dz, sr) in enumerate(((h * 0.62, r), (h * 0.82, r * 0.78), (h * 1.02, r * 0.5))):
        blob = sphere(f"{name}_Foliage_{k}", sr, (x + rnd.uniform(-0.25, 0.25), y + rnd.uniform(-0.25, 0.25), -PLATFORM_H + dz), segs=9, rings=6)
        blob.scale = (1.0, 1.0, 0.8)
        blob.data.materials.append(MAT["leaf"])
        blob.rotation_euler = (0, 0, rnd.uniform(0, 3.14))

for k in range(5):
    tree(f"Tree_N{k}", -19 + k * 6.5, -19.5, h=3.0 + (k % 3) * 0.8, r=1.3 + (k % 2) * 0.4, seed=11 + k)
for k in range(5):
    tree(f"Tree_S{k}", -19 + k * 6.5, 19.5, h=2.8 + (k % 3) * 0.7, r=1.2 + (k % 2) * 0.4, seed=31 + k)
for k in range(3):
    tree(f"Tree_W{k}", -23.0, -10 + k * 10, h=3.4 + (k % 2) * 0.6, r=1.4, seed=51 + k)
for k in range(3):
    tree(f"Tree_E{k}", 23.0, -10 + k * 10, h=3.2 + (k % 2) * 0.7, r=1.3, seed=61 + k)

# ================================================================ 7. MATERIALS ASSIGNMENT
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if o.data.materials and any(o.data.materials):
        continue  # already assigned at creation (roofs, eave bands, lanterns, bells, trees)
    n = o.name
    if n.startswith(("Column", "Lintel", "Gallery", "Interior_Core", "Pavilion_Post", "PavBeam", "PavRail", "Bell_Yoke")):
        o.data.materials.append(MAT["wood"])
    elif n.startswith("Stone"):
        o.data.materials.append(MAT["stone"])
    elif n.startswith("Door_Upper"):
        o.data.materials.append(pbr("Pagoda_Door_Red", (0.38, 0.05, 0.04), rough=0.7))
    elif n.startswith(("Balcony", "GroundRail", "Door")):
        o.data.materials.append(MAT["wood"])
    elif ("_Base" in n or n.startswith(("Boundary_Wall", "Wall_Cap", "Courtyard_Paving",
                                        "Walkway", "Gate_Base"))):
        o.data.materials.append(MAT["stone"])
    elif n.startswith(("Corridor_", "SideHall_", "Gate_")) or "_Body" in n:
        o.data.materials.append(MAT["wood"])
    elif n.startswith(("Tree_", "WindBell_", "Bronze_", "Bell_")):
        pass  # per-part materials already set
    elif n.startswith("CornerOrn"):
        o.data.materials.append(MAT["tile"])
    elif n.startswith(("Ridge", "Finial")):
        o.data.materials.append(MAT["gold"] if "Finial" in n else MAT["wood_ul"])
    elif n.startswith("Lantern"):
        pass  # per-part materials already set

# ================================================================ 8. ENVIRONMENT
place(box("Ground_Plane", (90, 90, 0.1), (0, 0, -PLATFORM_H - 0.051)), "Environment")
gp = bpy.data.objects["Ground_Plane"]

def ground_mat():
    """Fired-brick courtyard paving — the real complex is paved with bricks."""
    existing = bpy.data.materials.get("Env_Ground_Brick")
    if existing:
        return existing
    mat = bpy.data.materials.new("Env_Ground_Brick")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    uv = _obj_uv(nt)
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 0.30
    brick.inputs["Row Height"].default_value = 0.15
    brick.inputs["Mortar Size"].default_value = 0.010
    brick.inputs["Color1"].default_value = (0.235, 0.115, 0.062, 1.0)
    brick.inputs["Color2"].default_value = (0.165, 0.080, 0.042, 1.0)
    brick.inputs["Mortar"].default_value = (0.115, 0.062, 0.038, 1.0)
    nt.links.new(uv, brick.inputs["Vector"])
    wcol, wf = _weathering(nt, strength=0.45, lo=0.70, hi=1.15)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = wf
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(wcol, mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = 0.08
    nt.links.new(brick.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.92
    return mat

gp.data.materials.append(ground_mat())

world = bpy.data.worlds.new("Sky_World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.42, 0.60, 0.85, 1.0)
bg.inputs[1].default_value = 1.15

# ================================================================ 9. LIGHTING
sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 5.5
sun.data.angle = radians(2.0)
sun.data.color = (1.0, 0.95, 0.86)
# sun shines from the hero-camera side so visible roof slopes are lit
sun_dir = V((-cos(radians(48)) * cos(radians(-40)),
             -cos(radians(48)) * sin(radians(-40)),
             -sin(radians(48))))
sun.rotation_euler = sun_dir.to_track_quat('-Z', 'Y').to_euler()
place(sun, "Lighting")

fill = bpy.data.objects.new("Fill_Sky", bpy.data.lights.new("Fill_Sky", 'AREA'))
fill.data.energy = 550
fill.data.size = 12
fill.data.color = (0.85, 0.90, 1.0)
fill.location = (-8, -7, 7)
fill.rotation_euler = Euler((radians(48), 0, radians(38)))
place(fill, "Lighting")

# ================================================================ 10. CAMERAS
def camera(name, loc, look_at, lens=36):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.location = loc
    direction = V(look_at) - V(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 300
    place(cam, "Cameras")
    return cam

TOP_Z = Z_ROOF2_TOP + R3_H + 0.9
cam_a = camera("Camera_Hero", (22.5, -21.0, 7.4), (0, 0, TOP_Z * 0.53), 36)
cam_b = camera("Camera_ThreeQuarter", (16.5, 13.0, 7.6), (0, 0, TOP_Z * 0.46), 36)
cam_c = camera("Camera_Eaves", (10.0, -9.0, 9.6), (0.8, 0.8, Z_ROOF1 + 1.8), 44)
cam_d = camera("Camera_Courtyard", (22.5, -21.5, 7.2), (-2, 2, TOP_Z * 0.30), 33)

# ================================================================ 11. ANIMATION
scene.frame_start = 1
scene.frame_end = 192
lantern_roots = [o for o in bpy.data.objects if o.name.startswith("Lantern_") and o.type == 'EMPTY']
for i, root in enumerate(lantern_roots):
    ph = (i * 0.9) % (2 * pi)
    root.rotation_euler.y = 0.22 * sin(ph)
    root.rotation_euler.x = 0.08 * sin(ph * 1.7)
    root.keyframe_insert("rotation_euler", frame=1)
    root.rotation_euler.y = 0.22 * sin(ph + pi)
    root.rotation_euler.x = 0.08 * sin(ph * 1.7 + pi)
    root.keyframe_insert("rotation_euler", frame=96)
    root.rotation_euler.y = 0.22 * sin(ph)
    root.rotation_euler.x = 0.08 * sin(ph * 1.7)
    root.keyframe_insert("rotation_euler", frame=192)

origin = V((0, 0, TOP_Z * 0.44))
cam_a.rotation_mode = 'QUATERNION'
for f in range(1, 193, 24):
    ang = radians(210 + (f - 1) / 191 * 120)
    cam_a.location = (origin.x + 17.5 * cos(ang), origin.y + 17.5 * sin(ang), 5.4)
    d = origin - V(cam_a.location)
    cam_a.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    cam_a.keyframe_insert("location", frame=f)
    cam_a.keyframe_insert("rotation_quaternion", frame=f)
for fc in cam_a.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

# ================================================================ 12. RENDER SETTINGS
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.eevee.taa_render_samples = 48
if hasattr(scene.eevee, "use_raytracing"):
    scene.eevee.use_raytracing = True
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
except Exception:
    scene.view_settings.view_transform = 'AgX'

# ================================================================ 13. VIEWPORT DISPLAY
# Make the .blend open showing COLORS, not grey solid-mode clay:
# all 3D viewports start in Material Preview with scene lights/world,
# and the Layout workspace starts framed on the hero camera.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for space in area.spaces:
            if space.type != 'VIEW_3D':
                continue
            space.shading.type = 'MATERIAL'
            space.shading.use_scene_lights = True
            space.shading.use_scene_world = True
            space.shading.color_type = 'MATERIAL'
            if screen.name == "Layout":
                space.region_3d.view_perspective = 'CAMERA'

# ================================================================ 13b. VISITORS (pilgrims + tourists)
if "Visitors" not in COL:
    COL["Visitors"] = bpy.data.collections.new("Visitors")
    scene.collection.children.link(COL["Visitors"])

# visitors_module places feet at z=0; the courtyard paving sits at -PLATFORM_H
# so we offset the whole group after creation via an empty parent shift: simplest
# is to pass positions already in world space and lift each object after.
visitor_specs = [
    # courtyard: pilgrims admiring the tower
    (-4.0, -9.0, 15, 'family'), (4.2, -11.0, 165, 'couple'),
    (-1.5, -6.0, 170, 'photographer'), (6.5, -6.5, 200, 'adult'),
    (-6.8, -3.0, 40, 'couple'),
    # walkway to the tower: stream of visitors
    (0.6, -14.0, 5, 'adult'), (-0.5, -17.0, 3, 'couple'),
    (0.5, -20.0, 175, 'family'), (-0.4, -23.0, 178, 'photographer'),
    # kids chasing each other on the plaza
    (-9.0, -13.0, -30, 'kid'), (-10.5, -10.5, 120, 'kid'), (9.8, -14.5, 60, 'kid'),
    (11.0, -11.5, -90, 'kid'),
    # monks crossing the courtyard
    (-7.5, 2.0, 100, 'monk'), (-8.3, 4.6, 95, 'monk'), (-9.0, 7.2, 92, 'monk'),
    # side hall visitors
    (-14.0, 3.0, 80, 'adult'), (14.5, 1.5, -80, 'photographer'),
    (13.0, -2.0, -60, 'kid'),
]
_pbr_keo = pbr
_mats_keo = MAT
visitors = add_visitors(bpy, V, box, cylinder, sphere, place, _pbr_keo, _mats_keo,
                        visitor_specs, col="Visitors", seed=42)
for o in visitors:
    o.location.z -= PLATFORM_H   # courtyard surface is below z=0

# ================================================================ 14. SAVE + RENDER
os.makedirs(RENDER_DIR, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("SAVED_BLEND:", BLEND_PATH)

if "--render-only" not in sys.argv:
    for cam, tag in ((cam_a, "hero"), (cam_b, "three_quarter"), (cam_c, "eaves"), (cam_d, "courtyard")):
        scene.camera = cam
        scene.render.filepath = os.path.join(RENDER_DIR, f"preview_{tag}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDER_DONE:", tag)

tris = 0
for o in bpy.data.objects:
    if o.type == 'MESH':
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
print("TRIANGLE_COUNT:", tris)
print("MESH_OBJECTS:", sum(1 for o in bpy.data.objects if o.type == 'MESH'))
print("TOTAL_HEIGHT_M:", round(TOP_Z, 2))
print("BUILD_OK")
