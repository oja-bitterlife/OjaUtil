import bpy
from . import UI_Setting
from .aovmute import AOVMute


# AOVの状況UI
# ===========================================================================================
# 3DView Tools Panel
class AOV_MUTE_PT_render_ui(bpy.types.Panel):
    bl_idname = "AOV_MUTE_PT_RENDER_UI"
    bl_label = "Fast Rendering"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY
    bl_order = UI_Setting.UI_ORDER_3DVIEW.FAST_RENDERING.value

    def draw(self, context):
        box = self.layout.box()
        # UseNodes ON/OFF
        box.prop(context.scene, 'use_nodes', text="Use Composit")

        row = box.row()
        # UseSimplify ON/OFF
        row.prop(context.scene.render, 'use_simplify', text="Simplify")
        # UseSingleLayer ON/OFF
        row.prop(context.scene.render, 'use_single_layer', text="Single Layer")


# 3DView Tools Panel
class AOV_MUTE_PT_ui(bpy.types.Panel):
    bl_idname = "AOV_MUTE_PT_UI"
    bl_label = "AOV Mute"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = UI_Setting.UI_ORDER_3DVIEW.AOV_MUTE.value

    def draw(self, context):
        row = self.layout.row()
        row.operator("aov_mute.show")
        row.operator("aov_mute.mute")
        self.layout.template_list("AOV_MUTE_UL_aov_list", "", context.scene, "aov_list", context.scene, "aov_list_index")
        self.layout.operator("aov_mute.reload")
        self.layout.operator("aov_mute.sync")


# AOVの状況プロパティ表示の仕方
class AOV_MUTE_UL_aov_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # print(data, item, active_data, active_propname)

        if item.type == "COLOR":
            layout.prop(item, "type", text="", emboss=False, icon="EVENT_C", icon_only=True)
        else:
            layout.prop(item, "type", text="", emboss=False, icon="EVENT_V", icon_only=True)

        layout.prop(item, "name", text="", emboss=False)

        if item.mute == False:
            layout.prop(item, "mute", text="", emboss=False, icon="HIDE_OFF")
        else:
            layout.prop(item, "mute", text="", emboss=False, icon="HIDE_ON")


# 設定用データ
# =================================================================================================
class AOVItem(bpy.types.PropertyGroup):
    name:  bpy.props.StringProperty()
    mute:  bpy.props.BoolProperty()
    type:  bpy.props.StringProperty()

modules = [
    AOVMute,
]

def register():
    bpy.types.Scene.aov_list = bpy.props.CollectionProperty(type=AOVItem)
    bpy.types.Scene.aov_list_index = bpy.props.IntProperty()  # template_list使うときはこれも必要

    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
