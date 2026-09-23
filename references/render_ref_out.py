import bpy, math, mathutils, sys
S = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f"{S}/scan.glb")
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
pivot = bpy.data.objects.new("pivot", None); bpy.context.scene.collection.objects.link(pivot)
pts = [o.matrix_world @ mathutils.Vector(c) for o in meshes for c in o.bound_box]
lo = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo+hi)/2; size = max(hi-lo)
for o in [o for o in bpy.context.scene.objects if o.parent is None and o is not pivot]:
    o.location -= center; o.parent = pivot
sc = bpy.context.scene
sc.render.resolution_x = sc.render.resolution_y = 480
sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, 96
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 16; sc.cycles.use_denoising = False
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1,1,1,1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = size*1.15
up_axis = 2  # glTF import is Z-up in Blender
cam.location = (0, -size*3, 0); cam.rotation_euler = (math.radians(90), 0, 0)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-40))
# hover turn: hold, ease 0->35deg, hold, ease back, hold
keys = [(1,0),(13,0),(61,35),(96,35)]
for f,deg in keys:
    pivot.rotation_euler = (0,0,math.radians(deg)); pivot.keyframe_insert("rotation_euler", frame=f)
for fc in pivot.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "AUTO"
sc.render.film_transparent = True; sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
sc.render.filepath = f"{S}/ref_out/f_"
bpy.ops.render.render(animation=True)
