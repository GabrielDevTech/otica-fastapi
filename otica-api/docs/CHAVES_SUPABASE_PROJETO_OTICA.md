# Chaves do Supabase - Projeto Otica

## 📋 Informações do Projeto

- **Nome**: otica
- **ID**: qnkuxvthwpuqjnlnekns
- **Região**: sa-east-1 (São Paulo)
- **Status**: ACTIVE_HEALTHY
- **Database**: PostgreSQL 17.6.1

## 🔑 Chaves de API

### ✅ SUPABASE_URL
```
https://qnkuxvthwpuqjnlnekns.supabase.co
```

### ✅ SUPABASE_ANON_KEY
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFua3V4dnRod3B1cWpubG5la25zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxMTQwNTgsImV4cCI6MjA3OTY5MDA1OH0.zXoJ3kGSpeI_J_SjRWgptZIk-0ZrXd9CjyVY7c1CWE0
```

### ⚠️ SUPABASE_SERVICE_KEY

**Esta chave não pode ser obtida automaticamente por questões de segurança.**

Para obter:

1. Acesse: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/settings/api
2. Na seção **Project API keys**
3. Clique em **Reveal** na chave **service_role** (secret)
4. Copie o valor completo

## 📝 Configuração no .env

Adicione ao arquivo `otica-api/.env`:

```env
# Supabase Auth
SUPABASE_URL=https://qnkuxvthwpuqjnlnekns.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFua3V4dnRod3B1cWpubG5la25zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxMTQwNTgsImV4cCI6MjA3OTY5MDA1OH0.zXoJ3kGSpeI_J_SjRWgptZIk-0ZrXd9CjyVY7c1CWE0
SUPABASE_SERVICE_KEY=cole_a_service_key_aqui
```

## 🔒 Segurança

- ⚠️ **NUNCA** exponha a `SUPABASE_SERVICE_KEY` no frontend
- ✅ A `SUPABASE_ANON_KEY` pode ser usada no frontend (com RLS habilitado)
- 🔐 Mantenha o `.env` fora do controle de versão (já está no `.gitignore`)

## 🔗 Links Úteis

- **Dashboard**: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns
- **API Settings**: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/settings/api
- **JWKS Endpoint**: https://qnkuxvthwpuqjnlnekns.supabase.co/auth/v1/.well-known/jwks.json
