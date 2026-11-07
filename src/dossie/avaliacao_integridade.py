"""Nota de risco de integridade (0-100, regras explícitas) + due diligence dos
sócios, lidas da API pública do dashboard (projeto_grande_vitoria_empresas,
`GET /empresas/{cnpj}`) — é lá que a nota é calculada, a partir do SQLite
completo (inclui `ocorrencias_socios`, que não é sincronizado pro Directus).

Desde nov/2026 é o ÍNDICE PRINCIPAL do dossiê; os scores preditivos
(tabular/GNN, modelo de pesquisa do experimento2026) ficam como sinais
auxiliares de priorização.
"""
from __future__ import annotations

import os

import requests

API = os.environ.get("DASHBOARD_API_URL", "https://empresas.brunokobi.tech").rstrip("/")


def buscar(cnpj: str) -> dict | None:
    """{'avaliacao': {...}, 'ocorrencias_socios': [...]} ou None se a API
    do dashboard não responder (o dossiê segue só com os scores preditivos)."""
    try:
        r = requests.get(f"{API}/empresas/{cnpj}", timeout=30,
                         headers={"User-Agent": "kobi-intelligence-hub/1.0"})
        r.raise_for_status()
        dados = r.json()
    except (requests.RequestException, ValueError):
        return None
    av = dados.get("avaliacao_integridade")
    if not av:
        return None
    return {"avaliacao": av, "ocorrencias_socios": dados.get("ocorrencias_socios") or []}
