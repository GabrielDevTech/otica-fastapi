# Planejamento: Estrutura Backend - Fase 2 (Ciclo de Venda)

## 📋 Visão Geral

Este documento detalha a estrutura completa do backend para a **Fase 2: O Ciclo de Venda**, seguindo os padrões estabelecidos no projeto.

**Princípio Central**: Separação de responsabilidades entre Seller (operacional) e Manager (gerencial).

---

## 🗂️ Estrutura de Módulos

### Módulos Principais

1. **Cash Sessions** (Apoio de Caixa)
2. **Service Orders** (Hub de Vendas / Ordem de Serviço)
3. **Sales/Checkout** (Pagamento / PDV)
4. **Lab Queue** (Fila de Laboratório)
5. **Products Search** (Busca Unificada)
6. **Cash Movements** (Sangria/Suprimento)
7. **Receivable Accounts** (Contas a Receber)
8. **Kardex** (Histórico de Movimentação)

---

## 1️⃣ Módulo: Cash Sessions (Apoio de Caixa)

### 📊 Model: `CashSession`

**Arquivo**: `app/models/cash_session_model.py`

```python
class CashSessionStatus(str, enum.Enum):
    OPEN = "OPEN"              # Caixa aberto
    CLOSED = "CLOSED"          # Caixa fechado normalmente
    PENDING_AUDIT = "PENDING_AUDIT"  # Fechado com divergência (aguardando auditoria)

class CashSession(BaseModel):
    __tablename__ = "cash_sessions"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    
    # Status e controle
    status = Column(Enum(CashSessionStatus), default=CashSessionStatus.OPEN, nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Valores financeiros
    opening_balance = Column(Numeric(10, 2), nullable=False, doc="Fundo de troco inicial")
    closing_balance = Column(Numeric(10, 2), nullable=True, doc="Valor informado pelo vendedor ao fechar")
    calculated_balance = Column(Numeric(10, 2), nullable=True, doc="Valor calculado pelo sistema")
    discrepancy = Column(Numeric(10, 2), nullable=True, doc="Diferença (calculated - closing)")
    
    # Auditoria
    audit_resolved_by = Column(Integer, ForeignKey("staff_members.id"), nullable=True)
    audit_resolved_at = Column(DateTime(timezone=True), nullable=True)
    audit_action = Column(String(50), nullable=True, doc="ACCEPT_LOSS, CHARGE_STAFF, CORRECT_VALUE")
    audit_notes = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="cash_sessions")
    staff = relationship("StaffMember", foreign_keys=[staff_id], backref="cash_sessions")
    auditor = relationship("StaffMember", foreign_keys=[audit_resolved_by])
    
    __table_args__ = (
        Index('idx_cash_org_store', 'organization_id', 'store_id'),
        Index('idx_cash_staff_status', 'staff_id', 'status'),
        Index('idx_cash_status_org', 'status', 'organization_id'),
    )
```

### 📝 Schemas: `CashSession`

**Arquivo**: `app/schemas/cash_session_schema.py`

```python
class CashSessionBase(BaseModel):
    opening_balance: Decimal = Field(..., ge=0, description="Fundo de troco inicial")

class CashSessionCreate(CashSessionBase):
    store_id: int = Field(..., description="ID da loja")

class CashSessionClose(BaseModel):
    closing_balance: Decimal = Field(..., ge=0, description="Valor informado ao fechar")

class CashSessionAudit(BaseModel):
    action: Literal["ACCEPT_LOSS", "CHARGE_STAFF", "CORRECT_VALUE"]
    corrected_value: Optional[Decimal] = Field(None, description="Novo valor (se action=CORRECT_VALUE)")
    notes: Optional[str] = None

class CashSessionResponse(CashSessionBase):
    id: int
    organization_id: str
    store_id: int
    staff_id: int
    status: CashSessionStatus
    opened_at: datetime
    closed_at: Optional[datetime]
    closing_balance: Optional[Decimal]
    calculated_balance: Optional[Decimal]
    discrepancy: Optional[Decimal]
    audit_resolved_by: Optional[int]
    audit_resolved_at: Optional[datetime]
    audit_action: Optional[str]
    audit_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CashSessionStats(BaseModel):
    """KPIs para dashboard gerencial"""
    active_sessions_count: int
    pending_audit_count: int
    total_discrepancy: Decimal
    card_fees_estimated: Decimal  # Taxas de cartão estimadas (mês)
```

### 🛣️ Router: `cash_sessions.py`

**Arquivo**: `app/routers/v1/cash_sessions.py`

#### Endpoints

