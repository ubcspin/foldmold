import svglib
from lxml import etree
import logging
import mathutils as M
import os.path as os_path
import sys
import bmesh
import bpy
import bl_operators
from math import pi, ceil, asin, atan2, floor
from svgpathtools import parse_path, Line, Path, QuadraticBezier, CubicBezier, Arc
from . import utilities

class Stickers:
    def __init__(self):
        self.pin_edges = []
        self.sawtooth_edges = []
        self.glue_edges = []
        self.current_edge = "auto"

    """ returns svg root of svg at path"""
    def load_svg(self, path):
        logger = logging.getLogger(__name__)
        parser = etree.XMLParser(remove_comments=True, recover=True)
        try:
            doc = etree.parse(path, parser=parser)
            svg_root = doc.getroot()
        except Exception as exc:
            logger.error("Failed to load input file! (%s)" % exc)
        else:
            return svg_root

    """ returns an array of UVVertices converted from the svg file at path"""
    def svg2uv(self, path):
        ns = {"u": "http://www.w3.org/2000/svg"}
        vertices = []
        svg_root = self.load_svg(path)
        if svg_root is None:
            print("SVG import blowed up, no root!")
            return

        polylines = svg_root.findall("u:polyline", ns)
        lines = svg_root.findall("u:line", ns)
        rectangles = svg_root.findall("u:rect", ns)
        paths = svg_root.findall("u:path", ns)

        # Make Polyline Vectors
        polyline_vectors = []

        for p in polylines:
            points = p.attrib['points']
            points += " 0.5,0.5"
            polyline_vectors += self.vectorize_polylines(points)
            # polyline_vectors += vectorize_polylines("600,600") #delimiter
        for v in polyline_vectors:
            vertices.append(self.makeUVVertices(v))

        # Make Lines
        for l in lines:
            vertices += self.vectorize_lines(l)

        # Make Rectangles
        for r in rectangles:
            vertices += self.vectorize_rects(r)

        # Make Path vectors
        path_vectors = []
        for p in paths:
            path = p.attrib['d']
            path_vectors += self.vectorize_paths(path)
        
        for v in path_vectors:
            vertices.append(self.pathToUVVertices(v))

        return vertices



    def vectorize_paths(self, path):
        paths = parse_path(path)
        uv_vertices = []
        NUM_SAMPLES = 10
        for subpath in paths:
            uv_vertices.append(subpath.start)
            if isinstance(subpath, Line):
                pass
            elif isinstance(subpath, CubicBezier) or isinstance(subpath, QuadraticBezier) or isinstance(subpath, Arc):
                for i in range(NUM_SAMPLES):
                    uv_vertices.append(subpath.point(i/(NUM_SAMPLES-1)))
            uv_vertices.append(subpath.end)
        return uv_vertices


    def vectorize_polylines(self, points):
        points = points.replace(",", " ")

        ps = points.split()
        xs = ps[0::2]  # every second element starting at 0
        ys = ps[1::2]  # every second element starting at 1
        lines = []

        for i in range(0, len(xs)):
            x1 = float(xs[i])
            y1 = float(ys[i])
            # fs = [float(i) for i in [x1,y1,x2,y2]]
            o = {'x1': x1, 'y1': y1}
            lines.append(o)
        return lines

    def vectorize_lines(line):
        return [UVVertex(M.Vector((float(line.attrib['x1']), float(line.attrib['y1']))) * 0.00001), \
        UVVertex(M.Vector((float(line.attrib['x2']), float(line.attrib['y2']))) * 0.00001)]
    
    def vectorize_rects(rect):
        x1, y1 = float(rect.attrib['x']), float(rect.attrib['y'])
        width, height = float(rect.attrib['width']), float(rect.attrib['height'])
        return [UVVertex(M.Vector((x1, y1)) * 0.00001), \
                UVVertex(M.Vector((x1 + width, y1)) * 0.00001), \
                UVVertex(M.Vector((x1 + width, y1 + height)) * 0.00001), \
                UVVertex(M.Vector((x1, y1 + height)) * 0.00001), \
                UVVertex(M.Vector((x1, y1)) * 0.00001)]

    def makeUVVertices(self, v):
        if not (v["x1"] == 0.5):
            v1 = UVVertex(M.Vector((v["x1"], v["y1"])) * 0.00001)  # scaling down to avoid overflow
        else:
            v1 = UVVertex(M.Vector((v["x1"], v["y1"]))  )  # scaling down to avoid overflow

        return v1

    def pathToUVVertices(v):
        return UVVertex(M.Vector((v.real, v.imag)) * 0.00001)

    def load_geometry(self, sp):
        path_to_stickers_mac = "/Applications/Blender.app/Contents/Resources/2.82/scripts/addons/foldmold/Stickers/"
        path_to_stickers_win = "C:\Program Files\\Blender Foundation\\Blender 2.81\\2.81\\scripts\\addons\\Stickers\\"

        if sys.platform.startswith('win32'):
            path_to_stickers = path_to_stickers_win
        elif sys.platform.startswith('darwin'):
            path_to_stickers = path_to_stickers_mac
        else:
            raise ValueError('Please add path for system other than windows or osx')

        return self.svg2uv(os_path.join(path_to_stickers, sp))


