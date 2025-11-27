# Resolver: Token com Aspas do Console

## Problema

Quando você copia o token do console do navegador, pode vir assim:

```
"eyJhbGciOiJSUzI1NiIs..."  ← Com aspas!
```

Ou assim:

```
Bearer "eyJhbGciOiJSUzI1NiIs..."  ← Com Bearer e aspas!
```

## Solução Rápida

Use o script de formatação:

```powershell
.\venv\Scripts\python.exe scripts\format_token.py "seu_token_com_aspas"
```

## Exemplo Prático

### 1. Você copiou do console:
```
"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3QiOnsiaXNzIjoiaHR0cHM6Ly9kYXNoYm9hcmQuY2xlcmsuY29tIiwic2lkIjoic2Vzc18zNjJPN1F6aWhva2FwejNCY2h2UlViZnpkb24iLCJzdWIiOiJ1c2VyXzM1emMwOU9vand5ZVFPNzJMTmdmNU5QQUtqeCJ9LCJhenAiOiJodHRwczovL3Rob3JvdWdoLW11dHQtNy5hY2NvdW50cy5kZXYiLCJleHAiOjE3NjQyMTI4NjEsImZ2YSI6WzEwLDEwXSwiaWF0IjoxNzY0MjEyODAxLCJpc3MiOiJodHRwczovL3Rob3JvdWdoLW11dHQtNy5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3NjQyMTI3OTEsIm8iOnsiaWQiOiJvcmdfMzYyT1lSQmFYTUFuQ2tMbExtcFlxUFdPZTh6Iiwicm9sIjoiYWRtaW4iLCJzbGciOiJ0ZXN0ZS0xNzY0MjAxMjQ2In0sInNpZCI6InNlc3NfMzYya2dYRnF5NzBpVG8ydEE2bTFqSnpmUks0Iiwic3RzIjoiYWN0aXZlIiwic3ViIjoidXNlcl8zNjJqdTNaSkpVWTRhWTNjTzZZQklqSFdDSHoiLCJ2IjoyfQ.NoVmGenwXz8RAn1kWzHPr5au_lWlpQEB8rdb-6H02EhC9Pa5CYm0TFMPfZVv0Q9GV7o0kPmU1NjAL-gNLLFt4zK69Aw-m0pCW-FXBk0rIHBFquM4sjXT9xZJm_w4GCt49a4NQl6_hmbqfDjEnhITaGkpP7I885tmVsEPQpJJrvchQYP2I3kKg-xqjPrQSIES8Zm79a1m-9wvHWz0R4Xd952PqeerniYn_vqCAWTv9YNCDLKKnnWWPj7I8rr7Wd6nAGlc7fKswYIlPodADqo1FBU-fFfAK9IwWiMAGUBgxCc9Ms86XL_8SVuhq3lC02VeBhMAar2jYMzPAYChQlnHXA"
```

### 2. Execute o script:
```powershell
.\venv\Scripts\python.exe scripts\format_token.py "eyJhbGciOiJSUzI1NiIs..."
```

### 3. Copie o token limpo que aparecer

### 4. Cole na documentação OpenAPI → Authorize

## Sobre Impersonation

Se você está usando **"Impersonate User"** no Clerk:

⚠️ **Tokens de impersonation podem não funcionar corretamente!**

### Verificar se é Impersonation

```powershell
.\venv\Scripts\python.exe scripts\check_token_org.py seu_token_aqui
```

Se aparecer "Token é de IMPERSONATION", você precisa:

1. **Sair do modo impersonation** no Clerk Dashboard
2. **Gerar um token normal** (não impersonado)
3. Usar esse token na API

## Fluxo Completo

```powershell
# 1. Pegue o token do console (pode ter aspas)
# 2. Formate o token
.\venv\Scripts\python.exe scripts\format_token.py "token_com_aspas"

# 3. Verifique se tem organization_id
.\venv\Scripts\python.exe scripts\check_token_org.py <token_formatado>

# 4. Se tudo OK, cole na documentação OpenAPI
```

## Dica

Se você está sempre pegando do console, crie um alias:

```powershell
# No PowerShell, adicione ao seu perfil:
function Format-Token {
    param([string]$token)
    .\venv\Scripts\python.exe scripts\format_token.py $token
}

# Uso:
Format-Token "seu_token_com_aspas"
```

