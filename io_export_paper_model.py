# -*- coding: utf-8 -*-
# This script is Free software. Please share and reuse.
# ♡2010-2019 Adam Dominec <adominec@gmail.com>

## Code structure
# This file consists of several components, in this order:
# * Unfolding and baking
# * Export (SVG or PDF)
# * User interface
# During the unfold process, the mesh is mirrored into a 2D structure: UVFace, UVEdge, stickers.UVVertex.

# bl_info = {
#     "name": "Export Paper Model",
#     "author": "Addam Dominec",
#     "version": (1, 1),
#     "blender": (2, 80, 0),
#     "location": "File > Export > Paper Model",
#     "warning": "",
#     "description": "Export printable net of the active mesh",
#     "category": "Import-Export",
#     "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
#                 "Scripts/Import-Export/Paper_Model"
# }

# Task: split into four files (SVG and PDF separately)
# does any portion of baking belong into the export module?
# sketch out the code for GCODE and two-sided export

# TODO:
# sanitize the constructors Edge, Face, UVFace so that they don't edit their parent object
# The Exporter classes should take parameters as a whole pack, and parse it themselves
# remember objects selected before baking (except selected to active)
# add 'estimated number of pages' to the export UI
# QuickSweepline is very much broken -- it throws GeometryError for all nets > ~15 faces
# rotate islands to minimize area -- and change that only if necessary to fill the page size
# Sticker.vertices should be of type Vector

# check conflicts in island naming and either:
#  * append a number to the conflicting names or
#  * enumerate faces uniquely within all islands of the same name (requires a check that both label and abbr. equals)

import copy
import bpy
import bl_operators
import bmesh
import mathutils as M
from re import compile as re_compile
from itertools import chain, repeat, product, combinations
from math import pi, ceil, asin, atan2, floor
import os.path as os_path
import sys
import re

from . import utilities
u = utilities.Utilities()

from . import stickers
s = stickers.Stickers()

from . import svg
from . import pdf
from . import mesh

default_priority_effect = {
    'CONVEX': 0.5,
    'CONCAVE': 1,
    'LENGTH': -0.05
}

global_paper_sizes = [
    ('USER', "User defined", "User defined paper size"),
    ('A4', "A4", "International standard paper size"),
    ('A3', "A3", "International standard paper size"),
    ('US_LETTER', "Letter", "North American paper size"),
    ('US_LEGAL', "Legal", "North American paper size")
]


class UnfoldError(ValueError):
    def mesh_select(self):
        if len(self.args) > 1:
            elems, bm = self.args[1:3]
            bpy.context.tool_settings.mesh_select_mode = [bool(elems[key]) for key in ("verts", "edges", "faces")]
            for elem in chain(bm.verts, bm.edges, bm.faces):
                elem.select = False
            for elem in chain(*elems.values()):
                elem.select_set(True)
            bmesh.update_edit_mesh(bpy.context.object.data, False, False)


