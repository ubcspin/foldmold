import bpy
import bl_operators
import bmesh
import mathutils as M
import math
import numpy as np





#define colors
mat_zero = bpy.data.materials.new("mat_zero") #none
mat_zero.diffuse_color = (0, 0, 0, 1)
mat_one = bpy.data.materials.new("mat_one") #red means sharp x angle
mat_one.diffuse_color = (1, 0, 0, 1)
mat_two = bpy.data.materials.new("mat_two") #blue means sharp y angle
mat_two.diffuse_color = (0, 1, 0, 1)
mat_three = bpy.data.materials.new("mat_three") #green means sharp z angle
mat_three.diffuse_color = (0, 0, 1, 1)
mat_four = bpy.data.materials.new("mat_four") #orange means sharp x and y angle
mat_four.diffuse_color = (0.5, 0, 0.5, 1)
mat_five = bpy.data.materials.new("mat_five") #purple means sharp z and y angle
mat_five.diffuse_color = (0.5, 0.5, 0, 1)
mat_six = bpy.data.materials.new("mat_six") #yellow means sharp z and x angle
mat_six.diffuse_color = (0.4, 0.3, 0.2, 1)
mat_seven = bpy.data.materials.new("mat_seven") #white means all sharp
mat_seven.diffuse_color = (1, 1, 1, 1)


current_obj = bpy.context.active_object
# current_obj = bpy.context.edit_object
me = current_obj.data
me = current_obj.data
bm = bmesh.new()
bm.from_mesh(me)



current_obj.data.materials.append(mat_zero)
current_obj.data.materials.append(mat_one)
current_obj.data.materials.append(mat_two)
current_obj.data.materials.append(mat_three)
current_obj.data.materials.append(mat_four)
current_obj.data.materials.append(mat_five)
current_obj.data.materials.append(mat_six)
current_obj.data.materials.append(mat_seven)

print("==========================================")
def angle_between_normals(a, b):
        dp = np.dot(a, b)
        if(dp > 1):
            dp = 1
        return math.degrees(math.acos(dp))


def angle_between_normals_x(a, b):
    dp = np.dot(a[0], b[0])
    if (dp > 1):
        dp = 1
    return math.degrees(math.acos(dp))

def angle_between_normals_y(a, b):
    dp = np.dot(a[1], b[1])
    if (dp > 1):
        dp = 1
    return math.degrees(math.acos(dp))

def angle_between_normals_z(a, b):
    dp = np.dot(a[2], b[2])
    if (dp > 1):
        dp = 1
    return math.degrees(math.acos(dp))



i=0
for polygon_a in bm.faces:

    polygon_a_avg_x = 0
    polygon_a_avg_y = 0
    polygon_a_avg_z = 0

    polycount = 0
    for edge in polygon_a.edges:
        linked = edge.link_faces
        for polygon_b in linked:
            polycount+=1
            try:
                angle_x = angle_between_normals_x(polygon_a.normal, polygon_b.normal)
                angle_y = angle_between_normals_y(polygon_a.normal, polygon_b.normal)
                angle_z = angle_between_normals_z(polygon_a.normal, polygon_b.normal)

                polygon_a_avg_x += angle_x
                polygon_a_avg_y += angle_y
                polygon_a_avg_z += angle_z

            except ValueError:
                print("error")

    polygon_a_avg_x /= polycount
    polygon_a_avg_y /= polycount
    polygon_a_avg_z /= polycount


    sharp_x = (polygon_a_avg_x > 75)
    sharp_y = (polygon_a_avg_y > 75)
    sharp_z = (polygon_a_avg_z > 75)
    if (sharp_x):  # sharp x
        if (sharp_y and sharp_z):  # all sharp
            polygon_a.material_index = 7
            print ("all")
        elif (sharp_y):  # sharp x and y
            polygon_a.material_index = 4

            print ("x and y")
        elif (sharp_z):  # sharp x and z
            polygon_a.material_index = 6
            print ("x and z")
        else:
            polygon_a.material_index = 1
            print ("x")
    elif (sharp_y):  # sharp y
        if (sharp_z):  # sharp y and z
            polygon_a.material_index = 5
            print ("y and z")
        else:
            polygon_a.material_index = 2
            print ("y")
    elif (sharp_z):  # sharp z
        polygon_a.material_index = 3
        print ("z")
    else:
        polygon_a.material_index = 0
        print("none")
bm.to_mesh(me)