# Sistema de Cargos e Permissões Granulares

## 📋 Índice

1. [Sistema Atual](#sistema-atual)
2. [Problema e Necessidades](#problema-e-necessidades)
3. [Opções de Solução](#opções-de-solução)
4. [Recomendação](#recomendação)
5. [Implementação Detalhada](#implementação-detalhada)
6. [Integração Frontend/Backend](#integração-frontendbackend)

---

## 🔍 Sistema Atual

### Roles Existentes

O sistema atual possui **4 roles fixos** definidos como Enum:

```python
class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"        # Acesso total à organização
    MANAGER = "MANAGER"    # Gestão e relatórios
    STAFF = "STAFF"        # Acesso básico
    ASSISTANT = "ASSISTANT" # Acesso limitado (não usado ainda)
```

### Limitações

1. **Poucos roles**: Apenas 4 opções, não cobre cargos específicos
2. **Sem granularidade**: Não diferencia "vendedor" de "gerente de vendas"
3. **Sem permissões específicas**: Não permite controlar ações individuais
4. **Rígido**: Para adicionar novo cargo, precisa modificar código

### Como Funciona Atualmente

```python
# Verificação de role
current_staff: StaffMember = Depends(require_admin)  # Apenas ADMIN
current_staff: StaffMember = Depends(require_manager_or_admin)  # MANAGER ou ADMIN
current_staff: StaffMember = Depends(require_staff_or_above)  # STAFF, MANAGER ou ADMIN
```

---

## 🎯 Problema e Necessidades

### Cargos Necessários

Você precisa de cargos específicos como:
- **Vendedor**: Cadastra vendas, gerencia clientes
- **Gerente**: Gerencia equipe, relatórios
- **Auxiliar**: Apoio operacional
- **Motoboy**: Acesso muito limitado (só uma página)
- **Outros**: Podem surgir no futuro

### Requisitos

1. **Cargos específicos**: Cada cargo tem responsabilidades diferentes
2. **Permissões granulares**: Controlar ações individuais (criar venda, ver relatório, etc.)
3. **Controle no Frontend**: Next.js precisa saber quais páginas mostrar
4. **Controle no Backend**: API precisa validar permissões
5. **Flexibilidade**: Fácil adicionar novos cargos/permissões

---

## 💡 Opções de Solução

### Opção 1: Expandir Enum de Roles (Simples)

**Conceito**: Adicionar mais roles ao enum existente.

```python
class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    ASSISTANT = "ASSISTANT"
    # Novos cargos
    VENDEDOR = "VENDEDOR"
    GERENTE_VENDAS = "GERENTE_VENDAS"
    AUXILIAR = "AUXILIAR"
    MOTOBOY = "MOTOBOY"
```

**Vantagens**:
- ✅ Simples de implementar
- ✅ Não requer mudanças estruturais
- ✅ Funciona com código existente

**Desvantagens**:
- ❌ Ainda é rígido (precisa modificar código para novo cargo)
- ❌ Não permite permissões granulares
- ❌ Enum pode ficar muito grande
- ❌ Difícil controlar ações específicas (ex: "vendedor pode criar venda mas não deletar")

**Quando usar**: Se você tem poucos cargos (5-10) e não precisa de permissões muito específicas.

---

### Opção 2: Sistema de Permissões Granulares (Flexível)

**Conceito**: Separar **cargos** (títulos) de **permissões** (ações).

**Estrutura**:
- **Cargos**: Vendedor, Gerente, Auxiliar, Motoboy (apenas títulos)
- **Permissões**: `vendas.criar`, `vendas.editar`, `vendas.deletar`, `clientes.ver`, etc.

```python
# Tabela de cargos (flexível)
class JobTitle(BaseModel):
    __tablename__ = "job_titles"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(String, nullable=False)
    name = Column(String, nullable=False)  # "Vendedor", "Gerente", etc.
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

# Tabela de permissões
class Permission(BaseModel):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # "vendas.criar"
    name = Column(String, nullable=False)  # "Criar Venda"
    category = Column(String, nullable=False)  # "vendas", "clientes", etc.

# Tabela de associação (cargo tem permissões)
class JobTitlePermission(BaseModel):
    __tablename__ = "job_title_permissions"
    
    job_title_id = Column(Integer, ForeignKey("job_titles.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))
    # Unique constraint: (job_title_id, permission_id)

# Modificar StaffMember
class StaffMember(BaseModel):
    # ... campos existentes ...
    job_title_id = Column(Integer, ForeignKey("job_titles.id"), nullable=True)
    role = Column(Enum(StaffRole), nullable=True)  # Manter para compatibilidade
```

**Vantagens**:
- ✅ Muito flexível (adiciona cargos sem modificar código)
- ✅ Permissões granulares (controla cada ação)
- ✅ Fácil gerenciar via interface admin
- ✅ Escalável (suporta muitos cargos)

**Desvantagens**:
- ❌ Mais complexo de implementar
- ❌ Requer mudanças estruturais
- ❌ Mais queries (verificar permissões)

**Quando usar**: Se você precisa de controle fino sobre ações ou muitos cargos diferentes.

---

### Opção 3: Híbrido (Roles + Permissões Específicas) ⭐ RECOMENDADO

**Conceito**: Manter roles hierárquicos (ADMIN, MANAGER, STAFF) + adicionar campo de cargo específico + permissões opcionais.

**Estrutura**:
```python
class StaffMember(BaseModel):
    # ... campos existentes ...
    
    # Role hierárquico (mantém compatibilidade)
    role = Column(Enum(StaffRole), default=StaffRole.STAFF, nullable=False)
    
    # Cargo específico (novo campo)
    job_title = Column(String, nullable=True)  # "Vendedor", "Gerente de Vendas", "Motoboy"
    
    # Permissões customizadas (opcional, para casos especiais)
    custom_permissions = Column(JSON, nullable=True)  # ["vendas.criar", "clientes.ver"]
```

**Lógica de Permissões**:
```python
def has_permission(staff: StaffMember, permission: str) -> bool:
    """
    Verifica se staff tem permissão.
    
    Hierarquia:
    1. ADMIN tem todas as permissões
    2. MANAGER tem permissões de gestão
    3. Verifica permissões do cargo (job_title)
    4. Verifica permissões customizadas
    """
    
    # ADMIN tem tudo
    if staff.role == StaffRole.ADMIN:
        return True
    
    # Permissões baseadas em role
    role_permissions = get_role_permissions(staff.role)
    if permission in role_permissions:
        return True
    
    # Permissões do cargo
    if staff.job_title:
        job_permissions = get_job_title_permissions(staff.job_title)
        if permission in job_permissions:
            return True
    
    # Permissões customizadas
    if staff.custom_permissions:
        if permission in staff.custom_permissions:
            return True
    
    return False
```

**Vantagens**:
- ✅ Mantém compatibilidade com código existente
- ✅ Flexível para adicionar cargos
- ✅ Permite permissões granulares quando necessário
- ✅ Simples para casos comuns (usa role)
- ✅ Complexo apenas quando necessário (custom_permissions)

**Desvantagens**:
- ⚠️ Lógica um pouco mais complexa
- ⚠️ Precisa definir mapeamento de cargos para permissões

**Quando usar**: **RECOMENDADO** para a maioria dos casos. Balanceia simplicidade e flexibilidade.

---

## 🎯 Recomendação

### Para o Seu Caso: **Opção 3 (Híbrido)**

**Por quê?**
1. Você já tem código funcionando com roles → mantém compatibilidade
2. Precisa de cargos específicos (Vendedor, Motoboy) → campo `job_title`
3. Alguns cargos precisam de controle fino (Motoboy só uma página) → `custom_permissions`
4. Fácil de implementar gradualmente → não quebra nada existente

### Estrutura Recomendada

```python
# Roles hierárquicos (mantém)
ADMIN > MANAGER > STAFF > ASSISTANT

# Cargos específicos (novo campo)
job_title: "Vendedor" | "Gerente de Vendas" | "Auxiliar" | "Motoboy" | null

# Mapeamento de permissões por cargo
JOB_TITLE_PERMISSIONS = {
    "Vendedor": [
        "vendas.criar",
        "vendas.editar",
        "vendas.ver",
        "clientes.ver",
        "clientes.criar",
        "clientes.editar"
    ],
    "Gerente de Vendas": [
        "vendas.*",  # Todas as permissões de vendas
        "clientes.*",
        "relatorios.ver",
        "equipe.ver"
    ],
    "Auxiliar": [
        "clientes.ver",
        "produtos.ver"
    ],
    "Motoboy": [
        "entregas.ver_minhas"  # Só vê suas próprias entregas
    ]
}
```

---

## 🛠️ Implementação Detalhada

### Fase 1: Adicionar Campo `job_title`

#### 1.1. Modificar Model

```python
# app/models/staff_model.py
class StaffMember(BaseModel):
    # ... campos existentes ...
    role = Column(Enum(StaffRole), default=StaffRole.STAFF, nullable=False)
    
    # NOVO: Cargo específico
    job_title = Column(String, nullable=True, index=True)  # "Vendedor", "Motoboy", etc.
    
    # NOVO: Permissões customizadas (JSON)
    custom_permissions = Column(JSON, nullable=True)  # ["vendas.criar", "clientes.ver"]
```

#### 1.2. Migration

```python
# scripts/migrations/add_job_title.py
from sqlalchemy import text

async def upgrade():
    # Adicionar coluna job_title
    await db.execute(text("""
        ALTER TABLE staff_members 
        ADD COLUMN job_title VARCHAR(100) NULL;
    """))
    
    # Adicionar coluna custom_permissions
    await db.execute(text("""
        ALTER TABLE staff_members 
        ADD COLUMN custom_permissions JSONB NULL;
    """))
    
    # Criar índice
    await db.execute(text("""
        CREATE INDEX idx_staff_job_title ON staff_members(organization_id, job_title);
    """))
```

#### 1.3. Atualizar Schema

```python
# app/schemas/staff_schema.py
class StaffBase(BaseModel):
    # ... campos existentes ...
    role: StaffRole
    job_title: Optional[str] = Field(None, description="Cargo específico: Vendedor, Motoboy, etc.")
    custom_permissions: Optional[List[str]] = Field(None, description="Permissões customizadas")
```

### Fase 2: Sistema de Permissões

#### 2.1. Criar Módulo de Permissões

```python
# app/core/permissions.py (adicionar)

# Mapeamento de permissões por cargo
JOB_TITLE_PERMISSIONS: dict[str, list[str]] = {
    "Vendedor": [
        "vendas.criar",
        "vendas.editar",
        "vendas.ver",
        "clientes.ver",
        "clientes.criar",
        "clientes.editar",
        "produtos.ver"
    ],
    "Gerente de Vendas": [
        "vendas.*",
        "clientes.*",
        "relatorios.ver",
        "equipe.ver"
    ],
    "Auxiliar": [
        "clientes.ver",
        "produtos.ver",
        "estoque.ver"
    ],
    "Motoboy": [
        "entregas.ver_minhas",
        "entregas.atualizar_status"
    ]
}

# Permissões por role hierárquico
ROLE_PERMISSIONS: dict[StaffRole, list[str]] = {
    StaffRole.ADMIN: ["*"],  # Tudo
    StaffRole.MANAGER: [
        "vendas.*",
        "clientes.*",
        "relatorios.*",
        "equipe.ver",
        "equipe.editar"
    ],
    StaffRole.STAFF: [
        "vendas.ver",
        "clientes.ver",
        "produtos.ver"
    ],
    StaffRole.ASSISTANT: [
        "clientes.ver"
    ]
}

def has_permission(staff: StaffMember, permission: str) -> bool:
    """
    Verifica se staff tem permissão.
    
    Args:
        staff: StaffMember
        permission: Código da permissão (ex: "vendas.criar")
    
    Returns:
        True se tem permissão, False caso contrário
    """
    # 1. ADMIN tem tudo
    if staff.role == StaffRole.ADMIN:
        return True
    
    # 2. Verifica permissões do role
    role_perms = ROLE_PERMISSIONS.get(staff.role, [])
    if _check_permission(permission, role_perms):
        return True
    
    # 3. Verifica permissões do cargo
    if staff.job_title:
        job_perms = JOB_TITLE_PERMISSIONS.get(staff.job_title, [])
        if _check_permission(permission, job_perms):
            return True
    
    # 4. Verifica permissões customizadas
    if staff.custom_permissions:
        if _check_permission(permission, staff.custom_permissions):
            return True
    
    return False

def _check_permission(permission: str, allowed_permissions: list[str]) -> bool:
    """
    Verifica se permission está em allowed_permissions.
    Suporta wildcard: "vendas.*" permite "vendas.criar", "vendas.editar", etc.
    """
    # Permissão exata
    if permission in allowed_permissions:
        return True
    
    # Wildcard: "vendas.*" permite "vendas.criar"
    for allowed in allowed_permissions:
        if allowed.endswith(".*"):
            prefix = allowed[:-2]  # Remove ".*"
            if permission.startswith(prefix + "."):
                return True
    
    # Wildcard global: "*" permite tudo
    if "*" in allowed_permissions:
        return True
    
    return False

def require_permission(permission: str):
    """
    Factory que cria dependency para verificar permissão específica.
    
    Uso:
        @router.post("/vendas")
        async def criar_venda(
            current_staff: StaffMember = Depends(require_permission("vendas.criar"))
        ):
            ...
    """
    async def check_permission(
        current_staff: StaffMember = Depends(get_current_staff)
    ) -> StaffMember:
        if not has_permission(current_staff, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Permissão necessária: {permission}"
            )
        return current_staff
    
    return check_permission
```

#### 2.2. Usar em Endpoints

```python
# app/routers/v1/sales.py
from app.core.permissions import require_permission

@router.post("/vendas", response_model=VendaResponse)
async def criar_venda(
    venda_data: VendaCreate,
    current_staff: StaffMember = Depends(require_permission("vendas.criar")),
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova venda. Requer permissão 'vendas.criar'."""
    # ...

@router.get("/vendas", response_model=List[VendaResponse])
async def listar_vendas(
    current_staff: StaffMember = Depends(require_permission("vendas.ver")),
    db: AsyncSession = Depends(get_db),
):
    """Lista vendas. Requer permissão 'vendas.ver'."""
    # ...

@router.delete("/vendas/{venda_id}")
async def deletar_venda(
    venda_id: int,
    current_staff: StaffMember = Depends(require_permission("vendas.deletar")),
    db: AsyncSession = Depends(get_db),
):
    """Deleta venda. Requer permissão 'vendas.deletar'."""
    # ...
```

### Fase 3: Endpoint para Listar Permissões

```python
# app/routers/v1/staff.py (adicionar)

@router.get("/me/permissions")
async def get_my_permissions(
    current_staff: StaffMember = Depends(get_current_staff),
):
    """
    Retorna todas as permissões do usuário atual.
    Usado pelo frontend para controlar UI.
    """
    from app.core.permissions import get_all_permissions
    
    permissions = get_all_permissions(current_staff)
    
    return {
        "role": current_staff.role.value,
        "job_title": current_staff.job_title,
        "permissions": permissions,
        "can": {
            "create_sale": has_permission(current_staff, "vendas.criar"),
            "edit_sale": has_permission(current_staff, "vendas.editar"),
            "delete_sale": has_permission(current_staff, "vendas.deletar"),
            "view_reports": has_permission(current_staff, "relatorios.ver"),
            # ... outras permissões
        }
    }

def get_all_permissions(staff: StaffMember) -> list[str]:
    """Retorna lista de todas as permissões do staff."""
    permissions = set()
    
    # Permissões do role
    role_perms = ROLE_PERMISSIONS.get(staff.role, [])
    permissions.update(role_perms)
    
    # Permissões do cargo
    if staff.job_title:
        job_perms = JOB_TITLE_PERMISSIONS.get(staff.job_title, [])
        permissions.update(job_perms)
    
    # Permissões customizadas
    if staff.custom_permissions:
        permissions.update(staff.custom_permissions)
    
    return sorted(list(permissions))
```

---

## 🎨 Integração Frontend/Backend

### Backend: Endpoint de Permissões

```python
GET /api/v1/staff/me/permissions

Resposta:
{
  "role": "STAFF",
  "job_title": "Vendedor",
  "permissions": [
    "vendas.criar",
    "vendas.editar",
    "vendas.ver",
    "clientes.ver",
    "clientes.criar"
  ],
  "can": {
    "create_sale": true,
    "edit_sale": true,
    "delete_sale": false,
    "view_reports": false
  }
}
```

### Frontend (Next.js): Hook de Permissões

```typescript
// hooks/usePermissions.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface Permissions {
  role: string;
  job_title: string | null;
  permissions: string[];
  can: {
    create_sale: boolean;
    edit_sale: boolean;
    delete_sale: boolean;
    view_reports: boolean;
    // ...
  };
}

export function usePermissions() {
  const { data, isLoading } = useQuery<Permissions>({
    queryKey: ['permissions'],
    queryFn: async () => {
      const response = await api.get('/staff/me/permissions');
      return response.data;
    },
  });

  return {
    permissions: data,
    isLoading,
    hasPermission: (permission: string) => {
      return data?.permissions.includes(permission) || false;
    },
    can: data?.can || {},
  };
}
```

### Frontend: Componente de Proteção

```typescript
// components/ProtectedRoute.tsx
import { usePermissions } from '@/hooks/usePermissions';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredJobTitle?: string;
}

export function ProtectedRoute({
  children,
  requiredPermission,
  requiredJobTitle,
}: ProtectedRouteProps) {
  const { permissions, isLoading } = usePermissions();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    // Verifica permissão
    if (requiredPermission) {
      const hasPermission = permissions?.permissions.includes(requiredPermission);
      if (!hasPermission) {
        router.push('/unauthorized');
        return;
      }
    }

    // Verifica cargo
    if (requiredJobTitle) {
      if (permissions?.job_title !== requiredJobTitle) {
        router.push('/unauthorized');
        return;
      }
    }
  }, [permissions, isLoading, requiredPermission, requiredJobTitle, router]);

  if (isLoading) {
    return <div>Carregando...</div>;
  }

  return <>{children}</>;
}
```

### Frontend: Uso em Páginas

```typescript
// app/vendas/page.tsx
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { usePermissions } from '@/hooks/usePermissions';

export default function VendasPage() {
  const { can } = usePermissions();

  return (
    <ProtectedRoute requiredPermission="vendas.ver">
      <div>
        <h1>Vendas</h1>
        
        {can.create_sale && (
          <button>Criar Venda</button>
        )}
        
        {can.edit_sale && (
          <button>Editar</button>
        )}
        
        {can.delete_sale && (
          <button>Deletar</button>
        )}
      </div>
    </ProtectedRoute>
  );
}
```

### Frontend: Menu Condicional

```typescript
// components/Sidebar.tsx
import { usePermissions } from '@/hooks/usePermissions';

export function Sidebar() {
  const { can, permissions } = usePermissions();

  return (
    <nav>
      <Link href="/dashboard">Dashboard</Link>
      
      {can.create_sale && (
        <Link href="/vendas">Vendas</Link>
      )}
      
      {can.view_reports && (
        <Link href="/relatorios">Relatórios</Link>
      )}
      
      {/* Motoboy só vê entregas */}
      {permissions?.job_title === 'Motoboy' && (
        <Link href="/entregas">Minhas Entregas</Link>
      )}
    </nav>
  );
}
```

---

## 📊 Exemplos de Uso

### Exemplo 1: Vendedor

```python
# Criar vendedor
staff = StaffMember(
    full_name="João Silva",
    email="joao@example.com",
    role=StaffRole.STAFF,  # Role hierárquico
    job_title="Vendedor",  # Cargo específico
    organization_id="org_xxx"
)

# Permissões automáticas:
# - vendas.criar ✅
# - vendas.editar ✅
# - vendas.ver ✅
# - clientes.ver ✅
# - clientes.criar ✅
# - produtos.ver ✅
```

### Exemplo 2: Motoboy (Acesso Limitado)

```python
# Criar motoboy
staff = StaffMember(
    full_name="Pedro Entregador",
    email="pedro@example.com",
    role=StaffRole.ASSISTANT,  # Role mais baixo
    job_title="Motoboy",  # Cargo específico
    organization_id="org_xxx"
)

# Permissões automáticas:
# - entregas.ver_minhas ✅
# - entregas.atualizar_status ✅
# - Nada mais ❌
```

### Exemplo 3: Vendedor com Permissão Extra

```python
# Vendedor que também pode ver relatórios
staff = StaffMember(
    full_name="Maria Vendedora",
    email="maria@example.com",
    role=StaffRole.STAFF,
    job_title="Vendedor",
    custom_permissions=["relatorios.ver"],  # Permissão extra
    organization_id="org_xxx"
)

# Permissões:
# - Todas de "Vendedor" ✅
# - relatorios.ver ✅ (custom)
```

---

## 🎯 Resumo

### Sistema Recomendado: Híbrido (Opção 3)

1. **Mantém roles hierárquicos** (ADMIN, MANAGER, STAFF, ASSISTANT) → compatibilidade
2. **Adiciona campo `job_title`** → cargos específicos (Vendedor, Motoboy, etc.)
3. **Adiciona `custom_permissions`** → permissões granulares quando necessário
4. **Sistema de verificação** → `has_permission()` e `require_permission()`
5. **Endpoint de permissões** → frontend consulta para controlar UI

### Vantagens

- ✅ Compatível com código existente
- ✅ Flexível para novos cargos
- ✅ Permissões granulares quando necessário
- ✅ Fácil de usar no frontend
- ✅ Escalável

### Próximos Passos

1. Adicionar campos `job_title` e `custom_permissions` ao model
2. Criar migration
3. Implementar sistema de permissões
4. Atualizar endpoints para usar `require_permission()`
5. Criar endpoint `/staff/me/permissions`
6. Integrar com frontend

---

**Documento criado em**: 2025-01-XX  
**Status**: Proposta de arquitetura (não implementado)  
**Recomendação**: Opção 3 (Híbrido)

