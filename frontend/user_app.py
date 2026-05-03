import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000/api"


@st.cache_data(ttl=60)
def fetch_json(url, headers=None):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def render_user_dashboard(user, token):
    st.header("👤 Reviewer Dashboard")
    st.info("Write reviews, browse businesses, and track your review activity.")

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    tab1, tab2, tab3 = st.tabs(["📝 Submit Review", "🏢 Browse Businesses", "📊 My Analytics"])

    with tab1:
        st.subheader("Write a Review")
        business_id = st.number_input("Business ID", min_value=1, value=1, key="review_business_id")
        review_text = st.text_area("Your review", height=150, key="review_text")

        if st.button("Submit Review", key="submit_review"):
            if not review_text:
                st.error("Enter a review before submitting.")
            else:
                payload = {
                    "business_id": business_id,
                    "content": review_text,
                }
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/reviews",
                        headers=headers,
                        json=payload,
                    )
                    if response.status_code == 201:
                        st.success("Review submitted successfully.")
                    else:
                        error_detail = response.json().get("detail", response.text)
                        st.error(f"Failed to submit review: {error_detail}")
                except Exception as exc:
                    st.error(f"Unable to connect to backend: {exc}")

    with tab2:
        st.subheader("Browse Businesses")
        try:
            businesses = fetch_json(f"{API_BASE_URL}/businesses", headers=headers)
        except Exception as exc:
            st.error(f"Unable to load businesses: {exc}")
            businesses = []

        if businesses:
            for business in businesses:
                with st.container():
                    st.markdown(f"**{business.get('name', 'Business')}**")
                    st.write(business.get('short_description', 'No description available.'))
                    st.caption(f"Location: {business.get('location', 'Unknown')} | ID: {business.get('id')}")
        else:
            st.info("No businesses available at this time.")

    with tab3:
        st.subheader("My Review Analytics")
        st.metric("Signed in as", f"{user.get('firstname')} {user.get('lastname')}")
        st.metric("Role", user.get("role", "reviewer"))
        st.write("This dashboard can be extended to show your submitted reviews, helpful votes, and review history.")


if __name__ == "__main__":
    st.set_page_config(page_title="VibeCheck Reviewer Dashboard", layout="wide")
    st.warning("This page is intended to be opened through the main authentication flow.")
