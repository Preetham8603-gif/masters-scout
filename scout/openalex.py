"""Small OpenAlex client (https://openalex.org) with on-disk caching.

Without an API key OpenAlex gives a small shared daily budget (~100 requests), so every
response is cached for 14 days and each search asks for 200 results per request.
A free personal key (openalex.org/settings/api) can be added on the Home page.
"""
import json
from datetime import date

import requests_cache

from .paths import CACHE
from .profile import load_settings

API = "https://api.openalex.org"
USAGE_FILE = CACHE / "openalex_usage.json"

# OpenAlex sub-field ids: 1702 Artificial Intelligence, 1707 Computer Vision and Pattern Recognition
AI_SUBFIELDS = {"1702": "Artificial Intelligence", "1707": "Computer Vision & Pattern Recognition"}

_session = requests_cache.CachedSession(
    str(CACHE / "openalex_http"), backend="sqlite", expire_after=14 * 86400, allowable_codes=(200,)
)


class BudgetError(RuntimeError):
    pass


def _record_usage(cost: float) -> None:
    today = date.today().isoformat()
    usage = json.loads(USAGE_FILE.read_text()) if USAGE_FILE.exists() else {}
    if usage.get("date") != today:
        usage = {"date": today, "requests": 0, "cost_usd": 0.0}
    usage["requests"] += 1
    usage["cost_usd"] = round(usage["cost_usd"] + (cost or 0), 4)
    USAGE_FILE.write_text(json.dumps(usage))


def usage_today() -> dict:
    if USAGE_FILE.exists():
        u = json.loads(USAGE_FILE.read_text())
        if u.get("date") == date.today().isoformat():
            return u
    return {"date": date.today().isoformat(), "requests": 0, "cost_usd": 0.0}


def get(path: str, params: dict) -> dict:
    params = dict(params)
    key = load_settings().get("openalex_api_key", "").strip()
    if key:
        params["api_key"] = key
    r = _session.get(f"{API}{path}", params=params, timeout=60)
    if r.status_code == 429:
        raise BudgetError(
            "OpenAlex daily free limit reached. Results already fetched still work (cached). "
            "Try again tomorrow, or add a free OpenAlex API key on the Home page."
        )
    r.raise_for_status()
    data = r.json()
    if not getattr(r, "from_cache", False):
        _record_usage(data.get("meta", {}).get("cost_usd", 0.001))
    return data


def search_works(query: str, countries: list[str], since_year: int, pages: int = 1) -> list[dict]:
    """Most relevant recent works for `query` with at least one author in `countries`."""
    flt = ",".join(
        [
            "authorships.institutions.country_code:" + "|".join(c.upper() for c in countries),
            f"from_publication_date:{since_year}-01-01",
            "type:article|preprint",
        ]
    )
    works = []
    for page in range(1, pages + 1):
        data = get(
            "/works",
            {
                "search": query,
                "filter": flt,
                "per-page": 200,
                "page": page,
                "select": "id,doi,title,publication_year,authorships,primary_topic,cited_by_count",
            },
        )
        works += data.get("results", [])
        if len(data.get("results", [])) < 200:
            break
    return works


def author_works(author_id: str, since_year: int, n: int = 25) -> list[dict]:
    """Recent works of one author (for the 'more papers' view on a professor card)."""
    aid = author_id.rsplit("/", 1)[-1]
    data = get(
        "/works",
        {
            "filter": f"author.id:{aid},from_publication_date:{since_year}-01-01",
            "sort": "publication_date:desc",
            "per-page": n,
            "select": "id,doi,title,publication_year,primary_topic,cited_by_count",
        },
    )
    return data.get("results", [])


def topic_counts(since: str, until: str | None = None) -> dict[str, dict]:
    """Paper counts per OpenAlex topic within the AI sub-fields for a date range."""
    flt = f"primary_topic.subfield.id:{'|'.join(AI_SUBFIELDS)},from_publication_date:{since}"
    if until:
        flt += f",to_publication_date:{until}"
    data = get("/works", {"filter": flt, "group_by": "primary_topic.id"})
    return {g["key"].rsplit("/", 1)[-1]: {"name": g["key_display_name"], "count": g["count"]} for g in data.get("group_by", [])}


def ai_topics() -> list[dict]:
    """All topics in the AI sub-fields, with description and keywords."""
    out = []
    for page in (1, 2):
        data = get(
            "/topics",
            {
                "filter": f"subfield.id:{'|'.join(AI_SUBFIELDS)}",
                "per-page": 200,
                "page": page,
                "select": "id,display_name,description,keywords,works_count,subfield",
            },
        )
        out += data.get("results", [])
        if len(data.get("results", [])) < 200:
            break
    return out


def topic_top_works(topic_id: str, countries: list[str], since_year: int, n: int = 8) -> list[dict]:
    flt = f"primary_topic.id:{topic_id},from_publication_date:{since_year}-01-01"
    if countries:
        flt += ",authorships.institutions.country_code:" + "|".join(c.upper() for c in countries)
    data = get(
        "/works",
        {
            "filter": flt,
            "sort": "cited_by_count:desc",
            "per-page": n,
            "select": "id,doi,title,publication_year,authorships,cited_by_count",
        },
    )
    return data.get("results", [])


def work_url(w: dict) -> str:
    return w.get("doi") or w.get("id", "")
