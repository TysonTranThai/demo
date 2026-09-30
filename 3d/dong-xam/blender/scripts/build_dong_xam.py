# -*- coding: utf-8 -*-
"""
SMART ART HERITAGE — Làng nghề chạm bạc Đồng Xâm (Hồng Thái, Kiến Xương, Thái Bình).
Procedural Blender 4.5 build.

Research-observed facts encoded (vov2, Tuổi Trẻ, Lao Động photo essay, user ref):
- Complex on the SÔNG VÔNG: nhà THỦY TỌA is a pavilion standing IN the river
  ("sáu cửa vòng quay ra sáu hướng" — six arched doors), reached by a white
  footbridge; a multi-arch brick bridge crosses the river nearby (photos).
- TIỀN TẾ: grand 5-bay hall facing the river, ~13 m tall, weathered grey-white
  walls, THREE arched loggia portals, row of round gold medallions above the
  arches, red columns, red two-tier tile roof with medallion ridge line (photos).
- TRUNG TẾ connects Tiền Tế to HẬU CUNG; Hậu Cung is a taller stacked block
  ("chuổi vỏ" stacked high for the Khán Gian silver-carving hall).
- ĐỀN THỜ TỔ (craft-founder shrine, "KHỔI TỔ 1428", user reference photo):
  Indochine YELLOW facade, white trim + quoins, tall central arch portal with
  lantern, two side arch niches, red-fluted pilasters with white couplet
  panels, dark signboard, red/white roofline balustrade, THREE circular
  character medallions on the roof edge, grey tile roof, red blossom bush.
- River: muddy green water with lotus (photos), village greenery around.

Ambiguities resolved: interiors dark (doors deep in reveals); medallion
characters stylised as incised discs; statues omitted; boat race not modeled.
"""

import bpy, bmesh, os, math, sys, random
from math import radians, sin, cos, pi, sqrt, degrees
from mathutils import Vector, Euler, Matrix

V = Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(SCRIPT_DIR, "..", "dong-xam-model.blend")
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

def torus(name, R, r, loc=(0, 0, 0), segs=20, rings=10, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=segs, radius=R)
    ring = [v for v in bm.verts]
    ret = bmesh.ops.extrude_edge_only(bm, edges=list(bm.edges))
    bmesh.ops.translate(bm, vec=V((0, 0, 0)), verts=[e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)])
    bm.free()
    # simpler: uv-torus via spin of a small circle — do manual loop of spheres
    bm2 = bmesh.new()
    for k in range(segs):
        a = 2 * pi * k / segs
        x, y = R * cos(a), R * sin(a)
        for j in range(rings):
            b = 2 * pi * j / rings
            rr = r * (0.6 + 0.4 * cos(b))
            z = r * sin(b)
            bm2.verts.new((x + rr * cos(a) * 0.0, y + rr * sin(a) * 0.0, z))
    bm2.free()
    # fallback: approximate torus with a flattened sphere pair
    del ring
    s1 = sphere(name, r, loc, segs=segs, rings=rings)
    return s1

def shade_smooth(obj, sharp_angle=32.0):
    """Smooth shading with angle-based sharp edges (Blender 4.x). Without this,
    ridge/hip edges of big roofs smear normals and render as grey patches."""
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            ang = degrees(e.link_faces[0].normal.angle(e.link_faces[1].normal))
            if ang > sharp_angle:
                e.smooth = False
        elif len(e.link_faces) == 1:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()