class Tooth:
    __slots__ = ("geometry", "width")
    def __init__(self):

        def load_geometry():
            s = Stickers()
            return s.load_geometry("tooth.svg")

        def getWidth():
            # get bounding box of geometry
            return 0.005 # stub

        self.geometry = load_geometry()
        self.width = getWidth()

class Gap:
    __slots__ = ("geometry", "width")
    def __init__(self):

        def load_geometry():
            s = Stickers()
            return s.load_geometry("gap.svg")

        def getWidth():
            # get bounding box of geometry
            return  0.003

        self.geometry = load_geometry()
        self.width = getWidth()

class SawtoothPattern:
    __slots__ = ("tileset", "width")
    def __init__(self, isreversed):
        def getWidth(tileset):
            width = 0
            for tile in tileset:
                width += tile.width
            return width

        if(isreversed):
            self.tileset = [Tooth(), Gap()]
        else:
            self.tileset = [Gap(), Tooth()]
        self.width = getWidth(self.tileset)


    def getGeometry(self):
        vertices = []
        for tile in self.tileset:
            for vi in tile.geometry:
                vertices.insert(len(vertices), vi)

        return vertices



class Hole:
    __slots__ = ("geometry", "width")
    def __init__(self):

        def load_geometry():
            s = Stickers()
            return s.load_geometry("hole.svg")

        def getWidth():
            # get bounding box of geometry
            return 0.003 # stub

        self.geometry = load_geometry()
        self.width = getWidth()

class Connector:
    __slots__ = ("geometry", "width")
    def __init__(self):

        def load_geometry():
            s = Stickers()
            return s.load_geometry("gap2.svg")

        def getWidth():
            # get bounding box of geometry
            return  0.003

        self.geometry = load_geometry()
        self.width = getWidth()

class Pin:
    __slots__ = ("geometry", "width")
    def __init__(self):

        def load_geometry():
            s = Stickers()
            return s.load_geometry("pin.svg")

        def getWidth():
            # get bounding box of geometry
            return  0.003

        self.geometry = load_geometry()
        self.width = getWidth()


class PinPattern:
    __slots__ = ("tileset", "width")
    def __init__(self, isreversed):
        def getWidth(tileset):
            width = 0
            for tile in tileset:
                width += tile.width
            return width


        if(isreversed):
            self.tileset = [Hole(), Connector()]
        else:
            self.tileset = [Pin(), Gap()]
        self.width = getWidth(self.tileset)


    def getGeometry(self):
        vertices = []
        for tile in self.tileset:
            for vi in tile.geometry:
                vertices.insert(len(vertices), vi)

        return vertices

class PourHoleTile:
    __slots__ = ("geometry", "width")
    def __init__(self):

        def load_geometry():
            s = Stickers()
            return s.load_geometry("pourhole.svg")

        def getWidth():
            # get bounding box of geometry
            return 0.003 # stub

        self.geometry = load_geometry()
        self.width = getWidth()


