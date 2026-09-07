"""Kobi Intelligence Hub — API dos dados brutos do dossiê de due diligence.

Retorna o JSON estruturado (dados_factuais + rede_societaria + score
preditivo) pronto pra virar Markdown — a redação do parecer final (LLM)
fica no workflow n8n (ver README.md), não aqui: separação deliberada
(dado factual auditável de um lado, texto interpretativo do outro).

Rodar: uvicorn main:app --reload
"""
from fastapi import FastAPI, HTTPException

from src.dossie.montar import montar_dossie

app = FastAPI(title="Kobi Intelligence Hub", version="0.1.0")


@app.get("/")
def raiz():
    return {"status": "ok", "servico": "kobi-intelligence-hub"}


@app.get("/dossie/{cnpj}")
def dossie(cnpj: str):
    cnpj_limpo = "".join(c for c in cnpj if c.isdigit())
    dados = montar_dossie(cnpj_limpo)
    if dados is None:
        raise HTTPException(status_code=404, detail=f"CNPJ {cnpj_limpo} não encontrado na base.")
    return dados
