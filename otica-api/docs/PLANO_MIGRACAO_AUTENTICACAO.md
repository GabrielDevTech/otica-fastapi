# Plano de Migração: Clerk → Supabase Authentication

## 📋 Contexto

O Clerk no plano gratuito permite apenas **5 usuários por organização**, o que limita o crescimento do sistema. Este documento apresenta um plano de migração para **Supabase Authentication** com **mínimo impacto** na API e **sem alterar a interface de entrada/saída dos endpoints**.

**Decisão**: Migração para **Supabase Authentication** devido à integração nativa com o PostgreSQL do Supabase já utilizado no projeto, ausência de limite de usuários no plano gratuito e menor complexidade de implementação.

---

## 🎯 Objetivos

1. ✅ **Manter compatibilidade total** com a interface atual dos endpoints
2. ✅ **Migração gradual** sem downtime
3. ✅ **Abstração da autenticação** para facilitar futuras mudanças
4. ✅ **Preservar isolamento multi-tenant** existente
5. ✅ **Manter estrutura de dados** atual (com adaptações mínimas)

---

## 🔍 Análise da Situação Atual

### Componentes que usam Clerk

#### 1. **Autenticação (JWT Validation)**
- **Arquivo**: `app/core/security.py`
- **Funções críticas**:
  - `verify_token()`: Valida JWT via JWKS do Clerk
  - `get_current_org_id()`: Extrai `org_id` do token
  - `get_current_user_id()`: Extrai `user_id` (clerk_id) do token
- **Dependências**: `python-jose`, `cryptography`, `httpx` (para JWKS)

#### 2. **Serviço Clerk**
- **Arquivo**: `app/services/clerk_service.py`
- **Métodos**:
  - `create_user_invitation()`: Cria convites
  - `create_user()`: Cria usuários diretamente
  - `add_user_to_organization()`: Adiciona usuário à organização
  - `get_user_by_email()`: Busca usuário por email
  - `delete_user()`: Deleta usuário

#### 3. **Modelos de Dados**
- **`Organization.clerk_org_id`**: String(255) - ID da organização no Clerk
- **`StaffMember.clerk_id`**: String - ID do usuário no Clerk (nullable)

#### 4. **Permissions**
- **Arquivo**: `app/core/permissions.py`
- **Funções**:
  - `get_user_email_from_clerk()`: Busca email via API do Clerk
  - `get_current_staff()`: Busca staff pelo `clerk_id` ou email

#### 5. **Routers que usam Clerk**
- `invitations.py`: Cria convites via Clerk API
- Vários routers usam `get_org_internal_id()` que busca por `clerk_org_id`

---

## 🏗️ Arquitetura Proposta

### Camada de Abstração (Auth Provider)

Criar uma interface comum que abstrai a diferença entre Clerk e Supabase, permitindo migração gradual:

```
app/core/auth/
├── __init__.py
├── base_auth_provider.py      # Interface abstrata
├── clerk_provider.py           # Implementação Clerk (legado)
├── supabase_provider.py        # Implementação Supabase
└── auth_factory.py             # Factory para escolher provider
```

### Estrutura da Interface

```python
# app/core/auth/base_auth_provider.py
from abc import ABC, abstractmethod
from typing import Optional, Dict

class BaseAuthProvider(ABC):
    """Interface para providers de autenticação."""
    
    @abstractmethod
    async def verify_token(self, token: str) -> Dict:
        """Valida token e retorna payload com org_id e user_id."""
        pass
    
    @abstractmethod
    async def get_user_email(self, user_id: str) -> Optional[str]:
        """Busca email do usuário."""
        pass
    
    @abstractmethod
    async def create_user_invitation(
        self, email: str, organization_id: str, role: str
    ) -> Dict:
        """Cria convite para usuário."""
        pass
    
    @abstractmethod
    async def create_user(
        self, email: str, first_name: str, last_name: str
    ) -> Dict:
        """Cria usuário diretamente."""
        pass
    
    @abstractmethod
    async def add_user_to_organization(
        self, user_id: str, organization_id: str, role: str
    ) -> Dict:
        """Adiciona usuário à organização."""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Busca usuário por email."""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Deleta usuário."""
        pass
```

---

## 🎯 Por que Supabase Authentication?

