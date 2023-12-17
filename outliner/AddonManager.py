import bpy, addon_utils


# Utility
# ===========================================================================================
# コレクション名を元にLayerCollection(Outliner上のcollectionクラス)を取得する
def get_layer_collection(layer_collection, target_name):
    # LayerCollectionを見つけた
    if layer_collection.name == target_name:
        return layer_collection

    # 再帰チェック
    for child in layer_collection.children:
        collection = get_layer_collection(child, target_name)
        if collection:
            return collection

    # 見つからなかった
    return None


# Addonの状態を調べる
# ===========================================================================================
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

# コレクションツリーをたぐりながら、オブジェクトの状態をaddonの状態に合わせる
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
                obj.hide_set(not (addon_enabled and addon_loaded))
            else:
                obj.hide_render = True
                obj.hide_set(True)

    # コレクションの有効/無効関係なくツリーはたぐる
    for child in layer_collection.children:
        load_addon_status(child, from_mod_names, from_addon_names)


# Addonの状態を変更する
# ===========================================================================================
class SaveStatus(bpy.types.Operator):
    bl_idname = "ojautil.outliner_save_addon_status"
    bl_label = "Save Addon Status"

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
        save_addon_status(layer_collection, from_mod_names, from_addon_names)
        return {'FINISHED'}

# コレクションツリーをたぐりながら、オブジェクトの状態をaddonの状態に合わせる
def save_addon_status(layer_collection, from_mod_names, from_addon_names):
    # コレクションが有効かチェック
    if layer_collection.exclude == False:
        # オブジェクトを処理
        for obj in layer_collection.collection.objects:
            # インストールされているか(モジュール名優先)
            if obj.name in from_mod_names or obj.name in from_addon_names:
                # 引っかかった名前でモジュール取得
                if obj.name in from_mod_names:  # 優先
                    mod = from_mod_names[obj.name]
                else:
                    mod = from_addon_names[obj.name]

                # 現在の有効/無効状態取得
                outliner_enabled = not obj.hide_get()
                addon_enabled, addon_loaded = addon_utils.check(mod.__name__)

                if outliner_enabled != (addon_enabled and addon_loaded):
                    if outliner_enabled:
                        addon_utils.enable(mod.__name__, default_set=True)
                        print("enable: " + mod.__name__)
                    else:
                        addon_utils.disable(mod.__name__, default_set=True)
                        print("disable: " + mod.__name__)
            else:
                obj.hide_render = True  # インストールされてなかったことを通知



    # コレクションの有効/無効関係なくツリーはたぐる
    for child in layer_collection.children:
        save_addon_status(child, from_mod_names, from_addon_names)


# register/unregister
# *****************************************************************************
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
