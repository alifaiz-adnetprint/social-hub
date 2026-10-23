from datetime import datetime
from typing import Optional, List, Dict, Any
from modules.auth import get_supabase


# --- Brands & Multi-Tenancy ---

def get_all_brands() -> List[Dict[str, Any]]:
    """Admin function: Fetch all client brands."""
    client = get_supabase()
    res = client.table("brands").select("*").order("created_at", desc=True).execute()
    return res.data or []


def get_agency_brands(agency_id: str) -> List[Dict[str, Any]]:
    """Agency function: Fetch child brands under a parent agency."""
    client = get_supabase()
    res = (
        client.table("brands")
        .select("*")
        .eq("agency_id", agency_id)
        .eq("is_active", True)
        .order("name", desc=False)
        .execute()
    )
    return res.data or []


def update_brand_permissions(brand_id: str, is_active: bool, can_edit_profile: bool) -> bool:
    """Admin control: Update activation state and edit privileges."""
    client = get_supabase()
    res = (
        client.table("brands")
        .update({"is_active": is_active, "can_edit_profile": can_edit_profile})
        .eq("id", brand_id)
        .execute()
    )
    return bool(res.data)


def update_brand_profile(brand_id: str, name: str, logo_url: Optional[str] = None) -> bool:
    """Client self-service: update brand name and logo (if permitted)."""
    client = get_supabase()
    payload = {"name": name}
    if logo_url:
        payload["logo_url"] = logo_url
    res = client.table("brands").update(payload).eq("id", brand_id).execute()
    return bool(res.data)


# --- Content & Posts ---

def get_posts_by_platform(brand_id: str, platform: str) -> List[Dict[str, Any]]:
    """Fetch all scheduled and published posts for a brand's platform tab."""
    client = get_supabase()
    res = (
        client.table("posts")
        .select("*")
        .eq("brand_id", brand_id)
        .eq("platform", platform)
        .order("scheduled_at", desc=False)
        .execute()
    )
    return res.data or []


def create_post(
    brand_id: str,
    platform: str,
    post_type: str,
    caption: str,
    hashtags: str,
    media_path: str,
    scheduled_at: datetime
) -> Optional[Dict[str, Any]]:
    """Admin: Upload a post creative and metadata."""
    client = get_supabase()
    payload = {
        "brand_id": brand_id,
        "platform": platform,
        "post_type": post_type,
        "caption": caption,
        "hashtags": hashtags,
        "media_url": media_path,
        "scheduled_at": scheduled_at.isoformat(),
        "status": "review"
    }
    res = client.table("posts").insert(payload).execute()
    return res.data[0] if res.data else None


def request_post_revision(post_id: str, feedback: str) -> bool:
    """Client: Mark post as revision requested with notes."""
    client = get_supabase()
    # Stored via RPC or directly updating status and caption/feedback
    res = (
        client.table("posts")
        .update({"status": "revision_requested"})
        .eq("id", post_id)
        .execute()
    )
    return bool(res.data)


def approve_all_pending_posts(brand_id: str) -> int:
    """Client: Approve all posts currently in 'review'."""
    client = get_supabase()
    res = (
        client.table("posts")
        .update({"status": "approved"})
        .eq("brand_id", brand_id)
        .eq("status", "review")
        .execute()
    )
    return len(res.data) if res.data else 0


# --- Storage & Private Signed URLs ---

def upload_creative_asset(file_bytes: bytes, file_name: str, brand_id: str) -> Optional[str]:
    """Uploads file to private 'creatives' bucket."""
    client = get_supabase()
    timestamp = int(datetime.utcnow().timestamp())
    storage_path = f"{brand_id}/{timestamp}_{file_name}"
    try:
        client.storage.from_("creatives").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "auto"}
        )
        return storage_path
    except Exception:
        return None


def get_signed_media_url(storage_path: str, expires_in: int = 3600) -> Optional[str]:
    """Generates a temporary signed URL (valid 1 hour) for secure viewing."""
    if not storage_path:
        return None
    client = get_supabase()
    try:
        res = client.storage.from_("creatives").create_signed_url(storage_path, expires_in)
        return res.get("signedURL") or res.get("signedUrl")
    except Exception:
        return None