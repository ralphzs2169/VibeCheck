import asyncio
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.user import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User.username))
        usernames = [row[0] for row in result.fetchall()]
        print('Available usernames:')
        for u in usernames:
            print(f'  {u}')

if __name__ == "__main__":
    asyncio.run(main())