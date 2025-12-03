"""
Script de Migration para Sprint 1 - Alicerces do Sistema

Este script aplica todas as mudanças necessárias no banco de dados:
1. Atualiza tabela stores (adiciona address_data, tax_rate_machine)
2. Atualiza tabela departments (adiciona description)
3. Atualiza tabela staff_members (torna store_id e department_id obrigatórios, adiciona job_title)
4. Cria tabela products_frames
5. Cria tabela inventory_levels
6. Cria tabela products_lenses
7. Cria tabela lens_stock_grid
8. Cria tabela customers
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path do Python
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from app.core.database import engine


async def run_migrations():
    """Executa todas as migrations."""
    # Usa engine.connect() ao invés de begin() para permitir rollback em caso de erro
    async with engine.connect() as conn:
        # Inicia transação manualmente
        await conn.begin()
        print("🔄 Iniciando migrations da Sprint 1...")
        
        # 1. Atualizar stores
        print("\n1️⃣ Atualizando tabela stores...")
        try:
            await conn.execute(text("""
                ALTER TABLE stores 
                ADD COLUMN IF NOT EXISTS address_data JSONB NULL;
            """))
            print("   ✅ Campo address_data adicionado")
        except Exception as e:
            print(f"   ⚠️ Erro ao adicionar address_data: {e}")
        
        try:
            await conn.execute(text("""
                ALTER TABLE stores 
                ADD COLUMN IF NOT EXISTS tax_rate_machine NUMERIC(5, 2) NULL;
            """))
            print("   ✅ Campo tax_rate_machine adicionado")
        except Exception as e:
            print(f"   ⚠️ Erro ao adicionar tax_rate_machine: {e}")
        
        # 2. Atualizar departments
        print("\n2️⃣ Atualizando tabela departments...")
        try:
            await conn.execute(text("""
                ALTER TABLE departments 
                ADD COLUMN IF NOT EXISTS description TEXT NULL;
            """))
            print("   ✅ Campo description adicionado")
        except Exception as e:
            print(f"   ⚠️ Erro ao adicionar description: {e}")
        
        # 3. Atualizar staff_members
        print("\n3️⃣ Atualizando tabela staff_members...")
        try:
            # Adicionar job_title se não existir
            await conn.execute(text("""
                ALTER TABLE staff_members 
                ADD COLUMN IF NOT EXISTS job_title VARCHAR NULL;
            """))
            print("   ✅ Campo job_title adicionado")
        except Exception as e:
            print(f"   ⚠️ Erro ao adicionar job_title: {e}")
        
        # Atualizar registros NULL de store_id e department_id
        print("   🔄 Atualizando registros NULL de store_id e department_id...")
        try:
            # Primeiro, atualizar store_id NULL
            await conn.execute(text("""
                UPDATE staff_members 
                SET store_id = (
                    SELECT id FROM stores 
                    WHERE organization_id = (
                        SELECT id FROM organizations 
                        WHERE clerk_org_id = staff_members.organization_id
                    ) 
                    LIMIT 1
                )
                WHERE store_id IS NULL
                AND EXISTS (
                    SELECT 1 FROM stores 
                    WHERE organization_id = (
                        SELECT id FROM organizations 
                        WHERE clerk_org_id = staff_members.organization_id
                    )
                );
            """))
            print("   ✅ Registros NULL de store_id atualizados")
        except Exception as e:
            print(f"   ⚠️ Erro ao atualizar store_id: {e}")
        
        try:
            # Atualizar department_id NULL
            await conn.execute(text("""
                UPDATE staff_members 
                SET department_id = (
                    SELECT id FROM departments 
                    WHERE organization_id = (
                        SELECT id FROM organizations 
                        WHERE clerk_org_id = staff_members.organization_id
                    ) 
                    LIMIT 1
                )
                WHERE department_id IS NULL
                AND EXISTS (
                    SELECT 1 FROM departments 
                    WHERE organization_id = (
                        SELECT id FROM organizations 
                        WHERE clerk_org_id = staff_members.organization_id
                    )
                );
            """))
            print("   ✅ Registros NULL de department_id atualizados")
        except Exception as e:
            print(f"   ⚠️ Erro ao atualizar department_id: {e}")
        
        # Verificar se ainda há NULL antes de tornar obrigatório
        result = await conn.execute(text("""
            SELECT COUNT(*) as null_count 
            FROM staff_members 
            WHERE store_id IS NULL;
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            print(f"   ⚠️ Ainda há {null_count} registros com store_id NULL")
            print("   💡 Não é possível tornar store_id obrigatório. Atualize os registros manualmente.")
        else:
            try:
                await conn.execute(text("""
                    ALTER TABLE staff_members 
                    ALTER COLUMN store_id SET NOT NULL;
                """))
                print("   ✅ store_id agora é obrigatório")
            except Exception as e:
                print(f"   ⚠️ Erro ao tornar store_id obrigatório: {e}")
        
        result = await conn.execute(text("""
            SELECT COUNT(*) as null_count 
            FROM staff_members 
            WHERE department_id IS NULL;
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            print(f"   ⚠️ Ainda há {null_count} registros com department_id NULL")
            print("   💡 Não é possível tornar department_id obrigatório. Atualize os registros manualmente.")
        else:
            try:
                await conn.execute(text("""
                    ALTER TABLE staff_members 
                    ALTER COLUMN department_id SET NOT NULL;
                """))
                print("   ✅ department_id agora é obrigatório")
            except Exception as e:
                print(f"   ⚠️ Erro ao tornar department_id obrigatório: {e}")
        
        # 4. Criar tabela products_frames
        print("\n4️⃣ Criando tabela products_frames...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS products_frames (
                    id SERIAL PRIMARY KEY,
                    organization_id VARCHAR NOT NULL,
                    reference_code VARCHAR(100) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    brand VARCHAR(100),
                    model VARCHAR(100),
                    cost_price NUMERIC(10, 2),
                    sell_price NUMERIC(10, 2) NOT NULL,
                    min_stock_alert INTEGER DEFAULT 0 NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """))
            print("   ✅ Tabela products_frames criada")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar products_frames: {e}")
        
        # Índices para products_frames
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_frame_org_code_unique 
                ON products_frames(organization_id, reference_code);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_frame_org_active 
                ON products_frames(organization_id, is_active);
            """))
            print("   ✅ Índices de products_frames criados")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar índices: {e}")
        
        # 5. Criar tabela inventory_levels
        print("\n5️⃣ Criando tabela inventory_levels...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS inventory_levels (
                    id SERIAL PRIMARY KEY,
                    organization_id VARCHAR NOT NULL,
                    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                    product_frame_id INTEGER NOT NULL REFERENCES products_frames(id) ON DELETE CASCADE,
                    quantity INTEGER DEFAULT 0 NOT NULL,
                    reserved_quantity INTEGER DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """))
            print("   ✅ Tabela inventory_levels criada")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar inventory_levels: {e}")
        
        # Índices para inventory_levels
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_inv_store_frame 
                ON inventory_levels(store_id, product_frame_id);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_inv_org_store 
                ON inventory_levels(organization_id, store_id);
            """))
            print("   ✅ Índices de inventory_levels criados")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar índices: {e}")
        
        # 6. Criar tabela products_lenses
        print("\n6️⃣ Criando tabela products_lenses...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS products_lenses (
                    id SERIAL PRIMARY KEY,
                    organization_id VARCHAR NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    brand VARCHAR(100),
                    model VARCHAR(100),
                    cost_price NUMERIC(10, 2),
                    sell_price NUMERIC(10, 2) NOT NULL,
                    is_lab_order BOOLEAN DEFAULT FALSE NOT NULL,
                    treatment VARCHAR(100),
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """))
            print("   ✅ Tabela products_lenses criada")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar products_lenses: {e}")
        
        # Índices para products_lenses
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_lens_org_active 
                ON products_lenses(organization_id, is_active);
            """))
            print("   ✅ Índices de products_lenses criados")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar índices: {e}")
        
        # 7. Criar tabela lens_stock_grid
        print("\n7️⃣ Criando tabela lens_stock_grid...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lens_stock_grid (
                    id SERIAL PRIMARY KEY,
                    organization_id VARCHAR NOT NULL,
                    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                    product_lens_id INTEGER NOT NULL REFERENCES products_lenses(id) ON DELETE CASCADE,
                    spherical NUMERIC(5, 2) NOT NULL,
                    cylindrical NUMERIC(5, 2) NOT NULL,
                    axis INTEGER,
                    quantity INTEGER DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """))
            print("   ✅ Tabela lens_stock_grid criada")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar lens_stock_grid: {e}")
        
        # Índices para lens_stock_grid
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_lens_grid_unique 
                ON lens_stock_grid(store_id, product_lens_id, spherical, cylindrical, axis);
            """))
            print("   ✅ Índices de lens_stock_grid criados")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar índices: {e}")
        
        # 8. Criar tabela customers
        print("\n8️⃣ Criando tabela customers...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    organization_id VARCHAR NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    cpf VARCHAR(11) NOT NULL,
                    birth_date DATE NOT NULL,
                    email VARCHAR(255),
                    phone VARCHAR(20),
                    profession VARCHAR(100),
                    address_street VARCHAR(255),
                    address_number VARCHAR(20),
                    address_complement VARCHAR(100),
                    address_neighborhood VARCHAR(100),
                    address_city VARCHAR(100),
                    address_state VARCHAR(2),
                    address_zipcode VARCHAR(10),
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """))
            print("   ✅ Tabela customers criada")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar customers: {e}")
        
        # Índices para customers
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_org_cpf 
                ON customers(organization_id, cpf);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_customer_org_name 
                ON customers(organization_id, full_name);
            """))
            print("   ✅ Índices de customers criados")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar índices: {e}")
        
        # Atualizar enum StaffRole para incluir SELLER
        print("\n9️⃣ Atualizando enum StaffRole...")
        try:
            await conn.execute(text("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_enum 
                        WHERE enumlabel = 'SELLER' 
                        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'staffrole')
                    ) THEN
                        ALTER TYPE staffrole ADD VALUE 'SELLER';
                    END IF;
                END $$;
            """))
            print("   ✅ Valor SELLER adicionado ao enum StaffRole")
        except Exception as e:
            print(f"   ⚠️ Erro ao atualizar enum: {e}")
            print("   💡 O enum pode já ter o valor SELLER ou não existir")
        
        # Commit da transação
        await conn.commit()
        print("\n✅ Migrations concluídas!")
        print("\n📝 Próximos passos:")
        print("   1. Verifique se todas as tabelas foram criadas corretamente")
        print("   2. Verifique se os índices foram criados")
        print("   3. Se houver registros com store_id/department_id NULL, atualize-os manualmente")
        print("   4. Teste os endpoints da API")


if __name__ == "__main__":
    asyncio.run(run_migrations())

