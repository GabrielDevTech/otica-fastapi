# Como Obter o organization_id do Token Clerk

## Método 1: Decodificar Token JWT Online

1. **Acesse**: https://jwt.io

2. **Cole seu token JWT** no campo "Encoded"

3. **Procure no Payload** (lado direito) pelo campo:
   ```json
   {
     "org_id": "org_xxx",  // ← Este é o organization_id!
     "sub": "user_362f7Ug2v5SRN",
     ...
   }
   ```

4. **Copie o valor** de `org_id`

## Método 2: Via Python

```python
import jwt

token = "seu_token_aqui"
decoded = jwt.decode(token, options={"verify_signature": False})
org_id = decoded.get("org_id")
print(f"Organization ID: {org_id}")
```

## Método 3: Via Dashboard do Clerk

1. Acesse: https://dashboard.clerk.com
2. Vá em **"Organizations"**
3. Selecione sua organização
4. O **Organization ID** está na URL ou nas configurações

## Método 4: Via Frontend (Next.js)

```typescript
import { useOrganization } from '@clerk/nextjs';

function MyComponent() {
  const { organization } = useOrganization();
  
  console.log('Organization ID:', organization?.id);
}
```

## Importante

- O `organization_id` é **obrigatório** no token para a API funcionar
- Se o token não tiver `org_id`, você receberá erro 403
- Cada organização tem seu próprio `organization_id`

