# -*- coding: utf-8 -*-
"""
Shared VISITORS module for the Smart Art Heritage assets.
Import in a build script AFTER `place`/`box`/`cylinder`/`sphere` are defined and
after build_materials() has run, then call add_visitors(...) with a list of
(pos, rot_z, kind, variant) spawn specs.

Humans are stylised low-poly figures (~9 objects each, no rigging):
- adult: legs, torso (shirt), arms, head, hair, optional hat
- kid: same at 0.62 scale, brighter shirt colors
- monk: ochre robe (single tapered cylinder), shaven head, alms bowl
- photographer: adult + black camera held at face, elbow pose
- couple: two adults joined at hand height
Each is one joined-by-material family: skin/hair/shirt/pants/props materials
are registered into the host script's MAT dict under visitor_* keys.
"""
import random
from math import radians, sin, cos, pi

_SKIN = [(0.42, 0.27, 0.185), (0.50, 0.33, 0.225), (0.335, 0.215, 0.15), (0.55, 0.38, 0.265)]
_SHIRT = [(0.72, 0.20, 0.16), (0.16, 0.34, 0.62), (0.85, 0.66, 0.10), (0.14, 0.46, 0.30),
          (0.78, 0.78, 0.76), (0.52, 0.24, 0.58), (0.90, 0.44, 0.12), (0.20, 0.55, 0.72)]
_PANTS = [(0.16, 0.18, 0.24), (0.30, 0.28, 0.24), (0.42, 0.42, 0.45), (0.55, 0.50, 0.40)]
_HAIR = [(0.075, 0.055, 0.040), (0.16, 0.11, 0.07), (0.35, 0.26, 0.16), (0.55, 0.50, 0.44)]
_HAT = [(0.85, 0.72, 0.30), (0.75, 0.16, 0.12), (0.20, 0.35, 0.60)]


def _register_materials(bpy, pbr, MAT):
    """Create visitor materials in the host scene (idempotent).
    Note: host `pbr` may return an EXISTING material for shared colors, so the
    MAT dict entry must be the returned material, and duplicate colors map to
    the same datablock — fine for our use."""
    def m(key, color, rough):
        mat = pbr(key, color, rough=rough)
        MAT[key] = mat
    m("visitor_skin", _SKIN[0], 0.65)
    m("visitor_skin2", _SKIN[1], 0.65)
    m("visitor_hair", _HAIR[0], 0.85)
    m("visitor_hair2", _HAIR[2], 0.85)
    m("visitor_pants", _PANTS[0], 0.8)
    m("visitor_pants2", _PANTS[2], 0.8)
    m("visitor_shoe", (0.10, 0.10, 0.11), 0.75)
    m("visitor_shirt", _SHIRT[0], 0.78)
    m("visitor_shirt2", _SHIRT[1], 0.78)
    m("visitor_shirt3", _SHIRT[2], 0.78)
    m("visitor_shirt4", _SHIRT[3], 0.78)
    m("visitor_shirt5", _SHIRT[4], 0.78)
    m("visitor_shirt6", _SHIRT[5], 0.78)
    m("visitor_shirt7", _SHIRT[6], 0.78)
    m("visitor_shirt8", _SHIRT[7], 0.78)
    m("visitor_robe", (0.78, 0.48, 0.10), 0.8)          # monk ochre
    m("visitor_robe_sash", (0.62, 0.30, 0.08), 0.8)
    m("visitor_camera", (0.05, 0.05, 0.055), 0.4)
    m("visitor_bowl", (0.55, 0.42, 0.18), 0.5)
    m("visitor_balloon", (0.85, 0.15, 0.20), 0.5)
    m("visitor_hat", _HAT[0], 0.8)
    m("visitor_bag", (0.35, 0.20, 0.12), 0.75)


def _variant_mats(rnd):
    """Pick a coherent outfit variant: (shirt_key, pants_key, skin_key, hair_key)."""
    s = rnd.choice(["visitor_shirt"] + [f"visitor_shirt{i}" for i in range(2, 9)])
    p = rnd.choice(["visitor_pants", "visitor_pants", "visitor_pants2"])
    sk = rnd.choice(["visitor_skin", "visitor_skin", "visitor_skin2"])
    h = rnd.choice(["visitor_hair", "visitor_hair", "visitor_hair2"])
    return s, p, sk, h


