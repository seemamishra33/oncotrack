"""
app.py
======
Entry point for the OncoTrack Streamlit dashboard.

Shows a login page first. Once logged in, shows a home page
with quick navigation to the main sections.
"""

import streamlit as st
from api_client import api_is_alive, login, get_patients

st.set_page_config(
    page_title = "OncoTrack",
    page_icon  = "🏥",
    layout     = "wide"
)


# -- Initialize session state ------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None


# -- Check API connection ------------------------------------------
if not api_is_alive():
    st.error("Cannot connect to API. Make sure FastAPI is running on port 8000.")
    st.stop()


# ╔══════════════════════════════════════════════════════════════╗
# ║  LOGIN PAGE                                                  ║
# ╚══════════════════════════════════════════════════════════════╝

def show_login_page():
    st.title("🏥 OncoTrack")
    st.subheader("Oncology Patient Data Management")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.markdown("### Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                result = login(username, password)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.user = result
                    st.rerun()
                else:
                    st.error("Incorrect username or password")

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
# ║  HOME PAGE (after login)                                     ║
# ╚══════════════════════════════════════════════════════════════╝

def show_home_page():
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"### {user['username']}")
        st.caption(f"Role: {user['role']}")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    st.title("OncoTrack")
    st.subheader(f"Welcome back, {user['username']}")

    # -- Quick stats -------------------------------------------------
    patients = get_patients(limit=500)
    active = len([p for p in patients if p["status"] == "Active"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Patients", len(patients))
    col2.metric("Active Cases", active)
    col3.metric("Your Role", user["role"].title())

    st.divider()

    # -- Navigation cards ----------------------------------------------
    st.subheader("Quick Navigation")

    nav1, nav2, nav3 = st.columns(3)

    with nav1:
        with st.container(border=True):
            st.markdown("#### 👥 Patients")
            st.write("Browse, search, and manage patient records.")
            if st.button("Go to Patients", use_container_width=True):
                st.switch_page("pages/1_Patients.py")

    with nav2:
        with st.container(border=True):
            st.markdown("#### 📊 Dashboard")
            st.write("View aggregate metrics and trends across all patients.")
            if st.button("Go to Dashboard", use_container_width=True):
                st.switch_page("pages/2_Dashboard.py")

    with nav3:
        with st.container(border=True):
            st.markdown("#### ➕ Add Patient")
            st.write("Register a new patient record.")
            if st.button("Go to Add Patient", use_container_width=True):
                st.switch_page("pages/1_Patients.py")

    st.divider()
    st.caption("OncoTrack —  All patient data is synthetic.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  MAIN — route based on login state                           ║
# ╚══════════════════════════════════════════════════════════════╝

if st.session_state.logged_in:
    show_home_page()
else:
    show_login_page()