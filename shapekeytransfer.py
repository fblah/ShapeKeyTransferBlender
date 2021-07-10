#----------------------------------------------------------
# File shapekeytransfer.py
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
import bmesh
from mathutils import Vector

from bpy.types import (Operator, 
                       UIList, 
                       Panel)

# __reload_order_index__ = 1

# Class which handles shape key transfers
# ----------------------------------------------------------

class ShapeKeyTransfer:
    """
    Class with required methods to transfer shape keys between 2 meshes.
    """
    def __init__(self):
        # Increment radius used to select nearby vertices in the source mesh for copying its positions to the destination mesh vertex
        self.increment_radius = .05
        self.number_of_increments = 20
        # set total vertices incase you want to run for less number of vertices also set specify_end_vertex to True
        # set current_vertex index incase you want to continue from another index
        # use_one_vertex will transfer the weight of the closest vertex within the selection sphere
        self.current_vertex_index = 0
        self.total_vertices       = 0
        self.specify_end_vertex   = False # not yet implemented
        self.use_one_vertex       = True

        # shape keys to ignore
        self.default_excluded_keys = self.excluded_shape_keys = ['Basis', 'Expressions_IDHumans_max'] 

        # internal references used by this class
        self.dest_mesh            = None
        self.src_mesh             = None
        self.src_mwi              = None
        self.dest_shape_key_index = 0
        self.src_shape_key_index  = 0
        self.do_once_per_vertex   = False        
        self.current_vertex       = None
        self.src_chosen_vertices  = []
        self.message              = ""
        self.skip_vertices_with_no_pair = False

    # select required vertices within a radius and return array of indices
    def select_vertices(self, center, radius):            
        src_chosen_vertices = []
        closest_vertex_index = -1
        radius_vec = center + Vector((0, 0, radius))        
        # put selection sphere in local coords.
        lco = self.src_mwi @ center
        r   = self.src_mwi @ (radius_vec) - lco
        closest_length = r.length        

        # select verts within radius
        for index, v in enumerate(self.src_mesh.data.shape_keys.key_blocks[0].data):
            is_selected = (v.co - lco).length <= r.length     
            if(is_selected):
                src_chosen_vertices.append(index)
                if(self.use_one_vertex):
                    if((v.co - lco).length <= closest_length):
                        closest_length = (v.co - lco).length
                        closest_vertex_index = index            

        # update closest vertex
        if(self.use_one_vertex):                
            src_chosen_vertices = []
            if(closest_vertex_index > - 1):
                src_chosen_vertices.append(closest_vertex_index)            

        return src_chosen_vertices

    # this select function initially starts (if level=0) by matching a point in same space as the source mesh and if it cant find similar positioned point we increment search radius   
    def select_required_verts(self, vert, rad, level=0):    
        verts = []
        if(level > self.number_of_increments):
            return verts 
        verts = self.select_vertices(vert, rad)    
        if(len(verts) == 0):
            return self.select_required_verts(vert, rad + self.increment_radius, level + 1)
        else:        
            return verts

    # set the new vertex position on the shape key
    def set_vertex_position(self, v_pos):    
        self.dest_mesh.data.shape_keys.key_blocks[self.dest_shape_key_index].data[self.current_vertex_index].co = v_pos

    # update 1 vertex of destination mesh
    def update_vertex(self):
        if(self.current_vertex_index >= self.total_vertices ):
            return False

        if(self.do_once_per_vertex):
            #mathutils now uses the PEP 465 binary operator for multiplying matrices change * to @
            self.current_vertex = self.dest_mesh.matrix_world @ self.dest_mesh.data.shape_keys.key_blocks[0].data[self.current_vertex_index].co       
            self.src_chosen_vertices = self.select_required_verts(self.current_vertex,0)   
            self.do_once_per_vertex = False

        if(len(self.src_chosen_vertices) == 0):
            self.message = ("Failed to find surrounding vertices | Try increasing increment radius | vertex index " + str(self.current_vertex_index) + " at shape key index " + str(self.src_shape_key_index))
            self.current_vertex_index += 1
            if(not self.skip_vertices_with_no_pair):
                return True
            else:
                return False

        result_position = Vector()    
        for v in self.src_chosen_vertices:
            result_position +=  self.src_mesh.data.shape_keys.key_blocks[0].data[v].co    
        result_position /= len(self.src_chosen_vertices)

        result_position2 = Vector()
        for v in self.src_chosen_vertices:
            result_position2 += self.src_mesh.data.shape_keys.key_blocks[self.src_shape_key_index].data[v].co        
        result_position2 /= len(self.src_chosen_vertices)    
        result = result_position2 - result_position + self.current_vertex        
        self.set_vertex_position(result)
        return False

    # store shapekey index 
    def update_global_shapekey_indices(self, p_key_name): 
        for index, sk in enumerate(self.dest_mesh.data.shape_keys.key_blocks):
            if sk.name == p_key_name:            
                self.dest_shape_key_index = index
        for index, sk in enumerate(self.src_mesh.data.shape_keys.key_blocks):
            if sk.name == p_key_name:            
                self.src_shape_key_index = index

    def get_parent(self, mesh):
        for ob in bpy.data.objects:
            if (ob.data) == mesh:
                return ob
        return None

    def transfer_shape_keys(self, src, dest, use_only_excluded_shape_keys = False):
        self.src_mesh   = self.get_parent(src)
        self.dest_mesh  = self.get_parent(dest)
        self.src_mwi    = self.src_mesh.matrix_world.inverted()
        
        self.current_vertex_index = 0

        local_shape_key_list = [] # used only when considering excluded shape keys

        if(not(self.src_mesh and self.dest_mesh)):
            self.message = "The meshes are not valid!"
            return True
        if(self.specify_end_vertex == False):
            self.total_vertices = len(self.dest_mesh.data.vertices)            
        if(not hasattr(self.src_mesh.data.shape_keys, "key_blocks")):
            self.message = "There are no Shape Keys in the source mesh!"
            return True
        # Check if dest_mesh has any shape key if not create one
        if(not hasattr(self.dest_mesh.data.shape_keys, "key_blocks")):
            self.dest_mesh.shape_key_add(name="Basis")
        # add missing shape keys to dest_mesh    
        for src_shape_key_iter in self.src_mesh.data.shape_keys.key_blocks:
            valid_shape_key = False        
            if(use_only_excluded_shape_keys and (src_shape_key_iter.name in self.excluded_shape_keys)):
                local_shape_key_list.append(src_shape_key_iter.name)   
            if((not use_only_excluded_shape_keys) and (src_shape_key_iter.name in self.excluded_shape_keys)):
                continue
            if(use_only_excluded_shape_keys and (not (src_shape_key_iter.name in self.excluded_shape_keys))):
                continue
            for dest_shape_key_iter in self.dest_mesh.data.shape_keys.key_blocks:
                if(src_shape_key_iter.name == dest_shape_key_iter.name):
                    valid_shape_key = True
            if(not valid_shape_key):
                self.dest_mesh.shape_key_add(name=src_shape_key_iter.name)
                

        # all vertices in destination mesh
        while(self.current_vertex_index < self.total_vertices):
            self.do_once_per_vertex = True
            print("Vertex: " + str(self.current_vertex_index + 1) + "/" + str(self.total_vertices))
            if(use_only_excluded_shape_keys):
                for key_name in local_shape_key_list:
                    self.update_global_shapekey_indices(key_name)            
                    if(self.update_vertex()):
                        return True
            else:
                # Iterate all shape keys 
                for shape_key_iter in self.src_mesh.data.shape_keys.key_blocks:    
                    key_name = shape_key_iter.name
                    # exclude shapekeys not needed
                    if(not (key_name in self.excluded_shape_keys)):
                        self.update_global_shapekey_indices(key_name)            
                        if(self.update_vertex()):
                            return True
            self.current_vertex_index += 1
        self.message = "Transferred Shape Keys successfully!"
        return False
    
    # get the default excluded shape keys
    def get_default_excluded_keys(self):
        return list(set(self.default_excluded_keys) - set(["Basis"]))

    # Update the excluded shape keys list
    def update_shape_keys_list(self, excluded_keys):
        keys = []
        for item in excluded_keys:
            keys.append(item.name)
        keys.append("Basis")
        # remove duplicates
        keys = list(set(keys))
        self.excluded_shape_keys = keys

    #get shape keys of a  mesh
    def get_shape_keys_mesh(self, mesh):
        obj = self.get_parent(mesh)
        keys = []
        if(not hasattr(obj.data.shape_keys, "key_blocks")):
            self.message = "There are no Shape Keys in the mesh!"
            return True
        for shape_key_iter in obj.data.shape_keys.key_blocks:
            keys.append(shape_key_iter.name)
        self.message = keys
        return False

