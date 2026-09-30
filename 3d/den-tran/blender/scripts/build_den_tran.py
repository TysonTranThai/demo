# -*- coding: utf-8 -*-
"""
SMART ART HERITAGE — Đền Trần (Thiên Trường), Hưng Hà, Thái Bình.
Procedural Blender 4.5 build.

Reference-observed facts encoded:
- Red-brick enclosure wall with FIVE arched openings (3 large centre + 2 small
  side arches), brick cornice + red tile coping.
- Two-tier gate pavilion over the wall: long hall + centre pavilion, red-tile
  hip roofs with upswept corners, white balustrade along the wall-top terrace,
  orange banner on the wall face.
- Ornate white corner pillars (cột) with stacked capitals, two pairs.
- Small red-tile gate pavilions in the wall left/right of the main gate.
- Ancient 4-column nghi môn (weathered stone, tile caps) in the first courtyard.
- Đại điện main hall: timber, two-tier sweeping brown-tile roofs, on a stone
  platform; red doors; flanked by two side halls (tả vu / hữu vu).
- Gravel forecourt with a GIANT flagpole and waving red flag.
- Axial avenue lined with two rows of stone columns running through rice
  fields, flanked by two grass mounds (the historic earthworks).
- Bright blue sky, strong sun (drone-photo look).

Ambiguities resolved: interiors dark; brick relief patterns suggested by
material; column statues simplified to stacked discs + finials.
"""

import bpy, bmesh, os, math, sys, random
from math import radians, sin, cos, pi, sqrt, atan2
from mathutils import Vector, Euler, Matrix

V = Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(SCRIPT_DIR, "..", "den-tran-model.blend")
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
    """Masonry wall block with real through-openings.
    openings: list of (cx, half_w, kind, spring_z, rise). kind 'arc' or 'rect'."""
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

def hip_roof(name, half_w, half_d, rise, z, curve=0.8, seg=8, thick=0.16, mat="tile"):
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
    obj.data.materials.append(MAT[mat])
    obj.data.materials.append(MAT["wood"])
    shade_smooth(obj)
    return obj

def arch_trim(name, cx, hw, sz, y_face, band=0.28, depth=0.14, segs=12, col="Wall_Gate"):
    """Proud white-lime band outlining a vault opening."""
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
    obj.data.materials.append(MAT["lime"])
    place(obj, col)
    for sgn in (-1, 1):
        jb = box(f"{name}_Jamb_{sgn}", (band * 1.55, depth, sz + 0.35),
                 (cx + sgn * (hw + band * 0.5), y_face + depth / 2, (sz + 0.35) / 2))
        jb.data.materials.append(MAT["lime"])
        place(jb, col)
    return obj

def balustrade_x(tag, x0, x1, y, z, col, n_scale=0.34):
    ln = x1 - x0
    t = box(f"{tag}_Top", (ln, 0.14, 0.09), ((x0 + x1) / 2, y, z + 0.50))
    b = box(f"{tag}_Bot", (ln, 0.12, 0.08), ((x0 + x1) / 2, y, z + 0.07))
    n = max(2, int(ln / n_scale))
    for i in range(n + 1):
        p = cylinder(f"{tag}_Post_{i}", 0.042, 0.48, (x0 + i * ln / n, y, z + 0.24), verts=6)
        p.data.materials.append(MAT["lime"])
        place(p, col)
    for o in (t, b):
        o.data.materials.append(MAT["lime"])
        place(o, col)

def balustrade_y(tag, y0, y1, x, z, col, n_scale=0.34):
    ln = y1 - y0
    t = box(f"{tag}_Top", (0.14, ln, 0.09), (x, (y0 + y1) / 2, z + 0.50))
    b = box(f"{tag}_Bot", (0.12, ln, 0.08), (x, (y0 + y1) / 2, z + 0.07))
    n = max(2, int(ln / n_scale))
    for i in range(n + 1):
        p = cylinder(f"{tag}_Post_{i}", 0.042, 0.48, (x, y0 + i * ln / n, z + 0.24), verts=6)
        p.data.materials.append(MAT["lime"])
        place(p, col)
    for o in (t, b):
        o.data.materials.append(MAT["lime"])
        place(o, col)

def dao_tips(roof_name, half_w, half_d, rise, z, curve=0.8, off_x=0.0, off_y=0.0, col="Wall_Gate"):
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (half_w - 0.02), sy * (half_d - 0.02)
            u = max(abs(x) / half_w, abs(y) / half_d)
            h = rise * (1 - u) + curve * rise * 0.9 * ((abs(x) / half_w) * (abs(y) / half_w)) ** 4
            tip = cylinder(f"{roof_name}_Dao_{sx}_{sy}", 0.04, 0.38,
                           (off_x + x, off_y + y, z + h + 0.15), verts=7,
                           rot=(radians(38) * sy, radians(-38) * sx, 0))
            tip.data.materials.append(MAT["tile"])
            place(tip, col)

def flag_cloth(name, x, y, z_top, w=1.5, h=0.95, mat="flag_r"):
    bm = bmesh.new()
    nx, ny = 10, 6
    verts = []
    for iy in range(ny + 1):
        row = []
        for ix in range(nx + 1):
            row.append(bm.verts.new((ix / nx * w - 0.05, 0, h - iy / ny * h)))
        verts.append(row)
    for iy in range(ny):
        for ix in range(nx):
            bm.faces.new((verts[iy][ix], verts[iy][ix + 1],
                          verts[iy + 1][ix + 1], verts[iy + 1][ix]))
    cloth = build_mesh(name, bm, (x, y, z_top))
    cloth.data.materials.append(MAT[mat])
    cloth.rotation_mode = 'XYZ'
    place(cloth, "Flags")
    return cloth

def lattice_panel(name, cx, cy, w, h, z0, axis='x', col="Temple", mull=5, mat=None):
    """Wooden lattice screen: frame + vertical mullions + two rails."""
    mmat = mat or MAT["lattice"]
    if axis == 'x':
        fr = box(f"{name}_Frame", (w, 0.06, h), (cx, cy, z0 + h / 2))
    else:
        fr = box(f"{name}_Frame", (0.06, w, h), (cx, cy, z0 + h / 2))
    fr.data.materials.append(mmat)
    place(fr, col)
    for i in range(mull):
        off = -w / 2 + (i + 1) * w / (mull + 1)
        if axis == 'x':
            m = box(f"{name}_Mull_{i}", (0.05, 0.045, h - 0.10), (cx + off, cy, z0 + h / 2))
        else:
            m = box(f"{name}_Mull_{i}", (0.045, 0.05, h - 0.10), (cx, cy + off, z0 + h / 2))
        m.data.materials.append(mmat)
        place(m, col)
    for zz in (z0 + h * 0.28, z0 + h * 0.72):
        if axis == 'x':
            r = box(f"{name}_Rail_{zz:.2f}", (w - 0.05, 0.045, 0.05), (cx, cy, zz))
        else:
            r = box(f"{name}_Rail_{zz:.2f}", (0.045, w - 0.05, 0.05), (cx, cy, zz))
        r.data.materials.append(mmat)
        place(r, col)

