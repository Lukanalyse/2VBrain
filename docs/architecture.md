# Architecture

## Principle

Research OS does not own the knowledge base. The Obsidian vault remains the
canonical source of knowledge and must stay fully portable.

The application may add metadata, indexes, and intelligence layers, but it
must not require proprietary note formats.

## Backend Layers

- `api`: FastAPI routers, request wiring, and HTTP concerns.
- `core`: application settings, constants, and cross-cutting configuration.
- `database`: SQLAlchemy engine, sessions, migrations boundary.
- `models`: SQLAlchemy ORM models.
- `schemas`: Pydantic input/output contracts.
- `repositories`: persistence access patterns.
- `services`: use-case orchestration.
- `workers`: background task entry points.
- `utils`: generic helpers with no domain ownership.

FastAPI code should call services. Services may call repositories. Repositories
own database access. This keeps the application portable if transport, storage,
or workers change later.

## Frontend Layers

- `routes`: SvelteKit routing and page composition.
- `lib/layouts`: application shells and page layouts.
- `lib/features`: isolated product areas.
- `lib/components/ui`: reusable design-system primitives.
- `lib/services`: API clients and integration boundaries.
- `lib/stores`: shared Svelte state.
- `lib/types`: shared TypeScript contracts.
- `lib/hooks`: reusable client hooks.

Feature-specific components should live inside their feature folder first. Only
promote components to `lib/components` when they are genuinely shared.

## Future Integrations

Vector search and LLM providers are represented in configuration only. Their
runtime integrations should be added behind service interfaces when needed.

## Workspace Configuration

`config/workspace.json` stores local machine configuration, starting with the
active Obsidian vault path. It is intentionally not a database table because the
first version of the application must remain transparent and easy to reset.

The backend `VaultManager` owns validation and persistence of this file. Import,
PDF processing, embeddings, and AI workflows must stay outside this service.
