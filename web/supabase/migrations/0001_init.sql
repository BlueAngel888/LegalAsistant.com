-- LegalAssistant.com — initial schema
-- Run in Supabase: SQL Editor → paste → Run (or `supabase db push`).
--
-- Auth is handled by Clerk. The app talks to Postgres only from the server
-- with the service role key and filters every query by the Clerk user id.
-- RLS is enabled with no policies, so the anon key can read nothing.

create extension if not exists "pgcrypto";

-- ── Enums ──────────────────────────────────────────────────────────────────
do $$ begin
  create type document_status as enum ('uploaded', 'processing', 'analyzed', 'failed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type review_status as enum ('pending', 'approved', 'changes_requested', 'rejected');
exception when duplicate_object then null; end $$;

-- ── Users (mirrors Clerk) ──────────────────────────────────────────────────
create table if not exists users (
  id           text primary key,              -- Clerk user id (user_...)
  email        text,
  full_name    text,
  role         text not null default 'client', -- client | analyst | admin
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- ── Documents ──────────────────────────────────────────────────────────────
create table if not exists documents (
  id              uuid primary key default gen_random_uuid(),
  user_id         text not null references users(id) on delete cascade,
  file_name       text not null,
  storage_path    text not null,               -- path inside the storage bucket
  mime_type       text not null default 'application/pdf',
  size_bytes      bigint not null,
  page_count      int,
  extracted_text  text,                        -- null/empty for scanned PDFs
  text_hash       text,                        -- sha256 of file bytes, used for result caching
  country_code    text not null default 'RO',  -- ISO 3166-1 alpha-2
  document_type   text not null default 'other', -- contract | fine | court_decision | other
  language        text not null default 'ro',  -- language of the analysis
  status          document_status not null default 'uploaded',
  error_message   text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists documents_user_created_idx on documents (user_id, created_at desc);
create index if not exists documents_hash_idx on documents (text_hash);

-- ── Analysis results ───────────────────────────────────────────────────────
create table if not exists analysis_results (
  id               uuid primary key default gen_random_uuid(),
  document_id      uuid not null references documents(id) on delete cascade,
  user_id          text not null references users(id) on delete cascade,
  -- cache key: identical file + jurisdiction + type + language + prompt version
  cache_key        text not null,
  model            text not null,
  prompt_version   text not null,
  result           jsonb not null,             -- structured analysis (see src/lib/analysis-schema.ts)
  usage            jsonb,                      -- token usage incl. cache reads/writes
  cost_usd         numeric(10, 5),
  from_cache       boolean not null default false,
  -- legal analyst verification (Week 5)
  review_status    review_status not null default 'pending',
  reviewer_id      text references users(id),
  reviewer_notes   text,
  reviewed_at      timestamptz,
  created_at       timestamptz not null default now()
);
create index if not exists analysis_document_idx on analysis_results (document_id, created_at desc);
create index if not exists analysis_cache_key_idx on analysis_results (cache_key);

-- ── Jurisdiction data (legislation references per country) ─────────────────
create table if not exists jurisdiction_data (
  id             uuid primary key default gen_random_uuid(),
  country_code   text not null,
  country_name   text not null,
  document_type  text,                         -- null = applies to every document type
  title          text not null,
  reference      text not null,                -- official citation
  summary        text,
  source_url     text,
  verified       boolean not null default false, -- set true after lawyer review
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index if not exists jurisdiction_country_idx on jurisdiction_data (country_code, document_type);

-- ── updated_at triggers ────────────────────────────────────────────────────
create or replace function set_updated_at() returns trigger as $$
begin new.updated_at = now(); return new; end;
$$ language plpgsql;

drop trigger if exists users_updated_at on users;
create trigger users_updated_at before update on users for each row execute function set_updated_at();
drop trigger if exists documents_updated_at on documents;
create trigger documents_updated_at before update on documents for each row execute function set_updated_at();
drop trigger if exists jurisdiction_updated_at on jurisdiction_data;
create trigger jurisdiction_updated_at before update on jurisdiction_data for each row execute function set_updated_at();

-- ── RLS: deny-all for anon/authenticated; the service role bypasses RLS ───
alter table users enable row level security;
alter table documents enable row level security;
alter table analysis_results enable row level security;
alter table jurisdiction_data enable row level security;

-- ── Storage bucket (private) ───────────────────────────────────────────────
insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;
