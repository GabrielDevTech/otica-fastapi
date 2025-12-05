# Correção: Soft Delete de Customers

## Problema Identificado

O endpoint `DELETE /api/v1/customers/{customer_id}` estava funcionando corretamente (retornando 204 No Content após soft delete), mas havia duas inconsistências:

**Problema 1**: Os endpoints `GET` e `PATCH` não filtravam por `is_active == True`, permitindo que clientes deletados (soft delete) ainda fossem acessados ou atualizados.

**Problema 2**: A validação de CPF único nos endpoints `POST` não considerava `is_active`, impedindo cadastrar um novo cliente com CPF de um cliente já deletado.

### Comportamento Anterior

```python
# GET /api/v1/customers/{customer_id}
# ❌ Não filtrava por is_active
select(Customer).where(
    Customer.id == customer_id,
    Customer.organization_id == current_org_id
    # Faltava: Customer.is_active == True
)

# PATCH /api/v1/customers/{customer_id}
# ❌ Não filtrava por is_active
select(Customer).where(
    Customer.id == customer_id,
    Customer.organization_id == current_org_id
    # Faltava: Customer.is_active == True
)
```

### Impacto

1. **Frontend**: Após deletar um cliente, ele ainda aparecia ao buscar pelo ID
2. **Inconsistência**: `GET /api/v1/customers` (lista) filtrava por `is_active`, mas `GET /api/v1/customers/{id}` não
3. **Possível erro**: Frontend tentando atualizar um cliente já deletado
4. **Bloqueio de cadastro**: Não era possível cadastrar novo cliente com CPF de cliente deletado (ex: CPF `47621519800`)

## Solução Implementada

### Correções Aplicadas

1. **GET /api/v1/customers/{customer_id}**: Agora filtra por `is_active == True`
2. **PATCH /api/v1/customers/{customer_id}**: Agora filtra por `is_active == True`
3. **POST /api/v1/customers**: Validação de CPF único agora considera apenas `is_active == True`
4. **POST /api/v1/customers/quick**: Validação de CPF único agora considera apenas `is_active == True`
5. **PATCH /api/v1/customers/{customer_id}**: Validação de CPF único ao atualizar CPF considera apenas clientes ativos

### Código Corrigido

```python
# GET /api/v1/customers/{customer_id}
@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(...):
    """Obtém um cliente específico (apenas clientes ativos)."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id,
            Customer.is_active == True  # ✅ Adicionado
        )
    )
    # ...

# PATCH /api/v1/customers/{customer_id}
@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(...):
    """Atualiza um cliente (apenas clientes ativos)."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id,
            Customer.is_active == True  # ✅ Adicionado
        )
    )
    # ...
    # Se CPF está sendo atualizado, valida apenas clientes ativos
    if "cpf" in update_data and update_data["cpf"] != customer.cpf:
        existing_cpf = await db.execute(
            select(Customer).where(
                Customer.organization_id == current_org_id,
                Customer.cpf == update_data["cpf"],
                Customer.is_active == True,  # ✅ Considera apenas ativos
                Customer.id != customer_id
            )
        )
    # ...
```

# POST /api/v1/customers
@router.post("", response_model=CustomerResponse)
async def create_customer(...):
    """Cria um novo cliente."""
    # Verifica se CPF já existe (apenas clientes ativos)
    existing = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf,
            Customer.is_active == True  # ✅ Adicionado
        )
    )
    # ...

# POST /api/v1/customers/quick
@router.post("/quick", response_model=CustomerResponse)
async def create_customer_quick(...):
    """Cria cliente rapidamente."""
    # Verifica se CPF já existe (apenas clientes ativos)
    existing = await db.execute(
        select(Customer).where(
            Customer.organization_id == current_org_id,
            Customer.cpf == customer_data.cpf,
            Customer.is_active == True  # ✅ Adicionado
        )
    )
    # ...
```

### DELETE (Mantido como estava)

O endpoint `DELETE` não precisa filtrar por `is_active` porque:
- Permite idempotência (deletar um cliente já deletado não causa erro)
- Retorna 404 apenas se o cliente não existir ou não pertencer à organização

```python
# DELETE /api/v1/customers/{customer_id}
@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(...):
    """Desativa um cliente (soft delete)."""
    # Não filtra por is_active - permite deletar novamente (idempotência)
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == current_org_id
        )
    )
    # ...
    customer.is_active = False
    await db.commit()
```

## Comportamento Esperado Agora

### Fluxo Completo

1. **Criar cliente**: `POST /api/v1/customers` → Cliente criado com `is_active = True`
2. **Listar clientes**: `GET /api/v1/customers` → Retorna apenas `is_active == True`
3. **Buscar cliente**: `GET /api/v1/customers/{id}` → Retorna apenas se `is_active == True`
4. **Atualizar cliente**: `PATCH /api/v1/customers/{id}` → Funciona apenas se `is_active == True`
5. **Deletar cliente**: `DELETE /api/v1/customers/{id}` → Define `is_active = False`
6. **Após deletar**: 
   - `GET /api/v1/customers` → Cliente não aparece mais na lista
   - `GET /api/v1/customers/{id}` → Retorna 404 (cliente não encontrado)
   - `PATCH /api/v1/customers/{id}` → Retorna 404 (cliente não encontrado)
   - **Novo cadastro com mesmo CPF**: `POST /api/v1/customers` → ✅ Permite cadastrar (CPF de cliente deletado não bloqueia)

## Testes Recomendados

### Frontend

1. **Teste de Deleção**:
   ```javascript
   // Deletar cliente
   await fetch(`/api/v1/customers/${id}`, { method: 'DELETE' });
   
   // Tentar buscar após deletar
   const response = await fetch(`/api/v1/customers/${id}`);
   // Esperado: 404 Not Found
   ```

2. **Teste de Atualização após Deletar**:
   ```javascript
   // Deletar cliente
   await fetch(`/api/v1/customers/${id}`, { method: 'DELETE' });
   
   // Tentar atualizar após deletar
   const response = await fetch(`/api/v1/customers/${id}`, {
     method: 'PATCH',
     body: JSON.stringify({ full_name: 'Novo Nome' })
   });
   // Esperado: 404 Not Found
   ```

### Backend (via Swagger/Postman)

1. Criar um cliente com CPF `47621519800`
2. Buscar o cliente pelo ID → Deve retornar 200
3. Deletar o cliente → Deve retornar 204
4. Buscar o cliente pelo ID novamente → Deve retornar 404
5. Tentar atualizar o cliente → Deve retornar 404
6. **Criar novo cliente com CPF `47621519800`** → ✅ Deve permitir (cliente anterior deletado)

## Observações

- **Soft Delete**: O cliente não é removido fisicamente do banco, apenas marcado como `is_active = False`
- **Restauração**: Se necessário restaurar um cliente, seria preciso criar um endpoint específico ou fazer um `PATCH` direto no banco
- **Consistência**: Agora todos os endpoints de leitura/atualização respeitam o `is_active == True`

## Arquivos Modificados

- `otica-api/app/routers/v1/customers.py`
  - `get_customer()`: Adicionado filtro `is_active == True`
  - `update_customer()`: Adicionado filtro `is_active == True` + validação de CPF único considerando apenas ativos
  - `create_customer()`: Validação de CPF único agora considera apenas `is_active == True`
  - `create_customer_quick()`: Validação de CPF único agora considera apenas `is_active == True`