class PourHolePattern:
    __slots__ = ("tileset", "width")
    def __init__(self):
        def getWidth(tileset):
            width = 0
            for tile in tileset:
                width += tile.width
            return width


        self.tileset = [PourHoleTile()]
        self.width = getWidth(self.tileset)


    def getGeometry(self):
        vertices = []
        for tile in self.tileset:
            for vi in tile.geometry:
                vertices.insert(len(vertices), vi)

        return vertices

class UVVertex:
        """Vertex in 2D"""
        __slots__ = ('co', 'tup')

        def __init__(self, vector):
            self.co = vector.xy
            self.tup = tuple(self.co)

        def __next__(self):
            raise StopIteration()

        def __iter__(self):
            return self

class UVEdge:
    """Edge in 2D"""
    # Every UVEdge is attached to only one UVFace
    # UVEdges are doubled as needed because they both have to point clockwise around their faces
    __slots__ = ('va', 'vb', 'uvface', 'loop',
                 'min', 'max', 'bottom', 'top',
                 'neighbor_left', 'neighbor_right', 'sticker', 'is_kerf', 'type', 'pourhole')

    def __init__(self, vertex1: UVVertex, vertex2: UVVertex, uvface, loop, is_kerf, stobj):
        self.va = vertex1
        self.vb = vertex2
        # self.update()
        self.uvface = uvface
        self.sticker = None
        self.loop = loop
        self.is_kerf = is_kerf
        self.type = 'auto'
        self.pourhole = None

        print(self.loop.edge.index)
        print(stobj.pin_edges)
        if(self.loop.edge.index in stobj.pin_edges):
            self.type = 'pin'
        elif(self.loop.edge.index in stobj.sawtooth_edges):
            self.type = 'tooth'
        elif(self.loop.edge.index in stobj.glue_edges):
            self.type = 'glue'
        else:
            self.type = 'auto'

    def update(self):
        """Update data if UVVertices have moved"""
        self.min, self.max = (self.va, self.vb) if (self.va.tup < self.vb.tup) else (self.vb, self.va)
        y1, y2 = self.va.co.y, self.vb.co.y
        self.bottom, self.top = (y1, y2) if y1 < y2 else (y2, y1)

    def is_uvface_upwards(self):
        return (self.va.tup < self.vb.tup) ^ self.uvface.flipped

    def __repr__(self):
        return "({0.va} - {0.vb})".format(self)

class PhantomUVEdge:
    """Temporary 2D Segment for calculations"""
    __slots__ = ('va', 'vb', 'min', 'max', 'bottom', 'top')

    def __init__(self, vertex1: UVVertex, vertex2: UVVertex, flip):
        self.va, self.vb = (vertex2, vertex1) if flip else (vertex1, vertex2)
        self.min, self.max = (self.va, self.vb) if (self.va.tup < self.vb.tup) else (self.vb, self.va)
        y1, y2 = self.va.co.y, self.vb.co.y
        self.bottom, self.top = (y1, y2) if y1 < y2 else (y2, y1)

    def is_uvface_upwards(self):
        return self.va.tup < self.vb.tup

    def __repr__(self):
        return "[{0.va} - {0.vb}]".format(self)


