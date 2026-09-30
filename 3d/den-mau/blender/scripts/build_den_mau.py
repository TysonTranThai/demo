# -*- coding: utf-8 -*-
"""
SMART ART HERITAGE — Đền Mẫu (Hoa Dương Linh Từ), Phố Hiến, Hưng Yên + hồ Bán Nguyệt.
Procedural Blender 4.5 build.  v2 (clean rewrite)

Researched / reference-observed facts encoded:
- Nghi môn gate: "chồng diêm hai tầng tám mái" — stacked 2-story pavilion with 8
  roof planes over a masonry wall with 3 vaulted openings (1 main + 2 side),
  circular moon window (vòm trăng) on the upper story, đao flame tips, tablets.
- Temple: masonry hall, 3 vaulted loggia arches + 2 side doors, upper open
  terrace with balustrade + red flags, central belvedere + side wings with
  small tiled roofs, steps to the courtyard.
- Hồ Bán Nguyệt: crescent pond in front of the gate, stone coping, central
  stone walkway crossing the crescent opening to the gate.
- Setting: mature trees, flagpoles with waving flags, low perimeter walls.

Ambiguities resolved: interiors dark (web budget), relief carvings suggested by
insets/tablets, trees low-poly, flags animated as rigid cloth sway.
"""

import bpy, bmesh, os, math, sys, random
from math import radians, sin, cos, pi, sqrt, atan2
from mathutils import Vector, Euler

V = Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(SCRIPT_DIR, "..", "den-mau-model.blend")
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

def arch_wall(name, width, depth, height, openings, slices=30, pier_mat=None):
    """Masonry wall block with real through-openings (vòm cuốn).
    openings: list of (cx, half_w, kind, spring_z, rise)
      kind 'arc': opening top = spring_z + sqrt(R^2 - dx^2) capped at spring_z+rise
                  (R = half_w; rise = R normally) — use rise>R for stilted arch
      kind 'rect': opening top = spring_z (flat lintel)
    Slices follow the opening profile; smooth half-cylinder shells dress the arcs.
    Origin: bottom centre of the wall."""
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
            Euler((0, 0, 0)).to_matrix().to_4x4()
            @ __import__('mathutils').Matrix.Translation((xm, 0, z0 + zh / 2))
            @ __import__('mathutils').Matrix.Diagonal((sw, depth, zh, 1))))
    # smooth shells for arc openings (cover slice steps inside the passage)
    for (cx, hw, kind, sz, rise) in openings:
        if kind != 'arc':
            continue
        R = hw
        segs = 12
        ring_f, ring_b = [], []
        for k in range(segs + 1):
            a = pi * k / segs
            x = cx + R * cos(a)
            z = sz + rise * sin(a) if rise > 0 else sz
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

