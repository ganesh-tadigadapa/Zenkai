# Zenkai frontend

The Next.js app for Zenkai. It renders the landing page and the signed-in
product, and talks to the FastAPI backend in `../backend` for all data.

```bash
npm install
npm run dev      # http://localhost:3000
npm run lint
npm run build
```

Set `NEXT_PUBLIC_API_URL` if the backend is not on `http://localhost:8000`.

## Layout

```
src/
├── app/          # routes: landing, (auth), (app) and the health check
├── components/   # UI grouped by feature: opportunity, filters, marketing, ui…
├── lib/          # API client, server actions, formatting and style helpers
│   └── auth/     # session cookie and signed-in user guards
└── proxy.ts      # redirects signed-out visitors away from private pages
```

See the [project README](../README.md) and [docs/](../docs) for the rest.
