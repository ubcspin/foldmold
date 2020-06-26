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
        if not mesh.name.startswith("Ribbed"):
            mesh.name = "Ribbed-"+mesh.name
        for i in range(self.num_slices):
            spot = (mesh.location.x - mesh.dimensions.x/2) + i*(mesh.dimensions.x)/(self.num_slices )
            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y, mesh.dimensions.z)
            bpy.context.active_object.name = "Slice"

    def slice_y(self, mesh):
        if not mesh.name.startswith("Ribbed"):
            mesh.name = "Ribbed-"+mesh.name
        for i in range(self.num_slices):
            spot = (mesh.location.y - mesh.dimensions.y/2) + i*(mesh.dimensions.y)/(self.num_slices)
            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, spot, mesh.location.z))
            bpy.context.active_object.scale = (mesh.dimensions.x, self.thickness/1000, mesh.dimensions.z)
            bpy.context.active_object.name = "Slice"

    def slice_z(self, mesh):
        if not mesh.name.startswith("Ribbed"):
            mesh.name = "Ribbed-"+mesh.name
        for i in range(self.num_slices):
            spot = (mesh.location.z - mesh.dimensions.z/2) + i*(mesh.dimensions.z)/(self.num_slices)
            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, mesh.location.y, spot))
            bpy.context.active_object.scale = (mesh.dimensions.x, mesh.dimensions.y, self.thickness/1000)
            bpy.context.active_object.name = "Slice"

    def conform(self):
        slices = [obj for obj in bpy.context.scene.objects if obj.name.startswith("Slice")]
        not_slice = [obj for obj in bpy.context.scene.objects if obj.name.startswith("Ribbed")]

        # bpy.ops.object.editmode_toggle()
        # bpy.ops.mesh.select_all(action='SELECT')
        #
        # bpy.ops.mesh.flip_normals()
        # bpy.ops.object.editmode_toggle()
        # print(slices[0].name)
        # print(not_slice[0].name)
        i = 0
        for slice in slices:
            bpy.context.view_layer.objects.active = slice
            diff = slice.modifiers.new(name="Boolean"+str(i), type="BOOLEAN")
            diff.object = not_slice[0]
            diff.operation = "DIFFERENCE"
            diff.double_threshold = 0
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean"+str(i))
            # print(slice.name, diff.object.name)
            i+=1
            bpy.ops.object.select_all(action='DESELECT')
