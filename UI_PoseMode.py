import bpy
from .pose_mode import ChangeRotationMode

# Main UI
# ===========================================================================================
# Compositing Tools Panel
class UI_PoseMode(bpy.types.Panel):
    bl_label = "Pose mode Util"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OjaUtil"
    bl_idname = "OJA_UTIL_PT_POSE"

    def draw(self, context):
        self.layout.operator("ojautil.pose_changerotationmode")

modules = [
    ChangeRotationMode,
]

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
