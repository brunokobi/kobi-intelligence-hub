# Kobi Intelligence Hub — Multi-Agent Due Diligence

Gera um dossiê de due diligence (Markdown) sobre uma empresa da Grande Vitória a
partir de um CNPJ ou razão social — cadastro, sanções, dívida ativa, processos
judiciais, rede societária (conexões via sócio comum) e um parecer redigido por
LLM, incluindo (com ressalva metodológica) um score de risco preditivo.

**Status (08/09/2026): pipeline completo funcionando de ponta a ponta**,
testado contra dado real. `POST https://n8n-brunokobi.duckdns.org/webhook/
kobi-dossie` com `{"cnpj": "..."}` devolve o dossiê em Markdown. Falta só
frontend/UI (hoje só a API + workflow). Ver `CLAUDE.md` pro que falta.

## Por que isso não é um projeto do zero

Amarra 3 projetos já em produção do mesmo dono:

| Peça | Vem de onde | Status |
|---|---:|---|
| Dados cadastrais/sanções/dívida ativa/processos judiciais | `grande_vitoria_empresas_extracao` → Postgres do Directus (`kobi`) | ✅ produção, sincronizado diariamente |
| Rede societária (grafo: sócio comum entre empresas) | `experimento2026` → Neo4j (`neo4j.brunokobi.duckdns.org`) | ✅ produção, atualizado diariamente |
| Score de risco preditivo (modelo tabular XGBoost) | `experimento2026` (baseline treinado pra dissertação) | ⚠️ reaproveitado de pesquisa — ver ressalva abaixo |
| Redação do parecer (LLM) + orquestração | n8n + Ollama, já rodando na VPS | ✅ infra pronta, workflow novo a construir |

## Exemplo de saída (dossiê-alvo)

```
RELATÓRIO DE INTELIGÊNCIA E ANÁLISE DE RISCO
Empresa Alvo: Exemplo Comércio e Serviços Ltda. (CNPJ: 00.000.000/0001-00)
Gerado por: Kobi Intelligence Hub (n8n + FastAPI + MCP Agent Cluster)

1. Resumo Executivo & Índice de Risco
   Score de Risco Preditivo (Modelo Tabular): 78/100 (🔴 Alto Risco)
   ⚠️ Nota metodológica: score gerado por modelo de pesquisa treinado numa
   base com <0,1% de empresas sancionadas. Interpretar como sinal de
   priorização para investigação manual, não como veredito — não substitui
   due diligence presencial nem decisão automatizada de crédito/contrato.
   Status Cadastral: Ativa (Receita Federal / JUCEES)

2. Análise Cadastral e Estrutura Societária
   ...
   Conexões de Grafo Detectadas: Sócio A aparece em outras 3 empresas,
   uma delas com dívida ativa junto à PGFN.

3. Auditoria de Regularidade e Passivos
   Sanções (CEIS/CNEP/...), Dívida Ativa (PGFN), Processos Judiciais (DJEN)

4. Parecer Técnico Consolidado (LLM via Ollama)
```

## Arquitetura (proposta)

```
Frontend (React, painel novo OU rota dentro do kobi existente)
        │  CNPJ/razão social
        ▼
FastAPI (novo serviço, nesta pasta)
        │
        ├─ consulta Postgres do Directus (dados cadastrais/sanções/dívida/processos)
        ├─ consulta Neo4j (rede societária, Cypher)
        ├─ consulta modelo tabular (experimento2026, inferência do XGBoost já treinado)
        └─ chama workflow n8n (webhook) → Ollama redige o parecer final
        │
        ▼
Dossiê em Markdown (retornado ao frontend / MCP / chat)
```

## Ressalva sobre o score preditivo (não remover do relatório)

O modelo vem do `experimento2026` (pesquisa acadêmica, dissertação de mestrado),
treinado contra uma base com taxa-base de sancionadas de ~0,04-0,05% —
mesmo com lift de 18-56x sobre o acaso (ver `experimento2026/README.md`),
isso está longe da confiabilidade de um score de crédito tradicional. Todo
dossiê que exibir o score **precisa** incluir a nota metodológica explícita
(ver exemplo acima) — decisão travada em 07/09/2026, não reabrir sem motivo
novo.
