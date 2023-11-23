from enum import Enum, auto

UI_CATEGORY = "OjaUtil"  # アドオンのカテゴリ

class UI_ORDER(Enum):
    FAST_RENDERING = auto()
    AOV_MUTE = auto()


# NodeTreeの画面確認
def is_shader_node(context):
    return context.space_data.tree_type == 'ShaderNodeTree'

def is_composit_node(context):
    return context.space_data.tree_type == 'CompositorNodeTree'
