import bpy

# アクティブなCurveのポイント(ベジェはハンドル含む)にキーを打つ

# Curveの編集モードのみ有効
def is_curve_edit(context):
    obj = context.active_object
    return obj is not None and obj.type == 'CURVE' and context.mode == 'EDIT_CURVE'

# ポイントにキーを打つ(selected_only=Trueなら選択中のみ)
def key_points(context, selected_only):
    frame = context.scene.frame_current
    count = 0
    for spline in context.active_object.data.splines:
        if spline.type == 'BEZIER':
            for point in spline.bezier_points:
                if selected_only and not (point.select_control_point or point.select_left_handle or point.select_right_handle):
                    continue
                for prop in ("co", "handle_left", "handle_right"):
                    point.keyframe_insert(prop, frame=frame)
                count += 1
        else:  # NURBS / Poly
            for point in spline.points:
                if selected_only and not point.select:
                    continue
                point.keyframe_insert("co", frame=frame)
                count += 1
    return count


class OjaUtil_OT_CurveKeyAllPoints(bpy.types.Operator):
    bl_idname = "ojautil.curve_key_all_points"
    bl_label = "Key All Points"
    bl_description = "アクティブなCurveの全ポイントにキーを打つ"
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
    bl_label = "Key Selected Points"
    bl_description = "アクティブなCurveの選択中のポイントにキーを打つ"
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


classes = [
    OjaUtil_OT_CurveKeyAllPoints,
    OjaUtil_OT_CurveKeySelectedPoints,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
