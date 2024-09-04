import bpy
import os.path

TARGET_NODE_GROUPS = [
    # Material
    "OjaNPR2024.9.4",
    "OjaSpec2024.9",
    # World
    "OjaWorldSpace2023.11",
    # GeometryNodes
    "OjaGN_Billboard_ZRot",
    "OjaGN_GostBlur2023.11",
    "OjaGetLightVec",
    # Compositing
    "OjaCOMPIL_Normal",
]

APPEND_BUTTON_LABEL = "Append NodeGroups"


# Append NodeGroups
# *****************************************************************************
class AppendNodeGroups(bpy.types.Operator):
    bl_idname = "ojautil.append_nodegroups"
    bl_label = APPEND_BUTTON_LABEL

    def execute(self, context):
        # すでに全部読み込んであれば何もしない
        if all([bpy.data.node_groups.get(ng) != None for ng in TARGET_NODE_GROUPS]):
            return{'FINISHED'}

        # データ転送
        script_file = os.path.realpath(__file__)
        resource_file = os.path.join(os.path.dirname(script_file), "resource", "resource.blend")

        with bpy.data.libraries.load(resource_file, link=False, relative=True) as (data_from, data_to):
            for ng in data_from.node_groups:
                # 追加対象のみ処理
                if ng in TARGET_NODE_GROUPS:
                    if bpy.data.node_groups.get(ng):  # 存在すればなにもしない
                        continue
                    else:
                        data_to.node_groups.append(ng)
                        print("append:", ng)

        return{'FINISHED'}


# register/unregister
# *****************************************************************************
classes = [
    AppendNodeGroups,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

