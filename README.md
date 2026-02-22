# IPL Performance Dashboard (Streamlit)

## Analytical Objective
Track IPL team performance over seasons and identify patterns related to winning (dominance years, result types, win margins).

## Data Source (Public)
This project uses IPL match-level data from Cricsheet (public cricket datasets).
- Data type: match summaries (CSV)
- Coverage: IPL seasons (varies by dataset snapshot)

## How Data Was Collected
Option A (Static for assignment):
1. Download the IPL match dataset manually from Cricsheet.
2. Export/save as `data/matches.csv`.
3. Commit `data/matches.csv` into this repository.

Option B (Refreshable workflow):
1. Download the latest IPL data from Cricsheet.
2. Replace `data/matches.csv` with the updated file.
3. Redeploy Streamlit Cloud (or push to GitHub, it redeploys automatically).

## How to Refresh / Update Data (Future Seasons)
When a new IPL season finishes:
1. Download the updated dataset (same source).
2. Replace `data/matches.csv` in the repo.
3. Push changes to GitHub; Streamlit Cloud will redeploy automatically.

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
