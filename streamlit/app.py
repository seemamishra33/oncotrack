"""


Shows a login page first. Once logged in, shows the dashboard.

CONCEPTS DEMONSTRATED:
    - st.session_state : persists data across reruns
    - st.form           : groups inputs, submits together
    - Conditional rendering based on auth state
"""

import streamlit as st
from api_client import api_is_alive, login, get_patients

st.set_page_config(
    page_title = "OncoTrack",
    page_icon  = "🏥",
    layout     = "wide"
)


# -- Initialize session state (runs once per session) -----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None


# -- Check API connection ----------------------------------------
if not api_is_alive():
    st.error("Cannot connect to API. Make sure FastAPI is running on port 8000.")
    st.stop()


# ╔══════════════════════════════════════════════════════════════╗
# ║  LOGIN PAGE                                                  ║
# ╚══════════════════════════════════════════════════════════════╝

def show_login_page():
    st.title("OncoTrack")
    st.subheader("Oncology Patient Data Management")

    # Center the login form using columns
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.markdown("### Login")

        # st.form groups inputs — nothing submits until the button is clicked
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                result = login(username, password)
                if result:
                    # Save to session state — persists across reruns
                    st.session_state.logged_in = True
                    st.session_state.user = result
                    st.rerun()   # force immediate rerun to show dashboard
                else:
                    st.error("Incorrect username or password")

        # Demo credentials helper
        with st.expander("Demo Credentials"):
            st.markdown("""
            | Role        | Username    | Password  |
            |-------------|-------------|-----------|
            | Admin       | admin       | admin123  |
            | Oncologist  | dr_smith    | demo123   |
            | Nurse       | nurse_jane  | demo123   |
            | Viewer      | viewer1     | demo123   |
            """)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DASHBOARD (after login)                                     ║
# ╚══════════════════════════════════════════════════════════════╝

def show_dashboard():
    user = st.session_state.user

    # Sidebar — shows user info and logout
    with st.sidebar:
        st.markdown(f"### Welcome, {user['username']}")
        st.caption(f"Role: {user['role']}")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            #st.rerun()

    st.title("OncoTrack Dashboard")
    st.success(f"Logged in as **{user['username']}** ({user['role']})")

    # Quick test — fetch and display patients
    st.subheader("Patients")
    patients = get_patients(limit=10)

    if patients:
        st.write(f"Showing {len(patients)} of many patients")
        st.dataframe(patients, use_container_width=True)
    else:
        st.warning("No patients found.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  MAIN — route based on login state                           ║
# ╚══════════════════════════════════════════════════════════════╝

if st.session_state.logged_in:
    show_dashboard()
else:
    show_login_page()