def hanging_lantern(name, x, y, z_top, scale=1.0, col="Wall_Gate"):
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
    obj.data.materials.append(MAT["fascia"])
    obj.data.materials.append(MAT["gold"])
    for f in obj.data.polygons:
        cz = f.center.z
        f.material_index = 0 if (-0.56 * s < cz < -0.34 * s) else 1
    shade_smooth(obj)
    obj.rotation_mode = 'XYZ'
    place(obj, "Flags")
    return obj

def stele(name, x, y, rot=0.0, col="Temple"):
    """Stone stele (bia) on a turtle base — classic Trần courtyard element."""
    base = box(f"{name}_TurtleBase", (1.5, 2.3, 0.35), (x, y, 0.18))
    base.data.materials.append(MAT["stone"])
    place(base, col)
    shell = sphere(f"{name}_Shell", 0.72, (x, y - 0.15, 0.45), segs=12, rings=8)
    shell.scale = (1.0, 1.45, 0.55)
    shell.data.materials.append(MAT["stone"])
    place(shell, col)
    head = box(f"{name}_Head", (0.42, 0.5, 0.4), (x, y + 1.35, 0.48))
    head.data.materials.append(MAT["stone"])
    place(head, col)
    slab = box(f"{name}_Slab", (1.1, 0.22, 2.3), (x, y - 0.2, 1.65))
    slab.data.materials.append(MAT["lime"])
    place(slab, col)
    cap = box(f"{name}_Cap", (1.35, 0.45, 0.22), (x, y - 0.2, 2.90))
    cap.data.materials.append(MAT["stone"])
    place(cap, col)
    for o in (base, shell, head, slab, cap):
        o.rotation_euler = (0, 0, rot)

def urn(name, x, y, z=0.0, s=1.0, col="Temple"):
    foot = cylinder(f"{name}_Foot", 0.15 * s, 0.12 * s, (x, y, z + 0.06 * s), verts=10)
    foot.data.materials.append(MAT["urn"])
    place(foot, col)
    bowl = cylinder(f"{name}_Bowl", 0.33 * s, 0.34 * s, (x, y, z + 0.29 * s), verts=12)
    bowl.data.materials.append(MAT["urn"])
    place(bowl, col)
    rim = cylinder(f"{name}_Rim", 0.36 * s, 0.06 * s, (x, y, z + 0.49 * s), verts=12)
    rim.data.materials.append(MAT["gold"])
    place(rim, col)

def lamp_post(name, x, y):
    post = cylinder(f"{name}_Post", 0.09, 2.3, (x, y, 1.15), verts=8)
    post.data.materials.append(MAT["stone"])
    place(post, "Grounds")
    head = box(f"{name}_Head", (0.34, 0.34, 0.42), (x, y, 2.45))
    head.data.materials.append(MAT["gold"])
    place(head, "Grounds")
    cap = hip_roof(f"{name}_Cap", 0.30, 0.30, 0.20, 2.66, seg=4)
    place(cap, "Grounds")

def corbel_band(name, hw, hd, z, col, mat=None):
    """Protruding corbel/under-eave band ring around a pavilion tier."""
    mmat = mat or MAT["wood"]
    for tag, size, loc in (("N", (2 * hw + 0.2, hd * 2 + 0.2, 0.14), (0, 0, z)),):
        b = box(f"{name}_{tag}", size, loc)
        b.data.materials.append(mmat)
        place(b, col)

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

def tile_roof(name, c1, c2, rough=0.5):
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
    brick.inputs["Mortar"].default_value = (0.08, 0.06, 0.05, 1.0)
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
    MAT["brick"]  = masonry("DenTran_Brick", (0.640, 0.098, 0.030), (0.500, 0.072, 0.026),
                            (0.32, 0.20, 0.15), bw=0.42, rh=0.20, weather=0.35,
                            lo=0.80, hi=1.12, streak=True)
    MAT["brick_d"] = masonry("DenTran_BrickDark", (0.500, 0.078, 0.028), (0.380, 0.058, 0.022),
                             (0.25, 0.16, 0.12), bw=0.42, rh=0.20, weather=0.38,
                             lo=0.80, hi=1.1, streak=True)
    MAT["tile"]   = tile_roof("DenTran_Tile_Red", (0.260, 0.088, 0.042), (0.330, 0.118, 0.058), rough=0.46)
    MAT["tile_old"] = tile_roof("DenTran_Tile_Old", (0.130, 0.105, 0.078), (0.175, 0.145, 0.108), rough=0.55)
    MAT["stone"]  = masonry("DenTran_Stone", (0.415, 0.408, 0.392), (0.335, 0.330, 0.318),
                            (0.30, 0.295, 0.285), bw=0.62, rh=0.30, weather=0.4, bump=0.1)
    MAT["lime"]   = masonry("DenTran_Lime", (0.720, 0.705, 0.675), (0.640, 0.625, 0.598),
                            (0.60, 0.59, 0.565), bw=0.5, rh=0.25, weather=0.42,
                            lo=0.68, hi=1.15, streak=True)
    MAT["wood"]   = pbr("DenTran_Wood_Dark", (0.068, 0.048, 0.030), rough=0.8)
    MAT["door"]   = pbr("DenTran_Door_Brown", (0.115, 0.062, 0.034), rough=0.72)
    MAT["leaf3"]  = pbr("DenTran_Foliage_Olive", (0.130, 0.155, 0.048), rough=0.85)
    MAT["col_red"] = pbr("DenTran_Column_Lacquer", (0.310, 0.050, 0.028), rough=0.5)
    MAT["fascia"]  = pbr("DenTran_Fascia_Red", (0.365, 0.058, 0.030), rough=0.6)
    MAT["lattice"] = pbr("DenTran_Lattice_Wood", (0.085, 0.055, 0.035), rough=0.75)
    MAT["gold"]   = pbr("DenTran_Gold", (0.72, 0.55, 0.20), rough=0.4, metal=0.85)
    MAT["flag_r"] = pbr("DenTran_Flag_Red", (0.45, 0.030, 0.020), rough=0.75)
    MAT["banner"] = pbr("DenTran_Banner_Orange", (0.68, 0.28, 0.04), rough=0.7)
    MAT["banner_y"] = pbr("DenTran_Banner_Yellow", (0.75, 0.55, 0.08), rough=0.7)
    MAT["leaf"]   = pbr("DenTran_Foliage", (0.062, 0.120, 0.040), rough=0.85)
    MAT["leaf2"]  = pbr("DenTran_Foliage_Light", (0.110, 0.180, 0.052), rough=0.85)
    MAT["trunk"]  = pbr("DenTran_Trunk", (0.15, 0.115, 0.082), rough=0.9)
    MAT["gravel"] = pbr("DenTran_Gravel", (0.470, 0.452, 0.418), rough=0.96)
    MAT["pave"]   = pbr("DenTran_Paving", (0.398, 0.385, 0.362), rough=0.92)
    MAT["field1"] = pbr("DenTran_Field_Light", (0.150, 0.235, 0.050), rough=0.95)
    MAT["field2"] = pbr("DenTran_Field_Dark", (0.095, 0.170, 0.038), rough=0.95)
    MAT["paddy"]  = pbr("DenTran_Paddy_Water", (0.042, 0.085, 0.038), rough=0.22)
    MAT["grass_mound"] = pbr("DenTran_Mound_Grass", (0.105, 0.185, 0.045), rough=0.95)
    MAT["urn"]    = pbr("DenTran_Urn_Bronze", (0.105, 0.078, 0.042), rough=0.35, metal=0.9)
    MAT["ground"] = pbr("DenTran_Ground_Earth", (0.245, 0.190, 0.125), rough=0.95)

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
build_materials()

