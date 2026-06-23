"""
CommerceMind VoiceCare AI — Database Seeder
Seeds the database with fictional demo data and ingests policy documents into Chroma.
Run: python -m app.utils.seed_db
"""

import asyncio
import uuid
import structlog
from datetime import datetime

from app.core.database import engine, async_session, Base
from app.db.models import (
    User, Product, Order, OrderItem, Shipment, Return, Refund,
    Payment, EscalationRule,
)
from data.seed.seed_data import (
    SEED_USERS, SEED_PRODUCTS, SEED_ORDERS, SEED_SHIPMENTS,
    SEED_RETURNS, SEED_REFUNDS, SEED_PAYMENTS, SEED_ESCALATION_RULES,
    PRODUCT_IDS,
)
from data.policies.policy_documents import get_all_policies
from app.services.chroma_service import get_chroma_service

logger = structlog.get_logger()


async def seed_database():
    """Seed all tables with fictional demo data."""

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")

    async with async_session() as db:
        # Users
        for u in SEED_USERS:
            db.add(User(**u, created_at=datetime.utcnow()))
        await db.flush()
        print(f"✅ {len(SEED_USERS)} users seeded")

        # Products
        for p in SEED_PRODUCTS:
            db.add(Product(**p, created_at=datetime.utcnow()))
        await db.flush()
        print(f"✅ {len(SEED_PRODUCTS)} products seeded")

        # Orders + Order Items
        for i, o in enumerate(SEED_ORDERS):
            order = Order(**o, created_at=datetime.utcnow())
            db.add(order)
            await db.flush()
            # Add 1-2 items per order
            product_idx = i % len(PRODUCT_IDS)
            db.add(OrderItem(
                order_id=o["order_id"],
                product_id=PRODUCT_IDS[product_idx],
                quantity=1,
                price_at_purchase=SEED_PRODUCTS[product_idx]["price"],
            ))
        await db.flush()
        print(f"✅ {len(SEED_ORDERS)} orders seeded with items")

        # Shipments
        for s in SEED_SHIPMENTS:
            db.add(Shipment(**s, created_at=datetime.utcnow()))
        await db.flush()
        print(f"✅ {len(SEED_SHIPMENTS)} shipments seeded")

        # Returns
        return_ids = []
        for r in SEED_RETURNS:
            ret = Return(**r, requested_at=datetime.utcnow())
            db.add(ret)
            await db.flush()
            return_ids.append(ret.return_id)
        print(f"✅ {len(SEED_RETURNS)} returns seeded")

        # Refunds
        for ref in SEED_REFUNDS:
            return_idx = ref.pop("return_order_index")
            db.add(Refund(
                return_id=return_ids[return_idx] if return_idx < len(return_ids) else None,
                order_id=ref["order_id"],
                amount=ref["amount"],
                status=ref["status"],
                credited_at=ref.get("credited_at"),
                created_at=datetime.utcnow(),
            ))
        await db.flush()
        print(f"✅ {len(SEED_REFUNDS)} refunds seeded")

        # Payments
        for p in SEED_PAYMENTS:
            db.add(Payment(**p, transaction_date=datetime.utcnow()))
        await db.flush()
        print(f"✅ {len(SEED_PAYMENTS)} payments seeded")

        # Escalation Rules
        for rule in SEED_ESCALATION_RULES:
            db.add(EscalationRule(**rule, created_at=datetime.utcnow()))
        await db.flush()
        print(f"✅ {len(SEED_ESCALATION_RULES)} escalation rules seeded")

        await db.commit()
        print("✅ All database seeding complete!")

    # Ingest policies into Chroma
    chroma = get_chroma_service()
    policies = get_all_policies()
    count = chroma.ingest_policies(policies)
    print(f"✅ {count} policy documents ingested into Chroma")
    print(f"   Chroma collection size: {chroma.get_collection_count()}")


if __name__ == "__main__":
    asyncio.run(seed_database())
