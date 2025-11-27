# Troubleshooting: Erro de Validação de Token

## Erro: "Não foi possível encontrar a chave pública para validar o token"

Este erro indica que o sistema não conseguiu encontrar a chave pública (JWKS) correspondente ao token.

## Possíveis Causas

### 1. CLERK_ISSUER Incorreto

**Sintoma**: Erro ao buscar JWKS

**Solução**:
1. Verifique o `.env`:
   ```bash
   CLERK_ISSUER=https://thorough-mutt-7.clerk.accounts.dev
   ```

2. Teste a URL do JWKS manualmente:
   ```bash
   curl https://thorough-mutt-7.clerk.accounts.dev/.well-known/jwks.json
   ```

3. Se não funcionar, verifique no dashboard do Clerk qual é o issuer correto

### 2. Token de Clerk Diferente

**Sintoma**: Token tem `kid` diferente dos disponíveis no JWKS

**Solução**:
- Certifique-se que o token é do mesmo Clerk configurado no `.env`
- Tokens de diferentes ambientes (dev/prod) têm JWKS diferentes

### 3. Token Inválido ou Malformado

**Sintoma**: Token não tem `kid` no header

**Solução**:
- Gere um novo token do Clerk
- Certifique-se que é um token JWT válido

## Como Debugar

### Método 1: Script de Debug

Execute o script de debug com seu token:

```powershell
.\venv\Scripts\python.exe scripts\debug_token.py seu_token_aqui
```

O script mostra:
- Header do token
- Payload do token
- Se tem `kid`, `org_id`, `sub`
- JWKS disponíveis
- Se encontra a chave correspondente

### Método 2: Verificar Manualmente

1. **Decodifique o token** em https://jwt.io
2. **Verifique o header** - deve ter `"kid"`
3. **Verifique o payload** - deve ter `"iss"` igual ao `CLERK_ISSUER`
4. **Teste a URL do JWKS**:
   ```bash
   curl https://thorough-mutt-7.clerk.accounts.dev/.well-known/jwks.json
   ```

### Método 3: Verificar Configuração

```powershell
.\venv\Scripts\python.exe scripts\verify_config.py
```

Verifique se o `CLERK_ISSUER` está correto.

## Soluções Rápidas

### Solução 1: Verificar CLERK_ISSUER

```powershell
# Verificar configuração
.\venv\Scripts\python.exe -c "from app.core.config import settings; print(settings.CLERK_ISSUER)"
```

### Solução 2: Testar JWKS Manualmente

```python
import asyncio
import httpx
from app.core.config import settings

async def test_jwks():
    url = f"{settings.CLERK_ISSUER}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        print(f"JWKS: {response.json()}")

asyncio.run(test_jwks())
```

### Solução 3: Usar Token do Mesmo Ambiente

- Se `CLERK_ISSUER` aponta para `thorough-mutt-7.clerk.accounts.dev`
- O token deve ser gerado do mesmo Clerk (mesmo projeto)

## Checklist

Antes de reportar erro, verifique:

- [ ] `CLERK_ISSUER` está correto no `.env`
- [ ] URL do JWKS está acessível
- [ ] Token é do mesmo Clerk configurado
- [ ] Token tem `kid` no header
- [ ] Token tem `org_id` no payload
- [ ] Token não está expirado

## Mensagens de Erro Melhoradas

Agora o sistema mostra mais detalhes:

- Se não encontrar `kid`: mostra que o token não tem Key ID
- Se não encontrar chave: mostra o `kid` do token e os `kids` disponíveis no JWKS
- Se erro ao buscar JWKS: mostra o erro de conexão

Isso ajuda a identificar exatamente qual é o problema!

