# Endpoints Backend - Fase 2 (Ciclo de Venda) - Guia Frontend

## 📋 Visão Geral

Este documento detalha **todas as rotas da API** da Fase 2, incluindo request bodies, response bodies, códigos de status e regras de negócio que o frontend precisa conhecer.

**Base URL**: `http://localhost:8000/api/v1` (ou conforme configuração)

**Autenticação**: Todas as rotas requerem header:
```
Authorization: Bearer <token_clerk>
```

---

## 🔐 Permissões por Role

| Role | Permissões |
|------|------------|
| **SELLER** | Criar/editar suas próprias OS, abrir/fechar seu caixa, processar vendas |
| **STAFF** | Mesmas permissões do SELLER |
| **MANAGER** | Todas as permissões + aprovar descontos, auditar caixas, ver dashboard |
| **ADMIN** | Acesso total |

---

## 1️⃣ Módulo: Apoio de Caixa (Cash Sessions)

### 1.1. Obter Sessão Atual do Vendedor

**GET** `/cash-sessions/my-session`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Descrição**: Retorna a sessão de caixa ativa do vendedor logado. Se não houver sessão aberta, retorna `null`.

**Response 200 OK** (Sessão encontrada):
```json
{
  "id": 1,
  "organization_id": "org_xxx",
  "store_id": 5,
  "staff_id": 10,
  "status": "OPEN",
  "opened_at": "2024-12-04T08:00:00Z",
  "closed_at": null,
  "opening_balance": 100.00,
  "closing_balance": null,
  "calculated_balance": null,
  "discrepancy": null,
  "audit_resolved_by": null,
  "audit_resolved_at": null,
  "audit_action": null,
  "audit_notes": null,
  "is_active": true,
  "created_at": "2024-12-04T08:00:00Z",
  "updated_at": "2024-12-04T08:00:00Z"
}
```

**Response 200 OK** (Sem sessão aberta):
```json
null
```

**Status Possíveis**:
- `OPEN`: Caixa aberto
- `CLOSED`: Caixa fechado normalmente
- `PENDING_AUDIT`: Fechado com divergência (aguardando auditoria)

---

### 1.2. Abrir Nova Sessão de Caixa

**POST** `/cash-sessions`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Descrição**: Abre uma nova sessão de caixa para o vendedor logado.

**Request Body**:
```json
{
  "store_id": 5,
  "opening_balance": 100.00
}
```

**Campos**:
- `store_id` (integer, obrigatório): ID da loja
- `opening_balance` (decimal, obrigatório, >= 0): Fundo de troco inicial

**Response 201 Created**:
```json
{
  "id": 1,
  "organization_id": "org_xxx",
  "store_id": 5,
  "staff_id": 10,
  "status": "OPEN",
  "opened_at": "2024-12-04T08:00:00Z",
  "closed_at": null,
  "opening_balance": 100.00,
  "closing_balance": null,
  "calculated_balance": null,
  "discrepancy": null,
  "audit_resolved_by": null,
  "audit_resolved_at": null,
  "audit_action": null,
  "audit_notes": null,
  "is_active": true,
  "created_at": "2024-12-04T08:00:00Z",
  "updated_at": "2024-12-04T08:00:00Z"
}
```

**Erros**:
- `400 Bad Request`: Já existe sessão aberta para este vendedor
- `404 Not Found`: Loja não encontrada ou não pertence à organização

---

### 1.3. Fechar Sessão de Caixa

**POST** `/cash-sessions/{session_id}/close`

**Permissão**: SELLER (apenas sua sessão), MANAGER, ADMIN

**Descrição**: Fecha a sessão de caixa informando o valor final.

**Request Body**:
```json
{
  "closing_balance": 450.50
}
```

**Campos**:
- `closing_balance` (decimal, obrigatório, >= 0): Valor informado pelo vendedor ao fechar

