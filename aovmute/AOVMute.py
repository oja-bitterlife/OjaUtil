import bpy
import json

# 定数
AOV_MUTE_PROPERTY_NAME = "AOV_MUTE"  # プロパティ名


# Main UI
# ===========================================================================================
# アドオンのリストを全部表示に
class AOV_MUTE_OT_show(bpy.types.Operator):
    bl_idname = "aov_mute.show"
    bl_label = "Show All"

    # execute
    def execute(self, context):
        for list in context.scene.aov_list:
            list.mute = False
        return{'FINISHED'}

# アドオンのリストを全部MUTEに
class AOV_MUTE_OT_mute(bpy.types.Operator):
    bl_idname = "aov_mute.mute"
    bl_label = "Mute All"

    # execute
    def execute(self, context):
        for list in context.scene.aov_list:
            list.mute = True
        return{'FINISHED'}


# 更新ボタン(リスト更新のみ)
# *************************************************************************************************
class AOV_MUTE_OT_reload(bpy.types.Operator):
    bl_idname = "aov_mute.reload"
    bl_label = "Reload List"

    # execute
    def execute(self, context):
        self.reload(context)
        return{'FINISHED'}

    # 同期
    def reload(self, context):
        # カスタムプロパティを取得しておく
        if context.view_layer.get(AOV_MUTE_PROPERTY_NAME) == None:
            PROPERTY_LIST = {}
        else:
            PROPERTY_LIST = json.loads(context.view_layer.get(AOV_MUTE_PROPERTY_NAME))

        # 存在するAOV情報を集める
        exists_aovs = {}
        for key in PROPERTY_LIST:  # カスタムプロパティ側
            exists_aovs[key] = {"type": PROPERTY_LIST[key]["type"], "mute": True}
        for aov in context.view_layer.aovs:  # AOV側(後にしてカスタムプロパティより優先されるように)
            exists_aovs[aov.name] = {"type": aov.type, "mute": False}

        # ソートしておく
        exists_aovs = dict(sorted(exists_aovs.items()))

        # アドオンのリストを存在するAOVのリストに変更
        context.scene.aov_list.clear()
        for aov_name in exists_aovs:
            item = context.scene.aov_list.add()
            item.name = aov_name
            item.type = exists_aovs[aov_name]["type"]
            item.mute = exists_aovs[aov_name]["mute"]


# 同期ボタン(これを押さないと反映されない)
# *************************************************************************************************
class AOV_MUTE_OT_sync(bpy.types.Operator):
    bl_idname = "aov_mute.sync"
    bl_label = "AOV Sync"

    # execute
    def execute(self, context):
        self.sync(context)
        return{'FINISHED'}

    # 同期
    def sync(self, context):
        # カスタムプロパティを取得しておく
        if context.view_layer.get(AOV_MUTE_PROPERTY_NAME) == None:
            PROPERTY_LIST = {}
        else:
            PROPERTY_LIST = json.loads(context.view_layer.get(AOV_MUTE_PROPERTY_NAME))


        # 存在しないAOVをアドオンのリストから除去
        # ---------------------------------------------------------------------
        exists_aovs = {}
        for list in context.scene.aov_list:
            if list == None or list.name == None or list.name == "":  # アドオンのリストがおかしい
                continue  # 除外する
            if context.view_layer.aovs.find(list.name) == -1:  # AOVにない
                if list.name not in PROPERTY_LIST: # プロパティにもない
                    continue  # 除外する
            exists_aovs[list.name] = {"type": list.type, "mute": list.mute}

        # ソートもしておく
        exists_aovs = dict(sorted(exists_aovs.items()))

        # アドオンのリストを存在するAOVのリストに変更
        context.scene.aov_list.clear()
        for aov_name in exists_aovs:
            item = context.scene.aov_list.add()
            item.name = aov_name
            item.type = exists_aovs[aov_name]["type"]
            item.mute = exists_aovs[aov_name]["mute"]


        # マージ処理
        # ---------------------------------------------------------------------
        # 現在のAOVの状態をアドオンのリストに反映
        for aov in context.view_layer.aovs:
            # アドンのリストに無ければ追加
            if context.scene.aov_list.get(aov.name) == None:
                item = context.scene.aov_list.add()
                item.name = aov.name
                item.type = aov.type
                item.mute = False
            # あればtype合わせ
            else:
                context.scene.aov_list.get(aov.name).type = aov.type

        # カスタムプロパティの状態をアドオンのリストに反映
        for prop_name in PROPERTY_LIST:
            # アドンのリストに無ければ追加
            # あれば無視(アドオンのリストが優先)
            if context.scene.aov_list.get(prop_name) == None:
                item = context.scene.aov_list.add()
                item.name = prop_name
                item.type = PROPERTY_LIST[prop_name]["type"]
                item.mute = True
            # あればtype合わせ
            else:
                context.scene.aov_list.get(prop_name).type = PROPERTY_LIST[prop_name]["type"]


        # アドオンのリストで更新
        # ---------------------------------------------------------------------
        # カスタムプロパティを更新
        AOV_MUTE = {}
        for list in context.scene.aov_list:
            if list.mute:
                AOV_MUTE[list.name] = {"type": list.type}
        context.view_layer[AOV_MUTE_PROPERTY_NAME] = json.dumps(AOV_MUTE)

        # AOVを更新
        for list in context.scene.aov_list:
            aov_index = context.view_layer.aovs.find(list.name)
            if list.mute:
                # AOVにあれば削除
                if aov_index != -1:
                    context.view_layer.active_aov_index = aov_index
                    bpy.ops.scene.view_layer_remove_aov()
            else:
                # AOVに無ければ追加
                if aov_index == -1:
                    aov = context.view_layer.aovs.add()
                    aov.name = list.name
                    aov.type = list.type


# =================================================================================================
classes = [
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
