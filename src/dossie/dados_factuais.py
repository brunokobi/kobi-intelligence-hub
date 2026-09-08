"""Consultas ao Postgres do Directus (app `kobi`) — cadastro, sanções,
dívida ativa, processos judiciais e sócios de uma empresa, por CNPJ.

Fonte de dado factual é o Directus (não o SQLite do
grande_vitoria_empresas_extracao direto) — decisão travada em
CLAUDE.md: já é o destino sincronizado diariamente, evita duplicar lógica
de acesso a dado.
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


def buscar_empresa(cnpj: str) -> dict | None:
    """Dados cadastrais + id interno (lead_id) da empresa. None se o CNPJ
    não existir na base."""
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM leads_empresas WHERE cnpj = %s", (cnpj,))
        row = cur.fetchone()
        return dict(row) if row else None


def buscar_socios(lead_id: int) -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT nome_socio, cpf_parcial, qualificacao, data_entrada, faixa_etaria "
            "FROM leads_socios WHERE lead_id = %s", (lead_id,))
        return [dict(r) for r in cur.fetchall()]


def buscar_sancoes(lead_id: int) -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT tipo, motivo, orgao_sancionador, data_inicio, data_fim, valor_multa, "
            "fundamentacao FROM leads_sancoes WHERE lead_id = %s", (lead_id,))
        return [dict(r) for r in cur.fetchall()]


def buscar_dividas_ativas(lead_id: int) -> list[dict]:
    """`tipo_devedor` importa pra interpretar o valor: quando 'CORRESPONSAVEL'
    ou 'SOLIDARIO', o valor listado é o total da dívida que TODOS os
    corresponsáveis respondem integralmente (responsabilidade solidária) —
    não é dívida "própria" da empresa sozinha. Sem esse campo, o dossiê
    mostraria o mesmo valor gigante pra empresas diferentes sem contexto
    nenhum (achado investigando um caso real em 08/09/2026 — ver
    CLAUDE.md)."""
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT orgao, valor, situacao, data_inscricao, tipo_tributo, ajuizada, tipo_devedor "
            "FROM leads_dividas_ativas WHERE lead_id = %s", (lead_id,))
        return [dict(r) for r in cur.fetchall()]


def buscar_infracoes_ambientais(lead_id: int) -> list[dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT orgao, tipo_infracao, valor_multa, status, data_auto, gravidade, "
            "enquadramento FROM leads_infracoes_ambientais WHERE lead_id = %s", (lead_id,))
        return [dict(r) for r in cur.fetchall()]


def buscar_processos_judiciais(lead_id: int, limite: int = 20) -> list[dict]:
    """Só os `limite` mais recentes por padrão — empresa com histórico
    grande (ex.: milhares de processos) não deve travar o dossiê."""
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT numero_processo, tribunal, classe, assunto, polo, status, "
            "data_ultima_movimentacao, match_confianca FROM leads_processos_judiciais "
            "WHERE lead_id = %s ORDER BY data_ultima_movimentacao DESC NULLS LAST LIMIT %s",
            (lead_id, limite))
        return [dict(r) for r in cur.fetchall()]


def montar_dados_factuais(cnpj: str) -> dict | None:
    """Junta tudo num único dict pronto pra virar seção do dossiê. None se
    o CNPJ não existir na base."""
    empresa = buscar_empresa(cnpj)
    if empresa is None:
        return None
    lead_id = empresa["id"]
    return {
        "empresa": empresa,
        "socios": buscar_socios(lead_id),
        "sancoes": buscar_sancoes(lead_id),
        "dividas_ativas": buscar_dividas_ativas(lead_id),
        "processos_judiciais": buscar_processos_judiciais(lead_id),
        "infracoes_ambientais": buscar_infracoes_ambientais(lead_id),
    }
