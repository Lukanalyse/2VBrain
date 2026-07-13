# Docker

Run the full application stack from the repository root:

```bash
docker compose up --build
```

The application is exposed through the `app` reverse proxy at:

```text
http://localhost:7001
```

The backend and frontend services are not published directly on host ports.
Nginx proxies `/api/v1/*` to FastAPI and all other requests to the SvelteKit
preview server.

Docker can only validate and read host folders that are mounted into the
backend container. The host Vault path is configured in `.env`:

```text
RESEARCH_OS_HOST_VAULT_PATH=/absolute/path/to/Obsidian Vault
```

The path is mounted at the same absolute path inside the container, so the
backend validates the exact path the user selected.
