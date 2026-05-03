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
# Fetch dashboard data
# -----------------------------
dashboard = fetch_json(
    f"{API_URL}/{business_id}/dashboard"
)

# -----------------------------
# CORE DATA EXTRACTION
# -----------------------------
vibe_over_time = dashboard.get("vibe_over_time", {})
vibe_trend = dashboard.get("vibe_trend", {})
vibe_volatility = dashboard.get("vibe_volatility", {})
latest_vibe = dashboard.get("latest_vibe", {})

distribution = dashboard.get("distribution", {})
trend = dashboard.get("trend", {})
volatility = dashboard.get("volatility", {})
peak_drop = dashboard.get("peak_drop", {})
temporal = dashboard.get("temporal", {})
forecast = dashboard.get("forecast", None)
aspects = dashboard.get("aspects", {})

# -----------------------------
# META HANDLING (NEW STANDARD)
# -----------------------------
def is_reliable(meta):
    if not meta:
        return False
    return meta.get("is_reliable", False)


# -----------------------------
# CURRENT VIBE SUMMARY
# -----------------------------
st.subheader("🌟 Current Vibe Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Vibe Label",
        latest_vibe.get("vibe_label", "No data")
    )

with col2:
    st.metric(
        "Vibe Score",
        latest_vibe.get("vibe_score", "-")
    )

with col3:
    st.metric(
        "Reviews",
        vibe_over_time.get("meta", {}).get("sample_size", 0)
    )

st.write(latest_vibe.get("summary_text", "No summary available."))


# -----------------------------
# VIBE OVER TIME
# -----------------------------
st.subheader("📈 Vibe Score Over Time")

if vibe_over_time.get("data"):

    df_vibe = pd.DataFrame(vibe_over_time["data"])

    df_vibe["date"] = pd.to_datetime(df_vibe["period"], errors="coerce")
    df_vibe = df_vibe.set_index("date")

    st.line_chart(df_vibe["score"])

else:
    st.info("No vibe snapshot history available.")


# -----------------------------
# VIBE METRICS
# -----------------------------
st.subheader("📊 Vibe Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Vibe Trend",
        vibe_trend.get("trend", "N/A"),
        delta=round(vibe_trend.get("slope", 0), 4)
    )

with col2:
    st.metric(
        "Vibe Volatility",
        vibe_volatility.get("stability", "N/A"),
        delta=round(vibe_volatility.get("volatility", 0), 4)
    )

with col3:
    st.metric(
        "Latest Vibe Score",
        latest_vibe.get("vibe_score", 0)
    )


# -----------------------------
# SENTIMENT OVER TIME
# -----------------------------
st.subheader("📈 Sentiment Trend Over Time")

if temporal and temporal.get("data"):

    df_temporal = pd.DataFrame(temporal["data"])
    df_temporal = df_temporal.set_index("period")

    st.line_chart(df_temporal["avg_score"])

else:
    st.info("No temporal data available.")


# -----------------------------
# SENTIMENT DISTRIBUTION
# -----------------------------
st.subheader("🥧 Sentiment Distribution")

dist = distribution.get("distribution", {})

if dist:

    # Extract count and percentage from nested structure
    counts_only = {label: data["count"] for label, data in dist.items()}
    
    df_dist = pd.DataFrame.from_dict(
        counts_only,
        orient="index",
        columns=["count"]
    )

    fig, ax = plt.subplots()

    df_dist["count"].plot.pie(
        autopct="%1.1f%%",
        legend=False,
        ylabel="",
        ax=ax
    )

    st.pyplot(fig)

else:
    st.info("No distribution data.")


# -----------------------------
# ANALYTICS METRICS
# -----------------------------
st.subheader("📌 Analytics Metrics")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Trend",
        trend.get("trend", "N/A"),
        delta=round(trend.get("slope", 0), 4)
    )

with col2:
    st.metric(
        "Volatility",
        volatility.get("stability", "N/A"),
        delta=round(volatility.get("volatility", 0), 4)
    )


# -----------------------------
# PEAK / DROP
# -----------------------------
st.subheader("🚨 Major Sentiment Changes")

