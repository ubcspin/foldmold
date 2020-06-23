# import stickers
import bpy





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