# Instantiate the class
# ----------------------------------------------------------

SKT = ShapeKeyTransfer()


# Helper function to check if a valid selection is made
# ----------------------------------------------------------

def can_transfer_keys(context):
    """Checks if selected source and destination meshes are valid"""
    skt = context.scene.shapekeytransfer
    if(skt.src_mesh and skt.dest_mesh):
        if(skt.src_mesh == skt.dest_mesh):
            return False
        else:
            return True
    else:
        return False


# Copy all Shape Key names to Clipboard Button
# ----------------------------------------------------------

class SKT_OT_copyKeyNames(Operator):
    """Copy all Shape Key names to Clipboard"""
    bl_idname = "skt.copy_key_names"
    bl_label = "Copy Shape Key Names"
    bl_description = "Copy Shape Key Names from Source Mesh to Clipboard"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        skt = context.scene.shapekeytransfer
        return (skt.src_mesh is not None)

    def execute(self, context):
        global SKT
        skt = context.scene.shapekeytransfer        
        if(skt.src_mesh):
            if(SKT.get_shape_keys_mesh(skt.src_mesh)):
                self.report({'INFO'}, SKT.message)                
            else:
                keys = SKT.message
                temp_str = ""
                for key in keys:
                    if(key == "Basis"):
                        continue
                    temp_str += key + "\n"
                context.window_manager.clipboard = temp_str
                self.report({'INFO'}, "Copied to Clipboard")
        else:
            self.report({'INFO'}, "Invalid Source Mesh")
        return{'FINISHED'}


