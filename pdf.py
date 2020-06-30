import mathutils as M
import os.path as os_path
from itertools import chain, repeat, product, combinations



if __package__ is None or __package__ == '':
    # uses current directory visibility
    import stickers
else:
    # uses current package visibility
    from . import stickers

class PDF:
    """Simple PDF exporter"""

    mm_to_pt = 72 / 25.4
    character_width_packed = {
        191: "'", 222: 'ijl\x82\x91\x92',
        278: '|¦\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !,./:;I[\\]ft\xa0·ÌÍÎÏìíîï',
        333: '()-`r\x84\x88\x8b\x93\x94\x98\x9b¡¨\xad¯²³´¸¹{}', 350: '\x7f\x81\x8d\x8f\x90\x95\x9d', 365: '"ºª*°',
        469: '^', 500: 'Jcksvxyz\x9a\x9eçýÿ', 584: '¶+<=>~¬±×÷', 611: 'FTZ\x8e¿ßø',
        667: '&ABEKPSVXY\x8a\x9fÀÁÂÃÄÅÈÉÊËÝÞ', 722: 'CDHNRUwÇÐÑÙÚÛÜ', 737: '©®', 778: 'GOQÒÓÔÕÖØ', 833: 'Mm¼½¾',
        889: '%æ', 944: 'W\x9c', 1000: '\x85\x89\x8c\x97\x99Æ', 1015: '@', }
    character_width = {c: value for (value, chars) in character_width_packed.items() for c in chars}

    def __init__(self, page_size: M.Vector, style, margin, pure_net=True, angle_epsilon=0):
        self.page_size = page_size
        self.style = style
        self.margin = M.Vector((margin, margin))
        self.pure_net = pure_net
        self.angle_epsilon = angle_epsilon

    def text_width(self, text, scale=None):
        return (scale or self.text_size) * sum(self.character_width.get(c, 556) for c in text) / 1000

    @classmethod
    def encode_image(cls, bpy_image):
        data = bytes(int(255 * px) for (i, px) in enumerate(bpy_image.pixels) if i % 4 != 3)
        image = {
            "Type": "XObject", "Subtype": "Image", "Width": bpy_image.size[0], "Height": bpy_image.size[1],
            "ColorSpace": "DeviceRGB", "BitsPerComponent": 8, "Interpolate": True,
            "Filter": ["ASCII85Decode", "FlateDecode"], "stream": data}
        return image

    def write(self, mesh, filename):
        def format_dict(obj, refs=tuple()):
            return "<< " + "".join(
                "/{} {}\n".format(key, format_value(value, refs)) for (key, value) in obj.items()) + ">>"

        def line_through_simple(seq):

            return "".join(
                "{0.x:.6f} {0.y:.6f} {1} ".format(1000 * v.co, c) for (v, c) in zip(seq, chain("m", repeat("l"))))


        def line_through_sticker(seq):
            lists = list()
            curr = list()
            for point in seq:
                # print(point.co)
                if(point.co.x == 0.5):
                    lists.append(curr)
                    curr = list()
                    # print("DELIM")
                else:
                    curr.append(point)
            lists.append(curr)

            finalstring = ""
            for sublist in lists:
                finalstring +=  "".join(
                    "{0.x:.6f} {0.y:.6f} {1} ".format(1000 * v.co, c) for (v, c) in zip(sublist, chain("m", repeat("l"))))

            return finalstring

        def format_value(value, refs=tuple()):
            if value in refs:
                return "{} 0 R".format(refs.index(value) + 1)
            elif type(value) is dict:
                return format_dict(value, refs)
            elif type(value) in (list, tuple):
                return "[ " + " ".join(format_value(item, refs) for item in value) + " ]"
            elif type(value) is int:
                return str(value)
            elif type(value) is float:
                return "{:.6f}".format(value)
            elif type(value) is bool:
                return "true" if value else "false"
            else:
                return "/{}".format(value)  # this script can output only PDF names, no strings

        def write_object(index, obj, refs, f, stream=None):
            byte_count = f.write("{} 0 obj\n".format(index))
            if type(obj) is not dict:
                stream, obj = obj, dict()
            elif "stream" in obj:
                stream = obj.pop("stream")
            if stream:
                if True or type(stream) is bytes:
                    obj["Filter"] = ["ASCII85Decode", "FlateDecode"]
                    stream = encode(stream)
                obj["Length"] = len(stream)
            byte_count += f.write(format_dict(obj, refs))
            if stream:
                byte_count += f.write("\nstream\n")
                byte_count += f.write(stream)
                byte_count += f.write("\nendstream")
            return byte_count + f.write("\nendobj\n")

        def encode(data):
            from base64 import a85encode
            from zlib import compress
            if hasattr(data, "encode"):
                data = data.encode()
            return a85encode(compress(data), adobe=True, wrapcol=250)[2:].decode()

        page_size_pt = 1000 * self.mm_to_pt * self.page_size
        root = {"Type": "Pages", "MediaBox": [0, 0, page_size_pt.x, page_size_pt.y], "Kids": list()}
        catalog = {"Type": "Catalog", "Pages": root}
        font = {
            "Type": "Font", "Subtype": "Type1", "Name": "F1",
            "BaseFont": "Helvetica", "Encoding": "MacRomanEncoding"}

        dl = [length * self.style.line_width * 1000 for length in (1, 4, 9)]
        format_style = {
            'SOLID': list(), 'DOT': [dl[0], dl[1]], 'DASH': [dl[1], dl[2]],
            'LONGDASH': [dl[2], dl[1]], 'DASHDOT': [dl[2], dl[1], dl[0], dl[1]]}
        styles = {
            "Gtext": {"ca": self.style.text_color[3], "Font": [font, 1000 * self.text_size]},
            "Gsticker": {"ca": self.style.sticker_fill[3]}}
        for name in ("outer", "convex", "concave", "freestyle"):
            gs = {
                "LW": self.style.line_width * 1000 * getattr(self.style, name + "_width"),
                "CA": getattr(self.style, name + "_color")[3],
                "D": [format_style[getattr(self.style, name + "_style")], 0]}
            styles["G" + name] = gs
        for name in ("outbg", "inbg"):
            gs = {
                "LW": self.style.line_width * 1000 * getattr(self.style, name + "_width"),
                "CA": getattr(self.style, name + "_color")[3],
                "D": [format_style['SOLID'], 0]}
            styles["G" + name] = gs

        objects = [root, catalog, font]
        objects.extend(styles.values())

        for page in mesh.pages:
            commands = ["{0:.6f} 0 0 {0:.6f} 0 0 cm".format(self.mm_to_pt)]
            resources = {"Font": {"F1": font}, "ExtGState": styles, "XObject": dict()}
            for island in page.islands:
                commands.append("q 1 0 0 1 {0.x:.6f} {0.y:.6f} cm".format(1000 * (self.margin + island.pos)))
                if island.embedded_image:
                    identifier = "Im{}".format(len(resources["XObject"]) + 1)
                    commands.append(self.command_image.format(1000 * island.bounding_box, identifier))
                    objects.append(island.embedded_image)
                    resources["XObject"][identifier] = island.embedded_image

                if island.title:
                    commands.append(self.command_label.format(
                        size=1000 * self.text_size,
                        x=500 * (island.bounding_box.x - self.text_width(island.title)),
                        y=1000 * 0.2 * self.text_size,
                        label=island.title))

                data_markers, data_stickerfill, data_outer, data_convex, data_concave, data_freestyle = (list() for i in
                                                                                                         range(6))
                for marker in island.markers:
                    if isinstance(marker, stickers.Sticker):
                        data_stickerfill.append(line_through_sticker(marker.vertices))
                        if marker.text:
                            data_markers.append(self.command_sticker.format(
                                label=marker.text,
                                pos=1000 * marker.center,
                                mat=marker.rot,
                                align=-500 * self.text_width(marker.text, marker.width),
                                size=1000 * marker.width))
                    elif isinstance(marker, stickers.PourHole):
                        data_stickerfill.append(line_through_sticker(marker.vertices))
                        if marker.text:
                            data_markers.append(self.command_sticker.format(
                                label=marker.text,
                                pos=1000 * marker.center,
                                mat=marker.rot,
                                align=-500 * self.text_width(marker.text, marker.width),
                                size=1000 * marker.width))
                    elif isinstance(marker, Arrow):
                        size = 1000 * marker.size
                        position = 1000 * (marker.center + marker.size * marker.rot @ M.Vector((0, -0.9)))
                        data_markers.append(self.command_arrow.format(
                            index=marker.text,
                            arrow_pos=1000 * marker.center,
                            pos=position - 1000 * M.Vector((0.5 * self.text_width(marker.text), 0.4 * self.text_size)),
                            mat=size * marker.rot,
                            size=size))
                    elif isinstance(marker, stickers.NumberAlone):
                        data_markers.append(self.command_number.format(
                            label=marker.text,
                            pos=1000 * marker.center,
                            mat=marker.rot,
                            size=1000 * marker.size))

                outer_edges = set(island.boundary)
                while outer_edges:
                    data_loop = list()
                    uvedge = outer_edges.pop()
                    while 1:
                        if uvedge.sticker:
                            data_loop.extend(uvedge.sticker.vertices[1:])
                        elif uvedge.pourhole:
                            data_loop.extend(uvedge.pourhole.vertices[1:])
                        else:
                            vertex = uvedge.vb if uvedge.uvface.flipped else uvedge.va
                            data_loop.append(vertex)
                        uvedge = uvedge.neighbor_right
                        try:
                            outer_edges.remove(uvedge)
                        except KeyError:
                            break
                    data_outer.append(line_through_sticker(data_loop) + "s")

                for loop, uvedge in island.edges.items():
                    edge = mesh.edges[loop.edge]
                    if edge.is_cut(uvedge.uvface.face) and not (uvedge.sticker or uvedge.pourhole):
                        continue
                    data_uvedge = line_through_simple((uvedge.va, uvedge.vb)) + "S"
                    if edge.freestyle:
                        data_freestyle.append(data_uvedge)
                    # each uvedge exists in two opposite-oriented variants; we want to add each only once
                    if uvedge.sticker or uvedge.uvface.flipped != (id(uvedge.va) > id(uvedge.vb)):
                        if edge.angle > self.angle_epsilon:
                            # if(edge.is_kerf):
                                # print("ADDED((((((((((((((((((")
                            data_convex.append(data_uvedge)
                        # elif edge.angle < -self.angle_epsilon:
                        else:
                            # if(edge.is_kerf):
                                # print("ADDED))))))))))))))))))")
                            data_concave.append(data_uvedge)
                if island.is_inside_out:
                    data_convex, data_concave = data_concave, data_convex

                if data_stickerfill and self.style.sticker_fill[3] > 0:
                    commands.append("/Gsticker gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} rg".format(self.style.sticker_fill))
                    commands.extend(data_stickerfill)
                if data_freestyle:
                    commands.append(
                        "/Gfreestyle gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} RG".format(self.style.freestyle_color))
                    commands.extend(data_freestyle)
                if (data_convex or data_concave) and not self.pure_net and self.style.use_inbg:
                    commands.append("/Ginbg gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} RG".format(self.style.inbg_color))
                    commands.extend(chain(data_convex, data_concave))
                if data_convex:
                    commands.append("/Gconvex gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} RG".format(self.style.convex_color))
                    commands.extend(data_convex)
                if data_concave:
                    commands.append("/Gconcave gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} RG".format(self.style.concave_color))
                    commands.extend(data_concave)
                if data_outer:
                    if not self.pure_net and self.style.use_outbg:
                        commands.append("/Goutbg gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} RG".format(self.style.outbg_color))
                        commands.extend(data_outer)
                    commands.append("/Gouter gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} RG".format(self.style.outer_color))
                    commands.extend(data_outer)
                commands.append("/Gtext gs {0[0]:.3f} {0[1]:.3f} {0[2]:.3f} rg".format(self.style.text_color))
                commands.extend(data_markers)
                commands.append("Q")
            content = "\n".join(commands)
            page = {"Type": "Page", "Parent": root, "Contents": content, "Resources": resources}
            root["Kids"].append(page)
            objects.extend((page, content))

        root["Count"] = len(root["Kids"])
        with open(filename, "w+") as f:
            xref_table = list()
            position = f.write("%PDF-1.4\n")
            for index, obj in enumerate(objects, 1):
                xref_table.append(position)
                position += write_object(index, obj, objects, f)
            xref_pos = position
            f.write("xref_table\n0 {}\n".format(len(xref_table) + 1))
            f.write("{:010} {:05} f\n".format(0, 65536))
            for position in xref_table:
                f.write("{:010} {:05} n\n".format(position, 0))
            f.write("trailer\n")
            f.write(format_dict({"Size": len(xref_table), "Root": catalog}, objects))
            f.write("\nstartxref\n{}\n%%EOF\n".format(xref_pos))

    command_label = "/Gtext gs BT {x:.6f} {y:.6f} Td ({label}) Tj ET"
    command_image = "q {0.x:.6f} 0 0 {0.y:.6f} 0 0 cm 1 0 0 -1 0 1 cm /{1} Do Q"
    command_sticker = "q {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {pos.x:.6f} {pos.y:.6f} cm BT {align:.6f} 0 Td /F1 {size:.6f} Tf ({label}) Tj ET Q"
    command_arrow = "q BT {pos.x:.6f} {pos.y:.6f} Td /F1 {size:.6f} Tf ({index}) Tj ET {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {arrow_pos.x:.6f} {arrow_pos.y:.6f} cm 0 0 m 1 -1 l 0 -0.25 l -1 -1 l f Q"
    command_number = "q {mat[0][0]:.6f} {mat[1][0]:.6f} {mat[0][1]:.6f} {mat[1][1]:.6f} {pos.x:.6f} {pos.y:.6f} cm BT /F1 {size:.6f} Tf ({label}) Tj ET Q"