**1. GET `/api/v1/cash-sessions/my-session`**
- **Permissão**: `require_staff_or_above` (SELLER, STAFF, MANAGER, ADMIN)
- **Descrição**: Retorna a sessão de caixa ativa do vendedor logado
- **Lógica**:
  - Busca sessão com `staff_id = current_staff.id` e `status = OPEN`
  - Se não encontrar, retorna `null` (caixa fechado)
- **Response**: `CashSessionResponse | null`

**2. POST `/api/v1/cash-sessions`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Abre nova sessão de caixa
- **Body**: `CashSessionCreate`
- **Lógica**:
  - Valida que não existe sessão aberta para o vendedor
  - Valida que `store_id` pertence à organização
  - Cria sessão com `status = OPEN`, `opened_at = now()`
- **Response**: `CashSessionResponse` (201)

**3. POST `/api/v1/cash-sessions/{session_id}/close`**
- **Permissão**: `require_staff_or_above` (apenas o dono da sessão ou MANAGER/ADMIN)
- **Descrição**: Fecha a sessão de caixa
- **Body**: `CashSessionClose`
- **Lógica**:
  - Calcula `calculated_balance` = `opening_balance` + entradas - saídas (cash movements)
  - Compara com `closing_balance` informado
  - Se houver divergência: `status = PENDING_AUDIT`, `discrepancy = calculated - closing`
  - Se não houver divergência: `status = CLOSED`
  - `closed_at = now()`
- **Response**: `CashSessionResponse` (200)

**4. GET `/api/v1/cash-sessions/dashboard-stats`**
- **Permissão**: `require_manager_or_admin`
- **Descrição**: KPIs para dashboard gerencial
- **Lógica**:
  - Conta sessões ativas (`status = OPEN`)
  - Conta sessões pendentes de auditoria (`status = PENDING_AUDIT`)
  - Soma total de divergências
  - Calcula taxas de cartão estimadas (usando `store.tax_rate_machine`)
- **Response**: `CashSessionStats` (200)

**5. GET `/api/v1/cash-sessions`**
- **Permissão**: `require_manager_or_admin`
- **Descrição**: Lista todas as sessões (filtros opcionais)
- **Query Params**:
  - `status`: Filter por status
  - `store_id`: Filter por loja
  - `staff_id`: Filter por vendedor
- **Response**: `List[CashSessionResponse]` (200)

**6. POST `/api/v1/cash-sessions/{session_id}/audit`**
- **Permissão**: `require_manager_or_admin`
- **Descrição**: Resolve divergência de caixa
- **Body**: `CashSessionAudit`
- **Lógica**:
  - Valida que sessão está em `PENDING_AUDIT`
  - Se `action = ACCEPT_LOSS`: Cria despesa automática (futuro módulo financeiro)
  - Se `action = CHARGE_STAFF`: Cria conta a receber contra o vendedor
  - Se `action = CORRECT_VALUE`: Atualiza `calculated_balance` com `corrected_value`
  - Atualiza `audit_resolved_by`, `audit_resolved_at`, `audit_action`, `audit_notes`
  - `status = CLOSED`
- **Response**: `CashSessionResponse` (200)

---

## 2️⃣ Módulo: Cash Movements (Sangria/Suprimento)

### 📊 Model: `CashMovement`

**Arquivo**: `app/models/cash_movement_model.py`

```python
class CashMovementType(str, enum.Enum):
    WITHDRAWAL = "WITHDRAWAL"  # Sangria / Retirada
    DEPOSIT = "DEPOSIT"         # Suprimento / Entrada

class CashMovement(BaseModel):
    __tablename__ = "cash_movements"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    
    # Dados
    movement_type = Column(Enum(CashMovementType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False, doc="Valor da movimentação")
    description = Column(String(255), nullable=True, doc="Motivo (ex: 'Pagar lanche', 'Buscar troco')")
    movement_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    cash_session = relationship("CashSession", backref="cash_movements")
    staff = relationship("StaffMember", backref="cash_movements")
    
    __table_args__ = (
        Index('idx_cash_mov_session', 'cash_session_id', 'movement_date'),
        Index('idx_cash_mov_org', 'organization_id', 'movement_date'),
    )
```

### 📝 Schemas: `CashMovement`

**Arquivo**: `app/schemas/cash_movement_schema.py`

