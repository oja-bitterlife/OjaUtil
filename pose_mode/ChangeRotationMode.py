import bpy

class ChangeRotationModeOperator(bpy.types.Operator):
    bl_idname = "ojautil.pose.changerotationmode"
    bl_label = "ChangeRotationMode"

    def execute(self, context):
        return {'FINISHED'}


