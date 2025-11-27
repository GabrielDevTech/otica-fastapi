# System Patterns

## Arquitetura do Sistema
**Multi-tenancy Lógico**: Schema compartilhado no PostgreSQL, isolamento de dados via `organization_id` em todas as tabelas de negócio.

**Camadas**:
- **Core**: Configuração, segurança, database
- **Models**: SQLAlchemy ORM (tabelas do banco)
- **Schemas**: Pydantic (validação de entrada/saída)
- **Routers**: Endpoints FastAPI (lógica de API)
- **Services**: (Futuro) Lógica de negócio complexa

## Decisões Técnicas Principais
- **Async/Await**: SQLAlchemy async com asyncpg para melhor performance
- **Dependency Injection**: `current_org_id` injetado via FastAPI dependencies
- **Token Validation**: Validação de JWT Clerk via JWKS (chaves públicas)
- **Indexes**: Indexes compostos para garantir unicidade e performance por tenant

## Padrões de Design em Uso
- **Repository Pattern**: (Futuro) Services para abstrair lógica de negócio
- **Dependency Injection**: FastAPI dependencies para `current_org_id` e validação de token
- **Schema Validation**: Pydantic para validação de entrada/saída
- **Base Model**: Classe base para models com campos comuns

## Relacionamentos entre Componentes
```
main.py → routers → services (futuro)
                ↓
            schemas (validação)
                ↓
            models (ORM)
                ↓
            database (SQLAlchemy)
                ↓
            PostgreSQL
```

**Security Flow**:
1. Request com Bearer Token
2. `core/security.py` valida token via JWKS
3. Extrai `org_id` do token
4. Injeta `current_org_id` como dependency
5. Router usa `current_org_id` para filtrar queries

## Estrutura de Dados
**StaffMember**:
- `id`: Primary key
- `clerk_id`: Vínculo com usuário Clerk (nullable)
- `organization_id`: **CRÍTICO** - isolamento multi-tenant
- `full_name`, `email`, `role`, `department`, `is_active`, `avatar_url`

**Constraints**:
- Email único por organização (index composto)
- `organization_id` obrigatório em todas as tabelas de negócio

## Fluxos Principais
1. **Autenticação**:
   - Frontend → Clerk (login)
   - Clerk → JWT Token
   - Frontend → API com Bearer Token
   - API → Valida token → Extrai `org_id`

2. **CRUD Staff**:
   - GET /api/v1/staff → Lista com filtro por `org_id`
   - POST /api/v1/staff → Cria com `org_id` do token
   - GET /api/v1/staff/stats → Agregações por `org_id`

---

**Nota**: Este documento captura a arquitetura e os padrões técnicos do sistema. Atualize conforme o sistema evolui.