```python
class CashMovementBase(BaseModel):
    movement_type: CashMovementType
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None

class CashMovementCreate(CashMovementBase):
    pass

class CashMovementResponse(CashMovementBase):
    id: int
    organization_id: str
    cash_session_id: int
    staff_id: int
    movement_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 🛣️ Router: `cash_movements.py`

**Arquivo**: `app/routers/v1/cash_movements.py`

#### Endpoints

**1. POST `/api/v1/cash-movements`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Registra sangria ou suprimento
- **Body**: `CashMovementCreate`
- **Lógica**:
  - Busca sessão ativa do vendedor (`cash_session_id`)
  - Valida que sessão está `OPEN`
  - Cria movimento
- **Response**: `CashMovementResponse` (201)

**2. GET `/api/v1/cash-movements`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Lista movimentos da sessão atual
- **Query Params**:
  - `cash_session_id`: ID da sessão (opcional, usa sessão atual se não informado)
- **Response**: `List[CashMovementResponse]` (200)

---

## 3️⃣ Módulo: Service Orders (Hub de Vendas)

### 📊 Model: `ServiceOrder`

**Arquivo**: `app/models/service_order_model.py`

```python
class ServiceOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"                    # Rascunho (pode editar)
    PENDING = "PENDING"                # Aguardando pagamento
    PAID = "PAID"                      # Paga, aguardando montagem
    AWAITING_LENS = "AWAITING_LENS"    # Aguardando lente (surfaçagem)
    IN_PRODUCTION = "IN_PRODUCTION"    # Em produção
    READY = "READY"                    # Pronto / Controle qualidade
    DELIVERED = "DELIVERED"            # Entregue
    CANCELLED = "CANCELLED"            # Cancelada

class ServiceOrder(BaseModel):
    __tablename__ = "service_orders"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    
    # Status e controle
    status = Column(Enum(ServiceOrderStatus), default=ServiceOrderStatus.DRAFT, nullable=False)
    order_number = Column(String(50), nullable=False, unique=True, index=True, doc="Número da OS (ex: OS-2024-001)")
    
    # Valores
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    discount_percentage = Column(Numeric(5, 2), nullable=True, doc="Percentual de desconto aplicado")
    total = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Controle de desconto
    discount_approved_by = Column(Integer, ForeignKey("staff_members.id"), nullable=True, doc="Quem aprovou desconto acima do limite")
    max_discount_allowed = Column(Numeric(5, 2), nullable=True, default=10.0, doc="Limite de desconto (%)")
    
    # Datas
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Observações
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    customer = relationship("Customer", backref="service_orders")
    store = relationship("Store", backref="service_orders")
    seller = relationship("StaffMember", foreign_keys=[seller_id], backref="service_orders")
    approver = relationship("StaffMember", foreign_keys=[discount_approved_by])
    items = relationship("ServiceOrderItem", back_populates="service_order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_so_org_status', 'organization_id', 'status'),
        Index('idx_so_store_date', 'store_id', 'created_at'),
        Index('idx_so_seller', 'seller_id', 'created_at'),
    )
```

### 📊 Model: `ServiceOrderItem`

**Arquivo**: `app/models/service_order_item_model.py`

```python
class ServiceOrderItem(BaseModel):
    __tablename__ = "service_order_items"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    service_order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tipo de item
    item_type = Column(String(20), nullable=False, doc="FRAME, LENS, SERVICE")
    
    # Produto (pode ser frame ou lens)
    product_frame_id = Column(Integer, ForeignKey("products_frames.id"), nullable=True)
    product_lens_id = Column(Integer, ForeignKey("products_lenses.id"), nullable=True)
    
    # Quantidade e preços
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Reserva de estoque
    reserved_quantity = Column(Integer, default=0, nullable=False, doc="Quantidade reservada em inventory_levels")
    reserved_at = Column(DateTime(timezone=True), nullable=True, doc="Quando foi reservado")
    
    # Lente específica
    lens_spherical = Column(Numeric(5, 2), nullable=True, doc="Esférico")
    lens_cylindrical = Column(Numeric(5, 2), nullable=True, doc="Cilíndrico")
    lens_axis = Column(Integer, nullable=True, doc="Eixo")
    lens_addition = Column(Numeric(5, 2), nullable=True, doc="Adição")
    lens_side = Column(String(10), nullable=True, doc="OD, OE, AMBOS")
    
    # Flags
    needs_purchasing = Column(Boolean, default=False, nullable=False, doc="Lente surfaçagem precisa comprar")
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    service_order = relationship("ServiceOrder", back_populates="items")
    product_frame = relationship("ProductFrame", backref="order_items")
    product_lens = relationship("ProductLens", backref="order_items")
    
    __table_args__ = (
        Index('idx_soi_order', 'service_order_id', 'item_type'),
        Index('idx_soi_reserved', 'reserved_quantity', 'reserved_at'),
    )
