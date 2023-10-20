import bpy

# Main UI
# ===========================================================================================
# Compositing Tools Panel
class UI_PoseMode(bpy.types.Panel):
    bl_label = "Pose mode Util"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "OjaUtil"
    bl_idname = "OJA_UTIL_POSE"

    def draw(self, context):
        context.layout.operator("ojautil.pose.changerotationmode")
