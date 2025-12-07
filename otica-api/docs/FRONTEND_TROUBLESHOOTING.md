# Troubleshooting Frontend: Problemas Comuns de Autenticação

Este documento ajuda a diagnosticar e resolver problemas comuns de autenticação no frontend após a migração para Supabase.

## ❌ Erro: "Invalid audience" ou "Token inválido: Invalid audience"

### Causa

O token JWT do Supabase contém um campo `aud` (audience) que pode não corresponder ao esperado pelo backend. Este é um problema comum quando o backend tenta validar o `aud` claim do token.

### Status

✅ **CORRIGIDO** no backend - A validação agora ignora o campo `aud` do token.

### ⚠️ Ação Imediata Necessária

**O servidor backend DEVE ser reiniciado** para que a correção tenha efeito!

Se você ainda vê este erro, é muito provável que o servidor não foi reiniciado após a correção.

### Verificação no Frontend

Se você ainda vê este erro, verifique:

1. **Token está sendo enviado corretamente?**
   ```typescript
   const { data: { session } } = await supabase.auth.getSession()
   const token = session?.access_token
   
   console.log('Token:', token) // Deve mostrar um JWT válido
   ```

2. **Header Authorization está correto?**
   ```typescript
   fetch('/api/v1/staff', {
     headers: {
       'Authorization': `Bearer ${token}` // Deve ter "Bearer " antes do token
     }
   })
   ```

3. **Token não está expirado?**
   ```typescript
   // Verifique a expiração
   const { data: { session } } = await supabase.auth.getSession()
   if (session) {
     const expiresAt = session.expires_at
     const now = Math.floor(Date.now() / 1000)
     console.log('Token expira em:', expiresAt - now, 'segundos')
   }
   ```

### Solução

1. **IMPORTANTE: Reinicie o servidor backend** após a correção:
   ```bash
   # Pare o servidor (Ctrl+C)
   # Inicie novamente
   .\venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```
   
   ⚠️ **O servidor DEVE ser reiniciado** para que as mudanças tenham efeito!

2. **Limpe o cache do navegador** e faça login novamente:
   - Pressione `Ctrl+Shift+Delete` no navegador
   - Limpe cache e cookies
   - Faça logout e login novamente no Supabase

3. **Verifique se o token está sendo renovado automaticamente**

4. **Se o erro persistir após reiniciar**, verifique:
   - Se o arquivo `supabase_provider.py` foi atualizado corretamente
   - Se há algum cache do Python (tente deletar `__pycache__` se existir)
   - Se o servidor está usando a versão correta do código

---

## ❌ Erro: 401 Unauthorized em todas as requisições

### Possíveis Causas

#### 1. Token não está sendo enviado

**Verificação**:
```typescript
// Adicione logs para debug
const { data: { session } } = await supabase.auth.getSession()
console.log('Session:', session)
console.log('Token:', session?.access_token)

if (!session || !session.access_token) {
  console.error('❌ Nenhum token disponível!')
  // Redirecionar para login
}
```

**Solução**: Certifique-se de que o usuário está logado antes de fazer requisições.

#### 2. Token expirado

**Verificação**:
```typescript
const { data: { session } } = await supabase.auth.getSession()

if (session) {
  const expiresAt = session.expires_at * 1000 // Converte para milissegundos
  const now = Date.now()
  
  if (expiresAt < now) {
    console.error('❌ Token expirado!')
    // Faça refresh ou logout
    await supabase.auth.refreshSession()
  }
}
```

**Solução**: Implemente renovação automática de token ou redirecione para login quando expirar.

#### 3. Backend não está configurado para Supabase

**Verificação**: Verifique se o backend tem `AUTH_PROVIDER=supabase` no `.env`

**Solução**: Peça ao time de backend para verificar a configuração.

---

## ❌ Erro: "Missing Supabase environment variables"

### Causa

As variáveis de ambiente do Supabase não estão configuradas no frontend.

### Solução

1. **Verifique o arquivo `.env.local` ou `.env`** do frontend:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://qnkuxvthwpuqjnlnekns.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **Reinicie o servidor de desenvolvimento** após adicionar variáveis:
   ```bash
   # Next.js
   npm run dev
   
   # Vite
   npm run dev
   ```

3. **Verifique se as variáveis têm o prefixo correto**:
   - Next.js: `NEXT_PUBLIC_`
   - Vite: `VITE_`
   - React puro: Sem prefixo (mas precisa configurar manualmente)

---

## ❌ Erro: "Invalid API key" ou "Invalid credentials"

### Causa

A chave `NEXT_PUBLIC_SUPABASE_ANON_KEY` está incorreta ou não está configurada.

### Solução

1. **Verifique a chave no Supabase Dashboard**:
   - Acesse: https://app.supabase.com/project/qnkuxvthwpuqjnlnekns/settings/api
   - Copie a chave **anon/public** (não a service_role!)

2. **Atualize o `.env`**:
   ```env
   NEXT_PUBLIC_SUPABASE_ANON_KEY=sua_chave_aqui
   ```

3. **Reinicie o servidor de desenvolvimento**

---

