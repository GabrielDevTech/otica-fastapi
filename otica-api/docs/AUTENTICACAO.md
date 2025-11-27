# Autenticação com Clerk - Como Funciona

## Visão Geral

A autenticação **NÃO usa middleware global**. Em vez disso, usa **Dependency Injection** do FastAPI, que é mais flexível e permite rotas públicas e privadas.

## Arquitetura de Autenticação

### 1. HTTPBearer (Extração do Token)

```python
# app/core/security.py
from fastapi.security import HTTPBearer

security = HTTPBearer()  # ← Extrai o Bearer Token do header
```

**O que faz**:
- Lê o header `Authorization: Bearer <token>`
- Extrai o token automaticamente
- Retorna `HTTPAuthorizationCredentials` com o token

### 2. verify_token (Validação)

```python
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    # Valida o token JWT
    # Verifica assinatura via JWKS
    # Extrai organization_id
    # Retorna dados do token
```

**O que faz**:
- Busca JWKS do Clerk
- Valida assinatura do token
- Verifica issuer
- Extrai `organization_id`
- Retorna 401 se inválido, 403 se sem org_id

### 3. get_current_org_id (Dependency Principal)

```python
async def get_current_org_id(
    token_data: dict = Depends(verify_token)
) -> str:
    return token_data["org_id"]
```

**O que faz**:
- Depende de `verify_token`
- Retorna apenas o `organization_id`
- Usado em todas as rotas que precisam de autenticação

## Como é Aplicado nos Endpoints

### Endpoints Públicos (SEM autenticação)

```python
# app/main.py
@app.get("/")
async def root():
    # ✅ Público - não precisa de token
    return {"message": "Otica API"}

@app.get("/health")
async def health():
    # ✅ Público - não precisa de token
    return {"status": "ok"}
```

### Endpoints Protegidos (COM autenticação)

```python
# app/routers/v1/staff.py
@router.get("")
async def list_staff(
    current_org_id: str = Depends(get_current_org_id),  # ← Exige token!
    db: AsyncSession = Depends(get_db),
):
    # ✅ Protegido - token obrigatório
    # Se não tiver token → 401 Unauthorized
    # Se token inválido → 401 Unauthorized
    # Se token sem org_id → 403 Forbidden
    ...
```

## Fluxo de Autenticação

```
┌─────────────────────────────────────────┐
│  1. Cliente faz requisição              │
│     Header: Authorization: Bearer <token>│
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. HTTPBearer() extrai o token         │
│     (app/core/security.py:14)           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. verify_token() valida o token       │
│     - Busca JWKS do Clerk               │
│     - Valida assinatura                 │
│     - Verifica issuer                   │
│     - Extrai org_id                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. get_current_org_id() retorna org_id  │
│     (Dependency injection)               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Endpoint recebe current_org_id       │
│     Usa para filtrar dados               │
└─────────────────────────────────────────┘
```

## Por que NÃO usar Middleware Global?

### Vantagens da Dependency Injection (Atual)

✅ **Flexibilidade**: Alguns endpoints públicos, outros privados  
✅ **Granularidade**: Cada endpoint decide se precisa de auth  
✅ **Testabilidade**: Fácil mockar dependências  
✅ **Performance**: Valida apenas quando necessário  
✅ **Clareza**: Fica explícito no código quais endpoints precisam de auth  

### Desvantagens do Middleware Global

❌ **Tudo protegido**: Até `/health` precisaria de token  
❌ **Menos flexível**: Difícil ter rotas públicas  
❌ **Mais complexo**: Precisa de exceções/whitelist  

## Endpoints Atuais

| Endpoint | Autenticação | Status |
|----------|--------------|--------|
| `GET /` | ❌ Não | Público |
| `GET /health` | ❌ Não | Público |
| `GET /docs` | ❌ Não | Público (FastAPI) |
| `GET /api/v1/staff` | ✅ Sim | Protegido |
| `GET /api/v1/staff/stats` | ✅ Sim | Protegido |
| `POST /api/v1/staff` | ✅ Sim | Protegido |

## Como Testar

### 1. Sem Token (deve falhar)

```bash
curl http://localhost:8000/api/v1/staff
# Resposta: 403 Forbidden - "Not authenticated"
```

### 2. Com Token Inválido (deve falhar)

```bash
curl -H "Authorization: Bearer token_invalido" \
     http://localhost:8000/api/v1/staff
# Resposta: 401 Unauthorized - "Token inválido"
```

### 3. Com Token Válido (deve funcionar)

```bash
curl -H "Authorization: Bearer <token_do_clerk>" \
     http://localhost:8000/api/v1/staff
# Resposta: 200 OK - Lista de staff
```

## Resumo

| Aspecto | Implementação |
|---------|---------------|
| **Método** | Dependency Injection (não middleware) |
| **Extração** | `HTTPBearer()` do FastAPI |
| **Validação** | `verify_token()` - valida JWT via JWKS |
| **Isolamento** | `get_current_org_id()` - extrai org_id |
| **Aplicação** | Por endpoint via `Depends()` |
| **Rotas Públicas** | Endpoints sem `Depends(get_current_org_id)` |
| **Rotas Protegidas** | Endpoints com `Depends(get_current_org_id)` |

## Conclusão

✅ **Autenticação está funcionando corretamente**  
✅ **Token é obrigatório nos endpoints de staff**  
✅ **Validação completa (assinatura, issuer, org_id)**  
✅ **Rotas públicas disponíveis** (`/`, `/health`, `/docs`)  
✅ **Isolamento multi-tenant garantido**  

A implementação atual é a **melhor prática** para FastAPI: flexível, testável e performática!

