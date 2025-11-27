# Planejamento: Controle de Acesso por Cargos/Roles

## Visão Geral

Este documento descreve o planejamento para implementar um sistema robusto de controle de acesso baseado em cargos/roles, permitindo permissões granulares por funcionalidade.

## Situação Atual

### Roles Existentes
```python
class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"        # Administrador
    MANAGER = "MANAGER"    # Gerente
    STAFF = "STAFF"        # Funcionário
    ASSISTANT = "ASSISTANT" # Assistente
```

### Implementação Atual
- ✅ Verificação básica de roles implementada
- ✅ Dependencies `require_admin`, `require_manager_or_admin`, etc.
- ✅ Vínculo Clerk ↔ Staff via `clerk_id`
- ⚠️ Permissões ainda são simples (apenas verificação de role)

## Objetivos

1. **Sistema de Permissões Granular**
   - Definir permissões por funcionalidade
   - Mapear roles para permissões
   - Permitir múltiplos roles por usuário (futuro)

2. **Cargos Específicos do Negócio**
   - Gerente de Vendas
   - Vendedor
   - Óptico
   - Recepcionista
   - etc.

3. **Controle Flexível**
   - Permissões por módulo (Staff, Pacientes, Produtos, Vendas)
   - Permissões por ação (criar, ler, atualizar, deletar)
   - Permissões por recurso (próprios dados vs. todos os dados)

## Arquitetura Proposta

### 1. Sistema de Permissões

#### Estrutura de Permissões

```python
# app/core/permissions.py

class Permission(str, enum.Enum):
    # Staff
    STAFF_VIEW = "staff:view"
    STAFF_CREATE = "staff:create"
    STAFF_UPDATE = "staff:update"
    STAFF_DELETE = "staff:delete"
    STAFF_VIEW_STATS = "staff:view_stats"
    
    # Pacientes (futuro)
    PATIENT_VIEW = "patient:view"
    PATIENT_CREATE = "patient:create"
    PATIENT_UPDATE = "patient:update"
    PATIENT_DELETE = "patient:delete"
    
    # Produtos (futuro)
    PRODUCT_VIEW = "product:view"
    PRODUCT_CREATE = "product:create"
    PRODUCT_UPDATE = "product:update"
    PRODUCT_DELETE = "product:delete"
    
    # Vendas (futuro)
    SALE_VIEW = "sale:view"
    SALE_CREATE = "sale:create"
    SALE_UPDATE = "sale:update"
    SALE_DELETE = "sale:delete"
    SALE_VIEW_REPORTS = "sale:view_reports"
```

#### Mapeamento Role → Permissões

```python
# app/core/permissions.py

ROLE_PERMISSIONS: dict[StaffRole, list[Permission]] = {
    StaffRole.ADMIN: [
        # Todas as permissões
        Permission.STAFF_VIEW,
        Permission.STAFF_CREATE,
        Permission.STAFF_UPDATE,
        Permission.STAFF_DELETE,
        Permission.STAFF_VIEW_STATS,
        # ... todas as outras
    ],
    
    StaffRole.MANAGER: [
        Permission.STAFF_VIEW,
        Permission.STAFF_VIEW_STATS,
        Permission.STAFF_UPDATE,  # Pode atualizar, mas não criar/deletar
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.SALE_VIEW,
        Permission.SALE_VIEW_REPORTS,
        # ...
    ],
    
    StaffRole.STAFF: [
        Permission.STAFF_VIEW,  # Apenas visualizar
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.SALE_VIEW,
        Permission.SALE_CREATE,
        # ...
    ],
    
    StaffRole.ASSISTANT: [
        Permission.PATIENT_VIEW,
        Permission.STAFF_VIEW,  # Apenas visualizar
        # ...
    ],
}
```

### 2. Cargos Específicos do Negócio

#### Opção A: Usar Roles Existentes com Contexto

```python
# Manter roles genéricos, mas adicionar campo "department"
# StaffMember já tem: department = Column(String, nullable=True)

# Exemplos:
# - role=MANAGER, department="Vendas" → Gerente de Vendas
# - role=STAFF, department="Vendas" → Vendedor
# - role=STAFF, department="Óptica" → Óptico
```

#### Opção B: Criar Roles Específicos

