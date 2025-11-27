"""Script para testar autenticação com token do Clerk."""
import asyncio
import httpx
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================
# CONFIGURE SEU TOKEN AQUI
# ============================================
TOKEN = "seu_token_do_clerk_aqui"  # ← Cole o token aqui


async def test_endpoints():
    """Testa os endpoints da API com o token fornecido."""
    
    if TOKEN == "seu_token_do_clerk_aqui":
        print("=" * 60)
        print("❌ ERRO: Configure o TOKEN no script primeiro!")
        print("=" * 60)
        print()
        print("1. Obtenha um token JWT do Clerk")
        print("2. Edite este arquivo e cole o token na variável TOKEN")
        print("3. Execute novamente: python scripts/test_auth.py")
        print()
        print("Veja: docs/COMO_OBTER_TOKEN_CLERK.md para mais detalhes")
        sys.exit(1)
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("TESTE DE AUTENTICAÇÃO - Otica API")
    print("=" * 60)
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Teste 1: Health (público - não precisa de token)
        print("1️⃣  Testando GET /health (público)...")
        try:
            response = await client.get("http://127.0.0.1:8000/health")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Resposta: {response.json()}")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        print()
        
        # Teste 2: Root (público)
        print("2️⃣  Testando GET / (público)...")
        try:
            response = await client.get("http://127.0.0.1:8000/")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Resposta: {response.json()}")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        print()
        
        # Teste 3: List staff (protegido - precisa de token)
        print("3️⃣  Testando GET /api/v1/staff (protegido)...")
        try:
            response = await client.get(
                "http://127.0.0.1:8000/api/v1/staff",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Sucesso! Encontrados {len(data)} membros")
                if data:
                    print(f"   📋 Primeiro membro: {data[0].get('full_name', 'N/A')}")
            elif response.status_code == 401:
                print(f"   ❌ 401 Unauthorized - Token inválido ou expirado")
                print(f"   📄 Erro: {response.json()}")
            elif response.status_code == 403:
                print(f"   ❌ 403 Forbidden - Token sem organization_id")
                print(f"   📄 Erro: {response.json()}")
            elif response.status_code == 404:
                print(f"   ❌ 404 Not Found - Usuário não encontrado no staff")
                print(f"   💡 Dica: Crie um registro em staff_members com o clerk_id do token")
                print(f"   📄 Erro: {response.json()}")
            else:
                print(f"   ⚠️  Status inesperado: {response.status_code}")
                print(f"   📄 Resposta: {response.text}")
        except httpx.ConnectError:
            print(f"   ❌ Erro: Não foi possível conectar ao servidor")
            print(f"   💡 Certifique-se que o servidor está rodando em http://127.0.0.1:8000")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        print()
        
        # Teste 4: Stats (protegido - precisa de token e role MANAGER/ADMIN)
        print("4️⃣  Testando GET /api/v1/staff/stats (protegido - MANAGER/ADMIN)...")
        try:
            response = await client.get(
                "http://127.0.0.1:8000/api/v1/staff/stats",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Sucesso!")
                print(f"   📄 Resposta: {response.json()}")
            elif response.status_code == 403:
                print(f"   ❌ 403 Forbidden - Role insuficiente (precisa MANAGER ou ADMIN)")
                print(f"   📄 Erro: {response.json()}")
            else:
                print(f"   📄 Resposta: {response.text}")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        print()
    
    print("=" * 60)
    print("✅ Testes concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_endpoints())

