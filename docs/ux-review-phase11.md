# Phase 11 UX Review

## Global Decisions

- Research Explorer is the primary exploration surface. The older Explore page remains available by URL but is removed from primary navigation.
- Page headers are now standardized with `PageHeader`.
- Static cards no longer show hover states. Hover is reserved for interactive rows, buttons, and links.
- Main navigation uses fewer competing entries: Home, Research Explorer, Library, Reviews, Knowledge, Projects, Brainstorm.
- Creation flows stay local to their workspace. No new functional surface was added.

## Home

- Frequent actions: resume work, search, import PDF, create workspace objects.
- Friction: Quick Actions and page title used custom visual patterns.
- Simplification: standardized page header and retained only high-value action shortcuts.

## Research Explorer

- Frequent actions: search, open an object, navigate related objects, back/forward.
- Friction: duplicated mental model with legacy Explore.
- Simplification: Research Explorer is the only primary navigation entry for exploration.

## Library

- Frequent actions: import PDF, inspect recent imports, open a Paper.
- Friction: page header differed from every other research screen.
- Simplification: standardized header and clearer page description.

## Knowledge / Concepts

- Frequent actions: create Concept, open Concept, link objects.
- Friction: related workflows are split across Knowledge, Concept detail, and Research Explorer.
- Simplification: no new UI added; Research Explorer becomes the recommended navigation path for discovery.

## Projects

- Frequent actions: select Project, create Project, link related objects.
- Friction: sidebar and selected object headers used different typography and spacing.
- Simplification: standardized sidebar and detail headers.

## Brainstorm

- Frequent actions: create note, capture thinking, link concepts/papers/projects.
- Friction: same layout as Projects but inconsistent header language.
- Simplification: standardized headers and clarified the workspace description.

## Literature Reviews

- Frequent actions: create Review, add Papers/Concepts, write synthesis, reopen.
- Friction: visually close to Projects/Brainstorm but with custom header treatment.
- Simplification: standardized headers and kept Writing as the dominant editing surface.

## Settings

- Frequent actions: verify Vault and storage paths.
- Friction: currently acceptable for a system screen.
- Simplification: no change; avoid churn until storage actions become real.

## AI

- Frequent actions: none yet.
- Friction: placeholder exists in navigation before functionality.
- Simplification deferred: keep visible because the product roadmap expects it, but avoid expanding it before intelligence phases.

## Component Follow-Up

- Button variants and form inputs still appear inline in several screens.
- A future cleanup should introduce shared `Button`, `TextInput`, `ObjectRow`, and `TabBar` primitives once current screen behavior stabilizes.
