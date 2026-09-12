"""Orquestra as 3 fontes (Postgres/Directus, Neo4j, score pré-computado)
num único dict — a "matéria-prima" do dossiê, antes da redação por LLM
(n8n, ver README.md)."""
from __future__ import annotations

from src.dossie import dados_factuais, rede_societaria, score_preditivo


def montar_dossie(cnpj: str) -> dict | None:
    """None se o CNPJ não existir na base (kobi/Directus)."""
    factual = dados_factuais.montar_dados_factuais(cnpj)
    if factual is None:
        return None

    conexoes = rede_societaria.buscar_conexoes_societarias(cnpj, factual["socios"])
    enderecos = rede_societaria.buscar_enderecos_compartilhados(cnpj)
    centralidade = rede_societaria.buscar_centralidade(cnpj)
    comunidade = rede_societaria.buscar_comunidade(cnpj)
    risco_indireto = rede_societaria.buscar_risco_indireto(cnpj)
    score = score_preditivo.buscar_score(cnpj)
    score_gnn = score_preditivo.buscar_score_gnn(cnpj)

    return {
        "cnpj": cnpj,
        **factual,
        "rede_societaria": conexoes,
        "enderecos_compartilhados": enderecos,
        "centralidade_rede": centralidade,
        "comunidade_rede": comunidade,
        "risco_indireto_rede": risco_indireto,
        "score_preditivo": score,
        "score_gnn": score_gnn,
    }
