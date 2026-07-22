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
- Logs tecnicos sem conteudo financeiro: 30 a 90 dias, conforme necessidade comprovada.
- Auditoria financeira: definir prazo com revisao juridica e obrigacao fiscal aplicavel.
- Backups: retencao curta e documentada, com expiracao que tambem respeite exclusoes.
- Prompts e respostas do Fin: nao registrar por padrao.

## Resposta A Incidentes

1. Isolar a credencial, sessao, servico ou integracao afetada.
2. Revogar familias de sessao e rotacionar segredos quando aplicavel.
3. Preservar evidencias sem ampliar a exposicao de dados pessoais.
4. Avaliar impacto, titulares, natureza dos dados e medidas de contencao.
5. Acionar responsavel juridico e encarregado para avaliar comunicacoes a ANPD e titulares.
6. Corrigir a causa, validar em homologacao e registrar as acoes tomadas.
