"""Private, consistency-first progress view."""

from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from app_state import initialize_account_state


initialize_account_state()
sessions = st.session_state.review_history

st.markdown('<div class="eyebrow">Private practice log</div>', unsafe_allow_html=True)
st.title("Your progress")
st.markdown('<p class="lede">Track consistency and compare your own practice over time. Progress is filtered to comparable exercise and camera setups.</p>', unsafe_allow_html=True)

if not sessions:
    with st.container(border=True):
        st.subheader("Your first session starts the record")
        st.write("Save a review from Lesson review and this page will begin tracking your practice rhythm, measurable trends, and personal bests.")
        st.caption("Use Lesson review in the navigation above to save your first session.")
    st.stop()

frame = pd.DataFrame(sessions)
frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="coerce")
frame["confidence"] = pd.to_numeric(frame["confidence"], errors="coerce").fillna(0)
today = datetime.now(timezone.utc).date()
recent_days = {row.date() for row in frame["date"].dropna()}
streak = 0
cursor = today
while cursor in recent_days:
    streak += 1
    cursor -= timedelta(days=1)

metric_cols = st.columns(4)
metric_cols[0].metric("Sessions logged", len(frame))
metric_cols[1].metric("Current streak", f"{streak} day{'s' if streak != 1 else ''}")
metric_cols[2].metric("This month", int((frame["date"].dt.month == today.month).sum()))
metric_cols[3].metric("High-confidence", int((frame["confidence"] >= .75).sum()))

st.subheader("Compare like with like")
frame["comparison"] = frame["exercise"].astype(str) + " · " + frame["camera_view"].astype(str) + " view"
comparison = st.selectbox("Exercise and camera view", sorted(frame["comparison"].unique()))
filtered = frame[frame["comparison"] == comparison].copy().sort_values("date")
high_confidence = filtered[filtered["confidence"] >= .75].copy()

if high_confidence.empty:
    st.warning("There are no high-confidence sessions in this comparison yet. Improve framing and lighting before using the trend.")
else:
    metric_names = sorted({name for item in high_confidence["metrics"] for name in (item or {}).keys()})
    if metric_names:
        metric_name = st.selectbox("Metric", metric_names)
        high_confidence[metric_name] = high_confidence["metrics"].apply(lambda item: (item or {}).get(metric_name))
        trend = high_confidence.dropna(subset=[metric_name]).set_index("date")[[metric_name]]
        st.line_chart(trend)
        st.caption("Only sessions with at least 75% usable pose confidence are included. Lower values are not automatically better; interpret each metric using its label and cue.")
        best = high_confidence.loc[high_confidence[metric_name].idxmin()]
        st.markdown(f'<div class="assessment-note"><strong>Personal best in this view</strong><br>{best[metric_name]:.2f} on {best["date"].date().isoformat()} · {best["feel"]}</div>', unsafe_allow_html=True)

st.subheader("Recent sessions")
for _, session in filtered.sort_values("date", ascending=False).head(8).iterrows():
    with st.container(border=True):
        session_date = session["date"].strftime("%b %d, %Y") if pd.notna(session["date"]) else "Undated session"
        st.markdown(f"**{session_date} · {session['exercise']} · {session['camera_view']} view**")
        st.caption(f"{session['feel']} · confidence {session['confidence']:.0%}")
        if session.get("note"):
            st.write(session["note"])
