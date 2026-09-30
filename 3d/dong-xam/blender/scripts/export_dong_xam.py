# -*- coding: utf-8 -*-
"""
Export Khu lưu niệm Đồng Xâm .blend to a web-optimized GLB.
Same pipeline as the other heritage assets.
"""

import bpy, os, json, re, math
from math import sin, pi, radians

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_IN = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "dong-xam-model.blend"))
GLB_OUT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "exports", "dong-xam-model.glb"))

bpy.ops.wm.open_mainfile(filepath=BLEND_IN)
scene = bpy.context.scene

# ---- 1. drop what the website does not need
for col_name in ("Environment", "Lighting", "Cameras"):
    col = bpy.data.collections.get(col_name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# ---- 2. classify
flag_re = re.compile(r"^(Lantern_|Flag_Cloth)")
flag_cloths = [o for o in scene.objects if o.type == 'MESH' and flag_re.match(o.name)]
arch_meshes = [o for o in scene.objects if o.type == 'MESH' and not flag_re.match(o.name)]
cloth_world = {o.name: o.matrix_world.copy() for o in flag_cloths}

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

# ---- 4. lantern rig: pivot per cloth + sway action
scene.frame_start = 1
scene.frame_end = 96
for i, cloth in enumerate(sorted(flag_cloths, key=lambda o: o.name)):
    mw = cloth_world[cloth.name]
    pivot = bpy.data.objects.new(f"Lantern_Pivot_{i:02d}", None)
    scene.collection.objects.link(pivot)
    pivot.matrix_world = mw
    cloth.parent = pivot
    cloth.matrix_parent_inverse = mw.inverted()
    cloth.matrix_world = mw
    if cloth.animation_data:
        cloth.animation_data_clear()

    pivot.rotation_mode = 'XYZ'
    ph = i * 1.1
    amp = 0.10
    keys = {1: 0.0, 24: amp, 48: 0.0, 72: -amp, 96: 0.0}
    for f, a in keys.items():
        pivot.rotation_euler.y = amp * 0.45 * sin(ph + f / 96 * 2 * pi)
        pivot.rotation_euler.z = a
        pivot.keyframe_insert("rotation_euler", frame=f)
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'SINE'

# ---- 5. join architecture per material
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

# ---- 6. bake procedural materials to textures
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
        continue
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="UVMap")
    bpy.ops.uv.smart_project(angle_limit=radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

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

engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'

# ---- 7. purge orphans + export
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
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
    export_apply=True,
    export_animations=True,
    export_skins=False,
    export_materials='EXPORT',
    export_yup=True)
print("GLB_EXPORTED:", GLB_OUT, os.path.getsize(GLB_OUT), "bytes")

meshes = [o for o in scene.objects if o.type == 'MESH']
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
pivots = [o for o in scene.objects if o.name.startswith("Lantern_Pivot")]
stats = {
    "triangles": tris,
    "meshes_after_join": len(meshes),
    "draw_calls_approx": len(meshes),
    "animations": [a.name for a in bpy.data.actions],
    "lantern_pivots": len(pivots),
    "glb_bytes": os.path.getsize(GLB_OUT),
}
with open(os.path.join(os.path.dirname(GLB_OUT), "export_stats.json"), "w") as f:
    json.dump(stats, f, indent=2)
print("EXPORT_STATS:", json.dumps(stats))
