"""5^12 6^2 cage: equal-edge wireframe, Y-axis frames, guest jitter.

The polyhedron is the sI large cage (tetrakaidecahedron): two opposite
hexagons and twelve pentagons. Coordinates are four hexagonal rings with
edge length 1, solved so the vertices sit on a narrow radial band.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import motion

FRAMES = 36
DUR = f"{motion.MOTION['cage_dur_s']}s"
_PITCH = math.radians(20)
_CAM = 7.5

# Ring radii and heights. Edge length is 1; radial span stays near 1.51–1.62.
_RA = 1.0
_ZA = 1.13125
_RB = 1.58281
_ZB = 0.31869
_RC = 1.51656
_ZC = -0.27494


def _rings():
    verts = []
    for k in range(6):
        angle = k * math.pi / 3
        verts.append((_RA * math.cos(angle), _RA * math.sin(angle), _ZA))
    for k in range(6):
        angle = k * math.pi / 3
        verts.append((_RB * math.cos(angle), _RB * math.sin(angle), _ZB))
    for k in range(6):
        angle = k * math.pi / 3 + math.pi / 6
        verts.append((_RC * math.cos(angle), _RC * math.sin(angle), _ZC))
    for k in range(6):
        angle = k * math.pi / 3 + math.pi / 6
        verts.append((_RA * math.cos(angle), _RA * math.sin(angle), -_ZA))
    return verts


def _edges():
    edges = []
    for k in range(6):
        edges.append((k, (k + 1) % 6))
        edges.append((18 + k, 18 + (k + 1) % 6))
        edges.append((k, 6 + k))
        edges.append((6 + k, 12 + k))
        edges.append((6 + k, 12 + (k - 1) % 6))
        edges.append((12 + k, 18 + k))
    return edges


def _order_neighbors(index, neighbors, verts):
    ox, oy, oz = verts[index]
    length = math.sqrt(ox * ox + oy * oy + oz * oz) or 1.0
    nx, ny, nz = ox / length, oy / length, oz / length
    ax, ay, az = (0.0, 1.0, 0.0) if abs(ny) < 0.9 else (1.0, 0.0, 0.0)
    ux = ny * az - nz * ay
    uy = nz * ax - nx * az
    uz = nx * ay - ny * ax
    ul = math.sqrt(ux * ux + uy * uy + uz * uz) or 1.0
    ux, uy, uz = ux / ul, uy / ul, uz / ul
    vx = ny * uz - nz * uy
    vy = nz * ux - nx * uz
    vz = nx * uy - ny * ux

    def angle(other):
        dx = verts[other][0] - ox
        dy = verts[other][1] - oy
        dz = verts[other][2] - oz
        return math.atan2(dx * vx + dy * vy + dz * vz, dx * ux + dy * uy + dz * uz)

    return sorted(neighbors, key=angle)


def _walk_faces(verts, edges, step):
    neighbors = {i: [] for i in range(len(verts))}
    for left, right in edges:
        neighbors[left].append(right)
        neighbors[right].append(left)
    order = {i: _order_neighbors(i, nlist, verts) for i, nlist in neighbors.items()}
    directed = [(a, b) for a, b in edges] + [(b, a) for a, b in edges]
    used = set()
    faces = []
    for start_a, start_b in directed:
        if (start_a, start_b) in used:
            continue
        face = []
        a, b = start_a, start_b
        for _ in range(len(verts) + 2):
            if (a, b) in used and face:
                break
            used.add((a, b))
            face.append(a)
            nxt = order[b]
            b, a = nxt[(nxt.index(a) + step) % len(nxt)], b
        else:
            continue
        if len(face) >= 3:
            faces.append(face)
    unique = []
    seen = set()
    for face in faces:
        key = tuple(sorted(face))
        if key in seen:
            continue
        seen.add(key)
        unique.append(face)
    return unique


def polyhedron():
    verts = _rings()
    edges = _edges()
    faces = _walk_faces(verts, edges, -1)
    if sorted(len(face) for face in faces).count(5) != 12:
        faces = _walk_faces(verts, edges, 1)
    return verts, edges, faces


def _rot_x(x, y, z, angle):
    c, s = math.cos(angle), math.sin(angle)
    return x, y * c - z * s, y * s + z * c


def _rot_y(x, y, z, angle):
    c, s = math.cos(angle), math.sin(angle)
    return x * c + z * s, y, -x * s + z * c


def _project(x, y, z, cx, cy, scale):
    factor = _CAM / (_CAM - z)
    return cx + x * scale * factor, cy - y * scale * factor


def _num(value):
    text = f"{value:.1f}"
    return "0.0" if text == "-0.0" else text


def _segment(x0, y0, x1, y1):
    return f"M{_num(x0)} {_num(y0)}L{_num(x1)} {_num(y1)}"


def _posed(verts, yaw):
    posed = []
    for x, y, z in verts:
        x, y, z = _rot_x(x, y, z, _PITCH)
        posed.append(_rot_y(x, y, z, yaw))
    return posed


def _shade(depth, near, far):
    span = near - far
    unit = 0.0 if span == 0 else (depth - far) / span
    unit = min(1.0, max(0.0, unit))
    # Far edges stay readable; near edges are about twice the previous 0.9–1.8 px.
    return 0.28 + 0.72 * unit, 1.35 + 1.55 * unit, unit


def _mix_white(color, amount=0.62):
    raw = color.lstrip("#")
    parts = []
    for index in (0, 2, 4):
        channel = int(raw[index : index + 2], 16)
        mixed = int(round(channel * (1 - amount) + 255 * amount))
        parts.append(f"{mixed:02x}")
    return "#" + "".join(parts)


def _face_nz(posed, face):
    nx = ny = nz = 0.0
    count = len(face)
    for index in range(count):
        x1, y1, z1 = posed[face[index]]
        x2, y2, z2 = posed[face[(index + 1) % count]]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    cx = sum(posed[index][0] for index in face) / count
    cy = sum(posed[index][1] for index in face) / count
    cz = sum(posed[index][2] for index in face) / count
    if nx * cx + ny * cy + nz * cz < 0:
        nz = -nz
        nx = -nx
        ny = -ny
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nz / length


def _ring(flat, face):
    points = [flat[index] for index in face]
    parts = [f"M{_num(points[0][0])} {_num(points[0][1])}"]
    for x, y in points[1:]:
        parts.append(f"L{_num(x)} {_num(y)}")
    parts.append("Z")
    return "".join(parts)


def _core_opacity(unit):
    if unit < 0.42:
        return 0.0
    return min(1.0, (unit - 0.42) / 0.58) * 0.92


def _glint_point(flat, depth):
    z_min, z_max = min(depth), max(depth)
    y_min = min(y for _x, y in flat)
    y_max = max(y for _x, y in flat)
    best = flat[0]
    score = -1e9
    for (x, y), z in zip(flat, depth):
        near = 0.0 if z_max == z_min else (z - z_min) / (z_max - z_min)
        upper = 0.0 if y_max == y_min else (y_max - y) / (y_max - y_min)
        rank = near * 0.55 + upper * 0.45
        if rank > score:
            score = rank
            best = (x, y)
    return best


def edge_tracks(cx, cy, scale, count=FRAMES):
    """Per edge and per vertex, one sample per yaw. The sample command is always M L."""
    verts, edges, _faces = polyhedron()
    samples = []
    for index in range(count):
        posed = _posed(verts, 2 * math.pi * index / count)
        flat = [_project(x, y, z, cx, cy, scale) for x, y, z in posed]
        depth = [z for _x, _y, z in posed]
        samples.append((flat, depth))
    near = max(z for _flat, depth in samples for z in depth)
    far = min(z for _flat, depth in samples for z in depth)
    tracks = []
    for left, right in edges:
        frames = []
        for flat, depth in samples:
            z = (depth[left] + depth[right]) / 2
            opacity, width, _unit = _shade(z, near, far)
            x0, y0 = flat[left]
            x1, y1 = flat[right]
            frames.append((_segment(x0, y0, x1, y1), opacity, width))
        tracks.append(frames)
    dots = []
    for vertex in range(len(verts)):
        dots.append([flat[vertex] for flat, _depth in samples])
    return tracks, dots


def _circle(cx, cy, radius, color):
    return f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(radius)}" fill="{color}"/>'


def _guests(cx, cy, scale, color, animated):
    spline = "0.65 0 0.35 1"
    arm = max(8.0, scale * 0.22)
    co2_y = cy - scale * 0.16
    bond = (
        f'<line x1="{_num(cx - arm)}" y1="{_num(co2_y)}" x2="{_num(cx + arm)}" y2="{_num(co2_y)}" '
        f'stroke="{color}" stroke-width="1.25" stroke-linecap="round"/>'
    )
    co2 = bond + _circle(cx, co2_y, 2.15, color)
    co2 += _circle(cx - arm, co2_y, 2.7, color) + _circle(cx + arm, co2_y, 2.7, color)
    ch4 = _methane(cx + scale * 0.04, cy + scale * 0.30, max(7.0, scale * 0.18), color)
    if not animated:
        return f'<g class="guest-co2">{co2}</g><g class="guest-ch4">{ch4}</g>'
    return (
        f'<g class="guest-co2">{co2}'
        f'<animateTransform attributeName="transform" type="translate" dur="2s" '
        f'repeatCount="indefinite" calcMode="spline" keyTimes="0;0.25;0.5;0.75;1" '
        f'keySplines="{spline};{spline};{spline};{spline}" '
        f'values="0 0;1.5 -1.0;-1.2 0.9;0.6 1.2;0 0"/>'
        f"</g>"
        f'<g class="guest-ch4">{ch4}'
        f'<animateTransform attributeName="transform" type="translate" dur="1.6s" '
        f'repeatCount="indefinite" calcMode="spline" keyTimes="0;0.25;0.5;0.75;1" '
        f'keySplines="{spline};{spline};{spline};{spline}" '
        f'values="0 0;-1.1 1.3;1.4 -0.6;-0.5 -1.1;0 0"/>'
        f"</g>"
    )


def _methane(cx, cy, size, color):
    raw = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))
    norm = math.sqrt(3)
    points = []
    for x, y, z in raw:
        x, y, z = _rot_x(x / norm, y / norm, z / norm, 0.5)
        x, y, z = _rot_y(x, y, z, 0.7)
        points.append((cx + x * size, cy - y * size))
    parts = []
    for i in range(4):
        for j in range(i + 1, 4):
            x0, y0 = points[i]
            x1, y1 = points[j]
            parts.append(
                f'<line x1="{_num(x0)}" y1="{_num(y0)}" x2="{_num(x1)}" y2="{_num(y1)}" '
                f'stroke="{color}" stroke-width="1.05" stroke-linecap="round"/>'
            )
    parts.append(_circle(cx, cy, 2.5, color))
    for x, y in points:
        parts.append(_circle(x, y, 1.85, color))
    return "".join(parts)


def fit_scale(y0, y1, x_room, count=FRAMES):
    """Largest scale whose whole turn fits the box."""
    verts, _edges, _faces = polyhedron()
    x_half = 1.0
    y_half = 1.0
    for index in range(count):
        posed = _posed(verts, 2 * math.pi * index / count)
        for x, y, z in posed:
            px, py = _project(x, y, z, 0, 0, 1)
            x_half = max(x_half, abs(px))
            y_half = max(y_half, abs(py))
    return min(((y1 - y0) * 0.5) / y_half, (x_room * 0.5) / x_half)


def spin_schedule(count=FRAMES):
    """Hold each quarter, then ease the existing 10° samples. First frame closes the loop."""
    if count % 4:
        raise ValueError("spin frames must divide into four quarters")
    step = count // 4
    hold = motion.MOTION["cage_hold_s"]
    rotate = motion.MOTION["cage_rotate_s"]
    quarter = hold + rotate
    dur = 4 * quarter
    frames = []
    times = []
    for turn in range(4):
        start = turn * step
        origin = turn * quarter
        frames.append(start)
        times.append(origin / dur)
        frames.append(start)
        times.append((origin + hold) / dur)
        for index in range(1, step):
            frames.append(start + index)
            eased = motion.inverse_in_out(index / step)
            times.append((origin + hold + eased * rotate) / dur)
    frames.append(0)
    times.append(1.0)
    return frames, times


def _times(times):
    text = []
    previous = -1.0
    for index, raw in enumerate(times):
        value = 0.0 if index == 0 else (1.0 if index == len(times) - 1 else raw)
        if index not in (0, len(times) - 1) and value <= previous:
            value = previous + 0.0001
        previous = value
        if value in (0.0, 1.0):
            text.append("0" if value == 0 else "1")
        else:
            text.append(f"{value:.4f}".rstrip("0"))
    return ";".join(text)


def _packed(values):
    return ";".join(values)


def _remapped(samples):
    order, times = spin_schedule(len(samples))
    packed = _packed([samples[index] for index in order])
    return packed, _times(times)


def _anim(name, values, times):
    return (
        f'<animate attributeName="{name}" calcMode="linear" dur="{DUR}" repeatCount="indefinite" '
        f'keyTimes="{times}" values="{values}"/>'
    )


def _glint(points, color, animated):
    x0, y0 = points[0]
    base = f'<circle class="glint" r="2.5" fill="{color}" cx="{_num(x0)}" cy="{_num(y0)}"'
    if not animated:
        return base + ' opacity="1"/>'
    dur = float(motion.MOTION["cage_dur_s"])
    quarter = dur / 4
    rows = []
    for index, (x, y) in enumerate(points):
        start = index * quarter
        rows.append((start, 0.0, x, y))
        rows.append((start + 0.05, 1.0, x, y))
        rows.append((start + 0.11, 1.0, x, y))
        rows.append((start + 0.20, 0.0, x, y))
    rows.append((dur, 0.0, points[0][0], points[0][1]))
    times, ops, xs, ys = [], [], [], []
    previous = -1.0
    for raw, opacity, x, y in rows:
        frac = raw / dur
        if times and frac <= previous:
            frac = previous + 0.0001
        previous = frac
        if frac == 0:
            times.append("0")
        elif frac >= 1:
            times.append("1")
        else:
            times.append(f"{frac:.4f}".rstrip("0"))
        ops.append(f"{opacity:.2f}")
        xs.append(_num(x))
        ys.append(_num(y))
    key = ";".join(times)
    return (
        base
        + ' opacity="0">'
        + _anim("opacity", ";".join(ops), key)
        + _anim("cx", ";".join(xs), key)
        + _anim("cy", ";".join(ys), key)
        + "</circle>"
    )


def sprite(cx, cy, scale, color, animate_back_faces=True):
    """Bold glass cage. Panes, tubes, and the glint are flat fills — no gradient or filter."""
    verts, edges, faces = polyhedron()
    samples = []
    for index in range(FRAMES):
        posed = _posed(verts, 2 * math.pi * index / FRAMES)
        flat = [_project(x, y, z, cx, cy, scale) for x, y, z in posed]
        depth = [z for _x, _y, z in posed]
        samples.append((posed, flat, depth))
    near = max(z for _pose, _flat, depth in samples for z in depth)
    far = min(z for _pose, _flat, depth in samples for z in depth)
    highlight = _mix_white(color)

    edge_frames = []
    for left, right in edges:
        frames = []
        for _pose, flat, depth in samples:
            opacity, width, unit = _shade((depth[left] + depth[right]) / 2, near, far)
            x0, y0 = flat[left]
            x1, y1 = flat[right]
            frames.append((_segment(x0, y0, x1, y1), opacity, width, _core_opacity(unit)))
        edge_frames.append(frames)

    pane_frames = []
    for face in faces:
        frames = []
        for posed, flat, depth in samples:
            facing = (_face_nz(posed, face) + 1) / 2
            fill = 0.05 + 0.09 * min(1.0, max(0.0, facing))
            frames.append((_ring(flat, face), fill, sum(depth[index] for index in face) / len(face)))
        pane_frames.append(frames)
    pane_frames.sort(key=lambda frames: frames[0][2])

    dot_frames = []
    for vertex in range(len(verts)):
        frames = []
        for _pose, flat, depth in samples:
            _opacity, width, _unit = _shade(depth[vertex], near, far)
            frames.append((*flat[vertex], width * 0.72))
        dot_frames.append(frames)

    step = FRAMES // 4
    glints = [_glint_point(samples[turn * step][1], samples[turn * step][2]) for turn in range(4)]

    still = ['<g class="cage-still">']
    spin = ['<g class="cage-spin"><defs>']
    for index, frames in enumerate(edge_frames):
        d0 = frames[0][0]
        d_values, times = _remapped([item[0] for item in frames])
        spin.append(f'<path id="cage-e{index}" d="{d0}">{_anim("d", d_values, times)}</path>')
    spin.append("</defs>")

    for frames in pane_frames:
        d0, fill0, _depth = frames[0]
        front = max(item[1] for item in frames) >= 0.09
        still.append(
            f'<path class="pane" fill="{color}" fill-opacity="{fill0:.2f}" d="{d0}"/>'
        )
        if animate_back_faces or front:
            d_values, times = _remapped([item[0] for item in frames])
            fill_values, _fill_times = _remapped([f"{item[1]:.2f}" for item in frames])
            spin.append(
                f'<path class="pane" fill="{color}" fill-opacity="{fill0:.2f}" d="{d0}">'
                f'{_anim("d", d_values, times)}'
                f'{_anim("fill-opacity", fill_values, times)}'
                f"</path>"
            )
        else:
            spin.append(
                f'<path class="pane" fill="{color}" fill-opacity="{fill0:.2f}" d="{d0}"/>'
            )

    for index, frames in enumerate(edge_frames):
        d0, opacity, width, core = frames[0]
        _d_values, times = _remapped([item[0] for item in frames])
        fade_values, _fade_times = _remapped([f"{item[1]:.2f}" for item in frames])
        width_values, _width_times = _remapped([f"{item[2]:.2f}" for item in frames])
        core_values, _core_times = _remapped([f"{item[3]:.2f}" for item in frames])
        still.append(
            f'<path class="edge" fill="none" stroke="{color}" stroke-linecap="round" '
            f'd="{d0}" stroke-opacity="{opacity:.2f}" stroke-width="{width:.2f}"/>'
        )
        still.append(
            f'<path class="core" fill="none" stroke="{highlight}" stroke-linecap="round" '
            f'd="{d0}" stroke-width="0.8" stroke-opacity="{core:.2f}"/>'
        )
        spin.append(
            f'<use class="edge" href="#cage-e{index}" fill="none" stroke="{color}" stroke-linecap="round" '
            f'stroke-opacity="{opacity:.2f}" stroke-width="{width:.2f}">'
            f'{_anim("stroke-opacity", fade_values, times)}'
            f'{_anim("stroke-width", width_values, times)}'
            f"</use>"
        )
        spin.append(
            f'<use class="core" href="#cage-e{index}" fill="none" stroke="{highlight}" stroke-linecap="round" '
            f'stroke-width="0.8" stroke-opacity="{core:.2f}">'
            f'{_anim("stroke-opacity", core_values, times)}'
            f"</use>"
        )

    for frames in dot_frames:
        x0, y0, radius = frames[0]
        cx_values, times = _remapped([_num(x) for x, _y, _r in frames])
        cy_values, _cy_times = _remapped([_num(y) for _x, y, _r in frames])
        r_values, _r_times = _remapped([_num(radius) for _x, _y, radius in frames])
        spin.append(
            f'<circle r="{_num(radius)}" fill="{color}" cx="{_num(x0)}" cy="{_num(y0)}">'
            f'{_anim("cx", cx_values, times)}'
            f'{_anim("cy", cy_values, times)}'
            f'{_anim("r", r_values, times)}'
            f"</circle>"
        )
        still.append(f'<circle r="{_num(radius)}" fill="{color}" cx="{_num(x0)}" cy="{_num(y0)}"/>')

    still.append(_glint(glints, highlight, False))
    spin.append(_glint(glints, highlight, True))
    still.append(_guests(cx, cy, scale, color, False))
    spin.append(_guests(cx, cy, scale, color, True))
    still.append("</g>")
    spin.append("</g>")
    return "".join(still) + "".join(spin)
