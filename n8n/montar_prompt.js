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
  const principais = d.dividas_ativas.filter(x => x.tipo_devedor === 'PRINCIPAL');
  const corresponsaveis = d.dividas_ativas.filter(x => x.tipo_devedor !== 'PRINCIPAL');
  const totalPrincipal = principais.reduce((a, x) => a + (x.valor || 0), 0);
  if (principais.length) linhas.push(`Dívida ativa PRÓPRIA (devedor principal, ${principais.length} registro(s)): total R$ ${totalPrincipal.toLocaleString('pt-BR')}`);
  if (corresponsaveis.length) {
    const totalCorresp = corresponsaveis.reduce((a, x) => a + (x.valor || 0), 0);
    linhas.push(`Dívida ativa por RESPONSABILIDADE SOLIDÁRIA/CORRESPONSÁVEL (${corresponsaveis.length} registro(s), dívida de outro devedor pela qual esta empresa também responde legalmente): total R$ ${totalCorresp.toLocaleString('pt-BR')} — NÃO é dívida própria, avaliar com contexto`);
  }
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
if (d.score_preditivo) linhas.push(`Score de risco preditivo tabular (modelo estatístico, XGBoost): ${d.score_preditivo.score_0_100}/100 (${d.score_preditivo.nivel})`);
if (d.score_gnn) linhas.push(`Score de risco preditivo por rede (GNN, usa a estrutura de conexões societárias): ${d.score_gnn.score_0_100}/100 (${d.score_gnn.nivel})`);
if (d.centralidade_rede) {
  const c = d.centralidade_rede;
  linhas.push(`Centralidade na rede societária (comparado a todas as empresas do dataset): percentil ${c.pagerank_percentil}% em importância geral (PageRank) e percentil ${c.betweenness_percentil}% como "ponte" entre grupos distintos (betweenness) -- quanto mais alto, mais central/conectada é a empresa na rede.`);
}
if (d.comunidade_rede) {
  const co = d.comunidade_rede;
  linhas.push(`Comunidade na rede (cluster #${co.id_comunidade}, detecção automática de agrupamento/Louvain): ${co.tamanho} empresa(s) no mesmo cluster, das quais ${co.pct_sancionada}% têm sanção administrativa direta.`);
}
if (d.risco_indireto_rede && d.risco_indireto_rede.length) {
  const minSaltos = Math.min(...d.risco_indireto_rede.map(r => r.saltos));
  linhas.push(`Risco indireto na rede: ${d.risco_indireto_rede.length} conexão(ões) de 2-3 graus de distância (não direta) com empresa(s) SANCIONADA(S) encontrada(s), a partir de ${minSaltos} salto(s) (ex.: sócio do sócio, ou endereço de quem compartilha endereço).`);
}

const prompt = `Você é um analista de compliance/due diligence especialista em risco empresarial no Brasil.
Escreva um PARECER TÉCNICO CONSOLIDADO (parágrafo único, até 150 palavras, português do Brasil, tom formal e objetivo) sobre a empresa abaixo, avaliando o risco de contratação/parceria com base SOMENTE nos dados fornecidos. Não invente números nem fatos que não estejam listados. Se não houver nenhum alerta (sanção, dívida, processo, rede de risco), diga isso claramente e recomende prosseguir normalmente.
IMPORTANTE sobre dívida ativa: trate "dívida PRÓPRIA (devedor principal)" e "dívida por RESPONSABILIDADE SOLIDÁRIA/CORRESPONSÁVEL" como riscos DIFERENTES — a segunda é dívida de OUTRO devedor pela qual esta empresa também pode ser cobrada (responsabilidade solidária prevista em lei), não uma dívida que a empresa contraiu. Nunca some ou confunda os dois valores nem apresente o valor solidário como se fosse dívida própria da empresa.
IMPORTANTE sobre os dois scores preditivos: são dois modelos DIFERENTES (um vê atributos da empresa, o outro vê a estrutura da rede societária) — se divergirem bastante, isso não é erro nem contradição, é informação: mencione a divergência e o que ela sugere (ex.: atributos isolados baixos mas posição de risco na rede), não escolha "o certo" entre os dois.
IMPORTANTE sobre centralidade/comunidade/risco indireto na rede: alta centralidade (PageRank/betweenness) NÃO é, sozinha, sinal de risco — holdings e grupos econômicos legítimos também são centrais na rede; mencione só como contexto estrutural, sem alarmismo. Já uma comunidade com % alta de empresas sancionadas, ou uma conexão indireta (2-3 saltos) encontrada com empresa sancionada, SÃO sinais relevantes de risco por associação e devem ser destacados no parecer.

Dados:
${linhas.join('\n')}`;

return [{ json: { ...d, prompt } }];
