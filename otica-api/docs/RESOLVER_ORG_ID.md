# Como Resolver: "Token não contém organization_id"

## Problema

O token JWT está sendo validado com sucesso, mas não contém o campo `org_id` no payload.

## Causa

O usuário no Clerk **não está associado a uma organização**, ou o token foi gerado sem contexto de organização.

## Soluções

### Solução 1: Adicionar Usuário a uma Organização no Clerk (Recomendado)

1. **Acesse o Dashboard do Clerk**
   - Vá para: https://dashboard.clerk.com
   - Faça login

2. **Vá em "Organizations"**
   - No menu lateral, clique em **"Organizations"**

3. **Crie ou Selecione uma Organização**
   - Se não tiver, crie uma nova organização
   - Anote o **Organization ID** (será usado depois)

4. **Adicione o Usuário à Organização**
   - Vá em **"Users"** → Selecione seu usuário
   - Vá em **"Organizations"** ou **"Memberships"**
   - Clique em **"Add to organization"**
   - Selecione a organização
   - Defina o role (Member, Admin, etc.)

5. **Gere um Novo Token**
   - Faça logout e login novamente no frontend
   - Ou gere um novo token com contexto de organização
   - O novo token deve conter `org_id` no payload

### Solução 2: Usar Frontend com Clerk (Mais Fácil)

Se você tem um frontend Next.js/React com Clerk:

```typescript
import { useOrganization } from '@clerk/nextjs';

function MyComponent() {
  const { organization } = useOrganization();
  const { getToken } = useAuth();
  
  // Token gerado com contexto de organização
  const token = await getToken({
    template: 'default'  // ou seu template customizado
  });
  
  // Este token terá org_id se o usuário estiver em uma organização
}
```

### Solução 3: Verificar Token Atual

Decodifique seu token em https://jwt.io e verifique:

```json
{
  "sub": "user_xxx",
  "iss": "https://...",
  // ❌ Se NÃO tiver "org_id" aqui, o problema é este!
  "org_id": "org_xxx"  // ← Deve ter este campo
}
```

## Verificar se Usuário Está em Organização

### Via Dashboard Clerk

1. Users → Seu usuário → Organizations
2. Deve mostrar a organização associada

### Via API Clerk

```bash
curl -X GET "https://api.clerk.com/v1/users/user_xxx/organization_memberships" \
  -H "Authorization: Bearer YOUR_CLERK_SECRET_KEY"
```

## Criar Organização de Teste

Se você não tem uma organização:

1. **Dashboard Clerk** → **Organizations** → **Create Organization**
2. Nome: "Test Organization" (ou qualquer nome)
3. Copie o **Organization ID**
4. Adicione seu usuário à organização
5. Gere novo token

## Testar Após Corrigir

Depois de adicionar o usuário à organização e gerar novo token:

1. **Decodifique o token** em https://jwt.io
2. **Verifique se tem `org_id`** no payload
3. **Teste na API**:
   ```powershell
   .\venv\Scripts\python.exe scripts\test_auth.py
   ```

## Importante

- ✅ Token válido + com `org_id` = Funciona
- ❌ Token válido + sem `org_id` = Erro 403
- ❌ Token inválido = Erro 401

O erro que você está vendo (403 - "Token não contém organization_id") significa que:
- ✅ A validação da chave pública está funcionando
- ✅ O token é válido
- ❌ Mas o token não tem `org_id` (usuário não está em organização)

## Próximo Passo

**Adicione seu usuário a uma organização no Clerk e gere um novo token!**

Depois disso, o token terá `org_id` e a API funcionará.

