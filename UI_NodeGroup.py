import bpy
from . import UI_Setting
from .node_group import AppendNodes

APPEND_NODE_LABEL = "NodeGroupUtil"

# Main UI
# ===========================================================================================
# Compositing Tools Panel
class OjaUtil_PT_nodegroup_ui(bpy.types.Panel):
    bl_idname = "OJAUTIL_PT_NODEEDIT_UI"
    bl_label = APPEND_NODE_LABEL
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = UI_Setting.UI_CATEGORY

    def draw(self, context):
        self.layout.operator("ojautil.append_nodegroups")


# register/unregister
# *****************************************************************************
modules = [
    AppendNodes,
]

def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, "unregister"):
            module.unregister()