class Unfolder:
    def __init__(self, ob):
        global s
        self.do_create_uvmap = False
        bm = bmesh.from_edit_mesh(ob.data)
        self.mesh = mesh.Mesh(bm, ob.matrix_world, s)
        self.mesh.check_correct()

    def __del__(self):
        if not self.do_create_uvmap:
            self.mesh.delete_uvmap()

    def prepare(self, cage_size=None, priority_effect=default_priority_effect, scale=1, limit_by_page=False):
        """Create the islands of the net"""
        self.mesh.generate_cuts(cage_size / scale if limit_by_page and cage_size else None, priority_effect)
        self.mesh.finalize_islands(cage_size or M.Vector((1, 1)))
        self.mesh.enumerate_islands()
        self.mesh.save_uv()

    def copy_island_names(self, island_list):
        """Copy island label and abbreviation from the best matching island in the list"""
        orig_islands = [{face.id for face in item.faces} for item in island_list]
        matching = list()
        for i, island in enumerate(self.mesh.islands):
            islfaces = {face.index for face in island.faces}
            matching.extend((len(islfaces.intersection(item)), i, j) for j, item in enumerate(orig_islands))
        matching.sort(reverse=True)
        available_new = [True for island in self.mesh.islands]
        available_orig = [True for item in island_list]
        for face_count, i, j in matching:
            if available_new[i] and available_orig[j]:
                available_new[i] = available_orig[j] = False
                self.mesh.islands[i].label = island_list[j].label
                self.mesh.islands[i].abbreviation = island_list[j].abbreviation

    def save(self, properties):
        """Export the document"""
        # Note about scale: input is directly in blender length
        # Mesh.scale_islands multiplies everything by a user-defined ratio
        # exporters (SVG or PDF) multiply everything by 1000 (output in millimeters)
        Exporter = svg.SVG if properties.file_format == 'SVG' else pdf.PDF
        filepath = properties.filepath
        extension = properties.file_format.lower()
        filepath = bpy.path.ensure_ext(filepath, "." + extension)
        # page size in meters
        page_size = M.Vector((properties.output_size_x, properties.output_size_y))
        # printable area size in meters
        printable_size = page_size - 2 * properties.output_margin * M.Vector((1, 1))
        unit_scale = bpy.context.scene.unit_settings.scale_length
        ppm = properties.output_dpi * 100 / 2.54  # pixels per meter

        # after this call, all dimensions will be in meters
        self.mesh.scale_islands(unit_scale / properties.scale)
        if properties.do_create_stickers:
            self.mesh.generate_stickers(properties.sticker_width, properties.do_create_numbers)
        # elif properties.do_create_numbers:
        #     self.mesh.generate_numbers_alone(properties.sticker_width)
        #
        text_height = properties.sticker_width if (properties.do_create_numbers and len(self.mesh.islands) > 1) else 0
        # title height must be somewhat larger that text size, glyphs go below the baseline
        self.mesh.finalize_islands(printable_size, title_height=text_height * 1.2)
        self.mesh.fit_islands(printable_size)

        if properties.output_type != 'NONE':
            # bake an image and save it as a PNG to disk or into memory
            image_packing = properties.image_packing if properties.file_format == 'SVG' else 'ISLAND_EMBED'
            use_separate_images = image_packing in ('ISLAND_LINK', 'ISLAND_EMBED')
            self.mesh.save_uv(cage_size=printable_size, separate_image=use_separate_images)

            sce = bpy.context.scene
            rd = sce.render
            bk = rd.bake
            # TODO: do we really need all this recollection?
            recall = rd.engine, sce.cycles.bake_type, sce.cycles.samples, bk.use_selected_to_active, bk.margin, bk.cage_extrusion, bk.use_cage, bk.use_clear
            rd.engine = 'CYCLES'
            recall_pass = {p: getattr(bk, f"use_pass_{p}") for p in (
            'ambient_occlusion', 'color', 'diffuse', 'direct', 'emit', 'glossy', 'indirect', 'subsurface',
            'transmission')}
            for p in recall_pass:
                setattr(bk, f"use_pass_{p}", (properties.output_type != 'TEXTURE'))
            lookup = {'TEXTURE': 'DIFFUSE', 'AMBIENT_OCCLUSION': 'AO', 'RENDER': 'COMBINED',
                      'SELECTED_TO_ACTIVE': 'COMBINED'}
            sce.cycles.bake_type = lookup[properties.output_type]
            bk.use_selected_to_active = (properties.output_type == 'SELECTED_TO_ACTIVE')
            bk.margin, bk.cage_extrusion, bk.use_cage, bk.use_clear = 1, 10, False, False
            if properties.output_type == 'TEXTURE':
                bk.use_pass_direct, bk.use_pass_indirect, bk.use_pass_color = False, False, True
                sce.cycles.samples = 1
            else:
                sce.cycles.samples = properties.bake_samples
            if sce.cycles.bake_type == 'COMBINED':
                bk.use_pass_direct, bk.use_pass_indirect = True, True
                bk.use_pass_diffuse, bk.use_pass_glossy, bk.use_pass_transmission, bk.use_pass_subsurface, bk.use_pass_ambient_occlusion, bk.use_pass_emit = True, False, False, True, True, True

            if image_packing == 'PAGE_LINK':
                self.mesh.save_image(printable_size * ppm, filepath)
            elif image_packing == 'ISLAND_LINK':
                image_dir = filepath[:filepath.rfind(".")]
                self.mesh.save_separate_images(ppm, image_dir)
            elif image_packing == 'ISLAND_EMBED':
                self.mesh.save_separate_images(ppm, filepath, embed=Exporter.encode_image)

            rd.engine, sce.cycles.bake_type, sce.cycles.samples, bk.use_selected_to_active, bk.margin, bk.cage_extrusion, bk.use_cage, bk.use_clear = recall
            for p, v in recall_pass.items():
                setattr(bk, f"use_pass_{p}", v)

        exporter = Exporter(page_size, properties.style, properties.output_margin, (properties.output_type == 'NONE'),
                            properties.angle_epsilon)
        # exporter.do_create_stickers = properties.do_create_stickers
        exporter.text_size = properties.sticker_width
        exporter.write(self.mesh, filepath)


class Arrow:
    """Mark in the document: an arrow denoting the number of the edge it points to"""
    __slots__ = ('bounds', 'center', 'rot', 'text', 'size')

    def __init__(self, uvedge, size, index):
        self.text = str(index)
        edge = (uvedge.vb.co - uvedge.va.co) if not uvedge.uvface.flipped else (uvedge.va.co - uvedge.vb.co)
        self.center = (uvedge.va.co + uvedge.vb.co) / 2
        self.size = size
        tangent = edge.normalized()
        cos, sin = tangent
        self.rot = M.Matrix(((cos, -sin), (sin, cos)))
        normal = M.Vector((sin, -cos))
        self.bounds = [self.center, self.center + (1.2 * normal + tangent) * size,
                       self.center + (1.2 * normal - tangent) * size]


# /////////////////////////////////////////////////////////////////////////////////////////////////////////////

    # print("this line goes from point [%d, %d] to point [%d, %d]" % (v["x1"], v["y1"], v["x2"], v["y2"]))

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////






