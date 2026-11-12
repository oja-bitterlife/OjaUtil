import bpy
import re
from bpy_extras import anim_utils

# Curve(旧カーブ)と Curves(新カーブ)を同じように扱うための共通処理
# *****************************************************************************
# ポイントは「カーブ番号 + カーブ内のポイント番号」で扱う
#   Curve : splines[カーブ番号].points[ポイント番号]
#   Curves: points[カーブの先頭番号 + ポイント番号](全カーブ通しの番号)
#
# カーブ間でコピーするときは、プロパティを共通の名前(セマンティック)に置き換える
#   co(位置 xyz) / w(NURBSの重み) / tilt / radius / hl(左ハンドル) / hr(右ハンドル)

CURVE_OBJECT_TYPES = {'CURVE', 'CURVES'}

# Curves の curve_type アトリビュートの値
CURVES_TYPE_BEZIER = 2
CURVES_TYPE_NURBS = 3

# Curves のハンドルタイプ(handle_type_left/right の値) <-> Curve のハンドルタイプ
CURVES_HANDLE_TYPES = ('FREE', 'AUTO', 'VECTOR', 'ALIGNED')


def point_group_name(curve_index, point_index):
    return f"S{curve_index} P{point_index}"


# 編集モード
# *****************************************************************************
def get_edit_objects(context):
    if context.mode == 'EDIT_CURVE':
        obj_type = 'CURVE'
    elif context.mode == 'EDIT_CURVES':
        obj_type = 'CURVES'
    else:
        return []
    return [obj for obj in context.view_layer.objects if obj.type == obj_type and obj.mode == 'EDIT']

def is_edit(context):
    return len(get_edit_objects(context)) > 0


# アニメーション
# *****************************************************************************
def get_channelbag(id_data):
    ad = id_data.animation_data
    if ad is None or ad.action is None or ad.action_slot is None:
        return None
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)

def has_point_animation(obj):
    cb = get_channelbag(obj.data)
    if cb is None:
        return False
    lookup = make_lookup(obj)
    return any(parse_point_path(obj, fc.data_path, lookup) is not None for fc in cb.fcurves)


# 構造
# *****************************************************************************
def curves_ranges(data):
    return [(c.first_point_index, c.points_length) for c in data.curves]

def curves_kind(data, curve_index):
    attr = data.attributes.get('curve_type')
    value = attr.data[curve_index].value if attr is not None else 0
    if value == CURVES_TYPE_BEZIER:
        return 'BEZIER'
    if value == CURVES_TYPE_NURBS:
        return 'NURBS'
    return 'POLY'

# カーブごとの (タイプ, ポイント数) のリスト。タイプは 'BEZIER' / 'NURBS' / 'POLY'
def get_structure(obj):
    if obj.type == 'CURVE':
        result = []
        for spline in obj.data.splines:
            if spline.type == 'BEZIER':
                result.append(('BEZIER', len(spline.bezier_points)))
            else:
                result.append(('NURBS' if spline.type == 'NURBS' else 'POLY', len(spline.points)))
        return result
    data = obj.data
    return [(curves_kind(data, ci), size) for ci, (first, size) in enumerate(curves_ranges(data))]

# カーブ数とカーブごとのポイント数が同じなら、同じ構成とみなす(タイプは問わない)
def is_same_structure(src, dst):
    return [n for _, n in get_structure(src)] == [n for _, n in get_structure(dst)]

# Curves の通し番号 -> (カーブ番号, ポイント番号)
def make_lookup(obj):
    if obj.type != 'CURVES':
        return None
    data = obj.data
    lookup = [None] * len(data.points)
    for ci, (first, size) in enumerate(curves_ranges(data)):
        for pi in range(size):
            lookup[first + pi] = (ci, pi)
    return lookup

