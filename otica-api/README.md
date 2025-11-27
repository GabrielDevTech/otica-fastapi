# Otica API

Sistema SaaS Multi-tenant para gestão de óticas.

## Stack Tecnológica

- **Python**: 3.14
- **Framework**: FastAPI
- **Banco de Dados**: PostgreSQL
- **ORM**: SQLAlchemy (async)
- **Autenticação**: Clerk (JWT)

## Setup

### 1. Instalar dependências

```bash
cd otica-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite `.env` com suas configurações:
- `CLERK_ISSUER`: URL do seu Clerk (ex: https://your-clerk.clerk.accounts.dev)
- `DATABASE_URL`: Connection string do PostgreSQL
- `CORS_ORIGINS`: Origens permitidas (separadas por vírgula)

### 3. Configurar banco de dados

Crie o banco de dados PostgreSQL:

```sql
CREATE DATABASE otica_db;
```

### 4. Criar tabelas

Execute o script de criação das tabelas (ou use Alembic para migrations):

```python
# scripts/create_tables.py (criar se necessário)
from app.core.database import engine, Base
from app.models import staff_model
import asyncio

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())
```

### 5. Executar servidor

```bash
uvicorn app.main:app --reload
```

A API estará disponível em:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estrutura do Projeto

```
otica-api/
├── app/
│   ├── core/           # Config, security, database
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── routers/         # FastAPI endpoints
│   └── main.py         # App FastAPI
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

## Endpoints

### Staff (Equipe)

- `GET /api/v1/staff` - Lista membros da equipe
- `GET /api/v1/staff/stats` - Estatísticas da equipe
- `POST /api/v1/staff` - Cria novo membro

Todas as rotas requerem autenticação via Bearer Token (Clerk JWT).

## Segurança

- **Multi-tenancy**: Dados isolados por `organization_id` extraído do token JWT
- **Validação**: Tokens validados via JWKS do Clerk
- **Isolamento**: `organization_id` nunca aceito do corpo da requisição, sempre do token

## Desenvolvimento

Para desenvolvimento com hot-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