COL = {}
for cname in ["Wall_Gate", "Temple", "Grounds", "Fields", "Trees", "Flags",
              "Lighting", "Cameras", "Environment"]:
    COL[cname] = bpy.data.collections.new(cname)
    scene.collection.children.link(COL[cname])

def place(obj, cname):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    COL[cname].objects.link(obj)
    return obj

# ---------------------------------------------------------------- dimensions
WALL_W, WALL_D, WALL_H = 60.0, 2.8, 4.3
ARCH_HW, ARCH_TOP = 1.55, 3.30           # 3 big arches: centres -4.8, 0, 4.8
ARCH_CXS = (-4.8, 0.0, 4.8)
SM_ARCH_CX, SM_ARCH_HW, SM_ARCH_TOP = 21.5, 1.05, 2.75
GATE_T1_W, GATE_T1_D, GATE_T1_H = 16.0, 4.6, 2.4   # tier-1 hall over the wall
GATE_T2_W, GATE_T2_D, GATE_T2_H = 7.0, 3.6, 2.1    # centre pavilion
SIDE_GATE_CX = 14.0

T_Z0 = 0.9                                # temple platform height
DY = 34.0                                 # đại điện centre y
DD_W, DD_D, DD_H = 18.0, 8.5, 4.3
SH_W, SH_D, SH_H = 8.0, 6.0, 3.2          # side halls
SH_CX = 15.5

FLAG_XY = (0.0, -13.0)
FLAG_H = 22.0

AV_Y0, AV_Y1 = -8.0, -72.0                # avenue extent
AV_W = 9.0
MOUND_XY = (17.0, -40.0)

# ================================================================ 1. GROUND + FIELDS
gnd = box("Ground_Earth", (300, 300, 0.1), (0, -20, -0.06))
place(gnd, "Environment")
gnd.data.materials.append(MAT["ground"])

# rice paddies both sides of the avenue + around the complex
def field(name, cx, cy, w, d, mat):
    f = box(name, (w, 0.08, d), (cx, cy, -0.02))
    f.rotation_euler = (0, 0, 0)
    f.scale = (1, 1, 1)
    f.data.materials.append(MAT[mat])
    place(f, "Fields")
    return f

# build flat field slabs (x,z sizes mapped: use size (w, d, 0.06))
def field2(name, cx, cy, w, d, mat):
    f = box(name, (w, d, 0.06), (cx, cy, -0.03))
    f.data.materials.append(MAT[mat])
    place(f, "Fields")
    return f

field2("Field_W_Far", -70, -30, 110, 110, "field1")
field2("Field_E_Far", 70, -30, 110, 110, "field2")
field2("Field_W_Near", -46, -18, 55, 80, "field2")
field2("Field_E_Near", 46, -18, 55, 80, "field1")
field2("Field_North", 0, 60, 200, 60, "field1")
# paddy water strips (reflective)
for i, (px, py, pw, pd) in enumerate([(-32, -30, 22, 30), (34, -44, 26, 34),
                                      (-52, -52, 30, 24), (55, -18, 20, 26)]):
    p = box(f"Paddy_{i}", (pw, pd, 0.045), (px, py, -0.01))
    p.data.materials.append(MAT["paddy"])
    place(p, "Fields")

# gravel forecourt inside + in front of the wall
fc = box("Forecourt", (66, 40, 0.08), (0, -8.5, -0.02))
fc.data.materials.append(MAT["gravel"])
place(fc, "Grounds")
# temple courtyard gravel
cy = box("Temple_Yard", (52, 26, 0.08), (0, 18, -0.02))
cy.data.materials.append(MAT["gravel"])
place(cy, "Grounds")

# axial avenue: raised paved strip from the gate through the fields
av = box("Avenue_Paving", (AV_W, AV_Y0 - AV_Y1, 0.10), (0, (AV_Y0 + AV_Y1) / 2, -0.01))
av.data.materials.append(MAT["pave"])
place(av, "Grounds")

# stone columns lining the avenue
COL_N = 9
for i in range(COL_N):
    y = -14.0 - i * 6.2
    for sgn in (-1, 1):
        x = sgn * 3.8
        ped = box(f"AveCol_Ped_{sgn}_{i}", (0.9, 0.9, 0.55), (x, y, 0.20))
        ped.data.materials.append(MAT["stone"])
        place(ped, "Grounds")
        shaft = cylinder(f"AveCol_Shaft_{sgn}_{i}", 0.21, 3.3, (x, y, 2.10), verts=9)
        shaft.data.materials.append(MAT["lime"])
        place(shaft, "Grounds")
        cap = sphere(f"AveCol_Ball_{sgn}_{i}", 0.26, (x, y, 3.95), segs=9, rings=6)
        cap.data.materials.append(MAT["stone"])
        place(cap, "Grounds")

# two grass mounds flanking the avenue (historic earthworks)
for sgn in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=10,
        radius=6.8, location=(sgn * 15.0, -31.0 + sgn * 3.0, -1.2))
    mound = bpy.context.object
    mound.name = f"Earth_Mound_{sgn}"
    mound.scale = (1.0, 1.25, 0.62)
    shade_smooth(mound)
    mound.data.materials.append(MAT["grass_mound"])
    place(mound, "Fields")

