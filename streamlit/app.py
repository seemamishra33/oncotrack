"""

Entry point for the OncoTrack Streamlit dashboard.
For now — just verifies the API client works.
"""

import streamlit as st
from api_client import api_is_alive, get_patients

st.set_page_config(
    page_title = "OncoTrack",
    page_icon  = "🏥",
    layout     = "wide"
)

st.title("OncoTrack Dashboard")

# -- Check API connection --------------------------------------
if api_is_alive():
    st.success("Connected to OncoTrack API")
else:
    st.error("Cannot connect to API. Make sure FastAPI is running on port 8000.")
    st.stop()   # stops the rest of the page from running

# -- Quick test: fetch and display patients ---------------------
st.subheader("Patients (test)")
patients = get_patients(limit=5)

if patients:
    st.write(f"Found {len(patients)} patients")
    st.dataframe(patients)
else:
    st.warning("No patients found.")