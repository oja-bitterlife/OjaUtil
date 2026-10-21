import bpy
import re
from .CurveKey import get_edit_curves, is_curve_edit, group_point_channels, get_channelbag, point_group_name, POINT_PATH_RE

# 選択中のポイントのチャンネルだけを展開・選択して見つけやすくする

GROUP_NAME_RE = re.compile(r'^S\d+ P\d+$')

# 選択中のポイントのグループ名を集める
def get_selected_point_names(obj):
    names = set()
    for si, spline in enumerate(obj.data.splines):
        if spline.type == 'BEZIER':
            for pi, point in enumerate(spline.bezier_points):
                if point.select_control_point or point.select_left_handle or point.select_right_handle:
                    names.add(point_group_name(si, pi))
        else:
            for pi, point in enumerate(spline.points):
                if point.select:
                    names.add(point_group_name(si, pi))
    return names


class OjaUtil_OT_CurveFocusSelectedChannels(bpy.types.Operator):
    bl_idname = "ojautil.curve_focus_selected_channels"
    bl_label = "Focus Selected Channels"
    bl_description = "選択中のポイントのチャンネルだけを展開・選択する(グラフエディタでは他を非表示)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_curve_edit(context)

    def execute(self, context):
        count = 0
        for obj in get_edit_curves(context):
            group_point_channels(obj)
            cb = get_channelbag(obj.data)
            if cb is None:
                continue
            selected = get_selected_point_names(obj)

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
            for fc in cb.fcurves:
                if not POINT_PATH_RE.match(fc.data_path):
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