class Island:
    """Part of the net to be exported"""
    __slots__ = ('mesh', 'faces', 'edges', 'vertices', 'fake_vertices', 'boundary', 'markers',
                 'pos', 'bounding_box',
                 'image_path', 'embedded_image',
                 'number', 'label', 'abbreviation', 'title',
                 'has_safe_geometry', 'is_inside_out',
                 'sticker_numbering')

    def __init__(self, mesh, face, matrix, normal_matrix, stobj):
        """Create an Island from a single Face"""
        self.mesh = mesh
        self.faces = dict()  # face -> uvface
        self.edges = dict()  # loop -> uvedge
        self.vertices = dict()  # loop -> uvvertex
        self.fake_vertices = list()
        self.markers = list()
        self.label = None
        self.abbreviation = None
        self.title = None
        self.pos = M.Vector((0, 0))
        self.image_path = None
        self.embedded_image = None
        self.is_inside_out = False  # swaps concave <-> convex edges
        self.has_safe_geometry = True
        self.sticker_numbering = 0

        uvface = UVFace(stobj, face, self, matrix, normal_matrix)
        self.vertices.update(uvface.vertices)
        self.edges.update(uvface.edges)
        self.faces[face] = uvface
        # UVEdges on the boundary
        self.boundary = list(self.edges.values())

    def add_marker(self, marker):
        self.fake_vertices.extend(marker.bounds)
        self.markers.append(marker)

    def generate_label(self, label=None, abbreviation=None):
        """Assign a name to this island automatically"""
        abbr = abbreviation or self.abbreviation or str(self.number)
        # TODO: dots should be added in the last instant when outputting any text
        u = utilities.Utilities()
        if u.is_upsidedown_wrong(abbr):
            abbr += "."
        self.label = label or self.label or "Island {}".format(self.number)
        self.abbreviation = abbr

    def save_uv(self, tex, cage_size):
        """Save UV Coordinates of all UVFaces to a given UV texture
        tex: UV Texture layer to use (BMLayerItem)
        page_size: size of the page in pixels (vector)"""
        scale_x, scale_y = 1 / cage_size.x, 1 / cage_size.y
        for loop, uvvertex in self.vertices.items():
            if not(uvvertex.co.x == 0.5):
                uv = uvvertex.co + self.pos
            loop[tex].uv = uv.x * scale_x, uv.y * scale_y

    def save_uv_separate(self, tex):
        """Save UV Coordinates of all UVFaces to a given UV texture, spanning from 0 to 1
        tex: UV Texture layer to use (BMLayerItem)
        page_size: size of the page in pixels (vector)"""
        scale_x, scale_y = 1 / self.bounding_box.x, 1 / self.bounding_box.y
        for loop, uvvertex in self.vertices.items():
            loop[tex].uv = uvvertex.co.x * scale_x, uvvertex.co.y * scale_y

class UVFace:
    """Face in 2D"""
    __slots__ = ('vertices', 'edges', 'face', 'island', 'flipped', 'uvedges')

    def __init__(self, stobj, face: bmesh.types.BMFace, island: Island, matrix=1, normal_matrix=1):
        self.face = face
        self.island = island
        self.flipped = False  # a flipped UVFace has edges clockwise
        flatten = self.z_up_matrix(normal_matrix @ face.normal) @ matrix
        self.vertices = {loop: UVVertex(flatten @ loop.vert.co) for loop in face.loops}
        self.edges = {loop: UVEdge(self.vertices[loop], self.vertices[loop.link_loop_next], self, loop, self.face.smooth, stobj) for loop in
                      face.loops}
        self.uvedges = [UVEdge(self.vertices[loop], self.vertices[loop.link_loop_next], self, loop, self.face.smooth, stobj) for loop in
                      face.loops]

    def z_up_matrix(self, n):
        """Get a rotation matrix that aligns given vector upwards."""
        b = n.xy.length
        s = n.length
        if b > 0:
            return M.Matrix((
                (n.x * n.z / (b * s), n.y * n.z / (b * s), -b / s),
                (-n.y / b, n.x / b, 0),
                (0, 0, 0)
            ))
        else:
            # no need for rotation
            return M.Matrix((
                (1, 0, 0),
                (0, (-1 if n.z < 0 else 1), 0),
                (0, 0, 0)
            ))