# Copy all Shape Key names from clipboard Button
# ----------------------------------------------------------

class SKT_OT_insertKeyNames(Operator):
    """Copy all Shape Key Names from the Clipboard"""
    bl_idname = "skt.insert_key_names"
    bl_label = "Insert Shape Key Names"
    bl_description = "Insert Shape Key Names from Clipboard (Each name per Row)"
    bl_options = {'INTERNAL'}   

    def execute(self, context):
        scn = context.scene
        for key in context.window_manager.clipboard.split("\n"):
            if(len(key)):
                item = scn.customshapekeylist.add()
                item.name = key
                item.obj_type = "STRING"
                item.obj_id = len(scn.customshapekeylist)
                scn.shapekeytransfer_list_index = len(scn.customshapekeylist)-1
        self.report({'INFO'}, "Added shape key names from Clipboard")
        return{'FINISHED'}


# Transfer Shape Keys Button (Operator)
# ----------------------------------------------------------

class SKT_OT_transferShapeKeys(Operator):
    """Transfers Shape Keys to Selected Mesh"""
    bl_idname = "skt.transfer_shape_keys"
    bl_label = "Transfer Shape Keys"
    bl_description = "The two meshes should overlap each other or positioned pretty close"
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}
    
    @classmethod
    def poll(cls, context):
        return can_transfer_keys(context)

    def execute(self, context):
        global SKT
        skt = context.scene.shapekeytransfer
        SKT.increment_radius = skt.increment_radius
        SKT.use_one_vertex   = skt.use_one_vertex
        SKT.skip_vertices_with_no_pair = skt.skip_unpaired_vertices
        SKT.number_of_increments = skt.number_of_increments

        SKT.update_shape_keys_list(context.scene.customshapekeylist)
        result = SKT.transfer_shape_keys(skt.src_mesh, skt.dest_mesh)
        if(result):
            self.report({'ERROR'}, SKT.message)            
        else:
            self.report({'INFO'}, SKT.message)
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        skt = context.scene.shapekeytransfer
        col = layout.column()
        col.label(text="Vertex influence:")       
        col.prop(skt, "increment_radius")
        col.prop(skt, "use_one_vertex")
        col.prop(skt, "skip_unpaired_vertices")
        col.prop(skt, "number_of_increments")


# Transfer Shape Keys in excluded shape keys list Button  (Operator)
# ----------------------------------------------------------

