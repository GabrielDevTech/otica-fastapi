# Tech Context

## Tecnologias Utilizadas
- **Linguagem**: Python 3.14
- **Framework Web**: FastAPI
- **Banco de Dados**: PostgreSQL
- **ORM**: SQLAlchemy (modo assíncrono)
- **Driver DB**: asyncpg
- **Autenticação**: Clerk (JWT via JWKS)
- **Validação**: Pydantic
- **HTTP Client**: httpx (para validação JWKS)

## Setup de Desenvolvimento
1. Python 3.14 instalado
2. PostgreSQL instalado e rodando
3. Conta Clerk configurada
4. Ambiente virtual Python
5. Variáveis de ambiente no `.env`

## Dependências Principais
- `fastapi==0.122.0`: Framework web
- `uvicorn[standard]==0.38.0`: ASGI server
- `sqlalchemy[asyncio]==2.0.44`: ORM assíncrono
- `asyncpg==0.31.0`: Driver PostgreSQL assíncrono
- `pydantic==2.12.4`: Validação de dados
- `pydantic-settings==2.12.0`: Configurações com Pydantic
- `python-jose[cryptography]==3.5.0`: Validação JWT
- `httpx==0.28.1`: Cliente HTTP para JWKS
- `python-dotenv==1.2.1`: Carregamento de .env
- `cryptography==46.0.3`: Criptografia para validação de tokens

**Status**: Todas as dependências instaladas e testadas no ambiente virtual.

## Restrições Técnicas
- Python 3.14 obrigatório
- PostgreSQL obrigatório (não suporta SQLite)
- Clerk obrigatório para autenticação
- Modo assíncrono obrigatório (SQLAlchemy async)

## Ferramentas de Desenvolvimento
- Python 3.14
- PostgreSQL
- FastAPI (com auto-docs em /docs)
- Uvicorn (servidor de desenvolvimento)

## Configurações Importantes
**Variáveis de Ambiente (.env)**:
- `CLERK_ISSUER`: URL do issuer do Clerk (obrigatório)
- `CLERK_PUBLISHABLE_KEY`: Chave pública do Clerk (opcional, para uso futuro)
- `CLERK_SECRET_KEY`: Chave secreta do Clerk (opcional, para uso futuro)
- `DATABASE_URL`: Connection string PostgreSQL (formato: postgresql+asyncpg://user:pass@host:port/dbname)
- `CORS_ORIGINS`: Origens permitidas para CORS (separadas por vírgula)

**Configuração Atual**:
- Clerk: Configurado (thorough-mutt-7.clerk.accounts.dev)
- Database: Supabase PostgreSQL (aws-1-sa-east-1.pooler.supabase.com)
- CORS: localhost:3000, localhost:5173

**Configuração do Database Engine**:
- `statement_cache_size: 0` - Desabilitado para compatibilidade com pgbouncer (Supabase)
- `jit: off` - Desabilitado para compatibilidade
- Todas as queries são assíncronas (async/await)
- Pool de conexões gerenciado automaticamente pelo SQLAlchemy

**Estrutura de Diretórios**:
```
otica-api/
├── app/
│   ├── core/        # Config, security, database
│   ├── models/      # SQLAlchemy models
│   ├── schemas/     # Pydantic schemas
│   ├── routers/     # FastAPI endpoints
│   └── services/    # (Futuro) Lógica de negócio
├── scripts/
│   ├── create_tables.py  # Script para criar tabelas
│   └── verify_config.py  # Script para verificar .env
├── venv/            # Ambiente virtual Python
├── .env             # Variáveis de ambiente (não versionado)
├── .env.example     # Template de variáveis
├── requirements.txt # Dependências do projeto
├── README.md        # Documentação principal
└── CONFIGURACAO.md  # Guia de configuração
```

**Scripts Úteis**:
- `scripts/verify_config.py`: Verifica se as configurações do .env estão corretas
- `scripts/create_tables.py`: Cria todas as tabelas no banco de dados

---

**Nota**: Este documento mantém o contexto técnico necessário para trabalhar no projeto.