**Response 200 OK**:
```json
{
  "id": 1,
  "organization_id": "org_xxx",
  "store_id": 5,
  "staff_id": 10,
  "status": "CLOSED",  // ou "PENDING_AUDIT" se houver divergência
  "opened_at": "2024-12-04T08:00:00Z",
  "closed_at": "2024-12-04T18:00:00Z",
  "opening_balance": 100.00,
  "closing_balance": 450.50,
  "calculated_balance": 450.00,  // Calculado pelo sistema
  "discrepancy": -0.50,  // calculated - closing (negativo = falta dinheiro)
  "audit_resolved_by": null,
  "audit_resolved_at": null,
  "audit_action": null,
  "audit_notes": null,
  "is_active": true,
  "created_at": "2024-12-04T08:00:00Z",
  "updated_at": "2024-12-04T18:00:00Z"
}
```

**Regras de Negócio**:
- Se `discrepancy != 0`: Status muda para `PENDING_AUDIT`
- Se `discrepancy == 0`: Status muda para `CLOSED`
- `calculated_balance` = `opening_balance` + entradas - saídas (cash movements)

**Erros**:
- `400 Bad Request`: Sessão já está fechada
- `403 Forbidden`: SELLER tentando fechar sessão de outro vendedor
- `404 Not Found`: Sessão não encontrada

---

### 1.4. Dashboard de Estatísticas (Gerencial)

**GET** `/cash-sessions/dashboard-stats`

**Permissão**: MANAGER, ADMIN

**Descrição**: Retorna KPIs para o dashboard gerencial.

**Response 200 OK**:
```json
{
  "active_sessions_count": 3,
  "pending_audit_count": 2,
  "total_discrepancy": -15.50,
  "card_fees_estimated": 1250.00
}
```

**Campos**:
- `active_sessions_count` (integer): Número de caixas abertos
- `pending_audit_count` (integer): Número de caixas com divergência pendente
- `total_discrepancy` (decimal): Soma de todas as divergências pendentes
- `card_fees_estimated` (decimal): Taxas de cartão estimadas do mês

---

### 1.5. Listar Todas as Sessões

**GET** `/cash-sessions`

**Permissão**: MANAGER, ADMIN

**Query Parameters**:
- `status` (string, opcional): Filter por status (`OPEN`, `CLOSED`, `PENDING_AUDIT`)
- `store_id` (integer, opcional): Filter por loja
- `staff_id` (integer, opcional): Filter por vendedor

**Response 200 OK**:
```json
[
  {
    "id": 1,
    "organization_id": "org_xxx",
    "store_id": 5,
    "staff_id": 10,
    "status": "OPEN",
    "opened_at": "2024-12-04T08:00:00Z",
    "closed_at": null,
    "opening_balance": 100.00,
    "closing_balance": null,
    "calculated_balance": null,
    "discrepancy": null,
    "audit_resolved_by": null,
    "audit_resolved_at": null,
    "audit_action": null,
    "audit_notes": null,
    "is_active": true,
    "created_at": "2024-12-04T08:00:00Z",
    "updated_at": "2024-12-04T08:00:00Z"
  }
]
```

---

### 1.6. Resolver Divergência de Caixa

**POST** `/cash-sessions/{session_id}/audit`

**Permissão**: MANAGER, ADMIN

**Descrição**: Resolve divergência de caixa com uma das ações disponíveis.

**Request Body**:
```json
{
  "action": "ACCEPT_LOSS",  // ou "CHARGE_STAFF" ou "CORRECT_VALUE"
  "corrected_value": null,  // Obrigatório se action = "CORRECT_VALUE"
  "notes": "Vendedor esqueceu de lançar sangria"
}
```

**Ações Disponíveis**:
- `ACCEPT_LOSS`: A loja assume o prejuízo (cria despesa automática)
- `CHARGE_STAFF`: Gera conta a receber contra o vendedor
- `CORRECT_VALUE`: Ajusta o valor calculado (ex: vendedor esqueceu de lançar sangria)

