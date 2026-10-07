import streamlit as st

from app_state import account_export_json, delete_local_account_data, initialize_account_state


initialize_account_state()
profile = st.session_state.account_profile

st.title("My account")
st.write("Manage your ballet goals, training preferences, saved plans, and privacy choices.")

is_logged_in = bool(getattr(st.user, "is_logged_in", False))
if is_logged_in:
    identity = getattr(st.user, "email", None) or getattr(st.user, "name", None) or "Signed-in user"
    st.success(f"Signed in as {identity}")
else:
    st.info(
        "Local demo mode is active. Your settings are available during this browser session only. "
        "Secure cross-session accounts will be enabled after an OIDC provider and database are connected.",
    )

with st.form("profile_form"):
    st.subheader("Profile")
    profile["name"] = st.text_input("Name", value=profile["name"])
    profile["level"] = st.selectbox(
        "Current ballet level",
        ["Foundational", "Developing", "Intermediate", "Advanced", "Professional"],
        index=["Foundational", "Developing", "Intermediate", "Advanced", "Professional"].index(profile["level"]),
    )
    profile["goals"] = st.multiselect(
        "Current technique goals",
        ["Pliés", "Tendus", "Pirouettes", "Arabesque", "Turnout", "Balance", "Foot and ankle strength", "Core strength"],
        default=profile["goals"],
    )
    profile["practice_days"] = st.slider("Practice days per week", 1, 7, profile["practice_days"])
    profile["minutes_per_session"] = st.selectbox(
        "Typical time per session",
        ["10 minutes", "20 minutes", "30 minutes", "45 minutes", "60 minutes"],
        index=["10 minutes", "20 minutes", "30 minutes", "45 minutes", "60 minutes"].index(profile["minutes_per_session"]),
    )
    profile["equipment"] = st.text_input("Available equipment", value=profile["equipment"])
    if st.form_submit_button("Save profile", type="primary"):
        st.session_state.account_profile = profile
        st.success("Profile saved for this session.")

st.subheader("Privacy and data")
profile["retain_videos"] = st.checkbox(
    "Keep uploaded videos for future progress comparisons",
    value=profile["retain_videos"],
    help="This preference will control persistent video storage once an account database is connected.",
)
profile["share_for_product_improvement"] = st.checkbox(
    "Allow anonymized results to support product improvement",
    value=profile["share_for_product_improvement"],
)
st.session_state.account_profile = profile

with st.container(border=True):
    st.subheader("Your saved data")
    st.write(f"Saved training plans: {len(st.session_state.saved_training_plans)}")
    st.write(f"Review history items: {len(st.session_state.review_history)}")
    st.write(f"Bookmarked resources: {len(st.session_state.bookmarked_resources)}")
    st.download_button(
        "Export my data",
        data=account_export_json(),
        file_name="ballet_technique_platform_account.json",
        mime="application/json",
    )

with st.expander("Delete local account data", expanded=False):
    st.warning("This removes the profile, saved plans, review history, and bookmarks from this session.")
    if st.button("Delete local data", type="secondary"):
        delete_local_account_data()
        st.success("Local account data deleted.")
        st.rerun()
