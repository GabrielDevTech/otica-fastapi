# Configuração do Supabase Authentication

Este guia explica como configurar o Supabase Authentication no projeto para migração do Clerk.

## 📋 Pré-requisitos

1. Projeto Supabase criado (ou usar o existente)
2. Acesso ao Dashboard do Supabase
3. Chaves de API do Supabase

## 🔧 Passo 1: Obter Chaves do Supabase

### Método 1: Via Dashboard (Recomendado)

1. Acesse o [Dashboard do Supabase](https://app.supabase.com)
2. Faça login na sua conta
3. Selecione o projeto **"otica"** (ou o nome do seu projeto)
4. No menu lateral, clique em **Settings** (⚙️)
5. Clique em **API** no submenu
6. Na seção **Project API keys**, você encontrará:

   **Project URL** (copie o valor completo):
   ```
   https://xxxxx.supabase.co
   ```
   → Use como `SUPABASE_URL`

   **anon public** (clique em "Reveal" se estiver oculto):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   → Use como `SUPABASE_ANON_KEY`

   **service_role** (⚠️ SECRETO - clique em "Reveal"):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   → Use como `SUPABASE_SERVICE_KEY`

### Método 2: Via URL Direta

Se você já conhece o ID do projeto, acesse diretamente:
```
https://app.supabase.com/project/[PROJECT_ID]/settings/api
```

Substitua `[PROJECT_ID]` pelo ID do seu projeto.

### 📸 Onde Encontrar no Dashboard

```
Dashboard → [Seu Projeto] → Settings (⚙️) → API
```

Na página de API, você verá:
- **Project URL**: No topo da página
- **Project API keys**: Seção com as chaves
  - `anon` `public` → SUPABASE_ANON_KEY
  - `service_role` `secret` → SUPABASE_SERVICE_KEY

## 🔧 Passo 2: Configurar Variáveis de Ambiente

Adicione ao arquivo `.env` na raiz de `otica-api/`:

```env
# Auth Provider
AUTH_PROVIDER=supabase  # ou "clerk" para voltar ao Clerk

# Supabase Auth (Projeto: otica)
SUPABASE_URL=https://qnkuxvthwpuqjnlnekns.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFua3V4dnRod3B1cWpubG5la25zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxMTQwNTgsImV4cCI6MjA3OTY5MDA1OH0.zXoJ3kGSpeI_J_SjRWgptZIk-0ZrXd9CjyVY7c1CWE0
SUPABASE_SERVICE_KEY=sua_service_key_aqui  # ⚠️ Obtenha manualmente no Dashboard (Settings → API → service_role)

# Clerk (manter para rollback se necessário)
CLERK_ISSUER=https://seu-clerk.clerk.accounts.dev
CLERK_SECRET_KEY=sua_clerk_secret_key
```

### ✅ Chaves Obtidas Automaticamente

- ✅ **SUPABASE_URL**: `https://qnkuxvthwpuqjnlnekns.supabase.co`
- ✅ **SUPABASE_ANON_KEY**: Configurada acima
- ⚠️ **SUPABASE_SERVICE_KEY**: **Você precisa obter manualmente** (por segurança, não é retornada pela API)

### Como Obter a SERVICE_KEY

1. Acesse: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/settings/api
2. Na seção **Project API keys**
3. Clique em **Reveal** na chave **service_role**
4. Copie e cole no `.env` como `SUPABASE_SERVICE_KEY`

## 🔧 Passo 3: Configurar Authentication no Supabase

### 3.1 Habilitar Email Provider

1. No Dashboard do Supabase, vá em **Authentication** → **Providers**
2. Certifique-se de que **Email** está habilitado
3. Configure as opções de email:
   - ✅ **Enable email confirmations** (recomendado)
   - ✅ **Enable email change confirmations**

### 3.2 Configurar Email Templates (Opcional)

1. Vá em **Authentication** → **Email Templates**
2. Personalize os templates de:
   - **Invite user** (para convites)
   - **Magic Link** (se usar)
   - **Change Email Address**

### 3.3 Configurar Site URL

1. Vá em **Authentication** → **URL Configuration**
2. Configure:
   - **Site URL**: URL do seu frontend (ex: `http://localhost:3000`)
   - **Redirect URLs**: Adicione URLs permitidas para redirecionamento

## 🔧 Passo 4: Configurar Custom Claims (app_metadata)

O sistema usa `app_metadata.organization_id` para armazenar o ID da organização no token.

### Opção A: Via Dashboard (Manual)

1. Vá em **Authentication** → **Users**
2. Ao criar/editar usuário, adicione em **App Metadata**:
   ```json
   {
     "organization_id": "org_xxx"
   }
   ```

### Opção B: Via API (Automático)

O `SupabaseProvider` já configura automaticamente o `app_metadata` ao:
- Criar convites (`create_user_invitation`)
- Adicionar usuário à organização (`add_user_to_organization`)

## 🔧 Passo 5: Testar Configuração

### 5.1 Verificar JWKS Endpoint

Acesse no navegador:
```
https://seu-projeto.supabase.co/auth/v1/.well-known/jwks.json
```

**Nota**: O Supabase usa `/auth/v1/.well-known/jwks.json` (não apenas `/.well-known/jwks.json`)

Deve retornar um JSON com as chaves públicas.

### 5.2 Validar Chaves Configuradas

Execute o script para validar se as chaves estão corretas:
```bash
cd otica-api
python scripts/get_supabase_keys.py
```

Este script verifica:
- Se as variáveis estão no `.env`
- Se o JWKS endpoint está acessível
- Se as chaves são válidas

### 5.3 Testar Validação de Token

Execute o script de teste completo:
```bash
python scripts/test_supabase_auth.py
```

## ⚠️ Importante

1. **Service Key**: Nunca exponha a `SUPABASE_SERVICE_KEY` no frontend. Use apenas no backend.
2. **Anon Key**: Pode ser usada no frontend, mas com Row Level Security (RLS) habilitado.
3. **Organization ID**: Deve ser o mesmo `clerk_org_id` usado no banco de dados para manter compatibilidade.

## 🔄 Rollback

Se precisar voltar ao Clerk:

1. Altere no `.env`:
   ```env
   AUTH_PROVIDER=clerk
   ```

2. Reinicie o servidor

O sistema automaticamente voltará a usar o Clerk.

## 📚 Referências

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Supabase Admin API](https://supabase.com/docs/reference/javascript/auth-admin-createuser)
- [Supabase JWT Guide](https://supabase.com/docs/guides/auth/jwts)
