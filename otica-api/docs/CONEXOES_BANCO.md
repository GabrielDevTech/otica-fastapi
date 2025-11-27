# Como Funcionam as Conexões com o Banco de Dados

## Visão Geral

As conexões são gerenciadas pelo **SQLAlchemy Engine** que cria e gerencia um pool de conexões automaticamente. Todas as conexões usam o mesmo `DATABASE_URL` do arquivo `.env`.

## Arquitetura de Conexões

### 1. Engine (Motor de Conexão)

O engine é criado uma vez em `app/core/database.py`:

```python
engine = create_async_engine(
    settings.DATABASE_URL,  # Lê do .env
    echo=True,  # Log SQL queries
    future=True,
)
```

**Características**:
- Pool de conexões automático
- Conexões assíncronas via `asyncpg`
- Reutiliza conexões quando possível
- Gerencia timeouts e reconexões

### 2. Script de Criação de Tabelas (`create_tables.py`)

**Quando executado**: Uma vez, para criar as tabelas no banco.

**Como funciona**:
```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

- Cria uma conexão temporária
- Executa os comandos DDL (CREATE TABLE, etc.)
- Fecha a conexão automaticamente
- **Não é usado durante a execução normal da API**

### 3. Execução Normal da API (Durante Requisições)

**Quando usado**: A cada requisição HTTP que precisa acessar o banco.

**Como funciona**:
```python
# Em app/core/database.py
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Disponibiliza a sessão
        finally:
            await session.close()  # Fecha ao finalizar
```

**Fluxo**:
1. FastAPI chama `get_db()` como dependency
2. Cria uma nova sessão do pool
3. Router usa a sessão para queries
4. Sessão é fechada automaticamente após a requisição

**Exemplo em um router**:
```python
@router.get("/staff")
async def list_staff(
    db: AsyncSession = Depends(get_db),  # ← Dependency injection
    current_org_id: str = Depends(get_current_org_id),
):
    # db é uma sessão ativa do pool
    query = select(StaffMember).where(...)
    result = await db.execute(query)
    return result.scalars().all()
    # Sessão é fechada automaticamente aqui
```

## Resumo

| Situação | Como a Conexão é Feita | Quando |
|----------|------------------------|--------|
| **Criar tabelas** | Script `create_tables.py` usa `engine.begin()` | Uma vez, setup inicial |
| **Requisições API** | Dependency `get_db()` cria sessão do pool | A cada requisição HTTP |
| **Pool de conexões** | Gerenciado automaticamente pelo SQLAlchemy | Sempre ativo |

## Vantagens desta Abordagem

✅ **Pool de conexões**: Reutiliza conexões, melhor performance  
✅ **Assíncrono**: Não bloqueia o servidor durante queries  
✅ **Automático**: SQLAlchemy gerencia tudo  
✅ **Seguro**: Cada requisição tem sua própria sessão isolada  
✅ **Multi-tenant**: Filtragem por `organization_id` garante isolamento  

## Importante

- **Não crie conexões manualmente** - use sempre `get_db()` como dependency
- **Não feche o engine manualmente** - ele é gerenciado pelo FastAPI
- **O script `create_tables.py` é apenas para setup** - não é usado em produção

## Verificação

Para verificar se as tabelas foram criadas:

```sql
-- No PostgreSQL
\dt  -- Lista todas as tabelas
\d staff_members  -- Descreve a tabela staff_members
```