```

### 📝 Schemas: `ServiceOrder`

**Arquivo**: `app/schemas/service_order_schema.py`

```python
class ServiceOrderItemBase(BaseModel):
    item_type: Literal["FRAME", "LENS", "SERVICE"]
    product_frame_id: Optional[int] = None
    product_lens_id: Optional[int] = None
    quantity: int = Field(1, gt=0)
    unit_price: Decimal = Field(..., gt=0)
    discount_amount: Decimal = Field(0, ge=0)
    # Lente específica
    lens_spherical: Optional[Decimal] = None
    lens_cylindrical: Optional[Decimal] = None
    lens_axis: Optional[int] = Field(None, ge=0, le=180)
    lens_addition: Optional[Decimal] = None
    lens_side: Optional[Literal["OD", "OE", "AMBOS"]] = None

class ServiceOrderItemCreate(ServiceOrderItemBase):
    pass

class ServiceOrderItemResponse(ServiceOrderItemBase):
    id: int
    service_order_id: int
    total_price: Decimal
    reserved_quantity: int
    needs_purchasing: bool
    is_active: bool
    
    class Config:
        from_attributes = True

class ServiceOrderBase(BaseModel):
    customer_id: int = Field(..., description="ID do cliente")
    store_id: int = Field(..., description="ID da loja")
    notes: Optional[str] = None

class ServiceOrderCreate(ServiceOrderBase):
    items: List[ServiceOrderItemCreate] = Field(..., min_items=1)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

class ServiceOrderUpdate(BaseModel):
    """Permite editar apenas enquanto DRAFT"""
    items: Optional[List[ServiceOrderItemCreate]] = None
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = None

class ServiceOrderResponse(ServiceOrderBase):
    id: int
    organization_id: str
    seller_id: int
    status: ServiceOrderStatus
    order_number: str
    subtotal: Decimal
    discount_amount: Decimal
    discount_percentage: Optional[Decimal]
    total: Decimal
    max_discount_allowed: Optional[Decimal]
    discount_approved_by: Optional[int]
    paid_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    items: List[ServiceOrderItemResponse]
    
    class Config:
        from_attributes = True
```

### 🛣️ Router: `service_orders.py`

**Arquivo**: `app/routers/v1/service_orders.py`

#### Endpoints

**1. POST `/api/v1/service-orders`**
- **Permissão**: `require_staff_or_above` (SELLER pode criar)
- **Descrição**: Cria nova Ordem de Serviço
- **Body**: `ServiceOrderCreate`
- **Lógica**:
  - Gera `order_number` único (ex: `OS-2024-001`)
  - Valida `customer_id`, `store_id` pertencem à organização
  - Calcula `subtotal`, `discount_amount`, `total`
  - Para cada item:
    - Se `item_type = FRAME`: Valida estoque e reserva (`reserved_quantity++`)
    - Se `item_type = LENS`: Valida estoque na `lens_stock_grid` ou marca `needs_purchasing = true`
  - Se `discount_percentage > max_discount_allowed`: Requer aprovação de MANAGER/ADMIN
  - `status = DRAFT`
- **Response**: `ServiceOrderResponse` (201)

**2. GET `/api/v1/service-orders`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Lista OS (filtros)
- **Query Params**:
  - `status`: Filter por status
  - `customer_id`: Filter por cliente
  - `store_id`: Filter por loja
  - `seller_id`: Filter por vendedor (SELLER vê apenas as suas)
- **Lógica**:
  - SELLER: Filtra automaticamente por `seller_id = current_staff.id`
  - MANAGER/ADMIN: Vê todas
- **Response**: `List[ServiceOrderResponse]` (200)

**3. GET `/api/v1/service-orders/{order_id}`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Obtém OS específica
- **Lógica**: Valida acesso (SELLER só vê as suas)
- **Response**: `ServiceOrderResponse` (200)

**4. PATCH `/api/v1/service-orders/{order_id}`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Edita OS (apenas se `status = DRAFT`)
- **Body**: `ServiceOrderUpdate`
- **Lógica**:
  - Valida que `status = DRAFT`
  - Libera reservas antigas
  - Aplica novas reservas
  - Recalcula totais
- **Response**: `ServiceOrderResponse` (200)

**5. PATCH `/api/v1/service-orders/{order_id}/approve-discount`**
- **Permissão**: `require_manager_or_admin`
- **Descrição**: Aprova desconto acima do limite
- **Lógica**:
  - Atualiza `discount_approved_by = current_staff.id`
  - Recalcula totais
- **Response**: `ServiceOrderResponse` (200)

**6. POST `/api/v1/service-orders/{order_id}/send-to-payment`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Envia OS para pagamento
- **Lógica**:
  - Valida que `status = DRAFT`
  - Valida estoque final
  - `status = PENDING`
- **Response**: `ServiceOrderResponse` (200)

**7. PATCH `/api/v1/service-orders/{order_id}/status`**
- **Permissão**: `require_manager_or_admin` ou `require_lab_role` (futuro)
- **Descrição**: Atualiza status (para laboratório)
- **Body**: `{"status": "IN_PRODUCTION" | "READY" | ...}`
- **Lógica**:
  - Valida transições de status permitidas
  - Registra log de mudança (futuro: `service_order_status_logs`)
- **Response**: `ServiceOrderResponse` (200)

**8. POST `/api/v1/service-orders/{order_id}/cancel`**
- **Permissão**: `require_manager_or_admin`
- **Descrição**: Cancela OS (estorno)
- **Lógica**:
  - Libera todas as reservas de estoque
  - `status = CANCELLED`
  - Reverte lançamentos financeiros (se já pago)
- **Response**: `ServiceOrderResponse` (200)

---

## 4️⃣ Módulo: Products Search (Busca Unificada)

### 🛣️ Router: `products.py`

**Arquivo**: `app/routers/v1/products.py`

#### Endpoints

**1. GET `/api/v1/products/search`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Busca unificada de Armações e Lentes
- **Query Params**:
  - `q`: Termo de busca (código, nome, marca)
  - `type`: `FRAME` | `LENS` | `ALL` (default)
  - `store_id`: Filter por loja (para verificar estoque)
- **Lógica**:
  - Busca em `products_frames` e `products_lenses`
  - Se `store_id` fornecido: Inclui `quantity` e `reserved_quantity` do estoque
- **Response**: 
```json
{
  "frames": [
    {
      "id": 1,
      "reference_code": "ABC123",
      "name": "Armação X",
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
      "id": 1,
      "name": "Lente Y",
      "sell_price": 200.00,
      "is_lab_order": false
    }
  ]
}
```

---

## 5️⃣ Módulo: Sales/Checkout (Pagamento)

### 📊 Model: `Sale`

**Arquivo**: `app/models/sale_model.py`

```python
class PaymentMethod(str, enum.Enum):
    CASH = "CASH"              # Dinheiro
    CARD = "CARD"              # Cartão
    PIX = "PIX"                # Pix
    CREDIT = "CREDIT"          # Crediário

