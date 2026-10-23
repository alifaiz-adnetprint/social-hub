-- 1. Custom Types & Enums
create type user_role as enum ('admin', 'agency', 'client');
create type post_status as enum ('draft', 'review', 'revision_requested', 'approved', 'published');
create type post_type_enum as enum ('post', 'reel', 'carousel', 'story');

-- 2. Agencies Table (Parent workspace for digital marketing companies)
create table if not exists agencies (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    created_at timestamptz default now(),
    deleted_at timestamptz
);

-- 3. Brands Table (Individual client companies)
create table if not exists brands (
    id uuid primary key default gen_random_uuid(),
    agency_id uuid references agencies(id) on delete set null,
    name text not null,
    contact_name text not null,
    email text not null,
    logo_url text,
    active_platforms text[] default array['Instagram'],
    monthly_post_quota int default 16,
    timezone text default 'Asia/Kolkata',
    is_active boolean default false,         -- Access lock: false = pending, true = active
    can_edit_profile boolean default false,  -- Permission lock: true = client can edit name/logo
    created_at timestamptz default now(),
    deleted_at timestamptz
);

-- 4. User Profiles Table (Maps Supabase auth.users to roles and workspaces)
create table if not exists user_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    role user_role not null default 'client',
    agency_id uuid references agencies(id),
    brand_id uuid references brands(id),
    created_at timestamptz default now()
);

-- 5. Posts Table
create table if not exists posts (
    id uuid primary key default gen_random_uuid(),
    brand_id uuid not null references brands(id) on delete cascade,
    agency_id uuid references agencies(id),  -- Denormalized for zero-join security checks
    platform text not null,
    post_type post_type_enum not null default 'post',
    caption text,
    hashtags text,
    media_url text,                          -- Private bucket file path
    scheduled_at timestamptz not null default now(),
    status post_status not null default 'draft',
    campaign_objective text,
    created_at timestamptz default now(),
    deleted_at timestamptz
);

-- 6. Post Media Table (Child table for carousels & multiple assets)
create table if not exists post_media (
    id uuid primary key default gen_random_uuid(),
    post_id uuid not null references posts(id) on delete cascade,
    media_url text not null,
    sort_order int default 1,
    file_type text default 'image'
);

-- 7. Post Events & Feedback History (Audit log)
create table if not exists post_events (
    id uuid primary key default gen_random_uuid(),
    post_id uuid not null references posts(id) on delete cascade,
    user_id uuid references auth.users(id),
    event_type text not null,                -- 'uploaded', 'feedback_submitted', 'approved'
    message text,
    created_at timestamptz default now()
);

-- 8. Setup Private Storage Bucket
insert into storage.buckets (id, name, public) 
values ('creatives', 'creatives', false)
on conflict (id) do nothing;