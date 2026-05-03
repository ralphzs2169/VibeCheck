import asyncio
from backend.app.core.database import AsyncSessionLocal
from backend.app.services.user_service import authenticate_user

async def main():
    async with AsyncSessionLocal() as db:
        # Test with the first user
        user = await authenticate_user(db, "matthew34", "Password123")
        if user:
            print(f'Authentication successful for {user.username}')
        else:
            print('Authentication failed')

if __name__ == "__main__":
    asyncio.run(main())