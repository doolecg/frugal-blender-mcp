# Design

## Token budget

Exactly four advertised tools keep discovery separate from execution. `inspect` defaults to 20 objects,
accepts up to 100, and exposes an offset for pagination. Detailed mesh counts/materials appear only for
named objects. No meshes, vertex arrays, scene-wide node dumps or screenshots are returned implicitly.

`execute` accepts up to 100 operations and caps expansion at 500 units per batch. It returns completed
operation/change counts and output basenames rather than echoing every object. `array` is a reusable
local procedure: the model specifies count and offset once, and Blender does the loop.

The four-tool interface alone does not guarantee lower total tokens. Extra discovery calls may cost more
on tiny tasks; batching and narrowly scoped feedback are the main measurable benefits in this release.

## Authority and state

The Blender-side `Engine` owns permissions; the model cannot change them. It edits only data tagged
`blender_compact_mcp`. Object operations additionally require membership in the active scene. This is
an application convention, not cryptographic ownership. A user can deliberately share managed data
with other scenes; managed material changes can affect every consumer of that material.

The add-on creates a managed collection rather than clearing the scene. Camera creation explicitly
changes the active scene camera. Transform arguments are local coordinates; target points used for
new camera/light aiming are world coordinates because newly created objects are unparented.
Material assignment detaches shared mesh data first, preserving other array instances.

## Protocol and lifecycle

One UTF-8 JSON line per TCP connection, max 256 KiB, bound to `127.0.0.1` on an OS-selected port.
The protocol is private to this bridge; MCP clients use the SDK stdio server, not the socket directly.
The descriptor carries protocol version, PID, port, secret and export root.

Each request includes a random client request ID. The server caches the last 128 authenticated
responses and a digest of their arguments. Replaying one cached ID returns the same result; reusing
it with different arguments fails. This is a bounded session cache, **not durable exactly-once delivery**.
There are no automatic mutation retries. After timeout/disconnect, the caller must inspect the state.
An operation may finish after the client stops waiting. Restarting Blender invalidates the token/cache.

Eight clients maximum, bounded receive work, at most one dispatched command per timer tick. Idle
partial connections expire after ten seconds. No background threads are used. Rendering is synchronous:
the UI and transport wait until it finishes, and Stop cannot preempt an in-progress render. There is
no asynchronous job or cancellation API in this first release.

Closing the bridge unregisters the exact timer callable and deletes its descriptor. Loading a `.blend`
stops the bridge; it starts again only if auto-start is on in preferences. Auth tokens are never included in tool results.

## Failure and Undo semantics

All step syntax and permissions are validated before a batch starts. Existence checks run per operation
so later steps can reference earlier creations. Runtime failures stop the batch. In interactive Blender the batch is
then undone back to its checkpoint and the result says `rolled_back`; in background mode completed operations
persist and a failed operation can have partial effects. Files already saved or rendered stay on disk. `dry_run` checks only syntax/permissions,
not object existence, Blender context viability or disk access. It is not a transaction simulation.

Interactive Blender receives before/after Undo checkpoints when available. One-step undo of a
transform batch is covered by a real UI test. Not all Blender effects are undoable, and files already
rendered or saved remain on disk. Background mode makes no undo promise. Save copies never overwrite.

## Scope after v0.1

Potential extensions: named JSON recipes with explicit parameters, Geometry Nodes operations, versioned
scene deltas, background render jobs, additional export formats and comparative end-to-end agent tasks.
Any new operation needs bounded output, actual Blender tests, and an explicit permission category.

## Decisions since the fork (2026-10-24)

- **Permissions in preferences.** They were scene properties, so a downloaded .blend could carry
  "python allowed" into an auto-started bridge. They now live in Blender user preferences and the
  file cannot change them. Auto-start is off by default.
- **Token budget is a rule.** The fixed cost was measured at 338 tokens (289 definitions, 49
  instructions, o200k). Features arrive through `discover` or the add-on, so they cost nothing per request.
- **Stale connection files.** Blender does not call `unregister` on quit, so the file stayed behind. An
  `atexit` hook removes it. The client deletes a file only when its port refuses a connection, never on a
  timeout, because a busy Blender can be slow to accept.
- **Approval is a held request, not a popup.** A popup needs the Blender event loop, which a timer
  callback cannot drive reliably. The request is parked, the sidebar shows Approve and Deny, and the
  client keeps waiting. It is denied after 120 seconds, shorter than the client's 180 second timeout.
- **Delete removes unused data.** Mesh, light and camera data, and materials this add-on created, are removed
  once nothing uses them. Shared mesh data from `array` copies stays until the last copy goes.
- **Export argument is `engine`.** The step validator treats any argument named `target` as a point, so
  the first draft with `target: godot` failed. Axes: Godot uses glTF (Y-up, modifiers applied). Unity uses
  FBX with -Z forward, Y up. Unreal uses FBX with -Y forward, Z up. Scale is baked in. Unity and Unreal
  settings come from common import recipes and have not been tried in those engines.
- **Capture sheet.** Three temporary orthographic cameras (front, right, top) frame the bounding box of all
  meshes, then the scene camera adds a fourth tile. Tiles are rendered to hidden files, stitched with numpy
  (bundled with Blender) and the temporary files, cameras and images are removed.
- **One `Run` for both modes.** The batch used to be a loop. It is now an object with `advance()`, so normal
  mode runs it to the end inside one request and visible mode lets the timer advance it one step per tick.
  Rollback, the activity log and highlight all live in the same place. A client that disconnects mid-batch
  leaves what already ran in place and unlocks the interface; there is no undo at that point because the
  disconnect can arrive during a file load.
- **Pause refuses, it does not queue.** A paused bridge answers new requests with an error saying nothing ran.
  Queueing would leave the client waiting past its timeout with an unknown outcome.
- **Headless is a separate process.** `blender --background` plus a host script that calls `poll()` in a loop,
  because background Blender runs no timers. The test host already worked this way. Windows `terminate()` does
  not run exit hooks, so a killed headless Blender can leave a stale connection file; the client prunes those.
- **Extension next to the legacy add-on.** Installing both makes Blender load two copies that register the same
  class names, and one fails. Use one or the other.
- **Release route.** The PyPI name and MCP registry entry belong to the original author, so 0.3.0 is
  installed from GitHub with `uvx --from git+...`. `server.json` and `glama.json` still carry the original
  author's identity and are not published from here. The release workflow builds the wheel, source archive,
  add-on zip and extension zip and attaches them to a GitHub release; the PyPI and registry jobs were removed.
- **Fixed a flaky upstream test.** `test_request_size_limit` polled the server ten times with no pause and failed
  about one run in eight while the bytes were still arriving over loopback. It now waits up to half a second.
