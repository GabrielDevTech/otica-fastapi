# Entendendo o organization_id

## Como Funciona

O `organization_id` **NÃO é algo que você coloca manualmente** na documentação OpenAPI. Ele vem **automaticamente do token JWT** do Clerk.

## Fluxo

```
1. Você coloca o TOKEN JWT na documentação
   ↓
2. Backend valida o token
   ↓
3. Backend EXTRAI o org_id do payload do token
   ↓
4. Backend usa esse org_id para filtrar dados
```

## O que Você Precisa Fazer

### Na Documentação OpenAPI (/docs)

1. **Clique em "Authorize"** (cadeado no topo)
2. **Cole apenas o TOKEN JWT**:
   ```
   Bearer seu_token_jwt_aqui
   ```
   ou apenas:
   ```
   seu_token_jwt_aqui
   ```
3. **NÃO precisa colocar organization_id** - ele vem do token!

## O Problema Atual

Seu token JWT **não contém** `org_id` no payload. Isso significa:

- ❌ O usuário no Clerk não está em uma organização
- ❌ O token foi gerado sem contexto de organização

## Solução

### Passo 1: Adicionar Usuário a Organização no Clerk

1. Dashboard Clerk → **Organizations**
2. Crie ou selecione uma organização
3. **Users** → Seu usuário → **Add to organization**

### Passo 2: Gerar Novo Token

Depois de adicionar à organização, gere um **novo token** que terá `org_id` automaticamente.

### Passo 3: Usar na Documentação

1. Cole o **novo token** (que tem org_id) no campo "Authorize"
2. Não precisa colocar organization_id manualmente
3. O backend extrai automaticamente do token

## Verificar se Token Tem org_id

Execute:

```powershell
.\venv\Scripts\python.exe scripts\check_token_org.py seu_token_aqui
```

Ou decodifique em: https://jwt.io

O payload deve ter:
```json
{
  "org_id": "org_xxx",  // ← Deve ter este campo!
  "sub": "user_xxx",
  ...
}
```

## Resumo

| O que fazer | O que NÃO fazer |
|-------------|-----------------|
| ✅ Colar TOKEN JWT no "Authorize" | ❌ Colocar organization_id manualmente |
| ✅ Token deve ter org_id no payload | ❌ Token sem org_id não funciona |
| ✅ Backend extrai org_id do token | ❌ Não precisa enviar org_id no body |

## Importante

- O `organization_id` vem **do token**, não do corpo da requisição
- É uma **regra de segurança** - nunca confiar em dados do body
- O token precisa ser gerado **com contexto de organização** no Clerk

