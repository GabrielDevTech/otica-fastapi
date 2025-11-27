"""Script para verificar se o token tem organization_id."""
import sys
import jwt

if len(sys.argv) < 2:
    print("Uso: python scripts/check_token_org.py <token_jwt>")
    print()
    print("Exemplo:")
    print("  python scripts/check_token_org.py eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")
    sys.exit(1)

token = sys.argv[1]

try:
    # Decodifica sem validar (apenas para inspeção)
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    print("=" * 60)
    print("ANÁLISE DO TOKEN")
    print("=" * 60)
    print()
    
    print("📋 PAYLOAD DO TOKEN:")
    for key, value in decoded.items():
        print(f"   {key}: {value}")
    print()
    
    print("🔍 VERIFICAÇÕES:")
    
    # Verificar impersonation
    if "act" in decoded:
        act = decoded.get("act", {})
        if isinstance(act, dict) and "sub" in act:
            print(f"   ⚠️  Token é de IMPERSONATION")
            print(f"      Usuário original: {act.get('sub')}")
            print(f"      Usuário impersonado: {decoded.get('sub')}")
            print(f"   💡 Para API, use token normal (não impersonado)")
    
    # Verificar org_id (direto ou em o.id)
    org_id = decoded.get("org_id")
    if not org_id and "o" in decoded:
        org_obj = decoded.get("o", {})
        if isinstance(org_obj, dict):
            org_id = org_obj.get("id")
            if org_id:
                print(f"   ✅ Token TEM 'o.id' (organization): {org_id}")
                print(f"   💡 Você pode usar este token na API!")
    elif org_id:
        print(f"   ✅ Token TEM 'org_id': {org_id}")
        print(f"   💡 Você pode usar este token na API!")
    else:
        print(f"   ❌ Token NÃO tem 'org_id' nem 'o.id'")
        print(f"   💡 Solução:")
        print(f"      1. Acesse dashboard.clerk.com")
        print(f"      2. Vá em Organizations")
        print(f"      3. Adicione seu usuário a uma organização")
        print(f"      4. Gere um novo token")
    
    # Verificar sub (user_id)
    if "sub" in decoded:
        print(f"   ✅ Token tem 'sub' (user_id): {decoded['sub']}")
    else:
        print(f"   ❌ Token NÃO tem 'sub'")
    
    # Verificar issuer
    if "iss" in decoded:
        print(f"   ✅ Token tem 'iss' (issuer): {decoded['iss']}")
    else:
        print(f"   ❌ Token NÃO tem 'iss'")
    
    print()
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Erro ao decodificar token: {str(e)}")
    print("💡 Certifique-se que é um token JWT válido")

