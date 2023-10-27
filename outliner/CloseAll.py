import bpy

CLOSE_REPEAT = 100

# outlinerをcollapse
class CloseAll(bpy.types.Operator):
    bl_idname = "ojautil.outliner_closeall"
    bl_label = "Close All"

    def execute(self, context):
        for _ in range(CLOSE_REPEAT):
            bpy.ops.outliner.show_one_level(open=False)
        return {'FINISHED'}


classes = [
    CloseAll,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
