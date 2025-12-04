# ✅ Telas Pendentes - Sprint 1

## 🎉 Status: TODOS OS ENDPOINTS IMPLEMENTADOS!

**✅ ATUALIZAÇÃO**: Todos os endpoints pendentes foram implementados! Este documento agora serve apenas como referência histórica.

**✅ IMPLEMENTADO**:
- `PUT /api/v1/staff/{staff_id}` - ✅ Implementado
- `GET /api/v1/staff/{staff_id}` - ✅ Implementado

**📝 NOTA**: Este documento foi mantido para referência, mas todas as funcionalidades estão agora disponíveis. Consulte `TELAS_PRONTAS_SPRINT1.md` para a documentação completa.

---

## 📋 Índice

1. [2º Passo: Finalizar Equipe (staff_members) - Endpoints Pendentes](#2º-passo-finalizar-equipe-staff_members---endpoints-pendentes)

---

## 2º Passo: Finalizar Equipe (staff_members) - Endpoints Pendentes

### ⚠️ Endpoints que FALTAM Implementar

#### PUT `/api/v1/staff/{staff_id}`

**Status**: 🚧 **NÃO IMPLEMENTADO**

**Descrição**: Atualiza um membro da equipe (especialmente para vincular loja e setor).

**Por que é necessário**: 
- Permite editar membros existentes
- Permite vincular loja e setor a membros que já existem mas não têm esses campos preenchidos
- Essencial para o fluxo de "Finalizar Equipe"

**O que deveria fazer**:
- Atualizar campos do membro (role, store_id, department_id, job_title, etc.)
- Validar se store e department pertencem à organização
- Validar se email já existe (se estiver sendo alterado)

**Request Body esperado** (todos os campos opcionais, mas `store_id` e `department_id` são obrigatórios se o membro ainda não tiver):
```typescript
{
  "role": "SELLER",        // Opcional
  "store_id": 10,          // OBRIGATÓRIO se ainda não tiver
  "department_id": 2,      // OBRIGATÓRIO se ainda não tiver
  "job_title": "Vendedor", // Opcional
  "is_active": true        // Opcional
}
```

**Response esperado**: Mesmo formato do POST `/api/v1/staff`

**Erros esperados**:
- `400 Bad Request`: Loja ou setor não pertence à organização
- `403 Forbidden`: Acesso negado (não é ADMIN)
- `404 Not Found`: Membro não encontrado

**Telas que ficam pendentes**:
- **Editar Membro da Equipe** (`/equipe/{id}/editar`): Formulário pré-preenchido com os dados atuais do membro. Campos: role (select), loja (select obrigatório - buscar lojas da organização), setor (select obrigatório - buscar setores da organização), cargo específico (job_title - opcional), status ativo (checkbox). Botão de salvar e cancelar. **Importante**: Esta é a tela principal para "finalizar" a equipe, vinculando cada membro à sua loja e setor.

---

#### GET `/api/v1/staff/{staff_id}`

**Status**: 🚧 **NÃO IMPLEMENTADO**

**Descrição**: Obtém um membro específico da equipe.

**Por que é necessário**:
- Permite visualizar detalhes completos de um membro
- Necessário para preencher o formulário de edição
- Melhora a experiência do usuário ao ver informações detalhadas

**Response esperado**: Mesmo formato do POST `/api/v1/staff`

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões esperadas**: STAFF, MANAGER ou ADMIN

**Telas que ficam pendentes**:
- **Detalhes do Membro** (`/equipe/{id}`): Tela de visualização com todos os dados do membro: nome, email, role, cargo, loja (nome), setor (nome), status. Deve ter botão para editar.

---

## 📊 Resumo do Impacto

### Telas que NÃO podem ser implementadas:

1. **Editar Membro da Equipe** (`/equipe/{id}/editar`)
   - **Bloqueio**: Falta endpoint `PUT /api/v1/staff/{staff_id}`
   - **Impacto**: Não é possível editar membros existentes ou vincular loja/setor a membros antigos

2. **Detalhes do Membro** (`/equipe/{id}`)
   - **Bloqueio**: Falta endpoint `GET /api/v1/staff/{staff_id}`
   - **Impacto**: Não é possível ver detalhes de um membro específico (mas pode usar a lista)

### Workaround Temporário

Enquanto os endpoints não são implementados, o frontend pode:

1. **Para visualizar detalhes**: Usar a lista (`GET /api/v1/staff`) e filtrar pelo ID no frontend (não ideal, mas funcional)

2. **Para editar membros**: 
   - **Opção 1**: Aguardar implementação do endpoint PUT
   - **Opção 2**: Criar um novo membro e desativar o antigo (não recomendado, perde histórico)

---

## 🔄 Status de Implementação

| Endpoint | Status | Prioridade | Impacto |
|----------|--------|------------|---------|
| `PUT /api/v1/staff/{staff_id}` | 🚧 Pendente | 🔴 Alta | Bloqueia edição de membros |
| `GET /api/v1/staff/{staff_id}` | 🚧 Pendente | 🟡 Média | Bloqueia tela de detalhes |

---

## 📝 Notas para o Backend

### O que precisa ser implementado:

1. **Endpoint PUT `/api/v1/staff/{staff_id}`**:
   - Validar se o membro existe e pertence à organização
   - Validar se store_id e department_id pertencem à organização (se fornecidos)
   - Atualizar apenas campos fornecidos (PATCH parcial)
   - Retornar membro atualizado

2. **Endpoint GET `/api/v1/staff/{staff_id}`**:
   - Validar se o membro existe e pertence à organização
   - Retornar dados completos do membro
   - Incluir relacionamentos (nome da loja, nome do setor) se possível

### Schema necessário:

Criar `StaffUpdate` schema (já existe no `staff_schema.py`):
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

---

## ⏳ Estimativa

**Tempo estimado para implementação**: 1-2 horas

**Dependências**: Nenhuma (todos os models e schemas já existem)

**Complexidade**: Baixa (similar aos outros endpoints de update)

---

**Documento criado em**: 2025-12-03  
**Status**: 🚧 Aguardando Implementação  
**Prioridade**: 🔴 Alta (bloqueia funcionalidade crítica)

