# Como Criar Repositório no GitHub

## Passo 1: Configurar Git (se ainda não configurou)

Configure seu nome e email no Git:

```powershell
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@example.com"
```

Ou apenas para este repositório:

```powershell
git config user.name "Seu Nome"
git config user.email "seu.email@example.com"
```

## Passo 2: Fazer Commit

Depois de configurar, faça o commit:

```powershell
git commit -m "Initial commit: Projeto Ótica - Sistema SaaS Multi-tenant com FastAPI e Clerk"
```

## Passo 3: Criar Repositório no GitHub

### Opção A: Via Site do GitHub (Recomendado)

1. Acesse: https://github.com/new
2. Preencha:
   - **Repository name**: `projeto-otica` (ou o nome que preferir)
   - **Description**: "Sistema SaaS Multi-tenant para gestão de óticas"
   - **Visibility**: Escolha Public ou Private
   - **NÃO marque** "Initialize with README" (já temos um)
3. Clique em **"Create repository"**

### Opção B: Via GitHub CLI (se tiver instalado)

```powershell
gh repo create projeto-otica --public --description "Sistema SaaS Multi-tenant para gestão de óticas" --source=. --remote=origin --push
```

## Passo 4: Conectar e Fazer Push

Depois de criar o repositório no GitHub, execute:

```powershell
# Adicione o remote (substitua SEU_USUARIO pelo seu username do GitHub)
git remote add origin https://github.com/SEU_USUARIO/projeto-otica.git

# Ou se preferir SSH:
# git remote add origin git@github.com:SEU_USUARIO/projeto-otica.git

# Faça o push
git branch -M main
git push -u origin main
```

## Verificação

Depois do push, acesse:
```
https://github.com/SEU_USUARIO/projeto-otica
```

Você deve ver todos os arquivos do projeto!

## Estrutura que será enviada

✅ **memory-bank/** - Toda a documentação do Memory Bank
✅ **otica-api/** - Todo o código da API (exceto venv e .env)
✅ **README.md** - Documentação principal
✅ **.gitignore** - Arquivos ignorados (venv, .env, __pycache__, etc.)

## Arquivos que NÃO serão enviados (por segurança)

❌ `.env` - Variáveis de ambiente (sensíveis)
❌ `venv/` - Ambiente virtual Python
❌ `__pycache__/` - Cache do Python
❌ Arquivos temporários

## Próximos Passos

Depois de criar o repositório:

1. Adicione um `.env.example` com exemplos (sem valores reais)
2. Configure GitHub Actions (se necessário)
3. Adicione badges no README
4. Configure branch protection (se for equipe)

