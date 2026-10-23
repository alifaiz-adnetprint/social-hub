import streamlit as st
from datetime import datetime
from modules.db import (
    get_posts_by_platform,
    get_signed_media_url,
    request_post_revision,
    approve_all_pending_posts
)
from modules.mailer import email_batch_approved, email_revision_requested

# --- Custom Dark Theme CSS ---
DARK_THEME_CSS = """
<style>
    /* App background & default text */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Hide top Streamlit toolbar/header padding */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1350px !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0D1117 !important;
        border-right: 1px solid #1E2430;
    }
    
    /* Progress Pill Container */
    .quota-box {
        background: #161B26;
        border: 1px solid #283042;
        border-radius: 20px;
        padding: 6px 16px;
        display: inline-flex;
        align-items: center;
        gap: 12px;
    }
    .quota-text {
        font-size: 0.82rem;
        font-weight: 500;
        color: #CBD5E1;
    }
    .quota-bar-bg {
        width: 100px;
        height: 6px;
        background: #2D3748;
        border-radius: 999px;
        overflow: hidden;
    }
    .quota-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #6366F1, #8B5CF6);
        border-radius: 999px;
    }

    /* Custom Platform Tab styling */
    div[data-testid="stTabs"] button[role="tab"] {
        background-color: transparent !important;
        color: #94A3B8 !important;
        font-weight: 500;
        font-size: 0.95rem;
        border: none !important;
        padding: 10px 18px !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        font-weight: 600;
        border-bottom: 2px solid #8B5CF6 !important;
    }
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
        background-color: #8B5CF6 !important;
    }

    /* Post Card Box */
    .post-card {
        background-color: #151922;
        border: 1px solid #222938;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .post-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .post-card-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        font-weight: 600;
        color: #F8FAFC;
    }

    /* Badges */
    .badge {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        display: inline-block;
    }
    .badge-review {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .badge-approved {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .badge-revision {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }

    /* Client Feedback Callout */
    .feedback-bubble {
        background: #1C1936;
        border: 1px solid #4C1D95;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.8rem;
        color: #DDD6FE;
        margin-top: 10px;
    }

    /* Primary Violet Action Button */
    div.stButton > button:first-child[kind="primary"] {
        background: #6D28D9;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 6px 18px;
        transition: all 0.2s;
    }
    div.stButton > button:first-child[kind="primary"]:hover {
        background: #5B21B6;
    }

    /* Secondary buttons */
    div.stButton > button:first-child[kind="secondary"] {
        background: #1E2433;
        color: #E2E8F0;
        border: 1px solid #334155;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 500;
    }
    div.stButton > button:first-child[kind="secondary"]:hover {
        background: #283145;
        border-color: #64748B;
    }
</style>
"""


