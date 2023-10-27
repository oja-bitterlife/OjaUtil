import bpy

# アウトライナのコレクションを全部Enableに
class EnableHierarchy(bpy.types.Operator):
    bl_idname = "ojautil.outliner_enablehierarchy"
    bl_label = "Enable Hierarchy"

    def execute(self, context):
        # 全ての選択コレクションとその子コレクションを対象に
        selected_collection = [x for x in context.selected_ids if x.bl_rna.identifier == 'Collection']
        all_collection = selected_collection.copy()
        for collection in selected_collection:
            all_collection += collection.children_recursive

        # 名前だけユニークで取り出す
        collection_names = set([collection.name for collection in all_collection])

        # 再帰でチェック
        EnableHierarchy.rec_check(context, bpy.context.view_layer.layer_collection, collection_names)

        return {'FINISHED'}

    # 入力レイヤーコレクションがコレクション名リストにあれば有効化する。子を再帰
    @classmethod
    def rec_check(cls, context, layer_collection, collection_names):
        if layer_collection.name in collection_names:  # 選択コレクションリストに含まれていれば
            layer_collection.exclude = False  # 有効化

        # 子もチェック
        for lc_child in layer_collection.children:
            EnableHierarchy.rec_check(context, lc_child, collection_names)


classes = [
    EnableHierarchy,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
