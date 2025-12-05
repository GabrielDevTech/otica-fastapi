# Implementação Sprint 1: Alicerces do Sistema

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Análise do Estado Atual](#análise-do-estado-atual)
3. [Implementação Passo a Passo](#implementação-passo-a-passo)
4. [Modelos de Dados](#modelos-de-dados)
5. [Endpoints da API](#endpoints-da-api)
6. [Schemas Pydantic](#schemas-pydantic)
7. [Regras de Negócio](#regras-de-negócio)
8. [Migrations](#migrations)
9. [Testes](#testes)

---

## 🎯 Visão Geral

### Objetivo

Criar a base de dados necessária para suportar o Hub de Vendas, incluindo:
1. Cadastro de Lojas (stores) - ✅ Parcialmente implementado
2. Cadastro de Departamentos (departments) - ✅ Parcialmente implementado
3. Finalizar Equipe (staff_members) - ⚠️ Precisa ajustes
4. Cadastro de Armações (products_frames) - ❌ Novo
5. Cadastro de Lentes (products_lenses) - ❌ Novo
6. Cadastro de Clientes (customers) - ❌ Novo

### Ordem de Dependência

```
1A/1B (Stores + Departments) → 2 (Staff) → 3 (Frames) → 4 (Lenses) → 5 (Customers)
```

---

## 🔍 Análise do Estado Atual

### ✅ O Que Já Existe

1. **Stores (Lojas)**
   - ✅ Model criado (`app/models/store_model.py`)
   - ✅ Router criado (`app/routers/v1/stores.py`)
   - ✅ Schemas criados (`app/schemas/store_schema.py`)
   - ⚠️ **Falta**: Campo `tax_rate_machine` e `address_data` (JSONB)

2. **Departments (Setores)**
   - ✅ Model criado (`app/models/department_model.py`)
   - ✅ Router criado (`app/routers/v1/departments.py`)
   - ✅ Schemas criados (`app/schemas/department_schema.py`)
   - ⚠️ **Falta**: Campo `description` e seed automático

3. **Staff Members (Equipe)**
   - ✅ Model criado (`app/models/staff_model.py`)
   - ✅ Router criado (`app/routers/v1/staff.py`)
   - ✅ Schemas criados (`app/schemas/staff_schema.py`)
   - ⚠️ **Falta**: `store_id` e `department_id` como obrigatórios

### ❌ O Que Precisa Ser Criado

1. **Products Frames (Armações)**
2. **Inventory Levels (Níveis de Estoque)**
3. **Products Lenses (Lentes)**
4. **Lens Stock Grid (Grade de Estoque de Lentes)**
5. **Customers (Clientes)**

---

## 🛠️ Implementação Passo a Passo

### Passo 1A: Atualizar Stores (Lojas)

#### 1.1. Modificar Model

```python
# app/models/store_model.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class Store(BaseModel):
    """Model para lojas de uma organização."""
    
    __tablename__ = "stores"
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # NOVOS CAMPOS
    address_data = Column(JSON, nullable=True, doc="Endereço completo em JSON")
    phone = Column(String(20), nullable=True)
    tax_rate_machine = Column(Numeric(5, 2), nullable=True, doc="Taxa da máquina de cartão (ex: 2.5)")
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organization", backref="stores")
```

#### 1.2. Atualizar Schema

```python
# app/schemas/store_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from decimal import Decimal


class StoreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address_data: Optional[Dict[str, Any]] = Field(None, description="Endereço completo em JSON")
    phone: Optional[str] = Field(None, max_length=20)
    tax_rate_machine: Optional[Decimal] = Field(None, ge=0, le=100, description="Taxa da máquina (ex: 2.5)")


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address_data: Optional[Dict[str, Any]] = None
    phone: Optional[str] = Field(None, max_length=20)
    tax_rate_machine: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### 1.3. Migration

```python
# scripts/migrations/add_store_fields.py
from sqlalchemy import text

async def upgrade():
    # Adicionar campo address_data
    await db.execute(text("""
        ALTER TABLE stores 
        ADD COLUMN address_data JSONB NULL;
    """))
    
    # Adicionar campo tax_rate_machine
    await db.execute(text("""
        ALTER TABLE stores 
        ADD COLUMN tax_rate_machine NUMERIC(5, 2) NULL;
    """))
    
    # Adicionar índice para busca por organização
    await db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stores_org_active 
        ON stores(organization_id, is_active);
    """))
```

---

### Passo 1B: Atualizar Departments (Setores)

#### 1.1. Modificar Model

```python
# app/models/department_model.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class Department(BaseModel):
    """Model para setores de uma organização."""
    
    __tablename__ = "departments"
    
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # NOVO CAMPO
    description = Column(Text, nullable=True, doc="Descrição do setor")
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organization", backref="departments")
```

#### 1.2. Atualizar Schema

```python
# app/schemas/department_schema.py
from pydantic import BaseModel, Field
from typing import Optional


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Descrição do setor")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### 1.3. Criar Seed de Departamentos

```python
# scripts/seed_departments.py
from app.models.department_model import Department
from app.models.organization_model import Organization
from sqlalchemy import select

DEPARTMENTS_SEED = [
    {"name": "Vendas", "description": "Equipe de vendas e atendimento ao cliente"},
    {"name": "Gerência", "description": "Gestão e administração"},
    {"name": "Financeiro", "description": "Controle financeiro e contábil"},
    {"name": "Laboratório", "description": "Laboratório e montagem de óculos"},
]


async def seed_departments_for_org(org_id: int, db: AsyncSession):
    """Cria departamentos padrão para uma organização."""
    
    # Verifica se já existem departamentos
    result = await db.execute(
        select(Department).where(Department.organization_id == org_id)
    )
    existing = result.scalars().all()
    
    if existing:
        print(f"⚠️ Organização {org_id} já tem departamentos. Pulando seed.")
        return
    
    # Cria departamentos
    for dept_data in DEPARTMENTS_SEED:
        department = Department(
            organization_id=org_id,
            **dept_data
        )
        db.add(department)
    
    await db.commit()
    print(f"✅ Departamentos criados para organização {org_id}")


async def seed_all_organizations(db: AsyncSession):
    """Cria departamentos para todas as organizações existentes."""
    result = await db.execute(select(Organization))
    orgs = result.scalars().all()
    
    for org in orgs:
        await seed_departments_for_org(org.id, db)
```

#### 1.4. Migration

```python
# scripts/migrations/add_department_description.py
from sqlalchemy import text

async def upgrade():
    await db.execute(text("""
        ALTER TABLE departments 
        ADD COLUMN description TEXT NULL;
    """))
```

---

### Passo 2: Atualizar Staff Members (Equipe)

#### 2.1. Modificar Model (Tornar store_id e department_id Obrigatórios)

```python
# app/models/staff_model.py
from sqlalchemy import Column, Integer, String, Boolean, Enum, Index, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.models.base_class import BaseModel


class StaffRole(str, enum.Enum):
    """Roles dos membros da equipe."""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    ASSISTANT = "ASSISTANT"
    # NOVO: Adicionar role SELLER se necessário
    SELLER = "SELLER"  # Vendedor


class StaffMember(BaseModel):
    """Model para membros da equipe."""
    
    __tablename__ = "staff_members"
    
    clerk_id = Column(String, unique=True, nullable=True, doc="Vínculo com usuário Clerk")
    organization_id = Column(String, nullable=False, index=True)
    
    # MODIFICAR: Tornar obrigatórios
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=False, index=True)
    
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    role = Column(Enum(StaffRole), default=StaffRole.STAFF, nullable=False)
    job_title = Column(String, nullable=True, index=True)  # Campo já existe
    is_active = Column(Boolean, default=True, nullable=False)
    avatar_url = Column(String, nullable=True)
    
    # Relationships
    store = relationship("Store", backref="staff_members")
    department = relationship("Department", backref="staff_members")
    
    __table_args__ = (
        Index('idx_staff_org_email', 'organization_id', 'email', unique=True),
        Index('idx_staff_org_role', 'organization_id', 'role'),
    )
```

#### 2.2. Atualizar Schema

```python
# app/schemas/staff_schema.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.staff_model import StaffRole


class StaffBase(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    role: StaffRole
    store_id: int = Field(..., description="ID da loja (obrigatório)")
    department_id: int = Field(..., description="ID do setor (obrigatório)")
    job_title: Optional[str] = Field(None, description="Cargo específico")
    is_active: bool = True


class StaffCreate(StaffBase):
    pass


class StaffUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    email: Optional[EmailStr] = None
    role: Optional[StaffRole] = None
    store_id: Optional[int] = Field(None, description="ID da loja")
    department_id: Optional[int] = Field(None, description="ID do setor")
    job_title: Optional[str] = None
    is_active: Optional[bool] = None


class StaffResponse(StaffBase):
    id: int
    clerk_id: Optional[str] = None
    organization_id: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### 2.3. Atualizar Router (Validações)

```python
# app/routers/v1/staff.py (adicionar validações)

@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria um novo membro da equipe.
    
    **Permissões**: ADMIN apenas
    """
    # Converter org_id para ID interno
    org_id = await get_org_internal_id(db, current_org_id)
    
    # Validar se store pertence à organização
    store_result = await db.execute(
        select(Store).where(
            Store.id == staff_data.store_id,
            Store.organization_id == org_id
        )
    )
    store = store_result.scalar_one_or_none()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loja não encontrada ou não pertence à organização"
        )
    
    # Validar se department pertence à organização
    dept_result = await db.execute(
        select(Department).where(
            Department.id == staff_data.department_id,
            Department.organization_id == org_id
        )
    )
    department = dept_result.scalar_one_or_none()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setor não encontrado ou não pertence à organização"
        )
    
    # Verifica se email já existe na organização
    existing = await db.execute(
        select(StaffMember).where(
            StaffMember.organization_id == current_org_id,
            StaffMember.email == staff_data.email
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado nesta organização"
        )
    
    # Cria novo membro
    new_staff = StaffMember(
        **staff_data.model_dump(),
        organization_id=current_org_id
    )
    
    db.add(new_staff)
    await db.commit()
    await db.refresh(new_staff)
    
    return new_staff
```

#### 2.4. Migration

```python
# scripts/migrations/make_staff_store_dept_required.py
from sqlalchemy import text

async def upgrade():
    # Primeiro, atualizar registros NULL (se houver)
    await db.execute(text("""
        UPDATE staff_members 
        SET store_id = (
            SELECT id FROM stores 
            WHERE organization_id = (
                SELECT id FROM organizations 
                WHERE clerk_org_id = staff_members.organization_id
            ) 
            LIMIT 1
        )
        WHERE store_id IS NULL;
    """))
    
    await db.execute(text("""
        UPDATE staff_members 
        SET department_id = (
            SELECT id FROM departments 
            WHERE organization_id = (
                SELECT id FROM organizations 
                WHERE clerk_org_id = staff_members.organization_id
            ) 
            LIMIT 1
        )
        WHERE department_id IS NULL;
    """))
    
    # Tornar obrigatórios
    await db.execute(text("""
        ALTER TABLE staff_members 
        ALTER COLUMN store_id SET NOT NULL;
    """))
    
    await db.execute(text("""
        ALTER TABLE staff_members 
        ALTER COLUMN department_id SET NOT NULL;
    """))
```

---

### Passo 3: Criar Products Frames (Armações)

#### 3.1. Criar Model

```python
# app/models/product_frame_model.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class ProductFrame(BaseModel):
    """Model para armações de óculos."""
    
    __tablename__ = "products_frames"
    
    organization_id = Column(String, nullable=False, index=True)
    
    # Campos essenciais
    reference_code = Column(String(100), nullable=False, index=True, doc="Código de barras")
    name = Column(String(255), nullable=False, doc="Nome da armação")
    brand = Column(String(100), nullable=True, doc="Marca")
    model = Column(String(100), nullable=True, doc="Modelo")
    
    # Preços
    cost_price = Column(Numeric(10, 2), nullable=True, doc="Preço de custo")
    sell_price = Column(Numeric(10, 2), nullable=False, doc="Preço de venda")
    
    # Estoque
    min_stock_alert = Column(Integer, default=0, nullable=False, doc="Quantidade mínima para alerta")
    
    # Outros
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        # Garante código único por organização
        Index('idx_frame_org_code', 'organization_id', 'reference_code', unique=True),
        Index('idx_frame_org_active', 'organization_id', 'is_active'),
    )
```

#### 3.2. Criar Model de Inventory Levels

```python
# app/models/inventory_level_model.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class InventoryLevel(BaseModel):
    """Model para níveis de estoque por loja."""
    
    __tablename__ = "inventory_levels"
    
    organization_id = Column(String, nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_frame_id = Column(Integer, ForeignKey("products_frames.id", ondelete="CASCADE"), nullable=False, index=True)
    
    quantity = Column(Integer, default=0, nullable=False, doc="Quantidade em estoque")
    reserved_quantity = Column(Integer, default=0, nullable=False, doc="Quantidade reservada")
    
    # Relationships
    store = relationship("Store", backref="inventory_levels")
    product_frame = relationship("ProductFrame", backref="inventory_levels")
    
    __table_args__ = (
        # Garante um registro único por loja + produto
        Index('idx_inv_store_frame', 'store_id', 'product_frame_id', unique=True),
        Index('idx_inv_org_store', 'organization_id', 'store_id'),
    )
```

#### 3.3. Criar Schemas

```python
# app/schemas/product_frame_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ProductFrameBase(BaseModel):
    reference_code: str = Field(..., min_length=1, max_length=100, description="Código de barras")
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sell_price: Decimal = Field(..., ge=0)
    min_stock_alert: int = Field(0, ge=0)
    description: Optional[str] = None


class ProductFrameCreate(ProductFrameBase):
    initial_stock: Optional[int] = Field(None, ge=0, description="Estoque inicial na loja do usuário")


class ProductFrameUpdate(BaseModel):
    reference_code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sell_price: Optional[Decimal] = Field(None, ge=0)
    min_stock_alert: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class InventoryLevelResponse(BaseModel):
    id: int
    store_id: int
    product_frame_id: int
    quantity: int
    reserved_quantity: int
    store_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductFrameResponse(ProductFrameBase):
    id: int
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    inventory_levels: Optional[list[InventoryLevelResponse]] = None
    
    class Config:
        from_attributes = True
```

#### 3.4. Criar Router

```python
# app/routers/v1/product_frames.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above, require_admin
from app.models.product_frame_model import ProductFrame
from app.models.inventory_level_model import InventoryLevel
from app.models.store_model import Store
from app.models.staff_model import StaffMember
from app.schemas.product_frame_schema import (
    ProductFrameCreate,
    ProductFrameUpdate,
    ProductFrameResponse
)

router = APIRouter(prefix="/product-frames", tags=["product-frames"])


async def get_org_internal_id(db: AsyncSession, clerk_org_id: str) -> int:
    """Obtém o ID interno da organização."""
    from app.models.organization_model import Organization
    result = await db.execute(
        select(Organization).where(Organization.clerk_org_id == clerk_org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(404, "Organização não encontrada")
    return org.id


@router.get("", response_model=List[ProductFrameResponse])
async def list_product_frames(
    q: Optional[str] = Query(None, description="Busca em nome/código/marca"),
    store_id: Optional[int] = Query(None, description="Filtrar por loja"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Lista armações da organização."""
    query = select(ProductFrame).where(
        ProductFrame.organization_id == current_org_id,
        ProductFrame.is_active == True
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                ProductFrame.name.ilike(search_term),
                ProductFrame.reference_code.ilike(search_term),
                ProductFrame.brand.ilike(search_term)
            )
        )
    
    result = await db.execute(query)
    frames = result.scalars().all()
    
    # Se store_id fornecido, adiciona níveis de estoque
    if store_id:
        org_id = await get_org_internal_id(db, current_org_id)
        for frame in frames:
            inv_result = await db.execute(
                select(InventoryLevel).where(
                    InventoryLevel.product_frame_id == frame.id,
                    InventoryLevel.store_id == store_id
                )
            )
            inv = inv_result.scalar_one_or_none()
            if inv:
                frame.inventory_levels = [inv]
    
    return frames


@router.post("", response_model=ProductFrameResponse, status_code=status.HTTP_201_CREATED)
async def create_product_frame(
    frame_data: ProductFrameCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria uma nova armação.
    
    Se `initial_stock` for fornecido, cria registro em inventory_levels
    para a loja do usuário logado.
    """
    # Verifica se código já existe
    existing = await db.execute(
        select(ProductFrame).where(
            ProductFrame.organization_id == current_org_id,
            ProductFrame.reference_code == frame_data.reference_code
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de referência já existe nesta organização"
        )
    
    # Cria armação
    new_frame = ProductFrame(
        **frame_data.model_dump(exclude={"initial_stock"}),
        organization_id=current_org_id
    )
    db.add(new_frame)
    await db.flush()  # Para obter o ID
    
    # Se initial_stock fornecido, cria inventory_level
    if frame_data.initial_stock is not None:
        org_id = await get_org_internal_id(db, current_org_id)
        
        # Usa loja do staff logado
        inv_level = InventoryLevel(
            organization_id=current_org_id,
            store_id=current_staff.store_id,
            product_frame_id=new_frame.id,
            quantity=frame_data.initial_stock
        )
        db.add(inv_level)
    
    await db.commit()
    await db.refresh(new_frame)
    
    return new_frame
```

#### 3.5. Migration

```python
# scripts/migrations/create_products_frames.py
from sqlalchemy import text

async def upgrade():
    # Tabela products_frames
    await db.execute(text("""
        CREATE TABLE products_frames (
            id SERIAL PRIMARY KEY,
            organization_id VARCHAR NOT NULL,
            reference_code VARCHAR(100) NOT NULL,
            name VARCHAR(255) NOT NULL,
            brand VARCHAR(100),
            model VARCHAR(100),
            cost_price NUMERIC(10, 2),
            sell_price NUMERIC(10, 2) NOT NULL,
            min_stock_alert INTEGER DEFAULT 0 NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
    """))
    
    # Índices
    await db.execute(text("""
        CREATE INDEX idx_frame_org_code ON products_frames(organization_id, reference_code);
    """))
    
    await db.execute(text("""
        CREATE UNIQUE INDEX idx_frame_org_code_unique 
        ON products_frames(organization_id, reference_code);
    """))
    
    # Tabela inventory_levels
    await db.execute(text("""
        CREATE TABLE inventory_levels (
            id SERIAL PRIMARY KEY,
            organization_id VARCHAR NOT NULL,
            store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
            product_frame_id INTEGER NOT NULL REFERENCES products_frames(id) ON DELETE CASCADE,
            quantity INTEGER DEFAULT 0 NOT NULL,
            reserved_quantity INTEGER DEFAULT 0 NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
    """))
    
    # Índices
    await db.execute(text("""
        CREATE UNIQUE INDEX idx_inv_store_frame 
        ON inventory_levels(store_id, product_frame_id);
    """))
```

---

### Passo 4: Criar Products Lenses (Lentes)

#### 4.1. Criar Model

```python
# app/models/product_lens_model.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class ProductLens(BaseModel):
    """Model para lentes de óculos."""
    
    __tablename__ = "products_lenses"
    
    organization_id = Column(String, nullable=False, index=True)
    
    # Campos comuns
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    
    # Preços
    cost_price = Column(Numeric(10, 2), nullable=True)
    sell_price = Column(Numeric(10, 2), nullable=False)
    
    # Tipo de lente
    is_lab_order = Column(Boolean, default=False, nullable=False, doc="True = Surfaçagem (laboratório), False = Estoque")
    
    # Tratamentos (para lentes de estoque)
    treatment = Column(String(100), nullable=True, doc="Ex: Anti-reflexo, Blue Light, etc.")
    
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_lens_org_active', 'organization_id', 'is_active'),
    )
```

#### 4.2. Criar Model de Lens Stock Grid

```python
# app/models/lens_stock_grid_model.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class LensStockGrid(BaseModel):
    """Model para grade de estoque de lentes (Esférico x Cilíndrico)."""
    
    __tablename__ = "lens_stock_grid"
    
    organization_id = Column(String, nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_lens_id = Column(Integer, ForeignKey("products_lenses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Graus
    spherical = Column(Numeric(5, 2), nullable=False, doc="Esférico (ex: -2.00)")
    cylindrical = Column(Numeric(5, 2), nullable=False, doc="Cilíndrico (ex: -1.00)")
    axis = Column(Integer, nullable=True, doc="Eixo (0-180)")
    
    # Estoque
    quantity = Column(Integer, default=0, nullable=False)
    
    # Relationships
    store = relationship("Store", backref="lens_stock_grid")
    product_lens = relationship("ProductLens", backref="lens_stock_grid")
    
    __table_args__ = (
        # Garante combinação única
        Index('idx_lens_grid_unique', 'store_id', 'product_lens_id', 'spherical', 'cylindrical', 'axis', unique=True),
    )
```

#### 4.3. Criar Schemas

```python
# app/schemas/product_lens_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class ProductLensBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sell_price: Decimal = Field(..., ge=0)
    is_lab_order: bool = Field(False, description="True = Surfaçagem, False = Estoque")
    treatment: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class LensStockGridCreate(BaseModel):
    spherical: Decimal = Field(..., description="Esférico (ex: -2.00)")
    cylindrical: Decimal = Field(..., description="Cilíndrico (ex: -1.00)")
    axis: Optional[int] = Field(None, ge=0, le=180)
    quantity: int = Field(0, ge=0)


class ProductLensCreate(ProductLensBase):
    initial_stock_grid: Optional[List[LensStockGridCreate]] = Field(
        None, 
        description="Grade inicial de estoque (apenas se is_lab_order = False)"
    )


class ProductLensResponse(ProductLensBase):
    id: int
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### 4.4. Criar Router

```python
# app/routers/v1/product_lenses.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above, require_admin
from app.models.product_lens_model import ProductLens
from app.models.lens_stock_grid_model import LensStockGrid
from app.models.staff_model import StaffMember
from app.schemas.product_lens_schema import (
    ProductLensCreate,
    ProductLensResponse
)

router = APIRouter(prefix="/product-lenses", tags=["product-lenses"])


@router.get("", response_model=List[ProductLensResponse])
async def list_product_lenses(
    is_lab_order: Optional[bool] = Query(None, description="Filtrar por tipo"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Lista lentes da organização."""
    query = select(ProductLens).where(
        ProductLens.organization_id == current_org_id,
        ProductLens.is_active == True
    )
    
    if is_lab_order is not None:
        query = query.where(ProductLens.is_lab_order == is_lab_order)
    
    result = await db.execute(query)
    lenses = result.scalars().all()
    
    return lenses


@router.post("", response_model=ProductLensResponse, status_code=status.HTTP_201_CREATED)
async def create_product_lens(
    lens_data: ProductLensCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_admin),
):
    """
    Cria uma nova lente.
    
    Se is_lab_order = False e initial_stock_grid fornecido,
    cria grade de estoque.
    """
    # Cria lente
    new_lens = ProductLens(
        **lens_data.model_dump(exclude={"initial_stock_grid"}),
        organization_id=current_org_id
    )
    db.add(new_lens)
    await db.flush()
    
    # Se não é lab_order e tem grade inicial, cria estoque
    if not lens_data.is_lab_order and lens_data.initial_stock_grid:
        for grid_item in lens_data.initial_stock_grid:
            grid = LensStockGrid(
                organization_id=current_org_id,
                store_id=current_staff.store_id,
                product_lens_id=new_lens.id,
                **grid_item.model_dump()
            )
            db.add(grid)
    
    await db.commit()
    await db.refresh(new_lens)
    
    return new_lens
```

---

### Passo 5: Criar Customers (Clientes)

#### 5.1. Criar Model

```python
# app/models/customer_model.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Index
from sqlalchemy.orm import relationship
from app.models.base_class import BaseModel


class Customer(BaseModel):
    """Model para clientes."""
    
    __tablename__ = "customers"
    
    organization_id = Column(String, nullable=False, index=True)
    
    # Dados pessoais
    full_name = Column(String(255), nullable=False)
    cpf = Column(String(11), nullable=False, index=True, doc="CPF (11 dígitos, sem formatação)")
    birth_date = Column(Date, nullable=False, doc="Data de nascimento (obrigatório para cálculo de adição)")
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Dados profissionais
    profession = Column(String(100), nullable=True, doc="Profissão (ajuda na venda consultiva)")
    
    # Endereço
    address_street = Column(String(255), nullable=True)
    address_number = Column(String(20), nullable=True)
    address_complement = Column(String(100), nullable=True)
    address_neighborhood = Column(String(100), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(2), nullable=True)
    address_zipcode = Column(String(10), nullable=True)
    
    # Outros
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        # Garante CPF único por organização
        Index('idx_customer_org_cpf', 'organization_id', 'cpf', unique=True),
        Index('idx_customer_org_name', 'organization_id', 'full_name'),
    )
```

#### 5.2. Criar Schemas

```python
# app/schemas/customer_schema.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import date, datetime
import re


class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF (11 dígitos, sem formatação)")
    birth_date: date = Field(..., description="Data de nascimento")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    profession: Optional[str] = Field(None, max_length=100)
    address_street: Optional[str] = Field(None, max_length=255)
    address_number: Optional[str] = Field(None, max_length=20)
    address_complement: Optional[str] = Field(None, max_length=100)
    address_neighborhood: Optional[str] = Field(None, max_length=100)
    address_city: Optional[str] = Field(None, max_length=100)
    address_state: Optional[str] = Field(None, max_length=2)
    address_zipcode: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Remove formatação
        cpf = re.sub(r'[^0-9]', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    profession: Optional[str] = Field(None, max_length=100)
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zipcode: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: int
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerQuickCreate(BaseModel):
    """Schema otimizado para criação rápida via Modal."""
    full_name: str = Field(..., min_length=2, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=11)
    birth_date: date
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('cpf')
    def validate_cpf(cls, v):
        cpf = re.sub(r'[^0-9]', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf
```

#### 5.3. Criar Router

```python
# app/routers/v1/customers.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.core.security import get_current_org_id
from app.core.permissions import require_staff_or_above, require_admin
from app.models.customer_model import Customer
from app.models.staff_model import StaffMember
from app.schemas.customer_schema import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerQuickCreate
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    q: Optional[str] = Query(None, description="Busca em nome/CPF/email"),
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Lista clientes da organização."""
    query = select(Customer).where(
        Customer.organization_id == current_org_id,
        Customer.is_active == True
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Customer.full_name.ilike(search_term),
                Customer.cpf.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        )
    
    result = await db.execute(query)
    customers = result.scalars().all()
    
    return customers


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """Cria um novo cliente."""
    # Verifica se CPF já existe
    existing = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado nesta organização"
        )
    
    new_customer = Customer(
        **customer_data.model_dump(),
        organization_id=current_org_id
    )
    
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    
    return new_customer


@router.post("/quick", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_quick(
    customer_data: CustomerQuickCreate,
    db: AsyncSession = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id),
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    """
    Cria cliente rapidamente (otimizado para Modal na tela de vendas).
    
    Campos mínimos: nome, CPF, data de nascimento, telefone (opcional).
    """
    # Verifica se CPF já existe
    existing = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado nesta organização"
        )
    
    new_customer = Customer(
        full_name=customer_data.full_name,
        cpf=customer_data.cpf,
        birth_date=customer_data.birth_date,
        phone=customer_data.phone,
        organization_id=current_org_id
    )
    
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    
    return new_customer
```

#### 5.4. Migration

```python
# scripts/migrations/create_customers.py
from sqlalchemy import text

async def upgrade():
    await db.execute(text("""
        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            organization_id VARCHAR NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            cpf VARCHAR(11) NOT NULL,
            birth_date DATE NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(20),
            profession VARCHAR(100),
            address_street VARCHAR(255),
            address_number VARCHAR(20),
            address_complement VARCHAR(100),
            address_neighborhood VARCHAR(100),
            address_city VARCHAR(100),
            address_state VARCHAR(2),
            address_zipcode VARCHAR(10),
            notes TEXT,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
    """))
    
    # Índices
    await db.execute(text("""
        CREATE UNIQUE INDEX idx_customer_org_cpf 
        ON customers(organization_id, cpf);
    """))
    
    await db.execute(text("""
        CREATE INDEX idx_customer_org_name 
        ON customers(organization_id, full_name);
    """))
```

---

## 📝 Resumo das Mudanças

### Tabelas Criadas

1. `products_frames` - Armações
2. `inventory_levels` - Estoque por loja
3. `products_lenses` - Lentes
4. `lens_stock_grid` - Grade de estoque de lentes
5. `customers` - Clientes

### Tabelas Modificadas

1. `stores` - Adicionado `address_data` (JSONB) e `tax_rate_machine`
2. `departments` - Adicionado `description`
3. `staff_members` - `store_id` e `department_id` tornados obrigatórios

### Endpoints Criados

- `GET /api/v1/product-frames` - Lista armações
- `POST /api/v1/product-frames` - Cria armação
- `GET /api/v1/product-lenses` - Lista lentes
- `POST /api/v1/product-lenses` - Cria lente
- `GET /api/v1/customers` - Lista clientes
- `POST /api/v1/customers` - Cria cliente
- `POST /api/v1/customers/quick` - Cria cliente rápido (Modal)

### Importante: Multi-tenancy

**TODOS os modelos criados incluem `organization_id`** para garantir isolamento por organização:
- ✅ `products_frames.organization_id`
- ✅ `inventory_levels.organization_id`
- ✅ `products_lenses.organization_id`
- ✅ `lens_stock_grid.organization_id`
- ✅ `customers.organization_id`

**Todas as queries filtram por `organization_id`** extraído do token JWT.

---

**Documento criado em**: 2025-01-XX  
**Status**: Plano de implementação  
**Próximos passos**: Executar migrations e implementar endpoints

