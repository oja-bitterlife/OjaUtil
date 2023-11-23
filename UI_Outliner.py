import bpy
from . import UI_Setting
from .outliner import EnableHierarchy, CloseAll

# Main UI
# ===========================================================================================
# Outlinerのコレクションのメニューに追加するもの
def collection_menu_func(self, context):
    self.layout.separator()
    self.layout.operator("ojautil.outliner_enablehierarchy")
    self.layout.operator("ojautil.outliner_closeall")


# Outlinerのオブジェクトのメニューに追加するもの
def object_menu_func(self, context):
    self.layout.separator()
    self.layout.operator("ojautil.outliner_closeall")


modules = [
    EnableHierarchy,
    CloseAll,
]

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

    # アウトライナーは直接メニューに追加
    bpy.types.OUTLINER_MT_collection.append(collection_menu_func)
    bpy.types.OUTLINER_MT_object.append(object_menu_func)

def unregister():
    # メニューから消しておく(複数登録避け)
    bpy.types.OUTLINER_MT_collection.remove(collection_menu_func)
    bpy.types.OUTLINER_MT_object.remove(object_menu_func)

    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