# ================================================================ 2. ENCLOSURE WALL + GATE
wall = arch_wall(
    "Wall_Main", WALL_W, WALL_D, WALL_H,
    openings=[(cx, ARCH_HW, 'arc', ARCH_TOP - ARCH_HW, ARCH_HW) for cx in ARCH_CXS] +
             [(-SM_ARCH_CX, SM_ARCH_HW, 'arc', SM_ARCH_TOP - SM_ARCH_HW, SM_ARCH_HW),
              (SM_ARCH_CX, SM_ARCH_HW, 'arc', SM_ARCH_TOP - SM_ARCH_HW, SM_ARCH_HW)],
    slices=48, pier_mat=MAT["brick"])
place(wall, "Wall_Gate")

# brick cornice + red tile coping along the wall top
corn = box("Wall_Cornice", (WALL_W + 0.5, WALL_D + 0.4, 0.24), (0, 0, WALL_H + 0.12))
corn.data.materials.append(MAT["brick_d"])
place(corn, "Wall_Gate")
cop = box("Wall_Coping", (WALL_W + 0.6, WALL_D + 0.55, 0.14), (0, 0, WALL_H + 0.30))
cop.data.materials.append(MAT["tile"])
place(cop, "Wall_Gate")

# white arch trims on the 3 big + 2 small arches (double rings, front + back)
for cx in ARCH_CXS:
    arch_trim(f"WallTrim_{cx:.0f}", cx, ARCH_HW, ARCH_TOP - ARCH_HW, WALL_D / 2)
    arch_trim(f"WallTrimB_{cx:.0f}", cx, ARCH_HW, ARCH_TOP - ARCH_HW, -WALL_D / 2 - 0.14)
    arch_trim(f"WallTrim2_{cx:.0f}", cx, ARCH_HW + 0.16, ARCH_TOP - ARCH_HW + 0.10, WALL_D / 2 - 0.02)
for sgn in (-1, 1):
    arch_trim(f"WallTrim_S_{sgn}", sgn * SM_ARCH_CX, SM_ARCH_HW, SM_ARCH_TOP - SM_ARCH_HW, WALL_D / 2)
    arch_trim(f"WallTrim2_S_{sgn}", sgn * SM_ARCH_CX, SM_ARCH_HW + 0.12,
              SM_ARCH_TOP - SM_ARCH_HW + 0.08, WALL_D / 2 - 0.02)

# dark tunnel back-panels (so arches read deep) + narrow open door pairs
for cx in ARCH_CXS:
    rv = box(f"Wall_Reveal_{cx:.0f}", (ARCH_HW * 2 - 0.15, 0.30, ARCH_TOP - 0.06),
             (cx, 0.0, (ARCH_TOP - 0.06) / 2))
    rv.data.materials.append(MAT["wood"])
    place(rv, "Wall_Gate")
    for sgn in (-1, 1):
        d = box(f"Wall_Door_{cx:.0f}_{sgn}", (ARCH_HW * 0.52, 0.08, ARCH_TOP - 0.35),
                (cx + sgn * ARCH_HW * 0.50, WALL_D / 2 - 0.38, (ARCH_TOP - 0.35) / 2))
        d.data.materials.append(MAT["door"])
        place(d, "Wall_Gate")
for sgn in (-1, 1):
    rv = box(f"Wall_Reveal_S_{sgn}", (SM_ARCH_HW * 2 - 0.12, 0.30, SM_ARCH_TOP - 0.05),
             (sgn * SM_ARCH_CX, 0.0, (SM_ARCH_TOP - 0.05) / 2))
    rv.data.materials.append(MAT["wood"])
    place(rv, "Wall_Gate")
    d = box(f"Wall_Door_S_{sgn}", (SM_ARCH_HW * 1.6, 0.08, SM_ARCH_TOP - 0.3),
            (sgn * SM_ARCH_CX, WALL_D / 2 - 0.38, (SM_ARCH_TOP - 0.3) / 2))
    d.data.materials.append(MAT["door"])
    place(d, "Wall_Gate")

# orange banner on the wall between arch tops and cornice
ban = box("Wall_Banner", (10.5, 0.06, 0.95), (0, WALL_D / 2 + 0.05, WALL_H - 0.72))
ban.data.materials.append(MAT["banner"])
place(ban, "Wall_Gate")
ban2 = box("Wall_Banner_Text", (9.6, 0.02, 0.5), (0, WALL_D / 2 + 0.09, WALL_H - 0.72))
ban2.data.materials.append(MAT["banner_y"])
place(ban2, "Wall_Gate")

# ---- gate pavilion tier 1 (long hall) + tier 2 (centre pavilion)
GZ = WALL_H + 0.36
t1 = box("Gate_T1_Body", (GATE_T1_W, GATE_T1_D, GATE_T1_H), (0, 0, GZ + GATE_T1_H / 2))
t1.data.materials.append(MAT["brick"])
place(t1, "Wall_Gate")
# tier-1 open hall: white columns along front/back
for k in range(7):
    x = -GATE_T1_W / 2 + 0.9 + k * ((GATE_T1_W - 1.8) / 6)
    for sy in (-1, 1):
        c = cylinder(f"Gate_T1_Col_{k}_{sy}", 0.13, GATE_T1_H,
                     (x, sy * (GATE_T1_D / 2 - 0.35), GZ + GATE_T1_H / 2), verts=8)
        c.data.materials.append(MAT["lime"])
        place(c, "Wall_Gate")
r_t1 = hip_roof("Gate_Roof_T1", GATE_T1_W / 2 + 1.0, GATE_T1_D / 2 + 0.7, 1.25, GZ + GATE_T1_H - 0.04, mat="tile")
place(r_t1, "Wall_Gate")
dao_tips("Gate_Roof_T1", GATE_T1_W / 2 + 1.0, GATE_T1_D / 2 + 0.7, 1.25, GZ + GATE_T1_H - 0.04)

T2_Z = GZ + GATE_T1_H + 0.75
t2 = box("Gate_T2_Body", (GATE_T2_W, GATE_T2_D, GATE_T2_H), (0, 0, T2_Z + GATE_T2_H / 2))
t2.data.materials.append(MAT["brick"])
place(t2, "Wall_Gate")
for k in range(4):
    x = -GATE_T2_W / 2 + 0.6 + k * ((GATE_T2_W - 1.2) / 3)
    for sy in (-1, 1):
        c = cylinder(f"Gate_T2_Col_{k}_{sy}", 0.11, GATE_T2_H,
                     (x, sy * (GATE_T2_D / 2 - 0.3), T2_Z + GATE_T2_H / 2), verts=8)
        c.data.materials.append(MAT["lime"])
        place(c, "Wall_Gate")
r_t2 = hip_roof("Gate_Roof_T2", GATE_T2_W / 2 + 0.9, GATE_T2_D / 2 + 0.55, 1.05, T2_Z + GATE_T2_H - 0.04, mat="tile")
place(r_t2, "Wall_Gate")
dao_tips("Gate_Roof_T2", GATE_T2_W / 2 + 0.9, GATE_T2_D / 2 + 0.55, 1.05, T2_Z + GATE_T2_H - 0.04)
fin = sphere("Gate_Finial", 0.13, (0, 0, T2_Z + GATE_T2_H + 1.05))
fin.data.materials.append(MAT["gold"])
place(fin, "Wall_Gate")

