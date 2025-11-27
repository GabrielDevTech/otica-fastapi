# Controle de Acesso Baseado em Roles (RBAC)

## Visão Geral

O sistema implementa **controle de acesso baseado em roles (RBAC)** no **backend**. O frontend pode fazer controle visual, mas a segurança real está no backend.

## Por que Backend?

### ❌ Apenas Frontend (INSEGURO)

```typescript
// Frontend - pode ser burlado!
if (user.role === 'ADMIN') {
  // Mostra botão
  // Mas usuário pode chamar API diretamente!
}
```

**Problemas**:
- ❌ Usuário pode chamar API diretamente (curl, Postman)
- ❌ Frontend pode ser modificado
- ❌ Não há segurança real

### ✅ Backend + Frontend (SEGURO)

```python
# Backend - segurança real
@router.post("/staff")
async def create_staff(
    current_staff: StaffMember = Depends(require_admin)  # ← Verifica no backend!
):
    ...
```

**Vantagens**:
- ✅ Backend valida sempre
- ✅ Frontend apenas controla UI
- ✅ Segurança garantida

## Roles Disponíveis

```python
class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"        # Acesso total
    MANAGER = "MANAGER"    # Gerenciamento
    STAFF = "STAFF"        # Operacional
    ASSISTANT = "ASSISTANT" # Assistente
```

## Hierarquia de Permissões

```
ADMIN (mais permissões)
  └─> MANAGER
      └─> STAFF
          └─> ASSISTANT (menos permissões)
```

## Como Funciona

### 1. Identificação do Usuário

```python
# app/core/permissions.py
async def get_current_staff(
    current_org_id: str = Depends(get_current_org_id),
    current_user_id: str = Depends(get_current_user_id),  # ← clerk_id do token
    db: AsyncSession = Depends(get_db),
) -> StaffMember:
    # Busca o StaffMember pelo clerk_id
    # Verifica se está ativo
    # Retorna o staff member completo (com role)
```

### 2. Verificação de Role

```python
# Factory function
def require_role(*allowed_roles: StaffRole):
    async def check_role(
        current_staff: StaffMember = Depends(get_current_staff)
    ) -> StaffMember:
        if current_staff.role not in allowed_roles:
            raise HTTPException(403, "Acesso negado")
        return current_staff
    return check_role
```

### 3. Dependencies Pré-configuradas

```python
# app/core/permissions.py
require_admin = require_role(StaffRole.ADMIN)
require_manager_or_admin = require_role(StaffRole.ADMIN, StaffRole.MANAGER)
require_staff_or_above = require_role(StaffRole.ADMIN, StaffRole.MANAGER, StaffRole.STAFF)
```

## Permissões por Endpoint

| Endpoint | Permissão | Roles Permitidos |
|----------|-----------|-----------------|
| `GET /api/v1/staff` | `require_staff_or_above` | ADMIN, MANAGER, STAFF |
| `GET /api/v1/staff/stats` | `require_manager_or_admin` | ADMIN, MANAGER |
| `POST /api/v1/staff` | `require_admin` | ADMIN |

## Fluxo de Autenticação e Autorização

```
┌─────────────────────────────────────────┐
│  1. Cliente envia token JWT              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. verify_token() valida token         │
│     - Extrai user_id (clerk_id)          │
│     - Extrai organization_id             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. get_current_staff() busca usuário   │
│     - Busca StaffMember por clerk_id     │
│     - Verifica se está ativo             │
│     - Retorna StaffMember com role       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. require_role() verifica permissão   │
│     - Compara role do staff              │
│     - Com roles permitidos               │
│     - Retorna 403 se negado             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Endpoint executa                    │
│     - Recebe current_staff               │
│     - Pode usar role, id, etc.          │
└─────────────────────────────────────────┘
```

## Exemplos de Uso

### Endpoint Apenas para Admin

```python
@router.post("/staff")
async def create_staff(
    current_staff: StaffMember = Depends(require_admin),  # ← Apenas ADMIN
):
    # current_staff.role == StaffRole.ADMIN
    # current_staff.id - ID do staff
    # current_staff.clerk_id - ID do Clerk
    ...
```

### Endpoint para Manager ou Admin

```python
@router.get("/stats")
async def get_stats(
    current_staff: StaffMember = Depends(require_manager_or_admin),
):
    # current_staff.role == StaffRole.MANAGER ou ADMIN
    ...
```

### Endpoint para Staff ou Acima

```python
@router.get("/staff")
async def list_staff(
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    # current_staff.role == STAFF, MANAGER ou ADMIN
    ...
```

## Respostas de Erro

### Usuário não encontrado no Staff

```json
{
  "detail": "Usuário não encontrado na equipe ou inativo"
}
```
**Status**: 404 Not Found

### Acesso Negado (Role Insuficiente)

```json
{
  "detail": "Acesso negado. Roles permitidos: ADMIN. Seu role: STAFF"
}
```
**Status**: 403 Forbidden

## Vínculo Clerk ↔ Staff

O sistema vincula usuários Clerk com Staff através do campo `clerk_id`:

```python
# StaffMember
clerk_id = Column(String, unique=True, nullable=True)
```

**Fluxo**:
1. Usuário faz login no Clerk → recebe token JWT
2. Token contém `sub` (user_id do Clerk)
3. Backend busca `StaffMember` onde `clerk_id == sub`
4. Se encontrado e ativo → permite acesso
5. Verifica role do staff para autorização

## Boas Práticas

### ✅ Fazer

- ✅ Sempre verificar permissões no backend
- ✅ Usar `get_current_staff` para obter dados do usuário
- ✅ Verificar `is_active` antes de permitir acesso
- ✅ Frontend pode controlar UI, mas backend é a fonte da verdade

### ❌ Não Fazer

- ❌ Confiar apenas no frontend para segurança
- ❌ Aceitar role do corpo da requisição
- ❌ Permitir acesso sem verificar `is_active`
- ❌ Ignorar erros 403/404

## Resumo

| Aspecto | Implementação |
|---------|---------------|
| **Identificação** | `clerk_id` do token → `StaffMember` |
| **Autorização** | Verificação de `role` no backend |
| **Dependencies** | `require_admin`, `require_manager_or_admin`, etc. |
| **Segurança** | Backend valida sempre, frontend apenas UI |
| **Erros** | 404 se não encontrado, 403 se sem permissão |

## Conclusão

✅ **Controle de acesso implementado no backend**  
✅ **Roles verificados em cada endpoint**  
✅ **Vínculo Clerk ↔ Staff via clerk_id**  
✅ **Segurança garantida independente do frontend**  

O frontend pode controlar a UI, mas a segurança real está no backend!

