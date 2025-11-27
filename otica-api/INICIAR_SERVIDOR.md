# Como Iniciar o Servidor

## Comando Básico

```powershell
cd otica-api
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Comando com Opções

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## URLs Disponíveis

Após iniciar o servidor:

- **API**: http://localhost:8000
- **Documentação Interativa (Swagger)**: http://localhost:8000/docs
- **Documentação Alternativa (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## Endpoints Disponíveis

### Staff (Equipe)

- `GET /api/v1/staff` - Lista membros da equipe
- `GET /api/v1/staff/stats` - Estatísticas da equipe
- `POST /api/v1/staff` - Cria novo membro

**Nota**: Todos os endpoints requerem autenticação via Bearer Token (Clerk JWT).

## Testando a API

### 1. Health Check (sem autenticação)

```powershell
curl http://localhost:8000/health
```

### 2. Documentação Interativa

Abra no navegador: http://localhost:8000/docs

### 3. Testar Endpoints (com token Clerk)

Você precisará de um token JWT válido do Clerk. Use a documentação interativa em `/docs` para testar com autenticação.

## Troubleshooting

### Erro: "Module not found"
- Certifique-se de estar no diretório `otica-api`
- Verifique se o ambiente virtual está ativado

### Erro: "Address already in use"
- Outro processo está usando a porta 8000
- Use outra porta: `--port 8001`

### Erro de conexão com banco
- Verifique se o `.env` está configurado corretamente
- Execute: `python scripts/verify_config.py`

