import bpy
import bl_operators
import bmesh

obj = bpy.context.active_object

x, y, z = obj.dimensions
me = obj.data
bm = bmesh.new()
bm.from_mesh(me)

loc = obj.location
print(loc)

###########################Create left side x, scale it, subdivide it, get diff from positive
bpy.ops.mesh.primitive_cube_add(location=(loc.x - x * 0.5, loc.y, loc.z))
cube = bpy.context.selected_objects[0]
cube.name = "left-y"
arm = bpy.data.objects['left-y']

arm.scale = (x * 0.5, y * 1.5, z * 1.5)

bpy.data.objects['left-y'].select_set(True)
armme = bpy.context.active_object.data
armbm = bmesh.new()
armbm.from_mesh(armme)
print(armbm)
bmesh.ops.subdivide_edges(armbm,
                          edges=armbm.edges,
                          use_grid_fill=True,
                          cuts=1)
armbm.to_mesh(armme)

diff = arm.modifiers.new(name="Boolean", type="BOOLEAN")
diff.object = obj
diff.operation = "DIFFERENCE"
diff.double_threshold = 0
bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

##########################Now the same for right side x

bpy.ops.mesh.primitive_cube_add(location=(loc.x + x * 0.5, loc.y, loc.z))
cube = bpy.context.selected_objects[0]
cube.name = "right-y"
arm2 = bpy.data.objects['right-y']

arm2.scale = (x * 0.5, y * 1.5, z * 1.5)

bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['right-y'].select_set(True)

armme2 = bpy.context.active_object.data
armbm2 = bmesh.new()
armbm2.from_mesh(armme2)
print(armbm2)
bmesh.ops.subdivide_edges(armbm2,
                          edges=armbm2.edges,
                          use_grid_fill=True,
                          cuts=1)
armbm2.to_mesh(armme2)

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='SELECT')

bpy.ops.mesh.flip_normals()
bpy.ops.object.editmode_toggle()

diff = arm2.modifiers.new(name="Boolean2", type="BOOLEAN")
diff.object = obj
diff.operation = "DIFFERENCE"
diff.double_threshold = 0
bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean2")

###########################Create left side z, scale it, subdivide it, get diff from positive
bpy.ops.mesh.primitive_cube_add(location=(loc.x - x * 0.45, loc.y, loc.z))
cube = bpy.context.selected_objects[0]
cube.name = "left-z"
arm3 = bpy.data.objects['left-z']

arm3.scale = (x * 0.4, y * 1.5, z * 1.5)

bpy.data.objects['left-z'].select_set(True)
armme3 = bpy.context.active_object.data
armbm3 = bmesh.new()
armbm3.from_mesh(armme3)
print(armbm3)
bmesh.ops.subdivide_edges(armbm3,
                          edges=armbm3.edges,
                          use_grid_fill=True,
                          cuts=1)
armbm3.to_mesh(armme3)

diff = arm3.modifiers.new(name="Boolean3", type="BOOLEAN")
diff.object = obj
diff.operation = "DIFFERENCE"
diff.double_threshold = 0
bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean3")

##########################Now the same for right side z

bpy.ops.mesh.primitive_cube_add(location=(loc.x + x * 0.45, loc.y, loc.z))
cube = bpy.context.selected_objects[0]
cube.name = "right-z"
arm4 = bpy.data.objects['right-z']

arm4.scale = (x * 0.4, y * 1.5, z * 1.5)

bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['right-z'].select_set(True)

armme4 = bpy.context.active_object.data
armbm4 = bmesh.new()
armbm4.from_mesh(armme4)
print(armbm4)
bmesh.ops.subdivide_edges(armbm4,
                          edges=armbm4.edges,
                          use_grid_fill=True,
                          cuts=1)
armbm4.to_mesh(armme4)

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='SELECT')

bpy.ops.mesh.flip_normals()
bpy.ops.object.editmode_toggle()

diff = arm4.modifiers.new(name="Boolean4", type="BOOLEAN")
diff.object = obj
diff.operation = "DIFFERENCE"
diff.double_threshold = 0
bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean4")

bm.to_mesh(me)

