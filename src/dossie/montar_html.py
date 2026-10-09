"""Monta o dossiê final como HTML estilizado — porta de `n8n/montar_html.js`
para Python (mesmo template visual, CSS escopado sob `.kobi-doc`). Fonte de
verdade visual agora é este arquivo (o .js em n8n/ fica só de referência
histórica, o workflow n8n não é mais usado)."""
from __future__ import annotations

import datetime
from html import escape as esc

SITUACAO = {"01": "Nula", "02": "Ativa", "03": "Suspensa", "04": "Inapta", "08": "Baixada"}
PORTE = {"01": "Não informado", "02": "Micro Empresa (ME)", "03": "Peq. porte (EPP)", "05": "Demais"}

CSS = """
.kobi-doc{
  --bg:#070b09; --panel:#0c1310; --panel-2:#0f1713;
  --line:rgba(74,222,148,0.18); --line-strong:rgba(74,222,148,0.38);
  --green:#3ee08a; --green-soft:rgba(62,224,138,0.12); --green-dim:#6fa98c;
  --text:#d9f2e4; --text-dim:#82a794;
  --red:#ff6b6b; --red-soft:rgba(255,107,107,0.1);
  --amber:#f0c05a; --amber-soft:rgba(240,192,90,0.1);
  --mono:"JetBrains Mono","SF Mono",ui-monospace,Menlo,Consolas,monospace;
  --sans:"Inter",-apple-system,"Segoe UI",Roboto,sans-serif;
  font-family:var(--sans); color:var(--text);
}
.kobi-doc, .kobi-doc *{ box-sizing:border-box; }
.kobi-doc .doc{ max-width:880px; margin:0 auto; background:var(--panel); border:1px solid var(--line); border-radius:14px; overflow:hidden; box-shadow:0 0 0 1px rgba(0,0,0,0.4), 0 30px 60px -30px rgba(0,0,0,0.8); }
.kobi-doc .header{ padding:24px 26px 22px; border-bottom:1px solid var(--line); background:linear-gradient(180deg, rgba(62,224,138,0.06), transparent 70%); }
.kobi-doc .eyebrow{ font-family:var(--mono); font-size:11px; letter-spacing:0.08em; color:var(--green-dim); margin-bottom:10px; }
.kobi-doc h1.company{ font-size:19px; line-height:1.3; margin:0 0 6px; color:#eafff1; font-weight:700; }
.kobi-doc .cnpj-line{ font-family:var(--mono); font-size:12.5px; color:var(--text-dim); margin-bottom:16px; }
.kobi-doc .cnpj-line span.alias{ color:var(--green); }
.kobi-doc .badges{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
.kobi-doc .badge{ font-family:var(--mono); font-size:11px; padding:5px 11px; border-radius:999px; border:1px solid var(--line-strong); background:var(--green-soft); color:var(--text); display:inline-flex; align-items:center; gap:6px; white-space:nowrap; }
.kobi-doc .badge.status{ border-color:rgba(62,224,138,0.6); color:var(--green); }
.kobi-doc .badge.status.inativa{ border-color:rgba(255,107,107,0.5); color:var(--red); }
.kobi-doc .badge .dot{ width:6px; height:6px; border-radius:50%; background:var(--green); display:inline-block; }
.kobi-doc .badge.status.inativa .dot{ background:var(--red); }
.kobi-doc .alert-banner{ display:flex; align-items:center; gap:10px; padding:11px 15px; border-radius:8px; border:1px solid rgba(255,107,107,0.4); background:var(--red-soft); color:var(--red); font-size:13px; font-weight:600; }
.kobi-doc .body{ padding:6px 26px 26px; }
.kobi-doc section{ padding:24px 0; border-bottom:1px solid var(--line); }
.kobi-doc section:last-child{ border-bottom:none; }
.kobi-doc .section-label{ font-family:var(--mono); font-size:11px; letter-spacing:0.08em; color:var(--green-dim); margin-bottom:14px; display:flex; align-items:center; gap:8px; }
.kobi-doc .section-label::before{ content:""; width:3px; height:12px; background:var(--green); border-radius:2px; display:inline-block; }
.kobi-doc h2.section-title{ font-size:15px; margin:0 0 16px; color:#eafff1; font-weight:700; }
.kobi-doc .risk-row{ display:flex; gap:20px; align-items:stretch; flex-wrap:wrap; }
.kobi-doc .risk-score-card{ flex:0 0 180px; background:var(--panel-2); border:1px solid var(--line); border-radius:12px; padding:18px; text-align:center; display:flex; flex-direction:column; justify-content:center; }
.kobi-doc .risk-score-value{ font-family:var(--mono); font-size:36px; font-weight:700; color:var(--green); line-height:1; }
.kobi-doc .risk-score-value.mid{ color:var(--amber); }
.kobi-doc .risk-score-value.high{ color:var(--red); }
.kobi-doc .risk-score-max{ font-size:15px; color:var(--text-dim); }
.kobi-doc .risk-score-label{ margin-top:10px; font-size:12px; color:var(--green); font-weight:600; }
.kobi-doc .risk-score-label.mid{ color:var(--amber); }
.kobi-doc .risk-score-label.high{ color:var(--red); }
.kobi-doc .risk-bar-track{ margin-top:12px; height:6px; border-radius:4px; background:rgba(255,255,255,0.06); overflow:hidden; }
.kobi-doc .risk-bar-fill{ height:100%; background:var(--green); border-radius:4px; }
.kobi-doc .risk-bar-fill.mid{ background:var(--amber); }
.kobi-doc .risk-bar-fill.high{ background:var(--red); }
.kobi-doc .risk-details{ flex:1; min-width:240px; display:flex; flex-direction:column; gap:11px; }
.kobi-doc .note{ display:flex; gap:10px; padding:13px 15px; border-radius:8px; border:1px solid rgba(240,192,90,0.3); background:var(--amber-soft); font-size:12.5px; line-height:1.6; color:#e7d9b0; }
.kobi-doc .note b{ color:var(--amber); }
.kobi-doc .note a{ color:var(--amber); text-decoration:underline; }
.kobi-doc .status-line{ font-size:13px; color:var(--text-dim); }
.kobi-doc .status-line b{ color:var(--text); font-weight:600; }
.kobi-doc .alert-list{ margin:6px 0 0; padding:0; list-style:none; }
.kobi-doc .alert-list li{ font-size:13px; padding:7px 0 7px 22px; position:relative; color:var(--text); }
.kobi-doc .alert-list li::before{ content:"▲"; position:absolute; left:0; top:7px; color:var(--amber); font-size:10px; }
.kobi-doc .grid-2{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px; }
@media (max-width:560px){ .kobi-doc .grid-2{ grid-template-columns:1fr; } }
.kobi-doc .fact{ background:var(--panel-2); border:1px solid var(--line); border-radius:10px; padding:13px 15px; }
.kobi-doc .fact .k{ font-family:var(--mono); font-size:10px; letter-spacing:0.06em; color:var(--green-dim); margin-bottom:6px; text-transform:uppercase; }
.kobi-doc .fact .v{ font-size:14px; color:var(--text); font-weight:600; }
.kobi-doc table.socios{ width:100%; border-collapse:collapse; font-size:13px; margin-top:4px; }
.kobi-doc table.socios th{ text-align:left; font-family:var(--mono); font-size:10px; letter-spacing:0.05em; color:var(--green-dim); text-transform:uppercase; padding:8px 10px; border-bottom:1px solid var(--line-strong); }
.kobi-doc table.socios td{ padding:10px; border-bottom:1px solid var(--line); color:var(--text); }
.kobi-doc table.socios td.cpf{ font-family:var(--mono); color:var(--text-dim); }
.kobi-doc .graph-note{ margin-top:14px; display:flex; gap:12px; flex-wrap:wrap; }
.kobi-doc .pill-stat{ background:var(--green-soft); border:1px solid var(--line-strong); border-radius:10px; padding:10px 14px; font-size:12.5px; color:var(--text); flex:1; min-width:220px; }
.kobi-doc .pill-stat b{ color:var(--green); }
.kobi-doc .check-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:20px; }
@media (max-width:640px){ .kobi-doc .check-grid{ grid-template-columns:1fr; } }
.kobi-doc .check-card{ background:var(--panel-2); border:1px solid var(--line); border-radius:10px; padding:13px 15px; }
.kobi-doc .check-card.issue{ border-color:rgba(240,192,90,0.35); }
.kobi-doc .check-card .ck-title{ font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px; }
.kobi-doc .check-card .ck-status{ font-size:12px; color:var(--green); display:flex; align-items:center; gap:6px; }
.kobi-doc .check-card .ck-status::before{ content:"✓"; font-weight:700; }
.kobi-doc .check-card.issue .ck-status{ color:var(--amber); }
.kobi-doc .check-card.issue .ck-status::before{ content:"⚠"; }
.kobi-doc .process-list{ display:flex; flex-direction:column; gap:8px; }
.kobi-doc .process-item{ display:flex; justify-content:space-between; align-items:center; gap:12px; padding:11px 13px; background:var(--panel-2); border:1px solid var(--line); border-radius:8px; font-size:13px; flex-wrap:wrap; }
.kobi-doc .process-item .court{ font-family:var(--mono); font-size:11px; color:var(--green); background:var(--green-soft); border-radius:5px; padding:3px 8px; margin-right:8px; flex-shrink:0; }
.kobi-doc .process-item .desc{ flex:1; color:var(--text); min-width:140px; }
.kobi-doc .process-item .polo{ font-family:var(--mono); font-size:11px; color:var(--text-dim); flex-shrink:0; }
.kobi-doc .process-more{ text-align:center; font-size:12px; color:var(--text-dim); font-family:var(--mono); padding-top:4px; }
.kobi-doc .parecer{ background:var(--panel-2); border:1px solid var(--line); border-radius:12px; padding:20px 22px; }
.kobi-doc .parecer h3{ font-size:12.5px; letter-spacing:0.04em; color:var(--green); margin:0 0 12px; font-family:var(--mono); }
.kobi-doc .parecer p{ font-size:13.5px; line-height:1.75; color:var(--text); margin:0 0 12px; }
.kobi-doc .conclusion-banner{ margin-top:16px; display:flex; gap:12px; align-items:center; padding:13px 15px; border-radius:10px; border:1px solid rgba(62,224,138,0.4); background:var(--green-soft); flex-wrap:wrap; }
.kobi-doc .conclusion-banner.mid{ border-color:rgba(240,192,90,0.4); background:var(--amber-soft); }
.kobi-doc .conclusion-banner.high{ border-color:rgba(255,107,107,0.4); background:var(--red-soft); }
.kobi-doc .conclusion-banner .badge-final{ font-family:var(--mono); font-weight:700; color:var(--green); font-size:12.5px; white-space:nowrap; }
.kobi-doc .conclusion-banner.mid .badge-final{ color:var(--amber); }
.kobi-doc .conclusion-banner.high .badge-final{ color:var(--red); }
.kobi-doc .conclusion-banner p{ margin:0; font-size:12.5px; color:var(--text); line-height:1.6; }
.kobi-doc .footer{ padding:16px 26px; border-top:1px solid var(--line); display:flex; justify-content:space-between; align-items:center; font-family:var(--mono); font-size:11px; color:var(--text-dim); flex-wrap:wrap; gap:6px; }
.kobi-doc .footer .brand{ color:var(--green); }
"""


