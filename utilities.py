import mathutils as M
from math import pi, ceil, asin, atan2, floor
import bpy

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

    def cage_fit(self, points, aspect):
        """Find rotation for a minimum bounding box with a given aspect ratio
        returns a tuple: rotation angle, box height"""

        def guesses(polygon):
            """Yield all tentative extrema of the bounding box height wrt. polygon rotation"""
            for a, b in self.pairs(polygon):
                if a == b:
                    continue
                direction = (b - a).normalized()
                sinx, cosx = -direction.y, direction.x
                rot = M.Matrix(((cosx, -sinx), (sinx, cosx)))
                rot_polygon = [rot @ p for p in polygon]
                left, right = [fn(rot_polygon, key=lambda p: p.to_tuple()) for fn in (min, max)]
                bottom, top = [fn(rot_polygon, key=lambda p: p.yx.to_tuple()) for fn in (min, max)]
                # print(f"{rot_polygon.index(left)}-{rot_polygon.index(right)}, {rot_polygon.index(bottom)}-{rot_polygon.index(top)}")
                horz, vert = right - left, top - bottom
                # solve (rot * a).y == (rot * b).y
                yield max(aspect * horz.x, vert.y), sinx, cosx
                # solve (rot * a).x == (rot * b).x
                yield max(horz.x, aspect * vert.y), -cosx, sinx
                # solve aspect * (rot * (right - left)).x == (rot * (top - bottom)).y
                # using substitution t = tan(rot / 2)
                q = aspect * horz.x - vert.y
                r = vert.x + aspect * horz.y
                t = ((r ** 2 + q ** 2) ** 0.5 - r) / q if q != 0 else 0
                t = -1 / t if abs(t) > 1 else t  # pick the positive solution
                siny, cosy = 2 * t / (1 + t ** 2), (1 - t ** 2) / (1 + t ** 2)
                rot = M.Matrix(((cosy, -siny), (siny, cosy)))
                for p in rot_polygon:
                    p[:] = rot @ p  # note: this also modifies left, right, bottom, top
                # print(f"solve {aspect * (right - left).x} == {(top - bottom).y} with aspect = {aspect}")
                if left.x < right.x and bottom.y < top.y and all(
                        left.x <= p.x <= right.x and bottom.y <= p.y <= top.y for p in rot_polygon):
                    # print(f"yield {max(aspect * (right - left).x, (top - bottom).y)}")
                    yield max(aspect * (right - left).x,
                              (top - bottom).y), sinx * cosy + cosx * siny, cosx * cosy - sinx * siny

        polygon = [points[i] for i in M.geometry.convex_hull_2d(points)]
        height, sinx, cosx = min(guesses(polygon))
        return atan2(sinx, cosx), height


    def create_blank_image(self, image_name, dimensions, alpha=1):
        """Create a new image and assign white color to all its pixels"""
        image_name = image_name[:64]
        width, height = int(dimensions.x), int(dimensions.y)
        image = bpy.data.images.new(image_name, width, height, alpha=True)
        if image.users > 0:
            raise UnfoldError(
                "There is something wrong with the material of the model. "
                "Please report this on the BlenderArtists forum. Export failed.")
        image.pixels = [1, 1, 1, alpha] * (width * height)
        image.file_format = 'PNG'
        return image

    
    



    def hello(self, hi):
        print("Hi w %s" % hi)