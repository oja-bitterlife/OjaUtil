import bpy
import re
from .CurveData import (
    get_edit_objects, is_edit, get_channelbag, group_point_channels,
    point_group_name, parse_point_path, make_lookup, get_selected_points,
)

# 選択中のポイントのチャンネルだけを展開・選択し、現在フレームのキーを選択する(Curve / Curves)

GROUP_NAME_RE = re.compile(r'^S\d+ P\d+$')

# 選択中のポイントのチャンネルを展開・選択する(グラフエディタでは他を非表示)
def focus_channels(obj, selected):
    cb = get_channelbag(obj.data)
    if cb is None:
        return
    names = {point_group_name(ci, pi) for ci, pi in selected}

    # グループの展開・選択(ドープシート/グラフエディタ)
    for group in cb.groups:
        if not GROUP_NAME_RE.match(group.name):
            continue
        on = group.name in names
        group.show_expanded = on
        group.show_expanded_graph = on
        group.select = on

    # FCurveの選択と、グラフエディタでの表示
    lookup = make_lookup(obj)
    for fc in cb.fcurves:
        if parse_point_path(obj, fc.data_path, lookup) is None:
            continue
        on = fc.group is not None and fc.group.name in names
        fc.select = on
        fc.hide = not on

# 選択中のポイントの現在フレームのキーだけを選択する(他のキーは選択解除)。選択したキー数を返す
def select_frame_keys(obj, selected, frame):
    cb = get_channelbag(obj.data)
    if cb is None:
        return 0
    count = 0
    lookup = make_lookup(obj)
    for fc in cb.fcurves:
        r = parse_point_path(obj, fc.data_path, lookup)
        if r is None:
            continue
        target = (r[0], r[1]) in selected
        for key in fc.keyframe_points:
            on = target and abs(key.co.x - frame) < 0.001
            key.select_control_point = on
            key.select_left_handle = False
            key.select_right_handle = False
            count += on
    return count


class OjaUtil_OT_CurveFocusSelectedChannels(bpy.types.Operator):
    bl_idname = "ojautil.curve_focus_selected_channels"
    bl_label = "Focus Frame Keys"
    bl_description = "選択中のポイントのチャンネルを展開・選択し(グラフエディタでは他を非表示)、現在フレームのキーだけを選択する"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_edit(context)

    def execute(self, context):
        frame = context.scene.frame_current
        points = 0
        keys = 0
        for obj in get_edit_objects(context):
            group_point_channels(obj)
            selected = get_selected_points(obj)
            focus_channels(obj, selected)
            keys += select_frame_keys(obj, selected, frame)
            points += len(selected)

        for area in context.screen.areas:
            if area.type in {'DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'TIMELINE'}:
                area.tag_redraw()

        if keys == 0:
            self.report({'WARNING'}, f"Focused {points} points, no keys at current frame")
        else:
            self.report({'INFO'}, f"Focused {points} points, selected {keys} keys")
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
