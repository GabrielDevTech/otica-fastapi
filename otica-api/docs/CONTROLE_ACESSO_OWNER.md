# Controle de Acesso - Sistema Owner/Super Admin

## 📋 Índice

1. [Sistema Atual de Controle de Acesso](#sistema-atual-de-controle-de-acesso)
2. [Proposta: Sistema Owner/Super Admin](#proposta-sistema-ownersuper-admin)
3. [Arquitetura Técnica Proposta](#arquitetura-técnica-proposta)
4. [Impactos no Sistema Atual](#impactos-no-sistema-atual)
5. [Fluxos de Negócio](#fluxos-de-negócio)
6. [Implementação Futura](#implementação-futura)
7. [Considerações de Segurança](#considerações-de-segurança)

---

## 🔐 Sistema Atual de Controle de Acesso

### Estrutura Atual

O sistema atual utiliza **Role-Based Access Control (RBAC)** com 4 níveis hierárquicos:

```
ADMIN > MANAGER > STAFF > ASSISTANT
```

### Roles Existentes

1. **ADMIN**: Acesso total à organização
   - Pode criar/editar/deletar staff
   - Pode gerenciar lojas e setores
   - Pode aprovar/rejeitar solicitações de acesso
   - Pode enviar convites diretos

2. **MANAGER**: Acesso a gestão e relatórios
   - Pode visualizar estatísticas
   - Pode listar staff, lojas e setores
   - Não pode criar/editar/deletar

3. **STAFF**: Acesso básico de funcionário
   - Pode visualizar dados da organização
   - Acesso somente leitura

4. **ASSISTANT**: Acesso limitado
   - Acesso mínimo (não implementado ainda)

### Limitações do Sistema Atual

1. **Isolamento por Organização**: Cada usuário pertence a apenas uma organização
2. **Sem Criação de Organizações**: Não há endpoint para criar organizações
3. **Sem Super Admin**: Não existe usuário que possa acessar múltiplas organizações
4. **Dependência do Token**: O `organization_id` vem sempre do token JWT

### Como Funciona Atualmente

```python
# 1. Token JWT contém organization_id
token_data = verify_token()  # Extrai org_id do token

# 2. Todas as queries filtram por organization_id
query = select(StaffMember).where(
    StaffMember.organization_id == current_org_id
)

# 3. Validação de permissões por role
current_staff = get_current_staff()  # Busca staff na organização do token
require_admin(current_staff)  # Verifica se é ADMIN
```

**Problema**: Se um usuário precisa acessar múltiplas organizações, ele precisa:
- Ter múltiplas contas no Clerk
- Fazer login em cada organização separadamente
- Não há forma de gerenciar todas as organizações de um único lugar

---

## 👑 Proposta: Sistema Owner/Super Admin

### Conceito

Criar um novo tipo de usuário **OWNER** que:

1. **Pode acessar qualquer organização** (não limitado ao `organization_id` do token)
2. **Tem uma organização principal** (sua organização padrão)
3. **Pode criar novas organizações** via API
4. **Pode gerenciar todas as organizações** do sistema
5. **Tem permissões de ADMIN em todas as organizações** que acessar

### Casos de Uso

1. **Administrador da Plataforma**: Pessoa responsável por criar e gerenciar organizações
2. **Suporte Técnico**: Acesso para resolver problemas em qualquer organização
3. **Auditoria**: Acesso para auditorias e relatórios globais
4. **Multi-tenant Owner**: Dono de uma rede de óticas que gerencia múltiplas organizações

### Hierarquia Proposta

```
OWNER (Super Admin)
  └─ Pode acessar qualquer organização
  └─ Pode criar organizações
  └─ Tem permissões de ADMIN em todas as orgs

ADMIN (por organização)
  └─ Acesso total à sua organização
  └─ Não pode criar outras organizações

MANAGER > STAFF > ASSISTANT
  └─ (mantém como está)
```

---

## 🏗️ Arquitetura Técnica Proposta

### ⚠️ 0. Considerações sobre Row Level Security (RLS)

**O que é RLS?**
Row Level Security (RLS) é um recurso do PostgreSQL que permite criar políticas de segurança que filtram automaticamente as linhas retornadas por queries baseado em condições definidas.

**Problema com Owner e RLS**:
Se o banco de dados usa RLS para isolar dados por `organization_id`, as políticas normalmente fazem algo como:

```sql
-- Policy típica (sem suporte a owner)
CREATE POLICY staff_members_org_isolation ON staff_members
  FOR ALL
  USING (organization_id = current_setting('app.current_org_id', TRUE));
```

**O que acontece com Owner?**:
1. Owner pode não ter `organization_id` no token (ou ter `null`)
2. Owner precisa acessar **todas** as organizações
3. RLS bloqueia queries porque `organization_id` não corresponde
4. Resultado: Owner não consegue acessar dados mesmo tendo permissão

**Solução**:
As políticas RLS precisam ser modificadas para:
1. Verificar se o usuário é owner
2. Se for owner, **bypassar** o filtro de `organization_id`
3. Se não for owner, aplicar filtro normal

**Como implementar**:
- Usar função `is_owner()` que consulta tabela `owners`
- Modificar policies para incluir condição: `is_owner() OR organization_id = ...`
- Definir variáveis de sessão (`SET LOCAL`) antes das queries

**Importante**: Tanto a Opção A quanto a Opção B precisam lidar com RLS. A Opção B é mais segura porque a verificação de owner acontece no banco, não dependendo de claims do token.

---

### 1. Novo Model: Owner

**Tabela**: `owners`

```python
class Owner(BaseModel):
    """Model para Owners (Super Admins)."""
    
    __tablename__ = "owners"
    
    clerk_id = Column(String, unique=True, nullable=False)
    primary_organization_id = Column(String, nullable=True)  # Org principal (opcional)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    can_create_organizations = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Características**:
- **Não tem `organization_id`**: Owner não pertence a uma organização específica
- **`primary_organization_id`**: Organização padrão (opcional, para UI)
- **`can_create_organizations`**: Flag para controlar criação de orgs
- **Email único global**: Diferente de StaffMember que é único por org

### 2. Modificação no Sistema de Autenticação

#### ⚠️ IMPORTANTE: Row Level Security (RLS) do PostgreSQL

**Problema**: Se o banco de dados usa RLS (Row Level Security), as políticas normalmente filtram por `organization_id` baseado no usuário da sessão. Quando um OWNER acessa o sistema:

1. **Token pode ter `org_id: null`** (se owner não está em nenhuma org específica)
2. **RLS bloqueia queries** porque não encontra `organization_id` válido
3. **Queries retornam vazias** mesmo com permissões corretas

**Solução**: É necessário configurar o RLS para reconhecer owners e permitir acesso a todas as organizações.

---

#### Opção A: Owner via Token Custom Claim

Adicionar claim customizado no token JWT do Clerk:

```python
# No payload do token:
{
  "sub": "user_xxx",
  "org_id": "org_xxx",  # Organização atual (pode ser null para owner)
  "is_owner": true,     # Novo claim
  "owner_id": "owner_xxx"  # ID do owner (se for owner)
}
```

**Vantagens**:
- Informação vem direto do token
- Não precisa consultar banco para verificar se é owner
- Pode ser usado diretamente no RLS do PostgreSQL

**Desvantagens**:
- Requer configuração no Clerk (custom claims)
- Token pode ficar maior
- **RLS precisa ser configurado para reconhecer `is_owner`**

**Como Resolver o RLS na Opção A**:

1. **Configurar RLS no PostgreSQL** para verificar se usuário é owner:

```sql
-- Função para verificar se usuário é owner
CREATE OR REPLACE FUNCTION is_owner(user_clerk_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM owners 
    WHERE clerk_id = user_clerk_id 
    AND is_active = TRUE
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Policy para staff_members (exemplo)
CREATE POLICY staff_members_org_isolation ON staff_members
  FOR ALL
  USING (
    -- Se for owner, permite acesso a todas as organizações
    is_owner(current_setting('app.current_user_clerk_id', TRUE))
    OR
    -- Se não for owner, filtra por organization_id
    organization_id = current_setting('app.current_org_id', TRUE)
  );

-- Policy para organizations (exemplo)
CREATE POLICY organizations_owner_access ON organizations
  FOR ALL
  USING (
    -- Owner pode acessar todas
    is_owner(current_setting('app.current_user_clerk_id', TRUE))
    OR
    -- Staff normal não acessa diretamente (via staff_members)
    FALSE
  );
```

2. **No código Python**, definir variáveis de sessão antes das queries:

```python
async def get_db() -> AsyncSession:
    """Dependency para obter sessão do banco de dados."""
    async with AsyncSessionLocal() as session:
        try:
            # Define variáveis de sessão para RLS
            token_data = await verify_token()  # Já validado anteriormente
            
            # Define clerk_id na sessão
            await session.execute(
                text(f"SET LOCAL app.current_user_clerk_id = '{token_data['user_id']}'")
            )
            
            # Define org_id na sessão (pode ser null para owner)
            org_id = token_data.get("org_id") or ""
            await session.execute(
                text(f"SET LOCAL app.current_org_id = '{org_id}'")
            )
            
            # Se for owner (is_owner = true no token), define flag
            if token_data.get("is_owner"):
                await session.execute(
                    text("SET LOCAL app.is_owner = 'true'")
                )
            
            yield session
        finally:
            await session.close()
```

3. **Alternativa mais simples**: Desabilitar RLS para owners e usar apenas filtros no código:

```sql
-- Desabilitar RLS para queries de owner (não recomendado para produção)
-- Melhor: criar policy que permite tudo para owner
CREATE POLICY bypass_rls_for_owner ON staff_members
  FOR ALL
  USING (
    is_owner(current_setting('app.current_user_clerk_id', TRUE))
  )
  WITH CHECK (
    is_owner(current_setting('app.current_user_clerk_id', TRUE))
  );
```

**Recomendação para Opção A**: Usar variáveis de sessão (`SET LOCAL`) para passar informações do token para o RLS, permitindo que as policies verifiquem se o usuário é owner.

---

#### Opção B: Owner via Consulta ao Banco

Verificar se `clerk_id` existe na tabela `owners`:

```python
async def get_current_user_type(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserType:
    """Retorna se usuário é OWNER ou STAFF."""
    
    # 1. Verifica se é owner
    owner_result = await db.execute(
        select(Owner).where(
            Owner.clerk_id == current_user_id,
            Owner.is_active == True
        )
    )
    owner = owner_result.scalar_one_or_none()
    
    if owner:
        return UserType.OWNER
    
    # 2. Se não é owner, é staff normal
    return UserType.STAFF
```

**Vantagens**:
- Não requer mudanças no Clerk
- Mais flexível (pode adicionar flags no banco)
- **RLS pode consultar tabela `owners` diretamente**

**Desvantagens**:
- Query extra em cada requisição
- Pode ser otimizado com cache

**Como Resolver o RLS na Opção B**:

1. **Configurar RLS no PostgreSQL** para consultar tabela `owners`:

```sql
-- Função para verificar se usuário é owner (mesma da Opção A)
CREATE OR REPLACE FUNCTION is_owner(user_clerk_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM owners 
    WHERE clerk_id = user_clerk_id 
    AND is_active = TRUE
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Policy para staff_members
CREATE POLICY staff_members_org_isolation ON staff_members
  FOR ALL
  USING (
    -- Se for owner, permite acesso a todas as organizações
    is_owner(current_setting('app.current_user_clerk_id', TRUE))
    OR
    -- Se não for owner, filtra por organization_id
    organization_id = current_setting('app.current_org_id', TRUE)
  );

-- Policy para organizations
CREATE POLICY organizations_owner_access ON organizations
  FOR ALL
  USING (
    -- Owner pode acessar todas
    is_owner(current_setting('app.current_user_clerk_id', TRUE))
    OR
    -- Staff normal não acessa diretamente
    FALSE
  );
```

2. **No código Python**, definir variáveis de sessão antes das queries:

```python
async def get_db() -> AsyncSession:
    """Dependency para obter sessão do banco de dados."""
    async with AsyncSessionLocal() as session:
        try:
            # Define variáveis de sessão para RLS
            token_data = await verify_token()
            current_user_id = token_data['user_id']
            current_org_id = token_data.get("org_id") or ""
            
            # Define clerk_id na sessão
            await session.execute(
                text(f"SET LOCAL app.current_user_clerk_id = '{current_user_id}'")
            )
            
            # Define org_id na sessão
            await session.execute(
                text(f"SET LOCAL app.current_org_id = '{current_org_id}'")
            )
            
            # RLS vai consultar tabela owners usando is_owner()
            # Não precisa definir flag adicional
            
            yield session
        finally:
            await session.close()
```

3. **Vantagem da Opção B**: A função `is_owner()` consulta a tabela `owners` diretamente, então não precisa passar informação adicional do token. O RLS verifica automaticamente se o `clerk_id` da sessão existe na tabela `owners`.

**Recomendação para Opção B**: Usar função `is_owner()` que consulta a tabela `owners` diretamente. Mais seguro porque a verificação acontece no banco, não depende de claims do token.

---

#### Comparação: Opção A vs Opção B com RLS

| Aspecto | Opção A (Token Claim) | Opção B (Consulta Banco) |
|---------|------------------------|---------------------------|
| **RLS** | Precisa de `is_owner` no token | Consulta tabela `owners` |
| **Segurança** | Depende de token (pode ser alterado) | Verificação no banco (mais seguro) |
| **Performance** | Mais rápido (sem query extra) | Query extra para verificar owner |
| **Flexibilidade** | Menos flexível (depende do Clerk) | Mais flexível (flags no banco) |
| **Recomendação** | Se RLS não for usado | **Melhor para RLS** |

**Recomendação Final**: **Opção B** é mais segura quando RLS está ativo, pois a verificação de owner acontece diretamente no banco de dados, não dependendo de claims do token que podem ser manipulados.

### 3. Nova Dependency: `get_current_org_id_flexible`

Para permitir que owner acesse qualquer organização:

```python
async def get_current_org_id_flexible(
    token_data: dict = Depends(verify_token),
    target_org_id: Optional[str] = Query(None, description="Organization ID (apenas para owners)"),
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> str:
    """
    Retorna organization_id com suporte a owner.
    
    - Se for STAFF: usa organization_id do token (ignora target_org_id)
    - Se for OWNER: pode usar target_org_id se fornecido, senão usa do token
    """
    
    # Verifica se é owner
    owner_result = await db.execute(
        select(Owner).where(
            Owner.clerk_id == current_user_id,
            Owner.is_active == True
        )
    )
    owner = owner_result.scalar_one_or_none()
    
    if owner:
        # OWNER: pode usar target_org_id se fornecido
        if target_org_id:
            # Valida que organização existe
            org_result = await db.execute(
                select(Organization).where(
                    Organization.clerk_org_id == target_org_id,
                    Organization.is_active == True
                )
            )
            if org_result.scalar_one_or_none():
                return target_org_id
            else:
                raise HTTPException(404, "Organização não encontrada")
        
        # Se não forneceu target_org_id, usa do token (organização principal)
        return token_data.get("org_id") or owner.primary_organization_id
    
    # STAFF: sempre usa do token (ignora target_org_id)
    return token_data["org_id"]
```

### 4. Nova Dependency: `require_owner_or_admin`

Para endpoints que precisam de owner OU admin da organização:

```python
async def require_owner_or_admin(
    current_user_id: str = Depends(get_current_user_id),
    current_org_id: str = Depends(get_current_org_id_flexible),
    db: AsyncSession = Depends(get_db),
) -> tuple[bool, Optional[Owner], Optional[StaffMember]]:
    """
    Retorna se usuário é owner ou admin da organização.
    
    Returns:
        (is_owner, owner, staff)
    """
    
    # 1. Verifica se é owner
    owner_result = await db.execute(
        select(Owner).where(
            Owner.clerk_id == current_user_id,
            Owner.is_active == True
        )
    )
    owner = owner_result.scalar_one_or_none()
    
    if owner:
        return (True, owner, None)
    
    # 2. Se não é owner, verifica se é admin da organização
    staff_result = await db.execute(
        select(StaffMember).where(
            StaffMember.clerk_id == current_user_id,
            StaffMember.organization_id == current_org_id,
            StaffMember.role == StaffRole.ADMIN,
            StaffMember.is_active == True
        )
    )
    staff = staff_result.scalar_one_or_none()
    
    if staff:
        return (False, None, staff)
    
    raise HTTPException(
        status_code=403,
        detail="Acesso negado. Requer OWNER ou ADMIN da organização."
    )
```

### 5. Novo Router: Organizations

**Base Path**: `/api/v1/organizations`

#### POST `/api/v1/organizations`

Cria uma nova organização.

**Autenticação**: ✅ Requerida (OWNER apenas)

**Body**:
```json
{
  "clerk_org_id": "org_xxx",  // ID da organização no Clerk (criada via API do Clerk primeiro)
  "name": "Ótica Nova",
  "cnpj": "12345678000190",
  "access_code": "ABC123",
  "plan": "basic"
}
```

**Processo**:
1. Owner cria organização no Clerk via API
2. Owner cria registro na tabela `organizations`
3. Owner pode se tornar ADMIN da nova organização (opcional)

#### GET `/api/v1/organizations`

Lista todas as organizações (apenas para owners).

**Autenticação**: ✅ Requerida (OWNER apenas)

**Query Parameters**:
- `is_active` (boolean, opcional): Filtrar por status
- `plan` (string, opcional): Filtrar por plano

**Resposta**: `200 OK`
```json
[
  {
    "id": 1,
    "clerk_org_id": "org_xxx",
    "name": "Ótica Central",
    "cnpj": "12345678000190",
    "access_code": "ABC123",
    "plan": "basic",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

#### GET `/api/v1/organizations/{org_id}`

Obtém detalhes de uma organização específica.

**Autenticação**: ✅ Requerida (OWNER apenas)

#### PATCH `/api/v1/organizations/{org_id}`

Atualiza uma organização.

**Autenticação**: ✅ Requerida (OWNER apenas)

#### DELETE `/api/v1/organizations/{org_id}`

Desativa uma organização (soft delete).

**Autenticação**: ✅ Requerida (OWNER apenas)

---

## 🔄 Impactos no Sistema Atual

### 1. Modificações Necessárias

#### `app/core/security.py`
- ✅ Manter `verify_token()` como está
- ✅ Adicionar `get_current_org_id_flexible()` (nova dependency)
- ⚠️ `get_current_org_id()` continua funcionando (para compatibilidade)

#### `app/core/permissions.py`
- ✅ Adicionar `get_current_user_type()` (verifica se é owner)
- ✅ Adicionar `require_owner()` (dependency para owner apenas)
- ✅ Adicionar `require_owner_or_admin()` (owner OU admin)
- ✅ Modificar `get_current_staff()` para retornar `None` se for owner

#### `app/models/`
- ✅ Criar `owner_model.py` (nova tabela)
- ✅ Criar `owner_schema.py` (schemas Pydantic)

#### `app/routers/v1/`
- ✅ Criar `organizations.py` (novos endpoints)
- ⚠️ Modificar endpoints existentes para suportar owner (opcional)

### 2. Compatibilidade com Código Existente

**Boa Notícia**: O código atual **continua funcionando** sem modificações!

- Endpoints existentes usam `get_current_org_id()` → continua funcionando
- Endpoints existentes usam `require_admin()` → continua funcionando
- Owner pode acessar endpoints normais usando `target_org_id` query param

**Exemplo**:
```python
# Endpoint existente (sem modificação)
@router.get("/staff")
async def list_staff(
    current_org_id: str = Depends(get_current_org_id),  # Funciona para owner também
    current_staff: StaffMember = Depends(require_staff_or_above),
):
    # ...
```

**Para owner acessar outra organização**:
```
GET /api/v1/staff?target_org_id=org_xxx
```

### 3. Migração de Dados

**Não requer migração** se implementar gradualmente:
- Tabela `owners` é nova (não afeta dados existentes)
- Código existente continua funcionando
- Owner é adicionado como feature adicional

---

## 🔀 Fluxos de Negócio

### 1. Fluxo de Criação de Organização (Owner)

```
1. Owner acessa painel de organizações
   ↓
2. Owner preenche formulário de nova organização
   ↓
3. Frontend chama Clerk API para criar organização
   ↓
4. Clerk retorna clerk_org_id
   ↓
5. Frontend chama POST /api/v1/organizations com dados
   ↓
6. Backend valida que usuário é OWNER
   ↓
7. Backend cria registro na tabela organizations
   ↓
8. Backend pode criar primeiro ADMIN (opcional)
   ↓
9. Organização está pronta para uso
```

### 2. Fluxo de Acesso Multi-Organização (Owner)

```
1. Owner faz login (token contém org_id principal)
   ↓
2. Owner acessa lista de organizações (GET /organizations)
   ↓
3. Owner seleciona organização diferente no frontend
   ↓
4. Frontend armazena organization_id selecionada
   ↓
5. Frontend envia requisições com ?target_org_id=org_xxx
   ↓
6. Backend valida que usuário é OWNER
   ↓
7. Backend usa target_org_id ao invés do token
   ↓
8. Owner acessa dados da organização selecionada
```

### 3. Fluxo de Criação de Owner

```
1. Primeiro owner é criado manualmente no banco (seed)
   ↓
2. Owner acessa painel de owners
   ↓
3. Owner cria novo owner (POST /api/v1/owners)
   ↓
4. Backend cria registro na tabela owners
   ↓
5. Novo owner recebe acesso ao sistema
   ↓
6. Novo owner pode criar organizações (se can_create_organizations = true)
```

---

## 🚀 Implementação Futura

### Fase 1: Estrutura Base (Sem Breaking Changes)

1. ✅ Criar model `Owner`
2. ✅ Criar schemas `OwnerSchema`
3. ✅ Criar migration para tabela `owners`
4. ✅ Criar função `get_current_user_type()`
5. ✅ Criar dependency `require_owner()`

**Resultado**: Estrutura pronta, mas não usada ainda.

### Fase 2: Endpoints de Organizações

1. ✅ Criar router `organizations.py`
2. ✅ Implementar CRUD de organizações
3. ✅ Integrar com Clerk API para criar orgs
4. ✅ Testar criação de organizações

**Resultado**: Owner pode criar organizações.

### Fase 3: Acesso Multi-Organização

1. ✅ Criar `get_current_org_id_flexible()`
2. ✅ Adicionar suporte a `target_org_id` query param
3. ✅ Modificar endpoints para usar nova dependency (opcional)
4. ✅ Testar acesso a múltiplas organizações

**Resultado**: Owner pode acessar qualquer organização.

### Fase 4: Integração com Frontend

1. ✅ Frontend detecta se usuário é owner
2. ✅ Frontend mostra seletor de organizações
3. ✅ Frontend envia `target_org_id` nas requisições
4. ✅ Testar fluxo completo

**Resultado**: Sistema completo funcionando.

### Fase 5: Otimizações

1. ✅ Cache de verificação de owner (Redis)
2. ✅ Custom claims no Clerk (se necessário)
3. ✅ Auditoria de ações de owner
4. ✅ Rate limiting para criação de orgs

**Resultado**: Sistema otimizado e seguro.

---

## 🔒 Considerações de Segurança

### 1. Validação Rigorosa

**Sempre validar**:
- ✅ Owner existe e está ativo
- ✅ Organização existe e está ativa (quando usar `target_org_id`)
- ✅ Owner tem permissão para criar organizações (`can_create_organizations`)

### 2. Auditoria

**Registrar todas as ações de owner**:
- Criação de organizações
- Acesso a organizações diferentes
- Modificações em organizações

**Tabela proposta**: `owner_audit_log`
```python
class OwnerAuditLog(BaseModel):
    owner_id = Column(Integer, ForeignKey("owners.id"))
    action = Column(String)  # "create_org", "access_org", "update_org"
    organization_id = Column(String)
    details = Column(JSON)
    ip_address = Column(String)
    created_at = Column(DateTime)
```

### 3. Rate Limiting

**Limitar criação de organizações**:
- Máximo X organizações por dia por owner
- Prevenir abuso do sistema

### 4. Row Level Security (RLS) no PostgreSQL

**⚠️ CRÍTICO**: Se o banco de dados usa RLS, as políticas precisam ser configuradas para reconhecer owners.

**Problema**:
- RLS normalmente filtra por `organization_id`
- Owner precisa acessar **todas** as organizações
- RLS bloqueia queries se não reconhecer owner

**Solução**:
1. **Criar função `is_owner()`** no PostgreSQL que consulta tabela `owners`
2. **Modificar policies** para incluir condição: `is_owner() OR organization_id = ...`
3. **Definir variáveis de sessão** (`SET LOCAL`) antes de cada query

**Exemplo de Policy Correta**:
```sql
CREATE POLICY staff_members_org_isolation ON staff_members
  FOR ALL
  USING (
    -- Se for owner, permite acesso a todas as organizações
    is_owner(current_setting('app.current_user_clerk_id', TRUE))
    OR
    -- Se não for owner, filtra por organization_id
    organization_id = current_setting('app.current_org_id', TRUE)
  );
```

**No código Python**:
```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            token_data = await verify_token()
            
            # Define variáveis para RLS
            await session.execute(
                text(f"SET LOCAL app.current_user_clerk_id = '{token_data['user_id']}'")
            )
            await session.execute(
                text(f"SET LOCAL app.current_org_id = '{token_data.get('org_id') or ''}'")
            )
            
            yield session
        finally:
            await session.close()
```

**Recomendação**: Usar **Opção B** (consulta ao banco) porque a função `is_owner()` verifica diretamente no banco, sendo mais segura que depender de claims do token.

### 5. Isolamento de Dados

**Garantir que owner não vaze dados**:
- Owner ainda precisa especificar `target_org_id` explicitamente
- Não retornar dados de todas as organizações por padrão
- Queries sempre filtram por `organization_id` (mesmo para owner)
- **RLS garante isolamento mesmo se código falhar**

### 6. Permissões Granulares

**Flags no model Owner**:
```python
can_create_organizations = Column(Boolean, default=True)
can_delete_organizations = Column(Boolean, default=False)
can_access_all_orgs = Column(Boolean, default=True)
can_impersonate_users = Column(Boolean, default=False)  # Futuro
```

### 7. Integração com Clerk

**Considerações**:
- Owner precisa ter permissões no Clerk para criar organizações
- Usar `CLERK_SECRET_KEY` para chamadas à API do Clerk
- Validar que `clerk_org_id` existe no Clerk antes de criar no banco

---

## 📊 Comparação: Antes vs Depois

### Antes (Sistema Atual)

| Aspecto | Comportamento |
|---------|---------------|
| Acesso | Apenas à organização do token |
| Criação de orgs | Manual (via SQL ou Clerk) |
| Super admin | Não existe |
| Multi-organização | Não suportado |
| Hierarquia | ADMIN > MANAGER > STAFF > ASSISTANT |

### Depois (Com Owner)

| Aspecto | Comportamento |
|---------|---------------|
| Acesso | Owner pode acessar qualquer organização |
| Criação de orgs | Via API (endpoint `/organizations`) |
| Super admin | OWNER existe |
| Multi-organização | Suportado via `target_org_id` |
| Hierarquia | **OWNER** > ADMIN > MANAGER > STAFF > ASSISTANT |

---

## 🎯 Resumo

### O que o sistema atual NÃO tem:
- ❌ Usuário que pode acessar múltiplas organizações
- ❌ Endpoint para criar organizações
- ❌ Super admin / Owner
- ❌ Sistema de gerenciamento de organizações

### O que a proposta adiciona:
- ✅ Tipo de usuário OWNER
- ✅ Tabela `owners` separada de `staff_members`
- ✅ Endpoints para CRUD de organizações
- ✅ Suporte a `target_org_id` para acesso multi-org
- ✅ `primary_organization_id` para organização padrão do owner
- ✅ Permissões granulares (`can_create_organizations`, etc.)

### Compatibilidade:
- ✅ **100% compatível** com código existente
- ✅ Endpoints atuais continuam funcionando
- ✅ Implementação pode ser gradual (fases)
- ✅ Não requer migração de dados existentes

### Próximos Passos:
1. Decidir se implementa agora ou depois
2. Se implementar, seguir fases sugeridas
3. Criar primeiro owner manualmente (seed)
4. Testar criação de organizações
5. Integrar com frontend

---

**Documento criado em**: 2025-01-XX  
**Status**: Proposta de arquitetura (não implementado)  
**Autor**: Documentação técnica do projeto