def hip_roof(name, half_w, half_d, rise, z, curve=0.8, seg=10, thick=0.18, mat="tile",
             off_x=0.0, off_y=0.0, col="Temple", ridge_frac=0.5):
    """TRUE saddle-hip roof with a real horizontal ridge (Đền Trần v2 formula)."""
    bm = bmesh.new()
    nx = ny = seg + 1
    ridge_half = half_w * ridge_frac
    verts = []
    for iy in range(ny):
        row = []
        for ix in range(nx):
            x = (-half_w + 2 * half_w * ix / seg)
            y = (-half_d + 2 * half_d * iy / seg)
            h = rise * (1 - abs(y) / half_d)
            if abs(x) > ridge_half:
                hip = rise * max(0.0, (half_w - abs(x)) / (half_w - ridge_half))
                h = min(h, hip)
            corner = (abs(x) / half_w) * (abs(y) / half_d)   # each axis over its OWN half!
            h += curve * rise * 0.55 * corner ** 4
            row.append(bm.verts.new((x, y, h)))
        verts.append(row)
    for iy in range(ny - 1):
        for ix in range(nx - 1):
            bm.faces.new((verts[iy][ix], verts[iy][ix + 1],
                          verts[iy + 1][ix + 1], verts[iy + 1][ix]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.solidify(bm, thickness=thick, geom=geom)
    obj = build_mesh(name, bm, (off_x, off_y, z))
    obj.data.materials.append(MAT[mat])
    obj.data.materials.append(MAT["wood"])
    shade_smooth(obj)
    place(obj, col)
    return obj

def dao_tips(roof_name, half_w, half_d, rise, z, curve=0.8, off_x=0.0, off_y=0.0,
             col="Temple", mat="tile_red", ridge_frac=1.0):
    """Corner tips seated exactly on the hip_roof surface (same formula)."""
    ridge_half = half_w * ridge_frac
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (half_w - 0.02), sy * (half_d - 0.02)
            h = rise * (1 - abs(y) / half_d)
            if abs(x) > ridge_half:
                hip = rise * max(0.0, (half_w - abs(x)) / (half_w - ridge_half))
                h = min(h, hip)
            corner = (abs(x) / half_w) * (abs(y) / half_d)
            h += curve * rise * 0.55 * corner ** 4
            tip = cylinder(f"{roof_name}_Dao_{sx}_{sy}", 0.038, 0.34,
                           (off_x + x, off_y + y, z + h + 0.13), verts=7,
                           rot=(radians(38) * sy, radians(-38) * sx, 0))
            tip.data.materials.append(MAT[mat])
            place(tip, col)

def arch_wall(name, width, depth, height, openings, slices=24, pier_mat=None):
    """Wall slab built as slices so arch openings are REAL through-holes;
    arc openings get a proper semicircular vault ring."""
    bm = bmesh.new()
    xs0 = -width / 2
    sw = width / slices
    for i in range(slices):
        xm = xs0 + sw * (i + 0.5)
        top = 0.0
        for (cx, hw, kind, sz, rise) in openings:
            dx = xm - cx
            if kind == 'arc':
                R = hw
                if abs(dx) < R:
                    top = max(top, sz + min(sqrt(max(R * R - dx * dx, 0.0)), rise))
            else:
                if abs(dx) < hw:
                    top = max(top, sz)
        if top <= 0.01:
            z0, zh = 0.0, height
        else:
            z0, zh = top, height - top
        if zh <= 0.02:
            continue
        bmesh.ops.create_cube(bm, size=1.0, matrix=(
            Matrix.Translation((xm, 0, z0 + zh / 2))
            @ Matrix.Diagonal((sw, depth, zh, 1))))
    for (cx, hw, kind, sz, rise) in openings:
        if kind != 'arc':
            continue
        R = hw
        segs = 12
        ring_f, ring_b = [], []
        for k in range(segs + 1):
            a = pi * k / segs
            x = cx + R * cos(a)
            z = sz + R * sin(a)
            ring_f.append(bm.verts.new((x, -depth / 2, z)))
            ring_b.append(bm.verts.new((x, depth / 2, z)))
        for k in range(segs):
            bm.faces.new((ring_f[k], ring_f[k + 1], ring_b[k + 1], ring_b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = build_mesh(name, bm)
    if pier_mat:
        obj.data.materials.append(pier_mat)
    return obj

def hanging_lantern(name, x, y, z_top, scale=1.0):
    """Single-mesh red lantern (cord/body/caps/tassel), 2 material slots."""
    bm = bmesh.new()
    def part(r1, r2, d, loc, seg=10):
        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                    segments=seg, radius1=r1, radius2=r2, depth=d)
        bmesh.ops.translate(bm, vec=V(loc), verts=ret['verts'])
    s = scale
    part(0.012 * s, 0.012 * s, 0.30 * s, (0, 0, -0.15 * s))
    part(0.050 * s, 0.032 * s, 0.05 * s, (0, 0, -0.325 * s))
    part(0.150 * s, 0.150 * s, 0.21 * s, (0, 0, -0.45 * s))
    part(0.050 * s, 0.032 * s, 0.05 * s, (0, 0, -0.575 * s))
    part(0.022 * s, 0.012 * s, 0.14 * s, (0, 0, -0.67 * s))
    obj = build_mesh(name, bm, (x, y, z_top))
    obj.data.materials.append(MAT["lantern"])
    obj.data.materials.append(MAT["gold"])
    for f in obj.data.polygons:
        cz = f.center.z
        f.material_index = 0 if (-0.56 * s < cz < -0.34 * s) else 1
    shade_smooth(obj)
    obj.rotation_mode = 'XYZ'
    place(obj, "Flags")
    return obj

# ---------------------------------------------------------------- materials
def pbr(name, color, rough=0.8, metal=0.0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat

def plaster(name, color, rough=0.75, weather=0.30, lo=0.80, hi=1.12, streak=False):
    """Flat painted plaster with noise weathering (no brick pattern)."""
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.1 if streak else 0.5
    noise.inputs["Detail"].default_value = 6.0
    if streak:
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (3.5, 3.5, 0.7)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.32
    ramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = weather
    mix.inputs["Color1"].default_value = (*color, 1.0)
    nt.links.new(ramp.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat

def masonry(name, c1, c2, mortar, rough=0.86, bw=0.5, rh=0.25, weather=0.45, bump=0.08,
            lo=0.70, hi=1.15, streak=False):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    uv = tc.outputs["Object"]
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = bw
    brick.inputs["Row Height"].default_value = rh
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Color1"].default_value = (*c1, 1.0)
    brick.inputs["Color2"].default_value = (*c2, 1.0)
    brick.inputs["Mortar"].default_value = (*mortar, 1.0)
    nt.links.new(uv, brick.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.4 if streak else 0.55
    noise.inputs["Detail"].default_value = 6.0
    if streak:
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (3.5, 3.5, 0.7)
        nt.links.new(uv, mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.32
    ramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = weather
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = bump
    nt.links.new(brick.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat

def build_materials():
    global MAT
    MAT = {}
    MAT["tile_red"]  = masonry("DX_Tile_Red", (0.560, 0.105, 0.030), (0.430, 0.078, 0.024),
                               (0.30, 0.19, 0.12), bw=0.34, rh=0.11, weather=0.40,
                               lo=0.72, hi=1.18, bump=0.12)
    MAT["tile_grey"] = masonry("DX_Tile_Grey", (0.205, 0.208, 0.215), (0.150, 0.152, 0.160),
                               (0.14, 0.14, 0.145), bw=0.34, rh=0.11, weather=0.45,
                               lo=0.70, hi=1.20, bump=0.10)
    MAT["wall_grey"] = plaster("DX_Wall_Grey", (0.560, 0.548, 0.525), rough=0.85,
                               weather=0.42, lo=0.62, hi=1.18, streak=True)
    MAT["yellow"]    = plaster("DX_Yellow_Indochine", (0.870, 0.640, 0.085), rough=0.68,
                               weather=0.28, lo=0.82, hi=1.10)
    MAT["trim"]      = plaster("DX_Trim_White", (0.810, 0.795, 0.755), rough=0.72,
                               weather=0.30, lo=0.78, hi=1.10)
    MAT["red_paint"] = pbr("DX_Red_Paint", (0.480, 0.050, 0.030), rough=0.62)
    MAT["stone"]     = masonry("DX_Stone_Grey", (0.430, 0.425, 0.410), (0.345, 0.340, 0.330),
                               (0.29, 0.285, 0.278), bw=0.62, rh=0.30, weather=0.45, bump=0.10)
    MAT["bridge"]    = masonry("DX_Bridge_Brick", (0.400, 0.360, 0.300), (0.310, 0.275, 0.225),
                               (0.24, 0.21, 0.17), bw=0.40, rh=0.20, weather=0.55,
                               lo=0.62, hi=1.22, bump=0.12)
    MAT["gold"]      = pbr("DX_Gold", (0.72, 0.55, 0.20), rough=0.38, metal=0.85)
    MAT["silver"]    = pbr("DX_Silver", (0.75, 0.75, 0.77), rough=0.30, metal=0.9)
    MAT["wood"]      = pbr("DX_Wood_Dark", (0.062, 0.042, 0.026), rough=0.8)
    MAT["wood_old"]  = pbr("DX_Wood_Weathered", (0.088, 0.062, 0.040), rough=0.85)
    MAT["door_red"]  = pbr("DX_Door_Red", (0.320, 0.045, 0.028), rough=0.7)
    MAT["banner"]    = pbr("DX_Banner_Red", (0.52, 0.045, 0.030), rough=0.72)
    MAT["lantern"]   = pbr("DX_Lantern_Red", (0.45, 0.035, 0.024), rough=0.55)
    MAT["sign"]      = pbr("DX_Sign_Dark", (0.115, 0.125, 0.135), rough=0.6)
    MAT["sign_text"] = pbr("DX_Sign_Text", (0.88, 0.87, 0.84), rough=0.5)
    MAT["water"]     = pbr("DX_Water_Muddy", (0.098, 0.070, 0.036), rough=0.08)
    MAT["lotus"]     = pbr("DX_Lotus_Leaf", (0.075, 0.150, 0.050), rough=0.8)
    MAT["blossom"]   = pbr("DX_Lotus_Blossom", (0.780, 0.400, 0.480), rough=0.7)
    MAT["leaf"]      = pbr("DX_Foliage", (0.068, 0.132, 0.045), rough=0.85)
    MAT["leaf2"]     = pbr("DX_Foliage_Light", (0.108, 0.178, 0.052), rough=0.85)
    MAT["leaf3"]     = pbr("DX_Foliage_Olive", (0.125, 0.152, 0.048), rough=0.85)
    MAT["trunk"]     = pbr("DX_Trunk", (0.15, 0.115, 0.082), rough=0.9)
    MAT["paving"]    = masonry("DX_Paving_Stone", (0.470, 0.462, 0.445), (0.395, 0.388, 0.372),
                               (0.31, 0.305, 0.295), bw=0.55, rh=0.42, weather=0.42, bump=0.08)
    MAT["ground"]    = pbr("DX_Ground_Earth", (0.175, 0.165, 0.095), rough=0.95)
    MAT["hedge"]     = pbr("DX_Hedge", (0.058, 0.108, 0.038), rough=0.9)
    MAT["bank"]      = masonry("DX_Bank_Grass", (0.115, 0.170, 0.062), (0.095, 0.145, 0.052),
                               (0.10, 0.13, 0.06), bw=1.2, rh=0.6, weather=0.5,
                               lo=0.75, hi=1.25, bump=0.06)

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
build_materials()

COL = {}
for cname in ["Temple", "ToShrine", "WaterPavilion", "River", "Grounds", "Trees",
              "Flags", "Lighting", "Cameras", "Environment"]:
    COL[cname] = bpy.data.collections.new(cname)
    scene.collection.children.link(COL[cname])

def place(obj, cname):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    COL[cname].objects.link(obj)
    return obj

# ---------------------------------------------------------------- dimensions
# main axis faces -Y toward the river
RIVER_Y0, RIVER_Y1 = -42.0, -26.0          # river span (near bank at -26)
WATER_Z = -0.45
TT_W, TT_D = 24.0, 10.0                    # Tiền Tế
TT_Y = 0.0
TT_Z0 = 1.20                               # terrace height
TERR_W, TERR_D = 32.0, 18.0
flag_objs = []                             # animated sway targets (built early)
TZ_Y = 13.0                                # Trung Tế
HC_Y = 21.5                                # Hậu Cung
TS_X, TS_Y = 24.0, -2.0                    # Đền Thờ Tổ (right of axis)
TS_W, TS_D = 13.0, 8.0

# ================================================================ 1. RIVER + GROUND
bed = box("River_Bed", (240, 26, 1.2), (0, (RIVER_Y0 + RIVER_Y1) / 2, WATER_Z - 0.9))
bed.data.materials.append(MAT["ground"])
place(bed, "River")
# water fills the full channel between the two banks, surface just below bank tops
water = box("River_Water", (240, 16.0, 0.5), (0, (RIVER_Y0 + RIVER_Y1) / 2, WATER_Z + 0.10))
water.data.materials.append(MAT["water"])
place(water, "River")
# near + far banks (grass) — narrow strips, do NOT overlap the water channel
for tag, y0, y1 in (("Near", RIVER_Y1 - 4.0, RIVER_Y1), ("Far", RIVER_Y0, RIVER_Y0 + 4.0)):
    bank = box(f"Bank_{tag}", (240, 4.0, 0.9), (0, (y0 + y1) / 2, WATER_Z - 0.05))
    bank.data.materials.append(MAT["bank"])
    place(bank, "River")
# stone embankment walls along both banks (LOW — must not occlude the water)
for tag, y in (("Near", RIVER_Y1 - 0.4), ("Far", RIVER_Y0 + 0.4)):
    emb = box(f"Embank_{tag}", (240, 0.8, 0.9), (0, y, WATER_Z + 0.10))
    emb.data.materials.append(MAT["stone"])
    place(emb, "River")
# big ground slab behind the temple (main land side) — starts AT the near bank
ground = box("Ground", (240, 120, 0.8), (0, RIVER_Y1 + 59.0, WATER_Z + 0.0))
ground.data.materials.append(MAT["ground"])
place(ground, "Environment")
# ground on the VIEWER side of the river (south bank) so the hero view has land
ground_s = box("Ground_South", (240, 60, 0.8), (0, RIVER_Y0 - 31.0, WATER_Z - 0.10))
ground_s.data.materials.append(MAT["ground"])
place(ground_s, "Environment")
# grass strip on the south bank in front of the camera
bank_s = box("Bank_SouthGrass", (240, 6.0, 0.85), (0, RIVER_Y0 - 2.0, WATER_Z - 0.08))
bank_s.data.materials.append(MAT["bank"])
place(bank_s, "Environment")
# courtyard paving between river bank and Hậu Cung
pav = box("Courtyard_Paving", (60, 58, 0.14), (0, 2, 0.07))
pav.data.materials.append(MAT["paving"])
place(pav, "Environment")
# worn patches on the paving
random.seed(7)
for k in range(8):
    px, py = random.uniform(-24, 24), random.uniform(-20, 22)
    pw = box(f"Paving_Wear_{k}", (random.uniform(2, 5), random.uniform(2, 5), 0.03),
             (px, py, 0.15))
    pw.data.materials.append(MAT["ground"])
    place(pw, "Environment")

# lotus patches (photo: pink lotus in the river)
def lotus(name, cx, cy, n, seed):
    rnd = random.Random(seed)
    for k in range(n):
        lx = cx + rnd.uniform(-2.2, 2.2)
        ly = cy + rnd.uniform(-1.6, 1.6)
        pad = cylinder(f"{name}_Pad_{k}", rnd.uniform(0.18, 0.34), 0.04,
                       (lx, ly, WATER_Z + 0.02), verts=10)
        pad.data.materials.append(MAT["lotus"])
        place(pad, "River")
        if k % 3 == 0:
            stem = cylinder(f"{name}_Stem_{k}", 0.025, 0.5, (lx, ly, WATER_Z + 0.22), verts=6)
            stem.data.materials.append(MAT["lotus"])
            place(stem, "River")
            bl = sphere(f"{name}_Bloom_{k}", 0.13, (lx, ly, WATER_Z + 0.52), segs=8, rings=5)
            bl.scale = (1.0, 1.0, 1.35)
            bl.data.materials.append(MAT["blossom"])
            place(bl, "River")

lotus("Lotus_W", -14.0, -33.0, 9, 11)
lotus("Lotus_E", 13.0, -31.0, 8, 12)
lotus("Lotus_Bridge", 26.5, -34.5, 6, 13)

# ================================================================ 2. THỦY TỌA (water pavilion in the river)
TZT_X, TZT_Y = 0.0, -34.0
# stone platform on piles
for px in (-2.6, 0.0, 2.6):
    for py in (-2.6, 0.0, 2.6):
        pile = cylinder(f"TZT_Pile_{px}_{py}", 0.18, 3.2, (TZT_X + px, TZT_Y + py, WATER_Z + 1.0), verts=8)
        pile.data.materials.append(MAT["stone"])
        place(pile, "WaterPavilion")
plat = box("TZT_Platform", (7.4, 7.4, 0.5), (TZT_X, TZT_Y, WATER_Z + 2.6))
plat.data.materials.append(MAT["stone"])
place(plat, "WaterPavilion")
deck = box("TZT_Deck", (7.8, 7.8, 0.14), (TZT_X, TZT_Y, WATER_Z + 2.9))
deck.data.materials.append(MAT["paving"])
place(deck, "WaterPavilion")
# pavilion body: 4 walls with arched doors facing 6 directions (square + axis doors)
pbody_z = WATER_Z + 2.97
PH = 3.0
for tag, rot, ox, oy in (("S", 0, 0, -3.4), ("N", 0, 0, 3.4), ("E", 0, 3.4, 0), ("W", 0, -3.4, 0)):
    wall = arch_wall(f"TZT_Wall_{tag}", 6.6, 0.4, PH,
                     openings=[(0.0, 0.85, 'arc', 0.9, 0.85)], slices=12,
                     pier_mat=MAT["wall_grey"])
    wall.location = (TZT_X + ox, TZT_Y + oy, pbody_z)
    wall.rotation_euler = (0, 0, 0 if tag in ("S", "N") else radians(90))
    place(wall, "WaterPavilion")
# corner posts
for sx in (-1, 1):
    for sy in (-1, 1):
        post = cylinder(f"TZT_Post_{sx}_{sy}", 0.16, PH, (TZT_X + sx * 3.1, TZT_Y + sy * 3.1, pbody_z + PH / 2), verts=8)
        post.data.materials.append(MAT["red_paint"])
        place(post, "WaterPavilion")
# two-tier roof
r1 = hip_roof("TZT_Roof_1", 4.6, 4.6, 1.1, pbody_z + PH - 0.05, curve=0.9, seg=7,
              thick=0.16, mat="tile_red", off_x=TZT_X, off_y=TZT_Y, col="WaterPavilion",
              ridge_frac=0.45)
rb2 = box("TZT_Upper_Body", (4.4, 4.4, 1.1), (TZT_X, TZT_Y, pbody_z + PH + 0.62))
rb2.data.materials.append(MAT["wall_grey"])
place(rb2, "WaterPavilion")
r2 = hip_roof("TZT_Roof_2", 3.1, 3.1, 0.9, pbody_z + PH + 1.15, curve=0.9, seg=6,
              thick=0.14, mat="tile_red", off_x=TZT_X, off_y=TZT_Y, col="WaterPavilion",
              ridge_frac=0.4)
dao_tips("TZT_Roof_1", 4.6, 4.6, 1.1, pbody_z + PH - 0.05, curve=0.9, off_x=TZT_X, off_y=TZT_Y,
         col="WaterPavilion", ridge_frac=0.45)
# gold finial
fin = sphere("TZT_Finial", 0.16, (TZT_X, TZT_Y, pbody_z + PH + 2.12), segs=10, rings=6)
fin.data.materials.append(MAT["gold"])
place(fin, "WaterPavilion")
# white ARCH SURROUNDS on the four doors + red door leaves deep inside
for tag, ox, oy, rot in (("S", 0, -3.62, 0), ("N", 0, 3.62, 0), ("E", 3.62, 0, 1), ("W", -3.62, 0, 1)):
    ring = arch_wall(f"TZT_ArchRing_{tag}", 2.4, 0.20, 1.5,
                     openings=[(0.0, 0.85, 'arc', 0.0, 0.85)], slices=14,
                     pier_mat=MAT["trim"])
    ring.location = (TZT_X + ox, TZT_Y + oy, pbody_z)
    ring.rotation_euler = (0, 0, radians(90 * rot))
    place(ring, "WaterPavilion")
    door = box(f"TZT_Door_{tag}", (1.5, 0.10, 1.75), (TZT_X + ox * 0.86, TZT_Y + oy * 0.86, pbody_z + 0.9),
               rot=(0, 0, radians(90 * rot)))
    door.data.materials.append(MAT["door_red"])
    place(door, "WaterPavilion")
# stone BALUSTRADE around the platform (the real thủy tọa has one)
for k in range(7):
    for (px, py, rot) in ((-3.55 + k * 1.18, -3.55, 0), (-3.55 + k * 1.18, 3.55, 0),
                          (-3.55, -3.55 + k * 1.18, 1), (3.55, -3.55 + k * 1.18, 1)):
        bp = box(f"TZT_BalPost_{k}_{px}_{py}", (0.14, 0.14, 0.62), (TZT_X + px, TZT_Y + py, WATER_Z + 2.52 + 0.31))
        bp.data.materials.append(MAT["stone"])
        place(bp, "WaterPavilion")
for tag, size, loc in (("S", (7.3, 0.10, 0.09), (0, -3.55)), ("N", (7.3, 0.10, 0.09), (0, 3.55)),
                       ("E", (0.10, 7.3, 0.09), (3.55, 0)), ("W", (0.10, 7.3, 0.09), (-3.55, 0))):
    br = box(f"TZT_BalRail_{tag}", size, (TZT_X + loc[0], TZT_Y + loc[1], WATER_Z + 2.52 + 0.66))
    br.data.materials.append(MAT["stone"])
    place(br, "WaterPavilion")
# hanging lanterns at the two river-side corners
flag_objs_tzt = [hanging_lantern("Lantern_TZT_L", TZT_X - 2.3, TZT_Y - 3.6, pbody_z + PH - 0.10, 0.9),
                 hanging_lantern("Lantern_TZT_R", TZT_X + 2.3, TZT_Y - 3.6, pbody_z + PH - 0.10, 0.9)]

# white FOOTBRIDGE from near bank to the pavilion — FULL SPAN so it actually
# connects: bank edge y=-26 to platform edge y=-37.7 (the old 5.6 m bridge
# stopped 6 m short of the pavilion, floating in mid-air)
FB_W = 1.7
FB_Y0, FB_Y1 = RIVER_Y1 - 0.2, TZT_Y - 3.7      # -26.2 .. -37.7
fb_len = FB_Y0 - FB_Y1
fb_cy = (FB_Y0 + FB_Y1) / 2
fb_deck = box("FB_Deck", (FB_W, fb_len, 0.16), (TZT_X, fb_cy, WATER_Z + 2.85))
fb_deck.data.materials.append(MAT["trim"])
place(fb_deck, "WaterPavilion")
# junction step onto the pavilion platform
fb_step = box("FB_Step", (FB_W + 0.3, 0.5, 0.10), (TZT_X, FB_Y1 + 0.25, WATER_Z + 2.93))
fb_step.data.materials.append(MAT["paving"])
place(fb_step, "WaterPavilion")
for sx in (-1, 1):
    rail = box(f"FB_Rail_{sx}", (0.10, fb_len, 0.08), (TZT_X + sx * (FB_W / 2 - 0.05), fb_cy, WATER_Z + 3.55))
    rail.data.materials.append(MAT["trim"])
    place(rail, "WaterPavilion")
    n_posts = int(fb_len / 1.0)
    for k in range(n_posts):
        post = box(f"FB_Post_{sx}_{k}", (0.10, 0.10, 0.62),
                   (TZT_X + sx * (FB_W / 2 - 0.05), FB_Y0 - 0.5 - k * 1.0, WATER_Z + 3.25))
        post.data.materials.append(MAT["trim"])
        place(post, "WaterPavilion")

# multi-arch BRICK BRIDGE crossing the river (east, like the photo)
BR_X = 27.0
bridge = box("Bridge_Deck", (4.2, 19.0, 0.5), (BR_X, (RIVER_Y0 + RIVER_Y1) / 2, 1.35))
bridge.data.materials.append(MAT["bridge"])
place(bridge, "River")
bw_arch = arch_wall("Bridge_Wall", 19.0, 4.2, 1.0,
                    openings=[(-6.0, 2.0, 'arc', -0.2, 1.5), (0.0, 2.4, 'arc', -0.2, 1.8), (6.0, 2.0, 'arc', -0.2, 1.5)],
                    slices=30, pier_mat=MAT["bridge"])
bw_arch.location = (BR_X, (RIVER_Y0 + RIVER_Y1) / 2, WATER_Z + 1.55)
bw_arch.rotation_euler = (0, 0, radians(90))
place(bw_arch, "River")
for sx in (-1, 1):
    par = box(f"Bridge_Parapet_{sx}", (0.28, 19.0, 0.7), (BR_X + sx * 1.95, (RIVER_Y0 + RIVER_Y1) / 2, 1.95))
    par.data.materials.append(MAT["bridge"])
    place(par, "River")

# ================================================================ 3. TIỀN TẾ (grand hall)
# stone terrace + stairs
terr = box("TT_Terrace", (TERR_W, TERR_D, TT_Z0), (0, TT_Y, TT_Z0 / 2))
terr.data.materials.append(MAT["stone"])
place(terr, "Temple")
for k in range(4):
    st = box(f"TT_Step_{k}", (14.0, 0.55, TT_Z0 * (k + 1) / 4),
             (0, TT_Y - TERR_D / 2 - 0.35 - (3 - k) * 0.55, TT_Z0 * (k + 1) / 4 / 2))
    st.data.materials.append(MAT["stone"])
    place(st, "Temple")
# terrace balustrade
for k in range(-14, 15, 2):
    for py in (TT_Y - TERR_D / 2 + 0.15,):
        p = box(f"TT_BalPost_{k}", (0.16, 0.16, 0.75), (k * 1.05, py, TT_Z0 + 0.37))
        p.data.materials.append(MAT["stone"])
        place(p, "Temple")
    rail = box(f"TT_BalRail_{k}", (2.1, 0.10, 0.10), (k * 1.05, TT_Y - TERR_D / 2 + 0.15, TT_Z0 + 0.78))
    rail.data.materials.append(MAT["stone"])
    place(rail, "Temple")

# hall body: front loggia wall with 3 REAL arch openings + back wall
TT_WALL_H = 4.2
front_y = TT_Y - TT_D / 2
back = box("TT_BackWall", (TT_W, 0.5, TT_WALL_H), (0, TT_Y + TT_D / 2 - 0.25, TT_Z0 + TT_WALL_H / 2))
back.data.materials.append(MAT["wall_grey"])
place(back, "Temple")
sidew = box("TT_SideWall_E", (0.5, TT_D, TT_WALL_H), (TT_W / 2 - 0.25, TT_Y, TT_Z0 + TT_WALL_H / 2))
sidew.data.materials.append(MAT["wall_grey"])
place(sidew, "Temple")
sidew2 = box("TT_SideWall_W", (0.5, TT_D, TT_WALL_H), (-TT_W / 2 + 0.25, TT_Y, TT_Z0 + TT_WALL_H / 2))
sidew2.data.materials.append(MAT["wall_grey"])
place(sidew2, "Temple")
fwall = arch_wall("TT_FrontWall", TT_W, 0.55, TT_WALL_H,
                  openings=[(-6.5, 2.5, 'arc', 1.25, 1.5), (0.0, 2.7, 'arc', 1.25, 1.6), (6.5, 2.5, 'arc', 1.25, 1.5)],
                  slices=30, pier_mat=MAT["wall_grey"])
fwall.location = (0, front_y, TT_Z0)
place(fwall, "Temple")
# arch surrounds (white proud bands) — mounted fully IN FRONT of the wall face
# so no ring geometry intrudes into the openings
for (ax, ahw) in ((-6.5, 2.5), (0.0, 2.7), (6.5, 2.5)):
    ring = arch_wall(f"TT_ArchRing_{ax}", ahw * 2 + 0.9, 0.24, 2.0,
                     openings=[(0.0, ahw + 0.12, 'arc', 0.0, ahw + 0.12)], slices=18,
                     pier_mat=MAT["trim"])
    ring.location = (ax, front_y - 0.42, TT_Z0)
    place(ring, "Temple")
# dark recess box behind the wall (deep loggia shadow)
rec = box("TT_Recess", (TT_W - 1.2, 4.0, TT_WALL_H - 0.3), (0, TT_Y + 0.4, TT_Z0 + (TT_WALL_H - 0.3) / 2))
rec.data.materials.append(MAT["wood"])
place(rec, "Temple")
# red doors deep inside each arch
for dx in (-6.5, 0.0, 6.5):
    dr = box(f"TT_Door_{dx}", (3.4, 0.14, 3.2), (dx, TT_Y + 1.6, TT_Z0 + 1.7))
    dr.data.materials.append(MAT["door_red"])
    place(dr, "Temple")
# red columns between + beside arches
for cx in (-10.4, -3.3, 3.3, 10.4):
    c = cylinder(f"TT_Col_{cx}", 0.30, TT_WALL_H, (cx, front_y - 0.45, TT_Z0 + TT_WALL_H / 2), verts=12)
    c.data.materials.append(MAT["red_paint"])
    place(c, "Temple")
    cb = box(f"TT_ColBase_{cx}", (0.75, 0.75, 0.35), (cx, front_y - 0.45, TT_Z0 + 0.175))
    cb.data.materials.append(MAT["stone"])
    place(cb, "Temple")
# round GOLD MEDALLION row above the arches (signature detail from photos)
for k in range(9):
    mx = -8.0 + k * 2.0
    med = cylinder(f"TT_Medallion_{k}", 0.30, 0.09, (mx, front_y - 0.36, TT_Z0 + 3.45),
                   verts=14, rot=(radians(90), 0, 0))
    med.data.materials.append(MAT["gold"])
    place(med, "Temple")
    rim = cylinder(f"TT_MedRim_{k}", 0.36, 0.05, (mx, front_y - 0.34, TT_Z0 + 3.45),
                   verts=14, rot=(radians(90), 0, 0))
    rim.data.materials.append(MAT["trim"])
    place(rim, "Temple")
# couplet panels beside the portals
for sx in (-1, 1):
    cp = box(f"TT_Couplet_{sx}", (0.55, 0.06, 2.9), (sx * 4.6, front_y - 0.36, TT_Z0 + 2.0))
    cp.data.materials.append(MAT["trim"])
    place(cp, "Temple")
    cb2 = box(f"TT_CoupletText_{sx}", (0.38, 0.04, 2.6), (sx * 4.6, front_y - 0.40, TT_Z0 + 2.0))
    cb2.data.materials.append(MAT["sign"])
    place(cb2, "Temple")

# TWO-TIER RED ROOF, steep + nested (Đền Trần v2 formula)
R1 = 2.6
r1 = hip_roof("TT_Roof_1", TT_W / 2 + 1.6, TT_D / 2 + 1.4, R1, TT_Z0 + TT_WALL_H - 0.05,
              curve=0.9, seg=10, thick=0.28, mat="tile_red", off_y=TT_Y, ridge_frac=0.55)
# upper body nested (base buried in lower roof surface at corners)
ub = box("TT_Upper_Body", (11.0, 5.2, 2.2), (0, TT_Y, TT_Z0 + TT_WALL_H + 1.60))
ub.data.materials.append(MAT["wall_grey"])
place(ub, "Temple")
R2 = 1.9
r2 = hip_roof("TT_Roof_2", 7.2, 3.6, R2, TT_Z0 + TT_WALL_H + 2.62,
              curve=0.9, seg=8, thick=0.20, mat="tile_red", off_y=TT_Y, ridge_frac=0.5)
dao_tips("TT_Roof_1", TT_W / 2 + 1.6, TT_D / 2 + 1.4, R1, TT_Z0 + TT_WALL_H - 0.05,
         curve=0.9, off_y=TT_Y, ridge_frac=0.55)
dao_tips("TT_Roof_2", 7.2, 3.6, R2, TT_Z0 + TT_WALL_H + 2.62, curve=0.9, off_y=TT_Y, ridge_frac=0.5)
# MEDALLION RIDGE LINE: gold discs on posts along the upper ridge (photo signature)
Z_UR = TT_Z0 + TT_WALL_H + 2.62 + R2
for k in range(9):
    mx = -6.0 + k * 1.5
    pst = cylinder(f"TT_RidgePost_{k}", 0.05, 0.34, (mx, TT_Y, Z_UR + 0.15), verts=7)
    pst.data.materials.append(MAT["trim"])
    place(pst, "Temple")
    disc = cylinder(f"TT_RidgeDisc_{k}", 0.22, 0.07, (mx, TT_Y, Z_UR + 0.38), verts=12,
                    rot=(radians(90), 0, 0))
    disc.data.materials.append(MAT["gold"])
    place(disc, "Temple")
# ridge bar
rb = box("TT_Ridge_Bar", (7.2 * 0.5 * 2 - 0.5, 0.30, 0.26), (0, TT_Y, Z_UR + 0.10))
rb.data.materials.append(MAT["tile_red"])
place(rb, "Temple")

# hanging lanterns under the eaves
for k, lx in enumerate((-6.5, 0.0, 6.5)):
    flag_objs.append(hanging_lantern(f"Lantern_TT_{k}", lx, front_y - 0.55, TT_Z0 + TT_WALL_H - 0.25, 1.1))

# ================================================================ 4. TRUNG TẾ + HẬU CUNG
# connector
ct = box("TZ_Body", (10.0, 7.0, 3.4), (0, TZ_Y, 1.7))
ct.data.materials.append(MAT["wall_grey"])
place(ct, "Temple")
ctr = hip_roof("TZ_Roof", 6.4, 4.6, 1.5, 3.35, curve=0.9, seg=8, thick=0.20,
               mat="tile_red", off_y=TZ_Y, ridge_frac=0.5)
dao_tips("TZ_Roof", 6.4, 4.6, 1.5, 3.35, curve=0.9, off_y=TZ_Y, ridge_frac=0.5)
# doors
tdr = box("TZ_Door", (2.6, 0.12, 2.4), (0, TZ_Y - 3.55, 1.35))
tdr.data.materials.append(MAT["door_red"])
place(tdr, "Temple")

# HẬU CUNG — taller stacked 2-tier ("chuổi vỏ" blocks)
HC_W, HC_D = 15.0, 10.0
hc_pl = box("HC_Plinth", (HC_W + 2.0, HC_D + 2.0, 0.7), (0, HC_Y, 0.35))
hc_pl.data.materials.append(MAT["stone"])
place(hc_pl, "Temple")
hb1 = box("HC_Body_1", (HC_W, HC_D, 4.4), (0, HC_Y, 0.7 + 2.2))
hb1.data.materials.append(MAT["wall_grey"])
place(hb1, "Temple")
# arched door on front face
hdoor = arch_wall("HC_DoorWall", 4.6, 0.4, 3.6, openings=[(0.0, 1.15, 'arc', 0.9, 1.15)],
                  slices=12, pier_mat=MAT["wood"])
hdoor.location = (0, HC_Y - HC_D / 2 - 0.05, 0.7)
place(hdoor, "Temple")
H1 = 1.7
hr1 = hip_roof("HC_Roof_1", HC_W / 2 + 1.2, HC_D / 2 + 1.1, H1, 5.05,
               curve=0.9, seg=9, thick=0.24, mat="tile_red", off_y=HC_Y, ridge_frac=0.55)
ub2 = box("HC_Body_2", (8.5, 4.6, 1.9), (0, HC_Y, 6.35))
ub2.data.materials.append(MAT["wall_grey"])
place(ub2, "Temple")
H2 = 1.5
hr2 = hip_roof("HC_Roof_2", 5.9, 3.3, H2, 7.22, curve=0.9, seg=7, thick=0.18,
               mat="tile_red", off_y=HC_Y, ridge_frac=0.5)
dao_tips("HC_Roof_1", HC_W / 2 + 1.2, HC_D / 2 + 1.1, H1, 5.05, curve=0.9, off_y=HC_Y, ridge_frac=0.55)
dao_tips("HC_Roof_2", 5.9, 3.3, H2, 7.22, curve=0.9, off_y=HC_Y, ridge_frac=0.5)
hfin = sphere("HC_Finial", 0.15, (0, HC_Y, 7.22 + H2 + 0.12), segs=10, rings=6)
hfin.data.materials.append(MAT["gold"])
place(hfin, "Temple")
# side wings (hành lang) connecting Tiền Tế to Hậu Cung
for sx in (-1, 1):
    wing = box(f"Wing_{sx}", (4.0, 14.0, 3.0), (sx * (TT_W / 2 + 2.2), (TT_Y + HC_Y) / 2 - 1.0, 0.7 + 1.5))
    wing.data.materials.append(MAT["wall_grey"])
    place(wing, "Temple")
    wr = hip_roof(f"Wing_Roof_{sx}", 2.6, 7.6, 1.1, 3.65, curve=0.85, seg=7, thick=0.16,
                  mat="tile_red", off_x=sx * (TT_W / 2 + 2.2), off_y=(TT_Y + HC_Y) / 2 - 1.0,
                  ridge_frac=0.4)

# ================================================================ 5. ĐỀN THỜ TỔ (yellow founder shrine — user reference)
TS_Z0 = 0.55
TS_H = 4.6
# plinth + steps
pl = box("TS_Plinth", (TS_W + 1.8, TS_D + 1.8, TS_Z0), (TS_X, TS_Y, TS_Z0 / 2))
pl.data.materials.append(MAT["stone"])
place(pl, "ToShrine")
for k in range(3):
    st = box(f"TS_Step_{k}", (4.6 - k * 0.4, 0.5, TS_Z0 * (k + 1) / 3),
             (TS_X, TS_Y - TS_D / 2 - 0.35 - (2 - k) * 0.5, TS_Z0 * (k + 1) / 3 / 2))
    st.data.materials.append(MAT["stone"])
    place(st, "ToShrine")

# main yellow body (front wall with tall arch portal + 2 side niches)
body = box("TS_Body", (TS_W, TS_D - 1.2, TS_H), (TS_X, TS_Y + 0.6, TS_Z0 + TS_H / 2))
body.data.materials.append(MAT["yellow"])
place(body, "ToShrine")
fw = arch_wall("TS_FrontWall", TS_W, 0.55, TS_H,
               openings=[(0.0, 1.55, 'arc', 1.30, 1.35),
                         (-4.3, 1.05, 'arc', 1.05, 0.95),
                         (4.3, 1.05, 'arc', 1.05, 0.95)],
               slices=30, pier_mat=MAT["yellow"])
fw.location = (TS_X, TS_Y - (TS_D / 2 - 0.6), TS_Z0)
place(fw, "ToShrine")
# white arch surrounds on all 3 openings
for (ax, ahw) in ((0.0, 1.55), (-4.3, 1.05), (4.3, 1.05)):
    ring = arch_wall(f"TS_ArchRing_{ax}", ahw * 2 + 0.8, 0.22, 1.8,
                     openings=[(0.0, ahw, 'arc', 0.0, ahw)], slices=16,
                     pier_mat=MAT["trim"])
    ring.location = (TS_X + ax, TS_Y - (TS_D / 2 - 0.6) - 0.10, TS_Z0)
    place(ring, "ToShrine")
# dark recess right behind the portal arch (deep shadowed reveal like the ref)
trec = box("TS_Recess", (3.6, 2.2, 3.6), (TS_X, TS_Y - 1.7, TS_Z0 + 1.8))
trec.data.materials.append(MAT["wood"])
place(trec, "ToShrine")
tdoor = box("TS_Door", (2.4, 0.12, 2.6), (TS_X, TS_Y - 0.55, TS_Z0 + 1.4))
tdoor.data.materials.append(MAT["door_red"])
place(tdoor, "ToShrine")
flag_objs.append(hanging_lantern("Lantern_TS_0", TS_X, TS_Y - 1.0, TS_Z0 + 3.55, 1.0))
# side niches: dark insets
for sx in (-1, 1):
    nic = box(f"TS_Niche_{sx}", (1.7, 0.5, 2.4), (TS_X + sx * 4.3, TS_Y - (TS_D / 2 - 0.6) + 0.1, TS_Z0 + 1.5))
    nic.data.materials.append(MAT["wood"])
    place(nic, "ToShrine")

# tall pilasters with white capitals + red bands (photo: yellow pilasters, red/white flutes)
for px in (-6.2, -2.2, 2.2, 6.2):
    pil = box(f"TS_Pilaster_{px}", (0.75, 0.30, TS_H), (TS_X + px, TS_Y - (TS_D / 2 - 0.6) - 0.14, TS_Z0 + TS_H / 2))
    pil.data.materials.append(MAT["yellow"])
    place(pil, "ToShrine")
    cap = box(f"TS_PilCap_{px}", (0.95, 0.36, 0.30), (TS_X + px, TS_Y - (TS_D / 2 - 0.6) - 0.16, TS_Z0 + TS_H - 0.15))
    cap.data.materials.append(MAT["trim"])
    place(cap, "ToShrine")
    rb2 = box(f"TS_PilBand_{px}", (0.80, 0.32, 0.16), (TS_X + px, TS_Y - (TS_D / 2 - 0.6) - 0.15, TS_Z0 + 0.55))
    rb2.data.materials.append(MAT["red_paint"])
    place(rb2, "ToShrine")
# white couplet panels with red characters on the inner pilasters (photo)
for px in (-2.2, 2.2):
    cp = box(f"TS_Couplet_{px}", (0.5, 0.08, 3.1), (TS_X + px * 1.02, TS_Y - (TS_D / 2 - 0.6) - 0.32, TS_Z0 + 2.2))
    cp.data.materials.append(MAT["trim"])
    place(cp, "ToShrine")
    ct2 = box(f"TS_CoupletText_{px}", (0.34, 0.05, 2.8), (TS_X + px * 1.02, TS_Y - (TS_D / 2 - 0.6) - 0.37, TS_Z0 + 2.2))
    ct2.data.materials.append(MAT["sign"])
    place(ct2, "ToShrine")
# white QUOINS on the facade corners (photo signature)
for sx in (-1, 1):
    for q in range(5):
        qz = TS_Z0 + 0.45 + q * 0.9
        qy = TS_Y - (TS_D / 2 - 0.6) - 0.10
        qb = box(f"TS_Quoin_{sx}_{q}", (0.42, 0.24, 0.62), (TS_X + sx * (TS_W / 2 - 0.25), qy, qz))
        qb.data.materials.append(MAT["trim"])
        place(qb, "ToShrine")

# SIGNBOARD above portal: dark board + white title band + small blue line (photo)
sb_y = TS_Y - (TS_D / 2 - 0.6) - 0.22
sb = box("TS_SignBoard", (4.6, 0.14, 1.15), (TS_X, sb_y, TS_Z0 + 3.75))
sb.data.materials.append(MAT["sign"])
place(sb, "ToShrine")
sbt = box("TS_SignText", (4.0, 0.05, 0.52), (TS_X, sb_y - 0.09, TS_Z0 + 3.92))
sbt.data.materials.append(MAT["sign_text"])
place(sbt, "ToShrine")
sbb = box("TS_SignSub", (3.0, 0.05, 0.18), (TS_X, sb_y - 0.09, TS_Z0 + 3.48))
sbb.data.materials.append(MAT["banner"])
place(sbb, "ToShrine")

# ROOFLINE: white dentil cornice + red/white balustrade + grey tile roof behind
cor = box("TS_Cornice", (TS_W + 0.6, 0.75, 0.28), (TS_X, TS_Y - (TS_D / 2 - 0.6) + 0.1, TS_Z0 + TS_H + 0.10))
cor.data.materials.append(MAT["trim"])
place(cor, "ToShrine")
# balustrade across the top (photo: red/white patterned parapet)
for k in range(13):
    bx = TS_X - 5.6 + k * 0.95
    seg_mat = "red_paint" if k % 2 == 0 else "trim"
    bp = box(f"TS_Parapet_{k}", (0.80, 0.16, 0.42), (bx, TS_Y - (TS_D / 2 - 0.6) - 0.05, TS_Z0 + TS_H + 0.42))
    bp.data.materials.append(MAT[seg_mat])
    place(bp, "ToShrine")
top_rail = box("TS_ParapetRail", (TS_W + 0.4, 0.22, 0.10), (TS_X, TS_Y - (TS_D / 2 - 0.6) - 0.05, TS_Z0 + TS_H + 0.68))
top_rail.data.materials.append(MAT["trim"])
place(top_rail, "ToShrine")
# grey tile roof visible behind the parapet
tr = hip_roof("TS_Roof", TS_W / 2 + 0.9, TS_D / 2 + 0.8, 1.6, TS_Z0 + TS_H + 0.55,
              curve=0.9, seg=9, thick=0.22, mat="tile_grey", off_x=TS_X, off_y=TS_Y,
              col="ToShrine", ridge_frac=0.5)
dao_tips("TS_Roof", TS_W / 2 + 0.9, TS_D / 2 + 0.8, 1.6, TS_Z0 + TS_H + 0.55, curve=0.9,
         off_x=TS_X, off_y=TS_Y, col="ToShrine", mat="tile_grey", ridge_frac=0.5)
# THREE circular character medallions mounted ON the facade top edge (photo:
# discs sit just above the cornice, overlapping the roof edge — no gap)
MED_Z = TS_Z0 + TS_H + 1.35
MED_Y = TS_Y - 4.30   # mounted on the front roof slope, discs rise above the eave
for k, (mx, mr) in enumerate(((-1.85, 0.52), (0.0, 0.68), (1.85, 0.52))):
    ring = cylinder(f"TS_Medallion_Ring_{k}", mr, 0.16,
                    (TS_X + mx, MED_Y, MED_Z),
                    verts=16, rot=(radians(90), 0, 0))
    ring.data.materials.append(MAT["trim"])
    place(ring, "ToShrine")
    inner = cylinder(f"TS_Medallion_Disc_{k}", mr * 0.78, 0.13,
                     (TS_X + mx, MED_Y - 0.04, MED_Z),
                     verts=14, rot=(radians(90), 0, 0))
    inner.data.materials.append(MAT["tile_grey"])
    place(inner, "ToShrine")
    # incised character square at the centre (stylised chữ)
    ch = box(f"TS_Medallion_Char_{k}", (mr * 0.5, 0.05, mr * 0.5),
             (TS_X + mx, MED_Y - 0.08, MED_Z))
    ch.data.materials.append(MAT["trim"])
    place(ch, "ToShrine")
    # half-disc buried in the roof slope (no gap, no float)
    ped = box(f"TS_Medallion_Ped_{k}", (mr * 1.6, 0.9, mr * 0.9),
              (TS_X + mx, MED_Y + 0.45, MED_Z - mr * 0.6))
    ped.data.materials.append(MAT["trim"])
    place(ped, "ToShrine")
# corner finial pots (photo: small white pots with red on the roof corners)
for sx in (-1, 1):
    pot = cylinder(f"TS_CornerPot_{sx}", 0.20, 0.30,
                   (TS_X + sx * (TS_W / 2 + 0.35), TS_Y - (TS_D / 2 - 0.6) + 0.4, TS_Z0 + TS_H + 1.25), verts=10)
    pot.data.materials.append(MAT["trim"])
    place(pot, "ToShrine")
    pp = sphere(f"TS_CornerPotTop_{sx}", 0.10,
                (TS_X + sx * (TS_W / 2 + 0.35), TS_Y - (TS_D / 2 - 0.6) + 0.4, TS_Z0 + TS_H + 1.46), segs=8, rings=5)
    pp.data.materials.append(MAT["red_paint"])
    place(pp, "ToShrine")
# red blossom bush in front (photo foreground)
for k, (bx_, by_, br_) in enumerate(((-2.6, -6.6, 0.8), (-1.6, -6.9, 0.6), (2.4, -6.5, 0.85), (3.2, -6.2, 0.6))):
    bl = sphere(f"TS_Bush_{k}", br_, (TS_X + bx_, TS_Y + by_, 0.35 + br_ * 0.5), segs=9, rings=6)
    bl.scale = (1.0, 1.0, 0.75)
    bl.data.materials.append(MAT["hedge"])
    place(bl, "ToShrine")
    for j in range(4):
        fl = sphere(f"TS_Bloom_{k}_{j}", 0.10,
                    (TS_X + bx_ + random.uniform(-br_, br_) * 0.8,
                     TS_Y + by_ + random.uniform(-br_, br_) * 0.8,
                     0.45 + br_ * 0.5 + random.uniform(0, 0.45)), segs=7, rings=4)
        fl.data.materials.append(MAT["blossom"])
        place(fl, "ToShrine")
# bronze urns beside the steps
for sx in (-1, 1):
    u1 = cylinder(f"TS_Urn_{sx}", 0.30, 0.5, (TS_X + sx * 3.4, TS_Y - TS_D / 2 - 1.1, TS_Z0 + 0.25), verts=10)
    u1.data.materials.append(MAT["gold"])
    place(u1, "ToShrine")

# ================================================================ 6. GROUNDS
# flagpole in the courtyard (photo/aerial: flag near the hall)
fp = cylinder("Flagpole", 0.09, 16.0, (-9.0, -12.0, 8.0), verts=9)
fp.data.materials.append(MAT["silver"])
place(fp, "Grounds")
fb = box("Flag_Cloth", (0.06, 2.6, 1.7), (-8.92, -10.7, 14.6))
fb.data.materials.append(MAT["banner"])
place(fb, "Flags")
fb.rotation_mode = 'XYZ'
# pivot for the flag
piv = bpy.data.objects.new("Flag_Pivot", None)
piv.location = (-9.0, -12.0, 14.6)
bpy.context.scene.collection.objects.link(piv)
fb.parent = piv
fb.location = (-8.92 + 9.0, -10.7 + 12.0, 14.6 - 14.6)
flag_objs.append(fb)
# courtyard lamps
for k, (lx, ly) in enumerate(((-12.0, -16.0), (12.0, -16.0), (-16.0, 4.0), (16.0, 4.0))):
    p = cylinder(f"Lamp_{k}_Post", 0.07, 2.4, (lx, ly, 1.2), verts=8)
    p.data.materials.append(MAT["stone"])
    place(p, "Grounds")
    h = sphere(f"Lamp_{k}_Head", 0.18, (lx, ly, 2.55), segs=8, rings=5)
    h.data.materials.append(MAT["gold"])
    place(h, "Grounds")
# stone urns on the terrace corners
for sx in (-1, 1):
    u = cylinder(f"TT_Urn_{sx}", 0.35, 0.6, (sx * (TERR_W / 2 - 2.0), TT_Y - TERR_D / 2 + 1.2, TT_Z0 + 0.3), verts=10)
    u.data.materials.append(MAT["stone"])
    place(u, "Grounds")

# COURTYARD FURNITURE (the reference courtyard is richly dressed)
# stone steles (bia) on turtle bases flanking the axis
def stele(name, x, y):
    base = box(f"{name}_Turtle", (1.5, 2.2, 0.5), (x, y, 0.25))
    base.data.materials.append(MAT["stone"])
    place(base, "Grounds")
    hb = box(f"{name}_Head", (0.5, 0.7, 0.35), (x, y - 1.05, 0.62))
    hb.data.materials.append(MAT["stone"])
    place(hb, "Grounds")
    st = box(f"{name}_Stele", (1.05, 0.22, 2.3), (x, y + 0.1, 1.65))
    st.data.materials.append(MAT["stone"])
    place(st, "Grounds")
    top = box(f"{name}_Top", (1.25, 0.30, 0.30), (x, y + 0.1, 2.9), rot=(0, 0, 0))
    top.data.materials.append(MAT["stone"])
    place(top, "Grounds")
    txt = box(f"{name}_Text", (0.6, 0.06, 1.6), (x, y - 0.03, 1.75))
    txt.data.materials.append(MAT["sign"])
    place(txt, "Grounds")

for sx in (-1, 1):
    stele(f"Stele_{sx}", sx * 7.5, -14.0)
# carved altar + incense urn in front of the Tiền Tế steps
alt = box("Altar_Body", (3.4, 1.1, 0.9), (0, -15.5, 0.45 + TT_Z0 * 0))
alt.data.materials.append(MAT["stone"])
place(alt, "Grounds")
alt_lip = box("Altar_Lip", (3.7, 1.25, 0.12), (0, -15.5, 0.96))
alt_lip.data.materials.append(MAT["stone"])
place(alt_lip, "Grounds")
alt_u = cylinder("Altar_Urn", 0.28, 0.5, (0, -15.5, 1.27), verts=10)
alt_u.data.materials.append(MAT["gold"])
place(alt_u, "Grounds")
# incense smoke post (stylised)
for k in range(3):
    st = cylinder(f"Altar_Stick_{k}", 0.02, 0.55, (-0.2 + k * 0.2, -15.35, 1.55), verts=5)
    st.data.materials.append(MAT["wood"])
    place(st, "Grounds")
# stone lamp posts along the axis (photo: pairs of lantern posts)
for k, (lx, ly) in enumerate(((-4.5, -19.5), (4.5, -19.5), (-4.5, -8.5), (4.5, -8.5))):
    lp = cylinder(f"AxisLamp_{k}_Post", 0.10, 2.0, (lx, ly, 1.0), verts=8)
    lp.data.materials.append(MAT["stone"])
    place(lp, "Grounds")
    lb = box(f"AxisLamp_{k}_Case", (0.34, 0.34, 0.4), (lx, ly, 2.15))
    lb.data.materials.append(MAT["trim"])
    place(lb, "Grounds")
    lr = hip_roof(f"AxisLamp_{k}_Roof", 0.30, 0.30, 0.22, 2.36, curve=0.5, seg=5,
                  thick=0.05, mat="tile_grey", off_x=lx, off_y=ly, col="Grounds",
                  ridge_frac=0.3)
# planted urn rows (circular planters with bushes) along the courtyard edges
for k in range(6):
    for sx in (-1, 1):
        ux, uy = sx * (12.5 - (k % 2) * 1.5), -12.0 + k * 6.5
        pl = cylinder(f"Planter_{k}_{sx}", 0.55, 0.5, (ux, uy, 0.25), verts=10)
        pl.data.materials.append(MAT["stone"])
        place(pl, "Grounds")
        bush = sphere(f"PlanterBush_{k}_{sx}", 0.42, (ux, uy, 0.72), segs=8, rings=5)
        bush.scale = (1.0, 1.0, 0.8)
        bush.data.materials.append(MAT["hedge"])
        place(bush, "Grounds")
# axial PATH from the Tiền Tế steps to the footbridge (worn walkway)
path = box("Axis_Path", (5.0, 15.0, 0.10), (0, -18.0, 0.16))
path.data.materials.append(MAT["paving"])
place(path, "Environment")
path2 = box("Axis_Path2", (3.0, 9.0, 0.10), (0, -25.0 - 1.0, 0.16))
path2.data.materials.append(MAT["paving"])
place(path2, "Environment")

# trees around (village greenery from the aerial photo)
def tree(name, x, y, h=4.5, r=2.2, seed=1, lmat="leaf"):
    rnd = random.Random(seed)
    trunk = cylinder(f"{name}_Trunk", 0.20, h, (x, y, h / 2), verts=7)
    trunk.data.materials.append(MAT["trunk"])
    trunk.rotation_euler = (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 0)
    place(trunk, "Trees")
    for k, (dz, sr) in enumerate(((h * 0.55, r), (h * 0.75, r * 0.8), (h * 0.95, r * 0.55))):
        blob = sphere(f"{name}_Foliage_{k}", sr,
                      (x + rnd.uniform(-0.5, 0.5), y + rnd.uniform(-0.5, 0.5), dz),
                      segs=9, rings=6)
        blob.scale = (1.0, 1.0, 0.75)
        blob.data.materials.append(MAT[lmat])
        blob.rotation_euler = (0, 0, rnd.uniform(0, 3.14))
        place(blob, "Trees")

tree("Tree_BigW", -20.0, 6.0, h=6.5, r=3.0, seed=51)
tree("Tree_BigE", 20.0, 10.0, h=6.0, r=2.8, seed=52, lmat="leaf3")
tree("Tree_NE", -16.0, 22.0, h=5.5, r=2.6, seed=53, lmat="leaf2")
tree("Tree_NW", 16.0, 26.0, h=5.8, r=2.7, seed=54)
tree("Tree_SW", -24.0, -14.0, h=5.0, r=2.4, seed=55, lmat="leaf2")
tree("Tree_SE", 34.0, 2.0, h=5.2, r=2.5, seed=56)
tree("Tree_RiverW", -12.0, -22.5, h=4.6, r=2.2, seed=57, lmat="leaf3")
tree("Tree_RiverE", 12.0, -22.5, h=4.4, r=2.1, seed=58)
# dense village greenery west + east (aerial reference shows a green village)
for k, (tx, ty, th, tr_, sd, lm) in enumerate([
        (-34.0, -18.0, 5.4, 2.7, 61, "leaf3"), (-38.0, 0.0, 6.0, 3.0, 62, "leaf"),
        (-33.0, 14.0, 5.0, 2.5, 63, "leaf2"), (-40.0, 22.0, 5.6, 2.8, 64, "leaf3"),
        (34.0, 14.0, 5.4, 2.7, 65, "leaf"), (38.0, 26.0, 5.8, 2.9, 66, "leaf3"),
        (34.0, -16.0, 5.0, 2.5, 67, "leaf2"), (40.0, -6.0, 5.6, 2.8, 68, "leaf"),
        (-30.0, -28.0, 4.8, 2.4, 69, "leaf2"), (31.0, -26.0, 4.6, 2.3, 70, "leaf3")]):
    tree(f"Tree_Village_{k}", tx, ty, h=th, r=tr_, seed=sd, lmat=lm)
# extra village houses west (aerial reference: dense red roofs)
for k in range(5):
    hx, hy = -40.0 + k * 9.0, 40.0 + (k % 2) * 8.0
    hh = box(f"VillageHouse_W_{k}", (6.0, 5.0, 2.8), (hx, hy, 1.4))
    hh.data.materials.append(MAT["wall_grey"])
    place(hh, "Environment")
    hip_roof(f"VillageHouse_WRoof_{k}", 3.5, 3.0, 1.1, 2.8, curve=0.7, seg=5,
             thick=0.13, mat="tile_red", off_x=hx, off_y=hy, col="Environment",
             ridge_frac=0.4)
# village houses behind the complex (aerial photo: red-roofed village)
for k in range(8):
    hx = -34.0 + k * 10.0
    hy = 34.0 + (k % 3) * 7.0
    hh = box(f"VillageHouse_{k}", (6.5, 5.5, 3.0), (hx, hy, 1.5))
    hh.data.materials.append(MAT["wall_grey"])
    place(hh, "Environment")
    hr = hip_roof(f"VillageHouse_Roof_{k}", 3.8, 3.2, 1.2, 3.0, curve=0.7, seg=5,
                  thick=0.14, mat="tile_red", off_x=hx, off_y=hy, col="Environment",
                  ridge_frac=0.4)

# ================================================================ 6b. VISITORS (tourists + locals)
for cname in ("Visitors",):
    if cname not in COL:
        COL[cname] = bpy.data.collections.new(cname)
        scene.collection.children.link(COL[cname])

visitor_specs = [
    # axial walkway: couples + families heading to the temple
    (-1.8, -16.5, 15, 'couple'), (2.2, -18.5, 80, 'family'),
    (1.4, -13.0, 175, 'adult'), (-2.6, -11.0, 200, 'photographer'),
    (-3.4, -20.0, 30, 'family'), (3.0, -9.5, 260, 'couple'),
    # near the steles: tourists reading (kept clear of the turtle bases)
    (-8.8, -12.2, 45, 'photographer'), (8.8, -15.8, -35, 'adult'),
    (-8.0, -16.2, 12, 'kid'), (9.4, -12.4, -60, 'kid'),
    # altar area: worshippers
    (-1.6, -17.2, 80, 'adult'), (1.8, -16.8, 100, 'adult'),
    # monk procession along the front path
    (5.8, -21.5, 250, 'monk'), (6.5, -19.0, 250, 'monk'), (7.2, -16.5, 250, 'monk'),
    # terrace foot: resting visitors
    (-10.5, -10.8, 60, 'adult'), (10.8, -11.4, -50, 'adult'),
    (11.5, -13.2, -80, 'kid'),
    # footbridge: photographers + walkers over the river
    (0.4, -27.5, 8, 'photographer'), (-0.5, -30.5, 172, 'adult'),
    (0.6, -33.5, 168, 'couple'), (-0.3, -35.5, 185, 'kid'),
    # bridge approach on the far bank
    (-2.0, -24.0, 160, 'adult'), (2.4, -23.0, 200, 'family'),
    # pavilion deck (on the platform z): visitors admire the river
    (-1.5, -33.0, 95, 'photographer'), (1.6, -35.0, 140, 'couple'),
    # village street east: kids playing
    (16.0, -12.0, -20, 'kid'), (17.2, -10.2, 140, 'kid'), (15.4, -9.0, 30, 'adult'),
]
visitors = add_visitors(bpy, V, box, cylinder, sphere, place, pbr, MAT, visitor_specs,
                        col="Visitors", seed=515)
# pavilion-deck visitors stand on the platform: lift them
for o in visitors:
    if 'Visitor_22' in o.name or 'Visitor_23' in o.name:
        o.location.z += WATER_Z + 2.97

# ================================================================ 7. LIGHTING
world = bpy.data.worlds.new("Sky_World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.70, 0.77, 0.86, 1.0)
bg.inputs[1].default_value = 0.62

sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 5.4
sun.data.angle = radians(3.0)
sun.data.color = (1.0, 0.96, 0.88)
d = V((-0.42, 0.62, -0.66)).normalized()
sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
place(sun, "Lighting")

fill = bpy.data.objects.new("Fill_Sky", bpy.data.lights.new("Fill_Sky", 'AREA'))
fill.data.energy = 420
fill.data.size = 26
fill.data.color = (0.93, 0.95, 1.0)
fill.location = (-10, -20, 12)
fill.rotation_euler = Euler((radians(50), 0, radians(-20)))
place(fill, "Lighting")

# ================================================================ 8. CAMERAS
def camera(name, loc, look_at, lens=36):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.location = loc
    direction = V(look_at) - V(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 500
    place(cam, "Cameras")
    return cam

cam_a = camera("Camera_Hero", (-16.0, -54.0, 11.0), (2.0, -6.0, 3.5), 32)     # across the river
cam_b = camera("Camera_ToShrine", (TS_X + 4.0, TS_Y - 19.0, 4.4), (TS_X, TS_Y, 4.2), 35)  # reference angle
cam_c = camera("Camera_Hall", (15.0, -22.0, 6.5), (-2.0, 2.0, 5.0), 36)   # Tiền Tế 3/4 (clear of flagpole)
cam_d = camera("Camera_Aerial", (36.0, -46.0, 28.0), (2.0, -4.0, 2.0), 30)   # overview w/ river

# ================================================================ 9. ANIMATION (lantern sway + flag)
scene.frame_start = 1
scene.frame_end = 96
for i, sw in enumerate(flag_objs):
    ph = i * 1.15
    amp = 0.10
    for f in (1, 24, 48, 72, 96):
        sw.rotation_euler.y = amp * 0.45 * sin(ph + f / 96 * 2 * pi)
        sw.rotation_euler.z = amp * sin(ph * 1.3 + f / 96 * 2 * pi) if sw.name.startswith("Flag") else 0.0
        sw.keyframe_insert("rotation_euler", frame=f)
    if sw.animation_data and sw.animation_data.action:
        for fc in sw.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'SINE'

# ================================================================ 10. VIEWPORT DISPLAY
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
            if screen.name == "Layout":
                space.region_3d.view_perspective = 'CAMERA'

# ================================================================ 11. SAVE + RENDER
os.makedirs(RENDER_DIR, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("SAVED_BLEND:", BLEND_PATH)

for cam, tag in ((cam_a, "hero"), (cam_b, "toshrine"), (cam_c, "hall"), (cam_d, "aerial")):
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
print("BUILD_OK")
