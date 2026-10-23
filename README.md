# Social Hub — Client Portal & Social Media Approval Dashboard

A multi-tenant B2B SaaS platform built with **Streamlit**, **Supabase**, and **Resend**. It enables marketing agencies to manage client brand deliverables, upload scheduled creatives to private cloud storage, enforce access controls, and let clients review, approve, or request revisions on content.

---

## Theme & Architecture

* **Frontend:** Streamlit with custom CSS accents (`#7C3AED` primary purple, `#1E1035` deep navy)
* **Database & Auth:** Supabase PostgreSQL with Row Level Security (RLS) & Auth
* **Storage:** Supabase Storage (private `creatives` bucket with signed temporary URLs)
* **Transactional Email:** Resend API for activation alerts, revision requests, and batch approvals

---

## Repository Structure

```text
social-hub/
│
├── .streamlit/
│   ├── config.toml               # Custom UI theme & server limits
│   └── secrets.toml              # API keys & DB credentials (gitignored)
│
├── sql/
│   ├── 01_initial_schema.sql     # Tables, enums, relationships, & bucket setup
│   └── 02_rpc_and_security.sql   # RLS policies & SECURITY DEFINER RPCs
│
├── modules/
│   ├── __init__.py
│   ├── auth.py                   # Session-isolated Supabase auth & guards
│   ├── db.py                     # CRUD operations & signed URL handlers
│   └── mailer.py                 # Resend email templates & triggers
│
├── views/
│   ├── __init__.py
│   ├── admin_view.py             # Brand directory, access toggles, creative uploader
│   └── client_view.py            # Dynamic platform tabs, signed preview, batch approvals
│
├── app.py                        # Entry point, login gatekeeper, & role routing
├── requirements.txt              # Production dependencies
├── .gitignore                    # Credential & cache exclusions
└── README.md