-- 1. Helper Functions to get current user details fast
create or replace function get_auth_role()
returns user_role
language sql stable
as $$
  select role from user_profiles where id = auth.uid();
$$;

create or replace function get_auth_brand_id()
returns uuid
language sql stable
as $$
  select brand_id from user_profiles where id = auth.uid();
$$;

create or replace function get_auth_agency_id()
returns uuid
language sql stable
as $$
  select agency_id from user_profiles where id = auth.uid();
$$;

-- 2. Enable Row-Level Security (RLS)
alter table agencies enable row level security;
alter table brands enable row level security;
alter table user_profiles enable row level security;
alter table posts enable row level security;
alter table post_media enable row level security;
alter table post_events enable row level security;

-- 3. RLS Read Policies (SELECT)

-- Agencies: Admin sees all; Agency sees only their record
create policy "agencies_read_policy" on agencies
for select using (
    get_auth_role() = 'admin' or id = get_auth_agency_id()
);

-- Brands: Admin sees all; Agency sees all child brands; Client sees only their brand
create policy "brands_read_policy" on brands
for select using (
    get_auth_role() = 'admin' 
    or (get_auth_role() = 'agency' and agency_id = get_auth_agency_id())
    or (get_auth_role() = 'client' and id = get_auth_brand_id())
);

-- Posts: Admin sees all; Agency sees child brands' posts; Client sees active brand's posts
create policy "posts_read_policy" on posts
for select using (
    get_auth_role() = 'admin'
    or (get_auth_role() = 'agency' and agency_id = get_auth_agency_id())
    or (get_auth_role() = 'client' and brand_id = get_auth_brand_id())
);

-- User Profiles: Self read or Admin read
create policy "profiles_read_policy" on user_profiles
for select using (
    get_auth_role() = 'admin' or id = auth.uid()
);

-- 4. Storage Security Policies for 'creatives' bucket
create policy "creatives_admin_all" on storage.objects
for all using (
    bucket_id = 'creatives' and get_auth_role() = 'admin'
);

create policy "creatives_client_read" on storage.objects
for select using (
    bucket_id = 'creatives'
);

-- 5. Atomic RPC Functions for Safe Client Actions

-- Client Action: Request revision with feedback
create or replace function submit_post_revision(p_post_id uuid, p_feedback text)
returns void
language plpgsql
security definer
as $$
declare
    v_brand_id uuid;
begin
    select brand_id into v_brand_id from posts where id = p_post_id;
    
    if (get_auth_role() != 'admin' and get_auth_brand_id() != v_brand_id) then
        raise exception 'Unauthorized to edit this post';
    end if;

    update posts 
    set status = 'revision_requested' 
    where id = p_post_id;

    insert into post_events (post_id, user_id, event_type, message)
    values (p_post_id, auth.uid(), 'feedback_submitted', p_feedback);
end;
$$;

-- Client Action: Approve all pending posts in batch
create or replace function approve_pending_posts(p_brand_id uuid)
returns int
language plpgsql
security definer
as $$
declare
    v_count int;
begin
    if (get_auth_role() != 'admin' 
        and get_auth_brand_id() != p_brand_id 
        and (get_auth_role() = 'agency' and (select agency_id from brands where id = p_brand_id) != get_auth_agency_id())) then
        raise exception 'Unauthorized access to brand';
    end if;

    with updated as (
        update posts 
        set status = 'approved'
        where brand_id = p_brand_id and status = 'review'
        returning id
    )
    select count(*) into v_count from updated;

    insert into post_events (post_id, user_id, event_type, message)
    select id, auth.uid(), 'approved', 'Approved in batch'
    from posts
    where brand_id = p_brand_id and status = 'approved';

    return v_count;
end;
$$;