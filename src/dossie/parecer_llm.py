"""Redação do parecer técnico final via LLM — porta de `n8n/montar_prompt.js`
(prompt) para Python, chamando o OpenRouter (free tier) no lugar do
Ollama/n8n. Mesmo prompt, mesma regra de negócio; só o transporte mudou
(chamada direta em vez de workflow n8n)."""
from __future__ import annotations

import requests

from src import config

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _montar_prompt(d: dict) -> str:
    emp = d["empresa"]
    linhas = []
    nome = emp["razao_social"] + (f" ({emp['nome_fantasia']})" if emp.get("nome_fantasia") else "")
    linhas.append(f"Empresa: {nome}")
    linhas.append(f"CNPJ: {d['cnpj']}")
    situacao = "Ativa" if emp.get("situacao_cadastral") == "02" else emp.get("situacao_cadastral")
    linhas.append(f"Situação cadastral: {situacao}")
    linhas.append(f"Município: {emp.get('municipio')}")
    socios_nomes = ", ".join(s["nome_socio"] for s in d.get("socios", [])) or "nenhum registrado"
    linhas.append(f"Sócios: {socios_nomes}")

    sancoes = d.get("sancoes", [])
    if sancoes:
        desc = "; ".join(f"{s['tipo']} - {s['orgao_sancionador']}" for s in sancoes)
        linhas.append(f"Sanções administrativas ({len(sancoes)}): {desc}")

    vinculos_politicos = d.get("vinculos_politicos", [])
    if vinculos_politicos:
        peps_vistos = set()
        peps = []
        for v in vinculos_politicos:
            if v.get("fonte") != "PEP":
                continue
            chave = (v.get("nome_socio_vinculado"), v.get("cargo_ou_funcao"), v.get("orgao_ou_partido"), v.get("ano"))
            if chave in peps_vistos:
                continue
            peps_vistos.add(chave)
            peps.append(v)
        if peps:
            desc_pep = "; ".join(
                f"{v['nome_socio_vinculado']} ({v.get('cargo_ou_funcao') or 'cargo não especificado'}, "
                f"{v.get('orgao_ou_partido') or 'órgão não especificado'})" for v in peps
            )
            linhas.append(
                f"PEP -- Pessoa(s) Exposta(s) Politicamente entre os sócios ({len(peps)}): {desc_pep}. "
                f"NÃO é sanção nem indica irregularidade -- é só sinalizador de exposição pública "
                f"(cargo/função relevante nos últimos 5 anos), útil pra due diligence de conflito de "
                f"interesse/conexão política, não deve ser tratado como red flag por si só."
            )

    dividas = d.get("dividas_ativas", [])
    if dividas:
        principais = [x for x in dividas if x.get("tipo_devedor") == "PRINCIPAL"]
        corresponsaveis = [x for x in dividas if x.get("tipo_devedor") != "PRINCIPAL"]
        if principais:
            total = sum(x.get("valor") or 0 for x in principais)
            linhas.append(
                f"Dívida ativa PRÓPRIA (devedor principal, {len(principais)} registro(s)): "
                f"total R$ {total:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
            )
        if corresponsaveis:
            total = sum(x.get("valor") or 0 for x in corresponsaveis)
            total_fmt = f"{total:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
            linhas.append(
                f"Dívida ativa por RESPONSABILIDADE SOLIDÁRIA/CORRESPONSÁVEL "
                f"({len(corresponsaveis)} registro(s), dívida de outro devedor pela qual esta "
                f"empresa também responde legalmente): total R$ {total_fmt} — NÃO é dívida "
                f"própria, avaliar com contexto"
            )

    processos = d.get("processos_judiciais", [])
    if processos:
        linhas.append(f"Processos judiciais: {len(processos)} encontrados")

    infracoes = d.get("infracoes_ambientais", [])
    if infracoes:
        linhas.append(f"Infrações ambientais (IBAMA/IEMA): {len(infracoes)}")

    rede = d.get("rede_societaria") or []
    conexoes_sancionadas = [c for c in rede if c.get("sancionada_direto")]
    if conexoes_sancionadas:
        cnpjs = ", ".join(c["cnpj_conectada"] for c in conexoes_sancionadas)
        linhas.append(
            f"Rede societária: sócio em comum com {len(conexoes_sancionadas)} empresa(s) "
            f"SANCIONADA(S) (CNPJ: {cnpjs})"
        )
    elif rede:
        linhas.append(f"Rede societária: sócio em comum com {len(rede)} outra(s) empresa(s), nenhuma sancionada diretamente")

    enderecos = d.get("enderecos_compartilhados")
    if enderecos and enderecos.get("hub_alto_grau"):
        linhas.append("Endereço: prédio/condomínio comercial de alto volume (não avaliado individualmente)")
    elif enderecos and enderecos.get("empresas"):
        linhas.append(f"Endereço compartilhado com {len(enderecos['empresas'])} outra(s) empresa(s)")

    score = d.get("score_preditivo")
    if score:
        linhas.append(f"Score de risco preditivo tabular (modelo estatístico, XGBoost): {score['score_0_100']}/100 ({score['nivel']})")
    score_gnn = d.get("score_gnn")
    if score_gnn:
        linhas.append(f"Score de risco preditivo por rede (GNN, usa a estrutura de conexões societárias): {score_gnn['score_0_100']}/100 ({score_gnn['nivel']})")

    centralidade = d.get("centralidade_rede")
    if centralidade:
        linhas.append(
            f"Centralidade na rede societária (comparado a todas as empresas do dataset): "
            f"percentil {centralidade['pagerank_percentil']}% em importância geral (PageRank) e "
            f"percentil {centralidade['betweenness_percentil']}% como \"ponte\" entre grupos "
            f"distintos (betweenness) -- quanto mais alto, mais central/conectada é a empresa na rede."
        )
    comunidade = d.get("comunidade_rede")
    if comunidade and comunidade.get("pct_sancionada") is not None:
        linhas.append(
            f"Comunidade na rede (cluster #{comunidade['id_comunidade']}, detecção automática de "
            f"agrupamento/Louvain): {comunidade['tamanho']} empresa(s) no mesmo cluster, das quais "
            f"{comunidade['pct_sancionada']}% têm sanção administrativa direta."
        )
    risco_geografico = d.get("risco_geografico")
    if risco_geografico:
        linhas.append(
            f"Risco geográfico (município): {risco_geografico['pct_sancionada']}% das "
            f"{risco_geografico['total_empresas']} empresas do mesmo município têm sanção "
            f"administrativa direta (percentil {risco_geografico['percentil']}% comparado aos outros "
            f"municípios da Grande Vitória) -- contexto estrutural de onde a empresa está situada, "
            f"não uma característica da empresa em si."
        )

    risco_indireto = d.get("risco_indireto_rede") or []
    if risco_indireto:
        min_saltos = min(r["saltos"] for r in risco_indireto)
        linhas.append(
            f"Risco indireto na rede: {len(risco_indireto)} conexão(ões) de 2-3 graus de "
            f"distância (não direta) com empresa(s) SANCIONADA(S) encontrada(s), a partir de "
            f"{min_saltos} salto(s) (ex.: sócio do sócio, ou endereço de quem compartilha endereço)."
        )

    return f"""Você é um analista de compliance/due diligence especialista em risco empresarial no Brasil.
Escreva um PARECER TÉCNICO CONSOLIDADO (parágrafo único, até 150 palavras, português do Brasil, tom formal e objetivo) sobre a empresa abaixo, avaliando o risco de contratação/parceria com base SOMENTE nos dados fornecidos. Não invente números nem fatos que não estejam listados. Se não houver nenhum alerta (sanção, dívida, processo, rede de risco), diga isso claramente e recomende prosseguir normalmente.
IMPORTANTE sobre dívida ativa: trate "dívida PRÓPRIA (devedor principal)" e "dívida por RESPONSABILIDADE SOLIDÁRIA/CORRESPONSÁVEL" como riscos DIFERENTES — a segunda é dívida de OUTRO devedor pela qual esta empresa também pode ser cobrada (responsabilidade solidária prevista em lei), não uma dívida que a empresa contraiu. Nunca some ou confunda os dois valores nem apresente o valor solidário como se fosse dívida própria da empresa.
IMPORTANTE sobre os dois scores preditivos: são dois modelos DIFERENTES (um vê atributos da empresa, o outro vê a estrutura da rede societária) — se divergirem bastante, isso não é erro nem contradição, é informação: mencione a divergência e o que ela sugere (ex.: atributos isolados baixos mas posição de risco na rede), não escolha "o certo" entre os dois.
IMPORTANTE sobre centralidade/comunidade/risco indireto na rede: alta centralidade (PageRank/betweenness) NÃO é, sozinha, sinal de risco — holdings e grupos econômicos legítimos também são centrais na rede; mencione só como contexto estrutural, sem alarmismo. Já uma comunidade com % alta de empresas sancionadas, ou uma conexão indireta (2-3 saltos) encontrada com empresa sancionada, SÃO sinais relevantes de risco por associação e devem ser destacados no parecer.
IMPORTANTE sobre PEP: NÃO trate como sanção, irregularidade ou red flag — é só um sinalizador de exposição pública (a pessoa ocupa ou ocupou cargo público relevante), relevante pra avaliar conflito de interesse em contratações públicas, não um indicativo de risco de crédito/fiscal. Mencione como contexto, sem alarmismo.
IMPORTANTE sobre risco geográfico (município): é uma característica do LOCAL onde a empresa está situada, não da empresa em si — não culpe nem penalize a empresa por isso; mencione só como contexto estrutural regional, e apenas se o percentil for claramente alto (ex. >70%) vale destacar como um fator a mais a observar.

Dados:
{chr(10).join(linhas)}"""


def gerar_parecer(dados_dossie: dict) -> str:
    """Chama o OpenRouter (modelo free tier) e devolve o parecer em texto
    puro (parágrafo único). Levanta exceção se a chamada falhar — quem
    chama decide como tratar (ver main.py)."""
    prompt = _montar_prompt(dados_dossie)
    resp = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    if "choices" not in data:
        raise RuntimeError(f"OpenRouter sem 'choices' na resposta: {data}")
    return data["choices"][0]["message"]["content"].strip()
