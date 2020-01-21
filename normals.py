import bpy
import bl_operators
import bmesh
import mathutils as M
import math
import numpy as np



#define colors
mat_one = bpy.data.materials.new("mat_one") #red means sharp angle
mat_one.diffuse_color = (1, 0, 0, 1)
mat_two = bpy.data.materials.new("mat_two") #green means non-sharp angle
mat_two.diffuse_color = (0, 1, 0, 1)


current_obj = bpy.context.active_object
current_obj.data.materials.append(mat_one)
current_obj.data.materials.append(mat_two)

print("==========================================")
def angle_between_normals(a, b):
    dp = np.dot(a, b)
    return math.degrees(math.acos(dp))

i=0
while i in range(0, len(current_obj.data.polygons)):
    polygon_a = current_obj.data.polygons[i]
    i+=1
    polygon_b = current_obj.data.polygons[i]
    i+=1

    angle = angle_between_normals(polygon_a.normal, polygon_b.normal)
    print(angle)

    if(angle < 90 or angle > 270 ):
        polygon_a.material_index = 0
        polygon_b.material_index = 0
    else:
        polygon_a.material_index = 1
        polygon_b.material_index = 1
