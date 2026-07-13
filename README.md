# Research OS

Research OS is an intelligence layer for an Obsidian vault.

Obsidian remains the source of truth. Notes, PDFs, and images stay in open
formats and remain usable without this application.

## Phase 0 Scope

This repository contains the project foundations only:

- SvelteKit frontend shell
- FastAPI backend shell
- Shared configuration contract
- Clear folder boundaries
- Documentation for architecture decisions

No business features are implemented in Phase 0.

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
