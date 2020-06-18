import svglib
from lxml import etree
import logging
import mathutils as M
import os.path as os_path

import sys




class Stickers:
    def __init__(self):
        self.vertices = []

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

    def svg2uv(self, path):
        ns = {"u": "http://www.w3.org/2000/svg"}
        self.vertices.clear()
        svg_root = self.load_svg(path)
        if svg_root is None:
            print("SVG import blowed up, no root!")
            return

        polylines = svg_root.findall("u:polyline", ns)
        paths = svg_root.findall("u:path", ns)

        # Make Polyline Vectors
        polyline_vectors = []

        for p in polylines:
            points = p.attrib['points']
            points += " 0.5,0.5"
            polyline_vectors += self.vectorize_polylines(points)
            # polyline_vectors += vectorize_polylines("600,600") #delimiter
        for v in polyline_vectors:
            self.makeUVVertices(v)

        # Make Path vectors
        path_vectors = []
        for p in paths:
            path = p.attrib['d']
            path_vectors += self.vectorize_paths(path)
        return self.vertices.copy()



    def vectorize_paths(self, path):
        # "M0,0H250V395.28a104.71,104.71,0,0,0,11.06,46.83h0A104.71,104.71,0,0,0,354.72,500h40.56a104.71,104.71,0,0,0,93.66-57.89h0A104.71,104.71,0,0,0,500,395.28V0"
        r = re.compile('[MmHhAaVv][\d,\.-]*')  # split by commands
        p = re.sub(r'-', r',-', path)  # make sure to catch negatives
        commands = r.findall(p)
        for c in commands:
            command = c[0]
            parameters = [float(i) for i in c[1:].split(",")]
            print(command, parameters)

        print(commands)
        return []


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


    def makeUVVertices(self, v):
        if not (v["x1"] == 0.5):
            v1 = self.UVVertex(M.Vector((v["x1"], v["y1"])) * 0.00001)  # scaling down to avoid overflow
        else:
            v1 = self.UVVertex(M.Vector((v["x1"], v["y1"]))  )  # scaling down to avoid overflow

        self.vertices.append(v1)

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