**Response 200 OK**:
```json
{
  "id": 1,
  "status": "CLOSED",
  "audit_resolved_by": 5,  // ID do manager que resolveu
  "audit_resolved_at": "2024-12-04T19:00:00Z",
  "audit_action": "CORRECT_VALUE",
  "audit_notes": "Vendedor esqueceu de lançar sangria",
  "calculated_balance": 450.50,  // Atualizado se action = CORRECT_VALUE
  // ... outros campos
}
```

**Erros**:
- `400 Bad Request`: Sessão não está em `PENDING_AUDIT`
- `400 Bad Request`: `corrected_value` obrigatório se `action = CORRECT_VALUE`

---

## 2️⃣ Módulo: Sangria/Suprimento (Cash Movements)

### 2.1. Registrar Sangria ou Suprimento

**POST** `/cash-movements`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Descrição**: Registra uma sangria (retirada) ou suprimento (entrada) de dinheiro.

**Request Body**:
```json
{
  "movement_type": "WITHDRAWAL",  // ou "DEPOSIT"
  "amount": 50.00,
  "description": "Pagar lanche"
}
```

**Campos**:
- `movement_type` (string, obrigatório): `WITHDRAWAL` (sangria) ou `DEPOSIT` (suprimento)
- `amount` (decimal, obrigatório, > 0): Valor da movimentação
- `description` (string, opcional): Motivo da movimentação

**Response 201 Created**:
```json
{
  "id": 1,
  "organization_id": "org_xxx",
  "cash_session_id": 5,
  "staff_id": 10,
  "movement_type": "WITHDRAWAL",
  "amount": 50.00,
  "description": "Pagar lanche",
  "movement_date": "2024-12-04T14:30:00Z",
  "is_active": true,
  "created_at": "2024-12-04T14:30:00Z",
  "updated_at": "2024-12-04T14:30:00Z"
}
```

**Erros**:
- `400 Bad Request`: Não há sessão de caixa aberta para o vendedor
- `400 Bad Request`: Sessão de caixa não está `OPEN`

---

### 2.2. Listar Movimentações

**GET** `/cash-movements`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Query Parameters**:
- `cash_session_id` (integer, opcional): ID da sessão (se não informado, usa sessão atual)

**Response 200 OK**:
```json
[
  {
    "id": 1,
    "organization_id": "org_xxx",
    "cash_session_id": 5,
    "staff_id": 10,
    "movement_type": "WITHDRAWAL",
    "amount": 50.00,
    "description": "Pagar lanche",
    "movement_date": "2024-12-04T14:30:00Z",
    "is_active": true,
    "created_at": "2024-12-04T14:30:00Z",
    "updated_at": "2024-12-04T14:30:00Z"
  },
  {
    "id": 2,
    "cash_session_id": 5,
    "movement_type": "DEPOSIT",
    "amount": 200.00,
    "description": "Buscar troco no banco",
    "movement_date": "2024-12-04T15:00:00Z",
    // ...
  }
]
```

---

## 3️⃣ Módulo: Hub de Vendas (Service Orders)

### 3.1. Criar Ordem de Serviço

**POST** `/service-orders`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Descrição**: Cria uma nova Ordem de Serviço (OS).

**Request Body**:
```json
{
  "customer_id": 10,
  "store_id": 5,
  "items": [
    {
      "item_type": "FRAME",
      "product_frame_id": 20,
      "quantity": 1,
      "unit_price": 150.00,
      "discount_amount": 0
    },
    {
      "item_type": "LENS",
      "product_lens_id": 15,
      "quantity": 1,
      "unit_price": 200.00,
      "discount_amount": 10.00,
      "lens_spherical": -2.50,
      "lens_cylindrical": -0.75,
      "lens_axis": 90,
      "lens_addition": 0,
      "lens_side": "AMBOS"
    }
  ],
  "discount_percentage": 5,
  "notes": "Cliente prefere lente antirreflexo"
}
```

