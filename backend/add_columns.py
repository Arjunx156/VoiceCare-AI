import asyncio
import os
import asyncpg

DATABASE_URL = os.environ.get("DATABASE_URL")

async def add_audit_columns():
    conn = await asyncpg.connect(DATABASE_URL)
    tables = [
        "users", "orders", "returns", "refunds",
        "support_tickets", "support_messages", "support_resolutions"
    ]
    
    for table in tables:
        try:
            print(f"Adding columns to {table}...")
            await conn.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;")
            await conn.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS created_by VARCHAR(100);")
            await conn.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100);")
        except Exception as e:
            print(f"Error on {table}: {e}")
            
    await conn.close()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(add_audit_columns())