class Sale(BaseModel):
    __tablename__ = "sales"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=True, index=True, doc="Apenas se pagamento em dinheiro")
    
    # Valores
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Cartão específico
    card_fee_rate = Column(Numeric(5, 2), nullable=True, doc="Taxa aplicada (de store.tax_rate_machine)")
    card_gross_amount = Column(Numeric(10, 2), nullable=True, doc="Valor bruto")
    card_net_amount = Column(Numeric(10, 2), nullable=True, doc="Valor líquido (após taxa)")
    
    # Crediário
    receivable_account_id = Column(Integer, ForeignKey("receivable_accounts.id"), nullable=True, index=True)
    
    # Comissão
    commissionable_amount = Column(Numeric(10, 2), nullable=True, doc="Valor comissionável")
    
    # Datas
    sold_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    service_order = relationship("ServiceOrder", backref="sale")
    customer = relationship("Customer", backref="sales")
    store = relationship("Store", backref="sales")
    seller = relationship("StaffMember", foreign_keys=[seller_id], backref="sales")
    cash_session = relationship("CashSession", backref="sales")
    receivable_account = relationship("ReceivableAccount", backref="sales")
    
    __table_args__ = (
        Index('idx_sale_org_date', 'organization_id', 'sold_at'),
        Index('idx_sale_store_date', 'store_id', 'sold_at'),
        Index('idx_sale_seller', 'seller_id', 'sold_at'),
    )
```

### 📝 Schemas: `Sale`

**Arquivo**: `app/schemas/sale_schema.py`

```python
class SaleCheckout(BaseModel):
    payment_method: PaymentMethod
    cash_session_id: Optional[int] = None  # Obrigatório se payment_method = CASH

class SaleResponse(BaseModel):
    id: int
    organization_id: str
    service_order_id: int
    customer_id: int
    store_id: int
    seller_id: int
    cash_session_id: Optional[int]
    total_amount: Decimal
    payment_method: PaymentMethod
    card_fee_rate: Optional[Decimal]
    card_gross_amount: Optional[Decimal]
    card_net_amount: Optional[Decimal]
    receivable_account_id: Optional[int]
    commissionable_amount: Optional[Decimal]
    sold_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 🛣️ Router: `sales.py`

**Arquivo**: `app/routers/v1/sales.py`

#### Endpoints

