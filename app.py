import streamlit as st
from modules.auth import sign_in, sign_out, get_current_user_profile
from views.admin_view import render_admin_view
from views.client_view import render_client_view

# Page Configuration
st.set_page_config(
    page_title="Social Hub",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom SaaS Branding CSS (#7C3AED accent)
st.markdown("""
<style>
    /* Primary buttons */
    div.stButton > button:first-child[kind="primary"] {
        background-color: #7C3AED;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: opacity 0.2s ease-in-out;
    }
    div.stButton > button:first-child[kind="primary"]:hover {
        opacity: 0.9;
        color: #FFFFFF;
    }
    /* Metric & header styling */
    h1, h2, h3 {
        color: #1E1035;
        font-weight: 700;
    }
    /* Clean container borders */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #E9D5FF;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session Initialization
if "user" not in st.session_state:
    st.session_state.user = None

# --- View 1: Login Gatekeeper ---
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center; color: #1E1035;'>📱 Social Hub</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280; margin-bottom: 25px;'>Content Operations & Approval Portal</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Work Email", placeholder="alex@clientbrand.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            login_submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            
            if login_submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    success, message = sign_in(email.strip(), password)
                    if success:
                        st.rerun()
                    else:
                        st.error(f"Sign in failed: {message}")
    st.stop()

# --- Authenticated State ---
profile = get_current_user_profile()

# Profile fallback check
if not profile:
    st.error("User profile not found. Please contact your account administrator.")
    if st.button("Log Out"):
        sign_out()
        st.rerun()
    st.stop()

# Sidebar User Info & Logout
role = profile.get("role", "client")
brand = profile.get("brands")

with st.sidebar:
    st.markdown("### 👤 Session")
    st.write(f"**Role:** `{role.upper()}`")
    st.write(f"**Email:** `{st.session_state.user.email}`")
    if brand:
        st.write(f"**Workspace:** {brand.get('name')}")
    st.markdown("---")
    if st.button("Log Out", use_container_width=True):
        sign_out()
        st.rerun()

# --- View 2: Role-Based Routing ---

# 1. Admin Dashboard
if role == "admin":
    render_admin_view()

# 2. Client Dashboard
elif role == "client":
    if not brand:
        st.warning("⚠️ No brand workspace is associated with this account.")
        st.stop()
        
    # Access Lock Gate: False = Pending approval
    if not brand.get("is_active", False):
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning("⏳ Workspace Awaiting Activation")
        st.info(
            f"The workspace for **{brand.get('name')}** is currently pending review by your agency. "
            "You will receive an email as soon as your access is activated."
        )
        st.stop()
        
    # Active workspace UI
    render_client_view(brand)

# 3. Agency Dashboard (Parent agency managing child brands)
elif role == "agency":
    st.title("🏢 Agency Workspace")
    st.info("Multi-brand agency view is active. Use the brand selector to switch client spaces.")