import bpy
from .CurveKey import key_points
from .CurveData import (
    CURVE_OBJECT_TYPES, get_structure, is_same_structure, get_channelbag, has_point_animation,
    group_point_channels, point_group_name, parse_point_path, make_lookup,
    to_semantic, from_semantic, read_point_values, write_point_values, ensure_float_attribute,
)

# アクティブな Curve / Curves から、選択中の同じ構成の Curve / Curves へコピーする
#   ・ポイント(座標・ハンドル・tilt・radius)のコピー
#   ・ポイントのアニメーション(キー)のコピー
# Curve <-> Curves の間でもコピーできる(カーブ数とカーブごとのポイント数が同じものが対象)

def get_copy_targets(context):
    src = context.active_object
    if context.mode != 'OBJECT' or src is None or src.type not in CURVE_OBJECT_TYPES:
        return None, []
    targets = [obj for obj in context.selected_objects if obj.type in CURVE_OBJECT_TYPES and obj != src]
    return src, targets


# キー(FCurveのキーフレーム)をそのまま写す
def copy_fcurve_keys(src_fc, dst_fc):
    points = dst_fc.keyframe_points
    while len(points) > 0:
        points.remove(points[0], fast=True)
    points.add(len(src_fc.keyframe_points))
    for s, d in zip(src_fc.keyframe_points, points):
        d.co = s.co
        d.interpolation = s.interpolation
        d.easing = s.easing
        d.handle_left_type = s.handle_left_type
        d.handle_right_type = s.handle_right_type
        d.handle_left = s.handle_left
        d.handle_right = s.handle_right
        d.back = s.back
        d.amplitude = s.amplitude
        d.period = s.period
        d.type = s.type
    dst_fc.extrapolation = src_fc.extrapolation
    dst_fc.update()

# コピー先の既存のポイントのアニメーションを消す
def clear_point_animation(obj):
    cb = get_channelbag(obj.data)
    if cb is None:
        return
    lookup = make_lookup(obj)
    remove = [(fc.data_path, fc.array_index) for fc in cb.fcurves
              if parse_point_path(obj, fc.data_path, lookup) is not None]
    for data_path, index in remove:
        fc = cb.fcurves.find(data_path, index=index)
        if fc is not None:
            cb.fcurves.remove(fc)
    for name in [g.name for g in cb.groups if len(g.channels) == 0]:
        group = cb.groups.get(name)
        if group is not None:
            cb.groups.remove(group)

# ポイントのアニメーションをコピーする。コピーしたチャンネル数を返す
def copy_point_animation(context, src, dst):
    src_cb = get_channelbag(src.data)
    if src_cb is None:
        return 0
    dst_structure = get_structure(dst)
    src_lookup = make_lookup(src)
    if dst.type == 'CURVES':
        ensure_float_attribute(dst.data, 'tilt')

    jobs = []
    for fc in src_cb.fcurves:
        r = parse_point_path(src, fc.data_path, src_lookup)
        if r is None or len(fc.keyframe_points) == 0:
            continue
        ci, pi, prop = r
        sem = to_semantic(src, prop, fc.array_index)
        if sem is None:
            continue
        target = from_semantic(dst, ci, pi, dst_structure[ci][0], *sem)
        if target is None:
            continue
        jobs.append((fc, target, point_group_name(ci, pi)))
    if not jobs:
        return 0

    clear_point_animation(dst)
    for src_fc, (data_path, index), group in jobs:
        # キーを1つ打って、Action / スロット / FCurve を用意してから中身を写す
        frame = src_fc.keyframe_points[0].co.x
        try:
            dst.data.keyframe_insert(data_path, index=index, frame=frame, group=group)
        except TypeError:
            # 配列でないプロパティ(tilt / radius など)は index を指定できない
            dst.data.keyframe_insert(data_path, frame=frame, group=group)
        dst_fc = get_channelbag(dst.data).fcurves.find(data_path, index=index)
        if dst_fc is not None:
            copy_fcurve_keys(src_fc, dst_fc)
    group_point_channels(dst)
    return len(jobs)


class OjaUtil_OT_CurveCopyPointsFromActive(bpy.types.Operator):
    bl_idname = "ojautil.curve_copy_points_from_active"
    bl_label = "Copy Points from Active"
    bl_description = "アクティブなCurve/Curvesのポイントを、選択中の同じ構成のCurve/Curvesへコピーする(アニメ付きなら現在フレームにキーも打つ)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        src, targets = get_copy_targets(context)
        return src is not None and len(targets) > 0

    def execute(self, context):
        src, targets = get_copy_targets(context)
        values = read_point_values(src)
        copied = []
        skipped = []
        for obj in targets:
            if not is_same_structure(src, obj):
                skipped.append(obj.name)
                continue
            write_point_values(obj, values)
            # アニメ付きは、フレーム移動で上書きされないよう現在フレームにキーを打つ
            if has_point_animation(obj):
                key_points(context, [obj], selected_only=False)
            copied.append(obj.name)

        if skipped:
            self.report({'WARNING'}, f"Copied {len(copied)}, skipped (structure mismatch): {', '.join(skipped)}")
        else:
            self.report({'INFO'}, f"Copied to {len(copied)} curves")
        return{'FINISHED'} if copied else {'CANCELLED'}


class OjaUtil_OT_CurveCopyAnimationFromActive(bpy.types.Operator):
    bl_idname = "ojautil.curve_copy_animation_from_active"
    bl_label = "Copy Animation from Active"
    bl_description = "アクティブなCurve/Curvesのポイントのキーを、選択中の同じ構成のCurve/Curvesへコピーする(コピー先のポイントのキーは置き換え)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        src, targets = get_copy_targets(context)
        return src is not None and len(targets) > 0 and get_channelbag(src.data) is not None

    def execute(self, context):
        src, targets = get_copy_targets(context)
        copied = []
        skipped = []
        for obj in targets:
            if not is_same_structure(src, obj):
                skipped.append(obj.name)
                continue
            if copy_point_animation(context, src, obj) > 0:
                copied.append(obj.name)
            else:
                skipped.append(obj.name)

        # 今のフレームの値を反映し直す
        context.scene.frame_set(context.scene.frame_current)

        if skipped:
            self.report({'WARNING'}, f"Copied {len(copied)}, skipped: {', '.join(skipped)}")
        else:
            self.report({'INFO'}, f"Copied animation to {len(copied)} curves")
        return{'FINISHED'} if copied else {'CANCELLED'}


classes = [
    OjaUtil_OT_CurveCopyPointsFromActive,
    OjaUtil_OT_CurveCopyAnimationFromActive,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
