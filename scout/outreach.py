"""Outreach tracker (SQLite) and email drafts (Jinja templates)."""
import json
import sqlite3
from datetime import date, timedelta

from jinja2 import Environment, FileSystemLoader

from .paths import DB_FILE, TEMPLATES

STATUSES = ["Shortlisted", "Reading papers", "Emailed", "Replied", "Call scheduled", "Ongoing contact", "Not a fit"]
WAITING = {"Emailed"}  # statuses where we are waiting for them -> follow-up reminder


def connect(path=DB_FILE) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            institution TEXT,
            country TEXT,
            homepage TEXT,
            scholar_url TEXT,
            openalex_id TEXT,
            status TEXT DEFAULT 'Shortlisted',
            notes TEXT DEFAULT '',
            papers TEXT DEFAULT '[]',
            added TEXT,
            last_contact TEXT,
            next_followup TEXT,
            UNIQUE(name, institution)
        )"""
    )
    return con


def add_contact(con, prof: dict) -> bool:
    """Add a professor (dict from matcher). Returns False if already tracked."""
    cur = con.execute(
        """INSERT OR IGNORE INTO contacts (name, institution, country, homepage, scholar_url, openalex_id, papers, added)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            prof["name"],
            prof.get("institution"),
            prof.get("country"),
            prof.get("homepage"),
            prof.get("scholar_url"),
            prof.get("openalex_id"),
            json.dumps(prof.get("papers", [])),
            date.today().isoformat(),
        ),
    )
    con.commit()
    return cur.rowcount == 1


def next_followup_for(status: str, last_contact: str | None, followup_days: int) -> str | None:
    if status in WAITING and last_contact:
        return (date.fromisoformat(last_contact) + timedelta(days=followup_days)).isoformat()
    return None


def update_contact(con, cid: int, status: str, notes: str, last_contact: str | None, followup_days: int = 14) -> None:
    con.execute(
        "UPDATE contacts SET status=?, notes=?, last_contact=?, next_followup=? WHERE id=?",
        (status, notes, last_contact, next_followup_for(status, last_contact, followup_days), cid),
    )
    con.commit()


def delete_contact(con, cid: int) -> None:
    con.execute("DELETE FROM contacts WHERE id=?", (cid,))
    con.commit()


def list_contacts(con) -> list[dict]:
    rows = con.execute("SELECT * FROM contacts ORDER BY added DESC, id DESC").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["papers"] = json.loads(d["papers"] or "[]")
        out.append(d)
    return out


def due_followups(contacts: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    return [c for c in contacts if c.get("next_followup") and date.fromisoformat(c["next_followup"]) <= today]


_env = Environment(loader=FileSystemLoader(str(TEMPLATES)), trim_blocks=True, lstrip_blocks=True)

TEMPLATE_NAMES = {
    "First email": "email_first_contact.md.j2",
    "Follow-up (no reply)": "email_followup.md.j2",
    "Asking about MS / RA positions": "email_positions.md.j2",
}


def draft_email(template: str, contact: dict, profile, paper: dict | None, my_takeaway: str, my_question: str) -> str:
    last_name = contact["name"].split()[-1]
    return _env.get_template(TEMPLATE_NAMES[template]).render(
        prof_last=last_name,
        prof=contact,
        me=profile,
        paper=paper,
        takeaway=my_takeaway.strip(),
        question=my_question.strip(),
    )
