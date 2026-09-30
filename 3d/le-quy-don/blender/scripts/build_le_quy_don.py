# -*- coding: utf-8 -*-
"""
SMART ART HERITAGE — Khu lưu niệm Lê Quý Đôn, Hưng Hà, Thái Bình.
Procedural Blender 4.5 build.

Reference-observed facts encoded:
- Memorial hall (NHÀ TRƯNG BÀY): wide 5-bay hall on a stone terrace with wide
  stair flights (3 ways up), grey stone colonnade, aged terracotta roof with
  ornate WHITE DRAGON RIDGE crest (dragon heads + flame centre), white gable
  finials, red banner, hanging lanterns.
- Old timber house (NHÀ CỔ): dark wood, aged brown tile roof, distinctive
  WHITE LIME GABLE-END walls with curved profiles, red door band; flanked by
  TWO small arched gate pavilions (grey plaster, red-tile saddled roofs,
  arched openings) — one left, one right, slightly forward.
- Forecourt: stone lantern pedestals (bàn đá) + carved stone altar (hương án).
- Plaza: red brick paving (large), green benches, garden lamps, trimmed bushes,
  young trees, perimeter green hedge.
- Overcast-bright daylight.

Ambiguities resolved: interiors dark; dragon ridge stylised to white crest
with flame ball + horns; statues omitted; benches simplified.
"""

import bpy, bmesh, os, math, sys, random
from math import radians, sin, cos, pi, sqrt, degrees
from mathutils import Vector, Euler, Matrix

V = Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(SCRIPT_DIR, "..", "le-quy-don-model.blend")
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

def shade_smooth(obj, sharp_angle=32.0):
    """Smooth shading with angle-based sharp edges (Blender 4.x: sharp edges
    split normals natively). Without this, the ridge/hip edges of the big
    roofs smear their normals and render as large grey facet patches."""
    import bmesh as _bm
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True
    bm = _bm.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            n1, n2 = e.link_faces[0].normal, e.link_faces[1].normal
            ang = degrees(n1.angle(n2))
            if ang > sharp_angle:
                e.smooth = False
        elif len(e.link_faces) == 1:
            e.smooth = False          # boundary edges always sharp
    bm.to_mesh(me)
    bm.free()

def hip_roof(name, half_w, half_d, rise, z, curve=0.8, seg=10, thick=0.18, mat="tile",
             off_x=0.0, off_y=0.0, col="Hall", ridge_frac=0.5):
    """TRUE saddle-hip roof with a real horizontal RIDGE LINE: slopes down the
    long sides, hips only at the ends (ridge_frac = ridge half-length /
    half_w). Ridge ornaments can sit flat on z+rise along the ridge segment."""
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
            corner = (abs(x) / half_w) * (abs(y) / half_w)
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

def gable_roof(name, half_w, half_d, rise, z, curve=0.85, seg=10, thick=0.20,
               mat="tile_old", off_x=0.0, off_y=0.0, col="OldHouse"):
    """Full GABLE roof (ridge runs the full length along X, two slopes).
    Slight upswept corners for Vietnamese character."""
    bm = bmesh.new()
    nx = ny = seg + 1
    verts = []
    for iy in range(ny):
        row = []
        for ix in range(nx):
            x = (-half_w + 2 * half_w * ix / seg)
            y = (-half_d + 2 * half_d * iy / seg)
            h = rise * (1 - abs(y) / half_d)
            corner = (abs(x) / half_w) * (abs(y) / half_w)
            h += curve * rise * 0.45 * corner ** 4
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

def house_gable(name, sx, half_w, half_d, rise, z, col="OldHouse", off_y=0.0):
    """White lime gable-end wall whose curved top edge EXACTLY tracks the gable
    roof underside (same slope math, sampled pointwise) so no open slot or
    poking corner appears at the gable ends (the dark-triangle bug)."""
    bm = bmesh.new()
    # roof underside height at |y|: rise*(1-|y|/half_d) minus the roof plate z-gap
    under = [rise * (1 - abs(yy) / half_d) - 0.06 for yy in
             (-half_d + 0.06, -half_d * 0.70, -half_d * 0.40,
              0.0, half_d * 0.40, half_d * 0.70, half_d - 0.06)]
    prof = [(-half_d + 0.06, under[0]), (half_d - 0.06, under[0])]
    # inward points rise along the roof slope toward the ridge
    for yy, uh in ((half_d * 0.70, under[1]), (half_d * 0.40, under[2]),
                   (0.0, under[3] + 0.02)):
        prof.append((yy, uh))
    for yy, uh in ((-half_d * 0.40, under[2]), (-half_d * 0.70, under[1])):
        prof.append((yy, uh))
    vs = [bm.verts.new((0.0, yy, zz)) for (yy, zz) in prof]
    f = bm.faces.new(vs)
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    mv = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=V((0.16, 0, 0)), verts=mv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = build_mesh(name, bm, (sx * (half_w - 0.52), off_y, z))
    obj.data.materials.append(MAT["lime"])
    place(obj, col)
    shade_smooth(obj)
    return obj

