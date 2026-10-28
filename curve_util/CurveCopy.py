import bpy
from .CurveKey import key_points

# アクティブなCurveのポイント(座標・ハンドル・tilt・radius)を、選択中の他のCurveへコピーする
# スプライン数・タイプ・ポイント数が一致するCurveのみ対象

def get_copy_targets(context):
    src = context.active_object
    if context.mode != 'OBJECT' or src is None or src.type != 'CURVE':
        return None, []
    targets = [obj for obj in context.selected_objects if obj.type == 'CURVE' and obj != src]
    return src, targets

# スプライン構成が一致しているか
def is_same_structure(src_curve, dst_curve):
    if len(src_curve.splines) != len(dst_curve.splines):
        return False
    for a, b in zip(src_curve.splines, dst_curve.splines):
        if a.type != b.type:
            return False
        if a.type == 'BEZIER':
            if len(a.bezier_points) != len(b.bezier_points):
                return False
        elif len(a.points) != len(b.points):
            return False
    return True

def copy_points(src_curve, dst_curve):
    for a, b in zip(src_curve.splines, dst_curve.splines):
        if a.type == 'BEZIER':
            for sp, dp in zip(a.bezier_points, b.bezier_points):
                dp.handle_left_type = sp.handle_left_type
                dp.handle_right_type = sp.handle_right_type
                dp.co = sp.co
                dp.handle_left = sp.handle_left
                dp.handle_right = sp.handle_right
                dp.tilt = sp.tilt
                dp.radius = sp.radius
        else:
            for sp, dp in zip(a.points, b.points):
                dp.co = sp.co
                dp.tilt = sp.tilt
                dp.radius = sp.radius


class OjaUtil_OT_CurveCopyPointsFromActive(bpy.types.Operator):
    bl_idname = "ojautil.curve_copy_points_from_active"
    bl_label = "Copy Points from Active"
    bl_description = "アクティブなCurveのポイントを、選択中の同じ構成のCurveへコピーする(アニメ付きなら現在フレームにキーも打つ)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        src, targets = get_copy_targets(context)
        return src is not None and len(targets) > 0

    def execute(self, context):
        src, targets = get_copy_targets(context)
        copied = []
        skipped = []
        for obj in targets:
            if not is_same_structure(src.data, obj.data):
                skipped.append(obj.name)
                continue
            copy_points(src.data, obj.data)
            # アニメ付きのCurveは、フレーム移動で上書きされないよう現在フレームにキーを打つ
            ad = obj.data.animation_data
            if ad is not None and ad.action is not None:
                key_points(context, [obj], selected_only=False)
            obj.data.update_tag()
            copied.append(obj.name)

        if skipped:
            self.report({'WARNING'}, f"Copied {len(copied)}, skipped (structure mismatch): {', '.join(skipped)}")
        else:
            self.report({'INFO'}, f"Copied to {len(copied)} curves")
        return{'FINISHED'} if copied else {'CANCELLED'}


classes = [
    OjaUtil_OT_CurveCopyPointsFromActive,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
