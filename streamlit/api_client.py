"""

Central place for all calls to the FastAPI backend.

Every Streamlit page imports functions from here instead of
calling `requests` directly. If the API URL or response shape
ever changes, you only update it in ONE place.
"""

import requests
import logging

logger = logging.getLogger("oncotrack.streamlit")

# -- Base URL of your FastAPI backend --------------------------
BASE_URL = "http://localhost:8000"


# ╔══════════════════════════════════════════════════════════════╗
# ║  AUTH                                                        ║
# ╚══════════════════════════════════════════════════════════════╝

def login(username: str, password: str) -> dict | None:
    """
    Calls POST /auth/login.
    Returns user info dict on success, None on failure.
    """
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Login failed: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to API — is FastAPI running?")
        return None


# ╔══════════════════════════════════════════════════════════════╗
# ║  PATIENTS                                                     ║
# ╚══════════════════════════════════════════════════════════════╝

def get_patients(skip: int = 0, limit: int = 100,
                  status: str = None, stage: str = None) -> list:
    """
    Calls GET /api/patients with optional filters.
    Returns a list of patient dicts (empty list on error).
    """
    params = {"skip": skip, "limit": limit}
    if status:
        params["status"] = status
    if stage:
        params["stage"] = stage

    try:
        response = requests.get(f"{BASE_URL}/api/patients", params=params)
        response.raise_for_status()   # raises an error for 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"get_patients failed: {e}")
        return []


def get_patient(patient_id: int) -> dict | None:
    """Calls GET /api/patients/{id}. Returns None if not found."""
    try:
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"get_patient failed: {e}")
        return None


def get_patient_summary(patient_id: int) -> dict | None:
    """Calls GET /api/patients/{id}/summary."""
    try:
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/summary")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"get_patient_summary failed: {e}")
        return None


def create_patient(data: dict) -> dict | None:
    """Calls POST /api/patients. Returns created patient or None."""
    try:
        response = requests.post(f"{BASE_URL}/api/patients", json=data)
        if response.status_code == 201:
            return response.json()
        logger.warning(f"create_patient failed: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"create_patient failed: {e}")
        return None


def update_patient(patient_id: int, data: dict) -> dict | None:
    """Calls PATCH /api/patients/{id}. Send only fields to change."""
    try:
        response = requests.patch(f"{BASE_URL}/api/patients/{patient_id}", json=data)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"update_patient failed: {e}")
        return None


# ╔══════════════════════════════════════════════════════════════╗
# ║  LABS                                                         ║
# ╚══════════════════════════════════════════════════════════════╝

def get_labs(patient_id: int, abnormal_only: bool = False) -> list:
    """Calls GET /api/labs/patient/{id} or /abnormal variant."""
    url = f"{BASE_URL}/api/labs/patient/{patient_id}"
    if abnormal_only:
        url += "/abnormal"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"get_labs failed: {e}")
        return []


def create_lab(data: dict) -> dict | None:
    """Calls POST /api/labs."""
    try:
        response = requests.post(f"{BASE_URL}/api/labs", json=data)
        if response.status_code == 201:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"create_lab failed: {e}")
        return None


# ╔══════════════════════════════════════════════════════════════╗
# ║  TREATMENTS                                                   ║
# ╚══════════════════════════════════════════════════════════════╝

def get_treatments(patient_id: int, treatment_type: str = None) -> list:
    """Calls GET /api/treatments/patient/{id}."""
    params = {}
    if treatment_type:
        params["treatment_type"] = treatment_type
    try:
        response = requests.get(
            f"{BASE_URL}/api/treatments/patient/{patient_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"get_treatments failed: {e}")
        return []


def create_treatment(data: dict) -> dict | None:
    """Calls POST /api/treatments."""
    try:
        response = requests.post(f"{BASE_URL}/api/treatments", json=data)
        if response.status_code == 201:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"create_treatment failed: {e}")
        return None


# ╔══════════════════════════════════════════════════════════════╗
# ║  VISITS                                                       ║
# ╚══════════════════════════════════════════════════════════════╝

def get_visits(patient_id: int, visit_type: str = None) -> list:
    """Calls GET /api/visits/patient/{id}."""
    params = {}
    if visit_type:
        params["visit_type"] = visit_type
    try:
        response = requests.get(
            f"{BASE_URL}/api/visits/patient/{patient_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"get_visits failed: {e}")
        return []


def create_visit(data: dict) -> dict | None:
    """Calls POST /api/visits."""
    try:
        response = requests.post(f"{BASE_URL}/api/visits", json=data)
        if response.status_code == 201:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"create_visit failed: {e}")
        return None


# ╔══════════════════════════════════════════════════════════════╗
# ║  HEALTH CHECK                                                 ║
# ╚══════════════════════════════════════════════════════════════╝

def api_is_alive() -> bool:
    """Checks if FastAPI is running. Used to show a friendly error."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


import streamlit as st

def require_login():
    """
    Call this at the top of every page.
    Redirects to login if user is not authenticated.
    """
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first")
        st.page_link("app.py", label="Go to Login", icon="🔒")
        st.stop()


def show_user_sidebar():
    """Shows logged-in user info and logout button in sidebar."""
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"### {user['username']}")
        st.caption(f"Role: {user['role']}")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()