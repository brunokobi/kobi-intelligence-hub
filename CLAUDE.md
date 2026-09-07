# Kobi Intelligence Hub — Contexto do Projeto

Ver `README.md` pra visão geral/arquitetura. Este arquivo é o contexto técnico
pra sessões futuras do Claude Code.

## Decisões já travadas (07/09/2026, não reabrir sem motivo novo)

- **Pasta independente** (`/home/bruno/kobi-intelligence-hub`), não é uma
  feature dentro do repo `kobi` — projeto próprio, com seu próprio git.
- **Score preditivo é reaproveitado do `experimento2026`, com nota
  metodológica obrigatória** no dossiê (ver README) — não é pra tirar a
  ressalva pra "deixar o relatório mais limpo".
- Fonte de dado factual (cadastro/sanções/dívida/processos): **Postgres do
  Directus (app `kobi`)**, não o SQLite do `grande_vitoria_empresas_extracao`
  direto — o Directus já é o destino sincronizado diariamente (ver
  `grande_vitoria_empresas_extracao/scripts/sync_kobi_directus.py`), evita
  duplicar lógica de acesso a dado.

## Infra já existente que este projeto reaproveita (não recriar)

- **Postgres do Directus** (`kobi`): host `directus-db` dentro da rede docker
  `coolify` na VPS, só acessível via túnel SSH (`10.0.2.11:5432`, sem porta
  publica) — mesmo padrão de túnel usado em
  `grande_vitoria_empresas_extracao/scripts/sync_kobi_directus.sh`.
  Collections relevantes: `leads_empresas` + `leads_sancoes` +
  `leads_dividas_ativas` + `leads_processos_judiciais` + `leads_socios`.
- **Neo4j** (`experimento2026`): `bolt+s://neo4j.brunokobi.duckdns.org:7687`,
  público (usuário/senha, sem 2FA — risco aceito pelo pesquisador). Nós
  `Empresa`/`Socio`, relação `PARTICIPA_DE` — consulta de "sócio em comum ->
  outra empresa com pendência" é Cypher direto (2-3 hops).
  ⚠️ Esse grafo é **dinâmico** desde 07/09/2026 (atualiza via cron diário,
  ver `experimento2026/CLAUDE.md`) — não é mais o snapshot fixo do preprint.
- **Modelo tabular treinado**: até 07/09/2026 só existia dentro do harness de
  CV, nunca tinha sido persistido. Criado `experimento2026/scripts/
  treinar_modelo_final.py` — treina numa única passada (todo o dataset,
  sem split treino/teste — objetivo aqui é servir, não mais avaliar) e
  salva em `experimento2026/models/tabular_final/`: `modelo.joblib`,
  `colunas.json`, `metadata.json`, e **`scores.csv`** (cnpj → score 0-100
  já calculado pra TODAS as empresas). O serviço aqui **só lê o CSV**
  (`src/dossie/score_preditivo.py`) — não recalcula a HIN por request
  (custaria ~15s toda vez); o custo de recalcular fica concentrado no
  retreino (roda manual por enquanto, `uv run python scripts/
  treinar_modelo_final.py` no experimento2026 — considerar cron quando o
  volume de empresas sancionadas justificar retreinos periódicos).
  **Não precisa de sys.path pro experimento2026 em tempo de request** —
  só em tempo de TREINO (lá, não aqui).
- **n8n**: `https://n8n-brunokobi.duckdns.org` — orquestração do parecer via
  LLM (Ollama, `core-infra-ollama-1:11434`, modelo `phi3:mini` já carregado
  — avaliar se precisa de modelo maior pra qualidade de redação aceitável).
- **VPS**: Oracle Cloud, `129.213.96.52`, chave `~/ssh-key-2026-07-18.key`
  (ver `~/CLAUDE.md`, o guia geral de infra da VPS, pra detalhes de acesso).

## Status (07/09/2026)

**Backend de dados do dossiê funcionando, validado contra o banco real**
(`GET /dossie/{cnpj}` — testado com CNPJ real, 3 sócios, 1 sanção TCEES,
5 processos judiciais, 5 conexões societárias, score 95.05 "Alto Risco").

Arquitetura de fato (mais simples do que o README original previa — nenhum
"MCP Agent Cluster" nem multi-agente de verdade, é um pipeline estruturado
com 3 fontes + 1 chamada de LLM no fim):

```
main.py (FastAPI)
  └─ src/dossie/montar.py (orquestra as 3 fontes abaixo)
       ├─ dados_factuais.py  → Postgres do Directus (psycopg2, túnel SSH em dev)
       ├─ rede_societaria.py → Neo4j (driver oficial, endpoint público)
       └─ score_preditivo.py → lookup em scores.csv (experimento2026)
```

Não roda com o `.venv` próprio ainda — reaproveita
`/home/bruno/experimento2026/.venv` (tem torch/xgboost/pandas já
instalados + fastapi/uvicorn/psycopg2/dotenv adicionados em 07/09). Rodar:

```bash
ssh -f -N -i ~/ssh-key-2026-07-18.key -L 5433:10.0.2.11:5432 ubuntu@129.213.96.52
cd /home/bruno/kobi-intelligence-hub
/home/bruno/experimento2026/.venv/bin/python -m uvicorn main:app --app-dir . --reload
```

**Gotcha achado rodando pela 1ª vez**: `src/` e `src/dossie/` precisam de
`__init__.py` mesmo em Python 3 moderno — sem isso viram "namespace
packages" (PEP 420), e como o `experimento2026` (cujo venv é reaproveitado
aqui) TEM um `src/__init__.py` de verdade (pacote regular), a resolução do
Python encontra o `src` ERRADO (do experimento2026) em vez do daqui, e dá
`ModuleNotFoundError: No module named 'src.dossie'` — mensagem enganosa,
parece que o arquivo não existe, mas existe; é resolução de pacote
colidindo entre os dois projetos que compartilham o mesmo venv.

## Pendente

1. Workflow n8n: recebe payload do `GET /dossie/{cnpj}` → 1 chamada Ollama
   pro parecer final (seção 4 do dossiê) → devolve o Markdown completo.
   Avaliar se `phi3:mini` (já carregado no Ollama da VPS) dá conta da
   qualidade de redação necessária, ou se precisa de modelo maior.
2. Formatar o Markdown final (hoje o endpoint devolve só o JSON estruturado
   — falta a etapa de virar isso no formato do dossiê-exemplo do README).
3. Decidir frontend: painel React novo, ou reaproveitar componente do
   `kobi` existente.
4. `.venv` próprio (em vez de reaproveitar o do `experimento2026`) —
   avaliar quando for deployar em produção/VPS.
