import bpy
from . import UI_Setting

# 3DView Tools Panel
class FAST_RENDERING_PT_setting_ui(bpy.types.Panel):
    bl_idname = "FAST_RENDERING_PT_SETTING_UI"
    bl_label = "Fast Rendering"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY
    bl_order = UI_Setting.UI_ORDER_3DVIEW.FAST_RENDERING.value

    def draw(self, context):
        # 一括設定ボタン
        button_row = self.layout.row()
        button_row.operator("fast_rendering.fast")
        button_row.operator("fast_rendering.final")

        box = self.layout.box()

        # UseNodes ON/OFF
        box.prop(context.scene, 'use_nodes', text="Use Composit")

        row = box.row()
        # UseSimplify ON/OFF
        row.prop(context.scene.render, 'use_simplify', text="Simplify")
        # UseSingleLayer ON/OFF
        row.prop(context.scene.render, 'use_single_layer', text="Single Layer")



# 設定ボタン
# *************************************************************************************************
# 高速レンダリング用
class FAST_RENDERING_OT_fast(bpy.types.Operator):
    bl_idname = "fast_rendering.fast"
    bl_label = "Fast"

    # execute
    def execute(self, context):
        context.scene.use_nodes = False
        context.scene.render.use_simplify = True
        context.scene.render.use_single_layer = True
        return{'FINISHED'}


# 最終レンダリング用
class FAST_RENDERING_OT_final(bpy.types.Operator):
    bl_idname = "fast_rendering.final"
    bl_label = "Final"

    # execute
    def execute(self, context):
        context.scene.use_nodes = True
        context.scene.render.use_simplify = False
        context.scene.render.use_single_layer = False
        return{'FINISHED'}