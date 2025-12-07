# Registro do Projeto - Supermemory

## Informações do Projeto

**Nome do Projeto**: Otica API - Sistema SaaS Multi-tenant para Gestão de Óticas

**Tipo**: Backend API RESTful

**Status**: Em desenvolvimento ativo - Fase 2 concluída

---

## Visão Geral

Sistema SaaS Multi-tenant para gestão completa de óticas, desenvolvido em Python/FastAPI com arquitetura de isolamento lógico de dados por organização. O sistema permite que múltiplas óticas gerenciem suas operações de forma isolada e segura através de uma única instância da aplicação.

---

## Stack Tecnológica

- **Linguagem**: Python 3.14
- **Framework Web**: FastAPI 0.123.9
- **Banco de Dados**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0.44 (modo assíncrono)
- **Driver DB**: asyncpg 0.31.0
- **Autenticação**: Clerk (JWT via JWKS)
- **Validação**: Pydantic 2.12.5
- **Servidor**: Uvicorn 0.38.0

---

## Arquitetura

### Multi-tenancy Lógico
- Schema compartilhado no PostgreSQL
- Isolamento de dados via `organization_id` em todas as tabelas de negócio
- `organization_id` extraído do token JWT (nunca confiado do corpo da requisição)

### Estrutura de Camadas
```
main.py → routers → services (futuro)
                ↓
            schemas (validação Pydantic)
                ↓
            models (SQLAlchemy ORM)
                ↓
            database (SQLAlchemy async)
                ↓
            PostgreSQL
```

### Segurança
- Validação de tokens JWT Clerk via JWKS (chaves públicas)
- RBAC (Role-Based Access Control) com roles: ADMIN, MANAGER, STAFF, ASSISTANT, SELLER, LAB
- Dependency Injection para `current_org_id` e `current_staff`
- CORS configurado para origens específicas

---

## Módulos Implementados

### Fase 1 - Alicerces (Concluída)
- ✅ Autenticação Clerk (JWT)
- ✅ Multi-tenancy (isolamento por organização)
- ✅ Gestão de Equipe (Staff)
- ✅ Gestão de Lojas (Stores)
- ✅ Gestão de Departamentos (Departments)
- ✅ Gestão de Clientes (Customers)
- ✅ Produtos (Frames e Lenses)
- ✅ Controle de Acesso (RBAC)

### Fase 2 - Ciclo de Venda (Concluída)
- ✅ **Cash Sessions**: Apoio de caixa (abrir/fechar, auditoria)
- ✅ **Cash Movements**: Sangria e suprimento
- ✅ **Service Orders**: Ordens de serviço (OS) com itens
- ✅ **Sales/Checkout**: Processamento de pagamentos
- ✅ **Lab Queue**: Fila Kanban para laboratório
- ✅ **Products Search**: Busca unificada de produtos
- ✅ **Receivable Accounts**: Contas a receber
- ✅ **Kardex**: Histórico de movimentação de estoque

---

## Estrutura de Diretórios

```
projeto-otica/
├── otica-api/              # Backend API
│   ├── app/
│   │   ├── core/          # Config, security, database, permissions
│   │   ├── models/        # SQLAlchemy models (17 models)
│   │   ├── schemas/       # Pydantic schemas (14 schemas)
│   │   ├── routers/       # FastAPI endpoints (17 routers)
│   │   └── services/      # Lógica de negócio (futuro)
│   ├── scripts/           # Scripts de migração e utilitários
│   ├── docs/             # Documentação técnica (30+ documentos)
│   └── requirements.txt
├── memory-bank/           # Documentação do projeto
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   ├── activeContext.md
│   └── progress.md
└── README.md
```

---

## Endpoints Principais

### Fase 1
- `/api/v1/staff` - Gestão de equipe
- `/api/v1/stores` - Gestão de lojas
- `/api/v1/departments` - Gestão de departamentos
- `/api/v1/customers` - Gestão de clientes
- `/api/v1/product-frames` - Gestão de armações
- `/api/v1/product-lenses` - Gestão de lentes