**Campos**:
- `customer_id` (integer, obrigatório): ID do cliente
- `store_id` (integer, obrigatório): ID da loja
- `items` (array, obrigatório, min 1): Lista de itens da OS
  - `item_type` (string): `FRAME`, `LENS` ou `SERVICE`
  - `product_frame_id` (integer, opcional): ID da armação (se `item_type = FRAME`)
  - `product_lens_id` (integer, opcional): ID da lente (se `item_type = LENS`)
  - `quantity` (integer, obrigatório, > 0): Quantidade
  - `unit_price` (decimal, obrigatório, > 0): Preço unitário
  - `discount_amount` (decimal, obrigatório, >= 0): Desconto em valor
  - `lens_spherical`, `lens_cylindrical`, `lens_axis`, `lens_addition` (opcionais): Dados da lente
  - `lens_side` (string, opcional): `OD`, `OE` ou `AMBOS`
- `discount_percentage` (decimal, opcional, 0-100): Desconto percentual geral
- `notes` (string, opcional): Observações

**Response 201 Created**:
```json
{
  "id": 1,
  "organization_id": "org_xxx",
  "customer_id": 10,
  "store_id": 5,
  "seller_id": 8,
  "status": "DRAFT",
  "order_number": "OS-2024-001",
  "subtotal": 350.00,
  "discount_amount": 17.50,
  "discount_percentage": 5,
  "total": 332.50,
  "max_discount_allowed": 10.0,
  "discount_approved_by": null,
  "paid_at": null,
  "delivered_at": null,
  "created_at": "2024-12-04T10:00:00Z",
  "updated_at": "2024-12-04T10:00:00Z",
  "is_active": true,
  "items": [
    {
      "id": 1,
      "service_order_id": 1,
      "item_type": "FRAME",
      "product_frame_id": 20,
      "quantity": 1,
      "unit_price": 150.00,
      "discount_amount": 0,
      "total_price": 150.00,
      "reserved_quantity": 1,
      "needs_purchasing": false,
      "is_active": true
    },
    {
      "id": 2,
      "service_order_id": 1,
      "item_type": "LENS",
      "product_lens_id": 15,
      "quantity": 1,
      "unit_price": 200.00,
      "discount_amount": 10.00,
      "total_price": 190.00,
      "reserved_quantity": 0,
      "needs_purchasing": false,
      "is_active": true
    }
  ]
}
```

**Regras de Negócio**:
- `order_number` é gerado automaticamente (ex: `OS-2024-001`)
- Se `discount_percentage > max_discount_allowed` (padrão 10%): Requer aprovação de MANAGER/ADMIN
- Armações: Reserva estoque automaticamente (`reserved_quantity++`)
- Lentes: Valida estoque na `lens_stock_grid` ou marca `needs_purchasing = true`

**Erros**:
- `400 Bad Request`: Cliente ou loja não encontrados
- `400 Bad Request`: Estoque insuficiente
- `400 Bad Request`: Desconto acima do limite (requer aprovação)

---

### 3.2. Listar Ordens de Serviço

**GET** `/service-orders`

**Permissão**: SELLER (apenas suas), STAFF, MANAGER, ADMIN

**Query Parameters**:
- `status` (string, opcional): Filter por status
- `customer_id` (integer, opcional): Filter por cliente
- `store_id` (integer, opcional): Filter por loja
- `seller_id` (integer, opcional): Filter por vendedor

**Response 200 OK**:
```json
[
  {
    "id": 1,
    "order_number": "OS-2024-001",
    "customer_id": 10,
    "store_id": 5,
    "seller_id": 8,
    "status": "DRAFT",
    "total": 332.50,
    "created_at": "2024-12-04T10:00:00Z",
    "items": [
      // ... itens
    ]
  }
]
```

**Regras de Negócio**:
- SELLER: Vê apenas suas próprias OS (`seller_id = current_staff.id`)
- MANAGER/ADMIN: Vê todas as OS

---

### 3.3. Obter OS Específica

**GET** `/service-orders/{order_id}`

**Permissão**: SELLER (apenas suas), STAFF, MANAGER, ADMIN

**Response 200 OK**: Mesmo formato do POST (ServiceOrderResponse)

