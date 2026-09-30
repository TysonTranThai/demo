# -*- coding: utf-8 -*-
"""
Export the pagoda .blend to a web-optimized GLB (v3 — correct rig).

- Drops Environment/Lighting/Cameras.
- Architecture meshes: de-parent (bake world transforms), join per material.
- Lanterns: re-rigged under two scene-root empties (Lantern_Swing_A/B) that
  carry the sway animation; all lantern parts in each group are joined into a
  single mesh parented to that group -> 2 extra draw calls, animation intact.
- Purges orphan data (old per-lantern actions, camera action).
- Writes export stats JSON next to the GLB.
"""

import bpy, os, json
from math import sin, pi, radians

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_IN = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "nlt-agent-model.blend"))
GLB_OUT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "exports", "nlt-agent-model.glb"))

bpy.ops.wm.open_mainfile(filepath=BLEND_IN)
scene = bpy.context.scene

# ---- 1. drop what the website does not need
for col_name in ("Environment", "Lighting", "Cameras"):
    col = bpy.data.collections.get(col_name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# ---- 2. classify objects
import re
lantern_re = re.compile(r"^Lantern_\d+(_(Cord|Body|CapT|CapB|Tassel))?$")
root_re = re.compile(r"^Lantern_(\d+)$")
lantern_parts = [o for o in scene.objects if o.type == 'MESH' and lantern_re.match(o.name)]
# Compound buildings are kept as separate joined meshes per material so each
# structure (gate, corridors, halls, walls, trees) stays individually addressable
# for future website toggling — still efficient for the GPU.
arch_meshes = [o for o in scene.objects if o.type == 'MESH' and not lantern_re.match(o.name)]

# CAPTURE world transforms BEFORE touching the hierarchy
root_world = {o.name: o.matrix_world.copy() for o in scene.objects
              if o.type == 'EMPTY' and root_re.match(o.name)}
part_world = {o.name: o.matrix_world.copy() for o in lantern_parts}

# remove old lantern root empties + old root container (they carry stale actions)
for o in list(scene.objects):
    if o.type == 'EMPTY' and (root_re.match(o.name) or o.name == "Lanterns_Root"):
        bpy.data.objects.remove(o, do_unlink=True)

# ---- 3. bake world transforms into architecture meshes, clear parents
bpy.context.view_layer.update()
for o in arch_meshes:
    if o.parent:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
for o in arch_meshes:
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ---- 4. swing rig: one pivot empty per lantern at its eave point, each with
# its own pendulum action (phase alternates). Correct pivot, clean glTF export.
scene.frame_start = 1
scene.frame_end = 192

pivots = {}
for name, mw in sorted(root_world.items()):
    idx = int(root_re.match(name).group(1))
    pivot = bpy.data.objects.new(f"Lantern_Pivot_{idx:02d}", None)
    scene.collection.objects.link(pivot)
    pivot.matrix_world = mw
    pivots[idx] = pivot

phase_sign = 1.0
def make_swing(empty, amp_sign):
    empty.rotation_mode = 'XYZ'
    amp_y, amp_x = 0.10 * amp_sign, 0.05 * amp_sign
    keys = {1: (0.0, 0.0), 96: (amp_y, amp_x), 192: (0.0, 0.0)}
    for f, (ry, rx) in keys.items():
        empty.rotation_euler = (rx, ry, 0.0)
        empty.keyframe_insert("rotation_euler", frame=f)
    for fc in empty.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'SINE'

def part_index(o):
    return int(re.match(r"^Lantern_(\d+)", o.name).group(1))

for o in lantern_parts:
    pivot = pivots[part_index(o)]
    o.parent = pivot
    o.matrix_parent_inverse = pivot.matrix_world.inverted()
    o.matrix_world = part_world[o.name]

for idx, pivot in sorted(pivots.items()):
    make_swing(pivot, phase_sign)
    phase_sign *= -1.0

# join each lantern's 4 parts into ONE mesh under its pivot
for idx, pivot in sorted(pivots.items()):
    members = [o for o in scene.objects if o.type == 'MESH' and o.parent == pivot]
    if len(members) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in members:
            o.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        bpy.context.view_layer.update()
        bpy.ops.object.join()

# ---- 5. join architecture per material (deselect between groups!)
by_mat = {}
for o in arch_meshes:
    key = o.data.materials[0].name if (o.data.materials and o.data.materials[0]) else "none"
    by_mat.setdefault(key, []).append(o)
for key, objs in by_mat.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.context.view_layer.update()
    if len(objs) > 1:
        bpy.ops.object.join()

# ---- 6. bake procedural (noise-ramp) materials to small textures so glTF can carry them
scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
scene.render.bake.use_pass_color = True
scene.render.bake.margin = 4

BAKE_SIZE = 1024
baked = []
for o in [o for o in scene.objects if o.type == 'MESH']:
    m = o.data.materials[0] if o.data.materials and o.data.materials[0] else None
    if not m or m.name in baked:
        continue
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    base_in = bsdf.inputs["Base Color"]
    rough_in = bsdf.inputs["Roughness"]
    if not base_in.is_linked:
        continue  # flat-color material; exports fine as-is
    # UVs (bmesh primitives ship without UV layers)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="UVMap")
    bpy.ops.uv.smart_project(angle_limit=radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- bake COLOR
    img_c = bpy.data.images.new("Bake_" + m.name + "_C", BAKE_SIZE, BAKE_SIZE)
    node_c = m.node_tree.nodes.new("ShaderNodeTexImage")
    node_c.image = img_c
    m.node_tree.nodes.active = node_c
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True,
                        use_selected_to_active=False, target='IMAGE_TEXTURES')
    img_c.pack()
    for l in list(base_in.links):
        m.node_tree.links.remove(l)
    m.node_tree.links.new(node_c.outputs["Color"], base_in)

    # --- bake ROUGHNESS (if the roughness input is driven)
    if rough_in.is_linked:
        img_r = bpy.data.images.new("Bake_" + m.name + "_R", BAKE_SIZE, BAKE_SIZE)
        node_r = m.node_tree.nodes.new("ShaderNodeTexImage")
        node_r.image = img_r
        m.node_tree.nodes.active = node_r
        bpy.ops.object.bake(type='ROUGHNESS', use_clear=True,
                            use_selected_to_active=False, target='IMAGE_TEXTURES')
        img_r.pack()
        for l in list(rough_in.links):
            m.node_tree.links.remove(l)
        m.node_tree.links.new(node_r.outputs["Color"], rough_in)

    baked.append(m.name)
    print("BAKED_MATERIAL:", m.name)

scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in \
    [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'

# ---- 7. purge orphan data (stale actions, meshes, materials)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# ---- 7. export
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in ('MESH', 'EMPTY'):
        o.select_set(True)
bpy.context.view_layer.objects.active = next(
    (o for o in scene.objects if o.type == 'MESH'), None)

os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=GLB_OUT,
    export_format='GLB',
    use_selection=True,
    export_apply=False,
    export_animations=True,
    export_anim_slide_to_zero=True,
    export_yup=True,
    export_materials='EXPORT',
    export_image_format='JPEG',
    export_jpeg_quality=85,
)
print("GLB_EXPORTED:", GLB_OUT, os.path.getsize(GLB_OUT), "bytes")

# ---- 8. stats (world-space triangle count)
bpy.context.view_layer.update()
import mathutils
tris, meshes = 0, 0
for o in scene.objects:
    if o.type == 'MESH':
        meshes += 1
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
stats = {
    "triangles": tris,
    "meshes_after_join": meshes,
    "draw_calls_approx": meshes,
    "animations": sorted(a.name for a in bpy.data.actions),
    "glb_bytes": os.path.getsize(GLB_OUT),
    "lantern_pivots": len(pivots),
}
with open(os.path.join(os.path.dirname(GLB_OUT), "export_stats.json"), "w") as f:
    json.dump(stats, f, indent=2)
print("EXPORT_STATS:", json.dumps(stats))
print("EXPORT_OK")
