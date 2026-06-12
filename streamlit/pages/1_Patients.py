"""
1_Patients.py
=============
Patient list page — search, filter, and browse all patients.

CONCEPTS DEMONSTRATED:
    - Multi-page Streamlit apps
    - st.selectbox, st.text_input for filters
    - st.dataframe for tabular display
    - Linking to another page with patient id
"""

import streamlit as st
from api_client import require_login, show_user_sidebar, get_patients

st.set_page_config(page_title="Patients - OncoTrack", page_icon="🏥", layout="wide")

# -- Auth check (every page needs this) --------------------------
require_login()
show_user_sidebar()

st.title("Patients")

# ╔══════════════════════════════════════════════════════════════╗
# ║  FILTERS                                                      ║
# ╚══════════════════════════════════════════════════════════════╝

col1, col2, col3 = st.columns(3)

with col1:
    status_filter = st.selectbox(
        "Status",
        options=["All", "Active", "Remission", "Deceased", "Lost to Follow-up"]
    )

with col2:
    stage_filter = st.selectbox(
        "Cancer Stage",
        options=["All", "I", "II", "III", "IV", "Unknown"]
    )

with col3:
    search_term = st.text_input("Search by name or MRN")


# ╔══════════════════════════════════════════════════════════════╗
# ║  FETCH DATA                                                   ║
# ╚══════════════════════════════════════════════════════════════╝

# Convert "All" to None so api_client doesn't filter on it
status_param = None if status_filter == "All" else status_filter
stage_param  = None if stage_filter  == "All" else stage_filter

patients = get_patients(limit=200, status=status_param, stage=stage_param)

# Client-side search — filter the already-fetched list by name/MRN
if search_term:
    search_lower = search_term.lower()
    patients = [
        p for p in patients
        if search_lower in p["first_name"].lower()
        or search_lower in p["last_name"].lower()
        or search_lower in p["mrn"].lower()
    ]


# ╔══════════════════════════════════════════════════════════════╗
# ║  DISPLAY                                                      ║
# ╚══════════════════════════════════════════════════════════════╝

st.write(f"**{len(patients)}** patients found")

if not patients:
    st.info("No patients match your filters.")
else:
    # Build a simplified table for display
    table_data = [
        {
            "ID"         : p["id"],
            "MRN"        : p["mrn"],
            "Name"       : f"{p['first_name']} {p['last_name']}",
            "Gender"     : p["gender"],
            "Cancer Type": p["cancer_type"],
            "Stage"      : p["cancer_stage"],
            "Status"     : p["status"],
            "Diagnosed"  : p["diagnosis_date"],
        }
        for p in patients
    ]
    st.dataframe(table_data, use_container_width=True, hide_index=True)

    # -- Select a patient to view details ------------------------
    st.divider()
    st.subheader("View Patient Details")

    patient_options = {
        f"{p['mrn']} - {p['first_name']} {p['last_name']}": p["id"]
        for p in patients
    }

    selected = st.selectbox("Select a patient", options=list(patient_options.keys()))

    if st.button("View Details"):
        st.session_state.selected_patient_id = patient_options[selected]
        st.switch_page("pages/3_Patient_Detail.py")