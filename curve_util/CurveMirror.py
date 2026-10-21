import bpy
from mathutils import Matrix

# X軸のみ有効なMirrorモディファイアを、tiltを反転させつつ実体化して削除する

# X軸のみ有効なMirrorモディファイアを探す
def find_mirror_x(obj):
    if obj is None or obj.type != 'CURVE':
        return None
    for mod in obj.modifiers:
        if mod.type == 'MIRROR' and tuple(mod.use_axis) == (True, False, False):
            return mod
    return None

# ミラー変換行列(オブジェクトのローカル空間)
def get_mirror_matrix(obj, mod):
    mirror = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
    if mod.mirror_object is None:
        return mirror
    tmp = mod.mirror_object.matrix_world.inverted() @ obj.matrix_world
    return tmp.inverted() @ mirror @ tmp

# 全スプラインをミラーして追加する
def mirror_splines(curve, mtx):
    for spline in list(curve.splines):
        new = curve.splines.new(spline.type)
        if spline.type == 'BEZIER':
            new.bezier_points.add(len(spline.bezier_points) - 1)
            for src, dst in zip(spline.bezier_points, new.bezier_points):
                dst.handle_left_type = src.handle_left_type
                dst.handle_right_type = src.handle_right_type
                dst.co = mtx @ src.co
                dst.handle_left = mtx @ src.handle_left
                dst.handle_right = mtx @ src.handle_right
                dst.tilt = -src.tilt
                dst.radius = src.radius
                dst.weight_softbody = src.weight_softbody
        else:  # NURBS / Poly
            new.points.add(len(spline.points) - 1)
            for src, dst in zip(spline.points, new.points):
                co = mtx @ src.co.xyz
                dst.co = (co.x, co.y, co.z, src.co.w)
                dst.tilt = -src.tilt
                dst.radius = src.radius
                dst.weight = src.weight
                dst.weight_softbody = src.weight_softbody
            new.order_u = spline.order_u
            new.use_endpoint_u = spline.use_endpoint_u
            new.use_bezier_u = spline.use_bezier_u
        new.use_cyclic_u = spline.use_cyclic_u
        new.use_smooth = spline.use_smooth
        new.resolution_u = spline.resolution_u
        new.material_index = spline.material_index


class OjaUtil_OT_CurveApplyMirrorX(bpy.types.Operator):
    bl_idname = "ojautil.curve_apply_mirror_x"
    bl_label = "Apply Mirror X"
    bl_description = "X軸のみのMirrorモディファイアを実体化して削除する(tiltは反転)"
    bl_options = {'REGISTER', 'UNDO'}

    # X軸のみのMirrorがついたCurveのみ有効
    @classmethod
    def poll(cls, context):
        return find_mirror_x(context.active_object) is not None

    def execute(self, context):
        obj = context.active_object
        mod = find_mirror_x(obj)

        # 編集モードならいったんオブジェクトモードで処理する
        was_edit = (obj.mode == 'EDIT')
        if was_edit:
            bpy.ops.object.mode_set(mode='OBJECT')

        mirror_splines(obj.data, get_mirror_matrix(obj, mod))
        name = mod.name
        obj.modifiers.remove(mod)

        if was_edit:
            bpy.ops.object.mode_set(mode='EDIT')

        self.report({'INFO'}, f"Applied {name}")
        return{'FINISHED'}


classes = [
    OjaUtil_OT_CurveApplyMirrorX,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
