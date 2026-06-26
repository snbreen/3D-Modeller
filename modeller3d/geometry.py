from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, pi, sin
from typing import Iterable


Vec3 = tuple[float, float, float]
Face = tuple[int, ...]


@dataclass
class Mesh:
    vertices: list[Vec3]
    faces: list[Face]


@dataclass
class ModelObject:
    name: str
    mesh: Mesh
    color: str = "#4f8cff"
    position: Vec3 = (0.0, 0.0, 0.0)
    rotation: Vec3 = (0.0, 0.0, 0.0)
    scale: Vec3 = (1.0, 1.0, 1.0)
    visible: bool = True
    selected: bool = False
    metadata: dict[str, str] = field(default_factory=dict)

    def transformed_vertices(self) -> list[Vec3]:
        return [transform_vertex(v, self.position, self.rotation, self.scale) for v in self.mesh.vertices]

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "mesh": {"vertices": self.mesh.vertices, "faces": self.mesh.faces},
            "color": self.color,
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "visible": self.visible,
            "metadata": self.metadata,
        }

    @classmethod
    def from_json(cls, data: dict) -> "ModelObject":
        mesh_data = data["mesh"]
        return cls(
            name=data["name"],
            mesh=Mesh(
                vertices=[tuple(vertex) for vertex in mesh_data["vertices"]],
                faces=[tuple(face) for face in mesh_data["faces"]],
            ),
            color=data.get("color", "#4f8cff"),
            position=tuple(data.get("position", (0.0, 0.0, 0.0))),
            rotation=tuple(data.get("rotation", (0.0, 0.0, 0.0))),
            scale=tuple(data.get("scale", (1.0, 1.0, 1.0))),
            visible=data.get("visible", True),
            metadata=data.get("metadata", {}),
        )


def cube(size: float = 1.6) -> Mesh:
    h = size / 2.0
    vertices = [
        (-h, -h, -h),
        (h, -h, -h),
        (h, h, -h),
        (-h, h, -h),
        (-h, -h, h),
        (h, -h, h),
        (h, h, h),
        (-h, h, h),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    return Mesh(vertices, faces)


def pyramid(size: float = 1.8, height: float = 2.0) -> Mesh:
    h = size / 2.0
    vertices = [(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0), (0, 0, height)]
    faces = [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)]
    return Mesh(vertices, faces)


def cylinder(radius: float = 0.9, height: float = 1.8, segments: int = 24) -> Mesh:
    vertices: list[Vec3] = []
    half = height / 2.0
    for z in (-half, half):
        for step in range(segments):
            angle = 2.0 * pi * step / segments
            vertices.append((radius * cos(angle), radius * sin(angle), z))

    bottom_center = len(vertices)
    vertices.append((0.0, 0.0, -half))
    top_center = len(vertices)
    vertices.append((0.0, 0.0, half))

    faces: list[Face] = []
    for step in range(segments):
        nxt = (step + 1) % segments
        faces.append((step, nxt, nxt + segments, step + segments))
        faces.append((bottom_center, nxt, step))
        faces.append((top_center, step + segments, nxt + segments))
    return Mesh(vertices, faces)


def sphere(radius: float = 1.0, rings: int = 10, segments: int = 20) -> Mesh:
    vertices: list[Vec3] = [(0.0, 0.0, radius)]
    for ring in range(1, rings):
        phi = pi * ring / rings
        z = radius * cos(phi)
        r = radius * sin(phi)
        for step in range(segments):
            theta = 2.0 * pi * step / segments
            vertices.append((r * cos(theta), r * sin(theta), z))
    vertices.append((0.0, 0.0, -radius))

    south = len(vertices) - 1
    faces: list[Face] = []
    for step in range(segments):
        faces.append((0, 1 + step, 1 + ((step + 1) % segments)))

    for ring in range(rings - 2):
        current = 1 + ring * segments
        nxt_ring = current + segments
        for step in range(segments):
            nxt = (step + 1) % segments
            faces.append((current + step, current + nxt, nxt_ring + nxt, nxt_ring + step))

    base = 1 + (rings - 2) * segments
    for step in range(segments):
        faces.append((south, base + ((step + 1) % segments), base + step))
    return Mesh(vertices, faces)


def transform_vertex(vertex: Vec3, position: Vec3, rotation: Vec3, scale: Vec3) -> Vec3:
    x, y, z = vertex
    x *= scale[0]
    y *= scale[1]
    z *= scale[2]

    rx, ry, rz = rotation
    cy, sy = cos(ry), sin(ry)
    x, z = x * cy + z * sy, -x * sy + z * cy

    cx, sx = cos(rx), sin(rx)
    y, z = y * cx - z * sx, y * sx + z * cx

    cz, sz = cos(rz), sin(rz)
    x, y = x * cz - y * sz, x * sz + y * cz

    return (x + position[0], y + position[1], z + position[2])


def centroid(points: Iterable[Vec3]) -> Vec3:
    points = list(points)
    total = len(points) or 1
    return (
        sum(point[0] for point in points) / total,
        sum(point[1] for point in points) / total,
        sum(point[2] for point in points) / total,
    )

