"""Score de risco preditivo — lookup no CSV pré-computado pelo
experimento2026 (scripts/treinar_modelo_final.py), não recálculo em tempo
de request. Ver README.md: ressalva metodológica é OBRIGATÓRIA em
qualquer lugar que exiba esse score — não remover.
"""
from __future__ import annotations

import csv
import json

from src import config

# DOI "todas as versões" (fixo, sempre aponta pra versão mais recente do
# preprint) — ver experimento2026/README.md, seção "Publicação / Preprint".
ARTIGO_URL = "https://doi.org/10.5281/zenodo.21961062"

RESSALVA = (
    "Score gerado por modelo de pesquisa (XGBoost, experimento2026) treinado "
    "numa base com <0,1% de empresas sancionadas. Interprete como sinal de "
    "priorização para investigação manual, não como veredito — não substitui "
    "due diligence presencial nem decisão automatizada de crédito/contrato. "
    "Metodologia completa, validação estatística (30 folds, teste de "
    "Wilcoxon) e comparação com modelos de grafo (GNN/HAN) publicadas no "
    "preprint do autor (Zenodo, acesso aberto, CC BY 4.0)."
)

_cache: dict[str, float] | None = None


def _carregar_scores() -> dict[str, float]:
    global _cache
    if _cache is None:
        _cache = {}
        with open(config.MODELO_DIR / "scores.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                _cache[row["cnpj"]] = float(row["score_0_100"])
    return _cache


def metadata_modelo() -> dict:
    return json.loads((config.MODELO_DIR / "metadata.json").read_text(encoding="utf-8"))


def buscar_score(cnpj: str) -> dict | None:
    """None se o CNPJ não estava no dataset usado pro treino/score (ex.:
    empresa novíssima, ainda não entrou num ciclo de retreino)."""
    scores = _carregar_scores()
    score = scores.get(cnpj)
    if score is None:
        return None
    if score >= 66:
        nivel = "🔴 Alto Risco"
    elif score >= 33:
        nivel = "🟡 Risco Moderado"
    else:
        nivel = "🟢 Baixo Risco"
    return {
        "score_0_100": score,
        "nivel": nivel,
        "ressalva_metodologica": RESSALVA,
        "artigo_url": ARTIGO_URL,
    }
