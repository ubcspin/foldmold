import mathutils as M

class Utilities:
    def __init__(self):
        print("Initiated utilities.")

    def first_letters(self, text):
        """Iterator over the first letter of each word"""
        first_letters.pattern = re_compile("((?<!\w)\w)|\d")
        for match in first_letters.pattern.finditer(text):
            yield text[match.start()]
        


    def is_upsidedown_wrong(self, name):
        """Tell if the string would get a different meaning if written upside down"""
        chars = set(name)
        mistakable = set("69NZMWpbqd")
        rotatable = set("80oOxXIl").union(mistakable)
        print("is_upsidedown_wrong worked")
        return chars.issubset(rotatable) and not chars.isdisjoint(mistakable)



    def pairs(self, sequence):
        """Generate consecutive pairs throughout the given sequence; at last, it gives elements last, first."""
        i = iter(sequence)
        previous = first = next(i)
        for this in i:
            yield previous, this
            previous = this
        yield this, first    


    def fitting_matrix(self, v1, v2):
        """Get a matrix that rotates v1 to the same direction as v2"""
        return (1 / v1.length_squared) * M.Matrix((
            (v1.x * v2.x + v1.y * v2.y, v1.y * v2.x - v1.x * v2.y),
            (v1.x * v2.y - v1.y * v2.x, v1.x * v2.x + v1.y * v2.y)))


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


    def hello(self, hi):
        print("Hi w %s" % hi)