**Erros**:
- `403 Forbidden`: SELLER tentando acessar OS de outro vendedor
- `404 Not Found`: OS não encontrada

---

### 3.4. Editar Ordem de Serviço

**PATCH** `/service-orders/{order_id}`

**Permissão**: SELLER (apenas suas), STAFF, MANAGER, ADMIN

**Descrição**: Edita OS (apenas se `status = DRAFT`).

**Request Body**:
```json
{
  "items": [
    {
      "item_type": "FRAME",
      "product_frame_id": 25,
      "quantity": 1,
      "unit_price": 180.00,
      "discount_amount": 0
    }
  ],
  "discount_percentage": 8,
  "notes": "Atualizado: cliente mudou de armação"
}
```

**Campos**: Todos opcionais (partial update)

**Response 200 OK**: Mesmo formato do POST

**Erros**:
- `400 Bad Request`: OS não está em `DRAFT`
- `400 Bad Request`: Estoque insuficiente
- `403 Forbidden`: SELLER tentando editar OS de outro vendedor

---

### 3.5. Aprovar Desconto Acima do Limite

**POST** `/service-orders/{order_id}/approve-discount`

**Permissão**: MANAGER, ADMIN

**Descrição**: Aprova desconto acima do limite permitido.

**Request Body**: Vazio (não requer body)

**Response 200 OK**: Mesmo formato do GET, com `discount_approved_by` preenchido

**Erros**:
- `400 Bad Request`: Desconto não requer aprovação
- `404 Not Found`: OS não encontrada

---

### 3.6. Enviar OS para Pagamento

**POST** `/service-orders/{order_id}/send-to-payment`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Descrição**: Envia OS para etapa de pagamento.

**Request Body**: Vazio

**Response 200 OK**: Mesmo formato do GET, com `status = PENDING`

**Erros**:
- `400 Bad Request`: OS não está em `DRAFT`
- `400 Bad Request`: Estoque insuficiente

---

### 3.7. Atualizar Status (Laboratório)

**PATCH** `/service-orders/{order_id}/status`

**Permissão**: MANAGER, ADMIN (futuro: LAB_TECH)

**Descrição**: Atualiza status da OS (para movimentação no Kanban).

**Request Body**:
```json
{
  "status": "IN_PRODUCTION"  // ou "READY", "DELIVERED", etc.
}
```

**Status Possíveis**:
- `DRAFT`: Rascunho
- `PENDING`: Aguardando pagamento
- `PAID`: Paga, aguardando montagem
- `AWAITING_LENS`: Aguardando lente (surfaçagem)
- `IN_PRODUCTION`: Em produção
- `READY`: Pronto / Controle qualidade
- `DELIVERED`: Entregue
- `CANCELLED`: Cancelada

**Response 200 OK**: Mesmo formato do GET, com `status` atualizado

**Erros**:
- `400 Bad Request`: Transição de status não permitida

---

### 3.8. Cancelar OS

**POST** `/service-orders/{order_id}/cancel`

**Permissão**: MANAGER, ADMIN

**Descrição**: Cancela OS (estorno).

**Request Body**: Vazio

**Response 200 OK**: Mesmo formato do GET, com `status = CANCELLED`

**Regras de Negócio**:
- Libera todas as reservas de estoque
- Reverte lançamentos financeiros (se já pago)

---

## 4️⃣ Módulo: Busca Unificada de Produtos

### 4.1. Buscar Armações e Lentes

**GET** `/products/search`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Query Parameters**:
- `q` (string, opcional): Termo de busca (código, nome, marca)
- `type` (string, opcional): `FRAME`, `LENS` ou `ALL` (default)
- `store_id` (integer, opcional): ID da loja (para verificar estoque)

**Response 200 OK**:
```json
{
  "frames": [
    {
      "id": 20,
      "reference_code": "ABC123",
      "name": "Armação X",
      "brand": "Marca Y",
      "model": "Modelo Z",
      "sell_price": 150.00,
      "stock": {
        "quantity": 5,
        "reserved_quantity": 2,
        "available": 3
      }
    }
  ],
  "lenses": [
    {
      "id": 15,
      "name": "Lente Antirreflexo",
      "sell_price": 200.00,
      "is_lab_order": false
    }
  ]
}
```

