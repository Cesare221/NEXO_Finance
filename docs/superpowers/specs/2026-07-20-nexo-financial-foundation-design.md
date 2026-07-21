# Nexo: base financeira funcional, dados demonstrativos e temas

Data: 2026-07-20
Status: aprovado para planejamento

## Objetivo

Transformar os fluxos financeiros centrais do Nexo em uma experiência completa e verificável. O trabalho cobre dados demonstrativos opcionais, tema escuro, exclusão segura de categorias, refinamento do cadastro de cartões e correções funcionais diretamente relacionadas.

## Decisões aprovadas

- Dados demonstrativos são opcionais e nunca aparecem automaticamente em contas novas.
- O dataset é persistido no backend, participa de saldos, gráficos, faturas e consultas do Fin.
- A instalação usa uma operação transacional, idempotente e isolada por usuário.
- Os dados demonstrativos podem ser limpos com uma única ação sem remover registros reais.
- Categoria nunca utilizada é excluída definitivamente; categoria relacionada a histórico é arquivada.
- O tema escuro usa a direção visual Petróleo Nexo.
- O cadastro de cartão usa uma tela única organizada, com prévia e campos agrupados.

## Auditoria atual

1. O dia de fechamento do cartão é armazenado, mas a fatura é calculada pelo mês civil da compra.
2. O onboarding atual é informativo e não cria a estrutura financeira inicial.
3. O endpoint de exclusão de categoria sempre arquiva, mesmo sem dependências.
4. A árvore de categorias retornada pelo backend inclui categorias arquivadas.
5. O frontend usa cores literais sem um conjunto completo de tokens para modo escuro.
6. O formulário de cartão não possui prévia, formatação monetária, prevenção de duplicidade ou explicação do ciclo.

## Dataset demonstrativo

### Estrutura

Será criado um modelo `DemoDataset` vinculado ao usuário, com versão, status, data de instalação e manifesto dos recursos gerados. Os registros financeiros demonstrativos terão vínculo explícito com esse dataset.

O endpoint de instalação deve:

1. Verificar se já existe um dataset ativo da mesma versão para o usuário.
2. Criar todos os recursos em uma única transação de banco.
3. Registrar um evento de auditoria sem incluir dados financeiros sensíveis no payload.
4. Retornar um resumo das quantidades e valores criados.

O endpoint de limpeza deve:

1. Localizar apenas recursos pertencentes ao dataset do usuário autenticado.
2. Remover primeiro transações, faturas e demais dependências demonstrativas.
3. Remover contas, categorias e cartões que continuem exclusivamente demonstrativos.
4. Preservar e desvincular do dataset qualquer recurso que tenha adquirido dependências reais.
5. Registrar quantidades removidas e preservadas na auditoria.

### Conteúdo

- Conta principal, tipo corrente, saldo inicial de R$ 6.450,80.
- Reserva, tipo poupança, saldo inicial de R$ 12.000,00.
- Carteira, saldo inicial de R$ 180,00.
- Cartão principal com limite de R$ 7.000,00, fechamento no dia 10, vencimento no dia 17 e pagamento pela conta principal.
- Categorias de renda, moradia, alimentação, transporte, saúde, lazer e assinaturas, incluindo subcategorias úteis.
- Receitas e despesas distribuídas entre o mês atual e meses anteriores.
- Compras no cartão suficientes para gerar fatura aberta e limite utilizado.
- Uma regra recorrente de despesa para demonstrar compromissos futuros.

As datas são relativas ao dia da instalação para que dashboard e gráficos permaneçam úteis em qualquer mês ou ano.

## Experiência do dataset

- Onboarding e dashboard vazio exibem `Explorar com dados de exemplo`.
- Antes da instalação, uma confirmação resume contas, cartão, categorias e movimentações que serão criados.
- Durante instalação e limpeza, a ação fica bloqueada e mostra progresso.
- Configurações exibe o estado do dataset e a ação `Limpar dados de exemplo` quando ele estiver ativo.
- Após qualquer operação, dashboard, listas financeiras e contexto do Fin recebem o evento de atualização global.
- Falhas apresentam mensagem acionável e não deixam um conjunto parcialmente criado.

## Tema claro e escuro

### Preferência

Configurações terá um controle segmentado com `Sistema`, `Claro` e `Escuro`. A escolha será salva no perfil do usuário e em armazenamento local para aplicação imediata no dispositivo.

Um script executado antes da hidratação aplica `data-theme` no elemento raiz, evitando troca visível de cores. A opção `Sistema` acompanha `prefers-color-scheme` e reage a mudanças do sistema.

### Direção visual

