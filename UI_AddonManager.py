import bpy
from . import UI_Setting
from .outliner import AddonManager

# Main UI
# ===========================================================================================
class AddonManagerMenu(bpy.types.Menu):
    bl_idname = "OJAUTIL_MT_addon_manager_menu"
    bl_label = "AddonManager"

    def draw(self, context):
        # サブメニュー
        self.layout.operator("ojautil.outliner_load_addon_status")
        self.layout.operator("ojautil.outliner_save_addon_status")

# Outlinerのコレクションのメニューに追加するもの
def collection_menu_func(self, context):
    self.layout.separator()
    self.layout.menu(AddonManagerMenu.bl_idname)


modules = [
    AddonManager,
]

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

    # アウトライナーは直接メニューに追加
    bpy.types.OUTLINER_MT_collection.append(collection_menu_func)

def unregister():
    # メニューから消しておく(複数登録避け)
    bpy.types.OUTLINER_MT_collection.remove(collection_menu_func)

    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
