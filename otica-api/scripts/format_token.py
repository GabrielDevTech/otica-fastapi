"""
Script para formatar e limpar tokens JWT do console do navegador.

Remove aspas, espaços e caracteres extras que podem vir ao copiar do console.
"""
import sys
import re

def clean_token(token: str) -> str:
    """
    Remove aspas, espaços e caracteres extras do token.
    """
    # Remove aspas simples e duplas
    token = token.strip().strip('"').strip("'")
    
    # Remove espaços em branco
    token = token.strip()
    
    # Remove "Bearer " se estiver presente
    token = re.sub(r'^Bearer\s+', '', token, flags=re.IGNORECASE)
    
    # Remove qualquer caractere que não seja válido em JWT (base64url)
    # JWT válido: letras, números, -, _, .
    token = re.sub(r'[^A-Za-z0-9\-_.]', '', token)
    
    return token

def main():
    if len(sys.argv) < 2:
        print("Uso: python format_token.py <token>")
        print("\nExemplo:")
        print('  python format_token.py "eyJhbGciOiJSUzI1NiIs..."')
        print('  python format_token.py \'Bearer "eyJhbGciOiJSUzI1NiIs..."\'')
        sys.exit(1)
    
    # Pega o token (pode ter espaços se vier entre aspas)
    raw_token = " ".join(sys.argv[1:])
    
    print("=" * 60)
    print("FORMATADOR DE TOKEN JWT")
    print("=" * 60)
    print(f"\nToken original (primeiros 50 chars):")
    print(f"  {raw_token[:50]}...")
    
    cleaned_token = clean_token(raw_token)
    
    print(f"\nToken limpo (primeiros 50 chars):")
    print(f"  {cleaned_token[:50]}...")
    
    # Valida formato básico (deve ter 3 partes separadas por ponto)
    parts = cleaned_token.split('.')
    if len(parts) != 3:
        print(f"\n⚠️  AVISO: Token não parece válido (deve ter 3 partes, encontrado {len(parts)})")
    else:
        print(f"\n✅ Token formatado corretamente (3 partes encontradas)")
    
    print("\n" + "=" * 60)
    print("TOKEN PRONTO PARA USAR:")
    print("=" * 60)
    print(cleaned_token)
    print("=" * 60)
    
    print("\n💡 Dica: Copie o token acima e cole no campo 'Authorize' da documentação OpenAPI")
    print("   Ou use diretamente: Bearer " + cleaned_token[:30] + "...")

if __name__ == "__main__":
    main()