```python
class StaffRole(str, enum.Enum):
    # Administrativos
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    
    # Vendas
    SALES_MANAGER = "SALES_MANAGER"  # Gerente de Vendas
    SALES_STAFF = "SALES_STAFF"      # Vendedor
    
    # Técnicos
    OPTICIAN = "OPTICIAN"            # Óptico
    OPTICIAN_ASSISTANT = "OPTICIAN_ASSISTANT"  # Assistente de Óptica
    
    # Atendimento
    RECEPTIONIST = "RECEPTIONIST"    # Recepcionista
    
    # Genéricos
    STAFF = "STAFF"
    ASSISTANT = "ASSISTANT"
```

**Recomendação**: Opção A (roles genéricos + department) é mais flexível e escalável.

### 3. Sistema de Verificação de Permissões

#### Dependency para Verificar Permissão

```python
# app/core/permissions.py

def require_permission(permission: Permission):
    """
    Factory que cria uma dependency para verificar permissão específica.
    
    Uso:
        @router.post("/staff")
        async def create_staff(
            current_staff: StaffMember = Depends(require_permission(Permission.STAFF_CREATE))
        ):
            ...
    """
    async def check_permission(
        current_staff: StaffMember = Depends(get_current_staff)
    ) -> StaffMember:
        # Obter permissões do role
        role_permissions = ROLE_PERMISSIONS.get(current_staff.role, [])
        
        if permission not in role_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão necessária: {permission.value}. Seu role: {current_staff.role.value}"
            )
        
        return current_staff
    
    return check_permission
```

#### Helper para Verificar Múltiplas Permissões

```python
def require_any_permission(*permissions: Permission):
    """
    Verifica se o usuário tem pelo menos uma das permissões.
    """
    async def check_permissions(
        current_staff: StaffMember = Depends(get_current_staff)
    ) -> StaffMember:
        role_permissions = ROLE_PERMISSIONS.get(current_staff.role, [])
        
        if not any(perm in role_permissions for perm in permissions):
            perms_str = ", ".join([p.value for p in permissions])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Necessária uma das permissões: {perms_str}"
            )
        
        return current_staff
    
    return check_permissions
```

### 4. Controle por Recurso (Ownership)

#### Verificar se Usuário Pode Acessar Recurso Específico

```python
# app/core/permissions.py

async def can_access_resource(
    resource_org_id: str,
    resource_owner_id: Optional[int],
    current_staff: StaffMember,
    permission: Permission,
) -> bool:
    """
    Verifica se o usuário pode acessar um recurso específico.
    
    Regras:
    1. Deve estar na mesma organização
    2. Deve ter a permissão necessária
    3. Se for recurso próprio, pode acessar (mesmo sem permissão específica)
    4. Se for recurso de outro, precisa de permissão
    """
    # Mesma organização
    if resource_org_id != current_staff.organization_id:
        return False
    
    # Recurso próprio (pode acessar)
    if resource_owner_id and resource_owner_id == current_staff.id:
        return True
    
    # Verificar permissão
    role_permissions = ROLE_PERMISSIONS.get(current_staff.role, [])
    return permission in role_permissions
```

## Estrutura de Implementação

### Fase 1: Preparação

1. **Definir Permissões**
   - Listar todas as funcionalidades
   - Criar enum `Permission`
   - Documentar cada permissão

2. **Mapear Roles → Permissões**
   - Definir `ROLE_PERMISSIONS`
   - Revisar com stakeholders
   - Documentar regras de negócio

3. **Atualizar Model StaffMember** (se necessário)
   - Verificar se `department` é suficiente
   - Considerar adicionar campo `permissions_override` (futuro)

### Fase 2: Implementação Core

1. **Criar Sistema de Permissões**
   - `app/core/permissions.py` - Expandir com sistema completo
   - `require_permission()` - Dependency factory
   - `require_any_permission()` - Múltiplas permissões
   - `can_access_resource()` - Verificação de ownership

2. **Atualizar Endpoints Existentes**
   - Substituir `require_admin` por `require_permission(Permission.STAFF_CREATE)`
   - Aplicar permissões granulares
   - Adicionar verificação de ownership onde necessário

3. **Criar Helpers**
   - Função para listar permissões do usuário atual
   - Função para verificar permissão programaticamente
   - Decorators para simplificar uso

### Fase 3: Testes e Validação

1. **Testes Unitários**
   - Testar cada permissão
   - Testar combinações de roles
   - Testar edge cases

2. **Testes de Integração**
   - Testar endpoints com diferentes roles
   - Verificar respostas 403 corretas
   - Validar ownership

3. **Documentação**
   - Atualizar documentação de endpoints
   - Criar guia de permissões
   - Documentar regras de negócio

## Exemplos de Uso Futuro