O tema escuro Petróleo Nexo usa fundo verde-petróleo quase preto, superfícies elevadas discretamente esverdeadas, texto claro e destaques de coral, verde e amarelo já presentes na marca. As cores funcionais de receita, despesa, sucesso, alerta e erro mantêm contraste e não dependem apenas da cor.

As cores do app serão convertidas para tokens semânticos de canvas, superfície, superfície suave, texto, texto secundário, borda, ação primária, foco e estados. Componentes não devem introduzir cores de tema diretamente.

## Exclusão de categorias

O serviço verificará, dentro do usuário autenticado:

- transações vinculadas;
- planos de parcelas;
- regras recorrentes;
- subcategorias;
- propostas pendentes que referenciem a categoria, quando aplicável.

Sem dependências, a categoria é excluída definitivamente. Com qualquer dependência, ela e as subcategorias necessárias são arquivadas para preservar o histórico. A resposta informa `action: deleted` ou `action: archived`.

O frontend usa a ação `Excluir categoria`, explica antecipadamente que dados históricos causam arquivamento e apresenta o resultado real após a operação. Categorias arquivadas não aparecem na árvore ativa nem em seletores de novos lançamentos.

## Cadastro e ciclo do cartão

### Formulário

- Tela única com blocos `Identificação` e `Ciclo e pagamento`.
- Prévia visual contendo nome e limite.
- Campo monetário formatado em BRL sem alterar o valor decimal enviado à API.
- Campos de fechamento e vencimento com ajuda contextual.
- Conta de pagamento obrigatória e ação direta para criar uma conta quando a lista estiver vazia.
- Erros junto ao campo, estado de salvamento e proteção contra envio duplicado.
- Nome duplicado entre cartões ativos do mesmo usuário é rejeitado.
- Duas colunas no desktop e uma coluna no celular.

### Regra da fatura

O período considera o dia de fechamento do cartão:

- compra realizada até o fechamento entra na fatura corrente;
- compra após o fechamento entra no ciclo seguinte;
- o vencimento é calculado depois do encerramento do ciclo;
- dias inexistentes em meses curtos usam o último dia válido;
- viradas de mês e ano são tratadas explicitamente.

Alterar fechamento ou vencimento afeta apenas novos ciclos. Faturas já criadas preservam seus períodos e vencimentos.

## Refino dos fluxos relacionados

- Contas, categorias, cartões e transações compartilham estados de carregamento, vazio, sucesso e erro consistentes.
- Ações financeiras disparam atualização do dashboard e do contexto do Fin.
- Saldos bancários não são reduzidos por compras no cartão; somente o pagamento da fatura reduz a conta vinculada.
- Transferências não contam como receita ou despesa.
- Arquivamento preserva histórico e bloqueia novos lançamentos no recurso arquivado.
- Operações destrutivas exigem confirmação com descrição do impacto.

## API e segurança

- Todos os endpoints são autenticados e filtrados por `user_id`.
- Instalação, limpeza, exclusão e arquivamento são auditados.
- Dataset e limpeza usam transações de banco.
- Operações repetidas retornam estado estável e não duplicam lançamentos.
- Validação de origem permanece obrigatória nas rotas BFF mutáveis.
- Respostas não expõem manifestos internos ou identificadores de outros usuários.

## Testes e aceite

### Backend

- instalação completa, idempotência e rollback;
- isolamento entre usuários;
- limpeza seletiva e preservação de recursos adotados por dados reais;
- exclusão definitiva de categoria sem dependências;
- arquivamento com transação, filho, parcela ou recorrência;
- árvore e seletores sem categorias arquivadas;
- duplicidade de cartão ativo;
- compras antes, no dia e depois do fechamento;
- meses curtos e virada de ano;
- pagamento de fatura e saldo da conta;
- auditoria das novas operações.

### Frontend

- controle de tema e persistência entre recargas;
- aplicação sem flash de tema incorreto;
- contraste, foco e estados nos dois temas;
- instalação e limpeza de dataset com confirmação e feedback;
- formulário de cartão em desktop e celular;
- ação de exclusão mostrando `Excluída` ou `Arquivada`;
- atualização do dashboard após mutações.

### Verificação final

- suíte completa da API;
- smoke tests e build de produção do frontend;
- migração até um único head;
- screenshots em desktop e celular nos temas claro e escuro;
- teste visual de contas, categorias, cartões, dashboard e Configurações;
- atualização do grafo do projeto.

## Fora do escopo desta fase

- conexão Open Finance com bancos reais;
- importação automática de faturas por instituição;
- compartilhamento de conta financeira entre usuários;
- múltiplos workspaces ou organizações;
- alteração do e-mail de autenticação.
