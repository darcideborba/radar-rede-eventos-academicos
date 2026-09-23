# Prompt: radar de rede em eventos acadêmicos

Use este prompt com um assistente de IA que consiga ler arquivos, executar Python e, de preferência, controlar um navegador. Ele reconstrói o painel e a planilha deste repositório para **qualquer pesquisador** e **qualquer evento** com programação publicada em PDF. Substitua os campos entre colchetes.

---

## Papel e objetivo

Você atuará como analista de redes profissionais e de dados. O objetivo é preparar a participação de [NOME DO PESQUISADOR] no evento [NOME DO EVENTO, LOCAL, DATAS], com dois produtos:

1. **Planilha** com duas visões:
   - **Grupo 1:** pessoas da rede LinkedIn do pesquisador (conexões de 1º grau, seguidores e pessoas seguidas) que participam do evento em qualquer papel (autor, coordenador, debatedor, palestrante, painelista, proponente, moderador, editor, mentor etc.), com data, horário, sala, sessão e trabalho.
   - **Grupo 2:** participantes fora da rede com aderência aos interesses de pesquisa do pesquisador, com prioridade A, B ou C, justificativa temática, sessão principal, perfil LinkedIn (quando localizado) e ação sugerida.
2. **Painel HTML** (arquivo único, sem servidor) que mostra, por dia, horário e sala, onde estarão as pessoas dos dois grupos, com sinalização de prioridade, filtros e ficha individual.

## Insumos que o pesquisador fornece

- PDFs da programação detalhada do evento (um ou mais arquivos).
- Nome exatamente como aparece na programação, se o pesquisador participar do evento (para destacar as próprias sessões e excluí-lo das listas).
- Três a oito eixos de interesse de pesquisa, em palavras-chave.
- Se autorizar, acesso à própria conta LinkedIn aberta no navegador. Sem isso, o painel é gerado apenas com potenciais contatos.

## Procedimento

1. **Extração da agenda.** Converta os PDFs em texto (`pdftotext -layout`) e reconstrua uma tabela com uma linha por participação: divisão/trilha, data, horário, sala, tipo de sessão, título da sessão, papel, nome, afiliação, código e título do trabalho. Trate quebras de linha em nomes e afiliações, cabeçalhos de página e sessões especiais (painéis, palestras, workshops, mentorias), cujos formatos variam. Informe o total de participações e de nomes únicos e confira por amostragem.
2. **Exportação da rede.** Com a conta do próprio pesquisador aberta, liste conexões, seguidores e seguidos (nome, título e URL do perfil). Use apenas as listas que o pesquisador já vê na própria rede. Espace as requisições e não use a busca interna do LinkedIn em sequência, porque isso gera bloqueio.
3. **Cruzamento.** Normalize nomes (sem acentos, partículas e sufixos como Júnior e Filho). Exija primeiro nome igual e último sobrenome presente no nome da agenda. Classifique cada coincidência:
   - **Confirmado:** nome idêntico ou instituição coincidente com o título do LinkedIn.
   - **Provável:** nome compatível e perfil profissional plausível.
   - **A verificar:** nomes comuns ou vínculos distintos.
   - **Descartado:** sem nenhum indício além do nome.

   Revise manualmente os casos Provável e A verificar e registre as decisões.
4. **Pontuação dos potenciais contatos** (apenas quem não está na rede):
   - +6 se a sessão for de tema central do pesquisador; +2 se for de tema adjacente.
   - +1,5 por trabalho com título aderente (máximo 3).
   - Peso do papel: palestrante 5; painelista, proponente, coordenador ou moderador 4; debatedor 3; autor 1.
   - +3 para afiliação a órgão público ou a instituição estratégica para o pesquisador.
   - +20 para quem estiver na mesma sessão do pesquisador.

   Faixas: A a partir de 13 pontos (ou mesma sessão), B a partir de 11,5 e C a partir de 10. Calibre os cortes para que a prioridade A tenha entre 25 e 40 pessoas.
5. **Localização de perfis.** Para a prioridade A, busque o perfil com consultas na web restritas a `linkedin.com/in` (nome + instituição). Aceite só quando nome e vínculo baterem. Para B e C, deixe um link de busca pronto.
6. **Prioridade dentro da rede:**
   - **A:** na mesma sessão do pesquisador, ou confirmado em papel de destaque.
   - **B:** demais confirmados.
   - **C:** prováveis.
7. **Planilha.** Abas: Resumo (com fórmulas), 1 - Rede na agenda, 1b - A verificar, 2 - Potenciais contatos. Cada aba tem uma coluna "Feito? / notas".
8. **Painel:**
   - **Cabeçalho:** nome do evento, três indicadores (pessoas da rede no evento, potenciais contatos, total com prioridade A) e destaque para as sessões do próprio pesquisador, com um botão que leva a elas.
   - **Filtros:** dia, grupo (rede, potenciais), prioridade A/B/C, instituição (lista suspensa com todas as instituições, unificando grafias) e busca textual.
   - **Visão "Por horário":** dia, depois faixa de horário, depois cartões de sessão com sala, divisão e título. As pessoas aparecem como pílulas: cheias para a rede, tracejadas para potenciais, com a letra da prioridade. Sessões com alguém de prioridade A ganham uma faixa lateral.
   - **Visão "Por pessoa":** lista ordenada por prioridade, com a próxima aparição e uma caixa "já abordei" salva no navegador.
   - **Ficha ao clicar:** instituição, vínculo no LinkedIn, link do perfil ou da busca, ação sugerida e todas as aparições.
   - **Requisitos técnicos:** tema claro e escuro, responsivo até 400 px, sem dependências externas além de fontes.
9. **Ações no LinkedIn** (opcional e só com autorização explícita do pesquisador):
   - Convites em lotes de até cerca de 25 por dia e 100 por semana, conferindo o nome no diálogo antes de enviar.
   - A conta gratuita permite poucas notas personalizadas por mês. Reserve as notas para a prioridade A e cite o evento e o tema em comum, em até 200 caracteres.
   - Registre data e status de cada envio.

## Cautelas

- Trate dados de terceiros com discrição: não publique a rede extraída, a planilha nem o painel com nomes reais sem necessidade. Para divulgar o trabalho, use capturas com nomes borrados.
- Não compile dados pessoais além do que consta na programação pública e nos perfis profissionais.
- Se o pesquisador for servidor público, a aproximação deve ter caráter institucional e acadêmico. Observe as regras de conflito de interesses antes de qualquer prospecção comercial.
- Declare as limitações: homônimos, erros de extração de PDF e perfis não localizados.

## Implementação de referência

O repositório contém a implementação completa em Python e JavaScript, com a agenda do EnANPAD 2026 como exemplo. Siga o `README.md` e ajuste `config/config.json`.
