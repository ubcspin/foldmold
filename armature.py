import bpy
import bl_operators
import bmesh

obj = bpy.context.active_object

me = obj.data
bm = bmesh.new()
bm.from_mesh(me)

loc = obj.location
print(loc)
bpy.ops.mesh.primitive_cube_add(location=loc)
arm = bpy.data.objects['Cube']

diff = arm.modifiers.new(name="Boolean", type="BOOLEAN")
diff.object = obj
diff.operation = "DIFFERENCE"
bpy.ops.object.modifier_apply(apply_as='DATA',modifier=arm.modifiers[0].name)



bm.to_mesh(me)