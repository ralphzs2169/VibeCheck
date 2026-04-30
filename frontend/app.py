import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "http://127.0.0.1:8000/api/businesses"

st.set_page_config(
    page_title="Vibe Analytics Dashboard",
    layout="wide"
)

st.title("📊 Business Sentiment Analytics Dashboard")

business_id = st.number_input(
    "Business ID",
    min_value=1,
    value=1
)


@st.cache_data(ttl=60)
def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# -----------------------------
# Fetch dashboard data (ONE request only)
# -----------------------------
dashboard = fetch_json(
    f"{API_URL}/{business_id}/dashboard"
)

vibe = dashboard["vibe"]
distribution = dashboard["distribution"]
trend = dashboard["trend"]
volatility = dashboard["volatility"]
peak_drop = dashboard["peak_drop"]
temporal = dashboard["temporal"]


# -----------------------------
# Current Vibe Summary
# -----------------------------
st.subheader("🌟 Current Vibe Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Vibe Label", vibe["vibe_label"])

with col2:
    st.metric("Vibe Score", vibe["vibe_score"])

with col3:
    st.metric("Reviews", vibe["review_count"])

st.write(vibe["summary_text"])

st.write("**Keywords:**", ", ".join(vibe["keywords"]))


# -----------------------------
# Temporal Trend
# -----------------------------
st.subheader("📈 Sentiment Trend Over Time")

if temporal:
    df_temporal = pd.DataFrame(temporal)
    df_temporal = df_temporal.set_index("period")

    st.line_chart(df_temporal["avg_score"])
else:
    st.info("No temporal data available.")


# -----------------------------
# Distribution Pie Chart
# -----------------------------
st.subheader("🥧 Sentiment Distribution")

dist = distribution["distribution"]

df_dist = pd.DataFrame.from_dict(
    dist,
    orient="index",
    columns=["count"]
)

fig, ax = plt.subplots()
df_dist.plot.pie(
    y="count",
    autopct="%1.1f%%",
    legend=False,
    ylabel="",
    ax=ax
)

st.pyplot(fig)


# -----------------------------
# Analytics Metrics
# -----------------------------
st.subheader("📌 Analytics Metrics")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Trend",
        value=trend["trend"],
        delta=round(trend["slope"], 4)
    )

with col2:
    st.metric(
        label="Volatility",
        value=volatility["stability"],
        delta=round(volatility["volatility"], 4)
    )


# -----------------------------
# Peak / Drop Alerts
# -----------------------------
st.subheader("🚨 Major Sentiment Changes")

peak = peak_drop["peak"]
drop = peak_drop["drop"]

if peak:
    st.success(
        f"Peak increase: {peak['date']} ({peak['change']:.4f})"
    )

if drop:
    st.error(
        f"Largest drop: {drop['date']} ({drop['change']:.4f})"
    )


# -----------------------------
# Extra Signals
# -----------------------------
st.subheader("🔍 Additional Signals")

st.write(
    f"**Polarizing:** {vibe['score_distribution']['is_polarizing']}"
)

st.write(
    f"Positive: {vibe['score_distribution']['positive']} | "
    f"Mixed: {vibe['score_distribution']['mixed']} | "
    f"Negative: {vibe['score_distribution']['negative']}"
)