"""Exactly four MCP tools. Detailed operation descriptions are fetched on demand."""

import json
import uuid

from mcp.server.fastmcp import FastMCP, Image

from .client import Client


def lean(schema):
    """Trim generated JSON Schema noise the model never reads; tool definitions are resent every request."""
    if isinstance(schema, list):
        return [lean(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    options = schema.get("anyOf")
    if "default" in schema and schema["default"] is None and isinstance(options, list) and len(options) == 2:
        if {"type": "null"} in options:
            # Optional[X] = None: omitting the argument already means None.
            rest = {k: v for k, v in schema.items() if k not in ("anyOf", "default")}
            return lean({**rest, **next(o for o in options if o != {"type": "null"})})
    return {
        key: {name: lean(prop) for name, prop in value.items()} if key == "properties" else lean(value)
        for key, value in schema.items()
        if key != "title" and not (key == "additionalProperties" and value is True)
    }


class LeanFastMCP(FastMCP):
    async def list_tools(self):
        tools = await super().list_tools()
        for tool in tools:
            tool.description = " ".join((tool.description or "").split())
            tool.inputSchema = lean(tool.inputSchema)
        return tools


mcp = LeanFastMCP(
    "frugal-blender",
    instructions=(
        "Discover an operation before use. Batch related edits. Inspect narrowly; capture only when visual feedback "
        "is needed. Existing scenes are editable. Discover python for full bpy access (must be enabled in Blender). Partial batch failures persist; inspect before retrying."
    ),
)


def compact(result):
    return json.dumps(result, separators=(",", ":"), allow_nan=False)


@mcp.tool()
def inspect(names: list[str] | None = None, limit: int = 20, offset: int = 0) -> str:
    """Read a bounded scene summary; pass names for detailed object properties."""
    return compact(Client().call("inspect", {"names": names, "limit": limit, "offset": offset}))


@mcp.tool()
def discover(operation: str | None = None) -> str:
    """List operation summaries, or fetch one operation's arguments."""
    return compact(Client().call("discover", {"operation": operation}))


@mcp.tool()
def execute(steps: list[dict], dry_run: bool = False, timeout: int = 180) -> str:
    """Execute up to 100 {'op': name, ...arguments} steps. Returns counts/errors, not full scene data.

    dry_run checks syntax/permissions only. Runtime failures are partial, not transactional.
    """
    if not 1 <= timeout <= 86400:
        raise ValueError("timeout must be 1..86400 seconds; timeout does not cancel Blender work")
    return compact(Client().call("execute", {"steps": steps, "dry_run": dry_run}, timeout=timeout))


@mcp.tool()
def capture(size: int = 512, view: str = "camera", engine: str | None = None) -> Image:
    """PNG preview, longest edge 64..1024, scene aspect ratio: camera render or viewport (interactive only).

    Renders with EEVEE (fast); pass engine="CYCLES" for ray-traced quality.
    """
    client = Client()
    result = client.call(
        "capture",
        {"filename": f"preview-{uuid.uuid4().hex}.png", "size": size, "view": view, "engine": engine},
    )
    return Image(path=str(client.image_path(result["file"])))


def main():
    import argparse

    from . import __version__, install

    parser = argparse.ArgumentParser(
        prog="frugal-blender-mcp", description="Run the MCP server (default) or install the Blender add-on."
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    setup = commands.add_parser("install-addon", help="Copy the Blender add-on into Blender's user scripts")
    setup.add_argument("--blender-version", help="Target a specific Blender, e.g. 5.1 (default: newest)")
    setup.add_argument("--zip", metavar="PATH", help="Write an add-on ZIP for Install from Disk instead")
    args = parser.parse_args()
    if args.command is None:
        mcp.run(transport="stdio")
        return
    try:
        if args.zip:
            print(f"Wrote {install.write_zip(args.zip)}")
            print("In Blender: Edit > Preferences > Add-ons > Install from Disk, then pick that file.")
            return
        print(f"Installed to {install.install(args.blender_version)}")
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    print("Next, in Blender: Edit > Preferences > Add-ons, enable 'Frugal Blender MCP',")
    print("then open the 3D Viewport sidebar (N) > Frugal MCP > Start bridge.")


if __name__ == "__main__":
    main()
