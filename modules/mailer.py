import os
import streamlit as st
import resend

resend.api_key = st.secrets.get("RESEND_API_KEY", os.getenv("RESEND_API_KEY", ""))
DEFAULT_FROM = "Social Hub <onboarding@resend.dev>"


def send_email(to_email: str, subject: str, html_content: str) -> tuple[bool, str]:
    """Direct dispatch using Resend API."""
    if not resend.api_key:
        return False, "Missing RESEND_API_KEY"
    try:
        params = {
            "from": DEFAULT_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        res = resend.Emails.send(params)
        return True, str(res)
    except Exception as e:
        return False, str(e)


# --- Email Templates ---

def email_access_granted(to_email: str, brand_name: str, client_name: str, app_url: str):
    """Triggered when workspace is activated."""
    subject = f"🚀 Workspace Activated: {brand_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 580px; margin: auto; padding: 24px; border: 1px solid #e9d5ff; border-radius: 8px;">
        <h2 style="color: #1E1035; margin-top: 0;">Your Dashboard is Ready! 🚀</h2>
        <p style="color: #4b5563;">Hi {client_name},</p>
        <p style="color: #4b5563;">Access for <strong>{brand_name}</strong> has been granted. You can now view your content calendar, review upcoming creatives, and track deliveries.</p>
        <div style="margin: 24px 0;">
            <a href="{app_url}" style="background-color: #7C3AED; color: #ffffff; padding: 12px 22px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                Open Dashboard
            </a>
        </div>
        <p style="color: #9ca3af; font-size: 12px;">If you did not request this access, you can safely ignore this email.</p>
    </div>
    """
    return send_email(to_email, subject, html)


def email_access_revoked(to_email: str, brand_name: str, client_name: str):
    """Triggered when workspace access is unticked."""
    subject = f"⏸️ Workspace Suspended: {brand_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 580px; margin: auto; padding: 24px; border: 1px solid #fee2e2; border-radius: 8px;">
        <h2 style="color: #b91c1c; margin-top: 0;">Workspace Paused ⏸️</h2>
        <p style="color: #4b5563;">Hi {client_name},</p>
        <p style="color: #4b5563;">Access for <strong>{brand_name}</strong> has been temporarily suspended.</p>
        <p style="color: #6b7280; font-size: 13px;">Please reply directly to this email if you need your account reactivated.</p>
    </div>
    """
    return send_email(to_email, subject, html)


def email_revision_requested(admin_email: str, brand_name: str, platform: str, scheduled_date: str, feedback: str):
    """Triggered when a client clicks 'Request Revision'."""
    subject = f"🔄 Revision Requested: {brand_name} ({platform})"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 580px; margin: auto; padding: 24px; border: 1px solid #fed7aa; border-radius: 8px;">
        <h2 style="color: #c2410c; margin-top: 0;">Revision Requested</h2>
        <p style="color: #4b5563;">The client submitted changes for <strong>{brand_name}</strong>.</p>
        <div style="background-color: #fff7ed; padding: 14px; border-left: 4px solid #ea580c; border-radius: 4px; margin: 16px 0;">
            <p style="margin: 0 0 6px 0;"><strong>Platform:</strong> {platform}</p>
            <p style="margin: 0 0 6px 0;"><strong>Date:</strong> {scheduled_date}</p>
            <p style="margin: 0;"><strong>Notes:</strong> <em>"{feedback}"</em></p>
        </div>
    </div>
    """
    return send_email(admin_email, subject, html)


def email_batch_approved(admin_email: str, brand_name: str, approved_count: int):
    """Triggered when a client clicks 'Approve All'."""
    subject = f"✅ Content Batch Approved: {brand_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 580px; margin: auto; padding: 24px; border: 1px solid #bbf7d0; border-radius: 8px;">
        <h2 style="color: #15803d; margin-top: 0;">All Posts Approved! ✅</h2>
        <p style="color: #4b5563;">The client for <strong>{brand_name}</strong> has approved all pending posts in this batch.</p>
        <p style="color: #15803d; font-weight: bold; font-size: 16px;">Total Approved: {approved_count} post(s)</p>
    </div>
    """
    return send_email(admin_email, subject, html)