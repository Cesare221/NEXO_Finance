# Nexo: dashboard-first com painel contextual do Fin

**Data:** 2026-07-17  
**Status:** aprovado pelo usuario

## Objetivo

Reformular a experiencia do Nexo com a densidade, clareza editorial e revisao contextual associadas ao Pierre, sem transformar a conversa com o agente na tela principal. O dashboard continua sendo a pagina inicial autenticada e deve apresentar saldos, graficos, indicadores, vencimentos e medidas financeiras diretamente na tela. A conversa permanece disponivel no lado direito de todo o ambiente autenticado.

## Marca e nomenclatura

- `Nexo` e o nome do aplicativo e aparece em login, cadastro, cabecalho, metadados, manifesto PWA e textos institucionais.
- `Fin` e o nome exclusivo do agente financeiro e aparece no chat, em respostas, propostas e notificacoes reconhecidas pelo agente.
- A interface nao usa `Fin` como nome do produto nem `Nexo` como nome do agente.
- Nomes tecnicos internos, cookies e rotas podem ser migrados separadamente quando a troca imediata puder invalidar sessoes existentes.

## Decisoes aprovadas

1. A rota inicial autenticada continua sendo `/dashboard`.
2. O dashboard e a superficie principal do produto, com dados financeiros visiveis antes de qualquer conversa.
3. A navegacao global usa um botao de menu sanduiche como padrao em desktop, tablet e celular.
4. O Fin aparece em uma caixa de conversa fixa no lado direito de todas as paginas autenticadas em telas largas.
5. O Fin pode reconhecer e preparar movimentacoes autonomamente, mas nunca inclui uma movimentacao no livro financeiro sem aprovacao explicita.
6. Movimentacoes reconhecidas aparecem como notificacoes agrupadas em uma central de revisao dentro do aplicativo.

## Estrutura da tela

### Barra superior

A barra superior ocupa toda a largura e contem:

- botao sanduiche no canto esquerdo;
- marca Nexo e titulo da pagina atual;
- seletor de periodo quando aplicavel;
- acao primaria contextual, como `Nova transacao`;
- perfil e estado de sessao no canto direito.

Ela permanece compacta e fixa durante a rolagem. O botao sanduiche e o unico gatilho da navegacao global; nao existe sidebar de navegacao permanentemente aberta.

### Menu sanduiche

O menu abre um drawer lateral com:

- Dashboard;
- Contas;
- Cartoes;
- Transacoes;
- Categorias;
- Conversas com o Fin;
- Configuracoes;
- instalar aplicativo, quando a instalacao PWA estiver disponivel;
- identificacao da conta e acao de sair.

O drawer deve manter foco preso enquanto aberto, fechar com `Escape`, fechar ao selecionar um destino e devolver o foco ao botao de abertura. No desktop, ocupa no maximo 320 px. No celular, usa a largura disponivel com margem lateral de seguranca.

O item `Revisar movimentacoes` mostra um badge com a quantidade pendente e leva diretamente ao grupo de propostas aguardando decisao.

### Dashboard

O conteudo principal mantem:

- saldo total, receitas, despesas e faturas;
- grafico comparativo de receitas e despesas;
- leitura financeira do periodo;
- diagnosticos de saude financeira;
- movimentacoes recentes;
- proximos vencimentos;
- atalhos para operacoes frequentes;
- central compacta de movimentacoes reconhecidas aguardando aprovacao.

Os valores devem vir da API do usuario autenticado. Dados demonstrativos nao podem ser apresentados como se fossem reais. Durante carregamento, o layout preserva suas dimensoes com skeletons. Sem dados, cada area mostra um estado vazio com uma proxima acao clara.

### Caixa de conversa do Fin

Em telas com pelo menos 1180 px de largura, o chat fica fixo na coluna direita do `AppShell`, com largura entre 340 e 400 px e altura limitada pela viewport. Ele permanece disponivel ao navegar entre dashboard, contas, cartoes, transacoes, categorias e configuracoes. O painel possui:

- cabecalho com identidade do Fin, status e acao de recolher;
- historico rolavel;
- sugestoes contextuais curtas;
- propostas financeiras dentro da conversa;
- compositor fixo na base;
- indicador de envio e mensagens de erro recuperaveis.

O painel nao deve cobrir graficos, metricas ou comandos do dashboard. A grade reserva sua largura explicitamente.

Entre 768 e 1179 px, o chat inicia recolhido e abre como painel lateral sobreposto. Abaixo de 768 px, abre em tela cheia sobre o dashboard e respeita as areas seguras do dispositivo. Um botao flutuante com icone de mensagem oferece acesso ao Fin quando o painel nao estiver visivel.

## Central de movimentacoes reconhecidas

O Fin pode reconhecer movimentacoes a partir de mensagens, importacoes e futuras integracoes autorizadas. O reconhecimento cria uma proposta pendente, sem alterar saldo, fatura ou historico financeiro.

As propostas aparecem como notificacoes dentro do aplicativo e sao agrupadas por origem, conta associada e data de reconhecimento. Cada grupo mostra a quantidade de itens e o impacto financeiro estimado. Cada movimentacao apresenta descricao, valor, tipo, conta, categoria, data, confianca do reconhecimento e possivel duplicidade.

Acoes disponiveis:

- aprovar uma movimentacao;
- aprovar itens selecionados do grupo;
- editar antes de aprovar;
- rejeitar;
- marcar como duplicada;
- abrir o contexto original no chat.

A aprovacao em lote exige selecao explicita dos itens. Itens com possivel duplicidade, valor acima do limite configurado ou baixa confianca nao podem ser aprovados em lote. A interface usa badge no menu sanduiche, aviso compacto no dashboard e uma lista de revisao expandida, sem depender de notificacao do sistema operacional.

Estados da movimentacao reconhecida:

- `pending_review`: reconhecida e aguardando decisao;
- `approved`: convertida em transacao uma unica vez;
- `rejected`: descartada sem impacto financeiro;
- `duplicate`: vinculada ou marcada como repetida;
- `expired`: precisa ser reconhecida novamente.

## Conversa e revisao

Perguntas de consulta, como saldo e gastos do mes, produzem respostas de leitura. Pedidos de alteracao geram uma proposta contendo tipo, valor, conta, categoria, data, descricao e impacto estimado no saldo.

Estados da proposta:

- `proposed`: permite editar, confirmar ou cancelar;
- `executed`: apresenta comprovacao e identificador da transacao;
- `cancelled`: permanece no historico sem alterar dados;
- `expired` ou `failed`: explica o motivo e permite preparar uma nova proposta.

Confirmacoes sao idempotentes. O frontend desabilita repeticoes enquanto a requisicao esta em andamento, mas a garantia principal permanece no backend.

## Arquitetura de componentes

- `AppShell`: barra superior, menu sanduiche, area principal e ponto de montagem do painel do Fin.
- `NavigationDrawer`: navegacao global acessivel e responsiva.
- `FinChatPanel`: controla abertura, recolhimento, historico e compositor.
- `FinConversation`: continua responsavel por mensagens e propostas, sem conhecer o posicionamento da pagina.
- `DashboardDataProvider`: agrega metricas, serie temporal, vencimentos e movimentacoes da API.
- `DashboardSections`: componentes visuais recebem dados tipados e estados de carregamento, vazio e erro.
- `MovementReviewInbox`: agrupa propostas pendentes, controla selecao e encaminha aprovacoes, edicoes e rejeicoes.
- `PendingMovementNotice`: resumo compacto usado no dashboard e no menu sanduiche.

O painel do Fin faz parte do `AppShell` e aparece em todas as paginas autenticadas. Cada pagina pode fornecer contexto adicional ao painel sem duplicar a logica de conversa.

## Dados e API