class Unfold(bpy.types.Operator):
    """Blender Operator: unfold the selected object."""

    bl_idname = "mesh.unfold"
    bl_label = "Unfold"
    bl_description = "Mark seams so that the mesh can be exported as a paper model"
    bl_options = {'REGISTER', 'UNDO'}
    edit: bpy.props.BoolProperty(default=False, options={'HIDDEN'})
    priority_effect_convex: bpy.props.FloatProperty(
        name="Priority Convex", description="Priority effect for edges in convex angles",
        default=default_priority_effect['CONVEX'], soft_min=-1, soft_max=10, subtype='FACTOR')
    priority_effect_concave: bpy.props.FloatProperty(
        name="Priority Concave", description="Priority effect for edges in concave angles",
        default=default_priority_effect['CONCAVE'], soft_min=-1, soft_max=10, subtype='FACTOR')
    priority_effect_length: bpy.props.FloatProperty(
        name="Priority Length", description="Priority effect of edge length",
        default=default_priority_effect['LENGTH'], soft_min=-10, soft_max=1, subtype='FACTOR')
    do_create_uvmap: bpy.props.BoolProperty(
        name="Create UVMap", description="Create a new UV Map showing the islands and page layout", default=False)
    object = None
    # dropdown_list = bpy.props.EnumProperty(
    #     name="Edge Type",
    #     items=(
    #         ('1', 'Auto', ''),
    #         ('2', 'Pin Join', ''),
    #         ('3', 'Sawtooth Join', ''),
    #         ('4', 'Glue Tab', ''),
    #     ),
    #     update=myindex
    # )
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"


    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.active = not self.object or len(self.object.data.uv_layers) < 8
        col.prop(self.properties, "do_create_uvmap")
        layout.label(text="Edge Cutting Factors:")
        col = layout.column(align=True)
        col.label(text="Face Angle:")
        col.prop(self.properties, "priority_effect_convex", text="Convex")
        col.prop(self.properties, "priority_effect_concave", text="Concave")
        layout.prop(self.properties, "priority_effect_length", text="Edge Length")
        row = layout.row()
        row.prop(context.scene, "dropdown_list")

    def execute(self, context):
        sce = bpy.context.scene
        settings = sce.paper_model
        recall_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        self.object = context.object

        cage_size = M.Vector((settings.output_size_x, settings.output_size_y))
        priority_effect = {
            'CONVEX': self.priority_effect_convex,
            'CONCAVE': self.priority_effect_concave,
            'LENGTH': self.priority_effect_length}
        try:
            unfolder = Unfolder(self.object)
            unfolder.do_create_uvmap = self.do_create_uvmap
            scale = sce.unit_settings.scale_length / settings.scale
            unfolder.prepare(cage_size, priority_effect, scale, settings.limit_by_page)
            unfolder.mesh.mark_cuts()
        except UnfoldError as error:
            self.report(type={'ERROR_INVALID_INPUT'}, message=error.args[0])
            error.mesh_select()
            bpy.ops.object.mode_set(mode=recall_mode)
            return {'CANCELLED'}
        mesh = self.object.data
        mesh.update()
        if mesh.paper_island_list:
            unfolder.copy_island_names(mesh.paper_island_list)
        island_list = mesh.paper_island_list
        attributes = {item.label: (item.abbreviation, item.auto_label, item.auto_abbrev) for item in island_list}
        island_list.clear()  # remove previously defined islands
        for island in unfolder.mesh.islands:
            # add islands to UI list and set default descriptions
            list_item = island_list.add()
            # add faces' IDs to the island
            for face in island.faces:
                lface = list_item.faces.add()
                lface.id = face.index
            list_item["label"] = island.label
            list_item["abbreviation"], list_item["auto_label"], list_item["auto_abbrev"] = attributes.get(
                island.label,
                (island.abbreviation, True, True))
            island_item_changed(list_item, context)
            mesh.paper_island_index = -1

        del unfolder
        bpy.ops.object.mode_set(mode=recall_mode)
        return {'FINISHED'}


class ClearAllSeams(bpy.types.Operator):
    """Blender Operator: clear all seams of the active Mesh and all its unfold data"""

    bl_idname = "mesh.clear_all_seams"
    bl_label = "Clear All Seams"
    bl_description = "Clear all the seams and unfolded islands of the active object"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        ob = context.active_object
        mesh = ob.data

        for edge in mesh.edges:
            edge.use_seam = False
        mesh.paper_island_list.clear()

        return {'FINISHED'}

class ApplyScores(bpy.types.Operator):
    current_score_num = 0
    scoredir = 'x'
    bl_idname = "mesh.apply_scores"
    bl_label = "Apply Scores"
    bl_description = "Apply Scores"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        ob = context.object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        selectedEdges = [e for e in bm.edges if e.select]

        dirlist = []
        scoreedges = []
        for e in selectedEdges:
            diff = e.verts[0].co - e.verts[1].co

            if(self.scoredir == 'x' and abs(diff.x) > abs(diff.y) and abs(diff.x) > abs(diff.z)):
                dirlist.append(e)
            elif(self.scoredir == 'y' and abs(diff.y) > abs(diff.x) and abs(diff.y) > abs(diff.z)):
                dirlist.append(e)
            elif (self.scoredir == 'z' and abs(diff.z) > abs(diff.y) and abs(diff.z) > abs(diff.x)):
                dirlist.append(e)
            else:
                scoreedges.append(e)
        bmesh.ops.subdivide_edges(bm, edges=scoreedges, cuts=self.current_score_num)
        bmesh.update_edit_mesh(me)

        return {'FINISHED'}

class ApplyEdgeType(bpy.types.Operator):
    current_edge = "glue"
    bl_idname = "mesh.apply_edge_type"
    bl_label = "Apply Edge Type"
    bl_description = "Apply Edge Type"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):

        ob = context.object
        # ob.update_from_editmode()  # not available in older versions!
        # selectedEdges= [e for e in ob.data.edges if e.select]



        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        selectedEdges = [e.index for e in bm.edges if e.select]
        selectedEdgesSeams = [e for e in bm.edges if e.select]

        print(len(selectedEdges))
        print(self.current_edge)
        if(self.current_edge == "pin"):
            s.pin_edges.extend(selectedEdges)
        elif(self.current_edge == "tooth"):
            s.sawtooth_edges.extend(selectedEdges)
        elif(self.current_edge == "glue"):
            s.glue_edges.extend(selectedEdges)
        print(s.pin_edges)
        print(s.sawtooth_edges)
        print(s.glue_edges)

        for edge in selectedEdgesSeams:
            edge.seam = True
        bmesh.update_edit_mesh(me)
        return {'FINISHED'}


