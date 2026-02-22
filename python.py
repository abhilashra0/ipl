import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="IPL Performance Dashboard", layout="wide")

# -----------------------------
# Helper: Load Data
# -----------------------------
@st.cache_data
def load_matches(path="data/matches.csv"):
    df = pd.read_csv(path)

    # Standardize columns expected in the dashboard
    # REQUIRED columns: season, date, team1, team2, winner, venue, win_by_runs, win_by_wickets
    # If your file uses different names, rename here once.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Make a "match_id" if not present
    if "match_id" not in df.columns:
        df["match_id"] = np.arange(1, len(df) + 1)

    # Winner clean
    df["winner"] = df["winner"].fillna("No Result")

    # Season clean
    if "season" not in df.columns:
        # fallback: season from year of date
        df["season"] = df["date"].dt.year

    # Create a "result_type" feature
    df["result_type"] = np.where(df["winner"].eq("No Result"), "No Result",
                         np.where(df["win_by_runs"].fillna(0) > 0, "Won by Runs",
                         np.where(df["win_by_wickets"].fillna(0) > 0, "Won by Wickets", "Other")))

    return df


# -----------------------------
# UI Header
# -----------------------------
st.title("🏏 IPL Performance Dashboard")
st.write(
    """
**Analytical Objective:** Understand how IPL team performance changes across seasons and what patterns most strongly relate to winning.  
This dashboard uses **real, publicly available match data** and is designed as a maintainable tool (data refresh steps in README).
"""
)

# -----------------------------
# Load Data
# -----------------------------
try:
    matches = load_matches()
except Exception as e:
    st.error("Could not load data/matches.csv. Make sure it exists in your repo.")
    st.exception(e)
    st.stop()

# -----------------------------
# Sidebar Filters (Dashboard elements #1, #2, #3)
# -----------------------------
st.sidebar.header("Filters")

seasons = sorted(matches["season"].dropna().unique().tolist())
default_seasons = seasons[-5:] if len(seasons) >= 5 else seasons

season_sel = st.sidebar.multiselect("Select Season(s)", seasons, default=default_seasons)

teams = sorted(pd.unique(matches[["team1", "team2"]].values.ravel("K")))
team_sel = st.sidebar.multiselect("Select Team(s)", teams, default=[])

min_date = matches["date"].min()
max_date = matches["date"].max()
date_range = st.sidebar.date_input("Date Range", value=(min_date.date(), max_date.date()))

# Apply filters
f = matches.copy()

if season_sel:
    f = f[f["season"].isin(season_sel)]

# date filter
start_date, end_date = date_range
f = f[(f["date"] >= pd.to_datetime(start_date)) & (f["date"] <= pd.to_datetime(end_date))]

# team filter: keep matches where team appears in team1/team2
if team_sel:
    f = f[(f["team1"].isin(team_sel)) | (f["team2"].isin(team_sel))]

# If empty after filtering
if f.empty:
    st.warning("No matches found for the selected filters. Try changing seasons/teams/date range.")
    st.stop()

# -----------------------------
# Metric Cards (Dashboard elements #4)
# -----------------------------
total_matches = len(f)
no_result = int((f["winner"] == "No Result").sum())
unique_venues = f["venue"].nunique() if "venue" in f.columns else 0

# Most wins team
wins = f[f["winner"] != "No Result"]["winner"].value_counts()
top_team = wins.index[0] if len(wins) else "N/A"
top_team_wins = int(wins.iloc[0]) if len(wins) else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Matches", total_matches)
c2.metric("No Result", no_result)
c3.metric("Venues", unique_venues)
c4.metric("Top Winner", top_team, f"{top_team_wins} wins")

# -----------------------------
# Tabs requirement (2+ tabs)
# -----------------------------
tab1, tab2 = st.tabs(["📈 Season Overview", "🔎 Team & Result Analysis"])

# =========================================================
# TAB 1: Season Overview
# Must include interpretations in text
# Chart types: line, bar, heatmap (will do heatmap in tab2), scatter (tab2)
# =========================================================
with tab1:
    st.subheader("Season-level trends")

    # Line chart: matches per season
    season_counts = f.groupby("season")["match_id"].count().reset_index(name="matches")
    fig_line = px.line(season_counts, x="season", y="matches", markers=True, title="Matches per Season")
    st.plotly_chart(fig_line, use_container_width=True)

    # Bar chart: wins per team (top 10)
    win_counts = f[f["winner"] != "No Result"]["winner"].value_counts().reset_index()
    win_counts.columns = ["team", "wins"]
    win_counts = win_counts.head(10)

    fig_bar = px.bar(win_counts, x="team", y="wins", title="Top 10 Teams by Wins (Filtered Data)")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Written interpretation (required)
    st.markdown(
        """
**Interpretation (Season Overview):**
- The *matches per season* line chart highlights how IPL schedule volume changes across seasons (expansions, format shifts, or disruptions).
- The *top winners bar chart* shows which teams most consistently convert matches into wins under the selected filters.
- If one team dominates wins while match volume is stable, that suggests **sustained competitive advantage** rather than just “more matches played.”
"""
    )

# =========================================================
# TAB 2: Team & Result Analysis
# Chart types: heatmap + scatter + another bar/pie
# =========================================================
with tab2:
    st.subheader("Result patterns and team comparison")

    # Heatmap: team vs season win counts
    win_matrix = f[f["winner"] != "No Result"].groupby(["season", "winner"])["match_id"].count().reset_index()
    pivot = win_matrix.pivot(index="winner", columns="season", values="match_id").fillna(0)

    fig_heat = px.imshow(
        pivot,
        aspect="auto",
        title="Heatmap: Wins by Team (rows) vs Season (columns)",
        labels=dict(x="Season", y="Team", color="Wins")
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Scatter: win margin relationship (runs vs wickets)
    # Not all matches have both; this scatter helps identify how wins are achieved.
    s = f[(f["winner"] != "No Result")].copy()
    s["win_by_runs"] = s["win_by_runs"].fillna(0)
    s["win_by_wickets"] = s["win_by_wickets"].fillna(0)

    fig_scatter = px.scatter(
        s,
        x="win_by_runs",
        y="win_by_wickets",
        color="result_type",
        hover_data=["team1", "team2", "winner", "season"],
        title="Scatter: Win by Runs vs Win by Wickets (How Teams Win)"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Additional chart: Pie chart of result types
    result_counts = f["result_type"].value_counts().reset_index()
    result_counts.columns = ["result_type", "count"]
    fig_pie = px.pie(result_counts, names="result_type", values="count", title="Distribution of Result Types")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Written interpretation (required)
    st.markdown(
        """
**Interpretation (Team & Result Analysis):**
- The **wins heatmap** makes it easy to spot *dominant seasons* (strong blocks of high wins) and *down years* (sharp drop-offs).
- The **runs vs wickets scatter** shows *how matches are being won*: large run margins often indicate batting dominance, while wicket margins often reflect successful chases.
- If your filtered seasons show more wicket-based wins, that suggests **chasing advantage** or stronger second-innings execution in those years.
"""
    )

# -----------------------------
# Footer: Data note
# -----------------------------
st.caption(
    "Data source: public IPL match dataset (documented in README). "
    "This dashboard is designed to be refreshed as new seasons complete."
)
