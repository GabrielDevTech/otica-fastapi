# Solução CORS com Proxy Next.js

## Problema

Mesmo usando um proxy Next.js (`app/api/backend/[...path]/route.ts`), ainda há erros de CORS.

## Por que isso acontece?

O proxy Next.js resolve o problema de CORS **entre o navegador e o Next.js**, mas:

1. **O Next.js ainda precisa fazer requisições ao backend FastAPI**
2. **Essas requisições têm uma origem** (a URL do servidor Next.js)
3. **O backend precisa aceitar essa origem** na lista CORS

## Solução

### 1. Identificar a origem do servidor Next.js

O servidor Next.js pode estar rodando em:
- `http://localhost:3000` (desenvolvimento local)
- `http://192.168.0.100:3000` (acesso pela rede local)
- `http://127.0.0.1:3000` (loopback)

### 2. Adicionar a origem no backend

Edite o arquivo `.env` do backend (`otica-api/.env`):

```env
# CORS - Inclua TODAS as URLs possíveis
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.0.100:3000
```

**Importante**: Adicione **todas** as URLs que o Next.js pode usar, incluindo:
- `localhost` e `127.0.0.1`
- IP da rede local (ex: `192.168.0.100`)
- Qualquer outra URL que você acesse o frontend

### 3. Reiniciar o backend

Após alterar o `.env`, **reinicie o servidor FastAPI**:

```powershell
# Pare o servidor (Ctrl+C)
cd .\otica-api
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### 4. Verificar o proxy Next.js

Certifique-se de que o proxy está configurado corretamente:

**Arquivo**: `app/api/backend/[...path]/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'POST');
}

// ... outros métodos (PUT, PATCH, DELETE)

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const path = pathSegments.join('/');
  const url = `${backendUrl}/api/v1/${path}`;
  
  // Copiar headers importantes (especialmente Authorization)
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers['Authorization'] = authHeader;
  }
  
  // Fazer requisição ao backend
  const response = await fetch(url, {
    method,
    headers,
    body: method !== 'GET' ? await request.text() : undefined,
  });
  
  return NextResponse.json(await response.json(), {
    status: response.status,
  });
}
```

### 5. Verificar a configuração do frontend

**Arquivo**: `lib/api-config.ts` (ou similar)

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Se for localhost:8000, usar proxy
const useProxy = API_URL.includes('localhost:8000') || API_URL.includes('127.0.0.1:8000');

export function getApiUrl(path: string): string {
  if (useProxy) {
    return `/api/backend/${path}`;
  }
  return `${API_URL}/api/v1/${path}`;
}
```

## Checklist de Verificação

- [ ] Backend FastAPI está rodando em `localhost:8000`
- [ ] Frontend Next.js está rodando (ex: `http://192.168.0.100:3000`)
- [ ] Arquivo `.env` do backend tem a origem do Next.js na lista CORS
- [ ] Backend foi reiniciado após alterar o `.env`
- [ ] Proxy Next.js está configurado corretamente
- [ ] Frontend está usando o proxy (verificar no Network do navegador)

## Debug

### Verificar logs do backend

No terminal do backend, você deve ver:
```
INFO:     127.0.0.1:xxxxx - "OPTIONS /api/v1/..." 200 OK
```

Se ainda estiver vendo `400 Bad Request`, a origem não está na lista.

### Verificar no navegador

1. Abra o **Console do Navegador** (F12)
2. Vá para a aba **Network**
3. Faça uma requisição
4. Veja:
   - **Request URL**: Deve ser `/api/backend/...` (proxy) ou `http://localhost:8000/...` (direto)
   - **Status**: Deve ser `200 OK` ou `401 Unauthorized` (não `CORS error`)

### Erros comuns

1. **"CORS policy: No 'Access-Control-Allow-Origin' header"**
   - A origem não está na lista CORS do backend
   - **Solução**: Adicione a URL exata na lista CORS

2. **"Network Error" ou "Failed to fetch"**
   - Backend não está rodando
   - **Solução**: Verifique se o servidor FastAPI está ativo

3. **"401 Unauthorized"**
   - Token não está sendo enviado corretamente
   - **Solução**: Verifique se o proxy está copiando o header `Authorization`

## Solução Temporária para Desenvolvimento

Se você precisa de uma solução rápida para desenvolvimento, pode permitir todas as origens (⚠️ **NUNCA em produção**):

**Arquivo**: `app/main.py`

```python
# ⚠️ APENAS PARA DESENVOLVIMENTO
# Em produção, sempre use origens específicas
import os

if os.getenv("ENVIRONMENT") == "development":
    cors_origins = ["*"]
    allow_credentials = False  # Não pode usar "*" com credentials=True
else:
    cors_origins = settings.cors_origins_list
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

**⚠️ IMPORTANTE**: Esta solução **desabilita** `allow_credentials`, o que pode quebrar a autenticação. Use apenas para testes rápidos.