class Edge:
    """Wrapper for BPy Edge"""
    __slots__ = ('data', 'va', 'vb', 'main_faces', 'uvedges',
                 'vector', 'angle',
                 'is_main_cut', 'force_cut', 'priority', 'freestyle', 'is_kerf', 'type')

    def __init__(self, edge):
        self.data = edge
        self.va, self.vb = edge.verts
        self.vector = self.vb.co - self.va.co
        # if self.main_faces is set, then self.uvedges[:2] must correspond to self.main_faces, in their order
        # this constraint is assured at the time of finishing mesh.generate_cuts
        self.uvedges = list()

        self.force_cut = edge.seam  # such edges will always be cut
        self.main_faces = None  # two faces that may be connected in the island
        # is_main_cut defines whether the two main faces are connected
        # all the others will be assumed to be cut
        self.is_main_cut = True
        self.priority = None
        self.angle = None
        self.freestyle = False

        faces = edge.link_faces

        # print(self.data.index)
        # print(pin_edges)
        # if(self.data.index in pin_edges):
        #     self.type = 'pin'
        # elif(self.data.index in sawtooth_edges):
        #     self.type = 'tooth'
        # elif(self.data.index in glue_edges):
        #     self.type = 'glue'
        # else:
        #     self.type = 'auto'
        #
        # for uv in self.uvedges:
        #     uv.type = self.type

        if(faces[0].smooth and faces[1].smooth):
            self.is_kerf = True

            for uv in self.uvedges:
                uv.is_kerf = True
        else:
            self.is_kerf = False

    def choose_main_faces(self):
        """Choose two main faces that might get connected in an island"""
        from itertools import combinations
        loops = self.data.link_loops

        def score(pair):
            return abs(pair[0].face.normal.dot(pair[1].face.normal))

        if len(loops) == 2:
            self.main_faces = list(loops)
        elif len(loops) > 2:
            # find (with brute force) the pair of indices whose loops have the most similar normals
            self.main_faces = max(combinations(loops, 2), key=score)
        if self.main_faces and self.main_faces[1].vert == self.va:
            self.main_faces = self.main_faces[::-1]

    def calculate_angle(self):
        """Calculate the angle between the main faces"""
        loop_a, loop_b = self.main_faces
        normal_a, normal_b = (l.face.normal for l in self.main_faces)
        if not normal_a or not normal_b:
            self.angle = -3  # just a very sharp angle
        else:
            s = normal_a.cross(normal_b).dot(self.vector.normalized())
            s = max(min(s, 1.0), -1.0)  # deal with rounding errors
            self.angle = asin(s)
            if loop_a.link_loop_next.vert != loop_b.vert or loop_b.link_loop_next.vert != loop_a.vert:
                self.angle = abs(self.angle)


    def generate_priority(self, priority_effect, average_length):
        """Calculate the priority value for cutting"""
        angle = self.angle
        if angle > 0:
            self.priority = priority_effect['CONVEX'] * angle / pi
        else:
            self.priority = priority_effect['CONCAVE'] * angle / pi
        self.priority += (self.vector.length / average_length) * priority_effect['LENGTH']
        # print(self.priority)

    def is_cut(self, face):
        """Return False if this edge will the given face to another one in the resulting net
        (useful for edges with more than two faces connected)"""
        # Return whether there is a cut between the two main faces

        if self.main_faces and face in {loop.face for loop in self.main_faces}:
            return self.is_main_cut
        # All other faces (third and more) are automatically treated as cut
        else:
            return True

    def other_uvedge(self, this):
        """Get an uvedge of this edge that is not the given one
        causes an IndexError if case of less than two adjacent edges"""
        return self.uvedges[1] if this is self.uvedges[0] else self.uvedges[0]