# white balustrade on the wall-top terrace both sides of the pavilion
for sgn in (-1, 1):
    balustrade_x(f"WallBal_{sgn}", sgn * 8.2, sgn * 15.0, WALL_D / 2 + 0.25, WALL_H + 0.36, "Wall_Gate")
    balustrade_x(f"WallBalB_{sgn}", sgn * 8.2, sgn * 15.0, -WALL_D / 2 - 0.25, WALL_H + 0.36, "Wall_Gate")

# ---- small side gate pavilions in the wall
for sgn in (-1, 1):
    xg = sgn * SIDE_GATE_CX
    g = box(f"SideGate_Body_{sgn}", (3.4, 3.2, 2.5), (xg, 0, 1.25))
    g.data.materials.append(MAT["brick"])
    place(g, "Wall_Gate")
    ga = arch_wall(f"SideGate_Arch_{sgn}", 3.4, 3.2, 2.5,
                   openings=[(0.0, 0.85, 'arc', 2.5 - 0.85, 0.85)], slices=8,
                   pier_mat=MAT["brick"])
    ga.location = (xg, 0, 0)
    place(ga, "Wall_Gate")
    body = bpy.data.objects[f"SideGate_Body_{sgn}"]
    bpy.data.objects.remove(body, do_unlink=True)   # arch wall replaces solid body
    gr = hip_roof(f"SideGate_Roof_{sgn}", 2.4, 2.3, 0.75, 2.5 - 0.04, mat="tile")
    gr.location.x = xg
    place(gr, "Wall_Gate")
    dao_tips(f"SideGate_Roof_{sgn}", 2.4, 2.3, 0.75, 2.5 - 0.04, off_x=xg)

# ---- ornate corner pillars (two pairs, in front of the wall)
def corner_pillar(name, x, y, h=7.4):
    base = box(f"{name}_Base", (1.5, 1.5, 0.9), (x, y, 0.45))
    base.data.materials.append(MAT["lime"])
    place(base, "Wall_Gate")
    b2 = box(f"{name}_Base2", (1.15, 1.15, 0.5), (x, y, 1.12))
    b2.data.materials.append(MAT["stone"])
    place(b2, "Wall_Gate")
    shaft = box(f"{name}_Shaft", (0.72, 0.72, h - 2.4), (x, y, 1.35 + (h - 2.4) / 2))
    shaft.data.materials.append(MAT["lime"])
    place(shaft, "Wall_Gate")
    for k in range(3):
        disc = cylinder(f"{name}_Disc_{k}", 0.55 - k * 0.09, 0.16,
                        (x, y, h - 0.85 + k * 0.22), verts=10)
        disc.data.materials.append(MAT["stone"])
        place(disc, "Wall_Gate")
    tip = cone_tip = cylinder(f"{name}_Tip", 0.10, 0.7, (x, y, h + 0.15), verts=8)
    tip.data.materials.append(MAT["stone"])
    place(tip, "Wall_Gate")
    ball = sphere(f"{name}_Ball", 0.12, (x, y, h + 0.58))
    ball.data.materials.append(MAT["gold"])
    place(ball, "Wall_Gate")
    # red banner strip hanging on the front face
    bb = box(f"{name}_Banner", (0.5, 0.05, 2.6), (x, y - 0.42, h - 2.1))
    bb.data.materials.append(MAT["banner"])
    place(bb, "Wall_Gate")

corner_pillar("Pillar_NW", -10.6, -5.2)
corner_pillar("Pillar_NE", 10.6, -5.2)
corner_pillar("Pillar_FW", -16.5, -6.8, h=6.6)
corner_pillar("Pillar_FE", 16.5, -6.8, h=6.6)

# steps up to the big central arch
for k in range(2):
    st = box(f"Gate_Step_{k}", (6.4 - k * 0.6, 0.85, 0.16 * (k + 1)),
             (0, -WALL_D / 2 - 0.5 - k * 0.8, 0.08 * (k + 1)))
    st.data.materials.append(MAT["stone"])
    place(st, "Wall_Gate")

# ================================================================ 3. NGHI MÔN (4 columns)
NM_Y = 14.0
def nghi_col(name, x, h):
    base = box(f"{name}_Base", (1.0, 1.0, 0.5), (x, NM_Y, 0.25))
    base.data.materials.append(MAT["stone"])
    place(base, "Temple")
    shaft = box(f"{name}_Shaft", (0.66, 0.66, h - 1.4), (x, NM_Y, 0.5 + (h - 1.4) / 2))
    shaft.data.materials.append(MAT["lime"])
    place(shaft, "Temple")
    cap = hip_roof(f"{name}_Cap", 0.62, 0.62, 0.34, h - 0.30, seg=4, mat="tile_old")
    cap.location.x = x
    cap.location.y = NM_Y
    place(cap, "Temple")
    dao_tips(f"{name}_Cap", 0.62, 0.62, 0.34, h - 0.30, off_x=x, off_y=NM_Y, col="Temple")

nghi_col("NghiCol_WTall", -2.3, 6.8)
nghi_col("NghiCol_ETall", 2.3, 6.8)
nghi_col("NghiCol_WShort", -5.6, 5.2)
nghi_col("NghiCol_EShort", 5.6, 5.2)
# beams + connecting tile roofs between columns
for z, y_beam in ((4.4, 0.0), (3.4, 0.0)):
    pass
beam = box("Nghi_Beam_Main", (4.6 + 2.3, 0.4, 0.35), (0, NM_Y, 4.65))
beam.data.materials.append(MAT["wood"])
place(beam, "Temple")
for sgn in (-1, 1):
    bm2 = box(f"Nghi_Beam_Side_{sgn}", (3.3, 0.32, 0.28), (sgn * 3.95, NM_Y, 3.75))
    bm2.data.materials.append(MAT["wood"])
    place(bm2, "Temple")
    roof_s = hip_roof(f"Nghi_Roof_Side_{sgn}", 1.95, 0.75, 0.4, 4.05, seg=4, mat="tile_old")
    roof_s.location = (sgn * 3.95, NM_Y, 4.05)
    place(roof_s, "Temple")

# ================================================================ 4. ĐẠI ĐIỆN (main hall)
plinth = box("DD_Plinth", (DD_W + 3.2, DD_D + 3.2, T_Z0), (0, DY, T_Z0 / 2))
plinth.data.materials.append(MAT["stone"])
place(plinth, "Temple")
for k in range(3):
    st = box(f"DD_Step_{k}", (DD_W - 2 + (2 - k) * 1.2, 0.9, 0.22 * (k + 1)),
             (0, DY - DD_D / 2 - 1.6 - k * 0.85, 0.11 * (k + 1)))
    st.data.materials.append(MAT["stone"])
    place(st, "Temple")

