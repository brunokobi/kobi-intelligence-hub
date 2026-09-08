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

## Status (08/09/2026) — pipeline completo funcionando de ponta a ponta

`POST https://n8n-brunokobi.duckdns.org/webhook/kobi-dossie {"cnpj":"..."}`
devolve o dossiê em Markdown completo (score, cadastro, sanções, dívida
ativa, processos, infrações ambientais, rede societária + endereço
compartilhado, parecer técnico redigido por `llama3.1:8b` via Ollama) —
testado contra CNPJ real. Ver `n8n/README.md` pro detalhe do workflow
(id `Z1frcsogDSDtdI2v`, criado via API do n8n).

Backend deployado em `/opt/kobi-intelligence-hub` na VPS (container na
rede `coolify`, alcançável por `http://kobi-intelligence-hub:8000` de
qualquer outro container nessa rede, inclusive o n8n).

**Frontend**: botão "🔍 Gerar dossiê com IA" integrado direto no dashboard
público existente (`projeto_grande_vitoria_empresas`, `dashboard/
index.html`, modal da empresa) — chama o webhook n8n direto do navegador
(fetch, CORS já liberado), sem precisar de frontend próprio. Testado com
Playwright contra a página real (`empresas.brunokobi.duckdns.org`):
botão → confirm() → loading → dossiê renderizado. Como a página é
pública, tem confirmação antes de rodar (evita clique repetido gerando
carga à toa no Ollama compartilhado).

## Status (08/09/2026) — cache de dossiês + saída em HTML estilizado

Três mudanças pedidas pelo usuário, todas em produção:

1. **Nota metodológica cita e linka o artigo do autor** — `score_preditivo.py`
   expõe `artigo_url` (DOI "todas as versões" do preprint no Zenodo,
   `10.5281/zenodo.21961062`) junto do `ressalva_metodologica`; o
   `montar_html.js` monta o link `<a>` dentro do box de nota metodológica.
2. **Cache de dossiê gerado** — tabela própria `kobi_dossies_cache` (cnpj PK,
   html, gerado_em) no mesmo Postgres do Directus, criada on-demand no
   startup da API (`src/dossie/cache.py`, `garantir_tabela()`). Endpoints:
   `GET/POST /dossie/{cnpj}/cache`. O webhook `/kobi-dossie` aceita
   `{"cnpj","forcar"}` — sem `forcar`, devolve cache se existir (instantâneo)
   ou gera e salva; com `forcar:true`, sempre gera de novo e sobrescreve.
   Novo webhook leve `GET /kobi-dossie-cache?cnpj=...` só checa se existe
   (nunca aciona o LLM) — usado pelo dashboard ao abrir o modal da empresa,
   pra já mostrar o dossiê salvo + data + botão "Regerar" sem precisar
   clicar em nada. Ver `n8n/README.md` pro detalhe dos 2 webhooks/nós.
3. **Saída em HTML estilizado** (não mais Markdown) — `n8n/montar_html.js`
   substitui `montar_markdown.js` (removido), monta o HTML final seguindo o
   modelo visual que o usuário forneceu (`dossie_cyber_suite.html`): CSS
   escopado sob `.kobi-doc` (evita colidir com o CSS do dashboard onde é
   injetado via innerHTML), badges no header, card de score com barra de
   progresso, grid de fatos cadastrais, tabela de sócios, pills de
   grafo/endereço, check-cards de auditoria (✓ verde quando limpo, ⚠ âmbar
   quando tem achado), lista de processos, parecer com banner de conclusão
   colorido por nível de risco. **Simplificação consciente**: o parecer do
   LLM continua sendo 1 parágrafo único (prompt inalterado) em vez da
   estrutura com bullets + "Considerações Finais" do mockup do usuário —
   pedir esse nível de estrutura ao `llama3.1:8b` via Ollama arriscaria
   quebrar o parsing; o resto do template (badges, score, tabelas, checks)
   é 100% fiel ao modelo enviado.

Testado de ponta a ponta com o CNPJ real do exemplo do usuário
(`51517957000140`, CYBER SUITE): geração fresca (~41-85s) → cache
instantâneo (0,6s, mesmo `gerado_em`) → regeneração forçada (novo
`gerado_em`). Screenshot via Playwright confirmou o visual batendo com o
mockup.

**Achado, não é bug meu**: alguns `classe` de `leads_processos_judiciais`
têm capitalização quebrada de vogais acentuadas (ex.: `"AçãO TRABALHISTA -
RITO ORDINáRIO"`) — dado já vem assim do Postgres/DJEN, provavelmente algum
`.upper()` aplicado antes da normalização Unicode em algum ponto da
extração. Fora do escopo daqui (não é o dossiê que gera isso), mas fica
registrado caso apareça de novo.

## Pendente

1. **Tratamento de CNPJ não encontrado** no workflow n8n (hoje estoura
   erro se o backend devolver 404) — ver gotcha em `n8n/README.md`.
2. `.venv` próprio pro backend (em vez de reaproveitar o do
   `experimento2026` só localmente — o container já usa um `requirements.txt`
   isolado, isso é só uma pendência de dev local).
3. Retreino periódico do modelo/scores (`experimento2026/scripts/
   treinar_modelo_final.py`) — hoje é manual; e re-sincronizar
   `models/scores.csv` pro container na VPS depois de cada retreino (hoje
   também manual, via rsync/scp).
4. Rotacionar `DIRECTUS_DB_PASSWORD` e `NEO4J_PASSWORD` — ambos apareceram
   em texto puro na conversa em que este projeto foi criado (07-08/09/2026).
5. Capitalização quebrada em `leads_processos_judiciais.classe` (ver achado
   acima) — não é deste projeto, mas vale investigar em
   `grande_vitoria_empresas_extracao` algum dia.
