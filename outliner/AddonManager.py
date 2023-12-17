import bpy, addon_utils

# outlinerをcollapse
class LoadStatus(bpy.types.Operator):
    bl_idname = "ojautil.outliner_load_addon_status"
    bl_label = "Load Addon Status"

    def execute(self, context):
        # レイヤーコレクションを取得する
        layer_collection = get_layer_collection(context.view_layer.layer_collection, context.id.name)
        if layer_collection == None:
            self.report({'ERROR'}, "コレクションが見つかりません: " + context.id.name)
            return {'FINISHED'}

        # アドオン情報
        from_mod_names = {mod.__name__:mod for mod in addon_utils.modules()}  # モジュール名ベース
        from_addon_names = {mod.bl_info["name"]:mod for mod in addon_utils.modules()}  # アドオン名ベース

        # オブジェクトに情報を反映させる
        load_addon_status(layer_collection, from_mod_names, from_addon_names)
        return {'FINISHED'}

# コレクション名を元にLayerCollection(Outliner上のcollectionクラス)を取得する
def get_layer_collection(layer_collection, target_name):
    for child in layer_collection.children:
        # LayerCollectionを見つけた
        if child.name == target_name:
            return child
        # 再帰チェック
        return get_layer_collection(child, target_name)

    # 見つからなかった
    return None

def load_addon_status(layer_collection, from_mod_names, from_addon_names):
    # コレクションが有効かチェック
    if layer_collection.exclude == False:
        # オブジェクトを処理
        for obj in layer_collection.collection.objects:
            # インストールされているか(モジュール名優先)
            if obj.name in from_mod_names or obj.name in from_addon_names:
                obj.hide_render = False

                # 引っかかった名前でモジュール取得
                if obj.name in from_mod_names:  # 優先
                    mod = from_mod_names[obj.name]
                else:
                    mod = from_addon_names[obj.name]

                # 有効になっているか
                addon_enabled, addon_loaded = addon_utils.check(mod.__name__)
                obj.hide_set(not addon_enabled)
            else:
                obj.hide_render = True
                obj.hide_set(True)

    # コレクションの有効/無効関係なくツリーはたぐる
    for child in layer_collection.children:
        load_addon_status(child, from_mod_names, from_addon_names)


class SaveStatus(bpy.types.Operator):
    bl_idname = "ojautil.outliner_save_addon_status"
    bl_label = "Save Addon Status"

    def execute(self, context):
        return {'FINISHED'}


classes = [
    LoadStatus,
    SaveStatus,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
