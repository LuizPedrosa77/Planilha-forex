// =========================================================
// ingest-trades
//
// Endpoint público (sem JWT do Supabase) chamado diretamente pelo
// robô MT5 de cada usuário. Autenticação é feita por uma chave de
// API pessoal (header x-api-key), gerada pelo próprio usuário na
// tela de Configurações da planilha.
//
// Deploy precisa da flag --no-verify-jwt (ver README.md), já que
// o MT5 não consegue autenticar com o JWT padrão do Supabase.
// =========================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

async function sha256Hex(input: string): Promise<string> {
  const enc = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", enc);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

interface IncomingTrade {
  ticket?: string | number;       // ID da posição no MT5 (usado como external_id)
  symbol?: string;
  action?: string;                // "Buy" ou "Sell"
  volume?: number;
  open_time?: string;             // ISO 8601
  close_time?: string;            // ISO 8601
  open_price?: number;
  close_price?: number;
  tp?: number;
  sl?: number;
  pips?: number;
  profit?: number;
  swap?: number;
  commission?: number;
  comment?: string;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ ok: false, error: "Método não suportado, use POST" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const apiKey = req.headers.get("x-api-key");
    if (!apiKey) throw new Error("Header x-api-key ausente");

    const keyHash = await sha256Hex(apiKey);
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    const { data: conn, error: connErr } = await supabase
      .from("mt5_connections")
      .select("id, user_id")
      .eq("key_hash", keyHash)
      .maybeSingle();

    if (connErr) throw connErr;
    if (!conn) {
      return new Response(JSON.stringify({ ok: false, error: "Chave de API inválida" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    const body = await req.json();
    const accountId = String(body.account_id ?? "mt5");
    const trades: IncomingTrade[] = Array.isArray(body.trades) ? body.trades : [];

    if (trades.length === 0) {
      return new Response(JSON.stringify({ ok: true, synced: 0 }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    const rows = trades.map((t) => ({
      user_id: conn.user_id,
      external_id: String(t.ticket ?? ""),
      account_id: accountId,
      symbol: t.symbol ?? null,
      action: t.action ?? null,
      lot_type: "lots",
      lot_value: t.volume != null ? Number(t.volume) : null,
      open_time: t.open_time ?? null,
      close_time: t.close_time ?? null,
      open_price: t.open_price ?? null,
      close_price: t.close_price ?? null,
      tp: t.tp ?? null,
      sl: t.sl ?? null,
      pips: t.pips ?? null,
      profit: t.profit ?? null,
      interest: t.swap ?? null,
      commission: t.commission ?? null,
      comment: t.comment ?? null,
      raw: t,
      updated_at: new Date().toISOString(),
    })).filter((r) => r.external_id); // ignora linhas sem ticket válido

    if (rows.length === 0) {
      return new Response(JSON.stringify({ ok: true, synced: 0, message: "Nenhum trade com ticket válido." }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    const { error: upsertErr } = await supabase
      .from("trades")
      .upsert(rows, { onConflict: "user_id,external_id" });
    if (upsertErr) throw upsertErr;

    await supabase
      .from("mt5_connections")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", conn.id);

    return new Response(JSON.stringify({ ok: true, synced: rows.length }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error(err);
    return new Response(JSON.stringify({ ok: false, error: String(err) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
