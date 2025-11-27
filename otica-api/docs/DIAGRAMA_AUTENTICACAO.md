# Diagrama de Autenticação - Clerk

## Arquitetura Completa

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTE (Frontend)                       │
│  Envia: Authorization: Bearer <token_jwt_do_clerk>         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI APP (main.py)                    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MIDDLEWARE: CORS                                  │    │
│  │  (app.add_middleware)                              │    │
│  └────────────────────────────────────────────────────┘    │
│                       │                                      │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ROUTER: /api/v1/staff                             │    │
│  │                                                     │    │
│  │  @router.get("")                                   │    │
│  │  async def list_staff(                             │    │
│  │      current_org_id: str = Depends(                │    │
│  │          get_current_org_id  ← DEPENDENCY CHAIN    │
│  │      )                                              │    │
│  │  )                                                  │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         DEPENDENCY INJECTION CHAIN                          │
│                                                              │
│  1. get_current_org_id()                                    │
│     └─> Depends(verify_token)                              │
│          └─> Depends(security)  ← HTTPBearer()              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  HTTPBearer() (security.py:14)                     │    │
│  │  - Extrai token do header Authorization            │    │
│  │  - Retorna HTTPAuthorizationCredentials             │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│                         ▼                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  verify_token() (security.py:69)                    │    │
│  │  - Busca JWKS do Clerk                             │    │
│  │  - Valida assinatura do token                       │    │
│  │  - Verifica issuer                                  │    │
│  │  - Extrai organization_id                           │    │
│  │  - Retorna {org_id, user_id, payload}              │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│                         ▼                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  get_current_org_id() (security.py:131)            │    │
│  │  - Retorna apenas organization_id                   │    │
│  └──────────────────────┬─────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              ENDPOINT EXECUTA                               │
│  - Recebe current_org_id                                    │
│  - Filtra dados por organization_id                        │
│  - Retorna resposta                                        │
└─────────────────────────────────────────────────────────────┘
```

## Comparação: Middleware vs Dependency Injection

### ❌ Middleware Global (NÃO USAMOS)

```python
# Se fosse middleware global:
@app.middleware("http")
async def auth_middleware(request, call_next):
    # Valida TODAS as requisições
    # Até /health precisaria de token
    token = request.headers.get("Authorization")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, 401)
    # ...
```

**Problemas**:
- ❌ Todas as rotas precisam de token
- ❌ Difícil ter rotas públicas
- ❌ Menos flexível

### ✅ Dependency Injection (USAMOS)

```python
# Endpoint público
@app.get("/health")
async def health():
    # ✅ Não precisa de token
    return {"status": "ok"}

# Endpoint protegido
@router.get("/staff")
async def list_staff(
    current_org_id: str = Depends(get_current_org_id)  # ← Só aqui precisa
):
    # ✅ Precisa de token
    ...
```

**Vantagens**:
- ✅ Rotas públicas e privadas
- ✅ Flexível e claro
- ✅ Fácil de testar

## Middlewares Existentes

### 1. CORS Middleware (Global)

```python
# app/main.py:17-23
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**O que faz**: Gerencia CORS para todas as rotas

### 2. HTTPBearer (Por Endpoint)

```python
# app/core/security.py:14
security = HTTPBearer()
```

**O que faz**: Extrai token do header (usado via Dependency)

## Resumo

| Componente | Tipo | Escopo | Onde |
|------------|------|--------|------|
| **CORS Middleware** | Middleware Global | Todas as rotas | `main.py` |
| **HTTPBearer** | Dependency | Por endpoint | `security.py` |
| **verify_token** | Dependency | Por endpoint | `security.py` |
| **get_current_org_id** | Dependency | Por endpoint | `security.py` |

## Conclusão

✅ **Autenticação está implementada corretamente**  
✅ **Usa Dependency Injection (melhor prática FastAPI)**  
✅ **Token é obrigatório nos endpoints protegidos**  
✅ **Rotas públicas disponíveis**  
✅ **Não há middleware de autenticação global** (e não precisa!)

