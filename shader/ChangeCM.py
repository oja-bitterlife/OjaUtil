import bpy

# 選択中のイメージテクスチャノードのカラースペースをまとめて変更する

class SetSRGB(bpy.types.Operator):
    bl_idname = "ojautil.set_srgb"
    bl_label = "sRGB"

    def execute(self, context):
        for node in context.selected_nodes:
            if node.type == "TEX_IMAGE":
                node.image.colorspace_settings.name = "sRGB"

        return{'FINISHED'}

class SetNonColor(bpy.types.Operator):
    bl_idname = "ojautil.set_noncolor"
    bl_label = "Non-Color"

    def execute(self, context):
        for node in context.selected_nodes:
            if node.type == "TEX_IMAGE":
                node.image.colorspace_settings.name = "Non-Color"

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
