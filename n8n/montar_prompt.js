const d = $input.item.json;
const emp = d.empresa;
const linhas = [];
linhas.push(`Empresa: ${emp.razao_social}${emp.nome_fantasia ? ' (' + emp.nome_fantasia + ')' : ''}`);
linhas.push(`CNPJ: ${d.cnpj}`);
linhas.push(`Situação cadastral: ${emp.situacao_cadastral === '02' ? 'Ativa' : emp.situacao_cadastral}`);
linhas.push(`Município: ${emp.municipio}`);
linhas.push(`Sócios: ${(d.socios || []).map(s => s.nome_socio).join(', ') || 'nenhum registrado'}`);
if (d.sancoes.length) linhas.push(`Sanções administrativas (${d.sancoes.length}): ` + d.sancoes.map(s => `${s.tipo} - ${s.orgao_sancionador}`).join('; '));
if (d.dividas_ativas.length) {
  const total = d.dividas_ativas.reduce((a, x) => a + (x.valor || 0), 0);
  linhas.push(`Dívida ativa (${d.dividas_ativas.length} registro(s)): total R$ ${total.toLocaleString('pt-BR')}`);
}
if (d.processos_judiciais.length) linhas.push(`Processos judiciais: ${d.processos_judiciais.length} encontrados`);
if (d.infracoes_ambientais.length) linhas.push(`Infrações ambientais (IBAMA/IEMA): ${d.infracoes_ambientais.length}`);
const conexoesSancionadas = (d.rede_societaria || []).filter(c => c.sancionada_direto);
if (conexoesSancionadas.length) {
  linhas.push(`Rede societária: sócio em comum com ${conexoesSancionadas.length} empresa(s) SANCIONADA(S) (CNPJ: ${conexoesSancionadas.map(c => c.cnpj_conectada).join(', ')})`);
} else if ((d.rede_societaria || []).length) {
  linhas.push(`Rede societária: sócio em comum com ${d.rede_societaria.length} outra(s) empresa(s), nenhuma sancionada diretamente`);
}
if (d.enderecos_compartilhados && d.enderecos_compartilhados.hub_alto_grau) {
  linhas.push('Endereço: prédio/condomínio comercial de alto volume (não avaliado individualmente)');
} else if (d.enderecos_compartilhados && d.enderecos_compartilhados.empresas.length) {
  linhas.push(`Endereço compartilhado com ${d.enderecos_compartilhados.empresas.length} outra(s) empresa(s)`);
}
if (d.score_preditivo) linhas.push(`Score de risco preditivo (modelo estatístico): ${d.score_preditivo.score_0_100}/100 (${d.score_preditivo.nivel})`);

const prompt = `Você é um analista de compliance/due diligence especialista em risco empresarial no Brasil.
Escreva um PARECER TÉCNICO CONSOLIDADO (parágrafo único, até 150 palavras, português do Brasil, tom formal e objetivo) sobre a empresa abaixo, avaliando o risco de contratação/parceria com base SOMENTE nos dados fornecidos. Não invente números nem fatos que não estejam listados. Se não houver nenhum alerta (sanção, dívida, processo, rede de risco), diga isso claramente e recomende prosseguir normalmente.

Dados:
${linhas.join('\n')}`;

return [{ json: { ...d, prompt } }];