class Sticker:
    """Mark in the document: sticker tab"""
    __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices')

    def __init__(self, uvedge, default_width, index, other: UVEdge, isreversed=False):
        """Sticker is directly attached to the given UVEdge"""
        first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
        edge = first_vertex.co - second_vertex.co
        sticker_width = min(default_width, edge.length / 2)

        cos_a = cos_b = 0.5
        sin_a = sin_b = 0.75 ** 0.5
        # len_a is length of the side adjacent to vertex a, len_b likewise
        len_a = len_b = sticker_width / sin_a

        sin_a = abs(1 - cos_a ** 2) ** 0.5
        len_b = min(len_a, (edge.length * sin_a) / (sin_a * cos_b + sin_b * cos_a))
        len_a = 0 if sin_a == 0 else min(sticker_width / sin_a, (edge.length - len_b * cos_b) / cos_a)

        sin_b = abs(1 - cos_b ** 2) ** 0.5
        len_a = min(len_a, (edge.length * sin_b) / (sin_a * cos_b + sin_b * cos_a))
        len_b = 0 if sin_b == 0 else min(sticker_width / sin_b, (edge.length - len_a * cos_a) / cos_b)

        tangent = edge.normalized() #this is a Vector
        cos = tangent.x
        sin = tangent.y

        self.rot = M.Matrix(((cos, -sin), (sin, cos)))

        self.width = sticker_width

        if(uvedge.type == 'pin'):
            pin = PinSticker(uvedge, default_width, index, other, isreversed)
            tab_verts = []
            tab_verts_co = []
            for i in range(len(pin.geometry)):
                if not (pin.geometry_co[i][0] == 0.5):
                    vi = UVVertex((second_vertex.co + self.rot @ pin.geometry_co[i]))
                else:
                    vi = UVVertex((pin.geometry_co[i]))
                tab_verts.insert(len(tab_verts), vi)
                tab_verts_co.insert(len(tab_verts), vi.co)

            self.vertices = []
            self.vertices = tab_verts
            self.vertices.insert(len(tab_verts), first_vertex)
            self.vertices.insert(0, second_vertex)

            # if index and uvedge.uvface.island is not other.uvface.island:
            #     self.text = "{}:{}".format(other.uvface.island.abbreviation, index)
            # else:
            self.text = ""

            self.center = (uvedge.va.co + uvedge.vb.co) / 2
            self.bounds = tab_verts_co
            self.bounds.insert(len(tab_verts_co), self.center)
        elif(uvedge.type == 'tooth'):
            sawtooth = SawtoothSticker(uvedge, default_width, index, other, isreversed)
            tab_verts = []
            tab_verts_co = []
            for i in range(len(sawtooth.geometry)):
                if not(sawtooth.geometry_co[i][0] == 0.5):
                    vi = UVVertex((second_vertex.co + self.rot @ sawtooth.geometry_co[i]))
                else:
                    vi = UVVertex(( sawtooth.geometry_co[i]))
                tab_verts.insert(len(tab_verts), vi)
                tab_verts_co.insert(len(tab_verts), vi.co)

            #OPTIONAL ADJUSTMENT: +  self.rot @ M.Vector((0, self.width * 0.2))
            self.vertices = []
            self.vertices = tab_verts
            self.vertices.insert(len(tab_verts), first_vertex)
            self.vertices.insert(0, second_vertex)


            # if index and uvedge.uvface.island is not other.uvface.island:
            #     self.text = "{}:{}".format(other.uvface.island.abbreviation, index)
            # else:
            self.text = ""

            self.center = (uvedge.va.co + uvedge.vb.co) / 2
            self.bounds = tab_verts_co
            self.bounds.insert(len(tab_verts_co), self.center)
        else:

            other_first, other_second = (other.va, other.vb) if not other.uvface.flipped else (other.vb, other.va)
            other_edge = other_second.co - other_first.co

            # fix overlaps with the most often neighbour - its sticking target
            if first_vertex == other_second:
                cos_a = max(cos_a, edge.dot(other_edge) / (edge.length_squared))  # angles between pi/3 and 0
            elif second_vertex == other_first:
                cos_b = max(cos_b, edge.dot(other_edge) / (edge.length_squared))  # angles between pi/3 and 0

            # Fix tabs for sticking targets with small angles
            try:
                other_face_neighbor_left = other.neighbor_left
                other_face_neighbor_right = other.neighbor_right
                other_edge_neighbor_a = other_face_neighbor_left.vb.co - other.vb.co
                other_edge_neighbor_b = other_face_neighbor_right.va.co - other.va.co
                # Adjacent angles in the face
                cos_a = max(cos_a,
                            -other_edge.dot(other_edge_neighbor_a) / (other_edge.length * other_edge_neighbor_a.length))
                cos_b = max(cos_b,
                            other_edge.dot(other_edge_neighbor_b) / (other_edge.length * other_edge_neighbor_b.length))
            except AttributeError:  # neighbor data may be missing for edges with 3+ faces
                pass
            except ZeroDivisionError:
                pass

            # Calculate the lengths of the glue tab edges using the possibly smaller angles
            sin_a = abs(1 - cos_a ** 2) ** 0.5
            len_b = min(len_a, (edge.length * sin_a) / (sin_a * cos_b + sin_b * cos_a))
            len_a = 0 if sin_a == 0 else min(sticker_width / sin_a, (edge.length - len_b * cos_b) / cos_a)

            sin_b = abs(1 - cos_b ** 2) ** 0.5
            len_a = min(len_a, (edge.length * sin_b) / (sin_a * cos_b + sin_b * cos_a))
            len_b = 0 if sin_b == 0 else min(sticker_width / sin_b, (edge.length - len_a * cos_a) / cos_b)

            v3 = UVVertex(second_vertex.co + M.Matrix(((cos_b, -sin_b), (sin_b, cos_b))) @ edge * len_b / edge.length)
            v4 = UVVertex(first_vertex.co + M.Matrix(((-cos_a, -sin_a), (sin_a, -cos_a))) @ edge * len_a / edge.length)
            if v3.co != v4.co:
                self.vertices = [second_vertex, v3, v4, first_vertex]
            else:
                self.vertices = [second_vertex, v3, first_vertex]

            sin, cos = edge.y / edge.length, edge.x / edge.length
            self.rot = M.Matrix(((cos, -sin), (sin, cos)))
            self.width = sticker_width * 0.9
            # if index and uvedge.uvface.island is not other.uvface.island:
            #     self.text = "{}:{}".format(other.uvface.island.abbreviation, index)
            # else:
            #     self.text = index
            self.text = ""
            self.center = (uvedge.va.co + uvedge.vb.co) / 2 + self.rot @ M.Vector((0, self.width * 0.2))
            self.bounds = [v3.co, v4.co, self.center] if v3.co != v4.co else [v3.co, self.center]


