# Python 3D Modeller

A small dependency-free 3D modeller built with Python and Tkinter. Inspired by the
Architecture of Open Source Applications "500 Lines or Less" 3D modeller tutorial, but
packaged as a personal-project-friendly app with scene files and OBJ export.

## Features

- Add cube, sphere, cylinder, and pyramid primitives
- Orbit, pan, and zoom the camera
- Select, duplicate, delete, recolor, translate, rotate, and scale objects
- Save and load editable scene files as JSON
- Export the current scene to Wavefront OBJ for use in other 3D tools
- Runs with the Python standard library; no required third-party packages

## Run

```bash
python3 -m modeller3d
```

## Controls

- Drag: orbit the camera
- Shift + drag: pan the camera
- Mouse wheel: zoom
- Delete or Backspace: delete selected object
- Command/Ctrl + D: duplicate selected object
- Command/Ctrl + S: save scene
- Command/Ctrl + O: load scene
