"""Nemo, the guide that lives in the corner of every page.

Nemo is not a language model and does not pretend to be one. It reads a
message for the things Zenkai can actually filter on (a category, a topic,
"free", "remote", "closing soon"), runs the same search the browse page
runs, and answers in plain sentences. A handful of common questions about
careers and about the site itself get short, written-by-hand answers.

Keeping it rule-based means it costs nothing to run, answers instantly, and
can only ever point at opportunities that are really in the catalogue.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.models.enums import Category
from app.models.opportunity import Opportunity
from app.models.user import User
from app.repositories.opportunity_repository import OpportunityQuery
from app.services import opportunity_service as svc

#: How many results go into one reply. More than this stops being a chat.
RESULTS_PER_REPLY = 5

#: How many rows a topic search pulls before the whole-word check. The text
#: search is a substring match ("ai" is inside "email"), so it over-fetches
#: and the topic's own pattern decides what really matches.
TOPIC_CANDIDATES = 200


@dataclass(frozen=True)
class Topic:
    #: As it reads mid-sentence: "Python", "machine learning".
    label: str
    #: What the database substring search is given to narrow things down.
    term: str
    #: The whole-word pattern a record (and the message) must actually match.
    pattern: re.Pattern
    #: The search box text for "See all" on the browse page.
    browse: str


def _topic(label: str, term: str, pattern: str, browse: str | None = None) -> Topic:
    return Topic(label, term, re.compile(pattern, re.IGNORECASE), browse or term)


# Order matters: the more specific entry wins ("machine learning" before "AI",
# "javascript" before "java").
TOPICS: list[Topic] = [
    _topic("machine learning", "learning", r"\bmachine learning\b|\bml\b|\bdeep learning\b", "machine learning"),
    _topic("data science", "data", r"\bdata (science|scientist|analy\w+|engineer\w*)\b|\banalytics\b"),
    _topic("AI", "ai", r"\b(ai|a\.i\.|artificial intelligence|gen ?ai|llms?|generative)\b"),
    _topic("JavaScript", "script", r"\b(javascript|typescript|js|node(\.js)?)\b", "javascript"),
    _topic("React", "react", r"\breact\b"),
    _topic("Java", "java", r"\bjava\b"),
    _topic("Python", "python", r"\bpython\b"),
    _topic("C++", "c++", r"(?<!\w)c\+\+(?!\w)"),
    _topic("Rust", "rust", r"\brust\b"),
    _topic("Go", "golang", r"\bgolang\b"),
    _topic("SQL", "sql", r"\b(sql|postgres\w*|mysql|database\w*)\b"),
    _topic("web development", "web", r"\bweb ?(dev\w*)?\b|\bfront[- ]?end\b|\bback[- ]?end\b|\bfull[- ]?stack\b"),
    _topic("Android", "android", r"\bandroid\b|\bkotlin\b"),
    _topic("iOS", "ios", r"\bios\b|\bswift\b"),
    _topic("Flutter", "flutter", r"\bflutter\b"),
    _topic("mobile app", "mobile", r"\bmobile\b|\bapp dev\w*"),
    _topic("AWS", "aws", r"\baws\b|\bamazon web services\b"),
    _topic("Azure", "azure", r"\bazure\b"),
    _topic("Google Cloud", "google cloud", r"\bgoogle cloud\b|\bgcp\b"),
    _topic("cloud", "cloud", r"\bcloud\b"),
    _topic("DevOps", "devops", r"\bdev ?ops\b|\bkubernetes\b|\bdocker\b|\bci/cd\b"),
    _topic("cybersecurity", "security", r"\bcyber\w*|\bsecurity\b|\bethical hacking\b|\bpen ?test\w*"),
    _topic("blockchain", "blockchain", r"\bblockchain\b|\bweb3\b|\bcrypto\w*"),
    _topic("quantum", "quantum", r"\bquantum\b"),
    _topic("robotics", "robot", r"\brobot\w*|\biot\b|\bembedded\b"),
    _topic("game development", "game", r"\bgame ?dev\w*|\bgaming\b|\bunity\b|\bunreal\b"),
    _topic("design", "design", r"\b(ui|ux|ui/ux|figma|graphic design|product design|design)\b"),
    _topic("product management", "product", r"\bproduct manag\w*|\bpm intern\w*"),
    _topic("marketing", "marketing", r"\bmarketing\b|\bseo\b|\bsocial media\b"),
    _topic("finance", "financ", r"\bfinanc\w*|\bfintech\b|\binvest\w*|\bquant\b"),
    _topic("open source", "open source", r"\bopen[- ]source\b"),
    _topic("Linux", "linux", r"\blinux\b"),
    _topic("networking", "network", r"\bnetworking\b|\bcisco\b|\bccna\b"),
    _topic("research", "research", r"\bresearch\b"),
]

#: Category words, checked in this order. A message can name several.
CATEGORY_PATTERNS: list[tuple[str, re.Pattern]] = [
    (Category.INTERNSHIPS.value, re.compile(r"\bintern(ship)?s?\b|\bjobs?\b|\bplacements?\b|\bwork experience\b", re.I)),
    (Category.HACKATHONS.value, re.compile(r"\bhack(athon)?s?\b|\bcompetitions?\b|\bcontests?\b|\bchallenges?\b|\bquiz\w*|\bcase stud", re.I)),
    (Category.SCHOLARSHIPS.value, re.compile(r"\bscholarships?\b|\bgrants?\b|\bfunding\b|\bfinancial aid\b|\btuition\b", re.I)),
    (Category.PROGRAMS.value, re.compile(r"\bprogram(me)?s?\b|\bfellowships?\b|\bworkshops?\b|\bbootcamps?\b|\bmentor\w*|\bsummer school\b|\bgsoc\b|\boutreachy\b|\bambassador", re.I)),
    (Category.TECH_BENEFITS.value, re.compile(r"\bdiscounts?\b|\bstudent pack\b|\bcredits\b|\bsoftware\b|\bbenefits?\b|\bperks?\b|\blicen[cs]es?\b|\bfree tools?\b", re.I)),
    (Category.CERTIFICATIONS.value, re.compile(r"\bcertif\w*|\bcerts?\b|\bcourses?\b|\bexams?\b|\bcredentials?\b|\bbadges?\b|\blearn\w*|\bupskill\w*|\bstudy\b", re.I)),
]

CATEGORY_NOUNS = {
    Category.INTERNSHIPS.value: "internships",
    Category.HACKATHONS.value: "hackathons and competitions",
    Category.SCHOLARSHIPS.value: "scholarships",
    Category.PROGRAMS.value: "programs and workshops",
    Category.TECH_BENEFITS.value: "student tech benefits",
    Category.CERTIFICATIONS.value: "certifications and courses",
}

FREE = re.compile(r"\bfree\b|\bno cost\b|\bwithout paying\b|\bzero cost\b", re.I)
REMOTE = re.compile(r"\bremote\b|\bonline\b|\bwork from home\b|\bwfh\b|\bvirtual\b", re.I)
NEWEST = re.compile(r"\b(latest|newest|recent|new ones?|just added)\b", re.I)
FOR_ME = re.compile(r"\bfor me\b|\brecommend\w*|\bsuggest\w*|\bsuits? me\b|\bmatch\w* me\b|\bmy profile\b|\bbest for\b", re.I)
#: (pattern, days) - the first match wins, so the tightest window comes first.
WITHIN = [
    (re.compile(r"\btoday\b", re.I), 1),
    (re.compile(r"\btomorrow\b", re.I), 2),
    (re.compile(r"\bthis week\b|\bclosing soon\b|\bending soon\b|\burgent\b|\bsoon\b|\blast date\b", re.I), 7),
    (re.compile(r"\bnext week\b", re.I), 14),
    (re.compile(r"\bthis month\b|\bnext 30 days\b", re.I), 30),
]

GREETING = re.compile(r"^\s*(hi+|hello+|hey+|yo|hola|namaste|good (morning|afternoon|evening))\b", re.I)
THANKS = re.compile(r"\b(thanks?|thank you|thx|ty)\b", re.I)
BYE = re.compile(r"^\s*(bye|goodbye|see you|cya)\b", re.I)
HELP = re.compile(r"\bwho are you\b|\bwhat (can|do) you do\b|\bhow (do|does) (this|you|nemo) work\b|^\s*help\s*$|\bwhat is nemo\b", re.I)


@dataclass(frozen=True)
class Guide:
    pattern: re.Pattern
    text: str
    suggestions: tuple[str, ...] = ()
    #: Optional search run alongside the answer, as if the student had typed it.
    search: str | None = None
    #: A question about the site itself: answer it, never turn it into a search.
    about_site: bool = False


GUIDES: list[Guide] = [
    Guide(
        re.compile(r"\b(resume|cv|portfolio)\b", re.I),
        "A few things that make a resume land for internships: keep it to one page, "
        "lead with projects rather than coursework, and give every project a number "
        "(users, speed-up, accuracy). Link a GitHub or portfolio people can actually "
        "click. Hackathon projects count, and they are one of the fastest ways to get "
        "something real on the page.",
        ("Hackathons this month", "Free certifications"),
    ),
    Guide(
        re.compile(r"\binterview\w*|\bdsa\b|\bleetcode\b|\bplacement prep\b", re.I),
        "For tech interviews, split your prep: data structures and algorithms a little "
        "every day, plus one or two projects you can explain end to end, including what "
        "you would do differently. Coding contests are good practice under a clock.",
        ("Coding competitions", "Internships closing soon"),
        search="competitions",
    ),
    Guide(
        re.compile(r"\b(beginner|fresher|first year|just started|new to|no experience|where (do|should) i start|how (do|to) i start|getting started)\b", re.I),
        "Starting out is easier than it looks. Pick one area you are curious about, "
        "do a free course or certification in it, then build one small project and "
        "take it to a beginner-friendly hackathon. That gives you something to show "
        "when internship applications open. Here are some free places to start:",
        ("Beginner hackathons", "Student tech benefits"),
        search="free certifications",
    ),
    Guide(
        re.compile(r"\b(career (switch|change)|switch(ing)? (careers?|to)|working professional|experienced|mid[- ]career|upskill\w*)\b", re.I),
        "If you are already working, certifications from the big cloud and tech vendors "
        "are the quickest signal for a switch, and programs and fellowships give you a "
        "structured way in. Pair one credential with a project in the new area.",
        ("Cloud certifications", "Programs and fellowships"),
        search="certifications",
    ),
    Guide(
        re.compile(r"\bsav(e|ed|ing)\b|\bbookmark\w*", re.I),
        "Tap the bookmark on any opportunity to save it. Everything you save lives on "
        "the Saved page, and anything with a date also shows up under Deadlines, so "
        "you can see what closes next.",
        ("What closes this week?",),
        about_site=True,
    ),
    Guide(
        re.compile(r"\bprofile\b|\bpreferences?\b|\bpersonali[sz]\w*", re.I),
        "Fill in your profile with what you study, your skills and what you are "
        "interested in, and Zenkai ranks opportunities for you and shows why each one "
        "matched. Then ask me for \"recommendations for me\".",
        ("Recommend something for me",),
        about_site=True,
    ),
    Guide(
        re.compile(r"\bverif\w*|\bneeds review\b|\bcurated\b|\btrust\w*|\blegit\w*|\bscam\w*|\bfake\b", re.I),
        "Every listing links back to the page it came from. \"Curated\" ones were written "
        "by hand from the official page; \"Needs verification\" ones were found "
        "automatically and nobody has checked them yet. Either way, confirm the details "
        "on the official site before you apply, and never pay anyone to apply for an "
        "internship.",
        ("Free certifications", "Remote internships"),
        about_site=True,
    ),
    Guide(
        re.compile(r"\b(is (zenkai|this|it) free|cost to use|pricing|subscription)\b", re.I),
        "Zenkai is free. No subscription, no paid tier. Some opportunities cost money "
        "(a paid exam, for example) and the listing says so when the source publishes it.",
        ("Free certifications",),
        about_site=True,
    ),
]


@dataclass
class Understanding:
    categories: list[str] = field(default_factory=list)
    topics: list[Topic] = field(default_factory=list)
    free_only: bool = False
    remote: bool | None = None
    within_days: int | None = None
    newest: bool = False
    for_me: bool = False

    @property
    def is_search(self) -> bool:
        return bool(
            self.categories or self.topics or self.free_only or self.remote
            or self.within_days or self.newest or self.for_me
        )


@dataclass
class NemoReply:
    text: str
    results: list[tuple[Opportunity, dict]] = field(default_factory=list)
    browse_url: str | None = None
    suggestions: list[str] = field(default_factory=list)


def understand(message: str) -> Understanding:
    text = message.lower()
    u = Understanding()
    u.categories = [value for value, pattern in CATEGORY_PATTERNS if pattern.search(text)]
    for topic in TOPICS:
        if topic.pattern.search(text):
            # "machine learning" already claimed the word "learning"; do not let
            # the certifications pattern or a broader topic double count it.
            if topic.label == "cloud" and any(t.label in {"AWS", "Azure", "Google Cloud"} for t in u.topics):
                continue
            if topic.label == "AI" and any(t.label == "machine learning" for t in u.topics) and " ai" not in f" {text}":
                continue
            u.topics.append(topic)
    # "learn" in "machine learning" is not a request for courses.
    if (
        Category.CERTIFICATIONS.value in u.categories
        and any(t.label == "machine learning" for t in u.topics)
        and not re.search(r"\bcertif\w*|\bcerts?\b|\bcourses?\b|\bexams?\b|\blearn\b|\bupskill", text)
    ):
        u.categories.remove(Category.CERTIFICATIONS.value)
    u.free_only = bool(FREE.search(text))
    u.remote = True if REMOTE.search(text) else None
    u.newest = bool(NEWEST.search(text))
    u.for_me = bool(FOR_ME.search(text))
    for pattern, days in WITHIN:
        if pattern.search(text):
            u.within_days = days
            break
    return u


def _haystack(opportunity: Opportunity) -> str:
    parts = [
        opportunity.title or "",
        opportunity.summary or "",
        " ".join(opportunity.skills or []),
        " ".join(opportunity.tags or []),
        opportunity.organization.name if opportunity.organization else "",
    ]
    return " ".join(parts)


def _query(u: Understanding, user: User | None, statuses: list[str], *, search: str | None, limit: int) -> OpportunityQuery:
    if u.for_me and user is not None and user.preferences is not None:
        sort = "relevance"
    elif u.newest:
        sort = "newest"
    else:
        sort = "deadline"
    return OpportunityQuery(
        search=search,
        categories=list(u.categories),
        free_only=u.free_only,
        remote=u.remote,
        statuses=statuses,
        deadline_within_days=u.within_days,
        sort=sort,
        limit=limit,
    )


def _search(db: Session, u: Understanding, user: User | None, statuses: list[str]):
    """Return (results, total, exact). `exact` is False when total is a lower bound."""
    if not u.topics:
        return (*svc.list_opportunities(db, _query(u, user, statuses, search=None, limit=RESULTS_PER_REPLY), user), True)

    matched: list[tuple[Opportunity, dict]] = []
    seen: set[str] = set()
    capped = False
    for topic in u.topics[:2]:
        rows, total = svc.list_opportunities(
            db, _query(u, user, statuses, search=topic.term, limit=TOPIC_CANDIDATES), user
        )
        capped = capped or total > TOPIC_CANDIDATES
        for pair in rows:
            opportunity = pair[0]
            if opportunity.id not in seen and topic.pattern.search(_haystack(opportunity)):
                seen.add(opportunity.id)
                matched.append(pair)
    return matched[:RESULTS_PER_REPLY], len(matched), not capped


def _browse_url(u: Understanding, user: User | None) -> str:
    params: list[tuple[str, str]] = [("category", c) for c in u.categories]
    if u.topics:
        params.append(("q", u.topics[0].browse))
    if u.free_only:
        params.append(("free_only", "true"))
    if u.remote:
        params.append(("remote", "true"))
    if u.within_days:
        params.append(("deadline_within_days", str(u.within_days)))
    if u.for_me and user is not None and user.preferences is not None:
        params.append(("sort", "relevance"))
    elif u.newest:
        params.append(("sort", "newest"))
    return "/opportunities" + (f"?{urlencode(params)}" if params else "")


def _describe(u: Understanding) -> str:
    """'free remote Python internships closing this week', and so on."""
    words: list[str] = []
    if u.free_only:
        words.append("free")
    if u.remote:
        words.append("remote")
    if u.topics:
        words.append(" / ".join(t.label for t in u.topics[:2]))
    if len(u.categories) == 1:
        words.append(CATEGORY_NOUNS[u.categories[0]])
    elif u.categories:
        words.append(" and ".join(CATEGORY_NOUNS[c].split(" and ")[0] for c in u.categories[:2]))
    else:
        words.append("opportunities")
    phrase = " ".join(words)
    if u.within_days == 1:
        phrase += " closing today"
    elif u.within_days == 2:
        phrase += " closing by tomorrow"
    elif u.within_days == 7:
        phrase += " closing this week"
    elif u.within_days:
        phrase += f" closing in the next {u.within_days} days"
    return phrase


def _sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:]


def _follow_ups(u: Understanding) -> list[str]:
    """Quick replies that narrow the current search. Each one is a full message,
    because Nemo keeps no memory between turns."""
    topic = f"{u.topics[0].label} " if u.topics else ""
    noun = CATEGORY_NOUNS[u.categories[0]].split(" and ")[0] if u.categories else "opportunities"
    options: list[str] = []
    if not u.free_only:
        options.append(f"Free {topic}{noun}")
    if not u.remote and Category.INTERNSHIPS.value in u.categories:
        options.append(f"Remote {topic}internships")
    if not u.within_days:
        options.append(_sentence_case(f"{topic}{noun} closing this week"))
    if not topic and Category.INTERNSHIPS.value not in u.categories:
        options.append("Remote internships")
    for other in ("Hackathons this month", "Free certifications", "Scholarships"):
        if other.lower() in (o.lower() for o in options):
            continue
        if len(options) >= 3:
            break
        options.append(other)
    return options[:3]


def _search_reply(db: Session, u: Understanding, user: User | None, statuses: list[str], lead: str = "") -> NemoReply:
    results, total, exact = _search(db, u, user, statuses)
    what = _describe(u)

    if results:
        if u.for_me and (user is None or user.preferences is None):
            note = " Fill in your profile and I can rank these for you."
        else:
            note = ""
        if len(results) == 1:
            count = f"I found one match for {what}."
        elif len(results) < RESULTS_PER_REPLY or (exact and total <= RESULTS_PER_REPLY):
            count = f"Here are the {len(results)} {what} I could find."
        elif exact:
            count = f"I found {total:,} {what}. Here are the first few."
        else:
            count = f"Here are some {what}."
        if len(results) > 1 and not u.newest and not (u.for_me and user and user.preferences):
            count = count.rstrip(".") + ", soonest deadline first."
        return NemoReply(
            text=f"{lead}{count}{note}",
            results=results,
            browse_url=_browse_url(u, user),
            suggestions=_follow_ups(u),
        )

    # Nothing matched. Loosen the request one step at a time and say what changed.
    for loosen, said in (
        ("within_days", "with that deadline"),
        ("topics", "for that topic"),
        ("free_only", "that are free"),
        ("remote", "that are remote"),
    ):
        value = getattr(u, loosen)
        if not value:
            continue
        looser = Understanding(**{**u.__dict__, loosen: [] if loosen == "topics" else (None if loosen in {"within_days", "remote"} else False)})
        if not looser.is_search:
            continue
        retry, total, exact = _search(db, looser, user, statuses)
        if retry:
            return NemoReply(
                text=(
                    f"{lead}I couldn't find any {what} right now. "
                    f"Here are {_describe(looser)} instead."
                ),
                results=retry,
                browse_url=_browse_url(looser, user),
                suggestions=_follow_ups(looser),
            )
    return NemoReply(
        text=(
            f"{lead}I couldn't find any {what} right now. New listings come in every few "
            "hours, so it is worth asking again later, or try something broader."
        ),
        suggestions=["Internships", "Hackathons this month", "Free certifications"],
    )


INTRO = (
    "Hi, I'm Nemo. I help you find internships, hackathons, certifications, "
    "scholarships and programs on Zenkai. Tell me what you are after, in your own "
    "words, like \"free Python certifications\" or \"remote internships closing this week\"."
)
STARTERS = ["Internships closing this week", "Free AI certifications", "Hackathons this month", "I'm a beginner, where do I start?"]


def respond(db: Session, message: str, user: User | None, statuses: list[str]) -> NemoReply:
    message = (message or "").strip()
    if not message:
        return NemoReply(text=INTRO, suggestions=STARTERS)

    u = understand(message)

    if HELP.search(message):
        return NemoReply(
            text=(
                "I'm Nemo, Zenkai's guide. I search the catalogue for you: name a kind of "
                "opportunity, a skill or topic, and anything like \"free\", \"remote\" or "
                "\"closing this week\". I can also help with getting started, resumes and "
                "interviews, and explain how the site works. I'm not an AI model, so I "
                "only ever show listings that are really on Zenkai."
            ),
            suggestions=STARTERS,
        )

    for guide in GUIDES:
        if guide.pattern.search(message):
            if u.is_search and not guide.about_site:
                # "how do I prepare for a Google interview" is advice; "free Python
                # courses for beginners" is a search with a bit of context.
                return _search_reply(db, u, user, statuses, lead=guide.text.rstrip(":") + "\n\n")
            if guide.search:
                reply = _search_reply(db, understand(guide.search), user, statuses, lead=guide.text + "\n\n")
                reply.suggestions = list(guide.suggestions) or reply.suggestions
                return reply
            return NemoReply(text=guide.text, suggestions=list(guide.suggestions))

    if u.is_search:
        return _search_reply(db, u, user, statuses)

    if GREETING.search(message):
        first = (user.name or "").split(" ")[0] if user is not None and not user.is_demo else ""
        hello = f"Hi {first}! " if first and first.lower() != "guest" else "Hi! "
        return NemoReply(text=hello + INTRO[len("Hi, "):], suggestions=STARTERS)
    if THANKS.search(message):
        return NemoReply(text="Happy to help. Good luck with your applications!", suggestions=STARTERS[:3])
    if BYE.search(message):
        return NemoReply(text="See you. New opportunities land every few hours, so check back soon.")

    return NemoReply(
        text=(
            "I didn't quite catch that. I'm best at finding opportunities: try naming a "
            "kind (internships, hackathons, certifications, scholarships, programs) or a "
            "skill like Python, AI or design."
        ),
        suggestions=STARTERS,
    )
