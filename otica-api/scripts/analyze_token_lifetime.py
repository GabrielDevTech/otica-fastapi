"""
Script para analisar a validade e tipo de token JWT.

Mostra:
- Se é token de impersonation
- Tempo de validade restante
- Quando foi criado
- Quando expira
"""
import sys
import jwt
from datetime import datetime

def format_timestamp(ts: int) -> str:
    """Formata timestamp para data/hora legível."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def format_duration(seconds: int) -> str:
    """Formata duração em formato legível."""
    if seconds < 60:
        return f"{seconds} segundos"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes} minutos e {secs} segundos"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} horas e {minutes} minutos"

if len(sys.argv) < 2:
    print("Uso: python scripts/analyze_token_lifetime.py <token_jwt>")
    print()
    print("Exemplo:")
    print("  python scripts/analyze_token_lifetime.py eyJhbGciOiJSUzI1NiIs...")
    sys.exit(1)

token = sys.argv[1]

try:
    # Decodifica sem validar (apenas para inspeção)
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    print("=" * 70)
    print("ANÁLISE DE VALIDADE DO TOKEN")
    print("=" * 70)
    print()
    
    # Verificar tipo de token
    is_impersonation = "act" in decoded
    if is_impersonation:
        act = decoded.get("act", {})
        print("🔍 TIPO DE TOKEN: IMPERSONATION")
        print(f"   Usuário original (admin): {act.get('sub', 'N/A')}")
        print(f"   Usuário impersonado: {decoded.get('sub', 'N/A')}")
        print()
    else:
        print("🔍 TIPO DE TOKEN: NORMAL")
        print(f"   Usuário: {decoded.get('sub', 'N/A')}")
        print()
    
    # Informações de tempo
    iat = decoded.get("iat")
    exp = decoded.get("exp")
    nbf = decoded.get("nbf", iat)  # Not before (se não tiver, usa iat)
    
    now = datetime.now().timestamp()
    
    if iat:
        print(f"📅 CRIADO EM: {format_timestamp(iat)}")
    
    if nbf and nbf != iat:
        print(f"⏰ VÁLIDO A PARTIR DE: {format_timestamp(nbf)}")
    
    if exp:
        print(f"⏰ EXPIRA EM: {format_timestamp(exp)}")
        
        # Calcular tempo restante
        if now < exp:
            remaining = int(exp - now)
            print(f"⏳ TEMPO RESTANTE: {format_duration(remaining)}")
            
            # Aviso se for muito curto (impersonation)
            if remaining < 120 and is_impersonation:
                print()
                print("⚠️  AVISO: Token de impersonation com validade curta (comportamento esperado)")
                print("   Tokens de impersonation expiram em ~60 segundos por segurança")
        else:
            expired = int(now - exp)
            print(f"❌ TOKEN EXPIRADO há {format_duration(expired)}")
    
    # Duração total
    if iat and exp:
        total_duration = exp - iat
        print(f"⏱️  DURAÇÃO TOTAL: {format_duration(int(total_duration))}")
        
        if total_duration < 120:
            print()
            print("💡 Este é um token de IMPERSONATION (validade curta por segurança)")
        elif total_duration < 3600:
            print()
            print("💡 Este é um token com validade reduzida")
        else:
            print()
            print("💡 Este é um token NORMAL (validade padrão)")
    
    # Organization ID
    org_id = decoded.get("org_id")
    if not org_id and "o" in decoded:
        org_obj = decoded.get("o", {})
        if isinstance(org_obj, dict):
            org_id = org_obj.get("id")
    
    if org_id:
        print(f"🏢 ORGANIZATION ID: {org_id}")
    else:
        print("❌ ORGANIZATION ID: Não encontrado")
    
    print()
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Erro ao decodificar token: {str(e)}")
    print("💡 Certifique-se que é um token JWT válido")

