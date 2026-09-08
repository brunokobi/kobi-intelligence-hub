const original = $('Buscar Dossie').item.json;
const parecer = ($json.response || '').trim();
const emp = original.empresa;
const scorePred = original.score_preditivo;

function fmtMoeda(v) { return 'R$ ' + Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }); }

let md = `# RELATÓRIO DE INTELIGÊNCIA E ANÁLISE DE RISCO\n\n`;
md += `**Empresa Alvo:** ${emp.razao_social}${emp.nome_fantasia ? ' (' + emp.nome_fantasia + ')' : ''} (CNPJ: ${original.cnpj})\n\n`;
md += `**Data da Consulta:** ${new Date().toLocaleDateString('pt-BR')}\n`;
md += `**Gerado por:** Kobi Intelligence Hub\n\n---\n\n`;

md += `## 1. Resumo Executivo & Índice de Risco\n\n`;
if (scorePred) {
  md += `**Score de Risco Preditivo (Modelo Tabular):** ${scorePred.score_0_100}/100 (${scorePred.nivel})\n\n`;
  md += `> ⚠️ **Nota metodológica:** ${scorePred.ressalva_metodologica}\n\n`;
}
md += `**Status Cadastral:** ${emp.situacao_cadastral === '02' ? 'Ativa' : emp.situacao_cadastral} (Receita Federal)\n\n`;

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

md += `**Principais Alertas Encontrados:**\n`;
md += alertas.length ? alertas.map(a => `- ${a}`).join('\n') : '- Nenhum alerta encontrado nas fontes consultadas.';
md += `\n\n`;

md += `## 2. Análise Cadastral e Estrutura Societária\n\n`;
md += `- **Município:** ${emp.municipio}\n`;
md += `- **Capital Social:** ${fmtMoeda(emp.capital_social)}\n`;
md += `- **Quadro Societário:**\n`;
md += (original.socios.length ? original.socios.map(s => `  - ${s.nome_socio} (CPF ${s.cpf_parcial || 'não informado'})`).join('\n') : '  - Nenhum sócio registrado');
md += `\n\n`;
md += `- **Conexões de Grafo (sócio em comum):** `;
md += original.rede_societaria.length
  ? `${original.rede_societaria.length} empresa(s) conectada(s)${conexoesSancionadas.length ? `, sendo ${conexoesSancionadas.length} SANCIONADA(S)` : ''}.`
  : 'Nenhuma conexão societária relevante encontrada.';
md += `\n`;
if (original.enderecos_compartilhados.hub_alto_grau) {
  md += `- **Endereço:** compartilhado com ${original.enderecos_compartilhados.grau_total} empresas (prédio/condomínio comercial de alto volume — não avaliado individualmente).\n`;
} else if (original.enderecos_compartilhados.empresas.length) {
  md += `- **Endereço Compartilhado:** ${original.enderecos_compartilhados.empresas.length} outra(s) empresa(s) no mesmo endereço.\n`;
}
md += `\n`;

md += `## 3. Auditoria de Regularidade e Passivos\n\n`;
md += `**Sanções e Penalidades:**\n`;
md += (original.sancoes.length
  ? original.sancoes.map(s => `- ⚠️ ${s.tipo} (${s.orgao_sancionador}) — desde ${s.data_inicio}${s.data_fim ? ' até ' + s.data_fim : ''}`).join('\n')
  : '- Nenhuma sanção encontrada.');
md += `\n\n`;

md += `**Dívida Ativa:**\n`;
if (original.dividas_ativas.length) {
  const principais = original.dividas_ativas.filter(x => x.tipo_devedor === 'PRINCIPAL');
  const corresponsaveis = original.dividas_ativas.filter(x => x.tipo_devedor !== 'PRINCIPAL');
  if (principais.length) {
    const totalPrincipal = principais.reduce((a, x) => a + (x.valor || 0), 0);
    md += `- ⚠️ Dívida própria (devedor principal): ${principais.length} inscrição(ões), total ${fmtMoeda(totalPrincipal)}\n`;
  }
  if (corresponsaveis.length) {
    const totalCorresp = corresponsaveis.reduce((a, x) => a + (x.valor || 0), 0);
    md += `- ⚠️ Responsabilidade solidária/corresponsável (dívida de OUTRO devedor, não própria): ${corresponsaveis.length} inscrição(ões), total ${fmtMoeda(totalCorresp)}\n`;
  }
} else {
  md += `- Nenhuma dívida ativa encontrada.\n`;
}
md += `\n`;

md += `**Processos Judiciais (DJEN):**\n`;
md += (original.processos_judiciais.length
  ? original.processos_judiciais.slice(0, 5).map(p => `- ⚖️ ${p.tribunal} — ${p.classe} (polo: ${p.polo})`).join('\n') +
    (original.processos_judiciais.length > 5 ? `\n- ... e mais ${original.processos_judiciais.length - 5} processo(s)` : '')
  : '- Nenhum processo judicial encontrado.');
md += `\n\n`;

md += `**Infrações Ambientais (IBAMA/IEMA):**\n`;
md += (original.infracoes_ambientais.length
  ? original.infracoes_ambientais.map(i => `- 🌱 ${i.orgao}${i.valor_multa ? ' — multa ' + fmtMoeda(i.valor_multa) : ''}`).join('\n')
  : '- Nenhuma infração ambiental encontrada.');
md += `\n\n`;

md += `## 4. Parecer Técnico Consolidado\n\n`;
md += `> ${parecer}\n`;

return [{ json: { markdown: md, cnpj: original.cnpj } }];
