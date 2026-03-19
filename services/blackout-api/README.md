# Blackout API (abstraction layer)

FastAPI service that provides app-level server/channel/member abstractions on top of Matrix.

## Auth/session contract (Option B)

This service expects:

- `Authorization: Bearer <app-jwt>` for abstraction endpoints.
- `X-Matrix-Access-Token: <matrix_access_token>` as the client's Matrix token passthrough.

The JWT secures application-level endpoints while Matrix access tokens remain client-owned.

## Local run

```bash
pip install -r services/blackout-api/requirements.txt
uvicorn blackout_api.main:app --reload --port 8080 --app-dir services/blackout-api
```

## Environment variables

- `BLACKOUT_API_DATABASE_URL` (default: `sqlite:///./blackout_api.db`)
- `BLACKOUT_API_JWT_SECRET` (default: `change-me`)
- `BLACKOUT_API_JWT_ALGORITHM` (default: `HS256`)
