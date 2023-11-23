import bpy

class SetSRGB(bpy.types.Operator):
    bl_idname = "ojautil.set_srgb"
    bl_label = "sRGB"

    def execute(self, context):
        return{'FINISHED'}

class SetNonColor(bpy.types.Operator):
    bl_idname = "ojautil.set_noncolor"
    bl_label = "Non-Color"

    def execute(self, context):
        return{'FINISHED'}


classes = [
    SetSRGB,
    SetNonColor,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
