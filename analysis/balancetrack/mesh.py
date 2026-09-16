from __future__ import annotations

from typing import Tuple

import numpy as np


def heightfield_mesh(height: np.ndarray, mask: np.ndarray, cell_mm: float) -> Tuple[np.ndarray, np.ndarray]:
    mask = np.pad(mask.astype(bool), 1)
    height = np.pad(height.astype(float), 1)
    rows, cols = mask.shape

    counts = np.zeros((rows + 1, cols + 1))
    sums = np.zeros((rows + 1, cols + 1))
    h = np.where(mask, height, 0.0)
    for dr in (0, 1):
        for dc in (0, 1):
            counts[dr:dr + rows, dc:dc + cols] += mask
            sums[dr:dr + rows, dc:dc + cols] += h

    used = counts > 0
    n = int(used.sum())
    top_idx = np.full(used.shape, -1)
    top_idx[used] = np.arange(n)
    bot_idx = np.where(used, top_idx + n, -1)

    r, c = np.nonzero(used)
    z = sums[used] / counts[used]
    xy = np.column_stack([c * cell_mm, r * cell_mm])
    vertices = np.vstack([
        np.column_stack([xy, z]),
        np.column_stack([xy, np.zeros(n)]),
    ])

    cr, cc = np.nonzero(mask)
    a_t, b_t = top_idx[cr, cc], top_idx[cr, cc + 1]
    c_t, d_t = top_idx[cr + 1, cc + 1], top_idx[cr + 1, cc]
    a_b, b_b = bot_idx[cr, cc], bot_idx[cr, cc + 1]
    c_b, d_b = bot_idx[cr + 1, cc + 1], bot_idx[cr + 1, cc]

    faces = [
        np.column_stack([a_t, b_t, c_t]),
        np.column_stack([a_t, c_t, d_t]),
        np.column_stack([a_b, c_b, b_b]),
        np.column_stack([a_b, d_b, c_b]),
    ]

    s = ~mask[cr - 1, cc]
    faces += [np.column_stack([a_b, b_b, b_t])[s], np.column_stack([a_b, b_t, a_t])[s]]
    s = ~mask[cr + 1, cc]
    faces += [np.column_stack([c_b, d_b, d_t])[s], np.column_stack([c_b, d_t, c_t])[s]]
    s = ~mask[cr, cc - 1]
    faces += [np.column_stack([d_b, a_b, a_t])[s], np.column_stack([d_b, a_t, d_t])[s]]
    s = ~mask[cr, cc + 1]
    faces += [np.column_stack([b_b, c_b, c_t])[s], np.column_stack([b_b, c_t, b_t])[s]]

    faces = np.vstack(faces).astype(np.int64)
    vertices[:, :2] -= vertices[:, :2].min(axis=0)
    return vertices, faces


def is_watertight(faces: np.ndarray) -> bool:
    directed = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    if len(np.unique(directed, axis=0)) != len(directed):
        return False
    undirected = np.sort(directed, axis=1)
    _, counts = np.unique(undirected, axis=0, return_counts=True)
    return bool(np.all(counts == 2))


def volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    v0, v1, v2 = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    return float(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6.0)


def face_normals(vertices, faces):
    v0, v1, v2 = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    n = np.cross(v1 - v0, v2 - v0)
    length = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(length, 1e-12)


STL_DTYPE = np.dtype([
    ("normal", "<f4", (3,)),
    ("v0", "<f4", (3,)),
    ("v1", "<f4", (3,)),
    ("v2", "<f4", (3,)),
    ("attr", "<u2"),
])


def write_stl(path, vertices, faces, name="balance track insole"):
    data = np.zeros(len(faces), dtype=STL_DTYPE)
    data["normal"] = face_normals(vertices, faces)
    data["v0"] = vertices[faces[:, 0]]
    data["v1"] = vertices[faces[:, 1]]
    data["v2"] = vertices[faces[:, 2]]

    header = name.encode("ascii")[:80].ljust(80, b" ")
    with open(path, "wb") as f:
        f.write(header)
        f.write(np.uint32(len(faces)).tobytes())
        f.write(data.tobytes())


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        count = int(np.frombuffer(f.read(4), dtype="<u4")[0])
        data = np.frombuffer(f.read(), dtype=STL_DTYPE, count=count)
    return data
