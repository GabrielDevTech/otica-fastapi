# Telas Prontas para Implementação - Sprint 1

## ✅ Status: Endpoints Implementados e Prontos para Uso

Este documento lista **TODAS as telas que podem ser implementadas AGORA** com os endpoints que já estão funcionando no backend.

---

## 📋 Índice

1. [1º Passo (A): Cadastro de Lojas (stores)](#1º-passo-a-cadastro-de-lojas-stores) ✅ PRONTO
2. [1º Passo (B): Cadastro de Departamentos (departments)](#1º-passo-b-cadastro-de-departamentos-departments) ✅ PRONTO
3. [2º Passo: Finalizar Equipe (staff_members)](#2º-passo-finalizar-equipe-staff_members) ✅ PRONTO
4. [3º Passo: Cadastro de Armações (products_frames)](#3º-passo-cadastro-de-armações-products_frames) ✅ PRONTO
5. [4º Passo: Cadastro de Lentes (products_lenses)](#4º-passo-cadastro-de-lentes-products_lenses) ✅ PRONTO
6. [5º Passo: Cadastro de Clientes (customers)](#5º-passo-cadastro-de-clientes-customers) ✅ PRONTO

---

## 1º Passo (A): Cadastro de Lojas (stores) ✅ PRONTO

### Endpoints Disponíveis

#### GET `/api/v1/stores`

**Descrição**: Lista todas as lojas ativas da organização.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Query Parameters**: Nenhum

**Response 200 OK**:
```typescript
[
  {
    "id": 1,
    "organization_id": 1,
    "name": "Óticas Diniz - Filial Shopping",
    "address_data": {
      "rua": "Av. Central",
      "numero": "100",
      "cep": "88000-000",
      "cidade": "Florianópolis",
      "estado": "SC"
    },
    "phone": "(48) 9999-9999",
    "tax_rate_machine": 2.5,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

**Telas a Implementar**:
- **Lista de Lojas** (`/lojas`): Tela que exibe todas as lojas da organização em formato de tabela ou cards. Deve mostrar: nome, endereço (formatado do JSON `address_data`), telefone, taxa da máquina (`tax_rate_machine`) e status (ativa/inativa). Deve ter botão para criar nova loja e ações para editar/excluir cada loja.

---

#### POST `/api/v1/stores`

**Descrição**: Cria uma nova loja.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body**:
```typescript
{
  "name": "Óticas Diniz - Filial Shopping",  // Obrigatório
  "address_data": {                          // Opcional, JSON
    "rua": "Av. Central",
    "numero": "100",
    "cep": "88000-000",
    "cidade": "Florianópolis",
    "estado": "SC"
  },
  "phone": "(48) 9999-9999",                 // Opcional
  "tax_rate_machine": 2.5                    // Opcional, taxa da máquina (%)
}
```

**Response 201 Created**:
```typescript
{
  "id": 1,
  "organization_id": 1,
  "name": "Óticas Diniz - Filial Shopping",
  "address_data": {
    "rua": "Av. Central",
    "numero": "100",
    "cep": "88000-000",
    "cidade": "Florianópolis",
    "estado": "SC"
  },
  "phone": "(48) 9999-9999",
  "tax_rate_machine": 2.5,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `400 Bad Request`: Já existe uma loja com este nome
- `403 Forbidden`: Acesso negado (não é ADMIN)

**Telas a Implementar**:
- **Criar Loja** (`/lojas/novo`): Formulário com campos: nome (obrigatório), endereço (campos separados que serão agrupados em JSON: rua, número, CEP, cidade, estado), telefone (opcional), taxa da máquina em % (opcional, numérico com 2 casas decimais). Botão de salvar e cancelar.

---

#### GET `/api/v1/stores/{store_id}`

**Descrição**: Obtém uma loja específica.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Detalhes da Loja** (`/lojas/{id}`): Tela de visualização com todos os dados da loja. Deve ter botão para editar e opção de desativar.

---

#### PATCH `/api/v1/stores/{store_id}`

**Descrição**: Atualiza uma loja.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body** (todos os campos opcionais):
```typescript
{
  "name": "Óticas Diniz - Filial Shopping Atualizada",
  "address_data": { /* ... */ },
  "phone": "(48) 1111-2222",
  "tax_rate_machine": 3.0,
  "is_active": false
}
```

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Editar Loja** (`/lojas/{id}/editar`): Formulário pré-preenchido com os dados atuais da loja. Mesmos campos do formulário de criação. Botão de salvar e cancelar.

---

#### DELETE `/api/v1/stores/{store_id}`

**Descrição**: Desativa uma loja (soft delete).

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Response 204 No Content**

**Telas a Implementar**:
- Ação de desativar pode ser um botão na tela de detalhes ou lista, com confirmação antes de executar.

---

## 1º Passo (B): Cadastro de Departamentos (departments) ✅ PRONTO

### Endpoints Disponíveis

#### GET `/api/v1/departments`

**Descrição**: Lista todos os setores ativos da organização.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Query Parameters**: Nenhum

**Response 200 OK**:
```typescript
[
  {
    "id": 1,
    "organization_id": 1,
    "name": "Vendas",
    "description": "Equipe de vendas e atendimento ao cliente",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

**Telas a Implementar**:
- **Lista de Setores** (`/setores`): Tela que exibe todos os setores da organização. Deve mostrar: nome, descrição e status. Deve ter botão para criar novo setor e ações para editar/excluir cada setor. Nota: Ao criar uma organização, o sistema já cria automaticamente 4 setores padrão (Vendas, Gerência, Financeiro, Laboratório), mas o admin pode criar novos.

---

#### POST `/api/v1/departments`

**Descrição**: Cria um novo setor.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body**:
```typescript
{
  "name": "Laboratório e Montagem",                    // Obrigatório
  "description": "Responsável pela conferência e montagem de óculos"  // Opcional
}
```

**Response 201 Created**:
```typescript
{
  "id": 1,
  "organization_id": 1,
  "name": "Laboratório e Montagem",
  "description": "Responsável pela conferência e montagem de óculos",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `400 Bad Request`: Já existe um setor com este nome
- `403 Forbidden`: Acesso negado (não é ADMIN)

**Telas a Implementar**:
- **Criar Setor** (`/setores/novo`): Formulário simples com campos: nome (obrigatório) e descrição (opcional, textarea). Botão de salvar e cancelar.

---

#### GET `/api/v1/departments/{department_id}`

**Descrição**: Obtém um setor específico.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Detalhes do Setor** (`/setores/{id}`): Tela de visualização com nome e descrição do setor. Deve ter botão para editar e opção de desativar.

---

#### PATCH `/api/v1/departments/{department_id}`

**Descrição**: Atualiza um setor.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body** (todos os campos opcionais):
```typescript
{
  "name": "Laboratório e Montagem Atualizado",
  "description": "Nova descrição",
  "is_active": false
}
```

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Editar Setor** (`/setores/{id}/editar`): Formulário pré-preenchido com os dados atuais do setor. Mesmos campos do formulário de criação. Botão de salvar e cancelar.

---

#### DELETE `/api/v1/departments/{department_id}`

**Descrição**: Desativa um setor (soft delete).

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Response 204 No Content**

**Telas a Implementar**:
- Ação de desativar pode ser um botão na tela de detalhes ou lista, com confirmação antes de executar.

---

## 2º Passo: Finalizar Equipe (staff_members) ✅ PRONTO

### Endpoints Disponíveis

#### GET `/api/v1/staff`

**Descrição**: Lista membros da equipe da organização atual.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Query Parameters**:
```typescript
{
  q?: string;           // Busca textual em nome/email
  role?: "ADMIN" | "MANAGER" | "STAFF" | "ASSISTANT" | "SELLER";  // Filtrar por role
}
```

**Response 200 OK**:
```typescript
[
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
]
```

**Telas a Implementar**:
- **Lista de Membros da Equipe** (`/equipe`): Tela que exibe todos os membros da equipe. Deve mostrar: nome, email, role, cargo (job_title), loja (nome - precisa buscar pelo store_id), setor (nome - precisa buscar pelo department_id) e status. Deve ter filtros de busca (nome/email) e por role. Deve ter botão para criar novo membro e ações para editar cada membro.

---

#### POST `/api/v1/staff`

**Descrição**: Cria um novo membro da equipe.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body**:
```typescript
{
  "full_name": "Maria Santos",        // Obrigatório
  "email": "maria@example.com",      // Obrigatório, único na organização
  "role": "SELLER",                   // Obrigatório: ADMIN, MANAGER, STAFF, ASSISTANT, SELLER
  "store_id": 10,                     // OBRIGATÓRIO: ID da loja
  "department_id": 2,                 // OBRIGATÓRIO: ID do setor
  "job_title": "Vendedor",            // Opcional: cargo específico
  "is_active": true                   // Opcional, padrão: true
}
```

**Response 201 Created**:
```typescript
{
  "id": 2,
  "clerk_id": null,
  "organization_id": "org_xxx",
  "store_id": 10,
  "department_id": 2,
  "full_name": "Maria Santos",
  "email": "maria@example.com",
  "role": "SELLER",
  "job_title": "Vendedor",
  "is_active": true,
  "avatar_url": null,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `400 Bad Request`: Email já cadastrado ou loja/setor não pertence à organização
- `403 Forbidden`: Acesso negado (não é ADMIN)

**Telas a Implementar**:
- **Criar Membro da Equipe** (`/equipe/novo`): Formulário com campos: nome completo (obrigatório), email (obrigatório), role (select obrigatório com opções: ADMIN, MANAGER, STAFF, ASSISTANT, SELLER), loja (select obrigatório - buscar lojas via `GET /api/v1/stores`), setor (select obrigatório - buscar setores via `GET /api/v1/departments`), cargo específico (job_title - opcional, texto livre), status ativo (checkbox, padrão true). Botão de salvar e cancelar.

---

#### GET `/api/v1/staff/stats`

**Descrição**: Retorna estatísticas agregadas da equipe.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: MANAGER ou ADMIN

**Response 200 OK**:
```typescript
{
  "total_users": 10,
  "active_users": 8,
  "admins": 2,
  "managers": 3
}
```

**Telas a Implementar**:
- Pode ser exibido como cards ou gráficos na tela de lista de equipe ou em um dashboard.

---

#### GET `/api/v1/staff/{staff_id}`

**Descrição**: Obtém um membro específico da equipe.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Response 200 OK**: Mesmo formato do POST acima.

**Erros**:
- `404 Not Found`: Membro não encontrado

**Telas a Implementar**:
- **Detalhes do Membro** (`/equipe/{id}`): Tela de visualização com todos os dados do membro: nome, email, role, cargo, loja (nome - precisa buscar pelo store_id), setor (nome - precisa buscar pelo department_id), status. Deve ter botão para editar.

---

#### PUT `/api/v1/staff/{staff_id}`

**Descrição**: Atualiza um membro da equipe (especialmente para vincular loja e setor).

**Autenticação**: ✅ Requerida (ADMIN apenas)

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

**Response 200 OK**: Mesmo formato do POST acima.

**Erros**:
- `400 Bad Request`: Loja ou setor não pertence à organização, ou email já cadastrado
- `403 Forbidden`: Acesso negado (não é ADMIN)
- `404 Not Found`: Membro não encontrado

**Telas a Implementar**:
- **Editar Membro da Equipe** (`/equipe/{id}/editar`): Formulário pré-preenchido com os dados atuais do membro (buscar via `GET /api/v1/staff/{id}`). Campos: nome completo (opcional), email (opcional), role (select opcional), loja (select opcional - buscar lojas via `GET /api/v1/stores`), setor (select opcional - buscar setores via `GET /api/v1/departments`), cargo específico (job_title - opcional), status ativo (checkbox opcional). Botão de salvar e cancelar. **Importante**: Esta é a tela principal para "finalizar" a equipe, vinculando cada membro à sua loja e setor.

---

## 3º Passo: Cadastro de Armações (products_frames) ✅ PRONTO

### Endpoints Disponíveis

#### GET `/api/v1/product-frames`

**Descrição**: Lista armações da organização.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Query Parameters**:
```typescript
{
  q?: string;           // Busca em nome/código/marca
  store_id?: number;    // Filtrar por loja (opcional) - se fornecido, retorna níveis de estoque
}
```

**Response 200 OK**:
```typescript
[
  {
    "id": 1,
    "organization_id": "org_xxx",
    "reference_code": "1234567890123",
    "name": "Armação Ray-Ban Aviator",
    "brand": "Ray-Ban",
    "model": "RB3025",
    "cost_price": "150.00",
    "sell_price": "299.90",
    "min_stock_alert": 5,
    "description": "Armação clássica",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "inventory_levels": [  // Apenas se store_id fornecido
      {
        "id": 1,
        "store_id": 1,
        "product_frame_id": 1,
        "quantity": 10,
        "reserved_quantity": 0,
        "store_name": "Loja Centro"
      }
    ]
  }
]
```

**Telas a Implementar**:
- **Lista de Armações** (`/produtos/armacoes`): Tela que exibe todas as armações da organização. Deve mostrar: código de referência (código de barras), nome, marca, modelo, preço de venda, estoque (se loja selecionada) e status. Deve ter filtro de busca (nome/código/marca) e filtro por loja (select - ao selecionar, mostra estoque daquela loja). Deve ter botão para criar nova armação e ações para editar/excluir cada armação. **Importante**: O código de referência é usado no leitor de código de barras do PDV.

---

#### POST `/api/v1/product-frames`

**Descrição**: Cria uma nova armação.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body**:
```typescript
{
  "reference_code": "1234567890123",  // Obrigatório, único na organização
  "name": "Armação Ray-Ban Aviator",   // Obrigatório
  "brand": "Ray-Ban",                  // Opcional
  "model": "RB3025",                   // Opcional
  "cost_price": 150.00,                // Opcional
  "sell_price": 299.90,                // Obrigatório
  "min_stock_alert": 5,                // Opcional, padrão: 0
  "description": "Armação clássica",   // Opcional
  "initial_stock": 10                  // Opcional: cria estoque na loja do usuário logado
}
```

**Response 201 Created**:
```typescript
{
  "id": 1,
  "organization_id": "org_xxx",
  "reference_code": "1234567890123",
  "name": "Armação Ray-Ban Aviator",
  "brand": "Ray-Ban",
  "model": "RB3025",
  "cost_price": "150.00",
  "sell_price": "299.90",
  "min_stock_alert": 5,
  "description": "Armação clássica",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `400 Bad Request`: Código de referência já existe nesta organização
- `403 Forbidden`: Acesso negado (não é ADMIN)

**Telas a Implementar**:
- **Criar Armação** (`/produtos/armacoes/novo`): Formulário com campos: código de referência (obrigatório, input numérico ou texto - usado no leitor de código de barras), nome (obrigatório), marca (opcional), modelo (opcional), preço de custo (opcional, numérico com 2 casas decimais), preço de venda (obrigatório, numérico com 2 casas decimais), quantidade mínima para alerta (opcional, numérico inteiro, padrão 0), descrição (opcional, textarea), estoque inicial (opcional, numérico inteiro - se preenchido, cria estoque na loja do usuário logado). Botão de salvar e cancelar.

---

#### GET `/api/v1/product-frames/{frame_id}`

**Descrição**: Obtém uma armação específica.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Detalhes da Armação** (`/produtos/armacoes/{id}`): Tela de visualização com todos os dados da armação. Deve mostrar também os níveis de estoque por loja (se houver). Deve ter botão para editar e opção de desativar.

---

#### PATCH `/api/v1/product-frames/{frame_id}`

**Descrição**: Atualiza uma armação.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body** (todos os campos opcionais):
```typescript
{
  "reference_code": "1234567890123",
  "name": "Armação Ray-Ban Aviator Atualizada",
  "brand": "Ray-Ban",
  "model": "RB3025",
  "cost_price": 160.00,
  "sell_price": 309.90,
  "min_stock_alert": 10,
  "description": "Nova descrição",
  "is_active": false
}
```

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Editar Armação** (`/produtos/armacoes/{id}/editar`): Formulário pré-preenchido com os dados atuais da armação. Mesmos campos do formulário de criação. Botão de salvar e cancelar.

---

#### DELETE `/api/v1/product-frames/{frame_id}`

**Descrição**: Desativa uma armação (soft delete).

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Response 204 No Content**

**Telas a Implementar**:
- Ação de desativar pode ser um botão na tela de detalhes ou lista, com confirmação antes de executar.

---

## 4º Passo: Cadastro de Lentes (products_lenses) ✅ PRONTO

### Endpoints Disponíveis

#### GET `/api/v1/product-lenses`

**Descrição**: Lista lentes da organização.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Query Parameters**:
```typescript
{
  is_lab_order?: boolean;  // Filtrar por tipo: true = Surfaçagem, false = Estoque
}
```

**Response 200 OK**:
```typescript
[
  {
    "id": 1,
    "organization_id": "org_xxx",
    "name": "Lente Transitions",
    "brand": "Essilor",
    "model": "Transitions Signature",
    "cost_price": "80.00",
    "sell_price": "250.00",
    "is_lab_order": false,  // false = Estoque, true = Surfaçagem
    "treatment": "Anti-reflexo",
    "description": "Lente fotossensível",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

**Telas a Implementar**:
- **Lista de Lentes** (`/produtos/lentes`): Tela que exibe todas as lentes da organização. Deve mostrar: nome, marca, modelo, tipo (Estoque ou Surfaçagem), tratamento (se aplicável), preço de venda e status. Deve ter filtro por tipo (Estoque/Surfaçagem/Todos). Deve ter botão para criar nova lente e ações para editar/excluir cada lente.

---

#### POST `/api/v1/product-lenses`

**Descrição**: Cria uma nova lente.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body - Lente de Estoque**:
```typescript
{
  "name": "Lente Transitions",           // Obrigatório
  "brand": "Essilor",                    // Opcional
  "model": "Transitions Signature",      // Opcional
  "cost_price": 80.00,                   // Opcional
  "sell_price": 250.00,                  // Obrigatório
  "is_lab_order": false,                // false = Estoque
  "treatment": "Anti-reflexo",          // Opcional
  "description": "Lente fotossensível",  // Opcional
  "initial_stock_grid": [                // Opcional: grade inicial de estoque
    {
      "spherical": -2.00,    // Esférico (obrigatório)
      "cylindrical": -1.00,  // Cilíndrico (obrigatório)
      "axis": 90,            // Eixo (opcional, 0-180)
      "quantity": 5           // Quantidade (padrão: 0)
    }
  ]
}
```

**Request Body - Lente de Surfaçagem (Laboratório)**:
```typescript
{
  "name": "Lente Multifocal Progressiva",  // Obrigatório
  "brand": "Varilux",                      // Opcional
  "model": "Comfort",                      // Opcional
  "cost_price": 100.00,                    // Opcional
  "sell_price": 400.00,                    // Obrigatório
  "is_lab_order": true,                     // true = Surfaçagem
  "description": "Lente progressiva",      // Opcional
  // NÃO incluir initial_stock_grid (não tem estoque físico)
}
```

**Response 201 Created**:
```typescript
{
  "id": 1,
  "organization_id": "org_xxx",
  "name": "Lente Transitions",
  "brand": "Essilor",
  "model": "Transitions Signature",
  "cost_price": "80.00",
  "sell_price": "250.00",
  "is_lab_order": false,
  "treatment": "Anti-reflexo",
  "description": "Lente fotossensível",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `403 Forbidden`: Acesso negado (não é ADMIN)

**Telas a Implementar**:
- **Criar Lente** (`/produtos/lentes/novo`): Formulário com campos: nome (obrigatório), marca (opcional), modelo (opcional), preço de custo (opcional), preço de venda (obrigatório), tipo de lente (radio ou select obrigatório: "Estoque" ou "Surfaçagem/Laboratório"). Se tipo = "Estoque": mostrar campo tratamento (opcional) e seção para grade inicial de estoque (tabela onde pode adicionar linhas com: esférico, cilíndrico, eixo, quantidade). Se tipo = "Surfaçagem": não mostrar grade de estoque. Campo descrição (opcional, textarea). Botão de salvar e cancelar. **Importante**: O sistema trata dois tipos de produto na mesma tela - lentes de estoque (com grade) e lentes de surfaçagem (sem estoque físico).

---

#### GET `/api/v1/product-lenses/{lens_id}`

**Descrição**: Obtém uma lente específica.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Detalhes da Lente** (`/produtos/lentes/{id}`): Tela de visualização com todos os dados da lente. Se for lente de estoque, deve mostrar também a grade de estoque por loja (se houver). Deve ter botão para editar e opção de desativar.

---

#### PATCH `/api/v1/product-lenses/{lens_id}`

**Descrição**: Atualiza uma lente.

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Request Body** (todos os campos opcionais):
```typescript
{
  "name": "Lente Transitions Atualizada",
  "brand": "Essilor",
  "model": "Transitions Signature",
  "cost_price": 85.00,
  "sell_price": 260.00,
  "is_lab_order": false,
  "treatment": "Anti-reflexo + Blue Light",
  "description": "Nova descrição",
  "is_active": false
}
```

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Editar Lente** (`/produtos/lentes/{id}/editar`): Formulário pré-preenchido com os dados atuais da lente. Mesmos campos do formulário de criação, adaptados conforme o tipo (Estoque ou Surfaçagem). Botão de salvar e cancelar.

---

#### DELETE `/api/v1/product-lenses/{lens_id}`

**Descrição**: Desativa uma lente (soft delete).

**Autenticação**: ✅ Requerida (ADMIN apenas)

**Response 204 No Content**

**Telas a Implementar**:
- Ação de desativar pode ser um botão na tela de detalhes ou lista, com confirmação antes de executar.

---

## 5º Passo: Cadastro de Clientes (customers) ✅ PRONTO

### Endpoints Disponíveis

#### GET `/api/v1/customers`

**Descrição**: Lista clientes da organização.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Query Parameters**:
```typescript
{
  q?: string;  // Busca em nome/CPF/email
}
```

**Response 200 OK**:
```typescript
[
  {
    "id": 1,
    "organization_id": "org_xxx",
    "full_name": "João Silva",
    "cpf": "12345678901",
    "birth_date": "1990-05-15",
    "email": "joao@example.com",
    "phone": "(48) 99999-9999",
    "profession": "Engenheiro",
    "address_street": "Rua Principal",
    "address_number": "123",
    "address_complement": "Apto 101",
    "address_neighborhood": "Centro",
    "address_city": "Florianópolis",
    "address_state": "SC",
    "address_zipcode": "88000-000",
    "notes": "Cliente preferencial",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

**Telas a Implementar**:
- **Lista de Clientes** (`/clientes`): Tela que exibe todos os clientes da organização. Deve mostrar: nome, CPF (formatado), telefone, email e status. Deve ter filtro de busca (nome/CPF/email). Deve ter botão para criar novo cliente e ações para editar/visualizar cada cliente. **Importante**: CPF é obrigatório para NFC-e.

---

#### POST `/api/v1/customers`

**Descrição**: Cria um novo cliente (formulário completo).

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Request Body**:
```typescript
{
  "full_name": "João Silva",              // Obrigatório
  "cpf": "12345678901",                   // Obrigatório (11 dígitos, sem formatação)
  "birth_date": "1990-05-15",            // Obrigatório (YYYY-MM-DD)
  "email": "joao@example.com",           // Opcional
  "phone": "(48) 99999-9999",            // Opcional
  "profession": "Engenheiro",             // Opcional
  "address_street": "Rua Principal",      // Opcional
  "address_number": "123",                // Opcional
  "address_complement": "Apto 101",       // Opcional
  "address_neighborhood": "Centro",       // Opcional
  "address_city": "Florianópolis",        // Opcional
  "address_state": "SC",                  // Opcional (2 caracteres)
  "address_zipcode": "88000-000",         // Opcional
  "notes": "Cliente preferencial"         // Opcional
}
```

**Response 201 Created**:
```typescript
{
  "id": 1,
  "organization_id": "org_xxx",
  "full_name": "João Silva",
  "cpf": "12345678901",
  "birth_date": "1990-05-15",
  "email": "joao@example.com",
  "phone": "(48) 99999-9999",
  "profession": "Engenheiro",
  "address_street": "Rua Principal",
  "address_number": "123",
  "address_complement": "Apto 101",
  "address_neighborhood": "Centro",
  "address_city": "Florianópolis",
  "address_state": "SC",
  "address_zipcode": "88000-000",
  "notes": "Cliente preferencial",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `400 Bad Request`: CPF já cadastrado nesta organização
- `422 Unprocessable Entity`: Validação de campos (CPF deve ter 11 dígitos)

**Telas a Implementar**:
- **Criar Cliente** (`/clientes/novo`): Formulário completo com seções: Dados Pessoais (nome completo obrigatório, CPF obrigatório com máscara e validação de 11 dígitos, data de nascimento obrigatória com date picker, email opcional, telefone opcional com máscara), Dados Profissionais (profissão opcional - ajuda na venda consultiva), Endereço (todos os campos opcionais: rua, número, complemento, bairro, cidade, estado - select com UF, CEP com máscara), Observações (textarea opcional). Botão de salvar e cancelar. **Importante**: Data de nascimento é obrigatória pois é usada para cálculo de "Adição" em lentes multifocais.

---

#### POST `/api/v1/customers/quick`

**Descrição**: Cria cliente rapidamente (otimizado para Modal na tela de vendas).

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Request Body**:
```typescript
{
  "full_name": "João Silva",    // Obrigatório
  "cpf": "12345678901",          // Obrigatório (11 dígitos, sem formatação)
  "birth_date": "1990-05-15",   // Obrigatório (YYYY-MM-DD)
  "phone": "(48) 99999-9999"    // Opcional
}
```

**Response 201 Created**:
```typescript
{
  "id": 1,
  "organization_id": "org_xxx",
  "full_name": "João Silva",
  "cpf": "12345678901",
  "birth_date": "1990-05-15",
  "phone": "(48) 99999-9999",
  "email": null,
  "profession": null,
  "address_street": null,
  "address_number": null,
  "address_complement": null,
  "address_neighborhood": null,
  "address_city": null,
  "address_state": null,
  "address_zipcode": null,
  "notes": null,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Erros**:
- `400 Bad Request`: CPF já cadastrado
- `422 Unprocessable Entity`: Validação de campos

**Telas a Implementar**:
- **Modal Criar Cliente Rápido**: Modal/popup que aparece dentro da tela de vendas (`/vendas`). Formulário simplificado com apenas: nome completo (obrigatório), CPF (obrigatório, com máscara e validação), data de nascimento (obrigatória, date picker), telefone (opcional, com máscara). Botão de criar e cancelar. Após criar, fecha o modal e retorna o ID do cliente criado para ser usado na venda. **Importante**: Este endpoint é otimizado para ser chamado via Modal durante o processo de venda, permitindo criar cliente rapidamente sem sair da tela de vendas.

---

#### GET `/api/v1/customers/{customer_id}`

**Descrição**: Obtém um cliente específico.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Detalhes do Cliente** (`/clientes/{id}`): Tela de visualização com todos os dados do cliente organizados em seções: Dados Pessoais, Dados Profissionais, Endereço, Observações. Deve ter botão para editar.

---

#### PATCH `/api/v1/customers/{customer_id}`

**Descrição**: Atualiza um cliente.

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Request Body** (todos os campos opcionais):
```typescript
{
  "full_name": "João Silva Atualizado",
  "cpf": "12345678901",
  "birth_date": "1990-05-15",
  "email": "joao.novo@example.com",
  "phone": "(48) 88888-8888",
  "profession": "Arquiteto",
  // ... outros campos opcionais
  "is_active": false
}
```

**Response 200 OK**: Mesmo formato do POST acima.

**Telas a Implementar**:
- **Editar Cliente** (`/clientes/{id}/editar`): Formulário pré-preenchido com os dados atuais do cliente. Mesmos campos do formulário de criação. Botão de salvar e cancelar.

---

#### DELETE `/api/v1/customers/{customer_id}`

**Descrição**: Desativa um cliente (soft delete).

**Autenticação**: ✅ Requerida (Bearer Token)

**Permissões**: STAFF, MANAGER ou ADMIN

**Response 204 No Content**

**Telas a Implementar**:
- Ação de desativar pode ser um botão na tela de detalhes ou lista, com confirmação antes de executar.

---

## 🔐 Autenticação

Todos os endpoints requerem:

```
Authorization: Bearer <token_jwt_do_clerk>
```

O token deve ser incluído no header de todas as requisições.

---

## ⚠️ Validações Importantes

### CPF
- Deve ter exatamente 11 dígitos
- Sem formatação (apenas números)
- Único por organização
- Obrigatório para NFC-e

### Data de Nascimento
- Formato: `YYYY-MM-DD`
- Obrigatório (usado para cálculo de adição em lentes multifocais)

### Código de Referência (Armações)
- Único por organização
- Usado para leitor de código de barras no PDV

### Store ID e Department ID (Staff)
- Obrigatórios ao criar staff
- Devem pertencer à organização do usuário
- Validados automaticamente pelo backend

---

## 📝 Notas para o Frontend

1. **Multi-tenancy**: Todos os dados são automaticamente filtrados por `organization_id` extraído do token JWT. Não é necessário enviar `organization_id` no body das requisições.

2. **Validações**: O backend valida automaticamente:
   - Se store e department pertencem à organização (ao criar staff)
   - Se CPF é único na organização (ao criar cliente)
   - Se código de referência é único na organização (ao criar armação)

3. **Soft Delete**: Todos os endpoints de DELETE fazem soft delete (marcam `is_active = false`), não deletam fisicamente.

4. **Relacionamentos**: Para exibir nomes de lojas e setores na lista de staff, você precisará fazer chamadas adicionais:
   - `GET /api/v1/stores` para obter nomes das lojas
   - `GET /api/v1/departments` para obter nomes dos setores
   - Ou fazer join no frontend usando os IDs retornados

---

**Documento criado em**: 2025-12-03  
**Status**: ✅ Pronto para Implementação  
**Última atualização**: Sprint 1

