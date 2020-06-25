import bpy
import bmesh

class Ribbing:
    def __init__(self):
        self.num_slices = 0
        self.thickness = 0

    def settings(self, num_slices, thickness):
        self.num_slices = num_slices
        self.thickness = thickness

    def slice_x(self, mesh):
        for i in range(self.num_slices):
            spot = (mesh.location.x - mesh.dimensions.x/2) + i*(mesh.dimensions.x)/self.num_slices
            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y, mesh.dimensions.z)