def ensure_float_attribute(data, name, fill=None):
    attr = data.attributes.get(name)
    if attr is None:
        attr = data.attributes.new(name, 'FLOAT', 'POINT')
        if fill is not None:
            for d in attr.data:
                d.value = fill
    return attr


# 選択
# *****************************************************************************
def _read_bool(attr):
    if attr.data_type == 'BOOLEAN':
        return [d.value for d in attr.data]
    return [d.value > 0.0 for d in attr.data]

# Curves の選択状態をポイントごとの bool のリストで返す(ハンドルの選択も含む)
def curves_point_selection(data):
    count = len(data.points)
    names = ('.selection', '.selection_handle_left', '.selection_handle_right')
    attrs = [data.attributes.get(n) for n in names]
    if attrs[0] is None:
        # 選択アトリビュートが無いときは全選択扱い
        return [True] * count
    result = [False] * count
    ranges = curves_ranges(data)
    for attr in attrs:
        if attr is None:
            continue
        values = _read_bool(attr)
        if attr.domain == 'CURVE':
            for ci, (first, size) in enumerate(ranges):
                if values[ci]:
                    for i in range(first, first + size):
                        result[i] = True
        else:
            for i, v in enumerate(values):
                if v:
                    result[i] = True
    return result

# (カーブ番号, ポイント番号, タイプ, 選択中か) を順番に返す
def iter_points(obj):
    if obj.type == 'CURVE':
        for si, spline in enumerate(obj.data.splines):
            if spline.type == 'BEZIER':
                for pi, p in enumerate(spline.bezier_points):
                    yield si, pi, 'BEZIER', (p.select_control_point or p.select_left_handle or p.select_right_handle)
            else:
                kind = 'NURBS' if spline.type == 'NURBS' else 'POLY'
                for pi, p in enumerate(spline.points):
                    yield si, pi, kind, p.select
        return
    data = obj.data
    selection = curves_point_selection(data)
    for ci, (first, size) in enumerate(curves_ranges(data)):
        kind = curves_kind(data, ci)
        for pi in range(size):
            yield ci, pi, kind, selection[first + pi]

def get_selected_points(obj):
    return {(ci, pi) for ci, pi, _, sel in iter_points(obj) if sel}


# データパス
# *****************************************************************************
LEGACY_PATH_RE = re.compile(r'^splines\[(\d+)\]\.(?:bezier_points|points)\[(\d+)\]\.(\w+)$')
CURVES_POINT_RE = re.compile(r'^points\[(\d+)\]\.(\w+)$')
CURVES_ATTR_RE = re.compile(r'^attributes\["([^"]+)"\]\.data\[(\d+)\]\.(\w+)$')
CURVES_ATTR_PROPS = {'tilt', 'nurbs_weight', 'handle_left', 'handle_right'}

# data_path から (カーブ番号, ポイント番号, プロパティ名) を返す。ポイントのパスでなければ None
def parse_point_path(obj, data_path, lookup=None):
    if obj.type == 'CURVE':
        m = LEGACY_PATH_RE.match(data_path)
        return (int(m[1]), int(m[2]), m[3]) if m else None
    m = CURVES_POINT_RE.match(data_path)
    if m:
        index, prop = int(m[1]), m[2]
    else:
        m = CURVES_ATTR_RE.match(data_path)
        if m is None or m[1] not in CURVES_ATTR_PROPS:
            return None
        index, prop = int(m[2]), m[1]
    if lookup is None:
        lookup = make_lookup(obj)
    if index >= len(lookup) or lookup[index] is None:
        return None
    ci, pi = lookup[index]
    return ci, pi, prop

