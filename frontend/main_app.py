import streamlit as st
import requests
import json
from datetime import datetime

import merchant_dashboard
import user_app

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000/api"

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'token' not in st.session_state:
    st.session_state.token = None
if 'role' not in st.session_state:
    st.session_state.role = None

def login(username, password):
    """Login user and get token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/users/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]

            # Get user info
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(f"{API_BASE_URL}/users/me", headers=headers)

            if user_response.status_code == 200:
                user = user_response.json()
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.token = token
                st.session_state.role = user.get("role", "reviewer")
                return True, "Login successful!"
            else:
                return False, "Failed to get user information"
        else:
            return False, "Invalid username or password"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def signup(username, firstname, lastname, password, role="reviewer"):
    """Create new user account"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/users",
            json={
                "username": username,
                "firstname": firstname,
                "lastname": lastname,
                "password": password,
                "role": role,
            }
        )
        if response.status_code == 201:
            return True, "Account created successfully! Please login."
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, f"Failed to create account: {error_detail}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def logout():
    """Clear session state"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.token = None
    st.session_state.role = None

def main():
    st.set_page_config(
        page_title="VibeCheck - Business Review Analytics",
        page_icon="📊",
        layout="wide"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.authenticated:
        # Authentication Page
        st.markdown('<h1 class="main-header">📊 VibeCheck</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Business Review Analytics Platform</p>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab1:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.subheader("Login to Your Account")

            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submit_button = st.form_submit_button("Login", type="primary")

                if submit_button:
                    if not username or not password:
                        st.error("Please fill in all fields")
                    else:
                        with st.spinner("Logging in..."):
                            success, message = login(username, password)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.subheader("Create New Account")

            with st.form("signup_form"):
                new_username = st.text_input("Username", key="signup_username")
                firstname = st.text_input("First Name", key="signup_firstname")
                lastname = st.text_input("Last Name", key="signup_lastname")
                role = st.selectbox("Account role", ["reviewer", "merchant"], index=0, key="signup_role")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

                submit_button = st.form_submit_button("Create Account", type="primary")

                if submit_button:
                    if not all([new_username, firstname, lastname, new_password, confirm_password]):
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    else:
                        with st.spinner("Creating account..."):
                            success, message = signup(new_username, firstname, lastname, new_password, role)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Authenticated user - show appropriate dashboard based on role
        user = st.session_state.user

        # Header with user info and logout
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.title(f"Welcome back, {user['firstname']}!")
        with col2:
            st.write(f"Role: {st.session_state.role.title()}")
        with col3:
            if st.button("🚪 Logout", key="logout"):
                logout()
                st.rerun()

        # Role-based dashboard routing
        if st.session_state.role == "merchant":
            merchant_dashboard.render_merchant_dashboard()
        else:  # user/reviewer
            user_app.render_user_dashboard(user, st.session_state.token)

if __name__ == "__main__":
    main()