# dark timber hall body with red door band
body = box("DD_Body", (DD_W, DD_D, DD_H), (0, DY, T_Z0 + DD_H / 2))
body.data.materials.append(MAT["wood"])
place(body, "Temple")
for k in range(5):
    dx = -6.4 + k * 3.2
    d = box(f"DD_Door_{k}", (1.9, 0.12, 2.6), (dx, DY - DD_D / 2 - 0.03, T_Z0 + 1.35))
    d.data.materials.append(MAT["door"])
    place(d, "Temple")
# front colonnade — RED LACQUER columns + dark lattice panels between them
for k in range(7):
    x = -DD_W / 2 + 1.1 + k * ((DD_W - 2.2) / 6)
    c = cylinder(f"DD_Col_{k}", 0.17, DD_H, (x, DY - DD_D / 2 + 0.55, T_Z0 + DD_H / 2), verts=10)
    c.data.materials.append(MAT["col_red"])
    place(c, "Temple")
    b2 = box(f"DD_ColBase_{k}", (0.5, 0.5, 0.25), (x, DY - DD_D / 2 + 0.55, T_Z0 + 0.12))
    b2.data.materials.append(MAT["stone"])
    place(b2, "Temple")
    if k < 6:
        mid = (x + (x + (DD_W - 2.2) / 6) / 2)
        lp = lattice_panel(f"DD_Lattice_{k}", mid + (DD_W - 2.2) / 12, DY - DD_D / 2 + 0.55,
                           1.4, 2.1, T_Z0 + 0.55, axis='x', col="Temple", mull=4)
# plaque above the doors (gold on red, framed)
pl = box("DD_Plaque", (4.6, 0.10, 0.9), (0, DY - DD_D / 2 - 0.08, T_Z0 + 3.35))
pl.data.materials.append(MAT["fascia"])
place(pl, "Temple")
plf = box("DD_PlaqueFrame", (4.85, 0.08, 1.12), (0, DY - DD_D / 2 - 0.05, T_Z0 + 3.35))
plf.data.materials.append(MAT["gold"])
place(plf, "Temple")
plt = box("DD_PlaqueText", (3.6, 0.04, 0.42), (0, DY - DD_D / 2 - 0.13, T_Z0 + 3.35))
plt.data.materials.append(MAT["gold"])
place(plt, "Temple")
# lattice above doors between the columns
for k in range(5):
    dx = -6.4 + k * 3.2
    lattice_panel(f"DD_Fanlight_{k}", dx, DY - DD_D / 2 - 0.04, 1.7, 0.7, T_Z0 + 2.85,
                  axis='x', col="Temple", mull=6, mat=MAT["wood"])

# corbel band under the roofline + red fascia band (Trần hall signature)
corbel_band("DD_Corbel", DD_W / 2 + 1.3, DD_D / 2 + 1.1, T_Z0 + DD_H - 0.16, "Temple")
fas = box("DD_Fascia_Band", (DD_W - 0.6, 0.12, 0.30), (0, DY - DD_D / 2 - 1.30, T_Z0 + DD_H - 0.20))
fas.data.materials.append(MAT["fascia"])
place(fas, "Temple")
fas2 = box("DD_Fascia_Band_B", (DD_W - 0.6, 0.12, 0.30), (0, DY + DD_D / 2 + 1.30, T_Z0 + DD_H - 0.20))
fas2.data.materials.append(MAT["fascia"])
place(fas2, "Temple")

# two-tier roof stack (Trần style): STEEP lower roof, upper tier buried deep
# into its slope, intermediate eave skirt between tiers — no floating gaps
T1_RISE = 3.4
r1_dd = hip_roof("DD_Roof_T1", DD_W / 2 + 1.6, DD_D / 2 + 1.4, T1_RISE, T_Z0 + DD_H - 0.06,
                 curve=0.85, seg=10, thick=0.34, mat="tile_old")
place(r1_dd, "Temple")
dao_tips("DD_Roof_T1", DD_W / 2 + 1.6, DD_D / 2 + 1.4, T1_RISE, T_Z0 + DD_H - 0.06, curve=0.85, col="Temple")
# intermediate eave skirt (chồng diêm) where the upper tier passes through T1
UP_W, UP_D, UP_H = 11.0, 5.6, 2.5
upz = T_Z0 + DD_H + T1_RISE - 2.6          # upper body base INSIDE the T1 slope
sk = hip_roof("DD_Roof_Mid", UP_W / 2 + 1.15, UP_D / 2 + 1.15, 0.55, upz - 0.02,
              curve=0.7, seg=6, thick=0.18, mat="tile_old")
sk.location.y = DY
place(sk, "Temple")
dao_tips("DD_Roof_Mid", UP_W / 2 + 1.15, UP_D / 2 + 1.15, 0.55, upz - 0.02, curve=0.7,
         off_y=DY, col="Temple")
up = box("DD_Upper_Body", (UP_W, UP_D, UP_H), (0, DY, upz + UP_H / 2))
up.data.materials.append(MAT["wood"])
place(up, "Temple")
r2_dd = hip_roof("DD_Roof_T2", UP_W / 2 + 1.5, UP_D / 2 + 1.4, 2.0, upz + UP_H - 0.05,
                 curve=0.85, seg=8, thick=0.28, mat="tile_old")
r2_dd.location.y = DY
place(r2_dd, "Temple")
dao_tips("DD_Roof_T2", UP_W / 2 + 1.5, UP_D / 2 + 1.4, 2.0, upz + UP_H - 0.05, curve=0.85,
         off_y=DY, col="Temple")
# ridge bars + dragon-horn end tips on both roof tiers
for tag2, hw2, z_ap in (("T1", DD_W / 2 + 1.6, T_Z0 + DD_H + T1_RISE - 0.35),
                        ("T2", UP_W / 2 + 1.5, upz + UP_H + 1.85)):
    rb3 = box(f"DD_RidgeBar_{tag2}", (hw2 * 2 - 1.0, 0.20, 0.14), (0, DY, z_ap))
    rb3.data.materials.append(MAT["lime"])
    place(rb3, "Temple")
    for sx2 in (-1, 1):
        horn = cylinder(f"DD_RidgeHorn_{tag2}_{sx2}", 0.05, 0.75,
                        (sx2 * (hw2 - 0.55), DY, z_ap + 0.28), verts=7,
                        rot=(0, radians(-42) * sx2, 0))
        horn.data.materials.append(MAT["lime"])
        place(horn, "Temple")
