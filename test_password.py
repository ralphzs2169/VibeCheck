import asyncio
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.services.user_service import verify_password
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalars().first()
        if user:
            print(f'Testing user: {user.username}')
            print(f'Hashed password: {user.hashed_password}')
            is_valid = verify_password("Password123", user.hashed_password)
            print(f'Password "Password123" valid: {is_valid}')

if __name__ == "__main__":
    asyncio.run(main())