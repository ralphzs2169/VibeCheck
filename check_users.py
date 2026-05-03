import asyncio
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.user import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f'Found {len(users)} users:')
        for u in users[:3]:
            print(f'  {u.username}: {u.hashed_password[:20]}...')

if __name__ == "__main__":
    asyncio.run(main())