def page_size_preset_changed(self, context):
    """Update the actual document size to correct values"""
    if hasattr(self, "limit_by_page") and not self.limit_by_page:
        return
    if self.page_size_preset == 'A4':
        self.output_size_x = 0.210
        self.output_size_y = 0.297
    elif self.page_size_preset == 'A3':
        self.output_size_x = 0.297
        self.output_size_y = 0.420
    elif self.page_size_preset == 'US_LETTER':
        self.output_size_x = 0.216
        self.output_size_y = 0.279
    elif self.page_size_preset == 'US_LEGAL':
        self.output_size_x = 0.216
        self.output_size_y = 0.356


class PaperModelStyle(bpy.types.PropertyGroup):
    line_styles = [
        ('SOLID', "Solid (----)", "Solid line"),
        ('DOT', "Dots (. . .)", "Dotted line"),
        ('DASH', "Short Dashes (- - -)", "Solid line"),
        ('LONGDASH', "Long Dashes (-- --)", "Solid line"),
        ('DASHDOT', "Dash-dotted (-- .)", "Solid line")
    ]
    outer_color: bpy.props.FloatVectorProperty(
        name="Outer Lines", description="Color of net outline",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    outer_style: bpy.props.EnumProperty(
        name="Outer Lines Drawing Style", description="Drawing style of net outline",
        default='SOLID', items=line_styles)
    line_width: bpy.props.FloatProperty(
        name="Base Lines Thickness",
        description="Base thickness of net lines, each actual value is a multiple of this length",
        default=1e-4, min=0, soft_max=5e-3, precision=5, step=1e-2, subtype="UNSIGNED", unit="LENGTH")
    outer_width: bpy.props.FloatProperty(
        name="Outer Lines Thickness", description="Relative thickness of net outline",
        default=3, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    use_outbg: bpy.props.BoolProperty(
        name="Highlight Outer Lines", description="Add another line below every line to improve contrast",
        default=True)
    outbg_color: bpy.props.FloatVectorProperty(
        name="Outer Highlight", description="Color of the highlight for outer lines",
        default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    outbg_width: bpy.props.FloatProperty(
        name="Outer Highlight Thickness", description="Relative thickness of the highlighting lines",
        default=5, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')

    convex_color: bpy.props.FloatVectorProperty(
        name="Inner Convex Lines", description="Color of lines to be folded to a convex angle",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    convex_style: bpy.props.EnumProperty(
        name="Convex Lines Drawing Style", description="Drawing style of lines to be folded to a convex angle",
        default='DASH', items=line_styles)
    convex_width: bpy.props.FloatProperty(
        name="Convex Lines Thickness", description="Relative thickness of concave lines",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    concave_color: bpy.props.FloatVectorProperty(
        name="Inner Concave Lines", description="Color of lines to be folded to a concave angle",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    concave_style: bpy.props.EnumProperty(
        name="Concave Lines Drawing Style", description="Drawing style of lines to be folded to a concave angle",
        default='DASHDOT', items=line_styles)
    concave_width: bpy.props.FloatProperty(
        name="Concave Lines Thickness", description="Relative thickness of concave lines",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    freestyle_color: bpy.props.FloatVectorProperty(
        name="Freestyle Edges", description="Color of lines marked as Freestyle Edge",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    freestyle_style: bpy.props.EnumProperty(
        name="Freestyle Edges Drawing Style", description="Drawing style of Freestyle Edges",
        default='SOLID', items=line_styles)
    freestyle_width: bpy.props.FloatProperty(
        name="Freestyle Edges Thickness", description="Relative thickness of Freestyle edges",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')
    use_inbg: bpy.props.BoolProperty(
        name="Highlight Inner Lines", description="Add another line below every line to improve contrast",
        default=True)
    inbg_color: bpy.props.FloatVectorProperty(
        name="Inner Highlight", description="Color of the highlight for inner lines",
        default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, subtype='COLOR', size=4)
    inbg_width: bpy.props.FloatProperty(
        name="Inner Highlight Thickness", description="Relative thickness of the highlighting lines",
        default=2, min=0, soft_max=10, precision=1, step=10, subtype='FACTOR')

    sticker_fill: bpy.props.FloatVectorProperty(
        name="Tabs Fill", description="Fill color of sticking tabs",
        default=(0.9, 0.9, 0.9, 1.0), min=0, max=1, subtype='COLOR', size=4)
    text_color: bpy.props.FloatVectorProperty(
        name="Text Color", description="Color of all text used in the document",
        default=(0.0, 0.0, 0.0, 1.0), min=0, max=1, subtype='COLOR', size=4)


bpy.utils.register_class(PaperModelStyle)


class ExportPaperModel(bpy.types.Operator):
    """Blender Operator: save the selected object's net and optionally bake its texture"""

    bl_idname = "export_mesh.paper_model"
    bl_label = "Export Paper Model"
    bl_description = "Export the selected object's net and optionally bake its texture"
    filepath: bpy.props.StringProperty(
        name="File Path", description="Target file to save the SVG", options={'SKIP_SAVE'})
    filename: bpy.props.StringProperty(
        name="File Name", description="Name of the file", options={'SKIP_SAVE'})
    directory: bpy.props.StringProperty(
        name="Directory", description="Directory of the file", options={'SKIP_SAVE'})
    page_size_preset: bpy.props.EnumProperty(
        name="Page Size", description="Size of the exported document",
        default='A4', update=page_size_preset_changed, items=global_paper_sizes)
    output_size_x: bpy.props.FloatProperty(
        name="Page Width", description="Width of the exported document",
        default=0.210, soft_min=0.105, soft_max=0.841, subtype="UNSIGNED", unit="LENGTH")
    output_size_y: bpy.props.FloatProperty(
        name="Page Height", description="Height of the exported document",
        default=0.297, soft_min=0.148, soft_max=1.189, subtype="UNSIGNED", unit="LENGTH")
    output_margin: bpy.props.FloatProperty(
        name="Page Margin", description="Distance from page borders to the printable area",
        default=0.005, min=0, soft_max=0.1, step=0.1, subtype="UNSIGNED", unit="LENGTH")
    output_type: bpy.props.EnumProperty(
        name="Textures", description="Source of a texture for the model",
        default='NONE', items=[
            ('NONE', "No Texture", "Export the net only"),
            ('TEXTURE', "From Materials", "Render the diffuse color and all painted textures"),
            ('AMBIENT_OCCLUSION', "Ambient Occlusion", "Render the Ambient Occlusion pass"),
            ('RENDER', "Full Render", "Render the material in actual scene illumination"),
            ('SELECTED_TO_ACTIVE', "Selected to Active", "Render all selected surrounding objects as a texture")
        ])
    do_create_stickers: bpy.props.BoolProperty(
        name="Create Tabs", description="Create gluing tabs around the net (useful for paper)",
        default=True)
    do_create_numbers: bpy.props.BoolProperty(
        name="Create Numbers", description="Enumerate edges to make it clear which edges should be sticked together",
        default=True)
    sticker_width: bpy.props.FloatProperty(
        name="Tabs and Text Size", description="Width of gluing tabs and their numbers",
        default=0.005, soft_min=0, soft_max=0.05, step=0.1, subtype="UNSIGNED", unit="LENGTH")
    angle_epsilon: bpy.props.FloatProperty(
        name="Hidden Edge Angle", description="Folds with angle below this limit will not be drawn",
        default=pi / 360, min=0, soft_max=pi / 4, step=0.01, subtype="ANGLE", unit="ROTATION")
    output_dpi: bpy.props.FloatProperty(
        name="Resolution (DPI)", description="Resolution of images in pixels per inch",
        default=90, min=1, soft_min=30, soft_max=600, subtype="UNSIGNED")
    bake_samples: bpy.props.IntProperty(
        name="Samples", description="Number of samples to render for each pixel",
        default=64, min=1, subtype="UNSIGNED")
    file_format: bpy.props.EnumProperty(
        name="Document Format", description="File format of the exported net",
        default='PDF', items=[
            ('PDF', "PDF", "Adobe Portable Document Format 1.4"),
            ('SVG', "SVG", "W3C Scalable Vector Graphics"),
        ])
    image_packing: bpy.props.EnumProperty(
        name="Image Packing Method", description="Method of attaching baked image(s) to the SVG",
        default='ISLAND_EMBED', items=[
            ('PAGE_LINK', "Single Linked", "Bake one image per page of output and save it separately"),
            ('ISLAND_LINK', "Linked", "Bake images separately for each island and save them in a directory"),
            ('ISLAND_EMBED', "Embedded", "Bake images separately for each island and embed them into the SVG")
        ])
    scale: bpy.props.FloatProperty(
        name="Scale", description="Divisor of all dimensions when exporting",
        default=1, soft_min=1.0, soft_max=100.0, subtype='FACTOR', precision=1)
    do_create_uvmap: bpy.props.BoolProperty(
        name="Create UVMap", description="Create a new UV Map showing the islands and page layout",
        default=False, options={'SKIP_SAVE'})
    ui_expanded_document: bpy.props.BoolProperty(
        name="Show Document Settings Expanded",
        description="Shows the box 'Document Settings' expanded in user interface",
        default=True, options={'SKIP_SAVE'})
    ui_expanded_style: bpy.props.BoolProperty(
        name="Show Style Settings Expanded", description="Shows the box 'Colors and Style' expanded in user interface",
        default=False, options={'SKIP_SAVE'})
    style: bpy.props.PointerProperty(type=PaperModelStyle)

    unfolder = None

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def prepare(self, context):
        sce = context.scene
        self.recall_mode = context.object.mode
        bpy.ops.object.mode_set(mode='EDIT')

        self.object = context.active_object
        self.unfolder = Unfolder(self.object)
        cage_size = M.Vector((sce.paper_model.output_size_x, sce.paper_model.output_size_y))
        self.unfolder.prepare(cage_size, scale=sce.unit_settings.scale_length / self.scale,
                              limit_by_page=sce.paper_model.limit_by_page)
        if self.scale == 1:
            self.scale = ceil(self.get_scale_ratio(sce))

    def recall(self):
        if self.unfolder:
            del self.unfolder
        bpy.ops.object.mode_set(mode=self.recall_mode)

    def invoke(self, context, event):
        self.scale = context.scene.paper_model.scale
        try:
            self.prepare(context)
        except UnfoldError as error:
            self.report(type={'ERROR_INVALID_INPUT'}, message=error.args[0])
            error.mesh_select()
            self.recall()
            return {'CANCELLED'}
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.unfolder:
            self.prepare(context)
        self.unfolder.do_create_uvmap = self.do_create_uvmap
        try:
            if self.object.data.paper_island_list:
                self.unfolder.copy_island_names(self.object.data.paper_island_list)
            self.unfolder.save(self.properties)
            self.report({'INFO'}, "Saved a {}-page document".format(len(self.unfolder.mesh.pages)))
            return {'FINISHED'}
        except UnfoldError as error:
            self.report(type={'ERROR_INVALID_INPUT'}, message=error.args[0])
            return {'CANCELLED'}
        finally:
            self.recall()

    def get_scale_ratio(self, sce):
        margin = self.output_margin + self.sticker_width
        if min(self.output_size_x, self.output_size_y) <= 2 * margin:
            return False
        output_inner_size = M.Vector((self.output_size_x - 2 * margin, self.output_size_y - 2 * margin))
        ratio = self.unfolder.mesh.largest_island_ratio(output_inner_size)
        return ratio * sce.unit_settings.scale_length / self.scale

    def draw(self, context):
        layout = self.layout

        layout.prop(self.properties, "do_create_uvmap")

        row = layout.row(align=True)
        row.menu("VIEW3D_MT_paper_model_presets", text=bpy.types.VIEW3D_MT_paper_model_presets.bl_label)
        row.operator("export_mesh.paper_model_preset_add", text="", icon='ADD')
        row.operator("export_mesh.paper_model_preset_add", text="", icon='REMOVE').remove_active = True

        row.prop(context.scene, "dropdown_list")

        layout.prop(self.properties, "scale", text="Scale: 1/")
        scale_ratio = self.get_scale_ratio(context.scene)
        if scale_ratio > 1:
            layout.label(
                text="An island is roughly {:.1f}x bigger than page".format(scale_ratio),
                icon="ERROR")
        elif scale_ratio > 0:
            layout.label(text="Largest island is roughly 1/{:.1f} of page".format(1 / scale_ratio))

        if context.scene.unit_settings.scale_length != 1:
            layout.label(
                text="Unit scale {:.1f} makes page size etc. not display correctly".format(
                    context.scene.unit_settings.scale_length), icon="ERROR")
        box = layout.box()
        row = box.row(align=True)
        row.prop(
            self.properties, "ui_expanded_document", text="",
            icon=('TRIA_DOWN' if self.ui_expanded_document else 'TRIA_RIGHT'), emboss=False)
        row.label(text="Document Settings")

        if self.ui_expanded_document:
            box.prop(self.properties, "file_format", text="Format")
            box.prop(self.properties, "page_size_preset")
            col = box.column(align=True)
            col.active = self.page_size_preset == 'USER'
            col.prop(self.properties, "output_size_x")
            col.prop(self.properties, "output_size_y")
            box.prop(self.properties, "output_margin")
            col = box.column()
            col.prop(self.properties, "do_create_stickers")
            col.prop(self.properties, "do_create_numbers")
            col = box.column()
            col.active = self.do_create_stickers or self.do_create_numbers
            col.prop(self.properties, "sticker_width")
            box.prop(self.properties, "angle_epsilon")

            box.prop(self.properties, "output_type")
            col = box.column()
            col.active = (self.output_type != 'NONE')
            if len(self.object.data.uv_layers) == 8:
                col.label(text="No UV slots left, No Texture is the only option.", icon='ERROR')
            elif context.scene.render.engine != 'CYCLES' and self.output_type != 'NONE':
                col.label(text="Cycles will be used for texture baking.", icon='ERROR')
            row = col.row()
            row.active = self.output_type in ('AMBIENT_OCCLUSION', 'RENDER', 'SELECTED_TO_ACTIVE')
            row.prop(self.properties, "bake_samples")
            col.prop(self.properties, "output_dpi")
            row = col.row()
            row.active = self.file_format == 'SVG'
            row.prop(self.properties, "image_packing", text="Images")

        box = layout.box()
        row = box.row(align=True)
        row.prop(
            self.properties, "ui_expanded_style", text="",
            icon=('TRIA_DOWN' if self.ui_expanded_style else 'TRIA_RIGHT'), emboss=False)
        row.label(text="Colors and Style")

        if self.ui_expanded_style:
            box.prop(self.style, "line_width", text="Default line width")
            col = box.column()
            col.prop(self.style, "outer_color")
            col.prop(self.style, "outer_width", text="Relative width")
            col.prop(self.style, "outer_style", text="Style")
            col = box.column()
            col.active = self.output_type != 'NONE'
            col.prop(self.style, "use_outbg", text="Outer Lines Highlight:")
            sub = col.column()
            sub.active = self.output_type != 'NONE' and self.style.use_outbg
            sub.prop(self.style, "outbg_color", text="")
            sub.prop(self.style, "outbg_width", text="Relative width")
            col = box.column()
            col.prop(self.style, "convex_color")
            col.prop(self.style, "convex_width", text="Relative width")
            col.prop(self.style, "convex_style", text="Style")
            col = box.column()
            col.prop(self.style, "concave_color")
            col.prop(self.style, "concave_width", text="Relative width")
            col.prop(self.style, "concave_style", text="Style")
            col = box.column()
            col.prop(self.style, "freestyle_color")
            col.prop(self.style, "freestyle_width", text="Relative width")
            col.prop(self.style, "freestyle_style", text="Style")
            col = box.column()
            col.active = self.output_type != 'NONE'
            col.prop(self.style, "use_inbg", text="Inner Lines Highlight:")
            sub = col.column()
            sub.active = self.output_type != 'NONE' and self.style.use_inbg
            sub.prop(self.style, "inbg_color", text="")
            sub.prop(self.style, "inbg_width", text="Relative width")
            col = box.column()
            col.active = self.do_create_stickers
            col.prop(self.style, "sticker_fill")
            box.prop(self.style, "text_color")


def menu_func_export(self, context):
    self.layout.operator("export_mesh.paper_model", text="Paper Model (.pdf/.svg)")


def menu_func_unfold(self, context):
    self.layout.operator("mesh.unfold", text="Unfold")


class SelectIsland(bpy.types.Operator):
    """Blender Operator: select all faces of the active island"""

    bl_idname = "mesh.select_paper_island"
    bl_label = "Select Island"
    bl_description = "Select an island of the paper model net"

    operation: bpy.props.EnumProperty(
        name="Operation", description="Operation with the current selection",
        default='ADD', items=[
            ('ADD', "Add", "Add to current selection"),
            ('REMOVE', "Remove", "Remove from selection"),
            ('REPLACE', "Replace", "Select only the ")
        ])

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        island = me.paper_island_list[me.paper_island_index]
        faces = {face.id for face in island.faces}
        edges = set()
        verts = set()
        if self.operation == 'REPLACE':
            for face in bm.faces:
                selected = face.index in faces
                face.select = selected
                if selected:
                    edges.update(face.edges)
                    verts.update(face.verts)
            for edge in bm.edges:
                edge.select = edge in edges
            for vert in bm.verts:
                vert.select = vert in verts
        else:
            selected = (self.operation == 'ADD')
            for index in faces:
                face = bm.faces[index]
                face.select = selected
                edges.update(face.edges)
                verts.update(face.verts)
            for edge in edges:
                edge.select = any(face.select for face in edge.link_faces)
            for vert in verts:
                vert.select = any(edge.select for edge in vert.link_edges)
        bmesh.update_edit_mesh(me, False, False)
        return {'FINISHED'}


class VIEW3D_MT_paper_model_presets(bpy.types.Menu):
    bl_label = "Paper Model Presets"
    preset_subdir = "export_mesh"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class AddPresetPaperModel(bl_operators.presets.AddPresetBase, bpy.types.Operator):
    """Add or remove a Paper Model Preset"""
    bl_idname = "export_mesh.paper_model_preset_add"
    bl_label = "Add Paper Model Preset"
    preset_menu = "VIEW3D_MT_paper_model_presets"
    preset_subdir = "export_mesh"
    preset_defines = ["op = bpy.context.active_operator"]

    @property
    def preset_values(self):
        op = bpy.ops.export_mesh.paper_model
        properties = op.get_rna().bl_rna.properties.items()
        blacklist = bpy.types.Operator.bl_rna.properties.keys()
        return [
            "op.{}".format(prop_id) for (prop_id, prop) in properties
            if not (prop.is_hidden or prop.is_skip_save or prop_id in blacklist)]


class VIEW3D_PT_paper_model_tools(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paper'
    bl_label = "Unfold"

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        obj = context.active_object
        mesh = obj.data if obj and obj.type == 'MESH' else None

        layout.operator("mesh.unfold")
        row = layout.row()
        row.prop(context.scene, "dropdown_list")
        layout.operator("mesh.apply_edge_type")


        if context.mode == 'EDIT_MESH':
            row = layout.row(align=True)
            row.operator("mesh.mark_seam", text="Mark Seam").clear = False
            row.operator("mesh.mark_seam", text="Clear Seam").clear = True
        else:
            layout.operator("mesh.clear_all_seams")

        row = layout.row()
        row.prop(context.scene, "score_direction")
        row = layout.row()
        row.prop(context.scene, "score_num")
        layout.operator("mesh.apply_scores")

class VIEW3D_PT_paper_model_settings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paper'
    bl_label = "Export"

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        obj = context.active_object
        mesh = obj.data if obj and obj.type == 'MESH' else None

        layout.operator("export_mesh.paper_model")
        props = sce.paper_model
        layout.prop(props, "scale", text="Model Scale:  1/")
        # row = layout.row()
        # row.prop(context.scene, "dropdown_list")


        layout.prop(props, "limit_by_page")
        col = layout.column()
        col.active = props.limit_by_page
        col.prop(props, "page_size_preset")
        sub = col.column(align=True)
        sub.active = props.page_size_preset == 'USER'
        sub.prop(props, "output_size_x")
        sub.prop(props, "output_size_y")


class DATA_PT_paper_model_islands(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_label = "Paper Model Islands"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        sce = context.scene
        obj = context.active_object
        mesh = obj.data if obj and obj.type == 'MESH' else None

        layout.operator("mesh.unfold", icon='FILE_REFRESH')
        if mesh and mesh.paper_island_list:
            layout.label(
                text="1 island:" if len(mesh.paper_island_list) == 1 else
                "{} islands:".format(len(mesh.paper_island_list)))
            layout.template_list(
                'UI_UL_list', 'paper_model_island_list', mesh,
                'paper_island_list', mesh, 'paper_island_index', rows=1, maxrows=5)
            sub = layout.split(align=True)
            sub.operator("mesh.select_paper_island", text="Select").operation = 'ADD'
            sub.operator("mesh.select_paper_island", text="Deselect").operation = 'REMOVE'
            sub.prop(sce.paper_model, "sync_island", icon='UV_SYNC_SELECT', toggle=True)
            if mesh.paper_island_index >= 0:
                list_item = mesh.paper_island_list[mesh.paper_island_index]
                sub = layout.column(align=True)
                sub.prop(list_item, "auto_label")
                sub.prop(list_item, "label")
                sub.prop(list_item, "auto_abbrev")
                row = sub.row()
                row.active = not list_item.auto_abbrev
                row.prop(list_item, "abbreviation")


        else:
            layout.box().label(text="Not unfolded")

        row.prop(context.scene, "dropdown_list")

def label_changed(self, context):
    """The label of an island was changed"""
    # accessing properties via [..] to avoid a recursive call after the update
    self["auto_label"] = not self.label or self.label.isspace()
    island_item_changed(self, context)


def island_item_changed(self, context):
    """The labelling of an island was changed"""

    def increment(abbrev, collisions):
        letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"
        while abbrev in collisions:
            abbrev = abbrev.rstrip(letters[-1])
            abbrev = abbrev[:2] + letters[letters.find(abbrev[-1]) + 1 if len(abbrev) == 3 else 0]
        return abbrev

    # accessing properties via [..] to avoid a recursive call after the update
    island_list = context.active_object.data.paper_island_list
    if self.auto_label:
        self["label"] = ""  # avoid self-conflict
        number = 1
        while any(item.label == "Island {}".format(number) for item in island_list):
            number += 1
        self["label"] = "Island {}".format(number)
    if self.auto_abbrev:
        self["abbreviation"] = ""  # avoid self-conflict
        abbrev = "".join(u.first_letters(self.label))[:3].upper()
        self["abbreviation"] = increment(abbrev, {item.abbreviation for item in island_list})
    elif len(self.abbreviation) > 3:
        self["abbreviation"] = self.abbreviation[:3]
    self.name = "[{}] {} ({} {})".format(
        self.abbreviation, self.label, len(self.faces), "faces" if len(self.faces) > 1 else "face")


def island_index_changed(self, context):
    """The active island was changed"""
    if context.scene.paper_model.sync_island and SelectIsland.poll(context):
        bpy.ops.mesh.select_paper_island(operation='REPLACE')


class FaceList(bpy.types.PropertyGroup):
    id: bpy.props.IntProperty(name="Face ID")


class IslandList(bpy.types.PropertyGroup):
    faces: bpy.props.CollectionProperty(
        name="Faces", description="Faces belonging to this island", type=FaceList)
    label: bpy.props.StringProperty(
        name="Label", description="Label on this island",
        default="", update=label_changed)
    abbreviation: bpy.props.StringProperty(
        name="Abbreviation", description="Three-letter label to use when there is not enough space",
        default="", update=island_item_changed)
    auto_label: bpy.props.BoolProperty(
        name="Auto Label", description="Generate the label automatically",
        default=True, update=island_item_changed)
    auto_abbrev: bpy.props.BoolProperty(
        name="Auto Abbreviation", description="Generate the abbreviation automatically",
        default=True, update=island_item_changed)


class PaperModelSettings(bpy.types.PropertyGroup):
    sync_island: bpy.props.BoolProperty(
        name="Sync", description="Keep faces of the active island selected",
        default=False, update=island_index_changed)
    limit_by_page: bpy.props.BoolProperty(
        name="Limit Island Size", description="Do not create islands larger than given dimensions",
        default=False, update=page_size_preset_changed)
    page_size_preset: bpy.props.EnumProperty(
        name="Page Size", description="Maximal size of an island",
        default='A4', update=page_size_preset_changed, items=global_paper_sizes)
    output_size_x: bpy.props.FloatProperty(
        name="Width", description="Maximal width of an island",
        default=0.2, soft_min=0.105, soft_max=0.841, subtype="UNSIGNED", unit="LENGTH")
    output_size_y: bpy.props.FloatProperty(
        name="Height", description="Maximal height of an island",
        default=0.29, soft_min=0.148, soft_max=1.189, subtype="UNSIGNED", unit="LENGTH")
    scale: bpy.props.FloatProperty(
        name="Scale", description="Divisor of all dimensions when exporting",
        default=1, soft_min=1.0, soft_max=100.0, subtype='FACTOR', precision=1)


module_classes = (
    Unfold,
    ExportPaperModel,
    ClearAllSeams,
    ApplyEdgeType,
    ApplyScores,
    SelectIsland,
    AddPresetPaperModel,
    FaceList,
    IslandList,
    PaperModelSettings,
    VIEW3D_MT_paper_model_presets,
    DATA_PT_paper_model_islands,
    VIEW3D_PT_paper_model_tools,
    VIEW3D_PT_paper_model_settings,
)

def index_edge (self, context):

    if (int(context.scene.dropdown_list) == 1):
        ApplyEdgeType.current_edge = "auto"
    elif(int(context.scene.dropdown_list) == 2):
        ApplyEdgeType.current_edge = "pin"
    elif(int(context.scene.dropdown_list) == 3):
        ApplyEdgeType.current_edge = "tooth"
    elif(int(context.scene.dropdown_list) == 4):
        ApplyEdgeType.current_edge = "glue"

def index_score(self, context):

    if (int(context.scene.score_direction) == 1):
        ApplyScores.scoredir = 'x'
    elif(int(context.scene.score_direction) == 2):
        ApplyScores.scoredir = 'y'
    elif(int(context.scene.score_direction) == 3):
        ApplyScores.scoredir = 'z'


def score_density(self, context):
   ApplyScores.current_score_num = context.scene.score_num

def register():
    bpy.types.Scene.paper_model = bpy.props.PointerProperty(
        name="Paper Model", description="Settings of the Export Paper Model script",
        type=PaperModelSettings, options={'SKIP_SAVE'})
    bpy.types.Mesh.paper_island_list = bpy.props.CollectionProperty(
        name="Island List", type=IslandList)
    bpy.types.Mesh.paper_island_index = bpy.props.IntProperty(
        name="Island List Index",
        default=-1, min=-1, max=100, options={'SKIP_SAVE'}, update=island_index_changed)

    bpy.types.Scene.dropdown_list = bpy.props.EnumProperty(
        name="Edge Type",
        items=(
            ('1', 'Auto', ''),
            ('2', 'Pin Join', ''),
            ('3', 'Sawtooth Join', ''),
            ('4', 'Glue Tab', ''),
        ),
    update=index_edge
    )
    bpy.types.Scene.score_direction = bpy.props.EnumProperty(
        name="Score axis",
        items=(
            ('1', 'x', ''),
            ('2', 'y', ''),
            ('3', 'z', ''),
        ),
        update=index_score
    )

    bpy.types.Scene.score_num = bpy.props.IntProperty(
        name="Number of Scores",
        default=5,
        min=1,
        max=20,
        update=score_density
    )
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_edit_mesh.prepend(menu_func_unfold)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func_unfold)



# if __name__ == "__main__":
#     register()
