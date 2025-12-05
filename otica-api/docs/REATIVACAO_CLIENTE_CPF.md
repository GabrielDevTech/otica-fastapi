# Reativação Automática de Cliente por CPF

## Comportamento Implementado

Quando um cliente é cadastrado com um CPF que já existe no banco de dados, o sistema agora:

1. **Se existe cliente ATIVO com o CPF** → ❌ Retorna erro 400 (CPF já cadastrado)
2. **Se existe cliente INATIVO (deletado) com o CPF** → ✅ **Reativa e atualiza** o cliente existente
3. **Se não existe nenhum cliente com o CPF** → ✅ Cria novo cliente

## Por que essa Abordagem?

- ✅ **Mantém histórico**: Não perde dados históricos do cliente
- ✅ **Evita duplicatas**: Não cria múltiplos registros com mesmo CPF
- ✅ **Preserva relacionamentos**: Mantém vínculos com vendas, receitas, etc.
- ✅ **Não precisa alterar banco**: Funciona com o índice único atual

## Fluxo Detalhado

### Cenário 1: Cliente Ativo Existe

```
Request: POST /api/v1/customers
{
  "cpf": "12345678901",
  "full_name": "João Silva",
  ...
}

Situação: Já existe cliente ativo com CPF 12345678901

Response: 400 Bad Request
{
  "detail": "CPF já cadastrado nesta organização"
}
```

### Cenário 2: Cliente Deletado Existe (Reativação)

```
Request: POST /api/v1/customers
{
  "cpf": "47621519800",
  "full_name": "Maria Santos",
  "birth_date": "1990-01-01",
  "phone": "11999999999",
  "email": "maria@email.com",
  ...
}

Situação: Existe cliente INATIVO com CPF 47621519800
  - ID: 4
  - Nome antigo: "Maria da Silva"
  - is_active: False

Ação do Sistema:
  1. Busca cliente inativo com CPF 47621519800
  2. Reativa: is_active = True
  3. Atualiza todos os campos com novos dados
  4. Retorna cliente reativado

Response: 201 Created
{
  "id": 4,  // Mesmo ID do cliente anterior
  "cpf": "47621519800",
  "full_name": "Maria Santos",  // Nome atualizado
  "birth_date": "1990-01-01",
  "phone": "11999999999",
  "email": "maria@email.com",
  "is_active": true,  // Reativado
  "created_at": "2024-01-15T10:00:00",  // Data original mantida
  "updated_at": "2024-12-04T20:30:00"   // Data atualizada
}
```

### Cenário 3: Cliente Não Existe

```
Request: POST /api/v1/customers
{
  "cpf": "99988877766",
  "full_name": "Pedro Oliveira",
  ...
}

Situação: Não existe nenhum cliente com CPF 99988877766

Ação do Sistema:
  1. Cria novo cliente
  2. Retorna cliente criado

Response: 201 Created
{
  "id": 10,  // Novo ID
  "cpf": "99988877766",
  "full_name": "Pedro Oliveira",
  "is_active": true,
  ...
}
```

## Endpoints Afetados

### 1. `POST /api/v1/customers`

**Comportamento:**
- Verifica se existe cliente ativo → Erro se existir
- Verifica se existe cliente inativo → Reativa e atualiza **todos os campos**
- Se não existe → Cria novo

**Campos atualizados na reativação:**
- `full_name`
- `cpf` (mesmo valor, mas atualizado)
- `birth_date`
- `email`
- `phone`
- `profession`
- `address_*` (todos os campos de endereço)
- `notes`
- `is_active` → `True`

### 2. `POST /api/v1/customers/quick`

**Comportamento:**
- Verifica se existe cliente ativo → Erro se existir
- Verifica se existe cliente inativo → Reativa e atualiza **apenas campos do quick create**
- Se não existe → Cria novo

**Campos atualizados na reativação:**
- `full_name`
- `cpf`
- `birth_date`
- `phone`
- `is_active` → `True`

**Campos preservados (não alterados):**
- `email`
- `profession`
- `address_*`
- `notes`
- Outros campos que não fazem parte do quick create

## Exemplo Prático

### Passo 1: Criar Cliente

```http
POST /api/v1/customers
{
  "full_name": "João Silva",
  "cpf": "12345678901",
  "birth_date": "1985-05-15",
  "email": "joao@email.com",
  "phone": "11987654321"
}

Response: 201 Created
{
  "id": 1,
  "full_name": "João Silva",
  "cpf": "12345678901",
  "is_active": true,
  ...
}
```

### Passo 2: Deletar Cliente

```http
DELETE /api/v1/customers/1

Response: 200 OK
{
  "message": "Cliente deletado com sucesso",
  "id": 1
}
```

### Passo 3: Tentar Cadastrar Novamente (Reativação)

```http
POST /api/v1/customers
{
  "full_name": "João da Silva Santos",  // Nome atualizado
  "cpf": "12345678901",  // Mesmo CPF
  "birth_date": "1985-05-15",
  "email": "joao.novo@email.com",  // Email atualizado
  "phone": "11999999999"  // Telefone atualizado
}

Response: 201 Created
{
  "id": 1,  // ✅ MESMO ID (cliente reativado)
  "full_name": "João da Silva Santos",  // ✅ Nome atualizado
  "cpf": "12345678901",
  "email": "joao.novo@email.com",  // ✅ Email atualizado
  "phone": "11999999999",  // ✅ Telefone atualizado
  "is_active": true,  // ✅ Reativado
  "created_at": "2024-01-15T10:00:00",  // ✅ Data original preservada
  "updated_at": "2024-12-04T20:30:00"   // ✅ Data atualizada
}
```

## Vantagens

1. **Histórico Preservado**: O `id` e `created_at` são mantidos
2. **Dados Atualizados**: Informações são atualizadas com os novos dados
3. **Sem Duplicatas**: Não cria múltiplos registros
4. **Compatível com Soft Delete**: Funciona perfeitamente com soft delete
5. **Não Precisa Alterar Banco**: Funciona com estrutura atual

## Observações

- **ID Preservado**: O ID do cliente é mantido na reativação
- **Created At Preservado**: A data de criação original é mantida
- **Updated At Atualizado**: A data de atualização é atualizada automaticamente
- **Relacionamentos Preservados**: Vínculos com outras tabelas (vendas, receitas, etc.) são mantidos

## Arquivos Modificados

- `otica-api/app/routers/v1/customers.py`
  - `create_customer()`: Adicionada lógica de reativação
  - `create_customer_quick()`: Adicionada lógica de reativação

## Testes Recomendados

1. ✅ Criar cliente → Deve criar novo
2. ✅ Deletar cliente → Deve marcar como inativo
3. ✅ Criar cliente com CPF deletado → Deve reativar e atualizar
4. ✅ Criar cliente com CPF ativo → Deve retornar erro 400
5. ✅ Verificar que ID é preservado na reativação
6. ✅ Verificar que created_at é preservado na reativação

