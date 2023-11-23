import bpy
from . import UI_Setting
from .shader import ChangeCM

# Main UI
# ===========================================================================================
# Compositing Tools Panel
class OjaUtil_PT_Shader_ui(bpy.types.Panel):
    bl_idname = "OJAUTIL_PT_SHADER_UI"
    bl_label = "ShaderUtil"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY

    def draw(self, context):
        # シェーダー画面のみ表示
        if UI_Setting.is_shader_node(context):
            self.layout.label(text="Set ColorSpace to selected nodes")
            row = self.layout.row()
            row.operator("ojautil.set_srgb")
            row.operator("ojautil.set_noncolor")



# register/unregister
# *****************************************************************************
modules = [
    ChangeCM,
]

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