def hip_roof(name, half_w, half_d, rise, z, curve=0.8, seg=8, thick=0.16):
    bm = bmesh.new()
    nx = ny = seg + 1
    verts = []
    for iy in range(ny):
        row = []
        for ix in range(nx):
            x = (-half_w + 2 * half_w * ix / seg)
            y = (-half_d + 2 * half_d * iy / seg)
            u = max(abs(x) / half_w, abs(y) / half_d)
            h = rise * (1 - u)
            corner = (abs(x) / half_w) * (abs(y) / half_w)
            h += curve * rise * 0.9 * corner ** 4
            row.append(bm.verts.new((x, y, h)))
        verts.append(row)
    for iy in range(ny - 1):
        for ix in range(nx - 1):
            bm.faces.new((verts[iy][ix], verts[iy][ix + 1],
                          verts[iy + 1][ix + 1], verts[iy + 1][ix]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.solidify(bm, thickness=thick, geom=geom)
    obj = build_mesh(name, bm, (0, 0, z))
    obj.data.materials.append(MAT["tile"])
    obj.data.materials.append(MAT["wood"])
    shade_smooth(obj)
    return obj

def white_fascia(name, hw, hd, z, cx=0.0, cy=0.0):
    """White lime fascia band around a roof's eave perimeter (reference look)."""
    for tag, size, loc in (("N", (2 * hw + 0.18, 0.15, 0.17), (cx, cy + hd + 0.02, z + 0.05)),
                           ("S", (2 * hw + 0.18, 0.15, 0.17), (cx, cy - hd - 0.02, z + 0.05)),
                           ("E", (0.15, 2 * hd + 0.18, 0.17), (cx + hw + 0.02, cy, z + 0.05)),
                           ("W", (0.15, 2 * hd + 0.18, 0.17), (cx - hw - 0.02, cy, z + 0.05))):
        b = box(f"{name}_Fascia_{tag}", size, loc)
        b.data.materials.append(MAT["ridge"])
        place(b, "Gate" if cy == 0 and z < 12 else "Temple")

def apex_cap(name, x, y, z, r=0.14):
    cap = sphere(f"{name}_Apex", r, (x, y, z), segs=10, rings=7)
    cap.data.materials.append(MAT["ridge"])
    place(cap, "Gate" if y == 0 and z < 12 else "Temple")
    ball = sphere(f"{name}_ApexBall", r * 0.55, (x, y, z + r * 0.95), segs=10, rings=6)
    ball.data.materials.append(MAT["gold"])
    place(ball, "Gate" if y == 0 and z < 12 else "Temple")

def arch_trim(name, cx, hw, sz, y_face, band=0.16, depth=0.14, segs=12):
    """Proud white-lime band outlining a vault opening (jamb strips + arch ring)."""
    bm = bmesh.new()
    R2 = hw + band
    ring_o, ring_i = [], []
    for k in range(segs + 1):
        a = pi * k / segs
        ring_o.append(bm.verts.new((cx + R2 * cos(a), -depth / 2, sz + R2 * sin(a))))
        ring_i.append(bm.verts.new((cx + hw * cos(a), -depth / 2, sz + hw * sin(a))))
    faces = []
    for k in range(segs):
        faces.append(bm.faces.new((ring_i[k], ring_i[k + 1], ring_o[k + 1], ring_o[k])))
    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    verts = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=V((0, depth, 0)), verts=verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = build_mesh(name, bm, (0, y_face, 0))
    obj.data.materials.append(MAT["ridge"])
    place(obj, "Gate")
    # jamb strips down to the ground
    for sgn in (-1, 1):
        jb = box(f"{name}_Jamb_{sgn}", (band * 1.7, depth, sz + 0.35),
                 (cx + sgn * (hw + band * 0.6), y_face + depth / 2, (sz + 0.35) / 2))
        jb.data.materials.append(MAT["ridge"])
        place(jb, "Gate")
    return obj

def hanging_lantern(name, x, y, z_top, scale=1.0):
    """Single-mesh red lantern (cord+body+caps+tassel) hanging from z_top.
    Two material slots: red body, gold hardware. Rigid-sway animated."""
    bm = bmesh.new()
    def part(r1, r2, d, loc, seg=10):
        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                    segments=seg, radius1=r1, radius2=r2, depth=d)
        bmesh.ops.translate(bm, vec=V(loc), verts=ret['verts'])
    s = scale
    part(0.012 * s, 0.012 * s, 0.30 * s, (0, 0, -0.15 * s))
    part(0.048 * s, 0.030 * s, 0.05 * s, (0, 0, -0.325 * s))
    part(0.145 * s, 0.145 * s, 0.20 * s, (0, 0, -0.45 * s))
    part(0.048 * s, 0.030 * s, 0.05 * s, (0, 0, -0.575 * s))
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

def crescent(name, r_in, r_out, open_half_deg, z_top, z_bot, segs=56):
    """Watertight crescent (annulus sector) solid, opening facing +Y.
    Sector spans 360 - 2*open_half degrees, centred on -Y (the bulge)."""
    bm = bmesh.new()
    a0 = radians(90 + open_half_deg)
    sweep = radians(360 - 2 * open_half_deg)
    n = segs
    ring_o, ring_i = [], []
    for i in range(n + 1):
        a = a0 + sweep * i / n
        ring_o.append(bm.verts.new((r_out * cos(a), r_out * sin(a), z_top)))
        ring_i.append(bm.verts.new((r_in * cos(a), r_in * sin(a), z_top)))
    faces = []
    for i in range(n):
        f = bm.faces.new((ring_i[i], ring_i[i + 1], ring_o[i + 1], ring_o[i]))
        faces.append(f)
    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    verts = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=V((0, 0, z_bot - z_top)), verts=verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return build_mesh(name, bm)

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

def _obj_uv(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs["Object"]

def _weathering(nt, strength=0.4, lo=0.70, hi=1.15, streak=False):
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.4 if streak else 0.55
    noise.inputs["Detail"].default_value = 6.0
    if streak:
        # stretch noise vertically -> rain-streak stains running down the wall
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (3.5, 3.5, 0.7)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30 if streak else 0.32
    ramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    ramp.color_ramp.elements[1].position = 0.62 if streak else 0.72
    ramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    return ramp.outputs["Color"], strength

def masonry(name, c1, c2, mortar, rough=0.86, bw=0.5, rh=0.25, weather=0.45, bump=0.08, lo=0.70, hi=1.15, streak=False):
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
    brick.inputs["Brick Width"].default_value = bw
    brick.inputs["Row Height"].default_value = rh
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Color1"].default_value = (*c1, 1.0)
    brick.inputs["Color2"].default_value = (*c2, 1.0)
    brick.inputs["Mortar"].default_value = (*mortar, 1.0)
    nt.links.new(uv, brick.inputs["Vector"])
    wcol, wf = _weathering(nt, strength=weather, lo=lo, hi=hi, streak=streak)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = wf
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(wcol, mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = bump
    nt.links.new(brick.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat

def tile_roof(name, c1, c2, rough=0.52):
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
    brick.inputs["Brick Width"].default_value = 0.36
    brick.inputs["Row Height"].default_value = 0.115
    brick.inputs["Mortar Size"].default_value = 0.012
    brick.inputs["Color1"].default_value = (*c1, 1.0)
    brick.inputs["Color2"].default_value = (*c2, 1.0)
    brick.inputs["Mortar"].default_value = (0.085, 0.07, 0.055, 1.0)
    nt.links.new(uv, brick.inputs["Vector"])
    wcol, wf = _weathering(nt, strength=0.3)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = wf
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(wcol, mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bumpn = nt.nodes.new("ShaderNodeBump")
    bumpn.inputs["Strength"].default_value = 0.12
    nt.links.new(brick.outputs["Fac"], bumpn.inputs["Height"])
    nt.links.new(bumpn.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat

def build_materials():
    global MAT
    MAT = {}
    MAT["plaster"] = masonry("DenMau_Plaster", (0.315, 0.300, 0.272), (0.245, 0.232, 0.210),
                             (0.255, 0.245, 0.228), weather=0.55, lo=0.62, hi=1.18, streak=True)
    MAT["gate"]    = masonry("DenMau_GateMasonry", (0.335, 0.318, 0.286), (0.262, 0.248, 0.222),
                             (0.27, 0.26, 0.242), bw=0.46, rh=0.23, weather=0.6, lo=0.60, hi=1.22, streak=True)
    MAT["stone"]   = masonry("DenMau_Stone", (0.360, 0.353, 0.338), (0.290, 0.285, 0.275),
                             (0.255, 0.25, 0.24), bw=0.62, rh=0.30, weather=0.45, bump=0.1)
    MAT["tile"]    = tile_roof("DenMau_Tile", (0.052, 0.056, 0.050), (0.080, 0.085, 0.075))
    MAT["wood"]    = pbr("DenMau_Wood_Dark", (0.052, 0.036, 0.024), rough=0.8)
    MAT["door"]    = pbr("DenMau_Door_Red", (0.148, 0.030, 0.022), rough=0.7)
    MAT["flag_r"]  = pbr("DenMau_Flag_Red", (0.43, 0.032, 0.022), rough=0.75)
    MAT["flag_y"]  = pbr("DenMau_Flag_Yellow", (0.56, 0.38, 0.05), rough=0.75)
    MAT["leaf"]    = pbr("DenMau_Foliage", (0.070, 0.135, 0.046), rough=0.85)
    MAT["trunk"]   = pbr("DenMau_Trunk", (0.16, 0.125, 0.09), rough=0.9)
    MAT["gold"]    = pbr("DenMau_Gold", (0.72, 0.55, 0.20), rough=0.4, metal=0.85)
    MAT["silt"]    = pbr("DenMau_Pond_Bed", (0.055, 0.058, 0.042), rough=0.95)
    MAT["water"]   = pbr("DenMau_Water", (0.030, 0.048, 0.036), rough=0.13)
    # ground: fired-brick courtyard paving
    MAT["ground"]  = masonry("DenMau_Ground", (0.300, 0.258, 0.212), (0.238, 0.200, 0.163),
                             (0.175, 0.15, 0.125), bw=0.34, rh=0.17, weather=0.5, bump=0.06)
    MAT["ground"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.93
    MAT["ridge"]   = pbr("DenMau_Ridge_Lime", (0.78, 0.765, 0.735), rough=0.78)
    MAT["lantern"] = pbr("DenMau_Lantern_Red", (0.42, 0.032, 0.022), rough=0.55)
    MAT["urn"]     = pbr("DenMau_Urn_Bronze", (0.105, 0.080, 0.042), rough=0.35, metal=0.9)

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
build_materials()

COL = {}
for cname in ["Gate", "Temple", "Lake", "Grounds", "Trees", "Flags",
              "Lighting", "Cameras", "Environment"]:
    COL[cname] = bpy.data.collections.new(cname)
    scene.collection.children.link(COL[cname])

def place(obj, cname):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    COL[cname].objects.link(obj)
    return obj

# ---------------------------------------------------------------- dimensions
GATE_W, GATE_DEPTH = 9.6, 3.2
MAIN_HW, MAIN_SPRING = 1.075, 1.5          # main vault half-width / springer z
SIDE_HW, SIDE_SPRING = 0.725, 1.25         # side vaults
SIDE_CX = 3.05                              # side opening centres
L1_TOP = 5.5                                # gate wall top (centre portion)
SIDE_TOP = 3.55                             # gate wall top (side portions)
S2_W, S2_H = 7.0, 1.8                       # story-2 pavilion (wide, massive — like reference)
S3_W, S3_H = 5.0, 1.55                      # story-3 pavilion

T_W, T_D, T_H1, T_Z0 = 15.0, 9.0, 5.3, 0.75
TY = 22.5                                   # temple centre y
BELV_W, BELV_H = 4.2, 2.6

L_Y, L_RI, L_RO, L_OPEN = -12.0, 9.5, 16.0, 50.0   # lake centre/radii/opening half-angle
WALK_W = 2.6
GROUND_Z = -0.02

# ================================================================ 1. GROUND
gnd = box("Ground_Plane", (110, 110, 0.1), (0, 0, GROUND_Z - 0.05))
place(gnd, "Environment")
gnd.data.materials.append(MAT["ground"])

# ================================================================ 2. LAKE (hồ Bán Nguyệt)
water = crescent("Lake_Water", L_RI, L_RO, L_OPEN, GROUND_Z + 0.10, GROUND_Z - 0.35)
water.location = (0, L_Y, 0)
place(water, "Lake")
water.data.materials.append(MAT["water"])
shade_smooth(water)
bed = crescent("Lake_Bed", L_RI - 0.25, L_RO + 0.25, L_OPEN, GROUND_Z - 0.30, GROUND_Z - 0.85)
bed.location = (0, L_Y, 0)
place(bed, "Lake")
bed.data.materials.append(MAT["silt"])
# stone coping along both arcs (thin crescent bands, proud of the water)
for tag, ri, ro in (("Outer", L_RO - 0.08, L_RO + 0.45), ("Inner", L_RI - 0.45, L_RI + 0.08)):
    cop = crescent(f"Lake_Coping_{tag}", ri, ro, L_OPEN, GROUND_Z + 0.15, GROUND_Z - 0.45, segs=48)
    cop.location = (0, L_Y, 0)
    place(cop, "Lake")
    cop.data.materials.append(MAT["stone"])
    shade_smooth(cop)

# balustrade posts + rail around the OUTER coping (reference shows a full railing)
def lake_balustrade():
    segs = 54
    a0 = radians(90 + L_OPEN)
    sweep = radians(360 - 2 * L_OPEN)
    rr = L_RO + 0.40
    tops = []
    for i in range(segs + 1):
        a = a0 + sweep * i / segs
        x, y = rr * cos(a), L_Y + rr * sin(a)
        if i % 3 == 0:
            post = cylinder(f"LakeRail_Post_{i}", 0.075, 0.62, (x, y, GROUND_Z + 0.31), verts=7)
            post.data.materials.append(MAT["stone"])
            place(post, "Lake")
        if i < segs:
            tops.append((x, y))
    for i in range(len(tops) - 1):
        x, y = tops[i]
        x2, y2 = tops[i + 1]
        ln = math.hypot(x2 - x, y2 - y)
        ang = math.atan2(y2 - y, x2 - x)
        rail = box(f"LakeRail_Seg_{i}", (ln, 0.085, 0.075), ((x + x2) / 2, (y + y2) / 2, GROUND_Z + 0.62),
                   rot=(0, 0, ang))
        rail.data.materials.append(MAT["stone"])
        place(rail, "Lake")
lake_balustrade()

# lotus pads on the water (flat dark-green discs, as in the reference photos)
lot_seed = random.Random(7)
for i in range(16):
    a = radians(90 + L_OPEN) + radians(360 - 2 * L_OPEN) * lot_seed.random()
    rr = L_RI + 0.8 + (L_RO - L_RI - 1.6) * lot_seed.random()
    lx, ly = rr * cos(a), L_Y + rr * sin(a)
    if abs(lx) < WALK_W / 2 + 0.7:
        continue  # keep the walkway clear
    pad = cylinder(f"Lotus_Pad_{i}", lot_seed.uniform(0.22, 0.45), 0.03,
                   (lx, ly, GROUND_Z + 0.13), verts=9)
    pad.data.materials.append(MAT["leaf"])
    place(pad, "Lake")

# walkway across the crescent opening: from front edge (y=-21) to gate steps (y=+1.6)
wx = WALK_W / 2
deck = box("Walkway_Deck", (WALK_W, 23.0, 0.18), (0, (L_Y + 1.6) / 2 + 0.9, GROUND_Z + 0.05))
place(deck, "Lake")
deck.data.materials.append(MAT["stone"])
for sgn in (-1, 1):
    par = box(f"Walkway_Parapet_{sgn}", (0.30, 23.0, 0.40), (sgn * (wx + 0.15), (L_Y + 1.6) / 2 + 0.9, GROUND_Z + 0.28))
    place(par, "Lake")
    par.data.materials.append(MAT["stone"])
    for k in range(16):   # parapet posts
        py = (L_Y + 1.6) / 2 + 0.9 - 11 + k * (22 / 15)
        pp = cylinder(f"WalkParapet_Post_{sgn}_{k}", 0.075, 0.52, (sgn * (wx + 0.15), py, GROUND_Z + 0.36), verts=6)
        pp.data.materials.append(MAT["stone"])
        place(pp, "Lake")

# coping-end piers where the walkway meets the water (little stone posts)
for sgn in (-1, 1):
    for r_ in (L_RI - 0.3, L_RO + 0.3):
        a_end = radians(90 + L_OPEN * (1 if sgn > 0 else -1))
        px, py = r_ * cos(a_end), L_Y + r_ * sin(a_end)
        post = cylinder(f"Lake_EndPost_{sgn}_{r_:.0f}", 0.16, 0.9, (px, py, GROUND_Z + 0.43), verts=8)
        post.data.materials.append(MAT["stone"])
        place(post, "Lake")

# ================================================================ 3. GATE (nghi môn)
place(box("Gate_Plinth", (GATE_W + 2.6, GATE_DEPTH + 2.4, 0.55), (0, 0, 0.20)), "Gate")
place(box("Gate_Step_F", (GATE_W + 1.2, 1.1, 0.16), (0, GATE_DEPTH / 2 + 0.6, 0.08)), "Gate")
place(box("Gate_Step_B", (GATE_W + 1.2, 1.1, 0.16), (0, -(GATE_DEPTH / 2 + 0.6), 0.08)), "Gate")

# STEPPED massing (matches reference): tall centre bay + lower side bays
centre_w = 2 * (SIDE_CX - SIDE_HW)              # 4.65 centre block
gate_centre = arch_wall(
    "Gate_Wall_Centre", centre_w, GATE_DEPTH, L1_TOP,
    openings=[(0.0, MAIN_HW, 'arc', MAIN_SPRING, MAIN_HW)],
    slices=18, pier_mat=MAT["gate"])
place(gate_centre, "Gate")
SIDE_CX2 = 3.3                                  # side opening centres (world x)
side_w = GATE_W / 2 - (SIDE_CX - SIDE_HW)       # 2.475 from centre block edge to gate end
for sgn in (-1, 1):
    blk_x = sgn * (GATE_W / 2 - side_w / 2)     # world x of this side block's centre
    blk = arch_wall(f"Gate_Wall_Side_{sgn}", side_w, GATE_DEPTH, SIDE_TOP,
                    openings=[(sgn * SIDE_CX2 - blk_x, SIDE_HW, 'arc', SIDE_SPRING, SIDE_HW)],
                    slices=10, pier_mat=MAT["gate"])
    blk.location = (blk_x, 0, 0)
    place(blk, "Gate")

# cornice bands: full-width at side-top; centre block continues above
place(box("Gate_Cornice_Side", (GATE_W + 0.7, GATE_DEPTH + 0.5, 0.30), (0, 0, SIDE_TOP + 0.15)), "Gate")
place(box("Gate_Cornice_Centre", (2 * (SIDE_CX - SIDE_HW) + 1.0, GATE_DEPTH + 0.4, 0.28), (0, 0, L1_TOP + 0.14)), "Gate")
c1_ = bpy.data.objects["Gate_Cornice_Side"]; c1_.data.materials.append(MAT["stone"])
c2_ = bpy.data.objects["Gate_Cornice_Centre"]; c2_.data.materials.append(MAT["stone"])

# dark reveals behind each vault so tunnels read deep
for tag, cx, hw, sz in (("Main", 0.0, MAIN_HW, MAIN_SPRING), ("L", -SIDE_CX2, SIDE_HW, SIDE_SPRING), ("R", SIDE_CX2, SIDE_HW, SIDE_SPRING)):
    rv = box(f"Gate_Reveal_{tag}", (hw * 2 - 0.12, 0.35, sz + hw + 0.2), (cx, GATE_DEPTH / 2 - 0.45, (sz + hw) / 2))
    rv.data.materials.append(MAT["wood"])
    place(rv, "Gate")

# --- story 2 + story 3 pavilions (chồng diêm) over the centre bay
S2_Z = L1_TOP + 0.30
place(box("Gate_S2_Body", (S2_W, GATE_DEPTH - 0.7, S2_H), (0, 0, S2_Z + S2_H / 2)), "Gate")
r1 = hip_roof("Gate_Roof_S2", S2_W / 2 + 1.1, GATE_DEPTH / 2 + 0.55, 1.05, S2_Z + S2_H - 0.05, thick=0.20)
place(r1, "Gate")

S3_Z = S2_Z + S2_H + 0.65
place(box("Gate_S3_Body", (S3_W, GATE_DEPTH - 1.2, S3_H), (0, 0, S3_Z + S3_H / 2)), "Gate")
# moon window rings front + back of story 3
for sgn in (-1, 1):
    bpy.ops.mesh.primitive_torus_add(align='WORLD',
        location=(0, sgn * (GATE_DEPTH / 2 - 0.5), S3_Z + 1.02),
        rotation=(radians(90), 0, 0), major_radius=0.60, minor_radius=0.12)
    tor = bpy.context.object
    tor.name = f"Gate_MoonRing_{sgn}"
    place(tor, "Gate")
    tor.data.materials.append(MAT["stone"])
    disc = cylinder(f"Gate_MoonDark_{sgn}", 0.56, 0.05, (0, sgn * (GATE_DEPTH / 2 - 0.52), S3_Z + 1.02),
                    verts=24, rot=(radians(90), 0, 0))
    disc.data.materials.append(MAT["wood"])
    place(disc, "Gate")
r2 = hip_roof("Gate_Roof_S3", S3_W / 2 + 0.95, GATE_DEPTH / 2 + 0.35, 0.95, S3_Z + S3_H - 0.05, thick=0.20)
place(r2, "Gate")

# side pavilions: cap + small roof over each stepped side bay
for sgn in (-1, 1):
    place(box(f"Gate_SideCap_{sgn}", (side_w + 0.7, GATE_DEPTH - 0.7, 0.85),
              (sgn * (GATE_W / 2 - side_w / 2), 0, SIDE_TOP + 0.30 + 0.42)), "Gate")
    r = hip_roof(f"Gate_Roof_Side_{sgn}", (side_w + 0.7) / 2 + 0.5, GATE_DEPTH / 2 + 0.1, 0.85,
                 SIDE_TOP + 1.15 - 0.04, thick=0.18)
    r.location.x = sgn * (GATE_W / 2 - side_w / 2)
    place(r, "Gate")

# đao flame tips on roof corners
def dao_tips(roof_name, half_w, half_d, rise, z, curve=0.8, off_x=0.0):
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (half_w - 0.02), sy * (half_d - 0.02)
            u = max(abs(x) / half_w, abs(y) / half_d)
            h = rise * (1 - u) + curve * rise * 0.9 * ((abs(x) / half_w) * (abs(y) / half_w)) ** 4
            tip = cylinder(f"{roof_name}_Dao_{sx}_{sy}", 0.04, 0.38,
                           (off_x + x, y, z + h + 0.15), verts=7,
                           rot=(radians(38) * sy, radians(-38) * sx, 0))
            tip.data.materials.append(MAT["tile"])
            place(tip, "Gate")
dao_tips("Gate_Roof_S2", S2_W / 2 + 1.1, GATE_DEPTH / 2 + 0.55, 1.05, S2_Z + S2_H - 0.05)
dao_tips("Gate_Roof_S3", S3_W / 2 + 0.95, GATE_DEPTH / 2 + 0.35, 0.95, S3_Z + S3_H - 0.05)
for sgn in (-1, 1):
    dao_tips(f"Gate_Roof_Side_{sgn}", (side_w + 0.7) / 2 + 0.5, GATE_DEPTH / 2 + 0.1, 0.85,
             SIDE_TOP + 1.15 - 0.04, off_x=sgn * (GATE_W / 2 - side_w / 2))

# ridges + finial
place(box("Gate_Ridge_S2", (S2_W + 1.4, 0.20, 0.14), (0, 0, S2_Z + S2_H + 1.02)), "Gate")
place(box("Gate_Ridge_S3", (S3_W + 1.1, 0.18, 0.12), (0, 0, S3_Z + S3_H + 0.92)), "Gate")
fin = sphere("Gate_Finial", 0.14, (0, 0, S3_Z + S3_H + 1.10))
fin.data.materials.append(MAT["gold"])
place(fin, "Gate")
spire = cylinder("Gate_Finial_Spire", 0.035, 0.5, (0, 0, S3_Z + S3_H + 1.42), verts=8)
spire.data.materials.append(MAT["gold"])
place(spire, "Gate")

# tablets (hảnh chữ) over the vaults
tb = box("Gate_Tablet_Main", (1.9, 0.10, 0.72), (0, GATE_DEPTH / 2 + 0.03, MAIN_SPRING + 1.1))
tb.data.materials.append(MAT["stone"])
place(tb, "Gate")
for sgn in (-1, 1):
    t2 = box(f"Gate_Tablet_Side_{sgn}", (1.2, 0.10, 0.5),
             (sgn * SIDE_CX2, GATE_DEPTH / 2 + 0.03, SIDE_SPRING + 0.75))
    t2.data.materials.append(MAT["stone"])
    place(t2, "Gate")

# material fallback for remaining gate meshes
for o in bpy.data.objects:
    if o.type != 'MESH' or (o.data.materials and any(o.data.materials)):
        continue
    if o.name.startswith("Gate_"):
        o.data.materials.append(MAT["gate"])

# ================================================================ 4. TEMPLE
place(box("Temple_Plinth", (T_W + 2.0, T_D + 2.0, T_Z0), (0, TY, T_Z0 / 2)), "Temple")
for k in range(3):
    st = box(f"Temple_Step_{k}", (T_W - 2 + (2 - k) * 1.1, 0.72, 0.16 * (k + 1)),
             (0, TY - T_D / 2 - 0.55 - k * 0.68, 0.08 * (k + 1)))
    st.data.materials.append(MAT["stone"])
    place(st, "Temple")

tz = T_Z0
front_y = TY - T_D / 2
# dark interior core (seen through arches)
place(box("Temple_Interior", (T_W - 1.2, T_D - 1.6, T_H1 - 0.2), (0, TY + 0.3, tz + (T_H1 - 0.2) / 2)), "Temple")
ti = bpy.data.objects["Temple_Interior"]
ti.data.materials.append(MAT["wood"])
# side + back walls
for tag, loc, size in (("Back", (0, TY + T_D / 2 - 0.4, tz + T_H1 / 2), (T_W, 0.8, T_H1)),
                       ("L", (-T_W / 2 + 0.4, TY, tz + T_H1 / 2), (0.8, T_D - 1.6, T_H1)),
                       ("R", (T_W / 2 - 0.4, TY, tz + T_H1 / 2), (0.8, T_D - 1.6, T_H1))):
    w = box(f"Temple_Wall_{tag}", size, loc)
    w.data.materials.append(MAT["plaster"])
    place(w, "Temple")
# front wall with 3 vaulted loggias + 2 side door openings (real through-openings)
fw = arch_wall(
    "Temple_FrontWall", T_W, 0.9, T_H1,
    openings=[(-3.4, 1.3, 'arc', 1.7, 1.3), (0.0, 1.3, 'arc', 1.7, 1.3), (3.4, 1.3, 'arc', 1.7, 1.3),
              (-6.1, 0.85, 'rect', 2.4, 0.0), (6.1, 0.85, 'rect', 2.4, 0.0)],
    slices=34, pier_mat=MAT["plaster"])
fw.location = (0, front_y + 0.45, tz)
place(fw, "Temple")
# red doors in the side openings
for sgn in (-1, 1):
    d = box(f"Temple_SideDoor_{sgn}", (1.55, 0.10, 2.3), (sgn * 6.1, front_y + 0.45, tz + 1.15))
    d.data.materials.append(MAT["door"])
    place(d, "Temple")
# interior floor line visible through arches
fl = box("Temple_FloorLine", (T_W - 1.4, 0.5, 0.08), (0, TY, tz + 0.04))
fl.data.materials.append(MAT["stone"])
place(fl, "Temple")

# upper terrace
tz2 = tz + T_H1
slab = box("Temple_Terrace", (T_W - 1.0, T_D - 2.2, 0.35), (0, TY, tz2 + 0.17))
slab.data.materials.append(MAT["plaster"])
place(slab, "Temple")
place(box("Temple_TerraceBack", (T_W - 1.6, 0.6, 2.4), (0, TY + (T_D - 2.2) / 2 - 0.3, tz2 + 0.35 + 1.2)), "Temple")
tbk = bpy.data.objects["Temple_TerraceBack"]
tbk.data.materials.append(MAT["plaster"])

def rail_x(tag, x0, x1, y, z, col="Temple"):
    ln = x1 - x0
    t = box(f"{tag}_Top", (ln, 0.15, 0.10), ((x0 + x1) / 2, y, z + 0.52))
    b = box(f"{tag}_Bot", (ln, 0.13, 0.08), ((x0 + x1) / 2, y, z + 0.07))
    n = max(2, int(ln / 0.28))
    for i in range(n + 1):
        p = cylinder(f"{tag}_Post_{i}", 0.045, 0.50, (x0 + i * ln / n, y, z + 0.25), verts=6)
        p.data.materials.append(MAT["stone"])
        place(p, col)
    for o in (t, b):
        o.data.materials.append(MAT["stone"])
        place(o, col)

def rail_y(tag, y0, y1, x, z, col="Temple"):
    ln = y1 - y0
    t = box(f"{tag}_Top", (0.15, ln, 0.10), (x, (y0 + y1) / 2, z + 0.52))
    b = box(f"{tag}_Bot", (0.13, ln, 0.08), (x, (y0 + y1) / 2, z + 0.07))
    n = max(2, int(ln / 0.28))
    for i in range(n + 1):
        p = cylinder(f"{tag}_Post_{i}", 0.045, 0.50, (x, y0 + i * ln / n, z + 0.25), verts=6)
        p.data.materials.append(MAT["stone"])
        place(p, col)
    for o in (t, b):
        o.data.materials.append(MAT["stone"])
        place(o, col)

tz2t = tz2 + 0.35
hx = (T_W - 1.0) / 2
hy = (T_D - 2.2) / 2
rail_x("TerraceRail_F", -hx, hx, TY - hy, tz2t)
rail_x("TerraceRail_B", -hx, hx, TY + hy, tz2t)
rail_y("TerraceRail_L", TY - hy, TY + hy, -hx, tz2t)
rail_y("TerraceRail_R", TY - hy, TY + hy, hx, tz2t)

# belvedere + wings on the terrace
place(box("Temple_Belvedere", (BELV_W, 3.4, BELV_H), (0, TY, tz2t + BELV_H / 2)), "Temple")
bv = bpy.data.objects["Temple_Belvedere"]
bv.data.materials.append(MAT["plaster"])
rb = hip_roof("Temple_Belvedere_Roof", BELV_W / 2 + 0.9, 2.3, 0.85, tz2t + BELV_H - 0.04)
rb.location = (0, TY, 0)
place(rb, "Temple")
rail_x("Belv_Rail", -BELV_W / 2, BELV_W / 2, TY - 1.7, tz2t + BELV_H)

# small red flags on the terrace front edge (as in the reference photos)
def terrace_flag(x, h=2.4):
    pole = cylinder(f"TerraceFlagPole_{x:.0f}", 0.028, h, (x, TY - hy + 0.3, tz2t + h / 2), verts=7)
    pole.data.materials.append(MAT["wood"])
    place(pole, "Flags")
    bm = bmesh.new()
    nx, ny = 8, 5
    verts = []
    for iy in range(ny + 1):
        row = []
        for ix in range(nx + 1):
            row.append(bm.verts.new((ix / nx * 0.85 - 0.03, 0, 0.55 - iy / ny * 0.55)))
        verts.append(row)
    for iy in range(ny):
        for ix in range(nx):
            bm.faces.new((verts[iy][ix], verts[iy][ix + 1],
                          verts[iy + 1][ix + 1], verts[iy + 1][ix]))
    cloth = build_mesh(f"TerraceFlag_{x:.0f}", bm, (x, TY - hy + 0.3, tz2t + h - 0.75))
    cloth.data.materials.append(MAT["flag_r"])
    cloth.rotation_mode = 'XYZ'
    place(cloth, "Flags")
    return cloth

flag_objs = []
for fx in (-4.6, -2.3, 2.3, 4.6):
    flag_objs.append(terrace_flag(fx))
for sgn in (-1, 1):
    xw = sgn * (BELV_W / 2 + 1.7)
    place(box(f"Temple_UpperWing_{sgn}", (2.7, 3.2, 1.5), (xw, TY, tz2t + 0.75)), "Temple")
    wng = bpy.data.objects[f"Temple_UpperWing_{sgn}"]
    wng.data.materials.append(MAT["plaster"])
    rw = hip_roof(f"Temple_Wing_Roof_{sgn}", 1.75, 1.9, 0.7, tz2t + 1.5 - 0.04)
    rw.location = (xw, TY, 0)
    place(rw, "Temple")

# ================================================================ 5. FLAGPOLES + FLAGS
def flagpole(x, y, h=9.0, flag_mat="flag_r"):
    pole = cylinder(f"FlagPole_{x:.0f}_{y:.0f}", 0.055, h, (x, y, GROUND_Z + h / 2), verts=8)
    pole.data.materials.append(MAT["trunk"])
    place(pole, "Flags")
    ball = sphere(f"FlagBall_{x:.0f}_{y:.0f}", 0.09, (x, y, GROUND_Z + h + 0.05), segs=10, rings=6)
    ball.data.materials.append(MAT["gold"])
    place(ball, "Flags")
    bm = bmesh.new()
    nx, ny = 10, 6
    verts = []
    for iy in range(ny + 1):
        row = []
        for ix in range(nx + 1):
            row.append(bm.verts.new((ix / nx * 1.5 - 0.05, 0, 0.95 - iy / ny * 0.95)))
        verts.append(row)
    for iy in range(ny):
        for ix in range(nx):
            bm.faces.new((verts[iy][ix], verts[iy][ix + 1],
                          verts[iy + 1][ix + 1], verts[iy + 1][ix]))
    cloth = build_mesh(f"Flag_Cloth_{x:.0f}_{y:.0f}", bm, (x, y, GROUND_Z + h - 1.15))
    cloth.data.materials.append(MAT[flag_mat])
    cloth.rotation_mode = 'XYZ'
    place(cloth, "Flags")
    return cloth

flag_objs.append(flagpole(-10.5, 6.0, 9.0, "flag_r"))
flag_objs.append(flagpole(10.5, 6.0, 9.0, "flag_y"))
flag_objs.append(flagpole(-6.5, -15.5, 8.0, "flag_r"))
flag_objs.append(flagpole(6.5, -15.5, 8.0, "flag_y"))

# ================================================================ 6. WALLS + TREES
for sgn in (-1, 1):
    w = box(f"PerimWall_{sgn}", (13.5, 0.5, 1.5), (sgn * (GATE_W / 2 + 7.1), 2.0, 0.75))
    w.data.materials.append(MAT["plaster"])
    place(w, "Grounds")
    cap = box(f"PerimWall_Cap_{sgn}", (13.7, 0.72, 0.14), (sgn * (GATE_W / 2 + 7.1), 2.0, 1.57))
    cap.data.materials.append(MAT["stone"])
    place(cap, "Grounds")

def tree(name, x, y, h=4.5, r=2.2, seed=1):
    rnd = random.Random(seed)
    trunk = cylinder(f"{name}_Trunk", 0.22, h, (x, y, GROUND_Z + h / 2), verts=7)
    trunk.data.materials.append(MAT["trunk"])
    trunk.rotation_euler = (rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), 0)
    place(trunk, "Trees")
    for k, (dz, sr) in enumerate(((h * 0.55, r), (h * 0.75, r * 0.8), (h * 0.95, r * 0.55))):
        blob = sphere(f"{name}_Foliage_{k}", sr,
                      (x + rnd.uniform(-0.5, 0.5), y + rnd.uniform(-0.5, 0.5), GROUND_Z + dz),
                      segs=9, rings=6)
        blob.scale = (1.0, 1.0, 0.75)
        blob.data.materials.append(MAT["leaf"])
        blob.rotation_euler = (0, 0, rnd.uniform(0, 3.14))
        place(blob, "Trees")

tree("Tree_FL", -14.0, 5.0, h=5.5, r=2.6, seed=11)
tree("Tree_FR", 14.0, 5.0, h=5.2, r=2.4, seed=12)
tree("Tree_BL", -11.5, 16.5, h=5.8, r=2.7, seed=13)
tree("Tree_BR", 11.5, 16.5, h=5.6, r=2.5, seed=14)
tree("Tree_FarL", -20.0, 28.0, h=6.2, r=2.9, seed=15)
tree("Tree_FarR", 20.0, 28.0, h=6.0, r=2.8, seed=16)
tree("Tree_OutL", -19.0, -20.0, h=5.0, r=2.4, seed=17)
tree("Tree_OutR", 19.0, -20.0, h=4.8, r=2.3, seed=18)

# ================================================================ 6b. DETAIL PASS
# --- window insets on the gate story walls (break up blank masonry)
for sgn in (-1, 1):   # S2 story: 3 windows front + back, 1 each side
    for k in (-1, 0, 1):
        w = box(f"Gate_S2_Window_F_{sgn}_{k}", (0.72, 0.10, 0.95),
                (k * 1.55, sgn * (GATE_DEPTH / 2 - 0.36 + 0.02), S2_Z + S2_H * 0.52))
        w.data.materials.append(MAT["wood"])
        place(w, "Gate")
        wf = box(f"Gate_S2_WinFrame_F_{sgn}_{k}", (0.86, 0.06, 1.09),
                 (k * 1.55, sgn * (GATE_DEPTH / 2 - 0.36), S2_Z + S2_H * 0.52))
        wf.data.materials.append(MAT["ridge"])
        place(wf, "Gate")
for sgn in (-1, 1):   # S2 sides
    w = box(f"Gate_S2_Window_E_{sgn}", (0.10, 0.9, 0.95),
            (sgn * (S2_W / 2 + 0.02), 0, S2_Z + S2_H * 0.52))
    w.data.materials.append(MAT["wood"])
    place(w, "Gate")
for sgn in (-1, 1):   # S3 story: small windows flanking the moon window
    for k in (-1, 1):
        w = box(f"Gate_S3_Window_{sgn}_{k}", (0.5, 0.09, 0.6),
                (k * 1.25, sgn * (GATE_DEPTH / 2 - 0.56 + 0.02), S3_Z + S3_H * 0.62))
        w.data.materials.append(MAT["wood"])
        place(w, "Gate")
        wf2 = box(f"Gate_S3_WinFrame_{sgn}_{k}", (0.62, 0.05, 0.72),
                  (k * 1.25, sgn * (GATE_DEPTH / 2 - 0.56), S3_Z + S3_H * 0.62))
        wf2.data.materials.append(MAT["ridge"])
        place(wf2, "Gate")

# --- ridge bars along the apex of the stacked pavilion roofs
for tag, hw2, z_ap in (("S2", S2_W / 2 + 1.1, S2_Z + S2_H + 1.05),
                       ("S3", S3_W / 2 + 0.95, S3_Z + S3_H + 0.95)):
    rb2 = box(f"Gate_RidgeBar_{tag}", (hw2 * 2 - 0.3, 0.16, 0.12), (0, 0, z_ap))
    rb2.data.materials.append(MAT["ridge"])
    place(rb2, "Gate")
# --- white-lime arch surrounds (the signature look in the reference photos)
arch_trim("GateTrim_Main", 0.0, MAIN_HW, MAIN_SPRING, GATE_DEPTH / 2)
arch_trim("GateTrim_Main_B", 0.0, MAIN_HW, MAIN_SPRING, -GATE_DEPTH / 2 - 0.14)
for sgn in (-1, 1):
    arch_trim(f"GateTrim_Side_{sgn}", sgn * SIDE_CX2, SIDE_HW, SIDE_SPRING, GATE_DEPTH / 2)
for k in (-3.4, 0.0, 3.4):
    arch_trim(f"TempleTrim_{k:.0f}", k, 1.3, 1.7, front_y - 0.02)

# --- white fascia bands + apex caps on every small roof
white_fascia("Fas_S2", S2_W / 2 + 1.1, GATE_DEPTH / 2 + 0.55, S2_Z + S2_H - 0.02)
white_fascia("Fas_S3", S3_W / 2 + 0.95, GATE_DEPTH / 2 + 0.35, S3_Z + S3_H - 0.02)
for sgn in (-1, 1):
    white_fascia(f"Fas_Side_{sgn}", (side_w + 0.7) / 2 + 0.5, GATE_DEPTH / 2 + 0.1,
                 SIDE_TOP + 1.15 - 0.02, cx=sgn * (GATE_W / 2 - side_w / 2))
white_fascia("Fas_Belv", BELV_W / 2 + 0.9, 2.3, tz2t + BELV_H - 0.02, cy=TY)
for sgn in (-1, 1):
    white_fascia(f"Fas_Wing_{sgn}", 1.75, 1.9, tz2t + 1.5 - 0.02,
                 cx=sgn * (BELV_W / 2 + 1.7), cy=TY)

apex_cap("Cap_S2", 0, 0, S2_Z + S2_H + 1.18)
apex_cap("Cap_S3", 0, 0, S3_Z + S3_H + 1.02)
apex_cap("Cap_Belv", 0, TY, tz2t + BELV_H + 0.83)
for sgn in (-1, 1):
    apex_cap(f"Cap_Wing_{sgn}", sgn * (BELV_W / 2 + 1.7), TY, tz2t + 1.5 + 0.68)

# --- moon window detail: cross mullions + stone sill
for sgn in (-1, 1):
    yf = sgn * (GATE_DEPTH / 2 - 0.5)
    for horiz in (True, False):
        mull = box(f"Gate_MoonMullion_{sgn}_{horiz}",
                   (1.10, 0.06, 0.055) if horiz else (0.055, 0.06, 1.10),
                   (0, yf, S3_Z + 1.02))
        mull.data.materials.append(MAT["ridge"])
        place(mull, "Gate")
    sill = box(f"Gate_MoonSill_{sgn}", (1.5, 0.28, 0.12), (0, yf, S3_Z + 0.32))
    sill.data.materials.append(MAT["stone"])
    place(sill, "Gate")

# --- inscription tablets get frames + gold character bars
for tag, cx, cw, ch, cz in (("Main", 0.0, 1.9, 0.72, MAIN_SPRING + 1.1),
                            ("L", -SIDE_CX2, 1.2, 0.5, SIDE_SPRING + 0.75),
                            ("R", SIDE_CX2, 1.2, 0.5, SIDE_SPRING + 0.75)):
    fr = box(f"Gate_TabletFrame_{tag}", (cw + 0.22, 0.07, ch + 0.22),
             (cx, GATE_DEPTH / 2 + 0.06, cz))
    fr.data.materials.append(MAT["ridge"])
    place(fr, "Gate")
    n_chars = 3 if tag == "Main" else 1
    for i in range(n_chars):
        bar = box(f"Gate_TabletChar_{tag}_{i}", (ch * 0.42, 0.03, ch * 0.42),
                  (cx - cw / 2 + cw / (n_chars + 1) * (i + 1), GATE_DEPTH / 2 + 0.11, cz))
        bar.data.materials.append(MAT["gold"])
        place(bar, "Gate")

# --- hanging red lanterns under the gate roofs + terrace
lans = []
for sx in (-1, 1):
    for sy in (-1, 1):
        lans.append(hanging_lantern(f"HangingLantern_GateC_{sx}_{sy}",
                    sx * (S2_W / 2 + 0.55), sy * (GATE_DEPTH / 2 + 0.28),
                    S2_Z + S2_H + 0.32, 1.0))
for sx in (-1, 1):
    lans.append(hanging_lantern(f"HangingLantern_GateF_{sx}",
                sx * (S3_W / 2 + 0.3), GATE_DEPTH / 2 - 0.25, S3_Z + S3_H + 0.30, 0.8))
for sx in (-2.3, 2.3, -hx + 0.5, hx - 0.5):
    lans.append(hanging_lantern(f"HangingLantern_Terrace_{sx:.0f}",
                sx, TY - hy + 0.15, tz2t + 0.60, 0.9))
flag_objs.extend(lans)

# --- lantern pillars flanking the walkway
def lantern_pillar(name, x, y):
    base = box(f"{name}_Base", (0.85, 0.85, 0.5), (x, y, GROUND_Z + 0.25))
    base.data.materials.append(MAT["stone"])
    place(base, "Grounds")
    col = cylinder(f"{name}_Column", 0.16, 2.5, (x, y, GROUND_Z + 1.75), verts=10)
    col.data.materials.append(MAT["gate"])
    place(col, "Grounds")
    cap = box(f"{name}_Cap", (0.62, 0.62, 0.14), (x, y, GROUND_Z + 3.07))
    cap.data.materials.append(MAT["ridge"])
    place(cap, "Grounds")
    box1 = box(f"{name}_Case", (0.42, 0.42, 0.55), (x, y, GROUND_Z + 3.40))
    box1.data.materials.append(MAT["gate"])
    place(box1, "Grounds")
    win1 = box(f"{name}_Window", (0.26, 0.44, 0.34), (x, y, GROUND_Z + 3.40))
    win1.data.materials.append(MAT["gold"])
    place(win1, "Grounds")
    roof = hip_roof(f"{name}_Roof", 0.42, 0.42, 0.28, GROUND_Z + 3.68, seg=4)
    place(roof, "Grounds")

lantern_pillar("Pillar_W", -4.4, -6.0)
lantern_pillar("Pillar_E", 4.4, -6.0)

# --- bronze urns (bình hương) at gate steps + terrace
def urn(name, x, y, z, s=1.0):
    foot = cylinder(f"{name}_Foot", 0.16 * s, 0.12 * s, (x, y, z + 0.06 * s), verts=10)
    foot.data.materials.append(MAT["urn"])
    place(foot, "Grounds" if z < 4 else "Temple")
    bowl = cylinder(f"{name}_Bowl", 0.34 * s, 0.34 * s, (x, y, z + 0.30 * s), verts=12)
    bowl.data.materials.append(MAT["urn"])
    place(bowl, "Grounds" if z < 4 else "Temple")
    rim = cylinder(f"{name}_Rim", 0.37 * s, 0.06 * s, (x, y, z + 0.50 * s), verts=12)
    rim.data.materials.append(MAT["gold"])
    place(rim, "Grounds" if z < 4 else "Temple")

urn("Urn_GateL", -4.6, 2.4, 0.47)
urn("Urn_GateR", 4.6, 2.4, 0.47)
urn("Urn_TempleL", -(hx - 0.9), TY - 1.0, tz2t + 0.35, 0.8)
urn("Urn_TempleR", hx - 0.9, TY - 1.0, tz2t + 0.35, 0.8)

# --- shrubs along walls and lake ends
for i, (bx_, by_, s_) in enumerate([(-17.5, 0.5, 1.0), (17.5, 0.5, 1.1), (-17.0, 3.5, 0.8),
                                    (17.0, 3.5, 0.9), (-13.0, -15.0, 1.0), (13.0, -15.0, 0.9),
                                    (-7.8, -14.0, 0.7), (7.8, -14.0, 0.8)]):
    for k in range(3):
        bl = sphere(f"Bush_{i}_{k}", 0.5 * s_ * (1 - k * 0.18),
                    (bx_ + (k - 1) * 0.45 * s_, by_ + (i % 3) * 0.2, GROUND_Z + 0.28 * s_ + k * 0.1),
                    segs=8, rings=5)
        bl.scale = (1.0, 1.0, 0.75)
        bl.data.materials.append(MAT["leaf"])
        place(bl, "Trees")

# ================================================================ 7. LIGHTING
world = bpy.data.worlds.new("Sky_World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.45, 0.62, 0.86, 1.0)
bg.inputs[1].default_value = 1.1

sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 5.0
sun.data.angle = radians(2.5)
sun.data.color = (1.0, 0.96, 0.88)
d = V((-0.42, 0.50, -0.72)).normalized()
sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
place(sun, "Lighting")

fill = bpy.data.objects.new("Fill_Sky", bpy.data.lights.new("Fill_Sky", 'AREA'))
fill.data.energy = 420
fill.data.size = 18
fill.data.color = (0.85, 0.90, 1.0)
fill.location = (-11, -13, 9)
fill.rotation_euler = Euler((radians(52), 0, radians(-28)))
place(fill, "Lighting")

# ================================================================ 8. CAMERAS
def camera(name, loc, look_at, lens=36):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.location = loc
    direction = V(look_at) - V(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 400
    place(cam, "Cameras")
    return cam

cam_a = camera("Camera_Hero", (-16.0, -25.0, 7.0), (0, 4.0, 5.2), 31)
cam_b = camera("Camera_Front", (0, -28.0, 3.8), (0, 3.0, 5.2), 34)
cam_c = camera("Camera_Temple", (20.0, 32.0, 13.0), (0, TY, 5.0), 36)
cam_d = camera("Camera_ThroughGate", (0, -15.0, 2.4), (0, 12.0, 3.4), 34)

# ================================================================ 8b. VISITORS
if "Visitors" not in COL:
    COL["Visitors"] = bpy.data.collections.new("Visitors")
    scene.collection.children.link(COL["Visitors"])

visitor_specs = [
    # walkway over the crescent lake: sightseers crossing
    (0.5, -18.5, 3, 'couple'), (-0.5, -15.0, 2, 'photographer'),
    (0.4, -11.5, 180, 'adult'), (-0.4, -8.0, 182, 'family'),
    # lakeside path: kids + parents watching the lotus
    (-13.5, -14.0, 60, 'family'), (13.0, -16.5, -45, 'couple'),
    (-15.8, -9.0, 80, 'kid'), (15.5, -11.0, -100, 'kid'), (16.8, -13.0, -60, 'kid'),
    # courtyard in front of the gate
    (-3.8, -4.5, 10, 'photographer'), (3.6, -6.0, -15, 'adult'),
    (5.2, -3.0, -80, 'couple'),
    # inside the gate tunnel + terrace beyond
    (0.3, 1.5, 4, 'adult'),
    # temple terrace: worshippers
    (-2.2, 14.0, 175, 'adult'), (2.4, 15.5, 185, 'adult'),
    (0.0, 17.0, 180, 'monk'),
    # strollers on the outer paths
    (-22.0, -2.0, 75, 'couple'), (22.0, -5.0, -75, 'photographer'),
]
add_visitors(bpy, V, box, cylinder, sphere, place, pbr, MAT, visitor_specs,
             col="Visitors", seed=919)

# ================================================================ 9. ANIMATION (flag sway)
scene.frame_start = 1
scene.frame_end = 96
for i, cloth in enumerate(flag_objs):
    ph = i * 1.3
    amp = 0.10
    for f, s in ((1, 0.0), (24, amp), (48, 0.0), (72, -amp), (96, 0.0)):
        cloth.rotation_euler.y = amp * 0.4 * sin(ph + f / 96 * 2 * pi)
        cloth.rotation_euler.z = s * cos(ph)
        cloth.keyframe_insert("rotation_euler", frame=f)
    for fc in cloth.animation_data.action.fcurves:
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

for cam, tag in ((cam_a, "hero"), (cam_b, "front"), (cam_c, "temple"), (cam_d, "throughgate")):
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
