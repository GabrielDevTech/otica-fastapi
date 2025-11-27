# Como Verificar se as Roles (Enum) Foram Criadas no Banco

## Situação

Você quer verificar se o enum `staffrole` com os valores (ADMIN, MANAGER, STAFF, ASSISTANT) já existe no banco de dados PostgreSQL.

## Métodos de Verificação

### Método 1: Via Script Python (Recomendado)

Crie um script `scripts/verify_roles.py`:

```python
"""Script para verificar se o enum staffrole foi criado."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text


async def verify_roles():
    """Verifica se o enum staffrole existe e quais valores tem."""
    try:
        async with engine.connect() as conn:
            # Verifica se o enum existe
            result = await conn.execute(
                text("""
                    SELECT typname 
                    FROM pg_type 
                    WHERE typname = 'staffrole'
                """)
            )
            
            if result.scalar():
                print("✅ Enum 'staffrole' existe no banco!")
                
                # Lista os valores do enum
                values_result = await conn.execute(
                    text("""
                        SELECT enumlabel 
                        FROM pg_enum 
                        WHERE enumtypid = (
                            SELECT oid 
                            FROM pg_type 
                            WHERE typname = 'staffrole'
                        )
                        ORDER BY enumsortorder
                    """)
                )
                
                values = [row[0] for row in values_result.fetchall()]
                print(f"\n📋 Valores do enum ({len(values)}):")
                for value in values:
                    print(f"   - {value}")
                
                # Valores esperados
                expected = ['ADMIN', 'MANAGER', 'STAFF', 'ASSISTANT']
                missing = [v for v in expected if v not in values]
                extra = [v for v in values if v not in expected]
                
                if missing:
                    print(f"\n⚠️  Valores faltando: {missing}")
                if extra:
                    print(f"\n⚠️  Valores extras: {extra}")
                if not missing and not extra:
                    print("\n✅ Todos os valores esperados estão presentes!")
                    
            else:
                print("❌ Enum 'staffrole' NÃO existe no banco!")
                print("Execute: python scripts/create_tables.py")
                
    except Exception as e:
        print(f"❌ Erro ao verificar roles: {str(e)}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_roles())
```

**Como usar**:
```powershell
.\venv\Scripts\python.exe scripts\verify_roles.py
```

### Método 2: Via SQL Direto (psql ou cliente SQL)

Conecte-se ao banco e execute:

```sql
-- Verificar se o enum existe
SELECT typname 
FROM pg_type 
WHERE typname = 'staffrole';

-- Se existir, listar os valores
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (
    SELECT oid 
    FROM pg_type 
    WHERE typname = 'staffrole'
)
ORDER BY enumsortorder;
```

**Resultado esperado**:
```
 typname
---------
 staffrole

 enumlabel
----------
 ADMIN
 MANAGER
 STAFF
 ASSISTANT
```

### Método 3: Via Script de Verificação de Tabelas

O script `verify_tables.py` já verifica se o enum existe. Você pode executar:

```powershell
.\venv\Scripts\python.exe scripts\verify_tables.py
```

Ele mostra:
```
✅ Enum 'staffrole' criado com sucesso!
```

## O que Acontece Quando Você Muda o Enum?

### Cenário 1: Adicionar Novo Valor

Se você adicionar um novo valor ao enum no código Python:

```python
class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    ASSISTANT = "ASSISTANT"
    NEW_ROLE = "NEW_ROLE"  # ← Novo valor
```

**Problema**: O SQLAlchemy `create_all()` **NÃO atualiza** enums existentes automaticamente!

**Solução**: Você precisa adicionar manualmente no banco:

```sql
ALTER TYPE staffrole ADD VALUE 'NEW_ROLE';
```

### Cenário 2: Remover Valor

**Atenção**: PostgreSQL **NÃO permite** remover valores de enum facilmente!

Se você remover um valor do código, mas ele ainda existir no banco:
- O código pode não funcionar corretamente
- Dados existentes podem ter valores "antigos"

**Solução**: 
1. Migrar dados para outro valor
2. Recriar o enum (complexo, requer downtime)

### Cenário 3: Mudar Nome de Valor

Se você mudar:
```python
# Antes
ADMIN = "ADMIN"

# Depois
ADMINISTRATOR = "ADMINISTRATOR"
```

**Problema**: O valor no banco continua sendo "ADMIN", mas o código espera "ADMINISTRATOR"

**Solução**: 
1. Adicionar novo valor: `ALTER TYPE staffrole ADD VALUE 'ADMINISTRATOR';`
2. Migrar dados: `UPDATE staff_members SET role = 'ADMINISTRATOR' WHERE role = 'ADMIN';`
3. Remover valor antigo (se necessário, complexo)

## Como Verificar se Há Dados Usando o Enum

```sql
-- Ver quantos registros usam cada role
SELECT role, COUNT(*) 
FROM staff_members 
GROUP BY role;

-- Ver todos os valores únicos de role na tabela
SELECT DISTINCT role 
FROM staff_members;
```

## Checklist de Verificação

Quando você fizer mudanças no enum:

- [ ] Verificar se enum existe: `SELECT typname FROM pg_type WHERE typname = 'staffrole';`
- [ ] Listar valores atuais: `SELECT enumlabel FROM pg_enum WHERE enumtypid = ...`
- [ ] Comparar com valores no código Python
- [ ] Verificar se há dados usando valores antigos
- [ ] Se adicionar valor: executar `ALTER TYPE staffrole ADD VALUE 'NOVO_VALOR';`
- [ ] Se remover valor: migrar dados primeiro
- [ ] Testar criação de registros com novos valores

## Resumo

| Pergunta | Resposta |
|----------|----------|
| **Como verificar se existe?** | Script Python ou SQL direto |
| **Onde está o enum?** | PostgreSQL: tipo `staffrole` |
| **Valores esperados?** | ADMIN, MANAGER, STAFF, ASSISTANT |
| **Mudanças são automáticas?** | ❌ Não! Precisa atualizar manualmente |
| **Como adicionar valor?** | `ALTER TYPE staffrole ADD VALUE 'NOVO';` |
| **Como remover valor?** | Complexo, requer migração de dados |

## Quando Executar Verificação

Execute a verificação quando:
- ✅ Iniciar o projeto pela primeira vez
- ✅ Fazer mudanças no enum `StaffRole`
- ✅ Suspeitar que o banco está desatualizado
- ✅ Antes de criar novos registros com roles

---

**Nota**: Este documento é apenas informativo. Execute os scripts quando precisar verificar.

