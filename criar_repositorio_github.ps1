# Script para criar repositório no GitHub e fazer push
# Execute: .\criar_repositorio_github.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Criar Repositório no GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Solicitar nome do repositório
$repoName = Read-Host "Digite o nome do repositório (ex: projeto-otica)"
if ([string]::IsNullOrWhiteSpace($repoName)) {
    $repoName = "projeto-otica"
    Write-Host "Usando nome padrão: $repoName" -ForegroundColor Yellow
}

# Solicitar username do GitHub
$username = Read-Host "Digite seu username do GitHub"
if ([string]::IsNullOrWhiteSpace($username)) {
    Write-Host "Erro: Username é obrigatório!" -ForegroundColor Red
    exit 1
}

# Escolher visibilidade
Write-Host ""
Write-Host "Escolha a visibilidade:" -ForegroundColor Yellow
Write-Host "1. Public (público)"
Write-Host "2. Private (privado)"
$visibility = Read-Host "Digite 1 ou 2 (padrão: 1)"
if ($visibility -ne "2") {
    $visibility = "public"
} else {
    $visibility = "private"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Próximos Passos:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Abra seu navegador e acesse:" -ForegroundColor Yellow
Write-Host "   https://github.com/new" -ForegroundColor Green
Write-Host ""
Write-Host "2. Preencha:" -ForegroundColor Yellow
Write-Host "   Repository name: $repoName" -ForegroundColor White
Write-Host "   Description: Sistema SaaS Multi-tenant para gestão de óticas" -ForegroundColor White
Write-Host "   Visibility: $visibility" -ForegroundColor White
Write-Host "   NÃO marque 'Initialize with README'" -ForegroundColor Red
Write-Host ""
Write-Host "3. Clique em 'Create repository'" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Depois de criar, pressione ENTER aqui para continuar..." -ForegroundColor Cyan
Read-Host

Write-Host ""
Write-Host "Configurando remote e fazendo push..." -ForegroundColor Yellow
Write-Host ""

# Renomear branch para main
git branch -M main

# Adicionar remote
$remoteUrl = "https://github.com/$username/$repoName.git"
Write-Host "Adicionando remote: $remoteUrl" -ForegroundColor Cyan
git remote add origin $remoteUrl

# Verificar se já existe remote
$existingRemote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote add origin $remoteUrl
} else {
    Write-Host "Remote já existe. Atualizando..." -ForegroundColor Yellow
    git remote set-url origin $remoteUrl
}

# Fazer push
Write-Host ""
Write-Host "Fazendo push para GitHub..." -ForegroundColor Yellow
Write-Host ""
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ Sucesso!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repositório criado e código enviado!" -ForegroundColor Green
    Write-Host "Acesse: https://github.com/$username/$repoName" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ Erro ao fazer push" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique:" -ForegroundColor Yellow
    Write-Host "1. Se o repositório foi criado no GitHub" -ForegroundColor White
    Write-Host "2. Se você tem permissão para fazer push" -ForegroundColor White
    Write-Host "3. Se sua autenticação está configurada" -ForegroundColor White
    Write-Host ""
    Write-Host "Para fazer push manualmente:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor White
    Write-Host ""
}