**Nota**: Se `store_id` não for fornecido, `stock` será `null`.

---

## 5️⃣ Módulo: Checkout / Pagamento

### 5.1. Processar Pagamento

**POST** `/sales/{order_id}/checkout`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Descrição**: Processa pagamento e finaliza a venda.

**Request Body**:
```json
{
  "payment_method": "CASH",  // ou "CARD", "PIX", "CREDIT"
  "cash_session_id": 5  // Obrigatório se payment_method = "CASH"
}
```

**Campos**:
- `payment_method` (string, obrigatório): Método de pagamento
- `cash_session_id` (integer, opcional): ID da sessão de caixa (obrigatório se `CASH`)

**Response 201 Created**:
```json
{
  "id": 1,
  "organization_id": "org_xxx",
  "service_order_id": 10,
  "customer_id": 15,
  "store_id": 5,
  "seller_id": 8,
  "cash_session_id": 5,  // Preenchido se payment_method = CASH
  "total_amount": 332.50,
  "payment_method": "CASH",
  "card_fee_rate": null,  // Preenchido se payment_method = CARD
  "card_gross_amount": null,
  "card_net_amount": null,
  "receivable_account_id": null,  // Preenchido se payment_method = PIX ou CREDIT
  "commissionable_amount": 332.50,
  "sold_at": "2024-12-04T11:00:00Z",
  "is_active": true,
  "created_at": "2024-12-04T11:00:00Z",
  "updated_at": "2024-12-04T11:00:00Z"
}
```

**Regras de Negócio**:

1. **Dinheiro (CASH)**:
   - Requer `cash_session_id` e sessão deve estar `OPEN`
   - Cria lançamento de entrada no caixa

2. **Cartão (CARD)**:
   - Calcula taxa usando `store.tax_rate_machine`
   - `card_gross_amount` = `total_amount`
   - `card_net_amount` = `total_amount * (1 - tax_rate_machine/100)`

3. **Pix/Crediário (PIX/CREDIT)**:
   - Cria `ReceivableAccount` (conta a receber)
   - `receivable_account_id` é preenchido

4. **Baixa de Estoque**:
   - Converte `reserved_quantity` em baixa real
   - `inventory_levels.quantity -= reserved_quantity`
   - `inventory_levels.reserved_quantity = 0`

5. **Atualização de OS**:
   - `service_order.status = PAID`
   - `service_order.paid_at = now()`

**Erros**:
- `400 Bad Request`: OS não está em `PENDING`
- `400 Bad Request`: `cash_session_id` obrigatório se `payment_method = CASH`
- `400 Bad Request`: Sessão de caixa não está `OPEN`
- `400 Bad Request`: Estoque insuficiente

---

## 6️⃣ Módulo: Fila de Laboratório

### 6.1. Obter Fila Kanban

**GET** `/lab/queue`

**Permissão**: SELLER (read), STAFF, MANAGER, ADMIN

**Query Parameters**:
- `store_id` (integer, opcional): Filter por loja

**Response 200 OK**:
```json
{
  "awaiting_mount": [
    {
      "id": 10,
      "order_number": "OS-2024-001",
      "customer_id": 15,
      "status": "PAID",
      "total": 332.50,
      "created_at": "2024-12-04T10:00:00Z",
      "paid_at": "2024-12-04T11:00:00Z",
      "items": [
        // ... itens
      ]
    }
  ],
  "awaiting_lens": [
    {
      "id": 11,
      "order_number": "OS-2024-002",
      "status": "AWAITING_LENS",
      // ...
    }
  ],
  "in_production": [
    {
      "id": 12,
      "order_number": "OS-2024-003",
      "status": "IN_PRODUCTION",
      // ...
    }
  ],
  "ready": [
    {
      "id": 13,
      "order_number": "OS-2024-004",
      "status": "READY",
      // ...
    }
  ]
}
```

