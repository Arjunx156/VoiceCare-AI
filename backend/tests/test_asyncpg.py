import asyncio
import asyncpg
import os

url = 'postgresql://neondb_owner:npg_aYef9q1lPHTE@ep-winter-smoke-ai8i8i6x.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require'

async def main():
    try:
        print("Connecting to:", url)
        conn = await asyncpg.connect(url)
        print("Success!")
        await conn.close()
    except Exception as e:
        print("Error:", repr(e))

asyncio.run(main())
