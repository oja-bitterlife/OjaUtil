from enum import Enum, auto

UI_CATEGORY = "OjaUtil"  # アドオンのカテゴリ

class UI_ORDER_3DVIEW(Enum):
    FAST_RENDERING = auto()
    AOV_MUTE = auto()
    GN_REMOVE = auto()
    NODE_GROUP = auto()


# NodeTreeの画面確認
def is_shader_node(context):
    return context.space_data.tree_type == 'ShaderNodeTree'

def is_composit_node(context):
    return context.space_data.tree_type == 'CompositorNodeTree'
