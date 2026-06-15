"""

Full patient detail view — labs, treatments, visits with charts.


"""

import streamlit as st
import plotly.express as px
import pandas as pd

from api_client import (
    require_login, show_user_sidebar,
    get_patient, get_patient_summary,
    get_labs, get_treatments, get_visits
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
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("MRN", patient["mrn"])
col2.metric("Gender", patient["gender"])
col3.metric("Cancer Type", patient["cancer_type"])
col4.metric("Stage", patient["cancer_stage"])
col5.metric("Status", patient["status"])

st.caption(f"Diagnosed: {patient['diagnosis_date']} | DOB: {patient['dob']}")

st.divider()


# ╔══════════════════════════════════════════════════════════════╗
# ║  SUMMARY METRICS                                             ║
# ╚══════════════════════════════════════════════════════════════╝

summary = get_patient_summary(patient_id)

if summary:
    s = summary["summary"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Labs", s["total_labs"])
    m2.metric("Abnormal Labs", s["abnormal_labs"],
              delta=None if s["abnormal_labs"] == 0 else "⚠ needs review",
              delta_color="inverse")
    m3.metric("Treatments", s["total_treatments"])
    m4.metric("Visits", s["total_visits"])

st.divider()


# ╔══════════════════════════════════════════════════════════════╗
# ║  TABS                                                         ║
# ╚══════════════════════════════════════════════════════════════╝

tab_labs, tab_treatments, tab_visits = st.tabs(["Lab Results", "Treatments", "Visits"])


# -- LABS TAB ------------------------------------------------------
with tab_labs:
    labs = get_labs(patient_id)

    if not labs:
        st.info("No lab results recorded.")
    else:
        # Convert to DataFrame for easier charting
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

        # Add reference range as shaded band
        if test_df["reference_low"].notna().any():
            ref_low  = test_df["reference_low"].iloc[0]
            ref_high = test_df["reference_high"].iloc[0]
            fig.add_hrect(
                y0=ref_low, y1=ref_high,
                fillcolor="green", opacity=0.1,
                annotation_text="Normal range", annotation_position="top left"
            )

        st.plotly_chart(fig, use_container_width=True)

        # -- Abnormal results highlighted -------------------------
        st.subheader("All Lab Results")

        display_df = df[[
            "test_name", "value", "unit", "is_abnormal",
            "reference_low", "reference_high", "collected_at"
        ]].sort_values("collected_at", ascending=False)

        # Highlight abnormal rows
        def highlight_abnormal(row):
            color = "background-color: #ffcccc" if row["is_abnormal"] else ""
            return [color] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_abnormal, axis=1),
            use_container_width=True,
            hide_index=True
        )


# -- TREATMENTS TAB -------------------------------------------------
with tab_treatments:
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


# -- VISITS TAB -----------------------------------------------------
with tab_visits:
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