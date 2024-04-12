import bpy
from . import UI_Setting
from .gn_remove import GNRemove


# GeoNodesの状況UI
# ===========================================================================================
# 3DView Tools Panel
class GN_REMOVE_PT_ui(bpy.types.Panel):
    bl_idname = "GN_REMOVE_PT_UI"
    bl_label = "GNRemove"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = UI_Setting.UI_ORDER_3DVIEW.GN_REMOVE.value

    def draw(self, context):
        self.layout.template_list("GN_REMOVE_UL_modifires_list", "", context.scene, "geonodes_list", context.scene, "geonodes_list_index")
        self.layout.operator("gn_remove.reload")
        self.layout.operator("gn_remove.remove")


# AOVの状況プロパティ表示の仕方
class GN_REMOVE_UL_modifires_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # print(data, item, active_data, active_propname)

        layout.prop(item, "name", text="", emboss=False)



# 設定用データ
# =================================================================================================
class GN_REMOVE_Item(bpy.types.PropertyGroup):
    name:  bpy.props.StringProperty()

modules = [
    GNRemove,
]

def register():
    bpy.types.Scene.geonodes_list = bpy.props.CollectionProperty(type=GN_REMOVE_Item)
    bpy.types.Scene.geonodes_list_index = bpy.props.IntProperty()  # template_list使うときはこれも必要

    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
