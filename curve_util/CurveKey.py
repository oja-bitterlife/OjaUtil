import bpy
import re
from bpy_extras import anim_utils

# 編集中の(選択中の)Curveのポイント(ベジェはハンドル含む、tilt/radiusも)にキーを打つ

# キーを打つプロパティ
BEZIER_PROPS = ("co", "handle_left", "handle_right", "tilt", "radius")
POINT_PROPS = ("co", "tilt", "radius")

# 編集モード中のCurveを取得(マルチオブジェクト編集対応)
def get_edit_curves(context):
    if context.mode != 'EDIT_CURVE':
        return []
    return [obj for obj in context.view_layer.objects if obj.type == 'CURVE' and obj.mode == 'EDIT']

# Curveの編集モードのみ有効
def is_curve_edit(context):
    return len(get_edit_curves(context)) > 0

# チャンネルをポイントごとにグループ化する
# *****************************************************************************
POINT_PATH_RE = re.compile(r'^splines\[(\d+)\]\.(?:bezier_points|points)\[(\d+)\]\.')

def point_group_name(spline_index, point_index):
    return f"S{spline_index} P{point_index}"

def get_channelbag(id_data):
    ad = id_data.animation_data
    if ad is None or ad.action is None or ad.action_slot is None:
        return None
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)

def group_point_channels(obj):
    cb = get_channelbag(obj.data)
    if cb is None:
        return
    targets = []
    for fc in cb.fcurves:
        m = POINT_PATH_RE.match(fc.data_path)
        if m:
            targets.append((fc.data_path, fc.array_index, (int(m[1]), int(m[2]))))

    # グループを番号順に先に全部作る(作成後はFCurveを取り直す必要がある)
    for key in sorted({t[2] for t in targets}):
        name = point_group_name(*key)
        if cb.groups.get(name) is None:
            group = cb.groups.new(name)
            group.show_expanded = False
            group.show_expanded_graph = False

    for data_path, index, key in targets:
        name = point_group_name(*key)
        fc = cb.fcurves.find(data_path, index=index)
        if fc is not None and (fc.group is None or fc.group.name != name):
            fc.group = cb.groups[name]


# ポイントにキーを打つ(selected_only=Trueなら選択中のみ)
def key_points(context, selected_only):
    frame = context.scene.frame_current
    count = 0
    for obj in get_edit_curves(context):
        for spline in obj.data.splines:
            if spline.type == 'BEZIER':
                for point in spline.bezier_points:
                    if selected_only and not (point.select_control_point or point.select_left_handle or point.select_right_handle):
                        continue
                    for prop in BEZIER_PROPS:
                        point.keyframe_insert(prop, frame=frame)
                    count += 1
            else:  # NURBS / Poly
                for point in spline.points:
                    if selected_only and not point.select:
                        continue
                    for prop in POINT_PROPS:
                        point.keyframe_insert(prop, frame=frame)
                    count += 1
        group_point_channels(obj)
    return count


# 選択中のポイントのデータパスの先頭を集める
def get_selected_point_paths(obj):
    paths = []
    for si, spline in enumerate(obj.data.splines):
        if spline.type == 'BEZIER':
            for pi, point in enumerate(spline.bezier_points):
                if point.select_control_point or point.select_left_handle or point.select_right_handle:
                    paths.append(f"splines[{si}].bezier_points[{pi}].")
        else:
            for pi, point in enumerate(spline.points):
                if point.select:
                    paths.append(f"splines[{si}].points[{pi}].")
    return paths

# 選択中のポイントの現在フレームのキーを削除する(空になったチャンネルとグループも削除)
def delete_selected_point_keys(context):
    frame = context.scene.frame_current
    count = 0
    for obj in get_edit_curves(context):
        cb = get_channelbag(obj.data)
        if cb is None:
            continue
        prefixes = tuple(get_selected_point_paths(obj))
        if not prefixes:
            continue

        deleted_points = set()
        empty_fcurves = []
        for fc in cb.fcurves:
            if not fc.data_path.startswith(prefixes):
                continue
            for key in reversed(fc.keyframe_points):
                if abs(key.co.x - frame) < 0.001:
                    fc.keyframe_points.remove(key, fast=True)
                    deleted_points.add(fc.data_path.rsplit(".", 1)[0])
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


class OjaUtil_OT_CurveKeyAllPoints(bpy.types.Operator):
    bl_idname = "ojautil.curve_key_all_points"
    bl_label = "Add Key All Points"
    bl_description = "編集中の全Curveの全ポイントにキーを打つ"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_curve_edit(context)

    def execute(self, context):
        count = key_points(context, selected_only=False)
        self.report({'INFO'}, f"Keyed {count} points")
        return{'FINISHED'}


class OjaUtil_OT_CurveKeySelectedPoints(bpy.types.Operator):
    bl_idname = "ojautil.curve_key_selected_points"
    bl_label = "Add Key Selected Points"
    bl_description = "編集中の全Curveの選択中のポイントにキーを打つ"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_curve_edit(context)

    def execute(self, context):
        count = key_points(context, selected_only=True)
        if count == 0:
            self.report({'WARNING'}, "No points selected")
            return{'CANCELLED'}
        self.report({'INFO'}, f"Keyed {count} points")
        return{'FINISHED'}


class OjaUtil_OT_CurveDeleteKeySelectedPoints(bpy.types.Operator):
    bl_idname = "ojautil.curve_delete_key_selected_points"
    bl_label = "Delete Key Selected Points"
    bl_description = "編集中の全Curveの選択中のポイントから、現在フレームのキーを削除する"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_curve_edit(context)

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
