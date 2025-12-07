# Guia Frontend: Integração com Supabase Authentication

Este documento explica tudo que o **frontend** precisa saber para integrar com Supabase Authentication após a migração do Clerk.

## 📋 O que Mudou?

- **Antes**: Frontend usava Clerk para autenticação
- **Agora**: Frontend deve usar Supabase Authentication
- **Backend**: Continua funcionando da mesma forma (mesma interface de API)

## 🔑 Variáveis de Ambiente para o Frontend

### Variáveis Obrigatórias

Adicione ao arquivo `.env` do seu frontend (ou `.env.local`, `.env.production`, etc.):

```env
# Supabase - Configuração do Projeto
NEXT_PUBLIC_SUPABASE_URL=https://qnkuxvthwpuqjnlnekns.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFua3V4dnRod3B1cWpubG5la25zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxMTQwNTgsImV4cCI6MjA3OTY5MDA1OH0.zXoJ3kGSpeI_J_SjRWgptZIk-0ZrXd9CjyVY7c1CWE0

# API Backend
NEXT_PUBLIC_API_URL=http://localhost:8000  # ou sua URL de produção
```

### ⚠️ Importante sobre as Chaves

- ✅ **NEXT_PUBLIC_SUPABASE_URL**: Pode ser pública (já é pública)
- ✅ **NEXT_PUBLIC_SUPABASE_ANON_KEY**: Pode ser pública (é segura para frontend)
- ❌ **SUPABASE_SERVICE_KEY**: **NUNCA** exponha no frontend! É apenas para backend.

## 📦 Instalação de Dependências

### Para React/Next.js

```bash
npm install @supabase/supabase-js
# ou
yarn add @supabase/supabase-js
```

### Para Vue.js

```bash
npm install @supabase/supabase-js
# ou
yarn add @supabase-js/vue
```

### Para outros frameworks

Consulte: https://supabase.com/docs/guides/getting-started/quickstarts

## 🔧 Configuração do Cliente Supabase

### Exemplo: React/Next.js

Crie um arquivo `lib/supabase.ts` (ou similar):

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### Exemplo: Vue.js

```typescript
// plugins/supabase.ts
import { createClient } from '@supabase/supabase-js'

export default defineNuxtPlugin(() => {
  const supabaseUrl = useRuntimeConfig().public.supabaseUrl
  const supabaseAnonKey = useRuntimeConfig().public.supabaseAnonKey

  const supabase = createClient(supabaseUrl, supabaseAnonKey)

  return {
    provide: {
      supabase
    }
  }
})
```

## 🔐 Autenticação no Frontend

### 1. Login com Email/Senha

```typescript
import { supabase } from '@/lib/supabase'

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'senha123'
})

if (error) {
  console.error('Erro no login:', error)
} else {
  // Login bem-sucedido
  const token = data.session?.access_token
  // Use este token nas requisições para a API
}
```

### 2. Obter Token JWT

```typescript
// Após login, obtenha o token
const { data: { session } } = await supabase.auth.getSession()

if (session) {
  const token = session.access_token
  
  // Use nas requisições HTTP
  const response = await fetch('http://localhost:8000/api/v1/staff', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
}
```

### 3. Verificar Sessão Ativa

```typescript
// Verificar se usuário está logado
const { data: { session } } = await supabase.auth.getSession()

if (session) {
  // Usuário está logado
  console.log('User ID:', session.user.id)
  console.log('Email:', session.user.email)
}
```

### 4. Logout

```typescript
const { error } = await supabase.auth.signOut()

if (error) {
  console.error('Erro no logout:', error)
} else {
  // Logout bem-sucedido
}
```

### 5. Escutar Mudanças de Autenticação

```typescript
// Escutar mudanças na sessão (login/logout)
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    console.log('Usuário logou:', session?.user.email)
    // Atualizar estado da aplicação
  } else if (event === 'SIGNED_OUT') {
    console.log('Usuário deslogou')
    // Limpar estado da aplicação
  }
})
```

## 🔄 Integração com a API Backend

### Configurar Cliente HTTP

```typescript
// lib/api.ts
import { supabase } from './supabase'

async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token || null
}

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
) {
  const token = await getAuthToken()
  
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  })
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`)
  }
  
  return response.json()
}

// Exemplo de uso
export async function getStaff() {
  return apiRequest('/api/v1/staff')
}
```

## 📝 Estrutura do Token JWT

O token do Supabase contém:

```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "app_metadata": {
    "organization_id": "org_3681K8KpYEaeTqOAnBIVDeDqoqF"
  },
  "user_metadata": {
    "full_name": "Nome Completo"
  },
  "iat": 1234567890,
  "exp": 1234571490
}
```

**Importante**: O `organization_id` está em `app_metadata.organization_id` e é usado pelo backend para isolamento multi-tenant.

## 🎯 Fluxo Completo de Autenticação

### 1. Usuário faz Login

```typescript
// Login no Supabase
const { data, error } = await supabase.auth.signInWithPassword({
  email: email,
  password: password
})

if (error) {
  // Mostrar erro para o usuário
  return
}

