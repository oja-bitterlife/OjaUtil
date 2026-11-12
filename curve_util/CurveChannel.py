import bpy
import re
from .CurveData import (
    get_edit_objects, is_edit, get_channelbag, group_point_channels,
    point_group_name, parse_point_path, make_lookup, get_selected_points,
)

# 選択中のポイントのチャンネルだけを展開・選択して見つけやすくする(Curve / Curves)

GROUP_NAME_RE = re.compile(r'^S\d+ P\d+$')


class OjaUtil_OT_CurveFocusSelectedChannels(bpy.types.Operator):
    bl_idname = "ojautil.curve_focus_selected_channels"
    bl_label = "Focus Selected Channels"
    bl_description = "選択中のポイントのチャンネルだけを展開・選択する(グラフエディタでは他を非表示)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_edit(context)

    def execute(self, context):
        count = 0
        for obj in get_edit_objects(context):
            group_point_channels(obj)
            cb = get_channelbag(obj.data)
            if cb is None:
                continue
            selected = {point_group_name(ci, pi) for ci, pi in get_selected_points(obj)}

            # グループの展開・選択(ドープシート/グラフエディタ)
            for group in cb.groups:
                if not GROUP_NAME_RE.match(group.name):
                    continue
                on = group.name in selected
                group.show_expanded = on
                group.show_expanded_graph = on
                group.select = on
                count += on

            # FCurveの選択と、グラフエディタでの表示
            lookup = make_lookup(obj)
            for fc in cb.fcurves:
                if parse_point_path(obj, fc.data_path, lookup) is None:
                    continue
                on = fc.group is not None and fc.group.name in selected
                fc.select = on
                fc.hide = not on

        for area in context.screen.areas:
            if area.type in {'DOPESHEET_EDITOR', 'GRAPH_EDITOR'}:
                area.tag_redraw()

        self.report({'INFO'}, f"Focused {count} points")
        return{'FINISHED'}


classes = [
    OjaUtil_OT_CurveFocusSelectedChannels,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
