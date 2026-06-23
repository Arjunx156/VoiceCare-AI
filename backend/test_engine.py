import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

url = 'postgresql+asyncpg://neondb_owner:npg_aYef9q1lPHTE@ep-winter-smoke-ai8i8i6x-pooler.c-4.us-east-1.aws.neon.tech/neondb?ssl=require'

async def test_engine():
    engine = create_async_engine(url, echo=True)
    try:
        async with engine.begin() as conn:
            print("Connected!")
    except Exception as e:
        print("Error:", repr(e))

asyncio.run(test_engine())
