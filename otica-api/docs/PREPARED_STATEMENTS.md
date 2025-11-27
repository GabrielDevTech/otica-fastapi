# Prepared Statements vs Queries Diretas

## O que são Prepared Statements?

**Prepared Statements** são queries SQL que são "preparadas" (compiladas) uma vez e depois reutilizadas com diferentes parâmetros. É como um template que você preenche.

### Exemplo:

```python
# Prepared Statement (com cache)
stmt = await conn.prepare("SELECT * FROM staff_members WHERE organization_id = $1")
result1 = await stmt.fetch("org_123")  # Reutiliza o statement preparado
result2 = await stmt.fetch("org_456")  # Reutiliza novamente
```

```python
# Query Direta (sem cache)
result1 = await conn.fetch("SELECT * FROM staff_members WHERE organization_id = $1", "org_123")
result2 = await conn.fetch("SELECT * FROM staff_members WHERE organization_id = $1", "org_456")
```

## Diferenças

| Aspecto | Prepared Statements | Queries Diretas |
|---------|-------------------|----------------|
| **Performance** | ✅ Mais rápido (compilado uma vez) | ⚠️ Mais lento (compila toda vez) |
| **Segurança** | ✅ Proteção contra SQL injection | ✅ Também seguro (com parâmetros) |
| **Compatibilidade** | ❌ Não funciona com pgbouncer | ✅ Funciona com pgbouncer |
| **Cache** | ✅ Reutiliza statement preparado | ❌ Sem cache |

## Por que o Supabase não suporta Prepared Statements?

O **Supabase usa pgbouncer** como proxy de conexão. O pgbouncer tem dois modos:

1. **Transaction mode**: Conexões são compartilhadas entre transações
2. **Statement mode**: Conexões são compartilhadas entre statements

**Problema**: Prepared statements são armazenados **na conexão**. Quando o pgbouncer reutiliza uma conexão para outra requisição, o prepared statement já existe e causa erro:

```
DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_1__" already exists
```

## Nossa Configuração

No `app/core/database.py`, configuramos:

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={
        "statement_cache_size": 0,  # Desabilita cache de prepared statements
    },
)
```

### O que isso significa?

- ✅ **Queries são assíncronas** (usando `async/await`)
- ✅ **Funciona com pgbouncer** (Supabase)
- ⚠️ **Sem cache de prepared statements** (compila toda vez)
- ✅ **Ainda é seguro** (SQLAlchemy usa parâmetros)

## Performance

### Com Prepared Statements (não funciona no Supabase):
- Primeira query: ~10ms (compila)
- Queries seguintes: ~2ms (reutiliza)

### Sem Prepared Statements (nossa configuração):
- Todas as queries: ~5ms (compila toda vez)

**Impacto**: A diferença é mínima (~3ms por query). Para a maioria das aplicações, isso é imperceptível.

## Resumo

| Pergunta | Resposta |
|----------|----------|
| **As queries são assíncronas?** | ✅ Sim, todas usam `async/await` |
| **Usamos prepared statements?** | ❌ Não, por compatibilidade com pgbouncer |
| **Isso afeta a segurança?** | ❌ Não, SQLAlchemy ainda usa parâmetros |
| **Isso afeta muito a performance?** | ❌ Não, diferença mínima (~3ms) |
| **Funciona com Supabase?** | ✅ Sim, perfeitamente! |

## Conclusão

**Todas as queries são assíncronas**, mas não usamos prepared statements por compatibilidade com o pgbouncer do Supabase. Isso é uma limitação do ambiente (Supabase), não do nosso código. A performance ainda é excelente e a segurança é mantida.

