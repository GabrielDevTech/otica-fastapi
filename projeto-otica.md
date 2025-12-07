# Projeto Ótica - Documentação Completa do Backend

## 📋 Índice

1. [Proposta do Sistema](#proposta-do-sistema)
2. [Arquitetura e Tecnologias](#arquitetura-e-tecnologias)
3. [Fluxo de Autenticação](#fluxo-de-autenticação)
4. [Modelos de Dados (Tabelas)](#modelos-de-dados-tabelas)
5. [Endpoints da API](#endpoints-da-api)
6. [Fluxos de Negócio](#fluxos-de-negócio)
7. [Controle de Acesso (RBAC)](#controle-de-acesso-rbac)
8. [Multi-tenancy](#multi-tenancy)
9. [Considerações Técnicas Importantes](#considerações-técnicas-importantes)

---

## 🎯 Proposta do Sistema

### Visão Geral

Sistema SaaS multi-tenant para gestão de óticas, permitindo que múltiplas organizações (óticas) gerenciem seus funcionários, lojas, setores e solicitações de acesso de forma isolada e segura.

### Características Principais

- **Multi-tenancy**: Cada organização tem seus dados completamente isolados
- **Autenticação Externa**: Integração com Clerk para gerenciamento de identidade
- **RBAC**: Controle de acesso baseado em roles (ADMIN, MANAGER, STAFF, ASSISTANT)
- **API RESTful**: Endpoints padronizados seguindo boas práticas
- **Async/Await**: Operações assíncronas para melhor performance

### Objetivos

1. Permitir que organizações gerenciem sua equipe (staff)
2. Gerenciar múltiplas lojas por organização
3. Organizar funcionários em setores/departamentos
4. Processar solicitações de acesso de novos usuários
5. Enviar convites diretos para novos membros da equipe

---

## 🏗️ Arquitetura e Tecnologias

### Stack Tecnológico

- **Framework**: FastAPI (Python 3.14+)
- **ORM**: SQLAlchemy (Async) com asyncpg
- **Banco de Dados**: PostgreSQL (Supabase)
- **Autenticação**: Clerk (JWT via JWKS)
- **Validação**: Pydantic
- **HTTP Client**: httpx (async)

### Estrutura de Diretórios

```
otica-api/
├── app/
│   ├── core/              # Configurações centrais
│   │   ├── config.py      # Settings e variáveis de ambiente
│   │   ├── database.py    # Configuração SQLAlchemy async
│   │   ├── security.py    # Validação JWT e autenticação
│   │   └── permissions.py # RBAC e controle de acesso
│   ├── models/            # SQLAlchemy Models (tabelas)
│   │   ├── base_class.py
│   │   ├── staff_model.py
│   │   ├── organization_model.py
│   │   ├── store_model.py
│   │   ├── department_model.py
│   │   └── access_request_model.py
│   ├── schemas/           # Pydantic Schemas (validação)
│   │   ├── staff_schema.py
│   │   ├── organization_schema.py
│   │   ├── store_schema.py
│   │   ├── department_schema.py
│   │   └── access_request_schema.py
│   ├── routers/           # Endpoints FastAPI
│   │   └── v1/
│   │       ├── staff.py
│   │       ├── stores.py
│   │       ├── departments.py
│   │       ├── access_requests.py
│   │       └── invitations.py
│   ├── services/          # Serviços externos
│   │   └── clerk_service.py
│   └── main.py           # Aplicação principal
├── scripts/              # Scripts utilitários
└── docs/                 # Documentação técnica
```

### Configurações Importantes

**Variáveis de Ambiente (.env)**:
- `CLERK_ISSUER`: URL do Clerk (ex: `https://thorough-mutt-7.clerk.accounts.dev`)
- `CLERK_SECRET_KEY`: Chave secreta do Clerk (para API calls)
- `DATABASE_URL`: Connection string do PostgreSQL
- `CORS_ORIGINS`: Origens permitidas (separadas por vírgula)

**Configurações do Banco**:
- Desabilitado cache de prepared statements (`statement_cache_size: 0`) para compatibilidade com pgbouncer (Supabase)
- Desabilitado JIT (`jit: off`) para compatibilidade com pgbouncer
- Todas as queries são assíncronas

---

## 🔐 Fluxo de Autenticação

### Visão Geral

O sistema utiliza **JWT tokens do Clerk** para autenticação. O token contém informações sobre o usuário e a organização à qual ele pertence.

### Processo de Validação

1. **Cliente envia requisição** com header `Authorization: Bearer <token>`
2. **Backend extrai o token** via `HTTPBearer` dependency
3. **Busca JWKS** do Clerk (`{CLERK_ISSUER}/.well-known/jwks.json`)
4. **Encontra a chave pública** correspondente ao `kid` do token
5. **Converte JWK para PEM** (formato necessário para validação)
6. **Valida assinatura** e decodifica o token
7. **Extrai `organization_id`** do payload (campo `org_id` ou `o.id`)
8. **Extrai `user_id`** do payload (campo `sub` - Clerk user ID)

### Dependências de Autenticação

```python
# Dependência base: valida token e retorna dados
verify_token() -> dict {
    "org_id": str,
    "user_id": str,
    "payload": dict
}

# Dependência simplificada: retorna apenas org_id
get_current_org_id() -> str

# Dependência simplificada: retorna apenas user_id
get_current_user_id() -> str
```

### Fluxo de Vinculação de Usuário

Quando um usuário aceita um convite do Clerk:

1. **Usuário cria conta no Clerk** (via email do convite)
2. **Primeira requisição** ao backend com token JWT
3. **Backend busca StaffMember** pelo `clerk_id` (não encontra, pois ainda não está vinculado)
4. **Backend busca email** do usuário na API do Clerk
5. **Backend busca StaffMember** pelo email (encontra registro criado antes do convite)
6. **Backend atualiza** `clerk_id` no StaffMember
7. **Próximas requisições** encontram diretamente pelo `clerk_id`

### Tratamento de Erros

- **401 Unauthorized**: Token inválido, expirado ou sem assinatura válida
- **403 Forbidden**: Token válido mas sem `organization_id`
- **404 Not Found**: Usuário não encontrado na equipe ou inativo

---

## 📊 Modelos de Dados (Tabelas)

### BaseModel (Classe Base)

Todos os models herdam de `BaseModel` que inclui:
- `id`: Integer (PK, auto-increment)
- `created_at`: DateTime (timezone-aware, auto)
- `updated_at`: DateTime (timezone-aware, auto-update)

### 1. Organization (Organizações/Tenants)

**Tabela**: `organizations`

**Campos**:
- `id`: Integer (PK)
- `clerk_org_id`: String(255) - ID da organização no Clerk (único)
- `name`: String(255) - Nome fantasia
- `cnpj`: String(14) - CNPJ (opcional)
- `access_code`: String(20) - Código para solicitar acesso (único)
- `plan`: String(50) - Plano (basic, pro, enterprise)
- `is_active`: Boolean - Status da organização
- `created_at`: DateTime
- `updated_at`: DateTime

**Relacionamentos**:
- `stores`: List[Store] (CASCADE delete)
- `departments`: List[Department] (CASCADE delete)
- `access_requests`: List[AccessRequest] (CASCADE delete)

**Observações**:
- Cada organização é um tenant isolado
- `clerk_org_id` é usado para vincular com Clerk
- `access_code` é usado para solicitações públicas de acesso

### 2. StaffMember (Membros da Equipe)

**Tabela**: `staff_members`

**Campos**:
- `id`: Integer (PK)
- `clerk_id`: String - ID do usuário no Clerk (único, nullable)
- `organization_id`: String - ID da organização (Clerk org_id, não FK)
- `store_id`: Integer (FK para stores, nullable)
- `department_id`: Integer (FK para departments, nullable)
- `full_name`: String - Nome completo
- `email`: String - Email (único por organização)
- `role`: Enum(StaffRole) - ADMIN, MANAGER, STAFF, ASSISTANT
- `is_active`: Boolean - Status do membro
- `avatar_url`: String - URL do avatar (opcional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Índices**:
- `idx_staff_org_email`: (organization_id, email) - UNIQUE
- `idx_staff_org_role`: (organization_id, role)
- Índices em `organization_id`, `store_id`, `department_id`, `email`

**Relacionamentos**:
- `store`: Store (opcional)
- `department`: Department (opcional)

**Observações**:
- `organization_id` é String (Clerk org_id), não FK para organizations
- Email é único **dentro** da mesma organização
- `clerk_id` pode ser NULL até o usuário aceitar o convite

### 3. Store (Lojas)

**Tabela**: `stores`

**Campos**:
- `id`: Integer (PK)
- `organization_id`: Integer (FK para organizations, CASCADE delete)
- `name`: String(255) - Nome da loja
- `address`: String - Endereço (opcional)
- `phone`: String(20) - Telefone (opcional)
- `is_active`: Boolean - Status da loja
- `created_at`: DateTime
- `updated_at`: DateTime

**Relacionamentos**:
- `organization`: Organization
- `staff_members`: List[StaffMember] (via backref)
- `access_requests`: List[AccessRequest] (via backref)

**Observações**:
- Uma organização pode ter múltiplas lojas
- Soft delete via `is_active = False`

### 4. Department (Setores)

**Tabela**: `departments`

**Campos**:
- `id`: Integer (PK)
- `organization_id`: Integer (FK para organizations, CASCADE delete)
- `name`: String(255) - Nome do setor
- `is_active`: Boolean - Status do setor
- `created_at`: DateTime
- `updated_at`: DateTime

**Relacionamentos**:
- `organization`: Organization
- `staff_members`: List[StaffMember] (via backref)
- `access_requests`: List[AccessRequest] (via backref)

**Observações**:
- Setores são globais da organização (não específicos de loja)
- Soft delete via `is_active = False`

### 5. AccessRequest (Solicitações de Acesso)

**Tabela**: `access_requests`

**Campos**:
- `id`: Integer (PK)
- `organization_id`: Integer (FK para organizations, CASCADE delete)
- `store_id`: Integer (FK para stores, nullable)
- `department_id`: Integer (FK para departments, nullable)
- `full_name`: String(255) - Nome do solicitante
- `email`: String(255) - Email do solicitante
- `message`: Text - Mensagem opcional
- `status`: Enum(AccessRequestStatus) - pending, approved, rejected
- `assigned_role`: String(50) - Role atribuído na aprovação (opcional)
- `reviewed_at`: String - Data/hora da revisão (ISO format)
- `reviewed_by`: Integer - ID do staff que revisou (opcional)
- `rejection_reason`: Text - Motivo da rejeição (opcional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Enum AccessRequestStatus**:
- `PENDING`: Aguardando aprovação
- `APPROVED`: Aprovada
- `REJECTED`: Rejeitada

**Relacionamentos**:
- `organization`: Organization
- `store`: Store (opcional)
- `department`: Department (opcional)

**Observações**:
- Endpoint público para criar solicitação (sem autenticação)
- Aprovação cria convite no Clerk e StaffMember no banco
- Rejeição apenas atualiza status

---

## 🛣️ Endpoints da API

### Base URL

Todos os endpoints estão sob `/api/v1`

### Autenticação

Todos os endpoints (exceto públicos) requerem:
```
Authorization: Bearer <token_jwt_do_clerk>
```

---

### 1. Staff (Equipe)

**Base Path**: `/api/v1/staff`

#### GET `/api/v1/staff`

Lista membros da equipe da organização atual.

**Autenticação**: ✅ Requerida (STAFF, MANAGER ou ADMIN)

**Query Parameters**:
- `q` (string, opcional): Busca textual em nome/email
- `role` (enum, opcional): Filtrar por role (ADMIN, MANAGER, STAFF, ASSISTANT)

**Resposta**: `200 OK`
```json
[
  {
    "id": 1,
    "clerk_id": "user_xxx",
    "organization_id": "org_xxx",
    "store_id": 1,
    "department_id": 2,
    "full_name": "João Silva",
    "email": "joao@example.com",
    "role": "ADMIN",
    "is_active": true,
    "avatar_url": null,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

#### GET `/api/v1/staff/stats`

Retorna estatísticas agregadas da equipe.

**Autenticação**: ✅ Requerida (MANAGER ou ADMIN)

**Resposta**: `200 OK`
```json
{
  "total_users": 10,
  "active_users": 8,
  "admins": 2,
  "managers": 3
}
```

#### POST `/api/v1/staff`

Cria um novo membro da equipe.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body**:
```json
{
  "full_name": "Maria Santos",
  "email": "maria@example.com",
  "role": "STAFF",
  "store_id": 1,
  "department_id": 2,
  "is_active": true
}
```

**Resposta**: `201 Created`
```json
{
  "id": 2,
  "clerk_id": null,
  "organization_id": "org_xxx",
  "store_id": 1,
  "department_id": 2,
  "full_name": "Maria Santos",
  "email": "maria@example.com",
  "role": "STAFF",
  "is_active": true,
  "avatar_url": null,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Validações**:
- Email deve ser único na organização
- `organization_id` é injetado automaticamente do token (ignorado se enviado no body)

---

### 2. Stores (Lojas)

**Base Path**: `/api/v1/stores`

#### GET `/api/v1/stores`

Lista todas as lojas ativas da organização.

**Autenticação**: ✅ Requerida (STAFF, MANAGER ou ADMIN)

**Resposta**: `200 OK`
```json
[
  {
    "id": 1,
    "organization_id": 1,
    "name": "Loja Centro",
    "address": "Rua Principal, 123",
    "phone": "(11) 1234-5678",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

#### GET `/api/v1/stores/{store_id}`

Obtém uma loja específica.

**Autenticação**: ✅ Requerida (STAFF, MANAGER ou ADMIN)

**Resposta**: `200 OK` ou `404 Not Found`

#### POST `/api/v1/stores`

Cria uma nova loja.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body**:
```json
{
  "name": "Loja Norte",
  "address": "Av. Norte, 456",
  "phone": "(11) 9876-5432",
  "is_active": true
}
```

**Resposta**: `201 Created`

**Validações**:
- Nome deve ser único na organização
- `organization_id` é injetado automaticamente

#### PATCH `/api/v1/stores/{store_id}`

Atualiza uma loja.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body** (campos opcionais):
```json
{
  "name": "Loja Norte Atualizada",
  "address": "Nova Rua, 789",
  "phone": "(11) 1111-2222",
  "is_active": false
}
```

**Resposta**: `200 OK` ou `404 Not Found`

#### DELETE `/api/v1/stores/{store_id}`

Desativa uma loja (soft delete).

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Resposta**: `204 No Content` ou `404 Not Found`

**Observação**: Apenas define `is_active = False`, não deleta fisicamente.

---

### 3. Departments (Setores)

**Base Path**: `/api/v1/departments`

#### GET `/api/v1/departments`

Lista todos os setores ativos da organização.

**Autenticação**: ✅ Requerida (STAFF, MANAGER ou ADMIN)

**Resposta**: `200 OK`
```json
[
  {
    "id": 1,
    "organization_id": 1,
    "name": "Vendas",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

#### GET `/api/v1/departments/{department_id}`

Obtém um setor específico.

**Autenticação**: ✅ Requerida (STAFF, MANAGER ou ADMIN)

**Resposta**: `200 OK` ou `404 Not Found`

#### POST `/api/v1/departments`

Cria um novo setor.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body**:
```json
{
  "name": "Atendimento",
  "is_active": true
}
```

**Resposta**: `201 Created`

**Validações**:
- Nome deve ser único na organização
- `organization_id` é injetado automaticamente

#### PATCH `/api/v1/departments/{department_id}`

Atualiza um setor.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body** (campos opcionais):
```json
{
  "name": "Atendimento ao Cliente",
  "is_active": false
}
```

**Resposta**: `200 OK` ou `404 Not Found`

#### DELETE `/api/v1/departments/{department_id}`

Desativa um setor (soft delete).

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Resposta**: `204 No Content` ou `404 Not Found`

---

### 4. Access Requests (Solicitações de Acesso)

**Base Path**: `/api/v1/access-requests`

#### POST `/api/v1/access-requests/public` ⚠️ PÚBLICO

Cria uma solicitação de acesso (sem autenticação).

**Autenticação**: ❌ Não requerida

**Body**:
```json
{
  "access_code": "ABC123",
  "full_name": "Pedro Oliveira",
  "email": "pedro@example.com",
  "message": "Gostaria de trabalhar na loja",
  "store_id": 1,
  "department_id": 2
}
```

**Resposta**: `201 Created`
```json
{
  "id": 1,
  "organization_id": 1,
  "store_id": 1,
  "department_id": 2,
  "full_name": "Pedro Oliveira",
  "email": "pedro@example.com",
  "message": "Gostaria de trabalhar na loja",
  "status": "pending",
  "assigned_role": null,
  "requested_at": "2025-01-01T00:00:00Z",
  "reviewed_at": null,
  "reviewed_by": null,
  "rejection_reason": null
}
```

**Validações**:
- `access_code` deve existir e estar ativo
- Email não pode ter solicitação pendente na mesma organização
- Email não pode já ser membro da organização
- `store_id` e `department_id` devem pertencer à organização

#### GET `/api/v1/access-requests/public/validate-code` ⚠️ PÚBLICO

Valida um código de acesso e retorna informações básicas.

**Autenticação**: ❌ Não requerida

**Query Parameters**:
- `code` (string, obrigatório): Código de acesso

**Resposta**: `200 OK`
```json
{
  "organization_name": "Ótica Central",
  "stores": [
    {"id": 1, "name": "Loja Centro"}
  ],
  "departments": [
    {"id": 1, "name": "Vendas"}
  ]
}
```

**Resposta de Erro**: `404 Not Found` (código inválido)

#### GET `/api/v1/access-requests`

Lista solicitações de acesso da organização.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Query Parameters**:
- `status_filter` (enum, opcional): Filtrar por status (pending, approved, rejected)

**Resposta**: `200 OK`
```json
[
  {
    "id": 1,
    "organization_id": 1,
    "store_id": 1,
    "department_id": 2,
    "full_name": "Pedro Oliveira",
    "email": "pedro@example.com",
    "message": "Gostaria de trabalhar",
    "status": "pending",
    "assigned_role": null,
    "requested_at": "2025-01-01T00:00:00Z",
    "reviewed_at": null,
    "reviewed_by": null,
    "rejection_reason": null,
    "store_name": "Loja Centro",
    "department_name": "Vendas",
    "organization_name": "Ótica Central"
  }
]
```

#### GET `/api/v1/access-requests/{request_id}`

Obtém uma solicitação específica.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Resposta**: `200 OK` ou `404 Not Found`

#### POST `/api/v1/access-requests/{request_id}/approve`

Aprova uma solicitação de acesso.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body**:
```json
{
  "assigned_role": "STAFF"
}
```

**Resposta**: `200 OK`
```json
{
  "message": "Solicitação aprovada com sucesso. Um email foi enviado para o usuário.",
  "staff_id": 3,
  "invitation_id": "inv_xxx"
}
```

**Processo**:
1. Cria convite no Clerk (envia email automático)
2. Cria StaffMember no banco (com `clerk_id = null`)
3. Atualiza status da solicitação para `approved`
4. Quando usuário aceitar convite, `clerk_id` será vinculado automaticamente

#### POST `/api/v1/access-requests/{request_id}/reject`

Rejeita uma solicitação de acesso.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body**:
```json
{
  "rejection_reason": "Não atende aos requisitos"
}
```

**Resposta**: `200 OK`
```json
{
  "message": "Solicitação rejeitada"
}
```

#### DELETE `/api/v1/access-requests/{request_id}`

Deleta uma solicitação de acesso.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Resposta**: `204 No Content` ou `404 Not Found`

---

### 5. Invitations (Convites Diretos)

**Base Path**: `/api/v1/invitations`

#### POST `/api/v1/invitations`

Convida um novo usuário diretamente (sem solicitação).

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Body**:
```json
{
  "full_name": "Ana Costa",
  "email": "ana@example.com",
  "role": "MANAGER",
  "store_id": 1,
  "department_id": 2
}
```

**Resposta**: `201 Created`
```json
{
  "message": "Convite enviado com sucesso!",
  "staff_id": 4,
  "invitation_id": "inv_xxx",
  "email": "ana@example.com"
}
```

**Processo**:
1. Valida que email não existe na organização
2. Cria convite no Clerk (envia email automático)
3. Cria StaffMember no banco (com `clerk_id = null`)
4. Quando usuário aceitar convite, `clerk_id` será vinculado automaticamente

#### POST `/api/v1/invitations/resend/{staff_id}`

Reenvia convite para um usuário que ainda não aceitou.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Resposta**: `200 OK`
```json
{
  "message": "Convite reenviado com sucesso!",
  "invitation_id": "inv_xxx",
  "email": "ana@example.com"
}
```

**Validações**:
- Staff deve existir e não ter `clerk_id` (ainda não aceitou)

---

## 🔄 Fluxos de Negócio

### 1. Fluxo de Solicitação de Acesso

```
1. Usuário acessa página pública
   ↓
2. Usuário informa código de acesso
   ↓
3. Frontend valida código (GET /access-requests/public/validate-code)
   ↓
4. Frontend mostra nome da organização e formulário
   ↓
5. Usuário preenche formulário e envia (POST /access-requests/public)
   ↓
6. Backend cria AccessRequest com status PENDING
   ↓
7. Admin visualiza solicitação (GET /access-requests)
   ↓
8. Admin aprova ou rejeita (POST /access-requests/{id}/approve ou /reject)
   ↓
9. Se aprovado:
   - Clerk envia email de convite
   - StaffMember é criado (clerk_id = null)
   ↓
10. Usuário aceita convite e cria conta no Clerk
   ↓
11. Na primeira requisição, backend vincula clerk_id ao StaffMember
```

### 2. Fluxo de Convite Direto

```
1. Admin acessa painel de convites
   ↓
2. Admin preenche formulário (POST /invitations)
   ↓
3. Backend valida email único
   ↓
4. Backend cria convite no Clerk
   ↓
5. Clerk envia email automático
   ↓
6. Backend cria StaffMember (clerk_id = null)
   ↓
7. Usuário recebe email e cria conta
   ↓
8. Na primeira requisição, backend vincula clerk_id ao StaffMember
```

### 3. Fluxo de Autenticação em Cada Requisição

```
1. Cliente envia requisição com token JWT
   ↓
2. Backend valida token (verify_token)
   ↓
3. Backend extrai organization_id e user_id
   ↓
4. Backend busca StaffMember pelo clerk_id + organization_id
   ↓
5. Se não encontrar, tenta buscar por email (para novos usuários)
   ↓
6. Se encontrar por email, vincula clerk_id
   ↓
7. Verifica permissões (RBAC)
   ↓
8. Executa endpoint com dados isolados por organization_id
```

---

## 🔒 Controle de Acesso (RBAC)

### Roles Disponíveis

1. **ADMIN**: Acesso total à organização
2. **MANAGER**: Acesso a gestão e relatórios
3. **STAFF**: Acesso básico de funcionário
4. **ASSISTANT**: Acesso limitado

### Hierarquia de Permissões

```
ADMIN > MANAGER > STAFF > ASSISTANT
```

### Dependências de Permissão

```python
# Requer ADMIN
require_admin = require_role(StaffRole.ADMIN)

# Requer MANAGER ou ADMIN
require_manager_or_admin = require_role(StaffRole.ADMIN, StaffRole.MANAGER)

# Requer STAFF, MANAGER ou ADMIN
require_staff_or_above = require_role(
    StaffRole.ADMIN, 
    StaffRole.MANAGER, 
    StaffRole.STAFF
)
```

### Matriz de Permissões por Endpoint

| Endpoint | ADMIN | MANAGER | STAFF | ASSISTANT |
|----------|-------|---------|-------|-----------|
| GET /staff | ✅ | ✅ | ✅ | ❌ |
| GET /staff/stats | ✅ | ✅ | ❌ | ❌ |
| POST /staff | ✅ | ❌ | ❌ | ❌ |
| GET /stores | ✅ | ✅ | ✅ | ❌ |
| POST /stores | ✅ | ❌ | ❌ | ❌ |
| PATCH /stores/{id} | ✅ | ❌ | ❌ | ❌ |
| DELETE /stores/{id} | ✅ | ❌ | ❌ | ❌ |
| GET /departments | ✅ | ✅ | ✅ | ❌ |
| POST /departments | ✅ | ❌ | ❌ | ❌ |
| PATCH /departments/{id} | ✅ | ❌ | ❌ | ❌ |
| DELETE /departments/{id} | ✅ | ❌ | ❌ | ❌ |
| GET /access-requests | ✅ | ❌ | ❌ | ❌ |
| POST /access-requests/{id}/approve | ✅ | ❌ | ❌ | ❌ |
| POST /access-requests/{id}/reject | ✅ | ❌ | ❌ | ❌ |
| POST /invitations | ✅ | ❌ | ❌ | ❌ |

---

## 🏢 Multi-tenancy

### Estratégia: Logical Multi-tenancy

O sistema utiliza **logical multi-tenancy** com isolamento por `organization_id`:

- **Schema compartilhado**: Todas as organizações usam as mesmas tabelas
- **Isolamento por filtro**: Todas as queries filtram por `organization_id`
- **Isolamento automático**: `organization_id` vem do token JWT (não pode ser alterado pelo cliente)

### Implementação

1. **Token JWT contém `organization_id`**: Extraído automaticamente
2. **Dependency `get_current_org_id`**: Injeta `organization_id` em todos os endpoints
3. **Queries sempre filtram**: `WHERE organization_id = current_org_id`
4. **Validação de acesso**: Verifica se recursos pertencem à organização do token

### Pontos de Atenção

- **Nunca confiar no `organization_id` do body**: Sempre usar do token
- **Validar relacionamentos**: Verificar se `store_id`/`department_id` pertencem à organização
- **Conversão de IDs**: `organization_id` no token é String (Clerk), mas nas tabelas pode ser Integer

### Exemplo de Isolamento

```python
# ❌ ERRADO: Aceitar organization_id do body
new_staff = StaffMember(
    organization_id=staff_data.organization_id  # PERIGO!
)

# ✅ CORRETO: Usar organization_id do token
new_staff = StaffMember(
    organization_id=current_org_id  # Do token, sempre seguro
)
```

---

## ⚠️ Considerações Técnicas Importantes

### 1. Compatibilidade com Supabase/pgbouncer

**Problema**: Supabase usa pgbouncer que não suporta prepared statements.

**Solução**: Desabilitar cache de prepared statements:
```python
connect_args={
    "statement_cache_size": 0,
    "server_settings": {"jit": "off"}
}
```

**Impacto**: Queries podem ser ligeiramente mais lentas, mas funcionam corretamente.

### 2. Async/Await em Todas as Operações

**Padrão**: Todas as operações de banco são assíncronas.

**Benefícios**:
- Melhor performance com múltiplas requisições
- Não bloqueia thread principal
- Escalabilidade melhor

**Cuidado**: Sempre usar `await` em operações de banco.

### 3. Vinculação de Clerk ID

**Problema**: Quando um convite é criado, o `clerk_id` ainda não existe.

**Solução**: 
- Criar StaffMember com `clerk_id = null`
- Na primeira requisição, buscar por email e vincular
- Usar API do Clerk para obter email do usuário

**Fluxo**:
1. Convite criado → StaffMember com `clerk_id = null`
2. Usuário aceita → Cria conta no Clerk
3. Primeira requisição → Backend busca por email e vincula `clerk_id`

### 4. Validação de Token JWT

**Processo**:
1. Busca JWKS do Clerk (cache pode ser implementado)
2. Converte JWK para PEM (formato necessário)
3. Valida assinatura RSA
4. Verifica issuer (`CLERK_ISSUER`)
5. Extrai `organization_id` e `user_id`

**Erros Comuns**:
- Token expirado → Gerar novo token
- Issuer incorreto → Verificar `CLERK_ISSUER` no `.env`
- Token sem `organization_id` → Usuário deve estar em organização no Clerk

### 5. Soft Delete vs Hard Delete

**Padrão**: Soft delete via `is_active = False`

**Tabelas com soft delete**:
- `stores` (via `is_active`)
- `departments` (via `is_active`)
- `staff_members` (via `is_active`)

**Tabelas sem soft delete**:
- `access_requests` (DELETE físico)

**Razão**: Manter histórico e permitir reativação.

### 6. Conversão de Organization ID

**Problema**: `organization_id` no token é String (Clerk), mas nas tabelas é Integer.

**Solução**: Função helper `get_org_internal_id()`:
```python
async def get_org_internal_id(db, clerk_org_id: str) -> int:
    org = await db.execute(
        select(Organization).where(
            Organization.clerk_org_id == clerk_org_id
        )
    )
    return org.id
```

**Uso**: Sempre converter antes de usar em FKs.

### 7. Validação de Email Único

**Regra**: Email deve ser único **dentro da mesma organização**.

**Implementação**: Índice composto único:
```python
Index('idx_staff_org_email', 'organization_id', 'email', unique=True)
```

**Impacto**: Permite mesmo email em organizações diferentes.

### 8. Integração com Clerk API

**Serviço**: `ClerkService` encapsula chamadas à API do Clerk.

**Métodos principais**:
- `create_user_invitation()`: Cria convite e envia email
- `get_user_by_email()`: Busca usuário por email
- `add_user_to_organization()`: Adiciona usuário existente

**Autenticação**: Usa `CLERK_SECRET_KEY` no header `Authorization: Bearer {key}`

**Erros**: Tratados e propagados como HTTPException.

### 9. CORS Configuration

**Configuração**: Permitir origens específicas.

**Padrão**: `http://localhost:3000,http://localhost:5173`

**Produção**: Atualizar `CORS_ORIGINS` no `.env` com domínios reais.

### 10. Logging e Debug

**Atual**: `echo=True` no SQLAlchemy (mostra queries SQL).

**Produção**: Desabilitar `echo=True` para melhor performance.

**Debug**: Scripts em `scripts/` para debug de tokens e configurações.

---

## 📝 Notas Finais

### Decisões de Design

1. **Multi-tenancy lógico**: Escolhido por simplicidade e facilidade de manutenção
2. **Clerk para autenticação**: Terceiriza complexidade de autenticação
3. **Soft delete**: Mantém histórico e permite auditoria
4. **Async/await**: Melhor performance e escalabilidade
5. **Pydantic para validação**: Validação automática e documentação

### Pontos de Atenção para Novos Desenvolvimentos

1. **Sempre filtrar por `organization_id`**: Nunca confiar no cliente
2. **Validar relacionamentos**: Verificar se FKs pertencem à organização
3. **Usar async**: Todas as operações de banco devem ser assíncronas
4. **Tratar erros do Clerk**: API pode falhar, sempre tratar exceções
5. **Validar permissões**: Usar dependências de RBAC apropriadas
6. **Documentar endpoints**: Adicionar docstrings descritivas
7. **Testar isolamento**: Garantir que dados não vazam entre organizações

### Próximos Passos Sugeridos

1. **Migrations**: Implementar Alembic para versionamento de schema
2. **Testes**: Adicionar testes unitários e de integração
3. **Cache**: Implementar cache para JWKS e queries frequentes
4. **Webhooks**: Implementar webhooks do Clerk para sincronização
5. **Logging**: Implementar sistema de logs estruturado
6. **Rate Limiting**: Adicionar rate limiting para proteção
7. **Novos Módulos**: Pacientes, Produtos, Vendas, etc.

---

**Documento gerado em**: 2025-01-XX  
**Versão da API**: 1.0.0  
**Última atualização**: Após merge da branch `art` para `main`