### Vantagens do Supabase Auth

| Característica | Benefício |
|----------------|-----------|
| **Limite gratuito** | Ilimitado (usuários ativos) - sem restrição de 5 usuários por org |
| **Multi-tenancy nativo** | Row Level Security (RLS) integrado |
| **JWT padrão** | Compatível com estrutura atual do Clerk |
| **JWKS** | Validação de tokens via chaves públicas |
| **Organizações** | Suporte nativo via metadata ou RLS |
| **Convites** | API nativa para criação de convites |
| **Integração com DB** | Nativa - já usa Supabase PostgreSQL |
| **Complexidade** | Baixa - API similar ao Clerk |
| **Custo escalável** | Pago por uso de recursos, não por usuário |

### Motivos da Escolha

1. ✅ **Já usa Supabase PostgreSQL** - integração nativa e natural
2. ✅ **Sem limite de usuários** - resolve o problema do Clerk (5 usuários/org)
3. ✅ **Multi-tenancy nativo** - Row Level Security integrado
4. ✅ **JWT padrão** - compatível com estrutura atual
5. ✅ **API similar ao Clerk** - menor curva de aprendizado
6. ✅ **Menos complexidade** - tudo em um lugar (Auth + DB)

---

## 🚀 Plano de Migração (Supabase)

### Fase 1: Preparação e Abstração (Sem Breaking Changes)

#### 1.1 Criar Estrutura de Abstração
- [ ] Criar `app/core/auth/` com interface base
- [ ] Implementar `ClerkProvider` (refatorar código existente)
- [ ] Criar `AuthFactory` que retorna provider baseado em env var
- [ ] Manter Clerk como padrão inicial

#### 1.2 Refatorar `security.py`
- [ ] Substituir lógica direta do Clerk por `AuthProvider.verify_token()`
- [ ] Manter mesma interface de `get_current_org_id()` e `get_current_user_id()`
- [ ] Testar que nada quebra

#### 1.3 Refatorar `clerk_service.py`
- [ ] Renomear para `clerk_provider.py` e implementar `BaseAuthProvider`
- [ ] Manter compatibilidade com código existente
- [ ] Criar `auth_service.py` que usa factory

#### 1.4 Atualizar Configurações
- [ ] Adicionar `AUTH_PROVIDER=clerk` no `.env`
- [ ] Manter todas as variáveis `CLERK_*` funcionando

**Resultado**: Sistema continua funcionando exatamente como antes, mas com abstração pronta.

---

### Fase 2: Implementação Supabase (Paralelo)

