# Guia de Configuração - Variáveis de Ambiente

## Arquivo .env

O arquivo `.env` foi criado a partir do `.env.example`. Agora você precisa configurar as seguintes variáveis:

## 1. CLERK_ISSUER

**O que é**: URL do seu provedor de autenticação Clerk.

**Como obter**:
1. Acesse o [dashboard do Clerk](https://dashboard.clerk.com)
2. Selecione seu aplicativo
3. Vá em **API Keys** ou **Settings**
4. Copie o **Issuer URL** (formato: `https://seu-dominio.clerk.accounts.dev`)

**Exemplo**:
```
CLERK_ISSUER=https://clerk.otica-app.clerk.accounts.dev
```

**Importante**: 
- Se você ainda não tem uma conta Clerk, crie uma em [clerk.com](https://clerk.com)
- O Clerk oferece um plano gratuito para desenvolvimento

## 2. DATABASE_URL

**O que é**: String de conexão com o banco de dados PostgreSQL.

**Formato**: `postgresql+asyncpg://usuario:senha@host:porta/database`

**Exemplos**:

### Local (PostgreSQL local):
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/otica_db
```

### PostgreSQL em servidor remoto:
```
DATABASE_URL=postgresql+asyncpg://usuario:senha@servidor.com:5432/otica_db
```

### Com SSL:
```
DATABASE_URL=postgresql+asyncpg://usuario:senha@servidor.com:5432/otica_db?ssl=require
```

**Como configurar**:
1. Instale o PostgreSQL se ainda não tiver
2. Crie o banco de dados:
   ```sql
   CREATE DATABASE otica_db;
   ```
3. Ajuste o `.env` com suas credenciais

## 3. CORS_ORIGINS

**O que é**: Lista de origens permitidas para requisições CORS (frontend).

**Formato**: URLs separadas por vírgula (sem espaços extras)

**Exemplos**:

### Desenvolvimento local:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

### Produção:
```
CORS_ORIGINS=https://app.otica.com,https://www.otica.com
```

**Nota**: 
- `localhost:3000` - React/Next.js padrão
- `localhost:5173` - Vite padrão
- Adicione todas as origens do seu frontend

## Verificação

Após configurar o `.env`, você pode testar se está correto:

```powershell
# No diretório otica-api
.\venv\Scripts\python.exe -c "from app.core.config import settings; print('CLERK_ISSUER:', settings.CLERK_ISSUER); print('DATABASE_URL:', settings.DATABASE_URL[:50] + '...'); print('CORS:', settings.cors_origins_list)"
```

## Próximos Passos

1. ✅ Configure o `.env` com suas credenciais
2. Crie o banco de dados PostgreSQL
3. Execute `python scripts/create_tables.py` para criar as tabelas
4. Inicie o servidor: `uvicorn app.main:app --reload`

## Troubleshooting

### Erro: "CLERK_ISSUER is required"
- Verifique se o arquivo `.env` existe na raiz de `otica-api/`
- Verifique se não há espaços extras nas variáveis
- Certifique-se de que não há aspas nas variáveis (exceto se necessário)

### Erro de conexão com banco de dados
- Verifique se o PostgreSQL está rodando
- Confirme usuário, senha e nome do banco
- Teste a conexão manualmente com `psql`

### Erro CORS
- Adicione a origem do seu frontend em `CORS_ORIGINS`
- Verifique se não há espaços extras entre as URLs

