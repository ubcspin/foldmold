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
            #top
            spot = (mesh.location.x - mesh.dimensions.x/2) + i*(mesh.dimensions.x)/(self.num_slices )
            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z + mesh.dimensions.z*0.8/2))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y, mesh.dimensions.z*0.8/2)
            bpy.context.active_object.name = "Slice"
            mainobj = bpy.context.active_object

            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z + mesh.dimensions.z*0.9))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y*0.8, mesh.dimensions.z*0.2/2)
            bpy.context.active_object.name = "toptop"

            tops = [obj for obj in bpy.context.scene.objects if obj.name.startswith("toptop")]
            bpy.context.view_layer.objects.active = mainobj
            diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
            diff.object = tops[0]
            diff.operation = "UNION"
            diff.double_threshold = 0
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            bpy.ops.object.select_all(action='DESELECT')

            objs = bpy.data.objects
            objs.remove(objs["toptop"], do_unlink=True)

            #bottom
            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z -mesh.dimensions.z*0.8/2))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y, mesh.dimensions.z*0.8/2)
            bpy.context.active_object.name = "Slice"
            mainobj = bpy.context.active_object

            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z -mesh.dimensions.z*0.9))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y*0.8, mesh.dimensions.z*0.2/2)
            bpy.context.active_object.name = "bottombottom"

            bottoms = [obj for obj in bpy.context.scene.objects if obj.name.startswith("bottombottom")]
            bpy.context.view_layer.objects.active = mainobj
            diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
            diff.object = bottoms[0]
            diff.operation = "UNION"
            diff.double_threshold = 0
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            bpy.ops.object.select_all(action='DESELECT')

            objs = bpy.data.objects
            objs.remove(objs["bottombottom"], do_unlink=True)


    def slice_y(self, mesh):
        if not mesh.name.startswith("Ribbed"):
            mesh.name = "Ribbed-"+mesh.name
        for i in range(self.num_slices):

            #left
            spot = (mesh.location.y - mesh.dimensions.y/2) + i*(mesh.dimensions.y)/(self.num_slices)
            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x+mesh.dimensions.x*0.8/2, spot, mesh.location.z))
            bpy.context.active_object.scale = (mesh.dimensions.x*0.8/2, self.thickness/1000, mesh.dimensions.z)
            bpy.context.active_object.name = "Slice"
            mainobj = bpy.context.active_object

            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x+mesh.dimensions.x*0.9, spot, mesh.location.z))
            bpy.context.active_object.scale = ((mesh.dimensions.x*0.2)/2, self.thickness/1000, mesh.dimensions.z*0.8)
            bpy.context.active_object.name = "leftleft"

            # lefts = [obj for obj in bpy.context.scene.objects if obj.name.startswith("leftleft")]
            # bpy.context.view_layer.objects.active = mainobj
            # diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
            # diff.object = lefts[0]
            # diff.operation = "UNION"
            # diff.double_threshold = 0
            # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            # bpy.ops.object.select_all(action='DESELECT')
            #
            # objs = bpy.data.objects
            # objs.remove(objs["leftleft"], do_unlink=True)

            lefts = [obj for obj in bpy.context.scene.objects if obj.name.startswith("leftleft")]
            bpy.context.view_layer.objects.active = lefts[0]
            diff = lefts[0].modifiers.new(name="Boolean", type="BOOLEAN")
            diff.object = mainobj
            diff.operation = "UNION"
            diff.double_threshold = 0.2
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            bpy.ops.object.select_all(action='DESELECT')

            objs = bpy.data.objects
            objs.remove(mainobj, do_unlink=True)
            lefts[0].name = "Slice"


            #right
            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x-mesh.dimensions.x*0.8/2, spot, mesh.location.z))
            bpy.context.active_object.scale = (mesh.dimensions.x*0.8/2, self.thickness/1000, mesh.dimensions.z)
            bpy.context.active_object.name = "Slice"
            mainobj = bpy.context.active_object

            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x-mesh.dimensions.x*0.9, spot, mesh.location.z))
            bpy.context.active_object.scale = ((mesh.dimensions.x*0.2)/2, self.thickness/1000, mesh.dimensions.z*0.8)
            bpy.context.active_object.name = "rightright"

            rights = [obj for obj in bpy.context.scene.objects if obj.name.startswith("rightright")]
            bpy.context.view_layer.objects.active = rights[0]
            diff = rights[0].modifiers.new(name="Boolean", type="BOOLEAN")
            diff.object = mainobj
            diff.operation = "UNION"
            diff.double_threshold = 0.2
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            bpy.ops.object.select_all(action='DESELECT')

            objs = bpy.data.objects
            objs.remove(mainobj, do_unlink=True)
            rights[0].name = "Slice"


    def slice_z(self, mesh):
        if not mesh.name.startswith("Ribbed"):
            mesh.name = "Ribbed-"+mesh.name

        #top left
        bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, mesh.location.y+mesh.dimensions.y*0.8/2, mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x, mesh.dimensions.y*0.8/2, self.thickness/1000)
        bpy.context.active_object.name = "Slice"
        mainobj = bpy.context.active_object

        bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, mesh.location.y+mesh.dimensions.y*0.9, mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x*0.8, mesh.dimensions.y*0.2/2, self.thickness/1000)
        bpy.context.active_object.name = "leftleft"

        lefts = [obj for obj in bpy.context.scene.objects if obj.name.startswith("leftleft")]
        bpy.context.view_layer.objects.active = mainobj
        diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
        diff.object = lefts[0]
        diff.operation = "UNION"
        diff.double_threshold = 0
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
        bpy.ops.object.select_all(action='DESELECT')

        objs = bpy.data.objects
        objs.remove(objs["leftleft"], do_unlink=True)

        #top right
        bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, mesh.location.y-mesh.dimensions.y*0.8/2, mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x, mesh.dimensions.y*0.8/2, self.thickness/1000)
        bpy.context.active_object.name = "Slice"
        mainobj = bpy.context.active_object

        bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, mesh.location.y-mesh.dimensions.y*0.9, mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x*0.8, mesh.dimensions.y*0.2/2, self.thickness/1000)
        bpy.context.active_object.name = "rightright"

        rights = [obj for obj in bpy.context.scene.objects if obj.name.startswith("rightright")]
        bpy.context.view_layer.objects.active = rights[0]
        diff = rights[0].modifiers.new(name="Boolean", type="BOOLEAN")
        diff.object = mainobj
        diff.operation = "UNION"
        diff.double_threshold = 0
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
        bpy.ops.object.select_all(action='DESELECT')

        objs = bpy.data.objects
        objs.remove(mainobj, do_unlink=True)
        rights[0].name = "Slice"

        # bottom left
        bpy.ops.mesh.primitive_cube_add(
            location=(mesh.location.x, mesh.location.y + mesh.dimensions.y * 0.8 / 2, mesh.location.z -mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x, mesh.dimensions.y * 0.8 / 2, self.thickness / 1000)
        bpy.context.active_object.name = "Slice"
        mainobj = bpy.context.active_object

        bpy.ops.mesh.primitive_cube_add(
            location=(mesh.location.x, mesh.location.y + mesh.dimensions.y * 0.9, mesh.location.z -mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x * 0.8, mesh.dimensions.y * 0.2 / 2, self.thickness / 1000)
        bpy.context.active_object.name = "leftleft"

        lefts = [obj for obj in bpy.context.scene.objects if obj.name.startswith("leftleft")]
        bpy.context.view_layer.objects.active = mainobj
        diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
        diff.object = lefts[0]
        diff.operation = "UNION"
        diff.double_threshold = 0
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
        bpy.ops.object.select_all(action='DESELECT')

        objs = bpy.data.objects
        objs.remove(objs["leftleft"], do_unlink=True)

        # bottom right
        bpy.ops.mesh.primitive_cube_add(
            location=(mesh.location.x, mesh.location.y - mesh.dimensions.y * 0.8 / 2, mesh.location.z -mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x, mesh.dimensions.y * 0.8 / 2, self.thickness / 1000)
        bpy.context.active_object.name = "Slice"
        mainobj = bpy.context.active_object

        bpy.ops.mesh.primitive_cube_add(
            location=(mesh.location.x, mesh.location.y - mesh.dimensions.y * 0.9, mesh.location.z -mesh.dimensions.z*0.8))
        bpy.context.active_object.scale = (mesh.dimensions.x * 0.8, mesh.dimensions.y * 0.2 / 2, self.thickness / 1000)
        bpy.context.active_object.name = "rightright"

        rights = [obj for obj in bpy.context.scene.objects if obj.name.startswith("rightright")]
        bpy.context.view_layer.objects.active = rights[0]
        diff = rights[0].modifiers.new(name="Boolean", type="BOOLEAN")
        diff.object = mainobj
        diff.operation = "UNION"
        diff.double_threshold = 0
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
        bpy.ops.object.select_all(action='DESELECT')

        objs = bpy.data.objects
        objs.remove(mainobj, do_unlink=True)
        rights[0].name = "Slice"

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
            diff = slice.modifiers.new(name="Boolean-c"+str(i), type="BOOLEAN")
            diff.object = not_slice[0]
            diff.operation = "DIFFERENCE"
            diff.double_threshold = 0
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean-c"+str(i))
            # print(slice.name, diff.object.name)


            selectedEdges = [e for e in bpy.context.active_object.data.edges if e.select]
            for edge in selectedEdges:
                edge.use_seam = True

            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.remove_doubles()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.object.mode_set(mode='OBJECT')
            selectedEdges = [e for e in bpy.context.active_object.data.edges if e.select]
            for edge in selectedEdges:
                edge.use_seam = False




            i+=1
            bpy.ops.object.select_all(action='DESELECT')