**Nota**: SELLER pode apenas visualizar. MANAGER/ADMIN podem mover cards.

---

## 7️⃣ Módulo: Contas a Receber

### 7.1. Listar Contas a Receber

**GET** `/receivable-accounts`

**Permissão**: MANAGER, ADMIN

**Query Parameters**:
- `status` (string, opcional): Filter por status
- `customer_id` (integer, opcional): Filter por cliente
- `due_date_from`, `due_date_to` (date, opcional): Range de vencimento

**Response 200 OK**:
```json
[
  {
    "id": 1,
    "organization_id": "org_xxx",
    "customer_id": 15,
    "sale_id": 5,
    "total_amount": 332.50,
    "paid_amount": 0,
    "remaining_amount": 332.50,
    "status": "PENDING",
    "due_date": "2024-12-15",
    "paid_at": null,
    "notes": null,
    "is_active": true,
    "created_at": "2024-12-04T11:00:00Z",
    "updated_at": "2024-12-04T11:00:00Z"
  }
]
```

**Status Possíveis**:
- `PENDING`: Pendente
- `PARTIAL`: Parcialmente pago
- `PAID`: Pago
- `OVERDUE`: Vencido
- `CANCELLED`: Cancelado

---

## 8️⃣ Módulo: Kardex (Histórico)

### 8.1. Listar Movimentações

**GET** `/kardex`

**Permissão**: SELLER, STAFF, MANAGER, ADMIN

**Query Parameters**:
- `store_id` (integer, opcional): Filter por loja
- `product_frame_id` (integer, opcional): Filter por armação
- `product_lens_id` (integer, opcional): Filter por lente
- `movement_type` (string, opcional): `ENTRY`, `EXIT`, `RESERVATION`, `RELEASE`
- `start_date`, `end_date` (datetime, opcional): Range de datas

**Response 200 OK**:
```json
[
  {
    "id": 1,
    "organization_id": "org_xxx",
    "store_id": 5,
    "product_frame_id": 20,
    "product_lens_id": null,
    "sale_id": 1,
    "service_order_id": 10,
    "movement_type": "EXIT",
    "quantity": -1,
    "balance_before": 5,
    "balance_after": 4,
    "moved_by": 8,
    "movement_date": "2024-12-04T11:00:00Z",
    "notes": "Venda OS-2024-001",
    "created_at": "2024-12-04T11:00:00Z"
  }
]
```

---

## 🔄 Fluxos de Trabalho

### Fluxo 1: Venda Completa (Dinheiro)

1. **Abrir Caixa**: `POST /cash-sessions`
2. **Criar OS**: `POST /service-orders` (status: `DRAFT`)
3. **Editar OS** (se necessário): `PATCH /service-orders/{id}`
4. **Enviar para Pagamento**: `POST /service-orders/{id}/send-to-payment` (status: `PENDING`)
5. **Processar Pagamento**: `POST /sales/{id}/checkout` com `payment_method: "CASH"` (status: `PAID`)
6. **Fechar Caixa**: `POST /cash-sessions/{id}/close`

### Fluxo 2: Venda com Cartão

1. **Criar OS**: `POST /service-orders`
2. **Enviar para Pagamento**: `POST /service-orders/{id}/send-to-payment`
3. **Processar Pagamento**: `POST /sales/{id}/checkout` com `payment_method: "CARD"`
4. Sistema calcula automaticamente taxa de cartão

### Fluxo 3: Venda com Crediário

1. **Criar OS**: `POST /service-orders`
2. **Enviar para Pagamento**: `POST /service-orders/{id}/send-to-payment`
3. **Processar Pagamento**: `POST /sales/{id}/checkout` com `payment_method: "CREDIT"`
4. Sistema cria `ReceivableAccount` automaticamente

### Fluxo 4: Laboratório (Kanban)