def render_sidebar(brand: dict):
    """Renders the left navigation panel matching the screenshot."""
    with st.sidebar:
        # User profile badge
        col_avatar, col_user = st.columns([1, 2.5])
        with col_avatar:
            st.image("https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80", width=50)
        with col_user:
            st.markdown("<p style='margin:0; font-weight:600; font-size:0.9rem;'>Agency Admin</p>", unsafe_allow_html=True)
            st.markdown("<span style='background:rgba(59,130,246,0.15); color:#60A5FA; padding:2px 8px; border-radius:10px; font-size:0.7rem;'>Agency Super Admin</span>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("WORKSPACE BRANDS")
        
        # Brand list selector
        st.markdown("""
        <div style="display:flex; flex-direction:column; gap:6px;">
            <div style="padding:7px 10px; border-radius:6px; color:#94A3B8; font-size:0.85rem; display:flex; align-items:center; gap:8px;">
                <span>🔥</span> Apex Fitness
            </div>
            <div style="padding:7px 10px; border-radius:6px; color:#94A3B8; font-size:0.85rem; display:flex; align-items:center; gap:8px;">
                <span>☁️</span> CloudTech Corp
            </div>
            <div style="padding:7px 10px; border-radius:6px; background:#1C1936; border:1px solid #6D28D9; color:#FFFFFF; font-weight:600; font-size:0.85rem; display:flex; align-items:center; gap:8px;">
                <span>🌿</span> Organic Bistro
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1E2430; margin: 18px 0;'>", unsafe_allow_html=True)
        st.caption("MENU")

        # Nav items
        nav_items = [
            ("📊", "Dashboard", True),
            ("📅", "Content Calendar", False),
            ("🖼️", "Media Library", False),
            ("📈", "Analytics", False),
            ("🎨", "Brand Kit", False),
            ("⚙️", "Settings", False),
        ]
        for icon, label, active in nav_items:
            style = "background:#1C1936; color:#A78BFA; font-weight:600;" if active else "color:#94A3B8;"
            st.markdown(
                f"<div style='padding:8px 12px; border-radius:8px; margin-bottom:4px; font-size:0.86rem; cursor:pointer; {style}'>"
                f"{icon} &nbsp; {label}</div>",
                unsafe_allow_html=True
            )


def render_client_view(brand: dict):
    # Inject CSS
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

    # 1. Sidebar Navigation
    render_sidebar(brand)

    # 2. Header Area: Brand title, post progress bar, and Batch Approval
    brand_name = brand.get("name", "Organic Bistro")
    quota = brand.get("monthly_post_quota", 16)
    delivered = 12  # Dynamic in production: calculate from approved/published count
    pct = min(int((delivered / quota) * 100), 100) if quota > 0 else 0

    col_title, col_stats, col_btn = st.columns([2.2, 1.6, 1.1])

    with col_title:
        st.markdown(
            f"""
            <div style="display:flex; flex-direction:column;">
                <h2 style="margin:0; font-size:1.6rem; color:#FFFFFF; font-weight:700;">Social Media Operations & Client Hub</h2>
                <div style="display:flex; align-items:center; gap:6px; margin-top:4px;">
                    <span style="font-size:1.1rem;">🌿</span>
                    <span style="font-weight:600; font-size:0.95rem; color:#F1F5F9;">{brand_name}</span>
                    <span style="font-size:0.75rem; color:#64748B;">▼</span>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    with col_stats:
        st.markdown(
            f"""
            <div class="quota-box">
                <span class="quota-text">{delivered} / {quota} Posts Delivered This Month</span>
                <div class="quota-bar-bg">
                    <div class="quota-bar-fill" style="width: {pct}%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_btn:
        admin_email = st.secrets.get("ADMIN_EMAIL", "alifaiz9111@gmail.com")
        if st.button("Approve All Pending", type="primary", use_container_width=True):
            count = approve_all_pending_posts(brand["id"])
            if count > 0:
                email_batch_approved(admin_email, brand_name, count)
                st.toast(f"Approved {count} pending posts!")
                st.rerun()
            else:
                st.toast("No pending review posts found.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 3. Platform Navigation Tabs
    tab_instagram, tab_linkedin, tab_facebook, tab_twitter = st.tabs([
        "📷  Instagram", 
        "💼  LinkedIn", 
        "👥  Facebook", 
        "🐦  X / Twitter"
    ])

    platforms_map = {
        "📷  Instagram": "Instagram",
        "💼  LinkedIn": "LinkedIn",
        "👥  Facebook": "Facebook",
        "🐦  X / Twitter": "Twitter"
    }

    # Render tab content
    for tab_obj, (tab_label, platform_name) in zip(
        [tab_instagram, tab_linkedin, tab_facebook, tab_twitter], 
        platforms_map.items()
    ):
        with tab_obj:
            posts = get_posts_by_platform(brand["id"], platform_name)

            if not posts:
                st.info(f"No scheduled posts for {platform_name}.")
                continue

            # Render 3-column grid
            cols = st.columns(3)
            for idx, post in enumerate(posts):
                col = cols[idx % 3]
                with col:
                    render_post_card(post, brand, admin_email)


def render_post_card(post: dict, brand: dict, admin_email: str):
    """Renders a single social creative card matching the reference design."""
    status = post.get("status", "review")
    post_type = post.get("post_type", "post").title()
    scheduled_dt = post.get("scheduled_at")
    date_str = ""
    if scheduled_dt:
        if isinstance(scheduled_dt, str):
            try:
                date_str = datetime.fromisoformat(scheduled_dt.replace("Z", "")).strftime("%b %d")
            except Exception:
                date_str = scheduled_dt[:10]
        else:
            date_str = scheduled_dt.strftime("%b %d")

    # Status tag pill styling
    status_badges = {
        "review": '<span class="badge badge-review">Under Review</span>',
        "approved": '<span class="badge badge-approved">Approved</span>',
        "revision_requested": '<span class="badge badge-revision">Revision Requested</span>',
        "published": '<span class="badge badge-approved">Published</span>',
    }
    badge_html = status_badges.get(status, f'<span class="badge">{status}</span>')

    # Card Container
    with st.container():
        # Header: Type and Status
        st.markdown(
            f"""
            <div style="background:#151922; border:1px solid #222938; border-top-left-radius:14px; border-top-right-radius:14px; padding:12px 14px 4px 14px;">
                <div class="post-card-header">
                    <div class="post-card-title">
                        <span>📱</span>
                        <span>Instagram {post_type}</span>
                    </div>
                    <span style="color:#64748B; font-size:1.1rem; cursor:pointer;">•••</span>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Creative Media Section
        media_url = post.get("media_url")
        if media_url:
            signed_url = get_signed_media_url(media_url)
            if signed_url:
                if media_url.lower().endswith((".mp4", ".mov")):
                    st.video(signed_url)
                else:
                    st.image(signed_url, use_container_width=True)
            else:
                st.image("https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80", use_container_width=True)
        else:
            # Fallback aesthetic preview image
            fallback_img = "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80"
            st.image(fallback_img, use_container_width=True)

        # Body: Schedule, Status Badge, Caption, Tags
        caption = post.get("caption", "")
        hashtags = post.get("hashtags", "")

        st.markdown(
            f"""
            <div style="background:#151922; border-left:1px solid #222938; border-right:1px solid #222938; padding:10px 14px 0 14px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="color:#94A3B8; font-size:0.85rem; font-weight:500;">{date_str}</span>
                    {badge_html}
                </div>
                <div style="color:#E2E8F0; font-size:0.84rem; line-height:1.4; margin-bottom:6px;">
                    {caption[:110] + ('...' if len(caption) > 110 else '')}
                </div>
                <div style="color:#818CF8; font-size:0.75rem; margin-bottom:10px;">
                    {hashtags}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Bottom Action / Comment Section
        st.markdown('<div style="background:#151922; border:1px solid #222938; border-bottom-left-radius:14px; border-bottom-right-radius:14px; padding:0 14px 14px 14px;">', unsafe_allow_html=True)
        
        if status == "review":
            with st.expander("💬 Add Revision Note"):
                feedback = st.text_input("Comment...", key=f"fb_in_{post['id']}", placeholder="e.g. Please swap the primary font to bold")
                if st.button("Send Feedback", key=f"btn_fb_{post['id']}", type="secondary"):
                    if feedback.strip():
                        request_post_revision(post["id"], feedback)
                        email_revision_requested(
                            admin_email=admin_email,
                            brand_name=brand.get("name", "Brand"),
                            platform=post.get("platform", "Instagram"),
                            scheduled_date=date_str,
                            feedback=feedback
                        )
                        st.success("Note sent to creative team!")
                        st.rerun()

        elif status == "approved":
            st.button("📥 Download Source Assets", key=f"dl_{post['id']}", type="secondary", use_container_width=True)

        elif status == "revision_requested":
            st.markdown(
                """
                <div class="feedback-bubble">
                    💬 <strong>Client Note:</strong> Please swap the primary font to bold
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)