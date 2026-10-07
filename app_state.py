"""Session-scoped account data for the local/demo version of the platform."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import streamlit as st


DEFAULT_PROFILE = {
    "name": "",
    "level": "Foundational",
    "goals": [],
    "practice_days": 4,
    "minutes_per_session": "20 minutes",
    "equipment": "Barre or sturdy chair",
    "retain_videos": False,
    "share_for_product_improvement": False,
}


def initialize_account_state() -> None:
    """Create account-shaped state without claiming it is persistent auth."""
    st.session_state.setdefault("account_profile", DEFAULT_PROFILE.copy())
    st.session_state.setdefault("saved_training_plans", [])
    st.session_state.setdefault("review_history", [])
    st.session_state.setdefault("bookmarked_resources", [])


def account_snapshot() -> dict[str, object]:
    initialize_account_state()
    return {
        "profile": st.session_state.account_profile,
        "saved_training_plans": st.session_state.saved_training_plans,
        "review_history": st.session_state.review_history,
        "bookmarked_resources": st.session_state.bookmarked_resources,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


def account_export_json() -> str:
    return json.dumps(account_snapshot(), indent=2, ensure_ascii=False)


def delete_local_account_data() -> None:
    for key in ("account_profile", "saved_training_plans", "review_history", "bookmarked_resources"):
        st.session_state.pop(key, None)


def save_review_session(session: dict[str, object]) -> None:
    """Store one private practice review in the current account session."""
    initialize_account_state()
    st.session_state.review_history.append(session)
