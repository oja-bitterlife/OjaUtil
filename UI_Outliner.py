import bpy
from .outliner import EnableHierarchy

# Main UI
# ===========================================================================================
# Outlinerのコレクションのメニューに追加するもの
def collection_menu_func(self, context):
    self.layout.separator()
    self.layout.operator("ojautil.outliner_enablehierarchy")

modules = [
    EnableHierarchy,
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
