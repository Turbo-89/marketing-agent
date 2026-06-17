# Local Workspace Context

## Purpose

Local workspace context lets the UI browse configured local repository roots, open a read-only text file, and send only that open file's metadata with chat requests. The backend can safely resolve, hash, and preview the open file. Prompt injection is disabled by default and only uses a limited preview when explicitly enabled.

## Required Environment Variables

Filesystem roots are configured by environment variable. Only configured roots are exposed.

- `WORKSPACE_ROOT`
- `MARKETING_AGENT_ROOT`
- `TURBO_UI_ROOT`
- `TURBOSERVICES_ROOT`

Each root is exposed to the frontend by alias only. The frontend must use aliases and relative paths, not absolute paths.

## Endpoints

- `GET /api/fs/roots`
  Returns configured root aliases.

- `GET /api/fs/list?root=<alias>&path=<relative-path>`
  Lists directory entries under a scoped root.

- `GET /api/fs/read?root=<alias>&path=<relative-path>`
  Reads an allowed text-like file under a scoped root.

Chat requests may include optional metadata:

```json
{
  "context": {
    "open_file": {
      "root": "marketing_agent",
      "path": "server.py",
      "sha256": "<optional sha256>"
    },
    "selected_files": [
      {
        "root": "turbo_ui",
        "path": "app/chat/page.tsx",
        "sha256": "<optional sha256>"
      }
    ]
  }
}
```

## Feature Flags

- `ENABLE_OPEN_FILE_CONTEXT`
  Disabled by default. Enabled values are `1`, `true`, `yes`, or `on` case-insensitive.

  When disabled, the backend logs and previews the file but passes the original user message unchanged to `RouterEngine`.

  When enabled, the backend appends a clearly delimited workspace-context block to the user message before calling `RouterEngine`. The block uses only the limited preview, not the full file.

- `ENABLE_SELECTED_FILES_CONTEXT`
  Disabled by default. Enabled values are `1`, `true`, `yes`, or `on` case-insensitive.

  When disabled, selected files are logged and previewed but do not change the message sent to `RouterEngine`.

  When enabled, the backend appends a clearly delimited selected-workspace-context block to the user message before calling `RouterEngine`. The block uses only limited previews, not full files, and is capped at 10 selected files.

- `OPEN_FILE_CONTEXT_MAX_LINES`
  Default: `20`. Must be a positive integer. Hard cap: `300`.

- `OPEN_FILE_CONTEXT_MAX_CHARS`
  Default: `4000`. Must be a positive integer. Hard cap: `60000`.

Invalid, missing, zero, or negative preview-limit values fall back to defaults.

## Safety Rules

- Filesystem endpoints are read-only.
- Absolute paths are rejected.
- Traversal outside the scoped root is rejected.
- Responses do not return absolute filesystem paths.
- Secret and token files are blocked.
- Blocked path parts include `.git`, `.next`, `node_modules`, `.venv`, `venv`, and `__pycache__`.
- Only text-like file extensions are readable: `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.css`, `.html`, `.sql`, `.sh`, `.ps1`, and `.env.example`.
- Open-file metadata is logged as metadata only.
- Selected-files metadata is logged as metadata only and is limited to 10 valid entries.
- Selected files are safely resolved, read, hashed, and previewed server-side. Their previews are injected only when `ENABLE_SELECTED_FILES_CONTEXT` is enabled.
- The backend verifies the file exists, is a file, and is text-like before reading.
- SHA-256 mismatches are warnings only and do not fail chat.
- Full file content is not returned to chat callers or logged.
- Preview injection is disabled unless `ENABLE_OPEN_FILE_CONTEXT` is enabled.

## Validation Commands

From the backend repo:

```powershell
python -m py_compile server.py
```

Or with the local virtual environment:

```powershell
.\.venv312\Scripts\python.exe -m py_compile server.py
```

Optional import check:

```powershell
.\.venv312\Scripts\python.exe -c "from server import app; print('backend import ok')"
```

Expected log shape when an open file is provided:

```text
workspace context open_file root=marketing_agent path=server.py sha256=<hash>
workspace open_file loaded root=marketing_agent path=server.py sha256=<computed> chars=<n> sha256_match=true
workspace open_file preview limits lines=20 chars=4000
workspace open_file preview root=marketing_agent path=server.py lines=<n> preview_chars=<n>
workspace open_file context injection enabled=false
```
