# PickPilot

PickPilot Phase 1 is an internal product-management dashboard for importing ecommerce product spreadsheets, storing normalized product fields plus dynamic JSONB attributes, filtering products, viewing product detail, and deleting SKUs safely.

Competitor scraping, product matching, LLM calls, search URL generation, background scraping jobs, billing, notifications, and workflow engines are intentionally out of scope for Phase 1.

## Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL.
- Frontend: Next.js, React, TypeScript, TanStack Query, TanStack Table, Zod, plain CSS.
- Local database: Docker Compose PostgreSQL.

## Local Setup

```bash 
cp .env.example .env
docker compose up -d postgres

python -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
backend/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another shell:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Or restart everything cleanly:

```bash
bash start.sh
```

This keeps one terminal open. Press `Ctrl+C` in that terminal to stop both the backend and frontend.

## Environment Variables

See `.env.example`.

Important backend variables:

- `PICKPILOT_DATABASE_URL`
- `PICKPILOT_CORS_ORIGINS`
- `PICKPILOT_MAX_UPLOAD_BYTES`
- `PICKPILOT_MAX_IMPORT_ROWS`
- `PICKPILOT_MAX_SKU_FILTER_ROWS`
- `PICKPILOT_IMPORT_BATCH_SIZE`
- `PICKPILOT_SCRAPE_OUTPUT_DIR`
- `PICKPILOT_SCRAPE_TIMEOUT_SECONDS`
- `PICKPILOT_SCRAPE_MAX_RESULTS`
- `PICKPILOT_OPENROUTER_API_KEY`
- `PICKPILOT_OPENROUTER_MODEL`
- `PICKPILOT_MATCH_AUTO_ENABLED`

Frontend uses same-origin `/api` calls. Next proxies those to `NEXT_INTERNAL_API_BASE_URL`, falling back to `NEXT_PUBLIC_API_BASE_URL`, then `http://127.0.0.1:8000`.

## Excel Import Rules

- Accepts `.xls` and `.xlsx`.
- Each non-empty row represents one SKU.
- `SKU` is mandatory.
- SKU values are trimmed strings. Text SKUs like `00123` keep leading zeros.
- Header matching trims whitespace, is case-insensitive, normalizes repeated whitespace, accepts underscores for configured aliases, and does not use fuzzy matching.
- Canonical fields: SKU, Title, Bullet Points, Specs, Category, Product Type, Attribute Set, L1, L2, L3, L4.
- Unknown headers are preserved in product `attributes`.
- The complete uploaded row is preserved in `source_row` using original header names.
- Empty cells are stored as `null`.
- Formula cells are read as stored workbook values with `data_only=True`; formulas are not executed.
- Duplicate SKUs inside one workbook are row errors and are excluded from import.

## Upsert Semantics

SKU is the Phase 1 business key.

- New SKU: insert.
- Existing SKU: update the existing product.
- Update mode is replacement, not merge.
- Attributes absent from the new upload are removed from the stored imported representation.
- `created_at` remains unchanged; `updated_at` changes.

## Deletion Safeguards

- Single-product deletion deletes by product ID.
- Selected deletion sends explicit IDs/SKUs and requires `DELETE N PRODUCTS`.
- Delete-by-filter sends structured filters to the backend, rejects empty filters, previews the exact count, requires `DELETE N PRODUCTS`, re-checks the count, and records an audit row.
- Delete-by-filter never means “delete current visible page.”

## Tests

```bash
backend/.venv/bin/pytest backend/tests
rm -rf frontend/.next && npm run build --prefix frontend
```

The backend tests use SQLite for fast local checks and PostgreSQL for runtime via Docker/Alembic. PostgreSQL remains the production database.

## Phase 1 Limitations

- No auth integration yet; audit user fields are nullable.
- SKU filter uploads create temporary server-side tokens and do not permanently store uploaded files.
- `bullet_points` and `specs` are text columns because source format is not guaranteed to be structured.
- No JSONB GIN index is added until a demonstrated dynamic-attribute query needs it.

## Phase 2 Scraping

Imports can include a `Search Query` / `search_query` header. Selected products with a search query can be scraped against Amazon AE, Noon UAE, Sharaf DG, and Carrefour UAE from the product table.

The backend generates marketplace URLs, creates an async scrape job, stores structured results in PostgreSQL, and writes markdown files to `PICKPILOT_SCRAPE_OUTPUT_DIR`.

Marketplace URL templates:

- Amazon: `https://www.amazon.ae/s?k={query_plus}`
- Noon: `https://www.noon.com/uae-en/search/?q={query_plus}`
- Sharaf DG: `https://uae.sharafdg.com/?q={query_percent}&post_type=product`
- Carrefour: `https://www.carrefouruae.com/mafuae/en/search?keyword={query_percent}`

Phase 2 uses Scrapling's static fetcher. Sites that block scraping are recorded as per-marketplace failures; proxy/CAPTCHA handling is intentionally deferred.

## LLM Product Matching

Completed scrape results can be matched against the indexed product with OpenRouter. The matcher sends the stored product fields and structured top scrape result rows to the configured model, stores the suggested best candidate, confidence, reason, and per-candidate evidence, and leaves the result as a human-review suggestion.

Set `PICKPILOT_OPENROUTER_API_KEY` in `.env`. The default model is `tencent/hy3:free`; override it with `PICKPILOT_OPENROUTER_MODEL` when that free endpoint changes. Matching runs automatically after successful scrapes when `PICKPILOT_MATCH_AUTO_ENABLED=true`, and can be rerun from the product detail page.
