# Kobi Intelligence Hub

Dossiê de due diligence (Markdown) sobre qualquer empresa da Grande Vitória (ES),
a partir do CNPJ — cadastro, sanções, dívida ativa, processos judiciais,
infrações ambientais, rede societária (grafo) e um parecer técnico redigido por
IA, incluindo um score de risco preditivo (com ressalva metodológica obrigatória).

**Status: funcionando de ponta a ponta em produção.** Já integrado como botão
**"🔍 Gerar dossiê com IA"** no dashboard público
[empresas.brunokobi.tech](https://empresas.brunokobi.tech) (modal de qualquer
empresa) — sem precisar de frontend próprio.

## Como usar

Via dashboard: abra qualquer empresa em [empresas.brunokobi.tech](https://empresas.brunokobi.tech)
e clique em "Gerar dossiê com IA".

Via API direto:
```bash
curl -X POST "https://n8n-brunokobi.duckdns.org/webhook/kobi-dossie" \
  -H "Content-Type: application/json" \
  -d '{"cnpj": "00000000000100"}'
# -> {"markdown": "...", "cnpj": "..."} — leva ~30-90s (geração em CPU)
```

## Por que isso não é um projeto do zero

Amarra 3 projetos já em produção do mesmo dono, sem duplicar nenhum dado ou lógica:

| Peça | Vem de onde |
|---|---|
| Cadastro, sócios, sanções, dívida ativa, processos judiciais, infrações ambientais | [`grande_vitoria_empresas_extracao`](https://github.com/brunokobi/grande_vitoria_empresas_extracao) → Postgres do Directus, sincronizado diariamente |
| Rede societária (grafo: sócio em comum, endereço compartilhado) | `experimento2026` → Neo4j, atualizado diariamente |
| Score de risco preditivo (XGBoost) | `experimento2026` — modelo da dissertação de mestrado do autor, ver seção abaixo |
| Redação do parecer técnico | n8n + Ollama (`llama3.1:8b`) |

## Arquitetura

```
Dashboard público (botão) ──┐
API direta (curl/webhook) ──┴─► n8n (webhook kobi-dossie)
                                   │
                                   ├─ GET /dossie/{cnpj} ──► FastAPI (este repo)
                                   │                           │
                                   │                           ├─ Postgres do Directus (dados factuais)
                                   │                           ├─ Neo4j (rede societária, Cypher)
                                   │                           └─ scores.csv pré-computado (score preditivo)
                                   │
                                   ├─ Ollama (llama3.1:8b) ──► parecer técnico
                                   └─ monta o Markdown final ──► resposta
```

Deployado como container na VPS (rede Docker `coolify`, ao lado do n8n e do
Directus — sem túnel/porta pública em produção). `n8n/README.md` documenta o
workflow completo (nós, prompt do parecer, gotchas).

## O score preditivo é reaproveitamento de pesquisa real — não é um enfeite

A rede societária e o score do dossiê vêm de um **projeto de pesquisa de
mestrado dedicado** (`experimento2026`, repositório privado), que usa este
mesmo dataset pra investigar se uma empresa conectada a uma empresa já
sancionada — via sócio em comum, mesmo endereço, ou vínculo político do sócio —
tem risco maior de também estar envolvida em irregularidade. O trabalho compara,
com CV estratificada repetida (30 folds) + teste de Wilcoxon, 3 famílias de
modelo (tabular/XGBoost, GNN homogênea, HAN/HGT heterogênea de verdade) sobre
uma Rede Heterogênea de Informação com as 351 mil empresas do dataset.

**Preprint publicado em acesso aberto** (Zenodo, CC BY 4.0, DOI permanente):
[10.5281/zenodo.21961063](https://doi.org/10.5281/zenodo.21961063).

Justamente por vir de um modelo de pesquisa (treinado numa base com <0,1% de
empresas sancionadas), **todo dossiê que exibir o score inclui uma nota
metodológica explícita** — interpretar como sinal de priorização para
investigação manual, nunca como veredito ou substituto de due diligence
presencial/decisão automatizada de crédito.

## Desenvolvimento local

```bash
# túnel SSH pro Postgres do Directus (não tem porta pública)
ssh -f -N -i ~/ssh-key-2026-07-18.key -L 5433:10.0.2.11:5432 ubuntu@129.213.96.52

cp .env.example .env   # preencher com as credenciais reais
uvicorn main:app --reload
# -> http://localhost:8000/dossie/{cnpj}
```

Ver `CLAUDE.md` para detalhes técnicos completos (infra reaproveitada, gotchas
já resolvidos, pendências).
