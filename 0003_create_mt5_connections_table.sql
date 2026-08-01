-- =========================================================
-- Tabela de conexões MT5 (chave pessoal por usuário/robô)
-- =========================================================
-- Cada usuário pode gerar 1+ chaves (ex: uma por conta MT5 que
-- quiser conectar). O robô (EA) usa essa chave em vez de um
-- login/senha, então nunca precisamos guardar credenciais de
-- corretora nem de terceiros.

create table if not exists public.mt5_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  label text not null default 'Conta MT5',

  -- nunca guardamos a chave em texto puro, só o hash (SHA-256).
  -- a chave real só existe no momento em que é gerada, mostrada
  -- uma única vez para o usuário copiar.
  key_hash text not null unique,

  created_at timestamptz not null default now(),
  last_sync_at timestamptz
);

alter table public.mt5_connections enable row level security;

create policy "mt5_connections_select_own"
  on public.mt5_connections for select
  using (auth.uid() = user_id);

create policy "mt5_connections_insert_own"
  on public.mt5_connections for insert
  with check (auth.uid() = user_id);

create policy "mt5_connections_delete_own"
  on public.mt5_connections for delete
  using (auth.uid() = user_id);

-- Observação: a Edge Function `ingest-trades` usa a service_role key
-- (ignora RLS) para autenticar pela key_hash e gravar os trades em
-- nome do usuário correto, sem precisar de sessão de login ativa.
