# Masters Scout 🎓

A free, local planner for an AI/ML masters abroad. Use it to compare countries, shortlist universities, find
scholarships, and **find professors whose research matches your interests**, then keep track of your conversations with them.

## Getting started (Mac)

1. Go to https://github.com/Preetham8603-gif/masters-scout and click **Code → Download ZIP**. Unzip it and move the folder somewhere permanent (e.g. Documents).
2. Double-click **`setup.command`** (one time only). It installs everything and then opens the app.
   - If macOS says it "cannot be opened": **right-click → Open → Open**. You only need to do this once per script.
   - If you don't have Python 3.10+, it opens python.org. Install it, then run `setup.command` again.
3. From then on, double-click **`start.command`** to open the app. Keep that window open while you use the app.
4. When there's a new version, double-click **`update.command`**. Your profile, professor tracker and ranks are kept.

The first professor search downloads a small local AI model (about 90 MB, one time only).

Your personal files are in `data/` (`profile.json`, `scout.db`, `rankings.csv`, `settings.json`).
To be safe, back them up now and then. Updates replace `countries.yaml` and `scholarships.yaml`,
so if you have notes of your own, put them in the app's notes fields rather than in those files.

## For the maintainer: sending an update

```bash
cd ~/masters-scout
git add -A && git commit -m "Describe the change"
git push
```

Then tell your brother to double-click `update.command`.

## Pages

| Page | What it does |
|---|---|
| **Home** | Profile (interests, target countries, projects) and settings |
| **Countries** | Rank ~20 countries by what matters to you (cost, work visa, funding, jobs...) |
| **Universities** | AI research strength by university; add QS/THE/ARWU ranks to keep only the top 500; build a shortlist |
| **Professors** | Describe what you want to work on and get matching faculty with their recent papers, homepage and Scholar link. Or browse by area |
| **Scholarships** | ~40 funding options open to Indian students, filtered by country / funding type / work-experience need |
| **Outreach** | Track each professor (Shortlisted → Emailed → Replied...), follow-up reminders, email drafts built from a paper you actually read |
| **Explore Interests** | AI research topics, how fast they are growing, and top papers, to help decide what to specialise in |

## Where the data comes from

- **CSRankings** (csrankings.org): who is AI faculty, their homepages, and papers at top AI conferences. Refreshed monthly. Personal, non-commercial use.
- **OpenAlex** (openalex.org): papers and topics. Without a key there is a small *shared* free daily allowance (about 100 requests).
  Every result is cached for 14 days, so repeat searches are free. You can add a free personal key on the Home page.
- **data/countries.yaml** and **data/scholarships.yaml**: hand-written notes (checked 2026-11). Edit them as you learn more.
  Fees, visas and deadlines change, so always confirm on the official link.
- **QS / THE / ARWU ranks**: not freely downloadable, so you type them in on the Universities page (saved to `data/rankings.csv`).

Your own data (profile, tracker, ranks) lives in `data/` on your computer only. The app never sends emails.

## Tests

```bash
.venv/bin/python -m pytest -q
```
