# Próximos Passos Após Configurar as Chaves

Agora que você já configurou as chaves do Supabase no `.env`, siga estes passos:

## ✅ Passo 1: Validar Configuração

Execute o script para verificar se tudo está correto:

```bash
cd otica-api
python scripts/get_supabase_keys.py
```

**O que esperar:**
- ✅ Todas as variáveis configuradas
- ✅ JWKS endpoint acessível
- ✅ ANON_KEY válida
- ✅ SERVICE_KEY válida

Se houver erros, corrija antes de continuar.

## ✅ Passo 2: Testar Supabase Auth

Execute o teste completo:

```bash
python scripts/test_supabase_auth.py
```

**O que esperar:**
- ✅ JWKS acessível
- ✅ Provider inicializado
- ✅ (Opcional) Criação de usuário de teste

## ✅ Passo 3: Decidir Quando Migrar

### Opção A: Testar Agora (Recomendado)

Se quiser testar a migração:

1. **Mantenha `AUTH_PROVIDER=clerk`** por enquanto
2. Execute simulação de migração:
   ```bash
   python scripts/migrate_clerk_to_supabase.py
   ```
   Isso mostra o que seria feito **sem fazer alterações reais**.

3. Se a simulação estiver OK, você pode:
   - Testar em ambiente de staging primeiro
   - Ou aguardar até estar pronto para produção

### Opção B: Migrar Depois

Se preferir migrar depois:
- Sistema continua funcionando com Clerk normalmente
- Quando estiver pronto, mude `AUTH_PROVIDER=supabase` no `.env`
- Execute a migração

## 🔄 Fluxo de Migração (Quando Estiver Pronto)

### 1. Simular Migração
```bash
python scripts/migrate_clerk_to_supabase.py
```

### 2. Executar Migração (Staging/Teste)
```bash
# 1. Mude AUTH_PROVIDER=supabase no .env
# 2. Execute migração
python scripts/migrate_clerk_to_supabase.py --execute
```

### 3. Validar Migração
```bash
python scripts/validate_migration.py
```

### 4. Testar Endpoints
- Inicie o servidor: `uvicorn app.main:app --reload`
- Teste autenticação com tokens do Supabase
- Verifique logs para erros

## ⚠️ Importante

- **Por enquanto**: Mantenha `AUTH_PROVIDER=clerk` se ainda não migrou
- **Sistema funciona normalmente**: Com Clerk até você migrar
- **Rollback fácil**: Basta mudar `AUTH_PROVIDER=clerk` se precisar voltar

## 📋 Checklist

- [x] Chaves configuradas no `.env`
- [ ] Validar configuração (`get_supabase_keys.py`)
- [ ] Testar Supabase Auth (`test_supabase_auth.py`)
- [ ] Simular migração (quando estiver pronto)
- [ ] Executar migração em staging (quando estiver pronto)
- [ ] Validar migração
- [ ] Executar migração em produção (quando estiver pronto)

## 🆘 Problemas?

Se encontrar erros:

1. Verifique se todas as chaves estão no `.env`
2. Execute `get_supabase_keys.py` para diagnosticar
3. Verifique se o projeto Supabase está ativo
4. Consulte `GUIA_MIGRACAO_PASSO_A_PASSO.md` para mais detalhes