**1. POST `/api/v1/sales/{order_id}/checkout`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Processa pagamento e finaliza venda
- **Body**: `SaleCheckout`
- **Lógica**:
  - Valida que `service_order.status = PENDING`
  - Se `payment_method = CASH`:
    - Valida que `cash_session_id` existe e está `OPEN`
    - Valida que `cash_session.staff_id = current_staff.id`
    - Cria lançamento de entrada (futuro: `financial_entries`)
  - Se `payment_method = CARD`:
    - Calcula `card_gross_amount = total_amount`
    - Calcula `card_net_amount = total_amount * (1 - tax_rate_machine/100)`
    - Usa `store.tax_rate_machine`
  - Se `payment_method = PIX` ou `CREDIT`:
    - Cria `ReceivableAccount` (conta a receber)
  - Baixa estoque definitivo:
    - `inventory_levels.quantity -= reserved_quantity`
    - `inventory_levels.reserved_quantity = 0`
  - Cria registro em `Kardex` (histórico)
  - Atualiza `service_order.status = PAID`
  - Cria `Sale`
  - Calcula `commissionable_amount` (futuro: regras de comissão)
- **Response**: `SaleResponse` (201)

---

## 6️⃣ Módulo: Receivable Accounts (Contas a Receber)

### 📊 Model: `ReceivableAccount`

**Arquivo**: `app/models/receivable_account_model.py`

```python
class ReceivableStatus(str, enum.Enum):
    PENDING = "PENDING"        # Pendente
    PARTIAL = "PARTIAL"        # Parcialmente pago
    PAID = "PAID"              # Pago
    OVERDUE = "OVERDUE"        # Vencido
    CANCELLED = "CANCELLED"    # Cancelado

class ReceivableAccount(BaseModel):
    __tablename__ = "receivable_accounts"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True, index=True)
    
    # Valores
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    remaining_amount = Column(Numeric(10, 2), nullable=False, doc="total_amount - paid_amount")
    
    # Status e controle
    status = Column(Enum(ReceivableStatus), default=ReceivableStatus.PENDING, nullable=False)
    due_date = Column(Date, nullable=False, doc="Data de vencimento")
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Observações
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    customer = relationship("Customer", backref="receivable_accounts")
    sale = relationship("Sale", backref="receivable_accounts")
    
    __table_args__ = (
        Index('idx_rec_org_status', 'organization_id', 'status'),
        Index('idx_rec_customer', 'customer_id', 'due_date'),
        Index('idx_rec_due_date', 'due_date', 'status'),
    )
```

### 📝 Schemas: `ReceivableAccount`

**Arquivo**: `app/schemas/receivable_account_schema.py`

```python
class ReceivableAccountBase(BaseModel):
    customer_id: int
    total_amount: Decimal = Field(..., gt=0)
    due_date: date
    notes: Optional[str] = None

class ReceivableAccountCreate(ReceivableAccountBase):
    sale_id: Optional[int] = None

class ReceivableAccountResponse(ReceivableAccountBase):
    id: int
    organization_id: str
    sale_id: Optional[int]
    paid_amount: Decimal
    remaining_amount: Decimal
    status: ReceivableStatus
    paid_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

---

## 7️⃣ Módulo: Lab Queue (Fila de Laboratório)

### 🛣️ Router: `lab.py`

**Arquivo**: `app/routers/v1/lab.py`

#### Endpoints

**1. GET `/api/v1/lab/queue`**
- **Permissão**: `require_staff_or_above` (todos podem ver)
- **Descrição**: Retorna OS organizadas por status (Kanban)
- **Query Params**:
  - `store_id`: Filter por loja
- **Lógica**:
  - Agrupa OS por `status`
  - Filtra apenas `status IN (PAID, AWAITING_LENS, IN_PRODUCTION, READY)`
- **Response**:
```json
{
  "awaiting_mount": [...],  // status = PAID
  "awaiting_lens": [...],   // status = AWAITING_LENS
  "in_production": [...],   // status = IN_PRODUCTION
  "ready": [...]            // status = READY
}
```

**2. PATCH `/api/v1/service-orders/{order_id}/status`**
- **Permissão**: `require_manager_or_admin` ou `require_lab_role` (futuro)
- **Descrição**: Atualiza status da OS (mover no Kanban)
- **Body**: `{"status": "IN_PRODUCTION" | "READY" | "DELIVERED"}`
- **Lógica**:
  - Valida transições permitidas
  - Se `status = READY`: Baixa estoque de lentes (se houver quebra, registra)
  - Registra log de mudança
- **Response**: `ServiceOrderResponse` (200)

---

## 8️⃣ Módulo: Kardex (Histórico de Movimentação)

### 📊 Model: `Kardex`

**Arquivo**: `app/models/kardex_model.py`

```python
class KardexType(str, enum.Enum):
    ENTRY = "ENTRY"        # Entrada (compra, ajuste positivo)
    EXIT = "EXIT"          # Saída (venda, ajuste negativo)
    RESERVATION = "RESERVATION"  # Reserva
    RELEASE = "RELEASE"    # Liberação de reserva

