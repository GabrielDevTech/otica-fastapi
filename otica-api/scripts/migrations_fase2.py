"""Script de migração para Fase 2 - Ciclo de Venda.

Cria todas as tabelas necessárias para a Fase 2:
- cash_sessions
- cash_movements
- service_orders
- service_order_items
- sales
- receivable_accounts
- kardex
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models import (
    cash_session_model,
    cash_movement_model,
    service_order_model,
    service_order_item_model,
    sale_model,
    receivable_account_model,
    kardex_model
)


async def create_fase2_tables():
    """Cria todas as tabelas da Fase 2."""
    print("🔧 Criando tabelas da Fase 2 (Ciclo de Venda)...")
    print()
    
    try:
        async with engine.begin() as conn:
            # Cria todas as tabelas definidas nos models
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tabelas da Fase 2 criadas com sucesso!")
        print()
        print("📋 Tabelas criadas:")
        print("   - cash_sessions (Sessões de Caixa)")
        print("   - cash_movements (Movimentações de Caixa)")
        print("   - service_orders (Ordens de Serviço)")
        print("   - service_order_items (Itens das OS)")
        print("   - sales (Vendas)")
        print("   - receivable_accounts (Contas a Receber)")
        print("   - kardex (Histórico de Movimentação)")
        print()
        print("📊 Enums criados:")
        print("   - CashSessionStatus (OPEN, CLOSED, PENDING_AUDIT)")
        print("   - CashMovementType (WITHDRAWAL, DEPOSIT)")
        print("   - ServiceOrderStatus (DRAFT, PENDING, PAID, AWAITING_LENS, IN_PRODUCTION, READY, DELIVERED, CANCELLED)")
        print("   - PaymentMethod (CASH, CARD, PIX, CREDIT)")
        print("   - ReceivableStatus (PENDING, PARTIAL, PAID, OVERDUE, CANCELLED)")
        print()
        print("✅ Migração concluída!")
        
    except Exception as e:
        print("=" * 60)
        print("❌ ERRO AO CRIAR TABELAS")
        print("=" * 60)
        print()
        print(f"Erro: {str(e)}")
        print()
        print("Verifique:")
        print("1. Se o DATABASE_URL está correto no .env")
        print("2. Se o banco de dados está acessível")
        print("3. Se as credenciais estão corretas")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_fase2_tables())

