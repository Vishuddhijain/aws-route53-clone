# Route 53 Console

A clean-room Route 53 inspired DNS management console built with Next.js, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy, and SQLite. This project is an educational mock console; authentication and AWS service state are simulated locally.

## Features

- Mock sign-in/out with browser-persisted session
- Dashboard and AWS-style responsive navigation
- Hosted zone CRUD, search, and pagination
- DNS record CRUD, search, type filter, and pagination
- Record types A, AAAA, CNAME, TXT, MX, NS, PTR, SRV, and CAA, with type-aware forms and validation
- Public hosted zones receive mocked NS and SOA apex records automatically; private zones do not
- Pydantic validation and useful REST error responses
- SQLite persistence and cascading HostedZone → DNSRecord relationship
- JSON and BIND zone file export from the console, and BIND zone file import (upload a `.zone`/`.txt` file to a hosted zone; invalid lines are reported and skipped without failing the whole import)
- Dark mode toggle in the top navigation bar, persisted per browser
- Keyboard shortcuts: `Esc` closes the open modal, `n` opens "Create hosted zone" / "Create record" for the current page
- Traffic Policies, Health Checks, Resolver, and Profiles coming-soon routes
- FastAPI Swagger UI at `/docs`, OpenAPI JSON at `/openapi.json`, and `/health`

## Architecture

`frontend/` contains the Next.js App Router client console. Reusable console UI lives in `frontend/src/components/console/`, shared TypeScript models in `frontend/src/types/`, and the HTTP API client in `frontend/src/lib/api.ts`. The browser calls the REST API using `NEXT_PUBLIC_API_URL`. `backend/` contains FastAPI route handlers, Pydantic request validation, SQLAlchemy models, and SQLite persistence. The browser session is mock-only and is not an authorization boundary.

## Database schema

`hosted_zones`: `id`, unique `name`, `comment`, `is_private`, `created_at`.

`dns_records`: `id`, `zone_id` foreign key, `name`, `type`, `value`, `ttl`, `routing_policy`, `created_at`. Deleting a zone cascades to its records. New public zones receive example NS and SOA records at the apex; private zones start empty. The NS and SOA values are mock data and are not delegated or published to real DNS.

## Local setup

Requirements: Node.js 20.9+, npm, and Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
```

For the API test suite, install `pip install -r backend/requirements-dev.txt` and run `python -m pytest backend/tests -q` from the repository root. For the browser CRUD/session workflow, run `cd frontend`, `npx playwright install chromium`, and `npm run e2e`. The browser test builds and starts an isolated frontend and a backend using a separate SQLite file on local test ports; it covers zone/record create, edit, delete, search/filter, public NS/SOA defaults, refresh persistence, logout/login persistence, and placeholder routes.

Run the backend from the `backend` directory:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Demo login: `demo@route53.local` / `route53-demo`. The mock accepts any valid email and non-empty password. Backend defaults to `http://localhost:8000`; API documentation is at http://localhost:8000/docs.

## API

| Method             | Path                                            | Purpose                                                                                       |
| ------------------ | ----------------------------------------------- | --------------------------------------------------------------------------------------------- |
| GET, POST          | `/api/zones`                                    | Search/paginate or create hosted zones                                                        |
| GET                | `/api/summary`                                  | Dashboard counts for zones and records                                                        |
| GET, PATCH, DELETE | `/api/zones/{zone_id}`                          | Read, update, or remove a zone                                                                |
| GET, POST          | `/api/zones/{zone_id}/records`                  | Search/filter/paginate or create records                                                      |
| PATCH, DELETE      | `/api/records/{record_id}`                      | Update or remove a record                                                                     |
| GET                | `/api/zones/{zone_id}/export?format=json\|bind` | Export zone and records                                                                       |
| POST               | `/api/zones/{zone_id}/import`                   | Import records from BIND zone file text (`{"content": "..."}`); returns `{imported, skipped}` |
| GET                | `/health`                                       | Liveness check                                                                                |

List endpoints accept `search`, `page` (one-based), and `page_size` (1–100); records also accept `record_type`. List responses have `items`, `total`, `page`, and `page_size`. Invalid input is returned as HTTP 422; missing resources as 404; duplicate zones and conflicting CNAME data as 409. `/api/zones/{zone_id}/export?format=json` returns JSON; `format=bind` returns a BIND zone file.

## Environment variables

Copy `.env.example` to the project root as `.env` for the backend, and to `frontend/.env.local` for Next.js. `DATABASE_URL` defaults to `sqlite:///./route53.db`, `CORS_ORIGINS` defaults to `http://localhost:3000`, and the frontend uses `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api`). Set these in the respective deployment services. SQLite file storage is suitable for local development; use a persistent disk or managed database for production persistence.

## Deployment notes

- **Vercel:** set the project root to `frontend`, configure `NEXT_PUBLIC_API_URL` to the public backend API URL, and deploy the Next.js app.
- **Render / Railway:** deploy `backend` as a Python web service with start command `uvicorn main:app --host 0.0.0.0 --port $PORT`; set `CORS_ORIGINS` to the deployed frontend origin. Configure `DATABASE_URL`; for SQLite, attach persistent storage and use an absolute file path. A managed PostgreSQL URL is recommended when the platform does not provide persistent disks.
- This demonstration has intentionally mock authentication and no production authorization. Add real identity, protected APIs, migrations, and secrets management before exposing it as a production service.
