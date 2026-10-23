import streamlit as st
from modules.db import (
    get_posts_by_platform,
    get_signed_media_url,
    request_post_revision,
    approve_all_pending_posts
)
from modules.mailer import email_revision_requested, email_batch_approved

def render_client_view(brand: dict):
    st.title(f"📱 {brand.get('name', 'Brand')} Hub")
    
    # Header summary & batch action
    platforms = brand.get("active_platforms", ["Instagram"])
    admin_email = st.secrets.get("ADMIN_EMAIL", "alifaiz9111@gmail.com")
    
    col_info, col_action = st.columns([3, 1])
    with col_info:
        st.write(f"Welcome back, **{brand.get('contact_name', 'Client')}**!")
        st.caption(f"Monthly Quota: {brand.get('monthly_post_quota', 16)} posts")
        
    with col_action:
        if st.button("✅ Approve All Pending", type="primary", use_container_width=True):
            approved_count = approve_all_pending_posts(brand["id"])
            if approved_count > 0:
                email_batch_approved(admin_email, brand["name"], approved_count)
                st.toast(f"Approved {approved_count} post(s)!")
                st.rerun()
            else:
                st.info("No pending review posts found.")

    st.markdown("---")

    # Dynamic platform tabs
    tabs = st.tabs(platforms)
    
    for idx, platform in enumerate(platforms):
        with tabs[idx]:
            posts = get_posts_by_platform(brand["id"], platform)
            
            if not posts:
                st.info(f"No posts scheduled yet for {platform}.")
                continue
            
            for post in posts:
                status_color = {
                    "review": "orange",
                    "approved": "green",
                    "revision_requested": "red",
                    "published": "blue",
                    "draft": "gray"
                }.get(post["status"], "gray")
                
                with st.container():
                    col_media, col_details = st.columns([1, 2])
                    
                    # Media Column
                    with col_media:
                        if post.get("media_url"):
                            signed_url = get_signed_media_url(post["media_url"])
                            if signed_url:
                                if post["media_url"].lower().endswith((".mp4", ".mov")):
                                    st.video(signed_url)
                                else:
                                    st.image(signed_url, use_column_width=True)
                            else:
                                st.caption("🔒 Media access restricted")
                        else:
                            st.caption("No media attached")
                    
                    # Content Details & Feedback Column
                    with col_details:
                        st.markdown(f":{status_color}[● **Status: {post['status'].replace('_', ' ').title()}**]")
                        st.write(f"**Scheduled for:** `{post['scheduled_at']}`")
                        st.write(f"**Type:** `{post.get('post_type', 'post').upper()}`")
                        
                        st.markdown("**Caption:**")
                        st.info(post.get("caption") or "No caption provided.")
                        
                        if post.get("hashtags"):
                            st.caption(f"**Tags:** {post['hashtags']}")
                        
                        # Client Actions
                        if post["status"] == "review":
                            with st.expander("💬 Request Revisions"):
                                feedback = st.text_area("Notes / Changes needed:", key=f"fb_{post['id']}")
                                if st.button("Submit Revision", key=f"sub_{post['id']}"):
                                    if feedback.strip():
                                        request_post_revision(post["id"], feedback)
                                        email_revision_requested(
                                            admin_email=admin_email,
                                            brand_name=brand["name"],
                                            platform=platform,
                                            scheduled_date=str(post["scheduled_at"]),
                                            feedback=feedback
                                        )
                                        st.success("Revision requested. Admin notified!")
                                        st.rerun()
                                    else:
                                        st.error("Please add revision notes.")
                    
                    st.divider()