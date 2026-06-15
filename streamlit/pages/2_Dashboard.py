"""

High-level overview dashboard — aggregate metrics and charts
across all patients.


"""

import streamlit as st
import pandas as pd
import plotly.express as px

from api_client import require_login, show_user_sidebar, get_patients

st.set_page_config(page_title="Dashboard - OncoTrack", page_icon="🏥", layout="wide")

require_login()
show_user_sidebar()

st.title("Dashboard Overview")


# ╔══════════════════════════════════════════════════════════════╗
# ║  FETCH ALL PATIENTS                                          ║
# ╚══════════════════════════════════════════════════════════════╝

patients = get_patients(limit=500)

if not patients:
    st.warning("No patient data available.")
    st.stop()

df = pd.DataFrame(patients)


# ╔══════════════════════════════════════════════════════════════╗
# ║  KEY METRICS ROW                                             ║
# ╚══════════════════════════════════════════════════════════════╝

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Patients", len(df))

active_count = len(df[df["status"] == "Active"])
col2.metric("Active Patients", active_count)

remission_count = len(df[df["status"] == "Remission"])
col3.metric("In Remission", remission_count)

stage_iv_count = len(df[df["cancer_stage"] == "IV"])
col4.metric("Stage IV Cases", stage_iv_count)

st.divider()


# ╔══════════════════════════════════════════════════════════════╗
# ║  CHARTS ROW 1 — Status and Stage                             ║
# ╚══════════════════════════════════════════════════════════════╝

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Patients by Status")

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    fig = px.pie(
        status_counts,
        names="status",
        values="count",
        hole=0.4,   # makes it a donut chart
        color="status",
        color_discrete_map={
            "Active"            : "#1f77b4",
            "Remission"         : "#2ca02c",
            "Deceased"          : "#7f7f7f",
            "Lost to Follow-up" : "#d62728",
        }
    )
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("Patients by Cancer Stage")

    stage_counts = df["cancer_stage"].value_counts().reset_index()
    stage_counts.columns = ["stage", "count"]

    # Order stages logically, not alphabetically
    stage_order = ["I", "II", "III", "IV", "Unknown"]
    stage_counts["stage"] = pd.Categorical(
        stage_counts["stage"], categories=stage_order, ordered=True
    )
    stage_counts = stage_counts.sort_values("stage")

    fig = px.bar(
        stage_counts,
        x="stage",
        y="count",
        color="stage",
        color_discrete_sequence=px.colors.sequential.Reds
    )
    st.plotly_chart(fig, use_container_width=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  CHARTS ROW 2 — Cancer Type and Gender                       ║
# ╚══════════════════════════════════════════════════════════════╝

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("Patients by Cancer Type")

    type_counts = df["cancer_type"].value_counts().reset_index()
    type_counts.columns = ["cancer_type", "count"]

    fig = px.bar(
        type_counts,
        x="count",
        y="cancer_type",
        orientation="h",   # horizontal bars — better for long labels
        color="count",
        color_continuous_scale="Blues"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

with chart_col4:
    st.subheader("Patients by Gender")

    gender_counts = df["gender"].value_counts().reset_index()
    gender_counts.columns = ["gender", "count"]

    fig = px.pie(
        gender_counts,
        names="gender",
        values="count",
        hole=0.4
    )
    st.plotly_chart(fig, use_container_width=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  AGE DISTRIBUTION                                            ║
# ╚══════════════════════════════════════════════════════════════╝

st.divider()
st.subheader("Age Distribution")

# Calculate age from dob
df["dob"] = pd.to_datetime(df["dob"])
today = pd.Timestamp.now()
df["age"] = ((today - df["dob"]).dt.days / 365.25).astype(int)

fig = px.histogram(
    df,
    x="age",
    nbins=20,
    title="Patient Age Distribution",
    color_discrete_sequence=["#636EFA"]
)
fig.update_layout(bargap=0.1)
st.plotly_chart(fig, use_container_width=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  RECENT PATIENTS TABLE                                       ║
# ╚══════════════════════════════════════════════════════════════╝

st.divider()
st.subheader("Recently Diagnosed Patients")

recent = df.sort_values("diagnosis_date", ascending=False).head(5)
recent_display = recent[[
    "mrn", "first_name", "last_name", "cancer_type",
    "cancer_stage", "status", "diagnosis_date"
]]
st.dataframe(recent_display, use_container_width=True, hide_index=True)