#----------------------------------------------------------
# File uisettings.py
#----------------------------------------------------------
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

import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       PointerProperty)

from bpy.types import PropertyGroup


# Scene Properties
# ----------------------------------------------------------

class SKT_PG_settings(PropertyGroup):
    """SKT scene properties"""

    src_mesh: PointerProperty(
        type=bpy.types.Mesh, 
        name="Source Mesh", 
        description="Select a source mesh", 
        options={'ANIMATABLE'}, 
        update=None
        )
    
    dest_mesh: PointerProperty(
        type=bpy.types.Mesh, 
        name="Destination Mesh", 
        description="Select a destination mesh", 
        options={'ANIMATABLE'}, 
        update=None
        )

    specify_end_vertex: BoolProperty(
        name="Specify End Vertex",
        description="Execute till last vertex specified.",
        default = False
        )

    use_one_vertex: BoolProperty(
        name="Use Closest Vertex",
        description="Use the position of the closet vertex only or several vertices within the range.",
        default = True
        )
    
    skip_unpaired_vertices: BoolProperty(
        name="Skip unpaired vertices",
        description="Use this to skip vertices which cant find naerby vertices in source mesh to copy position from.",
        default = True
        )

    increment_radius: FloatProperty(
        name = "Increment Radius",
        description = "Radius to increment selection sphere.",
        default = 0.05,
        soft_min = 0.01,
        soft_max  = 1,
        min = 0.00000001
        )
    
    number_of_increments: IntProperty(
        name = "Number of increments",
        description = "Number of times to increment selection radius before giving up.",
        default = 2,
        soft_min = 1,
        soft_max  = 50,
        min = 1
        )

# Property of 1 item in the excluded shape key list
# ----------------------------------------------------------

class SKT_PG_shapeKeyListItem(PropertyGroup):
    """List box properties"""
    #name : StringProperty() -> Instantiated by default    
    obj_type: StringProperty()
    obj_id: IntProperty()