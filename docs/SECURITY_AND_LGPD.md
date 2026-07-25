# Seguranca E LGPD Do Nexo

Este documento descreve controles tecnicos do produto. Ele nao substitui revisao juridica, pentest independente ou configuracao segura da infraestrutura.

## Controles Implementados

- Senhas com Argon2id e migracao de hashes legados.
- Access tokens curtos e refresh tokens armazenados somente como fingerprint.
- Rotacao atomica de refresh token com familia de sessao e revogacao da familia em caso de reutilizacao.
- Cookies `HttpOnly`, `Secure` em producao, `SameSite=Strict` e prefixo `__Host-` em producao.
- CORS e hosts explicitos, cabecalhos defensivos, limite de corpo e IDs de requisicao.
- Rate limiting distribuido via Redis obrigatorio em producao para autenticacao, escrita financeira e Fin.
- Propostas do Fin com schema estrito, idempotencia, isolamento por usuario, expiracao, auditoria e aprovacao humana.
- Groq `openai/gpt-oss-20b` sem acesso direto ao banco e com ferramentas somente para leitura e criacao de rascunho.
- Consentimento revogavel para IA externa; sem consentimento o Fin usa o mecanismo local.
- Exportacao dos dados sem hashes de senha ou refresh token e exclusao de conta confirmada por senha.
- Gerenciamento e revogacao de sessoes ativas.
- Avatar validado por MIME, assinatura binaria, Base64 e limite de tamanho.
- CI com testes, lockfiles com hashes, `pip-audit`, `npm audit`, CodeQL e dependency review.
- Verificacao de e-mail com tokens unicos e expiracao (30 minutos).
- Recuperacao de senha com tokens expirados (20 minutos), revogacao de todas as sessoes ativas.
- MFA TOTP com chaves criptografadas (Fernet), 10 codigos de recuperacao de uso unico (Argon2 hash), e limitacao de 5 tentativas de challenge.

## Fronteira De Confianca Do Fin

O modelo e tratado como entrada nao confiavel. Ele pode solicitar apenas:

1. Resumo financeiro do usuario autenticado.
2. Movimentacoes recentes do mesmo usuario.
3. Preparacao de receita ou despesa pendente.

Toda ferramenta valida argumentos no servidor. IDs de conta e categoria sao novamente verificados contra o usuario. O modelo nunca recebe segredos, credenciais de banco ou ferramenta de execucao financeira. Falha, timeout ou limite da Groq ativa o mecanismo local.

## Bloqueadores Antes Da Producao Publica

- Configurar verificacao de e-mail, recuperacao de senha e MFA ou passkeys com provedores reais.
- Preencher identificacao legal do operador, encarregado, contato e prazos de retencao no Aviso de Privacidade.
- Assinar e revisar termos de tratamento de dados dos subprocessadores; habilitar Zero Data Retention na Groq.
- Ativar TLS, criptografia de banco e backups, banco privado, rotacao de segredos e separacao entre homologacao e producao.
- Configurar WAF, protecao contra bots, alertas de credential stuffing e monitoramento de anomalias.
- Executar pentest independente autenticado e nao autenticado, incluindo IDOR, CSRF, SSRF e prompt injection.
- Testar restauracao de backup e resposta a incidente antes de receber dados reais.

## Direitos Do Titular

O usuario pode corrigir o perfil, revogar consentimento de IA, exportar os dados e excluir a conta em Configuracoes. Solicitacoes que dependam de obrigacao legal, oposicao, anonimizacao ou revisao de retencao precisam de processo operacional e canal humano documentado.

## Retencao Recomendada

- Dados ativos: enquanto a conta existir e forem necessarios ao servico.
- Tokens de seguranca expirados: 30 dias, exclusao automatica via cron diario (`python -m app.maintenance purge-expired-security-records`, 03:17 UTC).
- Logs tecnicos sem conteudo financeiro: 30 a 90 dias, conforme necessidade comprovada.
- Sentry events (scrubbed): conforme plano (90 dias padrao).
- Auditoria financeira: definir prazo com revisao juridica e obrigacao fiscal aplicavel.
- Backups: retencao curta e documentada, com expiracao que tambem respeite exclusoes.
- Prompts e respostas do Fin: nao registrar por padrao.

Consulte `docs/DATA_RETENTION.md` para a politica completa e `docs/INCIDENT_RESPONSE.md` para o processo de resposta a incidentes.

## Controles De Identidade E MFA

### Temporizacao De Tokens

- Token de verificacao de e-mail: 30 minutos.
- Token de recuperacao de senha: 20 minutos.
- Challenge MFA (TOTP): 5 minutos.
- Access token JWT: configuravel (padrao 15 minutos).
- Refresh token: configuravel (padrao 7 dias).

### Comportamento De Revogacao

- Recuperacao de senha revoca todas as sessoes ativas do usuario e incrementa `token_version`.
- Desativacao MFA revoca todas as outras sessoes ativas do usuario.
- Reutilizacao de refresh token revoca toda a familia de sessao.
- Tokens invalidados retornam 401 Unauthorized.

### Variaveis De Ambiente Para Identidade

```text
MAIL_PROVIDER=resend              # "resend" em producao, "console" em desenvolvimento
RESEND_API_KEY=<chave-da-api>    # Obrigatoria quando MAIL_PROVIDER=resend
EMAIL_FROM=Nexo <no-reply@nexo.example>
PUBLIC_WEB_URL=https://app.nexo.example  # Deve ser HTTPS em producao
EMAIL_VERIFICATION_TTL_MINUTES=30
PASSWORD_RESET_TTL_MINUTES=20
MFA_CHALLENGE_TTL_MINUTES=5
MFA_ENCRYPTION_KEYS=v1:<chave-fernet>    # Formato: versao:chave-fernet
MFA_ACTIVE_KEY_VERSION=v1
```

### MFA E Recuperacao

- Cada usuario pode ter apenas um metodo TOTP ativo.
- A chave TOTP e criptografada com Fernet (chave dedicada, nao SECRET_KEY).
- 10 codigos de recuperacao sao gerados na ativacao do MFA; cada codigo e de uso unico.
- Cada tentativa de challenge e limitada a 5 tentativas.
- Regeneracao de codigos de recuperacao requer senha atual e invalida os anteriores.
- Desativacao MFA requer senha + codigo TOTP ou de recuperacao.

### Suporte E Recuperacao

- O suporte NAO pode recuperar uma chave TOTP perdida. O usuario deve usar um codigo de recuperacao.
- Se todos os codigos de recuperacao forem perdidos e a chave TOTP for inacessivel, a conta requer intervencao manual do operador.
- Operadores podem redefinir senha apenas via fluxo de recuperacao de e-mail.
- Nenhum funcionario ou sistema interno tem acesso a senhas ou chaves TOTP em texto plano.

## Resposta A Incidentes

1. Isolar a credencial, sessao, servico ou integracao afetada.
2. Revogar familias de sessao e rotacionar segredos quando aplicavel.
3. Preservar evidencias sem ampliar a exposicao de dados pessoais.
4. Avaliar impacto, titulares, natureza dos dados e medidas de contencao.
5. Acionar responsavel juridico e encarregado para avaliar comunicacoes a ANPD e titulares.
6. Corrigir a causa, validar em homologacao e registrar as acoes tomadas.