# 1ポイント分のキーを打つデータパスのリスト
def point_paths(obj, ci, pi, kind):
    if obj.type == 'CURVE':
        if kind == 'BEZIER':
            base = f"splines[{ci}].bezier_points[{pi}]."
            return [base + p for p in ("co", "handle_left", "handle_right", "tilt", "radius")]
        base = f"splines[{ci}].points[{pi}]."
        return [base + p for p in ("co", "tilt", "radius")]
    data = obj.data
    g = data.curves[ci].first_point_index + pi
    paths = [f"points[{g}].position", f"points[{g}].radius", f'attributes["tilt"].data[{g}].value']
    if kind == 'BEZIER':
        paths += [f'attributes["handle_left"].data[{g}].vector', f'attributes["handle_right"].data[{g}].vector']
    elif kind == 'NURBS' and data.attributes.get('nurbs_weight') is not None:
        paths.append(f'attributes["nurbs_weight"].data[{g}].value')
    return paths

# (プロパティ名, 配列番号) -> (セマンティック, 成分)
def to_semantic(obj, prop, array_index):
    if obj.type == 'CURVE':
        if prop == 'co':
            return ('co', array_index) if array_index < 3 else ('w', 0)
        table = {'handle_left': 'hl', 'handle_right': 'hr', 'tilt': 'tilt', 'radius': 'radius'}
    else:
        table = {'position': 'co', 'radius': 'radius', 'tilt': 'tilt', 'nurbs_weight': 'w',
                 'handle_left': 'hl', 'handle_right': 'hr'}
    sem = table.get(prop)
    if sem is None:
        return None
    return sem, (array_index if sem in ('co', 'hl', 'hr') else 0)

# (セマンティック, 成分) -> コピー先の (data_path, 配列番号)。コピー先に無いものは None
def from_semantic(obj, ci, pi, kind, sem, comp):
    if obj.type == 'CURVE':
        if kind == 'BEZIER':
            base = f"splines[{ci}].bezier_points[{pi}]."
            table = {'co': 'co', 'hl': 'handle_left', 'hr': 'handle_right', 'tilt': 'tilt', 'radius': 'radius'}
            if sem not in table:
                return None
            return base + table[sem], comp
        base = f"splines[{ci}].points[{pi}]."
        if sem == 'co':
            return base + "co", comp
        if sem == 'w':
            return base + "co", 3
        if sem in ('tilt', 'radius'):
            return base + sem, 0
        return None
    data = obj.data
    g = data.curves[ci].first_point_index + pi
    if sem == 'co':
        return f"points[{g}].position", comp
    if sem == 'radius':
        return f"points[{g}].radius", 0
    if sem == 'tilt':
        ensure_float_attribute(data, 'tilt')
        return f'attributes["tilt"].data[{g}].value', 0
    if sem == 'w' and kind == 'NURBS':
        ensure_float_attribute(data, 'nurbs_weight', fill=1.0)
        return f'attributes["nurbs_weight"].data[{g}].value', 0
    if sem in ('hl', 'hr') and kind == 'BEZIER':
        name = 'handle_left' if sem == 'hl' else 'handle_right'
        return f'attributes["{name}"].data[{g}].vector', comp
    return None


# チャンネルをポイントごとにグループ化する
# *****************************************************************************
def group_point_channels(obj):
    cb = get_channelbag(obj.data)
    if cb is None:
        return
    lookup = make_lookup(obj)
    targets = []
    for fc in cb.fcurves:
        r = parse_point_path(obj, fc.data_path, lookup)
        if r is not None:
            targets.append((fc.data_path, fc.array_index, (r[0], r[1])))

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