def _fmt_moeda(v) -> str:
    v = float(v or 0)
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")


def _fmt_cnpj(c) -> str:
    d = "".join(ch for ch in str(c or "") if ch.isdigit()).rjust(14, "0")
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def montar_html(original: dict, parecer: str) -> str:
    emp = original["empresa"]
    score_pred = original.get("score_preditivo")
    score_gnn = original.get("score_gnn")
    ativa = emp.get("situacao_cadastral") == "02"
    situacao_label = SITUACAO.get(emp.get("situacao_cadastral"), emp.get("situacao_cadastral") or "Não informado")

    badges = [f'<span class="badge">🏢 {esc(PORTE.get(emp.get("porte"), "Porte não informado"))}</span>']
    if emp.get("regime_tributario"):
        badges.append(f'<span class="badge">🧾 {esc(emp["regime_tributario"])}</span>')
    if emp.get("municipio"):
        badges.append(f'<span class="badge">📍 {esc(emp["municipio"])}/ES</span>')
    badges.append(f'<span class="badge">💰 {esc(_fmt_moeda(emp.get("capital_social")))}</span>')
    badges.append(
        f'<span class="badge status {"" if ativa else "inativa"}"><span class="dot"></span> {esc(situacao_label)}</span>'
    )

    alertas = []
    if original["sancoes"]:
        alertas.append(f'{len(original["sancoes"])} sanção(ões) administrativa(s) registrada(s)')
    dividas_proprias = [x for x in original["dividas_ativas"] if x.get("tipo_devedor") == "PRINCIPAL"]
    if dividas_proprias:
        alertas.append(f'{len(dividas_proprias)} inscrição(ões) em dívida ativa própria')
    dividas_corresp = [x for x in original["dividas_ativas"] if x.get("tipo_devedor") != "PRINCIPAL"]
    if dividas_corresp:
        alertas.append(f'{len(dividas_corresp)} inscrição(ões) por responsabilidade solidária (dívida de terceiro)')
    if original["processos_judiciais"]:
        alertas.append(f'{len(original["processos_judiciais"])} processo(s) judicial(is) localizado(s)')
    if original["infracoes_ambientais"]:
        alertas.append(f'{len(original["infracoes_ambientais"])} infração(ões) ambiental(is)')
    conexoes_sancionadas = [c for c in (original.get("rede_societaria") or []) if c.get("sancionada_direto")]
    if conexoes_sancionadas:
        alertas.append(f'Sócio em comum com {len(conexoes_sancionadas)} empresa(s) sancionada(s)')

    tem_pendencia = len(alertas) > 0

    nivel_classe = ""
    recomendacao = "Score preditivo não disponível para esta empresa — avalie com base apenas nos dados factuais acima."
    if score_pred:
        if score_pred["score_0_100"] >= 66:
            nivel_classe = "high"
            recomendacao = "Recomenda-se cautela — investigação manual aprofundada antes de qualquer contratação/parceria."
        elif score_pred["score_0_100"] >= 33:
            nivel_classe = "mid"
            recomendacao = "Recomenda-se investigação manual adicional antes de prosseguir com a contratação/parceria."
        else:
            recomendacao = "Recomenda-se prosseguir com a contratação/parceria, mantendo monitoramento padrão dos itens listados acima."

    if score_pred:
        largura = min(100, max(0, score_pred["score_0_100"]))
        risk_card_html = f"""
    <div class="risk-score-card">
      <div><span class="risk-score-value {nivel_classe}">{score_pred["score_0_100"]:.2f}</span><span class="risk-score-max">/100</span></div>
      <div class="risk-score-label {nivel_classe}">{esc(score_pred["nivel"].upper())}</div>
      <div class="risk-bar-track"><div class="risk-bar-fill {nivel_classe}" style="width:{largura}%"></div></div>
    </div>"""
    else:
        risk_card_html = """
    <div class="risk-score-card">
      <div class="risk-score-value" style="color:var(--text-dim);font-size:22px;">N/D</div>
      <div class="risk-score-label" style="color:var(--text-dim);">FORA DA BASE DO MODELO</div>
    </div>"""

    nota_metodologica = ""
    if score_pred:
        link = ""
        if score_pred.get("artigo_url"):
            doi = score_pred["artigo_url"].replace("https://doi.org/", "")
            link = f' Ver metodologia completa no <a href="{esc(score_pred["artigo_url"])}" target="_blank" rel="noopener">artigo do autor (Zenodo, DOI {esc(doi)})</a>.'
        nota_metodologica = f'<div class="note"><span>⚠️</span><span><b>Nota metodológica (score tabular):</b> {esc(score_pred["ressalva_metodologica"])}{link}</span></div>'

    risk_card_gnn_html = ""
    nota_metodologica_gnn = ""
    if score_gnn:
        nivel_classe_gnn = ""
        if score_gnn["score_0_100"] >= 66:
            nivel_classe_gnn = "high"
        elif score_gnn["score_0_100"] >= 33:
            nivel_classe_gnn = "mid"
        largura_gnn = min(100, max(0, score_gnn["score_0_100"]))
        risk_card_gnn_html = f"""
    <div class="risk-score-card">
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;">REDE (GNN)</div>
      <div><span class="risk-score-value {nivel_classe_gnn}">{score_gnn["score_0_100"]:.2f}</span><span class="risk-score-max">/100</span></div>
      <div class="risk-score-label {nivel_classe_gnn}">{esc(score_gnn["nivel"].upper())}</div>
      <div class="risk-bar-track"><div class="risk-bar-fill {nivel_classe_gnn}" style="width:{largura_gnn}%"></div></div>
    </div>"""
        nota_metodologica_gnn = f'<div class="note"><span>⚠️</span><span><b>Nota metodológica (score de rede/GNN):</b> {esc(score_gnn["ressalva_metodologica"])}</span></div>'

    if original["socios"]:
        socios_html = "".join(
            f'<tr><td>{esc(s["nome_socio"])}</td><td class="cpf">{esc(s.get("cpf_parcial") or "não informado")}</td></tr>'
            for s in original["socios"]
        )
    else:
        socios_html = '<tr><td colspan="2" style="color:var(--text-dim);">Nenhum sócio registrado</td></tr>'

    rede = original.get("rede_societaria") or []
    if rede:
        extra = f", sendo <b>{len(conexoes_sancionadas)} SANCIONADA(S)</b>" if conexoes_sancionadas else ""
        pill_grafo = f'<div class="pill-stat">🔗 Conexões de grafo (sócio em comum): <b>{len(rede)} empresa(s)</b> conectada(s){extra}.</div>'
    else:
        pill_grafo = '<div class="pill-stat">🔗 Nenhuma conexão societária relevante encontrada.</div>'

    pill_endereco = ""
    enderecos = original.get("enderecos_compartilhados")
    if enderecos and enderecos.get("hub_alto_grau"):
        pill_endereco = f'<div class="pill-stat">🏢 Endereço compartilhado com <b>{enderecos["grau_total"]} empresas</b> — prédio/condomínio comercial de alto volume (não avaliado individualmente).</div>'
    elif enderecos and enderecos.get("empresas"):
        pill_endereco = f'<div class="pill-stat">🏢 Endereço compartilhado com <b>{len(enderecos["empresas"])} outra(s) empresa(s)</b>.</div>'

    centralidade = original.get("centralidade_rede")
    comunidade = original.get("comunidade_rede")
    risco_geografico = original.get("risco_geografico")
    risco_indireto = original.get("risco_indireto_rede") or []
    peps_vistos = set()
    peps = []
    for v in (original.get("vinculos_politicos") or []):
        if v.get("fonte") != "PEP":
            continue
        chave = (v.get("nome_socio_vinculado"), v.get("cargo_ou_funcao"), v.get("orgao_ou_partido"), v.get("ano"))
        if chave in peps_vistos:
            continue
        peps_vistos.add(chave)
        peps.append(v)

    pill_centralidade = ""
    if centralidade:
        pill_centralidade = (
            f'<div class="pill-stat">📡 Centralidade na rede: percentil <b>{centralidade["pagerank_percentil"]}%</b> '
            f'em importância geral (PageRank) · percentil <b>{centralidade["betweenness_percentil"]}%</b> como ponte '
            f'entre grupos (betweenness).</div>'
        )
    pill_comunidade = ""
    if comunidade and comunidade.get("pct_sancionada") is not None:
        alerta_comunidade = " ⚠️" if comunidade["pct_sancionada"] >= 10 else ""
        pill_comunidade = (
            f'<div class="pill-stat">🧩 Cluster #{esc(str(comunidade["id_comunidade"]))} da rede: '
            f'<b>{comunidade["tamanho"]} empresa(s)</b> no mesmo grupo, <b>{comunidade["pct_sancionada"]}%</b> '
            f'sancionada(s){alerta_comunidade}</div>'
        )
    pill_risco_indireto = ""
    if risco_indireto:
        min_saltos = min(r["saltos"] for r in risco_indireto)
        pill_risco_indireto = (
            f'<div class="pill-stat" style="border-color:rgba(255,107,107,0.45);">🔗⚠️ Risco indireto: '
            f'<b>{len(risco_indireto)} conexão(ões)</b> com empresa(s) sancionada(s) a partir de '
            f'<b>{min_saltos} salto(s)</b> de distância (não direta).</div>'
        )
    pill_risco_geografico = ""
    if risco_geografico:
        alerta_geo = " ⚠️" if risco_geografico["percentil"] >= 70 else ""
        pill_risco_geografico = (
            f'<div class="pill-stat">📍 Risco geográfico: <b>{risco_geografico["pct_sancionada"]}%</b> das '
            f'{risco_geografico["total_empresas"]} empresas do mesmo município têm sanção direta '
            f'(percentil <b>{risco_geografico["percentil"]}%</b> entre os municípios da região){alerta_geo}.</div>'
        )
    pill_pep = ""
    if peps:
        nomes_pep_unicos = list(dict.fromkeys(v["nome_socio_vinculado"] for v in peps))
        nomes_pep = ", ".join(esc(n) for n in nomes_pep_unicos)
        pill_pep = (
            f'<div class="pill-stat" style="border-color:rgba(100,180,255,0.4);">🏛️ PEP: '
            f'<b>{len(nomes_pep_unicos)} sócio(s)</b> com exposição pública ({nomes_pep}) — não é sanção, '
            f'sinalizador de cargo público pra avaliação de conflito de interesse.</div>'
        )
    tem_analise_rede = bool(pill_centralidade or pill_comunidade or pill_risco_indireto or pill_risco_geografico or pill_pep)

    def check_card(titulo, ok, texto_ok, texto_issue):
        cls = "" if ok else "issue"
        texto = texto_ok if ok else texto_issue
        return f'<div class="check-card {cls}"><div class="ck-title">{esc(titulo)}</div><div class="ck-status">{esc(texto)}</div></div>'

    check_sancoes = check_card("Sanções e Penalidades", len(original["sancoes"]) == 0, "Nenhuma sanção encontrada", f'{len(original["sancoes"])} sanção(ões) encontrada(s)')
    total_dividas = len(original["dividas_ativas"])
    texto_issue_dividas = ", ".join(filter(None, [
        f"{len(dividas_proprias)} própria(s)" if dividas_proprias else "",
        f"{len(dividas_corresp)} solidária(s)" if dividas_corresp else "",
    ]))
    check_dividas = check_card("Dívida Ativa", total_dividas == 0, "Nenhuma dívida ativa encontrada", texto_issue_dividas)
    check_infracoes = check_card("Infrações Ambientais", len(original["infracoes_ambientais"]) == 0, "Nenhuma infração encontrada (IBAMA/IEMA)", f'{len(original["infracoes_ambientais"])} infração(ões) encontrada(s)')

    processos = original["processos_judiciais"]
    if processos:
        itens = "".join(
            f'<div class="process-item"><span class="court">{esc(p.get("tribunal") or "—")}</span>'
            f'<span class="desc">{esc(p.get("classe") or "Classe não informada")}</span>'
            f'<span class="polo">Polo: {esc(p.get("polo") or "—")}</span></div>'
            for p in processos[:5]
        )
        if len(processos) > 5:
            itens += f'<div class="process-more">+ {len(processos) - 5} processo(s) adicionais</div>'
        processos_html = itens
    else:
        processos_html = '<div class="process-item"><span class="desc" style="color:var(--text-dim)">Nenhum processo judicial encontrado.</span></div>'

    data_consulta = datetime.datetime.now().strftime("%d/%m/%Y")
    num_analise_rede = "03" if tem_analise_rede else None
    num_auditoria = "04" if tem_analise_rede else "03"
    num_conclusao = "05" if tem_analise_rede else "04"

    secao_analise_rede = ""
    if tem_analise_rede:
        secao_analise_rede = f"""<section>
      <div class="section-label">{num_analise_rede} — ANÁLISE ESTRUTURAL DA REDE</div>
      <h2 class="section-title">Posição na Rede Societária (Grafo)</h2>
      <div class="graph-note">{pill_centralidade}{pill_comunidade}{pill_risco_geografico}{pill_risco_indireto}{pill_pep}</div>
    </section>"""

    badge_final = esc(score_pred["nivel"].upper()) if score_pred else "SEM SCORE"

    html = f"""<div class="kobi-doc"><style>{CSS}</style>
<div class="doc">
  <div class="header">
    <div class="eyebrow">DOSSIÊ DE DUE DILIGENCE — KOBI INTELLIGENCE HUB</div>
    <h1 class="company">{esc(emp["razao_social"])}</h1>
    <div class="cnpj-line">{esc(_fmt_cnpj(original["cnpj"]))}{f' &nbsp;·&nbsp; <span class="alias">{esc(emp["nome_fantasia"])}</span>' if emp.get("nome_fantasia") else ""}</div>
    <div class="badges">{"".join(badges)}</div>
    {'<div class="alert-banner">⚠️ Pendência jurídico-fiscal identificada — ver seções abaixo</div>' if tem_pendencia else ""}
  </div>
  <div class="body">
    <section>
      <div class="section-label">01 — RESUMO EXECUTIVO</div>
      <h2 class="section-title">Índice de Risco</h2>
      <div class="risk-row">
        {risk_card_html}
        {risk_card_gnn_html}
        <div class="risk-details">
          {nota_metodologica}
          {nota_metodologica_gnn}
          <div class="status-line">Status Cadastral: <b>{esc(situacao_label)} (Receita Federal)</b></div>
          <div>
            <div class="status-line" style="margin-bottom:2px;">Principais Alertas Encontrados:</div>
            <ul class="alert-list">{"".join(f"<li>{esc(a)}</li>" for a in alertas) if alertas else "<li>Nenhum alerta encontrado nas fontes consultadas.</li>"}</ul>
          </div>
        </div>
      </div>
    </section>
    <section>
      <div class="section-label">02 — ESTRUTURA SOCIETÁRIA</div>
      <h2 class="section-title">Análise Cadastral e Estrutura Societária</h2>
      <div class="grid-2">
        <div class="fact"><div class="k">Município</div><div class="v">{esc(emp.get("municipio") or "—")}/ES</div></div>
        <div class="fact"><div class="k">Capital Social</div><div class="v">{esc(_fmt_moeda(emp.get("capital_social")))}</div></div>
      </div>
      <table class="socios"><thead><tr><th>Sócio</th><th>CPF</th></tr></thead><tbody>{socios_html}</tbody></table>
      <div class="graph-note">{pill_grafo}{pill_endereco}</div>
    </section>
    {secao_analise_rede}
    <section>
      <div class="section-label">{num_auditoria} — AUDITORIA</div>
      <h2 class="section-title">Regularidade e Passivos</h2>
      <div class="check-grid">{check_sancoes}{check_dividas}{check_infracoes}</div>
      <div class="section-label" style="margin-top:4px;">PROCESSOS JUDICIAIS (DJEN)</div>
      <div class="process-list">{processos_html}</div>
    </section>
    <section>
      <div class="section-label">{num_conclusao} — CONCLUSÃO</div>
      <h2 class="section-title">Parecer Técnico Consolidado</h2>
      <div class="parecer">
        <h3>PARECER TÉCNICO CONSOLIDADO</h3>
        <p>{esc(parecer)}</p>
        <div class="conclusion-banner {nivel_classe}">
          <span class="badge-final">{badge_final}</span>
          <p>{esc(recomendacao)}</p>
        </div>
      </div>
    </section>
  </div>
  <div class="footer">
    <span>Gerado por <span class="brand">Kobi Intelligence Hub</span></span>
    <span>Consulta em {data_consulta}</span>
  </div>
</div>
</div>"""
    return html
