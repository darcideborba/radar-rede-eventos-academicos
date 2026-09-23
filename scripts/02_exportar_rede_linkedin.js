/*
 * Etapa 2 - Exporta a PRÓPRIA rede LinkedIn (conexões, seguidores e seguidos).
 *
 * Como usar:
 *   1. Entre no LinkedIn com a sua conta, no seu navegador.
 *   2. Abra https://www.linkedin.com/mynetwork/network-manager/people-follow/followers/
 *   3. Abra o console do navegador (F12 > Console), cole este script e pressione Enter.
 *   4. Aguarde a mensagem final; o arquivo rede_linkedin.json será baixado.
 *   5. Mova o arquivo para a pasta dados/ do projeto.
 *
 * Observações:
 *   - Usa apenas os endpoints internos que a própria página chama ao listar a sua rede
 *     (nenhum dado de terceiros além do que você já vê na sua lista).
 *   - Pausas entre as chamadas evitam sobrecarga; não reduza os intervalos.
 *   - O identificador QUERY_ID muda de tempos em tempos. Se a coleta de seguidores/seguidos
 *     voltar vazia, abra a aba Rede > Seguidores, veja em F12 > Network uma requisição
 *     "voyagerSearchDashClusters.<hash>" e copie o hash para QUERY_ID.
 *   - Respeite os Termos de Uso do LinkedIn; use somente para organizar a sua própria rede.
 */
(async () => {
  const QUERY_ID = 'voyagerSearchDashClusters.e438ab99259203e9c1cd3f358e217282';
  const csrf = (document.cookie.match(/JSESSIONID="?([^";]+)/) || [])[1];
  const H = { 'csrf-token': csrf, 'x-restli-protocol-version': '2.0.0',
              'accept': 'application/vnd.linkedin.normalized+json+2.1' };
  const pausa = ms => new Promise(r => setTimeout(r, ms));
  const out = { extraido_em: new Date().toISOString(), conexoes: [], seguidores: [], seguindo: [] };

  // Conexões de 1º grau
  const vistos = new Set();
  for (let s = 0; s < 30000; s += 40) {
    const u = `/voyager/api/relationships/dash/connections?decorationId=com.linkedin.voyager.dash.deco.web.mynetwork.ConnectionListWithProfile-16&count=40&q=search&sortType=RECENTLY_ADDED&start=${s}`;
    const j = await (await fetch(u, { headers: H })).json();
    const ps = (j.included || []).filter(x => x.firstName !== undefined && x.publicIdentifier);
    if (!ps.length) break;
    ps.forEach(x => { if (!vistos.has(x.publicIdentifier)) { vistos.add(x.publicIdentifier);
      out.conexoes.push({ nome: `${x.firstName} ${x.lastName}`.trim(), titulo: x.headline || '',
                          url: `https://www.linkedin.com/in/${x.publicIdentifier}/` }); } });
    console.log('conexões:', out.conexoes.length);
    await pausa(400);
  }

  // Seguidores (FOLLOWERS) e seguidos (PEOPLE_FOLLOW)
  async function lista(tipo, destino) {
    const vistos = new Set();
    for (let s = 0; s < 30000; s += 50) {
      const u = `/voyager/api/graphql?variables=(start:${s},count:50,origin:CurationHub,query:(flagshipSearchIntent:MYNETWORK_CURATION_HUB,includeFiltersInResponse:true,queryParameters:List((key:resultType,value:List(${tipo})))))&queryId=${QUERY_ID}`;
      const j = await (await fetch(u, { headers: H })).json();
      let n = 0;
      (j.included || []).forEach(x => {
        if (x.navigationUrl && x.navigationUrl.includes('/in/') && x.title) {
          const slug = x.navigationUrl.split('/in/')[1].split(/[/?]/)[0];
          if (!vistos.has(slug)) { vistos.add(slug); n++;
            destino.push({ nome: x.title.text, titulo: (x.primarySubtitle || {}).text || '',
                           url: `https://www.linkedin.com/in/${slug}/` }); }
        }
      });
      console.log(tipo, destino.length);
      if (!n) break;
      await pausa(500);
    }
  }
  await lista('FOLLOWERS', out.seguidores);
  await lista('PEOPLE_FOLLOW', out.seguindo);

  const blob = new Blob([JSON.stringify(out, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'rede_linkedin.json'; a.click();
  console.log(`Pronto: ${out.conexoes.length} conexões, ${out.seguidores.length} seguidores, ${out.seguindo.length} seguidos.`);
})();
