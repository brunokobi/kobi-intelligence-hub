// Substitui "Montar Markdown Final" — monta o dossiê final como HTML
// estilizado (modelo visual definido pelo usuário, dossie_cyber_suite.html),
// deterministicamente a partir do JSON do node "Buscar Dossie" + o parecer
// do LLM (node "Chamar Ollama"). CSS escopado sob ".kobi-doc" pra não
// vazar/colidir com o CSS do dashboard onde isso é injetado via innerHTML.
const original = $('Buscar Dossie').item.json;
const parecer = ($json.response || '').trim();
const emp = original.empresa;
const scorePred = original.score_preditivo;

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function fmtMoeda(v) { return 'R$ ' + Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }); }
function fmtCnpj(c) {
  const d = String(c || '').replace(/\D/g, '').padStart(14, '0');
  return `${d.slice(0,2)}.${d.slice(2,5)}.${d.slice(5,8)}/${d.slice(8,12)}-${d.slice(12,14)}`;
}
function fmtDataYmd(s) {
  if (!s || String(s).length !== 8) return null;
  const t = String(s);
  return `${t.slice(6,8)}/${t.slice(4,6)}/${t.slice(0,4)}`;
}

const SITUACAO = { '01': 'Nula', '02': 'Ativa', '03': 'Suspensa', '04': 'Inapta', '08': 'Baixada' };
const PORTE = { '01': 'Não informado', '02': 'Micro Empresa (ME)', '03': 'Peq. porte (EPP)', '05': 'Demais' };
const ativa = emp.situacao_cadastral === '02';
const situacaoLabel = SITUACAO[emp.situacao_cadastral] || (emp.situacao_cadastral || 'Não informado');

// ---- CSS escopado (modelo visual: dossie_cyber_suite.html) ----
const css = `
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
`;

// ---- Badges do header ----
const badges = [];
badges.push(`<span class="badge">🏢 ${esc(PORTE[emp.porte] || 'Porte não informado')}</span>`);
if (emp.regime_tributario) badges.push(`<span class="badge">🧾 ${esc(emp.regime_tributario)}</span>`);
if (emp.municipio) badges.push(`<span class="badge">📍 ${esc(emp.municipio)}/ES</span>`);
badges.push(`<span class="badge">💰 ${esc(fmtMoeda(emp.capital_social))}</span>`);
badges.push(`<span class="badge status ${ativa ? '' : 'inativa'}"><span class="dot"></span> ${esc(situacaoLabel)}</span>`);

// ---- Alertas (mesma lógica do relatório anterior) ----
const alertas = [];
if (original.sancoes.length) alertas.push(`${original.sancoes.length} sanção(ões) administrativa(s) registrada(s)`);
const dividasProprias = original.dividas_ativas.filter(x => x.tipo_devedor === 'PRINCIPAL');
if (dividasProprias.length) alertas.push(`${dividasProprias.length} inscrição(ões) em dívida ativa própria`);
const dividasCorresp = original.dividas_ativas.filter(x => x.tipo_devedor !== 'PRINCIPAL');
if (dividasCorresp.length) alertas.push(`${dividasCorresp.length} inscrição(ões) por responsabilidade solidária (dívida de terceiro)`);
if (original.processos_judiciais.length) alertas.push(`${original.processos_judiciais.length} processo(s) judicial(is) localizado(s)`);
if (original.infracoes_ambientais.length) alertas.push(`${original.infracoes_ambientais.length} infração(ões) ambiental(is)`);
const conexoesSancionadas = (original.rede_societaria || []).filter(c => c.sancionada_direto);
if (conexoesSancionadas.length) alertas.push(`Sócio em comum com ${conexoesSancionadas.length} empresa(s) sancionada(s)`);

const temPendencia = alertas.length > 0;

// ---- Nível de risco -> classe CSS + rótulo de recomendação ----
let nivelClasse = '';
let recomendacao = 'Score preditivo não disponível para esta empresa — avalie com base apenas nos dados factuais acima.';
if (scorePred) {
  if (scorePred.score_0_100 >= 66) { nivelClasse = 'high'; recomendacao = 'Recomenda-se cautela — investigação manual aprofundada antes de qualquer contratação/parceria.'; }
  else if (scorePred.score_0_100 >= 33) { nivelClasse = 'mid'; recomendacao = 'Recomenda-se investigação manual adicional antes de prosseguir com a contratação/parceria.'; }
  else { recomendacao = 'Recomenda-se prosseguir com a contratação/parceria, mantendo monitoramento padrão dos itens listados acima.'; }
}