### Endpoint com Permissão Específica

```python
@router.post("/staff")
async def create_staff(
    staff_data: StaffCreate,
    current_staff: StaffMember = Depends(require_permission(Permission.STAFF_CREATE)),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
):
    # Apenas usuários com STAFF_CREATE podem criar
    ...
```

### Endpoint com Múltiplas Permissões

```python
@router.get("/staff/{staff_id}")
async def get_staff(
    staff_id: int,
    current_staff: StaffMember = Depends(require_any_permission(
        Permission.STAFF_VIEW,
        Permission.STAFF_UPDATE
    )),
    db: AsyncSession = Depends(get_db),
):
    # Pode visualizar se tiver VIEW ou UPDATE
    ...
```

### Endpoint com Verificação de Ownership

```python
@router.put("/staff/{staff_id}")
async def update_staff(
    staff_id: int,
    staff_data: StaffUpdate,
    current_staff: StaffMember = Depends(require_permission(Permission.STAFF_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    # Buscar staff a ser atualizado
    target_staff = await db.get(StaffMember, staff_id)
    
    # Verificar ownership
    can_access = await can_access_resource(
        resource_org_id=target_staff.organization_id,
        resource_owner_id=target_staff.id,
        current_staff=current_staff,
        permission=Permission.STAFF_UPDATE,
    )
    
    if not can_access:
        raise HTTPException(403, "Sem permissão para atualizar este membro")
    
    # Atualizar...
```

## Cargos Específicos: Exemplos

### Gerente de Vendas

```python
# Configuração
role = StaffRole.MANAGER
department = "Vendas"

# Permissões
- STAFF_VIEW
- STAFF_VIEW_STATS
- PATIENT_VIEW
- PATIENT_CREATE
- SALE_VIEW
- SALE_CREATE
- SALE_UPDATE
- SALE_VIEW_REPORTS
```

### Vendedor

```python
# Configuração
role = StaffRole.STAFF
department = "Vendas"

# Permissões
- STAFF_VIEW (apenas visualizar equipe)
- PATIENT_VIEW
- PATIENT_CREATE
- SALE_VIEW
- SALE_CREATE
- SALE_UPDATE (apenas próprias vendas)
```

### Óptico

```python
# Configuração
role = StaffRole.STAFF
department = "Óptica"

# Permissões
- PATIENT_VIEW
- PATIENT_UPDATE (dados ópticos)
- PRODUCT_VIEW
- PRODUCT_UPDATE (estoque de lentes)
```

## Considerações Importantes

### 1. Backward Compatibility

- Manter `require_admin`, `require_manager_or_admin` funcionando
- Criar wrappers que usam o novo sistema
- Migração gradual

### 2. Performance

- Cache de permissões por role (não buscar do banco toda vez)
- Verificação rápida (lookup em dict)
- Evitar queries desnecessárias

### 3. Flexibilidade Futura

- Considerar permissões customizadas por usuário (futuro)
- Permitir múltiplos roles (futuro)
- Sistema de herança de permissões

### 4. Segurança

- **Nunca confiar no frontend** - sempre validar no backend
- Logs de tentativas de acesso negado
- Auditoria de mudanças de permissões

## Checklist de Implementação

### Preparação
- [ ] Definir todas as permissões necessárias
- [ ] Mapear roles → permissões
- [ ] Documentar regras de negócio
- [ ] Revisar com stakeholders

### Implementação
- [ ] Criar enum `Permission`
- [ ] Criar dict `ROLE_PERMISSIONS`
- [ ] Implementar `require_permission()`
- [ ] Implementar `require_any_permission()`
- [ ] Implementar `can_access_resource()`
- [ ] Atualizar endpoints existentes
- [ ] Adicionar testes

### Validação
- [ ] Testar todos os roles
- [ ] Testar todas as permissões
- [ ] Validar ownership
- [ ] Documentar mudanças
- [ ] Treinar equipe

## Próximos Passos

1. **Revisar este planejamento** com a equipe
2. **Definir permissões específicas** para cada módulo
3. **Mapear roles do negócio** (Gerente, Vendedor, etc.)
4. **Priorizar implementação** por módulo
5. **Implementar gradualmente** (não tudo de uma vez)

## Referências

- Documentação atual: `docs/CONTROLE_ACESSO.md`
- Código atual: `app/core/permissions.py`
- Model Staff: `app/models/staff_model.py`

---

**Nota**: Este é um planejamento. A implementação deve ser feita gradualmente, testando cada etapa antes de prosseguir.

