# Como Obter Token JWT do Clerk para Testar a API

## Visão Geral

Para testar os endpoints protegidos da API, você precisa de um **token JWT válido do Clerk** que contenha o `organization_id`.

## Métodos para Obter Token

### Método 1: Via Dashboard do Clerk (Recomendado para Testes)

1. **Acesse o Dashboard do Clerk**
   - Vá para: https://dashboard.clerk.com
   - Faça login na sua conta

2. **Acesse a seção de usuários**
   - No menu lateral, clique em **"Users"**
   - Selecione um usuário ou crie um novo

3. **Obter Session Token**
   - Clique no usuário
   - Vá em **"Sessions"** ou **"Tokens"**
   - Copie o token JWT

**Nota**: Tokens do dashboard podem não ter `org_id` se o usuário não estiver em uma organização.

### Método 2: Via Frontend (Next.js/React) - Mais Realista

Se você tem um frontend integrado com Clerk:

```typescript
// No seu frontend Next.js/React
import { useAuth } from '@clerk/nextjs';

function MyComponent() {
  const { getToken, userId } = useAuth();
  
  const testAPI = async () => {
    // Obter token do Clerk
    const token = await getToken();
    
    // Usar na requisição
    const response = await fetch('http://localhost:8000/api/v1/staff', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('Token:', token); // Copie este token para testes
  };
}
```

### Método 3: Via Clerk API (Programático)

```bash
# Obter token via API do Clerk
curl -X POST https://api.clerk.com/v1/sessions \
  -H "Authorization: Bearer YOUR_CLERK_SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_xxx",
    "organization_id": "org_xxx"
  }'
```

### Método 4: Criar Token Manualmente (Apenas para Desenvolvimento)

⚠️ **ATENÇÃO**: Este método é apenas para desenvolvimento/testes locais!

```python
# scripts/generate_test_token.py
import jwt
from datetime import datetime, timedelta

# Chave secreta do Clerk (obtenha do dashboard)
CLERK_SECRET_KEY = "sk_test_..."

# Dados do token
payload = {
    "sub": "user_test_123",  # user_id
    "org_id": "org_test_123",  # organization_id (IMPORTANTE!)
    "iss": "https://thorough-mutt-7.clerk.accounts.dev",  # Seu CLERK_ISSUER
    "iat": datetime.utcnow(),
    "exp": datetime.utcnow() + timedelta(hours=1),
}

# Gerar token (simplificado - em produção use as chaves corretas)
token = jwt.encode(payload, CLERK_SECRET_KEY, algorithm="HS256")
print(f"Token: {token}")
```

## Verificar se o Token Tem organization_id

O token JWT precisa ter o campo `org_id` no payload. Você pode decodificar o token (sem validar) para verificar:

```python
import jwt

token = "seu_token_aqui"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)

# Verificar se tem org_id
if "org_id" in decoded:
    print(f"✅ Token tem org_id: {decoded['org_id']}")
else:
    print("❌ Token NÃO tem org_id!")
```

## Testar na Documentação Interativa

1. **Acesse**: http://127.0.0.1:8000/docs

2. **Clique em um endpoint protegido** (ex: `GET /api/v1/staff`)

3. **Clique em "Authorize"** (cadeado no topo)

4. **Cole o token**:
   - No campo "Value", cole: `Bearer seu_token_aqui`
   - Ou apenas: `seu_token_aqui` (o Swagger adiciona "Bearer" automaticamente)

5. **Clique em "Authorize"** e depois "Close"

6. **Teste o endpoint** clicando em "Try it out" → "Execute"

## Testar via cURL

```bash
# Substitua YOUR_TOKEN pelo token real
curl -X GET "http://127.0.0.1:8000/api/v1/staff" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## Testar via PowerShell

```powershell
$token = "seu_token_aqui"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/staff" -Headers $headers
```

## Erros Comuns

### 401 Unauthorized - "Token inválido"
- Token expirado
- Token malformado
- Assinatura inválida

**Solução**: Gere um novo token

### 403 Forbidden - "Token não contém organization_id"
- Token não tem campo `org_id` no payload

**Solução**: 
- Certifique-se que o usuário está em uma organização no Clerk
- Use um token que foi gerado com `org_id`

### 404 Not Found - "Usuário não encontrado na equipe"
- O `clerk_id` do token não existe na tabela `staff_members`
- O usuário não está ativo (`is_active = False`)

**Solução**: 
- Crie um registro em `staff_members` com o `clerk_id` do token
- Ou use um token de um usuário que já está cadastrado

## Criar Usuário de Teste no Staff

Para testar, você precisa criar um registro em `staff_members`:

```sql
-- Exemplo: criar staff member de teste
INSERT INTO staff_members (
    clerk_id,
    organization_id,
    full_name,
    email,
    role,
    is_active
) VALUES (
    'user_test_123',  -- clerk_id do token
    'org_test_123',   -- org_id do token
    'Usuário Teste',
    'teste@example.com',
    'ADMIN',          -- Role para ter todas as permissões
    true
);
```

Ou via API (se você tiver um endpoint público de criação inicial):

```bash
# Primeiro, criar via SQL ou script Python
```

## Script de Teste Completo

Crie `scripts/test_auth.py`:

```python
"""Script para testar autenticação com token do Clerk."""
import asyncio
import httpx
import sys

# Token do Clerk (cole aqui)
TOKEN = "seu_token_aqui"

async def test_endpoints():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Teste 1: Health (público)
        print("1. Testando /health (público)...")
        response = await client.get("http://127.0.0.1:8000/health")
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.json()}\n")
        
        # Teste 2: List staff (protegido)
        print("2. Testando /api/v1/staff (protegido)...")
        response = await client.get(
            "http://127.0.0.1:8000/api/v1/staff",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Resposta: {response.json()}\n")
        else:
            print(f"   Erro: {response.text}\n")

if __name__ == "__main__":
    if TOKEN == "seu_token_aqui":
        print("❌ Configure o TOKEN no script primeiro!")
        sys.exit(1)
    asyncio.run(test_endpoints())
```

## Resumo

| Método | Quando Usar | Dificuldade |
|--------|-------------|-------------|
| **Dashboard Clerk** | Testes rápidos | Fácil |
| **Frontend** | Desenvolvimento real | Média |
| **Clerk API** | Automação | Média |
| **Token Manual** | Apenas dev/testes | Fácil |

## Checklist

Antes de testar, certifique-se:

- [ ] Token JWT válido do Clerk
- [ ] Token contém `org_id` no payload
- [ ] Usuário existe em `staff_members` com o `clerk_id` correto
- [ ] Usuário está ativo (`is_active = True`)
- [ ] Usuário tem role adequado para o endpoint

---

**Dica**: A forma mais fácil é usar o frontend integrado com Clerk, que gera tokens automaticamente com todas as informações necessárias.

