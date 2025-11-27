Master Prompt: Especificação Técnica - API de Gestão de Óticas
Contexto para a IA:
Você atuará como um Engenheiro de Software Sênior especializado em Python/FastAPI. Sua tarefa é estruturar e desenvolver o backend de um sistema SaaS Multi-tenant para gestão de óticas. Abaixo está a documentação completa da arquitetura, regras de negócio e especificações técnicas de implementação.
1. Visão Geral e Stack Tecnológica
Linguagem: Python 3.10+
Framework Web: FastAPI
Banco de Dados: PostgreSQL
ORM: SQLAlchemy (Modo Assíncrono com asyncpg)
Autenticação: Clerk (Gestão de Identidade e Acesso)
Arquitetura: Multi-tenancy Lógico (Schema Compartilhado, dados isolados por organization_id).
2. Estrutura de Diretórios
otica-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # App FastAPI
│   ├── core/
│   │   ├── config.py        # Envs (CLERK_ISSUER, DB_URL)
│   │   ├── security.py      # Lógica de validação do Token Clerk + Extração de org_id
│   │   └── database.py      # SessionManager do SQLAlchemy
│   ├── models/              # Tabelas do Banco
│   │   ├── base_class.py
│   │   └── staff_model.py
│   ├── schemas/             # Pydantic Models
│   │   └── staff_schema.py
│   ├── routers/             # Endpoints
│   │   └── v1/
│   │       └── staff.py
│   └── services/            
├── .env
└── requirements.txt


3. Arquitetura de Segurança e Multi-tenancy
3.1. Autenticação (Clerk)
O frontend gerencia o login e a seleção da organização ativa.
O Backend recebe um Bearer Token (JWT).
O Backend deve validar a assinatura do token usando as chaves públicas (JWKS) do Clerk.
3.2. Regra de Ouro do Isolamento (Tenant Isolation)
Dados: Todas as tabelas de negócio (ex: staff_members, pacientes) DEVEM possuir a coluna organization_id.
Identificação: O organization_id NUNCA deve ser confiado se vier do corpo da requisição. Ele deve ser extraído do claim org_id dentro do Token JWT validado.
Filtragem: Toda query ao banco deve ter a cláusula .where(Model.organization_id == current_org_id).
4. Detalhamento Técnico: Módulo de Gestão de Equipe (Staff)
Este é o primeiro módulo a ser implementado. Ele gerencia os usuários que trabalham dentro de uma ótica.
4.1. Modelo de Banco de Dados (app/models/staff_model.py)
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Index
from app.core.database import Base
import enum

class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    ASSISTANT = "ASSISTANT"

class StaffMember(Base):
    __tablename__ = "staff_members"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, nullable=True, doc="Vínculo com usuário Clerk")
    
    # CRÍTICO: MULTI-TENANCY
    organization_id = Column(String, nullable=False, index=True)

    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True) # Unique por Tenant via index composto
    role = Column(Enum(StaffRole), default=StaffRole.STAFF, nullable=False)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar_url = Column(String, nullable=True)

    __table_args__ = (
        # Garante email único DENTRO da mesma organização
        Index('idx_staff_org_email', 'organization_id', 'email', unique=True),
        Index('idx_staff_org_role', 'organization_id', 'role'),
    )


4.2. Schemas Pydantic (app/schemas/staff_schema.py)
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.staff_model import StaffRole

class StaffBase(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    role: StaffRole
    department: Optional[str] = None
    is_active: bool = True

class StaffCreate(StaffBase):
    # NÃO aceita organization_id (injetado pelo backend)
    pass

class StaffFilter(BaseModel):
    q: Optional[str] = None
    role: Optional[StaffRole] = None

class StaffResponse(StaffBase):
    id: int
    organization_id: str
    class Config:
        from_attributes = True

class StaffStats(BaseModel):
    total_users: int
    active_users: int
    admins: int
    managers: int


4.3. Especificação dos Endpoints (app/routers/v1/staff.py)
Todas as rotas devem injetar a dependência current_org_id.
1. GET /api/v1/staff
Lógica: Listar usuários filtrando por organization_id == current_org_id.
Filtros: Aplicar busca textual (ILIKE) em nome/email se q for fornecido.
2. GET /api/v1/staff/stats
Lógica: Retornar contagens agregadas da organização atual.
SQL Esperado: Usar func.count().filter(...) para retornar total, active, admins, managers em uma única query.
3. POST /api/v1/staff
Lógica: Criar novo membro.
Segurança: Sobrescrever o campo organization_id do modelo com o valor vindo do token (Dependency Injection). O backend ignora qualquer org_id enviado no JSON.
5. Diretrizes de Segurança e Escala
Statelessness: Nenhuma sessão salva em memória ou arquivo local. Tudo via Token.
Environment: Segredos (Chaves do Clerk, DB Password) apenas no .env.
CORS: Configurar para aceitar apenas a origem do frontend.
Tratamento de Erros: Retornar 401 para token inválido e 403 se o token não tiver org_id.