def make_human(bpy, V, box, cylinder, sphere, place, MAT, name, x, y, z, rot=0.0,
               kind="adult", rnd=None, col="Visitors"):
    """Build one stylised human. Returns list of created objects."""
    rnd = rnd or random.Random(hash(name) & 0xffff)
    objs = []
    s, p, sk, h = _variant_mats(rnd)
    sc = 0.62 if kind == "kid" else rnd.uniform(0.94, 1.05)

    def add(o, mkey, dz=0.0):
        o.data.materials.append(MAT[mkey])
        place(o, col)
        objs.append(o)
        return o

    if kind == "monk":
        # robe: tapered cylinder, bare feet, bowl
        robe = cylinder(f"{name}_Robe", 0.26 * sc, 1.05 * sc, (x, y, z + 0.55 * sc), verts=10)
        add(robe, "visitor_robe")
        chest = sphere(f"{name}_Chest", 0.24 * sc, (x, y, z + 1.12 * sc), segs=9, rings=6)
        add(chest, "visitor_robe")
        sash = box(f"{name}_Sash", (0.10 * sc, 0.30 * sc, 0.55 * sc),
                   (x + 0.16 * sc, y, z + 0.95 * sc))
        add(sash, "visitor_robe_sash")
        head = sphere(f"{name}_Head", 0.15 * sc, (x, y, z + 1.42 * sc), segs=9, rings=6)
        add(head, sk)
        bowl = cylinder(f"{name}_Bowl", 0.11 * sc, 0.09 * sc,
                        (x + 0.30 * sc * cos(rot + pi / 2), y + 0.30 * sc * sin(rot + pi / 2),
                         z + 0.95 * sc), verts=9)
        add(bowl, "visitor_bowl")
        return objs

    # --- legs (two)
    leg_w = 0.09 * sc
    for sx in (-1, 1):
        lx = x + sx * 0.10 * sc * cos(rot + pi / 2)
        ly = y + sx * 0.10 * sc * sin(rot + pi / 2)
        leg = cylinder(f"{name}_Leg_{sx}", leg_w, 0.52 * sc, (lx, ly, z + 0.26 * sc), verts=7)
        add(leg, p)
        shoe = box(f"{name}_Shoe_{sx}", (0.11 * sc, 0.20 * sc, 0.07 * sc),
                   (lx, ly, z + 0.035 * sc), rot=(0, 0, rot))
        add(shoe, "visitor_shoe")
    # --- torso
    torso = box(f"{name}_Torso", (0.36 * sc, 0.20 * sc, 0.56 * sc), (x, y, z + 0.80 * sc),
                rot=(0, 0, rot))
    add(torso, s)
    # --- arms (down, or bent up holding camera)
    arm_up = (kind == "photographer")
    for sx in (-1, 1):
        ax = x + sx * 0.24 * sc * cos(rot + pi / 2)
        ay = y + sx * 0.24 * sc * sin(rot + pi / 2)
        if arm_up and sx == 1:
            arm = box(f"{name}_Arm_{sx}", (0.09 * sc, 0.09 * sc, 0.42 * sc),
                      (ax, ay, z + 1.18 * sc), rot=(radians(-70), 0, rot))
            add(arm, s)
        else:
            arm = cylinder(f"{name}_Arm_{sx}", 0.055 * sc, 0.46 * sc, (ax, ay, z + 0.80 * sc), verts=7)
            add(arm, s)
        hand = sphere(f"{name}_Hand_{sx}", 0.05 * sc,
                      (ax + (0.02 if not (arm_up and sx == 1) else 0.10) * sc * cos(rot),
                       ay + (0.02 if not (arm_up and sx == 1) else 0.10) * sc * sin(rot),
                       z + (0.56 if not (arm_up and sx == 1) else 1.34) * sc), segs=7, rings=5)
        add(hand, sk)
    # --- head + hair (+hat)
    head = sphere(f"{name}_Head", 0.14 * sc, (x, y, z + 1.30 * sc), segs=9, rings=6)
    add(head, sk)
    hair = sphere(f"{name}_Hair", 0.145 * sc, (x, y, z + 1.345 * sc), segs=9, rings=6)
    hair.scale = (1.0, 1.0, 0.62)
    add(hair, h)
    if kind == "photographer" or rnd.random() < 0.3:
        hat = cylinder(f"{name}_Hat", 0.20 * sc, 0.06 * sc, (x, y, z + 1.44 * sc), verts=10)
        add(hat, "visitor_hat")
        cap = cylinder(f"{name}_HatTop", 0.11 * sc, 0.10 * sc, (x, y, z + 1.50 * sc), verts=9)
        add(cap, "visitor_hat")
    # --- props
    if kind == "photographer":
        cam = box(f"{name}_Camera", (0.14 * sc, 0.08 * sc, 0.10 * sc),
                  (x + 0.20 * sc * cos(rot), y + 0.20 * sc * sin(rot), z + 1.38 * sc),
                  rot=(0, 0, rot))
        add(cam, "visitor_camera")
    if kind == "kid" and rnd.random() < 0.5:
        # balloon on a string — pure delight
        bal = sphere(f"{name}_Balloon", 0.14 * sc,
                     (x + 0.34 * sc * cos(rot + 0.6), y + 0.34 * sc * sin(rot + 0.6),
                      z + 2.15 * sc), segs=9, rings=6)
        add(bal, "visitor_balloon")
        string = cylinder(f"{name}_BalStr", 0.006 * sc, 0.8 * sc,
                          (x + 0.30 * sc * cos(rot + 0.6), y + 0.30 * sc * sin(rot + 0.6),
                           z + 1.75 * sc), verts=4)
        add(string, "visitor_pants")
    if rnd.random() < 0.35:
        bag = box(f"{name}_Bag", (0.16 * sc, 0.08 * sc, 0.22 * sc),
                  (x + 0.27 * sc * cos(rot + pi), y + 0.27 * sc * sin(rot + pi), z + 0.62 * sc),
                  rot=(0, 0, rot))
        add(bag, "visitor_bag")
    return objs


