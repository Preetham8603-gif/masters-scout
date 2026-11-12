import streamlit as st

from scout.countries import country_names, load_scholarships
from scout.ui import profile, setup

setup("Scholarships", "💰")
p = profile()
names = {**country_names(), "ANY": "Any country", "HU": "Hungary"}

st.title("💰 Scholarships & funding")
st.caption("Checked 2026-11. Amounts, eligibility and deadlines change every year, so open the official link before planning around one.")

df = load_scholarships()
c1, c2, c3 = st.columns(3)
mine = c1.toggle("Only my target countries (+ 'any country')", value=True)
funding = c2.multiselect("Funding type", ["full", "partial", "loan"], ["full", "partial", "loan"])
fresh = c3.toggle("Hide schemes that need work experience", value=True)

if mine:
    df = df[df["country"].isin(p.countries + ["ANY"])]
df = df[df["funding"].isin(funding)]
if fresh:
    df = df[~df["needs_work_exp"]]

df = df.assign(where=df["country"].map(lambda c: names.get(c, c)))
st.write(f"**{len(df)} options**")
st.dataframe(
    df[["name", "where", "funding", "amount", "deadline", "needs_work_exp", "notes", "link"]],
    hide_index=True,
    use_container_width=True,
    column_config={
        "link": st.column_config.LinkColumn("Official link", display_text="open"),
        "needs_work_exp": "Needs work exp.",
        "where": "Study in",
    },
)

st.subheader("Tips")
st.markdown(
    """
- **The biggest "scholarship" is often a professor.** Thesis-based MSc in Canada, research masters in Australia/HK/Singapore,
  RA/TA roles in the US, and MEXT/GKS university tracks all go much better when a professor already knows you.
- **Erasmus Mundus** is one of the best fully funded options for a fresh graduate. Applications often close in Jan-Feb for the next September.
- **Germany, Italy, Austria and France** have low tuition, so a smaller scholarship or a student job can cover living costs.
- Indian **loan scholarships** (J.N. Tata, K.C. Mahindra, Narotam Sekhsaria) can be combined with university awards.
"""
)
