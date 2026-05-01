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
aspects = dashboard.get("aspects", {})


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


# -----------------------------
# ASPECT ANALYTICS
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
# ASPECT ANALYTICS (MERCHANT VIEW)
# -----------------------------
st.subheader("🍽️ Aspect Insights (Merchant View)")

aspects = dashboard.get("aspects", {})

if aspects:

    df_aspects = pd.DataFrame.from_dict(aspects, orient="index")
    df_aspects = df_aspects.reset_index().rename(columns={"index": "aspect"})

    # convert score → business-friendly label
    df_aspects["status"] = df_aspects["avg_score"].apply(convert_score_to_label)

    # -----------------------------
    # Layout (2 columns)
    # -----------------------------
    col1, col2 = st.columns(2)

    # -----------------------------
    # 1. Aspect Health Overview (LABELS instead of scores)
    # -----------------------------
    with col1:
        st.markdown("### 📊 Aspect Health")

        fig, ax = plt.subplots()

        colors = df_aspects["avg_score"].apply(
            lambda x: "green" if x > 0.2 else "orange" if x > -0.2 else "red"
        )

        ax.bar(df_aspects["aspect"], df_aspects["avg_score"], color=colors)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylabel("Sentiment Direction (Internal Only)")
        ax.set_xlabel("Aspect")

        st.pyplot(fig)

    # -----------------------------
    # 2. Mention Frequency (IMPORTANT FOR MERCHANTS)
    # -----------------------------
    with col2:
        st.markdown("### 📦 What Customers Talk About Most")

        fig2, ax2 = plt.subplots()
        ax2.bar(df_aspects["aspect"], df_aspects["count"])
        ax2.set_ylabel("Mentions")
        ax2.set_xlabel("Aspect")

        st.pyplot(fig2)

    # -----------------------------
    # 3. Merchant-Friendly Table
    # -----------------------------
    st.markdown("### 🧠 Summary (What You Should Focus On)")

    display_df = df_aspects[["aspect", "status", "count"]].copy()

    display_df = display_df.sort_values("count", ascending=False)

    st.dataframe(display_df, use_container_width=True)

    # -----------------------------
    # 4. Key Insight (MOST IMPORTANT FOR MERCHANTS)
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