## ❌ Erro: "Token não contém organization_id"

### Causa

O usuário não foi migrado corretamente ou não tem `organization_id` no `app_metadata`.

### Verificação

```typescript
// Decodifique o token para verificar (apenas para debug)
const { data: { session } } = await supabase.auth.getSession()
if (session) {
  // O token JWT contém o payload
  const payload = JSON.parse(atob(session.access_token.split('.')[1]))
  console.log('Token payload:', payload)
  console.log('app_metadata:', payload.app_metadata)
  console.log('organization_id:', payload.app_metadata?.organization_id)
}
```

### Solução

1. **Verifique se o usuário foi migrado**:
   - Execute `validate_migration.py` no backend
   - Verifique se o email do usuário está na lista de migrados

2. **Se não foi migrado**, peça ao time de backend para executar a migração

3. **Se foi migrado mas não tem organization_id**, peça ao time de backend para verificar o `app_metadata` no Supabase

---

## ❌ Erro: "Network error" ou CORS

### Causa

Problema de CORS ou URL da API incorreta.

### Verificação

```typescript
// Verifique a URL da API
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
console.log('API URL:', API_URL)

// Teste a conexão
try {
  const response = await fetch(`${API_URL}/health`)
  console.log('Backend está acessível:', response.ok)
} catch (error) {
  console.error('❌ Erro ao conectar com backend:', error)
}
```

### Solução

1. **Verifique a URL da API** no `.env`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. **Verifique se o backend está rodando**:
   ```bash
   # No backend
   curl http://localhost:8000/health
   ```

3. **Verifique CORS no backend**:
   - O backend deve permitir requisições do frontend
   - Verifique `CORS_ORIGINS` no `.env` do backend

---

## ✅ Checklist de Diagnóstico

Antes de reportar um problema, verifique:

- [ ] Variáveis de ambiente do Supabase estão configuradas (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
- [ ] Servidor de desenvolvimento foi reiniciado após mudanças no `.env`
- [ ] Usuário está logado (`supabase.auth.getSession()` retorna uma sessão)
- [ ] Token está sendo enviado no header `Authorization: Bearer <token>`
- [ ] Token não está expirado
- [ ] Backend está rodando e acessível
- [ ] URL da API está correta (`NEXT_PUBLIC_API_URL`)
- [ ] Usuário foi migrado do Clerk para Supabase
- [ ] `organization_id` está presente no token (`app_metadata.organization_id`)

---

## 🔍 Como Debugar Problemas

### 1. Adicionar Logs de Debug

```typescript
// lib/api.ts ou similar
import { supabase } from './supabase'

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    console.error('❌ Nenhuma sessão ativa')
    throw new Error('Usuário não autenticado')
  }
  
  const token = session.access_token
  console.log('📤 Enviando requisição:', endpoint)
  console.log('🔑 Token (primeiros 20 chars):', token.substring(0, 20) + '...')
  
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  })
  
  console.log('📥 Resposta:', response.status, response.statusText)
  
  if (!response.ok) {
    const errorText = await response.text()
    console.error('❌ Erro da API:', errorText)
    throw new Error(`API Error: ${response.statusText}`)
  }
  
  return response.json()
}
```

### 2. Verificar Token no Console

```typescript
// No console do navegador ou em um componente de debug
const { data: { session } } = await supabase.auth.getSession()

if (session) {
  // Decodifica o token (apenas para visualização)
  const parts = session.access_token.split('.')
  const payload = JSON.parse(atob(parts[1]))
  
  console.log('Token Info:', {
    user_id: payload.sub,
    email: payload.email,
    organization_id: payload.app_metadata?.organization_id,
    expires_at: new Date(payload.exp * 1000),
    issued_at: new Date(payload.iat * 1000),
  })
}
```

### 3. Testar Conexão com Backend

```typescript
// Teste simples de conexão
async function testBackendConnection() {
  try {
    const response = await fetch('http://localhost:8000/health')
    const data = await response.json()
    console.log('✅ Backend está acessível:', data)
    return true
  } catch (error) {
    console.error('❌ Erro ao conectar com backend:', error)
    return false
  }
}
```

---

## 📚 Recursos Adicionais

- `FRONTEND_SUPABASE_AUTH.md` - Guia completo de integração
- `TROUBLESHOOTING_AUTH.md` - Troubleshooting do backend
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Supabase JS Client Reference](https://supabase.com/docs/reference/javascript/introduction)

---

## 🆘 Quando Pedir Ajuda

Se você já verificou todos os itens do checklist e o problema persiste:

1. **Colete informações**:
   - Mensagem de erro completa
   - Logs do console do navegador
   - Status da sessão (`supabase.auth.getSession()`)
   - URL da API e variáveis de ambiente (sem expor chaves secretas)

2. **Verifique o backend**:
   - Se o backend está rodando
   - Se `AUTH_PROVIDER=supabase` está configurado
   - Logs do servidor backend

3. **Reporte ao time de backend** com:
   - Descrição do problema
   - Passos para reproduzir
   - Informações coletadas acima

---

**Última atualização**: 2024-12-19  
**Projeto**: Otica API - Migração Clerk → Supabase