peak = peak_drop.get("peak")
drop = peak_drop.get("drop")

if peak:
    st.success(
        f"Peak increase: {peak['date']} ({peak['change']:.4f})"
    )

if drop:
    st.error(
        f"Largest drop: {drop['date']} ({drop['change']:.4f})"
    )


# -----------------------------
# FORECAST
# -----------------------------
st.subheader("🔮 Sentiment Forecast")

if forecast and forecast.get("status") != "insufficient_data":
    st.metric(
        "Predicted Future Vibe",
        forecast.get("predicted_vibe", "N/A"),
        delta=round(forecast.get("forecast_score", 0), 4)
    )
else:
    meta = forecast.get("meta", {}) if forecast else {}
    min_required = meta.get("min_required", 6)
    sample_size = meta.get("sample_size", 0)
    st.warning(
        f"⚠️ Insufficient data for forecast. Need {min_required} months of data, have {sample_size} month(s)."
    )


# -----------------------------
# ADDITIONAL SIGNALS
# -----------------------------
st.subheader("🔍 Additional Signals")

score_dist = vibe_over_time.get("score_distribution", {})

if score_dist:

    st.write(
        f"**Polarizing:** {score_dist.get('is_polarizing', False)}"
    )

    st.write(
        f"Positive: {score_dist.get('positive', 0)} | "
        f"Mixed: {score_dist.get('mixed', 0)} | "
        f"Negative: {score_dist.get('negative', 0)}"
    )


# -----------------------------
# ASPECT ANALYTICS HELPERS
# -----------------------------
def convert_score_to_label(score: float) -> str:
    if score >= 0.3:
        return "Strong 👍"
    elif score >= 0.05:
        return "Good 🙂"
    elif score > -0.05:
        return "Neutral 😐"
    elif score > -0.3:
        return "Needs Improvement ⚠️"
    else:
        return "Critical 🔴"


# -----------------------------
# ASPECT ANALYTICS
# -----------------------------
st.subheader("🍽️ Aspect Insights (Merchant View)")

aspect_summary = aspects.get("summary", {}) if aspects else {}

if aspect_summary:

    df_aspects = pd.DataFrame.from_dict(aspect_summary, orient="index")
    df_aspects = df_aspects.reset_index().rename(columns={"index": "aspect"})

    df_aspects["status"] = df_aspects["avg_score"].apply(convert_score_to_label)

    col1, col2 = st.columns(2)

    # -----------------------------
    # Aspect Health
    # -----------------------------
    with col1:
        st.markdown("### 📊 Aspect Health")

        fig, ax = plt.subplots()

        colors = df_aspects["avg_score"].apply(
            lambda x: "green" if x > 0.2 else "orange" if x > -0.2 else "red"
        )

        ax.bar(df_aspects["aspect"], df_aspects["avg_score"], color=colors)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylabel("Sentiment Direction")
        ax.set_xlabel("Aspect")

        st.pyplot(fig)

    # -----------------------------
    # Mention Frequency
    # -----------------------------
    with col2:
        st.markdown("### 📦 What Customers Talk About Most")

        fig2, ax2 = plt.subplots()
        ax2.bar(df_aspects["aspect"], df_aspects["count"])
        ax2.set_ylabel("Mentions")
        ax2.set_xlabel("Aspect")

        st.pyplot(fig2)

    # -----------------------------
    # TABLE VIEW
    # -----------------------------
    st.markdown("### 🧠 Summary (Actionable Insights)")

    display_df = df_aspects[["aspect", "status", "count"]]
    display_df = display_df.sort_values("count", ascending=False)

    st.dataframe(display_df, use_container_width=True)

    # -----------------------------
    # KEY INSIGHTS
    # -----------------------------
    worst = df_aspects.sort_values("avg_score").iloc[0]
    best = df_aspects.sort_values("avg_score", ascending=False).iloc[0]

    st.error(
        f"⚠️ Needs Attention: {worst['aspect'].upper()} → {worst['status']}"
    )

    st.success(
        f"✅ Strongest Area: {best['aspect'].upper()} → {best['status']}"
    )

else:
    st.info("No aspect analytics available.")