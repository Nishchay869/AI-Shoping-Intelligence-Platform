-- Application tables deliberately use auth.users as the single identity source.
create extension if not exists pgcrypto;

create type public.retailer_code as enum ('amazon', 'flipkart', 'myntra');
create type public.alert_kind as enum ('any_drop', 'target_price', 'percentage_drop', 'restock');
create type public.notification_channel as enum ('email', 'push', 'sms', 'whatsapp');

create table public.user_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text check (char_length(display_name) between 1 and 80),
  timezone text not null default 'UTC', created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.retailers (id uuid primary key default gen_random_uuid(), code public.retailer_code not null unique, enabled boolean not null default false, created_at timestamptz not null default now());
create table public.products (id uuid primary key default gen_random_uuid(), title text not null, brand text, model_number text, gtin text, created_at timestamptz not null default now());
create table public.retailer_listings (
  id uuid primary key default gen_random_uuid(), retailer_id uuid not null references public.retailers(id), product_id uuid references public.products(id),
  external_listing_id text not null, url text not null, title text not null, source_payload jsonb not null default '{}', match_confidence numeric(4,3), created_at timestamptz not null default now(),
  unique(retailer_id, external_listing_id)
);
create table public.offers (id uuid primary key default gen_random_uuid(), listing_id uuid not null unique references public.retailer_listings(id) on delete cascade, currency char(3) not null, price_minor bigint not null check(price_minor >= 0), available boolean not null, checked_at timestamptz not null);
create table public.price_observations (id uuid primary key default gen_random_uuid(), offer_id uuid not null references public.offers(id) on delete cascade, price_minor bigint not null check(price_minor >= 0), currency char(3) not null, available boolean not null, observed_at timestamptz not null default now());
create index price_observations_offer_time on public.price_observations(offer_id, observed_at desc);
create table public.watchlists (id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade, name text not null check(char_length(name) <= 80), created_at timestamptz not null default now());
create table public.tracked_items (id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade, offer_id uuid not null references public.offers(id), watchlist_id uuid references public.watchlists(id) on delete set null, created_at timestamptz not null default now(), unique(user_id, offer_id));
create table public.alert_rules (id uuid primary key default gen_random_uuid(), tracked_item_id uuid not null references public.tracked_items(id) on delete cascade, kind public.alert_kind not null, target_price_minor bigint, percentage numeric(5,2), enabled boolean not null default true, created_at timestamptz not null default now());
create table public.notification_preferences (user_id uuid not null references auth.users(id) on delete cascade, channel public.notification_channel not null, enabled boolean not null default false, primary key(user_id, channel));
create table public.notification_events (id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade, fingerprint text not null unique, type text not null, payload jsonb not null, created_at timestamptz not null default now());
create table public.audit_logs (id uuid primary key default gen_random_uuid(), actor_id uuid references auth.users(id) on delete set null, action text not null, entity_type text not null, entity_id uuid, metadata jsonb not null default '{}', created_at timestamptz not null default now());

alter table public.user_profiles enable row level security;
alter table public.watchlists enable row level security;
alter table public.tracked_items enable row level security;
alter table public.alert_rules enable row level security;
alter table public.notification_preferences enable row level security;
alter table public.notification_events enable row level security;

create policy "profiles are private" on public.user_profiles for all using (id = auth.uid()) with check (id = auth.uid());
create policy "watchlists are private" on public.watchlists for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "tracked items are private" on public.tracked_items for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "rules owned through tracked item" on public.alert_rules for all using (exists(select 1 from public.tracked_items t where t.id = tracked_item_id and t.user_id = auth.uid())) with check (exists(select 1 from public.tracked_items t where t.id = tracked_item_id and t.user_id = auth.uid()));
create policy "preferences are private" on public.notification_preferences for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "events are private" on public.notification_events for select using (user_id = auth.uid());
