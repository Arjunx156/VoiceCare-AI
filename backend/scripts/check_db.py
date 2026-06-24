import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

async def main():
    load_dotenv('../.env')
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("No DATABASE_URL found.")
        return

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT ticket_id, status FROM support_tickets WHERE status = 'Escalated' ORDER BY created_at DESC LIMIT 5"))
        rows = res.fetchall()
        print('Escalated Tickets:', rows)

        res2 = await conn.execute(text("SELECT ticket_id, status FROM support_tickets"))
        rows2 = res2.fetchall()
        print('All Tickets Status:', [row[1] for row in rows2])

asyncio.run(main())
