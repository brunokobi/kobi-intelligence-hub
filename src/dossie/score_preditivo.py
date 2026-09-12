"""Score de risco preditivo — lookup nos CSVs pré-computados pelo
experimento2026 (scripts/treinar_modelo_final.py e
treinar_modelo_final_gnn.py), não recálculo em tempo de request. Ver
README.md: ressalva metodológica é OBRIGATÓRIA em qualquer lugar que exiba
qualquer um desses scores — não remover.

Dois modelos, mostrados lado a lado (não um substituindo o outro):
  - Tabular (XGBoost) — ``scores.csv``, o modelo já em produção desde
    07/09/2026.
  - GNN homogênea (GraphSAGE) — ``scores_gnn.csv``, adicionado em
    12/09/2026. Escolhida a variante homogênea, não HAN/HGT: o preprint
    mostrou a HAN/HGT ("mais sofisticada") perdendo estatisticamente pra
    homogênea em várias rodadas de comparação — não faz sentido servir a
    mais cara/complexa quando a mais simples já não perde.
  Os dois usam o MESMO rótulo (``y_direto``) e a mesma base de treino, mas
  a GNN enxerga a estrutura de rede (sócio comum, endereço comum, vínculo
  político) que o tabular só vê via features agregadas (grau_socio_comum
  etc.) — divergência entre os dois é sinal, não ruído: mostra quando a
  estrutura de rede pesa mais que os atributos isolados da empresa.
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

RESSALVA_GNN = (
    "Score gerado por uma GNN homogênea (GraphSAGE, experimento2026) treinada "
    "na mesma base do modelo tabular, mas usando a estrutura de rede (sócio "
    "em comum, endereço compartilhado, vínculo político) como sinal, não só "
    "atributos isolados da empresa. Mesma ressalva do score tabular: sinal de "
    "priorização para investigação manual, não veredito. Divergir do score "
    "tabular não é erro — é o ponto de comparar os dois: mostra quando a "
    "posição da empresa na rede pesa mais que seus atributos próprios."
)

_cache_tabular: dict[str, float] | None = None
_cache_gnn: dict[str, float] | None = None


def _carregar_csv(caminho) -> dict[str, float]:
    scores = {}
    with open(caminho, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            scores[row["cnpj"]] = float(row["score_0_100"])
    return scores


def _carregar_scores() -> dict[str, float]:
    global _cache_tabular
    if _cache_tabular is None:
        _cache_tabular = _carregar_csv(config.MODELO_DIR / "scores.csv")
    return _cache_tabular


def _carregar_scores_gnn() -> dict[str, float]:
    global _cache_gnn
    if _cache_gnn is None:
        try:
            _cache_gnn = _carregar_csv(config.MODELO_GNN_DIR / "scores_gnn.csv")
        except FileNotFoundError:
            _cache_gnn = {}
    return _cache_gnn


def metadata_modelo() -> dict:
    return json.loads((config.MODELO_DIR / "metadata.json").read_text(encoding="utf-8"))


def _nivel(score: float) -> str:
    if score >= 66:
        return "🔴 Alto Risco"
    if score >= 33:
        return "🟡 Risco Moderado"
    return "🟢 Baixo Risco"


def buscar_score(cnpj: str) -> dict | None:
    """None se o CNPJ não estava no dataset usado pro treino/score (ex.:
    empresa novíssima, ainda não entrou num ciclo de retreino)."""
    score = _carregar_scores().get(cnpj)
    if score is None:
        return None
    return {
        "score_0_100": score,
        "nivel": _nivel(score),
        "ressalva_metodologica": RESSALVA,
        "artigo_url": ARTIGO_URL,
    }


def buscar_score_gnn(cnpj: str) -> dict | None:
    """None se o CNPJ não estava no dataset de treino, OU se
    ``scores_gnn.csv`` ainda não foi gerado/copiado (modelo mais novo que o
    tabular — ver treinar_modelo_final_gnn.py)."""
    score = _carregar_scores_gnn().get(cnpj)
    if score is None:
        return None
    return {
        "score_0_100": score,
        "nivel": _nivel(score),
        "ressalva_metodologica": RESSALVA_GNN,
        "artigo_url": ARTIGO_URL,
    }
