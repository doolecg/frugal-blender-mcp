# Security

This add-on is a local editor-control service. Use it on a trusted workstation and keep source control
or checkpoints for valuable scenes. It is not an OS sandbox.

- Loopback binding and a per-start random bearer-equivalent secret are required. Every socket method
  checks the secret before dispatch. There are no browser HTTP/CORS endpoints.
- The descriptor is a credential. It lives in the user's local application state, not the repository.
  On Unix it is created with mode 0600; on Windows protection relies on the parent profile's inherited
  ACLs. Same-user processes can read it. Do not sync or share the state directory.
- **Write**, **render**, **delete**, **save** and **python** permissions are enforced in Blender. Only
  write and render default on. Stop and restart to change them. A client cannot grant itself permissions.
- Deletion also needs `confirm: true`. This is an explicit intent flag, not proof of human approval;
  the AI client's approval policy remains responsible for human confirmation.
- **The `python` permission is unrestricted local code execution.** When enabled, the agent can run any
  Python inside Blender with your user's privileges: read and write files, open network connections,
  and bypass every narrower toggle. It defaults off. Enable it only for agents and prompts you trust.
- With write permission, `properties` and `modifier` set arbitrary RNA properties on objects, object
  data, scene and render settings, including output paths. Treat write access as broad scene control.
- There is no separate shell, file-read, network-fetch or plugin-install endpoint outside `python`.
- Save/capture accept basenames under a fixed output directory, and existing files are refused.
  This is not a defense against a malicious same-user process racing the filesystem.
- Managed-object tagging is not a sandbox. Inspect can expose object names and positions to the AI;
  capture sends a rendered scene image. Your AI provider still processes the data your client sends.
- Render is blocking and cannot be remotely cancelled mid-call. Disconnect is not rollback. Timeouts
  explicitly report an unknown outcome and never automatically replay mutations.
- Assets already present in a `.blend` are trusted Blender content. This project does not make an
  untrusted Blender file safe to open or neutralize other installed add-ons.

The project itself has no telemetry. Test logs, descriptors, local paths and exports are excluded from
normal source commits. When reporting a bug, redact credentials and proprietary scene information.