def dao_tips(roof_name, half_w, half_d, rise, z, curve=0.8, off_x=0.0, off_y=0.0,
             col="Hall", mat="tile", ridge_frac=1.0):
    """Corner tips seated on the v2 saddle-hip surface — EXACT same height
    formula as hip_roof (incl. hip term and ridge_frac) so nothing floats."""
    ridge_half = half_w * ridge_frac
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (half_w - 0.02), sy * (half_d - 0.02)
            h = rise * (1 - abs(y) / half_d)
            if abs(x) > ridge_half:
                hip = rise * max(0.0, (half_w - abs(x)) / (half_w - ridge_half))
                h = min(h, hip)
            corner = (abs(x) / half_w) * (abs(y) / half_w)
            h += curve * rise * 0.55 * corner ** 4
            tip = cylinder(f"{roof_name}_Dao_{sx}_{sy}", 0.038, 0.34,
                           (off_x + x, off_y + y, z + h + 0.13), verts=7,
                           rot=(radians(38) * sy, radians(-38) * sx, 0))
            tip.data.materials.append(MAT[mat])
            place(tip, col)

def arch_wall(name, width, depth, height, openings, slices=24, pier_mat=None):
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

def _obj_uv(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs["Object"]

def _weathering(nt, strength=0.4, lo=0.70, hi=1.15, streak=False):
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.4 if streak else 0.55
    noise.inputs["Detail"].default_value = 6.0
    if streak:
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

def masonry(name, c1, c2, mortar, rough=0.86, bw=0.5, rh=0.25, weather=0.45, bump=0.08,
            lo=0.70, hi=1.15, streak=False):
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

def build_materials():
    global MAT
    MAT = {}
    MAT["tile"]   = masonry("LQD_Tile_Terracotta", (0.540, 0.128, 0.038), (0.420, 0.096, 0.030),
                            (0.28, 0.19, 0.135), bw=0.36, rh=0.115, weather=0.4,
                            lo=0.72, hi=1.18, bump=0.12)
    MAT["tile_old"] = masonry("LQD_Tile_Aged", (0.290, 0.105, 0.044), (0.215, 0.078, 0.034),
                              (0.22, 0.15, 0.105), bw=0.36, rh=0.115, weather=0.5,
                              lo=0.66, hi=1.2, bump=0.12)
    MAT["stone"]  = masonry("LQD_Stone_Grey", (0.400, 0.395, 0.382), (0.320, 0.315, 0.305),
                            (0.28, 0.275, 0.268), bw=0.62, rh=0.30, weather=0.42, bump=0.1)
    MAT["lime"]   = masonry("LQD_Lime_White", (0.690, 0.675, 0.645), (0.605, 0.590, 0.565),
                            (0.56, 0.55, 0.53), bw=0.5, rh=0.25, weather=0.45,
                            lo=0.68, hi=1.15, streak=True)
    MAT["wood"]   = pbr("LQD_Wood_Dark", (0.062, 0.042, 0.026), rough=0.8)
    MAT["wood_old"] = pbr("LQD_Wood_Weathered", (0.088, 0.062, 0.040), rough=0.85)
    MAT["door_red"] = pbr("LQD_Door_Red", (0.320, 0.045, 0.028), rough=0.7)
    MAT["gold"]   = pbr("LQD_Gold", (0.72, 0.55, 0.20), rough=0.4, metal=0.85)
    MAT["banner"] = pbr("LQD_Banner_Red", (0.52, 0.045, 0.030), rough=0.72)
    MAT["banner_y"] = pbr("LQD_Banner_Yellow", (0.78, 0.58, 0.10), rough=0.72)
    MAT["lantern"] = pbr("LQD_Lantern_Red", (0.45, 0.035, 0.024), rough=0.55)
    MAT["leaf"]   = pbr("LQD_Foliage", (0.068, 0.132, 0.045), rough=0.85)
    MAT["leaf2"]  = pbr("LQD_Foliage_Light", (0.108, 0.178, 0.052), rough=0.85)
    MAT["leaf3"]  = pbr("LQD_Foliage_Olive", (0.125, 0.152, 0.048), rough=0.85)
    MAT["trunk"]  = pbr("LQD_Trunk", (0.15, 0.115, 0.082), rough=0.9)
    MAT["bench"]  = pbr("LQD_Bench_Green", (0.045, 0.115, 0.055), rough=0.7)
    MAT["paving"] = masonry("LQD_Brick_Paving", (0.545, 0.148, 0.058), (0.435, 0.115, 0.045),
                            (0.33, 0.22, 0.15), bw=0.30, rh=0.15, weather=0.42,
                            lo=0.7, hi=1.18, bump=0.08)
    MAT["ground"] = pbr("LQD_Ground_Earth", (0.235, 0.185, 0.122), rough=0.95)
    MAT["hedge"]  = pbr("LQD_Hedge", (0.058, 0.108, 0.038), rough=0.9)

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
build_materials()

COL = {}
for cname in ["Hall", "OldHouse", "Grounds", "Plaza", "Trees", "Flags",
              "Lighting", "Cameras", "Environment"]:
    COL[cname] = bpy.data.collections.new(cname)
    scene.collection.children.link(COL[cname])

def place(obj, cname):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    COL[cname].objects.link(obj)
    return obj

# ---------------------------------------------------------------- dimensions
HALL_W, HALL_D, HALL_H = 22.0, 9.0, 3.6
HALL_Z0 = 1.35                     # terrace height
HALL_Y = 12.0
TERR_W, TERR_D = 30.0, 16.0

HOUSE_W, HOUSE_D, HOUSE_H = 13.0, 8.0, 3.0
HOUSE_Z0 = 0.45
HOUSE_Y = -6.0

GATE_CX = 15.5
GATE_Y = -3.0
PLAZA_R = 34.0

flag_objs = []

# ================================================================ 1. GROUND + PLAZA
gnd = box("Ground_Earth", (220, 220, 0.1), (0, 0, -0.06))
place(gnd, "Environment")
gnd.data.materials.append(MAT["ground"])

# big red-brick plaza (slightly irregular read via weathering)
plaza = box("Plaza_Paving", (66, 62, 0.08), (0, 2, -0.02))
plaza.data.materials.append(MAT["paving"])
place(plaza, "Plaza")
# darker worn path patches
for i, (px, py, pw, pd) in enumerate([(0, -14, 22, 16), (-18, 8, 14, 12), (17, 6, 15, 14)]):
    pat = box(f"Plaza_Wear_{i}", (pw, pd, 0.02), (px, py, 0.02))
    pat.data.materials.append(MAT["ground"])
    place(pat, "Plaza")

# ================================================================ 2. MEMORIAL HALL
# terrace + 3 stair flights (centre wide, two sides)
terr = box("Hall_Terrace", (TERR_W, TERR_D, HALL_Z0), (0, HALL_Y, HALL_Z0 / 2))
terr.data.materials.append(MAT["stone"])
place(terr, "Hall")

def stair_flight(tag, cx, width, steps=6):
    for k in range(steps):
        st = box(f"{tag}_Step_{k}", (width, 0.42, HALL_Z0 * (k + 1) / steps),
                 (cx, HALL_Y - TERR_D / 2 - 0.35 - (steps - 1 - k) * 0.42,
                  HALL_Z0 * (k + 1) / steps / 2))
        st.data.materials.append(MAT["stone"])
        place(st, "Hall")

stair_flight("Stair_C", 0.0, 9.0)
stair_flight("Stair_L", -10.5, 4.0)
stair_flight("Stair_R", 10.5, 4.0)
# cheek walls beside the centre flight
for sgn in (-1, 1):
    ch = box(f"Stair_Cheek_{sgn}", (0.5, 5.4, 0.75), (sgn * 4.9, HALL_Y - TERR_D / 2 - 1.6, 0.37))
    ch.data.materials.append(MAT["stone"])
    place(ch, "Hall")

# hall body: dark wood + grey stone colonnade
body = box("Hall_Body", (HALL_W, HALL_D, HALL_H), (0, HALL_Y, HALL_Z0 + HALL_H / 2))
body.data.materials.append(MAT["wood"])
place(body, "Hall")
front_y = HALL_Y - HALL_D / 2
for k in range(9):
    x = -HALL_W / 2 + 0.9 + k * ((HALL_W - 1.8) / 8)
    c = cylinder(f"Hall_Col_{k}", 0.16, HALL_H, (x, front_y + 0.5, HALL_Z0 + HALL_H / 2), verts=10)
    c.data.materials.append(MAT["stone"])
    place(c, "Hall")
    cb = box(f"Hall_ColBase_{k}", (0.42, 0.42, 0.22), (x, front_y + 0.5, HALL_Z0 + 0.11))
    cb.data.materials.append(MAT["stone"])
    place(cb, "Hall")
# door band (dark red) behind the colonnade
for k in range(5):
    dx = -6.4 + k * 3.2
    d = box(f"Hall_Door_{k}", (2.2, 0.10, 2.5), (dx, front_y + 0.75, HALL_Z0 + 1.3))
    d.data.materials.append(MAT["door_red"])
    place(d, "Hall")
# red banner between two centre columns
ban = box("Hall_Banner", (3.4, 0.06, 1.7), (0, front_y + 0.45, HALL_Z0 + 1.85))
ban.data.materials.append(MAT["banner"])
place(ban, "Hall")
ban_t = box("Hall_Banner_Text", (2.9, 0.03, 0.8), (0, front_y + 0.41, HALL_Z0 + 1.95))
ban_t.data.materials.append(MAT["banner_y"])
place(ban_t, "Hall")

# roof: big aged-terracotta saddle-hip with a REAL ridge line + dragon crest
R_HALL = 2.6
r_hall = hip_roof("Hall_Roof", HALL_W / 2 + 1.5, HALL_D / 2 + 1.3, R_HALL,
                  HALL_Z0 + HALL_H - 0.06, curve=0.9, seg=10, thick=0.30, mat="tile",
                  off_y=HALL_Y, ridge_frac=0.62)
dao_tips("Hall_Roof", HALL_W / 2 + 1.5, HALL_D / 2 + 1.3, R_HALL, HALL_Z0 + HALL_H - 0.06,
         curve=0.9, off_y=HALL_Y, ridge_frac=0.62)
# dragon crest sits ON the ridge line (z + rise); bar length CLAMPED to the
# ridge segment (ridge_frac * span) so its ends can't poke out of the hips
Z_RIDGE = HALL_Z0 + HALL_H - 0.06 + R_HALL
RIDGE_SEG = 2 * 0.62 * (HALL_W / 2 + 1.5)          # true ridge length = 15.5
ridge = box("Hall_Ridge_Bar", (RIDGE_SEG - 0.5, 0.34, 0.30), (0, HALL_Y, Z_RIDGE + 0.10))
ridge.data.materials.append(MAT["lime"])
place(ridge, "Hall")
flame = sphere("Hall_Ridge_Flame", 0.20, (0, HALL_Y, Z_RIDGE + 0.42), segs=10, rings=7)
flame.data.materials.append(MAT["lime"])
place(flame, "Hall")
flame_g = sphere("Hall_Ridge_FlameGold", 0.11, (0, HALL_Y, Z_RIDGE + 0.60), segs=8, rings=6)
flame_g.data.materials.append(MAT["gold"])
place(flame_g, "Hall")
for sx in (-1, 1):
    for k in range(3):
        hx = sx * (1.4 + k * 1.9)
        horn = cylinder(f"Hall_Ridge_Horn_{sx}_{k}", 0.055, 0.55,
                        (hx, HALL_Y, Z_RIDGE + 0.36), verts=7,
                        rot=(0, radians(-46) * sx, 0))
        horn.data.materials.append(MAT["lime"])
        place(horn, "Hall")
    head = sphere(f"Hall_Ridge_Head_{sx}", 0.19, (sx * (RIDGE_SEG / 2 - 0.3), HALL_Y, Z_RIDGE + 0.22),
                  segs=10, rings=7)
    head.scale = (1.25, 0.9, 0.9)
    head.data.materials.append(MAT["lime"])
    place(head, "Hall")
    horn0 = cylinder(f"Hall_Ridge_HeadHorn_{sx}", 0.045, 0.5,
                     (sx * (RIDGE_SEG / 2 - 0.15), HALL_Y, Z_RIDGE + 0.50), verts=7,
                     rot=(radians(-30), radians(-50) * sx, 0))
    horn0.data.materials.append(MAT["lime"])
    place(horn0, "Hall")
# (gable finials removed — the dragon crest carries the reference look)

# hanging lanterns along the colonnade
for k in (-3, -1, 1, 3):
    flag_objs.append(hanging_lantern(f"Lantern_Hall_{k}", k * 1.55, front_y + 0.30,
                                     HALL_Z0 + HALL_H - 0.10, 1.0))

# ================================================================ 3. OLD HOUSE
hz = HOUSE_Z0
pl2 = box("House_Plinth", (HOUSE_W + 1.6, HOUSE_D + 1.6, HOUSE_Z0), (0, HOUSE_Y, HOUSE_Z0 / 2))
pl2.data.materials.append(MAT["stone"])
place(pl2, "OldHouse")
for k in range(3):
    st = box(f"House_Step_{k}", (4.2 - k * 0.5, 0.5, HOUSE_Z0 * (k + 1) / 3),
             (0, HOUSE_Y - HOUSE_D / 2 - 0.4 - (2 - k) * 0.5, HOUSE_Z0 * (k + 1) / 3 / 2))
    st.data.materials.append(MAT["stone"])
    place(st, "OldHouse")

# timber body — front wall RECESSED 1.7 m so the roof overhang forms a real
# open loggia (the deep shadowed porch in the reference)
RECESS = 1.7
body_d = HOUSE_D - RECESS
hb = box("House_Body", (HOUSE_W, body_d, HOUSE_H), (0, HOUSE_Y + RECESS / 2, hz + HOUSE_H / 2))
hb.data.materials.append(MAT["wood_old"])
place(hb, "OldHouse")
# dark open doorway centre + red door band beside it (on the recessed wall)
dd = box("House_Door", (2.4, 0.15, 2.2), (0, HOUSE_Y - body_d / 2 - 0.02, hz + 1.1))
dd.data.materials.append(MAT["wood"])
place(dd, "OldHouse")
df = box("House_DoorFrame", (2.7, 0.10, 2.4), (0, HOUSE_Y - body_d / 2 + 0.02, hz + 1.2))
df.data.materials.append(MAT["wood_old"])
place(df, "OldHouse")
rd = box("House_RedBand", (1.5, 0.10, 2.0), (2.6, HOUSE_Y - body_d / 2 - 0.04, hz + 1.0))
rd.data.materials.append(MAT["door_red"])
place(rd, "OldHouse")
ld = box("House_LatticeDoor", (1.4, 0.10, 2.0), (-2.6, HOUSE_Y - body_d / 2 - 0.04, hz + 1.0))
ld.data.materials.append(MAT["wood"])
place(ld, "OldHouse")
# front loggia posts (stand at the ORIGINAL front line, under the roof overhang)
for k in (-1, 0, 1):
    p = cylinder(f"House_Post_{k}", 0.15, HOUSE_H, (k * 4.4, HOUSE_Y - HOUSE_D / 2 + 0.35,
                 hz + HOUSE_H / 2), verts=9)
    p.data.materials.append(MAT["wood_old"])
    place(p, "OldHouse")
    pb = box(f"House_PostBase_{k}", (0.4, 0.4, 0.2), (k * 4.4, HOUSE_Y - HOUSE_D / 2 + 0.35, hz + 0.1))
    pb.data.materials.append(MAT["stone"])
    place(pb, "OldHouse")
# loggia beam along the front
beam_h = box("House_PorchBeam", (HOUSE_W - 0.3, 0.22, 0.24),
             (0, HOUSE_Y - HOUSE_D / 2 + 0.35, hz + HOUSE_H - 0.20))
beam_h.data.materials.append(MAT["wood_old"])
place(beam_h, "OldHouse")
# porch floor slab (stone) in front of the recessed wall
pf = box("House_PorchFloor", (HOUSE_W - 0.4, RECESS + 0.4, 0.10),
         (0, HOUSE_Y - (body_d / 2 - RECESS / 2) + 0.3, hz + 0.05))
pf.data.materials.append(MAT["stone"])
place(pf, "OldHouse")

# WHITE LIME GABLE-END walls tucked under a full GABLE roof (bug fixed:
# the old version had gable wedges poking through a hip roof)
house_gable("House_Gable_E", 1, HOUSE_W / 2 + 0.30, HOUSE_D / 2, 0.98,
            hz + HOUSE_H - 0.10, off_y=HOUSE_Y)
house_gable("House_Gable_W", -1, HOUSE_W / 2 + 0.30, HOUSE_D / 2, 0.98,
            hz + HOUSE_H - 0.10, off_y=HOUSE_Y)
# full gable roof (aged terracotta) — ridge E-W like the reference
r_h = gable_roof("House_Roof", HOUSE_W / 2 + 0.45, HOUSE_D / 2 + 0.75, 1.55,
                 hz + HOUSE_H - 0.06, curve=0.85, seg=10, thick=0.22, mat="tile_old",
                 off_y=HOUSE_Y)
# white ridge bar along the house roof + horns (visible in the old photo)
hrb = box("House_Ridge_Bar", (HOUSE_W - 0.4, 0.22, 0.16), (0, HOUSE_Y, hz + HOUSE_H + 1.55))
hrb.data.materials.append(MAT["lime"])
place(hrb, "OldHouse")
for sx in (-1, 1):
    horn = cylinder(f"House_GableHorn_{sx}", 0.04, 0.5,
                    (sx * (HOUSE_W / 2 + 0.1), HOUSE_Y, hz + HOUSE_H + 1.80), verts=7,
                    rot=(0, radians(-50) * sx, 0))
    horn.data.materials.append(MAT["lime"])
    place(horn, "OldHouse")

# ================================================================ 4. GATE PAVILIONS
def gate_pavilion(name, x, y):
    # grey plaster block with arched opening
    gw, gd, gh = 2.6, 2.2, 2.7
    blk = arch_wall(f"{name}_Body", gw, gd, gh,
                    openings=[(0.0, 0.62, 'arc', gh - 1.1, 0.62)], slices=10,
                    pier_mat=MAT["lime"])
    blk.location = (x, y, 0.25)
    place(blk, "OldHouse")
    base = box(f"{name}_Base", (gw + 0.5, gd + 0.5, 0.25), (x, y, 0.125))
    base.data.materials.append(MAT["stone"])
    place(base, "OldHouse")
    # saddled red-tile roof (ridge_frac=0.5 so the crest bar fits the ridge)
    gr = hip_roof(f"{name}_Roof", gw / 2 + 0.42, gd / 2 + 0.42, 0.62, 0.25 + gh - 0.04,
                  curve=0.9, seg=6, thick=0.14, mat="tile", off_x=x, off_y=y, col="OldHouse",
                  ridge_frac=0.5)
    dao_tips(f"{name}_Roof", gw / 2 + 0.42, gd / 2 + 0.42, 0.62, 0.25 + gh - 0.04,
             curve=0.9, off_x=x, off_y=y, col="OldHouse", ridge_frac=0.5)
    # white ridge crest mini — bar clamped to the ridge segment (0.5 * 1.72)
    rb = box(f"{name}_Ridge", (1.5, 0.16, 0.14), (x, y, 0.25 + gh + 0.56))
    rb.data.materials.append(MAT["lime"])
    place(rb, "OldHouse")
    for sx in (-1, 1):
        horn = cylinder(f"{name}_Horn_{sx}", 0.035, 0.4,
                        (x + sx * 0.72, y, 0.25 + gh + 0.72), verts=6,
                        rot=(0, radians(-48) * sx, 0))
        horn.data.materials.append(MAT["lime"])
        place(horn, "OldHouse")

gate_pavilion("Gate_W", -GATE_CX, GATE_Y)
gate_pavilion("Gate_E", GATE_CX, GATE_Y)

# ================================================================ 5. FORECOURT ELEMENTS
# stone lantern pedestals (bàn đá) + carved altar (hương án) in front of the house
def stone_pedestal(name, x, y):
    b1 = cylinder(f"{name}_Base", 0.42, 0.22, (x, y, 0.11), verts=10)
    b1.data.materials.append(MAT["stone"])
    place(b1, "Grounds")
    b2 = cylinder(f"{name}_Shaft", 0.16, 1.0, (x, y, 0.72), verts=9)
    b2.data.materials.append(MAT["stone"])
    place(b2, "Grounds")
    bowl = cylinder(f"{name}_Bowl", 0.30, 0.22, (x, y, 1.33), verts=10)
    bowl.data.materials.append(MAT["stone"])
    place(bowl, "Grounds")
    cap = cylinder(f"{name}_Cap", 0.20, 0.10, (x, y, 1.50), verts=9)
    cap.data.materials.append(MAT["stone"])
    place(cap, "Grounds")
    tip = sphere(f"{name}_Tip", 0.07, (x, y, 1.62), segs=8, rings=5)
    tip.data.materials.append(MAT["stone"])
    place(tip, "Grounds")

def stone_altar(name, x, y):
    legs = box(f"{name}_Legs", (2.0, 0.9, 0.55), (x, y, 0.275))
    legs.data.materials.append(MAT["stone"])
    place(legs, "Grounds")
    body2 = box(f"{name}_Body", (2.2, 1.1, 0.55), (x, y, 0.83))
    body2.data.materials.append(MAT["stone"])
    place(body2, "Grounds")
    lip = box(f"{name}_Lip", (2.35, 1.2, 0.12), (x, y, 1.16))
    lip.data.materials.append(MAT["stone"])
    place(lip, "Grounds")
    for sx in (-1, 1):
        horn = cylinder(f"{name}_Horn_{sx}", 0.05, 0.35, (x + sx * 0.8, y, 1.42), verts=7)
        horn.data.materials.append(MAT["stone"])
        place(horn, "Grounds")

stone_altar("Altar_C", 0.0, HOUSE_Y - HOUSE_D / 2 - 2.2)
stone_pedestal("Ped_L", -2.1, HOUSE_Y - HOUSE_D / 2 - 2.2)
stone_pedestal("Ped_R", 2.1, HOUSE_Y - HOUSE_D / 2 - 2.2)
stone_pedestal("Ped_FarL", -4.6, HOUSE_Y - HOUSE_D / 2 - 1.2)
stone_pedestal("Ped_FarR", 4.6, HOUSE_Y - HOUSE_D / 2 - 1.2)

# ================================================================ 6. PLAZA FURNITURE
def bench(name, x, y, rot=0.0):
    b = box(f"{name}_Seat", (1.8, 0.45, 0.08), (x, y, 0.42))
    b.data.materials.append(MAT["bench"])
    place(b, "Plaza")
    for sx in (-1, 1):
        leg = box(f"{name}_Leg_{sx}", (0.08, 0.4, 0.4), (x + sx * 0.75, y, 0.2))
        leg.data.materials.append(MAT["stone"])
        place(leg, "Plaza")
    bk = box(f"{name}_Back", (1.8, 0.07, 0.35), (x, y - 0.19, 0.62))
    bk.data.materials.append(MAT["bench"])
    place(bk, "Plaza")
    for o in (b, bk):
        o.rotation_euler = (0, 0, rot)

def garden_lamp(name, x, y):
    p = cylinder(f"{name}_Post", 0.06, 2.1, (x, y, 1.05), verts=8)
    p.data.materials.append(MAT["stone"])
    place(p, "Plaza")
    h = box(f"{name}_Head", (0.26, 0.26, 0.34), (x, y, 2.25))
    h.data.materials.append(MAT["gold"])
    place(h, "Plaza")
    c = cylinder(f"{name}_Cap", 0.19, 0.08, (x, y, 2.46), verts=8)
    c.data.materials.append(MAT["stone"])
    place(c, "Plaza")

def bush(name, x, y, s=1.0):
    for k, (dx, dy, sr) in enumerate(((0, 0, 0.55 * s), (0.4 * s, 0.1, 0.4 * s), (-0.4 * s, -0.05, 0.42 * s))):
        bl = sphere(f"{name}_{k}", sr, (x + dx, y + dy, 0.30 * s + k * 0.08), segs=8, rings=5)
        bl.scale = (1.0, 1.0, 0.8)
        bl.data.materials.append(MAT["hedge"])
        place(bl, "Plaza")

for i, (bx_, by_) in enumerate([(-9.0, -18.0), (9.0, -18.0), (-13.0, -12.0), (13.0, -12.0),
                                (-19.0, 2.0), (19.0, 2.0), (-7.0, 24.0), (7.0, 24.0),
                                (-16.0, 20.0), (16.0, 20.0)]):
    bush(f"Bush_{i}", bx_, by_, 1.0 + (i % 3) * 0.25)
bench("Bench_1", -11.0, -9.0, radians(12))
bench("Bench_2", 11.0, -9.0, radians(-8))
bench("Bench_3", 14.5, -16.5, radians(-30))
garden_lamp("Lamp_1", -6.5, -16.0)
garden_lamp("Lamp_2", 6.5, -16.0)
garden_lamp("Lamp_3", -20.0, -4.0)
garden_lamp("Lamp_4", 20.0, -4.0)
garden_lamp("Lamp_5", -24.0, 14.0)
garden_lamp("Lamp_6", 24.0, 14.0)

# low hedge along plaza north edge behind the hall
for k in range(15):
    hx = -21.0 + k * 3.0
    hedge = box(f"Hedge_{k}", (2.6, 1.0, 1.0), (hx, 27.0, 0.5))
    hedge.data.materials.append(MAT["hedge"])
    place(hedge, "Trees")

# ================================================================ 7. TREES
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

tree("Tree_PalmL", -8.0, 25.0, h=7.0, r=1.6, seed=41, lmat="leaf2")
tree("Tree_PalmR", 8.0, 26.0, h=6.5, r=1.5, seed=42, lmat="leaf2")
tree("Tree_BigL", -22.0, 12.0, h=6.0, r=2.8, seed=43)
tree("Tree_BigR", 22.0, 12.0, h=6.2, r=2.9, seed=44, lmat="leaf3")
tree("Tree_BL", -24.0, -20.0, h=5.5, r=2.6, seed=45, lmat="leaf3")
tree("Tree_BR", 24.0, -20.0, h=5.8, r=2.7, seed=46)
tree("Tree_FL", -28.0, 4.0, h=5.0, r=2.4, seed=47, lmat="leaf2")
tree("Tree_FR", 28.0, 4.0, h=5.2, r=2.5, seed=48)

# ================================================================ 8. LIGHTING
world = bpy.data.worlds.new("Sky_World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.70, 0.77, 0.86, 1.0)
bg.inputs[1].default_value = 0.62

sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 5.2
sun.data.angle = radians(3.0)
sun.data.color = (1.0, 0.97, 0.90)
d = V((-0.35, 0.55, -0.68)).normalized()
sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
place(sun, "Lighting")

fill = bpy.data.objects.new("Fill_Sky", bpy.data.lights.new("Fill_Sky", 'AREA'))
fill.data.energy = 420
fill.data.size = 24
fill.data.color = (0.93, 0.95, 1.0)
fill.location = (-12, -14, 10)
fill.rotation_euler = Euler((radians(50), 0, radians(-25)))
place(fill, "Lighting")

# ================================================================ 9. CAMERAS
def camera(name, loc, look_at, lens=36):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.location = loc
    direction = V(look_at) - V(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 500
    place(cam, "Cameras")
    return cam

cam_a = camera("Camera_Hero", (-20.0, -22.0, 5.5), (0, 6.0, 4.5), 32)      # reference angle
cam_b = camera("Camera_House", (-13.0, -24.0, 3.4), (2.0, HOUSE_Y + 1.0, 2.6), 34)  # old house + gates
cam_c = camera("Camera_Hall", (14.0, -14.0, 6.0), (0, HALL_Y, 5.0), 36)    # hall 3/4
cam_d = camera("Camera_Plaza", (0.0, -30.0, 7.5), (0, 6.0, 3.0), 38)       # plaza overview

# ================================================================ 9b. VISITORS
if "Visitors" not in COL:
    COL["Visitors"] = bpy.data.collections.new("Visitors")
    scene.collection.children.link(COL["Visitors"])

visitor_specs = [
    # plaza centre: families + couples strolling
    (-3.0, -17.0, 20, 'family'), (3.5, -19.0, 160, 'couple'),
    (0.5, -13.5, 180, 'photographer'), (-6.0, -11.0, 40, 'adult'),
    (6.5, -12.0, 210, 'adult'), (-1.5, -9.0, 165, 'couple'),
    # kids playing near the benches (balloons!)
    (10.8, -10.5, -30, 'kid'), (12.4, -9.0, 120, 'kid'), (-11.5, -10.5, 20, 'kid'),
    # visitors at the old house porch (observing the altar)
    (-2.2, -11.5, 5, 'adult'), (2.4, -11.8, -5, 'photographer'),
    (-3.6, -10.2, 15, 'kid'),
    # hall stairs: school group + guide
    (-4.8, -2.5, 10, 'adult'), (-5.8, -0.5, 0, 'kid'), (-4.2, 0.6, -15, 'kid'),
    (4.8, -2.8, -10, 'adult'), (5.8, -0.8, 5, 'kid'),
    # monk + worshipper at the stone altar
    (-1.2, -9.4, 175, 'monk'), (1.4, -9.8, 185, 'adult'),
    # strollers on the far plaza edge
    (-15.0, -14.0, 70, 'couple'), (16.0, -15.0, -70, 'photographer'),
]
add_visitors(bpy, V, box, cylinder, sphere, place, pbr, MAT, visitor_specs,
             col="Visitors", seed=777)

# ================================================================ 10. ANIMATION
scene.frame_start = 1
scene.frame_end = 96
for i, cloth in enumerate(flag_objs):
    ph = i * 1.15
    amp = 0.10
    for f, a in ((1, 0.0), (24, amp), (48, 0.0), (72, -amp), (96, 0.0)):
        cloth.rotation_euler.y = amp * 0.45 * sin(ph + f / 96 * 2 * pi)
        cloth.rotation_euler.z = a
        cloth.keyframe_insert("rotation_euler", frame=f)
    for fc in cloth.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'SINE'

# ================================================================ 11. VIEWPORT DISPLAY
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

# ================================================================ 12. SAVE + RENDER
os.makedirs(RENDER_DIR, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("SAVED_BLEND:", BLEND_PATH)

for cam, tag in ((cam_a, "hero"), (cam_b, "house"), (cam_c, "hall"), (cam_d, "plaza")):
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