// ---- Card de risco ----
let riskCardHtml;
if (scorePred) {
  const largura = Math.min(100, Math.max(0, scorePred.score_0_100));
  riskCardHtml = `
    <div class="risk-score-card">
      <div><span class="risk-score-value ${nivelClasse}">${scorePred.score_0_100.toFixed(2)}</span><span class="risk-score-max">/100</span></div>
      <div class="risk-score-label ${nivelClasse}">${esc(scorePred.nivel.toUpperCase())}</div>
      <div class="risk-bar-track"><div class="risk-bar-fill ${nivelClasse}" style="width:${largura}%"></div></div>
    </div>`;
} else {
  riskCardHtml = `
    <div class="risk-score-card">
      <div class="risk-score-value" style="color:var(--text-dim);font-size:22px;">N/D</div>
      <div class="risk-score-label" style="color:var(--text-dim);">FORA DA BASE DO MODELO</div>
    </div>`;
}

const notaMetodologica = scorePred
  ? `<div class="note"><span>⚠️</span><span><b>Nota metodológica:</b> ${esc(scorePred.ressalva_metodologica)}${scorePred.artigo_url ? ` Ver metodologia completa no <a href="${esc(scorePred.artigo_url)}" target="_blank" rel="noopener">artigo do autor (Zenodo, DOI ${esc(scorePred.artigo_url.replace('https://doi.org/', ''))})</a>.` : ''}</span></div>`
  : '';

// ---- Sócios ----
const sociosHtml = original.socios.length
  ? original.socios.map(s => `<tr><td>${esc(s.nome_socio)}</td><td class="cpf">${esc(s.cpf_parcial || 'não informado')}</td></tr>`).join('')
  : `<tr><td colspan="2" style="color:var(--text-dim);">Nenhum sócio registrado</td></tr>`;

// ---- Pills de grafo/endereço ----
const pillGrafo = original.rede_societaria.length
  ? `<div class="pill-stat">🔗 Conexões de grafo (sócio em comum): <b>${original.rede_societaria.length} empresa(s)</b> conectada(s)${conexoesSancionadas.length ? `, sendo <b>${conexoesSancionadas.length} SANCIONADA(S)</b>` : ''}.</div>`
  : `<div class="pill-stat">🔗 Nenhuma conexão societária relevante encontrada.</div>`;
let pillEndereco = '';
if (original.enderecos_compartilhados && original.enderecos_compartilhados.hub_alto_grau) {
  pillEndereco = `<div class="pill-stat">🏢 Endereço compartilhado com <b>${original.enderecos_compartilhados.grau_total} empresas</b> — prédio/condomínio comercial de alto volume (não avaliado individualmente).</div>`;
} else if (original.enderecos_compartilhados && original.enderecos_compartilhados.empresas.length) {
  pillEndereco = `<div class="pill-stat">🏢 Endereço compartilhado com <b>${original.enderecos_compartilhados.empresas.length} outra(s) empresa(s)</b>.</div>`;
}

// ---- Check-cards de auditoria ----
function checkCard(titulo, ok, textoOk, textoIssue) {
  return `<div class="check-card ${ok ? '' : 'issue'}"><div class="ck-title">${esc(titulo)}</div><div class="ck-status">${ok ? esc(textoOk) : esc(textoIssue)}</div></div>`;
}
const checkSancoes = checkCard('Sanções e Penalidades', original.sancoes.length === 0, 'Nenhuma sanção encontrada', `${original.sancoes.length} sanção(ões) encontrada(s)`);
const totalDividas = original.dividas_ativas.length;
const checkDividas = checkCard('Dívida Ativa', totalDividas === 0, 'Nenhuma dívida ativa encontrada',
  [dividasProprias.length ? `${dividasProprias.length} própria(s)` : '', dividasCorresp.length ? `${dividasCorresp.length} solidária(s)` : ''].filter(Boolean).join(', '));
const checkInfracoes = checkCard('Infrações Ambientais', original.infracoes_ambientais.length === 0, 'Nenhuma infração encontrada (IBAMA/IEMA)', `${original.infracoes_ambientais.length} infração(ões) encontrada(s)`);

