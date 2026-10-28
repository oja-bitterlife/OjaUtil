import bpy
from . import UI_Setting
from .curve_util import CurveKey, CurveChannel, CurveMirror, CurveCopy


# Main UI
# ===========================================================================================
# 3DView Tools Panel
class OjaUtil_PT_CurveUtil_ui(bpy.types.Panel):
    bl_idname = "OJAUTIL_PT_CURVEUTIL_UI"
    bl_label = "CurveUtil"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY
    bl_order = UI_Setting.UI_ORDER_3DVIEW.CURVE_UTIL.value

    def draw(self, context):
        col = self.layout.column(align=True)
        col.operator("ojautil.curve_key_all_points", icon='KEY_HLT')
        col.operator("ojautil.curve_key_selected_points", icon='KEY_HLT')
        col.operator("ojautil.curve_delete_key_selected_points", icon='KEY_DEHLT')
        col.operator("ojautil.curve_focus_selected_channels", icon='VIEWZOOM')

        col = self.layout.column(align=True)
        col.operator("ojautil.curve_apply_mirror_x", icon='MOD_MIRROR')
        col.operator("ojautil.curve_copy_points_from_active", icon='PASTEDOWN')


# register/unregister
# *****************************************************************************
modules = [
    CurveKey,
    CurveChannel,
    CurveMirror,
    CurveCopy,
]

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
