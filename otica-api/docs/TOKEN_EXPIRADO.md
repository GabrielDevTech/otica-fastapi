# Token Expirado - Como Resolver

## Erro: "Signature has expired"

Este erro significa que o token JWT expirou e não é mais válido.

## Solução Rápida

**Gere um novo token do Clerk!**

## Como Gerar Novo Token

### Método 1: Via Frontend (Recomendado)

Se você tem um frontend com Clerk:

```typescript
// No seu frontend
const { getToken } = useAuth();
const token = await getToken(); // Gera novo token
```

### Método 2: Via Dashboard Clerk

1. Acesse: https://dashboard.clerk.com
2. Vá em **Users** → Seu usuário
3. Procure por **"Sessions"** ou **"Tokens"**
4. Gere um novo token

### Método 3: Fazer Logout/Login

- Faça logout no frontend
- Faça login novamente
- Um novo token será gerado automaticamente

## Validade do Token

Tokens JWT do Clerk geralmente expiram em:
- **1 hora** (padrão)
- Ou conforme configurado no Clerk

## Verificar Expiração

Você pode verificar quando o token expira decodificando em https://jwt.io:

```json
{
  "exp": 1764212861,  // ← Timestamp de expiração
  "iat": 1764212801,  // ← Timestamp de criação
  ...
}
```

## Dica

Para desenvolvimento, você pode:
- Gerar tokens com expiração maior no Clerk
- Ou configurar refresh automático no frontend

## Importante

⚠️ **Nunca use tokens expirados em produção!**
- Sempre valide a expiração
- Implemente refresh de tokens
- Trate erros de expiração adequadamente

