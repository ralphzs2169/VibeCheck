import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000/api"

# ── Session state init ────────────────────────────────────────────────────────
for key, default in {
    "authenticated": False,
    "user": None,
    "token": None,
    "role": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Auth helpers ──────────────────────────────────────────────────────────────
def login(username, password):
    try:
        res = requests.post(
            f"{API_BASE_URL}/users/login",
            json={"username": username, "password": password},
        )
        if res.status_code == 200:
            data = res.json()
            token = data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            me = requests.get(f"{API_BASE_URL}/users/me", headers=headers)
            if me.status_code == 200:
                user = me.json()
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.token = token
                st.session_state.role = user.get("role", "reviewer")
                return True, "Login successful!"
            return False, "Failed to get user info"
        return False, "Invalid username or password"
    except Exception as e:
        return False, f"Connection error: {e}"


def signup(username, firstname, lastname, password, role="reviewer"):
    try:
        res = requests.post(
            f"{API_BASE_URL}/users",
            json={
                "username": username,
                "firstname": firstname,
                "lastname": lastname,
                "password": password,
                "role": role,
            },
        )
        if res.status_code == 201:
            return True, "Account created! Please log in."
        return False, res.json().get("detail", "Unknown error")
    except Exception as e:
        return False, f"Connection error: {e}"


def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.token = None
    st.session_state.role = None

# ── CSS injection ─────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background: #FAF3E0; /* cream base */
        color: #2E2E2E;      /* dark gray text */
    }

    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 0 !important; }

    /* ── Top nav bar ── */
    .topbar {
        position: sticky;
        top: 0;
        z-index: 999;
        background: #FFF4E6; /* soft cream-orange */
        border-bottom: 1px solid #E0E0E0;
        padding: 0.75rem 2.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .topbar-logo {
        font-family: 'DM Serif Display', serif;
        font-size: 1.4rem;
        color: #FF7F11 !important; /* vibrant orange */
        letter-spacing: -0.02em;
    }
    .topbar-logo span { color: #2E2E2E !important; }
    .topbar-right { display: flex; align-items: center; gap: 1.5rem; }
    .topbar-user { color: #666; font-size: 0.85rem; }
    .topbar-name { color: #2E2E2E; font-weight: 600; font-size: 0.9rem; }
    .topbar-role {
        background: #FF7F11;
        color: #fff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .topbar-role.merchant { background: #2ECC71; } /* green for merchants */

    /* ── Auth page ── */
    .auth-wrap {
        min-height: 100vh;
        background: #FAF3E0;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    .auth-title {
        font-family: 'DM Serif Display', serif;
        font-size: 3.5rem;
        color: #2E2E2E;
        line-height: 1;
        margin: 0;
    }
    .auth-title .accent { color: #FF7F11 !important; }
    .auth-subtitle {
        color: #666;
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }

    /* Inputs */
    .stTextInput > label { color: #555 !important; font-size: 0.8rem !important; }
    .stTextInput > div > div > input {
        background: #FFFFFF !important;
        border: 1px solid #CCC !important;
        color: #2E2E2E !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #FF7F11 !important;
        box-shadow: 0 0 0 2px rgba(255,127,17,0.15) !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: #FF7F11 !important;
        color: #fff !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        width: 100%;
        padding: 0.6rem !important;
        font-size: 0.95rem !important;
        transition: opacity 0.2s;
    }
    .stButton > button[kind="primary"]:hover { opacity: 0.85 !important; }

    /* Logout button */
    .stButton > button:not([kind="primary"]) {
        background: transparent !important;
        border: 1px solid #CCC !important;
        color: #666 !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #FF7F11 !important;
        color: #FF7F11 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        background: #FFF4E6;
        color: #666;
        border-radius: 8px 8px 0 0;
        font-size: 0.85rem;
        padding: 0.5rem 1.25rem;
    }
    .stTabs [aria-selected="true"] {
        background: #FF7F11 !important;
        color: #fff !important;
        font-weight: 700 !important;
    }

    /* main bg when authenticated */
    .main-bg { background: #FAF3E0; min-height: 100vh; }
    </style>
    """, unsafe_allow_html=True)


# ── Top nav bar (rendered after login) ───────────────────────────────────────
def render_topbar():
    user = st.session_state.user
    role = st.session_state.role or "reviewer"
    name = f"{user.get('firstname', '')} {user.get('lastname', '')}"
    role_color = "#2ECC71" if role == "merchant" else "#FF7F11"

    logo_col, spacer, info_col, role_col, logout_col = st.columns([2, 4, 2, 1, 1])

    with logo_col:
        st.markdown(
            "<div style='padding:0.6rem 0'><span style='font-family:DM Serif Display,serif;font-size:1.4rem;color:#FF7F11'>Vibe</span><span style='font-family:DM Serif Display,serif;font-size:1.4rem;color:#2E2E2E'>Check</span></div>",
            unsafe_allow_html=True,
        )

    with info_col:
        st.markdown(
            f"<div style='text-align:right;padding-top:0.3rem'><div style='font-weight:600;font-size:0.9rem;color:#2E2E2E'>{name}</div><div style='font-size:0.78rem;color:#888'>@{user.get('username','')}</div></div>",
            unsafe_allow_html=True,
        )

    with role_col:
        st.markdown(
            f"<div style='padding-top:0.55rem;text-align:center'><span style='background:{role_color};color:#fff;font-size:0.7rem;font-weight:700;padding:3px 10px;border-radius:20px;text-transform:uppercase'>{role}</span></div>",
            unsafe_allow_html=True,
        )

    with logout_col:
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="topbar_logout"):
            logout()
            st.rerun()

    st.markdown("<hr style='margin:0;border:none;border-top:1px solid #E0E0E0'>", unsafe_allow_html=True)


# ── Auth page ─────────────────────────────────────────────────────────────────
def render_auth_page():
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(
           "<h1 style='text-align:center;font-family:DM Serif Display,serif;font-size:3rem;margin-bottom:0'>Vibe<span style='color:#FF7F11'>Check</span></h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center;color:#666;margin-top:0.25rem;margin-bottom:2rem'>Business review analytics — for merchants & reviewers</p>",
            unsafe_allow_html=True,
        )

        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", type="primary")
                if submitted:
                    if not username or not password:
                        st.error("Please fill in all fields.")
                    else:
                        with st.spinner("Logging in…"):
                            ok, msg = login(username, password)
                        if ok:
                            st.rerun()
                        else:
                            st.error(msg)

        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input("Username")
                col1, col2 = st.columns(2)
                with col1:
                    firstname = st.text_input("First Name")
                with col2:
                    lastname = st.text_input("Last Name")
                role = st.selectbox("I am a…", ["reviewer", "merchant"])
                new_password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account", type="primary")
                if submitted:
                    if not all([new_username, firstname, lastname, new_password, confirm]):
                        st.error("Please fill in all fields.")
                    elif new_password != confirm:
                        st.error("Passwords do not match.")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        with st.spinner("Creating account…"):
                            ok, msg = signup(new_username, firstname, lastname, new_password, role)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="VibeCheck",
        page_icon="📊",
        layout="wide",
    )
    inject_css()

    if not st.session_state.authenticated:
        render_auth_page()
    else:
        render_topbar()
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        if st.session_state.role == "merchant":
            import merchant_dashboard
            merchant_dashboard.render_merchant_dashboard()
        else:
            import user_app
            user_app.render_user_dashboard(
                st.session_state.user,
                st.session_state.token,
            )


if __name__ == "__main__":
    main()