class SKT_OT_transferExcludedShapeKeys(Operator):
    """Transfers Shape Keys from excluded Shape key list"""
    bl_idname = "skt.transfer_excluded_shape_keys"
    bl_label = "Transfer Excluded Shape Keys Only"
    bl_description = "The two meshes should overlap each other or positioned pretty close"
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    @classmethod
    def poll(cls, context):
        return can_transfer_keys(context)

    def execute(self, context):
        global SKT
        skt = context.scene.shapekeytransfer
        SKT.increment_radius = skt.increment_radius
        SKT.use_one_vertex   = skt.use_one_vertex
        SKT.skip_vertices_with_no_pair = skt.skip_unpaired_vertices
        SKT.number_of_increments = skt.number_of_increments
        
        SKT.update_shape_keys_list(context.scene.customshapekeylist)
        result = SKT.transfer_shape_keys(skt.src_mesh, skt.dest_mesh, True)
        if(result):
            self.report({'ERROR'}, SKT.message)            
        else:
            self.report({'INFO'}, SKT.message)
        return {'FINISHED'}
    
    def draw(self, context):
        skt = context.scene.shapekeytransfer
        layout = self.layout
        col = layout.column()
        col.label(text="Vertex influence:")       
        col.prop(skt, "increment_radius")
        col.prop(skt, "use_one_vertex")
        col.prop(skt, "skip_unpaired_vertices")
        col.prop(skt, "number_of_increments")
        

# Remove all Shape Keys in source mesh Button (Operator)
# ----------------------------------------------------------

class SKT_OT_removeShapeKeys(Operator):
    """Remove all Shape Keys of Source Mesh"""
    bl_idname = "skt.remove_src_shape_keys"
    bl_label = "Remove Shape Keys of Source"
    bl_description = "Remove all Shape Keys of Source Mesh"
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL','UNDO'}

    @classmethod
    def poll(cls, context):
        skt = context.scene.shapekeytransfer
        return (skt.src_mesh is not None)

    def execute(self, context):
        global SKT
        skt = context.scene.shapekeytransfer        
        if(skt.src_mesh):
            ob = SKT.get_parent(skt.src_mesh)
            if(ob.data.shape_keys):
                basis = None
                for x in ob.data.shape_keys.key_blocks:
                    if(basis):
                        ob.shape_key_remove(x)
                    else:
                        basis = x
                ob.shape_key_remove(basis)
            self.report({'INFO'}, "Removed all shape keys in source mesh!")
        else:
            self.report({'ERROR'}, "Select a valid source mesh!")            
        return {'FINISHED'}
    

# Manage customshapekeylist items (Operator)
# ----------------------------------------------------------

