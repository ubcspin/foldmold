import bpy
import bl_operators
import bmesh
import math
from math import ceil
import numpy as np

obj = bpy.context.active_object

# colours
mat_zero = bpy.data.materials.new("mat_zero")
mat_zero.diffuse_color = (0, 0, 0, 1)
mat_one = bpy.data.materials.new("mat_one")
mat_one.diffuse_color = (1, 0, 0, 1)
mat_two = bpy.data.materials.new("mat_two")
mat_two.diffuse_color = (0, 1, 0, 1)
mat_three = bpy.data.materials.new("mat_three")
mat_three.diffuse_color = (0, 0, 1, 1)

obj.data.materials.append(mat_zero)
obj.data.materials.append(mat_one)
obj.data.materials.append(mat_two)
obj.data.materials.append(mat_three)

me = obj.data
bm = bmesh.new()
bm.from_mesh(me)


def angle_between_normals(a, b):
    dp = np.dot(a, b)
    if (dp > 1):
        dp = 1
    return math.degrees(math.acos(dp))


def remove_duplicates(duplicate):
    final_list = []
    for num in duplicate:
        if num not in final_list:
            final_list.append(num)
    return final_list


def remove_list(original, list):
    final_list = []
    for num in original:
        if num not in list and num not in final_list:
            final_list.append(num)
    return final_list


def clamp_list(list, decimals):
    new_list = []
    for val in list:
        new_list.append(round(val, decimals))
    return new_list


if hasattr(bm.verts, "ensure_lookup_table"):
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

# find seams and loops
sharpest = 180
seamedge = bm.edges[0]
kerfedges = []

f = bm.edges[0].link_faces
normal_a = f[0].normal
normal_b = f[1].normal

prev_axis = np.cross(normal_a, normal_b) / np.linalg.norm(np.cross(normal_a, normal_b))
prev_axis = clamp_list(prev_axis, 5)

for i in range(1, len(bm.edges)):
    faces = bm.edges[i].link_faces
    normal_a = faces[0].normal
    normal_b = faces[1].normal
    axis = np.cross(normal_a, normal_b) / np.linalg.norm(np.cross(normal_a, normal_b))
    axis = clamp_list(axis, 5)

    # two axes the same
    if (abs(axis[0]) == abs(prev_axis[0]) and abs(axis[1]) == abs(prev_axis[1])):
        faces[0].material_index = 2
        faces[1].material_index = 2
    elif (abs(axis[1]) == abs(prev_axis[1]) and abs(axis[2]) == abs(prev_axis[2])):
        faces[0].material_index = 2
        faces[1].material_index = 2
    elif (abs(axis[0]) == abs(prev_axis[0]) and abs(axis[2]) == abs(prev_axis[2])):
        faces[0].material_index = 2
        faces[1].material_index = 2
    else:
        print(axis, prev_axis)
        prev_axis = axis

    # find seams
    if (faces[0].material_index == 2 and faces[1].material_index == 2 and not faces[0].smooth and not faces[1].smooth):
        if (angle_between_normals(faces[0].normal, faces[1].normal) < sharpest):
            seamedge = bm.edges[i]
    elif ((faces[0].smooth and faces[1].smooth) or (faces[0].smooth and faces[1].material_index == 2) or (
            faces[0].material_index == 2 and faces[1].smooth)):
        kerfedges.extend([bm.edges[i]])

seamedge.seam = True

bpy.ops.object.mode_set(mode="EDIT")

# change colour, subdivide edges

kerfs = []
for face in bm.faces:
    if (face.smooth):
        face.material_index = 1
        area = face.calc_area()
        print(area)
        kerfs.extend(face.edges)
kerfs = remove_duplicates(kerfs)
kerfs = [edge for edge in kerfs if edge not in kerfedges]
bmesh.ops.subdivide_edges(bm, edges=kerfs, cuts=1, use_grid_fill=True)
# UX?

# detect loop


bpy.ops.object.mode_set(mode="OBJECT")

bm.to_mesh(me)
print("done")