#### 2.1 Setup Supabase Auth
- [ ] Criar projeto no Supabase (ou usar existente)
- [ ] Configurar autenticação
- [ ] Obter chaves: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`
- [ ] Configurar JWKS URL do Supabase

#### 2.2 Implementar `SupabaseProvider`
- [ ] Implementar `verify_token()` usando JWKS do Supabase
- [ ] Implementar métodos de gerenciamento de usuários
- [ ] Implementar criação de organizações (via metadata ou tabela separada)
- [ ] Testes unitários

#### 2.3 Adaptar Modelos de Dados
- [ ] **Opção A (Recomendada)**: Manter `clerk_org_id` e `clerk_id` como campos genéricos
  - Renomear para `auth_org_id` e `auth_user_id` (ou manter nomes atuais)
  - Documentar que agora armazenam IDs do Supabase
- [ ] **Opção B**: Criar migration para renomear colunas
  - `clerk_org_id` → `auth_org_id`
  - `clerk_id` → `auth_user_id`
- [ ] Criar migration para popular dados existentes (se houver)

#### 2.4 Mapeamento de Organizações
- [ ] Criar tabela `auth_organizations` (se necessário) para mapear:
  - `organization_id` (interno) ↔ `supabase_org_id` (Supabase)
- [ ] Ou usar metadata do JWT do Supabase para armazenar `organization_id` interno

**Estratégia de Organizações no Supabase**:
- **Opção 1**: Custom claims no JWT com `organization_id` interno
- **Opção 2**: Tabela de mapeamento `auth_organizations`
- **Opção 3**: Usar `app_metadata` do Supabase para armazenar `organization_id`

---

### Fase 3: Migração Gradual (Feature Flag)

#### 3.1 Sistema Dual (Clerk + Supabase)
- [ ] Adicionar env var `AUTH_PROVIDER=supabase|clerk`
- [ ] Implementar feature flag por organização:
  - Tabela `organizations.auth_provider` (enum: 'clerk', 'supabase')
  - Ou usar env var global para migração completa
- [ ] Permitir que algumas orgs usem Supabase e outras Clerk

#### 3.2 Script de Migração de Dados
- [ ] Script para migrar usuários do Clerk para Supabase:
  - Lista todos os `StaffMember` com `clerk_id`
  - Cria usuários no Supabase
  - Atualiza `clerk_id` com novo `auth_user_id` do Supabase
- [ ] Script para migrar organizações:
  - Cria organizações no Supabase (se necessário)
  - Atualiza `clerk_org_id` com novo ID do Supabase

#### 3.3 Testes de Migração
- [ ] Ambiente de staging com dados de teste
- [ ] Migrar uma organização de teste
- [ ] Validar que todos os endpoints funcionam
- [ ] Testar fluxo completo: login → endpoints → permissões

---

### Fase 4: Cutover Completo

#### 4.1 Migração em Produção
- [ ] Backup completo do banco de dados
- [ ] Executar scripts de migração
- [ ] Atualizar `AUTH_PROVIDER=supabase` no `.env`
- [ ] Monitorar logs e erros

#### 4.2 Validação Pós-Migração
- [ ] Testar autenticação em todas as rotas
- [ ] Validar isolamento multi-tenant
- [ ] Verificar permissões e roles
- [ ] Testar criação de novos usuários

#### 4.3 Limpeza
- [ ] Remover código do Clerk (opcional, manter por segurança)
- [ ] Remover variáveis `CLERK_*` do `.env` (ou manter comentadas)
- [ ] Atualizar documentação

---

## 🔧 Detalhes Técnicos

### 1. Estrutura de Token Supabase

O Supabase usa JWT padrão com estrutura similar ao Clerk:

```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "app_metadata": {
    "organization_id": "org_internal_id"
  },
  "user_metadata": {
    "full_name": "Nome Completo"
  },
  "iat": 1234567890,
  "exp": 1234571490
}
```

**Estratégia para `organization_id`**:
- Usar `app_metadata.organization_id` no token
- Ou criar custom claim via Supabase Edge Function
- Ou buscar na tabela `auth_organizations` após validar token

### 2. Validação de Token Supabase

```python
# app/core/auth/supabase_provider.py
async def verify_token(self, token: str) -> Dict:
    """Valida token do Supabase via JWKS."""
    # 1. Buscar JWKS do Supabase
    jwks_url = f"{self.supabase_url}/.well-known/jwks.json"
    
    # 2. Validar assinatura (mesmo processo do Clerk)
    
    # 3. Extrair organization_id de app_metadata ou tabela
    
    return {
        "org_id": organization_id,
        "user_id": payload["sub"],
        "payload": payload
    }
```

### 3. Gerenciamento de Usuários Supabase

```python
# Usar Supabase Admin API
from supabase import create_client, Client

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY  # Admin key
)

# Criar usuário
user = supabase.auth.admin.create_user({
    "email": email,
    "password": None,  # Senha será definida no primeiro login
    "app_metadata": {"organization_id": org_id}
})

