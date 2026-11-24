import bpy
import re
from .CurveData import get_edit_objects, get_channelbag, group_point_channels

# 選択中のポイントを削除し、残ったポイントのアニメーションの番号を付け替える(Curves専用)
# *****************************************************************************
# 旧Curveは、編集モード終了時にBlenderが自動でアニメーションの番号を付け替えるので対象外
# 削除前に各ポイントへ「元の通し番号」の目印(一時的なINTアトリビュート)を付け、
# 削除後に目印を読んで対応表を作る

TAG_ATTR = "_ojautil_orig_index"
POINT_GROUP_RE = re.compile(r'^S\d+ P\d+$')

CURVES_POINT_RE = re.compile(r'^points\[(\d+)\]\.(.+)$')
CURVES_ATTR_RE = re.compile(r'^(attributes\["[^"]+"\]\.data)\[(\d+)\]\.(.+)$')


# 目印
# *****************************************************************************
def tag_points(data):
    attr = data.attributes.get(TAG_ATTR)
    if attr is not None:
        data.attributes.remove(attr)
    attr = data.attributes.new(TAG_ATTR, 'INT', 'POINT')
    for g, d in enumerate(attr.data):
        d.value = g

# 目印を読んで {旧通し番号: 新通し番号} を作り、目印を片付ける
def read_tags(data):
    attr = data.attributes.get(TAG_ATTR)
    if attr is None:
        return None
    mapping = {d.value: g for g, d in enumerate(attr.data)}
    data.attributes.remove(data.attributes[TAG_ATTR])
    return mapping


# アニメーションの付け替え
# *****************************************************************************
# 旧データパス -> (旧通し番号, 新データパス or None(削除))。ポイントのパスでなければ None
def remap_path(path, mapping):
    m = CURVES_POINT_RE.match(path)
    if m:
        old = int(m[1])
        new = mapping.get(old)
        return old, (None if new is None else f"points[{new}].{m[2]}")
    m = CURVES_ATTR_RE.match(path)
    if m:
        old = int(m[2])
        new = mapping.get(old)
        return old, (None if new is None else f"{m[1]}[{new}].{m[3]}")
    return None

def remap_animation(obj, mapping):
    cb = get_channelbag(obj.data)
    if cb is None:
        return 0, 0
    to_remove = []
    to_rename = []
    for fc in cb.fcurves:
        r = remap_path(fc.data_path, mapping)
        if r is None:
            continue
        old, new_path = r
        if new_path is None:
            to_remove.append((fc.data_path, fc.array_index))
        elif new_path != fc.data_path:
            to_rename.append((old, fc.data_path, fc.array_index, new_path))

    # 消えたポイントのチャンネルを削除
    for path, index in to_remove:
        fc = cb.fcurves.find(path, index=index)
        if fc is not None:
            cb.fcurves.remove(fc)

    # 番号の小さい順に付け替える(新番号 <= 旧番号なので、先に空いた番号へ詰めていける)
    for old, path, index, new_path in sorted(to_rename, key=lambda t: (t[0], t[1], t[2])):
        fc = cb.fcurves.find(path, index=index)
        if fc is not None:
            fc.data_path = new_path

    # ポイント用のグループ(S0 P0 など)をいったん全部消してから、番号順に付け直す
    # (古い番号のグループが残っていると、付け替え中にグループが消えてズレるため)
    for name in [g.name for g in cb.groups if POINT_GROUP_RE.match(g.name)]:
        group = cb.groups.get(name)
        if group is not None:
            cb.groups.remove(group)
    group_point_channels(obj)
    for name in [g.name for g in cb.groups if len(g.channels) == 0]:
        group = cb.groups.get(name)
        if group is not None:
            cb.groups.remove(group)
    return len(to_remove), len(to_rename)


class OjaUtil_OT_CurveDeletePointsKeepAnim(bpy.types.Operator):
    bl_idname = "ojautil.curve_delete_points_keep_anim"
    bl_label = "Delete Points (Keep Anim)"
    bl_description = "Curvesの選択中のポイントを削除し、残ったポイントのアニメーションの番号を自動で付け替える"
    bl_options = {'REGISTER', 'UNDO'}

    # Curvesの編集モードのみ有効(旧CurveはBlender標準の削除で番号が付け替わる)
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_CURVES' and len(get_edit_objects(context)) > 0

    def execute(self, context):
        objs = get_edit_objects(context)
        for obj in objs:
            tag_points(obj.data)

        try:
            bpy.ops.curves.delete()
        except RuntimeError as e:
            for obj in objs:
                read_tags(obj.data)
            self.report({'ERROR'}, f"Delete failed: {e}")
            return{'CANCELLED'}

        removed = renamed = 0
        for obj in objs:
            mapping = read_tags(obj.data)
            if mapping is None:
                self.report({'WARNING'}, f"{obj.name}: could not track points, animation not remapped")
                continue
            r, n = remap_animation(obj, mapping)
            removed += r
            renamed += n
            obj.data.update_tag()

        self.report({'INFO'}, f"Deleted points. Channels removed {removed}, remapped {renamed}")
        return{'FINISHED'}


classes = [
    OjaUtil_OT_CurveDeletePointsKeepAnim,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
