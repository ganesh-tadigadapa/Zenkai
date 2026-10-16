# Zenkai — Your opportunity radar

**Stop searching. Start discovering.**

Zenkai collects student opportunities from across the internet and shows them in one place: internships, hackathons, certifications, scholarships, programs and free student tech benefits.

🌐 **Live site:** https://zenkai-iota.vercel.app

---

## What is Zenkai?

Good opportunities for students are spread over many websites: Devpost for hackathons, Unstop for internships, Microsoft Learn for certifications, GitHub for student offers, and many more. Nobody has time to check all of them, so students miss things that were free and open to them.

Zenkai checks these websites for you, **every 6 hours, automatically**, and puts everything in one simple feed.

It covers six categories:

| Category | What you'll find |
|---|---|
| 💼 **Internships** | Paid and unpaid internships, linked to the company's own application page |
| 🏆 **Hackathons & Competitions** | Online and in-person events, with real registration deadlines |
| 🎓 **Certifications** | Courses and exams that give you a certificate |
| ✨ **Tech Benefits** | Free software, cloud credits and tools for students |
| 👥 **Programs & Fellowships** | Cohorts, ambassador programs and fellowships |
| 🎓 **Scholarships** | Money for studies, travel and research |

---

## How it works

1. **It fetches.** Every 6 hours, Zenkai reads official sources: Devpost, MLH, Unstop, SimplifyJobs, Microsoft Learn, the GitHub Student Pack, Outreachy, Google Developers and Opportunity Desk.
2. **It cleans up.** If the same opportunity appears on two sites, it's kept only once. Posts that aren't real opportunities (news, product updates) are filtered out.
3. **It keeps things fresh:**
   - New listings are added.
   - If a deadline changes, the record is updated.
   - When a deadline passes, or a listing is removed from its source, it disappears from Zenkai.
4. **It ranks for you.** If you add your degree, skills and interests, every opportunity gets a match score, with a clear reason for every point.

---

## How to use it

**Without an account:**
- Open the site and click **Explore opportunities**.
- Search (for example "AI hackathon" or "remote internship").
- Filter by category, cost, deadline, remote, and more.
- Click any opportunity to see its details and go straight to the official page to apply.

**With a free account:**
- **Overview:** your personal home page, with recommendations, new listings and ones closing soon.
- **Save:** bookmark opportunities you like.
- **Deadlines:** see what's closing today, this week, and later.
- **Profile:** add your degree, skills and interests to get better matches.

> ⚠️ Always check the details on the official website before applying. Listings found automatically show **"Needs verification"** until a person reviews them.

---

## Why it's useful

- **Saves time:** one site instead of ten.
- **Never miss a deadline:** closing-soon listings are easy to see.
- **Free things are easy to find:** filter for "Free" or "Free for students".
- **Honest:** every listing shows where it came from. Deadlines and costs are shown only when the source states them, never guessed.
- **Respects websites:** Zenkai follows each site's robots.txt rules and never fetches from sites that don't allow it.

---

## Tech stack

**Frontend**
- Next.js 16 (App Router, React Server Components)
- React 19, TypeScript
- Tailwind CSS v4

**Backend**
- Python 3.11
- FastAPI (REST API, with docs at `/docs`)
- SQLAlchemy 2.0 and Pydantic v2
- PostgreSQL (SQLite for local development)
- Argon2 password hashing, with secure sessions

**Data fetching (discovery)**
- httpx, with a polite fetcher that checks robots.txt, rate-limits each site and retries once on network errors
- Readers for each source: APIs (Devpost, Unstop, Microsoft Learn, SimplifyJobs), web pages (MLH, GitHub Student Pack) and RSS/Atom feeds

**Hosting**

| Part | Where it runs |
|---|---|
| Website | Vercel |
| API | Render (free plan) |
| Database | Neon PostgreSQL (free plan) |
| Fetching every 6 hours | GitHub Actions |
| Keep-awake ping every 10 minutes | GitHub Actions |

**Testing:** pytest, with 350+ backend tests.

---

## Run it on your computer

You need **Python 3.11+** and **Node 20+**.

```bash
# 1. Install everything
make install

# 2. Create the database and add starting data
make seed

# 3. Start the backend (port 8000), and keep this running
make backend

# 4. In a new terminal, start the website (port 3000)
make frontend

# 5. (Optional) Fetch live opportunities now
make discover
```

Open **http://localhost:3000**. The API docs are at **http://localhost:8000/docs**.

Run the tests:

```bash
make test    # backend tests
make lint    # frontend type check and lint
```

Settings go in `backend/.env` and `frontend/.env.local`. Copy them from `.env.example`. Never upload real `.env` files.

---

## Project structure

```
ZENKAI/
├── frontend/              # Next.js website
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── ingestion/     # fetching, cleaning and updating opportunities
│   │   ├── models/        # database tables
│   │   ├── services/      # matching, deadlines, accounts
│   │   └── seed/          # starting data and the list of sources
│   ├── tests/
│   └── run_discovery.py   # runs one fetch cycle
├── .github/workflows/     # 6-hour fetch and keep-awake jobs
└── render.yaml            # Render deployment setup
```

More detail: [ARCHITECTURE.md](ARCHITECTURE.md) · [DATABASE.md](DATABASE.md) · [DEVELOPMENT.md](DEVELOPMENT.md) · [DEPLOYMENT.md](DEPLOYMENT.md)

---

## What's next

- Password reset by email
- Sign in with Google or GitHub
- Email alerts for new matches and deadlines
- More scholarship sources
- A Chrome extension

---

## License

This project is licensed under the [MIT License](LICENSE).

Opportunity listings shown on the site belong to their original sources
(Devpost, Unstop, MLH, Microsoft Learn and others) and are subject to their terms.
