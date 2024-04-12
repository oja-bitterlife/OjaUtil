import bpy


# Main UI
# ===========================================================================================
# 更新ボタン(リスト更新のみ)
# *************************************************************************************************
class GN_REMOVE_OT_reload(bpy.types.Operator):
    bl_idname = "gn_remove.reload"
    bl_label = "Reload List"

    # execute
    def execute(self, context):
        self.reload(context)
        return{'FINISHED'}

    # 同期
    def reload(self, context):
        # 選択中のオブジェクトが対象
        objects = [obj for obj in context.selected_objects]

        # 使われているGeometryNodesを回収する
        geonodes_list = {}
        for obj in objects:
            for mod in obj.modifiers:
                if mod.type == "NODES":
                    geonodes_list[mod.name] = mod

        # リストを更新する
        context.scene.geonodes_list.clear()
        for geonodes_name in geonodes_list.keys():
            item = context.scene.geonodes_list.add()
            item.name = geonodes_name


# 削除ボタン
# *************************************************************************************************
class GN_REMOVE_OT_remove(bpy.types.Operator):
    bl_idname = "gn_remove.remove"
    bl_label = "Remove"

    # execute
    def execute(self, context):
        self.remove(context)
        return{'FINISHED'}

    # 同期
    def remove(self, context):
        index = context.scene.geonodes_list_index
        select_geonodes_name = context.scene.geonodes_list[index].name

        # 選択中のオブジェクトが対象
        objects = [obj for obj in context.selected_objects]

        # 指定したGeoNodesなら削除する
        for obj in objects:
            for mod in obj.modifiers:
                if mod.type == "NODES" and mod.name == select_geonodes_name:
                    obj.modifiers.remove(mod)

        # リストも削除しておく
        context.scene.geonodes_list.remove(index)


# =================================================================================================
classes = [
    GN_REMOVE_OT_reload,
    GN_REMOVE_OT_remove,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
