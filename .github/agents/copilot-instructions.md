---
name: PickPilot Developer Agent
description: Full-stack Python/FastAPI and Next.js agent guidance for PickPilot.
---

# PickPilot

PickPilot is an internal product catalog dashboard. It imports Excel SKU sheets, normalizes known product fields, preserves unknown fields as dynamic attributes, filters and deletes products, and runs marketplace scrape jobs for Amazon AE, Noon UAE, Sharaf DG, and Carrefour UAE.

## Real Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: Next.js App Router, React, TypeScript, TanStack Query, TanStack Table, Zod, Lucide React, plain CSS.
- Scraping: Scrapling static fetcher plus marketplace-specific CSS extraction.
- Local database: Docker Compose PostgreSQL.

## Guardrails

- Keep the app internal unless auth is explicitly added.
- LLM product matching uses OpenRouter over structured scrape rows, not markdown parsing.
- Keep scraping best-effort: blocked or changed marketplace pages should become per-marketplace failures, not whole-app failures.
- Prefer existing schemas, services, and tests over new layers.
- Add one focused backend test for behavior changes that touch import, delete, filtering, scraping, or markdown files.
