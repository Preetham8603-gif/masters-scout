import streamlit as st

from scout.countries import DEFAULT_WEIGHTS, FACTORS, load_countries, score_countries
from scout.profile import save_profile
from scout.ui import profile, setup

setup("Countries", "🌍")
p = profile()
st.title("🌍 Compare countries")
st.caption("Scores are rough 1-5 judgements (checked 2026-11), not official data. Visa rules change often: always check the official link.")

with st.sidebar:
    st.subheader("What matters to you?")
    st.caption("0 = ignore, 5 = very important")
    weights = {f: st.slider(label, 0, 5, DEFAULT_WEIGHTS[f], key=f"w_{f}") for f, label in FACTORS.items()}
    regions = st.multiselect("Regions", ["Europe", "UK & Ireland", "USA & Canada", "Asia-Pacific"],
                             ["Europe", "UK & Ireland", "USA & Canada", "Asia-Pacific"])

countries = [c for c in load_countries() if c["region"] in regions]
df = score_countries(weights, countries)

st.dataframe(
    df,
    hide_index=True,
    use_container_width=True,
    column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f")},
)

top = df.head(6)["Code"].tolist()
if st.button(f"Use the top 6 as my target countries ({', '.join(top)})"):
    p.countries = top
    save_profile(p)
    st.success("Saved to your profile. The Universities and Professors pages will use these countries.")

st.subheader("Details")
by_code = {c["code"]: c for c in countries}
for _, row in df.iterrows():
    c = by_code[row["Code"]]
    with st.expander(f"{c['name']} · score {row['Score']:.0f}"):
        st.markdown(
            f"**Tuition:** {c['tuition']}  \n**Living:** {c['living']}  \n**After graduation:** {c['post_study']}  \n"
            f"**Notes:** {c['notes']}  \n[Official study portal]({c['link']})"
        )
