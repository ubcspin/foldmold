import svglib
from lxml import etree
import logging
import mathutils as M
import os.path as os_path
import sys
import bmesh
import bpy
import bl_operators
import functools
from math import pi, ceil, asin, atan2, floor
from svgpathtools import parse_path, Line, Path, QuadraticBezier, CubicBezier, Arc
import functools


if __package__ is None or __package__ == '':
    # uses current directory visibility
    import utilities
else:
    # uses current package visibility
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

    def load_geometry(self, filename):
        path_to_stickers_mac = "/Applications/Blender.app/Contents/Resources/2.82/scripts/addons/foldmold/Stickers/"
        path_to_stickers_win = "C:\Program Files\\Blender Foundation\\Blender 2.81\\2.81\\scripts\\addons\\foldmold\\Stickers\\"

        if sys.platform.startswith('win32'):
            path_to_stickers = path_to_stickers_win
        elif sys.platform.startswith('darwin'):
            path_to_stickers = path_to_stickers_mac
        else:
            raise ValueError('Please add path for system other than windows or osx')

        return self.svg2uv(os_path.join(path_to_stickers, filename))



## Fundamental stickers
class AbstractSticker:
    """
    filenames: array of sticker filenames of different thickness
    thickness_switch(int): determines which svg filename to use
    """
    __slots__ = ("geometry", "width", "thickness_switch", "filenames")
    def __init__(self, filenames, width, thickness_switch=0):
        self.filenames = filenames
        self.width = width
        self.thickness_switch = thickness_switch
        self.geometry = self.load_geometry()

    def load_geometry(self):
        s = Stickers()
        filename = self.filenames[self.thickness_switch]
        return s.load_geometry(filename)

    def getWidth(self):
        return self.width

    def setThicknessSwitch(self, val):
        self.thickness_switch = val

# TODO: update sticker svg's to stickers with right thickness
class Tooth(AbstractSticker):
    def __init__(self, thickness_switch):
        AbstractSticker.__init__(self, ["tooth.svg"], 0.005, thickness_switch)

class Gap(AbstractSticker):
    def __init__(self, thickness_switch):
        AbstractSticker.__init__(self, ["gap.svg", "gap.svg", "gap.svg"], 0.003, thickness_switch)

class Hole(AbstractSticker):
    def __init__(self, thickness_switch):
        AbstractSticker.__init__(self, ["hole0.svg", "hole1.svg", "hole2.svg"], 0.003, thickness_switch)

class PourHoleTile(AbstractSticker):
    def __init__(self):
        AbstractSticker.__init__(self, ["pourhole.svg"], 0.003)

class Connector(AbstractSticker):
    def __init__(self, thickness_switch):
        AbstractSticker.__init__(self, ["gap2.svg", "gap2.svg", "gap2.svg"], 0.003, thickness_switch)

class Pin(AbstractSticker):
    def __init__(self, thickness_switch):
        AbstractSticker.__init__(self, ["pin0.svg", "pin1.svg", "pin2.svg"], 0.003, thickness_switch)

## Patterns
class AbstractPattern:
    __slots__ = ("tileset", "width")
    def __init__(self, isreversed, tileset_r, tileset_f):
        self.isreversed = isreversed
        self.tileset = tileset_r if isreversed else tileset_f
        self.width = self.getWidth(self.tileset)

    def getWidth(self, tileset):
        if (len(tileset) == 1):
            return tileset[0].width
        else:
            return functools.reduce(lambda a,b : a.width + b.width if b else a.width, tileset)
        
    def getGeometry(self):
        vertices = []
        for tile in self.tileset:
            for vi in tile.geometry:
                vertices.insert(len(vertices), vi)
        return vertices

class SawtoothPattern(AbstractPattern):
    def __init__(self, thickness_switch, isreversed):
        AbstractPattern.__init__(self, isreversed, [Gap(thickness_switch), Tooth(thickness_switch)], [Tooth(thickness_switch), Gap(thickness_switch)])

class PinPattern(AbstractPattern):
    def __init__(self, thickness_switch, isreversed):
        AbstractPattern.__init__(self, isreversed, [Hole(thickness_switch), Connector(thickness_switch)], [Pin(thickness_switch), Gap(thickness_switch)])

