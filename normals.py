import bpy
import bl_operators
import bmesh
import mathutils as M
import math
import numpy as np


current_obj = bpy.context.active_object

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
    print(angle_between_normals(polygon_a.normal, polygon_b.normal))