// ---- Processos judiciais ----
const processosHtml = original.processos_judiciais.length
  ? original.processos_judiciais.slice(0, 5).map(p => `<div class="process-item"><span class="court">${esc(p.tribunal || '—')}</span><span class="desc">${esc(p.classe || 'Classe não informada')}</span><span class="polo">Polo: ${esc(p.polo || '—')}</span></div>`).join('') +
    (original.processos_judiciais.length > 5 ? `<div class="process-more">+ ${original.processos_judiciais.length - 5} processo(s) adicionais</div>` : '')
  : `<div class="process-item"><span class="desc" style="color:var(--text-dim)">Nenhum processo judicial encontrado.</span></div>`;

// ---- Data da consulta ----
const dataConsulta = new Date().toLocaleDateString('pt-BR');

const html = `<div class="kobi-doc"><style>${css}</style>
<div class="doc">
  <div class="header">
    <div class="eyebrow">DOSSIÊ DE DUE DILIGENCE — KOBI INTELLIGENCE HUB</div>
    <h1 class="company">${esc(emp.razao_social)}</h1>
    <div class="cnpj-line">${esc(fmtCnpj(original.cnpj))}${emp.nome_fantasia ? ` &nbsp;·&nbsp; <span class="alias">${esc(emp.nome_fantasia)}</span>` : ''}</div>
    <div class="badges">${badges.join('')}</div>
    ${temPendencia ? '<div class="alert-banner">⚠️ Pendência jurídico-fiscal identificada — ver seções abaixo</div>' : ''}
  </div>
  <div class="body">
    <section>
      <div class="section-label">01 — RESUMO EXECUTIVO</div>
      <h2 class="section-title">Índice de Risco</h2>
      <div class="risk-row">
        ${riskCardHtml}
        <div class="risk-details">
          ${notaMetodologica}
          <div class="status-line">Status Cadastral: <b>${esc(situacaoLabel)} (Receita Federal)</b></div>
          <div>
            <div class="status-line" style="margin-bottom:2px;">Principais Alertas Encontrados:</div>
            <ul class="alert-list">${alertas.length ? alertas.map(a => `<li>${esc(a)}</li>`).join('') : '<li>Nenhum alerta encontrado nas fontes consultadas.</li>'}</ul>
          </div>
        </div>
      </div>
    </section>
    <section>
      <div class="section-label">02 — ESTRUTURA SOCIETÁRIA</div>
      <h2 class="section-title">Análise Cadastral e Estrutura Societária</h2>
      <div class="grid-2">
        <div class="fact"><div class="k">Município</div><div class="v">${esc(emp.municipio || '—')}/ES</div></div>
        <div class="fact"><div class="k">Capital Social</div><div class="v">${esc(fmtMoeda(emp.capital_social))}</div></div>
      </div>
      <table class="socios"><thead><tr><th>Sócio</th><th>CPF</th></tr></thead><tbody>${sociosHtml}</tbody></table>
      <div class="graph-note">${pillGrafo}${pillEndereco}</div>
    </section>
    <section>
      <div class="section-label">03 — AUDITORIA</div>
      <h2 class="section-title">Regularidade e Passivos</h2>
      <div class="check-grid">${checkSancoes}${checkDividas}${checkInfracoes}</div>
      <div class="section-label" style="margin-top:4px;">PROCESSOS JUDICIAIS (DJEN)</div>
      <div class="process-list">${processosHtml}</div>
    </section>
    <section>
      <div class="section-label">04 — CONCLUSÃO</div>
      <h2 class="section-title">Parecer Técnico Consolidado</h2>
      <div class="parecer">
        <h3>PARECER TÉCNICO CONSOLIDADO</h3>
        <p>${esc(parecer)}</p>
        <div class="conclusion-banner ${nivelClasse}">
          <span class="badge-final">${scorePred ? esc(scorePred.nivel.toUpperCase()) : 'SEM SCORE'}</span>
          <p>${esc(recomendacao)}</p>
        </div>
      </div>
    </section>
  </div>
  <div class="footer">
    <span>Gerado por <span class="brand">Kobi Intelligence Hub</span></span>
    <span>Consulta em ${dataConsulta}</span>
  </div>
</div>
</div>`;

return [{ json: { html, cnpj: original.cnpj } }];
