# import stickers
import bpy

class AbstractStickerConstructor:
    __slots__ = ('bounds', 'center', 'rot', 'text', 'width', 'vertices', "pattern", "geometry", "geometry_co", "offset_left", "offset_right")
    def __init__(self, uvedge, pattern):
        first_vertex, second_vertex = (uvedge.va, uvedge.vb) if not uvedge.uvface.flipped else (uvedge.vb, uvedge.va)
        edge = first_vertex.co - second_vertex.co
        self.width = edge.length
        self.offset_left = (self.width - midsection_width) / 2
        self.offset_right = (self.width - midsection_width) / 2
        self.pattern = pattern
        self.geometry, self.geometry_co = self.construct(self.offset_left, midsection_count, self.pattern)


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

class PourHoleSticker(AbstractStickerConstructor):
    def __init__(self, uvedge):
        midsection_count = 1
        midsection_width = self.pattern.width * midsection_count
        AbstractStickerConstructor.__init__(self, uvedge, PourHolePattern(True))

class SawtoothSticker(AbstractStickerConstructor):
    def __init__(self, uvedge, default_width, index, other: UVEdge, isreversed):
        midsection_count = floor(self.width / self.pattern.width)
        midsection_width = self.pattern.width * midsection_count
        AbstractStickerConstructor.__init__(self, uvedge, SawtoothPattern(isreversed))

class PinSticker:
    def __init__(self, uvedge, default_width, index, other: UVEdge, isreversed):
        midsection_count = floor(self.width / self.pattern.width)
        midsection_width = self.pattern.width * midsection_count
        AbstractStickerConstructor.__init__(self, uvedge, PinPattern(isreversed))



# import functools 
# import unittest
# import svglib
# import bpy
# from lxml import etree
# import stickers

# class StickerHandler:
#     __instance = None
#     @staticmethod 
#     def getInstance():
#         """ Static access method. """
#         if StickerHandler.__instance == None:
#             StickerHandler()
#         return StickerHandler.__instance
#     def __init__(self):
#         """ Virtually private constructor. """
#         if StickerHandler.__instance != None:
#             raise Exception("This class is a singleton! You only want one StickerHandler.")
#         else:
#             StickerHandler.__instance = self

#     # self.pin_edges = []
#     # self.sawtooth_edges = []
#     # self.glue_edges = []

# ## Unit tests
# class TestTileMethods(unittest.TestCase):
#     def test_widths(self):

#         t = stickers.Tooth()
#         g = stickers.Gap()
#         h = stickers.Hole()
#         p = stickers.PourHoleTile()
#         c = stickers.Connector()
#         i = stickers.Pin()
#         sp = stickers.SawtoothPattern(True)
#         pp = stickers.PinPattern(True)
#         php = stickers.PourHolePattern(True)

#         self.assertEqual(t.width, .005)
#         self.assertEqual(g.width, .003)
#         self.assertEqual(h.width, .003)
#         self.assertEqual(p.width, .003)
#         self.assertEqual(c.width, .003)
#         self.assertEqual(i.width, .003)
#         self.assertEqual(sp.width, .008)
#         self.assertEqual(pp.width, .006)
#         self.assertEqual(php.width, .003)

#     def test_reversals(self):
#         sp = stickers.SawtoothPattern(True)
#         self.assertTrue(sp.isreversed == True)
#         self.assertTrue(isinstance(sp.tileset[0], Gap))
#         self.assertTrue(isinstance(sp.tileset[1], Tooth))

#         sp = stickers.SawtoothPattern(False)
#         self.assertTrue(sp.isreversed == False)
#         self.assertTrue(isinstance(sp.tileset[0], Tooth))
#         self.assertTrue(isinstance(sp.tileset[1], Gap))

#     def test_singleton(self):
#         s = StickerHandler()
#         s1 = StickerHandler.getInstance()
#         s2 = StickerHandler.getInstance()
#         self.assertEqual(s1, s2)


# if __name__ == '__main__':
#     unittest.main()

