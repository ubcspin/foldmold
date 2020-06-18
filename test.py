import functools 
import unittest

## Fundamental stickers
class AbstractSticker:
    __slots__ = ("geometry", "width", "filename")
    def __init__(self, filename, width):
        self.filename = filename
        self.width = width
        self.geometry = self.load_geometry(filename)

    def load_geometry(self, filename):
        # s = Stickers()
        return filename

    def getWidth(self):
        return self.width


class Tooth(AbstractSticker):
    def __init__(self):
        AbstractSticker.__init__(self, "tooth.svg", 0.005)

class Gap(AbstractSticker):
    def __init__(self):
        AbstractSticker.__init__(self, "gap.svg", 0.003)

class Hole(AbstractSticker):
    def __init__(self):
        AbstractSticker.__init__(self, "hole.svg", 0.003)

class PourHoleTile(AbstractSticker):
    def __init__(self):
        AbstractSticker.__init__(self, "pourhole.svg", 0.003)

class Connector(AbstractSticker):
    def __init__(self):
        AbstractSticker.__init__(self, "gap2.svg", 0.003)

class Pin(AbstractSticker):
    def __init__(self):
        AbstractSticker.__init__(self, "pin.svg", 0.003)

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
    def __init__(self, isreversed):
        AbstractPattern.__init__(self, isreversed, [Gap(), Tooth()], [Tooth(), Gap()])

class PinPattern(AbstractPattern):
    def __init__(self, isreversed):
        AbstractPattern.__init__(self, isreversed, [Hole(), Connector()], [Pin(), Gap()])

class PourHolePattern(AbstractPattern):
    def __init__(self, isreversed):
        AbstractPattern.__init__(self, isreversed, [PourHoleTile()], [PourHoleTile()])


## Unit tests
class TestTileMethods(unittest.TestCase):
    def test_widths(self):
        t = Tooth()
        g = Gap()
        h = Hole()
        p = PourHoleTile()
        c = Connector()
        i = Pin()
        sp = SawtoothPattern(True)
        pp = PinPattern(True)
        php = PourHolePattern(True)

        self.assertEqual(t.width, .005)
        self.assertEqual(g.width, .003)
        self.assertEqual(h.width, .003)
        self.assertEqual(p.width, .003)
        self.assertEqual(c.width, .003)
        self.assertEqual(i.width, .003)
        self.assertEqual(sp.width, .008)
        self.assertEqual(pp.width, .006)
        self.assertEqual(php.width, .003)

    def test_reversals(self):
        sp = SawtoothPattern(True)
        self.assertTrue(sp.isreversed == True)
        self.assertTrue(isinstance(sp.tileset[0], Gap))
        self.assertTrue(isinstance(sp.tileset[1], Tooth))

        sp = SawtoothPattern(False)
        self.assertTrue(sp.isreversed == False)
        self.assertTrue(isinstance(sp.tileset[0], Tooth))
        self.assertTrue(isinstance(sp.tileset[1], Gap))

if __name__ == '__main__':
    unittest.main()

