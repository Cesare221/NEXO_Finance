# Resposta A Incidentes Do Nexo

Este documento define o processo operacional para triagem, contencao, comunicacao e pos-falha de incidentes de seguranca e privacidade no Nexo.

## Classificacao De Severidade

| Nivel | Descricao | Tempo De Resposta |
|-------|-----------|-------------------|
| **P0 — Critico** | Vazamento confirmado de dados pessoais, falha autenticacao em massa, acesso nao autorizado a contas | 1 hora |
| **P1 — Alto** | Servico indisponivel, falha de integracao critica (banco, email), suspeita de comprometimento | 4 horas |
| **P2 — Medio** | Anomalia monitorada, erro recorrente em endpoint nao critico, degradacao de performance | 24 horas |
| **P3 — Baixo** | Bug funcional sem impacto de seguranca, melhoria de observabilidade | Proximo ciclo |

## Papeis

- **Responsavel tecnico**: Coordena triagem tecnica, contencao e correcao.
- **Responsavel juridico**: Avalia obrigatoriedade de comunicacao a ANPD e titulares.
- **Encarregado de dados**: Ponto de contato para titulares e autoridades.
- **Operador de infraestrutura**: Executa rotacao de segredos, isolamento de servicos e restores.

## Fluxo De Resposta

### 1. Triagem (0–30 min)

1. Identificar o sinal: alerta Sentry, relato de usuario, anomalia de logs.
2. Classificar severidade (P0–P3).
3. Abrir registro do incidente com: timestamp, sinal original, ambiente, servicos afetados.

### 2. Contencao (imediato)

- **Credenciais comprometidas**: Revogar todas as sessoes do usuario afetado (`token_version` increment). Rotacionar a credencial exposta (API key, SECRET_KEY, MFA_ENCRYPTION_KEYS).
- **Servico comprometido**: Desativar endpoint ou feature flag. Isolar via variavel de ambiente ou deploy anterior.
- **Integracao comprometida**: Desativar integracao (ex: Groq, Resend). Ativar mecanismo local para IA.
- **Dados expostos**: Nao ampliar exposicao. Preservar evidencias em logs estruturados (request_id, timestamp, route).

### 3. Preservacao De Evidencias

- Nao deletar logs, breadcrumbs ou traces Sentry do periodo afetado.
- Exportar e salvar: logs JSON do periodo, Sentry events, traces de requisicao, estado do banco (snapshots, nao mutacoes).
- Armazenar evidencias em local separado do ambiente de producao.

### 4. Avaliacao De Impacto

Responder as perguntas:

1. Quais dados pessoais foram afetados? (nome, email, telefone, dados financeiros, hashes)
2. Quantos titulares foram impactados?
3. Qual o vetor de ataque? (IDOR, SQL injection, prompt injection, credencial exposta)
4. Os dados foram compartilhados com terceiros? (Sentry, Groq, Resend)
5. Existe risco de dano relevante aos titulares?

### 5. Comunicacao

#### Interna

- Notificar equipe tecnica imediatamente.
- Notificar responsavel juridico se houver potencial de notificacao a ANPD.

#### Externa (quando obrigatorio)

- **ANPD**: Comunicar vazamento de dados pessoais que possa causar risco ou dano relevante, no prazo maximo de 2 dias uteis apos a ciencia (Art. 48, LGPD).
- **Titulares**: Comunicar de forma clara, incluindo: natureza dos dados, medidas tomadas, direitos do titular, canal de duvidas.
- **Subprocessadores**: Notificar se o incidente envolver dados tratados por terceiros (Groq, Resend, Railway, Vercel).

### 6. Correcao E Validacao

1. Implementar correcao na causa raiz.
2. Validar em homologacao com testes de regressao.
3. Deploy em producao com monitoramento reforçado.
4. Confirmar que o sinal original nao persiste.

### 7. Pos-Falha

1. Documentar: cronologia, causa raiz, acoes tomadas, tempo de resposta.
2. Identificar melhorias: controles, alertas, testes, runbooks.
3. Atualizar este documento e SECURITY_AND_LGPD.md se aplicavel.
4. Revisar com equipe para prevenir recorrencia.

## Cenarios Especificos

### Comprometimento De Chave TOTP

1. O suporte NAO pode recuperar chave TOTP perdida.
2. Se todos os codigos de recuperacao forem perdidos: intervencao manual do operador.
3. Operador pode redefinir senha apenas via fluxo de recuperacao de e-mail.

### Prompt Injection No Fin

1. Se o modelo retornar dados de outro usuario ou acoes nao autorizadas: desativar IA imediatamente.
2. Revogar sessoes afetadas.
3. Verificar se o mecanismo local esta funcionando corretamente.
4. Revisar logs de prompts e respostas do periodo.

### Falha De Integracao Externa

- **Groq indisponivel**: Mecanismo local ativa automaticamente. Nenhum dado e enviado.
- **Resend indisponivel**: Emails ficam em fila. Verificar logs de envio.
- **Railway/Vercel indisponivel**: Verificar status pages e health checks.

## Contatos De Emergencia

| Papel | Contato | Disponibilidade |
|-------|---------|-----------------|
| Responsavel tecnico | [definir] | Horario comercial + on-call |
| Responsavel juridico | [definir] | Horario comercial |
| Encarregado de dados | [definir] | Horario comercial |
| Supabase/Railway support | [portal de suporte] | 24/7 (planos pagos) |
| Sentry support | [portal de suporte] | 24/7 (planos pagos) |

## Chaves De Monitoramento

- **Sentry**: Alertas para novos tipos de erro, spike de erros, falha de readiness.
- **Railway**: Alertas de health check, uso de CPU/memoria, restarts.
- **Logs estruturados**: Alertas para 4xx/5xx acima do threshold, latencia elevada.
- **Rate limiting**: Alertas para tentativas de autenticacao excedendo limites.
