import asyncio
from db import Base, engine
from models import (
    Moderator,
    User,
    Complaint,
    BloggerRequest,
    BuildingsRequest,
    ImprovementsRequest,
    ModerationRequest,
    ErrorRequest,
    GlobalCounter,
)


async def main():
    # Создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(main())
