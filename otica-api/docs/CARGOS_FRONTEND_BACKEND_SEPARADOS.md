# Sistema de Cargos: Backend (Roles) + Frontend (Funções)

## 📋 Índice

1. [Conceito](#conceito)
2. [Arquitetura Proposta](#arquitetura-proposta)
3. [Backend: Apenas Roles Hierárquicos](#backend-apenas-roles-hierárquicos)
4. [Frontend: Roles + Funções](#frontend-roles--funções)
5. [Fluxo de Funcionamento](#fluxo-de-funcionamento)
6. [Exemplos Práticos](#exemplos-práticos)
7. [Vantagens e Desvantagens](#vantagens-e-desvantagens)
8. [Implementação](#implementação)

---

## 🎯 Conceito

### Ideia Principal

**Separar responsabilidades**:
- **Backend**: Usa apenas **roles hierárquicos** (ADMIN, MANAGER, STAFF, ASSISTANT) para controle de acesso à API
- **Frontend**: Usa **roles + funções** (job_title) para controlar quais páginas/componentes mostrar

### Por Que Separar?

1. **Backend simples**: Mantém RBAC tradicional, fácil de entender e manter
2. **Frontend flexível**: Pode ter funções específicas (Vendedor, Motoboy) sem complicar o backend
3. **Segurança**: Backend sempre valida por role, frontend só controla UI
4. **Escalabilidade**: Fácil adicionar novas funções no frontend sem mudar backend

---

## 🏗️ Arquitetura Proposta

### Estrutura de Dados

```python
# Backend: StaffMember
class StaffMember(BaseModel):
    # Campos existentes
    role = Column(Enum(StaffRole), nullable=False)  # ADMIN, MANAGER, STAFF, ASSISTANT
    
    # NOVO: Campo para função (usado apenas pelo frontend)
    job_title = Column(String, nullable=True)  # "Vendedor", "Motoboy", "Gerente de Vendas", etc.
    
    # Exemplo de dados:
    # role = "ADMIN", job_title = "Vendedor"
    # role = "ASSISTANT", job_title = "Motoboy"
    # role = "STAFF", job_title = "Auxiliar"
```

### Mapeamento de Funções para Roles

| Função (Frontend) | Role (Backend) | Descrição |
|-------------------|----------------|-----------|
| **Vendedor** | ADMIN ou MANAGER | Pode criar vendas, gerenciar clientes |
| **Gerente de Vendas** | ADMIN ou MANAGER | Gerencia equipe, vê relatórios |
| **Auxiliar** | STAFF | Apoio operacional, acesso básico |
| **Motoboy** | ASSISTANT | Só visualiza página de entregas |
| **Caixa** | STAFF | Processa pagamentos, acesso limitado |

**Regra**: A função (`job_title`) **não afeta permissões no backend**, apenas controla UI no frontend.

---

## 🔐 Backend: Apenas Roles Hierárquicos

### Roles Existentes (Mantém Como Está)

```python
class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"        # Acesso total
    MANAGER = "MANAGER"    # Gestão e relatórios
    STAFF = "STAFF"        # Acesso básico
    ASSISTANT = "ASSISTANT" # Acesso limitado (só visualização)
```

### Controle de Acesso no Backend

**Backend sempre valida por ROLE, nunca por função**:

```python
# ✅ CORRETO: Valida por role
@router.post("/vendas")
async def criar_venda(
    current_staff: StaffMember = Depends(require_admin),  # Só ADMIN
):
    # ...

# ❌ ERRADO: Não validar por job_title
@router.post("/vendas")
async def criar_venda(
    current_staff: StaffMember = Depends(get_current_staff),
):
    if current_staff.job_title != "Vendedor":  # NÃO FAZER ISSO
        raise HTTPException(403)
```

### Endpoint que Retorna Dados do Usuário

```python
# app/routers/v1/staff.py

@router.get("/me")
async def get_my_info(
    current_staff: StaffMember = Depends(get_current_staff),
):
    """
    Retorna informações do usuário atual.
    Frontend usa para controlar UI.
    """
    return {
        "id": current_staff.id,
        "full_name": current_staff.full_name,
        "email": current_staff.email,
        "role": current_staff.role.value,  # "ADMIN", "STAFF", etc.
        "job_title": current_staff.job_title,  # "Vendedor", "Motoboy", etc. (pode ser null)
        "store_id": current_staff.store_id,
        "department_id": current_staff.department_id,
        "is_active": current_staff.is_active
    }
```

**Resposta**:
```json
{
  "id": 1,
  "full_name": "João Silva",
  "email": "joao@example.com",
  "role": "ADMIN",
  "job_title": "Vendedor",
  "store_id": 1,
  "department_id": 2,
  "is_active": true
}
```

---

## 🎨 Frontend: Roles + Funções

### Estrutura no Frontend

O frontend recebe **role** e **job_title** do backend e usa ambos para controlar a UI:

```typescript
// Tipos
interface UserInfo {
  id: number;
  full_name: string;
  email: string;
  role: "ADMIN" | "MANAGER" | "STAFF" | "ASSISTANT";
  job_title: string | null;  // "Vendedor", "Motoboy", etc.
  store_id: number | null;
  department_id: number | null;
  is_active: boolean;
}
```

### Hook para Obter Informações do Usuário

```typescript
// hooks/useUser.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useUser() {
  const { data, isLoading } = useQuery<UserInfo>({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await api.get('/staff/me');
      return response.data;
    },
  });

  return {
    user: data,
    isLoading,
    isAdmin: data?.role === 'ADMIN',
    isManager: data?.role === 'MANAGER' || data?.role === 'ADMIN',
    isStaff: data?.role === 'STAFF' || data?.role === 'MANAGER' || data?.role === 'ADMIN',
    isAssistant: data?.role === 'ASSISTANT',
    // Funções específicas
    isVendedor: data?.job_title === 'Vendedor',
    isMotoboy: data?.job_title === 'Motoboy',
    isAuxiliar: data?.job_title === 'Auxiliar',
    isGerenteVendas: data?.job_title === 'Gerente de Vendas',
  };
}
```

### Controle de Páginas por Função

```typescript
// app/layout.tsx ou _app.tsx
import { useUser } from '@/hooks/useUser';
import { useRouter } from 'next/navigation';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, isMotoboy } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    // Motoboy só pode acessar página de entregas
    if (isMotoboy && router.pathname !== '/entregas') {
      router.push('/entregas');
    }
  }, [user, isLoading, router]);

  return <>{children}</>;
}
```

### Menu Lateral Condicional

```typescript
// components/Sidebar.tsx
import { useUser } from '@/hooks/useUser';

export function Sidebar() {
  const { 
    isAdmin, 
    isVendedor, 
    isMotoboy, 
    isAuxiliar,
    isGerenteVendas 
  } = useUser();

  return (
    <nav>
      {/* Dashboard: todos veem */}
      <Link href="/dashboard">Dashboard</Link>

      {/* Vendas: Vendedor, Gerente de Vendas, Admin */}
      {(isVendedor || isGerenteVendas || isAdmin) && (
        <Link href="/vendas">Vendas</Link>
      )}

      {/* Clientes: Vendedor, Gerente de Vendas, Admin, Auxiliar */}
      {(isVendedor || isGerenteVendas || isAdmin || isAuxiliar) && (
        <Link href="/clientes">Clientes</Link>
      )}

      {/* Relatórios: Gerente de Vendas, Admin */}
      {(isGerenteVendas || isAdmin) && (
        <Link href="/relatorios">Relatórios</Link>
      )}

      {/* Entregas: Motoboy, Admin */}
      {(isMotoboy || isAdmin) && (
        <Link href="/entregas">Entregas</Link>
      )}

      {/* Configurações: Apenas Admin */}
      {isAdmin && (
        <Link href="/configuracoes">Configurações</Link>
      )}
    </nav>
  );
}
```

### Proteção de Rotas por Função

```typescript
// components/ProtectedRoute.tsx
import { useUser } from '@/hooks/useUser';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ("ADMIN" | "MANAGER" | "STAFF" | "ASSISTANT")[];
  allowedJobTitles?: string[];
  requireBoth?: boolean;  // Se true, precisa ter role E job_title
}

export function ProtectedRoute({
  children,
  allowedRoles,
  allowedJobTitles,
  requireBoth = false,
}: ProtectedRouteProps) {
  const { user, isLoading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!user) {
      router.push('/login');
      return;
    }

    // Verifica role
    if (allowedRoles) {
      const hasRole = allowedRoles.includes(user.role);
      if (!hasRole) {
        router.push('/unauthorized');
        return;
      }
    }

    // Verifica job_title
    if (allowedJobTitles) {
      const hasJobTitle = user.job_title && allowedJobTitles.includes(user.job_title);
      
      if (requireBoth) {
        // Precisa ter role E job_title
        if (!hasJobTitle) {
          router.push('/unauthorized');
          return;
        }
      } else {
        // Precisa ter role OU job_title
        if (!hasJobTitle && !allowedRoles?.includes(user.role)) {
          router.push('/unauthorized');
          return;
        }
      }
    }
  }, [user, isLoading, allowedRoles, allowedJobTitles, requireBoth, router]);

  if (isLoading) {
    return <div>Carregando...</div>;
  }

  return <>{children}</>;
}
```

### Uso em Páginas

```typescript
// app/vendas/page.tsx
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function VendasPage() {
  return (
    <ProtectedRoute 
      allowedRoles={["ADMIN", "MANAGER"]}
      allowedJobTitles={["Vendedor", "Gerente de Vendas"]}
    >
      <div>
        <h1>Vendas</h1>
        {/* Conteúdo da página */}
      </div>
    </ProtectedRoute>
  );
}
```

```typescript
// app/entregas/page.tsx
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function EntregasPage() {
  return (
    <ProtectedRoute 
      allowedRoles={["ASSISTANT", "ADMIN"]}
      allowedJobTitles={["Motoboy"]}
    >
      <div>
        <h1>Minhas Entregas</h1>
        {/* Conteúdo da página */}
      </div>
    </ProtectedRoute>
  );
}
```

---

## 🔄 Fluxo de Funcionamento

### 1. Usuário Faz Login

```
1. Frontend: Usuário faz login no Clerk
2. Frontend: Obtém token JWT
3. Frontend: Chama GET /api/v1/staff/me com token
4. Backend: Valida token, busca StaffMember
5. Backend: Retorna { role: "ADMIN", job_title: "Vendedor" }
6. Frontend: Armazena informações do usuário
```

### 2. Usuário Navega no Sistema

```
1. Frontend: Usuário clica em "Vendas"
2. Frontend: Verifica se user.job_title === "Vendedor" OU user.role === "ADMIN"
3. Frontend: Se permitido, mostra página
4. Frontend: Se não permitido, redireciona para /unauthorized
```

### 3. Usuário Faz Requisição à API

```
1. Frontend: Usuário cria uma venda
2. Frontend: POST /api/v1/vendas com token
3. Backend: Valida token, extrai role
4. Backend: Verifica se role === "ADMIN" (não verifica job_title)
5. Backend: Se permitido, cria venda
6. Backend: Se não permitido, retorna 403
```

**Importante**: Backend **sempre** valida por role, nunca por job_title.

---

## 📝 Exemplos Práticos

### Exemplo 1: Vendedor (Role ADMIN, Função Vendedor)

**Backend**:
```python
staff = StaffMember(
    full_name="João Silva",
    email="joao@example.com",
    role=StaffRole.ADMIN,  # Backend valida como ADMIN
    job_title="Vendedor",  # Frontend usa para controlar UI
    organization_id="org_xxx"
)
```

**Permissões Backend**:
- ✅ Pode criar/editar/deletar vendas (porque é ADMIN)
- ✅ Pode acessar todos os endpoints (porque é ADMIN)

**Permissões Frontend**:
- ✅ Vê menu "Vendas" (porque job_title === "Vendedor")
- ✅ Vê menu "Clientes" (porque job_title === "Vendedor")
- ❌ NÃO vê menu "Configurações" (mesmo sendo ADMIN, frontend pode esconder)
- ❌ NÃO vê menu "Relatórios" (se frontend decidir esconder para vendedor)

**Observação**: Mesmo sendo ADMIN no backend, o frontend pode limitar a UI baseado em `job_title`.

### Exemplo 2: Motoboy (Role ASSISTANT, Função Motoboy)

**Backend**:
```python
staff = StaffMember(
    full_name="Pedro Entregador",
    email="pedro@example.com",
    role=StaffRole.ASSISTANT,  # Backend valida como ASSISTANT
    job_title="Motoboy",  # Frontend usa para controlar UI
    organization_id="org_xxx"
)
```

**Permissões Backend**:
- ✅ Pode acessar endpoints que requerem ASSISTANT
- ❌ NÃO pode criar/editar/deletar (só visualização)

**Permissões Frontend**:
- ✅ Vê APENAS página "Entregas" (porque job_title === "Motoboy")
- ❌ NÃO vê menu "Vendas"
- ❌ NÃO vê menu "Clientes"
- ❌ NÃO vê menu "Relatórios"
- ❌ NÃO vê menu "Configurações"

**Fluxo**:
1. Motoboy faz login
2. Frontend verifica: `job_title === "Motoboy"`
3. Frontend redireciona automaticamente para `/entregas`
4. Frontend esconde todos os outros menus
5. Se tentar acessar outra página, redireciona para `/entregas`

### Exemplo 3: Gerente de Vendas (Role MANAGER, Função Gerente de Vendas)

**Backend**:
```python
staff = StaffMember(
    full_name="Maria Gerente",
    email="maria@example.com",
    role=StaffRole.MANAGER,  # Backend valida como MANAGER
    job_title="Gerente de Vendas",  # Frontend usa para controlar UI
    organization_id="org_xxx"
)
```

**Permissões Backend**:
- ✅ Pode acessar endpoints que requerem MANAGER ou ADMIN
- ✅ Pode ver relatórios, gerenciar equipe

**Permissões Frontend**:
- ✅ Vê menu "Vendas"
- ✅ Vê menu "Clientes"
- ✅ Vê menu "Relatórios" (porque job_title === "Gerente de Vendas")
- ✅ Vê menu "Equipe"
- ❌ NÃO vê menu "Configurações" (mesmo sendo MANAGER)

### Exemplo 4: Auxiliar (Role STAFF, Função Auxiliar)

**Backend**:
```python
staff = StaffMember(
    full_name="Ana Auxiliar",
    email="ana@example.com",
    role=StaffRole.STAFF,  # Backend valida como STAFF
    job_title="Auxiliar",  # Frontend usa para controlar UI
    organization_id="org_xxx"
)
```

**Permissões Backend**:
- ✅ Pode acessar endpoints que requerem STAFF, MANAGER ou ADMIN
- ✅ Acesso básico de leitura

**Permissões Frontend**:
- ✅ Vê menu "Clientes" (porque job_title === "Auxiliar")
- ✅ Vê menu "Produtos"
- ❌ NÃO vê menu "Vendas"
- ❌ NÃO vê menu "Relatórios"
- ❌ NÃO vê menu "Configurações"

---

## ✅ Vantagens e Desvantagens

### Vantagens

1. **Backend Simples**: Mantém RBAC tradicional, fácil de entender
2. **Frontend Flexível**: Pode ter funções específicas sem complicar backend
3. **Segurança**: Backend sempre valida por role (não pode ser burlado)
4. **Escalabilidade**: Fácil adicionar novas funções no frontend
5. **Compatibilidade**: Não quebra código existente
6. **Separação de Responsabilidades**: Backend = segurança, Frontend = UX

### Desvantagens

1. **Duplicação de Lógica**: Precisa manter mapeamento role → função no frontend
2. **Possível Inconsistência**: Se frontend e backend não estiverem alinhados
3. **Menos Granular no Backend**: Não pode ter permissões muito específicas por função
4. **Dependência do Frontend**: Se frontend for comprometido, usuário pode ver páginas (mas API ainda bloqueia)

### Mitigações

1. **Documentação**: Manter documentação clara de qual role cada função deve ter
2. **Validação no Backend**: Sempre validar por role, nunca confiar no frontend
3. **Testes**: Testar que frontend e backend estão alinhados
4. **Auditoria**: Logar ações para detectar inconsistências

---

## 🛠️ Implementação

### Passo 1: Adicionar Campo `job_title` ao Model

```python
# app/models/staff_model.py
class StaffMember(BaseModel):
    # ... campos existentes ...
    role = Column(Enum(StaffRole), default=StaffRole.STAFF, nullable=False)
    
    # NOVO: Campo para função (usado apenas pelo frontend)
    job_title = Column(String, nullable=True, index=True)
```

### Passo 2: Migration

```python
# scripts/migrations/add_job_title.py
from sqlalchemy import text

async def upgrade():
    await db.execute(text("""
        ALTER TABLE staff_members 
        ADD COLUMN job_title VARCHAR(100) NULL;
    """))
    
    await db.execute(text("""
        CREATE INDEX idx_staff_job_title 
        ON staff_members(organization_id, job_title);
    """))
```

### Passo 3: Atualizar Schema

```python
# app/schemas/staff_schema.py
class StaffResponse(StaffBase):
    # ... campos existentes ...
    role: StaffRole
    job_title: Optional[str] = Field(None, description="Função: Vendedor, Motoboy, etc.")
```

### Passo 4: Endpoint GET /staff/me

```python
# app/routers/v1/staff.py
@router.get("/me", response_model=StaffResponse)
async def get_my_info(
    current_staff: StaffMember = Depends(get_current_staff),
):
    """Retorna informações do usuário atual para o frontend."""
    return current_staff
```

### Passo 5: Frontend - Hook useUser

```typescript
// hooks/useUser.ts (código já mostrado acima)
```

### Passo 6: Frontend - Componentes de Proteção

```typescript
// components/ProtectedRoute.tsx (código já mostrado acima)
```

### Passo 7: Frontend - Menu Condicional

```typescript
// components/Sidebar.tsx (código já mostrado acima)
```

---

## 📊 Tabela de Mapeamento Recomendado

| Função (job_title) | Role (Backend) | Páginas no Frontend |
|-------------------|----------------|---------------------|
| **Vendedor** | ADMIN ou MANAGER | Vendas, Clientes, Produtos |
| **Gerente de Vendas** | MANAGER ou ADMIN | Vendas, Clientes, Relatórios, Equipe |
| **Auxiliar** | STAFF | Clientes, Produtos, Estoque |
| **Motoboy** | ASSISTANT | Apenas Entregas |
| **Caixa** | STAFF | Vendas (só processar pagamento), Clientes |
| **Gerente Geral** | ADMIN | Todas as páginas |

**Regra**: Escolha o role baseado nas **permissões de API** que a função precisa, não baseado no nome da função.

---

## 🎯 Resumo

### Conceito Principal

- **Backend**: Usa apenas **roles hierárquicos** (ADMIN, MANAGER, STAFF, ASSISTANT) para segurança
- **Frontend**: Usa **roles + funções** (job_title) para controlar UI
- **Separação**: Backend = segurança, Frontend = experiência do usuário

### Regras de Ouro

1. ✅ **Backend sempre valida por role**, nunca por job_title
2. ✅ **Frontend usa job_title** para controlar quais páginas mostrar
3. ✅ **Escolha role baseado em permissões de API**, não no nome da função
4. ✅ **Documente mapeamento** de funções para roles

### Exemplo de Uso

```python
# Criar vendedor
staff = StaffMember(
    role=StaffRole.ADMIN,      # Backend: pode tudo
    job_title="Vendedor"      # Frontend: só mostra páginas de vendedor
)

# Criar motoboy
staff = StaffMember(
    role=StaffRole.ASSISTANT,  # Backend: só visualização
    job_title="Motoboy"        # Frontend: só mostra página de entregas
)
```

---

**Documento criado em**: 2025-01-XX  
**Status**: Proposta de arquitetura (não implementado)  
**Abordagem**: Backend simples (roles) + Frontend flexível (funções)

