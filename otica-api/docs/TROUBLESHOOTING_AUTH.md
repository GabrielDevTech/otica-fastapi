# Troubleshooting: Problemas de Autenticação

## ❌ Erro: "decode() missing 1 required positional argument: 'key'"

**Causa**: O código estava tentando decodificar um JWT sem fornecer a chave necessária.

**Status**: ✅ **CORRIGIDO** na versão atual do código.

**Solução**: Se você ainda vê este erro, certifique-se de que está usando a versão mais recente do `supabase_provider.py`.

---

## ❌ Erro: 401 Unauthorized em todas as requisições

### Possíveis Causas:

### 1. AUTH_PROVIDER não está configurado corretamente

**Sintoma**: Todas as requisições retornam 401, mesmo com token válido.

**Verificação**:
```bash
# Verifique o .env
cat otica-api/.env | grep AUTH_PROVIDER
```

**Solução**:
- Se estiver usando **Supabase**, configure:
  ```env
  AUTH_PROVIDER=supabase
  ```

- Se estiver usando **Clerk**, configure:
  ```env
  AUTH_PROVIDER=clerk
  ```

**Importante**: O `AUTH_PROVIDER` deve corresponder ao tipo de token que o frontend está enviando!

---

### 2. Token não está sendo enviado corretamente

**Sintoma**: 401 em todas as requisições.

**Verificação no Frontend**:
```typescript
// Verifique se o token está sendo enviado
const token = await supabase.auth.getSession()
console.log('Token:', token.data.session?.access_token)

// Verifique o header da requisição
fetch('/api/v1/staff', {
  headers: {
    'Authorization': `Bearer ${token}`  // Deve ter "Bearer " antes do token
  }
})
```

**Solução**: Certifique-se de que:
- O token está sendo obtido corretamente
- O header `Authorization` está no formato: `Bearer <token>`
- O token não está expirado

---

### 3. Variáveis de ambiente do Supabase não configuradas

**Sintoma**: 401 ou erro ao iniciar o servidor.

**Verificação**:
```bash
# Verifique se as variáveis estão no .env
cat otica-api/.env | grep SUPABASE
```

**Deve ter**:
```env
AUTH_PROVIDER=supabase
SUPABASE_URL=https://qnkuxvthwpuqjnlnekns.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=sua_service_key_aqui
```

**Solução**: Configure todas as variáveis conforme `CONFIGURACAO_SUPABASE_AUTH.md`.

---

### 4. Token do Supabase não tem organization_id

**Sintoma**: 403 Forbidden com mensagem "Token não contém organization_id".

**Causa**: O usuário não foi associado a uma organização durante a migração.

**Verificação**:
```bash
# Execute o script de validação
py scripts/validate_migration.py
```

**Solução**:
1. Verifique se o usuário foi migrado corretamente
2. Verifique se o `app_metadata.organization_id` está configurado no Supabase
3. Re-execute a migração se necessário:
   ```bash
   py scripts/migrate_clerk_to_supabase.py --execute
   ```

---

### 5. JWKS está vazio ou inacessível

**Sintoma**: Erro "Token usa RS256 mas JWKS está vazio".

**Causa**: O endpoint JWKS do Supabase não está retornando chaves.

**Verificação**:
```bash
# Teste o endpoint JWKS
curl https://qnkuxvthwpuqjnlnekns.supabase.co/auth/v1/.well-known/jwks.json
```

**Solução**:
- Aguarde alguns minutos (as chaves podem estar sendo geradas)
- Verifique se a URL do Supabase está correta
- Se persistir, use tokens HS256 temporariamente (não recomendado para produção)

---

## ❌ Erro: "ModuleNotFoundError: No module named 'supabase'"

**Causa**: A biblioteca `supabase` não está instalada.

**Solução**:
```bash
# Ative o ambiente virtual
.\venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Ou instale apenas o supabase
pip install supabase>=2.0.0
```

---

## ❌ Erro: "SUPABASE_SERVICE_KEY não configurada"

**Causa**: A chave de serviço do Supabase não está no `.env`.

**Solução**:
1. Acesse: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/settings/api
2. Na seção **Project API keys**, clique em **Reveal** na chave **service_role**
3. Copie o valor e adicione ao `.env`:
   ```env
   SUPABASE_SERVICE_KEY=sua_service_key_aqui
   ```

---

## 🔍 Como Diagnosticar Problemas

### 1. Verificar Configuração

```bash
# Execute o script de verificação
py scripts/get_supabase_keys.py
```

### 2. Verificar Logs do Servidor

Observe os logs do uvicorn para mensagens de erro específicas:
```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### 3. Testar Token Manualmente

```python
# scripts/test_token.py
import asyncio
from app.core.auth.supabase_provider import SupabaseProvider

async def test():
    provider = SupabaseProvider()
    token = "seu_token_aqui"
    try:
        result = await provider.verify_token(token)
        print("✅ Token válido:", result)
    except Exception as e:
        print("❌ Erro:", str(e))

asyncio.run(test())
```

### 4. Verificar Token no Frontend

```typescript
// No console do navegador
const { data: { session } } = await supabase.auth.getSession()
console.log('Session:', session)
console.log('Token:', session?.access_token)
console.log('User:', session?.user)
```

---

## ✅ Checklist de Verificação

Antes de reportar um problema, verifique:

- [ ] `AUTH_PROVIDER` está configurado corretamente no `.env`
- [ ] Todas as variáveis do Supabase estão no `.env` (URL, ANON_KEY, SERVICE_KEY)
- [ ] O token está sendo enviado no header `Authorization: Bearer <token>`
- [ ] O token não está expirado
- [ ] O usuário foi migrado corretamente (execute `validate_migration.py`)
- [ ] O `app_metadata.organization_id` está configurado no Supabase
- [ ] As dependências estão instaladas (`pip install -r requirements.txt`)
- [ ] O servidor foi reiniciado após mudanças no `.env`

---

## 📚 Documentos Relacionados

- `CONFIGURACAO_SUPABASE_AUTH.md` - Como configurar Supabase
- `FRONTEND_SUPABASE_AUTH.md` - Como integrar no frontend
- `GUIA_MIGRACAO_PASSO_A_PASSO.md` - Guia completo de migração
- `CONFIGURAR_SENHAS_SUPABASE.md` - Como configurar senhas

---

**Última atualização**: 2024-12-19  
**Projeto**: Otica API - Migração Clerk → Supabase
