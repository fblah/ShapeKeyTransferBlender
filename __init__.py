# ----------------------------------------------------------
# File __init__.py
# ----------------------------------------------------------
#
# ShapeKeyTransfer - Copyright (C) 2018 Ajit Christopher D'Monte
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ----------------------------------------------------------

bl_info = {
    "name": "Shape Key Transfer",
    "description": "Copies shape keys from one mesh to another.",
    "author": "Ajit D'Monte (fBlah), email: ajitdmonte@gmail.com",
    "version": (1, 0, 2),
    "blender": (2, 93, 0),
    "location": "View3D > Tools > Shape Key Transfer",    
    "warning": "This has not been tested rigorously.",
    "wiki_url": "",    
    "category": 'Mesh'}


import bpy
from bpy.props import PointerProperty, CollectionProperty
from . uisettings import *
from . shapekeytransfer import *


classes = (
    SKT_PG_settings,
    SKT_PG_shapeKeyListItem,
    SKT_OT_copyKeyNames,
    SKT_OT_insertKeyNames,
    SKT_OT_transferShapeKeys,
    SKT_OT_transferExcludedShapeKeys,
    SKT_OT_removeShapeKeys,
    SKT_OT_actions,
    SKT_OT_clearList,
    SKT_OT_removeDuplicates,
    SKT_UL_items,
    SKT_PT_view3D
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.shapekeytransfer_list_index = IntProperty()
    bpy.types.Scene.shapekeytransfer = PointerProperty(type=SKT_PG_settings)
    bpy.types.Scene.customshapekeylist = CollectionProperty(type=SKT_PG_shapeKeyListItem)


def unregister():    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.shapekeytransfer
    del bpy.types.Scene.customshapekeylist
    del bpy.types.Scene.shapekeytransfer_list_index