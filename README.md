# Research OS

Research OS is an intelligence layer for an Obsidian vault.

Obsidian remains the source of truth. Notes, PDFs, and images stay in open
formats and remain usable without this application.

## Platform

- SvelteKit workspace for reading PDFs and writing Markdown notes side by side
- Persistent colored PDF highlights, keyboard shortcut, and navigation to saved passages
- Local PDF decoders, including scanned JBIG2 documents
- Shared note colors across Workspace, Library, and Map
- Linked papers, notes, projects, and a knowledge graph
- FastAPI backend and a local project research assistant using Ollama
- macOS desktop application packaged with Tauri

## Repository Layout

```text
research-os/
  frontend/   SvelteKit application
  backend/    FastAPI application
  vault/      Obsidian vault placeholder
  library/    Incoming PDF/library placeholder
  config/     Application configuration
  docs/       Architecture notes
  scripts/    Local developer scripts
  docker/     Future container assets
```

## Research Model

The object model and recommended workflow are documented in
[`docs/research-os-object-model.md`](docs/research-os-object-model.md).

## Local Privacy

- Project notes, PDFs, the SQLite index, and local workspace/model settings are
  excluded from Git. Highlight sidecars, exported screenshots, recordings, application
  bundles, and generated build files are also excluded. Only platform code,
  developer documentation, placeholders, and example configuration are tracked.
- The project assistant talks only to Ollama on the local loopback interface and
  retrieves evidence only from the selected project's managed Vault sources.
- Online bibliographic enrichment is disabled by default. It can be enabled
  explicitly with `RESEARCH_OS_ENABLE_ONLINE_METADATA=true`; this sends a PDF's
  DOI or title to Crossref or OpenAlex.
- The Docker application is published on `127.0.0.1:7001`, not on the local
  network.

## Development

Full Docker stack:

```bash
docker compose up --build
```

Open `http://localhost:7001`.

For Docker, set `RESEARCH_OS_HOST_VAULT_PATH` in `.env` to the absolute
Obsidian Vault path on the host. Compose mounts that folder into the backend at
the same path so validation uses the path the user selected.

Backend:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Desktop build

Install Python 3.12, Node.js, Rust/Cargo, and the macOS command-line developer tools.
Prepare the backend environment as described above, then build the desktop app:

```bash
cd frontend
npm ci
npm run desktop:build
```

The application bundle is generated in `frontend/src-tauri/target/release/bundle/macos/`.
PDF decoder resources are packaged locally, so viewing scanned documents does not
require an external CDN. Personal desktop data is stored separately from the app
bundle and is never part of this repository.
