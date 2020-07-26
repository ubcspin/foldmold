import mathutils as M
import bpy
if __package__ is None or __package__ == '':
    # uses current directory visibility
    import stickers
    import unfold
    import utilities
else:
    # uses current package visibility
    from . import stickers
    from . import unfold
    from . import utilities


from itertools import chain, repeat, product, combinations
u = utilities.Utilities()

class Mesh:
    """Wrapper for Bpy Mesh"""

    def __init__(self, bmesh, matrix, stobj):
        self.data = bmesh
        self.matrix = matrix.to_3x3()
        self.looptex = bmesh.loops.layers.uv.new("Unfolded")
        self.edges = {bmedge: stickers.Edge(bmedge) for bmedge in bmesh.edges}
        self.islands = list()
        self.pages = list()
        self.s = stobj
        for edge in self.edges.values():
            edge.choose_main_faces()
            if edge.main_faces:
                edge.calculate_angle()
        self.copy_freestyle_marks()
        self.thickness_switch = 0

    def setThicknessSwitch(self, thickness_switch):
        # print("thickness_switch set to:", thickness_switch)
        self.thickness_switch = thickness_switch

    def delete_uvmap(self):
        self.data.loops.layers.uv.remove(self.looptex) if self.looptex else None

    def copy_freestyle_marks(self):
        # NOTE: this is a workaround for NotImplementedError on bmesh.edges.layers.freestyle
        mesh = bpy.data.meshes.new("unfolder_temp")
        self.data.to_mesh(mesh)
        for bmedge, edge in self.edges.items():
            edge.freestyle = mesh.edges[bmedge.index].use_freestyle_mark
        bpy.data.meshes.remove(mesh)

    def mark_cuts(self):
        for bmedge, edge in self.edges.items():
            if edge.is_main_cut and not bmedge.is_boundary:
                bmedge.seam = True

    def check_correct(self, epsilon=1e-6):
        """Check for invalid geometry"""

        def is_twisted(face):
            if len(face.verts) <= 3:
                return False
            center = face.calc_center_median()
            plane_d = center.dot(face.normal)
            diameter = max((center - vertex.co).length for vertex in face.verts)
            threshold = 0.01 * diameter
            return any(abs(v.co.dot(face.normal) - plane_d) > threshold for v in face.verts)

        null_edges = {e for e in self.edges.keys() if e.calc_length() < epsilon and e.link_faces}
        null_faces = {f for f in self.data.faces if f.calc_area() < epsilon}
        twisted_faces = {f for f in self.data.faces if is_twisted(f)}
        inverted_scale = self.matrix.determinant() <= 0
        if not (null_edges or null_faces or twisted_faces or inverted_scale):
            return True
        if inverted_scale:
            raise unfold.UnfoldError("The object is flipped inside-out.\n"
                              "You can use Object -> Apply -> Scale to fix it. Export failed.")
        disease = [("Remove Doubles", null_edges or null_faces), ("Triangulate", twisted_faces)]
        cure = " and ".join(s for s, k in disease if k)
        raise unfold.UnfoldError(
            "The model contains:\n" +
            (" {} zero-length edge(s)\n".format(len(null_edges)) if null_edges else "") +
            (" {} zero-area face(s)\n".format(len(null_faces)) if null_faces else "") +
            (" {} twisted polygon(s)\n".format(len(twisted_faces)) if twisted_faces else "") +
            "The offenders are selected and you can use {} to fix them. Export failed.".format(cure),
            {"verts": set(), "edges": null_edges, "faces": null_faces | twisted_faces}, self.data)


    def add_hole(self, uvface):

        uvedge = uvface.uvedges[1]

        uvedge.pourhole = stickers.PourHole(uvedge)
        uvedge.uvface.island.add_marker(uvedge.pourhole)

    def generate_cuts(self, page_size, priority_effect):
        """Cut the mesh so that it can be unfolded to a flat net."""
        normal_matrix = self.matrix.inverted().transposed()
        islands = {stickers.Island(self, face, self.matrix, normal_matrix, self.s) for face in self.data.faces}
        uvfaces = {face: uvface for island in islands for face, uvface in island.faces.items()}
        uvedges = {loop: uvedge for island in islands for loop, uvedge in island.edges.items()}
        for loop, uvedge in uvedges.items():
            self.edges[loop.edge].uvedges.append(uvedge)
        # check for edges that are cut permanently
        edges = [edge for edge in self.edges.values() if not edge.force_cut and edge.main_faces]

        if edges:
            average_length = sum(edge.vector.length for edge in edges) / len(edges)
            for edge in edges:
                edge.generate_priority(priority_effect, average_length)
            edges.sort(reverse=False, key=lambda edge: edge.priority)
            # print([edge.is_kerf for edge in edges])
            for edge in edges:
                if not edge.vector:
                    continue
                edge_a, edge_b = (uvedges[l] for l in edge.main_faces)
                old_island = join(edge_a, edge_b, size_limit=page_size)
                if old_island:
                    islands.remove(old_island)

        self.islands = sorted(islands, reverse=True, key=lambda island: len(island.faces))



        for edge in self.edges.values():
            # some edges did not know until now whether their angle is convex or concave
            if edge.main_faces and (
                    uvfaces[edge.main_faces[0].face].flipped or uvfaces[edge.main_faces[1].face].flipped):
                edge.calculate_angle()
            # ensure that the order of faces corresponds to the order of uvedges
            if edge.main_faces:
                reordered = [None, None]
                for uvedge in edge.uvedges:
                    try:
                        index = edge.main_faces.index(uvedge.loop)
                        reordered[index] = uvedge
                    except ValueError:
                        reordered.append(uvedge)
                edge.uvedges = reordered

        for island in self.islands:
            # if the normals are ambiguous, flip them so that there are more convex edges than concave ones
            if any(uvface.flipped for uvface in island.faces.values()):
                island_edges = {self.edges[uvedge.edge] for uvedge in island.edges}
                balance = sum(
                    (+1 if edge.angle > 0 else -1) for edge in island_edges if not edge.is_cut(uvedge.uvface.face))
                if balance < 0:
                    island.is_inside_out = True

            # construct a linked list from each island's boundary
            # uvedge.neighbor_right is clockwise = forward = via uvedge.vb if not uvface.flipped
            neighbor_lookup, conflicts = dict(), dict()
            for uvedge in island.boundary:
                uvvertex = uvedge.va if uvedge.uvface.flipped else uvedge.vb
                if uvvertex not in neighbor_lookup:
                    neighbor_lookup[uvvertex] = uvedge
                else:
                    if uvvertex not in conflicts:
                        conflicts[uvvertex] = [neighbor_lookup[uvvertex], uvedge]
                    else:
                        conflicts[uvvertex].append(uvedge)

            for uvedge in island.boundary:
                uvvertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                if uvvertex not in conflicts:
                    # using the 'get' method so as to handle single-connected vertices properly
                    uvedge.neighbor_right = neighbor_lookup.get(uvvertex, uvedge)
                    uvedge.neighbor_right.neighbor_left = uvedge
                else:
                    conflicts[uvvertex].append(uvedge)

            # resolve merged vertices with more boundaries crossing
            def direction_to_float(vector):
                return (1 - vector.x / vector.length) if vector.y > 0 else (vector.x / vector.length - 1)

            for uvvertex, uvedges in conflicts.items():
                def is_inwards(uvedge):
                    return uvedge.uvface.flipped == (uvedge.va is uvvertex)

                def uvedge_sortkey(uvedge):
                    if is_inwards(uvedge):
                        return direction_to_float(uvedge.va.co - uvedge.vb.co)
                    else:
                        return direction_to_float(uvedge.vb.co - uvedge.va.co)

                uvedges.sort(key=uvedge_sortkey)
                for right, left in (
                        zip(uvedges[:-1:2], uvedges[1::2]) if is_inwards(uvedges[0])
                        else zip([uvedges[-1]] + uvedges[1::2], uvedges[:-1:2])):
                    left.neighbor_right = right
                    right.neighbor_left = left

        return True



    def generate_cuts_ribs(self, page_size, priority_effect):
        """Cut the mesh so that it can be unfolded to a flat net."""
        normal_matrix = self.matrix.inverted().transposed()
        initial_islands = {stickers.Island(self, face, self.matrix, normal_matrix, self.s) for face in self.data.faces}
        initial_uvfaces = {face: uvface for island in initial_islands for face, uvface in island.faces.items()}
        # uvedges = {loop: uvedge for island in islands for loop, uvedge in island.edges.items()}
        # for loop, uvedge in uvedges.items():
        #     self.edges[loop.edge].uvedges.append(uvedge)



        front_vector = M.Vector((1, 0, 0))
        frontestfaces = []
        # frontestuvface = None
        for face, uvface in initial_uvfaces.items():
            # print(face.normal)
            if(face.normal.x == front_vector.x and abs(round(face.normal.y, 3)) == front_vector.y and abs(round(face.normal.z, 3)) == front_vector.z):
                frontestfaces.append(face)
                # frontestuvface = uvface
            else:
                print(face.normal)

            # if((face.normal.x == frontestfaces[0].normal.x) and (abs(face.normal.y) == abs(frontestfaces[0].normal.y)) and (abs(face.normal.z) == abs(frontestfaces[0].normal.z) )):
            #     frontestfaces.append(face)
            # elif((face.normal-front_vector).length < (frontestfaces[0].normal-front_vector).length):
            #     frontestfaces = [face]

        # [print(f.normal) for f in frontestfaces]
        islands = {stickers.Island(self, face, self.matrix, normal_matrix, self.s) for face in frontestfaces}
        self.islands = sorted(islands, reverse=True, key=lambda island: len(island.faces))

        # print(islands)
        uvfaces = {face: uvface for island in islands for face, uvface in island.faces.items()}
        uvedges = {loop: uvedge for island in islands for loop, uvedge in island.edges.items()}
        # fold_list = [uvedge for island in islands for loop, uvedge in island.edges.items() if not loop.edge.seam]
        for loop, uvedge in uvedges.items():
            self.edges[loop.edge].uvedges.append(uvedge)
        # check for edges that are cut permanently
        edges = [edge for edge in self.edges.values() if not edge.force_cut and edge.main_faces]
        #
        # print(len(fold_list))
        if edges:
            average_length = sum(edge.vector.length for edge in edges) / len(edges)
            for edge in edges:
                edge.generate_priority(priority_effect, average_length)
            edges.sort(reverse=False, key=lambda edge: edge.priority)
            # print([edge.is_kerf for edge in edges])
            for edge in edges:
                if not edge.vector:
                    continue

        # edge_a, edge_b = (uvedges[l] for l in edge.main_faces if l.is_valid)
        # if(len(fold_list) == 2):
        #     edge_a = fold_list[0]
        #     edge_b = fold_list[1]
            # old_island = join_rib(edge_a, edge_b, size_limit=page_size)
            # islands = {old_island}
            # # if old_island:
            # #     islands.remove(old_island)


        # for edge in self.edges.values():
        #     # some edges did not know until now whether their angle is convex or concave
        #     if edge.main_faces and (
        #             uvfaces[edge.main_faces[0].face].flipped or uvfaces[edge.main_faces[1].face].flipped):
        #         edge.calculate_angle()
        #     # ensure that the order of faces corresponds to the order of uvedges
        #     if edge.main_faces:
        #         reordered = [None, None]
        #         for uvedge in edge.uvedges:
        #             try:
        #                 index = edge.main_faces.index(uvedge.loop)
        #                 reordered[index] = uvedge
        #             except ValueError:
        #                 reordered.append(uvedge)
        #         edge.uvedges = reordered

        for island in self.islands:
            # if the normals are ambiguous, flip them so that there are more convex edges than concave ones
            # if any(uvface.flipped for uvface in island.faces.values()):
            #     island_edges = {self.edges[uvedge.edge] for uvedge in island.edges}
            #     balance = sum(
            #         (+1 if edge.angle > 0 else -1) for edge in island_edges if not edge.is_cut(uvedge.uvface.face))
            #     if balance < 0:
            #         island.is_inside_out = True

            # construct a linked list from each island's boundary
            # uvedge.neighbor_right is clockwise = forward = via uvedge.vb if not uvface.flipped
            neighbor_lookup, conflicts = dict(), dict()
            for uvedge in island.boundary:
                uvvertex = uvedge.va if uvedge.uvface.flipped else uvedge.vb
                if uvvertex not in neighbor_lookup:
                    neighbor_lookup[uvvertex] = uvedge
                else:
                    if uvvertex not in conflicts:
                        conflicts[uvvertex] = [neighbor_lookup[uvvertex], uvedge]
                    else:
                        conflicts[uvvertex].append(uvedge)

            for uvedge in island.boundary:
                uvvertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                if uvvertex not in conflicts:
                    # using the 'get' method so as to handle single-connected vertices properly
                    uvedge.neighbor_right = neighbor_lookup.get(uvvertex, uvedge)
                    uvedge.neighbor_right.neighbor_left = uvedge
                else:
                    conflicts[uvvertex].append(uvedge)

            # resolve merged vertices with more boundaries crossing
            def direction_to_float(vector):
                return (1 - vector.x / vector.length) if vector.y > 0 else (vector.x / vector.length - 1)

            for uvvertex, uvedges in conflicts.items():
                def is_inwards(uvedge):
                    return uvedge.uvface.flipped == (uvedge.va is uvvertex)

                def uvedge_sortkey(uvedge):
                    if is_inwards(uvedge):
                        return direction_to_float(uvedge.va.co - uvedge.vb.co)
                    else:
                        return direction_to_float(uvedge.vb.co - uvedge.va.co)

                uvedges.sort(key=uvedge_sortkey)
                for right, left in (
                        zip(uvedges[:-1:2], uvedges[1::2]) if is_inwards(uvedges[0])
                        else zip([uvedges[-1]] + uvedges[1::2], uvedges[:-1:2])):
                    left.neighbor_right = right
                    right.neighbor_left = left

        return True

    def generate_stickers(self, default_width, do_create_numbers=True):
        """Add sticker faces where they are needed."""

        def uvedge_priority(uvedge):
            """Returns whether it is a good idea to stick something on this edge's face"""
            # TODO: it should take into account overlaps with faces and with other stickers
            face = uvedge.uvface.face
            return face.calc_area() / face.calc_perimeter()

        def add_sticker(uvedge, index, target_uvedge, thickness_switch, isreversed=False):
            uvedge.sticker = stickers.Sticker(uvedge, default_width, index, target_uvedge, thickness_switch, isreversed)
            uvedge.uvface.island.add_marker(uvedge.sticker)

        def is_index_obvious(uvedge, target):
            if uvedge in (target.neighbor_left, target.neighbor_right):
                return True
            if uvedge.neighbor_left.loop.edge is target.neighbor_right.loop.edge and uvedge.neighbor_right.loop.edge is target.neighbor_left.loop.edge:
                return True
            return False

        for edge in self.edges.values():
            index = None
            if edge.is_main_cut and len(edge.uvedges) >= 2 and edge.vector.length_squared > 0:
                target, source = edge.uvedges[:2]
                if uvedge_priority(target) < uvedge_priority(source):
                    target, source = source, target
                target_island = target.uvface.island
                add_sticker(target, index, source, self.thickness_switch, True)

        for edge in self.edges.values():
            index = None
            if edge.is_main_cut and len(edge.uvedges) >= 2 and edge.vector.length_squared > 0:
                target, source = edge.uvedges[:2]
                if uvedge_priority(target) < uvedge_priority(source):
                    target, source = source, target
                target_island = target.uvface.island
                if do_create_numbers:
                    for uvedge in [source] + edge.uvedges[2:]:
                        target_island.sticker_numbering += 1
                        index = str(target_island.sticker_numbering)
                        if u.is_upsidedown_wrong(index):
                            index += "."
                        # target_island.add_marker(Arrow(target, default_width, index))
                        break
                add_sticker(source, index, target, self.thickness_switch, False)


        islands = self.islands
        uvfaces = {face: uvface for island in islands for face, uvface in island.faces.items()}

        up_vector = M.Vector((0, 0, 1))
        toppestface = None
        toppestuvface = None
        for face, uvface in uvfaces.items():
            if( not toppestface):
                toppestface = face
                toppestuvface = uvface

            if((face.normal-up_vector).length < (toppestface.normal-up_vector).length):
                toppestface = face
                toppestuvface = uvface
        self.add_hole(toppestuvface)


    def generate_numbers_alone(self, size):
        global_numbering = 0
        for edge in self.edges.values():
            if edge.is_main_cut and len(edge.uvedges) >= 2:
                global_numbering += 1
                index = str(global_numbering)
                if u.is_upsidedown_wrong(index):
                    index += "."
                for uvedge in edge.uvedges:
                    uvedge.uvface.island.add_marker(stickers.NumberAlone(uvedge, index, size))

    def enumerate_islands(self):
        for num, island in enumerate(self.islands, 1):
            island.number = num
            island.generate_label()

    def scale_islands(self, scale):
        for island in self.islands:
            vertices = set(island.vertices.values())
            for point in chain((vertex.co for vertex in vertices), island.fake_vertices):
                point *= scale

    def finalize_islands(self, cage_size, title_height=0):
        for island in self.islands:
            if title_height:
                island.title = "[{}] {}".format(island.abbreviation, island.label)
            points = [vertex.co for vertex in set(island.vertices.values())] + island.fake_vertices


            points_c = list()
            for p in points:
                if(p.x != 0.5):
                    points_c.append(p)
            # DEBUG
            angle, _ = u.cage_fit(points_c, (cage_size.y - title_height) / cage_size.x)
            rot = M.Matrix.Rotation(angle, 2)
            for point in points:
                # note: we need an in-place operation, and Vector.rotate() seems to work for 3d vectors only
                if(point.x != 0.5):
                    point[:] = rot @ point
            for marker in island.markers:
                marker.rot = rot @ marker.rot
            top_right = M.Vector((max(v.x for v in points_c), max(v.y for v in points_c) - title_height))
            bottom_left = M.Vector((min(v.x for v in points_c), min(v.y for v in points_c) - title_height))
            # print(f"fitted aspect: {(top_right.y - bottom_left.y) / (top_right.x - bottom_left.x)}")
            for point in points_c:
                point -= bottom_left

            island.bounding_box = M.Vector((max(v.x for v in points_c), max(v.y for v in points_c)))
            # print(island.bounding_box)

    def largest_island_ratio(self, cage_size):
        return max(i / p for island in self.islands for (i, p) in zip(island.bounding_box, cage_size))

    def fit_islands(self, cage_size):
        """Move islands so that they fit onto pages, based on their bounding boxes"""

        def try_emplace(island, page_islands, stops_x, stops_y, occupied_cache):
            """Tries to put island to each pair from stops_x, stops_y
            and checks if it overlaps with any islands present on the page.
            Returns True and positions the given island on success."""
            bbox_x, bbox_y = island.bounding_box.xy
            for x in stops_x:
                if x + bbox_x > cage_size.x:
                    continue
                for y in stops_y:
                    if y + bbox_y > cage_size.y or (x, y) in occupied_cache:
                        continue
                    for i, obstacle in enumerate(page_islands):
                        # if this obstacle overlaps with the island, try another stop
                        if (x + bbox_x > obstacle.pos.x and
                                obstacle.pos.x + obstacle.bounding_box.x > x and
                                y + bbox_y > obstacle.pos.y and
                                obstacle.pos.y + obstacle.bounding_box.y > y):
                            if x >= obstacle.pos.x and y >= obstacle.pos.y:
                                occupied_cache.add((x, y))
                            # just a stupid heuristic to make subsequent searches faster
                            if i > 0:
                                page_islands[1:i + 1] = page_islands[:i]
                                page_islands[0] = obstacle
                            break
                    else:
                        # if no obstacle called break, this position is okay
                        island.pos.xy = x, y
                        page_islands.append(island)
                        stops_x.append(x + bbox_x)
                        stops_y.append(y + bbox_y)
                        return True
            return False

        def drop_portion(stops, border, divisor):
            stops.sort()
            # distance from left neighbor to the right one, excluding the first stop
            distances = [right - left for left, right in zip(stops, chain(stops[2:], [border]))]
            quantile = sorted(distances)[len(distances) // divisor]
            return [stop for stop, distance in zip(stops, chain([quantile], distances)) if distance >= quantile]

        if any(island.bounding_box.x > cage_size.x or island.bounding_box.y > cage_size.y for island in self.islands):
            # print(cage_size)
            raise unfold.UnfoldError(
                "An island is too big to fit onto page of the given size. "
                "Either downscale the model or find and split that island manually.\n"
                "Export failed, sorry.")
        # sort islands by their diagonal... just a guess
        remaining_islands = sorted(self.islands, reverse=True, key=lambda island: island.bounding_box.length_squared)
        page_num = 1  # TODO delete me

        while remaining_islands:
            # create a new page and try to fit as many islands onto it as possible
            page = Page(page_num)
            page_num += 1
            occupied_cache = set()
            stops_x, stops_y = [0], [0]
            for island in remaining_islands:
                try_emplace(island, page.islands, stops_x, stops_y, occupied_cache)
                # if overwhelmed with stops, drop a quarter of them
                if len(stops_x) ** 2 > 4 * len(self.islands) + 100:
                    stops_x = drop_portion(stops_x, cage_size.x, 4)
                    stops_y = drop_portion(stops_y, cage_size.y, 4)
            remaining_islands = [island for island in remaining_islands if island not in page.islands]
            self.pages.append(page)

    def save_uv(self, cage_size=M.Vector((1, 1)), separate_image=False):
        if separate_image:
            for island in self.islands:
                island.save_uv_separate(self.looptex)
        else:
            for island in self.islands:
                island.save_uv(self.looptex, cage_size)

    def save_image(self, page_size_pixels: M.Vector, filename):
        for page in self.pages:
            image = u.create_blank_image("Page {}".format(page.name), page_size_pixels, alpha=1)
            image.filepath_raw = page.image_path = "{}_{}.png".format(filename, page.name)
            faces = [face for island in page.islands for face in island.faces]
            self.bake(faces, image)
            image.save()
            image.user_clear()
            bpy.data.images.remove(image)

    def save_separate_images(self, scale, filepath, embed=None):
        for i, island in enumerate(self.islands):
            image_name = "Island {}".format(i)
            image = u.create_blank_image(image_name, island.bounding_box * scale, alpha=0)
            self.bake(island.faces.keys(), image)
            if embed:
                island.embedded_image = embed(image)
            else:
                from os import makedirs
                image_dir = filepath
                makedirs(image_dir, exist_ok=True)
                image_path = os_path.join(image_dir, "island{}.png".format(i))
                image.filepath_raw = image_path
                image.save()
                island.image_path = image_path
            image.user_clear()
            bpy.data.images.remove(image)

    def bake(self, faces, image):
        if not self.looptex:
            raise unfold.UnfoldError(
                "The mesh has no UV Map slots left. Either delete a UV Map or export the net without textures.")
        ob = bpy.context.active_object
        me = ob.data
        # in Cycles, the image for baking is defined by the active Image Node
        temp_nodes = dict()
        for mat in me.materials:
            mat.use_nodes = True
            img = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img.image = image
            temp_nodes[mat] = img
            mat.node_tree.nodes.active = img
        # move all excess faces to negative numbers (that is the only way to disable them)
        ignored_uvs = [loop[self.looptex].uv for f in self.data.faces if f not in faces for loop in f.loops]
        for uv in ignored_uvs:
            uv *= -1
        bake_type = bpy.context.scene.cycles.bake_type
        sta = bpy.context.scene.render.bake.use_selected_to_active
        try:
            ob.update_from_editmode()
            me.uv_layers.active = me.uv_layers[self.looptex.name]
            bpy.ops.object.bake(type=bake_type, margin=1, use_selected_to_active=sta, cage_extrusion=100,
                                use_clear=False)
        except RuntimeError as e:
            raise unfold.UnfoldError(*e.args)
        finally:
            for mat, node in temp_nodes.items():
                mat.node_tree.nodes.remove(node)
        for uv in ignored_uvs:
            uv *= -1

# class AbstractSweepLine:
#     def __init__(self):
#         self.children = list()    


def join(uvedge_a, uvedge_b, size_limit=None, epsilon=1e-6):
    """
    Try to join other island on given edge
    Returns False if they would overlap
    """
    def is_below(self, other, correct_geometry=True):
        if self is other:
            return False
        if self.top < other.bottom:
            return True
        if other.top < self.bottom:
            return False
        if self.max.tup <= other.min.tup:
            return True
        if other.max.tup <= self.min.tup:
            return False
        self_vector = self.max.co - self.min.co
        min_to_min = other.min.co - self.min.co
        cross_b1 = self_vector.cross(min_to_min)
        cross_b2 = self_vector.cross(other.max.co - self.min.co)
        if cross_b2 < cross_b1:
            cross_b1, cross_b2 = cross_b2, cross_b1
        if cross_b2 > 0 and (cross_b1 > 0 or (cross_b1 == 0 and not self.is_uvface_upwards())):
            return True
        if cross_b1 < 0 and (cross_b2 < 0 or (cross_b2 == 0 and self.is_uvface_upwards())):
            return False
        other_vector = other.max.co - other.min.co
        cross_a1 = other_vector.cross(-min_to_min)
        cross_a2 = other_vector.cross(self.max.co - other.min.co)
        if cross_a2 < cross_a1:
            cross_a1, cross_a2 = cross_a2, cross_a1
        if cross_a2 > 0 and (cross_a1 > 0 or (cross_a1 == 0 and not other.is_uvface_upwards())):
            return False
        if cross_a1 < 0 and (cross_a2 < 0 or (cross_a2 == 0 and other.is_uvface_upwards())):
            return True
        if cross_a1 == cross_b1 == cross_a2 == cross_b2 == 0:
            if correct_geometry:
                raise GeometryError
            elif self.is_uvface_upwards() == other.is_uvface_upwards():
                raise Intersection
            return False
        if self.min.tup == other.min.tup or self.max.tup == other.max.tup:
            return cross_a2 > cross_b2
        raise Intersection

    class Intersection(Exception):
        pass

    class GeometryError(Exception):
        pass

    class QuickSweepline:
        """Efficient sweepline based on binary search, checking neighbors only"""

        def __init__(self):
            self.children = list()

        def add(self, item, cmp=is_below):
            low, high = 0, len(self.children)
            while low < high:
                mid = (low + high) // 2
                if cmp(self.children[mid], item):
                    low = mid + 1
                else:
                    high = mid
            self.children.insert(low, item)

        def remove(self, item, cmp=is_below):
            index = self.children.index(item)
            self.children.pop(index)
            if index > 0 and index < len(self.children):
                # check for intersection
                if cmp(self.children[index], self.children[index - 1]):
                    raise GeometryError

    class BruteSweepline:
        """Safe sweepline which checks all its members pairwise"""

        def __init__(self):
            self.children = set()

        def add(self, item, cmp=is_below):
            for child in self.children:
                if child.min is not item.min and child.max is not item.max:
                    cmp(item, child, False)
            self.children.add(item)

        def remove(self, item):
            self.children.remove(item)


    def sweep(sweepline, segments):
        """Sweep across the segments and raise an exception if necessary"""
        # careful, 'segments' may be a use-once iterator
        events_add = sorted(segments, reverse=True, key=lambda uvedge: uvedge.min.tup)
        events_remove = sorted(events_add, reverse=True, key=lambda uvedge: uvedge.max.tup)
        while events_remove:
            while events_add and events_add[-1].min.tup <= events_remove[-1].max.tup:
                sweepline.add(events_add.pop())
            sweepline.remove(events_remove.pop())

    def root_find(value, tree):
        """Find the root of a given value in a forest-like dictionary
        also updates the dictionary using path compression"""
        parent, relink = tree.get(value), list()
        while parent is not None:
            relink.append(value)
            value, parent = parent, tree.get(parent)
        tree.update(dict.fromkeys(relink, value))
        return value

    def slope_from(position):
        def slope(uvedge):
            vec = (uvedge.vb.co - uvedge.va.co) if uvedge.va.tup == position else (uvedge.va.co - uvedge.vb.co)
            return (vec.y / vec.length + 1) if ((vec.x, vec.y) > (0, 0)) else (-1 - vec.y / vec.length)

        return slope

    island_a, island_b = (e.uvface.island for e in (uvedge_a, uvedge_b))
    if island_a is island_b:
        return False
    elif len(island_b.faces) > len(island_a.faces):
        uvedge_a, uvedge_b = uvedge_b, uvedge_a
        island_a, island_b = island_b, island_a
    # check if vertices and normals are aligned correctly
    verts_flipped = uvedge_b.loop.vert is uvedge_a.loop.vert
    flipped = verts_flipped ^ uvedge_a.uvface.flipped ^ uvedge_b.uvface.flipped
    # determine rotation
    # NOTE: if the edges differ in length, the matrix will involve uniform scaling.
    # Such situation may occur in the case of twisted n-gons
    first_b, second_b = (uvedge_b.va, uvedge_b.vb) if not verts_flipped else (uvedge_b.vb, uvedge_b.va)
    if not flipped:
        rot = u.fitting_matrix(first_b.co - second_b.co, uvedge_a.vb.co - uvedge_a.va.co)
    else:
        flip = M.Matrix(((-1, 0), (0, 1)))
        rot = u.fitting_matrix(flip @ (first_b.co - second_b.co), uvedge_a.vb.co - uvedge_a.va.co) @ flip
    trans = uvedge_a.vb.co - rot @ first_b.co
    # preview of island_b's vertices after the join operation
    phantoms = {uvvertex: stickers.UVVertex(rot @ uvvertex.co + trans) for uvvertex in island_b.vertices.values()}

    # check the size of the resulting island
    if size_limit:
        points = [vert.co for vert in chain(island_a.vertices.values(), phantoms.values())]
        left, right, bottom, top = (fn(co[i] for co in points) for i in (0, 1) for fn in (min, max))
        bbox_width = right - left
        bbox_height = top - bottom
        if min(bbox_width, bbox_height) ** 2 > size_limit.x ** 2 + size_limit.y ** 2:
            return False
        if (bbox_width > size_limit.x or bbox_height > size_limit.y) and (
                bbox_height > size_limit.x or bbox_width > size_limit.y):
            _, height = u.cage_fit(points, size_limit.y / size_limit.x)
            if height > size_limit.y:
                return False

    distance_limit = uvedge_a.loop.edge.calc_length() * epsilon
    # try and merge UVVertices closer than sqrt(distance_limit)
    merged_uvedges = set()
    merged_uvedge_pairs = list()

    # merge all uvvertices that are close enough using a union-find structure
    # uvvertices will be merged only in cases island_b->island_a and island_a->island_a
    # all resulting groups are merged together to a uvvertex of island_a
    is_merged_mine = False
    shared_vertices = {loop.vert for loop in chain(island_a.vertices, island_b.vertices)}
    for vertex in shared_vertices:
        uvs_a = {island_a.vertices.get(loop) for loop in vertex.link_loops} - {None}
        uvs_b = {island_b.vertices.get(loop) for loop in vertex.link_loops} - {None}
        for a, b in product(uvs_a, uvs_b):
            if (a.co - phantoms[b].co).length_squared < distance_limit:
                phantoms[b] = root_find(a, phantoms)
        for a1, a2 in combinations(uvs_a, 2):
            if (a1.co - a2.co).length_squared < distance_limit:
                a1, a2 = (root_find(a, phantoms) for a in (a1, a2))
                if a1 is not a2:
                    phantoms[a2] = a1
                    is_merged_mine = True
        for source, target in phantoms.items():
            target = root_find(target, phantoms)
            phantoms[source] = target

    for uvedge in (chain(island_a.boundary, island_b.boundary) if is_merged_mine else island_b.boundary):
        for loop in uvedge.loop.link_loops:
            partner = island_b.edges.get(loop) or island_a.edges.get(loop)
            if partner is not None and partner is not uvedge:
                paired_a, paired_b = phantoms.get(partner.vb, partner.vb), phantoms.get(partner.va, partner.va)
                if (partner.uvface.flipped ^ flipped) != uvedge.uvface.flipped:
                    paired_a, paired_b = paired_b, paired_a
                if phantoms.get(uvedge.va, uvedge.va) is paired_a and phantoms.get(uvedge.vb, uvedge.vb) is paired_b:
                    # if these two edges will get merged, add them both to the set
                    merged_uvedges.update((uvedge, partner))
                    merged_uvedge_pairs.append((uvedge, partner))
                    break

    if uvedge_b not in merged_uvedges:
        raise unfold.UnfoldError("Export failed. Please report this error, including the model if you can.")

    boundary_other = [
        stickers.PhantomUVEdge(phantoms[uvedge.va], phantoms[uvedge.vb], flipped ^ uvedge.uvface.flipped)
        for uvedge in island_b.boundary if uvedge not in merged_uvedges]
    # TODO: if is_merged_mine, it might make sense to create a similar list from island_a.boundary as well

    incidence = {vertex.tup for vertex in phantoms.values()}.intersection(
        vertex.tup for vertex in island_a.vertices.values())
    incidence = {position: list() for position in incidence}  # from now on, 'incidence' is a dict
    for uvedge in chain(boundary_other, island_a.boundary):
        if uvedge.va.co == uvedge.vb.co:
            continue
        for vertex in (uvedge.va, uvedge.vb):
            site = incidence.get(vertex.tup)
            if site is not None:
                site.append(uvedge)
    for position, segments in incidence.items():
        if len(segments) <= 2:
            continue
        segments.sort(key=slope_from(position))
        for right, left in u.pairs(segments):
            is_left_ccw = left.is_uvface_upwards() ^ (left.max.tup == position)
            is_right_ccw = right.is_uvface_upwards() ^ (right.max.tup == position)
            if is_right_ccw and not is_left_ccw and type(right) is not type(
                    left) and right not in merged_uvedges and left not in merged_uvedges:
                return False
            if (not is_right_ccw and right not in merged_uvedges) ^ (is_left_ccw and left not in merged_uvedges):
                return False

    # check for self-intersections
    try:
        try:
            sweepline = QuickSweepline() if island_a.has_safe_geometry and island_b.has_safe_geometry else BruteSweepline()
            sweep(sweepline, (uvedge for uvedge in chain(boundary_other, island_a.boundary)))
            island_a.has_safe_geometry &= island_b.has_safe_geometry
        except GeometryError:
            sweep(BruteSweepline(), (uvedge for uvedge in chain(boundary_other, island_a.boundary)))
            island_a.has_safe_geometry = False
    except Intersection:
        return False

    # mark all edges that connect the islands as not cut
    for uvedge in merged_uvedges:
        island_a.mesh.edges[uvedge.loop.edge].is_main_cut = False

    # include all trasformed vertices as mine
    island_a.vertices.update({loop: phantoms[uvvertex] for loop, uvvertex in island_b.vertices.items()})

    # re-link uvedges and uvfaces to their transformed locations
    for uvedge in island_b.edges.values():
        uvedge.va = phantoms[uvedge.va]
        uvedge.vb = phantoms[uvedge.vb]
        uvedge.update()
    if is_merged_mine:
        for uvedge in island_a.edges.values():
            uvedge.va = phantoms.get(uvedge.va, uvedge.va)
            uvedge.vb = phantoms.get(uvedge.vb, uvedge.vb)
    island_a.edges.update(island_b.edges)

    for uvface in island_b.faces.values():
        uvface.island = island_a
        uvface.vertices = {loop: phantoms[uvvertex] for loop, uvvertex in uvface.vertices.items()}
        uvface.flipped ^= flipped
    if is_merged_mine:
        # there may be own uvvertices that need to be replaced by phantoms
        for uvface in island_a.faces.values():
            if any(uvvertex in phantoms for uvvertex in uvface.vertices):
                uvface.vertices = {loop: phantoms.get(uvvertex, uvvertex) for loop, uvvertex in uvface.vertices.items()}
    island_a.faces.update(island_b.faces)

    island_a.boundary = [
        uvedge for uvedge in chain(island_a.boundary, island_b.boundary)
        if uvedge not in merged_uvedges]

    for uvedge, partner in merged_uvedge_pairs:
        # make sure that main faces are the ones actually merged (this changes nothing in most cases)
        edge = island_a.mesh.edges[uvedge.loop.edge]
        edge.main_faces = uvedge.loop, partner.loop

    # everything seems to be OK
    return island_b


class Page:
    """Container for several Islands"""
    __slots__ = ('islands', 'name', 'image_path')

    def __init__(self, num=1):
        self.islands = list()
        self.name = "page{}".format(num)  # TODO delete me
        self.image_path = None
