# Frugal Blender MCP 0.3.0

## New

- **Auto-start.** Tick "Start bridge when Blender opens" in Edit, Preferences, Add-ons, Frugal Blender MCP. The bridge then starts on its own, and starts again after you open a file.
- **Preferences page** with the five permissions, Safe, Build and Everything buttons, a Send-to folder and the options below.
- **Ask before risky steps.** Delete, save, python and export steps wait for you to press Approve in the Frugal MCP sidebar tab. They are denied after two minutes.
- **Export for games.** The new `export` operation writes a `.glb` for Godot or an `.fbx` for Unity or Unreal, and reports triangle counts, missing UVs and very large textures. A Send-to folder copies each file straight into your game project and never overwrites. The files are checked for valid headers only; I have not opened them in the engines.
- **Capture sheet.** `capture` with `view: sheet` returns front, right, top and camera views in one image.
- **More operations.** `parent`, `collection`, `world`, `lighting` (a ready-made three-point or sun rig) and `sprite_sheet`.
- **Headless mode.** `frugal-blender-mcp headless` runs Blender with no window. Set `FRUGAL_HEADLESS=1` in your MCP client and the server starts its own.
- **Visible mode.** A preference that runs each batch one step at a time and selects the object being changed. The sidebar shows the status, recent steps, a Pause agent button and a Stop this batch button.
- **Blender extension.** `install-addon --zip file.zip --extension` builds a Blender 4.2+ extension.

## Changed

- The fixed context cost is now 297 tokens, down from 338, and a test fails if it grows.
- A failed batch is now undone in interactive Blender. In a background Blender the earlier steps still stay, as before.
- Deleting an object also removes the mesh and material data it leaves behind.
- Permissions are saved in Blender's preferences, not in the .blend file, so a downloaded file cannot switch on python access.
- Loading a file used to stop the bridge for good. It now starts again if auto-start is on.
- The README and install commands now point at this fork. Install with `uvx --from git+https://github.com/doolecg/frugal-blender-mcp frugal-blender-mcp`.

## Fixed

- Blender never removed its connection file when you quit. It does now.
- A connection file left behind by a crash no longer stops the client finding the running Blender.
- The previews folder grew forever. It now keeps the newest 20.

---