class PourHolePattern(AbstractPattern):
    def __init__(self, isreversed):
        AbstractPattern.__init__(self, isreversed, [PourHoleTile()], [PourHoleTile()])

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

        # print(self.loop.edge.index)
        # print(stobj.pin_edges)
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
    __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices', 'sticker')

    def __init__(self, uvedge, default_width, index, other: UVEdge, thickness_switch, isreversed=False):
        """Sticker is directly attached to the given UVEdge"""
        first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
        other_first, other_second = (other.va, other.vb) if not other.uvface.flipped else (other.vb, other.va)

        edge = first_vertex.co - second_vertex.co
        other_edge = other_second.co - other_first.co

        sticker_width = min(default_width, edge.length / 2)
        direction = edge.normalized() # this is a unit vector

        self.rot = M.Matrix(((direction.x, -direction.y), (direction.y, direction.x)))
        self.width = sticker_width
        self.text = ""
        self.vertices = []
        self.bounds = []
        self.center = (uvedge.va.co + uvedge.vb.co) / 2 # changes if not tile pattern
        self.sticker = self.generate_sticker(uvedge, default_width, index, other, thickness_switch, isreversed)

        # print(uvedge.type)
        if (uvedge.type != 'pin' and uvedge.type != 'tooth'):
            k = 0.5

            sin_a = sin_b = abs(1 - k ** 2) ** 0.5

            # len_a is length of the side adjacent to vertex a, len_b likewise
            len_c = min(sticker_width / 0.75 ** 0.5, (edge.length * sin_a) / (sin_a * k + (0.75 ** 0.5) * k))
            len_a = min(sticker_width / sin_a, (edge.length - len_c * k) / k, (edge.length * sin_b) / (sin_a * k + sin_b * k))
            len_b = min(sticker_width / sin_b, (edge.length - len_a * k) / k)

            # fix overlaps with the most often neighbour - its sticking target

            k = max(k, edge.dot(other_edge) / (edge.length_squared))  # angles between pi/3 and 0

            cos_a = cos_b = 0.5 # stub

            # Fix tabs for sticking targets with small angles
            try:
                other_face_neighbor_left = other.neighbor_left
                other_face_neighbor_right = other.neighbor_right
                other_edge_neighbor_a = other_face_neighbor_left.vb.co - other.vb.co
                other_edge_neighbor_b = other_face_neighbor_right.va.co - other.va.co
                # Adjacent angles in the face
                cos_a = max(k,
                            -other_edge.dot(other_edge_neighbor_a) / (other_edge.length * other_edge_neighbor_a.length))
                cos_b = max(k,
                            other_edge.dot(other_edge_neighbor_b) / (other_edge.length * other_edge_neighbor_b.length))
            except AttributeError:  # neighbor data may be missing for edges with 3+ faces
                pass
            except ZeroDivisionError:
                pass

            # Calculate the lengths of the glue tab edges using the possibly smaller angles
            v3 = UVVertex(second_vertex.co + M.Matrix(((cos_b, -sin_b), (sin_b, cos_b))) @ edge * len_b / edge.length)
            v4 = UVVertex(first_vertex.co + M.Matrix(((-cos_a, -sin_a), (sin_a, -cos_a))) @ edge * len_a / edge.length)
            if v3.co != v4.co:
                self.vertices = [second_vertex, v3, v4, first_vertex]
            else:
                self.vertices = [second_vertex, v3, first_vertex]

            sin, cos = edge.y / edge.length, edge.x / edge.length
            self.rot = M.Matrix(((cos, -sin), (sin, cos)))
            self.width = sticker_width * 0.9
            self.center = (uvedge.va.co + uvedge.vb.co) / 2 + self.rot @ M.Vector((0, self.width * 0.2))
            self.bounds = [v3.co, v4.co, self.center] if v3.co != v4.co else [v3.co, self.center]

        else:
            for i in range(len(self.sticker.geometry)):
                if not (self.sticker.geometry_co[i][0] == 0.5):
                    vi = UVVertex((second_vertex.co + self.rot @ self.sticker.geometry_co[i]))
                else:
                    vi = UVVertex((self.sticker.geometry_co[i]))
                self.vertices.insert(len(self.vertices), vi)
                self.bounds.insert(len(self.vertices), vi.co)

            self.vertices.insert(len(self.vertices), first_vertex)
            self.vertices.insert(0, second_vertex)
            self.bounds.insert(len(self.bounds), self.center)

    # Returns: AbstractSticker object
    def generate_sticker(self, uvedge, default_width, index, other, thickness_switch, isreversed):
        if (uvedge.type == 'pin'):
            return PinSticker(uvedge, default_width, index, other, thickness_switch, isreversed)
        if (uvedge.type == 'tooth'):
            return SawtoothSticker(uvedge, default_width, index, other, thickness_switch, isreversed)
        return None

class AbstractStickerConstructor:
    __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices', "pattern", "geometry", "geometry_co", "offset_left", "offset_right")
    def __init__(self, uvedge, pattern):
        first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
        edge = first_vertex.co - second_vertex.co
        self.width = edge.length
        self.pattern = pattern
        midsection_count = self.get_midsection_count(self.width, self.pattern)
        midsection_width = self.get_midsection_width(midsection_count, self.pattern)
        self.offset_left = (self.width - midsection_width) / 2
        self.offset_right = (self.width - midsection_width) / 2
        self.geometry, self.geometry_co = self.construct(self.offset_left, midsection_count, self.pattern)

    def get_midsection_count(self, width, pattern):
        if (isinstance(pattern, PourHolePattern)):
            return 1
        else:
            return floor(width / pattern.width)

    def get_midsection_width(self, midsection_count, pattern):
        if (isinstance(pattern, PourHolePattern)):
            return pattern.width
        else:
            return pattern.width * midsection_count

    def construct(self, offset_left, midsection_count, pattern):
        tab_verts = []
        tab_verts_co = []
        tab = pattern.getGeometry()
        for n in range(0, midsection_count):
            for i in range(len(tab)):
                if not(tab[i].co.x == 0.5):
                    vi = UVVertex((tab[i].co) + M.Vector((pattern.width * n + offset_left, 0)))
                else:
                    vi = UVVertex((tab[i].co))

                tab_verts.insert(len(tab_verts), vi)
                tab_verts_co.insert(len(tab_verts), vi.co)

        return tab_verts, tab_verts_co

class PourHoleSticker(AbstractStickerConstructor):
    def __init__(self, uvedge):
        AbstractStickerConstructor.__init__(self, uvedge, PourHolePattern(True))

class SawtoothSticker(AbstractStickerConstructor):
    def __init__(self, uvedge, default_width, index, other: UVEdge, thickness_switch, isreversed):
        AbstractStickerConstructor.__init__(self, uvedge, SawtoothPattern(thickness_switch, isreversed))

class PinSticker(AbstractStickerConstructor):
    def __init__(self, uvedge, default_width, index, other: UVEdge, thickness_switch, isreversed):
        AbstractStickerConstructor.__init__(self, uvedge, PinPattern(thickness_switch, isreversed))


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