def add_visitors(bpy, V, box, cylinder, sphere, place, pbr, MAT, specs, col="Visitors",
                 register_col=None, seed=1234):
    """
    specs: list of (x, y, rot_deg, kind) — kind in
    adult | kid | monk | photographer | couple | family
    couple = 2 adults holding hands; family = 2 adults + 1-2 kids.
    Returns created objects.
    """
    _register_materials(bpy, pbr, MAT)
    if register_col:
        col = register_col
    rnd = random.Random(seed)
    made = []
    for i, (x, y, rotd, kind) in enumerate(specs):
        rot = radians(rotd)
        if kind == "couple":
            made += make_human(bpy, V, box, cylinder, sphere, place, MAT, f"Visitor_{i}a",
                               x - 0.22 * cos(rot + pi / 2), y - 0.22 * sin(rot + pi / 2),
                               0.0, rot, "adult", rnd, col)
            made += make_human(bpy, V, box, cylinder, sphere, place, MAT, f"Visitor_{i}b",
                               x + 0.22 * cos(rot + pi / 2), y + 0.22 * sin(rot + pi / 2),
                               0.0, rot, "adult", rnd, col)
            # joined hands: skip — arms already overlap visually at this scale
        elif kind == "family":
            made += make_human(bpy, V, box, cylinder, sphere, place, MAT, f"Visitor_{i}a",
                               x - 0.30 * cos(rot + pi / 2), y - 0.30 * sin(rot + pi / 2),
                               0.0, rot, "adult", rnd, col)
            made += make_human(bpy, V, box, cylinder, sphere, place, MAT, f"Visitor_{i}b",
                               x + 0.30 * cos(rot + pi / 2), y + 0.30 * sin(rot + pi / 2),
                               0.0, rot, "adult", rnd, col)
            nk = rnd.choice([1, 2])
            for j in range(nk):
                off = 0.55 + j * 0.5
                made += make_human(bpy, V, box, cylinder, sphere, place, MAT, f"Visitor_{i}k{j}",
                                   x + off * cos(rot), y + off * sin(rot), 0.0,
                                   rot + rnd.uniform(-0.5, 0.5), "kid", rnd, col)
        else:
            made += make_human(bpy, V, box, cylinder, sphere, place, MAT, f"Visitor_{i}",
                               x, y, 0.0, rot, kind, rnd, col)
    return made
