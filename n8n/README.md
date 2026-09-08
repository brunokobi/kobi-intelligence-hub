# Workflow n8n — Dossiê de Due Diligence

Workflow id `Z1frcsogDSDtdI2v`, nome "KOBI Intelligence Hub - Dossie Due
Diligence", **ativo**. Editado via API do n8n — se mexer no Code node direto
na UI, cole o resultado de volta aqui (ou exporte de novo via
`GET /api/v1/workflows/Z1frcsogDSDtdI2v`) pra não perder sincronismo.

## Dois webhooks (dois triggers na mesma workflow)

### 1. Gerar/regenerar dossiê — `POST /webhook/kobi-dossie`

Body: `{"cnpj": "00000000000100", "forcar": false}` (`forcar` opcional,
default `false`).

- `forcar: false` + já existe dossiê salvo no cache → devolve o cache
  **na hora** (sem tocar no Ollama).
- `forcar: false` + nunca foi gerado → gera do zero (grafo + score + LLM,
  ~30-90s) e salva no cache.
- `forcar: true` → sempre gera do zero e **sobrescreve** o cache, não
  importa se já existia.

Resposta (sempre as mesmas 4 chaves):
```json
{"cache": true|false, "cnpj": "...", "html": "<div class=\"kobi-doc\">...</div>", "gerado_em": "2026-09-08T17:01:50.15Z"}
```
`cache: true` = o `html` devolvido veio do banco (não gerou nada agora);
`cache: false` = acabou de gerar (e já salvou).

**Nós (ordem, caminho de geração):**
1. **Webhook** (POST `/kobi-dossie`, `responseMode: responseNode`)
2. **Normalizar Entrada** (Code) — limpa o CNPJ (só dígitos), lê `forcar`
3. **Checar Cache** (HTTP GET) — `http://kobi-intelligence-hub:8000/dossie/{cnpj}/cache`
4. **IF Usa Cache** — `cache == true` E `forcar == false`?
   - **TRUE** → vai direto pro nó **Responder** (resposta instantânea, cache)
   - **FALSE** → segue o caminho de geração:
5. **Buscar Dossie** (HTTP GET) — `http://kobi-intelligence-hub:8000/dossie/{cnpj}` (dado bruto: cadastro, sanções, dívida ativa, processos, infrações, rede societária, score)
6. **Montar Prompt** (Code) — `montar_prompt.js`
7. **Chamar Ollama** (HTTP POST) — `llama3.1:8b`, `stream:false`, timeout 120s
8. **Montar HTML Final** (Code) — `montar_html.js` — monta o HTML final **estilizado** (modelo visual definido pelo usuário; CSS escopado sob `.kobi-doc`) deterministicamente a partir do JSON do passo 5, com o parecer do LLM (passo 7) encaixado na seção 4
9. **Salvar Cache** (HTTP POST) — `http://kobi-intelligence-hub:8000/dossie/{cnpj}/cache`, grava o HTML, a resposta já vem no formato final (`cache:false, cnpj, html, gerado_em`)
10. **Responder** (Respond to Webhook, `JSON.stringify($json)`) — recebe tanto do IF-TRUE quanto do passo 9

### 2. Checar se existe dossiê salvo (sem gerar nada) — `GET /webhook/kobi-dossie-cache?cnpj=...`

Usado pelo dashboard **ao abrir o modal de uma empresa**, pra decidir se
mostra um dossiê já salvo (com a data) ou o botão padrão de gerar — nunca
dispara o LLM. Nós: **Webhook Checar Cache** → **Checar Cache (publico)**
(mesmo endpoint `GET /dossie/{cnpj}/cache` do backend) → **Responder Cache
Check**.

## `montar_prompt.js` e `montar_html.js` são a fonte de verdade

Ficam aqui (nesta pasta) — se editar o Code node direto na UI do n8n, cole
o resultado de volta aqui.

## Gotchas

- **Sem tratamento de CNPJ não encontrado** (404 do backend) — o node
  "Buscar Dossie" vai lançar erro e a execução falha. Funciona pro caminho
  feliz (testado com CNPJ real), mas falta um nó IF pra responder
  educadamente "CNPJ não encontrado" em vez de estourar erro 500. Ainda
  pendente (não afeta o caminho de cache, só a geração de um CNPJ novo que
  não existe na base).
- **Timeout do lado do cliente**: geração no `llama3.1:8b` em CPU levou
  ~40-90s no teste real (caminho SEM cache) — qualquer frontend/cliente que
  chamar `/kobi-dossie` sem cache precisa de timeout generoso (120s+). O
  caminho COM cache e o `/kobi-dossie-cache` respondem em <1s.
- Testado de ponta a ponta em 08/09/2026 com CNPJ real
  (`51517957000140`, CYBER SUITE): geração (41-85s) → cache instantâneo
  (0,6s) → regeneração forçada (`forcar:true`, 41s, `gerado_em` novo).
