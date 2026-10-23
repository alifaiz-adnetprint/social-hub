import streamlit as st
from datetime import datetime
from modules.auth import get_supabase
from modules.db import (
    get_all_brands,
    update_brand_permissions,
    create_post,
    upload_creative_asset
)
from modules.mailer import email_access_granted, email_access_revoked

def render_admin_view():
    st.title("🛡️ Admin Command Center")
    client = get_supabase()
    
    tab_brands, tab_upload = st.tabs(["🏢 Client Brands & Access", "📤 Upload Creatives"])
    
    # --- Tab 1: Brand Directory & Access Control ---
    with tab_brands:
        st.subheader("Manage Brand Access & Status")
        brands = get_all_brands()
        
        if not brands:
            st.info("No brands found in database. Create your first brand below.")
        else:
            for b in brands:
                with st.expander(f"📁 {b['name']} ({b['email']})", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Contact:** {b.get('contact_name')}")
                        st.write(f"**Platforms:** {', '.join(b.get('active_platforms', []))}")
                        st.write(f"**Monthly Quota:** {b.get('monthly_post_quota')} posts")
                    
                    with col2:
                        is_active = st.checkbox(
                            "Dashboard Access Active",
                            value=b.get("is_active", False),
                            key=f"active_{b['id']}"
                        )
                        can_edit = st.checkbox(
                            "Can Edit Profile/Logo",
                            value=b.get("can_edit_profile", False),
                            key=f"edit_{b['id']}"
                        )
                        
                        if st.button("Save Permissions", key=f"btn_{b['id']}"):
                            prev_status = b.get("is_active", False)
                            update_brand_permissions(b["id"], is_active, can_edit)
                            
                            # Email notification triggers on state change
                            app_url = st.secrets.get("APP_URL", "http://localhost:8501")
                            if not prev_status and is_active:
                                email_access_granted(b["email"], b["name"], b["contact_name"], app_url)
                                st.toast(f"Access granted & email sent to {b['email']}")
                            elif prev_status and not is_active:
                                email_access_revoked(b["email"], b["name"], b["contact_name"])
                                st.toast(f"Access revoked & email sent to {b['email']}")
                            
                            st.success("Permissions updated successfully!")
                            st.rerun()

        st.markdown("---")
        with st.expander("➕ Register New Brand"):
            with st.form("new_brand_form"):
                new_name = st.text_input("Brand / Company Name")
                new_contact = st.text_input("Contact Person Name")
                new_email = st.text_input("Client Email Address")
                platforms = st.multiselect(
                    "Active Platforms",
                    ["Instagram", "Facebook", "LinkedIn", "YouTube", "Twitter/X"],
                    default=["Instagram"]
                )
                quota = st.number_input("Monthly Post Quota", min_value=1, max_value=100, value=16)
                
                submitted = st.form_submit_button("Create Workspace", type="primary")
                if submitted and new_name and new_email:
                    payload = {
                        "name": new_name,
                        "contact_name": new_contact,
                        "email": new_email,
                        "active_platforms": platforms,
                        "monthly_post_quota": quota,
                        "is_active": False,
                        "can_edit_profile": False
                    }
                    client.table("brands").insert(payload).execute()
                    st.success(f"Workspace '{new_name}' created!")
                    st.rerun()

    # --- Tab 2: Upload Post Creatives ---
    with tab_upload:
        st.subheader("Schedule Post for Client Review")
        brands = get_all_brands()
        
        if not brands:
            st.warning("Please create a brand first.")
            return

        brand_options = {b["name"]: b for b in brands}
        selected_brand_name = st.selectbox("Select Target Brand", list(brand_options.keys()))
        selected_brand = brand_options[selected_brand_name]

        with st.form("upload_creative_form"):
            col_plat, col_type = st.columns(2)
            with col_plat:
                platform = st.selectbox("Platform", selected_brand.get("active_platforms", ["Instagram"]))
            with col_type:
                post_type = st.selectbox("Post Type", ["post", "reel", "carousel", "story"])
            
            caption = st.text_area("Caption Copy", placeholder="Enter the primary post copy...")
            hashtags = st.text_input("Hashtags", placeholder="#branding #design #socialmedia")
            scheduled_date = st.date_input("Scheduled Date", value=datetime.utcnow().date())
            scheduled_time = st.time_input("Scheduled Time", value=datetime.utcnow().time())
            
            file = st.file_uploader("Upload Creative (Image or Video)", type=["jpg", "jpeg", "png", "mp4"])
            
            upload_btn = st.form_submit_button("Upload & Send to Review", type="primary")
            
            if upload_btn:
                if not file:
                    st.error("Please attach a creative file.")
                else:
                    file_bytes = file.read()
                    storage_path = upload_creative_asset(file_bytes, file.name, selected_brand["id"])
                    
                    if storage_path:
                        scheduled_dt = datetime.combine(scheduled_date, scheduled_time)
                        create_post(
                            brand_id=selected_brand["id"],
                            platform=platform,
                            post_type=post_type,
                            caption=caption,
                            hashtags=hashtags,
                            media_path=storage_path,
                            scheduled_at=scheduled_dt
                        )
                        st.success(f"Creative uploaded and submitted for {selected_brand_name} review!")
                    else:
                        st.error("Failed to upload file to storage bucket.")