fin2 = sphere("DD_Finial", 0.15, (0, DY, upz + UP_H + 1.95))
fin2.data.materials.append(MAT["gold"])
place(fin2, "Temple")
spire = cylinder("DD_Finial_Spire", 0.04, 0.55, (0, DY, upz + UP_H + 2.3), verts=8)
spire.data.materials.append(MAT["gold"])
place(spire, "Temple")

# side halls (tả vu / hữu vu)
for sgn in (-1, 1):
    xh = sgn * SH_CX
    pl2 = box(f"SH_Plinth_{sgn}", (SH_W + 1.6, SH_D + 1.6, 0.45), (xh, DY, 0.225))
    pl2.data.materials.append(MAT["stone"])
    place(pl2, "Temple")
    hb = box(f"SH_Body_{sgn}", (SH_W, SH_D, SH_H), (xh, DY, 0.45 + SH_H / 2))
    hb.data.materials.append(MAT["wood"])
    place(hb, "Temple")
    hr = hip_roof(f"SH_Roof_{sgn}", SH_W / 2 + 1.0, SH_D / 2 + 0.9, 1.25, 0.45 + SH_H - 0.05,
                  seg=8, thick=0.24, mat="tile_old")
    hr.location.x = xh
    hr.location.y = DY
    place(hr, "Temple")
    dao_tips(f"SH_Roof_{sgn}", SH_W / 2 + 1.0, SH_D / 2 + 0.9, 1.25, 0.45 + SH_H - 0.05,
             off_x=xh, off_y=DY, col="Temple")
    for k in range(4):
        dx = xh - SH_W / 2 + 1.0 + k * ((SH_W - 2.0) / 3)
        d = box(f"SH_Door_{sgn}_{k}", (1.2, 0.10, 1.9), (dx, DY - SH_D / 2 - 0.03, 0.45 + 0.95))
        d.data.materials.append(MAT["door"])
        place(d, "Temple")

# ================================================================ 4b. DETAIL PASS
# --- hanging lanterns under the gate roofs + DD eave corners (animated)
flag_objs = []
for sx in (-1, 1):
    flag_objs.append(hanging_lantern(f"Lantern_Gate_{sx}", sx * 5.2, -(GATE_T1_D / 2 + 0.5), GZ + 1.6, 1.0))
for sx in (-1, 1):
    flag_objs.append(hanging_lantern(f"Lantern_DD_{sx}", sx * (DD_W / 2 - 0.8),
                                     DY - DD_D / 2 - 1.25, T_Z0 + DD_H - 0.15, 1.1))
flag_objs.append(hanging_lantern("Lantern_DD_C", 0.0, DY - DD_D / 2 - 1.35, T_Z0 + DD_H - 0.05, 1.2))

# --- stone steles on turtle bases + bronze urns in the courtyard
stele("Stele_W", -9.5, 20.0, rot=radians(-4))
stele("Stele_E", 9.5, 20.0, rot=radians(3))
urn("Urn_DD_L", -2.6, DY - DD_D / 2 - 3.1, 0.0, 1.15)
urn("Urn_DD_R", 2.6, DY - DD_D / 2 - 3.1, 0.0, 1.15)
urn("Urn_Gate_L", -3.0, 5.6, 0.0, 1.0, col="Grounds")
urn("Urn_Gate_R", 3.0, 5.6, 0.0, 1.0, col="Grounds")

# --- ornate avenue columns: red band + inscription ring + lotus-cap upgrade
for i in range(COL_N):
    y = -14.0 - i * 6.2
    for sgn in (-1, 1):
        x = sgn * 3.8
        band = cylinder(f"AveCol_Band_{sgn}_{i}", 0.225, 0.28, (x, y, 2.55), verts=9)
        band.data.materials.append(MAT["col_red"])
        place(band, "Grounds")
        ring = cylinder(f"AveCol_Ring_{sgn}_{i}", 0.235, 0.10, (x, y, 1.15), verts=9)
        ring.data.materials.append(MAT["stone"])
        place(ring, "Grounds")
        lotus = sphere(f"AveCol_Lotus_{sgn}_{i}", 0.24, (x, y, 3.92), segs=10, rings=7)
        lotus.scale = (1.0, 1.0, 0.75)
        lotus.data.materials.append(MAT["lime"])
        place(lotus, "Grounds")

# --- lamp posts along the avenue edges + courtyard
def lamp_post2(x, y):
    lp = lamp_post(f"Lamp_{x:.0f}_{y:.0f}", x, y)
    return lp

for k in range(4):
    yy = -16.0 - k * 12.0
    lamp_post2(-6.2, yy)
    lamp_post2(6.2, yy)
lamp_post2(-13.5, 12.0)
lamp_post2(13.5, 12.0)

# --- curbs + cross paths on the forecourt
curb = box("Forecourt_Curb_N", (52, 0.4, 0.12), (0, 11.2, 0.04))
curb.data.materials.append(MAT["stone"])
place(curb, "Grounds")
curb2 = box("Forecourt_Curb_S", (52, 0.4, 0.12), (0, -27.0, 0.04))
curb2.data.materials.append(MAT["stone"])
place(curb2, "Grounds")
for k, px in enumerate((-8.0, 0.0, 8.0)):
    path = box(f"Yard_Path_{k}", (1.6, 36.0, 0.07), (px, -7.5, 0.005))
    path.data.materials.append(MAT["pave"])
    place(path, "Grounds")

# ================================================================ 5. GIANT FLAG
pole = cylinder("Flagpole", 0.09, FLAG_H, (FLAG_XY[0], FLAG_XY[1], FLAG_H / 2), verts=10)
pole.data.materials.append(MAT["trunk"])
place(pole, "Flags")
ball = sphere("Flagpole_Ball", 0.16, (FLAG_XY[0], FLAG_XY[1], FLAG_H + 0.10), segs=10, rings=6)
ball.data.materials.append(MAT["gold"])
place(ball, "Flags")
base = cylinder("Flagpole_Base", 0.75, 0.9, (FLAG_XY[0], FLAG_XY[1], 0.45), verts=12)
base.data.materials.append(MAT["stone"])
place(base, "Flags")
big_flag = flag_cloth("Flag_Cloth_Giant", FLAG_XY[0] + 0.06, FLAG_XY[1], FLAG_H - 0.4,
                      w=2.6, h=1.7, mat="flag_r")
# small yellow banner flags on the corner pillars
f2 = flag_cloth("Flag_Cloth_PillarW", -10.6 + 0.06, -5.2, 7.0, w=1.1, h=0.7, mat="banner_y")
f3 = flag_cloth("Flag_Cloth_PillarE", 10.6 + 0.06, -5.2, 7.0, w=1.1, h=0.7, mat="banner_y")
flag_objs.extend([big_flag, f2, f3])

