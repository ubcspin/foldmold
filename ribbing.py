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
        mesh.name = "Ribbed-"+mesh.name
        for i in range(self.num_slices):
            spot = (mesh.location.x - mesh.dimensions.x/2) + i*(mesh.dimensions.x)/self.num_slices
            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y, mesh.dimensions.z)
            bpy.context.active_object.name = "Slice"

    def conform(self):
        slices = [obj for obj in bpy.context.scene.objects if obj.name.startswith("Slice")]
        not_slice = [obj for obj in bpy.context.scene.objects if obj.name.startswith("Ribbed")]

        # bpy.ops.object.editmode_toggle()
        # bpy.ops.mesh.select_all(action='SELECT')
        #
        # bpy.ops.mesh.flip_normals()
        # bpy.ops.object.editmode_toggle()
        print(slices[0].name)
        print(not_slice[0].name)

        for slice in slices:
            diff = slice.modifiers.new(name="Boolean1", type="BOOLEAN")
            diff.object = not_slice[0]
            diff.operation = "DIFFERENCE"
            diff.double_threshold = 0
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean1")
            print(slice.name, diff.object.name)
