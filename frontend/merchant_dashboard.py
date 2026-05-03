import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

API_BASE_URL = "http://127.0.0.1:8000/api"


@st.cache_data(ttl=60)
def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def convert_score_to_label(score: float) -> str:
    if score >= 0.3:
        return "Strong 👍"
    if score >= 0.05:
        return "Good 🙂"
    if score > -0.05:
        return "Neutral 😐"
    if score > -0.3:
        return "Needs Improvement ⚠️"
    return "Critical 🔴"


def render_merchant_dashboard():
    st.header("🏢 Merchant Dashboard")
    st.info("View sentiment, trend, and business analytics for merchant accounts.")

    business_id = st.number_input("Business ID", min_value=1, value=1, key="merchant_business_id")

    try:
        dashboard = fetch_json(f"{API_BASE_URL}/businesses/{business_id}/dashboard")
    except Exception as exc:
        st.error(f"Unable to load dashboard data: {exc}")
        return

    vibe = dashboard.get("vibe_summary", {})
    latest_vibe = dashboard.get("latest_vibe", {})
    vibe_trend = dashboard.get("vibe_trend", {})
    vibe_volatility = dashboard.get("vibe_volatility", {})
    temporal = dashboard.get("temporal", [])
    distribution = dashboard.get("distribution", {}).get("distribution", {})
    aspects = dashboard.get("aspects", {})

    st.subheader("🌟 Current Vibe Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vibe Label", vibe.get("vibe_label", "N/A"))
    with col2:
        st.metric("Vibe Score", latest_vibe.get("vibe_score", "N/A"))
    with col3:
        st.metric("Reviews", vibe.get("review_count", "N/A"))

    if isinstance(vibe.get("keywords"), list):
        st.write(vibe.get("summary_text", ""))
        st.write("**Keywords:**", ", ".join(vibe["keywords"]))

    st.subheader("📈 Sentiment Trend Over Time")
    if temporal:
        df_temporal = pd.DataFrame(temporal)
        if "period" in df_temporal.columns and "avg_score" in df_temporal.columns:
            df_temporal = df_temporal.set_index("period")
            st.line_chart(df_temporal["avg_score"])
        else:
            st.info("Not enough temporal data to display chart.")
    else:
        st.info("No temporal data available.")

    st.subheader("🥧 Sentiment Distribution")
    if distribution:
        df_dist = pd.DataFrame.from_dict(distribution, orient="index", columns=["count"])
        fig, ax = plt.subplots()
        df_dist.plot.pie(y="count", autopct="%1.1f%%", legend=False, ylabel="", ax=ax)
        st.pyplot(fig)
    else:
        st.info("Distribution data is not available.")

    st.subheader("📌 Aspect Insights")
    if aspects:
        df_aspects = pd.DataFrame.from_dict(aspects, orient="index")
        if not df_aspects.empty:
            df_aspects = df_aspects.reset_index().rename(columns={"index": "aspect"})
            df_aspects["status"] = df_aspects["avg_score"].apply(convert_score_to_label)
            st.dataframe(df_aspects[["aspect", "avg_score", "status"]])
        else:
            st.info("No aspect insights available.")
    else:
        st.info("No aspect analytics found.")


if __name__ == "__main__":
    st.set_page_config(page_title="Vibe Analytics Dashboard", layout="wide")
    render_merchant_dashboard()
