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
- **Modelo tabular treinado**: `experimento2026/src/models/tabular_baseline.py`
  + artefato salvo (checar `experimento2026/docs/` ou `scripts/` pra achar
  onde o modelo treinado foi persistido — não verificado ainda se foi
  salvo em disco (`.pkl`/`.json` do XGBoost) ou só roda no harness de
  avaliação; se não foi persistido, precisa re-treinar uma vez e salvar
  antes de servir inferência em produção).
- **n8n**: `https://n8n-brunokobi.duckdns.org` — orquestração do parecer via
  LLM (Ollama, `core-infra-ollama-1:11434`, modelo `phi3:mini` já carregado
  — avaliar se precisa de modelo maior pra qualidade de redação aceitável).
- **VPS**: Oracle Cloud, `129.213.96.52`, chave `~/ssh-key-2026-07-18.key`
  (ver `~/CLAUDE.md`, o guia geral de infra da VPS, pra detalhes de acesso).

## Pendente (nada implementado ainda)

1. Confirmar se o modelo tabular do `experimento2026` foi persistido em
   disco; se não, treinar+salvar uma versão servível.
2. Desenhar o schema do endpoint FastAPI (`POST /dossie/{cnpj}` ou similar).
3. Escrever a query Cypher de rede societária (sócio em comum → empresa com
   pendência) e validar contra o grafo real.
4. Montar o workflow n8n: recebe payload já montado pelo FastAPI → 1 chamada
   Ollama pro parecer final → devolve o Markdown.
5. Decidir frontend: painel React novo, ou reaproveitar componente do
   `kobi` existente (ver README, opção descartada nesta rodada mas não
   necessariamente pra sempre).