O frontend usa rotas BFF do Next.js para manter tokens fora do JavaScript do navegador. O dashboard precisa de uma rota autenticada agregada que retorne, no minimo:

- saldos e totais do periodo;
- serie mensal de receitas e despesas;
- transacoes recentes;
- faturas e vencimentos;
- pontuacoes ou insumos para diagnosticos.

Conversas e mensagens devem ser persistidas por usuario antes de habilitar retomada entre dispositivos. Ate essa persistencia existir, o painel deve comunicar que a conversa atual e temporaria, sem sugerir historico duravel.

As movimentacoes reconhecidas usam propostas persistidas no backend como fonte de verdade. Cada proposta registra origem, instante de reconhecimento, chave de agrupamento, nivel de confianca e sinal de possivel duplicidade. A confirmacao cria a transacao por uma chave idempotente unica; recarregar a pagina ou repetir uma requisicao nao pode duplicar o lancamento.

## Erros e resiliencia

- Falha total do dashboard mostra um estado de recuperacao sem remover a navegacao ou o chat.
- Falha de uma secao nao bloqueia as demais secoes.
- Falha no chat preserva a mensagem digitada e oferece nova tentativa.
- Falha ao aprovar um grupo identifica os itens concluidos e os itens que continuam pendentes; nao repete itens ja executados.
- Expiracao de sessao tenta renovacao uma vez e redireciona ao login se falhar.
- Nenhuma resposta financeira autenticada e armazenada no cache offline do service worker.

## Acessibilidade e responsividade

- Todos os controles possuem nome acessivel e foco visivel.
- Drawer e chat sobreposto prendem foco e restauram o foco de origem ao fechar.
- Graficos possuem resumo textual e tabela acessivel equivalente.
- Nao existe rolagem horizontal entre 320 e 1920 px.
- Botoes interativos possuem area minima de toque de 44 por 44 px no celular.
- Conteudo principal continua utilizavel com zoom de 200%.

## Criterios de aceite

1. Login bem-sucedido direciona para `/dashboard`.
2. Dashboard exibe informacoes e graficos sem exigir abertura do chat.
3. Menu sanduiche funciona em todos os breakpoints e substitui a navegacao lateral permanente.
4. Chat fica fixo a direita sem sobrepor o conteudo nas paginas autenticadas em telas largas.
5. Chat abre como painel lateral ou tela cheia em breakpoints menores.
6. Criar uma proposta pelo Fin nao altera saldo ou transacoes antes da confirmacao.
7. Dashboard nao exibe valores ficticios para um usuario sem dados.
8. Fluxos principais funcionam por teclado e leitor de tela.
9. Testes cobrem navegacao, breakpoints, consulta do Fin, proposta, edicao, cancelamento e confirmacao idempotente.
10. Movimentacoes reconhecidas aparecem agrupadas com badge de pendencias e permanecem sem impacto financeiro ate aprovacao.
11. Aprovacao individual ou em lote nao cria transacoes duplicadas, inclusive apos recarregar ou repetir a requisicao.
12. O produto e identificado como Nexo em todas as superficies; Fin identifica somente o agente.

## Fora do escopo desta reformulacao

- transformar o chat na pagina inicial;
- copiar marca, textos ou identidade proprietaria do Pierre;
- executar alteracoes financeiras sem aprovacao do usuario;
- armazenar dados financeiros privados no cache offline;
- substituir nesta fase todas as telas administrativas por conversas.

## Ordem recomendada

1. Aplicar a marca Nexo nas superficies do produto sem invalidar sessoes existentes.
2. Conectar dashboard a dados reais e criar estados de carregamento, vazio e erro.
3. Implementar barra superior e `NavigationDrawer`.
4. Implementar `MovementReviewInbox`, agrupamento e aprovacao idempotente.
5. Extrair e integrar `FinChatPanel` fixo e responsivo.
6. Persistir conversas e mensagens.
7. Completar CRUD financeiro e onboarding.
8. Adicionar IA estruturada, recuperacao de conta e endurecimento de producao.
