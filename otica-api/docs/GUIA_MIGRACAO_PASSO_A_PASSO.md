# Guia Passo a Passo: Migração Clerk → Supabase

Este guia detalha todos os passos necessários para migrar do Clerk para Supabase Authentication.

## 📋 Checklist Pré-Migração

- [ ] Backup completo do banco de dados
- [ ] Ambiente de staging configurado
- [ ] Projeto Supabase criado
- [ ] Chaves do Supabase obtidas
- [ ] Dependências instaladas (`pip install -r requirements.txt`)

## 🚀 Passo 1: Configurar Supabase (VOCÊ PRECISA FAZER)

### 1.1 Obter Chaves do Supabase

1. Acesse https://app.supabase.com
2. Selecione seu projeto (ou crie um novo)
3. Vá em **Settings** → **API**
4. Copie:
   - **Project URL** (ex: `https://xxxxx.supabase.co`)
   - **anon public** key
   - **service_role** key (⚠️ SECRETO!)

### 1.2 Configurar Authentication

1. No Dashboard, vá em **Authentication** → **Providers**
2. Certifique-se de que **Email** está habilitado
3. Configure **Authentication** → **URL Configuration**:
   - **Site URL**: URL do seu frontend
   - **Redirect URLs**: URLs permitidas

### 1.3 Testar Configuração

Execute o script de teste:
```bash
cd otica-api
python scripts/test_supabase_auth.py
```

Se tudo estiver OK, você verá: `✅ Todos os testes passaram!`

## 🔧 Passo 2: Configurar Variáveis de Ambiente (VOCÊ PRECISA FAZER)

Edite o arquivo `.env` em `otica-api/`:

```env
# Mude para supabase quando estiver pronto
AUTH_PROVIDER=clerk  # Por enquanto, mantenha como 'clerk'

# Supabase Auth (adicione suas chaves)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_anon_key_aqui
SUPABASE_SERVICE_KEY=sua_service_key_aqui

# Clerk (manter para rollback)
CLERK_ISSUER=https://seu-clerk.clerk.accounts.dev
CLERK_SECRET_KEY=sua_clerk_secret_key
```

⚠️ **IMPORTANTE**: Mantenha `AUTH_PROVIDER=clerk` por enquanto!

## 🧪 Passo 3: Testar em Staging (VOCÊ PRECISA FAZER)

### 3.1 Simular Migração (Dry Run)

Execute o script de migração em modo simulação:

```bash
cd otica-api
python scripts/migrate_clerk_to_supabase.py
```

Isso mostrará o que seria feito **sem fazer alterações reais**.

### 3.2 Executar Migração em Staging

Se a simulação estiver OK:

1. Configure `AUTH_PROVIDER=supabase` no `.env` de staging
2. Execute a migração real:
   ```bash
   python scripts/migrate_clerk_to_supabase.py --execute
   ```

### 3.3 Validar Migração

Execute o script de validação:
```bash
python scripts/validate_migration.py
```

### 3.4 Testar Endpoints

1. Inicie o servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Teste autenticação:
   - Faça login no frontend com Supabase
   - Teste alguns endpoints da API
   - Verifique logs para erros

## 🔄 Passo 4: Migração em Produção (VOCÊ PRECISA FAZER)

⚠️ **ATENÇÃO**: Só execute em produção após validar em staging!

### 4.1 Preparação

1. **Backup completo do banco de dados**
2. Agende janela de manutenção (se necessário)
3. Notifique usuários (se aplicável)

### 4.2 Executar Migração

1. Configure `AUTH_PROVIDER=supabase` no `.env` de produção
2. Execute migração:
   ```bash
   python scripts/migrate_clerk_to_supabase.py --execute
   ```
3. Valide:
   ```bash
   python scripts/validate_migration.py
   ```

### 4.3 Monitorar

- Monitore logs do servidor
- Verifique erros de autenticação
- Teste fluxos críticos

### 4.4 Rollback (Se Necessário)

Se algo der errado:

1. Reverta no `.env`:
   ```env
   AUTH_PROVIDER=clerk
   ```
2. Reinicie o servidor
3. Sistema volta a usar Clerk automaticamente

## 📝 Comandos Úteis

### Verificar configuração
```bash
python scripts/test_supabase_auth.py
```

### Simular migração
```bash
python scripts/migrate_clerk_to_supabase.py
```

### Executar migração
```bash
python scripts/migrate_clerk_to_supabase.py --execute
```

### Validar migração
```bash
python scripts/validate_migration.py
```

### Apenas validar organizações
```bash
python scripts/migrate_clerk_to_supabase.py --organizations-only
```

## ⚠️ Problemas Comuns

### Erro: "SUPABASE_URL não configurado"
- Verifique se as variáveis estão no `.env`
- Reinicie o servidor após alterar `.env`

### Erro: "Token não contém organization_id"
- Verifique se `app_metadata.organization_id` está configurado no Supabase
- Execute o script de migração para configurar automaticamente

### Usuários não encontrados após migração
- Execute `validate_migration.py` para diagnosticar
- Verifique se os emails coincidem entre Clerk e banco

## ✅ Pós-Migração

Após migração bem-sucedida:

1. ✅ Remover código do Clerk (opcional - manter por segurança)
2. ✅ Atualizar documentação
3. ✅ Comunicar mudança para equipe
4. ✅ Monitorar por alguns dias

## 📚 Documentação Adicional

- [Configuração Supabase Auth](./CONFIGURACAO_SUPABASE_AUTH.md)
- [Plano de Migração](./PLANO_MIGRACAO_AUTENTICACAO.md)
