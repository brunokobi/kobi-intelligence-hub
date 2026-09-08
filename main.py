"""Kobi Intelligence Hub — API dos dados brutos do dossiê de due diligence.

Retorna o JSON estruturado (dados_factuais + rede_societaria + score
preditivo) pronto pra virar HTML — a redação do parecer final (LLM) e a
montagem do HTML final ficam no workflow n8n (ver README.md), não aqui:
separação deliberada (dado factual auditável de um lado, texto
interpretativo/apresentação do outro).

Também expõe o cache de dossiês já gerados (`/dossie/{cnpj}/cache`) — o
próprio n8n consulta antes de regerar e grava depois de gerar, pra não
reprocessar tudo (grafo + score + LLM) toda vez que alguém abre uma empresa
já consultada.

Rodar: uvicorn main:app --reload
"""
from fastapi import Body, FastAPI, HTTPException

from src.dossie import cache as dossie_cache
from src.dossie.montar import montar_dossie

app = FastAPI(title="Kobi Intelligence Hub", version="0.1.0")


@app.on_event("startup")
def _startup():
    dossie_cache.garantir_tabela()


def _limpar_cnpj(cnpj: str) -> str:
    return "".join(c for c in cnpj if c.isdigit())


@app.get("/")
def raiz():
    return {"status": "ok", "servico": "kobi-intelligence-hub"}


@app.get("/dossie/{cnpj}")
def dossie(cnpj: str):
    cnpj_limpo = _limpar_cnpj(cnpj)
    dados = montar_dossie(cnpj_limpo)
    if dados is None:
        raise HTTPException(status_code=404, detail=f"CNPJ {cnpj_limpo} não encontrado na base.")
    return dados


@app.get("/dossie/{cnpj}/cache")
def dossie_cache_get(cnpj: str):
    """Sempre 200 (nunca 404) — resposta pensada pra n8n consumir direto
    num IF sem precisar tratar erro. `cache: false` = nunca foi gerado."""
    cnpj_limpo = _limpar_cnpj(cnpj)
    row = dossie_cache.buscar(cnpj_limpo)
    if row is None:
        return {"cache": False, "cnpj": cnpj_limpo, "html": None, "gerado_em": None}
    return {"cache": True, "cnpj": cnpj_limpo, "html": row["html"], "gerado_em": row["gerado_em"].isoformat()}


@app.post("/dossie/{cnpj}/cache")
def dossie_cache_post(cnpj: str, body: dict = Body(...)):
    cnpj_limpo = _limpar_cnpj(cnpj)
    html = body.get("html") or ""
    if not html.strip():
        raise HTTPException(status_code=400, detail="html vazio")
    gerado_em = dossie_cache.salvar(cnpj_limpo, html)
    return {"cache": False, "cnpj": cnpj_limpo, "html": html, "gerado_em": gerado_em}
