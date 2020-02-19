import logging
from lxml import etree
import re

the_path = "/Users/bucci/Google Drive/UBC/SPIN/Touch Sensor Team/UIST\'20/Stickers/tooth-pulltab.svg"
logger = logging.getLogger(__name__)
ns = {"u": "http://www.w3.org/2000/svg"}


def load_svg(path):
    parser = etree.XMLParser(remove_comments=True, recover=True)
    try:
        doc = etree.parse(path, parser=parser)
        svg_root = doc.getroot()
    except Exception as exc:
        logger.error("Failed to load input file! (%s)" % exc)
    else:
        return svg_root


def svg2uv(path):
    svg_root = load_svg(path)
    if svg_root is None:
        print("SVG import blowed up, no root!")
        return

    polylines = svg_root.findall("u:polyline", ns)
    paths = svg_root.findall("u:path", ns)

    # Make Polyline Vectors
    polyline_vectors = []

    for p in polylines:
        points = p.attrib['points']
        polyline_vectors += vectorize_polylines(points)
    for v in polyline_vectors:
        makeUVvector(v)
    # Make Path vectors
    path_vectors = []
    for p in paths:
        path = p.attrib['d']
        path_vectors += vectorize_paths(path)


def vectorize_paths(path):
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


def vectorize_polylines(points):
    ps = points.split()
    xs = ps[0::2]  # every second element starting at 0
    ys = ps[1::2]  # every second element starting at 1
    lines = []

    for i in range(0, len(xs) - 1):
        x1 = float(xs[i])
        y1 = float(ys[i])
        x2 = float(xs[i + 1])
        y2 = float(ys[i + 1])
        # fs = [float(i) for i in [x1,y1,x2,y2]]
        o = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
        lines.append(o)
    return lines


def makeUVvector(v):
    # TODO: fill in UV creation here
    print("this line goes from point [%d, %d] to point [%d, %d]" % (v["x1"], v["y1"], v["x2"], v["y2"]))


# svg2uv(the_path)