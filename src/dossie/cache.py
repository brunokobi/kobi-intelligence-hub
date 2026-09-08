"""Cache de dossiês já gerados (HTML final, pós-LLM) — evita reprocessar
tudo (grafo + score + chamada ao Ollama, ~30-90s) toda vez que alguém abre
uma empresa já consultada. Tabela própria no mesmo Postgres do Directus
(`kobi_dossies_cache`), fora do schema gerenciado pelo Directus (não é uma
collection `leads_*` sincronizada pela extração — é estado próprio deste
serviço), criada sob demanda no startup da API.
"""
from __future__ import annotations

import psycopg2
import psycopg2.extras

from src import config


def _conn():
    return psycopg2.connect(
        host=config.PG_HOST, port=config.PG_PORT, dbname=config.PG_DBNAME,
        user=config.PG_USER, password=config.PG_PASSWORD,
    )


def garantir_tabela() -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS kobi_dossies_cache ("
            "cnpj TEXT PRIMARY KEY, "
            "html TEXT NOT NULL, "
            "gerado_em TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        conn.commit()


def buscar(cnpj: str) -> dict | None:
    """None se nunca foi gerado um dossiê pra esse CNPJ."""
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT html, gerado_em FROM kobi_dossies_cache WHERE cnpj = %s", (cnpj,))
        row = cur.fetchone()
        return dict(row) if row else None


def salvar(cnpj: str, html: str) -> str:
    """Upsert (grava ou regrava por cima) — retorna gerado_em em ISO 8601."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kobi_dossies_cache (cnpj, html, gerado_em) VALUES (%s, %s, now()) "
            "ON CONFLICT (cnpj) DO UPDATE SET html = EXCLUDED.html, gerado_em = now() "
            "RETURNING gerado_em",
            (cnpj, html),
        )
        gerado_em = cur.fetchone()[0]
        conn.commit()
        return gerado_em.isoformat()
