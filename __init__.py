'''
Copyright (C) 2020
haniehs@cs.ubc.ca

Created by Hanieh Shakeri

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "FoldMold",
    "author": "Hanieh Shakeri, Paul Bucci, QianQian Feng",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Export > FoldMold",
    "warning": "This addon is still in development.",
    "description": "Export a foldable mold for casting. Based on Export Paper Model by Adam Dominec.",
    "wiki_url": "",
    "category": "Import-Export",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/Paper_Model"
}


import bpy


# ensure dependencies exist
try:
    import svglib, svgpathtools
except ImportError:
    import subprocess
    print("Installing dependencies...")
    subprocess.check_call([bpy.app.binary_path_python, '-m', 'pip', 'install', 'svglib', 'svgpathtools'])


from . import auto_load

auto_load.init()

# register
##################################

import traceback

def register():
    print("in __init__.py")
    #### copied from io
    auto_load.register()


def unregister():    
    auto_load.unregister()