class PourHoleSticker:
    __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices', "pattern", "geometry", "geometry_co")

    def __init__(self, uvedge):
        first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
        edge = first_vertex.co - second_vertex.co
        self.width = edge.length
        self.pattern = PourHolePattern()
        midsection_count = 1
        midsection_width = self.pattern.width * midsection_count
        offset_left = (self.width - midsection_width) / 2
        offset_right = (self.width - midsection_width) / 2
        self.geometry, self.geometry_co = self.construct(offset_left, midsection_count, self.pattern)

    def construct(self, offset_left, midsection_count, pattern):
        tab_verts = []
        tab_verts_co = []
        tab = self.pattern.getGeometry()
        for n in range(0, midsection_count):
            for i in range(len(tab)):
                if not(tab[i].co.x == 0.5):
                    vi = UVVertex((tab[i].co) + M.Vector((self.pattern.width * n + offset_left, 0)))
                else:
                    vi = UVVertex((tab[i].co))

                tab_verts.insert(len(tab_verts), vi)
                tab_verts_co.insert(len(tab_verts), vi.co)

        return tab_verts, tab_verts_co

class SawtoothSticker:
    __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices', "pattern", "geometry", "geometry_co")

    def __init__(self, uvedge, default_width, index, other: UVEdge, isreversed):
        first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
        edge = first_vertex.co - second_vertex.co
        self.width = edge.length
        self.pattern = SawtoothPattern(isreversed)
        midsection_count = floor(self.width / self.pattern.width)
        midsection_width = self.pattern.width * midsection_count
        offset_left = (self.width - midsection_width) / 2
        offset_right = (self.width - midsection_width) / 2
        self.geometry, self.geometry_co = self.construct(offset_left, midsection_count, self.pattern)
        # print(self.width, self.pattern.width, midsection_count)

    def construct(self, offset_left, midsection_count, pattern):
        tab_verts = []
        tab_verts_co = []
        tab = self.pattern.getGeometry()
        for n in range(0, midsection_count):
            for i in range(len(tab)):
                if not(tab[i].co.x == 0.5):
                    vi = UVVertex((tab[i].co) + M.Vector((self.pattern.width * n + offset_left, 0)))
                else:
                    vi = UVVertex((tab[i].co))
                tab_verts.insert(len(tab_verts), vi)
                tab_verts_co.insert(len(tab_verts), vi.co)

        # print(offset_left)
        return tab_verts, tab_verts_co