class Kardex(BaseModel):
    __tablename__ = "kardex"
    
    # Multi-tenancy
    organization_id = Column(String, nullable=False, index=True)
    
    # Relacionamentos
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    product_frame_id = Column(Integer, ForeignKey("products_frames.id"), nullable=True, index=True)
    product_lens_id = Column(Integer, ForeignKey("products_lenses.id"), nullable=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=True, index=True)
    
    # Dados
    movement_type = Column(Enum(KardexType), nullable=False)
    quantity = Column(Integer, nullable=False, doc="Quantidade movimentada (positivo ou negativo)")
    balance_before = Column(Integer, nullable=False, doc="Saldo antes da movimentação")
    balance_after = Column(Integer, nullable=False, doc="Saldo após a movimentação")
    
    # Rastreabilidade
    moved_by = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    movement_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    notes = Column(String(255), nullable=True)
    
    # Relationships
    store = relationship("Store", backref="kardex")
    product_frame = relationship("ProductFrame", backref="kardex")
    product_lens = relationship("ProductLens", backref="kardex")
    sale = relationship("Sale", backref="kardex")
    service_order = relationship("ServiceOrder", backref="kardex")
    staff = relationship("StaffMember", backref="kardex")
    
    __table_args__ = (
        Index('idx_kardex_store_date', 'store_id', 'movement_date'),
        Index('idx_kardex_product', 'product_frame_id', 'movement_date'),
        Index('idx_kardex_org_date', 'organization_id', 'movement_date'),
    )
```

### 📝 Schemas: `Kardex`

**Arquivo**: `app/schemas/kardex_schema.py`

```python
class KardexResponse(BaseModel):
    id: int
    organization_id: str
    store_id: int
    product_frame_id: Optional[int]
    product_lens_id: Optional[int]
    sale_id: Optional[int]
    service_order_id: Optional[int]
    movement_type: KardexType
    quantity: int
    balance_before: int
    balance_after: int
    moved_by: int
    movement_date: datetime
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 🛣️ Router: `kardex.py`

**Arquivo**: `app/routers/v1/kardex.py`

#### Endpoints

**1. GET `/api/v1/kardex`**
- **Permissão**: `require_staff_or_above`
- **Descrição**: Histórico de movimentações
- **Query Params**:
  - `store_id`: Filter por loja
  - `product_frame_id`: Filter por armação
  - `product_lens_id`: Filter por lente
  - `movement_type`: Filter por tipo
  - `start_date`, `end_date`: Range de datas
- **Response**: `List[KardexResponse]` (200)

---

## 🔐 Permissões RBAC

### Novas Dependencies

**Arquivo**: `app/core/permissions.py`

```python
# Adicionar ao arquivo existente

require_seller_or_above = require_role(
    StaffRole.ADMIN, 
    StaffRole.MANAGER, 
    StaffRole.STAFF, 
    StaffRole.SELLER
)

# Futuro: Role para laboratório
# require_lab_role = require_role(StaffRole.ADMIN, StaffRole.MANAGER, StaffRole.LAB_TECH)
```

### Matriz de Permissões

| Endpoint | SELLER | STAFF | MANAGER | ADMIN |
|----------|--------|-------|---------|-------|
| `GET /cash-sessions/my-session` | ✅ | ✅ | ✅ | ✅ |
| `POST /cash-sessions` | ✅ | ✅ | ✅ | ✅ |
| `POST /cash-sessions/{id}/close` | ✅ (próprio) | ✅ | ✅ | ✅ |
| `GET /cash-sessions/dashboard-stats` | ❌ | ❌ | ✅ | ✅ |
| `POST /cash-sessions/{id}/audit` | ❌ | ❌ | ✅ | ✅ |
| `POST /service-orders` | ✅ | ✅ | ✅ | ✅ |
| `GET /service-orders` | ✅ (próprias) | ✅ | ✅ | ✅ |
| `PATCH /service-orders/{id}` | ✅ (DRAFT) | ✅ | ✅ | ✅ |
| `POST /service-orders/{id}/approve-discount` | ❌ | ❌ | ✅ | ✅ |
| `POST /service-orders/{id}/cancel` | ❌ | ❌ | ✅ | ✅ |
| `PATCH /service-orders/{id}/status` | ❌ | ❌ | ✅ | ✅ |
| `POST /sales/{id}/checkout` | ✅ | ✅ | ✅ | ✅ |
| `GET /lab/queue` | ✅ (read) | ✅ | ✅ | ✅ |
| `PATCH /service-orders/{id}/status` (lab) | ❌ | ❌ | ✅ | ✅ |

