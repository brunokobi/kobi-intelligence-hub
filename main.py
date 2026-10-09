"""Kobi Intelligence Hub — API do dossiê de due diligence.

`/dossie/{cnpj}/gerar` monta o dossiê completo (dados factuais +
rede_societaria + score preditivo + parecer via OpenRouter + HTML final) —
substitui o workflow n8n original (Ollama local), migrado quando o backend
foi reconstruído na `vpsrafa` (ver CLAUDE.md). `/dossie/{cnpj}` continua
expondo só o JSON estruturado (sem parecer/HTML), útil pra debug.

`/dossie/{cnpj}/cache` evita reprocessar tudo (grafo + score + LLM) toda
vez que alguém abre uma empresa já consultada.

Rodar: uvicorn main:app --reload
"""
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.dossie import cache as dossie_cache
from src.dossie import parecer_llm
from src.dossie.montar import montar_dossie
from src.dossie.montar_html import montar_html

app = FastAPI(title="Kobi Intelligence Hub", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/dossie/{cnpj}/gerar")
def dossie_gerar(cnpj: str, body: dict = Body(default={})):
    """Substitui o workflow n8n (Webhook `/kobi-dossie`): gera (ou devolve
    do cache) o dossiê completo — dados + parecer via OpenRouter + HTML
    final. `forcar: true` sempre regenera e sobrescreve o cache."""
    cnpj_limpo = _limpar_cnpj(cnpj)
    forcar = bool(body.get("forcar", False))

    if not forcar:
        row = dossie_cache.buscar(cnpj_limpo)
        if row is not None:
            return {"cache": True, "cnpj": cnpj_limpo, "html": row["html"], "gerado_em": row["gerado_em"].isoformat()}

    dados = montar_dossie(cnpj_limpo)
    if dados is None:
        raise HTTPException(status_code=404, detail=f"CNPJ {cnpj_limpo} não encontrado na base.")

    parecer = parecer_llm.gerar_parecer(dados)
    html = montar_html(dados, parecer)
    gerado_em = dossie_cache.salvar(cnpj_limpo, html)
    return {"cache": False, "cnpj": cnpj_limpo, "html": html, "gerado_em": gerado_em}
