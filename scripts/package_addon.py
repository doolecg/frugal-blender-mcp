"""Build an installable Blender add-on ZIP, excluding caches and runtime state."""

import hashlib
from pathlib import Path

from compact_mcp import __version__
from compact_mcp.install import write_zip

dist = Path(__file__).resolve().parents[1] / "dist"
target = write_zip(dist / f"frugal-blender-mcp-addon-{__version__}.zip")
(dist / "SHA256SUMS").write_text(f"{hashlib.sha256(target.read_bytes()).hexdigest()}  {target.name}\n")
print(target)
