import bpy
from . import UI_Setting
from .curve_key import CurveKey


# Main UI
# ===========================================================================================
# 3DView Tools Panel
class OjaUtil_PT_CurveKey_ui(bpy.types.Panel):
    bl_idname = "OJAUTIL_PT_CURVEKEY_UI"
    bl_label = "Curve Key"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY
    bl_order = UI_Setting.UI_ORDER_3DVIEW.CURVE_KEY.value

    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator("ojautil.curve_key_all_points", icon='KEY_HLT')
        col.operator("ojautil.curve_key_selected_points", icon='KEY_HLT')


# register/unregister
# *****************************************************************************
modules = [
    CurveKey,
]

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
