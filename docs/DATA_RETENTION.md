# Retencao De Dados Do Nexo

Este documento define as politicas de retencao e exclusao de dados do Nexo, conforme necessidade operacional, obrigatoriedade legal e principios de minimizacao da LGPD.

## Politica Geral

O Nexo retem dados apenas pelo tempo necessario para a finalidade para a qual foram coletados ou para cumprir obrigacao legal. Apos o vencimento do periodo de retencao, os dados sao excluidos ou anonimizados de forma segura.

## Periodos De Retencao

### Dados De Conta

| Dado | Retencao | Acao Ao Vencimento |
|------|----------|-------------------|
| Dados do perfil (nome, email, telefone) | Enquanto a conta existir | Exclusao completa a pedido do titular |
| Hash de senha | Enquanto a conta existir | Exclusao com a conta |
| Preferencias e configuracoes | Enquanto a conta existir | Exclusao com a conta |
| Avatar | Enquanto a conta existir | Exclusao com a conta |
| Consentimento de IA | Enquanto a conta existir | Exclusao com a conta |
| Versao da politica de privacidade aceita | Enquanto a conta existir | Exclusao com a conta |

### Tokens De Seguranca

| Dado | Retencao | Acao Ao Vencimento |
|------|----------|-------------------|
| Token de verificacao de e-mail (expirado) | Apos expiracao + 30 dias | Exclusao automatica via cron |
| Token de recuperacao de senha (expirado) | Apos expiracao + 30 dias | Exclusao automatica via cron |
| Challenge MFA (expirado) | Apos expiracao + 30 dias | Exclusao automatica via cron |
| Refresh tokens (familia de sessao) | Ate revogacao ou expiracao | Exclusao automatica |

### Dados De Sessao

| Dado | Retencao | Acao Ao Vencimento |
|------|----------|-------------------|
| Sessoes ativas | Ate logout ou revogacao | Exclusao automatica |
| Historico de login (sem IP) | 90 dias | Exclusao automatica |

### Dados Financeiros

| Dado | Retencao | Acao Ao Vencimento |
|------|----------|-------------------|
| Contas e categorias | Enquanto a conta existir | Exclusao com a conta |
| Transacoes e movimentacoes | Enquanto a conta existir | Exclusao com a conta |
| Recorrencias e parcelas | Enquanto a conta existir | Exclusao com a conta |
| Auditoria financeira (logs de acao) | Conforme obrigacao fiscal (a definir) | Revisao juridica necessaria |

### Dados De Operacoes

| Dado | Retencao | Acao Ao Vencimento |
|------|----------|-------------------|
| Logs tecnicos (JSON, sem conteudo financeiro) | 30 a 90 dias | Exclusao automatica |
| Sentry events (scrubbed) | Conforme plano Sentry (90 dias padrao) | Expiracao automatica |
| Railway logs | Conforme plano Railway | Expiracao automatica |
| Request IDs | 30 dias | Exclusao automatica |

### Dados De IA

| Dado | Retencao | Acao Ao Vencimento |
|------|----------|-------------------|
| Prompts e respostas do Fin | Nao registrar por padrao | N/A |
| Propostas do Fin (rascunhos) | Enquanto a conta existir | Exclusao com a conta |
| Zero Data Retention (Groq) | Imediato | N/A |

## Exclusao De Conta

Quando um titular solicita a exclusao da conta:

1. **Identificacao**: Confirmar identidade via senha ou fluxo de autenticacao.
2. **Verificacao**: Confirmar que nao ha obrigacao legal de retencao para os dados especificos.
3. **Exclusao**: Remover todos os dados associados a conta, incluindo:
   - Dados de perfil
   - Tokens de seguranca
   - Sessoes ativas
   - Avatar
   - Dados financeiros (contas, categorias, transacoes, recorrencias)
   - Rascunhos de propostas do Fin
4. **Confirmacao**: Registrar a exclusao com timestamp e dados minimos para auditoria (sem dados pessoais).
5. **Subprocessadores**: Notificar subprocessadores para excluir dados tratados (Groq, Resend).

## Mantencao Automatica

O cron de manutencao (`python -m app.maintenance purge-expired-security-records`) roda diariamente as 03:17 UTC e exclui:

- Account action tokens expirados ha mais de 30 dias.
- MFA challenges expirados ha mais de 30 dias.

O cron NAO exclui:

- Dados de conta ou perfil.
- Dados financeiros.
- Logs de auditoria.
- Sessoes ativas.
- Registros obrigatorios por lei.

## Excecoes Legais

Alguns dados podem ser retidos alem do periodo padrao por obrigacao legal:

- **Obrigacao fiscal**: Registros financeiros podem ser retidos conforme legislacao tributaria aplicavel.
- **Prevencao a fraude**: Logs de autenticacao podem ser retidos para investigacao.
- **Ordem judicial**: Dados podem ser retidos se houver ordem judicial especifica.

Nessas excecoes, os dados sao isolados do ambiente de producao e excluidos assim que a obrigacao cessar.

## Direitos Do Titular

Conforme a LGPD, o titular tem direito a:

- **Acesso**: Solicitar acesso aos dados pessoais tratados.
- **Correcao**: Corrigir dados incompletos ou desatualizados.
- **Anonimizacao**: Solicitar anonimizacao de dados desnecessarios.
- **Portabilidade**: Solicitar exportacao dos dados em formato estruturado.
- **Eliminacao**: Solicitar exclusao dos dados pessoais.
- **Revogacao de consentimento**: Revogar consentimento para tratamento de dados.
- **Oposicao**: Opor-se ao tratamento de dados em bestimmte situações.

Solicitacoes que dependam de obrigacao legal, oposicao, anonimizacao ou revisao de retencao precisam de processo operacional e canal humano documentado.

## Contato

Para solicitacoes de dados ou duvidas sobre retencao:

- **Encarregado de dados**: [definir email]
- **Canal de suporte**: [definir canal]
- **Prazo de resposta**: 15 dias uteis (conforme Art. 18, LGPD)