// Login bem-sucedido
const token = data.session.access_token
```

### 2. Usar Token nas Requisições

```typescript
// Todas as requisições para a API devem incluir o token
const response = await fetch('/api/v1/staff', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### 3. Backend Valida Token

- Backend recebe o token
- Valida via JWKS do Supabase
- Extrai `organization_id` de `app_metadata.organization_id`
- Retorna dados filtrados por organização

## 🔄 Migração do Clerk para Supabase

### O que Precisa Mudar no Frontend

#### Antes (Clerk):

```typescript
import { useAuth } from '@clerk/nextjs'

const { getToken } = useAuth()
const token = await getToken()

fetch('/api/v1/staff', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

#### Agora (Supabase):

```typescript
import { supabase } from '@/lib/supabase'

const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token

fetch('/api/v1/staff', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### Componentes que Precisam Atualizar

1. **Login/Logout**: Trocar Clerk por Supabase
2. **Obter Token**: Usar `supabase.auth.getSession()` ao invés de `getToken()`
3. **Verificar Autenticação**: Usar `supabase.auth.getSession()` ou `onAuthStateChange()`
4. **Proteção de Rotas**: Verificar sessão do Supabase

## 📚 Exemplos Completos

### Hook React para Autenticação

```typescript
// hooks/useAuth.ts
import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import type { Session, User } from '@supabase/supabase-js'

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Verificar sessão inicial
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Escutar mudanças
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { data, error }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  }

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
  }

  return {
    session,
    user,
    loading,
    signIn,
    signOut,
    getToken,
  }
}
```

### Componente de Login

```typescript
// components/LoginForm.tsx
import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'

export function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const { signIn } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const { error } = await signIn(email, password)

    if (error) {
      setError(error.message)
    } else {
      // Redirecionar ou atualizar UI
      window.location.href = '/dashboard'
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Senha"
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit">Entrar</button>
    </form>
  )
}
```

### Proteção de Rotas (Next.js)

```typescript
// middleware.ts ou componente de proteção
import { supabase } from '@/lib/supabase'
import { redirect } from 'next/navigation'

export async function requireAuth() {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    redirect('/login')
  }
  
  return session
}

// Uso em página protegida
export default async function ProtectedPage() {
  const session = await requireAuth()
  
  return (
    <div>
      <h1>Página Protegida</h1>
      <p>Email: {session.user.email}</p>
    </div>
  )
}
```

## 🔗 URLs e Endpoints

### Supabase

- **Project URL**: `https://qnkuxvthwpuqjnlnekns.supabase.co`
- **Auth Endpoint**: `https://qnkuxvthwpuqjnlnekns.supabase.co/auth/v1`
- **JWKS**: `https://qnkuxvthwpuqjnlnekns.supabase.co/auth/v1/.well-known/jwks.json`

### API Backend

- **Desenvolvimento**: `http://localhost:8000`
- **Produção**: (configure conforme seu ambiente)

## ⚠️ Diferenças Importantes: Clerk vs Supabase

| Aspecto | Clerk | Supabase |
|---------|-------|----------|
| **Obter Token** | `getToken()` | `session.access_token` |
| **Verificar Sessão** | `useAuth().isSignedIn` | `supabase.auth.getSession()` |
| **Login** | `signIn()` | `signInWithPassword()` |
| **Logout** | `signOut()` | `signOut()` |
| **Escutar Mudanças** | `useAuth()` hook | `onAuthStateChange()` |
| **Organization ID** | No token (`org_id`) | No token (`app_metadata.organization_id`) |

## 🐛 Troubleshooting

### Erro: "Missing Supabase environment variables"

- Verifique se as variáveis estão no `.env` com prefixo `NEXT_PUBLIC_` (ou equivalente)
- Reinicie o servidor de desenvolvimento após adicionar variáveis

### Erro: "Invalid API key"

- Verifique se `NEXT_PUBLIC_SUPABASE_ANON_KEY` está correto
- Não use `SUPABASE_SERVICE_KEY` no frontend!

### Token não funciona na API

- Verifique se o token está sendo enviado no header: `Authorization: Bearer <token>`
- Verifique se o backend está configurado com `AUTH_PROVIDER=supabase`
- Verifique se o token não expirou (tokens JWT têm expiração)

### Usuário não tem organization_id

- Verifique se o usuário foi migrado corretamente
- Verifique se `app_metadata.organization_id` está configurado no Supabase
- Execute `validate_migration.py` para verificar

## 📚 Recursos Adicionais

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Supabase JS Client](https://supabase.com/docs/reference/javascript/introduction)
- [Supabase React Guide](https://supabase.com/docs/guides/getting-started/quickstarts/reactjs)
- [Supabase Next.js Guide](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)

## ✅ Checklist de Implementação

- [ ] Instalar `@supabase/supabase-js`
- [ ] Adicionar variáveis de ambiente (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
- [ ] Criar cliente Supabase
- [ ] Substituir login do Clerk por Supabase
- [ ] Atualizar obtenção de token
- [ ] Atualizar verificação de sessão
- [ ] Atualizar logout
- [ ] Testar autenticação completa
- [ ] Testar requisições para API backend
- [ ] Validar que `organization_id` está sendo enviado corretamente

---

**Última atualização**: 2024-12-19  
**Projeto**: Otica API - Migração Clerk → Supabase
