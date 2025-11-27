"""Script para verificar se as configurações do .env estão corretas."""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings
    
    print("=" * 60)
    print("VERIFICAÇÃO DE CONFIGURAÇÃO")
    print("=" * 60)
    print()
    
    # Verifica CLERK_ISSUER
    print("✅ CLERK_ISSUER:")
    print(f"   {settings.CLERK_ISSUER}")
    if "your-clerk-domain" in settings.CLERK_ISSUER:
        print("   ⚠️  ATENÇÃO: Você precisa configurar o CLERK_ISSUER real!")
    print()
    
    # Verifica CLERK_PUBLISHABLE_KEY (opcional)
    if settings.CLERK_PUBLISHABLE_KEY:
        print("✅ CLERK_PUBLISHABLE_KEY:")
        print(f"   {settings.CLERK_PUBLISHABLE_KEY[:20]}...{settings.CLERK_PUBLISHABLE_KEY[-10:]}")
        print()
    
    # Verifica CLERK_SECRET_KEY (opcional)
    if settings.CLERK_SECRET_KEY:
        print("✅ CLERK_SECRET_KEY:")
        print(f"   {settings.CLERK_SECRET_KEY[:10]}...{settings.CLERK_SECRET_KEY[-10:]}")
        print()
    
    # Verifica DATABASE_URL
    print("✅ DATABASE_URL:")
    # Mostra apenas os primeiros caracteres por segurança
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        # Esconde a senha
        parts = db_url.split("@")
        if len(parts) == 2:
            user_part = parts[0].split("//")[-1]
            if ":" in user_part:
                user = user_part.split(":")[0]
                print(f"   postgresql+asyncpg://{user}:***@{parts[1]}")
            else:
                print(f"   {db_url[:50]}...")
        else:
            print(f"   {db_url[:50]}...")
    else:
        print(f"   {db_url[:50]}...")
    print()
    
    # Verifica CORS_ORIGINS
    print("✅ CORS_ORIGINS:")
    for origin in settings.cors_origins_list:
        print(f"   - {origin}")
    print()
    
    print("=" * 60)
    print("✅ Configurações carregadas com sucesso!")
    print("=" * 60)
    print()
    print("Próximos passos:")
    print("1. Verifique se o CLERK_ISSUER está correto")
    print("2. Verifique se o DATABASE_URL está correto")
    print("3. Crie o banco de dados PostgreSQL se ainda não existir")
    print("4. Execute: python scripts/create_tables.py")
    
except Exception as e:
    print("=" * 60)
    print("❌ ERRO AO CARREGAR CONFIGURAÇÕES")
    print("=" * 60)
    print()
    print(f"Erro: {str(e)}")
    print()
    print("Verifique:")
    print("1. Se o arquivo .env existe na raiz de otica-api/")
    print("2. Se todas as variáveis estão definidas no .env")
    print("3. Se não há erros de sintaxe no .env")
    sys.exit(1)

