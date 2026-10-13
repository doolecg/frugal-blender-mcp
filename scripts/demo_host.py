"""Headless demo host: an empty factory scene with every permission enabled.

Run ONLY with Blender --background --factory-startup, never on a user scene:
    blender -b --factory-startup --python scripts/demo_host.py -- <state-dir>

Drive it with the CLI and BLENDER_COMPACT_CONNECTION=<state-dir>/connection.json.
Create <state-dir>/stop to exit.
"""

import sys
import time
from pathlib import Path

import bpy

folder = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "addon"))
import compact_blender  # noqa: E402

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
compact_blender.register()
server = compact_blender.start(
    folder / "exports",
    folder / "connection.json",
    ("write", "render", "save", "delete", "python"),
    timer=False,
)
print(f"Demo bridge ready: {folder / 'connection.json'}", flush=True)
try:
    while not (folder / "stop").exists():
        server.poll()
        time.sleep(0.005)
finally:
    compact_blender.unregister()
