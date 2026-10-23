import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any


def get_supabase() -> Client:
    """Returns a per-session Supabase client to prevent cross-user token contamination."""
    if "supabase_client" not in st.session_state:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


def get_current_user_profile() -> Optional[Dict[str, Any]]:
<<<<<<< HEAD
    """Fetches user profile and linked brand details from user_profiles table."""
=======
    """Fetches user profile and linked brand details safely."""
>>>>>>> 4a485fb (.)
    client = get_supabase()
    try:
        user_response = client.auth.get_user()
        if not user_response or not user_response.user:
            return None

        user_id = user_response.user.id
<<<<<<< HEAD
        res = (
            client.table("user_profiles")
            .select("*, brands(*)")
=======
        
        # 1. Fetch user profile directly
        res = (
            client.table("user_profiles")
            .select("*")
>>>>>>> 4a485fb (.)
            .eq("id", user_id)
            .single()
            .execute()
        )
<<<<<<< HEAD
        return res.data if res else None
    except Exception:
=======
        if not res or not res.data:
            return None
        
        profile = res.data
        
        # 2. Attach brand details if a brand_id exists
        brand_id = profile.get("brand_id")
        if brand_id:
            brand_res = (
                client.table("brands")
                .select("*")
                .eq("id", brand_id)
                .single()
                .execute()
            )
            profile["brands"] = brand_res.data if brand_res else None
        else:
            profile["brands"] = None

        return profile
    except Exception as e:
        st.sidebar.error(f"Auth error: {e}")
>>>>>>> 4a485fb (.)
        return None


def sign_in(email: str, password: str) -> tuple[bool, str]:
    """Authenticates the user and sets session state."""
    client = get_supabase()
    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.user = res.user
            return True, "Success"
        return False, "Invalid credentials."
    except Exception as e:
        return False, str(e)


def sign_out():
    """Logs out user and resets session states."""
    client = get_supabase()
    try:
        client.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    if "supabase_client" in st.session_state:
        del st.session_state["supabase_client"]