### Fase 2
- `/api/v1/cash-sessions` - Sessões de caixa (6 endpoints)
- `/api/v1/cash-movements` - Movimentações de caixa (2 endpoints)
- `/api/v1/service-orders` - Ordens de serviço (8 endpoints)
- `/api/v1/products/search` - Busca unificada
- `/api/v1/sales/{id}/checkout` - Checkout/pagamento
- `/api/v1/lab/queue` - Fila de laboratório
- `/api/v1/receivable-accounts` - Contas a receber
- `/api/v1/kardex` - Histórico de movimentação

**Total**: 21 endpoints na Fase 2

---

## Padrões e Convenções

### Nomenclatura
- Models: `snake_case` (ex: `cash_session_model.py`)
- Schemas: `snake_case` (ex: `cash_session_schema.py`)
- Routers: `snake_case` (ex: `cash_sessions.py`)
- Endpoints: `kebab-case` (ex: `/cash-sessions`)

### Multi-tenancy
- Todas as tabelas de negócio têm `organization_id`
- `organization_id` sempre extraído do token JWT
- Nunca aceitar `organization_id` do corpo da requisição

### Soft Delete
- Uso de `is_active` em vez de deleção física
- Endpoints filtram automaticamente por `is_active = True`

### Respostas HTTP
- DELETE retorna `200 OK` com JSON (não `204`) para compatibilidade com Next.js proxy

---

## Regras de Negócio Importantes

### Reserva de Estoque
- Armações: Reserva automática ao adicionar na OS
- Lentes: Validação via `lens_stock_grid` ou marca `needs_purchasing = true`
- Liberação: Ao remover item, cancelar OS, ou fechar venda

### Controle de Desconto
- Limite padrão: 10% (`max_discount_allowed`)
- Desconto > limite: Requer aprovação de MANAGER/ADMIN

### Pagamentos
- **CASH**: Requer sessão de caixa aberta
- **CARD**: Calcula taxa automaticamente (`store.tax_rate_machine`)
- **PIX/CREDIT**: Cria `ReceivableAccount` automaticamente (vencimento: 30 dias)

### Status de OS
- `DRAFT` → `PENDING` → `PAID` → `AWAITING_LENS` → `IN_PRODUCTION` → `READY` → `DELIVERED`
- Transições validadas pelo backend

---

## Estado Atual

### ✅ Concluído
- Fase 1: Alicerces (autenticação, staff, stores, departments, customers, produtos)
- Fase 2: Ciclo de venda completo (21 endpoints)
- Migrações: Todas as tabelas criadas
- Documentação: Completa para backend e frontend

### 🔧 Em Correção
- Relacionamento `Sale` ↔ `ReceivableAccount` (corrigido com `backref`)

### ⏳ Próximos Passos
- Testes dos endpoints da Fase 2
- Integração com frontend
- Fase 3: Módulo financeiro (lançamentos, comissões)

---

## Documentação

### Para Desenvolvedores
- `memory-bank/` - Documentação completa do projeto
- `otica-api/docs/` - Documentação técnica (30+ arquivos)
- `ENDPOINTS_FRONTEND_FASE2.md` - Guia completo para frontend

### Principais Documentos
- `planejamento_estrutura2.md` - Planejamento detalhado da Fase 2
- `PASSO_A_PASSO_FASE2.md` - Progresso da implementação
- `CHECKLIST_FASE2.md` - Checklist de verificação

---

## Configuração

### Variáveis de Ambiente (.env)
```
CLERK_ISSUER=https://thorough-mutt-7.clerk.accounts.dev
DATABASE_URL=postgresql+asyncpg://...
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Banco de Dados
- Supabase PostgreSQL
- Configurado para pgbouncer (`statement_cache_size: 0`)
- Modo assíncrono obrigatório

---

## Desafios Resolvidos

1. **Multi-tenancy**: Isolamento seguro por `organization_id`
2. **CORS/Proxy**: Compatibilidade com Next.js proxy (DELETE retorna 200 OK)
3. **Soft Delete**: Reativação de clientes por CPF
4. **Relacionamentos**: Correção de relacionamentos bidirecionais SQLAlchemy

---

## Contato e Suporte

- **Repositório**: GitHub (branch `gabrielteste`)
- **Documentação**: `/docs` no Swagger UI
- **Status**: ✅ API funcional e pronta para testes

---

**Última Atualização**: 2024-12-04
**Versão**: 1.0.0 (Fase 2)