# ================================================================ 6. TREES
def tree(name, x, y, h=5.0, r=2.4, seed=1, light=False):
    rnd = random.Random(seed)
    trunk = cylinder(f"{name}_Trunk", 0.24, h, (x, y, h / 2), verts=7)
    trunk.data.materials.append(MAT["trunk"])
    trunk.rotation_euler = (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 0)
    place(trunk, "Trees")
    lmat = "leaf2" if light else "leaf"
    for k, (dz, sr) in enumerate(((h * 0.55, r), (h * 0.75, r * 0.8), (h * 0.95, r * 0.55))):
        blob = sphere(f"{name}_Foliage_{k}", sr,
                      (x + rnd.uniform(-0.5, 0.5), y + rnd.uniform(-0.5, 0.5), dz),
                      segs=9, rings=6)
        blob = blob if blob else None
        b = bpy.data.objects[f"{name}_Foliage_{k}"]
        b.scale = (1.0, 1.0, 0.75)
        b.data.materials.append(MAT[lmat])
        b.rotation_euler = (0, 0, rnd.uniform(0, 3.14))
        place(b, "Trees")

tree("Tree_GW1", -22.0, 6.0, h=5.5, r=2.7, seed=21)
tree("Tree_GW2", -25.0, 14.0, h=6.0, r=2.9, seed=22)
tree("Tree_GE1", 22.0, 6.0, h=5.8, r=2.8, seed=23, light=True)
tree("Tree_GE2", 25.0, 14.0, h=6.2, r=3.0, seed=24, light=True)
tree("Tree_TW", -13.5, 27.5, h=6.0, r=2.8, seed=25)
tree("Tree_TE", 13.5, 27.5, h=6.2, r=2.9, seed=26, light=True)
tree("Tree_TB1", -11.0, 44.0, h=6.5, r=3.0, seed=27)
tree("Tree_TB2", 11.0, 44.0, h=6.4, r=3.0, seed=28, light=True)
tree("Tree_Ave1", -8.5, -26.0, h=4.5, r=2.2, seed=29)
tree("Tree_Ave2", 8.5, -34.0, h=4.8, r=2.3, seed=30)
tree("Tree_Ave3", -8.5, -46.0, h=5.0, r=2.4, seed=31, light=True)
tree("Tree_Ave4", 8.5, -56.0, h=4.6, r=2.2, seed=32)

# --- material fallback: nothing ships untextured grey
for o in bpy.data.objects:
    if o.type != 'MESH' or (o.data.materials and any(o.data.materials)):
        continue
    o.data.materials.append(MAT["brick"] if o.name.startswith("Wall_") else MAT["wood"])

# ================================================================ 7. LIGHTING
world = bpy.data.worlds.new("Sky_World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.38, 0.57, 0.88, 1.0)
bg.inputs[1].default_value = 0.75

sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 6.0
sun.data.angle = radians(2.0)
sun.data.color = (1.0, 0.965, 0.90)
d = V((-0.40, 0.45, -0.74)).normalized()
sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
place(sun, "Lighting")

fill = bpy.data.objects.new("Fill_Sky", bpy.data.lights.new("Fill_Sky", 'AREA'))
fill.data.energy = 360
fill.data.size = 20
fill.data.color = (0.93, 0.95, 1.0)
fill.location = (-14, -18, 11)
fill.rotation_euler = Euler((radians(52), 0, radians(-28)))
place(fill, "Lighting")

# ================================================================ 8. CAMERAS
def camera(name, loc, look_at, lens=36):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.location = loc
    direction = V(look_at) - V(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 600
    place(cam, "Cameras")
    return cam

cam_a = camera("Camera_Hero", (-31.0, -47.0, 17.5), (0, -2.0, 5.0), 33)     # drone 3/4
cam_b = camera("Camera_Front", (0.0, -38.0, 6.5), (0, 2.0, 6.0), 35)        # straight-on gate
cam_c = camera("Camera_Temple", (-27.0, 27.0, 8.2), (2.0, DY - 4.0, 5.5), 36) # courtyard → đại điện 3/4
cam_d = camera("Camera_Avenue", (1.8, -30.0, 2.2), (0, 10.0, 4.0), 40)      # along the columns
cam_e = camera("Camera_DDFront", (0.0, DY - 30.0, 5.5), (0, DY, 7.5), 40)   # straight-on hall

# ================================================================ 8b. VISITORS (pilgrims + tourists)
if "Visitors" not in COL:
    COL["Visitors"] = bpy.data.collections.new("Visitors")
    scene.collection.children.link(COL["Visitors"])

visitor_specs = [
    # forecourt: pilgrim families walking to the gate
    (-3.0, -22.0, 15, 'family'), (2.6, -24.0, 170, 'couple'),
    (-1.5, -27.0, 175, 'adult'), (4.5, -19.5, 100, 'photographer'),
    (-5.5, -18.5, 30, 'couple'),
    # kids playing near the mounds
    (-12.0, -20.0, -25, 'kid'), (12.5, -18.0, 130, 'kid'), (11.0, -21.5, 60, 'kid'),
    # through the middle gate arch
    (0.3, -13.2, 5, 'adult'), (-0.4, -12.0, 4, 'couple'),
    # courtyard: worshippers heading to the đại điện + monks
    (-2.5, -5.0, 8, 'adult'), (2.8, -3.5, -10, 'photographer'),
    (-6.0, -7.0, 15, 'monk'), (-6.7, -4.6, 12, 'monk'), (-7.4, -2.2, 10, 'monk'),
    (1.6, -7.5, 178, 'family'),
    # along the avenue: strolling visitors between the columns
    (2.2, 3.0, 4, 'couple'), (-2.0, 9.0, -3, 'adult'), (2.4, 14.0, 6, 'family'),
    (-2.4, 20.0, -6, 'photographer'),
    # near the steles + urns in the courtyard
    (-8.5, -10.5, 55, 'photographer'), (9.0, -9.5, -40, 'adult'),
    (8.2, -12.5, -15, 'kid'),
]
add_visitors(bpy, V, box, cylinder, sphere, place, pbr, MAT, visitor_specs,
             col="Visitors", seed=202)

# ================================================================ 9. ANIMATION (flags)
scene.frame_start = 1
scene.frame_end = 96
for i, cloth in enumerate(flag_objs):
    ph = i * 1.2
    amp = 0.16 if i == 0 else 0.10
    for f, a in ((1, 0.0), (24, amp), (48, 0.0), (72, -amp), (96, 0.0)):
        cloth.rotation_euler.y = amp * 0.4 * sin(ph + f / 96 * 2 * pi)
        cloth.rotation_euler.z = a
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

for cam, tag in ((cam_a, "hero"), (cam_b, "front"), (cam_c, "temple"), (cam_d, "avenue"), (cam_e, "hall")):
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
