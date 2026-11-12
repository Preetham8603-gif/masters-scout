from datetime import date

import pandas as pd

from scout.countries import load_countries, score_countries, load_scholarships
from scout.csrankings import clean_name, name_key
from scout.matcher import build_faculty_index, match_author
from scout import outreach


def test_country_scores_respect_weights():
    only_cost = {f: 0 for f in load_countries()[0]["scores"]}
    only_cost["affordability"] = 5
    df = score_countries(only_cost)
    assert df.iloc[0]["Affordability (tuition + living)"] == 5
    assert df["Score"].between(0, 100).all()


def test_all_country_and_scholarship_entries_have_links():
    assert all(c["link"].startswith("https://") for c in load_countries())
    s = load_scholarships()
    assert s["link"].str.startswith("https://").all()
    assert set(s["funding"]) <= {"full", "partial", "loan"}


def test_name_normalisation():
    assert clean_name("A. P. Vinod 0001") == "A. P. Vinod"
    assert name_key("Matthias Nießner") == name_key("Matthias Niessner") == "matthias niessner"
    assert name_key("Jürgen  Schmidhuber") == "jurgen schmidhuber"
    assert name_key("J. Doe-Smith") == "doe smith"


FAC = pd.DataFrame(
    [
        {"name": "Jane Doe", "institution": "University of Toronto", "orcid": "0000-0001-0000-0001", "name_key": "jane doe"},
        {"name": "Jane Doe 0002", "institution": "TU Munich", "orcid": None, "name_key": "jane doe"},
    ]
)


def _auth(name, inst, orcid=None):
    return {"author": {"display_name": name, "orcid": orcid}, "institutions": [{"display_name": inst}]}


def test_match_by_orcid_then_name_and_institution():
    idx = build_faculty_index(FAC)
    assert match_author(_auth("J. Doe", "x", "https://orcid.org/0000-0001-0000-0001"), FAC, *idx) == 0
    assert match_author(_auth("Jane Doe", "Technical University of Munich"), FAC, *idx) == 1
    assert match_author(_auth("Jane Doe", "Stanford University"), FAC, *idx) is None
    assert match_author(_auth("John Roe", "University of Toronto"), FAC, *idx) is None


def test_followups(tmp_path):
    con = outreach.connect(tmp_path / "t.db")
    assert outreach.add_contact(con, {"name": "Jane Doe", "institution": "U", "papers": []})
    assert not outreach.add_contact(con, {"name": "Jane Doe", "institution": "U", "papers": []})
    cid = outreach.list_contacts(con)[0]["id"]
    outreach.update_contact(con, cid, "Emailed", "", "2026-01-01", followup_days=14)
    c = outreach.list_contacts(con)[0]
    assert c["next_followup"] == "2026-01-15"
    assert outreach.due_followups([c], date(2026, 1, 14)) == []
    assert outreach.due_followups([c], date(2026, 1, 15)) == [c]
    outreach.update_contact(con, cid, "Replied", "", "2026-01-10")
    assert outreach.list_contacts(con)[0]["next_followup"] is None
