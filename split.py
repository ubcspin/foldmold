import bpy
import bl_operators
import bmesh
from math import ceil

obj = bpy.context.active_object

#colours
mat_zero = bpy.data.materials.new("mat_zero")
mat_zero.diffuse_color = (0, 0, 0, 1)
mat_one = bpy.data.materials.new("mat_one")
mat_one.diffuse_color = (1, 0, 0, 1)

obj.data.materials.append(mat_zero)
obj.data.materials.append(mat_one)

me = obj.data
bm = bmesh.new()
bm.from_mesh(me)


#mark seam so that kerfed part stays in one piece
for edge in bm.edges:
    linked = edge.link_faces
    if ((linked[0].smooth and not linked[1].smooth) or (not linked[0].smooth and linked[1].smooth)):
        edge.seam = True
        break

bpy.ops.object.mode_set(mode="EDIT")

#change colour, subdivide edges
for face in bm.faces:
    if (face.smooth):
        face.material_index = 1
        area = face.calc_area()
        print(area)
        bmesh.ops.subdivide_edges(bm, edges=face.edges, cuts=ceil(area))
        # UX?

bpy.ops.object.mode_set(mode="OBJECT")

bm.to_mesh(me)
print("done")