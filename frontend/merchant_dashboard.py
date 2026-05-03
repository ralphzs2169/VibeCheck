import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

API_BASE_URL = "http://127.0.0.1:8000/api"


def fetch_json(url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()


def vibe_color(score):
    if score is None:
        return "#555"
    if score >= 0.3:  return "#5af0b0"
    if score >= 0.05: return "#e8ff5a"
    if score > -0.05: return "#aaaaaa"
    if score > -0.3:  return "#ffb347"
    return "#ff6b6b"


def vibe_label(score):
    if score is None: return "N/A"
    if score >= 0.3:  return "Strong 👍"
    if score >= 0.05: return "Good 🙂"
    if score > -0.05: return "Neutral 😐"
    if score > -0.3:  return "Needs Work ⚠️"
    return "Critical 🔴"


def render_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ── Dashboard layout ── */
    .dash-section {
        background: #FFF4E6; /* cream */
        border: 1px solid #E8D5B7;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .dash-section-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.1rem;
        color: #2E2E2E; /* dark gray */
        margin: 0 0 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .dash-section-title span { color: #FF7F11; } /* Cebuano orange */

    /* ── KPI cards ── */
    .kpi-card {
        flex: 1; min-width: 130px;
        background: #FFF4E6;
        border: 1px solid #E8D5B7;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
    }
    .kpi-val { font-size: 2rem; font-weight: 700; line-height: 1; color: #FF7F11; }
    .kpi-lbl { font-size: 0.72rem; color: #777; text-transform: uppercase; letter-spacing: 0.07em; margin-top: 0.4rem; }
    .kpi-sub { font-size: 0.78rem; color: #999; margin-top: 0.25rem; }

    /* ── Aspect table ── */
    .aspect-row { border-bottom: 1px solid #E8D5B7; }
    .aspect-name { color: #2E2E2E; font-size: 0.88rem; text-transform: capitalize; }
    .aspect-bar-wrap { background: #FFE8CC; }
    .aspect-score { font-size: 0.82rem; font-weight: 600; color: #FF7F11; }

    /* ── Vibe hero ── */
    .vibe-hero {
        background: linear-gradient(135deg, #FFF4E6, #FFE8CC);
        border: 1px solid #E8D5B7;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    .vibe-label-big { font-family: 'DM Serif Display', serif; font-size: 1.6rem; color: #2E2E2E; }
    .vibe-meta { color: #777; font-size: 0.85rem; }
    .keyword-chip {
        background: #FFE8CC;
        border: 1px solid #E8D5B7;
        color: #2E2E2E;
    }

    /* Inputs */
    .stSelectbox > div > div {
        background: #FFF4E6 !important;
        border-color: #E8D5B7 !important;
        color: #2E2E2E !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_kpi(label, value, sub=None, color="#e8ff5a"):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val" style="color:{color}">{value}</div>
        <div class="kpi-lbl">{label}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_merchant_dashboard():
    render_css()
    token = st.session_state.get("token")

    # ── Load merchant's own businesses ───────────────────────────────────────
    try:
        businesses = fetch_json(f"{API_BASE_URL}/users/me/businesses", token=token)
    except Exception as e:
        st.error(f"Could not load your businesses: {e}")
        return

    if not businesses:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;">
            <p style="font-family:'DM Serif Display',serif;font-size:2rem;color:#fff;">No businesses yet</p>
            <p style="color:#555;">Register your first business to start seeing analytics.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Business selector
    options = {b["name"]: b for b in businesses}
    col_sel, _ = st.columns([2, 3])
    with col_sel:
        selected_name = st.selectbox("Your Business", list(options.keys()), key="merchant_biz_select", label_visibility="collapsed")
    biz = options[selected_name]
    biz_id = biz["id"]

    # ── Load dashboard ────────────────────────────────────────────────────────
    try:
        dash = fetch_json(f"{API_BASE_URL}/businesses/{biz_id}/dashboard", token=token)
    except Exception as e:
        st.error(f"Could not load dashboard: {e}")
        return

    vibe        = dash.get("vibe_summary", {})
    latest      = dash.get("latest_vibe", {})
    vibe_trend  = dash.get("vibe_trend", {})
    vibe_vol    = dash.get("vibe_volatility", {})
    temporal    = dash.get("temporal", [])
    distribution= dash.get("distribution", {}).get("distribution", {})
    aspects     = dash.get("aspects", {})
    forecast    = dash.get("forecast")

    score = latest.get("vibe_score")
    vc = vibe_color(score)
    vl = vibe.get("vibe_label") or vibe_label(score)
    review_count = vibe.get("review_count", "—")
    keywords = vibe.get("keywords", [])
    summary = vibe.get("summary_text", "")

    # ── Vibe Hero ─────────────────────────────────────────────────────────────
    score_display = f"{score:.2f}" if isinstance(score, (int, float)) else "—"
    kw_html = " ".join([f'<span class="keyword-chip">#{k}</span>' for k in keywords[:8]])
    st.markdown(f"""
    <div class="vibe-hero">
        <div class="vibe-score-ring" style="background:{vc}18;border:3px solid {vc};">
            <div class="vibe-score-big" style="color:{vc}">{score_display}</div>
            <div class="vibe-score-sub">vibe</div>
        </div>
        <div class="vibe-details">
            <p class="vibe-label-big">{vl}</p>
            <p class="vibe-meta">{selected_name} · {review_count} reviews</p>
            {('<p style="color:#888;font-size:0.85rem;margin:0.5rem 0 0.4rem;line-height:1.6">' + summary + '</p>') if summary else ''}
            <div style="margin-top:0.5rem">{kw_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    trend_val = vibe_trend.get("trend", "—")
    slope     = vibe_trend.get("slope", 0)
    stability = vibe_vol.get("stability", "—")
    vol       = vibe_vol.get("volatility", 0)
    forecast_score = forecast.get("forecast_score", None) if forecast else None
    fc = vibe_color(forecast_score)

    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]:
        render_kpi("Reviews", review_count, color="#fff")
    with cols[1]:
        render_kpi("Trend", trend_val, sub=f"slope {slope:+.4f}" if isinstance(slope, float) else None, color=vibe_color(slope if isinstance(slope, float) else 0))
    with cols[2]:
        render_kpi("Stability", stability, sub=f"volatility {vol:.4f}" if isinstance(vol, float) else None, color="#aaa")
    with cols[3]:
        fc_display = f"{forecast_score:.2f}" if isinstance(forecast_score, (int, float)) else "—"
        render_kpi("Forecast", fc_display, sub=forecast.get("predicted_vibe") if forecast else None, color=fc)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Two-column: Trend chart + Pie chart ──────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="dash-section">', unsafe_allow_html=True)
        st.markdown('<div class="dash-section-title">📈 <span>Sentiment</span> Over Time</div>', unsafe_allow_html=True)
        if temporal:
            df = pd.DataFrame(temporal)
            if "period" in df.columns and "avg_score" in df.columns:
                df = df.set_index("period")
                fig, ax = plt.subplots(figsize=(6, 2.5))
                fig.patch.set_facecolor("#161616")
                ax.set_facecolor("#161616")
                ax.plot(df.index, df["avg_score"], color=vc, linewidth=2, marker="o", markersize=4)
                ax.axhline(0, color="#333", linewidth=0.8, linestyle="--")
                ax.fill_between(df.index, df["avg_score"], 0, alpha=0.15, color=vc)
                ax.tick_params(colors="#555", labelsize=7)
                for spine in ax.spines.values():
                    spine.set_edgecolor("#2a2a2a")
                ax.set_ylabel("Score", color="#555", fontsize=7)
                plt.xticks(rotation=30, ha="right")
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            else:
                st.info("Not enough data to plot.")
        else:
            st.info("No temporal data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="dash-section">', unsafe_allow_html=True)
        st.markdown('<div class="dash-section-title">🥧 <span>Sentiment</span> Distribution</div>', unsafe_allow_html=True)
        if distribution:
            COLORS = {
                "positive": "#5af0b0",
                "neutral":  "#e8ff5a",
                "negative": "#ff6b6b",
            }
            labels = list(distribution.keys())
            sizes  = [distribution[k] for k in labels]
            colors = [COLORS.get(k.lower(), "#888") for k in labels]

            fig, ax = plt.subplots(figsize=(4, 3))
            fig.patch.set_facecolor("#FFF4E6")
            ax.set_facecolor("#FFF4E6")
            wedges, texts, autotexts = ax.pie( # type: ignore
                sizes,
                labels=None,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.75,
                wedgeprops={"linewidth": 2, "edgecolor": "#FFF4E6"},  # update edge color for cream scheme
            )

            for at in autotexts:
                at.set_color("#FFF4E6")
                at.set_fontsize(9)
                at.set_fontweight("bold")
            patches = [mpatches.Patch(color=colors[i], label=labels[i].capitalize()) for i in range(len(labels))]
            ax.legend(handles=patches, loc="lower center", ncol=len(labels),
                      bbox_to_anchor=(0.5, -0.08), frameon=False,
                      labelcolor="#aaa", fontsize=8)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("No distribution data yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Aspect Insights ───────────────────────────────────────────────────────
    if aspects:
        st.markdown('<div class="dash-section">', unsafe_allow_html=True)
        st.markdown('<div class="dash-section-title">🔍 <span>Aspect</span> Breakdown</div>', unsafe_allow_html=True)
        sorted_aspects = sorted(aspects.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True)
        for asp_name, asp_data in sorted_aspects:
            score_val = asp_data.get("avg_score", 0)
            count = asp_data.get("count", "")
            color = vibe_color(score_val)
            bar_pct = min(abs(score_val) * 100, 100)
            st.markdown(f"""
            <div class="aspect-row">
                <div class="aspect-name">{asp_name}</div>
                <div class="aspect-bar-wrap">
                    <div class="aspect-bar" style="width:{bar_pct}%;background:{color}"></div>
                </div>
                <div class="aspect-score" style="color:{color}">{score_val:+.2f}</div>
                <div style="color:#444;font-size:0.72rem;margin-left:0.5rem;width:40px;text-align:right">{count} rev</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Summary text ─────────────────────────────────────────────────────────
    if vibe.get("summary_text"):
        st.markdown('<div class="dash-section">', unsafe_allow_html=True)
        st.markdown('<div class="dash-section-title">💬 <span>AI</span> Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#888;font-size:0.9rem;line-height:1.7">{vibe["summary_text"]}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(page_title="Merchant Dashboard", layout="wide")
    st.warning("Open this through the main app.")