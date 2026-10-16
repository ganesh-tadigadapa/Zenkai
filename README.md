<div align="center">

<img src="docs/banner.svg" alt="Zenkai — Your opportunity radar" width="100%" />

<br />

**Internships, hackathons, certifications, scholarships, programs and free student tech  —    from across the internet, in one place, updated every 6 hours.**

<br />

[![Live site](https://img.shields.io/badge/🌐_Live_site-zenkai--iota.vercel.app-4f9df7?style=for-the-badge)](https://zenkai-iota.vercel.app)
[![Discovery](https://img.shields.io/github/actions/workflow/status/ganesh-tadigadapa/Zenkai/discovery.yml?style=for-the-badge&label=live%20fetch&logo=githubactions&logoColor=white)](https://github.com/ganesh-tadigadapa/Zenkai/actions/workflows/discovery.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-3fca8d?style=for-the-badge)](LICENSE)

![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React_19-20232a?style=flat-square&logo=react&logoColor=61dafb)
![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?style=flat-square&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_v4-0f172a?style=flat-square&logo=tailwindcss&logoColor=38bdf8)
![Python](https://img.shields.io/badge/Python_3.11-3776ab?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169e1?style=flat-square&logo=postgresql&logoColor=white)

[**Live site**](https://zenkai-iota.vercel.app) ·
[What it is](#-what-is-zenkai) ·
[How it works](#%EF%B8%8F-how-it-works) ·
[How to use it](#-how-to-use-it) ·
[Tech stack](#%EF%B8%8F-tech-stack) ·
[Run locally](#-run-it-on-your-computer)

</div>

<br />

<p align="center">
  <img src="docs/screenshots/landing.png" alt="Zenkai landing page" width="100%" />
</p>

---

## 🎯 What is Zenkai?

Good opportunities for students are spread over many websites: Devpost for hackathons, Unstop for internships, Microsoft Learn for certifications, GitHub for student offers, and many more. Nobody has time to check all of them, so students miss things that were free and open to them.

**Zenkai checks these websites for you, every 6 hours, automatically**, and puts everything in one simple feed.

<table>
  <tr>
    <td align="center" width="33%">💼<br /><b>Internships</b><br /><sub>Paid and unpaid, linked to the company's own application page</sub></td>
    <td align="center" width="33%">🏆<br /><b>Hackathons & Competitions</b><br /><sub>Online and in person, with real registration deadlines</sub></td>
    <td align="center" width="33%">📜<br /><b>Certifications</b><br /><sub>Courses and exams that give you a certificate</sub></td>
  </tr>
  <tr>
    <td align="center">✨<br /><b>Tech Benefits</b><br /><sub>Free software, cloud credits and tools for students</sub></td>
    <td align="center">👥<br /><b>Programs & Fellowships</b><br /><sub>Cohorts, ambassador programs and fellowships</sub></td>
    <td align="center">🎓<br /><b>Scholarships</b><br /><sub>Money for studies, travel and research</sub></td>
  </tr>
</table>

---

## ⚙️ How it works

```mermaid
flowchart LR
    A["🌍 Sources<br/>Devpost · MLH · Unstop<br/>SimplifyJobs · Microsoft Learn<br/>GitHub Student Pack · feeds"] -->|every 6 hours| B["📥 Fetch<br/>follows robots.txt"]
    B --> C["🧹 Clean up<br/>remove noise<br/>merge duplicates"]
    C --> D[("🗄️ Database")]
    D --> E["🔄 Keep fresh<br/>update changes<br/>close expired"]
    E --> D
    D --> F["🎯 Rank for you<br/>match score<br/>with reasons"]
    F --> G["💻 Website"]
```

1. **📥 It fetches.** Every 6 hours, Zenkai reads official sources: Devpost, MLH, Unstop, SimplifyJobs, Microsoft Learn, the GitHub Student Pack, Outreachy, Google Developers and Opportunity Desk.
2. **🧹 It cleans up.** If the same opportunity appears on two sites, it's kept only once. Posts that aren't real opportunities (news, product updates) are filtered out.
3. **🔄 It keeps things fresh:**
   - New listings are added.
   - If a deadline changes, the record is updated.
   - When a deadline passes, or a listing is removed from its source, it disappears from Zenkai.
4. **🎯 It ranks for you.** If you add your degree, skills and interests, every opportunity gets a match score, with a clear reason for every point.

---

## 🧭 How to use it

<p align="center">
  <img src="docs/screenshots/opportunities.png" alt="Browsing opportunities with filters" width="100%" />
</p>

| | Without an account | With a free account |
|---|:---:|:---:|
| 🔍 Search and filter every opportunity | ✅ | ✅ |
| 🔗 Go straight to the official page to apply | ✅ | ✅ |
| 🏠 **Overview:** personal home page with recommendations | | ✅ |
| 🔖 **Save** opportunities you like | | ✅ |
| ⏰ **Deadlines:** what's closing today, this week and later | | ✅ |
| 🎯 **Profile:** add your degree, skills and interests for better matches | | ✅ |

**Quick start:** open the [live site](https://zenkai-iota.vercel.app) → click **Explore opportunities** → search something like *"AI hackathon"* or *"remote internship"* → filter by category, cost, deadline or remote → open one and apply on the official page.

> [!IMPORTANT]
> Always check the details on the official website before applying. Listings found automatically show **"Needs verification"** until a person reviews them.

---

## 💡 Why it's useful

- ⏱️ **Saves time:** one site instead of ten.
- 📅 **Never miss a deadline:** closing-soon listings are easy to see.
- 💸 **Free things are easy to find:** filter for "Free" or "Free for students".
- 🔍 **Honest:** every listing shows where it came from. Deadlines and costs are shown only when the source states them, never guessed.
- 🤝 **Respects websites:** Zenkai follows each site's robots.txt rules and never fetches from sites that don't allow it.

---

## 🛠️ Tech stack

<table>
  <tr>
    <th>🎨 Frontend</th>
    <th>⚡ Backend</th>
    <th>📡 Data fetching</th>
  </tr>
  <tr valign="top">
    <td>
      • Next.js 16 (App Router, Server Components)<br />
      • React 19<br />
      • TypeScript<br />
      • Tailwind CSS v4
    </td>
    <td>
      • Python 3.11<br />
      • FastAPI (REST API, docs at <code>/docs</code>)<br />
      • SQLAlchemy 2.0 and Pydantic v2<br />
      • PostgreSQL (SQLite for local development)<br />
      • Argon2 password hashing, secure sessions
    </td>
    <td>
      • httpx, with a polite fetcher: checks robots.txt, rate-limits each site, retries once on network errors<br />
      • Readers for APIs (Devpost, Unstop, Microsoft Learn, SimplifyJobs), web pages (MLH, GitHub Student Pack) and RSS/Atom feeds
    </td>
  </tr>
</table>

**☁️ Hosting: all free plans**

| Part | Where it runs |
|---|---|
| 💻 Website | [Vercel](https://vercel.com) |
| ⚡ API | [Render](https://render.com) |
| 🗄️ Database | [Neon](https://neon.tech) PostgreSQL |
| 🔄 Fetching every 6 hours | GitHub Actions |
| 🔔 Keep-awake ping every 10 minutes | GitHub Actions |

**🧪 Testing:** pytest, with 350+ backend tests.

---

## 🚀 Run it on your computer

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

```bash
make test    # backend tests
make lint    # frontend type check and lint
```

> [!TIP]
> Settings go in `backend/.env` and `frontend/.env.local`. Copy them from `.env.example`. Never upload real `.env` files.

<details>
<summary><b>📁 Project structure</b> (click to open)</summary>

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

</details>

---

## 🗺️ What's next

- [ ] 🔑 Password reset by email
- [ ] 🔐 Sign in with Google or GitHub
- [ ] 📧 Email alerts for new matches and deadlines
- [ ] 🎓 More scholarship sources
- [ ] 🧩 A Chrome extension

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

Opportunity listings shown on the site belong to their original sources (Devpost, Unstop, MLH, Microsoft Learn and others) and are subject to their terms.

<div align="center">

<br />

**If Zenkai helps you find something, give it a ⭐**

<sub>Built by <a href="https://github.com/ganesh-tadigadapa">Ganesh Tadigadapa</a></sub>

</div>
