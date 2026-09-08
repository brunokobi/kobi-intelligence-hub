# Workflow n8n — Dossiê de Due Diligence

Criado via API do n8n em 08/09/2026 (workflow id `Z1frcsogDSDtdI2v`, nome
"KOBI Intelligence Hub - Dossie Due Diligence", **ativo**).

**Webhook**: `POST https://n8n-brunokobi.duckdns.org/webhook/kobi-dossie`
Body: `{"cnpj": "00000000000100"}`
Resposta (pode levar 30-90s — geração no Ollama, CPU): `{"markdown": "...", "cnpj": "..."}`

## Nós (em ordem)

1. **Webhook** (POST `/kobi-dossie`, `responseMode: responseNode`)
2. **Buscar Dossie** — `GET http://kobi-intelligence-hub:8000/dossie/{{ $json.body.cnpj }}`
   (container na mesma rede `coolify`, sem túnel/porta pública)
3. **Montar Prompt** (Code) — `montar_prompt.js` — monta o prompt do parecer
   a partir do JSON do passo 2 (só resumo textual, nunca manda o payload
   bruto pro LLM)
4. **Chamar Ollama** — `POST http://ollama:11434/api/generate`,
   `model: llama3.1:8b`, `stream: false`, timeout 120s
5. **Montar Markdown Final** (Code) — `montar_markdown.js` — monta as
   seções 1-3 do dossiê **deterministicamente** a partir do JSON do passo 2
   (nunca do texto do LLM) + a seção 4 (parecer) com o texto do passo 4
6. **Responder** (Respond to Webhook, JSON)

`montar_prompt.js` e `montar_markdown.js` aqui são a fonte de verdade — se
editar o Code node direto na UI do n8n, cole o resultado de volta aqui
(ou exporte o workflow de novo via `GET /api/v1/workflows/Z1frcsogDSDtdI2v`).

## Gotchas

- **Sem tratamento de CNPJ não encontrado** (404 do backend) — o node
  "Buscar Dossie" vai lançar erro e a execução falha. Funciona pro caminho
  feliz (testado com CNPJ real), mas falta um nó IF pra responder
  educadamente "CNPJ não encontrado" em vez de estourar erro 500. Próximo
  passo.
- **Timeout do lado do cliente**: geração no `llama3.1:8b` em CPU levou
  ~60-90s no teste real — qualquer frontend/cliente que chamar esse
  webhook precisa de timeout generoso (120s+), não o padrão de bibliotecas
  HTTP (que costuma ser 10-30s).
- Testado de ponta a ponta em 08/09/2026 com CNPJ real
  (`04545492000151`) — dossiê completo gerado corretamente (score,
  sanção TCEES, 6 processos judiciais, rede societária, endereço hub de
  alto grau suprimido, parecer coerente do LLM).
