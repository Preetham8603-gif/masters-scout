from datetime import date

import pandas as pd
import streamlit as st

from scout import openalex
from scout.outreach import (STATUSES, TEMPLATE_NAMES, connect, delete_contact, draft_email, due_followups,
                            list_contacts, update_contact)
from scout.profile import load_settings
from scout.ui import link, profile, setup

setup("Outreach", "✉️")
p = profile()
con = connect()
followup_days = int(load_settings().get("followup_days", 14))

st.title("✉️ Outreach tracker")

with st.expander("📖 How to contact professors well (read this first)", expanded=False):
    st.markdown(
        """
- **Quality over quantity.** Write to about 3-5 professors a month, not 50 at once. Professors spot copy-paste emails right away.
- **Read before you write.** Pick one recent paper, read it properly, and if possible run its code. Mention one specific thing.
- **Ask a real question**, not "can I join your lab?". A good question about the paper is what gets a reply.
- **Keep it short**: about 150 words. Put a clear subject, and attach a CV only when you ask about positions.
- **Follow up once** after about 2 weeks. If there's still no reply, move on politely. Professors are busy, and it's not personal.
- **Build the relationship over time**: share a small reproduction, blog post or extension of their work. When you ask about
  MS / RA positions, they will already know you.
- **Right timing:** start conversations about 9-12 months before the application deadline and ask about positions about 3-6 months before.
"""
    )

contacts = list_contacts(con)
if not contacts:
    st.info("No professors yet. Add some from the **Professors** page.")
    st.stop()

due = due_followups(contacts)
if due:
    st.warning("⏰ Follow-up due: " + ", ".join(c["name"] for c in due))

counts = pd.Series([c["status"] for c in contacts]).value_counts()
cols = st.columns(len(STATUSES))
for col, s in zip(cols, STATUSES):
    col.metric(s, int(counts.get(s, 0)))

flt = st.multiselect("Show statuses", STATUSES, [s for s in STATUSES if s != "Not a fit"])
for c in [c for c in contacts if c["status"] in flt]:
    badge = " ⏰" if c in due else ""
    with st.expander(f"**{c['name']}**, {c['institution']} · {c['status']}{badge}"):
        st.markdown(" · ".join(x for x in [link("Homepage", c["homepage"]), link("Scholar", c["scholar_url"]),
                                           link("OpenAlex", c["openalex_id"])] if x))
        papers = c["papers"]
        if c["openalex_id"] and st.button("Load their latest papers", key=f"more_{c['id']}"):
            try:
                ws = openalex.author_works(c["openalex_id"], date.today().year - 3)
                papers = [{"title": w["title"], "year": w["publication_year"], "url": openalex.work_url(w),
                           "cited_by": w.get("cited_by_count", 0)} for w in ws]
                st.session_state[f"papers_{c['id']}"] = papers
            except openalex.BudgetError as e:
                st.error(str(e))
        papers = st.session_state.get(f"papers_{c['id']}", papers)
        for pp in papers[:10]:
            st.markdown(f"- [{pp['title']}]({pp['url']}) ({pp['year']})")

        with st.form(f"f_{c['id']}"):
            a, b = st.columns(2)
            status = a.selectbox("Status", STATUSES, STATUSES.index(c["status"]) if c["status"] in STATUSES else 0)
            last = b.date_input("Last contact", date.fromisoformat(c["last_contact"]) if c["last_contact"] else None)
            notes = st.text_area("Notes (what they work on, what you discussed, ideas)", c["notes"] or "")
            s1, s2 = st.columns([1, 5])
            if s1.form_submit_button("Save", type="primary"):
                update_contact(con, c["id"], status, notes, last.isoformat() if last else None, followup_days)
                st.rerun()
            if s2.form_submit_button("Remove from tracker"):
                delete_contact(con, c["id"])
                st.rerun()
        if c["next_followup"]:
            st.caption(f"Follow up on {c['next_followup']} if there's no reply.")

        st.markdown("**Draft an email**")
        t = st.selectbox("Template", list(TEMPLATE_NAMES), key=f"t_{c['id']}")
        titles = [pp["title"] for pp in papers]
        chosen = st.selectbox("Paper you read", titles, key=f"p_{c['id']}") if titles else None
        paper = next((pp for pp in papers if pp["title"] == chosen), None)
        take = st.text_area("Your takeaway, in your own words", key=f"tk_{c['id']}",
                            placeholder="What the paper does and the part you found most interesting")
        qn = st.text_area("Your question", key=f"q_{c['id']}", placeholder="A specific question you had while reading")
        st.code(draft_email(t, c, p, paper, take, qn), language="markdown")
        st.caption("Copy this into your email app and edit it. The app never sends email itself.")
