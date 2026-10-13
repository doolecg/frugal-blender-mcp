<!-- mcp-name: io.github.mohakmalviya/blender-astra-mcp -->
<div align="center">

# Blender Astra MCP

**Let your AI agent build Blender scenes, with 4 tools instead of 31.**

[![Checks](https://github.com/mohakmalviya/blender-astra-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/mohakmalviya/blender-astra-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/blender-astra-mcp)](https://pypi.org/project/blender-astra-mcp/)
[![Blender 4.2+](https://img.shields.io/badge/Blender-4.2%2B-orange)](https://www.blender.org/)
[![MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/mohakmalviya/blender-astra-mcp/blob/main/LICENSE)

<img src="https://raw.githubusercontent.com/mohakmalviya/blender-astra-mcp/main/examples/lighthouse/lighthouse.gif" alt="A stylized lighthouse island at sunset with a rotating beam, a bobbing sailboat and moving ocean waves" width="100%">

*Five **`execute` calls** (109 operations) written by Claude, rendered with Cycles in Blender 5.1.
[Replay the exact calls](https://github.com/mohakmalviya/blender-astra-mcp/tree/main/examples/lighthouse): they run in under a second.*

</div>

## Why another Blender MCP?

Every MCP client sends each server's tool definitions to the model on every request, before you
type anything. Most Blender servers expose dozens of tools. This one exposes four:
**`discover`**, **`execute`**, **`inspect`** and **`capture`**.

| Server | Tools | Fixed context per request |
|---|---:|---:|
| **Blender Astra MCP** | **4** | **401 tokens** |
| [Blender Lab official](https://projects.blender.org/lab/blender_mcp) | 26 | 4,722 tokens (11.8x) |
| [ahujasid mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) | 31 | 7,464 tokens (18.6x) |

<sub>Measured with tiktoken `o200k_base` from each server's real `tools/list` response.
Even if the agent discovers every operation, the total is 1,319 tokens.
[Method, raw data and caveats](https://github.com/mohakmalviya/blender-astra-mcp/blob/main/docs/tool-context.md).</sub>

The agent fetches an operation's arguments only when it needs them, then sends many edits in one
call. A single `execute` can carry up to 100 operations, and it returns counts and errors instead of
echoing the scene back. The five calls that built the lighthouse returned **202 tokens in total**.

## Quick start

You need [Blender](https://www.blender.org/download/) 4.2+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

**1. Install the Blender add-on**

```bash
uvx blender-astra-mcp install-addon
```

In Blender, open **Edit → Preferences → Add-ons** and enable **Blender Astra MCP**. Then press `N` in
the 3D Viewport, open the **Astra MCP** tab and click **Start bridge**.

**2. Connect your agent**

Claude Code:

```bash
claude mcp add blender -- uvx blender-astra-mcp
```

Codex CLI:

```bash
codex mcp add blender -- uvx blender-astra-mcp
```

Claude Desktop, Cursor, Windsurf and other JSON-configured clients:

```json
{
  "mcpServers": {
    "blender": { "command": "uvx", "args": ["blender-astra-mcp"] }
  }
}
```

If a desktop app can't find `uvx`, use its absolute path (`which uvx` or `where uvx`).

**3. Ask for something**

> Build a small lighthouse island at golden hour: a red-and-white tower, a keeper's house, a few
> pines, rocks and a sailboat. Batch your edits, then capture a preview.

## What the agent can do

| Need | Operations |
|---|---|
| Build | `primitive`, `array` (up to 200 linked copies in one step), `transform`, `material`, `assign_material`, `light`, `camera`, `delete` |
| Refine | `modifier` (any Blender modifier), `properties` (any RNA property on objects, data, scene or render), `rna` (look up property names and enums) |
| Animate | `keyframes` (up to 1,000 keys per step), `frame` |
| Output | `capture` (preview image back to the agent), `render` (stills or animations), `save` (a `.blend` copy) |
| Anything else | `python`: the full `bpy` API, for Geometry Nodes, rigging, simulation and import/export. Off by default. |

Previews keep your scene's aspect ratio, so the agent sees the framing you'll render.

## Safety

Blender stays in control. Permissions are chosen in the add-on panel when you start the bridge, and
the agent can't change them.

- **Write** and **render** are on by default. **Delete**, **save** and **python** are off.
- **Python is unrestricted local code execution.** Turn it on only for agents you trust.
- The bridge listens on loopback only and requires a fresh random token each time you start it.
- Deletes need `confirm: true`. Saves and renders never overwrite existing files.
- Interactive sessions get an undo checkpoint before every batch.
- No telemetry.

Details: [SECURITY.md](https://github.com/mohakmalviya/blender-astra-mcp/blob/main/SECURITY.md).

## How it compares

Choose by what you need, not just context size:

- **Blender Lab's official server** also searches Blender's manual and API docs, which helps agents
  write correct `bpy`.
- **ahujasid's server** bundles asset providers (Poly Haven, Sketchfab, Hyper3D and others).
- **This server** keeps the fixed context small, batches edits, gates risky actions behind
  permissions, and still reaches the whole API through `python` when you allow it.

## More

<details>
<summary><b>CLI</b>: drive Blender from scripts with the same code path</summary>

```bash
uvx --from blender-astra-mcp blender-astra discover
uvx --from blender-astra-mcp blender-astra inspect
uvx --from blender-astra-mcp blender-astra execute --params '{"steps":[{"op":"primitive","kind":"cube","name":"Demo"}]}'
uvx --from blender-astra-mcp blender-astra capture --params '{"filename":"preview.png","size":768}'
```

PowerShell can pipe a file instead of quoting JSON:
`Get-Content -Raw examples/lighthouse/01-sky-and-sea.json | uvx --from blender-astra-mcp blender-astra execute --params -`

Captures, renders and saves go to the bridge's `exports/` folder, and the CLI prints the filename.
</details>

<details>
<summary><b>Multiple Blender instances</b></summary>

Each running bridge writes a connection descriptor. If more than one exists, set
`BLENDER_COMPACT_CONNECTION` to the one you want:

- Windows: `%LOCALAPPDATA%/blender-compact-mcp/connection-<pid>.json`
- Linux/macOS: `${XDG_STATE_HOME:-~/.local/state}/blender-compact-mcp/connection-<pid>.json`

Ambiguous discovery fails rather than picking a scene at random. Opening a different file stops the
bridge. After a crash, delete only the stale descriptor.
</details>

<details>
<summary><b>Install without uvx</b></summary>

- **Add-on:** download `blender-astra-mcp-addon-<version>.zip` from
  [Releases](https://github.com/mohakmalviya/blender-astra-mcp/releases) and use
  **Install from Disk** in Blender's add-on preferences, or run
  `uvx blender-astra-mcp install-addon --zip addon.zip`.
- **Server from source:** clone the repository, run `uv sync --frozen`, and point your client at
  `uv run --directory /absolute/path/to/blender-astra-mcp blender-astra-mcp`.

Configs that use the old `blender-compact-mcp` command keep working.
</details>

<details>
<summary><b>Architecture</b></summary>

```text
AI client -- MCP stdio --> Python bridge -- authenticated loopback JSON --> Blender add-on
CLI ----------------------------^                                         bpy.app.timers
```

Blender's timer accepts bounded socket input and runs operations on Blender's main thread. No
background thread touches Blender data. `discover` returns readable argument contracts, and the add-on
validates every batch again before running it. A batch that fails partway reports which step failed
and what already ran. See [design](https://github.com/mohakmalviya/blender-astra-mcp/blob/main/docs/design.md).
</details>

<details>
<summary><b>Development</b></summary>

```bash
uv sync --frozen
uv run ruff check --config pyproject.toml .
uv run ruff format --check --config pyproject.toml .
uv run pytest -q
```

Tests that need Blender skip unless `BLENDER_EXE` points at a Blender executable. Set
`BLENDER_TEST_UI=1` to also test interactive timers and undo. They launch separate factory-startup
Blender processes and never touch your scenes or preferences. Results: [validation](https://github.com/mohakmalviya/blender-astra-mcp/blob/main/docs/validation.md).

`scripts/demo_host.py` runs a headless bridge on an empty scene, which is handy for replaying
`examples/`.
</details>

MIT licensed. Independent project, not affiliated with the Blender Foundation or any model provider.
