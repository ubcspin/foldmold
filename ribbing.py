import bpy
import bmesh
import mathutils as M

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
        for i in range(1, self.num_slices+1):
            #top
            spot = (mesh.location.x - mesh.dimensions.x/2) + i*(mesh.dimensions.x)/(self.num_slices +1)
            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z + mesh.dimensions.z/2))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y, mesh.dimensions.z/2)
            bpy.context.active_object.name = "Slice-x-t"
            mainobj = bpy.context.active_object

            # bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z + mesh.dimensions.z*0.9))
            # bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y*0.8, mesh.dimensions.z*0.2/2)
            # bpy.context.active_object.name = "toptop"
            #
            # tops = [obj for obj in bpy.context.scene.objects if obj.name.startswith("toptop")]
            # bpy.context.view_layer.objects.active = mainobj
            # diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
            # diff.object = tops[0]
            # diff.operation = "UNION"
            # diff.double_threshold = 0
            # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            # bpy.ops.object.select_all(action='DESELECT')
            #
            # objs = bpy.data.objects
            # objs.remove(objs["toptop"], do_unlink=True)

            #bottom
            bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z -mesh.dimensions.z/2))
            bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y, mesh.dimensions.z/2)
            bpy.context.active_object.name = "Slice-x-b"
            mainobj = bpy.context.active_object

            # bpy.ops.mesh.primitive_cube_add(location=(spot, mesh.location.y, mesh.location.z -mesh.dimensions.z*0.9))
            # bpy.context.active_object.scale = (self.thickness/1000, mesh.dimensions.y*0.8, mesh.dimensions.z*0.2/2)
            # bpy.context.active_object.name = "bottombottom"
            #
            # bottoms = [obj for obj in bpy.context.scene.objects if obj.name.startswith("bottombottom")]
            # bpy.context.view_layer.objects.active = mainobj
            # diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
            # diff.object = bottoms[0]
            # diff.operation = "UNION"
            # diff.double_threshold = 0
            # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            # bpy.ops.object.select_all(action='DESELECT')
            #
            # objs = bpy.data.objects
            # objs.remove(objs["bottombottom"], do_unlink=True)


    def slice_y(self, mesh):
        if not mesh.name.startswith("Ribbed"):
            mesh.name = "Ribbed-"+mesh.name
        for i in range(1, self.num_slices+1):

            #left
            spot = (mesh.location.y - mesh.dimensions.y/2) + i*(mesh.dimensions.y)/(self.num_slices+1)
            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x+mesh.dimensions.x/2, spot, mesh.location.z))
            bpy.context.active_object.scale = (mesh.dimensions.x/2, self.thickness/1000, mesh.dimensions.z)
            bpy.context.active_object.name = "Slice-y"
            mainobj = bpy.context.active_object

            # bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x+mesh.dimensions.x*0.9, spot, mesh.location.z))
            # bpy.context.active_object.scale = ((mesh.dimensions.x*0.2)/2, self.thickness/1000, mesh.dimensions.z*0.8)
            # bpy.context.active_object.name = "leftleft"
            #
            # # lefts = [obj for obj in bpy.context.scene.objects if obj.name.startswith("leftleft")]
            # # bpy.context.view_layer.objects.active = mainobj
            # # diff = mainobj.modifiers.new(name="Boolean", type="BOOLEAN")
            # # diff.object = lefts[0]
            # # diff.operation = "UNION"
            # # diff.double_threshold = 0
            # # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            # # bpy.ops.object.select_all(action='DESELECT')
            # #
            # # objs = bpy.data.objects
            # # objs.remove(objs["leftleft"], do_unlink=True)
            #
            # lefts = [obj for obj in bpy.context.scene.objects if obj.name.startswith("leftleft")]
            # bpy.context.view_layer.objects.active = lefts[0]
            # diff = lefts[0].modifiers.new(name="Boolean", type="BOOLEAN")
            # diff.object = mainobj
            # diff.operation = "UNION"
            # diff.double_threshold = 0.2
            # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            # bpy.ops.object.select_all(action='DESELECT')
            #
            # objs = bpy.data.objects
            # objs.remove(mainobj, do_unlink=True)
            # lefts[0].name = "Slice-y"


            #right
            bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x-mesh.dimensions.x/2, spot, mesh.location.z))
            bpy.context.active_object.scale = (mesh.dimensions.x/2, self.thickness/1000, mesh.dimensions.z)
            bpy.context.active_object.name = "Slice-y"
            mainobj = bpy.context.active_object

            # bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x-mesh.dimensions.x*0.9, spot, mesh.location.z))
            # bpy.context.active_object.scale = ((mesh.dimensions.x*0.2)/2, self.thickness/1000, mesh.dimensions.z*0.8)
            # bpy.context.active_object.name = "rightright"
            #
            # rights = [obj for obj in bpy.context.scene.objects if obj.name.startswith("rightright")]
            # bpy.context.view_layer.objects.active = rights[0]
            # diff = rights[0].modifiers.new(name="Boolean", type="BOOLEAN")
            # diff.object = mainobj
            # diff.operation = "UNION"
            # diff.double_threshold = 0.2
            # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            # bpy.ops.object.select_all(action='DESELECT')
            #
            # objs = bpy.data.objects
            # objs.remove(mainobj, do_unlink=True)
            # rights[0].name = "Slice-y"


    def slice_z(self, mesh):
        if not mesh.name.startswith("Ribbed"):
            mesh.name = "Ribbed-"+mesh.name

        #top
        bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, mesh.location.y, mesh.dimensions.z*0.9))
        bpy.context.active_object.scale = (mesh.dimensions.x*1.2, mesh.dimensions.y*1.2, self.thickness/1000)
        bpy.context.active_object.name = "Slice-z-to"
        outside = bpy.context.active_object

        bpy.ops.mesh.primitive_cube_add(location=(mesh.location.x, mesh.location.y, mesh.dimensions.z*0.9))
        bpy.context.active_object.scale = (mesh.dimensions.x*0.65, mesh.dimensions.y*0.65, self.thickness/100)
        bpy.context.active_object.name = "Slice-z-ti"
        inside = bpy.context.active_object

        bpy.context.view_layer.objects.active = outside
        diff = outside.modifiers.new(name="Boolean", type="BOOLEAN")
        diff.object = inside
        diff.operation = "DIFFERENCE"
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
        bpy.ops.object.select_all(action='DESELECT')

        objs = bpy.data.objects
        objs.remove(inside, do_unlink=True)

        # bottom
        bpy.ops.mesh.primitive_cube_add(
            location=(mesh.location.x, mesh.location.y, mesh.location.z -mesh.dimensions.z*0.9))
        bpy.context.active_object.scale = (mesh.dimensions.x*1.2, mesh.dimensions.y*1.2, self.thickness / 1000)
        bpy.context.active_object.name = "Slice-z-bo"
        outside = bpy.context.active_object

        bpy.ops.mesh.primitive_cube_add(
            location=(mesh.location.x, mesh.location.y, mesh.location.z -mesh.dimensions.z*0.9))
        bpy.context.active_object.scale = (mesh.dimensions.x*0.65, mesh.dimensions.y*0.65, self.thickness / 100)
        bpy.context.active_object.name = "Slice-z-bi"
        inside = bpy.context.active_object

        bpy.context.view_layer.objects.active = outside
        diff = outside.modifiers.new(name="Boolean", type="BOOLEAN")
        diff.object = inside
        diff.operation = "DIFFERENCE"
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
        bpy.ops.object.select_all(action='DESELECT')

        objs = bpy.data.objects
        objs.remove(inside, do_unlink=True)
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
            if(slice.name.startswith("Slice-x") or slice.name.startswith("Slice-z")):
                bpy.context.view_layer.objects.active = slice
                diff = slice.modifiers.new(name="Boolean-c"+str(i), type="BOOLEAN")
                diff.object = not_slice[0]
                diff.operation = "DIFFERENCE"
                diff.double_threshold = 0
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean-c"+str(i))
            # print(slice.name, diff.object.name)
                if(slice.name.startswith("Slice-x")):
                    modifier = slice.modifiers.new(name="Remesh", type='REMESH')
                    # modifier.mode = "SHARP"
                    modifier.octree_depth = 5
                    modifier.use_remove_disconnected = True
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Remesh")


            bpy.context.view_layer.objects.active = slice
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.dissolve_limited()
            bpy.ops.object.mode_set(mode='OBJECT')

            # selectedEdges = [e for e in bpy.context.active_object.data.edges if e.select]
            # for edge in selectedEdges:
            #     edge.use_seam = True

            bpy.ops.object.mode_set(mode='EDIT')

            bm = bmesh.from_edit_mesh(slice.data)

            bpy.ops.mesh.remove_doubles()
            bpy.ops.mesh.select_all(action='DESELECT')

            def z_pos(vert):
                return vert.co.z
            def y_pos(vert):
                return vert.co.y

            #
            # if(slice.name.startswith("Slice-x")):
            #
            #     bpy.ops.mesh.remove_doubles()
            #     bpy.ops.mesh.select_non_manifold()
            #
            #     bpy.ops.object.mode_set(mode='OBJECT')
            #     selectedEdges = [e for e in bpy.context.active_object.data.edges if e.select]
            #     for edge in selectedEdges:
            #         edge.use_seam = False
            #
            #     i+=1
            #     bpy.ops.object.select_all(action='DESELECT')
            #
            #     bpy.ops.object.mode_set(mode='EDIT')
            #     bm = bmesh.from_edit_mesh(slice.data)
            #
            #     for vert in bm.verts:
            #         vert.co.x = round(vert.co.x)
            #     bmesh.update_edit_mesh(slice.data)
            #
            #
            #     front_vector = M.Vector((1, 0, 0))
            #     frontestfaces = []
            #     frontestverts = []
            #     # frontestuvface = None
            #     for face in bm.faces:
            #         # print(face.normal)
            #         if (face.normal.x == front_vector.x and abs(round(face.normal.y, 3)) == front_vector.y and abs(
            #                 round(face.normal.z, 3)) == front_vector.z):
            #             frontestfaces.append(face)
            #             # frontestuvface = uvface
            #             face.select = True
            #             for vert in face.verts:
            #                 frontestverts.append(vert)
            #
            #     bmesh.ops.delete(bm, geom=frontestfaces, context="FACES_ONLY")
            #
            #     bmesh.update_edit_mesh(slice.data)
            #     bpy.ops.object.mode_set(mode='OBJECT')
            #     bpy.ops.object.select_all(action='DESELECT')
            #
            #     bpy.ops.object.mode_set(mode='EDIT')
            #
            #     bm = bmesh.from_edit_mesh(slice.data)
            #     frontestverts = []
            #     for vert in bm.verts:
            #         if(vert.co.x == 1):
            #             frontestverts.append(vert)
            #             vert.select
            #
            #     useless_edges =[]
            #     for edge in bm.edges:
            #         if edge.select and not edge.seam:
            #             useless_edges.append(edge)
            #     # bmesh.ops.delete(bm, geom=useless_edges, context="EDGES")
            #     bmesh.update_edit_mesh(slice.data)
            #
            #     bpy.ops.object.mode_set(mode='OBJECT')
            #     bpy.ops.object.mode_set(mode='EDIT')
            #
            #     bm = bmesh.from_edit_mesh(slice.data)
            #
            #     face_verts = [edge for edge in bm.edges if edge.select]
            #
            #     bmesh.ops.contextual_create(bm, geom=face_verts)
            #     bmesh.update_edit_mesh(slice.data)
            #
            #     bpy.ops.object.mode_set(mode='OBJECT')
            #     bpy.ops.object.mode_set(mode='EDIT')
            #     bm = bmesh.from_edit_mesh(slice.data)
            #     back_verts = [edge for edge in bm.edges if edge.verts[0].co.x < 0 and edge.verts[1].co.x < 0 ]
            #     bmesh.ops.contextual_create(bm, geom=back_verts)

            # elif(slice.name.startswith("Slice-y")):
            #     useless_edges = []
            #     for edge in bm.edges:
            #         if(len(edge.link_faces) < 2):
            #             edge.select = True
            #             useless_edges.append(edge)
            #     # bmesh.ops.delete(bm, geom=useless_edges, context="EDGES")
            #     selectedVerts = []
            #     for vert in bm.verts:
            #         if(vert.select):
            #             selectedVerts.append(vert)
            #     selectedVerts.sort(key=z_pos)
            #     bmesh.ops.contextual_create(bm, geom=selectedVerts[:4])
            #     bmesh.ops.contextual_create(bm, geom=selectedVerts[4:])
            #
            #     bmesh.ops.contextual_create(bm, geom=bm.edges)
            #     bmesh.update_edit_mesh(slice.data)
            #
            #     for edge in bm.edges:
            #         edge.seam = True
            # elif(slice.name.startswith("Slice-z")):
            #
            #     bpy.context.view_layer.objects.active = slice
            #     bpy.ops.mesh.remove_doubles()
            #     #
            #     # bpy.ops.mesh.select_non_manifold()
            #     #
            #     # bpy.ops.object.mode_set(mode='OBJECT')
            #     # selectedEdges = [e for e in bpy.context.active_object.data.edges if e.select]
            #     # for edge in selectedEdges:
            #     #     edge.use_seam = False
            #
            #     # i+=1
            #     # bpy.ops.object.select_all(action='DESELECT')
            #     #
            #     # bpy.ops.object.mode_set(mode='EDIT')
            #     # bm = bmesh.from_edit_mesh(slice.data)
            #     #
            #     # for vert in bm.verts:
            #     #     vert.co.z = round(vert.co.z)
            #     # bmesh.update_edit_mesh(slice.data)
            #     #
            #     #
            #     # front_vector = M.Vector((0, 0, 1))
            #     # frontestfaces = []
            #     # frontestverts = []
            #     # frontestuvface = None
            #     # for face in bm.faces:
            #     #     # print(face.normal)
            #     #     if (abs(round(face.normal.x,3)) == front_vector.x and abs(round(face.normal.y, 3)) == front_vector.y and face.normal.z == front_vector.z):
            #     #         frontestfaces.append(face)
            #     #         # frontestuvface = uvface
            #     #         face.select = True
            #     #         for vert in face.verts:
            #     #             frontestverts.append(vert)
            #
            #     # bmesh.ops.delete(bm, geom=frontestfaces, context="FACES_ONLY")
            #
            #     # bmesh.update_edit_mesh(slice.data)
            #     # bpy.ops.object.mode_set(mode='OBJECT')
            #     # bpy.ops.object.select_all(action='DESELECT')
            #
            #     # bpy.ops.object.mode_set(mode='EDIT')
            #
            #     # bm = bmesh.from_edit_mesh(slice.data)
            #     # frontestverts = []
            #     # for vert in bm.verts:
            #     #     if(vert.co.z == 1):
            #     #         frontestverts.append(vert)
            #     #         vert.select
            #     #
            #     # useless_edges =[]
            #     # for edge in bm.edges:
            #     #     if edge.select and not edge.seam:
            #     #         useless_edges.append(edge)
            #     # bmesh.ops.delete(bm, geom=useless_edges, context="EDGES")
            #     # bmesh.update_edit_mesh(slice.data)
            #
            #     #
            #     # bpy.ops.object.mode_set(mode='OBJECT')
            #     # bpy.ops.object.mode_set(mode='EDIT')
            #     #
            #     # bm = bmesh.from_edit_mesh(slice.data)
            #     #
            #     # face_verts = [edge for edge in bm.edges if edge.select]
            #     #
            #     # bmesh.ops.contextual_create(bm, geom=face_verts)
            #
            #     # backestverts = []
            #     # for vert in bm.verts:
            #     #     if (vert.co.z < 0):
            #     #         backestverts.append(vert)
            #     #         vert.select
            #
            #     # useless_edges = []
            #     # for edge in bm.edges:
            #     #     if edge.select and not edge.seam:
            #     #         useless_edges.append(edge)
            #     # bmesh.ops.delete(bm, geom=useless_edges, context="EDGES")
            #     # face_verts = [edge for edge in bm.edges if edge.select and edge.is_valid]
            #     #
            #     # bmesh.ops.contextual_create(bm, geom=face_verts)
            #
            # # bmesh.update_edit_mesh(slice.data)
            #
            bpy.ops.object.mode_set(mode='OBJECT')


        #############RECALCULATE NORMALS
        for slice in slices:
            bpy.ops.object.select_all(action='DESELECT')
            # slice.select = True
            bpy.context.view_layer.objects.active = slice

            # go edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            # select al faces
            bpy.ops.mesh.select_all(action='SELECT')
            # recalculate outside normals
            bpy.ops.mesh.normals_make_consistent(inside=True)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.remove_doubles()
            # go object mode again
            bpy.ops.object.mode_set(mode='OBJECT')

            # if(slice.name.startswith("Slice-x")):
            #
            #     bpy.context.view_layer.objects.active = slice
            #
            #     # go edit mode
            #     bpy.ops.object.mode_set(mode='EDIT')
            #     bm = bmesh.from_edit_mesh(slice.data)
            #     bpy.ops.mesh.select_non_manifold()
            #     selectedVerts = []
            #     flat = []
            #     vertical = []
            #     for edge in bm.edges:
            #         if(edge.select):
            #             selectedVerts.append(edge)
            #             if(edge.verts[0].co.x == edge.verts[1].co.x and edge.verts[0].co.y == edge.verts[1].co.y):
            #                 if(edge.verts[0] not in vertical):
            #                     vertical.append(edge.verts[0])
            #                 if(edge.verts[1] not in vertical):
            #                     vertical.append(edge.verts[1])
            #             else:
            #                 if(edge.verts[0] not in flat):
            #                     flat.append(edge.verts[0])
            #                 if(edge.verts[1] not in flat):
            #                     flat.append(edge.verts[1])
            #
            #     flat.sort(key=y_pos)
            #     bmesh.ops.contextual_create(bm, geom=flat[:4])
            #     bmesh.ops.contextual_create(bm, geom=flat[4:])
            #
            #     vertical.sort(key=y_pos)
            #     bmesh.ops.contextual_create(bm, geom=vertical[:4])
            #     bmesh.ops.contextual_create(bm, geom=vertical[4:])

                # selectedVerts.sort(key=y_pos)
                # bmesh.ops.contextual_create(bm, geom=selectedVerts[:4])
                # # bmesh.ops.contextual_create(bm, geom=selectedVerts[2:4])
                # # bmesh.ops.contextual_create(bm, geom=selectedVerts[4:6])
                # bmesh.ops.contextual_create(bm, geom=selectedVerts[4:])
                #
                # bmesh.ops.contextual_create(bm, geom=bm.edges)
                # bmesh.update_edit_mesh(slice.data)
                #
                # for edge in bm.edges:
                #     edge.seam = True
                # bpy.ops.object.mode_set(mode='OBJECT')
        ######################SLOTS - Z


        mesh = not_slice[0]
        for slice in slices:

            if(slice.name.startswith("Slice-z-b")):
                bpy.context.view_layer.objects.active = slice
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles()
                bpy.ops.object.mode_set(mode='OBJECT')

                # yslices = [y for y in slices if y.name.startswith("Slice-y") if y.location.y > mesh.location.y]
                # for other in yslices:
                #     bpy.context.view_layer.objects.active = slice
                #     diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                #     diff.object = other
                #     diff.operation = "DIFFERENCE"
                #     # diff.double_threshold = 0
                #     bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                xslices = [x for x in slices if x.name.startswith("Slice-x-b")]
                for other in xslices:
                    bpy.context.view_layer.objects.active = slice
                    diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                    diff.object = other
                    diff.operation = "DIFFERENCE"
                    # diff.double_threshold = 0
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                yslices = [x for x in slices if x.name.startswith("Slice-y")]
                for other in yslices:
                    bpy.context.view_layer.objects.active = slice
                    diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                    diff.object = other
                    diff.operation = "DIFFERENCE"
                    # diff.double_threshold = 0
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

            elif(slice.name.startswith("Slice-z-t")):

                bpy.context.view_layer.objects.active = slice
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles()
                bpy.ops.object.mode_set(mode='OBJECT')
                #
                # yslices = [y for y in slices if y.name.startswith("Slice-y") if y.location.y > mesh.location.y]
                # for other in yslices:
                #     bpy.context.view_layer.objects.active = slice
                #     diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                #     diff.object = other
                #     diff.operation = "DIFFERENCE"
                #     # diff.double_threshold = 0
                #     bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")



                yslices = [x for x in slices if x.name.startswith("Slice-y")]
                for other in yslices:
                    bpy.context.view_layer.objects.active = slice
                    diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                    diff.object = other
                    diff.operation = "DIFFERENCE"
                    # diff.double_threshold = 0
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                xslices = [x for x in slices if x.name.startswith("Slice-x-t")]
                for other in xslices:
                    bpy.context.view_layer.objects.active = slice
                    diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                    diff.object = other
                    diff.operation = "DIFFERENCE"
                    # diff.double_threshold = 0
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

        ######################SLOTS - X

        for slice in slices:

            if(slice.name.startswith("Slice-x-t")):
                slice.location = (slice.location.x, slice.location.y, slice.location.z+slice.dimensions.z/1.5)

                slice_copy = slice.copy()
                slice_copy.name = "Copy"
                slice_copy.data = slice.data.copy()
                # new_obj.animation_data_clear()
                bpy.context.collection.objects.link(slice_copy)

                if(slice.location.x > mesh.location.x):
                    yslices = [y for y in slices if y.name.startswith("Slice-y") if y.location.x > mesh.location.x]
                    for other in yslices:
                        bpy.context.view_layer.objects.active = slice
                        diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                        diff.object = other
                        diff.operation = "DIFFERENCE"
                        # diff.double_threshold = 0
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                        #
                        # bpy.context.view_layer.objects.active = other
                        # diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                        # diff.object = slice_copy
                        # diff.operation = "DIFFERENCE"
                        # # diff.double_threshold = 0
                        # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
                else:
                    yslices = [y for y in slices if y.name.startswith("Slice-y") if y.location.x <= mesh.location.x]
                    for other in yslices:
                        bpy.context.view_layer.objects.active = slice
                        diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                        diff.object = other
                        diff.operation = "DIFFERENCE"
                        # diff.double_threshold = 0
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

                        # bpy.context.view_layer.objects.active = other
                        # diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                        # diff.object = slice_copy
                        # diff.operation = "DIFFERENCE"
                        # # diff.double_threshold = 0
                        # bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")


            if(slice.name.startswith("Slice-x-b")):
                    slice.location = (slice.location.x, slice.location.y, slice.location.z-slice.dimensions.z/1.5)

                    slice_copy= slice.copy()
                    slice_copy.name = "Copy"
                    slice_copy.data = slice.data.copy()
                    # new_obj.animation_data_clear()
                    bpy.context.collection.objects.link(slice_copy)

                    if(slice.location.x > mesh.location.x):
                        yslices = [y for y in slices if y.name.startswith("Slice-y") if y.location.x > mesh.location.x]
                        for other in yslices:
                            bpy.context.view_layer.objects.active = slice
                            diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                            diff.object = other
                            diff.operation = "DIFFERENCE"
                            # diff.double_threshold = 0
                            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
                    else:
                        yslices = [y for y in slices if y.name.startswith("Slice-y") if y.location.x <= mesh.location.x]
                        for other in yslices:
                            bpy.context.view_layer.objects.active = slice
                            diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                            diff.object = other
                            diff.operation = "DIFFERENCE"
                            # diff.double_threshold = 0
                            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")


        ############################SLOTS Y
        for slice in slices:

            if (slice.name.startswith("Slice-y")):
                bpy.context.view_layer.objects.active = slice
                diff = slice.modifiers.new(name="Boolean-c"+str(i), type="BOOLEAN")
                diff.object = not_slice[0]
                diff.operation = "DIFFERENCE"
                diff.double_threshold = 0
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean-c"+str(i))

                modifier = slice.modifiers.new(name="Remesh", type='REMESH')
                # modifier.mode = "SHARP"
                modifier.octree_depth = 5
                modifier.use_remove_disconnected = True
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Remesh")

                if (slice.location.x > mesh.location.x):
                    xslices = [x for x in bpy.context.scene.objects if x.name.startswith("Copy") if x.location.x > mesh.location.x]
                    for other in xslices:
                        bpy.context.view_layer.objects.active = slice
                        diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                        diff.object = other
                        diff.operation = "DIFFERENCE"
                        # diff.double_threshold = 0
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")


                else:
                    xslices = [x for x in bpy.context.scene.objects  if x.name.startswith("Copy") if x.location.x <= mesh.location.x]
                    for other in xslices:
                        bpy.context.view_layer.objects.active = slice
                        diff = slice.modifiers.new(name="Boolean", type="BOOLEAN")
                        diff.object = other
                        diff.operation = "DIFFERENCE"
                        # diff.double_threshold = 0
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")



                bpy.context.view_layer.objects.active = slice
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.dissolve_limited()
                bpy.ops.object.mode_set(mode='OBJECT')
        copies = [c for c in bpy.context.scene.objects if c.name.startswith("Copy")]
        for copy in copies:
            copy.select_set(True)
        bpy.ops.object.delete()


        for slice in slices:
            bpy.context.view_layer.objects.active = slice
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(slice.data)
            bpy.ops.mesh.remove_doubles()

            for edge in bm.edges:
                if edge.is_valid:
                    edge.seam = True
            bpy.ops.object.mode_set(mode='OBJECT')
            #     print(len(edge.link_faces))
            #     if (len(edge.link_faces) < 2):
            #         edge.seam = True
            #
            #     elif(len(edge.link_faces) > 2):
            #         edge.seam = False
            #     elif(edge.calc_face_angle() < 1):
            #             edge.seam = False
