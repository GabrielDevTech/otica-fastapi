# Impersonation no Clerk - Entendendo o Comportamento

## O que é Impersonation?

**Impersonation** (ou "Impersonar Usuário") é uma funcionalidade do Clerk que permite que administradores façam login como outro usuário para debug ou suporte.

## Por que o Token Expira Rápido?

### Tokens de Impersonation Têm Validade Curta

Quando você usa **"Impersonate User"** no Clerk:

1. ⏱️ **Tokens expiram em ~60 segundos** (não horas como tokens normais)
2. 🔄 **Clerk gera novos tokens automaticamente** quando o anterior está próximo de expirar
3. 📝 **O log muda** porque cada novo token tem um `session_id` diferente

### Por que isso acontece?

**Segurança**: Tokens de impersonation são temporários por design:
- Limita o tempo que alguém pode estar impersonando
- Reduz risco se o token for comprometido
- Força renovação frequente para auditoria

## Estrutura do Token de Impersonation

### Token Normal
```json
{
  "sub": "user_xxx",
  "org_id": "org_xxx",
  "exp": 1764212801,  // ← Expira em horas
  "iat": 1764212001,
  ...
}
```

### Token de Impersonation
```json
{
  "act": {                    // ← Campo "act" indica impersonation
    "iss": "...",
    "sid": "session_xxx",     // ← Sessão original (admin)
    "sub": "user_admin"       // ← Usuário que está impersonando
  },
  "sub": "user_impersonado",  // ← Usuário sendo impersonado
  "org_id": "org_xxx",
  "exp": 1764212801,          // ← Expira em ~60 segundos!
  "iat": 1764212741,
  "sid": "session_yyy",       // ← Nova sessão (impersonation)
  ...
}
```

## Comportamento Observado

### 1. Token Expira Rápido
- ✅ **Normal**: Tokens normais duram 1 hora
- ⚠️ **Impersonation**: Tokens duram ~60 segundos

### 2. Token é Renovado Automaticamente
- O Clerk **gera novos tokens automaticamente** antes do anterior expirar
- Isso acontece no frontend (SDK do Clerk)
- Você não precisa fazer nada

### 3. Logs Mudam
- Cada novo token tem um `session_id` (`sid`) diferente
- Por isso você vê logs diferentes a cada renovação
- É comportamento esperado

## Como Verificar

### Verificar se é Token de Impersonation

```powershell
.\venv\Scripts\python.exe scripts\check_token_org.py seu_token_aqui
```

Se aparecer:
```
⚠️  Token é de IMPERSONATION
   Usuário original: user_admin
   Usuário impersonado: user_xxx
```

### Verificar Expiração

Decodifique o token em https://jwt.io e veja:
- `exp`: Timestamp de expiração
- `iat`: Timestamp de criação
- Diferença: ~60 segundos para impersonation

## Impacto na API

### ✅ Funciona Normalmente

A API aceita tokens de impersonation:
- ✅ Valida assinatura
- ✅ Extrai `organization_id` (de `org_id` ou `o.id`)
- ✅ Extrai `user_id` (do campo `sub`)

### ⚠️ Considerações

1. **User ID**: O `user_id` será do usuário **impersonado**, não do admin
2. **Auditoria**: Se precisar saber quem está impersonando, use o campo `act.sub`
3. **Validade Curta**: Tokens expiram rápido, mas são renovados automaticamente

## Quando Usar Impersonation

### ✅ Uso Recomendado
- Debug de problemas específicos de usuário
- Suporte técnico
- Testes de permissões

### ❌ Não Recomendado para
- Desenvolvimento normal
- Testes automatizados
- Produção (exceto suporte)

## Para Desenvolvimento Normal

Se você quer tokens que duram mais tempo:

1. **Saia do modo impersonation** no Clerk Dashboard
2. **Faça login normal** como o usuário
3. **Use o token normal** (dura 1 hora)

## Fluxo de Renovação Automática

```
Token gerado (t=0s)
  ↓
Usado na API (t=10s) ✅
  ↓
Token próximo de expirar (t=50s)
  ↓
Clerk SDK gera novo token automaticamente (t=55s)
  ↓
Novo token ativo (t=60s)
  ↓
Token antigo expira (t=60s)
```

## Resumo

| Aspecto | Token Normal | Token Impersonation |
|---------|--------------|---------------------|
| **Validade** | ~1 hora | ~60 segundos |
| **Renovação** | Manual | Automática |
| **Campo `act`** | ❌ Não tem | ✅ Tem |
| **Uso** | Produção | Debug/Support |
| **Segurança** | Padrão | Extra (curta duração) |

## Conclusão

**É comportamento esperado do Clerk!** 

- ✅ Tokens de impersonation expiram rápido por segurança
- ✅ Clerk renova automaticamente
- ✅ API funciona normalmente
- ✅ Logs mudam porque cada token tem `session_id` diferente

**Não precisa alterar código** - o Clerk está funcionando corretamente. Se quiser tokens que duram mais, use login normal (sem impersonation).

