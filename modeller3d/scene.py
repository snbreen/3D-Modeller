from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .geometry import ModelObject, cube, cylinder, pyramid, sphere


PRIMITIVES = {
    "Cube": cube,
    "Pyramid": pyramid,
    "Sphere": sphere,
    "Cylinder": cylinder,
}


@dataclass
class Scene:
    objects: list[ModelObject] = field(default_factory=list)
    selected_index: int | None = None

    def add_primitive(self, primitive: str) -> ModelObject:
        if primitive not in PRIMITIVES:
            raise ValueError(f"Unknown primitive: {primitive}")
        count = sum(obj.name.startswith(primitive) for obj in self.objects) + 1
        obj = ModelObject(name=f"{primitive} {count}", mesh=PRIMITIVES[primitive]())
        obj.position = ((count - 1) * 0.35, (count - 1) * 0.25, 0.0)
        self.objects.append(obj)
        self.select(len(self.objects) - 1)
        return obj

    def select(self, index: int | None) -> None:
        self.selected_index = index if index is not None and 0 <= index < len(self.objects) else None
        for item_index, obj in enumerate(self.objects):
            obj.selected = item_index == self.selected_index

    @property
    def selected(self) -> ModelObject | None:
        if self.selected_index is None:
            return None
        if self.selected_index >= len(self.objects):
            self.select(None)
            return None
        return self.objects[self.selected_index]

    def delete_selected(self) -> None:
        if self.selected_index is None:
            return
        del self.objects[self.selected_index]
        next_index = min(self.selected_index, len(self.objects) - 1)
        self.select(next_index if self.objects else None)

    def duplicate_selected(self) -> ModelObject | None:
        selected = self.selected
        if selected is None:
            return None
        clone = ModelObject.from_json(selected.to_json())
        clone.name = f"{selected.name} copy"
        clone.position = (
            selected.position[0] + 0.5,
            selected.position[1] + 0.5,
            selected.position[2] + 0.2,
        )
        self.objects.append(clone)
        self.select(len(self.objects) - 1)
        return clone

    def save(self, path: Path) -> None:
        data = {"version": 1, "objects": [obj.to_json() for obj in self.objects]}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.objects = [ModelObject.from_json(obj) for obj in data.get("objects", [])]
        self.select(0 if self.objects else None)

    def export_obj(self, path: Path) -> None:
        lines = ["# Exported by Python 3D Modeller"]
        offset = 1
        for obj in self.objects:
            if not obj.visible:
                continue
            lines.append(f"o {obj.name.replace(' ', '_')}")
            vertices = obj.transformed_vertices()
            for x, y, z in vertices:
                lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
            for face in obj.mesh.faces:
                indices = " ".join(str(index + offset) for index in face)
                lines.append(f"f {indices}")
            offset += len(vertices)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

