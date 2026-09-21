# Deploying Zenkai

Zenkai is two deployable units:

| Unit | What it is | Where it goes |
|---|---|---|
| `frontend/` | Next.js 16 app | Vercel |
| `backend/` | FastAPI + PostgreSQL | Anywhere that runs a container or a Python process |

**Vercel hosts the frontend only.** The FastAPI service is not serverless and is
not deployed by Vercel. Until a backend is reachable, the marketing page works
in full and every signed-in route shows its error state.

---

## 1. Frontend on Vercel

### Project settings

| Setting | Value | Why |
|---|---|---|
| **Root Directory** | `frontend` | The repository root holds both units; without this Vercel builds the wrong directory. |
| Framework Preset | Next.js | Detected automatically once the root directory is right. |
| Build Command | *(default)* | `next build` |
| Install Command | *(default)* | `npm install` |
| Node version | 20 or newer | |

No `vercel.json` is needed, and none is committed — everything above is a
dashboard setting.

### Environment variables

Set these on the Vercel project (Production, Preview and Development):

| Variable | Example | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com` | Base URL of the deployed backend. No trailing slash. Public by design — it is just a URL. |
| `ZENKAI_ADMIN_TOKEN` | *(a long random secret)* | Sent server-side as `X-Admin-Token`. **Not** `NEXT_PUBLIC_`, so it never enters the browser bundle. Must match the backend's `ADMIN_TOKEN`. |

The build succeeds even when the backend is unreachable: the landing page is
fully self-contained, and the signed-in routes render on demand at runtime.

### What deploys

```
○  /                 static, revalidated every 2 minutes
ƒ  /dashboard        dynamic, rendered per request
ƒ  /opportunities    dynamic
ƒ  /opportunities/[slug]
ƒ  /saved  /deadlines  /profile  /admin
```

---

## 2. Backend

Any host that runs Python 3.11 and reaches a PostgreSQL instance will do —
Railway, Render, Fly.io, or a container on your own infrastructure.

```bash
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required environment:

| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://user:password@host:5432/dbname` |
| `ADMIN_TOKEN` | **Change from the default.** A service-account path for scripts; people authorise through their own `is_admin` account. Must match the frontend's `ZENKAI_ADMIN_TOKEN`. |
| `DEMO_USER_PASSWORD` / `DEMO_ADMIN_PASSWORD` | **Change both.** They seed the demo accounts and have known defaults. |
| `CORS_ORIGINS` | Your Vercel domain, e.g. `https://zenkai.vercel.app`. Comma-separated for several. |
| `ENV` | `production` — this stops `create_all()` running at startup. |
| `DEMO_USER_EMAIL` | Identity used when a request sends no `X-User-Id`. |

Then seed the catalogue once:

```bash
python -m app.seed.run
```

### Before a real launch

`ENV=production` disables the automatic `create_all()`, so the schema must be
applied another way. Add Alembic before there is a second environment — the
models are structured for autogenerate. Until then, run the seeder once against
a fresh database, which creates the tables as a side effect.

---

## 3. Checklist

- [ ] Vercel **Root Directory** is `frontend`
- [ ] `NEXT_PUBLIC_API_URL` points at the deployed backend, no trailing slash
- [ ] `ZENKAI_ADMIN_TOKEN` and the backend's `ADMIN_TOKEN` are the same value,
      and neither is `dev-admin-token`
- [ ] Backend `CORS_ORIGINS` includes the Vercel domain
- [ ] Backend `ENV=production`
- [ ] Database seeded
- [ ] `https://<your-domain>/` renders, and `/dashboard` shows opportunities

---

## 4. Before going public

Accounts are real: passwords are Argon2id-hashed, sessions are revocable, and
one account cannot see another's saved list or preferences. Two things still
need your attention:

- **Change the seeded passwords.** `DEMO_USER_PASSWORD` and
  `DEMO_ADMIN_PASSWORD` have known defaults. Set both, or delete the seeded
  accounts after creating your own.
- **Leave `ALLOW_DEMO_FALLBACK` unset.** It defaults to off outside
  development. Turning it on in production would let any visitor with no
  session act as the demo student.

### Known limitation

**There is no password reset.** A user who forgets their password cannot
recover the account without an admin editing the database directly. Adding it
needs an email provider — it is the top item on the roadmap.
