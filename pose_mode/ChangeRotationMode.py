import bpy

class ChangeRotationMode(bpy.types.Operator):
    bl_idname = "ojautil.pose_changerotationmode"
    bl_label = "ChangeRotationMode"

    def execute(self, context):
        return {'FINISHED'}

classes = [
    ChangeRotationMode,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
