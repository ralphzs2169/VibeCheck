import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000/api"


@st.cache_data(ttl=60)
def fetch_businesses(token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    res = requests.get(f"{API_BASE_URL}/businesses", headers=headers)
    res.raise_for_status()
    return res.json()


@st.cache_data(ttl=30)
def fetch_business_dashboard(business_id, token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    res = requests.get(f"{API_BASE_URL}/businesses/{business_id}/dashboard", headers=headers)
    res.raise_for_status()
    return res.json()


def submit_review(business_id, content, token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post(
        f"{API_BASE_URL}/reviews",
        headers=headers,
        json={"business_id": business_id, "content": content},
    )
    return res.status_code == 201, res.json() if res.status_code != 201 else {}


def vibe_color(label: str) -> str:
    label = (label or "").lower()
    if "strong" in label:   return "#1A8C4E"   # deep green
    if "good" in label:     return "#FF7F11"   # orange
    if "neutral" in label:  return "#888888"   # gray
    if "needs" in label:    return "#E07B00"   # amber
    return "#CC2200"                           # red

# CSS 
def render_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* Business card */
    .biz-card {
        background: #FFF4E6;
        border: 1px solid #E8D5B7;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
    }
    .biz-card:hover {
        border-color: #FF7F11;
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(255,127,17,0.12);
    }
    .biz-card-name {
        font-family: 'DM Serif Display', serif;
        font-size: 1.15rem;
        color: #2E2E2E;
        margin: 0 0 0.25rem;
    }
    .biz-card-desc { color: #888; font-size: 0.85rem; margin: 0 0 0.5rem; }
    .biz-card-loc { color: #aaa; font-size: 0.78rem; }
    .biz-card-loc span { color: #FF7F11; margin-right: 4px; }

    /* Vibe pill */
    .vibe-pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.5rem;
    }

    /* Profile hero */
    .profile-hero {
        background: linear-gradient(135deg, #FFF4E6 0%, #FFE8CC 100%);
        border: 1px solid #E8D5B7;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }
    .profile-name {
        font-family: 'DM Serif Display', serif;
        font-size: 2rem;
        color: #2E2E2E;
        margin: 0 0 0.25rem;
    }
    .profile-loc { color: #999; font-size: 0.9rem; }
    .profile-desc { color: #777; font-size: 0.9rem; margin-top: 0.75rem; line-height: 1.6; }

    /* Stat cards */
    .stat-row { display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }
    .stat-card {
        flex: 1; min-width: 120px;
        background: #FFF4E6;
        border: 1px solid #E8D5B7;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .stat-val { font-size: 1.5rem; font-weight: 700; color: #FF7F11; }
    .stat-lbl { font-size: 0.72rem; color: #aaa; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 4px; }

    /* Review textarea */
    .stTextArea textarea {
        background: #FFF4E6 !important;
        border: 1px solid #E8D5B7 !important;
        color: #2E2E2E !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextArea textarea:focus { border-color: #FF7F11 !important; }

    /* Section header */
    .section-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.3rem;
        color: #2E2E2E;
        margin: 1.5rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #E8D5B7;
    }
    </style>
    """, unsafe_allow_html=True)


def render_business_list(businesses, token):
    """Render the business listing page."""
    st.markdown('<p class="section-title">All Businesses</p>', unsafe_allow_html=True)
    st.caption(f"{len(businesses)} businesses found")

    for biz in businesses:
        col_card, col_btn = st.columns([5, 1])
        with col_card:
            st.markdown(f"""
            <div class="biz-card">
                <p class="biz-card-name">{biz.get('name', 'Business')}</p>
                <p class="biz-card-desc">{biz.get('short_description', '')}</p>
                <p class="biz-card-loc"><span>📍</span>{biz.get('location', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)
            if st.button("View →", key=f"view_{biz['id']}"):
                st.session_state["selected_business"] = biz
                st.rerun()


def render_business_profile(biz, token):
    """Render the individual business profile page."""
    biz_id = biz["id"]

    if st.button("← Back to businesses", key="back_btn"):
        st.session_state.pop("selected_business", None)
        st.rerun()

    # Load dashboard data
    try:
        dash = fetch_business_dashboard(biz_id, token)
    except Exception as e:
        st.error(f"Could not load business data: {e}")
        return

    vibe = dash.get("vibe_summary", {})
    latest = dash.get("latest_vibe", {})
    dist = dash.get("distribution", {}).get("distribution", {})
    aspects = dash.get("aspects", {})
    vibe_label = vibe.get("vibe_label", "N/A")
    vibe_score = latest.get("vibe_score", None)
    review_count = vibe.get("review_count", "—")
    vc = vibe_color(vibe_label)

    # Hero section
    st.markdown(f"""
    <div class="profile-hero">
        <span class="vibe-pill" style="background:{vc}22; color:{vc}; border:1px solid {vc}44;">{vibe_label}</span>
        <p class="profile-name">{biz.get('name', '')}</p>
        <p class="profile-loc">📍 {biz.get('location', '')}</p>
        <p class="profile-desc">{biz.get('short_description', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats
    score_display = f"{vibe_score:.2f}" if isinstance(vibe_score, (int, float)) else "—"
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-val">{score_display}</div>
            <div class="stat-lbl">Vibe Score</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">{review_count}</div>
            <div class="stat-lbl">Reviews</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color:{vc}">{vibe_label}</div>
            <div class="stat-lbl">Overall Feel</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Keywords
    keywords = vibe.get("keywords", [])
    if keywords:
        st.markdown('<p class="section-title">What people are saying</p>', unsafe_allow_html=True)
        st.markdown(
            " ".join([f'<span style="background:#FFF4E6;border:1px solid #E8D5B7;color:#888;padding:3px 10px;border-radius:20px;font-size:0.8rem;margin:2px;display:inline-block;">#{k}</span>' for k in keywords]),
            unsafe_allow_html=True,
        )
        if vibe.get("summary_text"):
            st.markdown(f'<p style="color:#888;font-size:0.88rem;margin-top:0.75rem;line-height:1.6;">{vibe["summary_text"]}</p>', unsafe_allow_html=True)

    # Top aspects
    if aspects:
        st.markdown('<p class="section-title">Aspect Highlights</p>', unsafe_allow_html=True)
        top = sorted(aspects.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True)[:4]
        cols = st.columns(len(top))
        for i, (asp, data) in enumerate(top):
            score = data.get("avg_score", 0)
            color = vibe_color("strong" if score > 0.3 else "good" if score > 0.05 else "needs" if score < -0.05 else "neutral")
            with cols[i]:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-val" style="font-size:1.1rem;color:{color}">{score:+.2f}</div>
                    <div class="stat-lbl">{asp}</div>
                </div>
                """, unsafe_allow_html=True)

    # Write a review
    st.markdown('<p class="section-title">Write a Review</p>', unsafe_allow_html=True)
    review_text = st.text_area(
        "Share your experience",
        height=130,
        placeholder="What did you think? Be honest — your review helps others make better decisions.",
        key=f"review_input_{biz_id}",
        label_visibility="collapsed",
    )
    if st.button("Submit Review ✍️", key=f"submit_{biz_id}", type="primary"):
        if not review_text.strip():
            st.error("Write something before submitting.")
        else:
            ok, err = submit_review(biz_id, review_text, token)
            if ok:
                st.success("Review submitted! Thanks for sharing.")
                st.cache_data.clear()
            else:
                st.error(f"Failed: {err.get('detail', 'Unknown error')}")


def render_user_dashboard(user, token):
    render_css()

    selected = st.session_state.get("selected_business")

    if selected:
        render_business_profile(selected, token)
    else:
        try:
            businesses = fetch_businesses(token)
        except Exception as e:
            st.error(f"Could not load businesses: {e}")
            return

        if not businesses:
            st.info("No businesses registered yet.")
            return

        render_business_list(businesses, token)


if __name__ == "__main__":
    st.set_page_config(page_title="VibeCheck", layout="wide")
    st.warning("Open this through the main app.")