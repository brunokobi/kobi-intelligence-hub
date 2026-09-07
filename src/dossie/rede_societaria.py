"""Rede societária (sócio em comum → outras empresas) via Neo4j
(experimento2026, dinâmico desde 07/09/2026 — ver experimento2026/CLAUDE.md).

O grafo só tem o rótulo booleano (`sancionada_direto`) como propriedade do
nó Empresa — dívida ativa/processos/etc. das empresas CONECTADAS são
buscados no Postgres (dados_factuais), não duplicados no Neo4j. Separação
de responsabilidade: Neo4j acha a REDE, Postgres detalha cada nó achado.

`chave_socio` do Neo4j (`experimento2026/src/graph/build_hin.py:_chave_socio`)
é `f"{cpf_parcial}|{nome_normalizado}"` — não é o nome exibível. Pra mostrar
"Sócio X" de verdade, recalcula a mesma chave pros sócios da empresa-alvo
(já buscados via Postgres) e casa com o que voltou do Neo4j.
"""
from __future__ import annotations

import re
import unicodedata

from neo4j import GraphDatabase

from src import config


def _normalizar_texto(valor) -> str:
    """Mesma normalização de experimento2026/src/graph/build_hin.py — precisa
    ser idêntica pra `_chave_socio` bater linha por linha."""
    if valor is None:
        return ""
    sem_acento = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.strip().upper())


def _chave_socio(cpf_parcial, nome_socio) -> str:
    cpf = "" if cpf_parcial is None else str(cpf_parcial).strip()
    return f"{cpf}|{_normalizar_texto(nome_socio)}"


def _driver():
    return GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))


def buscar_conexoes_societarias(cnpj: str, socios_alvo: list[dict], limite_empresas: int = 10) -> list[dict]:
    """Pra cada sócio em comum, lista outras empresas (CNPJ + se são
    sancionadas no grafo) conectadas ao CNPJ alvo. `socios_alvo` é a lista
    já buscada via Postgres (dados_factuais.buscar_socios) — usada só pra
    resolver o nome exibível de cada `chave_socio` que o Neo4j devolve.
    """
    chave_para_nome = {_chave_socio(s.get("cpf_parcial"), s.get("nome_socio")): s.get("nome_socio")
                        for s in socios_alvo}

    query = """
        MATCH (alvo:Empresa {id: $cnpj})<-[:PARTICIPA_DE]-(s:Socio)-[:PARTICIPA_DE]->(outra:Empresa)
        WHERE outra.id <> $cnpj
        RETURN outra.id AS cnpj_conectada, outra.sancionada_direto AS sancionada,
               collect(DISTINCT s.id) AS chaves_socio
        LIMIT $limite
    """
    with _driver() as driver, driver.session(database=config.NEO4J_DATABASE) as session:
        resultado = session.run(query, cnpj=cnpj, limite=limite_empresas)
        conexoes = []
        for row in resultado:
            nomes = [chave_para_nome.get(k, "(sócio não identificado)") for k in row["chaves_socio"]]
            conexoes.append({
                "cnpj_conectada": row["cnpj_conectada"],
                "sancionada_direto": bool(row["sancionada"]) if row["sancionada"] is not None else False,
                "socios_em_comum": nomes,
            })
    return conexoes