class SKT_OT_actions(Operator):
    """Move items up and down, add and remove"""
    bl_idname = "customshapekeylist.list_action"
    bl_label = "List Actions"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}

    action : bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ('DEFAULT', "Default", "")))    

    def invoke(self, context, event):
        scn = context.scene
        idx = scn.shapekeytransfer_list_index

        try:
            item = scn.customshapekeylist[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(scn.customshapekeylist) - 1:
                item_next = scn.customshapekeylist[idx+1].name
                scn.customshapekeylist.move(idx, idx+1)
                scn.shapekeytransfer_list_index += 1
                info = 'Item "%s" moved to position %d' % (item.name, scn.shapekeytransfer_list_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = scn.customshapekeylist[idx-1].name
                scn.customshapekeylist.move(idx, idx-1)
                scn.shapekeytransfer_list_index -= 1
                info = 'Item "%s" moved to position %d' % (item.name, scn.shapekeytransfer_list_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (scn.customshapekeylist[idx].name)
                scn.shapekeytransfer_list_index -= 1
                scn.customshapekeylist.remove(idx)
                self.report({'INFO'}, info)
            
        if self.action == 'ADD':                               
            scn = context.scene
            item = scn.customshapekeylist.add()
            item.name = "key"
            item.obj_type = "STRING"
            item.obj_id = len(scn.customshapekeylist)
            scn.shapekeytransfer_list_index = len(scn.customshapekeylist)-1             
            info = '"%s" added to list' % (item.name)
            self.report({'INFO'}, info)
        
        elif self.action == 'DEFAULT':
            for key in SKT.get_default_excluded_keys():                    
                item = scn.customshapekeylist.add()
                item.name = key
                item.obj_type = "STRING"
                item.obj_id = len(scn.customshapekeylist)
                scn.shapekeytransfer_list_index = len(scn.customshapekeylist)-1
                info = '"%s" added to list' % (item.name)
                self.report({'INFO'}, info)
        
        return {"FINISHED"}

# Clear customshapekeylist items (Operator)
# ----------------------------------------------------------

class SKT_OT_clearList(Operator):
    """Clear all items of the list"""
    bl_idname = "customshapekeylist.clear_list"
    bl_label = "Clear List"
    bl_description = "Clear all items of the list"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.customshapekeylist)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if bool(context.scene.customshapekeylist):
            context.scene.customshapekeylist.clear()
            self.report({'INFO'}, "All items removed")
        else:
            self.report({'INFO'}, "Nothing to remove")        
        return{'FINISHED'}

# Remove duplicates among customshapekeylist items (Operator)
# ----------------------------------------------------------

class SKT_OT_removeDuplicates(Operator):
    """Remove all duplicates in the list"""
    bl_idname = "customshapekeylist.remove_duplicates"
    bl_label = "Remove Doubles"
    bl_description = "Remove all Duplicates in the List"
    bl_options = {'INTERNAL'}

    def find_duplicates(self, context):
        """find all duplicates by name"""
        name_lookup = {}
        for c, i in enumerate(context.scene.customshapekeylist):
            name_lookup.setdefault(i.name, []).append(c)
        duplicates = set()
        for name, indices in name_lookup.items():
            for i in indices[1:]:
                duplicates.add(i)
        return sorted(list(duplicates))

    @classmethod
    def poll(cls, context):
        return bool(context.scene.customshapekeylist)

    def execute(self, context):
        scn = context.scene
        removed_items = []
        # Reverse the list before removing the items
        for i in self.find_duplicates(context)[::-1]:
            scn.customshapekeylist.remove(i)
            removed_items.append(i)
        if removed_items:
            scn.shapekeytransfer_list_index = len(scn.customshapekeylist)-1
            info = ', '.join(map(str, removed_items))
            self.report({'INFO'}, "Removed indices: %s" % (info))
        else:
            self.report({'INFO'}, "No duplicates")        
        return{'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

# customshapekeylist items (UIList)
# ----------------------------------------------------------

class SKT_UL_items(UIList):
    """Item in customshapekeylist"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        #split = layout.split(0.3)
        #split.label("Index: %d" % (index))
        #custom_icon = "OUTLINER_OB_%s" % item.obj_type
        #split.prop(item, "name", text="", emboss=False, translate=False, icon=custom_icon)
        #split.label(item.name, icon=custom_icon) # avoids renaming the item by accident
        layout.prop(item, "name", text="", emboss=False, icon_value=icon)        
    def invoke(self, context, event):        
        pass   

# Main addon panel (Panel)
# ----------------------------------------------------------

class SKT_PT_view3D(Panel):
    """Shape Key Tools Panel layout"""
    bl_label = "Shape Key Transfer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = "Tools"    
    
    @classmethod
    def poll(self,context):        
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        scn = context.scene
        skt = scn.shapekeytransfer
        
        '''
        if not can_transfer_keys(context):
            layout.label(text="Set required meshes", icon='INFO')
        '''

        layout.prop(skt, "src_mesh", text="Source Mesh") 
        layout.prop(skt, "dest_mesh", text="Destination Mesh")

        layout.separator()
        layout.operator(SKT_OT_transferShapeKeys.bl_idname, icon='ARROW_LEFTRIGHT')
        layout.operator(SKT_OT_transferExcludedShapeKeys.bl_idname, icon='KEYINGSET')
        layout.separator()
        layout.operator(SKT_OT_removeShapeKeys.bl_idname, icon='CANCEL')

        layout.separator()
        layout.label(text="Excluded Shape Keys")
        rows = 5
        row = layout.row()
        row.template_list("SKT_UL_items", "", scn, "customshapekeylist", scn, "shapekeytransfer_list_index", rows=rows)

        col = row.column(align=True)
        col.operator(SKT_OT_actions.bl_idname, icon='PLUS', text="").action = 'ADD'
        col.operator(SKT_OT_actions.bl_idname, icon='REMOVE', text="").action = 'REMOVE'
        col.separator()
        col.operator(SKT_OT_actions.bl_idname, icon='TRIA_UP', text="").action = 'UP'
        col.operator(SKT_OT_actions.bl_idname, icon='TRIA_DOWN', text="").action = 'DOWN'
        col.operator(SKT_OT_actions.bl_idname, icon='RECOVER_LAST', text="").action = 'DEFAULT'

        col = layout.column(align=True)        
        row = col.row(align=True)
        row.operator(SKT_OT_removeDuplicates.bl_idname, icon="FORCE_VORTEX")
        row.operator(SKT_OT_clearList.bl_idname, icon="X")
        col = col.column(align=True)
        col.operator(SKT_OT_copyKeyNames.bl_idname, icon="COPYDOWN")
        col.operator(SKT_OT_insertKeyNames.bl_idname, icon="IMPORT")

        layout.separator()