# Criar convite
invitation = supabase.auth.admin.invite_user_by_email(email)
```

### 4. Adaptação de `get_current_staff()`

```python
# app/core/permissions.py
async def get_current_staff(
    current_org_id: str = Depends(get_current_org_id),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> StaffMember:
    """Busca staff - funciona com qualquer provider."""
    
    # Busca pelo auth_user_id (genérico, funciona com Clerk ou Supabase)
    result = await db.execute(
        select(StaffMember).where(
            StaffMember.clerk_id == current_user_id,  # Armazena ID do Supabase após migração
            StaffMember.organization_id == current_org_id,
            StaffMember.is_active == True
        )
    )
    # ... resto do código igual
```

**Nota**: O campo `clerk_id` pode ser renomeado para `auth_user_id` ou mantido como está (apenas documentar que após a migração armazena ID do Supabase ao invés do Clerk).

---

## 📝 Checklist de Migração

### Preparação
- [x] Decidir por Supabase Authentication
- [ ] Configurar autenticação no projeto Supabase existente
- [ ] Obter chaves: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`
- [ ] Backup completo do banco de dados

### Implementação
- [ ] Criar estrutura de abstração (`BaseAuthProvider`)
- [ ] Implementar `SupabaseProvider`
- [ ] Refatorar `security.py` para usar abstração
- [ ] Refatorar `clerk_service.py` para `ClerkProvider`
- [ ] Atualizar `permissions.py` se necessário
- [ ] Criar scripts de migração de dados
- [ ] Testes unitários e de integração

### Migração
- [ ] Executar migração em ambiente de staging
- [ ] Validar todos os endpoints
- [ ] Testar fluxos críticos (login, permissões, multi-tenant)
- [ ] Executar migração em produção
- [ ] Monitorar logs e métricas
- [ ] Validar pós-migração

### Limpeza
- [ ] Remover código legado (opcional)
- [ ] Atualizar documentação
- [ ] Atualizar variáveis de ambiente
- [ ] Comunicar mudança para equipe

---

## ⚠️ Riscos e Mitigações

### Riscos

1. **Perda de dados durante migração**
   - **Mitigação**: Backup completo antes, script de rollback

2. **Downtime durante cutover**
   - **Mitigação**: Sistema dual permite migração gradual

3. **Incompatibilidade de tokens**
   - **Mitigação**: Validar estrutura de token antes da migração

4. **Problemas com organizações existentes**
   - **Mitigação**: Script de migração testado em staging

5. **Frontend precisa ser atualizado**
   - **Mitigação**: Backend mantém mesma interface, frontend só muda URL/keys

### Rollback Plan

1. Reverter `AUTH_PROVIDER=clerk` no `.env`
2. Restaurar backup do banco (se necessário)
3. Validar que sistema volta a funcionar com Clerk

---

## 📚 Referências

### Supabase Authentication
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Supabase JWT Guide](https://supabase.com/docs/guides/auth/jwts)
- [Supabase Admin API](https://supabase.com/docs/reference/javascript/auth-admin-createuser)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Supabase Auth Helpers](https://supabase.com/docs/guides/auth/auth-helpers)
- [Row Level Security (RLS)](https://supabase.com/docs/guides/auth/row-level-security)

---

## 🔐 Supabase Auth: Independência do Banco de Dados

### Pergunta Frequente

**"Se eu usar Supabase Authentication, preciso manter meu banco de dados no Supabase?"**

### Resposta: **NÃO, você pode usar qualquer banco de dados!**

O **Supabase Authentication** é um serviço **independente** do banco de dados. Você pode usar Supabase Auth com:

- ✅ **PostgreSQL do Supabase** (recomendado para integração completa)
- ✅ **PostgreSQL próprio** (self-hosted, AWS RDS, DigitalOcean, etc.)
- ✅ **Outros bancos de dados** (MySQL, SQL Server, etc.) - com algumas limitações

### Como Funciona

O Supabase Auth funciona através de:

1. **JWT Tokens**: Gera tokens JWT padrão que você valida no seu backend
2. **REST API**: API REST para gerenciar usuários, convites, etc.
3. **JWKS Endpoint**: Endpoint público para validar assinatura dos tokens

**Não há dependência direta com o banco de dados**. A autenticação é um serviço separado que apenas gera tokens JWT.

### Arquitetura com Banco Próprio

```
┌─────────────────┐
│  Supabase Auth  │  ← Serviço de autenticação (independente)
│  (JWT Tokens)   │
└────────┬────────┘
         │
         │ JWT Token
         │
         ▼
┌─────────────────┐
│   Seu Backend    │  ← Valida token via JWKS
│   (FastAPI)      │
└────────┬────────┘
         │
         │ Queries
         │
         ▼
┌─────────────────┐
│  Seu PostgreSQL  │  ← Pode estar em qualquer lugar
│  (Self-hosted)   │
└─────────────────┘
```

### Vantagens de Usar Banco Próprio

1. **Controle Total**: Você gerencia seu próprio banco de dados
2. **Custos**: Pode ser mais barato dependendo do volume
3. **Performance**: Otimizações específicas para seu caso
4. **Compliance**: Dados ficam onde você precisa (região, compliance, etc.)
5. **Flexibilidade**: Pode usar qualquer versão do PostgreSQL ou outro SGBD

### Vantagens de Usar PostgreSQL do Supabase

1. **Integração Nativa**: Row Level Security (RLS) funciona automaticamente
2. **Simplicidade**: Tudo em um lugar (Auth + DB)
3. **Features Extras**: Realtime, Storage, Edge Functions
4. **Menos Configuração**: Menos pontos de falha

### Implementação com Banco Próprio

Se você usar Supabase Auth com seu próprio PostgreSQL:

```python
# app/core/config.py
class Settings(BaseSettings):
    # Supabase Auth (independente do banco)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Seu próprio PostgreSQL (pode estar em qualquer lugar)
    DATABASE_URL: str  # postgresql+asyncpg://seu-servidor:5432/seu-banco
```

**Validação do Token**:
- Busca JWKS do Supabase: `{SUPABASE_URL}/.well-known/jwks.json`
- Valida assinatura do token
- Extrai `user_id` e `organization_id` do payload
- Usa esses dados para consultar **seu próprio banco**

**Gerenciamento de Usuários**:
- Usa Supabase Admin API para criar/gerenciar usuários
- Armazena apenas `auth_user_id` (ID do Supabase) no seu banco
- Não precisa armazenar senhas ou dados sensíveis

### Caso de Uso Atual

No seu caso, você já usa **Supabase PostgreSQL via ORM** (SQLAlchemy). Isso significa:

- ✅ Você **já tem** um projeto Supabase
- ✅ Você **já usa** o banco PostgreSQL do Supabase
- ✅ Migrar para Supabase Auth seria **natural** (mesmo projeto)
- ✅ Mas você **pode migrar o banco** para outro lugar depois sem problemas

### Recomendação para Seu Caso

**Opção 1: Manter tudo no Supabase** (Recomendado inicialmente)
- ✅ Mais simples
- ✅ Integração nativa
- ✅ Menos pontos de configuração
- ✅ Pode migrar o banco depois se necessário

**Opção 2: Usar Supabase Auth + Banco Próprio**
- ✅ Mais controle sobre o banco
- ✅ Pode otimizar custos
- ⚠️ Mais complexidade de configuração
- ⚠️ Perde integração com RLS automático

### Migração Futura do Banco

Se você decidir migrar o banco do Supabase para outro lugar no futuro:

1. **Supabase Auth continua funcionando** (é independente)
2. **Apenas muda a `DATABASE_URL`** no `.env`
3. **Nenhuma mudança no código de autenticação**
4. **Tokens continuam sendo validados da mesma forma**

### Resumo

| Aspecto | Supabase Auth | Banco de Dados |
|---------|---------------|----------------|
| **Localização** | Supabase Cloud | Qualquer lugar |
| **Dependência** | Independente | Independente |
| **Comunicação** | JWT + REST API | Connection String |
| **Migração** | Não afeta | Pode migrar quando quiser |

**Conclusão**: Você pode usar Supabase Authentication com **qualquer banco de dados PostgreSQL** (ou outro SGBD). A autenticação é um serviço separado que apenas gera e valida tokens JWT. Seu banco de dados pode estar onde você quiser!

---

## ✅ Conclusão

Este plano permite migração **gradual e segura** de Clerk para Supabase Authentication sem quebrar a API existente. A **abstração de autenticação** garante que futuras mudanças sejam mais fáceis e permite rollback se necessário.

**Benefícios da Migração**:
- ✅ Resolve limitação de 5 usuários por organização do Clerk
- ✅ Integração nativa com PostgreSQL do Supabase já utilizado
- ✅ Sem limite de usuários no plano gratuito
- ✅ Multi-tenancy nativo via Row Level Security
- ✅ API compatível com estrutura atual

**Próximos Passos**:
1. Revisar e aprovar este plano
2. Configurar Supabase Authentication no projeto existente
3. Iniciar Fase 1 (Preparação e Abstração)

---

**Última atualização**: 2024-12-19  
**Autor**: Plano de Migração - Projeto Ótica  
**Provider Escolhido**: Supabase Authentication
