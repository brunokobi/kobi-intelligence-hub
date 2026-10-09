# Kobi Intelligence Hub

Dossiê de due diligence (HTML estilizado) sobre qualquer empresa da Grande
Vitória (ES), a partir do CNPJ — cadastro, sanções, dívida ativa, processos
judiciais, infrações ambientais, PEP (pessoas expostas politicamente), rede
societária (grafo, incluindo risco geográfico por município) e um parecer
técnico redigido por IA, incluindo um score de risco preditivo (com ressalva
metodológica obrigatória, linkando o preprint do autor). Todo dossiê gerado
fica salvo (cache no Postgres) — reabrir a mesma empresa mostra o dossiê já
pronto, com a data de geração e um botão pra regerar.

**Status: funcionando de ponta a ponta em produção** (VPS `vpsrafa`,
Frankfurt). Já integrado como botão **"🔍 Gerar dossiê com IA"** no dashboard
público [empresas.brunokobi.tech](https://empresas.brunokobi.tech) (modal de
qualquer empresa) — sem precisar de frontend próprio.

## Como usar

Via dashboard: abra qualquer empresa em [empresas.brunokobi.tech](https://empresas.brunokobi.tech)
e clique em "Gerar dossiê com IA".

Via API direto (FastAPI deste repo, sem n8n no meio desde a migração pra
`vpsrafa` — ver `CLAUDE.md`):
```bash
curl -X POST "http://<vpsrafa>:8001/dossie/00000000000100/gerar" \
  -H "Content-Type: application/json" \
  -d '{"forcar": false}'
# -> {"cache": bool, "cnpj": "...", "html": "...", "gerado_em": "..."}
# forcar:false + já tem cache -> resposta instantânea (não chama o LLM)
# forcar:false + nunca gerou, ou forcar:true -> gera do zero (~30-90s) e salva

# só checar se já existe (nunca gera nada):
curl "http://<vpsrafa>:8001/dossie/00000000000100/cache"
```

## Por que isso não é um projeto do zero

Amarra 3 projetos já em produção do mesmo dono, sem duplicar nenhum dado ou lógica:

| Peça | Vem de onde |
|---|---|
| Cadastro, sócios, sanções, dívida ativa, processos judiciais, infrações ambientais, PEP | [`grande_vitoria_empresas_extracao`](https://github.com/brunokobi/grande_vitoria_empresas_extracao) → Postgres do Directus, sincronizado diariamente |
| Rede societária (grafo: sócio em comum, endereço compartilhado, centralidade, comunidade, risco geográfico por município) | `experimento2026` → Neo4j, atualizado diariamente |
| Score de risco preditivo (XGBoost + GNN) | `experimento2026` — modelo da dissertação de mestrado do autor, ver seção abaixo |
| Redação do parecer técnico | OpenRouter (LLM free tier), chamado direto pelo backend |

## Arquitetura

```
Dashboard público (botão) ──┐
API direta (curl) ──────────┴─► POST /dossie/{cnpj}/gerar ──► FastAPI (este repo)
                                                                  │
                                                                  ├─ Postgres do Directus (dados factuais, PEP)
                                                                  ├─ Neo4j (rede societária + risco geográfico, Cypher)
                                                                  ├─ scores.csv pré-computado (score preditivo)
                                                                  ├─ OpenRouter (LLM) ──► parecer técnico
                                                                  └─ monta o HTML final ──► resposta (+ cache no Postgres)
```

Deployado como container na VPS `vpsrafa` (Frankfurt), rede Docker própria
(`kobi`), ao lado do Postgres/Neo4j deste projeto. Não depende mais de n8n
nem de Ollama — essa migração aconteceu junto da reconstrução do backend na
`vpsrafa` (ver `CLAUDE.md` pra histórico e detalhes de infra).

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
ssh -f -N -i ~/ssh-key-2026-07-18.key -L 5433:10.0.2.11:5432 ubuntu@130.61.140.66

cp .env.example .env   # preencher com as credenciais reais
uvicorn main:app --reload
# -> http://localhost:8000/dossie/{cnpj}
# -> POST http://localhost:8000/dossie/{cnpj}/gerar  (dossiê completo, parecer incluso)
```

Ver `CLAUDE.md` para detalhes técnicos completos (infra reaproveitada, gotchas
já resolvidos, pendências).
