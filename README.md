# Projeto Ótica - Sistema SaaS Multi-tenant

Sistema de gestão para óticas com arquitetura multi-tenant, autenticação via Clerk e controle de acesso baseado em roles.

## 📁 Estrutura do Projeto

```
projeto-otica/
├── memory-bank/          # Documentação do projeto (Memory Bank)
│   ├── projectbrief.md   # Visão geral e objetivos
│   ├── productContext.md # Contexto do produto
│   ├── activeContext.md  # Contexto atual e próximos passos
│   ├── systemPatterns.md # Arquitetura e padrões
│   ├── techContext.md    # Tecnologias e configurações
│   └── progress.md      # Progresso e status
├── otica-api/            # API FastAPI
│   ├── app/             # Código da aplicação
│   ├── docs/            # Documentação técnica
│   ├── scripts/        # Scripts utilitários
│   └── requirements.txt # Dependências Python
└── projeto.md          # Especificação do projeto
```

## 🚀 Tecnologias

- **Python 3.14**
- **FastAPI** - Framework web
- **PostgreSQL** - Banco de dados
- **SQLAlchemy** (async) - ORM
- **Clerk** - Autenticação e gerenciamento de usuários
- **Pydantic** - Validação de dados

## 📚 Documentação

### Memory Bank
Documentação completa do projeto em `memory-bank/`:
- Visão geral e objetivos
- Contexto do produto
- Arquitetura e padrões
- Tecnologias utilizadas
- Progresso atual

### Documentação Técnica
Documentação técnica detalhada em `otica-api/docs/`:
- Autenticação com Clerk
- Controle de acesso (RBAC)
- Configuração
- Troubleshooting
- Guias de uso

## 🔧 Configuração

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd projeto-otica
   ```

2. **Configure o ambiente Python**
   ```bash
   cd otica-api
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   .\venv\Scripts\activate  # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure variáveis de ambiente**
   ```bash
   cp .env.example .env
   # Edite .env com suas configurações
   ```

5. **Configure o banco de dados**
   ```bash
   python scripts/create_tables.py
   ```

6. **Inicie o servidor**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📖 Documentação da API

Após iniciar o servidor, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Autenticação

O sistema usa Clerk para autenticação:
- Tokens JWT validados via JWKS
- Multi-tenancy por `organization_id`
- Controle de acesso baseado em roles (RBAC)

## 👥 Roles

- **ADMIN**: Acesso total
- **MANAGER**: Gerenciamento e visualização
- **STAFF**: Visualização e operações básicas
- **ASSISTANT**: Acesso limitado

## 📝 Licença

[Adicione sua licença aqui]

## 👤 Autor

[Seu nome]

