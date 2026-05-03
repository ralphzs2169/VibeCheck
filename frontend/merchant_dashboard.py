import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

API_BASE_URL = "http://127.0.0.1:8000/api"


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
    st.write("Merchant view for business performance, sentiment, and review analytics.")

    try:
        businesses = fetch_json(f"{API_BASE_URL}/businesses")
    except Exception as exc:
        st.error(f"Unable to load businesses: {exc}")
        return

    if not businesses:
        st.info("No businesses available yet.")
        return

    business_options = {business["name"]: business["id"] for business in businesses}
    business_name = st.selectbox("Select business", list(business_options.keys()), key="merchant_business_name")
    business_id = business_options[business_name]

    st.subheader(f"Analytics for {business_name}")

    try:
        dashboard = fetch_json(f"{API_BASE_URL}/businesses/{business_id}/dashboard")
    except Exception as exc:
        st.error(f"Unable to load dashboard for selected business: {exc}")
        return

    vibe = dashboard.get("vibe_summary", {})
    latest_vibe = dashboard.get("latest_vibe", {})
    vibe_trend = dashboard.get("vibe_trend", {})
    vibe_volatility = dashboard.get("vibe_volatility", {})
    temporal = dashboard.get("temporal", [])
    distribution = dashboard.get("distribution", {}).get("distribution", {})
    aspects = dashboard.get("aspects", {})
    forecast = dashboard.get("forecast", None)

    st.markdown("### Current Vibe Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vibe Label", vibe.get("vibe_label", "N/A"))
    with col2:
        st.metric("Vibe Score", latest_vibe.get("vibe_score", "N/A"))
    with col3:
        st.metric("Review Count", vibe.get("review_count", "N/A"))

    if isinstance(vibe.get("keywords"), list):
        st.write(vibe.get("summary_text", ""))
        st.write("**Top keywords:**", ", ".join(vibe["keywords"]))

    st.markdown("---")
    st.markdown("### Trend & Volatility")

    if temporal:
        df_temporal = pd.DataFrame(temporal)
        if "period" in df_temporal.columns and "avg_score" in df_temporal.columns:
            df_temporal = df_temporal.set_index("period")
            st.line_chart(df_temporal["avg_score"])
        else:
            st.info("Not enough trend data to display.")
    else:
        st.info("No temporal sentiment data available.")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Trend", vibe_trend.get("trend", "N/A"), delta=round(vibe_trend.get("slope", 0), 4))
    with col2:
        st.metric("Volatility", vibe_volatility.get("stability", "N/A"), delta=round(vibe_volatility.get("volatility", 0), 4))

    st.markdown("---")
    st.markdown("### Sentiment Distribution")

    if distribution:
        df_dist = pd.DataFrame.from_dict(distribution, orient="index", columns=["count"])
        fig, ax = plt.subplots()
        df_dist.plot.pie(y="count", autopct="%1.1f%%", legend=False, ylabel="", ax=ax)
        st.pyplot(fig)
    else:
        st.info("Distribution data is not available.")

    st.markdown("---")
    st.markdown("### Aspect Insights")

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

    st.markdown("---")
    st.markdown("### Forecast")

    if forecast:
        st.metric("Predicted Vibe", forecast.get("predicted_vibe", "N/A"), delta=round(forecast.get("forecast_score", 0), 4))
    else:
        st.info("No forecast available.")


if __name__ == "__main__":
    st.set_page_config(page_title="Vibe Analytics Dashboard", layout="wide")
    render_merchant_dashboard()
