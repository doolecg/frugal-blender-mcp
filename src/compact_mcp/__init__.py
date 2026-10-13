"""Blender Astra MCP client. Blender's add-on has no third-party dependencies."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("blender-astra-mcp")
except PackageNotFoundError:
    __version__ = "0+unknown"
