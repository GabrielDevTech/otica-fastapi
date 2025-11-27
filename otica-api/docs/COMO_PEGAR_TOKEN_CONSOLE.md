# Como Pegar Token do Console do Navegador

## Problema Comum

Quando você copia o token do console do navegador, pode vir com:
- ✅ Aspas extras: `"eyJhbGciOiJSUzI1NiIs..."`
- ✅ Espaços: `" eyJhbGciOiJSUzI1NiIs... "`
- ✅ Formato JSON: `{"token": "eyJhbGciOiJSUzI1NiIs..."}`
- ✅ Bearer prefix: `Bearer "eyJhbGciOiJSUzI1NiIs..."`

## Solução Rápida

Use o script de formatação:

```powershell
.\venv\Scripts\python.exe scripts\format_token.py "seu_token_com_aspas_aqui"
```

O script remove automaticamente:
- Aspas simples e duplas
- Espaços em branco
- Prefixo "Bearer"
- Caracteres inválidos

## Como Pegar Token Corretamente

### Método 1: Console do Navegador (Clerk)

```javascript
// No console do navegador (F12)
const { getToken } = window.Clerk || {};
if (getToken) {
  getToken().then(token => {
    console.log("Token limpo:", token);
    // Copie este token (sem aspas)
  });
}
```

### Método 2: localStorage/sessionStorage

```javascript
// No console do navegador
// Clerk geralmente armazena em:
localStorage.getItem('__clerk_db_jwt') 
// ou
sessionStorage.getItem('__clerk_db_jwt')
```

### Método 3: Network Tab

1. Abra **DevTools** (F12)
2. Vá em **Network**
3. Faça uma requisição autenticada
4. Clique na requisição
5. Vá em **Headers** → **Authorization**
6. Copie o token (sem "Bearer ")

## Impersonation (Impersonar Usuário)

Se você está usando **impersonation** no Clerk:

⚠️ **Tokens de impersonation podem ter comportamento diferente!**

### Verificar se é Impersonation

No payload do token, procure por:
```json
{
  "act": {
    "sub": "user_xxx"  // ← Usuário original
  },
  "sub": "user_yyy"    // ← Usuário impersonado
}
```

Se tiver `act`, é um token de impersonation.

### Solução

1. **Saia do modo impersonation** no Clerk Dashboard
2. **Gere um token normal** (não impersonado)
3. Use esse token na API

## Formato Correto do Token

O token JWT deve ter **3 partes** separadas por ponto:

```
eyJhbGciOiJSUzI1NiIs...  ← Header (base64url)
.
eyJhY3QiOnsiaXNzIjoi...  ← Payload (base64url)
.
NoVmGenwXz8RAn1kWzH...   ← Signature (base64url)
```

## Usar na Documentação OpenAPI

### Opção 1: Token Limpo

1. Cole apenas o token (sem aspas, sem "Bearer")
2. O sistema adiciona "Bearer " automaticamente

### Opção 2: Com Bearer

1. Cole: `Bearer eyJhbGciOiJSUzI1NiIs...`
2. Funciona também

## Script de Formatação

Criei um script para limpar tokens automaticamente:

```powershell
# Token com aspas
.\venv\Scripts\python.exe scripts\format_token.py '"eyJhbGciOiJSUzI1NiIs..."'

# Token com Bearer e aspas
.\venv\Scripts\python.exe scripts\format_token.py 'Bearer "eyJhbGciOiJSUzI1NiIs..."'

# Token normal (também funciona)
.\venv\Scripts\python.exe scripts\format_token.py eyJhbGciOiJSUzI1NiIs...
```

## Verificar Token Formatado

Depois de formatar, verifique se tem organization_id:

```powershell
.\venv\Scripts\python.exe scripts\check_token_org.py <token_formatado>
```

## Exemplo Completo

```powershell
# 1. Pegue o token do console (pode ter aspas)
$tokenComAspas = '"eyJhbGciOiJSUzI1NiIs..."'

# 2. Formate o token
.\venv\Scripts\python.exe scripts\format_token.py $tokenComAspas

# 3. Copie o token limpo que aparecer

# 4. Cole na documentação OpenAPI → Authorize

# 5. Teste o endpoint
```

## Dicas

- ✅ Sempre use o script `format_token.py` se copiar do console
- ✅ Verifique se o token tem 3 partes (header.payload.signature)
- ✅ Se usar impersonation, gere token normal
- ✅ Tokens expiram em ~1 hora, gere novo se necessário

