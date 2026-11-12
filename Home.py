import streamlit as st

from scout import openalex
from scout.countries import country_names
from scout.outreach import connect, due_followups, list_contacts
from scout.profile import save_profile, load_settings, save_settings
from scout.ui import profile, setup

setup("Home")
p = profile()

st.title("🎓 Masters Scout")
st.write(
    "A planner for a masters in AI/ML abroad. Use it to **compare countries**, **shortlist universities**, "
    "**find scholarships**, and **find professors whose research matches your interests**, then build a relationship "
    "with them over the next year."
)

contacts = list_contacts(connect())
due = due_followups(contacts)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Target countries", len(p.countries))
c2.metric("Interests set", len(p.interests) + (1 if p.interest_text else 0))
c3.metric("Professors tracked", len(contacts))
c4.metric("Follow-ups due", len(due))
if due:
    st.warning("Follow-ups due: " + ", ".join(f"{c['name']} ({c['institution']})" for c in due) + ". See the **Outreach** page.")

st.subheader("Suggested path")
st.markdown(
    """
1. **Explore Interests**: not sure what to work on yet? Browse fast-growing AI topics and tick the ones you like.
2. **Countries**: set what matters to you (cost, work visa, funding...) and see which countries rank highest.
3. **Universities**: compare AI research strength. Add QS/THE ranks to keep only the top 500.
4. **Professors**: get professors who match your interests, read 1-2 of their papers, and add them to Outreach.
5. **Outreach**: write a thoughtful first email, track replies, and follow up after about 2 weeks.
6. **Scholarships**: note deadlines. Many close 9-12 months before the intake.
"""
)

st.subheader("Profile")
names = country_names()
with st.form("profile"):
    a, b, c = st.columns(3)
    p.name = a.text_input("Name", p.name)
    p.degree = b.text_input("Degree", p.degree)
    p.graduation_year = c.number_input("Graduation year", 2025, 2035, p.graduation_year)
    p.cgpa = a.text_input("CGPA", p.cgpa)
    p.target_intake = b.text_input("Target intake", p.target_intake)
    p.budget_inr_lakh = c.number_input("Total budget (INR lakh, before scholarships)", 0, 200, p.budget_inr_lakh)
    p.countries = st.multiselect(
        "Countries you are considering", list(names), [x for x in p.countries if x in names],
        format_func=lambda x: f"{names[x]} ({x})",
    )
    p.interest_text = st.text_area(
        "Research interests in your own words (fine to leave empty for now)",
        p.interest_text,
        placeholder="e.g. making large language models reason more reliably; efficient inference on small devices",
    )
    tags = st.text_input("Interest tags (comma-separated)", ", ".join(p.interests))
    p.projects = st.text_area("Projects / research so far (used in email drafts)", p.projects)
    p.skills = st.text_input("Skills", p.skills, placeholder="Python, PyTorch, HuggingFace, ...")
    if st.form_submit_button("Save profile", type="primary"):
        p.interests = [t.strip() for t in tags.split(",") if t.strip()]
        save_profile(p)
        st.success("Saved.")

with st.expander("Settings: OpenAlex API key and follow-up timing"):
    s = load_settings()
    st.markdown(
        "Professor search uses **OpenAlex**, a free database of research papers. Without a key, everyone on your network "
        "shares a small daily allowance (about 100 searches). Results are cached, so repeat searches are free. "
        "For more, create a free key at [openalex.org/settings/api](https://openalex.org/settings/api) and paste it here."
    )
    key = st.text_input("OpenAlex API key (optional)", s.get("openalex_api_key", ""), type="password")
    days = st.number_input("Remind me to follow up after (days)", 5, 60, int(s.get("followup_days", 14)))
    if st.button("Save settings"):
        s.update({"openalex_api_key": key.strip(), "followup_days": int(days)})
        save_settings(s)
        st.success("Saved.")
    u = openalex.usage_today()
    st.caption(f"Today: {u['requests']} OpenAlex requests (≈ ${u['cost_usd']:.3f} of the free allowance).")

st.caption(
    "Data: CSRankings (faculty, AI venues), OpenAlex (papers, topics), and hand-curated country and scholarship notes "
    "(checked 2026-11). Always confirm fees, visas and deadlines on the official sites."
)
