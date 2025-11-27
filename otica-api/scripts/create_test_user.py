"""Script para criar usuário de teste no staff como ADMIN."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.staff_model import StaffMember, StaffRole
from sqlalchemy import select


async def create_test_user():
    """
    Cria um usuário de teste como ADMIN.
    
    IMPORTANTE: Você precisa fornecer o organization_id do seu token Clerk!
    """
    print("=" * 60)
    print("CRIAR USUÁRIO DE TESTE - ADMIN")
    print("=" * 60)
    print()
    
    # ============================================
    # CONFIGURE AQUI
    # ============================================
    CLERK_USER_ID = "user_362f7Ug2v5SRN"  # User ID do Clerk
    ORGANIZATION_ID = "org_xxx"  # ← SUBSTITUA pelo org_id do seu token!
    FULL_NAME = "123 123"
    EMAIL = "bielleandro75@gmail.com"
    ROLE = StaffRole.ADMIN  # ADMIN = máximo controle
    # ============================================
    
    if ORGANIZATION_ID == "org_xxx":
        print("❌ ERRO: Configure o ORGANIZATION_ID!")
        print()
        print("Para obter o organization_id:")
        print("1. Decodifique seu token JWT em: https://jwt.io")
        print("2. Procure pelo campo 'org_id' no payload")
        print("3. Cole o valor em ORGANIZATION_ID acima")
        print()
        sys.exit(1)
    
    async with AsyncSessionLocal() as db:
        try:
            # Verificar se já existe
            existing = await db.execute(
                select(StaffMember).where(
                    StaffMember.clerk_id == CLERK_USER_ID,
                    StaffMember.organization_id == ORGANIZATION_ID
                )
            )
            existing_user = existing.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  Usuário já existe! Atualizando...")
                print(f"   ID: {existing_user.id}")
                print(f"   Role atual: {existing_user.role.value}")
                print()
                
                # Atualizar para ADMIN
                existing_user.role = ROLE
                existing_user.is_active = True
                existing_user.full_name = FULL_NAME
                existing_user.email = EMAIL
                
                await db.commit()
                await db.refresh(existing_user)
                
                print("✅ Usuário atualizado com sucesso!")
                print()
                print("📋 Dados do usuário:")
                print(f"   ID: {existing_user.id}")
                print(f"   Clerk ID: {existing_user.clerk_id}")
                print(f"   Organization ID: {existing_user.organization_id}")
                print(f"   Nome: {existing_user.full_name}")
                print(f"   Email: {existing_user.email}")
                print(f"   Role: {existing_user.role.value}")
                print(f"   Ativo: {existing_user.is_active}")
            else:
                # Criar novo
                print("📝 Criando novo usuário...")
                print()
                
                new_user = StaffMember(
                    clerk_id=CLERK_USER_ID,
                    organization_id=ORGANIZATION_ID,
                    full_name=FULL_NAME,
                    email=EMAIL,
                    role=ROLE,
                    is_active=True,
                    department=None
                )
                
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                
                print("✅ Usuário criado com sucesso!")
                print()
                print("📋 Dados do usuário:")
                print(f"   ID: {new_user.id}")
                print(f"   Clerk ID: {new_user.clerk_id}")
                print(f"   Organization ID: {new_user.organization_id}")
                print(f"   Nome: {new_user.full_name}")
                print(f"   Email: {new_user.email}")
                print(f"   Role: {new_user.role.value}")
                print(f"   Ativo: {new_user.is_active}")
            
            print()
            print("=" * 60)
            print("✅ Pronto para testar!")
            print("=" * 60)
            print()
            print("Agora você pode:")
            print("1. Obter um token JWT do Clerk com este user_id")
            print("2. Testar os endpoints em http://127.0.0.1:8000/docs")
            print("3. Ou usar: python scripts/test_auth.py")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Erro ao criar usuário: {str(e)}")
            print()
            print("Verifique:")
            print("1. Se o DATABASE_URL está correto")
            print("2. Se o banco de dados está acessível")
            print("3. Se o organization_id está correto")
            raise


if __name__ == "__main__":
    asyncio.run(create_test_user())

