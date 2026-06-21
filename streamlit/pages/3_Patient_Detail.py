"""
3_Patient_Detail.py
====================
Full patient detail view — labs, treatments, visits with charts,
plus forms to add new records and update patient status.


    - Passing data between pages via session_state
    - st.tabs for organizing content
    - st.metric for key numbers
    - Plotly charts for lab trends
    - st.form for adding new records (CRUD - Create)
    - PATCH for updating patient status (CRUD - Update)
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

from api_client import (
    require_login, show_user_sidebar,
    get_patient, get_patient_summary,
    get_labs, get_treatments, get_visits,
    create_lab, create_treatment, create_visit,
    update_patient
)

st.set_page_config(page_title="Patient Detail - OncoTrack", page_icon="🏥", layout="wide")

require_login()
show_user_sidebar()


# ╔══════════════════════════════════════════════════════════════╗
# ║  GET PATIENT ID FROM SESSION STATE                           ║
# ╚══════════════════════════════════════════════════════════════╝

patient_id = st.session_state.get("selected_patient_id")

if not patient_id:
    st.warning("No patient selected.")
    st.page_link("pages/1_Patients.py", label="Go to Patient List", icon="👥")
    st.stop()


# ╔══════════════════════════════════════════════════════════════╗
# ║  FETCH PATIENT DATA                                          ║
# ╚══════════════════════════════════════════════════════════════╝

patient = get_patient(patient_id)

if not patient:
    st.error(f"Patient {patient_id} not found.")
    st.stop()


# ╔══════════════════════════════════════════════════════════════╗
# ║  HEADER                                                       ║
# ╚══════════════════════════════════════════════════════════════╝

st.title(f"{patient['first_name']} {patient['last_name']}")

# Back button
if st.button("← Back to Patient List"):
    st.switch_page("pages/1_Patients.py")

# -- Key info row -------------------------------------------------
# -- Key info row -------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.caption("MRN")
    st.markdown(f"**{patient['mrn']}**")

with col2:
    st.caption("Gender")
    st.markdown(f"**{patient['gender']}**")

with col3:
    st.caption("Cancer Type")
    st.markdown(f"**{patient['cancer_type']}**")

with col4:
    st.caption("Stage")
    st.markdown(f"**{patient['cancer_stage']}**")

with col5:
    st.caption("Status")
    st.markdown(f"**{patient['status']}**")

st.caption(f"Diagnosed: {patient['diagnosis_date']} | DOB: {patient['dob']}")

# -- Quick status update -----------------------------------------
with st.expander("Update Patient Status"):
    status_options = ["Active", "Remission", "Deceased", "Lost to Follow-up"]
    new_status = st.selectbox(
        "New Status",
        status_options,
        index=status_options.index(patient["status"])
    )
    if st.button("Update Status"):
        result = update_patient(patient_id, {"status": new_status})
        if result:
            st.success(f"Status updated to {new_status}")
            st.rerun()
        else:
            st.error("Update failed")

st.divider()


# ╔══════════════════════════════════════════════════════════════╗
# ║  SUMMARY METRICS                                             ║
# ╚══════════════════════════════════════════════════════════════╝

summary = get_patient_summary(patient_id)

if summary:
    s = summary["summary"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Labs", s["total_labs"])
    m2.metric(
        "Abnormal Labs", s["abnormal_labs"],
        delta=None if s["abnormal_labs"] == 0 else "needs review",
        delta_color="inverse"
    )
    m3.metric("Treatments", s["total_treatments"])
    m4.metric("Visits", s["total_visits"])

st.divider()


# ╔══════════════════════════════════════════════════════════════╗
# ║  TABS                                                         ║
# ╚══════════════════════════════════════════════════════════════╝

tab_labs, tab_treatments, tab_visits = st.tabs(["Lab Results", "Treatments", "Visits"])


# ╔══════════════════════════════════════════════════════════════╗
# ║  LABS TAB                                                     ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_labs:

    # -- Add new lab result ----------------------------------------
    with st.expander("➕ Add Lab Result"):
        with st.form("add_lab_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                test_name = st.text_input("Test Name (e.g. Hemoglobin)")
                test_category = st.selectbox(
                    "Category",
                    ["CBC", "Tumor Marker", "Metabolic Panel", "Coagulation", "Urinalysis", "Other"]
                )
            with c2:
                value = st.number_input("Value", step=0.01, format="%.3f")
                unit = st.text_input("Unit (e.g. g/dL)")
            with c3:
                ref_low = st.number_input("Reference Low", step=0.01, format="%.3f")
                ref_high = st.number_input("Reference High", step=0.01, format="%.3f")

            collected_date = st.date_input("Collection Date")
            collected_time = st.time_input("Collection Time")

            submitted = st.form_submit_button("Add Lab Result")

            if submitted:
                if not test_name or not unit:
                    st.error("Test Name and Unit are required.")
                else:
                    collected_at = datetime.combine(collected_date, collected_time)

                    new_lab = {
                        "patient_id": patient_id,
                        "test_name": test_name,
                        "test_category": test_category,
                        "value": value,
                        "unit": unit,
                        "reference_low": ref_low,
                        "reference_high": ref_high,
                        "collected_at": collected_at.isoformat(),
                    }

                    result = create_lab(new_lab)
                    if result:
                        abnormal = " (ABNORMAL)" if result["is_abnormal"] else ""
                        st.success(f"Added {test_name}: {value} {unit}{abnormal}")
                        st.rerun()
                    else:
                        st.error("Failed to add lab result")

    # -- Display existing labs --------------------------------------
    labs = get_labs(patient_id)

    if not labs:
        st.info("No lab results recorded.")
    else:
        df = pd.DataFrame(labs)

        # -- Filter by test name --------------------------------
        test_names = sorted(df["test_name"].unique())
        selected_test = st.selectbox("Select test to chart", options=test_names)

        test_df = df[df["test_name"] == selected_test].sort_values("collected_at")

        # -- Chart: value over time with reference range ---------
        fig = px.line(
            test_df,
            x="collected_at",
            y="value",
            title=f"{selected_test} over time",
            markers=True
        )

        if test_df["reference_low"].notna().any():
            ref_low_val = test_df["reference_low"].iloc[0]
            ref_high_val = test_df["reference_high"].iloc[0]
            fig.add_hrect(
                y0=ref_low_val, y1=ref_high_val,
                fillcolor="green", opacity=0.1,
                annotation_text="Normal range", annotation_position="top left"
            )

        st.plotly_chart(fig, use_container_width=True)

        # -- All lab results table --------------------------------
        st.subheader("All Lab Results")

        display_df = df[[
            "test_name", "value", "unit", "is_abnormal",
            "reference_low", "reference_high", "collected_at"
        ]].sort_values("collected_at", ascending=False)

        def highlight_abnormal(row):
            color = "background-color: #ffcccc" if row["is_abnormal"] else ""
            return [color] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_abnormal, axis=1),
            use_container_width=True,
            hide_index=True
        )


# ╔══════════════════════════════════════════════════════════════╗
# ║  TREATMENTS TAB                                               ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_treatments:

    # -- Add new treatment -------------------------------------------
    with st.expander("➕ Add Treatment"):
        with st.form("add_treatment_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                treatment_type = st.selectbox(
                    "Treatment Type",
                    ["Chemotherapy", "Radiation", "Surgery", "Immunotherapy",
                     "Targeted Therapy", "Hormone Therapy", "Palliative", "Other"]
                )
                protocol_name = st.text_input("Protocol Name (optional)")
                start_date = st.date_input("Start Date")

            with c2:
                dose_mg = st.number_input("Dose (mg)", min_value=0.0, step=1.0)
                frequency = st.text_input("Frequency (e.g. Every 3 weeks)")
                response = st.selectbox(
                    "Response",
                    ["Unknown", "Complete Response", "Partial Response",
                     "Stable Disease", "Progressive Disease"]
                )

            submitted = st.form_submit_button("Add Treatment")

            if submitted:
                if not treatment_type:
                    st.error("Treatment Type is required.")
                else:
                    new_treatment = {
                        "patient_id": patient_id,
                        "treatment_type": treatment_type,
                        "protocol_name": protocol_name or None,
                        "start_date": str(start_date),
                        "dose_mg": dose_mg if dose_mg > 0 else None,
                        "frequency": frequency or None,
                        "response": response,
                    }

                    result = create_treatment(new_treatment)
                    if result:
                        st.success(f"Added {treatment_type} treatment")
                        st.rerun()
                    else:
                        st.error("Failed to add treatment")

    # -- Display existing treatments ----------------------------------
    treatments = get_treatments(patient_id)

    if not treatments:
        st.info("No treatments recorded.")
    else:
        df = pd.DataFrame(treatments)

        display_df = df[[
            "treatment_type", "protocol_name", "drug_regimen",
            "start_date", "end_date", "response", "toxicity_grade"
        ]].sort_values("start_date", ascending=False)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # -- Treatment timeline chart -----------------------------
        st.subheader("Treatment Timeline")

        timeline_df = df.copy()
        timeline_df["end_date"] = timeline_df["end_date"].fillna(timeline_df["start_date"])

        fig = px.timeline(
            timeline_df,
            x_start="start_date",
            x_end="end_date",
            y="treatment_type",
            color="response",
            title="Treatment History"
        )
        st.plotly_chart(fig, use_container_width=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  VISITS TAB                                                   ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_visits:

    # -- Add new visit --------------------------------------------------
    with st.expander("➕ Add Visit"):
        with st.form("add_visit_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                visit_date = st.date_input("Visit Date")
                visit_type = st.selectbox(
                    "Visit Type",
                    ["Initial Consult", "Follow-up", "Chemo Session",
                     "Radiation Session", "Urgent", "Telehealth"]
                )
                weight_kg = st.number_input("Weight (kg)", min_value=0.0, step=0.1)

            with c2:
                height_cm = st.number_input("Height (cm)", min_value=0.0, step=0.1)
                ecog_score = st.selectbox("ECOG Score", [0, 1, 2, 3, 4, 5])
                assessment = st.text_area("Assessment", height=80)

            submitted = st.form_submit_button("Add Visit")

            if submitted:
                new_visit = {
                    "patient_id": patient_id,
                    "visit_date": str(visit_date) + "T00:00:00",
                    "visit_type": visit_type,
                    "weight_kg": weight_kg if weight_kg > 0 else None,
                    "height_cm": height_cm if height_cm > 0 else None,
                    "ecog_score": ecog_score,
                    "assessment": assessment or None,
                }

                result = create_visit(new_visit)
                if result:
                    st.success(f"Added {visit_type} visit")
                    st.rerun()
                else:
                    st.error("Failed to add visit")

    # -- Display existing visits ---------------------------------------
    visits = get_visits(patient_id)

    if not visits:
        st.info("No visits recorded.")
    else:
        df = pd.DataFrame(visits)

        display_df = df[[
            "visit_date", "visit_type", "weight_kg",
            "height_cm", "ecog_score", "assessment"
        ]].sort_values("visit_date", ascending=False)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # -- Weight trend chart -----------------------------------
        if df["weight_kg"].notna().any():
            st.subheader("Weight Trend")
            weight_df = df.sort_values("visit_date")

            fig = px.line(
                weight_df,
                x="visit_date",
                y="weight_kg",
                title="Weight over time",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