# ポイントの値の読み書き(コピー用)
# *****************************************************************************
# {(カーブ番号, ポイント番号): {'co':(x,y,z), 'w', 'tilt', 'radius', 'hl', 'hr', 'hlt', 'hrt'}}
def read_point_values(obj):
    values = {}
    if obj.type == 'CURVE':
        for si, spline in enumerate(obj.data.splines):
            if spline.type == 'BEZIER':
                for pi, p in enumerate(spline.bezier_points):
                    values[(si, pi)] = {'co': tuple(p.co), 'tilt': p.tilt, 'radius': p.radius,
                                        'hl': tuple(p.handle_left), 'hr': tuple(p.handle_right),
                                        'hlt': p.handle_left_type, 'hrt': p.handle_right_type}
            else:
                for pi, p in enumerate(spline.points):
                    values[(si, pi)] = {'co': tuple(p.co.xyz), 'w': p.co.w, 'tilt': p.tilt, 'radius': p.radius}
        return values

    data = obj.data
    attrs = data.attributes
    tilt = attrs.get('tilt')
    weight = attrs.get('nurbs_weight')
    hl, hr = attrs.get('handle_left'), attrs.get('handle_right')
    hlt, hrt = attrs.get('handle_type_left'), attrs.get('handle_type_right')
    for ci, (first, size) in enumerate(curves_ranges(data)):
        kind = curves_kind(data, ci)
        for pi in range(size):
            g = first + pi
            v = {'co': tuple(data.points[g].position), 'radius': data.points[g].radius,
                 'tilt': tilt.data[g].value if tilt is not None else 0.0}
            if kind == 'NURBS':
                v['w'] = weight.data[g].value if weight is not None else 1.0
            if kind == 'BEZIER' and hl is not None and hr is not None:
                v['hl'] = tuple(hl.data[g].vector)
                v['hr'] = tuple(hr.data[g].vector)
                if hlt is not None and hrt is not None:
                    v['hlt'] = CURVES_HANDLE_TYPES[hlt.data[g].value] if hlt.data[g].value < 4 else 'FREE'
                    v['hrt'] = CURVES_HANDLE_TYPES[hrt.data[g].value] if hrt.data[g].value < 4 else 'FREE'
            values[(ci, pi)] = v
    return values

# 構成が同じ前提で、ポイントの値を書き込む(コピー先に無い項目は無視)
def write_point_values(obj, values):
    if obj.type == 'CURVE':
        for si, spline in enumerate(obj.data.splines):
            if spline.type == 'BEZIER':
                for pi, p in enumerate(spline.bezier_points):
                    v = values.get((si, pi))
                    if v is None:
                        continue
                    if 'hlt' in v:
                        p.handle_left_type = v['hlt']
                        p.handle_right_type = v['hrt']
                    p.co = v['co']
                    if 'hl' in v:
                        p.handle_left = v['hl']
                        p.handle_right = v['hr']
                    p.tilt = v['tilt']
                    p.radius = v['radius']
            else:
                for pi, p in enumerate(spline.points):
                    v = values.get((si, pi))
                    if v is None:
                        continue
                    x, y, z = v['co']
                    p.co = (x, y, z, v.get('w', p.co.w))
                    p.tilt = v['tilt']
                    p.radius = v['radius']
        obj.data.update_tag()
        return

    data = obj.data
    tilt = ensure_float_attribute(data, 'tilt')
    for ci, (first, size) in enumerate(curves_ranges(data)):
        kind = curves_kind(data, ci)
        for pi in range(size):
            v = values.get((ci, pi))
            if v is None:
                continue
            g = first + pi
            data.points[g].position = v['co']
            data.points[g].radius = v['radius']
            tilt.data[g].value = v['tilt']
            if kind == 'NURBS' and 'w' in v:
                ensure_float_attribute(data, 'nurbs_weight', fill=1.0).data[g].value = v['w']
            if kind == 'BEZIER' and 'hl' in v:
                if 'hlt' in v:
                    for name, t in (('handle_type_left', v['hlt']), ('handle_type_right', v['hrt'])):
                        attr = data.attributes.get(name)
                        if attr is not None and t in CURVES_HANDLE_TYPES:
                            attr.data[g].value = CURVES_HANDLE_TYPES.index(t)
                hl = data.attributes.get('handle_left')
                hr = data.attributes.get('handle_right')
                if hl is not None and hr is not None:
                    hl.data[g].vector = v['hl']
                    hr.data[g].vector = v['hr']
    data.update_tag()
