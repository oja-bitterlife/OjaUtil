import bpy
from .CurveData import (
    CURVE_OBJECT_TYPES, get_edit_objects, is_edit, get_channelbag, group_point_channels,
    iter_points, point_paths, point_group_name, parse_point_path, make_lookup,
    get_selected_points, ensure_float_attribute,
)

# 編集中の(選択中の)Curve / Curves のポイントにキーを打つ
#   Curve : co(ベジェはハンドルも) / tilt / radius
#   Curves: position / radius / tilt(ベジェはハンドル、NURBSは重みも)

# 互換用(他のモジュールから使われていた名前)
get_edit_curves = get_edit_objects
is_curve_edit = is_edit


# ポイントにキーを打つ(selected_only=Trueなら選択中のみ)
def key_points(context, objects, selected_only):
    frame = context.scene.frame_current
    count = 0
    for obj in objects:
        if obj.type == 'CURVES':
            ensure_float_attribute(obj.data, 'tilt')
        for ci, pi, kind, selected in list(iter_points(obj)):
            if selected_only and not selected:
                continue
            group = point_group_name(ci, pi)
            for path in point_paths(obj, ci, pi, kind):
                obj.data.keyframe_insert(path, frame=frame, group=group)
            count += 1
        group_point_channels(obj)
    return count


# 選択中のポイントの現在フレームのキーを削除する(空になったチャンネルとグループも削除)
def delete_selected_point_keys(context):
    frame = context.scene.frame_current
    count = 0
    for obj in get_edit_objects(context):
        cb = get_channelbag(obj.data)
        if cb is None:
            continue
        selected = get_selected_points(obj)
        if not selected:
            continue
        lookup = make_lookup(obj)

        deleted_points = set()
        empty_fcurves = []
        for fc in cb.fcurves:
            r = parse_point_path(obj, fc.data_path, lookup)
            if r is None or (r[0], r[1]) not in selected:
                continue
            for key in reversed(fc.keyframe_points):
                if abs(key.co.x - frame) < 0.001:
                    fc.keyframe_points.remove(key, fast=True)
                    deleted_points.add((r[0], r[1]))
            if len(fc.keyframe_points) == 0:
                empty_fcurves.append((fc.data_path, fc.array_index))
            else:
                fc.update()

        # 空になったチャンネルを削除(削除後はFCurveを取り直す必要がある)
        for data_path, index in empty_fcurves:
            fc = cb.fcurves.find(data_path, index=index)
            if fc is not None:
                cb.fcurves.remove(fc)

        # 空になったグループを削除
        for name in [g.name for g in cb.groups if len(g.channels) == 0]:
            group = cb.groups.get(name)
            if group is not None:
                cb.groups.remove(group)

        count += len(deleted_points)
    return count


# 全ポイントキーの対象(編集モード:編集中 / オブジェクトモード:選択中の Curve / Curves)
def get_all_points_target_curves(context):
    if context.mode in {'EDIT_CURVE', 'EDIT_CURVES'}:
        return get_edit_objects(context)
    if context.mode == 'OBJECT':
        return [obj for obj in context.selected_objects if obj.type in CURVE_OBJECT_TYPES]
    return []


class OjaUtil_OT_CurveKeyAllPoints(bpy.types.Operator):
    bl_idname = "ojautil.curve_key_all_points"
    bl_label = "Add Key All Points"
    bl_description = "編集中(オブジェクトモードでは選択中)の全Curve/Curvesの全ポイントにキーを打つ"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_all_points_target_curves(context)) > 0

    def execute(self, context):
        count = key_points(context, get_all_points_target_curves(context), selected_only=False)
        self.report({'INFO'}, f"Keyed {count} points")
        return{'FINISHED'}


class OjaUtil_OT_CurveKeySelectedPoints(bpy.types.Operator):
    bl_idname = "ojautil.curve_key_selected_points"
    bl_label = "Add Key Selected Points"
    bl_description = "編集中の全Curve/Curvesの選択中のポイントにキーを打つ"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_edit(context)

    def execute(self, context):
        count = key_points(context, get_edit_objects(context), selected_only=True)
        if count == 0:
            self.report({'WARNING'}, "No points selected")
            return{'CANCELLED'}
        self.report({'INFO'}, f"Keyed {count} points")
        return{'FINISHED'}


class OjaUtil_OT_CurveDeleteKeySelectedPoints(bpy.types.Operator):
    bl_idname = "ojautil.curve_delete_key_selected_points"
    bl_label = "Delete Key Selected Points"
    bl_description = "編集中の全Curve/Curvesの選択中のポイントから、現在フレームのキーを削除する"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_edit(context)

    def execute(self, context):
        count = delete_selected_point_keys(context)
        if count == 0:
            self.report({'WARNING'}, "No keys to delete")
            return{'CANCELLED'}
        self.report({'INFO'}, f"Deleted keys of {count} points")
        return{'FINISHED'}


classes = [
    OjaUtil_OT_CurveKeyAllPoints,
    OjaUtil_OT_CurveKeySelectedPoints,
    OjaUtil_OT_CurveDeleteKeySelectedPoints,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