class PourHole:
    """Mark in the document: sticker tab"""
    __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices')

    def __init__(self, uvedge):
        first_vertex, second_vertex = (uvedge.va, uvedge.vb)
        edge = first_vertex.co - second_vertex.co
        sticker_width = edge.length / 2

        cos_a = cos_b = 0.5
        sin_a = sin_b = 0.75 ** 0.5
        # len_a is length of the side adjacent to vertex a, len_b likewise
        len_a = len_b = sticker_width / sin_a


        # Calculate the lengths of the glue tab edges using the possibly smaller angles
        sin_a = abs(1 - cos_a ** 2) ** 0.5
        len_b = min(len_a, (edge.length * sin_a) / (sin_a * cos_b + sin_b * cos_a))
        len_a = 0 if sin_a == 0 else min(sticker_width / sin_a, (edge.length - len_b * cos_b) / cos_a)

        sin_b = abs(1 - cos_b ** 2) ** 0.5
        len_a = min(len_a, (edge.length * sin_b) / (sin_a * cos_b + sin_b * cos_a))
        len_b = 0 if sin_b == 0 else min(sticker_width / sin_b, (edge.length - len_a * cos_a) / cos_b)

        tangent = edge.normalized() #this is a Vector
        cos = tangent.x
        sin = tangent.y

        self.rot = M.Matrix(((cos, -sin), (sin, cos)))

        self.width = sticker_width
        sawtooth = PourHoleSticker(uvedge)
        tab_verts = []
        tab_verts_co = []
        for i in range(len(sawtooth.geometry)):
            if not(sawtooth.geometry_co[i][0] == 0.5):
                vi = UVVertex((first_vertex.co - self.rot @ sawtooth.geometry_co[i]))
            else:
                vi = UVVertex(( sawtooth.geometry_co[i]))
            tab_verts.insert(len(tab_verts), vi)
            tab_verts_co.insert(len(tab_verts), vi.co)

        #OPTIONAL ADJUSTMENT: +  self.rot @ M.Vector((0, self.width * 0.2))
        self.vertices = []
        self.vertices = tab_verts
        self.text = ""

        self.center = (uvedge.va.co + uvedge.vb.co) / 2
        self.bounds = tab_verts_co
        self.bounds.insert(len(tab_verts_co), self.center)

class PinSticker:
        __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices', "pattern", "geometry", "geometry_co")

        def __init__(self, uvedge, default_width, index, other: UVEdge, isreversed):
            first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
            edge = first_vertex.co - second_vertex.co
            self.width = edge.length
            self.pattern = PinPattern(isreversed)
            midsection_count = floor(self.width / self.pattern.width)
            midsection_width = self.pattern.width * midsection_count
            offset_left = (self.width - midsection_width) / 2
            offset_right = (self.width - midsection_width) / 2
            self.geometry, self.geometry_co = self.construct(offset_left, midsection_count, self.pattern)
            # print(self.width, self.pattern.width, midsection_count)

        def construct(self, offset_left, midsection_count, pattern):
            tab_verts = []
            tab_verts_co = []
            tab = self.pattern.getGeometry()
            for n in range(0, midsection_count):
                for i in range(len(tab)):
                    if not(tab[i].co.x == 0.5):
                        vi = UVVertex((tab[i].co) + M.Vector((self.pattern.width * n + offset_left, 0)))
                    else:
                        vi = UVVertex((tab[i].co))

                    tab_verts.insert(len(tab_verts), vi)
                    tab_verts_co.insert(len(tab_verts), vi.co)

            # print(offset_left)
            return tab_verts, tab_verts_co


class NumberAlone:
    """Mark in the document: numbering inside the island denoting edges to be sticked"""
    __slots__ = ('bounds', 'center', 'rot', 'text', 'size')

    def __init__(self, uvedge, index, default_size=0.005):
        """Sticker is directly attached to the given UVEdge"""
        edge = (uvedge.va.co - uvedge.vb.co) if not uvedge.uvface.flipped else (uvedge.vb.co - uvedge.va.co)

        self.size = default_size
        sin, cos = edge.y / edge.length, edge.x / edge.length
        self.rot = M.Matrix(((cos, -sin), (sin, cos)))
        self.text = index
        self.center = (uvedge.va.co + uvedge.vb.co) / 2 - self.rot @ M.Vector((0, self.size * 1.2))
        self.bounds = [self.center]