---

## 📦 Estrutura de Arquivos

```
otica-api/
├── app/
│   ├── models/
│   │   ├── cash_session_model.py          # Novo
│   │   ├── cash_movement_model.py        # Novo
│   │   ├── service_order_model.py        # Novo
│   │   ├── service_order_item_model.py    # Novo
│   │   ├── sale_model.py                  # Novo
│   │   ├── receivable_account_model.py    # Novo
│   │   └── kardex_model.py                # Novo
│   ├── schemas/
│   │   ├── cash_session_schema.py         # Novo
│   │   ├── cash_movement_schema.py         # Novo
│   │   ├── service_order_schema.py         # Novo
│   │   ├── sale_schema.py                  # Novo
│   │   ├── receivable_account_schema.py   # Novo
│   │   └── kardex_schema.py               # Novo
│   ├── routers/
│   │   └── v1/
│   │       ├── cash_sessions.py           # Novo
│   │       ├── cash_movements.py          # Novo
│   │       ├── service_orders.py          # Novo
│   │       ├── products.py                # Novo (busca unificada)
│   │       ├── sales.py                   # Novo
│   │       ├── receivable_accounts.py     # Novo
│   │       ├── lab.py                     # Novo
│   │       └── kardex.py                  # Novo
│   └── core/
│       └── permissions.py                 # Atualizar (novas dependencies)
```

---

## 🔄 Regras de Negócio Críticas

### 1. Reserva de Estoque

- **Quando**: Ao adicionar item na OS (`status = DRAFT` ou `PENDING`)
- **Ação**: `inventory_levels.reserved_quantity++`
- **Liberação**: 
  - Ao remover item da OS
  - Ao cancelar OS
  - Ao fechar venda (converte em baixa real)
  - **Cron Job**: Libera reservas de OS inativas há 24h

### 2. Validação de Lentes

- **Lente de Estoque**: Verifica `lens_stock_grid` (spherical, cylindrical, axis, addition)
- **Sem Estoque**: Bloqueia venda ou alerta
- **Lente Surfaçagem**: Permite venda, marca `needs_purchasing = true`

### 3. Cálculo de Taxas de Cartão

- **Fonte**: `store.tax_rate_machine` (definido na Fase 1)
- **Cálculo**: `card_net_amount = card_gross_amount * (1 - tax_rate_machine/100)`
- **KPI**: Soma de todas as taxas do mês

### 4. Auditoria de Caixa

- **Divergência**: `discrepancy = calculated_balance - closing_balance`
- **Ações**:
  - `ACCEPT_LOSS`: Cria despesa (futuro módulo financeiro)
  - `CHARGE_STAFF`: Cria `ReceivableAccount` contra o vendedor
  - `CORRECT_VALUE`: Ajusta `calculated_balance`

### 5. Controle de Desconto

- **Limite Padrão**: `max_discount_allowed = 10%`
- **Override**: MANAGER/ADMIN pode aprovar desconto maior
- **Registro**: `discount_approved_by` registra quem aprovou

### 6. Baixa de Estoque

- **Quando**: Ao confirmar pagamento (`POST /sales/{id}/checkout`)
- **Ação**: 
  - `inventory_levels.quantity -= reserved_quantity`
  - `inventory_levels.reserved_quantity = 0`
  - Cria registro em `Kardex` (tipo `EXIT`)

---

## 📝 Observações Importantes

1. **Multi-tenancy**: Todos os models devem ter `organization_id` (String)
2. **Soft Delete**: Todos os models devem ter `is_active` (Boolean)
3. **Timestamps**: Herdam `created_at` e `updated_at` de `BaseModel`
4. **Validações**: Sempre validar que recursos pertencem à organização
5. **Índices**: Criar índices para queries frequentes (status, datas, relacionamentos)
6. **Transações**: Operações críticas (checkout, fechamento de caixa) devem usar transações
7. **Logs**: Registrar mudanças importantes (status, auditoria)

---

## 🚀 Próximos Passos

1. Criar migrations para todas as tabelas
2. Implementar models
3. Implementar schemas
4. Implementar routers com validações
5. Implementar regras de negócio
6. Testes unitários e integração
7. Documentação de endpoints (Swagger)

---

**Status**: 📋 Planejamento Completo - Pronto para Implementação

