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
    """Fetches user profile and linked brand details from user_profiles table."""
    client = get_supabase()
    try:
        user_response = client.auth.get_user()
        if not user_response or not user_response.user:
            return None

        user_id = user_response.user.id
        res = (
            client.table("user_profiles")
            .select("*, brands(*)")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return res.data if res else None
    except Exception:
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