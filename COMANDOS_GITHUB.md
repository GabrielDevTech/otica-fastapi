# Comandos para Criar Repositório no GitHub

## ✅ Commit já foi feito!

61 arquivos foram commitados com sucesso.

## Passo 1: Criar Repositório no GitHub

### Opção A: Via Navegador (Recomendado)

1. Acesse: **https://github.com/new**
2. Preencha:
   - **Repository name**: `projeto-otica` (ou outro nome)
   - **Description**: `Sistema SaaS Multi-tenant para gestão de óticas`
   - **Visibility**: Escolha Public ou Private
   - **NÃO marque** "Initialize with README" (já temos um)
3. Clique em **"Create repository"**

### Opção B: Via Script Interativo

Execute:
```powershell
.\criar_repositorio_github.ps1
```

O script vai pedir:
- Nome do repositório
- Seu username do GitHub
- Visibilidade (public/private)

## Passo 2: Conectar e Fazer Push

Depois de criar o repositório no GitHub, execute:

```powershell
# Substitua SEU_USUARIO pelo seu username do GitHub
# Substitua NOME_REPO pelo nome do repositório que você criou

git branch -M main
git remote add origin https://github.com/SEU_USUARIO/NOME_REPO.git
git push -u origin main
```

### Exemplo:

Se seu username é `gabrieldevtech` e o repositório é `projeto-otica`:

```powershell
git branch -M main
git remote add origin https://github.com/gabrieldevtech/projeto-otica.git
git push -u origin main
```

## Verificação

Depois do push, acesse:
```
https://github.com/SEU_USUARIO/NOME_REPO
```

Você deve ver todos os arquivos do projeto!

## Estrutura Enviada

✅ **memory-bank/** - Toda documentação do Memory Bank
✅ **otica-api/** - Todo código da API
✅ **README.md** - Documentação principal
✅ **projeto.md** - Especificação do projeto
✅ **61 arquivos** no total

## Arquivos NÃO Enviados (por segurança)

❌ `.env` - Variáveis de ambiente
❌ `venv/` - Ambiente virtual
❌ `__pycache__/` - Cache Python