1. **Visualizar Fila**: `GET /lab/queue`
2. **Mover Card**: `PATCH /service-orders/{id}/status` com novo status
3. **Status atualizado**: OS aparece na nova coluna do Kanban

### Fluxo 5: Auditoria de Caixa

1. **Fechar Caixa**: `POST /cash-sessions/{id}/close` (pode resultar em `PENDING_AUDIT`)
2. **Visualizar Pendências**: `GET /cash-sessions/dashboard-stats` (ver `pending_audit_count`)
3. **Resolver Divergência**: `POST /cash-sessions/{id}/audit` com ação escolhida

---

## ⚠️ Regras de Negócio Importantes

### Reserva de Estoque

- **Quando**: Ao adicionar armação na OS (`status = DRAFT` ou `PENDING`)
- **Ação**: `reserved_quantity++` em `inventory_levels`
- **Liberação**: 
  - Ao remover item da OS
  - Ao cancelar OS
  - Ao fechar venda (converte em baixa real)
  - **Automático**: Reservas de OS inativas há 24h são liberadas (cron job backend)

### Validação de Lentes

- **Lente de Estoque**: Backend verifica `lens_stock_grid` (spherical, cylindrical, axis, addition)
- **Sem Estoque**: Bloqueia venda ou alerta "Saldo Insuficiente"
- **Lente Surfaçagem**: Permite venda, marca `needs_purchasing = true` (para setor de Compras)

### Controle de Desconto

- **Limite Padrão**: 10% (`max_discount_allowed`)
- **Desconto > Limite**: Requer aprovação de MANAGER/ADMIN via `POST /service-orders/{id}/approve-discount`
- **Frontend**: Mostrar alerta quando desconto exceder limite

### Cálculo de Taxas de Cartão

- **Fonte**: `store.tax_rate_machine` (definido na Fase 1)
- **Cálculo Automático**: Backend calcula `card_net_amount` automaticamente
- **KPI**: Soma de todas as taxas do mês aparece em `GET /cash-sessions/dashboard-stats`

---

## 🎨 Sugestões de UI

### Tela: Apoio de Caixa (SELLER)

**Estado Fechado**:
- Card central: "Seu caixa está fechado"
- Botão grande: "Abrir Nova Sessão"
- Input: Valor do Fundo de Troco

**Estado Aberto**:
- Status: "Sessão Aberta às 08:00"
- Botões: [ Sangria ], [ Suprimento ], [ Fechar Caixa ]
- **Ocultar**: Gráficos, divergências de terceiros, faturamento total

### Tela: Dashboard Gerencial (MANAGER/ADMIN)

- KPIs: Sessões Ativas, Divergências Pendentes, Taxas de Cartão
- Lista: Conciliações Pendentes (link para resolver)
- Lista: Fechamentos Pendentes (link para forçar fechamento)

### Tela: Hub de Vendas

- Criar OS com busca de produtos unificada
- Adicionar itens (armação/lente)
- Calcular totais automaticamente
- Alertar se desconto exceder limite
- Botão: "Enviar para Pagamento"

### Tela: Checkout

- Mostrar resumo da OS
- Selecionar método de pagamento
- Se `CASH`: Validar que caixa está aberto
- Processar pagamento

### Tela: Laboratório (Kanban)

- 4 colunas: Aguardando Montagem, Aguardando Lente, Em Produção, Pronto
- Cards arrastáveis (drag & drop)
- Ao soltar: Chamar `PATCH /service-orders/{id}/status`

---

## 📝 Observações Finais

1. **Multi-tenancy**: Todos os endpoints filtram automaticamente por `organization_id` do token
2. **Soft Delete**: Recursos deletados têm `is_active = false` (não aparecem em listagens)
3. **Validações**: Backend valida todos os dados (estoque, permissões, regras de negócio)
4. **Erros**: Sempre retornam JSON com `detail` explicando o erro
5. **Timestamps**: Todos os recursos têm `created_at` e `updated_at` (ISO 8601)

---

**Status**: ✅ Documentação Completa - Pronto para Implementação Frontend

