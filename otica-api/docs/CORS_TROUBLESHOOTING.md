# Troubleshooting CORS - Erro 400 em Requisições OPTIONS

## Problema

Você está recebendo erros `400 Bad Request` em todas as requisições OPTIONS (preflight):

```
INFO:     127.0.0.1:63028 - "OPTIONS /api/v1/stores HTTP/1.1" 400 Bad Request
```

## Causa

Isso geralmente acontece quando:

1. **A origem do frontend não está na lista de origens permitidas**
   - O frontend está rodando em uma porta/URL diferente da configurada
   - O frontend está usando `127.0.0.1` em vez de `localhost` (ou vice-versa)

2. **O middleware CORS não está configurado corretamente**

## Solução

### 1. Verificar a origem do frontend

Abra o console do navegador (F12) e verifique qual URL está sendo usada. Exemplos:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

### 2. Adicionar a origem no `.env`

Edite o arquivo `.env` na raiz do projeto `otica-api`:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080
```

**Importante**: Adicione TODAS as URLs que seu frontend pode usar, incluindo:
- `localhost` e `127.0.0.1`
- Todas as portas possíveis (3000, 5173, 8080, etc.)

### 3. Reiniciar o servidor

Após alterar o `.env`, **reinicie o servidor** para que as mudanças tenham efeito:

```powershell
# Pare o servidor (Ctrl+C)
# Inicie novamente
cd .\otica-api
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### 4. Verificar se funcionou

Após reiniciar, as requisições OPTIONS devem retornar `200 OK` em vez de `400 Bad Request`:

```
INFO:     127.0.0.1:63028 - "OPTIONS /api/v1/stores HTTP/1.1" 200 OK
```

## Configuração Atual

O arquivo `app/main.py` já está configurado para:

- ✅ Permitir métodos: GET, POST, PUT, PATCH, DELETE, OPTIONS
- ✅ Permitir todos os headers: `["*"]`
- ✅ Permitir credenciais: `allow_credentials=True`
- ✅ Expor todos os headers: `expose_headers=["*"]`

A única coisa que precisa ser ajustada é a **lista de origens permitidas** no `.env`.

## Exemplo Completo de `.env`

```env
# Clerk
CLERK_ISSUER=https://seu-clerk.clerk.accounts.dev

# Database
DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/otica_db

# CORS - Adicione TODAS as URLs do seu frontend
# Inclua localhost, 127.0.0.1 e o IP da sua rede local (ex: 192.168.0.100)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080,http://192.168.0.100:3000
```

## Solução com Proxy Next.js

Se você está usando um **proxy Next.js** (como `app/api/backend/[...path]/route.ts`), há dois cenários:

### Cenário 1: Proxy funcionando corretamente
- O proxy Next.js faz requisições do **servidor Next.js** para o backend
- A origem vista pelo backend será `http://localhost:3000` ou `http://192.168.0.100:3000` (dependendo de onde o Next.js está rodando)
- **Solução**: Adicione a origem do servidor Next.js na lista CORS

### Cenário 2: Proxy não está funcionando
- O frontend ainda está fazendo requisições diretas ao backend
- A origem será a URL do navegador (ex: `http://192.168.0.100:3000`)
- **Solução**: Adicione a URL exata do frontend na lista CORS

### Como verificar qual cenário está acontecendo

1. Abra o **Console do Navegador** (F12 → Network)
2. Faça uma requisição
3. Veja qual URL está sendo chamada:
   - Se for `/api/backend/...` → Proxy está funcionando
   - Se for `http://localhost:8000/...` → Requisição direta (proxy não está funcionando)

### Solução Recomendada

Adicione **ambas** as URLs na lista CORS:
- URL do frontend (onde o navegador está acessando)
- URL do servidor Next.js (se diferente)

## Nota Importante

⚠️ **Em produção**, NUNCA use `["*"]` como origem quando `allow_credentials=True`. Sempre especifique as origens exatas do seu frontend.

## Ainda com problemas?

1. Verifique o console do navegador para ver a mensagem de erro completa
2. Verifique os logs do servidor para ver qual origem está sendo rejeitada
3. Certifique-se de que o arquivo `.env` está na raiz de `otica-api/`
4. Certifique-se de que reiniciou o servidor após alterar o `.env`

