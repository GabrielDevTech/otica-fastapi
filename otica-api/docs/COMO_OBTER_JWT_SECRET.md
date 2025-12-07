# Como Obter o JWT Secret do Supabase

## 🎯 Problema Resolvido

O erro "Invalid audience" estava ocorrendo porque estávamos usando `SUPABASE_SERVICE_KEY` (que é um JWT) como chave secreta para validar tokens de acesso. 

**A solução**: Usar o **JWT Secret** correto do projeto Supabase, que é uma string aleatória (não um token) usada especificamente para assinar/verificar tokens de acesso.

---

## 📋 Passo a Passo

### 1. Acesse o Supabase Dashboard

1. Vá para: https://app.supabase.com
2. Faça login na sua conta
3. Selecione o projeto **otica** (ou o projeto correto)

### 2. Navegue até as Configurações de API

1. No menu lateral esquerdo, clique em **Settings** (ícone de engrenagem ⚙️)
2. Clique em **API** no submenu

### 3. Encontre o JWT Secret

1. Role a página até a seção **JWT Settings**
2. Você verá um campo chamado **JWT Secret**
3. Clique no ícone de **olho** 👁️ para revelar o secret (ou no botão "Reveal")
4. **Copie o valor completo** (é uma string longa e aleatória)

### 4. Adicione ao arquivo `.env`

Abra o arquivo `.env` na raiz do projeto `otica-api` e adicione:

```env
SUPABASE_JWT_SECRET=0+7fYKoclzPmuwosXo3F30eCUYsuW+vZGDIp6VWYZ8MpvS+P9Oe4pBrS4VfJw8lSVv0/QDVLYop74DaDLNSHUA==
```

**Exemplo**:
```env
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters-long
```

### 5. Reinicie o Servidor

Após adicionar a variável, **reinicie o servidor backend**:

```powershell
# Pare o servidor (Ctrl+C)
# Inicie novamente
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

---

## ⚠️ Importante

### Diferença entre SERVICE_KEY e JWT_SECRET

- **`SUPABASE_SERVICE_KEY`**: 
  - É um **JWT pré-assinado** (começa com `eyJ...`)
  - Usado para operações admin no Supabase
  - **NÃO deve ser usado** para validar tokens de acesso de usuários

- **`SUPABASE_JWT_SECRET`**:
  - É uma **string aleatória** (não é um token)
  - Usado especificamente para assinar/verificar tokens de acesso (`access_token`)
  - **DEVE ser usado** para validar tokens HS256

---

## ✅ Verificação

Após configurar, teste novamente:

```powershell
.\venv\Scripts\python.exe scripts\test_token_api.py
```

Se tudo estiver correto, você deve ver:
- ✅ Assinatura válida (HS256)
- ✅ Requisições à API bem-sucedidas

---

## 🔒 Segurança

- **NUNCA** commite o `SUPABASE_JWT_SECRET` no Git
- Mantenha o `.env` no `.gitignore`
- Use variáveis de ambiente em produção
- Rotacione o JWT Secret periodicamente se necessário

---

## 📚 Referências

- [Supabase JWT Settings](https://supabase.com/docs/guides/auth/jwts)
- [Supabase Dashboard - API Settings](https://app.supabase.com/project/_/settings/api)

---

**Última atualização**: 2024-12-19  
**Status**: Solução implementada - Requer configuração do JWT Secret
