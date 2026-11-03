"""5^12 6^2 cage: equal-edge wireframe, Y-axis frames, guest jitter.

The polyhedron is the sI large cage (tetrakaidecahedron): two opposite
hexagons and twelve pentagons. Coordinates are four hexagonal rings with
edge length 1, solved so the vertices sit on a narrow radial band.
"""

import math

FRAMES = 36
DUR = "12s"
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
    return 0.28 + 0.72 * unit, 0.9 + 0.9 * unit


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
            opacity, width = _shade(z, near, far)
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
        f'<animateTransform attributeName="transform" type="translate" dur="2.2s" '
        f'repeatCount="indefinite" values="0 0;1.5 -1.0;-1.2 0.9;0.6 1.2;0 0"/>'
        f"</g>"
        f'<g class="guest-ch4">{ch4}'
        f'<animateTransform attributeName="transform" type="translate" dur="1.7s" '
        f'repeatCount="indefinite" values="0 0;-1.1 1.3;1.4 -0.6;-0.5 -1.1;0 0"/>'
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


def _loop(values):
    return ";".join(values) + ";" + values[0]


def sprite(cx, cy, scale, color):
    tracks, dots = edge_tracks(cx, cy, scale, FRAMES)
    spin = ['<g class="cage-spin">']
    still = ['<g class="cage-still">']
    for frames in tracks:
        d0, opacity, width = frames[0]
        spin.append(
            f'<path fill="none" stroke="{color}" stroke-linecap="round" '
            f'd="{d0}" stroke-opacity="{opacity:.2f}" stroke-width="{width:.2f}">'
            f'<animate attributeName="d" calcMode="linear" dur="{DUR}" repeatCount="indefinite" '
            f'values="{_loop([item[0] for item in frames])}"/>'
            f'<animate attributeName="stroke-opacity" calcMode="linear" dur="{DUR}" repeatCount="indefinite" '
            f'values="{_loop([f"{item[1]:.2f}" for item in frames])}"/>'
            f'<animate attributeName="stroke-width" calcMode="linear" dur="{DUR}" repeatCount="indefinite" '
            f'values="{_loop([f"{item[2]:.2f}" for item in frames])}"/>'
            f"</path>"
        )
        still.append(
            f'<path fill="none" stroke="{color}" stroke-linecap="round" '
            f'd="{d0}" stroke-opacity="{opacity:.2f}" stroke-width="{width:.2f}"/>'
        )
    radius = max(1.7, scale * 0.026)
    for frames in dots:
        x0, y0 = frames[0]
        spin.append(
            f'<circle r="{_num(radius)}" fill="{color}" cx="{_num(x0)}" cy="{_num(y0)}">'
            f'<animate attributeName="cx" calcMode="linear" dur="{DUR}" repeatCount="indefinite" '
            f'values="{_loop([_num(x) for x, _y in frames])}"/>'
            f'<animate attributeName="cy" calcMode="linear" dur="{DUR}" repeatCount="indefinite" '
            f'values="{_loop([_num(y) for _x, y in frames])}"/>'
            f"</circle>"
        )
        still.append(f'<circle r="{_num(radius)}" fill="{color}" cx="{_num(x0)}" cy="{_num(y0)}"/>')
    spin.append(_guests(cx, cy, scale, color, True))
    still.append(_guests(cx, cy, scale, color, False))
    spin.append("</g>")
    still.append("</g>")
    return "".join(still) + "".join(spin)
