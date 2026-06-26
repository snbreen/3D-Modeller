from __future__ import annotations

from dataclasses import replace
from math import cos, radians, sin
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from .geometry import ModelObject, Vec3, centroid
from .scene import Scene


BACKGROUND = "#151923"
GRID = "#2a3142"
EDGE = "#202635"
SELECTED = "#ffce54"


class ModelerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Python 3D Modeller")
        self.geometry("1180x760")
        self.minsize(960, 620)

        self.scene = Scene()
        self.camera_yaw = radians(-36)
        self.camera_pitch = radians(24)
        self.zoom = 150.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.drag_start: tuple[int, int] | None = None
        self.drag_mode = "orbit"

        self._build_ui()
        self._bind_events()
        self._seed_scene()
        self.redraw()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, padding=12)
        sidebar.grid(row=0, column=0, sticky="ns")

        ttk.Label(sidebar, text="Primitives", font=("", 13, "bold")).pack(anchor="w")
        primitive_row = ttk.Frame(sidebar)
        primitive_row.pack(fill="x", pady=(8, 14))
        for primitive in ("Cube", "Sphere", "Cylinder", "Pyramid"):
            ttk.Button(primitive_row, text=primitive, command=lambda p=primitive: self.add_primitive(p)).pack(fill="x", pady=2)

        ttk.Label(sidebar, text="Scene", font=("", 13, "bold")).pack(anchor="w")
        self.object_list = tk.Listbox(sidebar, height=12, exportselection=False)
        self.object_list.pack(fill="both", expand=True, pady=(8, 8))
        self.object_list.bind("<<ListboxSelect>>", self.on_list_select)

        action_row = ttk.Frame(sidebar)
        action_row.pack(fill="x", pady=(0, 12))
        ttk.Button(action_row, text="Duplicate", command=self.duplicate_selected).pack(fill="x", pady=2)
        ttk.Button(action_row, text="Delete", command=self.delete_selected).pack(fill="x", pady=2)

        ttk.Label(sidebar, text="Transform", font=("", 13, "bold")).pack(anchor="w")
        self.transform_vars: dict[str, tk.DoubleVar] = {}
        for label, key, start, end in (
            ("X", "px", -5, 5),
            ("Y", "py", -5, 5),
            ("Z", "pz", -5, 5),
            ("Rotate X", "rx", -180, 180),
            ("Rotate Y", "ry", -180, 180),
            ("Rotate Z", "rz", -180, 180),
            ("Scale", "scale", 0.2, 3),
        ):
            self._add_slider(sidebar, label, key, start, end)

        ttk.Button(sidebar, text="Color", command=self.choose_color).pack(fill="x", pady=(12, 4))
        ttk.Button(sidebar, text="Reset Camera", command=self.reset_camera).pack(fill="x", pady=2)

        file_row = ttk.Frame(sidebar)
        file_row.pack(fill="x", pady=(12, 0))
        ttk.Button(file_row, text="Save", command=self.save_scene).pack(fill="x", pady=2)
        ttk.Button(file_row, text="Load", command=self.load_scene).pack(fill="x", pady=2)
        ttk.Button(file_row, text="Export OBJ", command=self.export_obj).pack(fill="x", pady=2)

        viewport_frame = ttk.Frame(self)
        viewport_frame.grid(row=0, column=1, sticky="nsew")
        viewport_frame.columnconfigure(0, weight=1)
        viewport_frame.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(viewport_frame, background=BACKGROUND, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        status = ttk.Frame(viewport_frame, padding=(10, 6))
        status.grid(row=1, column=0, sticky="ew")
        self.status_text = tk.StringVar(value="Drag to orbit, Shift-drag to pan, mouse wheel to zoom.")
        ttk.Label(status, textvariable=self.status_text).pack(anchor="w")

    def _add_slider(self, parent: ttk.Frame, label: str, key: str, start: float, end: float) -> None:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(6, 0))
        var = tk.DoubleVar(value=1.0 if key == "scale" else 0.0)
        self.transform_vars[key] = var
        ttk.Scale(parent, from_=start, to=end, variable=var, command=lambda _value: self.update_transform()).pack(fill="x")

    def _bind_events(self) -> None:
        self.canvas.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.on_pointer_down)
        self.canvas.bind("<B1-Motion>", self.on_pointer_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_pointer_up)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.bind("<Delete>", lambda _event: self.delete_selected())
        self.bind("<BackSpace>", lambda _event: self.delete_selected())
        self.bind("<Control-d>", lambda _event: self.duplicate_selected())
        self.bind("<Control-s>", lambda _event: self.save_scene())
        self.bind("<Control-o>", lambda _event: self.load_scene())

    def _seed_scene(self) -> None:
        cube_obj = self.scene.add_primitive("Cube")
        cube_obj.color = "#4f8cff"
        sphere_obj = self.scene.add_primitive("Sphere")
        sphere_obj.color = "#67d391"
        sphere_obj.position = (2.1, 0.0, 0.0)
        self.scene.select(0)
        self.sync_object_list()
        self.sync_transform_controls()

    def add_primitive(self, primitive: str) -> None:
        self.scene.add_primitive(primitive)
        self.sync_object_list()
        self.sync_transform_controls()
        self.redraw()

    def duplicate_selected(self) -> None:
        self.scene.duplicate_selected()
        self.sync_object_list()
        self.sync_transform_controls()
        self.redraw()

    def delete_selected(self) -> None:
        self.scene.delete_selected()
        self.sync_object_list()
        self.sync_transform_controls()
        self.redraw()

    def choose_color(self) -> None:
        obj = self.scene.selected
        if obj is None:
            return
        chosen = colorchooser.askcolor(color=obj.color, parent=self)
        if chosen[1]:
            obj.color = chosen[1]
            self.redraw()

    def save_scene(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save scene",
            defaultextension=".json",
            filetypes=[("Scene JSON", "*.json")],
        )
        if path:
            self.scene.save(Path(path))
            self.status_text.set(f"Saved {Path(path).name}")

    def load_scene(self) -> None:
        path = filedialog.askopenfilename(parent=self, title="Load scene", filetypes=[("Scene JSON", "*.json")])
        if path:
            try:
                self.scene.load(Path(path))
            except (OSError, ValueError, KeyError) as exc:
                messagebox.showerror("Could not load scene", str(exc), parent=self)
                return
            self.sync_object_list()
            self.sync_transform_controls()
            self.redraw()
            self.status_text.set(f"Loaded {Path(path).name}")

    def export_obj(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Wavefront OBJ",
            defaultextension=".obj",
            filetypes=[("Wavefront OBJ", "*.obj")],
        )
        if path:
            self.scene.export_obj(Path(path))
            self.status_text.set(f"Exported {Path(path).name}")

    def on_list_select(self, _event: tk.Event) -> None:
        selection = self.object_list.curselection()
        self.scene.select(selection[0] if selection else None)
        self.sync_transform_controls()
        self.redraw()

    def sync_object_list(self) -> None:
        self.object_list.delete(0, tk.END)
        for obj in self.scene.objects:
            self.object_list.insert(tk.END, obj.name)
        if self.scene.selected_index is not None:
            self.object_list.selection_set(self.scene.selected_index)
            self.object_list.activate(self.scene.selected_index)

    def sync_transform_controls(self) -> None:
        obj = self.scene.selected
        values = {"px": 0.0, "py": 0.0, "pz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0, "scale": 1.0}
        if obj is not None:
            values.update(
                {
                    "px": obj.position[0],
                    "py": obj.position[1],
                    "pz": obj.position[2],
                    "rx": obj.rotation[0] * 180.0 / 3.1415926535,
                    "ry": obj.rotation[1] * 180.0 / 3.1415926535,
                    "rz": obj.rotation[2] * 180.0 / 3.1415926535,
                    "scale": obj.scale[0],
                }
            )
        for key, value in values.items():
            self.transform_vars[key].set(value)

    def update_transform(self) -> None:
        obj = self.scene.selected
        if obj is None:
            return
        obj.position = (
            self.transform_vars["px"].get(),
            self.transform_vars["py"].get(),
            self.transform_vars["pz"].get(),
        )
        obj.rotation = (
            radians(self.transform_vars["rx"].get()),
            radians(self.transform_vars["ry"].get()),
            radians(self.transform_vars["rz"].get()),
        )
        scale = self.transform_vars["scale"].get()
        obj.scale = (scale, scale, scale)
        self.redraw()

    def on_pointer_down(self, event: tk.Event) -> None:
        self.drag_start = (event.x, event.y)
        self.drag_mode = "pan" if event.state & 0x0001 else "orbit"

    def on_pointer_drag(self, event: tk.Event) -> None:
        if self.drag_start is None:
            return
        last_x, last_y = self.drag_start
        dx, dy = event.x - last_x, event.y - last_y
        if self.drag_mode == "pan":
            self.pan_x += dx
            self.pan_y += dy
        else:
            self.camera_yaw += dx * 0.01
            self.camera_pitch = max(radians(-80), min(radians(80), self.camera_pitch + dy * 0.01))
        self.drag_start = (event.x, event.y)
        self.redraw()

    def on_pointer_up(self, _event: tk.Event) -> None:
        self.drag_start = None

    def on_mouse_wheel(self, event: tk.Event) -> None:
        self.zoom = max(55.0, min(420.0, self.zoom * (1.1 if event.delta > 0 else 0.9)))
        self.redraw()

    def reset_camera(self) -> None:
        self.camera_yaw = radians(-36)
        self.camera_pitch = radians(24)
        self.zoom = 150.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.redraw()

    def redraw(self) -> None:
        self.canvas.delete("all")
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        self.draw_grid(width, height)

        faces_to_draw = []
        for obj in self.scene.objects:
            if not obj.visible:
                continue
            world_vertices = obj.transformed_vertices()
            camera_vertices = [self.to_camera(vertex) for vertex in world_vertices]
            screen_vertices = [self.project(vertex, width, height) for vertex in camera_vertices]
            for face in obj.mesh.faces:
                points_3d = [camera_vertices[index] for index in face]
                if not self.is_front_facing(points_3d):
                    continue
                depth = centroid(points_3d)[2]
                points_2d = [screen_vertices[index] for index in face]
                faces_to_draw.append((depth, obj, points_2d))

        for _depth, obj, points in sorted(faces_to_draw, key=lambda item: item[0], reverse=True):
            flat = [coord for point in points for coord in point]
            fill = obj.color if not obj.selected else self.lighten(obj.color)
            outline = SELECTED if obj.selected else EDGE
            self.canvas.create_polygon(flat, fill=fill, outline=outline, width=2 if obj.selected else 1)

        self.status_text.set(
            f"{len(self.scene.objects)} objects | zoom {self.zoom:.0f}% | drag to orbit, Shift-drag to pan, wheel to zoom"
        )

    def draw_grid(self, width: int, height: int) -> None:
        center_x = width / 2 + self.pan_x
        center_y = height / 2 + self.pan_y
        for offset in range(-8, 9):
            a = self.project(self.to_camera((offset, -8, -1.2)), width, height)
            b = self.project(self.to_camera((offset, 8, -1.2)), width, height)
            c = self.project(self.to_camera((-8, offset, -1.2)), width, height)
            d = self.project(self.to_camera((8, offset, -1.2)), width, height)
            self.canvas.create_line(*a, *b, fill=GRID)
            self.canvas.create_line(*c, *d, fill=GRID)
        self.canvas.create_oval(center_x - 3, center_y - 3, center_x + 3, center_y + 3, fill="#e6edf7", outline="")

    def to_camera(self, vertex: Vec3) -> Vec3:
        x, y, z = vertex
        cy, sy = cos(self.camera_yaw), sin(self.camera_yaw)
        x, z = x * cy + z * sy, -x * sy + z * cy
        cp, sp = cos(self.camera_pitch), sin(self.camera_pitch)
        y, z = y * cp - z * sp, y * sp + z * cp
        return (x, y, z + 8.0)

    def project(self, vertex: Vec3, width: int, height: int) -> tuple[float, float]:
        x, y, z = vertex
        focal = self.zoom * 4.0
        factor = focal / max(0.2, z)
        return (width / 2 + self.pan_x + x * factor, height / 2 + self.pan_y - y * factor)

    @staticmethod
    def is_front_facing(points: list[Vec3]) -> bool:
        if len(points) < 3:
            return False
        ax, ay, az = points[0]
        bx, by, bz = points[1]
        cx, cy, cz = points[2]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        normal_z = ux * vy - uy * vx
        return normal_z < 0 or abs(normal_z) < 0.0001

    @staticmethod
    def lighten(color: str) -> str:
        color = color.lstrip("#")
        r, g, b = (int(color[index : index + 2], 16) for index in (0, 2, 4))
        r = min(255, int(r + (255 - r) * 0.22))
        g = min(255, int(g + (255 - g) * 0.22))
        b = min(255, int(b + (255 - b) * 0.22))
        return f"#{r:02x}{g:02x}{b:02x}"


def main() -> None:
    app = ModelerApp()
    app.mainloop()

