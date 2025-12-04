# Implementação dos Endpoints de Staff - Sprint 1

## ✅ Status: Implementação Completa

Os endpoints pendentes de Staff foram implementados com sucesso!

---

## 📋 Endpoints Implementados

### 1. GET `/api/v1/staff/{staff_id}` ✅

**Descrição**: Obtém um membro específico da equipe.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Funcionalidades**:
- Busca membro por ID
- Valida se o membro pertence à organização do token
- Retorna dados completos do membro

**Response 200 OK**:
```typescript
{
  "id": 1,
  "clerk_id": "user_xxx",
  "organization_id": "org_xxx",
  "store_id": 10,
  "department_id": 2,
  "full_name": "João Silva",
  "email": "joao@example.com",
  "role": "SELLER",
  "job_title": "Vendedor",
  "is_active": true,
  "avatar_url": null,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `404 Not Found`: Membro não encontrado ou não pertence à organização

---

### 2. PUT `/api/v1/staff/{staff_id}` ✅

**Descrição**: Atualiza um membro da equipe.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Funcionalidades**:
- Atualiza campos do membro (PATCH parcial - apenas campos fornecidos)
- Valida se store_id pertence à organização (se fornecido)
- Valida se department_id pertence à organização (se fornecido)
- Valida se email já existe na organização (se estiver sendo alterado)
- Permite vincular loja e setor a membros existentes

**Request Body** (todos os campos opcionais):
```typescript
{
  "full_name": "João Silva Atualizado",  // Opcional
  "email": "joao.novo@example.com",      // Opcional (valida se já existe)
  "role": "SELLER",                       // Opcional
  "store_id": 10,                         // Opcional (valida se pertence à org)
  "department_id": 2,                     // Opcional (valida se pertence à org)
  "job_title": "Vendedor",                // Opcional
  "is_active": true                       // Opcional
}
```

**Response 200 OK**: Mesmo formato do GET acima.

**Erros**:
- `400 Bad Request`: 
  - Loja não encontrada ou não pertence à organização
  - Setor não encontrado ou não pertence à organização
  - Email já cadastrado nesta organização
- `403 Forbidden`: Acesso negado (não é ADMIN)
- `404 Not Found`: Membro não encontrado

---

## 🔧 Mudanças Realizadas

### 1. Schema Criado

**Arquivo**: `app/schemas/staff_schema.py`

Adicionado `StaffUpdate`:
```python
class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[StaffRole] = None
    store_id: Optional[int] = None
    department_id: Optional[int] = None
    job_title: Optional[str] = None
    is_active: Optional[bool] = None
```

### 2. Router Atualizado

**Arquivo**: `app/routers/v1/staff.py`

Adicionados dois novos endpoints:
- `GET /api/v1/staff/{staff_id}`
- `PUT /api/v1/staff/{staff_id}`

### 3. Validações Implementadas

- ✅ Validação de existência do membro
- ✅ Validação de pertencimento à organização
- ✅ Validação de store_id (se fornecido)
- ✅ Validação de department_id (se fornecido)
- ✅ Validação de email único (se estiver sendo alterado)

---

## ✅ Checklist de Implementação

- [x] Schema `StaffUpdate` criado
- [x] Endpoint `GET /api/v1/staff/{staff_id}` implementado
- [x] Endpoint `PUT /api/v1/staff/{staff_id}` implementado
- [x] Validações de store e department implementadas
- [x] Validação de email único implementada
- [x] Testes de importação realizados
- [x] Documentação atualizada

---

## 🚀 Próximos Passos

1. **Testar os endpoints**:
   - Testar GET com um ID válido
   - Testar GET com um ID inválido (deve retornar 404)
   - Testar PUT atualizando diferentes campos
   - Testar PUT com store_id/department_id inválidos

2. **Frontend pode implementar**:
   - Tela de detalhes do membro (`/equipe/{id}`)
   - Tela de edição do membro (`/equipe/{id}/editar`)

---

**Status**: ✅ Implementação Completa  
**Data**: 2025-12-03  
**Próximo**: Testar endpoints

